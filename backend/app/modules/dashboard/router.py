from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.request_context import get_request_id
from app.core.schemas import SuccessResponse
from app.core.security import require_internal_token
from app.db.session import get_db_session
from app.modules.dashboard.schemas import DashboardData
from app.modules.dashboard.service import DashboardService

router = APIRouter(
    prefix="/dashboard",
    tags=["工作台"],
    dependencies=[Depends(require_internal_token)],
)


@router.get("/overview", response_model=SuccessResponse[DashboardData])
async def overview(session: AsyncSession = Depends(get_db_session)) -> SuccessResponse[DashboardData]:
    data = await DashboardService().overview(session)
    return SuccessResponse(request_id=get_request_id(), data=data)
