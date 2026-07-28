from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.db.session import get_db_session
from app.infrastructure.llm.models import LlmRuntimeConfig
from app.modules.settings.service import SettingsService


async def get_runtime_llm_config(
    session: AsyncSession = Depends(get_db_session),
    settings: Settings = Depends(get_settings),
) -> LlmRuntimeConfig:
    return await SettingsService().effective_llm_config(session, settings)
