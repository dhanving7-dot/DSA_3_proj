from sqlalchemy.orm import Session

from app.models.audit import AuditLog


def log_action(
    db: Session,
    user_id: int | None,
    action: str,
    entity_type: str,
    entity_id: str = "",
    details: dict | None = None,
    ip_address: str = "",
) -> None:
    db.add(
        AuditLog(
            user_id=user_id,
            action=action,
            entity_type=entity_type,
            entity_id=str(entity_id),
            details=details or {},
            ip_address=ip_address,
        )
    )
    db.commit()
