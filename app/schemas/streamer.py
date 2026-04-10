from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class StreamerBase(BaseModel):
    name: str
    url: str
    platform: str = "twitch"
    real_name: Optional[str] = None
    twitch_username: Optional[str] = None
    youtube_channel: Optional[str] = None
    kick_username: Optional[str] = None
    tiktok_username: Optional[str] = None
    bio: Optional[str] = None
    language: str = "en"
    region: Optional[str] = None
    country: Optional[str] = None
    primary_game: Optional[str] = None
    games_played: Optional[list] = []
    content_categories: Optional[list] = []
    content_style: Optional[str] = None
    is_variety_streamer: bool = False
    tier: Optional[str] = "mid"
    category: Optional[str] = "gaming"
    tags: Optional[list] = []
    priority: int = 5
    contact_email: Optional[str] = None
    business_email: Optional[str] = None
    social_twitter: Optional[str] = None
    social_instagram: Optional[str] = None
    social_discord: Optional[str] = None


class StreamerCreate(StreamerBase):
    pass


class StreamerUpdate(BaseModel):
    name: Optional[str] = None
    url: Optional[str] = None
    platform: Optional[str] = None
    real_name: Optional[str] = None
    bio: Optional[str] = None
    twitch_username: Optional[str] = None
    youtube_channel: Optional[str] = None
    kick_username: Optional[str] = None
    primary_game: Optional[str] = None
    games_played: Optional[list] = None
    content_categories: Optional[list] = None
    content_style: Optional[str] = None
    is_variety_streamer: Optional[bool] = None
    tier: Optional[str] = None
    priority: Optional[int] = None
    contact_email: Optional[str] = None
    business_email: Optional[str] = None
    manager_name: Optional[str] = None
    manager_email: Optional[str] = None
    agency: Optional[str] = None
    social_twitter: Optional[str] = None
    social_instagram: Optional[str] = None
    social_discord: Optional[str] = None
    tags: Optional[list] = None
    is_active: Optional[bool] = None
    internal_notes: Optional[str] = None


class StreamerResponse(StreamerBase):
    model_config = {"from_attributes": True}

    id: int
    is_active: bool
    profile_image_url: Optional[str] = None
    banner_image_url: Optional[str] = None
    follower_count: Optional[int] = None
    subscriber_count: Optional[int] = None
    avg_viewers: Optional[int] = None
    peak_viewers: Optional[int] = None
    total_views: Optional[int] = None
    avg_stream_duration_hours: Optional[float] = None
    stream_schedule: Optional[str] = None
    is_partnered: bool = False
    is_affiliated: bool = False
    audience_age_range: Optional[str] = None
    audience_gender_split: Optional[dict] = None
    audience_top_countries: Optional[list] = None
    social_tiktok: Optional[str] = None
    social_youtube: Optional[str] = None
    social_facebook: Optional[str] = None
    twitter_followers: Optional[int] = None
    instagram_followers: Optional[int] = None
    discord_members: Optional[int] = None
    manager_name: Optional[str] = None
    manager_email: Optional[str] = None
    agency: Optional[str] = None
    agency_url: Optional[str] = None
    has_sponsorships: bool = False
    past_sponsors: Optional[list] = []
    estimated_sponsorship_rate: Optional[str] = None
    accepts_game_codes: Optional[bool] = None
    accepts_sponsored_streams: Optional[bool] = None
    has_merch_store: bool = False
    merch_url: Optional[str] = None
    is_esports_player: bool = False
    esports_team: Optional[str] = None
    esports_role: Optional[str] = None
    tournament_history: Optional[list] = []
    notable_achievements: Optional[list] = []
    recent_milestones: Optional[list] = []
    content_highlights: Optional[list] = []
    internal_notes: Optional[str] = None
    last_scraped_at: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None


class StreamerStatsResponse(BaseModel):
    total_streamers: int
    active_streamers: int
    streamers_by_platform: dict[str, int]
    streamers_by_tier: dict[str, int]
    streamers_by_language: dict[str, int]
    total_combined_followers: int
