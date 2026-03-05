from datetime import datetime

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.deps import AuthContext, require_roles
from app.core.roles import CompanyRole
from app.db.models import AIModelStatus, Company, Interview, Report, Score, User, UserCompanyRole
from app.db.session import get_db
from app.schemas.report import ReportRead
from app.schemas.superadmin import AIModelStatusRead, CompanyStatsRead, SuperadminOverviewRead
from app.services.ai_client import AIClient

router = APIRouter()
settings = get_settings()


async def _sync_ai_model_status(db: Session) -> list[AIModelStatus]:
    services = {
        "question": settings.ai_question_service_url or settings.ai_service_url,
        "tts": settings.ai_tts_service_url or settings.ai_service_url,
        "stt": settings.ai_stt_service_url or settings.ai_service_url,
        "analysis": settings.ai_analysis_service_url or settings.ai_service_url,
    }
    client = AIClient()
    persisted: list[AIModelStatus] = []

    for service_name, service_url in services.items():
        try:
            payload = await client.model_status(service_url)
            entries = payload.get("models", [])
            for entry in entries:
                status_row = db.scalar(
                    select(AIModelStatus).where(
                        AIModelStatus.service_name == service_name,
                        AIModelStatus.model_role == entry.get("role"),
                    )
                )
                if not status_row:
                    status_row = AIModelStatus(
                        service_name=service_name,
                        model_role=entry.get("role", "unknown"),
                        model_id=entry.get("model_id", "unknown"),
                        version=entry.get("version", "v1"),
                        is_loaded=bool(entry.get("loaded", False)),
                        ram_usage_mb=float(entry.get("ram_usage_mb", 0.0)),
                        last_error=entry.get("last_error"),
                    )
                    db.add(status_row)
                else:
                    status_row.model_id = entry.get("model_id", status_row.model_id)
                    status_row.version = entry.get("version", status_row.version)
                    status_row.is_loaded = bool(entry.get("loaded", False))
                    status_row.ram_usage_mb = float(entry.get("ram_usage_mb", 0.0))
                    status_row.last_error = entry.get("last_error")
                    status_row.updated_at = datetime.utcnow()
                persisted.append(status_row)
        except Exception as exc:  # pragma: no cover - network/runtime path
            status_row = db.scalar(
                select(AIModelStatus).where(
                    AIModelStatus.service_name == service_name,
                    AIModelStatus.model_role == "service",
                )
            )
            if not status_row:
                status_row = AIModelStatus(
                    service_name=service_name,
                    model_role="service",
                    model_id=service_url,
                    version="v1",
                    is_loaded=False,
                    ram_usage_mb=0.0,
                    last_error=str(exc),
                )
                db.add(status_row)
            else:
                status_row.is_loaded = False
                status_row.last_error = str(exc)
                status_row.ram_usage_mb = 0.0
                status_row.updated_at = datetime.utcnow()
            persisted.append(status_row)

    db.flush()
    return persisted


@router.get("/overview", response_model=SuperadminOverviewRead)
async def superadmin_overview(
    db: Session = Depends(get_db),
    _: AuthContext = Depends(require_roles(CompanyRole.SUPERADMIN)),
):
    statuses = await _sync_ai_model_status(db)
    db.commit()

    companies_count = db.scalar(select(func.count(Company.id))) or 0
    users_count = db.scalar(select(func.count(User.id))) or 0
    interviews_count = db.scalar(select(func.count(Interview.id))) or 0
    completed_interviews_count = db.scalar(select(func.count(Interview.id)).where(Interview.status == "completed")) or 0
    avg_score = db.scalar(select(func.avg(Score.overall_score))) or 0.0

    return SuperadminOverviewRead(
        companies_count=int(companies_count),
        users_count=int(users_count),
        interviews_count=int(interviews_count),
        completed_interviews_count=int(completed_interviews_count),
        avg_score=round(float(avg_score), 2),
        model_statuses=[
            AIModelStatusRead(
                service_name=status.service_name,
                model_role=status.model_role,
                model_id=status.model_id,
                version=status.version,
                is_loaded=status.is_loaded,
                ram_usage_mb=status.ram_usage_mb,
                last_error=status.last_error,
                updated_at=status.updated_at,
            )
            for status in statuses
        ],
    )


@router.get("/companies", response_model=list[CompanyStatsRead])
def superadmin_companies(
    db: Session = Depends(get_db),
    _: AuthContext = Depends(require_roles(CompanyRole.SUPERADMIN)),
):
    companies = db.scalars(select(Company).order_by(Company.created_at.desc())).all()
    items: list[CompanyStatsRead] = []
    for company in companies:
        users_count = (
            db.scalar(select(func.count(UserCompanyRole.id)).where(UserCompanyRole.company_id == company.id)) or 0
        )
        interviews_count = db.scalar(select(func.count(Interview.id)).where(Interview.company_id == company.id)) or 0
        completed = (
            db.scalar(
                select(func.count(Interview.id)).where(
                    Interview.company_id == company.id, Interview.status == "completed"
                )
            )
            or 0
        )
        items.append(
            CompanyStatsRead(
                company_id=company.id,
                company_name=company.name,
                users_count=int(users_count),
                interviews_count=int(interviews_count),
                completed_interviews_count=int(completed),
            )
        )
    return items


@router.get("/reports", response_model=list[ReportRead])
def superadmin_reports(
    db: Session = Depends(get_db),
    _: AuthContext = Depends(require_roles(CompanyRole.SUPERADMIN)),
):
    reports = db.scalars(select(Report).order_by(Report.created_at.desc()).limit(300)).all()
    return [
        ReportRead(
            id=report.id,
            company_id=report.company_id,
            interview_id=report.interview_id,
            report_type=report.report_type,
            summary=report.summary,
            content=report.content,
            created_at=report.created_at,
        )
        for report in reports
    ]


@router.get("/audit")
def superadmin_audit(
    limit: int = 200,
    db: Session = Depends(get_db),
    _: AuthContext = Depends(require_roles(CompanyRole.SUPERADMIN)),
):
    safe_limit = max(1, min(limit, 1000))
    from app.db.models import AuditLog

    logs = db.scalars(select(AuditLog).order_by(AuditLog.created_at.desc()).limit(safe_limit)).all()
    return [
        {
            "id": log.id,
            "company_id": log.company_id,
            "user_id": log.user_id,
            "action": log.action,
            "entity_type": log.entity_type,
            "entity_id": log.entity_id,
            "payload": log.payload,
            "created_at": log.created_at,
        }
        for log in logs
    ]
