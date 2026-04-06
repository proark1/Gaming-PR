from pydantic_settings import BaseSettings


SUPPORTED_LANGUAGES = {
    "en": "English",
    "zh-CN": "Mandarin Chinese",
    "hi": "Hindi",
    "es": "Spanish",
    "fr": "French",
    "ar": "Arabic",
    "bn": "Bengali",
    "pt": "Portuguese",
    "ru": "Russian",
    "ja": "Japanese",
}


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/gaming_pr"
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

    # Email service (external)
    EMAIL_SERVICE_URL: str = "http://localhost:3000"
    EMAIL_SERVICE_API_KEY: str = ""

    # Auth
    ADMIN_EMAIL: str = "admin@gaming-pr.com"
    ADMIN_PASSWORD: str = "admin123"
    SECRET_KEY: str = "your-secret-key-change-in-production"

    model_config = {"env_file": ".env"}


settings = Settings()
