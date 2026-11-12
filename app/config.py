from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Financial Ledger API"
    app_version: str = "0.1.0"
    database_url: str = "sqlite:///./financial_ledger.db"
    admin_api_key: str = "change-me"
    sqlite_busy_timeout_ms: int = 5000

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


@lru_cache()
def get_settings() -> Settings:
    return Settings()
