from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class AISettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    hf_home: Path = Field(default=Path("/models"), alias="HF_HOME")
    hf_token: str | None = Field(default=None, alias="HF_TOKEN")

    llm_model: str = Field(default="distilgpt2", alias="HF_LLM_MODEL")
    embedding_model: str = Field(default="sentence-transformers/all-MiniLM-L6-v2", alias="HF_EMBEDDING_MODEL")
    sentiment_model: str = Field(
        default="distilbert/distilbert-base-uncased-finetuned-sst-2-english", alias="HF_SENTIMENT_MODEL"
    )
    stt_model: str = Field(default="openai/whisper-tiny", alias="HF_STT_MODEL")
    tts_model: str = Field(default="microsoft/speecht5_tts", alias="HF_TTS_MODEL")
    tts_vocoder: str = Field(default="microsoft/speecht5_hifigan", alias="HF_TTS_VOCODER")
    service_mode: str = Field(default="all", alias="AI_SERVICE_MODE")
    service_name: str = Field(default="ai", alias="AI_SERVICE_NAME")

    prompts_dir: Path = Field(default=Path("services/ai/prompts"), alias="AI_PROMPTS_DIR")


@lru_cache(maxsize=1)
def get_ai_settings() -> AISettings:
    return AISettings()
