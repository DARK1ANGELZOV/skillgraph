from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.deps import AuthContext, require_roles
from app.core.roles import CompanyRole
from app.db.models import AuditLog, Interview, Test, TestResult
from app.db.session import get_db
from app.schemas.interview import CustomTestCreateRequest
from app.services.interview import create_custom_test

router = APIRouter()


@router.get("/interview/{interview_id}")
def list_test_results_for_interview(
    interview_id: str,
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
    interview = db.scalar(
        select(Interview).where(Interview.id == interview_id, Interview.company_id == ctx.company_id)
    )
    if not interview:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Interview not found")

    tests = db.scalars(select(Test).where(Test.interview_id == interview.id)).all()
    results = db.scalars(select(TestResult).where(TestResult.interview_id == interview.id)).all()
    tests_by_id = {test.id: test for test in tests}

    return [
        {
            "id": result.id,
            "test_id": result.test_id,
            "category": tests_by_id[result.test_id].category if result.test_id in tests_by_id else "unknown",
            "title": tests_by_id[result.test_id].title if result.test_id in tests_by_id else "unknown",
            "raw_score": result.raw_score,
            "normalized_score": result.normalized_score,
            "analysis_summary": result.ai_analysis.get("rationale", {}).get("summary"),
            "created_at": result.created_at,
        }
        for result in results
    ]


@router.get("/interview/{interview_id}/definitions")
def list_test_definitions_for_interview(
    interview_id: str,
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
    interview = db.scalar(
        select(Interview).where(Interview.id == interview_id, Interview.company_id == ctx.company_id)
    )
    if not interview:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Interview not found")

    tests = db.scalars(select(Test).where(Test.interview_id == interview.id).order_by(Test.created_at.asc())).all()
    return [
        {
            "id": test.id,
            "title": test.title,
            "category": test.category,
            "duration_sec": test.duration_sec,
            "questions_count": len(test.questions),
            "questions": [{"id": q["id"], "text": q["text"], "options": q["options"]} for q in test.questions],
            "created_at": test.created_at,
        }
        for test in tests
    ]


@router.post("/interview/{interview_id}/custom", status_code=status.HTTP_201_CREATED)
def create_custom_test_for_interview(
    interview_id: str,
    payload: CustomTestCreateRequest,
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
    interview = db.scalar(
        select(Interview).where(Interview.id == interview_id, Interview.company_id == ctx.company_id)
    )
    if not interview:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Interview not found")

    try:
        test = create_custom_test(
            db,
            interview=interview,
            title=payload.title,
            category=payload.category,
            duration_sec=payload.duration_sec,
            questions=[item.model_dump() for item in payload.questions],
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc

    db.add(
        AuditLog(
            company_id=ctx.company_id,
            user_id=ctx.user.id,
            action="custom_test_created",
            entity_type="test",
            entity_id=test.id,
            payload={"interview_id": interview.id, "title": test.title, "category": test.category},
        )
    )
    db.commit()
    return {
        "id": test.id,
        "title": test.title,
        "category": test.category,
        "duration_sec": test.duration_sec,
        "questions_count": len(test.questions),
    }
