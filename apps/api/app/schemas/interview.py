from datetime import datetime

from pydantic import BaseModel, Field


class QuestionRead(BaseModel):
    id: str
    order_index: int
    text: str
    prompt_version: str
    question_type: str
    time_limit_sec: int
    audio_base64: str | None


class InterviewPublicRead(BaseModel):
    interview_id: str
    candidate_name: str
    status: str
    questions: list[QuestionRead]


class AnswerSubmit(BaseModel):
    question_id: str
    text: str = Field(min_length=1)
    duration_sec: int | None = Field(default=None, ge=0)
    source_type: str = Field(default="text", pattern="^(text|speech)$")
    stt_confidence: float | None = Field(default=None, ge=0, le=1)
    speech_pause_ratio: float | None = Field(default=None, ge=0, le=1)
    filler_word_ratio: float | None = Field(default=None, ge=0, le=1)
    instability_score: float | None = Field(default=None, ge=0, le=1)


class ScoreRead(BaseModel):
    technical_score: float
    communication_score: float
    culture_score: float
    soft_skills_score: float
    logic_score: float
    psychological_stability_score: float
    nervousness_score: float
    overall_score: float
    recommendation: str
    risk_level: str
    rationale: dict
    model_version: str


class InterviewAdminRead(BaseModel):
    id: str
    candidate_id: str
    status: str
    started_at: datetime | None
    completed_at: datetime | None
    score: ScoreRead | None


class AntiCheatEventCreate(BaseModel):
    event_type: str = Field(min_length=2, max_length=100)
    severity: str = Field(default="medium", pattern="^(low|medium|high)$")
    question_id: str | None = None
    details: dict = Field(default_factory=dict)


class STTRequest(BaseModel):
    audio_base64: str = Field(min_length=16)
    language: str = Field(default="ru")


class STTResponse(BaseModel):
    text: str
    confidence: float
    pause_ratio: float
    filler_ratio: float
    instability_score: float


class TestQuestionRead(BaseModel):
    id: str
    text: str
    options: list[str]


class TestRead(BaseModel):
    id: str
    category: str
    title: str
    duration_sec: int
    questions: list[TestQuestionRead]


class TestAnswerSubmit(BaseModel):
    question_id: str
    selected_option: int | None = Field(default=None, ge=0)
    text_answer: str | None = None


class TestSubmitRequest(BaseModel):
    answers: list[TestAnswerSubmit] = Field(min_length=1)


class TestResultRead(BaseModel):
    test_id: str
    category: str
    raw_score: float
    normalized_score: float
    ai_analysis: dict


class TestQuestionCreate(BaseModel):
    text: str = Field(min_length=3, max_length=1000)
    options: list[str] = Field(min_length=2, max_length=8)
    correct_index: int = Field(ge=0, le=7)


class CustomTestCreateRequest(BaseModel):
    title: str = Field(min_length=3, max_length=255)
    category: str = Field(default="custom", max_length=64)
    duration_sec: int = Field(default=900, ge=60, le=7200)
    questions: list[TestQuestionCreate] = Field(min_length=1, max_length=40)
