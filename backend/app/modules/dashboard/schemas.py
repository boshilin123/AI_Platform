from datetime import date, datetime

from app.core.schemas import CamelModel
from app.modules.audits.schemas import AuditItem


class DashboardStats(CamelModel):
    business_requests: int
    upstream_calls: int
    total_tokens: int
    success_rate: float
    retry_count: int
    average_duration_ms: int


class UsageTrendPoint(CamelModel):
    date: date
    request_count: int


class DashboardData(CamelModel):
    stats: DashboardStats
    usage_trend: list[UsageTrendPoint]
    recent_requests: list[AuditItem]
    generated_at: datetime
