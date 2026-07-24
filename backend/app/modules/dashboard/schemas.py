from datetime import datetime

from app.core.schemas import CamelModel
from app.modules.audits.schemas import AuditItem


class DashboardStats(CamelModel):
    business_requests: int
    upstream_calls: int
    total_tokens: int
    success_rate: float
    retry_count: int
    average_duration_ms: int


class DashboardData(CamelModel):
    stats: DashboardStats
    recent_requests: list[AuditItem]
    generated_at: datetime
