from __future__ import annotations

import asyncio
import hashlib
from collections.abc import AsyncIterator
from time import perf_counter

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.error_codes import ErrorCode
from app.core.errors import LlmUpstreamError
from app.infrastructure.llm.models import UpstreamAttempt
from app.infrastructure.speech.client import SpeechClient
from app.infrastructure.speech.models import (
    SpeechRequest,
    SpeechResponse,
    SpeechStreamingResult,
)
from app.modules.audits.repository import AuditWrite
from app.modules.audits.service import AuditService


class SpeechSynthesisCapability:
    def __init__(self, audit_service: AuditService | None = None) -> None:
        self.audit_service = audit_service or AuditService()

    async def execute(
        self,
        *,
        session: AsyncSession,
        speech_client: SpeechClient,
        request_id: str,
        caller_system: str,
        interface_path: str,
        business_code: str,
        capability_code: str,
        request: SpeechRequest,
    ) -> SpeechResponse:
        started = perf_counter()
        attempts: list[UpstreamAttempt] = []
        try:
            response = await speech_client.synthesize(request)
            attempts.extend(response.attempts)
            await self._record(
                session=session,
                request_id=request_id,
                caller_system=caller_system,
                interface_path=interface_path,
                business_code=business_code,
                capability_code=capability_code,
                model=response.model,
                input_text=request.text,
                attempts=attempts,
                started=started,
                status="success",
                http_status=200,
                error_code=None,
                request_mode="binary",
                prompt_version="speech-v1",
            )
            return response
        except LlmUpstreamError as error:
            attempts.extend(error.attempts)
            await self._record(
                session=session,
                request_id=request_id,
                caller_system=caller_system,
                interface_path=interface_path,
                business_code=business_code,
                capability_code=capability_code,
                model=request.model,
                input_text=request.text,
                attempts=attempts,
                started=started,
                status="failed",
                http_status=error.http_status,
                error_code=error.code.value,
                request_mode="binary",
                prompt_version="speech-v1",
            )
            raise

    async def execute_stream(
        self,
        *,
        session: AsyncSession,
        speech_client: SpeechClient,
        request_id: str,
        caller_system: str,
        interface_path: str,
        business_code: str,
        capability_code: str,
        input_text: str,
        requests: list[SpeechRequest],
    ) -> SpeechStreamingResult:
        if not requests:
            raise ValueError("at least one speech request is required")

        started = perf_counter()
        attempts: list[UpstreamAttempt] = []
        first_request = requests[0]
        try:
            first_stream = await speech_client.open_stream(
                first_request,
                attempt_type="speech_synthesis_segment_1",
                allow_retries=True,
            )
        except LlmUpstreamError as error:
            attempts.extend(error.attempts)
            await self._record(
                session=session,
                request_id=request_id,
                caller_system=caller_system,
                interface_path=interface_path,
                business_code=business_code,
                capability_code=capability_code,
                model=first_request.model,
                input_text=input_text,
                attempts=attempts,
                started=started,
                status="failed",
                http_status=error.http_status,
                error_code=error.code.value,
                request_mode="stream",
                prompt_version="speech-stream-v1",
            )
            raise

        async def stream_chunks() -> AsyncIterator[bytes]:
            emitted = False
            business_status = "success"
            business_http_status = 200
            business_error_code: str | None = None
            current_stream = first_stream
            try:
                for segment_index, request in enumerate(requests, start=1):
                    if segment_index > 1:
                        try:
                            current_stream = await speech_client.open_stream(
                                request,
                                attempt_type=f"speech_synthesis_segment_{segment_index}",
                                allow_retries=False,
                            )
                        except LlmUpstreamError as error:
                            attempts.extend(error.attempts)
                            raise LlmUpstreamError(
                                ErrorCode.STREAM_INTERRUPTED,
                                f"语音流在第 {segment_index} 段生成时中断",
                                502,
                                False,
                                attempts=error.attempts,
                            ) from error

                    try:
                        async for chunk in current_stream.chunks:
                            emitted = True
                            yield chunk
                    finally:
                        await current_stream.aclose()
                        attempts.extend(current_stream.attempts)
            except asyncio.CancelledError:
                business_status = "failed"
                business_http_status = 499
                business_error_code = ErrorCode.STREAM_INTERRUPTED.value
                if current_stream.attempts:
                    active_attempt = current_stream.attempts[-1]
                    active_attempt.status = "failed"
                    active_attempt.error_code = ErrorCode.STREAM_INTERRUPTED.value
                raise
            except LlmUpstreamError as error:
                business_status = "failed"
                business_http_status = error.http_status
                business_error_code = (
                    ErrorCode.STREAM_INTERRUPTED.value if emitted else error.code.value
                )
                raise
            except Exception:
                business_status = "failed"
                business_http_status = 502
                business_error_code = ErrorCode.STREAM_INTERRUPTED.value
                raise
            finally:
                await self._record(
                    session=session,
                    request_id=request_id,
                    caller_system=caller_system,
                    interface_path=interface_path,
                    business_code=business_code,
                    capability_code=capability_code,
                    model=first_request.model,
                    input_text=input_text,
                    attempts=attempts,
                    started=started,
                    status=business_status,
                    http_status=business_http_status,
                    error_code=business_error_code,
                    request_mode="stream",
                    prompt_version="speech-stream-v1",
                )

        return SpeechStreamingResult(
            chunks=stream_chunks(),
            content_type=first_stream.content_type,
            model=first_stream.model,
            segment_count=len(requests),
        )

    async def _record(
        self,
        *,
        session: AsyncSession,
        request_id: str,
        caller_system: str,
        interface_path: str,
        business_code: str,
        capability_code: str,
        model: str,
        input_text: str,
        attempts: list[UpstreamAttempt],
        started: float,
        status: str,
        http_status: int,
        error_code: str | None,
        request_mode: str,
        prompt_version: str,
    ) -> None:
        encoded = input_text.encode("utf-8")
        await self.audit_service.record(
            session,
            AuditWrite(
                request_id=request_id,
                business_code=business_code,
                capability_code=capability_code,
                caller_system=caller_system,
                interface_path=interface_path,
                request_mode=request_mode,
                model=model,
                status=status,
                http_status=http_status,
                error_code=error_code,
                retry_count=sum(1 for attempt in attempts if attempt.attempt_no > 1),
                prompt_tokens=0,
                completion_tokens=0,
                total_tokens=0,
                duration_ms=int((perf_counter() - started) * 1000),
                request_content_hash=hashlib.sha256(encoded).hexdigest(),
                request_content_length=len(input_text),
                prompt_version=prompt_version,
                attempts=attempts,
            ),
        )
