# Architecture

## Context

SkillGraph is multi-tenant (multi-company) and role-driven.
One user can belong to one or more companies with different roles.

## Services

- `apps/api`: business API, auth, RBAC, persistence, audit.
- `services/ai`: model inference microservice.
- `apps/admin`: management UI for Owner/HR/Supervisor.
- `apps/web`: no-auth candidate interview app using magic links.

## Backend Layers

- `app/core`: config, security, role checks, auth dependencies.
- `app/db`: SQLAlchemy models, sessions, base metadata.
- `app/services`: business workflows (interview orchestration, AI client, audit).
- `app/api/routes`: endpoint layer.

## Data Model (Core)

Mandatory entities:
- `users`
- `companies`
- `user_company_roles`
- `candidates`
- `interviews`
- `questions`
- `answers`
- `scores`
- `reports`
- `audit_logs`
- `embeddings`

Additional entity:
- `vacancies` to support HR vacancy workflows.

## Runtime Flow

1. Owner registers company.
2. Owner/HR_SENIOR invites HR_JUNIOR or SUPERVISOR.
3. HR creates vacancy and candidate magic link.
4. Candidate opens public interview link.
5. API requests AI service for question generation + TTS.
6. Candidate submits answers.
7. API asks AI service for sentiment + embeddings per answer.
8. On completion, API requests scoring and writes `scores` + `reports`.
9. Admin and Supervisor consume analytics.

## Security Boundaries

- JWT in HttpOnly cookies.
- CORS allowlist for admin/web origins.
- RBAC check on protected routes.
- Audit log writes for auth and HR actions.
