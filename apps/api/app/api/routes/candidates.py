import secrets

from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.deps import AuthContext, require_roles
from app.core.roles import CompanyRole
from app.db.models import Candidate, Interview
from app.db.session import get_db
from app.schemas.candidate import CandidateInviteRequest, CandidateRead
from app.services.audit import log_audit

router = APIRouter()
settings = get_settings()


def _candidate_payload(candidate: Candidate, interview_id: str | None) -> CandidateRead:
    base_url = str(settings.frontend_admin_url).rstrip("/")
    interview_link = f"{base_url}/interview/{candidate.magic_link_token}"
    tests_link = f"{base_url}/interview/{candidate.magic_link_token}?mode=tests"
    return CandidateRead(
        id=candidate.id,
        full_name=candidate.full_name,
        email=candidate.email,
        status=candidate.status,
        vacancy_id=candidate.vacancy_id,
        experience_years=candidate.experience_years,
        skills=candidate.skills,
        education=candidate.education,
        magic_link_token=candidate.magic_link_token,
        interview_id=interview_id,
        interview_link=interview_link,
        tests_link=tests_link,
        created_at=candidate.created_at,
    )


@router.post("/magic-link", response_model=CandidateRead, status_code=status.HTTP_201_CREATED)
def create_magic_link(
    payload: CandidateInviteRequest,
    db: Session = Depends(get_db),
    ctx: AuthContext = Depends(
        require_roles(
            CompanyRole.OWNER,
            CompanyRole.HR_SENIOR,
            CompanyRole.HR_JUNIOR,
            CompanyRole.SUPERADMIN,
        )
    ),
):
    candidate = Candidate(
        company_id=ctx.company_id,
        vacancy_id=payload.vacancy_id,
        full_name=payload.full_name,
        email=payload.email.lower(),
        experience_years=payload.experience_years,
        skills=payload.skills,
        education=payload.education,
        magic_link_token=secrets.token_urlsafe(32),
        status="invited",
    )
    db.add(candidate)
    db.flush()

    interview = Interview(company_id=ctx.company_id, candidate_id=candidate.id, status="pending")
    db.add(interview)

    log_audit(
        db,
        action="candidate_magic_link_created",
        entity_type="candidate",
        entity_id=candidate.id,
        company_id=ctx.company_id,
        user_id=ctx.user.id,
        payload={"email": candidate.email},
    )
    db.commit()
    db.refresh(candidate)
    return _candidate_payload(candidate, interview.id)


@router.get("", response_model=list[CandidateRead])
def list_candidates(
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
    candidates = db.scalars(
        select(Candidate).where(Candidate.company_id == ctx.company_id).order_by(Candidate.created_at.desc())
    ).all()
    interviews = db.scalars(select(Interview).where(Interview.company_id == ctx.company_id)).all()
    interviews_by_candidate = {item.candidate_id: item.id for item in interviews}
    return [_candidate_payload(candidate, interviews_by_candidate.get(candidate.id)) for candidate in candidates]
