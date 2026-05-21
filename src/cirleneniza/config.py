"""Pydantic Settings for Canal Cirlene Niza."""

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Telegram
    telegram_bot_token: str = Field(..., alias="TELEGRAM_BOT_TOKEN")

    # AI / LLM
    gemini_api_key: str = Field("", alias="GEMINI_API_KEY")

    # Fal.ai
    fal_api_key: str = Field(..., alias="FAL_API_KEY")

    # MinIO
    minio_endpoint: str = Field("http://localhost:9000", alias="MINIO_ENDPOINT")
    minio_public_endpoint: str = Field("", alias="MINIO_PUBLIC_ENDPOINT")
    minio_access_key: str = Field(..., alias="MINIO_ACCESS_KEY")
    minio_secret_key: str = Field(..., alias="MINIO_SECRET_KEY")
    minio_bucket_work: str = Field("canal-cirlene-niza-work", alias="MINIO_BUCKET_WORK")
    minio_bucket_final: str = Field("canal-cirlene-niza-final", alias="MINIO_BUCKET_FINAL")

    # Baserow
    baserow_url: str = Field("http://localhost:8000", alias="BASEROW_URL")
    baserow_token: str = Field(..., alias="BASEROW_TOKEN")
    baserow_database_id: str = Field(..., alias="BASEROW_DATABASE_ID")
    baserow_table_productions: int = Field(726, alias="BASEROW_TABLE_PRODUCTIONS")
    baserow_table_scenes: int = Field(727, alias="BASEROW_TABLE_SCENES")
    baserow_table_posts: int = Field(728, alias="BASEROW_TABLE_POSTS")
    baserow_table_metrics: int = Field(729, alias="BASEROW_TABLE_METRICS")
    baserow_table_costs: int = Field(730, alias="BASEROW_TABLE_COSTS")

    # ElevenLabs (voz clonada Cirlene Niza)
    elevenlabs_api_key: str = Field(..., alias="ELEVENLABS_API_KEY")
    elevenlabs_voice_id: str = Field("Hjkdk1gQgapvWcOLaL1K", alias="ELEVENLABS_VOICE_ID")

    # Kokoro TTS (fallback local)
    kokoro_endpoint: str = Field("http://localhost:5000", alias="KOKORO_ENDPOINT")
    kokoro_voice: str = Field("af_sarah", alias="KOKORO_VOICE")

    # NCA Toolkit
    nca_toolkit_url: str = Field("http://localhost:8080", alias="NCA_TOOLKIT_URL")

    # HeyGen
    heygen_api_key: str = Field(..., alias="HEYGEN_API_KEY")
    heygen_talking_photo_id: str = Field(
        "a8ea07fc852d43728dd94c9607d462aa",
        alias="HEYGEN_TALKING_PHOTO_ID",
    )

    # Logging
    log_level: str = Field("INFO", alias="LOG_LEVEL")


@lru_cache
def get_settings() -> Settings:
    """Return cached singleton Settings instance."""
    return Settings()