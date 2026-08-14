import os
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite:///scraper.db"
    LOG_LEVEL: str = "INFO"
    SCRAPER_TIMEOUT: int = 30
    DEFAULT_CONCURRENCY: int = 5
    MAX_ENRICH_CONCURRENCY: int = 5
    USER_AGENT: str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    
    # We allow loading from .env if present
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

settings = Settings()
