from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT_ENV_FILE = Path(__file__).resolve().parents[3] / ".env"


class Settings(BaseSettings):
    app_name: str = "Animal Behaviour Interpreter API"
    api_v1_prefix: str = "/api/v1"
    mongodb_url: str = "mongodb://localhost:27017"
    mongodb_database: str = "animal_behaviour"
    cors_origins: str = "http://localhost:5173"
    frontend_url: str = "http://localhost:5173"
    jwt_secret: str = "development-only-change-me"
    access_token_minutes: int = 60 * 24 * 7
    confirmation_token_hours: int = 24
    email_delivery_mode: str = "console"
    gmail_address: str | None = None
    gmail_app_password: str | None = None
    email_from_name: str = "Whiskerwise"
    media_root: str = "data/media"
    max_video_bytes: int = 50 * 1024 * 1024
    max_video_seconds: int = 30
    gcs_dataset_bucket: str | None = None
    gcs_dataset_prefix: str = "raw/animal-kingdom"

    model_config = SettingsConfigDict(
        env_file=(ROOT_ENV_FILE, ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def allowed_origins(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
