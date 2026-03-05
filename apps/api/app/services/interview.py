from __future__ import annotations

from datetime import UTC, datetime
import math
import re
from statistics import mean
import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import (
    Answer,
    AuditLog,
    Candidate,
    Embedding,
    Interview,
    Question,
    Report,
    Score,
    Test,
    TestResult,
    Vacancy,
)
from app.services.ai_client import AIClient

_TEMPLATE_PATTERNS = [
    re.compile(r"\bas an ai\b", re.IGNORECASE),
    re.compile(r"\bin conclusion\b", re.IGNORECASE),
    re.compile(r"\bbest practices\b", re.IGNORECASE),
    re.compile(r"\blet me elaborate\b", re.IGNORECASE),
]

TEST_BLUEPRINTS = [
    {
        "category": "python",
        "title": "Python Technical Assessment",
        "duration_sec": 600,
        "questions": [
            {
                "id": "py_1",
                "text": "What is the most memory-efficient way to iterate large files line by line?",
                "options": ["read()", "readlines()", "for line in file", "json.load(file)"],
                "correct_index": 2,
            },
            {
                "id": "py_2",
                "text": "Which structure gives O(1) average lookup for unique values?",
                "options": ["list", "tuple", "set", "deque"],
                "correct_index": 2,
            },
            {
                "id": "py_3",
                "text": "Which statement about async/await in Python is accurate?",
                "options": [
                    "It makes CPU-heavy code faster by default",
                    "It improves throughput for I/O-bound tasks",
                    "It replaces threads in all workloads",
                    "It cannot be used with web frameworks",
                ],
                "correct_index": 1,
            },
        ],
    },
    {
        "category": "javascript",
        "title": "JavaScript Technical Assessment",
        "duration_sec": 600,
        "questions": [
            {
                "id": "js_1",
                "text": "What is the main advantage of event loop concurrency in JS?",
                "options": [
                    "Parallel CPU execution",
                    "Non-blocking I/O orchestration",
                    "Native multithreading in every function",
                    "Automatic DB transactions",
                ],
                "correct_index": 1,
            },
            {
                "id": "js_2",
                "text": "Which method creates a shallow copy of an array?",
                "options": ["splice()", "map()", "slice()", "pop()"],
                "correct_index": 2,
            },
            {
                "id": "js_3",
                "text": "What is true about closures?",
                "options": [
                    "They only work in strict mode",
                    "They retain access to lexical scope",
                    "They cannot be used in callbacks",
                    "They require classes",
                ],
                "correct_index": 1,
            },
        ],
    },
    {
        "category": "sql",
        "title": "SQL Technical Assessment",
        "duration_sec": 600,
        "questions": [
            {
                "id": "sql_1",
                "text": "Which clause filters grouped rows after aggregation?",
                "options": ["WHERE", "ORDER BY", "HAVING", "LIMIT"],
                "correct_index": 2,
            },
            {
                "id": "sql_2",
                "text": "Which join returns unmatched rows from both tables?",
                "options": ["INNER JOIN", "LEFT JOIN", "FULL OUTER JOIN", "CROSS JOIN"],
                "correct_index": 2,
            },
            {
                "id": "sql_3",
                "text": "Best index strategy for frequent lookups by email column is:",
                "options": ["No index", "B-tree on email", "Hash index on id", "GIN on timestamp"],
                "correct_index": 1,
            },
        ],
    },
    {
        "category": "algorithms",
        "title": "Algorithms Assessment",
        "duration_sec": 600,
        "questions": [
            {
                "id": "algo_1",
                "text": "Average complexity of binary search is:",
                "options": ["O(n)", "O(log n)", "O(n log n)", "O(1)"],
                "correct_index": 1,
            },
            {
                "id": "algo_2",
                "text": "Which structure is optimal for BFS traversal?",
                "options": ["Stack", "Queue", "Heap", "TreeSet"],
                "correct_index": 1,
            },
            {
                "id": "algo_3",
                "text": "Dynamic programming is most useful when:",
                "options": [
                    "Subproblems overlap",
                    "Input is sorted",
                    "You need randomization",
                    "Graph is acyclic only",
                ],
                "correct_index": 0,
            },
        ],
    },
    {
        "category": "soft_skills",
        "title": "Soft Skills Assessment",
        "duration_sec": 480,
        "questions": [
            {
                "id": "soft_1",
                "text": "A critical release is delayed. Your first action is:",
                "options": [
                    "Hide the issue until fix is ready",
                    "Escalate with impact, options, and ETA",
                    "Blame another team",
                    "Silence notifications",
                ],
                "correct_index": 1,
            },
            {
                "id": "soft_2",
                "text": "How do you handle disagreement on architecture?",
                "options": [
                    "Argue until others accept",
                    "Document tradeoffs and align on decision criteria",
                    "Avoid discussion",
                    "Escalate immediately without context",
                ],
                "correct_index": 1,
            },
            {
                "id": "soft_3",
                "text": "When mentoring junior engineers, you should:",
                "options": [
                    "Give tasks without feedback",
                    "Pair on problems and provide concrete feedback loops",
                    "Avoid code reviews",
                    "Only communicate through tickets",
                ],
                "correct_index": 1,
            },
        ],
    },
    {
        "category": "psychology",
        "title": "Psychological Stability Assessment",
        "duration_sec": 480,
        "questions": [
            {
                "id": "psy_1",
                "text": "Under sustained pressure, you typically:",
                "options": [
                    "Lose structure and stop communicating",
                    "Prioritize, communicate, and seek support early",
                    "Ignore deadlines",
                    "Work in isolation and hide blockers",
                ],
                "correct_index": 1,
            },
            {
                "id": "psy_2",
                "text": "After production incident, best response is:",
                "options": [
                    "Avoid retrospective",
                    "Run blameless postmortem with preventive actions",
                    "Delete logs",
                    "Shift ownership to another team",
                ],
                "correct_index": 1,
            },
            {
                "id": "psy_3",
                "text": "When feedback is tough, you:",
                "options": [
                    "Reject it immediately",
                    "Clarify examples, reflect, and set action plan",
                    "Ignore future feedback",
                    "Escalate as conflict",
                ],
                "correct_index": 1,
            },
        ],
    },
]


def _detect_answer_flags(answer_text: str, duration_sec: int | None) -> tuple[list[str], float]:
    text = answer_text.strip()
    lower = text.lower()
    words = re.findall(r"\w+", lower)
    word_count = len(words)
    unique_ratio = len(set(words)) / word_count if word_count else 0.0

    flags: list[str] = []
    if word_count > 150 and unique_ratio < 0.35:
        flags.append("high_repetition")
    if duration_sec is not None and duration_sec < 8 and word_count > 60:
        flags.append("too_fast_for_length")
    if any(pattern.search(text) for pattern in _TEMPLATE_PATTERNS):
        flags.append("template_phrase_detected")
    if word_count > 220 and sum(1 for c in text if c in ".!?") < 2:
        flags.append("oversized_monologue")

    quality = 1.0
    if word_count < 15:
        quality -= 0.35
    if unique_ratio < 0.45:
        quality -= 0.2
    quality -= min(0.4, 0.12 * len(flags))
    return flags, max(0.0, min(1.0, quality))


def _to_candidate_tests_payload(tests: list[Test]) -> list[dict]:
    payload: list[dict] = []
    for test in tests:
        payload.append(
            {
                "id": test.id,
                "category": test.category,
                "title": test.title,
                "duration_sec": test.duration_sec,
                "questions": [
                    {
                        "id": q["id"],
                        "text": q["text"],
                        "options": q["options"],
                    }
                    for q in test.questions
                ],
            }
        )
    return payload


async def ensure_questions(
    db: Session,
    *,
    interview: Interview,
    job_title: str,
    requirements: str,
    seniority: str,
    question_count: int = 6,
    prompt_version: str = "v1",
) -> list[Question]:
    existing = db.scalars(
        select(Question).where(Question.interview_id == interview.id).order_by(Question.order_index.asc())
    ).all()
    if existing:
        return existing

    client = AIClient()
    generated = await client.generate_questions(
        {
            "job_title": job_title,
            "requirements": requirements,
            "seniority": seniority,
            "count": question_count,
            "prompt_version": prompt_version,
        }
    )

    questions: list[Question] = []
    for idx, text in enumerate(generated):
        question_type = "technical" if idx < math.ceil(question_count / 2) else "behavioral"
        question = Question(
            interview_id=interview.id,
            order_index=idx,
            text=text,
            prompt_version=prompt_version,
            question_type=question_type,
            time_limit_sec=180 if question_type == "technical" else 210,
            audio_base64=None,
        )
        db.add(question)
        questions.append(question)

    if interview.status == "pending":
        interview.status = "in_progress"
        interview.started_at = datetime.now(UTC)

    db.flush()
    return questions


def ensure_tests(db: Session, *, interview: Interview) -> list[Test]:
    existing = db.scalars(select(Test).where(Test.interview_id == interview.id).order_by(Test.created_at.asc())).all()
    existing_categories = {item.category for item in existing}

    tests: list[Test] = list(existing)
    for blueprint in TEST_BLUEPRINTS:
        if blueprint["category"] in existing_categories:
            continue
        test = Test(
            company_id=interview.company_id,
            interview_id=interview.id,
            candidate_id=interview.candidate_id,
            category=blueprint["category"],
            title=blueprint["title"],
            duration_sec=blueprint["duration_sec"],
            questions=blueprint["questions"],
            is_active=True,
        )
        db.add(test)
        tests.append(test)
        existing_categories.add(blueprint["category"])
    db.flush()
    return tests


def create_custom_test(
    db: Session,
    *,
    interview: Interview,
    title: str,
    category: str,
    duration_sec: int,
    questions: list[dict],
) -> Test:
    normalized_questions: list[dict] = []
    for index, question in enumerate(questions):
        options = [str(item).strip() for item in question.get("options", []) if str(item).strip()]
        correct_index = int(question.get("correct_index", 0))
        if len(options) < 2:
            raise ValueError("Each custom test question must contain at least two options")
        if correct_index < 0 or correct_index >= len(options):
            raise ValueError("correct_index out of range for options")
        normalized_questions.append(
            {
                "id": f"custom_{index + 1}_{uuid.uuid4().hex[:6]}",
                "text": str(question.get("text", "")).strip(),
                "options": options,
                "correct_index": correct_index,
            }
        )

    if not normalized_questions:
        raise ValueError("Custom test requires at least one valid question")

    test = Test(
        company_id=interview.company_id,
        interview_id=interview.id,
        candidate_id=interview.candidate_id,
        category=category[:64] if category else "custom",
        title=title,
        duration_sec=duration_sec,
        questions=normalized_questions,
        is_active=True,
    )
    db.add(test)
    db.flush()
    return test


async def store_answer(
    db: Session,
    *,
    interview: Interview,
    question_id: str,
    answer_text: str,
    duration_sec: int | None,
    source_type: str = "text",
    stt_confidence: float | None = None,
    speech_pause_ratio: float | None = None,
    filler_word_ratio: float | None = None,
    instability_score: float | None = None,
) -> Answer:
    client = AIClient()
    sentiment = await client.analyze_sentiment(answer_text)
    embedding = await client.embed_text(answer_text)
    flags, quality = _detect_answer_flags(answer_text, duration_sec)

    answer = Answer(
        interview_id=interview.id,
        question_id=question_id,
        text=answer_text,
        duration_sec=duration_sec,
        source_type=source_type,
        sentiment_label=sentiment.get("label"),
        sentiment_score=sentiment.get("score"),
        stt_confidence=stt_confidence,
        speech_pause_ratio=speech_pause_ratio,
        filler_word_ratio=filler_word_ratio,
        instability_score=instability_score,
        anti_cheat_flags=flags,
        ai_quality_score=quality,
    )
    db.add(answer)

    vector = embedding.get("vector", [])
    db.add(
        Embedding(
            company_id=interview.company_id,
            candidate_id=interview.candidate_id,
            interview_id=interview.id,
            source_type="answer",
            source_id=question_id,
            vector=vector,
            dimensions=len(vector),
            model_name=embedding.get("model_name", "unknown"),
            is_normalized=True,
        )
    )

    if flags:
        for flag in flags:
            db.add(
                AuditLog(
                    company_id=interview.company_id,
                    user_id=None,
                    action="candidate_answer_flagged",
                    entity_type="interview",
                    entity_id=interview.id,
                    payload={"question_id": question_id, "flag": flag},
                )
            )
        interview.suspicious_events_count += len(flags)

    db.flush()
    return answer


async def evaluate_test_submission(
    db: Session,
    *,
    interview: Interview,
    test: Test,
    submitted_answers: list[dict],
) -> TestResult:
    question_map = {item["id"]: item for item in test.questions}
    total = len(test.questions)
    score = 0.0
    transcript_parts: list[str] = []
    persisted_answers: list[dict] = []

    for submitted in submitted_answers:
        question = question_map.get(submitted["question_id"])
        if not question:
            continue
        selected = submitted.get("selected_option")
        text_answer = submitted.get("text_answer")

        is_correct = selected is not None and selected == question.get("correct_index")
        if is_correct:
            score += 1.0

        picked_option = ""
        if selected is not None and 0 <= int(selected) < len(question["options"]):
            picked_option = question["options"][int(selected)]
        if text_answer:
            picked_option = text_answer

        transcript_parts.append(f"Q: {question['text']}\nA: {picked_option}")
        persisted_answers.append(
            {
                "question_id": question["id"],
                "selected_option": selected,
                "text_answer": text_answer,
                "is_correct": is_correct,
            }
        )

    normalized = (score / total * 100.0) if total else 0.0

    client = AIClient()
    analysis = await client.score_candidate(
        transcript="\n".join(transcript_parts),
        requirements=f"{test.category} assessment for hiring",
    )

    result = db.scalar(
        select(TestResult).where(
            TestResult.test_id == test.id,
            TestResult.interview_id == interview.id,
            TestResult.candidate_id == interview.candidate_id,
        )
    )
    if not result:
        result = TestResult(
            company_id=interview.company_id,
            test_id=test.id,
            interview_id=interview.id,
            candidate_id=interview.candidate_id,
            answers=persisted_answers,
            raw_score=score,
            normalized_score=normalized,
            ai_analysis=analysis,
            notes=analysis.get("rationale", {}).get("summary"),
        )
        db.add(result)
    else:
        result.answers = persisted_answers
        result.raw_score = score
        result.normalized_score = normalized
        result.ai_analysis = analysis
        result.notes = analysis.get("rationale", {}).get("summary")

    db.flush()
    return result


def _aggregate_test_signals(results: list[TestResult], tests: dict[str, Test]) -> dict:
    if not results:
        return {
            "technical_score": 0.0,
            "soft_score": 0.0,
            "psychology_score": 0.0,
            "overall": 0.0,
        }

    technical: list[float] = []
    soft: list[float] = []
    psychology: list[float] = []
    for result in results:
        category = tests.get(result.test_id).category if result.test_id in tests else ""
        if category in {"python", "javascript", "sql", "algorithms"}:
            technical.append(result.normalized_score)
        elif category == "soft_skills":
            soft.append(result.normalized_score)
        elif category == "psychology":
            psychology.append(result.normalized_score)

    all_scores = [item.normalized_score for item in results]
    return {
        "technical_score": round(mean(technical), 2) if technical else 0.0,
        "soft_score": round(mean(soft), 2) if soft else 0.0,
        "psychology_score": round(mean(psychology), 2) if psychology else 0.0,
        "overall": round(mean(all_scores), 2) if all_scores else 0.0,
    }


def _aggregate_speech_signals(answers: list[Answer]) -> dict:
    pause_ratios = [a.speech_pause_ratio for a in answers if a.speech_pause_ratio is not None]
    filler_ratios = [a.filler_word_ratio for a in answers if a.filler_word_ratio is not None]
    instability = [a.instability_score for a in answers if a.instability_score is not None]
    return {
        "pause_ratio": round(mean(pause_ratios), 4) if pause_ratios else 0.0,
        "filler_ratio": round(mean(filler_ratios), 4) if filler_ratios else 0.0,
        "instability_score": round(mean(instability), 4) if instability else 0.0,
    }


def _build_interview_report_content(
    *,
    candidate: Candidate,
    vacancy: Vacancy | None,
    questions: list[Question],
    answers: list[Answer],
    score: Score,
    test_results: list[TestResult],
    tests: dict[str, Test],
) -> dict:
    answers_by_question = {item.question_id: item for item in answers}
    question_blocks: list[dict] = []
    for question in sorted(questions, key=lambda q: q.order_index):
        answer = answers_by_question.get(question.id)
        question_blocks.append(
            {
                "question": question.text,
                "question_type": question.question_type,
                "answer": answer.text if answer else "",
                "answer_score": round((answer.ai_quality_score or 0.0) * 100.0, 2) if answer else 0.0,
                "sentiment": answer.sentiment_label if answer else None,
                "nervousness_signals": {
                    "pause_ratio": answer.speech_pause_ratio if answer else None,
                    "filler_ratio": answer.filler_word_ratio if answer else None,
                    "instability_score": answer.instability_score if answer else None,
                },
            }
        )

    test_blocks: list[dict] = []
    for result in test_results:
        test = tests.get(result.test_id)
        if not test:
            continue
        test_blocks.append(
            {
                "category": test.category,
                "title": test.title,
                "score": result.normalized_score,
                "analysis": result.ai_analysis.get("rationale", {}).get("summary"),
            }
        )

    strengths = score.rationale.get("strengths", [])
    risks = score.rationale.get("risks", [])

    return {
        "candidate_full_name": candidate.full_name,
        "candidate_profile": {
            "email": candidate.email,
            "experience_years": candidate.experience_years,
            "skills": candidate.skills,
            "education": candidate.education,
        },
        "position": vacancy.title if vacancy else "Generalist",
        "questions_and_answers": question_blocks,
        "tests": test_blocks,
        "overall_scoring": {
            "technical_level": score.technical_score,
            "soft_skills": score.soft_skills_score,
            "logical_thinking": score.logic_score,
            "psychological_stability": score.psychological_stability_score,
            "nervousness_level": score.nervousness_score,
            "overall": score.overall_score,
        },
        "risk_analysis": risks,
        "strengths": strengths,
        "ai_summary": score.rationale.get("summary", ""),
        "final_recommendation": score.recommendation,
    }


async def finalize_interview(db: Session, *, interview: Interview, requirements: str) -> Score:
    answers = db.scalars(select(Answer).where(Answer.interview_id == interview.id)).all()
    questions = db.scalars(
        select(Question).where(Question.interview_id == interview.id).order_by(Question.order_index.asc())
    ).all()
    transcript = "\n".join(f"Q: {q.text}\nA: {(next((a.text for a in answers if a.question_id == q.id), ''))}" for q in questions)

    test_results = db.scalars(select(TestResult).where(TestResult.interview_id == interview.id)).all()
    tests = db.scalars(select(Test).where(Test.interview_id == interview.id)).all()
    tests_by_id = {item.id: item for item in tests}
    test_signals = _aggregate_test_signals(test_results, tests_by_id)

    speech_signals = _aggregate_speech_signals(answers)
    anti_cheat_signals = {
        "suspicious_events_count": interview.suspicious_events_count,
        "flagged_answers_count": sum(1 for answer in answers if answer.anti_cheat_flags),
        "high_risk_flags": sum(len(answer.anti_cheat_flags) for answer in answers),
    }

    client = AIClient()
    scoring = await client.score_candidate(
        transcript=transcript,
        requirements=requirements,
        anti_cheat_signals=anti_cheat_signals,
        speech_signals=speech_signals,
        test_signals=test_signals,
    )

    score = db.scalar(select(Score).where(Score.interview_id == interview.id))
    recommendation = scoring.get("recommendation", "recommended_with_conditions")
    if recommendation == "recommended":
        risk_level = "low"
    elif recommendation == "recommended_with_conditions":
        risk_level = "medium"
    else:
        risk_level = "high"

    if not score:
        score = Score(
            interview_id=interview.id,
            technical_score=float(scoring["technical_score"]),
            communication_score=float(scoring["soft_skills_score"]),
            culture_score=float(scoring["psychological_stability_score"]),
            soft_skills_score=float(scoring["soft_skills_score"]),
            logic_score=float(scoring["logic_score"]),
            psychological_stability_score=float(scoring["psychological_stability_score"]),
            nervousness_score=float(scoring["nervousness_score"]),
            overall_score=float(scoring["overall_score"]),
            recommendation=recommendation,
            risk_level=risk_level,
            rationale=scoring.get("rationale", {}),
            model_version=scoring.get("model_version", "scoring-v1"),
        )
        db.add(score)
    else:
        score.technical_score = float(scoring["technical_score"])
        score.communication_score = float(scoring["soft_skills_score"])
        score.culture_score = float(scoring["psychological_stability_score"])
        score.soft_skills_score = float(scoring["soft_skills_score"])
        score.logic_score = float(scoring["logic_score"])
        score.psychological_stability_score = float(scoring["psychological_stability_score"])
        score.nervousness_score = float(scoring["nervousness_score"])
        score.overall_score = float(scoring["overall_score"])
        score.recommendation = recommendation
        score.risk_level = risk_level
        score.rationale = scoring.get("rationale", {})
        score.model_version = scoring.get("model_version", "scoring-v1")

    interview.status = "completed"
    interview.completed_at = datetime.now(UTC)

    candidate = db.get(Candidate, interview.candidate_id)
    vacancy = db.get(Vacancy, candidate.vacancy_id) if candidate and candidate.vacancy_id else None

    report_content = _build_interview_report_content(
        candidate=candidate,
        vacancy=vacancy,
        questions=questions,
        answers=answers,
        score=score,
        test_results=test_results,
        tests=tests_by_id,
    )
    executive_content = {
        "candidate": candidate.full_name,
        "overall_score": score.overall_score,
        "key_strengths": score.rationale.get("strengths", []),
        "key_risks": score.rationale.get("risks", []),
        "recommendation": score.recommendation,
    }

    interview_report = db.scalar(
        select(Report).where(Report.interview_id == interview.id, Report.report_type == "interview")
    )
    if not interview_report:
        interview_report = Report(
            company_id=interview.company_id,
            interview_id=interview.id,
            report_type="interview",
            summary=score.rationale.get("summary", "Interview report"),
            content=report_content,
        )
        db.add(interview_report)
    else:
        interview_report.summary = score.rationale.get("summary", "Interview report")
        interview_report.content = report_content

    executive_report = db.scalar(
        select(Report).where(Report.interview_id == interview.id, Report.report_type == "executive")
    )
    if not executive_report:
        executive_report = Report(
            company_id=interview.company_id,
            interview_id=interview.id,
            report_type="executive",
            summary=f"{candidate.full_name}: {score.recommendation}",
            content=executive_content,
        )
        db.add(executive_report)
    else:
        executive_report.summary = f"{candidate.full_name}: {score.recommendation}"
        executive_report.content = executive_content

    db.flush()
    return score


def candidate_tests_payload(db: Session, *, interview: Interview) -> list[dict]:
    tests = ensure_tests(db, interview=interview)
    return _to_candidate_tests_payload(tests)
