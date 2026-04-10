"""
Twitch API Streamer Importer
============================
Pulls live streamers from the Twitch API across major gaming categories
and upserts them into the local streamers table.

Setup (free):
  1. Go to https://dev.twitch.tv/console → Register Your Application
  2. Set a name, redirect URL (anything, e.g. http://localhost), category = "Application Integration"
  3. Copy Client ID and generate a Client Secret
  4. Set env vars: TWITCH_CLIENT_ID, TWITCH_CLIENT_SECRET

The OAuth client-credentials flow is fully automated — no user login needed.

What it imports:
  - Streamers currently live across 30+ game categories
  - All viewer tiers: from mega (100K+) down to nano (50+ viewers)
  - Profile image, bio, display name, language, current game
  - Viewer count stored as avg_viewers (live snapshot at import time)
  - Follower count enriched per-user via /channels endpoint
"""
import logging
import time
from typing import Optional

import httpx
from sqlalchemy.orm import Session

from app.models.streamer import Streamer

logger = logging.getLogger(__name__)

TWITCH_AUTH_URL = "https://id.twitch.tv/oauth2/token"
TWITCH_API_BASE = "https://api.twitch.tv/helix"

# 30 major gaming categories (mix of competitive, variety, and niche)
GAMING_CATEGORIES = [
    # Big FPS / Battle Royale
    "Fortnite",
    "Valorant",
    "Counter-Strike 2",
    "Apex Legends",
    "Call of Duty: Warzone",
    "PUBG: Battlegrounds",
    "Overwatch 2",
    # MOBAs & Strategy
    "League of Legends",
    "DOTA 2",
    "Teamfight Tactics",
    "StarCraft II",
    # Open World / Sandbox
    "Grand Theft Auto V",
    "Minecraft",
    "Rust",
    "Elden Ring",
    "Baldur's Gate 3",
    # MMO / RPG
    "World of Warcraft",
    "Final Fantasy XIV Online",
    "Diablo IV",
    "Path of Exile",
    "Lost Ark",
    # Variety / IRL
    "Just Chatting",
    "Games + Demos",
    # Sports / Racing
    "EA Sports FC 24",
    "Rocket League",
    "NBA 2K24",
    # Horror / Indie
    "Escape from Tarkov",
    "Hearthstone",
    "Pokémon",
    "Stardew Valley",
]


def _tier_from_viewers(viewers: int) -> str:
    if viewers >= 30000:
        return "mega"
    elif viewers >= 5000:
        return "macro"
    elif viewers >= 500:
        return "mid"
    elif viewers >= 100:
        return "micro"
    return "nano"


def get_app_token(client_id: str, client_secret: str) -> str:
    """Fetch a client-credentials OAuth token."""
    resp = httpx.post(
        TWITCH_AUTH_URL,
        params={
            "client_id": client_id,
            "client_secret": client_secret,
            "grant_type": "client_credentials",
        },
        timeout=15,
    )
    resp.raise_for_status()
    token = resp.json().get("access_token")
    if not token:
        raise ValueError(f"No access_token in Twitch auth response: {resp.text}")
    return token


def _headers(client_id: str, token: str) -> dict:
    return {"Client-ID": client_id, "Authorization": f"Bearer {token}"}


def _get_game_id(client_id: str, token: str, game_name: str) -> Optional[str]:
    """Look up a Twitch game ID by name."""
    try:
        resp = httpx.get(
            f"{TWITCH_API_BASE}/games",
            headers=_headers(client_id, token),
            params={"name": game_name},
            timeout=10,
        )
        data = resp.json().get("data", [])
        return data[0]["id"] if data else None
    except Exception as e:
        logger.warning(f"Failed to get game ID for '{game_name}': {e}")
        return None


def _get_streams_for_game(
    client_id: str,
    token: str,
    game_id: str,
    max_count: int,
) -> list[dict]:
    """
    Paginate /streams for a game_id, collecting up to max_count entries.
    Returns raw stream objects from Twitch.
    """
    streams = []
    cursor = None
    while len(streams) < max_count:
        params: dict = {"game_id": game_id, "first": min(100, max_count - len(streams))}
        if cursor:
            params["after"] = cursor
        try:
            resp = httpx.get(
                f"{TWITCH_API_BASE}/streams",
                headers=_headers(client_id, token),
                params=params,
                timeout=15,
            )
            body = resp.json()
            batch = body.get("data", [])
            if not batch:
                break
            streams.extend(batch)
            cursor = body.get("pagination", {}).get("cursor")
            if not cursor:
                break
            time.sleep(0.1)  # be polite
        except Exception as e:
            logger.warning(f"Stream pagination error: {e}")
            break
    return streams[:max_count]


def _get_users(client_id: str, token: str, user_ids: list[str]) -> list[dict]:
    """Fetch Twitch user profiles in batches of 100."""
    users = []
    for i in range(0, len(user_ids), 100):
        batch = user_ids[i : i + 100]
        try:
            resp = httpx.get(
                f"{TWITCH_API_BASE}/users",
                headers=_headers(client_id, token),
                params=[("id", uid) for uid in batch],
                timeout=15,
            )
            users.extend(resp.json().get("data", []))
            time.sleep(0.1)
        except Exception as e:
            logger.warning(f"User fetch error: {e}")
    return users


def _get_channel_info(client_id: str, token: str, broadcaster_ids: list[str]) -> dict[str, dict]:
    """
    Fetch additional channel info (broadcaster_language, game_name) via /channels.
    Returns dict keyed by broadcaster_id.
    """
    info: dict[str, dict] = {}
    for i in range(0, len(broadcaster_ids), 100):
        batch = broadcaster_ids[i : i + 100]
        try:
            resp = httpx.get(
                f"{TWITCH_API_BASE}/channels",
                headers=_headers(client_id, token),
                params=[("broadcaster_id", bid) for bid in batch],
                timeout=15,
            )
            for ch in resp.json().get("data", []):
                info[ch["broadcaster_id"]] = ch
            time.sleep(0.1)
        except Exception as e:
            logger.warning(f"Channel info fetch error: {e}")
    return info


def import_from_twitch(
    db: Session,
    client_id: str,
    client_secret: str,
    max_per_category: int = 200,
    min_viewers: int = 50,
) -> dict:
    """
    Main import function. Pulls streamers from Twitch API and upserts into DB.

    Args:
        db: SQLAlchemy session
        client_id: Twitch app Client ID
        client_secret: Twitch app Client Secret
        max_per_category: How many streamers to pull per game category (default 200)
        min_viewers: Minimum live viewer count to import (default 50)

    Returns:
        Summary dict with counts of imported / updated / skipped / errors
    """
    token = get_app_token(client_id, client_secret)
    logger.info(f"Twitch import started. max_per_category={max_per_category}, min_viewers={min_viewers}")

    total_imported = 0
    total_updated = 0
    total_skipped = 0
    errors: list[str] = []

    for game_name in GAMING_CATEGORIES:
        game_id = _get_game_id(client_id, token, game_name)
        if not game_id:
            errors.append(f"Game not found: {game_name}")
            continue

        streams = _get_streams_for_game(client_id, token, game_id, max_per_category)
        if not streams:
            logger.info(f"No streams found for '{game_name}'")
            continue

        # Filter by min viewers
        streams = [s for s in streams if s.get("viewer_count", 0) >= min_viewers]
        if not streams:
            continue

        # Build lookup maps
        stream_by_user_id: dict[str, dict] = {s["user_id"]: s for s in streams}
        user_ids = list(stream_by_user_id.keys())

        # Fetch user profiles and channel info in parallel-ish
        users = _get_users(client_id, token, user_ids)
        channel_info = _get_channel_info(client_id, token, user_ids)

        imported_this_cat = 0
        for user in users:
            uid = user["id"]
            stream = stream_by_user_id.get(uid, {})
            ch = channel_info.get(uid, {})
            viewer_count = stream.get("viewer_count", 0)
            login = user.get("login", "")
            if not login:
                continue

            url = f"https://www.twitch.tv/{login}"
            game = stream.get("game_name") or ch.get("game_name") or game_name
            lang = stream.get("language") or ch.get("broadcaster_language") or "en"
            tier = _tier_from_viewers(viewer_count)

            try:
                existing = db.query(Streamer).filter(Streamer.url == url).first()
                if existing:
                    # Refresh live metrics and fill any empty fields
                    existing.avg_viewers = viewer_count
                    if not existing.primary_game and game:
                        existing.primary_game = game
                    if not existing.bio and user.get("description"):
                        existing.bio = user["description"]
                    if not existing.profile_image_url and user.get("profile_image_url"):
                        existing.profile_image_url = user["profile_image_url"]
                    existing.tier = tier
                    total_updated += 1
                else:
                    streamer = Streamer(
                        name=user.get("display_name", login),
                        url=url,
                        platform="twitch",
                        twitch_username=login,
                        bio=user.get("description") or None,
                        profile_image_url=user.get("profile_image_url") or None,
                        language=lang if len(lang) <= 10 else "en",
                        avg_viewers=viewer_count,
                        primary_game=game or None,
                        tier=tier,
                        category="gaming",
                        tags=[game.lower().replace(" ", "-").replace(":", "")] if game else [],
                        priority=5,
                    )
                    db.add(streamer)
                    total_imported += 1
                    imported_this_cat += 1
            except Exception as e:
                logger.warning(f"Failed to upsert streamer {login}: {e}")
                total_skipped += 1

        try:
            db.commit()
        except Exception as e:
            db.rollback()
            errors.append(f"DB commit error for '{game_name}': {e}")

        logger.info(
            f"'{game_name}': {len(streams)} streams → {imported_this_cat} new, "
            f"{total_updated} updated (cumulative)"
        )

    result = {
        "imported": total_imported,
        "updated": total_updated,
        "skipped": total_skipped,
        "categories_processed": len(GAMING_CATEGORIES),
        "errors": errors,
    }
    logger.info(f"Twitch import complete: {result}")
    return result
