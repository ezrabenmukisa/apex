from functools import lru_cache
from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):

    database_url: SecretStr = Field(..., alias="DATABASE_URL")

    firebase_credentials: str = Field(..., alias="FIREBASE_CREDENTIALS")

    mail_server: str = Field(..., alias="MAIL_SERVER")
    mail_port: int = Field(..., alias="MAIL_PORT")
    mail_use_ssl: bool = Field(..., alias="MAIL_USE_SSL")
    mail_username: str = Field(..., alias="MAIL_USERNAME")
    mail_password: SecretStr = Field(..., alias="MAIL_PASSWORD")
    mail_default_sender: str = Field(..., alias="MAIL_DEFAULT_SENDER")
    
    invite_base_url: str = Field(..., alias="INVITE_BASE_URL")

    android_sha256_cert_fingerprint: str = Field(..., alias="ANDROID_SHA256_CERT_FINGERPRINT")
    
    model_config = SettingsConfigDict(
        env_file = ".env",
        env_file_encoding = "utf-8",
        extra = "ignore",
    )

@lru_cache
def get_settings() -> Settings:
    return Settings()