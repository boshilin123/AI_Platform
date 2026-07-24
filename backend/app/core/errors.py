from __future__ import annotations

from dataclasses import dataclass

from app.core.error_codes import ErrorCode


@dataclass(slots=True)
class AppError(Exception):
    code: ErrorCode
    message: str
    http_status: int = 500
    retryable: bool = False

    def __str__(self) -> str:
        return self.message


class LlmUpstreamError(AppError):
    def __init__(
        self,
        code: ErrorCode,
        message: str,
        http_status: int,
        retryable: bool,
        attempts: list[object] | None = None,
    ) -> None:
        super().__init__(code=code, message=message, http_status=http_status, retryable=retryable)
        self.attempts = attempts or []
