from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Annotated

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env", "../.env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_name: str = "BLUEDOT AI Agent 中台"
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
    gptsapi_speech_model: str = "tts-1"
    gptsapi_allowed_hosts: Annotated[list[str], NoDecode] = Field(
        default_factory=lambda: ["api.gptsapi.net"]
    )
    ai_connect_timeout_seconds: float = 10
    ai_read_timeout_seconds: float = 120
    ai_stream_idle_timeout_seconds: float = 30
    ai_max_retries: int = Field(default=2, ge=0, le=5)
    ai_retry_delays_seconds: Annotated[list[float], NoDecode] = Field(
        default_factory=lambda: [1, 2]
    )

    internal_api_token: str = ""
    admin_username: str = ""
    admin_password: SecretStr = SecretStr("")
    admin_session_ttl_minutes: int = Field(default=480, ge=15, le=1440)
    audit_retention_days: int = Field(default=90, ge=1, le=3650)
    recruitment_max_upload_mb: int = Field(default=10, ge=1, le=50)
    recruitment_max_pdf_pages: int = Field(default=20, ge=1, le=100)
    recruitment_max_extracted_chars: int = Field(default=100_000, ge=1_000, le=500_000)
    recruitment_max_docx_uncompressed_mb: int = Field(default=50, ge=1, le=200)
    speech_max_input_chars: int = Field(default=4096, ge=1, le=4096)
    speech_max_stream_chars: int = Field(default=50_000, ge=4096, le=200_000)
    speech_stream_first_segment_chars: int = Field(default=120, ge=1, le=4096)
    speech_stream_segment_chars: int = Field(default=400, ge=1, le=4096)
    speech_max_audio_mb: int = Field(default=25, ge=1, le=100)

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

    @field_validator("gptsapi_allowed_hosts", mode="before")
    @classmethod
    def parse_allowed_hosts(cls, value: object) -> object:
        if isinstance(value, str):
            return [item.strip().lower() for item in value.split(",") if item.strip()]
        return value

    @property
    def api_key_configured(self) -> bool:
        return bool(self.gptsapi_api_key.strip())

    @property
    def admin_auth_configured(self) -> bool:
        return bool(self.admin_username.strip() and self.admin_password.get_secret_value())

    @property
    def is_sqlite(self) -> bool:
        return self.database_url.startswith("sqlite")

    def ensure_runtime_directories(self) -> None:
        if self.is_sqlite:
            Path("data").mkdir(parents=True, exist_ok=True)


@lru_cache
def get_settings() -> Settings:
    return Settings()
