from app.core.schemas import CamelModel


class SettingsData(CamelModel):
    environment: str
    mock_mode: bool
    api_key_configured: bool
    base_url: str
    model: str
    connect_timeout_seconds: float
    read_timeout_seconds: float
    stream_idle_timeout_seconds: float
    max_retries: int
    retry_delays_seconds: list[float]
    audit_retention_days: int
    internal_auth_enabled: bool
