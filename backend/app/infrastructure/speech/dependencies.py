from fastapi import Depends

from app.core.config import Settings, get_settings
from app.infrastructure.llm.models import LlmRuntimeConfig
from app.infrastructure.speech.client import (
    MockSpeechClient,
    OpenAICompatibleSpeechClient,
    SpeechClient,
)
from app.infrastructure.speech.models import SpeechRuntimeConfig
from app.modules.settings.dependencies import get_runtime_llm_config


async def get_speech_client(
    settings: Settings = Depends(get_settings),
    runtime_config: LlmRuntimeConfig = Depends(get_runtime_llm_config),
) -> SpeechClient:
    if settings.ai_mock_mode:
        return MockSpeechClient(runtime_config.speech_model)
    return OpenAICompatibleSpeechClient(
        settings,
        SpeechRuntimeConfig(
            base_url=runtime_config.base_url,
            model=runtime_config.speech_model,
        ),
    )
