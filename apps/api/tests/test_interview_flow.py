from app.services.ai_client import AIClient


def test_full_interview_flow(client, monkeypatch):
    async def fake_questions(self, payload):
        return [
            "Tell me about a project you are proud of?",
            "How do you make architecture decisions?",
            "How do you handle team conflicts?",
        ]

    async def fake_tts(self, text, **kwargs):
        return {"audio_base64": "UklGRgAAAABXQVZFZm10IBAAAAABAAEA"}

    async def fake_sentiment(self, text):
        return {"label": "POSITIVE", "score": 0.94}

    async def fake_embed(self, text):
        return {"vector": [0.1, 0.2, 0.3], "model_name": "test-embed"}

    async def fake_score(self, transcript, requirements, **kwargs):
        return {
            "technical_score": 82,
            "communication_score": 80,
            "culture_score": 78,
            "soft_skills_score": 80,
            "logic_score": 79,
            "psychological_stability_score": 77,
            "nervousness_score": 24,
            "overall_score": 80.4,
            "recommendation": "recommended",
            "model_version": "test-model",
            "rationale": {"summary": "Good profile", "signals": {"semantic_similarity": 0.8}, "strengths": [], "risks": []},
        }

    monkeypatch.setattr(AIClient, "generate_questions", fake_questions)
    monkeypatch.setattr(AIClient, "tts", fake_tts)
    monkeypatch.setattr(AIClient, "analyze_sentiment", fake_sentiment)
    monkeypatch.setattr(AIClient, "embed_text", fake_embed)
    monkeypatch.setattr(AIClient, "score_candidate", fake_score)

    reg = client.post(
        "/api/auth/register-owner",
        json={
            "email": "owner@flow.dev",
            "password": "secret123",
            "company_name": "Flow Inc",
            "full_name": "Flow Owner",
        },
    )
    assert reg.status_code == 201

    vacancy = client.post(
        "/api/vacancies",
        json={
            "title": "Backend Engineer",
            "department": "Engineering",
            "seniority": "senior",
            "requirements": "Python, FastAPI, distributed systems",
        },
    )
    assert vacancy.status_code == 201
    vacancy_id = vacancy.json()["id"]

    candidate = client.post(
        "/api/candidates/magic-link",
        json={"full_name": "Alice", "email": "alice@example.com", "vacancy_id": vacancy_id},
    )
    assert candidate.status_code == 201
    token = candidate.json()["magic_link_token"]

    pub = client.get(f"/api/interviews/public/{token}")
    assert pub.status_code == 200
    questions = pub.json()["questions"]
    assert len(questions) == 3

    submit = client.post(
        f"/api/interviews/public/{token}/answers",
        json={"question_id": questions[0]["id"], "text": "I built a scalable API", "duration_sec": 12},
    )
    assert submit.status_code == 201

    tests_payload = client.get(f"/api/interviews/public/{token}/tests")
    assert tests_payload.status_code == 200
    for test in tests_payload.json():
        answers = [{"question_id": question["id"], "selected_option": 1} for question in test["questions"]]
        submitted = client.post(
            f"/api/interviews/public/{token}/tests/{test['id']}/submit",
            json={"answers": answers},
        )
        assert submitted.status_code == 200

    complete = client.post(f"/api/interviews/public/{token}/complete")
    assert complete.status_code == 200
    assert complete.json()["overall_score"] == 80.4
    assert complete.json()["recommendation"] == "recommended"

    reports = client.get("/api/analytics/reports")
    assert reports.status_code == 200
    assert len(reports.json()) == 2
