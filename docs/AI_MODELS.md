# AI Models

SkillGraph downloads models from HuggingFace and stores them in `HF_HOME`.

## Models

- LLM: `TinyLlama/TinyLlama-1.1B-Chat-v1.0`
- Embeddings: `sentence-transformers/all-MiniLM-L6-v2`
- Sentiment: `distilbert/distilbert-base-uncased-finetuned-sst-2-english`
- TTS: `microsoft/speecht5_tts`
- Vocoder: `microsoft/speecht5_hifigan`
- Speaker embeddings dataset: `Matthijs/cmu-arctic-xvectors`

## Download

```bash
python scripts/download_models.py
```

## Prompt Versioning

Prompt files:
- `services/ai/prompts/interview.yaml`
- `services/ai/prompts/scoring.yaml`

Each file contains `default_version` and `versions` map.
API can request explicit `prompt_version`.

## Memory Profile

The selected stack is designed for a 14-16 GB RAM machine with CPU inference.
For lower latency, use GPU and quantized LLM variants.
