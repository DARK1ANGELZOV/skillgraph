from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.deps import AuthContext, require_roles
from app.core.roles import CompanyRole
from app.db.models import Vacancy
from app.db.session import get_db
from app.schemas.candidate import VacancyCreate, VacancyRead
from app.services.audit import log_audit

router = APIRouter()


@router.post("", response_model=VacancyRead, status_code=status.HTTP_201_CREATED)
def create_vacancy(
    payload: VacancyCreate,
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
    vacancy = Vacancy(company_id=ctx.company_id, **payload.model_dump())
    db.add(vacancy)
    db.flush()
    log_audit(
        db,
        action="vacancy_created",
        entity_type="vacancy",
        entity_id=vacancy.id,
        company_id=ctx.company_id,
        user_id=ctx.user.id,
        payload={"title": vacancy.title},
    )
    db.commit()
    db.refresh(vacancy)
    return vacancy


@router.get("", response_model=list[VacancyRead])
def list_vacancies(
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
    return db.scalars(
        select(Vacancy).where(Vacancy.company_id == ctx.company_id).order_by(Vacancy.created_at.desc())
    ).all()
