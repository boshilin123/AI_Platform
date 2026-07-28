from __future__ import annotations

from dataclasses import asdict, dataclass

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import AdminOperationAudit, RuntimeLlmConfiguration, utc_now


@dataclass(frozen=True, slots=True)
class AdminOperationAuditWrite:
    request_id: str
    actor: str
    action: str
    status: str
    http_status: int
    error_code: str | None
    duration_ms: int
    old_base_url: str | None = None
    new_base_url: str | None = None
    old_model: str | None = None
    new_model: str | None = None


class SettingsRepository:
    async def get_runtime_configuration(
        self,
        session: AsyncSession,
        *,
        for_update: bool = False,
    ) -> RuntimeLlmConfiguration | None:
        statement = select(RuntimeLlmConfiguration).where(RuntimeLlmConfiguration.id == 1)
        if for_update:
            statement = statement.with_for_update()
        return await session.scalar(statement)

    async def save_runtime_configuration(
        self,
        session: AsyncSession,
        *,
        base_url: str,
        model: str,
        actor: str,
        audit: AdminOperationAuditWrite,
    ) -> RuntimeLlmConfiguration:
        row = await self.get_runtime_configuration(session, for_update=True)
        if row is None:
            row = RuntimeLlmConfiguration(
                id=1,
                base_url=base_url,
                model=model,
                updated_by=actor,
                updated_at=utc_now(),
            )
            session.add(row)
        else:
            row.base_url = base_url
            row.model = model
            row.updated_by = actor
            row.updated_at = utc_now()
        session.add(AdminOperationAudit(**asdict(audit)))
        await session.commit()
        await session.refresh(row)
        return row

    async def record_operation(
        self,
        session: AsyncSession,
        payload: AdminOperationAuditWrite,
    ) -> None:
        session.add(AdminOperationAudit(**asdict(payload)))
        await session.commit()

    async def list_operation_audits(
        self,
        session: AsyncSession,
        *,
        page: int,
        page_size: int,
    ) -> tuple[list[AdminOperationAudit], int]:
        total = int((await session.scalar(select(func.count(AdminOperationAudit.id)))) or 0)
        rows = (
            await session.scalars(
                select(AdminOperationAudit)
                .order_by(AdminOperationAudit.created_at.desc(), AdminOperationAudit.id.desc())
                .offset((page - 1) * page_size)
                .limit(page_size)
            )
        ).all()
        return list(rows), total
