from fastapi import APIRouter, UploadFile, File, Header, Query, HTTPException, status
from typing import List, Optional, Dict, Any
from app.models.audit import UserRole
from app.services.candidate_service import (
    process_and_save_cv, list_candidates, get_candidate_by_id,
    get_candidate_contact, delete_candidate, export_candidate_data,
    generate_gdpr_notice, simulate_candidate_expiration
)
from app.routers.job_posting import get_job_posting
import os
import glob

router = APIRouter(prefix="/api/v1/candidates", tags=["Candidats"])

def get_role(
    x_user_role: Optional[str] = Header(None, alias="X-User-Role"),
    role: Optional[str] = Query(None)
) -> UserRole:
    val = x_user_role or role or "recruteur"
    try:
        return UserRole(val.lower())
    except ValueError:
        return UserRole.RECRUTEUR

@router.post("/upload")
async def upload_candidate_cv(
    file: UploadFile = File(...),
    user_role: UserRole = Query(UserRole.RECRUTEUR)
):
    """
    Import d'un CV unique (Markdown, PDF, Image scannée).
    Extraction & minimisation immédiates, suppression de la copie brute en RAM.
    """
    job = await get_job_posting()
    job_text = f"{job.titre} chez {job.entreprise}\n{job.description}\n" + "\n".join(job.missions)
    
    file_bytes = await file.read()
    if not file_bytes:
        raise HTTPException(status_code=400, detail="Fichier vide.")
        
    try:
        candidate = await process_and_save_cv(
            filename=file.filename,
            file_bytes=file_bytes,
            job_posting_text=job_text,
            user_role=user_role
        )
        return {
            "status": "success",
            "message": "Candidat importé et extrait avec succès",
            "candidate": candidate
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Échec de traitement du CV : {str(e)}")

@router.post("/batch-import")
async def batch_import_directory(
    directory_path: str = Query(..., description="Chemin absolu vers le dossier contenant les CVs"),
    user_role: UserRole = Query(UserRole.RECRUTEUR)
):
    """
    Importe par lot un dossier de CVs.
    Gestion d'erreur propre : si un CV échoue ou si un fichier est illisible, l'import continue pour les autres !
    """
    if not os.path.exists(directory_path) or not os.path.isdir(directory_path):
        raise HTTPException(status_code=404, detail="Dossier introuvable.")

    job = await get_job_posting()
    job_text = f"{job.titre} chez {job.entreprise}\n{job.description}\n" + "\n".join(job.missions)

    supported_exts = ('*.pdf', '*.md', '*.txt', '*.png', '*.jpg', '*.jpeg')
    files_to_process = []
    for ext in supported_exts:
        files_to_process.extend(glob.glob(os.path.join(directory_path, ext)))
        files_to_process.extend(glob.glob(os.path.join(directory_path, ext.upper())))

    files_to_process = sorted(list(set(files_to_process)))
    if not files_to_process:
        return {"status": "warning", "message": "Aucun fichier supporté trouvé dans ce dossier.", "total": 0}

    imported = []
    failed = []

    for fpath in files_to_process:
        fname = os.path.basename(fpath)
        try:
            with open(fpath, "rb") as f:
                content = f.read()
            cand = await process_and_save_cv(
                filename=fname,
                file_bytes=content,
                job_posting_text=job_text,
                user_role=user_role
            )
            imported.append({
                "filename": fname,
                "id": cand.get("id"),
                "anonymous_id": cand.get("anonymous_id")
            })
        except Exception as e:
            failed.append({
                "filename": fname,
                "error": str(e)
            })

    return {
        "status": "completed",
        "total_files": len(files_to_process),
        "imported_count": len(imported),
        "failed_count": len(failed),
        "imported": imported,
        "failed": failed
    }

@router.get("")
async def get_all_candidates(user_role: UserRole = Query(UserRole.RECRUTEUR)):
    """Liste tous les candidats selon le rôle (Manager voit les profils anonymisés)."""
    return await list_candidates(user_role=user_role)

@router.get("/{candidate_id}")
async def get_candidate_details(candidate_id: str, user_role: UserRole = Query(UserRole.RECRUTEUR)):
    """Fiche détaillée d'un candidat."""
    cand = await get_candidate_by_id(candidate_id, user_role=user_role)
    if not cand:
        raise HTTPException(status_code=404, detail="Candidat introuvable.")
    return cand

@router.get("/{candidate_id}/contact")
async def reveal_contact_info(candidate_id: str, user_role: UserRole = Query(UserRole.RECRUTEUR)):
    """
    Révèle les coordonnées pour prise de contact.
    Bloqué côté code pour le rôle Manager (403 Forbidden).
    """
    try:
        contact = await get_candidate_contact(candidate_id, user_role=user_role)
        if not contact:
            raise HTTPException(status_code=404, detail="Candidat introuvable.")
        return contact
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))

@router.delete("/{candidate_id}")
async def delete_candidate_forget(candidate_id: str, user_role: UserRole = Query(UserRole.RECRUTEUR)):
    """
    Droit à l'oubli complet (Art. 17 RGPD) :
    Supprime le candidat et toutes ses traces de la base.
    Bloqué côté code pour le rôle Manager (403 Forbidden).
    """
    try:
        success = await delete_candidate(candidate_id, user_role=user_role)
        if not success:
            raise HTTPException(status_code=404, detail="Candidat introuvable ou déjà supprimé.")
        return {"status": "success", "message": "Candidat intégralement supprimé (Droit à l'oubli exécuté)."}
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))

@router.get("/{candidate_id}/prompt-context")
async def inspect_prompt_context(candidate_id: str):
    """
    Transparence & Explicabilité (Palier 2) :
    Permet d'inspecter le contexte exact envoyé au modèle (zéro donnée brute, uniquement faits nettoyés).
    """
    cand = await get_candidate_by_id(candidate_id, user_role=UserRole.RECRUTEUR)
    if not cand:
        raise HTTPException(status_code=404, detail="Candidat introuvable.")
    return {
        "candidate_id": cand.get("id"),
        "anonymous_id": cand.get("anonymous_id"),
        "prompt_extraction": cand.get("prompt_context_extraction"),
        "prompt_analysis": cand.get("prompt_context_analysis")
    }

@router.get("/{candidate_id}/export")
async def export_candidate(candidate_id: str, user_role: UserRole = Query(UserRole.RECRUTEUR)):
    """Portabilité des données (Art. 20 RGPD) au format JSON structuré."""
    data = await export_candidate_data(candidate_id, user_role=user_role)
    if not data:
        raise HTTPException(status_code=404, detail="Candidat introuvable.")
    return data

@router.get("/{candidate_id}/notice")
async def get_information_notice(candidate_id: str):
    """Génère la mention d'information pré-remplie à notifier au candidat (Art. 13 RGPD)."""
    notice = await generate_gdpr_notice(candidate_id)
    if not notice:
        raise HTTPException(status_code=404, detail="Candidat introuvable.")
    return {"notice_text": notice}

@router.post("/{candidate_id}/simulate-expiry")
async def simulate_expiry(candidate_id: str, days_in_past: int = 1):
    """Simulation de péremption pour la démo DPO (avance la date d'échéance dans le passé)."""
    success = await simulate_candidate_expiration(candidate_id, days_in_past)
    if not success:
        raise HTTPException(status_code=404, detail="Candidat introuvable.")
    return {"status": "success", "message": f"Date d'échéance simulée au passé ({days_in_past} jours)."}
