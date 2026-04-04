import os
import secrets

from pydantic_settings import BaseSettings


SUPPORTED_LANGUAGES = {
    "en": "English",
    "zh-CN": "Mandarin Chinese",
    "zh-HK": "Cantonese Chinese",
    "hi": "Hindi",
    "es": "Spanish",
    "fr": "French",
    "ar": "Arabic",
    "bn": "Bengali",
    "pt": "Portuguese",
    "ru": "Russian",
    "ja": "Japanese",
    "ko": "Korean",
    "de": "German",
    "it": "Italian",
    "tr": "Turkish",
    "th": "Thai",
    "id": "Indonesian",
    "pl": "Polish",
    "nl": "Dutch",
    "sv": "Swedish",
    "no": "Norwegian",
    "da": "Danish",
    "fi": "Finnish",
    "cs": "Czech",
    "ro": "Romanian",
    "hu": "Hungarian",
    "vi": "Vietnamese",
    "ms": "Malay",
    "tl": "Filipino",
    "uk": "Ukrainian",
    "el": "Greek",
    "he": "Hebrew",
    "fa": "Persian",
    "sw": "Swahili",
}


class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite:///gaming_pr.db"
    SCRAPE_INTERVAL_MINUTES: int = 30
    TRANSLATION_PROVIDER: str = "google"
    SCRAPE_CONCURRENCY: int = 10
    SCRAPE_REQUEST_TIMEOUT: int = 20
    SCRAPE_RATE_LIMIT_DELAY: float = 0.5
    FULL_CONTENT_EXTRACTION: bool = True
    RESPECT_ROBOTS_TXT: bool = True
    ENABLE_SITEMAP_DISCOVERY: bool = True
    DEDUP_SIMILARITY_THRESHOLD: float = 0.85
    PORT: int = 8000

    # v4: Advanced features
    ENABLE_BROWSER_FALLBACK: bool = True
    ENABLE_STEALTH_HEADERS: bool = True
    ENABLE_CIRCUIT_BREAKER: bool = True
    CIRCUIT_BREAKER_THRESHOLD: int = 5
    CIRCUIT_BREAKER_RECOVERY_SECONDS: float = 300.0
    ENABLE_RETRY_QUEUE: bool = True
    RETRY_MAX_ATTEMPTS: int = 3
    ENABLE_ADAPTIVE_SCHEDULING: bool = True
    ENABLE_WEBHOOKS: bool = True
    ENABLE_CHANGE_TRACKING: bool = True

    # Auth / JWT — auto-generates secure key if not set via env
    JWT_SECRET_KEY: str = os.environ.get("JWT_SECRET_KEY", secrets.token_urlsafe(48))
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_MINUTES: int = 1440  # 24 hours

    # Claude AI (for personalized outreach)
    ANTHROPIC_API_KEY: str = ""

    # Email service (external)
    EMAIL_SERVICE_URL: str = "http://localhost:3000"
    EMAIL_SERVICE_API_KEY: str = ""

    # Campaign automation
    CAMPAIGN_SEND_INTERVAL_SECONDS: int = 60
    CAMPAIGN_FOLLOW_UP_CHECK_MINUTES: int = 30
    CAMPAIGN_EVENT_SYNC_MINUTES: int = 10

    model_config = {"env_file": ".env"}


settings = Settings()
