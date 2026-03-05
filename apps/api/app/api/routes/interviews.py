from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.deps import AuthContext, require_roles
from app.core.roles import CompanyRole
from app.db.models import Answer, AuditLog, Candidate, Interview, Question, Score, Test, TestResult, Vacancy
from app.db.session import get_db
from app.schemas.interview import (
    AnswerSubmit,
    AntiCheatEventCreate,
    InterviewAdminRead,
    InterviewPublicRead,
    QuestionRead,
    STTRequest,
    STTResponse,
    ScoreRead,
    TestRead,
    TestResultRead,
    TestSubmitRequest,
)
from app.services.ai_client import AIClient
from app.services.interview import (
    candidate_tests_payload,
    ensure_questions,
    evaluate_test_submission,
    finalize_interview,
    store_answer,
)

router = APIRouter()


class TTSRequest(BaseModel):
    speech_rate: float = Field(default=1.0, ge=0.75, le=1.35)


def _resolve_public_interview(db: Session, token: str) -> tuple[Candidate, Interview]:
    candidate = db.scalar(select(Candidate).where(Candidate.magic_link_token == token))
    if not candidate:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Interview link not found")

    interview = db.scalar(select(Interview).where(Interview.candidate_id == candidate.id))
    if not interview:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Interview not found")
    return candidate, interview


@router.get("/public/{token}", response_model=InterviewPublicRead)
async def get_public_interview(token: str, db: Session = Depends(get_db)):
    candidate, interview = _resolve_public_interview(db, token)
    vacancy = db.get(Vacancy, candidate.vacancy_id) if candidate.vacancy_id else None
    questions = await ensure_questions(
        db,
        interview=interview,
        job_title=vacancy.title if vacancy else "Generalist",
        requirements=vacancy.requirements if vacancy else "General communication and analytical ability",
        seniority=vacancy.seniority if vacancy else "middle",
    )
    db.commit()

    return InterviewPublicRead(
        interview_id=interview.id,
        candidate_name=candidate.full_name,
        status=interview.status,
        questions=[
            QuestionRead(
                id=q.id,
                order_index=q.order_index,
                text=q.text,
                prompt_version=q.prompt_version,
                question_type=q.question_type,
                time_limit_sec=q.time_limit_sec,
                audio_base64=q.audio_base64,
            )
            for q in sorted(questions, key=lambda item: item.order_index)
        ],
    )


@router.get("/public/{token}/tests", response_model=list[TestRead])
def get_public_tests(token: str, db: Session = Depends(get_db)):
    _, interview = _resolve_public_interview(db, token)
    payload = candidate_tests_payload(db, interview=interview)
    db.commit()
    return payload


@router.post("/public/{token}/tests/{test_id}/submit", response_model=TestResultRead)
async def submit_public_test(
    token: str,
    test_id: str,
    payload: TestSubmitRequest,
    db: Session = Depends(get_db),
):
    _, interview = _resolve_public_interview(db, token)
    test = db.scalar(select(Test).where(Test.id == test_id, Test.interview_id == interview.id))
    if not test:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Test not found")

    result = await evaluate_test_submission(
        db,
        interview=interview,
        test=test,
        submitted_answers=[answer.model_dump() for answer in payload.answers],
    )
    db.commit()
    return TestResultRead(
        test_id=result.test_id,
        category=test.category,
        raw_score=result.raw_score,
        normalized_score=result.normalized_score,
        ai_analysis=result.ai_analysis,
    )


@router.post("/public/{token}/stt", response_model=STTResponse)
async def transcribe_public_audio(token: str, payload: STTRequest, db: Session = Depends(get_db)):
    _resolve_public_interview(db, token)
    client = AIClient()
    result = await client.stt(payload.audio_base64, language=payload.language)
    return STTResponse(
        text=result.get("text", ""),
        confidence=float(result.get("confidence", 0.0)),
        pause_ratio=float(result.get("pause_ratio", 0.0)),
        filler_ratio=float(result.get("filler_ratio", 0.0)),
        instability_score=float(result.get("instability_score", 0.0)),
    )


@router.post("/public/{token}/events", status_code=status.HTTP_201_CREATED)
def register_public_event(token: str, payload: AntiCheatEventCreate, db: Session = Depends(get_db)):
    _, interview = _resolve_public_interview(db, token)
    db.add(
        AuditLog(
            company_id=interview.company_id,
            user_id=None,
            action=f"candidate_{payload.event_type}",
            entity_type="interview",
            entity_id=interview.id,
            payload={"severity": payload.severity, "question_id": payload.question_id, "details": payload.details},
        )
    )
    if payload.severity in {"medium", "high"}:
        interview.suspicious_events_count += 1
    db.commit()
    return {"status": "logged"}


@router.post("/public/{token}/answers", status_code=status.HTTP_201_CREATED)
async def submit_public_answer(token: str, payload: AnswerSubmit, db: Session = Depends(get_db)):
    candidate, interview = _resolve_public_interview(db, token)
    question = db.get(Question, payload.question_id)
    if not question or question.interview_id != interview.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Question not found")

    answer = await store_answer(
        db,
        interview=interview,
        question_id=payload.question_id,
        answer_text=payload.text,
        duration_sec=payload.duration_sec,
        source_type=payload.source_type,
        stt_confidence=payload.stt_confidence,
        speech_pause_ratio=payload.speech_pause_ratio,
        filler_word_ratio=payload.filler_word_ratio,
        instability_score=payload.instability_score,
    )
    candidate.status = "in_progress"
    db.commit()
    return {
        "answer_id": answer.id,
        "sentiment": answer.sentiment_label,
        "score": answer.sentiment_score,
        "flags": answer.anti_cheat_flags,
    }


@router.post("/public/{token}/questions/{question_id}/tts")
async def get_question_tts(token: str, question_id: str, payload: TTSRequest, db: Session = Depends(get_db)):
    _, interview = _resolve_public_interview(db, token)
    question = db.get(Question, question_id)
    if not question or question.interview_id != interview.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Question not found")

    if question.audio_base64 and payload.speech_rate == 1.0:
        return {"audio_base64": question.audio_base64}

    client = AIClient()
    tts = await client.tts(question.text, speech_rate=payload.speech_rate)
    if payload.speech_rate == 1.0:
        question.audio_base64 = tts.get("audio_base64")
    db.commit()
    return {"audio_base64": tts.get("audio_base64")}


@router.post("/public/{token}/complete", response_model=ScoreRead)
async def complete_public_interview(token: str, db: Session = Depends(get_db)):
    candidate, interview = _resolve_public_interview(db, token)
    tests = db.scalars(select(Test).where(Test.interview_id == interview.id)).all()
    if not tests:
        candidate_tests_payload(db, interview=interview)
        tests = db.scalars(select(Test).where(Test.interview_id == interview.id)).all()

    results_count = db.scalar(select(func.count(TestResult.id)).where(TestResult.interview_id == interview.id)) or 0
    if int(results_count) < len(tests):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="All candidate tests must be completed before final submission",
        )

    vacancy = db.get(Vacancy, candidate.vacancy_id) if candidate.vacancy_id else None
    requirements = vacancy.requirements if vacancy else "Generalist competencies"

    score = await finalize_interview(db, interview=interview, requirements=requirements)
    candidate.status = "completed"
    db.commit()

    return ScoreRead(
        technical_score=score.technical_score,
        communication_score=score.communication_score,
        culture_score=score.culture_score,
        soft_skills_score=score.soft_skills_score,
        logic_score=score.logic_score,
        psychological_stability_score=score.psychological_stability_score,
        nervousness_score=score.nervousness_score,
        overall_score=score.overall_score,
        recommendation=score.recommendation,
        risk_level=score.risk_level,
        rationale=score.rationale,
        model_version=score.model_version,
    )


@router.get("", response_model=list[InterviewAdminRead])
def list_interviews(
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
    interviews = db.scalars(
        select(Interview).where(Interview.company_id == ctx.company_id).order_by(Interview.created_at.desc())
    ).all()
    items = []
    for interview in interviews:
        items.append(
            InterviewAdminRead(
                id=interview.id,
                candidate_id=interview.candidate_id,
                status=interview.status,
                started_at=interview.started_at,
                completed_at=interview.completed_at,
                score=(
                    ScoreRead(
                        technical_score=interview.score.technical_score,
                        communication_score=interview.score.communication_score,
                        culture_score=interview.score.culture_score,
                        soft_skills_score=interview.score.soft_skills_score,
                        logic_score=interview.score.logic_score,
                        psychological_stability_score=interview.score.psychological_stability_score,
                        nervousness_score=interview.score.nervousness_score,
                        overall_score=interview.score.overall_score,
                        recommendation=interview.score.recommendation,
                        risk_level=interview.score.risk_level,
                        rationale=interview.score.rationale,
                        model_version=interview.score.model_version,
                    )
                    if interview.score
                    else None
                ),
            )
        )
    return items


@router.get("/{interview_id}")
def get_interview_detail(
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

    candidate = db.get(Candidate, interview.candidate_id)
    answers = db.scalars(select(Answer).where(Answer.interview_id == interview.id)).all()
    questions = db.scalars(
        select(Question).where(Question.interview_id == interview.id).order_by(Question.order_index.asc())
    ).all()
    tests = db.scalars(select(Test).where(Test.interview_id == interview.id)).all()

    return {
        "id": interview.id,
        "candidate": {
            "id": candidate.id,
            "full_name": candidate.full_name,
            "email": candidate.email,
            "experience_years": candidate.experience_years,
            "skills": candidate.skills,
            "education": candidate.education,
            "magic_link_token": candidate.magic_link_token,
        }
        if candidate
        else None,
        "status": interview.status,
        "started_at": interview.started_at,
        "completed_at": interview.completed_at,
        "suspicious_events_count": interview.suspicious_events_count,
        "questions": [
            {
                "id": q.id,
                "order_index": q.order_index,
                "text": q.text,
                "prompt_version": q.prompt_version,
                "question_type": q.question_type,
                "time_limit_sec": q.time_limit_sec,
            }
            for q in questions
        ],
        "answers": [
            {
                "id": a.id,
                "question_id": a.question_id,
                "text": a.text,
                "sentiment_label": a.sentiment_label,
                "sentiment_score": a.sentiment_score,
                "duration_sec": a.duration_sec,
                "source_type": a.source_type,
                "anti_cheat_flags": a.anti_cheat_flags,
                "speech_pause_ratio": a.speech_pause_ratio,
                "filler_word_ratio": a.filler_word_ratio,
                "instability_score": a.instability_score,
            }
            for a in answers
        ],
        "tests": [
            {
                "id": test.id,
                "category": test.category,
                "title": test.title,
                "duration_sec": test.duration_sec,
            }
            for test in tests
        ],
        "score": (
            {
                "technical_score": interview.score.technical_score,
                "communication_score": interview.score.communication_score,
                "culture_score": interview.score.culture_score,
                "soft_skills_score": interview.score.soft_skills_score,
                "logic_score": interview.score.logic_score,
                "psychological_stability_score": interview.score.psychological_stability_score,
                "nervousness_score": interview.score.nervousness_score,
                "overall_score": interview.score.overall_score,
                "recommendation": interview.score.recommendation,
                "risk_level": interview.score.risk_level,
                "rationale": interview.score.rationale,
                "model_version": interview.score.model_version,
            }
            if interview.score
            else None
        ),
    }
