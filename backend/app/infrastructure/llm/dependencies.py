from fastapi import Depends

from app.core.config import Settings, get_settings
from app.infrastructure.llm.client import LlmClient, MockLlmClient, OpenAICompatibleLlmClient


async def get_llm_client(settings: Settings = Depends(get_settings)) -> LlmClient:
    if settings.ai_mock_mode:
        return MockLlmClient(settings.gptsapi_model)
    return OpenAICompatibleLlmClient(settings)
