from __future__ import annotations

import asyncio
import struct
from time import perf_counter
from typing import Protocol

import httpx

from app.core.config import Settings
from app.core.error_codes import ErrorCode
from app.core.errors import LlmUpstreamError
from app.infrastructure.llm.error_mapper import MappedError, map_http_error
from app.infrastructure.llm.models import UpstreamAttempt
from app.infrastructure.speech.models import (
    SpeechRequest,
    SpeechResponse,
    SpeechRuntimeConfig,
    SpeechStreamResponse,
)


class SpeechClient(Protocol):
    async def synthesize(self, request: SpeechRequest) -> SpeechResponse: ...

    async def open_stream(
        self,
        request: SpeechRequest,
        *,
        attempt_type: str,
        allow_retries: bool,
    ) -> SpeechStreamResponse: ...


class OpenAICompatibleSpeechClient:
    def __init__(self, settings: Settings, runtime_config: SpeechRuntimeConfig) -> None:
        self.settings = settings
        self.runtime_config = runtime_config

    @property
    def endpoint(self) -> str:
        return f"{self.runtime_config.base_url.rstrip('/')}/audio/speech"

    async def synthesize(self, request: SpeechRequest) -> SpeechResponse:
        if not self.settings.api_key_configured:
            raise LlmUpstreamError(
                ErrorCode.UPSTREAM_AUTH_ERROR,
                "服务端尚未配置 AI API Key",
                503,
                False,
                attempts=[],
            )

        attempts: list[UpstreamAttempt] = []
        max_calls = self.settings.ai_max_retries + 1
        timeout = httpx.Timeout(
            connect=self.settings.ai_connect_timeout_seconds,
            read=self.settings.ai_read_timeout_seconds,
            write=self.settings.ai_connect_timeout_seconds,
            pool=self.settings.ai_connect_timeout_seconds,
        )
        maximum_bytes = self.settings.speech_max_audio_mb * 1024 * 1024

        async with httpx.AsyncClient(timeout=timeout) as client:
            for call_index in range(max_calls):
                started = perf_counter()
                try:
                    response = await client.post(
                        self.endpoint,
                        headers={
                            "Authorization": f"Bearer {self.settings.gptsapi_api_key}",
                            "Content-Type": "application/json",
                        },
                        json={
                            "model": request.model,
                            "input": request.text,
                            "voice": request.voice,
                            "response_format": request.response_format,
                            "speed": request.speed,
                        },
                    )
                    duration_ms = int((perf_counter() - started) * 1000)
                    if response.is_success:
                        content_type = response.headers.get("Content-Type", "").split(";")[0].strip()
                        audio = response.content
                        if (
                            not audio
                            or len(audio) > maximum_bytes
                            or content_type not in self._allowed_content_types(request.response_format)
                        ):
                            attempts.append(
                                UpstreamAttempt(
                                    attempt_no=call_index + 1,
                                    attempt_type="speech_synthesis",
                                    status="failed",
                                    http_status=response.status_code,
                                    error_code=ErrorCode.UPSTREAM_UNAVAILABLE.value,
                                    retryable=False,
                                    duration_ms=duration_ms,
                                )
                            )
                            raise LlmUpstreamError(
                                ErrorCode.UPSTREAM_UNAVAILABLE,
                                "语音服务返回的音频格式异常",
                                502,
                                False,
                                attempts=attempts,
                            )
                        attempts.append(
                            UpstreamAttempt(
                                attempt_no=call_index + 1,
                                attempt_type="speech_synthesis",
                                status="success",
                                http_status=response.status_code,
                                error_code=None,
                                retryable=False,
                                duration_ms=duration_ms,
                            )
                        )
                        return SpeechResponse(
                            audio=audio,
                            content_type=content_type,
                            model=request.model,
                            attempts=attempts,
                        )

                    mapped = map_http_error(response.status_code, response.text[:1000])
                    attempts.append(
                        UpstreamAttempt(
                            attempt_no=call_index + 1,
                            attempt_type="speech_synthesis",
                            status="failed",
                            http_status=response.status_code,
                            error_code=mapped.code.value,
                            retryable=mapped.retryable,
                            duration_ms=duration_ms,
                        )
                    )
                    if mapped.retryable and call_index < max_calls - 1:
                        await asyncio.sleep(
                            self._retry_delay(call_index, response.headers.get("Retry-After"))
                        )
                        continue
                    raise self._upstream_error(mapped, attempts)
                except LlmUpstreamError:
                    raise
                except httpx.TimeoutException as exc:
                    duration_ms = int((perf_counter() - started) * 1000)
                    mapped = MappedError(
                        ErrorCode.UPSTREAM_TIMEOUT,
                        "语音服务响应超时，请稍后重试",
                        504,
                        True,
                    )
                    attempts.append(
                        UpstreamAttempt(
                            attempt_no=call_index + 1,
                            attempt_type="speech_synthesis",
                            status="failed",
                            http_status=None,
                            error_code=mapped.code.value,
                            retryable=True,
                            duration_ms=duration_ms,
                        )
                    )
                    if call_index < max_calls - 1:
                        await asyncio.sleep(self._retry_delay(call_index))
                        continue
                    raise self._upstream_error(mapped, attempts) from exc
                except httpx.RequestError as exc:
                    duration_ms = int((perf_counter() - started) * 1000)
                    mapped = MappedError(
                        ErrorCode.UPSTREAM_UNAVAILABLE,
                        "语音上游服务暂时不可用",
                        503,
                        True,
                    )
                    attempts.append(
                        UpstreamAttempt(
                            attempt_no=call_index + 1,
                            attempt_type="speech_synthesis",
                            status="failed",
                            http_status=None,
                            error_code=mapped.code.value,
                            retryable=True,
                            duration_ms=duration_ms,
                        )
                    )
                    if call_index < max_calls - 1:
                        await asyncio.sleep(self._retry_delay(call_index))
                        continue
                    raise self._upstream_error(mapped, attempts) from exc

        raise RuntimeError("unreachable")

    async def open_stream(
        self,
        request: SpeechRequest,
        *,
        attempt_type: str,
        allow_retries: bool,
    ) -> SpeechStreamResponse:
        if not self.settings.api_key_configured:
            raise LlmUpstreamError(
                ErrorCode.UPSTREAM_AUTH_ERROR,
                "服务端尚未配置 AI API Key",
                503,
                False,
                attempts=[],
            )

        attempts: list[UpstreamAttempt] = []
        max_calls = self.settings.ai_max_retries + 1 if allow_retries else 1
        maximum_bytes = self.settings.speech_max_audio_mb * 1024 * 1024
        timeout = httpx.Timeout(
            connect=self.settings.ai_connect_timeout_seconds,
            read=self.settings.ai_stream_idle_timeout_seconds,
            write=self.settings.ai_connect_timeout_seconds,
            pool=self.settings.ai_connect_timeout_seconds,
        )

        for call_index in range(max_calls):
            client = httpx.AsyncClient(timeout=timeout)
            started = perf_counter()
            try:
                response = await client.send(
                    client.build_request(
                        "POST",
                        self.endpoint,
                        headers={
                            "Authorization": f"Bearer {self.settings.gptsapi_api_key}",
                            "Content-Type": "application/json",
                        },
                        json=self._request_payload(request),
                    ),
                    stream=True,
                )
                if response.is_success:
                    content_type = (
                        response.headers.get("Content-Type", "").split(";")[0].strip()
                    )
                    if content_type not in self._allowed_content_types(request.response_format):
                        await response.aclose()
                        await client.aclose()
                        attempts.append(
                            UpstreamAttempt(
                                attempt_no=call_index + 1,
                                attempt_type=attempt_type,
                                status="failed",
                                http_status=response.status_code,
                                error_code=ErrorCode.UPSTREAM_UNAVAILABLE.value,
                                retryable=False,
                                duration_ms=int((perf_counter() - started) * 1000),
                            )
                        )
                        raise LlmUpstreamError(
                            ErrorCode.UPSTREAM_UNAVAILABLE,
                            "语音服务返回的音频格式异常",
                            502,
                            False,
                            attempts=attempts,
                        )

                    active_attempt = UpstreamAttempt(
                        attempt_no=call_index + 1,
                        attempt_type=attempt_type,
                        status="success",
                        http_status=response.status_code,
                        error_code=None,
                        retryable=False,
                        duration_ms=0,
                    )
                    attempts.append(active_attempt)
                    closed = False

                    async def close_stream() -> None:
                        nonlocal closed
                        if closed:
                            return
                        closed = True
                        active_attempt.duration_ms = int((perf_counter() - started) * 1000)
                        await response.aclose()
                        await client.aclose()

                    async def chunks():
                        emitted_bytes = 0
                        try:
                            async for chunk in response.aiter_bytes():
                                if not chunk:
                                    continue
                                emitted_bytes += len(chunk)
                                if emitted_bytes > maximum_bytes:
                                    active_attempt.status = "failed"
                                    active_attempt.error_code = (
                                        ErrorCode.UPSTREAM_UNAVAILABLE.value
                                    )
                                    raise LlmUpstreamError(
                                        ErrorCode.UPSTREAM_UNAVAILABLE,
                                        "语音服务返回的音频超过大小限制",
                                        502,
                                        False,
                                        attempts=attempts,
                                    )
                                yield chunk
                        except LlmUpstreamError:
                            raise
                        except (httpx.TimeoutException, httpx.RequestError) as exc:
                            active_attempt.status = "failed"
                            active_attempt.error_code = ErrorCode.STREAM_INTERRUPTED.value
                            raise LlmUpstreamError(
                                ErrorCode.STREAM_INTERRUPTED,
                                "语音流传输中断",
                                502,
                                False,
                                attempts=attempts,
                            ) from exc
                        finally:
                            await close_stream()

                    return SpeechStreamResponse(
                        chunks=chunks(),
                        content_type=content_type,
                        model=request.model,
                        attempts=attempts,
                        close_callback=close_stream,
                    )

                body = (await response.aread()).decode(errors="replace")
                mapped = map_http_error(response.status_code, body[:1000])
                attempts.append(
                    UpstreamAttempt(
                        attempt_no=call_index + 1,
                        attempt_type=attempt_type,
                        status="failed",
                        http_status=response.status_code,
                        error_code=mapped.code.value,
                        retryable=mapped.retryable,
                        duration_ms=int((perf_counter() - started) * 1000),
                    )
                )
                retry_after = response.headers.get("Retry-After")
                await response.aclose()
                await client.aclose()
                if mapped.retryable and call_index < max_calls - 1:
                    await asyncio.sleep(self._retry_delay(call_index, retry_after))
                    continue
                raise self._upstream_error(mapped, attempts)
            except LlmUpstreamError:
                if not client.is_closed:
                    await client.aclose()
                raise
            except httpx.TimeoutException as exc:
                await client.aclose()
                mapped = MappedError(
                    ErrorCode.UPSTREAM_TIMEOUT,
                    "语音服务响应超时，请稍后重试",
                    504,
                    True,
                )
                attempts.append(
                    UpstreamAttempt(
                        attempt_no=call_index + 1,
                        attempt_type=attempt_type,
                        status="failed",
                        http_status=None,
                        error_code=mapped.code.value,
                        retryable=True,
                        duration_ms=int((perf_counter() - started) * 1000),
                    )
                )
                if call_index < max_calls - 1:
                    await asyncio.sleep(self._retry_delay(call_index))
                    continue
                raise self._upstream_error(mapped, attempts) from exc
            except httpx.RequestError as exc:
                await client.aclose()
                mapped = MappedError(
                    ErrorCode.UPSTREAM_UNAVAILABLE,
                    "语音上游服务暂时不可用",
                    503,
                    True,
                )
                attempts.append(
                    UpstreamAttempt(
                        attempt_no=call_index + 1,
                        attempt_type=attempt_type,
                        status="failed",
                        http_status=None,
                        error_code=mapped.code.value,
                        retryable=True,
                        duration_ms=int((perf_counter() - started) * 1000),
                    )
                )
                if call_index < max_calls - 1:
                    await asyncio.sleep(self._retry_delay(call_index))
                    continue
                raise self._upstream_error(mapped, attempts) from exc

        raise RuntimeError("unreachable")

    @staticmethod
    def _request_payload(request: SpeechRequest) -> dict[str, object]:
        return {
            "model": request.model,
            "input": request.text,
            "voice": request.voice,
            "response_format": request.response_format,
            "speed": request.speed,
        }

    def _retry_delay(self, retry_index: int, retry_after: str | None = None) -> float:
        if retry_after:
            try:
                return max(0, min(float(retry_after), 60))
            except ValueError:
                pass
        delays = self.settings.ai_retry_delays_seconds
        if not delays:
            return 0
        return max(0, delays[min(retry_index, len(delays) - 1)])

    @staticmethod
    def _allowed_content_types(response_format: str) -> set[str]:
        expected = "audio/mpeg" if response_format == "mp3" else "audio/wav"
        return {
            expected,
            "audio/mp3",
            "audio/x-wav",
            "audio/wave",
            "application/octet-stream",
        }

    @staticmethod
    def _upstream_error(
        mapped: MappedError,
        attempts: list[UpstreamAttempt],
    ) -> LlmUpstreamError:
        return LlmUpstreamError(
            mapped.code,
            mapped.message,
            mapped.public_http_status,
            mapped.retryable,
            attempts=attempts,
        )


class MockSpeechClient:
    def __init__(self, model: str) -> None:
        self.model = model

    async def synthesize(self, request: SpeechRequest) -> SpeechResponse:
        await asyncio.sleep(0)
        return SpeechResponse(
            audio=self._silent_wav(),
            content_type="audio/wav",
            model=self.model,
            attempts=[],
        )

    async def open_stream(
        self,
        request: SpeechRequest,
        *,
        attempt_type: str,
        allow_retries: bool,
    ) -> SpeechStreamResponse:
        del attempt_type, allow_retries
        audio = self._silent_wav()

        async def chunks():
            midpoint = len(audio) // 2
            yield audio[:midpoint]
            await asyncio.sleep(0)
            yield audio[midpoint:]

        async def close_stream() -> None:
            return None

        return SpeechStreamResponse(
            chunks=chunks(),
            content_type="audio/wav",
            model=self.model,
            attempts=[],
            close_callback=close_stream,
        )

    @staticmethod
    def _silent_wav() -> bytes:
        sample_rate = 8000
        samples = b"\x00\x00" * (sample_rate // 4)
        return (
            b"RIFF"
            + struct.pack("<I", 36 + len(samples))
            + b"WAVEfmt "
            + struct.pack("<IHHIIHH", 16, 1, 1, sample_rate, sample_rate * 2, 2, 16)
            + b"data"
            + struct.pack("<I", len(samples))
            + samples
        )
