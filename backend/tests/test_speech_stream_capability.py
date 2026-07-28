from __future__ import annotations

import pytest

from app.capabilities.speech_synthesis.service import SpeechSynthesisCapability
from app.core.error_codes import ErrorCode
from app.core.errors import LlmUpstreamError
from app.infrastructure.llm.models import UpstreamAttempt
from app.infrastructure.speech.models import (
    SpeechRequest,
    SpeechResponse,
    SpeechStreamResponse,
)


def make_request(text: str) -> SpeechRequest:
    return SpeechRequest(
        text=text,
        model="tts-1",
        voice="alloy",
        response_format="mp3",
        speed=1,
    )


class RecordingAuditService:
    def __init__(self) -> None:
        self.payloads = []

    async def record(self, session, payload) -> None:
        del session
        self.payloads.append(payload)


class FailingSecondSegmentClient:
    def __init__(self) -> None:
        self.retry_flags: list[bool] = []

    async def synthesize(self, request: SpeechRequest) -> SpeechResponse:
        raise AssertionError("buffered synthesis is not expected")

    async def open_stream(
        self,
        request: SpeechRequest,
        *,
        attempt_type: str,
        allow_retries: bool,
    ) -> SpeechStreamResponse:
        del request
        self.retry_flags.append(allow_retries)
        attempt = UpstreamAttempt(
            attempt_no=1,
            attempt_type=attempt_type,
            status="success",
            http_status=200,
            error_code=None,
            retryable=False,
            duration_ms=1,
        )
        if len(self.retry_flags) == 2:
            attempt.status = "failed"
            attempt.http_status = 503
            attempt.error_code = ErrorCode.UPSTREAM_UNAVAILABLE.value
            raise LlmUpstreamError(
                ErrorCode.UPSTREAM_UNAVAILABLE,
                "unavailable",
                503,
                True,
                attempts=[attempt],
            )

        async def chunks():
            yield b"first-segment"

        async def close() -> None:
            return None

        return SpeechStreamResponse(
            chunks=chunks(),
            content_type="audio/mpeg",
            model="tts-1",
            attempts=[attempt],
            close_callback=close,
        )


@pytest.mark.asyncio
async def test_stream_does_not_retry_later_segment_and_records_interruption():
    audit = RecordingAuditService()
    client = FailingSecondSegmentClient()
    capability = SpeechSynthesisCapability(audit_service=audit)
    result = await capability.execute_stream(
        session=object(),
        speech_client=client,
        request_id="ai-test-stream",
        caller_system="pytest",
        interface_path="/api/v1/tts/synthesize-stream",
        business_code="tts",
        capability_code="tts.speech.synthesize",
        input_text="first segment. second segment.",
        requests=[make_request("first segment."), make_request("second segment.")],
    )

    iterator = result.chunks.__aiter__()
    assert await iterator.__anext__() == b"first-segment"
    with pytest.raises(LlmUpstreamError) as raised:
        await iterator.__anext__()

    assert raised.value.code == ErrorCode.STREAM_INTERRUPTED
    assert client.retry_flags == [True, False]
    assert len(audit.payloads) == 1
    assert audit.payloads[0].status == "failed"
    assert audit.payloads[0].error_code == ErrorCode.STREAM_INTERRUPTED.value
    assert len(audit.payloads[0].attempts) == 2
