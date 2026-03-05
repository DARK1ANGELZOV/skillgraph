from datetime import datetime

from pydantic import BaseModel


class CompanyStatsRead(BaseModel):
    company_id: str
    company_name: str
    users_count: int
    interviews_count: int
    completed_interviews_count: int


class AIModelStatusRead(BaseModel):
    service_name: str
    model_role: str
    model_id: str
    version: str
    is_loaded: bool
    ram_usage_mb: float
    last_error: str | None
    updated_at: datetime | None = None


class SuperadminOverviewRead(BaseModel):
    companies_count: int
    users_count: int
    interviews_count: int
    completed_interviews_count: int
    avg_score: float
    model_statuses: list[AIModelStatusRead]
