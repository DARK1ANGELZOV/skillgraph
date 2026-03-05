from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.models import Interview, Score


def build_executive_summary(db: Session, company_id: str) -> dict:
    total = db.scalar(select(func.count(Interview.id)).where(Interview.company_id == company_id)) or 0
    completed = (
        db.scalar(
            select(func.count(Interview.id)).where(
                Interview.company_id == company_id,
                Interview.status == "completed",
            )
        )
        or 0
    )
    avg_score = (
        db.scalar(
            select(func.avg(Score.overall_score)).join(Interview, Interview.id == Score.interview_id).where(
                Interview.company_id == company_id
            )
        )
        or 0.0
    )
    recommended_count = (
        db.scalar(
            select(func.count(Score.id))
            .join(Interview, Interview.id == Score.interview_id)
            .where(Interview.company_id == company_id, Score.recommendation == "recommended")
        )
        or 0
    )
    conditional_count = (
        db.scalar(
            select(func.count(Score.id))
            .join(Interview, Interview.id == Score.interview_id)
            .where(Interview.company_id == company_id, Score.recommendation == "recommended_with_conditions")
        )
        or 0
    )
    rejected_count = (
        db.scalar(
            select(func.count(Score.id))
            .join(Interview, Interview.id == Score.interview_id)
            .where(Interview.company_id == company_id, Score.recommendation == "not_recommended")
        )
        or 0
    )

    top_strength = (
        db.scalar(
            select(func.avg(Score.soft_skills_score)).join(Interview, Interview.id == Score.interview_id).where(
                Interview.company_id == company_id
            )
        )
        or 0.0
    )
    top_risk = (
        db.scalar(
            select(func.avg(Score.nervousness_score)).join(Interview, Interview.id == Score.interview_id).where(
                Interview.company_id == company_id
            )
        )
        or 0.0
    )

    return {
        "total_interviews": int(total),
        "completed_interviews": int(completed),
        "avg_score": round(float(avg_score), 2),
        "recommended_count": int(recommended_count),
        "conditional_count": int(conditional_count),
        "rejected_count": int(rejected_count),
        "top_strength": f"Soft skills avg {round(float(top_strength), 1)}",
        "top_risk": f"Nervousness avg {round(float(top_risk), 1)}",
    }
