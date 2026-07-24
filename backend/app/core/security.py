from hmac import compare_digest

from fastapi import Depends, Header

from app.core.config import Settings, get_settings
from app.core.error_codes import ErrorCode
from app.core.errors import AppError


async def require_internal_token(
    x_internal_token: str | None = Header(default=None),
    settings: Settings = Depends(get_settings),
) -> None:
    expected = settings.internal_api_token
    if not expected:
        return
    if not x_internal_token or not compare_digest(x_internal_token, expected):
        raise AppError(
            code=ErrorCode.UNAUTHORIZED,
            message="内部调用鉴权失败",
            http_status=401,
            retryable=False,
        )


async def get_caller_system(x_caller_system: str | None = Header(default=None)) -> str:
    value = (x_caller_system or "ai-platform-web").strip()
    return value[:64] or "unknown"
