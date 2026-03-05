# Security

## Authentication

- JWT access and refresh tokens.
- Tokens are stored in HttpOnly cookies (`sg_access_token`, `sg_refresh_token`).
- Refresh flow rotates session tokens.

## Passwords

- Password hashing via bcrypt (`passlib`).
- Raw passwords are never persisted.

## Authorization

Role-based access control is enforced in backend dependencies:
- OWNER
- HR_SENIOR
- HR_JUNIOR
- SUPERVISOR
- SUPERADMIN

Supervisor role is read-only for analytics/reporting endpoints.

## API Protection

- CORS allowlist for known frontend origins.
- Input validation with Pydantic.
- 401/403 responses for invalid or insufficient credentials.

## Auditability

- Sensitive operations are logged in `audit_logs`.
- Events include actor, company, action, entity type/id, and metadata.

## Operational Notes

- Keep `.env` out of VCS.
- Set strong `JWT_SECRET_KEY` in production.
- Enable `COOKIE_SECURE=true` behind HTTPS.
