from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )

    ENVIRONMENT: Literal["development", "production"]
    RELOAD_ENABLED: bool
    GROQ_API_KEY: str


app_settings = Settings()
