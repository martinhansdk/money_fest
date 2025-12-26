"""
Configuration management for Money Fest
Uses pydantic-settings to load from environment variables and .env file
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    # Security
    SECRET_KEY: str = "dev-secret-key-change-in-production"

    # Database
    DATABASE_PATH: str = "/app/data/categorizer.db"

    # Session
    SESSION_MAX_AGE: int = 60 * 60 * 24 * 30  # 30 days in seconds
    SESSION_COOKIE_NAME: str = "session_id"

    # Server
    CORS_ORIGINS: list[str] = ["http://localhost:1111", "http://127.0.0.1:1111"]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True
    )


# Global settings instance
settings = Settings()
