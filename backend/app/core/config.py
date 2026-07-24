from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Annotated

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env", "../.env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_name: str = "BLUEDOT AI 能力中台"
    app_env: str = "development"
    app_debug: bool = False
    app_host: str = "0.0.0.0"
    app_port: int = 8080
    app_cors_origins: Annotated[list[str], NoDecode] = Field(
        default_factory=lambda: ["http://localhost:5173"]
    )

    database_url: str = "sqlite+aiosqlite:///./data/ai_platform.db"
    auto_create_tables: bool = True

    ai_mock_mode: bool = True
    gptsapi_base_url: str = "https://api.gptsapi.net/v1"
    gptsapi_api_key: str = ""
    gptsapi_model: str = "gpt-5.6-luna"
    ai_connect_timeout_seconds: float = 10
    ai_read_timeout_seconds: float = 120
    ai_stream_idle_timeout_seconds: float = 30
    ai_max_retries: int = Field(default=2, ge=0, le=5)
    ai_retry_delays_seconds: Annotated[list[float], NoDecode] = Field(
        default_factory=lambda: [1, 2]
    )

    internal_api_token: str = ""
    audit_retention_days: int = Field(default=90, ge=1, le=3650)

    @field_validator("app_cors_origins", mode="before")
    @classmethod
    def parse_origins(cls, value: object) -> object:
        if isinstance(value, str):
            return [item.strip() for item in value.split(",") if item.strip()]
        return value

    @field_validator("ai_retry_delays_seconds", mode="before")
    @classmethod
    def parse_retry_delays(cls, value: object) -> object:
        if isinstance(value, str):
            return [float(item.strip()) for item in value.split(",") if item.strip()]
        return value

    @property
    def api_key_configured(self) -> bool:
        return bool(self.gptsapi_api_key.strip())

    @property
    def is_sqlite(self) -> bool:
        return self.database_url.startswith("sqlite")

    def ensure_runtime_directories(self) -> None:
        if self.is_sqlite:
            Path("data").mkdir(parents=True, exist_ok=True)


@lru_cache
def get_settings() -> Settings:
    return Settings()
