from datetime import datetime

from pydantic import BaseModel


class ReportRead(BaseModel):
    id: str
    company_id: str | None = None
    interview_id: str | None = None
    report_type: str
    summary: str
    content: dict
    created_at: datetime


class ExecutiveSummary(BaseModel):
    total_interviews: int
    completed_interviews: int
    avg_score: float
    recommended_count: int
    conditional_count: int
    rejected_count: int
    top_strength: str
    top_risk: str
