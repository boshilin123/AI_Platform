from fastapi import Depends

from app.core.config import Settings, get_settings
from app.infrastructure.llm.client import LlmClient, MockLlmClient, OpenAICompatibleLlmClient
from app.infrastructure.llm.models import LlmRuntimeConfig
from app.modules.settings.dependencies import get_runtime_llm_config


async def get_llm_client(
    settings: Settings = Depends(get_settings),
    runtime_config: LlmRuntimeConfig = Depends(get_runtime_llm_config),
) -> LlmClient:
    if settings.ai_mock_mode:
        return MockLlmClient(runtime_config.model)
    return OpenAICompatibleLlmClient(settings, runtime_config)
