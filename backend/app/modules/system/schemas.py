from app.core.schemas import CamelModel


class HealthData(CamelModel):
    status: str
    service: str
    environment: str
    database: str
    llm_mode: str
