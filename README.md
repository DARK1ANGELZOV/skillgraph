# SkillGraph MVP (Enterprise Core)

SkillGraph is an AI-HR SaaS platform for automated interviews, anti-cheat control, candidate scoring, and management analytics.

## 1. Project Structure

```text
apps/
  admin/         React admin panel (Owner/HR/Supervisor/Superadmin)
  web/           React candidate app (magic-link interview + tests)
  api/           FastAPI backend (JWT cookies, RBAC, PostgreSQL, Alembic)
services/
  ai/            HuggingFace AI inference service
infra/
  docker-compose.yml
  docker/
    Dockerfile.api
    Dockerfile.ai
    Dockerfile.admin
    Dockerfile.web
docs/
  ARCHITECTURE.md
  API.md
  AI_MODELS.md
  SECURITY.md
```

## 2. Key Features Implemented

- Owner self-registration + company creation.
- Invite flow for HR/Supervisor roles.
- JWT access + refresh in HttpOnly cookies.
- RBAC middleware on backend.
- Vacancy and candidate management.
- Magic-link candidate flow (no candidate registration).
- AI interview:
  - question generation
  - TTS voice questions
  - STT answer transcription (RU supported)
  - sentiment, embeddings, scoring
  - nervousness analysis
- Candidate testing:
  - Python, JavaScript, SQL, Algorithms
  - Soft skills
  - Psychological stability
- HR/руководитель can create custom tests per interview and share test links.
- Anti-cheat:
  - tab switch / window blur
  - copy/paste tracking
  - answer timeout
  - suspicious answer pattern detection
  - audit logging to `audit_logs`
- Reports:
  - full HR report
  - executive summary
- Superadmin panel:
  - all companies
  - usage stats
  - AI model statuses (loaded/version/RAM)
  - system audit feed

## 3. Database Tables

Implemented and migrated:

- `users`
- `companies`
- `user_company_roles`
- `invites`
- `vacancies`
- `candidates`
- `interviews`
- `questions`
- `answers`
- `scores`
- `reports`
- `audit_logs`
- `embeddings`
- `ai_model_status`
- `tests`
- `test_results`

Multi-company support is enforced by company-scoped relations.

## 4. AI Architecture (4 services)

`docker-compose` runs 4 separate AI containers:

- `ai-question` (question generation)
- `ai-tts` (text-to-speech)
- `ai-stt` (speech-to-text)
- `ai-analysis` (sentiment, embeddings, scoring)

All models are downloaded from HuggingFace and cached under `HF_HOME` volume.

Default RAM-safe model set:

- `distilgpt2` (LLM)
- `sentence-transformers/all-MiniLM-L6-v2` (embeddings)
- `distilbert/distilbert-base-uncased-finetuned-sst-2-english` (sentiment)
- `openai/whisper-tiny` (STT)
- `microsoft/speecht5_tts` + `microsoft/speecht5_hifigan` (TTS)

## 5. Environment

Create `.env`:

```bash
cp .env.example .env
```

## 6. Run with Docker

```bash
docker compose -f infra/docker-compose.yml up -d --build
```

Stop:

```bash
docker compose -f infra/docker-compose.yml down
```

## 7. Runtime Verification Checklist (executed)

- `pytest` passed: `6 passed`
- Frontend builds passed:
  - `npm --prefix apps/admin run build`
  - `npm --prefix apps/web run build`
- Docker stack up:
  - `postgres`
  - `api`
  - `ai-question`
  - `ai-tts`
  - `ai-stt`
  - `ai-analysis`
  - `admin`
  - `web`
- Alembic current head: `20260222_0002`
- PostgreSQL reachable and schema present
- AI endpoints checked:
  - `/v1/models/status`
  - `/v1/stt`
  - `/v1/tts`
- End-to-end interview flow executed successfully:
  - question generation
  - answer submission
  - tests submission
  - final scoring + reports

## 8. URLs

- API: `http://localhost:8000`
- Unified product entrypoint (landing + auth + candidate interview): `http://localhost:5173`
- Legacy candidate web (kept for compatibility): `http://localhost:5174`
- AI services:
  - question: `http://localhost:8101`
  - tts: `http://localhost:8102`
  - stt: `http://localhost:8103`
  - analysis: `http://localhost:8104`

## 9. Demo Access

- Superadmin:
  - email: `superadmin@skillgraph.dev`
  - password: `SkillGraphAdmin123!`
- Example candidate interview link created during verification:
  - `http://localhost:5173/interview/VvTkzpFVK6B4pwB4FgPWOPhu1pyDmHoByovSUObgCUM`
  - `http://localhost:5173/interview/VvTkzpFVK6B4pwB4FgPWOPhu1pyDmHoByovSUObgCUM?mode=tests`

## 10. Useful Commands

Run migrations manually:

```bash
docker exec skillgraph_mvp-api-1 alembic -c apps/api/alembic.ini upgrade head
```

Check compose status:

```bash
docker compose -f infra/docker-compose.yml ps
```

Download AI models in advance:

```bash
python scripts/download_models.py
```
