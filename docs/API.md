# API Overview

Base URL: `/api`

## Auth

- `POST /auth/register-owner`
- `POST /auth/login`
- `POST /auth/refresh`
- `POST /auth/logout`
- `GET /auth/me`
- `POST /auth/invites`
- `POST /auth/invites/accept`

## Company

- `GET /companies/current`
- `PUT /companies/current`
- `GET /companies/billing`

## Vacancy

- `POST /vacancies`
- `GET /vacancies`

## Candidates

- `POST /candidates/magic-link`
- `GET /candidates`

## Interviews

Public candidate flow:
- `GET /interviews/public/{token}`
- `POST /interviews/public/{token}/answers`
- `POST /interviews/public/{token}/complete`

Admin flow:
- `GET /interviews`
- `GET /interviews/{interview_id}`

## Analytics

- `GET /analytics/reports`
- `GET /analytics/executive-summary`
