from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.core.request_context import get_request_id
from app.core.schemas import SuccessResponse
from app.core.security import require_internal_token
from app.db.session import get_db_session
from app.infrastructure.llm.catalog import ModelCatalogClient, get_model_catalog_client
from app.modules.admin.dependencies import require_admin
from app.modules.admin.service import AdminIdentity
from app.modules.settings.schemas import (
    AdminOperationAuditList,
    LlmSettingsUpdate,
    ModelListData,
    SettingsData,
)
from app.modules.settings.service import SettingsService

router = APIRouter(
    prefix="/settings",
    tags=["基础配置"],
    dependencies=[Depends(require_internal_token)],
)


@router.get("", response_model=SuccessResponse[SettingsData])
async def read_settings(
    session: AsyncSession = Depends(get_db_session),
    settings: Settings = Depends(get_settings),
) -> SuccessResponse[SettingsData]:
    return SuccessResponse(
        request_id=get_request_id(),
        data=await SettingsService().read(session, settings),
    )


@router.get("/models", response_model=SuccessResponse[ModelListData])
async def list_models(
    base_url: str = Query(alias="baseUrl", min_length=1, max_length=512),
    identity: AdminIdentity = Depends(require_admin),
    session: AsyncSession = Depends(get_db_session),
    settings: Settings = Depends(get_settings),
    catalog_client: ModelCatalogClient = Depends(get_model_catalog_client),
) -> SuccessResponse[ModelListData]:
    request_id = get_request_id()
    data = await SettingsService(catalog_client=catalog_client).discover_models(
        session,
        settings,
        base_url=base_url,
        actor=identity.username,
        request_id=request_id,
    )
    return SuccessResponse(request_id=request_id, data=data)


@router.put("/llm", response_model=SuccessResponse[SettingsData])
async def update_llm_settings(
    payload: LlmSettingsUpdate,
    identity: AdminIdentity = Depends(require_admin),
    session: AsyncSession = Depends(get_db_session),
    settings: Settings = Depends(get_settings),
    catalog_client: ModelCatalogClient = Depends(get_model_catalog_client),
) -> SuccessResponse[SettingsData]:
    request_id = get_request_id()
    data = await SettingsService(catalog_client=catalog_client).update_llm_settings(
        session,
        settings,
        payload,
        actor=identity.username,
        request_id=request_id,
    )
    return SuccessResponse(request_id=request_id, data=data)


@router.get("/audits", response_model=SuccessResponse[AdminOperationAuditList])
async def list_configuration_audits(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, alias="pageSize", ge=1, le=100),
    _: AdminIdentity = Depends(require_admin),
    session: AsyncSession = Depends(get_db_session),
) -> SuccessResponse[AdminOperationAuditList]:
    data = await SettingsService().list_audits(
        session,
        page=page,
        page_size=page_size,
    )
    return SuccessResponse(request_id=get_request_id(), data=data)
