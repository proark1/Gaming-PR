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
    DATABASE_URL: str = "sqlite:///./gaming_pr.db"
    SCRAPE_INTERVAL_MINUTES: int = 60
    TRANSLATION_PROVIDER: str = "google"

    model_config = {"env_file": ".env"}


settings = Settings()
