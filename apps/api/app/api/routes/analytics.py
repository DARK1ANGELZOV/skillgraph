from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.deps import AuthContext, require_roles
from app.core.roles import CompanyRole
from app.db.models import Report
from app.db.session import get_db
from app.schemas.report import ExecutiveSummary, ReportRead
from app.services.analytics import build_executive_summary

router = APIRouter()


@router.get("/reports", response_model=list[ReportRead])
def list_reports(
    db: Session = Depends(get_db),
    ctx: AuthContext = Depends(
        require_roles(
            CompanyRole.OWNER,
            CompanyRole.HR_SENIOR,
            CompanyRole.HR_JUNIOR,
            CompanyRole.SUPERVISOR,
            CompanyRole.SUPERADMIN,
        )
    ),
):
    reports = db.scalars(
        select(Report).where(Report.company_id == ctx.company_id).order_by(Report.created_at.desc())
    ).all()
    return [
        ReportRead(
            id=rep.id,
            company_id=rep.company_id,
            interview_id=rep.interview_id,
            report_type=rep.report_type,
            summary=rep.summary,
            content=rep.content,
            created_at=rep.created_at,
        )
        for rep in reports
    ]


@router.get("/executive-summary", response_model=ExecutiveSummary)
def executive_summary(
    db: Session = Depends(get_db),
    ctx: AuthContext = Depends(
        require_roles(
            CompanyRole.OWNER,
            CompanyRole.HR_SENIOR,
            CompanyRole.SUPERVISOR,
            CompanyRole.SUPERADMIN,
        )
    ),
):
    summary = build_executive_summary(db, ctx.company_id)
    return ExecutiveSummary(**summary)
