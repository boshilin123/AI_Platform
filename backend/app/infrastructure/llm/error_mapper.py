from __future__ import annotations

from dataclasses import dataclass

from app.core.error_codes import ErrorCode


@dataclass(frozen=True, slots=True)
class MappedError:
    code: ErrorCode
    message: str
    public_http_status: int
    retryable: bool


def map_http_error(status_code: int, body: str = "") -> MappedError:
    lowered = body.lower()
    if status_code in (401, 403):
        return MappedError(
            ErrorCode.UPSTREAM_AUTH_ERROR,
            "AI 上游认证失败，请联系管理员检查服务配置",
            502,
            False,
        )
    if status_code == 404 or "model" in lowered and "not found" in lowered:
        return MappedError(ErrorCode.MODEL_NOT_FOUND, "AI 模型配置不可用", 502, False)
    if status_code == 429:
        return MappedError(ErrorCode.UPSTREAM_RATE_LIMIT, "AI 服务请求过多，请稍后重试", 503, True)
    if status_code >= 500:
        return MappedError(ErrorCode.UPSTREAM_UNAVAILABLE, "AI 上游服务暂时不可用", 503, True)
    if status_code == 400 and any(word in lowered for word in ("content", "safety", "policy")):
        return MappedError(ErrorCode.CONTENT_REJECTED, "请求内容无法由 AI 服务处理", 422, False)
    if 400 <= status_code < 500:
        return MappedError(ErrorCode.INVALID_REQUEST, "AI 请求参数不被上游接受", 400, False)
    return MappedError(ErrorCode.UPSTREAM_UNAVAILABLE, "AI 上游服务响应异常", 502, False)
