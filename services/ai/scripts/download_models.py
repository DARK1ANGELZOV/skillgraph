from datasets import load_dataset
from huggingface_hub import snapshot_download

from skillgraph_ai.config import get_ai_settings


def download_models() -> None:
    settings = get_ai_settings()
    cache = str(settings.hf_home)

    model_ids = [
        settings.llm_model,
        settings.embedding_model,
        settings.sentiment_model,
        settings.stt_model,
        settings.tts_model,
        settings.tts_vocoder,
    ]

    for model_id in model_ids:
        print(f"Downloading {model_id}...")
        snapshot_download(repo_id=model_id, cache_dir=cache, token=settings.hf_token)

    print("Downloading SpeechT5 speaker embeddings dataset...")
    load_dataset("Matthijs/cmu-arctic-xvectors", split="validation", cache_dir=cache)
    print("All models downloaded.")


if __name__ == "__main__":
    download_models()
