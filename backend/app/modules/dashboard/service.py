from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.audits.repository import AuditRepository
from app.modules.audits.service import AuditService
from app.modules.dashboard.schemas import DashboardData, DashboardStats


class DashboardService:
    def __init__(self) -> None:
        self.repository = AuditRepository()
        self.audit_service = AuditService(self.repository)

    async def overview(self, session: AsyncSession) -> DashboardData:
        now = datetime.now(timezone.utc)
        today = now.replace(hour=0, minute=0, second=0, microsecond=0)
        summary = await self.repository.summary_since(session, today)
        rows, _ = await self.repository.list(session, page=1, page_size=5)
        request_count = int(summary["request_count"])
        success_count = int(summary["success_count"])
        duration_total = int(summary["duration_total"])
        return DashboardData(
            stats=DashboardStats(
                business_requests=request_count,
                upstream_calls=int(summary["upstream_call_count"]),
                total_tokens=int(summary["total_tokens"]),
                success_rate=round(success_count * 100 / request_count, 2) if request_count else 100.0,
                retry_count=int(summary["retry_count"]),
                average_duration_ms=round(duration_total / request_count) if request_count else 0,
            ),
            recent_requests=[self.audit_service._to_item(row) for row in rows],
            generated_at=now,
        )
