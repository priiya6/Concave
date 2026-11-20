from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path

class Settings(BaseSettings):
    secret_key: str = "local-development-secret-change-me"
    database_url: str = "sqlite:///./data/app.db"
    app_timezone: str = "Asia/Kolkata"
    enable_background_jobs: bool = True
    escalation_interval_seconds: int = 60
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

settings = Settings()
