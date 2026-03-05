from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.deps import AuthContext, require_roles
from app.core.roles import CompanyRole
from app.db.models import Candidate, Company, Interview, UserCompanyRole
from app.db.session import get_db
from app.schemas.company import CompanyRead, CompanyUpdate
from app.services.audit import log_audit

router = APIRouter()


@router.get("/current", response_model=CompanyRead)
def get_current_company(
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
    company = db.get(Company, ctx.company_id)
    if not company:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found")
    return company


@router.put("/current", response_model=CompanyRead)
def update_company(
    payload: CompanyUpdate,
    db: Session = Depends(get_db),
    ctx: AuthContext = Depends(require_roles(CompanyRole.OWNER, CompanyRole.SUPERADMIN)),
):
    company = db.scalar(select(Company).where(Company.id == ctx.company_id))
    if not company:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found")

    company.name = payload.name
    log_audit(
        db,
        action="company_updated",
        entity_type="company",
        entity_id=company.id,
        company_id=ctx.company_id,
        user_id=ctx.user.id,
        payload={"name": payload.name},
    )
    db.commit()
    return company


@router.get("/billing")
def billing_stub(
    db: Session = Depends(get_db),
    ctx: AuthContext = Depends(require_roles(CompanyRole.OWNER, CompanyRole.SUPERADMIN)),
):
    members = db.scalar(select(func.count(UserCompanyRole.id)).where(UserCompanyRole.company_id == ctx.company_id)) or 0
    candidates = db.scalar(select(func.count(Candidate.id)).where(Candidate.company_id == ctx.company_id)) or 0
    interviews = db.scalar(select(func.count(Interview.id)).where(Interview.company_id == ctx.company_id)) or 0
    completed = (
        db.scalar(
            select(func.count(Interview.id)).where(
                Interview.company_id == ctx.company_id,
                Interview.status == "completed",
            )
        )
        or 0
    )

    base_price = 199.0
    usage_price = completed * 2.5 + max(0, members - 3) * 12.0
    projected_total = round(base_price + usage_price, 2)

    return {
        "company_id": ctx.company_id,
        "plan": "enterprise",
        "status": "active",
        "renewal_date": "2026-12-31",
        "usage": {
            "members": int(members),
            "candidates": int(candidates),
            "interviews_total": int(interviews),
            "interviews_completed": int(completed),
        },
        "pricing": {
            "base_monthly_usd": base_price,
            "completed_interview_unit_usd": 2.5,
            "extra_member_unit_usd": 12.0,
            "projected_monthly_total_usd": projected_total,
        },
    }
