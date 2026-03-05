from sqlalchemy.orm import Session

from app.db.models import AuditLog


def log_audit(
    db: Session,
    *,
    action: str,
    entity_type: str,
    entity_id: str | None,
    company_id: str | None,
    user_id: str | None,
    payload: dict | None = None,
) -> None:
    event = AuditLog(
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        company_id=company_id,
        user_id=user_id,
        payload=payload or {},
    )
    db.add(event)
