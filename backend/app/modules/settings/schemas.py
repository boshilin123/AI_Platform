from datetime import datetime

from pydantic import BaseModel, ConfigDict, ValidationInfo, field_validator

from app.core.schemas import CamelModel


class SettingsData(CamelModel):
    environment: str
    mock_mode: bool
    api_key_configured: bool
    base_url: str
    model: str
    speech_model: str
    connect_timeout_seconds: float
    read_timeout_seconds: float
    stream_idle_timeout_seconds: float
    max_retries: int
    retry_delays_seconds: list[float]
    speech_max_input_chars: int
    speech_max_stream_chars: int
    audit_retention_days: int
    internal_auth_enabled: bool
    admin_auth_configured: bool
    configuration_source: str
    updated_by: str | None
    updated_at: datetime | None


class LlmSettingsUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    baseUrl: str
    model: str
    speechModel: str

    @field_validator("baseUrl", "model", "speechModel")
    @classmethod
    def strip_value(cls, value: str, info: ValidationInfo) -> str:
        normalized = value.strip()
        maximum = 512 if info.field_name == "baseUrl" else 128
        if not normalized:
            raise ValueError("value is required")
        if len(normalized) > maximum:
            raise ValueError("value is too long")
        return normalized


class ModelListData(CamelModel):
    base_url: str
    models: list[str]
    chat_models: list[str]
    speech_models: list[str]


class AdminOperationAuditItem(CamelModel):
    request_id: str
    actor: str
    action: str
    status: str
    http_status: int
    error_code: str | None
    duration_ms: int
    old_base_url: str | None
    new_base_url: str | None
    old_model: str | None
    new_model: str | None
    old_speech_model: str | None
    new_speech_model: str | None
    created_at: datetime


class AdminOperationAuditList(CamelModel):
    items: list[AdminOperationAuditItem]
    page: int
    page_size: int
    total: int
