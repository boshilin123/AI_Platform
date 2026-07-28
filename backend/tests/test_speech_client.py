from __future__ import annotations

import json

import httpx
import pytest
import respx

from app.core.config import Settings
from app.core.errors import LlmUpstreamError
from app.infrastructure.speech.client import OpenAICompatibleSpeechClient
from app.infrastructure.speech.models import SpeechRequest, SpeechRuntimeConfig


def make_client() -> OpenAICompatibleSpeechClient:
    settings = Settings(
        ai_mock_mode=False,
        gptsapi_base_url="https://example.test/v1",
        gptsapi_api_key="test-placeholder-key",
        gptsapi_model="test-model",
        gptsapi_speech_model="tts-1",
        ai_max_retries=2,
        ai_retry_delays_seconds=[0, 0],
    )
    return OpenAICompatibleSpeechClient(
        settings,
        SpeechRuntimeConfig(base_url="https://example.test/v1", model="tts-1"),
    )


def make_request(speed: float = 1) -> SpeechRequest:
    return SpeechRequest(
        text="hello",
        model="tts-1",
        voice="alloy",
        response_format="mp3",
        speed=speed,
    )


@pytest.mark.asyncio
async def test_speech_rate_limit_retries_then_returns_audio():
    with respx.mock as mock:
        route = mock.post("https://example.test/v1/audio/speech")
        route.side_effect = [
            httpx.Response(429, headers={"Retry-After": "0"}, json={"error": "rate limit"}),
            httpx.Response(200, content=b"audio-bytes", headers={"Content-Type": "audio/mpeg"}),
        ]
        response = await make_client().synthesize(make_request())

    assert response.audio == b"audio-bytes"
    assert len(response.attempts) == 2
    assert response.attempts[0].error_code == "AI_UPSTREAM_RATE_LIMIT"
    assert route.call_count == 2


@pytest.mark.asyncio
async def test_speech_invalid_request_is_not_retried():
    with respx.mock as mock:
        route = mock.post("https://example.test/v1/audio/speech").mock(
            return_value=httpx.Response(400, json={"error": {"message": "invalid voice"}})
        )
        with pytest.raises(LlmUpstreamError) as raised:
            await make_client().synthesize(make_request())

    assert raised.value.code.value == "AI_INVALID_REQUEST"
    assert raised.value.retryable is False
    assert len(raised.value.attempts) == 1
    assert route.call_count == 1


@pytest.mark.asyncio
async def test_speech_json_success_payload_is_rejected():
    with respx.mock as mock:
        route = mock.post("https://example.test/v1/audio/speech").mock(
            return_value=httpx.Response(
                200,
                json={"unexpected": "payload"},
                headers={"Content-Type": "application/json"},
            )
        )
        with pytest.raises(LlmUpstreamError) as raised:
            await make_client().synthesize(make_request())

    assert raised.value.code.value == "AI_UPSTREAM_UNAVAILABLE"
    assert raised.value.retryable is False
    assert route.call_count == 1


@pytest.mark.asyncio
async def test_speech_stream_retries_before_first_audio_byte():
    with respx.mock as mock:
        route = mock.post("https://example.test/v1/audio/speech")
        route.side_effect = [
            httpx.Response(429, headers={"Retry-After": "0"}, json={"error": "rate limit"}),
            httpx.Response(200, content=b"streamed-audio", headers={"Content-Type": "audio/mpeg"}),
        ]
        stream = await make_client().open_stream(
            make_request(),
            attempt_type="speech_synthesis_segment_1",
            allow_retries=True,
        )
        audio = b"".join([chunk async for chunk in stream.chunks])
        await stream.aclose()

    assert audio == b"streamed-audio"
    assert len(stream.attempts) == 2
    assert stream.attempts[0].status == "failed"
    assert stream.attempts[1].status == "success"
    assert route.call_count == 2


@pytest.mark.asyncio
async def test_speech_stream_does_not_retry_after_response_started():
    with respx.mock as mock:
        route = mock.post("https://example.test/v1/audio/speech").mock(
            return_value=httpx.Response(503, json={"error": "unavailable"})
        )
        with pytest.raises(LlmUpstreamError):
            await make_client().open_stream(
                make_request(),
                attempt_type="speech_synthesis_segment_2",
                allow_retries=False,
            )

    assert route.call_count == 1


@pytest.mark.asyncio
async def test_speech_sends_selected_synthesis_speed_upstream():
    with respx.mock as mock:
        route = mock.post("https://example.test/v1/audio/speech").mock(
            return_value=httpx.Response(
                200,
                content=b"audio-bytes",
                headers={"Content-Type": "audio/mpeg"},
            )
        )
        await make_client().synthesize(make_request(speed=2.3))

    payload = json.loads(route.calls.last.request.content)
    assert payload["speed"] == 2.3
