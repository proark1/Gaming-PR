"""
Streamer discovery service.

Discovers gaming content creators from:
- Twitch: OAuth2 client-credentials + Helix API (top streams by game, channel lookup)
- YouTube: Public channel RSS + channel page scraping for subscriber count
- X/Twitter: Public profile page scraping for follower count and bio

Environment variables required for Twitch:
    TWITCH_CLIENT_ID      — from dev.twitch.tv app registration
    TWITCH_CLIENT_SECRET  — from dev.twitch.tv app registration

YouTube and X discovery are keyless (scrape / RSS).
"""

import logging
import re
import time
from datetime import datetime, timezone
from typing import Optional

import requests
from sqlalchemy.orm import Session

from app.models.streamer import Streamer

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Shared HTTP session (reused across calls within a request)
# ---------------------------------------------------------------------------
_http = requests.Session()
_http.headers.update(
    {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        )
    }
)

# ---------------------------------------------------------------------------
# Twitch helpers
# ---------------------------------------------------------------------------

_twitch_token: Optional[str] = None
_twitch_token_expires_at: float = 0.0


def _get_twitch_token(client_id: str, client_secret: str) -> str:
    """Fetch (or return cached) Twitch app access token."""
    global _twitch_token, _twitch_token_expires_at
    if _twitch_token and time.time() < _twitch_token_expires_at - 60:
        return _twitch_token
    resp = _http.post(
        "https://id.twitch.tv/oauth2/token",
        data={
            "client_id": client_id,
            "client_secret": client_secret,
            "grant_type": "client_credentials",
        },
        timeout=10,
    )
    resp.raise_for_status()
    data = resp.json()
    _twitch_token = data["access_token"]
    _twitch_token_expires_at = time.time() + data.get("expires_in", 3600)
    return _twitch_token


def _twitch_headers(client_id: str, token: str) -> dict:
    return {
        "Client-Id": client_id,
        "Authorization": f"Bearer {token}",
    }


def _twitch_game_id(client_id: str, token: str, game_name: str) -> Optional[str]:
    """Resolve a game name to a Twitch game ID."""
    resp = _http.get(
        "https://api.twitch.tv/helix/games",
        params={"name": game_name},
        headers=_twitch_headers(client_id, token),
        timeout=10,
    )
    resp.raise_for_status()
    data = resp.json().get("data", [])
    return data[0]["id"] if data else None


def _twitch_top_streams(
    client_id: str, token: str, game_id: str, limit: int, min_viewers: int
) -> list[dict]:
    """
    Pull top live streams for a game.
    Returns list of stream dicts with login/user_id/viewer_count etc.
    """
    streams: list[dict] = []
    cursor = None
    per_page = min(100, limit)
    while len(streams) < limit:
        params: dict = {"game_id": game_id, "first": per_page}
        if cursor:
            params["after"] = cursor
        resp = _http.get(
            "https://api.twitch.tv/helix/streams",
            params=params,
            headers=_twitch_headers(client_id, token),
            timeout=10,
        )
        resp.raise_for_status()
        body = resp.json()
        page = body.get("data", [])
        if not page:
            break
        for s in page:
            if s.get("viewer_count", 0) >= min_viewers:
                streams.append(s)
        cursor = body.get("pagination", {}).get("cursor")
        if not cursor:
            break
    return streams[:limit]


def _twitch_users_by_id(client_id: str, token: str, user_ids: list[str]) -> list[dict]:
    """Fetch channel details for up to 100 user IDs in one request."""
    if not user_ids:
        return []
    resp = _http.get(
        "https://api.twitch.tv/helix/users",
        params=[("id", uid) for uid in user_ids[:100]],
        headers=_twitch_headers(client_id, token),
        timeout=10,
    )
    resp.raise_for_status()
    return resp.json().get("data", [])


def _twitch_channel_followers(client_id: str, token: str, broadcaster_id: str) -> int:
    """Get total follower count for a channel (Helix /channels/followers endpoint)."""
    try:
        resp = _http.get(
            "https://api.twitch.tv/helix/channels/followers",
            params={"broadcaster_id": broadcaster_id},
            headers=_twitch_headers(client_id, token),
            timeout=10,
        )
        resp.raise_for_status()
        return resp.json().get("total", 0)
    except Exception:
        return 0


def discover_from_twitch(
    db: Session,
    game_name: str = "Fortnite",
    limit: int = 50,
    min_viewers: int = 100,
    client_id: str = "",
    client_secret: str = "",
) -> dict:
    """
    Discover top live Twitch streamers for a given game and upsert them into DB.

    Returns a summary dict with counts.
    """
    if not client_id or not client_secret:
        import os
        client_id = os.getenv("TWITCH_CLIENT_ID", "")
        client_secret = os.getenv("TWITCH_CLIENT_SECRET", "")
    if not client_id or not client_secret:
        return {"error": "TWITCH_CLIENT_ID / TWITCH_CLIENT_SECRET not configured", "added": 0, "updated": 0}

    try:
        token = _get_twitch_token(client_id, client_secret)
    except Exception as exc:
        logger.error("Twitch token fetch failed: %s", exc)
        return {"error": str(exc), "added": 0, "updated": 0}

    game_id = _twitch_game_id(client_id, token, game_name)
    if not game_id:
        return {"error": f"Game '{game_name}' not found on Twitch", "added": 0, "updated": 0}

    streams = _twitch_top_streams(client_id, token, game_id, limit, min_viewers)
    if not streams:
        return {"added": 0, "updated": 0, "message": "No streams found"}

    user_ids = [s["user_id"] for s in streams]
    user_details = {u["id"]: u for u in _twitch_users_by_id(client_id, token, user_ids)}

    # Build viewer_count map: user_id → viewer_count
    viewer_map = {s["user_id"]: s.get("viewer_count", 0) for s in streams}

    added = 0
    updated = 0
    now = datetime.now(timezone.utc)

    for user_id, user in user_details.items():
        login = user.get("login", "").lower()
        if not login:
            continue

        followers = _twitch_channel_followers(client_id, token, user_id)

        existing = db.query(Streamer).filter(Streamer.twitch_username == login).first()
        if existing:
            existing.twitch_followers = followers
            existing.twitch_avg_viewers = viewer_map.get(user_id, existing.twitch_avg_viewers)
            existing.twitch_description = user.get("description") or existing.twitch_description
            existing.twitch_profile_image_url = user.get("profile_image_url") or existing.twitch_profile_image_url
            existing.twitch_views_total = user.get("view_count") or existing.twitch_views_total
            existing.twitch_is_partner = user.get("broadcaster_type") == "partner"
            existing.twitch_is_affiliate = user.get("broadcaster_type") in ("partner", "affiliate")
            if not existing.profile_image_url:
                existing.profile_image_url = user.get("profile_image_url")
            _recompute_total_followers(existing)
            existing.last_stats_updated_at = now
            updated += 1
        else:
            streamer = Streamer(
                name=user.get("display_name") or login,
                primary_platform="twitch",
                twitch_username=login,
                twitch_channel_id=user_id,
                twitch_url=f"https://www.twitch.tv/{login}",
                twitch_followers=followers,
                twitch_avg_viewers=viewer_map.get(user_id, 0),
                twitch_description=user.get("description"),
                twitch_profile_image_url=user.get("profile_image_url"),
                twitch_views_total=user.get("view_count"),
                twitch_is_partner=user.get("broadcaster_type") == "partner",
                twitch_is_affiliate=user.get("broadcaster_type") in ("partner", "affiliate"),
                profile_image_url=user.get("profile_image_url"),
                game_focus=[game_name],
                content_types=["live_streaming"],
                last_stats_updated_at=now,
            )
            _recompute_total_followers(streamer)
            db.add(streamer)
            added += 1

    db.commit()
    return {"added": added, "updated": updated, "game": game_name, "streams_found": len(streams)}


# ---------------------------------------------------------------------------
# Category / genre presets for batch discovery
# ---------------------------------------------------------------------------

STREAMER_CATEGORIES: dict[str, list[str]] = {
    "fps": ["Valorant", "Counter-Strike", "Call of Duty: Warzone", "Apex Legends", "Overwatch 2", "Rainbow Six Siege", "Escape From Tarkov"],
    "battle_royale": ["Fortnite", "PUBG: BATTLEGROUNDS", "Apex Legends", "Call of Duty: Warzone"],
    "moba": ["League of Legends", "Dota 2", "SMITE"],
    "mmorpg": ["World of Warcraft", "Final Fantasy XIV Online", "Lost Ark", "New World"],
    "survival": ["Rust", "ARK: Survival Evolved", "Minecraft", "7 Days to Die", "DayZ", "Valheim"],
    "sports": ["EA Sports FC 25", "NBA 2K25", "Madden NFL 25", "Rocket League"],
    "fighting": ["Street Fighter 6", "TEKKEN 8", "Mortal Kombat 1", "Guilty Gear -Strive-"],
    "racing": ["Forza Horizon 5", "Forza Motorsport", "Gran Turismo 7", "F1 24"],
    "horror": ["Phasmophobia", "Dead by Daylight", "Lethal Company", "Outlast Trials"],
    "strategy": ["Civilization VI", "Age of Empires IV", "Total War: Warhammer III", "Hearts of Iron IV"],
    "indie": ["Hades II", "Celeste", "Hollow Knight", "Stardew Valley", "Balatro"],
    "mobile": ["PUBG Mobile", "Mobile Legends: Bang Bang", "Free Fire", "Genshin Impact", "Honkai: Star Rail"],
    "vtuber": ["Just Chatting", "Minecraft", "Valorant", "Horror"],
    "variety": ["Just Chatting", "Minecraft", "GTA V", "Fortnite", "Variety"],
    "esports": ["League of Legends", "Valorant", "Counter-Strike", "Dota 2", "Overwatch 2"],
}


def discover_by_category(
    db: Session,
    category: str,
    limit_per_game: int = 20,
    min_viewers: int = 100,
    client_id: str = "",
    client_secret: str = "",
) -> dict:
    """
    Discover streamers across all games in a predefined category.

    Iterates through the games mapped to the category and runs Twitch discovery
    for each, deduplicating by twitch_username.

    Returns a summary with total added/updated counts per game.
    """
    if not client_id or not client_secret:
        import os
        client_id = os.getenv("TWITCH_CLIENT_ID", "")
        client_secret = os.getenv("TWITCH_CLIENT_SECRET", "")
    if not client_id or not client_secret:
        return {"error": "TWITCH_CLIENT_ID / TWITCH_CLIENT_SECRET not configured"}

    category_lower = category.lower()
    games = STREAMER_CATEGORIES.get(category_lower)
    if not games:
        return {
            "error": f"Unknown category '{category}'. Available: {', '.join(sorted(STREAMER_CATEGORIES))}",
        }

    results = []
    total_added = 0
    total_updated = 0

    for game_name in games:
        result = discover_from_twitch(
            db,
            game_name=game_name,
            limit=limit_per_game,
            min_viewers=min_viewers,
            client_id=client_id,
            client_secret=client_secret,
        )
        results.append({
            "game": game_name,
            "added": result.get("added", 0),
            "updated": result.get("updated", 0),
            "streams_found": result.get("streams_found", 0),
            "error": result.get("error"),
        })
        total_added += result.get("added", 0)
        total_updated += result.get("updated", 0)

    return {
        "category": category,
        "games_searched": len(games),
        "total_added": total_added,
        "total_updated": total_updated,
        "per_game": results,
    }


def discover_youtube_by_search(
    db: Session,
    query: str,
    max_results: int = 20,
) -> dict:
    """
    Discover YouTube gaming channels by searching for gaming content.

    Uses YouTube's public search page to find channels, then upserts them.
    No API key required — relies on scraping search results.
    """
    search_url = f"https://www.youtube.com/results?search_query={requests.utils.quote(query + ' gaming')}&sp=EgIQAg%3D%3D"
    try:
        resp = _http.get(search_url, timeout=15)
        resp.raise_for_status()
        html = resp.text
    except Exception as exc:
        logger.warning("YouTube search failed for '%s': %s", query, exc)
        return {"error": str(exc), "added": 0, "updated": 0}

    # Extract channel IDs from search results
    channel_ids = re.findall(r'"channelId":"(UC[a-zA-Z0-9_-]{22})"', html)
    # Deduplicate while preserving order
    seen = set()
    unique_ids = []
    for cid in channel_ids:
        if cid not in seen:
            seen.add(cid)
            unique_ids.append(cid)
    unique_ids = unique_ids[:max_results]

    if not unique_ids:
        return {"query": query, "added": 0, "updated": 0, "channels_found": 0}

    added = 0
    updated = 0
    for channel_id in unique_ids:
        result = discover_youtube_channel(db, channel_id)
        if result.get("action") == "created":
            added += 1
        elif result.get("action") == "updated":
            updated += 1

    return {
        "query": query,
        "channels_found": len(unique_ids),
        "added": added,
        "updated": updated,
    }


# ---------------------------------------------------------------------------
# YouTube helpers
# ---------------------------------------------------------------------------

_YT_SUB_RE = re.compile(r'"subscriberCountText":\{"simpleText":"([^"]+)"')
_YT_SUB_RE2 = re.compile(r'"subscriberCount":"(\d+)"')
_YT_TITLE_RE = re.compile(r'"channelMetadataRenderer":\{"title":"([^"]+)"')
_YT_DESC_RE = re.compile(r'"description":"([^"]*)"', re.DOTALL)
_YT_AVATAR_RE = re.compile(r'"avatar":\{"thumbnails":\[.*?"url":"(https://yt3[^"]+)"', re.DOTALL)


def _yt_channel_page(channel_id: str) -> Optional[str]:
    """Fetch raw YouTube channel page HTML."""
    try:
        url = f"https://www.youtube.com/channel/{channel_id}"
        resp = _http.get(url, timeout=15)
        resp.raise_for_status()
        return resp.text
    except Exception as exc:
        logger.warning("YouTube channel page fetch failed for %s: %s", channel_id, exc)
        return None


def _yt_parse_subscribers(html: str) -> Optional[int]:
    """Parse subscriber count from channel page HTML (best-effort)."""
    m = _YT_SUB_RE2.search(html)
    if m:
        try:
            return int(m.group(1))
        except ValueError:
            pass
    # Fallback: text like "1.23M subscribers"
    m2 = _YT_SUB_RE.search(html)
    if m2:
        raw = m2.group(1).strip()
        return _parse_human_number(raw)
    return None


def _yt_rss_video_count(channel_id: str) -> int:
    """Count videos via the public YouTube RSS feed (up to 15 latest)."""
    try:
        feed_url = f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"
        resp = _http.get(feed_url, timeout=10)
        resp.raise_for_status()
        return resp.text.count("<entry>")
    except Exception:
        return 0


def discover_youtube_channel(db: Session, channel_id: str) -> dict:
    """
    Fetch YouTube channel data by channel ID and upsert the streamer record.
    """
    html = _yt_channel_page(channel_id)
    if not html:
        return {"error": f"Could not fetch channel page for {channel_id}"}

    subscribers = _yt_parse_subscribers(html)

    title_m = _YT_TITLE_RE.search(html)
    channel_name = title_m.group(1) if title_m else channel_id

    # Try to extract description (first occurrence, keep short)
    desc = None
    desc_m = _YT_DESC_RE.search(html)
    if desc_m:
        raw_desc = desc_m.group(1).replace("\\n", "\n").replace('\\"', '"')
        desc = raw_desc[:500] or None

    # Avatar
    avatar_m = _YT_AVATAR_RE.search(html)
    avatar_url = avatar_m.group(1) if avatar_m else None

    video_count = _yt_rss_video_count(channel_id)
    channel_url = f"https://www.youtube.com/channel/{channel_id}"
    now = datetime.now(timezone.utc)

    existing = db.query(Streamer).filter(Streamer.youtube_channel_id == channel_id).first()
    if existing:
        if subscribers is not None:
            existing.youtube_subscribers = subscribers
        existing.youtube_channel_name = channel_name or existing.youtube_channel_name
        existing.youtube_description = desc or existing.youtube_description
        existing.youtube_profile_image_url = avatar_url or existing.youtube_profile_image_url
        if video_count:
            existing.youtube_video_count = video_count
        if not existing.profile_image_url and avatar_url:
            existing.profile_image_url = avatar_url
        _recompute_total_followers(existing)
        existing.last_stats_updated_at = now
        db.commit()
        return {"action": "updated", "streamer_id": existing.id, "channel_name": channel_name}
    else:
        streamer = Streamer(
            name=channel_name,
            primary_platform="youtube",
            youtube_channel_id=channel_id,
            youtube_channel_name=channel_name,
            youtube_url=channel_url,
            youtube_subscribers=subscribers,
            youtube_video_count=video_count or None,
            youtube_description=desc,
            youtube_profile_image_url=avatar_url,
            profile_image_url=avatar_url,
            content_types=["let's_play", "reviews"],
            last_stats_updated_at=now,
        )
        _recompute_total_followers(streamer)
        db.add(streamer)
        db.commit()
        db.refresh(streamer)
        return {"action": "created", "streamer_id": streamer.id, "channel_name": channel_name}


# ---------------------------------------------------------------------------
# X/Twitter helpers
# ---------------------------------------------------------------------------

_X_FOLLOWERS_RE = re.compile(r'"followers_count":(\d+)')
_X_FOLLOWING_RE = re.compile(r'"friends_count":(\d+)')
_X_TWEETS_RE = re.compile(r'"statuses_count":(\d+)')
_X_DESC_RE = re.compile(r'"description":"([^"]*)"')
_X_NAME_RE = re.compile(r'"name":"([^"]+)"')


def refresh_x_profile(db: Session, streamer: Streamer) -> list[str]:
    """
    Scrape the public X/Twitter profile page for a streamer and update DB fields.
    Returns list of field names that were updated.
    """
    if not streamer.x_username:
        return []
    url = f"https://x.com/{streamer.x_username}"
    try:
        resp = _http.get(url, timeout=15)
        resp.raise_for_status()
        html = resp.text
    except Exception as exc:
        logger.warning("X profile fetch failed for @%s: %s", streamer.x_username, exc)
        return []

    updated: list[str] = []

    m = _X_FOLLOWERS_RE.search(html)
    if m:
        streamer.x_followers = int(m.group(1))
        updated.append("x_followers")

    m = _X_FOLLOWING_RE.search(html)
    if m:
        streamer.x_following = int(m.group(1))
        updated.append("x_following")

    m = _X_TWEETS_RE.search(html)
    if m:
        streamer.x_tweet_count = int(m.group(1))
        updated.append("x_tweet_count")

    m = _X_DESC_RE.search(html)
    if m:
        desc = m.group(1).replace("\\n", " ").strip()
        if desc:
            streamer.x_description = desc[:500]
            updated.append("x_description")

    if updated:
        _recompute_total_followers(streamer)
        streamer.last_stats_updated_at = datetime.now(timezone.utc)
        db.commit()

    return updated


# ---------------------------------------------------------------------------
# Kick helpers
# ---------------------------------------------------------------------------

_KICK_FOLLOWERS_RE = re.compile(r'"followers_count"\s*:\s*(\d+)')
_KICK_VIEWERS_RE = re.compile(r'"viewer_count"\s*:\s*(\d+)')
_KICK_VERIFIED_RE = re.compile(r'"is_verified"\s*:\s*(true|false)', re.I)
_KICK_BIO_RE = re.compile(r'"bio"\s*:\s*"([^"]*)"')
_KICK_AVATAR_RE = re.compile(r'"profile_pic"\s*:\s*"(https?://[^"]+)"')
_KICK_SLUG_RE = re.compile(r'"slug"\s*:\s*"([^"]+)"')


def _kick_channel_data(username: str) -> Optional[dict]:
    """Fetch Kick channel data via their public API."""
    try:
        resp = _http.get(
            f"https://kick.com/api/v2/channels/{username}",
            timeout=15,
        )
        if resp.status_code == 404:
            return None
        resp.raise_for_status()
        return resp.json()
    except Exception as exc:
        logger.warning("Kick channel fetch failed for %s: %s", username, exc)
        return None


def _kick_category_streams(category_slug: str, limit: int = 30) -> list[dict]:
    """Fetch live streams for a Kick category/subcategory."""
    streams: list[dict] = []
    try:
        resp = _http.get(
            f"https://kick.com/api/v1/subcategories/{category_slug}/livestreams",
            params={"limit": min(limit, 50), "sort": "viewers"},
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()
        if isinstance(data, dict):
            streams = data.get("data", data.get("livestreams", []))
        elif isinstance(data, list):
            streams = data
    except Exception as exc:
        logger.warning("Kick category fetch failed for %s: %s", category_slug, exc)
    return streams[:limit]


def discover_from_kick(
    db: Session,
    category: str = "gaming",
    limit: int = 30,
) -> dict:
    """
    Discover live Kick streamers by category and upsert them.
    No API key required — uses Kick's public API.
    """
    streams = _kick_category_streams(category, limit)
    if not streams:
        return {"added": 0, "updated": 0, "category": category, "streams_found": 0}

    added = 0
    updated = 0
    now = datetime.now(timezone.utc)

    for stream in streams:
        channel = stream.get("channel", stream)
        username = channel.get("slug") or channel.get("username", "")
        if not username:
            continue
        username = username.lower()

        followers = channel.get("followers_count") or channel.get("followersCount", 0)
        viewers = stream.get("viewer_count") or stream.get("viewers", 0)
        verified = channel.get("is_verified", False)
        bio = channel.get("bio") or channel.get("user", {}).get("bio", "")
        avatar = channel.get("profile_pic") or channel.get("user", {}).get("profile_pic", "")
        display_name = channel.get("user", {}).get("username", username)

        existing = db.query(Streamer).filter(Streamer.kick_username == username).first()
        if existing:
            existing.kick_followers = followers or existing.kick_followers
            existing.kick_avg_viewers = viewers or existing.kick_avg_viewers
            existing.kick_is_verified = verified
            existing.kick_description = bio[:500] if bio else existing.kick_description
            existing.kick_profile_image_url = avatar or existing.kick_profile_image_url
            _recompute_total_followers(existing)
            existing.last_stats_updated_at = now
            updated += 1
        else:
            streamer = Streamer(
                name=display_name or username,
                primary_platform="kick",
                kick_username=username,
                kick_url=f"https://kick.com/{username}",
                kick_followers=followers,
                kick_avg_viewers=viewers,
                kick_is_verified=verified,
                kick_description=bio[:500] if bio else None,
                kick_profile_image_url=avatar or None,
                profile_image_url=avatar or None,
                content_types=["live_streaming"],
                last_stats_updated_at=now,
            )
            _recompute_total_followers(streamer)
            db.add(streamer)
            added += 1

    db.commit()
    return {"added": added, "updated": updated, "category": category, "streams_found": len(streams)}


def refresh_kick_profile(db: Session, streamer: Streamer) -> list[str]:
    """Refresh Kick stats for a streamer."""
    if not streamer.kick_username:
        return []
    data = _kick_channel_data(streamer.kick_username)
    if not data:
        return []

    updated: list[str] = []
    followers = data.get("followers_count")
    if followers is not None:
        streamer.kick_followers = followers
        updated.append("kick_followers")
    verified = data.get("is_verified")
    if verified is not None:
        streamer.kick_is_verified = verified
        updated.append("kick_is_verified")
    bio = data.get("bio")
    if bio:
        streamer.kick_description = bio[:500]
        updated.append("kick_description")
    avatar = data.get("profile_pic")
    if avatar:
        streamer.kick_profile_image_url = avatar
        updated.append("kick_profile_image_url")

    if updated:
        _recompute_total_followers(streamer)
        streamer.last_stats_updated_at = datetime.now(timezone.utc)
        db.commit()
    return updated


# ---------------------------------------------------------------------------
# Rumble helpers
# ---------------------------------------------------------------------------

_RUMBLE_FOLLOWERS_RE = re.compile(r'(\d[\d,]*)\s*(?:followers|Followers)', re.I)
_RUMBLE_CHANNEL_RE = re.compile(r'href="/c/([^"]+)"')


def _rumble_search_channels(query: str, limit: int = 20) -> list[dict]:
    """Search Rumble for channels matching a query."""
    channels: list[dict] = []
    try:
        resp = _http.get(
            "https://rumble.com/search/channel",
            params={"q": query},
            timeout=15,
        )
        resp.raise_for_status()
        html = resp.text

        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, "html.parser")

        for item in soup.select(".channel-item, .search-result, [class*='channel']"):
            link = item.find("a", href=True)
            if not link:
                continue
            href = link.get("href", "")
            if "/c/" not in href and "/user/" not in href:
                continue

            name = link.get_text(strip=True) or ""
            channel_id = href.split("/c/")[-1].split("/")[0] if "/c/" in href else href.split("/user/")[-1].split("/")[0]
            if not channel_id or not name:
                continue

            # Try to find follower count nearby
            followers = None
            text = item.get_text()
            m = _RUMBLE_FOLLOWERS_RE.search(text)
            if m:
                followers = int(m.group(1).replace(",", ""))

            # Try to find avatar
            img = item.find("img", src=True)
            avatar = img.get("src", "") if img else ""

            channels.append({
                "channel_id": channel_id,
                "name": name[:200],
                "url": f"https://rumble.com/c/{channel_id}",
                "followers": followers,
                "avatar": avatar if avatar.startswith("http") else None,
            })

            if len(channels) >= limit:
                break

    except Exception as exc:
        logger.warning("Rumble search failed for '%s': %s", query, exc)

    return channels


def _rumble_channel_page(channel_id: str) -> Optional[dict]:
    """Scrape a Rumble channel page for metadata."""
    try:
        resp = _http.get(f"https://rumble.com/c/{channel_id}", timeout=15)
        resp.raise_for_status()
        html = resp.text

        name = channel_id
        followers = None
        description = None
        avatar = None

        # Extract from page
        m = _RUMBLE_FOLLOWERS_RE.search(html)
        if m:
            followers = int(m.group(1).replace(",", ""))

        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, "html.parser")

        title_el = soup.find("h1") or soup.find("title")
        if title_el:
            name = title_el.get_text(strip=True).replace(" - Rumble", "").strip()

        desc_el = soup.find("meta", attrs={"name": "description"})
        if desc_el:
            description = desc_el.get("content", "")[:500]

        img_el = soup.select_one(".channel-header img, .channel-avatar img, img[class*='avatar']")
        if img_el and img_el.get("src", "").startswith("http"):
            avatar = img_el["src"]

        return {
            "channel_id": channel_id,
            "name": name,
            "url": f"https://rumble.com/c/{channel_id}",
            "followers": followers,
            "description": description,
            "avatar": avatar,
        }
    except Exception as exc:
        logger.warning("Rumble channel page fetch failed for %s: %s", channel_id, exc)
        return None


def discover_from_rumble(
    db: Session,
    query: str,
    limit: int = 20,
) -> dict:
    """
    Discover Rumble channels by search query and upsert them.
    No API key required — scrapes public search results.
    """
    channels = _rumble_search_channels(query, limit)
    if not channels:
        return {"added": 0, "updated": 0, "query": query, "channels_found": 0}

    added = 0
    updated = 0
    now = datetime.now(timezone.utc)

    for ch in channels:
        cid = ch["channel_id"]
        existing = db.query(Streamer).filter(Streamer.rumble_channel_id == cid).first()
        if existing:
            if ch.get("followers") is not None:
                existing.rumble_followers = ch["followers"]
            if ch.get("avatar"):
                existing.rumble_profile_image_url = ch["avatar"]
            _recompute_total_followers(existing)
            existing.last_stats_updated_at = now
            updated += 1
        else:
            streamer = Streamer(
                name=ch["name"],
                primary_platform="rumble",
                rumble_channel_id=cid,
                rumble_url=ch["url"],
                rumble_followers=ch.get("followers"),
                rumble_profile_image_url=ch.get("avatar"),
                profile_image_url=ch.get("avatar"),
                content_types=["live_streaming"],
                last_stats_updated_at=now,
            )
            _recompute_total_followers(streamer)
            db.add(streamer)
            added += 1

    db.commit()
    return {"added": added, "updated": updated, "query": query, "channels_found": len(channels)}


def refresh_rumble_profile(db: Session, streamer: Streamer) -> list[str]:
    """Refresh Rumble stats for a streamer."""
    if not streamer.rumble_channel_id:
        return []
    data = _rumble_channel_page(streamer.rumble_channel_id)
    if not data:
        return []

    updated: list[str] = []
    if data.get("followers") is not None:
        streamer.rumble_followers = data["followers"]
        updated.append("rumble_followers")
    if data.get("description"):
        streamer.rumble_description = data["description"]
        updated.append("rumble_description")
    if data.get("avatar"):
        streamer.rumble_profile_image_url = data["avatar"]
        updated.append("rumble_profile_image_url")

    if updated:
        _recompute_total_followers(streamer)
        streamer.last_stats_updated_at = datetime.now(timezone.utc)
        db.commit()
    return updated


# ---------------------------------------------------------------------------
# TikTok helpers
# ---------------------------------------------------------------------------

_TT_FOLLOWERS_RE = re.compile(r'"followerCount"\s*:\s*(\d+)')
_TT_HEART_RE = re.compile(r'"heartCount"\s*:\s*(\d+)')
_TT_DESC_RE = re.compile(r'"signature"\s*:\s*"([^"]*)"')
_TT_AVATAR_RE = re.compile(r'"avatarLarger"\s*:\s*"(https?://[^"]+)"')
_TT_NICKNAME_RE = re.compile(r'"nickName"\s*:\s*"([^"]*)"')


def discover_tiktok_user(db: Session, username: str) -> dict:
    """
    Fetch a TikTok user profile and upsert the streamer.
    No API key required — scrapes public profile page.
    """
    username = username.lstrip("@").lower()
    try:
        resp = _http.get(f"https://www.tiktok.com/@{username}", timeout=15)
        resp.raise_for_status()
        html = resp.text
    except Exception as exc:
        logger.warning("TikTok profile fetch failed for @%s: %s", username, exc)
        return {"error": f"Could not fetch TikTok profile for @{username}: {exc}"}

    followers = None
    m = _TT_FOLLOWERS_RE.search(html)
    if m:
        followers = int(m.group(1))

    nickname = username
    m = _TT_NICKNAME_RE.search(html)
    if m:
        nickname = m.group(1) or username

    description = None
    m = _TT_DESC_RE.search(html)
    if m:
        description = m.group(1).replace("\\n", "\n").strip()[:500] or None

    avatar = None
    m = _TT_AVATAR_RE.search(html)
    if m:
        avatar = m.group(1).replace("\\u002F", "/")

    now = datetime.now(timezone.utc)
    existing = db.query(Streamer).filter(Streamer.tiktok_username == username).first()

    if existing:
        if followers is not None:
            existing.tiktok_followers = followers
        existing.tiktok_url = f"https://www.tiktok.com/@{username}"
        if not existing.profile_image_url and avatar:
            existing.profile_image_url = avatar
        _recompute_total_followers(existing)
        existing.last_stats_updated_at = now
        db.commit()
        return {"action": "updated", "streamer_id": existing.id, "username": username}
    else:
        streamer = Streamer(
            name=nickname,
            primary_platform="tiktok",
            tiktok_username=username,
            tiktok_url=f"https://www.tiktok.com/@{username}",
            tiktok_followers=followers,
            profile_image_url=avatar,
            content_types=["shorts", "live_streaming"],
            last_stats_updated_at=now,
        )
        _recompute_total_followers(streamer)
        db.add(streamer)
        db.commit()
        db.refresh(streamer)
        return {"action": "created", "streamer_id": streamer.id, "username": username}


def refresh_tiktok_profile(db: Session, streamer: Streamer) -> list[str]:
    """Refresh TikTok stats for a streamer."""
    if not streamer.tiktok_username:
        return []
    try:
        resp = _http.get(f"https://www.tiktok.com/@{streamer.tiktok_username}", timeout=15)
        resp.raise_for_status()
        html = resp.text
    except Exception as exc:
        logger.warning("TikTok refresh failed for @%s: %s", streamer.tiktok_username, exc)
        return []

    updated: list[str] = []
    m = _TT_FOLLOWERS_RE.search(html)
    if m:
        streamer.tiktok_followers = int(m.group(1))
        updated.append("tiktok_followers")

    if updated:
        _recompute_total_followers(streamer)
        streamer.last_stats_updated_at = datetime.now(timezone.utc)
        db.commit()
    return updated


# ---------------------------------------------------------------------------
# YouTube category discovery
# ---------------------------------------------------------------------------


def discover_youtube_by_category(
    db: Session,
    category: str,
    limit_per_game: int = 10,
) -> dict:
    """
    Discover YouTube channels across all games in a category.
    Reuses STREAMER_CATEGORIES and discover_youtube_by_search().
    """
    category_lower = category.lower()
    games = STREAMER_CATEGORIES.get(category_lower)
    if not games:
        return {"error": f"Unknown category '{category}'. Available: {', '.join(sorted(STREAMER_CATEGORIES))}"}

    results = []
    total_added = 0
    total_updated = 0

    for game_name in games:
        result = discover_youtube_by_search(db, query=game_name, max_results=limit_per_game)
        results.append({
            "game": game_name,
            "added": result.get("added", 0),
            "updated": result.get("updated", 0),
            "channels_found": result.get("channels_found", 0),
        })
        total_added += result.get("added", 0)
        total_updated += result.get("updated", 0)

    return {
        "category": category,
        "games_searched": len(games),
        "total_added": total_added,
        "total_updated": total_updated,
        "per_game": results,
    }


# ---------------------------------------------------------------------------
# Unified cross-platform discovery
# ---------------------------------------------------------------------------


def discover_all(
    db: Session,
    query: str,
    limit_per_platform: int = 20,
    min_viewers: int = 50,
) -> dict:
    """
    Discover streamers across ALL supported platforms with a single query.
    Runs Twitch, YouTube, Kick, and Rumble discovery in sequence.
    Returns per-platform results.
    """
    import os
    results: dict = {"query": query, "platforms": {}}
    total_added = 0
    total_updated = 0

    # Twitch (if credentials available)
    client_id = os.getenv("TWITCH_CLIENT_ID", "")
    client_secret = os.getenv("TWITCH_CLIENT_SECRET", "")
    if client_id and client_secret:
        try:
            twitch = discover_from_twitch(
                db, game_name=query, limit=limit_per_platform,
                min_viewers=min_viewers, client_id=client_id, client_secret=client_secret,
            )
            results["platforms"]["twitch"] = twitch
            total_added += twitch.get("added", 0)
            total_updated += twitch.get("updated", 0)
        except Exception as exc:
            results["platforms"]["twitch"] = {"error": str(exc)}
    else:
        results["platforms"]["twitch"] = {"skipped": "TWITCH_CLIENT_ID/SECRET not configured"}

    # YouTube (keyless)
    try:
        yt = discover_youtube_by_search(db, query=query, max_results=limit_per_platform)
        results["platforms"]["youtube"] = yt
        total_added += yt.get("added", 0)
        total_updated += yt.get("updated", 0)
    except Exception as exc:
        results["platforms"]["youtube"] = {"error": str(exc)}

    # Kick (keyless)
    try:
        kick = discover_from_kick(db, category=query, limit=limit_per_platform)
        results["platforms"]["kick"] = kick
        total_added += kick.get("added", 0)
        total_updated += kick.get("updated", 0)
    except Exception as exc:
        results["platforms"]["kick"] = {"error": str(exc)}

    # Rumble (keyless)
    try:
        rumble = discover_from_rumble(db, query=query, limit=limit_per_platform)
        results["platforms"]["rumble"] = rumble
        total_added += rumble.get("added", 0)
        total_updated += rumble.get("updated", 0)
    except Exception as exc:
        results["platforms"]["rumble"] = {"error": str(exc)}

    results["total_added"] = total_added
    results["total_updated"] = total_updated
    return results


# ---------------------------------------------------------------------------
# Refresh all platforms for a single streamer
# ---------------------------------------------------------------------------

def refresh_streamer(
    db: Session,
    streamer: Streamer,
    client_id: str = "",
    client_secret: str = "",
) -> list[str]:
    """
    Refresh live stats for all platforms linked to a streamer.
    Returns list of updated field names.
    """
    import os
    if not client_id:
        client_id = os.getenv("TWITCH_CLIENT_ID", "")
    if not client_secret:
        client_secret = os.getenv("TWITCH_CLIENT_SECRET", "")

    updated: list[str] = []

    # Twitch
    if streamer.twitch_username and client_id and client_secret:
        try:
            token = _get_twitch_token(client_id, client_secret)
            users = _twitch_users_by_id(client_id, token, [streamer.twitch_channel_id or ""])
            if not users and streamer.twitch_username:
                # fallback: lookup by login name
                resp = _http.get(
                    "https://api.twitch.tv/helix/users",
                    params={"login": streamer.twitch_username},
                    headers=_twitch_headers(client_id, token),
                    timeout=10,
                )
                resp.raise_for_status()
                users = resp.json().get("data", [])
            if users:
                u = users[0]
                uid = u["id"]
                followers = _twitch_channel_followers(client_id, token, uid)
                streamer.twitch_channel_id = uid
                streamer.twitch_followers = followers
                streamer.twitch_description = u.get("description") or streamer.twitch_description
                streamer.twitch_profile_image_url = u.get("profile_image_url") or streamer.twitch_profile_image_url
                streamer.twitch_views_total = u.get("view_count") or streamer.twitch_views_total
                streamer.twitch_is_partner = u.get("broadcaster_type") == "partner"
                streamer.twitch_is_affiliate = u.get("broadcaster_type") in ("partner", "affiliate")
                updated += ["twitch_followers", "twitch_channel_id", "twitch_description",
                            "twitch_is_partner", "twitch_is_affiliate"]
        except Exception as exc:
            logger.warning("Twitch refresh failed for %s: %s", streamer.twitch_username, exc)

    # YouTube
    if streamer.youtube_channel_id:
        try:
            html = _yt_channel_page(streamer.youtube_channel_id)
            if html:
                subs = _yt_parse_subscribers(html)
                if subs is not None:
                    streamer.youtube_subscribers = subs
                    updated.append("youtube_subscribers")
                vc = _yt_rss_video_count(streamer.youtube_channel_id)
                if vc:
                    streamer.youtube_video_count = vc
                    updated.append("youtube_video_count")
        except Exception as exc:
            logger.warning("YouTube refresh failed for %s: %s", streamer.youtube_channel_id, exc)

    # X
    x_fields = refresh_x_profile(db, streamer)
    updated += x_fields

    # Kick
    if streamer.kick_username:
        try:
            kick_fields = refresh_kick_profile(db, streamer)
            updated += kick_fields
        except Exception as exc:
            logger.warning("Kick refresh failed for %s: %s", streamer.kick_username, exc)

    # Rumble
    if streamer.rumble_channel_id:
        try:
            rumble_fields = refresh_rumble_profile(db, streamer)
            updated += rumble_fields
        except Exception as exc:
            logger.warning("Rumble refresh failed for %s: %s", streamer.rumble_channel_id, exc)

    # TikTok
    if streamer.tiktok_username:
        try:
            tiktok_fields = refresh_tiktok_profile(db, streamer)
            updated += tiktok_fields
        except Exception as exc:
            logger.warning("TikTok refresh failed for %s: %s", streamer.tiktok_username, exc)

    if updated:
        _recompute_total_followers(streamer)
        streamer.last_stats_updated_at = datetime.now(timezone.utc)
        db.commit()

    return list(dict.fromkeys(updated))  # deduplicate, preserve order


# ---------------------------------------------------------------------------
# Utility
# ---------------------------------------------------------------------------

def _recompute_total_followers(streamer: Streamer) -> None:
    """Sum followers across all tracked platforms and update total_followers."""
    total = 0
    for val in [
        streamer.twitch_followers,
        streamer.youtube_subscribers,
        streamer.x_followers,
        streamer.instagram_followers,
        streamer.tiktok_followers,
        streamer.kick_followers,
        streamer.rumble_followers,
    ]:
        if val:
            total += val
    streamer.total_followers = total or None


def _parse_human_number(raw: str) -> Optional[int]:
    """Parse human-readable numbers like '1.23M', '450K', '2B'."""
    raw = raw.strip().upper().replace(",", "")
    multipliers = {"K": 1_000, "M": 1_000_000, "B": 1_000_000_000}
    for suffix, mult in multipliers.items():
        if raw.endswith(suffix):
            try:
                return int(float(raw[:-1]) * mult)
            except ValueError:
                return None
    try:
        return int(float(raw))
    except ValueError:
        return None
