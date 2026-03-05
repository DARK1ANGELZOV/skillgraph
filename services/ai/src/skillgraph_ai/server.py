from functools import lru_cache

from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, Field

from skillgraph_ai.config import get_ai_settings
from skillgraph_ai.pipeline import InferencePipeline

app = FastAPI(title="SkillGraph AI", version="2.0.0")
settings = get_ai_settings()


@lru_cache(maxsize=1)
def get_pipeline() -> InferencePipeline:
    return InferencePipeline()


MODE_CAPABILITIES = {
    "all": {"questions", "sentiment", "embeddings", "score", "tts", "stt", "status"},
    "question": {"questions", "status"},
    "tts": {"tts", "status"},
    "stt": {"stt", "status"},
    "analysis": {"sentiment", "embeddings", "score", "status"},
}


def require_capability(capability: str) -> None:
    allowed = MODE_CAPABILITIES.get(settings.service_mode, MODE_CAPABILITIES["all"])
    if capability not in allowed:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Capability '{capability}' disabled for mode '{settings.service_mode}'",
        )


class QuestionRequest(BaseModel):
    job_title: str
    requirements: str
    seniority: str = "middle"
    count: int = Field(default=6, ge=3, le=15)
    prompt_version: str = "v1"


class SentimentRequest(BaseModel):
    text: str


class EmbeddingRequest(BaseModel):
    text: str


class ScoringRequest(BaseModel):
    transcript: str
    requirements: str
    prompt_version: str = "v1"
    anti_cheat_signals: dict = Field(default_factory=dict)
    speech_signals: dict = Field(default_factory=dict)
    test_signals: dict = Field(default_factory=dict)


class TTSRequest(BaseModel):
    text: str
    speech_rate: float = Field(default=1.0, ge=0.75, le=1.35)


class STTRequest(BaseModel):
    audio_base64: str
    language: str = "ru"


@app.get("/health")
def health():
    return {"status": "ok", "service": settings.service_name, "mode": settings.service_mode}


@app.get("/v1/models/status")
def model_status():
    require_capability("status")
    pipeline = get_pipeline()
    return pipeline.model_status()


@app.post("/v1/questions")
def questions(payload: QuestionRequest):
    require_capability("questions")
    pipeline = get_pipeline()
    items = pipeline.generate_questions(
        job_title=payload.job_title,
        requirements=payload.requirements,
        seniority=payload.seniority,
        count=payload.count,
        prompt_version=payload.prompt_version,
    )
    return {"questions": items}


@app.post("/v1/sentiment")
def sentiment(payload: SentimentRequest):
    require_capability("sentiment")
    pipeline = get_pipeline()
    result = pipeline.analyze_sentiment(payload.text)
    return {"label": result.label, "score": result.score}


@app.post("/v1/embeddings")
def embeddings(payload: EmbeddingRequest):
    require_capability("embeddings")
    pipeline = get_pipeline()
    vector = pipeline.embed_text(payload.text)
    return {"vector": vector, "model_name": pipeline.settings.embedding_model}


@app.post("/v1/score")
def score(payload: ScoringRequest):
    require_capability("score")
    pipeline = get_pipeline()
    return pipeline.score_candidate(
        transcript=payload.transcript,
        requirements=payload.requirements,
        prompt_version=payload.prompt_version,
        anti_cheat_signals=payload.anti_cheat_signals,
        speech_signals=payload.speech_signals,
        test_signals=payload.test_signals,
    )


@app.post("/v1/tts")
def tts(payload: TTSRequest):
    require_capability("tts")
    pipeline = get_pipeline()
    return {"audio_base64": pipeline.synthesize_speech(payload.text, speech_rate=payload.speech_rate)}


@app.post("/v1/stt")
def stt(payload: STTRequest):
    require_capability("stt")
    pipeline = get_pipeline()
    return pipeline.transcribe_speech(payload.audio_base64, language=payload.language)
