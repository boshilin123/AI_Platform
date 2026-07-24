from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.request_context import get_request_id
from app.core.schemas import SuccessResponse
from app.core.security import require_internal_token
from app.db.session import get_db_session
from app.modules.audits.schemas import AuditListData
from app.modules.audits.service import AuditService

router = APIRouter(prefix="/audits", tags=["调用审计"], dependencies=[Depends(require_internal_token)])


@router.get("", response_model=SuccessResponse[AuditListData])
async def list_audits(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, alias="pageSize", ge=1, le=100),
    status: str | None = Query(default=None),
    capability_code: str | None = Query(default=None, alias="capabilityCode"),
    request_id: str | None = Query(default=None, alias="requestId"),
    session: AsyncSession = Depends(get_db_session),
) -> SuccessResponse[AuditListData]:
    data = await AuditService().list(
        session,
        page=page,
        page_size=page_size,
        status=status,
        capability_code=capability_code,
        request_id=request_id,
    )
    return SuccessResponse(request_id=get_request_id(), data=data)


@router.get("/export")
async def export_audits(
    status: str | None = Query(default=None),
    capability_code: str | None = Query(default=None, alias="capabilityCode"),
    session: AsyncSession = Depends(get_db_session),
) -> Response:
    content = await AuditService().export_csv(
        session, status=status, capability_code=capability_code
    )
    return Response(
        content="\ufeff" + content,
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": 'attachment; filename="ai-audits.csv"'},
    )
