from __future__ import annotations

from dataclasses import dataclass
from time import perf_counter

import httpx

from app.core.error_codes import ErrorCode
from app.core.errors import LlmUpstreamError
from app.infrastructure.llm.error_mapper import map_http_error
from app.infrastructure.llm.models import UpstreamAttempt

SPEECH_MODELS = frozenset({"tts-1", "tts-1-hd"})
NON_CHAT_MODEL_PREFIXES = (
    "tts-",
    "whisper-",
    "text-embedding-",
)
NON_CHAT_MODEL_FRAGMENTS = (
    "image",
    "embedding",
    "transcription",
)


def is_speech_model(model: str) -> bool:
    return model.casefold() in SPEECH_MODELS


def is_chat_model(model: str) -> bool:
    normalized = model.casefold()
    return (
        normalized not in SPEECH_MODELS
        and not normalized.startswith(NON_CHAT_MODEL_PREFIXES)
        and not any(fragment in normalized for fragment in NON_CHAT_MODEL_FRAGMENTS)
    )


@dataclass(frozen=True, slots=True)
class ModelCatalogResult:
    models: list[str]
    attempt: UpstreamAttempt


class ModelCatalogClient:
    async def list_models(
        self,
        *,
        base_url: str,
        api_key: str,
        connect_timeout_seconds: float,
        read_timeout_seconds: float,
    ) -> ModelCatalogResult:
        if not api_key.strip():
            raise LlmUpstreamError(
                ErrorCode.UPSTREAM_AUTH_ERROR,
                "服务端尚未配置 AI API Key",
                503,
                False,
                attempts=[],
            )

        timeout = httpx.Timeout(
            connect=connect_timeout_seconds,
            read=read_timeout_seconds,
            write=connect_timeout_seconds,
            pool=connect_timeout_seconds,
        )
        started = perf_counter()
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.get(
                    f"{base_url.rstrip('/')}/models",
                    headers={"Authorization": f"Bearer {api_key}"},
                )
            duration_ms = int((perf_counter() - started) * 1000)
            if not response.is_success:
                mapped = map_http_error(response.status_code, response.text[:1000])
                attempt = UpstreamAttempt(
                    attempt_no=1,
                    attempt_type="model_discovery",
                    status="failed",
                    http_status=response.status_code,
                    error_code=mapped.code.value,
                    retryable=mapped.retryable,
                    duration_ms=duration_ms,
                )
                raise LlmUpstreamError(
                    mapped.code,
                    mapped.message,
                    mapped.public_http_status,
                    mapped.retryable,
                    attempts=[attempt],
                )

            try:
                payload = response.json()
                items = payload["data"]
                if not isinstance(items, list):
                    raise TypeError("model data is not a list")
                models = sorted(
                    {
                        item["id"].strip()
                        for item in items
                        if isinstance(item, dict)
                        and isinstance(item.get("id"), str)
                        and item["id"].strip()
                    },
                    key=str.casefold,
                )
                if not models:
                    raise ValueError("model list is empty")
            except (KeyError, TypeError, ValueError) as exc:
                attempt = UpstreamAttempt(
                    attempt_no=1,
                    attempt_type="model_discovery",
                    status="failed",
                    http_status=response.status_code,
                    error_code=ErrorCode.UPSTREAM_UNAVAILABLE.value,
                    retryable=False,
                    duration_ms=duration_ms,
                )
                raise LlmUpstreamError(
                    ErrorCode.UPSTREAM_UNAVAILABLE,
                    "AI 上游返回的模型列表格式异常",
                    502,
                    False,
                    attempts=[attempt],
                ) from exc

            return ModelCatalogResult(
                models=models,
                attempt=UpstreamAttempt(
                    attempt_no=1,
                    attempt_type="model_discovery",
                    status="success",
                    http_status=response.status_code,
                    error_code=None,
                    retryable=False,
                    duration_ms=duration_ms,
                ),
            )
        except LlmUpstreamError:
            raise
        except httpx.TimeoutException as exc:
            duration_ms = int((perf_counter() - started) * 1000)
            attempt = UpstreamAttempt(
                attempt_no=1,
                attempt_type="model_discovery",
                status="failed",
                http_status=None,
                error_code=ErrorCode.UPSTREAM_TIMEOUT.value,
                retryable=True,
                duration_ms=duration_ms,
            )
            raise LlmUpstreamError(
                ErrorCode.UPSTREAM_TIMEOUT,
                "获取上游模型列表超时",
                504,
                True,
                attempts=[attempt],
            ) from exc
        except httpx.RequestError as exc:
            duration_ms = int((perf_counter() - started) * 1000)
            attempt = UpstreamAttempt(
                attempt_no=1,
                attempt_type="model_discovery",
                status="failed",
                http_status=None,
                error_code=ErrorCode.UPSTREAM_UNAVAILABLE.value,
                retryable=True,
                duration_ms=duration_ms,
            )
            raise LlmUpstreamError(
                ErrorCode.UPSTREAM_UNAVAILABLE,
                "AI 上游服务暂时不可用",
                503,
                True,
                attempts=[attempt],
            ) from exc


def get_model_catalog_client() -> ModelCatalogClient:
    return ModelCatalogClient()
