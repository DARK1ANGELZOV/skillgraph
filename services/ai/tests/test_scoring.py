from skillgraph_ai.pipeline import InferencePipeline, SentimentResult


class FakePipeline(InferencePipeline):
    def __init__(self):
        super().__init__()

    @property
    def generator(self):
        return lambda prompt, **kwargs: [{"generated_text": prompt + "Strong technical alignment and clear communication."}]

    def embed_text(self, text: str) -> list[float]:
        if "python" in text.lower():
            return [0.9, 0.2, 0.1]
        return [0.8, 0.3, 0.1]

    def analyze_sentiment(self, text: str) -> SentimentResult:
        return SentimentResult(label="POSITIVE", score=0.95)


def test_score_candidate_output_shape():
    pipeline = FakePipeline()
    result = pipeline.score_candidate(
        transcript="I built Python APIs with FastAPI and improved latency.",
        requirements="Python FastAPI distributed systems",
    )

    assert result["overall_score"] >= 50
    assert "rationale" in result
    assert result["recommendation"] in {"recommended", "recommended_with_conditions", "not_recommended"}
