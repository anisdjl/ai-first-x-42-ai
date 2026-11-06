from datetime import datetime, timezone
import uuid
from app.database import get_database
from app.models.audit import AuditLog, AuditAction, UserRole
import logging

logger = logging.getLogger(__name__)

async def log_action(
    action: AuditAction,
    user_role: UserRole,
    candidate_id: str = None,
    anonymous_id: str = None,
    details: str = ""
):
    """
    Journal d'audit RGPD :
    Trace Qui, Quoi, Quand. Ne logge JAMAIS le contenu d'un CV.
    """
    db = get_database()
    entry = AuditLog(
        id=str(uuid.uuid4()),
        timestamp=datetime.now(timezone.utc),
        user_role=user_role,
        action=action,
        candidate_id=candidate_id,
        anonymous_id=anonymous_id,
        details=details
    )
    if db is not None:
        await db.audit_logs.insert_one(entry.model_dump())
    logger.info(f"[AUDIT] {user_role.value.upper()} - {action.value.upper()} - {details}")
    return entry

async def get_audit_logs(limit: int = 100):
    db = get_database()
    if db is None:
        return []
    cursor = db.audit_logs.find().sort("timestamp", -1).limit(limit)
    logs = []
    async for doc in cursor:
        doc["_id"] = str(doc["_id"])
        logs.append(doc)
    return logs
