from __future__ import annotations

import base64
import io
import re
from dataclasses import dataclass
from statistics import mean

import numpy as np
import psutil
from scipy.signal import resample

from skillgraph_ai.config import get_ai_settings
from skillgraph_ai.prompts import PromptRegistry


@dataclass(slots=True)
class SentimentResult:
    label: str
    score: float


class InferencePipeline:
    def __init__(self) -> None:
        self.settings = get_ai_settings()
        self.registry = PromptRegistry(self.settings.prompts_dir)

        self._generator = None
        self._sentiment = None
        self._embedder = None
        self._tts_processor = None
        self._tts_model = None
        self._tts_vocoder = None
        self._speaker_embedding = None
        self._stt = None

    @property
    def generator(self):
        if self._generator is None:
            from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline

            tokenizer = AutoTokenizer.from_pretrained(
                self.settings.llm_model,
                cache_dir=self.settings.hf_home,
                token=self.settings.hf_token,
            )
            model = AutoModelForCausalLM.from_pretrained(
                self.settings.llm_model,
                cache_dir=self.settings.hf_home,
                token=self.settings.hf_token,
            )
            self._generator = pipeline("text-generation", model=model, tokenizer=tokenizer, device=-1)
        return self._generator

    @property
    def sentiment(self):
        if self._sentiment is None:
            from transformers import pipeline

            self._sentiment = pipeline(
                "sentiment-analysis",
                model=self.settings.sentiment_model,
                tokenizer=self.settings.sentiment_model,
                device=-1,
            )
        return self._sentiment

    @property
    def embedder(self):
        if self._embedder is None:
            from sentence_transformers import SentenceTransformer

            self._embedder = SentenceTransformer(
                self.settings.embedding_model,
                cache_folder=str(self.settings.hf_home),
                token=self.settings.hf_token,
            )
        return self._embedder

    @property
    def stt(self):
        if self._stt is None:
            from transformers import pipeline

            self._stt = pipeline(
                "automatic-speech-recognition",
                model=self.settings.stt_model,
                device=-1,
            )
        return self._stt

    def _load_tts(self) -> None:
        if self._tts_processor is not None:
            return

        import torch
        from datasets import load_dataset
        from transformers import SpeechT5ForTextToSpeech, SpeechT5HifiGan, SpeechT5Processor

        self._tts_processor = SpeechT5Processor.from_pretrained(
            self.settings.tts_model,
            cache_dir=self.settings.hf_home,
            token=self.settings.hf_token,
        )
        self._tts_model = SpeechT5ForTextToSpeech.from_pretrained(
            self.settings.tts_model,
            cache_dir=self.settings.hf_home,
            token=self.settings.hf_token,
        )
        self._tts_vocoder = SpeechT5HifiGan.from_pretrained(
            self.settings.tts_vocoder,
            cache_dir=self.settings.hf_home,
            token=self.settings.hf_token,
        )
        xvectors = load_dataset(
            "Matthijs/cmu-arctic-xvectors",
            split="validation",
            cache_dir=str(self.settings.hf_home),
        )
        self._speaker_embedding = torch.tensor(xvectors[7306]["xvector"]).unsqueeze(0)

    def generate_questions(
        self,
        *,
        job_title: str,
        requirements: str,
        seniority: str,
        count: int,
        prompt_version: str = "v1",
    ) -> list[str]:
        template = self.registry.load_template("interview.yaml", prompt_version)
        prompt = template.format(
            count=count,
            job_title=job_title,
            requirements=requirements,
            seniority=seniority,
        )
        output = self.generator(
            prompt,
            max_new_tokens=280,
            do_sample=True,
            temperature=0.7,
            top_p=0.92,
        )[0]["generated_text"]

        generated_part = output[len(prompt) :]
        lines = [
            re.sub(r"^\s*(\d+[.)-]\s*)", "", line).strip()
            for line in generated_part.splitlines()
            if line.strip()
        ]

        unique_questions: list[str] = []
        for line in lines:
            normalized = line if line.endswith("?") else f"{line}?"
            if normalized not in unique_questions:
                unique_questions.append(normalized)
            if len(unique_questions) >= count:
                break

        defaults = [
            f"Describe a complex {job_title} project where you made a high-impact technical decision?",
            "How do you balance delivery speed with system reliability in production?",
            "Tell me about a conflict in your team and how you resolved it constructively?",
            "How would you evaluate tradeoffs between scalability, cost, and maintainability?",
            "What signals do you use to detect and reduce technical debt proactively?",
            "Describe a failure you owned, what you changed, and measurable results afterwards?",
        ]
        while len(unique_questions) < count:
            unique_questions.append(defaults[(len(unique_questions)) % len(defaults)])
        return unique_questions[:count]

    def analyze_sentiment(self, text: str) -> SentimentResult:
        result = self.sentiment(text[:1024] if text else "neutral")[0]
        label = str(result["label"]).upper()
        normalized = "POSITIVE" if "POS" in label else "NEGATIVE"
        return SentimentResult(label=normalized, score=float(result["score"]))

    def embed_text(self, text: str) -> list[float]:
        vector = self.embedder.encode([text], normalize_embeddings=True)[0]
        return vector.astype(float).tolist()

    def _cosine(self, a: list[float], b: list[float]) -> float:
        arr_a = np.array(a, dtype=float)
        arr_b = np.array(b, dtype=float)
        denom = np.linalg.norm(arr_a) * np.linalg.norm(arr_b)
        if denom == 0:
            return 0.0
        return float(np.dot(arr_a, arr_b) / denom)

    def _logic_signal(self, transcript: str) -> float:
        lower = transcript.lower()
        connectors = ["because", "therefore", "however", "if", "then", "tradeoff", "impact", "risk"]
        connector_hits = sum(lower.count(word) for word in connectors)
        sentences = max(1, len(re.split(r"[.!?]+", transcript)))
        return min(1.0, connector_hits / (sentences * 1.3))

    def _text_nervousness_signal(self, transcript: str) -> float:
        words = re.findall(r"\w+", transcript.lower())
        if not words:
            return 0.5
        filler_words = {"um", "uh", "like", "you know", "ээ", "эм", "как бы", "ну"}
        filler_count = sum(1 for word in words if word in filler_words)
        repetition = 0
        for idx in range(1, len(words)):
            if words[idx] == words[idx - 1]:
                repetition += 1
        filler_ratio = filler_count / len(words)
        repetition_ratio = repetition / len(words)
        return float(min(1.0, 0.65 * filler_ratio + 0.35 * repetition_ratio + 0.08))

    def score_candidate(
        self,
        *,
        transcript: str,
        requirements: str,
        prompt_version: str = "v1",
        anti_cheat_signals: dict | None = None,
        speech_signals: dict | None = None,
        test_signals: dict | None = None,
    ) -> dict:
        anti_cheat_signals = anti_cheat_signals or {}
        speech_signals = speech_signals or {}
        test_signals = test_signals or {}

        req_vector = self.embed_text(requirements)
        answer_vector = self.embed_text(transcript if transcript.strip() else "no response")
        similarity = max(0.0, self._cosine(req_vector, answer_vector))
        sentiment = self.analyze_sentiment(transcript if transcript.strip() else "neutral")

        word_count = len(transcript.split())
        completeness = min(1.0, word_count / 260.0)
        logic_signal = self._logic_signal(transcript)
        text_nervous = self._text_nervousness_signal(transcript)

        speech_pause = float(speech_signals.get("pause_ratio", 0.0))
        speech_filler = float(speech_signals.get("filler_ratio", 0.0))
        speech_instability = float(speech_signals.get("instability_score", 0.0))
        speech_nervous = min(1.0, 0.45 * speech_pause + 0.25 * speech_filler + 0.30 * speech_instability)
        nervousness = min(1.0, 0.55 * text_nervous + 0.45 * speech_nervous)

        suspicious_events = float(anti_cheat_signals.get("suspicious_events_count", 0.0))
        flagged_answers = float(anti_cheat_signals.get("flagged_answers_count", 0.0))
        anti_cheat_penalty = min(0.3, suspicious_events * 0.02 + flagged_answers * 0.03)

        technical_test = float(test_signals.get("technical_score", 0.0)) / 100.0
        soft_test = float(test_signals.get("soft_score", 0.0)) / 100.0
        psych_test = float(test_signals.get("psychology_score", 0.0)) / 100.0

        technical = min(100.0, max(0.0, 40 + 42 * similarity + 18 * technical_test - 10 * anti_cheat_penalty))
        soft_skills = min(
            100.0,
            max(
                0.0,
                38
                + 24 * completeness
                + 20 * soft_test
                + (16 * sentiment.score if sentiment.label == "POSITIVE" else -8 * sentiment.score),
            ),
        )
        logic = min(100.0, max(0.0, 35 + 50 * logic_signal + 15 * technical_test - 10 * anti_cheat_penalty))
        psychological_stability = min(
            100.0,
            max(0.0, 45 + 25 * psych_test + 20 * (1 - nervousness) + (8 if sentiment.label == "POSITIVE" else -5)),
        )
        nervousness_score = round(100 * nervousness, 2)

        communication = soft_skills
        culture = psychological_stability
        overall = (
            technical * 0.30
            + soft_skills * 0.20
            + logic * 0.20
            + psychological_stability * 0.20
            + (100 - nervousness_score) * 0.10
        )

        template = self.registry.load_template("scoring.yaml", prompt_version)
        prompt = template.format(requirements=requirements, transcript=transcript)
        llm_rationale = self.generator(prompt, max_new_tokens=200, do_sample=True, temperature=0.25)[0][
            "generated_text"
        ][len(prompt) :].strip()

        if overall >= 78 and nervousness_score <= 58 and anti_cheat_penalty <= 0.08:
            recommendation = "recommended"
        elif overall >= 62:
            recommendation = "recommended_with_conditions"
        else:
            recommendation = "not_recommended"

        strengths = []
        if technical >= 72:
            strengths.append("Strong technical alignment with role requirements")
        if logic >= 70:
            strengths.append("Structured reasoning and clear decision logic")
        if soft_skills >= 70:
            strengths.append("Effective communication and collaboration signals")
        if not strengths:
            strengths.append("Shows baseline role-fit potential with guided onboarding")

        risks = []
        if nervousness_score > 65:
            risks.append("Elevated nervousness markers under pressure")
        if anti_cheat_penalty > 0.12:
            risks.append("Suspicious interview behavior requires manual review")
        if technical < 60:
            risks.append("Technical depth below target level for the role")
        if not risks:
            risks.append("No critical hiring blockers detected")

        return {
            "technical_score": round(technical, 2),
            "communication_score": round(communication, 2),
            "culture_score": round(culture, 2),
            "soft_skills_score": round(soft_skills, 2),
            "logic_score": round(logic, 2),
            "psychological_stability_score": round(psychological_stability, 2),
            "nervousness_score": nervousness_score,
            "overall_score": round(overall, 2),
            "recommendation": recommendation,
            "model_version": f"{self.settings.llm_model}|scoring-{prompt_version}",
            "rationale": {
                "summary": llm_rationale[:900] if llm_rationale else "Candidate evaluation generated",
                "strengths": strengths,
                "risks": risks,
                "signals": {
                    "semantic_similarity": round(similarity, 4),
                    "sentiment": sentiment.label,
                    "sentiment_score": round(sentiment.score, 4),
                    "word_count": word_count,
                    "completeness": round(completeness, 4),
                    "logic_signal": round(logic_signal, 4),
                    "speech_pause_ratio": round(speech_pause, 4),
                    "speech_filler_ratio": round(speech_filler, 4),
                    "speech_instability": round(speech_instability, 4),
                    "anti_cheat_penalty": round(anti_cheat_penalty, 4),
                    "test_overall": test_signals.get("overall", 0.0),
                },
            },
        }

    def synthesize_speech(self, text: str, speech_rate: float = 1.0) -> str:
        import soundfile as sf

        self._load_tts()
        inputs = self._tts_processor(text=text, return_tensors="pt")
        speech = self._tts_model.generate_speech(inputs["input_ids"], self._speaker_embedding, vocoder=self._tts_vocoder)
        signal = speech.numpy()
        if speech_rate != 1.0:
            new_length = max(1, int(len(signal) / speech_rate))
            signal = resample(signal, new_length)

        wav_buffer = io.BytesIO()
        sf.write(wav_buffer, signal, samplerate=16000, format="WAV")
        return base64.b64encode(wav_buffer.getvalue()).decode("utf-8")

    def transcribe_speech(self, audio_base64: str, language: str = "ru") -> dict:
        import soundfile as sf

        audio_bytes = base64.b64decode(audio_base64)
        wav_data, sr = sf.read(io.BytesIO(audio_bytes))
        if wav_data.ndim > 1:
            wav_data = wav_data.mean(axis=1)

        result = self.stt(
            {"array": wav_data.astype(np.float32), "sampling_rate": sr},
            return_timestamps=True,
            generate_kwargs={"language": language, "task": "transcribe"},
        )
        text = str(result.get("text", "")).strip()
        chunks = result.get("chunks") or []
        gaps: list[float] = []
        last_end = 0.0
        for chunk in chunks:
            ts = chunk.get("timestamp")
            if not ts or ts[0] is None or ts[1] is None:
                continue
            start = float(ts[0])
            end = float(ts[1])
            if start > last_end:
                gaps.append(start - last_end)
            last_end = max(last_end, end)

        duration = last_end if last_end > 0 else len(wav_data) / float(sr)
        pause_ratio = min(1.0, sum(gaps) / duration) if duration > 0 else 0.0
        words = re.findall(r"\w+", text.lower())
        filler_lexicon = {"um", "uh", "like", "you", "know", "ээ", "эм", "как", "бы", "ну"}
        filler = sum(1 for word in words if word in filler_lexicon)
        filler_ratio = (filler / len(words)) if words else 0.0
        repeats = sum(1 for idx in range(1, len(words)) if words[idx] == words[idx - 1])
        repeat_ratio = (repeats / len(words)) if words else 0.0
        instability = min(1.0, 0.45 * pause_ratio + 0.30 * filler_ratio + 0.25 * repeat_ratio)
        confidence = max(0.15, min(0.99, 0.88 - 0.35 * instability))

        return {
            "text": text,
            "confidence": round(confidence, 4),
            "pause_ratio": round(pause_ratio, 4),
            "filler_ratio": round(filler_ratio, 4),
            "instability_score": round(instability, 4),
        }

    def model_status(self) -> dict:
        process = psutil.Process()
        ram_mb = process.memory_info().rss / 1024 / 1024
        models = [
            {
                "role": "question_generation",
                "model_id": self.settings.llm_model,
                "version": "v1",
                "loaded": self._generator is not None,
                "ram_usage_mb": round(ram_mb, 2),
                "last_error": None,
            },
            {
                "role": "embeddings",
                "model_id": self.settings.embedding_model,
                "version": "v1",
                "loaded": self._embedder is not None,
                "ram_usage_mb": round(ram_mb, 2),
                "last_error": None,
            },
            {
                "role": "sentiment",
                "model_id": self.settings.sentiment_model,
                "version": "v1",
                "loaded": self._sentiment is not None,
                "ram_usage_mb": round(ram_mb, 2),
                "last_error": None,
            },
            {
                "role": "tts",
                "model_id": self.settings.tts_model,
                "version": "v1",
                "loaded": self._tts_model is not None,
                "ram_usage_mb": round(ram_mb, 2),
                "last_error": None,
            },
            {
                "role": "stt",
                "model_id": self.settings.stt_model,
                "version": "v1",
                "loaded": self._stt is not None,
                "ram_usage_mb": round(ram_mb, 2),
                "last_error": None,
            },
        ]
        return {
            "service_name": self.settings.service_name,
            "service_mode": self.settings.service_mode,
            "ram_usage_mb": round(ram_mb, 2),
            "models": models,
            "loaded_count": sum(1 for model in models if model["loaded"]),
        }
