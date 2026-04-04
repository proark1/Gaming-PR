from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class StreamerBase(BaseModel):
    name: str
    primary_platform: str = "twitch"
    # Twitch
    twitch_username: Optional[str] = None
    twitch_channel_id: Optional[str] = None
    twitch_url: Optional[str] = None
    twitch_followers: Optional[int] = None
    twitch_avg_viewers: Optional[int] = None
    twitch_peak_viewers: Optional[int] = None
    twitch_is_partner: Optional[bool] = None
    twitch_is_affiliate: Optional[bool] = None
    twitch_description: Optional[str] = None
    twitch_profile_image_url: Optional[str] = None
    twitch_views_total: Optional[int] = None
    # YouTube
    youtube_channel_id: Optional[str] = None
    youtube_channel_name: Optional[str] = None
    youtube_url: Optional[str] = None
    youtube_subscribers: Optional[int] = None
    youtube_total_views: Optional[int] = None
    youtube_video_count: Optional[int] = None
    youtube_avg_views_per_video: Optional[int] = None
    youtube_description: Optional[str] = None
    youtube_profile_image_url: Optional[str] = None
    # X (Twitter)
    x_username: Optional[str] = None
    x_user_id: Optional[str] = None
    x_url: Optional[str] = None
    x_followers: Optional[int] = None
    x_following: Optional[int] = None
    x_tweet_count: Optional[int] = None
    x_description: Optional[str] = None
    x_profile_image_url: Optional[str] = None
    # Other platforms
    instagram_username: Optional[str] = None
    instagram_url: Optional[str] = None
    instagram_followers: Optional[int] = None
    tiktok_username: Optional[str] = None
    tiktok_url: Optional[str] = None
    tiktok_followers: Optional[int] = None
    # Content profile
    game_focus: Optional[list[str]] = None
    content_types: Optional[list[str]] = None
    language: Optional[str] = None
    country: Optional[str] = None
    region: Optional[str] = None
    # Reach
    total_followers: Optional[int] = None
    estimated_monthly_reach: Optional[int] = None
    # PR / contact
    contact_email: Optional[str] = None
    agent_name: Optional[str] = None
    agent_email: Optional[str] = None
    management_company: Optional[str] = None
    media_kit_url: Optional[str] = None
    # Metadata
    profile_image_url: Optional[str] = None
    description: Optional[str] = None
    is_active: bool = True
    is_verified: bool = False
    notes: Optional[str] = None


class StreamerCreate(StreamerBase):
    pass


class StreamerUpdate(BaseModel):
    name: Optional[str] = None
    primary_platform: Optional[str] = None
    twitch_username: Optional[str] = None
    twitch_channel_id: Optional[str] = None
    twitch_url: Optional[str] = None
    twitch_followers: Optional[int] = None
    twitch_avg_viewers: Optional[int] = None
    twitch_peak_viewers: Optional[int] = None
    twitch_is_partner: Optional[bool] = None
    twitch_is_affiliate: Optional[bool] = None
    twitch_description: Optional[str] = None
    twitch_profile_image_url: Optional[str] = None
    twitch_views_total: Optional[int] = None
    youtube_channel_id: Optional[str] = None
    youtube_channel_name: Optional[str] = None
    youtube_url: Optional[str] = None
    youtube_subscribers: Optional[int] = None
    youtube_total_views: Optional[int] = None
    youtube_video_count: Optional[int] = None
    youtube_avg_views_per_video: Optional[int] = None
    youtube_description: Optional[str] = None
    youtube_profile_image_url: Optional[str] = None
    x_username: Optional[str] = None
    x_user_id: Optional[str] = None
    x_url: Optional[str] = None
    x_followers: Optional[int] = None
    x_following: Optional[int] = None
    x_tweet_count: Optional[int] = None
    x_description: Optional[str] = None
    x_profile_image_url: Optional[str] = None
    instagram_username: Optional[str] = None
    instagram_url: Optional[str] = None
    instagram_followers: Optional[int] = None
    tiktok_username: Optional[str] = None
    tiktok_url: Optional[str] = None
    tiktok_followers: Optional[int] = None
    game_focus: Optional[list[str]] = None
    content_types: Optional[list[str]] = None
    language: Optional[str] = None
    country: Optional[str] = None
    region: Optional[str] = None
    total_followers: Optional[int] = None
    estimated_monthly_reach: Optional[int] = None
    contact_email: Optional[str] = None
    agent_name: Optional[str] = None
    agent_email: Optional[str] = None
    management_company: Optional[str] = None
    media_kit_url: Optional[str] = None
    profile_image_url: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None
    is_verified: Optional[bool] = None
    notes: Optional[str] = None


class StreamerResponse(StreamerBase):
    model_config = {"from_attributes": True}

    id: int
    last_stats_updated_at: Optional[datetime] = None
    twitch_last_live_at: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None


class StreamerDiscoverTwitchRequest(BaseModel):
    game_name: str = "Fortnite"
    limit: int = 50
    min_viewers: int = 100


class StreamerDiscoverYouTubeRequest(BaseModel):
    channel_id: str


class StreamerRefreshResponse(BaseModel):
    streamer_id: int
    updated_fields: list[str]
    message: str
