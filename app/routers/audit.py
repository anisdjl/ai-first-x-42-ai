from fastapi import APIRouter, Query
from typing import List, Dict, Any
from app.services.audit_service import get_audit_logs
from app.services.candidate_service import list_candidates
from app.models.audit import UserRole

router = APIRouter(prefix="/api/v1/audit", tags=["Journal d'audit & Échéances"])

@router.get("/logs")
async def read_audit_logs(limit: int = Query(100, ge=1, le=500)):
    """
    Journal d'audit RGPD :
    Trace les événements (import, consultation, export, effacement).
    ZÉRO contenu de CV dans les logs.
    """
    return await get_audit_logs(limit=limit)

@router.get("/expirations")
async def get_expirations():
    """
    Surveillance des durées de conservation (Palier 3).
    Alerte automatique sur les candidatures dont la date de rétention est dépassée.
    """
    candidates = await list_candidates(user_role=UserRole.RECRUTEUR)
    expired = [c for c in candidates if c.get("is_expired")]
    active = [c for c in candidates if not c.get("is_expired")]
    
    return {
        "total_candidatures": len(candidates),
        "expired_count": len(expired),
        "active_count": len(active),
        "alert_action_required": len(expired) > 0,
        "message": f"{len(expired)} candidature(s) expirée(s) nécessitant une purge manuelle." if expired else "Toutes les candidatures sont dans leur période de validité.",
        "expired_candidates": [
            {
                "id": c.get("id"),
                "anonymous_id": c.get("anonymous_id"),
                "nom": c.get("contact", {}).get("nom") or "Anonyme",
                "retention_date": c.get("retention_date")
            }
            for c in expired
        ]
    }
