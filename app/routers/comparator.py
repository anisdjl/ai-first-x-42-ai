from fastapi import APIRouter, Query
from typing import List, Dict, Any
from app.models.audit import UserRole
from app.services.candidate_service import list_candidates
from app.routers.job_posting import get_job_posting

router = APIRouter(prefix="/api/v1/comparator", tags=["Comparateur"])

@router.get("")
async def get_candidates_comparator(user_role: UserRole = Query(UserRole.RECRUTEUR)):
    """
    Tableau comparatif sur les critères explicites et modifiables de la fiche de poste.
    RÈGLE IA ACT : Zéro score global, zéro classement, zéro verdict.
    Distingue clairement les Faits des Déductions.
    """
    job = await get_job_posting()
    candidates = await list_candidates(user_role=user_role)
    
    criteria_list = [c.model_dump() for c in job.criteres_explicites]
    
    comparative_rows = []
    for c in candidates:
        evals = c.get("criteria_evaluation", {})
        row = {
            "id": c.get("id"),
            "anonymous_id": c.get("anonymous_id"),
            "nom": c.get("contact", {}).get("nom") if c.get("contact") else c.get("anonymous_id"),
            "evaluations_criteres": {
                crit["id"]: evals.get(crit["id"], "Non évalué")
                for crit in criteria_list
            },
            "points_forts": c.get("summary", {}).get("ce_qui_correspond", []),
            "points_faibles": c.get("summary", {}).get("ce_qui_manque", []),
            "a_verifier": c.get("summary", {}).get("a_verifier_en_entretien", [])
        }
        comparative_rows.append(row)
        
    return {
        "job_title": job.titre,
        "criteria": criteria_list,
        "candidates": comparative_rows
    }
