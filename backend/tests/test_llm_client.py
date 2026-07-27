from __future__ import annotations

import httpx
import pytest
import respx

from app.core.config import Settings
from app.core.errors import LlmUpstreamError
from app.infrastructure.llm.client import OpenAICompatibleLlmClient
from app.infrastructure.llm.models import LlmMessage, LlmRequest


def make_request() -> LlmRequest:
    return LlmRequest(
        model="test-model",
        messages=[LlmMessage(role="user", content="hello")],
    )


@pytest.mark.asyncio
async def test_rate_limit_retries_then_succeeds():
    settings = Settings(
        ai_mock_mode=False,
        gptsapi_base_url="https://example.test/v1",
        gptsapi_api_key="test-placeholder-key",
        gptsapi_model="test-model",
        ai_max_retries=2,
        ai_retry_delays_seconds=[0, 0],
    )
    with respx.mock as mock:
        route = mock.post("https://example.test/v1/chat/completions")
        route.side_effect = [
            httpx.Response(
                429, headers={"Retry-After": "0"}, json={"error": {"message": "rate limit"}}
            ),
            httpx.Response(
                200,
                json={
                    "model": "test-model",
                    "choices": [{"message": {"content": "{\"ok\": true}"}}],
                    "usage": {"prompt_tokens": 3, "completion_tokens": 2, "total_tokens": 5},
                },
            ),
        ]
        response = await OpenAICompatibleLlmClient(settings).chat(make_request())

    assert len(response.attempts) == 2
    assert response.attempts[0].error_code == "AI_UPSTREAM_RATE_LIMIT"
    assert response.usage.total_tokens == 5
    assert route.call_count == 2


@pytest.mark.asyncio
async def test_auth_error_is_not_retried():
    settings = Settings(
        ai_mock_mode=False,
        gptsapi_base_url="https://example.test/v1",
        gptsapi_api_key="test-placeholder-key",
        gptsapi_model="test-model",
        ai_max_retries=2,
        ai_retry_delays_seconds=[0, 0],
    )
    with respx.mock as mock:
        route = mock.post("https://example.test/v1/chat/completions").mock(
            return_value=httpx.Response(401, json={"error": {"message": "unauthorized"}})
        )
        with pytest.raises(LlmUpstreamError) as raised:
            await OpenAICompatibleLlmClient(settings).chat(make_request())

    assert raised.value.code.value == "AI_UPSTREAM_AUTH_ERROR"
    assert len(raised.value.attempts) == 1
    assert route.call_count == 1


@pytest.mark.asyncio
async def test_malformed_success_payload_is_failed_attempt_without_retry():
    settings = Settings(
        ai_mock_mode=False,
        gptsapi_base_url="https://example.test/v1",
        gptsapi_api_key="test-placeholder-key",
        gptsapi_model="test-model",
        ai_max_retries=2,
        ai_retry_delays_seconds=[0, 0],
    )
    with respx.mock as mock:
        route = mock.post("https://example.test/v1/chat/completions").mock(
            return_value=httpx.Response(
                200,
                json={
                    "model": "test-model",
                    "choices": [],
                    "usage": {"prompt_tokens": 3, "completion_tokens": 0, "total_tokens": 3},
                },
            )
        )
        with pytest.raises(LlmUpstreamError) as raised:
            await OpenAICompatibleLlmClient(settings).chat(make_request())

    assert raised.value.code.value == "AI_UPSTREAM_UNAVAILABLE"
    assert raised.value.retryable is False
    assert len(raised.value.attempts) == 1
    assert raised.value.attempts[0].http_status == 200
    assert raised.value.attempts[0].usage.total_tokens == 3
    assert route.call_count == 1
