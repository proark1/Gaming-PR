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
    SCRAPE_CONCURRENCY: int = 5
    SCRAPE_REQUEST_TIMEOUT: int = 20
    SCRAPE_RATE_LIMIT_DELAY: float = 1.0
    FULL_CONTENT_EXTRACTION: bool = True

    model_config = {"env_file": ".env"}


settings = Settings()
