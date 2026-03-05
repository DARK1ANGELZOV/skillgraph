from __future__ import annotations

from typing import Any

import httpx

from app.core.config import get_settings

settings = get_settings()


class AIClient:
    def __init__(self, base_url: str | None = None, timeout: float = 900.0) -> None:
        fallback = settings.ai_service_url
        self.base_url = (base_url or fallback).rstrip("/")
        self.question_url = (settings.ai_question_service_url or fallback).rstrip("/")
        self.tts_url = (settings.ai_tts_service_url or fallback).rstrip("/")
        self.stt_url = (settings.ai_stt_service_url or fallback).rstrip("/")
        self.analysis_url = (settings.ai_analysis_service_url or fallback).rstrip("/")
        self.timeout = timeout

    async def generate_questions(self, payload: dict[str, Any]) -> list[str]:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(f"{self.question_url}/v1/questions", json=payload)
            response.raise_for_status()
            return response.json()["questions"]

    async def analyze_sentiment(self, text: str) -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(f"{self.analysis_url}/v1/sentiment", json={"text": text})
            response.raise_for_status()
            return response.json()

    async def embed_text(self, text: str) -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(f"{self.analysis_url}/v1/embeddings", json={"text": text})
            response.raise_for_status()
            return response.json()

    async def score_candidate(
        self,
        transcript: str,
        requirements: str,
        *,
        anti_cheat_signals: dict[str, Any] | None = None,
        speech_signals: dict[str, Any] | None = None,
        test_signals: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{self.analysis_url}/v1/score",
                json={
                    "transcript": transcript,
                    "requirements": requirements,
                    "anti_cheat_signals": anti_cheat_signals or {},
                    "speech_signals": speech_signals or {},
                    "test_signals": test_signals or {},
                },
            )
            response.raise_for_status()
            return response.json()

    async def tts(self, text: str, *, speech_rate: float = 1.0) -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(f"{self.tts_url}/v1/tts", json={"text": text, "speech_rate": speech_rate})
            response.raise_for_status()
            return response.json()

    async def stt(self, audio_base64: str, language: str = "ru") -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{self.stt_url}/v1/stt",
                json={"audio_base64": audio_base64, "language": language},
            )
            response.raise_for_status()
            return response.json()

    async def model_status(self, service_url: str) -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(f"{service_url.rstrip('/')}/v1/models/status")
            response.raise_for_status()
            return response.json()
