# SkillGraph

AI-платформа для оценки навыков, AI-интервью и анализа кандидатов  
(ориентация на рынок РФ)

## Архитектура
- Frontend: Next.js
- Backend: FastAPI
- AI: локальные LLM (16 GB VRAM)
- DB: PostgreSQL
- Infra: Docker / Kubernetes

## Структура
См. `docs/ARCHITECTURE.md`

## Быстрый старт (dev)

### 1. Клонирование
```bash
git clone https://github.com/DARK1ANGELZOV/skillgraph.git
cd skillgraph

### 2. BACKEND
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn apps.api.main:app --reload

python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn apps.api.main:app --reload

### 3. FRONTEND
cd apps/web
npm install
npm run dev
