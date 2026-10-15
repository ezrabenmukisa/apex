from functools import lru_cache
from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):

    database_url: SecretStr = Field(..., alias="DATABASE_URL")

    firebase_credentials: str = Field(..., alias="FIREBASE_CREDENTIALS")

    model_config = SettingsConfigDict(
        env_file = ".env",
        env_file_encoding = "utf-8",
        extra = "ignore",
    )

@lru_cache
def get_settings() -> Settings:
    return Settings()