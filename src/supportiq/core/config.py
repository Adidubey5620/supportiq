from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "SupportIQ"
    debug: bool = True
    api_v1_prefix: str = "/api/v1"
    database_url: str
    database_url: str
    openrouter_api_key: str

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @field_validator("debug", mode="before")
    @classmethod
    def coerce_debug(cls, v):
        if isinstance(v, str) and v.lower() not in ("true", "false", "1", "0", "yes", "no"):
            return True
        return v


settings = Settings()
