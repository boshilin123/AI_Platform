from __future__ import annotations

from datetime import datetime

from app.core.schemas import CamelModel


class AuditAttemptItem(CamelModel):
    attempt_no: int
    attempt_type: str
    status: str
    http_status: int | None
    error_code: str | None
    retryable: bool
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    duration_ms: int


class AuditItem(CamelModel):
    request_id: str
    business_code: str
    capability_code: str
    caller_system: str
    interface_path: str
    request_mode: str
    model: str
    status: str
    http_status: int
    error_code: str | None
    retry_count: int
    upstream_call_count: int
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    request_content_length: int
    duration_ms: int
    prompt_version: str
    created_at: datetime


class AuditListData(CamelModel):
    items: list[AuditItem]
    page: int
    page_size: int
    total: int
