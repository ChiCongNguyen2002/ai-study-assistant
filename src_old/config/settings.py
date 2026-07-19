"""Application settings and configuration."""
from pydantic_settings import BaseSettings
from typing import Optional
import os


class Settings(BaseSettings):
    """Application configuration from environment variables."""

    # Anthropic API
    ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")
    ANTHROPIC_API_URL: str = "https://api.anthropic.com/v1/messages"
    ANTHROPIC_API_VERSION: str = "2023-06-01"
    ANTHROPIC_MODEL: str = "claude-opus-4-8"
    ANTHROPIC_MAX_TOKENS: int = 1024
    ANTHROPIC_TIMEOUT: int = 20  # Increased from 8s for longer queries

    # Firebase
    FIREBASE_PROJECT_ID: Optional[str] = os.getenv("FIREBASE_PROJECT_ID")
    FIREBASE_CREDENTIALS_JSON: Optional[str] = os.getenv("FIREBASE_CREDENTIALS_JSON")
    FIREBASE_STORAGE_BUCKET: Optional[str] = os.getenv("FIREBASE_STORAGE_BUCKET")

    # App
    APP_NAME: str = "AI Study Assistant"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"

    class Config:
        env_file = ".env.local"
        case_sensitive = True
        extra = "ignore"  # Ignore extra env vars


# Singleton instance
settings = Settings()
