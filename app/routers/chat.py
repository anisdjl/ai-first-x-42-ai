from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import List, Optional
from app.models.audit import UserRole
from app.services.ollama_service import ask_chat_pool
from app.services.candidate_service import list_candidates
from app.routers.job_posting import get_job_posting

router = APIRouter(prefix="/api/v1/chat", tags=["Q&A Assistant"])

class ChatRequest(BaseModel):
    query: str
    user_role: Optional[UserRole] = UserRole.RECRUTEUR

class ChatResponse(BaseModel):
    query: str
    response: str
    candidates_count: int

@router.post("", response_model=ChatResponse)
async def chat_with_candidate_pool(req: ChatRequest):
    """
    Q&A en langage naturel sur le vivier de candidats.
    Ex : « Qui a déjà travaillé avec des API REST ? »
    Le modèle local ne reçoit que les profils nettoyés (Palier 1), jamais les CV bruts.
    """
    candidates = await list_candidates(user_role=req.user_role)
    if not candidates:
        return ChatResponse(
            query=req.query,
            response="Aucun candidat n'est actuellement enregistré dans le vivier.",
            candidates_count=0
        )
        
    job = await get_job_posting()
    job_text = f"{job.titre} - {job.description}\n" + "\n".join(job.missions)

    try:
        answer = await ask_chat_pool(
            query=req.query,
            candidates_facts=candidates,
            job_posting_text=job_text
        )
        return ChatResponse(
            query=req.query,
            response=answer,
            candidates_count=len(candidates)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur du modèle de chat local : {str(e)}")
