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
