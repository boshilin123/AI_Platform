from __future__ import annotations

import csv
import io
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import AiRequestAudit
from app.modules.audits.repository import AuditRepository, AuditWrite
from app.modules.audits.schemas import AuditItem, AuditListData


def as_utc(value: datetime) -> datetime:
    """Restore UTC information that MySQL DATETIME does not preserve."""
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


class AuditService:
    def __init__(self, repository: AuditRepository | None = None) -> None:
        self.repository = repository or AuditRepository()

    async def record(self, session: AsyncSession, payload: AuditWrite) -> None:
        await self.repository.create(session, payload)

    async def list(
        self,
        session: AsyncSession,
        *,
        page: int,
        page_size: int,
        status: str | None,
        capability_code: str | None,
        request_id: str | None,
    ) -> AuditListData:
        rows, total = await self.repository.list(
            session,
            page=page,
            page_size=page_size,
            status=status,
            capability_code=capability_code,
            request_id=request_id,
        )
        return AuditListData(
            items=[self._to_item(row) for row in rows],
            page=page,
            page_size=page_size,
            total=total,
        )

    async def export_csv(
        self,
        session: AsyncSession,
        *,
        status: str | None,
        capability_code: str | None,
    ) -> str:
        rows = await self.repository.list_for_export(
            session, status=status, capability_code=capability_code
        )
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(
            [
                "Request ID",
                "业务",
                "能力",
                "调用方",
                "状态",
                "错误码",
                "上游调用",
                "重试",
                "Token",
                "耗时(ms)",
                "时间",
            ]
        )
        for row in rows:
            writer.writerow(
                [
                    row.request_id,
                    row.business_code,
                    row.capability_code,
                    row.caller_system,
                    row.status,
                    row.error_code or "",
                    row.upstream_call_count,
                    row.retry_count,
                    row.total_tokens,
                    row.duration_ms,
                    as_utc(row.created_at).isoformat(),
                ]
            )
        return output.getvalue()

    @staticmethod
    def _to_item(row: AiRequestAudit) -> AuditItem:
        return AuditItem(
            request_id=row.request_id,
            business_code=row.business_code,
            capability_code=row.capability_code,
            caller_system=row.caller_system,
            interface_path=row.interface_path,
            request_mode=row.request_mode,
            model=row.model,
            status=row.status,
            http_status=row.http_status,
            error_code=row.error_code,
            retry_count=row.retry_count,
            upstream_call_count=row.upstream_call_count,
            prompt_tokens=row.prompt_tokens,
            completion_tokens=row.completion_tokens,
            total_tokens=row.total_tokens,
            duration_ms=row.duration_ms,
            prompt_version=row.prompt_version,
            created_at=as_utc(row.created_at),
        )
