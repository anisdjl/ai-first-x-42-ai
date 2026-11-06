import uuid
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Optional
from app.database import get_database
from app.config import settings
from app.models.candidate import (
    CandidateInDB, ContactInfo, CandidateExtracted,
    CandidateSummary, CandidatePublic
)
from app.models.audit import AuditAction, UserRole
from app.services.ollama_service import extract_cv_text, extract_cv_vision, analyze_profile
from app.services.parser_service import parse_file_content
from app.services.audit_service import log_action

async def get_next_anonymous_id() -> str:
    db = get_database()
    count = await db.candidates.count_documents({}) + 1
    return f"CANDIDAT-{count:02d}"

async def process_and_save_cv(
    filename: str,
    file_bytes: bytes,
    job_posting_text: str,
    user_role: UserRole = UserRole.RECRUTEUR
) -> Dict[str, Any]:
    """
    Pipeline complet d'import d'un CV :
    1. Parse en mémoire
    2. Extraction des faits & minimisation (Ollama)
    3. PURGE DU FICHIER BRUT (Décision produit #1)
    4. Analyse IA explicable (Palier 2)
    5. Sauvegarde en DB
    6. Log d'audit (sans contenu brut)
    """
    # 1. Parse
    text_content, image_b64, file_type = parse_file_content(filename, file_bytes)
    
    # 2. Extraction locale
    if file_type == "image":
        extracted_raw, prompt_ext = await extract_cv_vision(image_b64)
    else:
        extracted_raw, prompt_ext = await extract_cv_text(text_content)
        
    # 3. DÉCISION PRODUIT #1 : Purge du fichier brut (garbage collected)
    del file_bytes
    del text_content
    del image_b64

    # 4. Analyse au regard du poste
    analysis_raw, prompt_ana = await analyze_profile(extracted_raw, job_posting_text)

    # 5. Préparation de l'enregistrement
    cand_id = str(uuid.uuid4())
    anon_id = await get_next_anonymous_id()
    now = datetime.now(timezone.utc)
    retention = now + timedelta(days=settings.DEFAULT_RETENTION_DAYS)

    contact = ContactInfo(**(extracted_raw.get("contact") or {}))
    extracted = CandidateExtracted(
        experiences=extracted_raw.get("experiences", []),
        competences=extracted_raw.get("competences", []),
        formation=extracted_raw.get("formation", []),
        langues=extracted_raw.get("langues", []),
        liens_professionnels=extracted_raw.get("liens_professionnels", [])
    )
    
    summary = CandidateSummary(
        ce_qui_correspond=analysis_raw.get("ce_qui_correspond", []),
        ce_qui_manque=analysis_raw.get("ce_qui_manque", []),
        a_verifier_en_entretien=analysis_raw.get("a_verifier_en_entretien", [])
    )

    candidate_db = CandidateInDB(
        id=cand_id,
        anonymous_id=anon_id,
        source_filename=filename,
        created_at=now,
        retention_date=retention,
        is_expired=False,
        contact=contact,
        extracted_data=extracted,
        summary=summary,
        interview_questions=analysis_raw.get("interview_questions", []),
        criteria_evaluation=analysis_raw.get("criteria_evaluation", {}),
        prompt_context_extraction=prompt_ext,
        prompt_context_analysis=prompt_ana
    )

    db = get_database()
    await db.candidates.insert_one(candidate_db.model_dump())

    # 6. Audit Log
    await log_action(
        action=AuditAction.IMPORT,
        user_role=user_role,
        candidate_id=cand_id,
        anonymous_id=anon_id,
        details=f"Import et extraction réussie depuis '{filename}'"
    )

    return candidate_db.model_dump()

async def list_candidates(user_role: UserRole) -> List[Dict[str, Any]]:
    db = get_database()
    cursor = db.candidates.find().sort("created_at", -1)
    results = []
    now = datetime.now(timezone.utc)
    
    async for doc in cursor:
        doc["_id"] = str(doc["_id"])
        # Vérification expiration
        retention = doc.get("retention_date")
        if retention:
            if isinstance(retention, str):
                retention_dt = datetime.fromisoformat(retention)
            else:
                retention_dt = retention
            if retention_dt.tzinfo is None:
                retention_dt = retention_dt.replace(tzinfo=timezone.utc)
            doc["is_expired"] = (now > retention_dt)

        # RBAC & Décision #2 : Masquage contact pour Manager
        if user_role == UserRole.MANAGER:
            doc["contact"] = None
            doc["source_filename"] = f"{doc['anonymous_id']}.pdf"

        results.append(doc)
    return results

async def get_candidate_by_id(candidate_id: str, user_role: UserRole) -> Optional[Dict[str, Any]]:
    db = get_database()
    doc = await db.candidates.find_one({"id": candidate_id})
    if not doc:
        return None
        
    doc["_id"] = str(doc["_id"])
    now = datetime.now(timezone.utc)
    retention = doc.get("retention_date")
    if retention:
        if isinstance(retention, str):
            retention_dt = datetime.fromisoformat(retention)
        else:
            retention_dt = retention
        if retention_dt.tzinfo is None:
            retention_dt = retention_dt.replace(tzinfo=timezone.utc)
        doc["is_expired"] = (now > retention_dt)

    # Log consultation
    await log_action(
        action=AuditAction.CONSULTATION,
        user_role=user_role,
        candidate_id=candidate_id,
        anonymous_id=doc.get("anonymous_id"),
        details="Consultation de la fiche détaillée"
    )

    # RBAC Manager
    if user_role == UserRole.MANAGER:
        doc["contact"] = None
        doc["source_filename"] = f"{doc['anonymous_id']}.pdf"
        
    return doc

async def get_candidate_contact(candidate_id: str, user_role: UserRole) -> Optional[Dict[str, Any]]:
    """Accès aux coordonnées (Strictement interdit au rôle Manager)."""
    if user_role == UserRole.MANAGER:
        raise PermissionError("Accès interdit : Le rôle Manager ne peut pas consulter les coordonnées directes (Décision #2 Anti-biais).")
        
    db = get_database()
    doc = await db.candidates.find_one({"id": candidate_id})
    if not doc:
        return None
        
    await log_action(
        action=AuditAction.CONSULTATION,
        user_role=user_role,
        candidate_id=candidate_id,
        anonymous_id=doc.get("anonymous_id"),
        details="Révélation des coordonnées de contact pour entretien"
    )
    return doc.get("contact")

async def delete_candidate(candidate_id: str, user_role: UserRole) -> bool:
    """
    Droit à l'oubli total (RGPD Art. 17).
    Interdit au rôle Manager (bloqué côté code).
    """
    if user_role == UserRole.MANAGER:
        raise PermissionError("Action interdite : Le rôle Manager n'a pas les privilèges pour supprimer un candidat.")

    db = get_database()
    candidate = await db.candidates.find_one({"id": candidate_id})
    if not candidate:
        return False
        
    anon_id = candidate.get("anonymous_id")
    # Suppression définitive en base
    res = await db.candidates.delete_one({"id": candidate_id})
    
    # Trace RGPD obligatoire dans le journal d'audit (sans données perso)
    await log_action(
        action=AuditAction.EFFACEMENT,
        user_role=user_role,
        candidate_id=candidate_id,
        anonymous_id=anon_id,
        details=f"Suppression définitive et complète du candidat (Droit à l'oubli exercé)"
    )
    return res.deleted_count > 0

async def export_candidate_data(candidate_id: str, user_role: UserRole) -> Optional[Dict[str, Any]]:
    """Portabilité des données (RGPD Art. 20)."""
    db = get_database()
    doc = await db.candidates.find_one({"id": candidate_id})
    if not doc:
        return None
        
    await log_action(
        action=AuditAction.EXPORT,
        user_role=user_role,
        candidate_id=candidate_id,
        anonymous_id=doc.get("anonymous_id"),
        details="Export de portabilité des données détenues sur le candidat"
    )
    
    export_payload = {
        "identifiant_systeme": doc.get("id"),
        "identifiant_anonyme": doc.get("anonymous_id"),
        "date_candidature": str(doc.get("created_at")),
        "date_expiration_prevue": str(doc.get("retention_date")),
        "coordonnees_enregistrees": doc.get("contact"),
        "faits_extraits_cv": doc.get("extracted_data"),
        "deductions_et_synthese_ia": doc.get("summary"),
        "questions_entretien_proposees": doc.get("interview_questions"),
        "mention_rgpd": "Données traitées localement sans aucun transfert externe."
    }
    return export_payload

async def generate_gdpr_notice(candidate_id: str) -> Optional[str]:
    """Génère la mention d'information prête à envoyer au candidat (Art. 13 RGPD)."""
    db = get_database()
    doc = await db.candidates.find_one({"id": candidate_id})
    if not doc:
        return None
        
    nom = doc.get("contact", {}).get("nom") or "Madame, Monsieur"
    retention_date = str(doc.get("retention_date", ""))[:10]
    
    notice = f"""Bonjour {nom},

Nous vous remercions pour votre candidature au poste de Développeur Python chez Atelier Nova.

Conformément au Règlement Général sur la Protection des Données (RGPD), nous vous informons que les données issues de votre CV font l'objet d'un traitement automatisé local :
- Responsable de traitement : Atelier Nova (Sarah, RH)
- Finalité : Évaluation objective de votre candidature pour le poste à pourvoir.
- Base légale : Mesures précontractuelles et intérêt légitime (Art. 6.1.b et 6.1.f RGPD).
- Souveraineté & Confidentialité : Vos données sont traitées 100% en local sur nos machines (modèle open-weight local). Aucun transfert vers un serveur tiers ou cloud n'est opéré.
- Durée de conservation : Vos données sont conservées pendant {settings.DEFAULT_RETENTION_DAYS} jours (échéance au {retention_date}). Passé ce délai, elles seront définitivement purgées.
- Vos droits : Vous disposez d'un droit d'accès, de rectification, de portabilité et d'effacement complet (« droit à l'oubli ») de vos données à tout moment en contactant rh@atelier-nova.example.

Bien cordialement,
L'équipe RH d'Atelier Nova"""
    return notice

async def simulate_candidate_expiration(candidate_id: str, days_in_past: int = 1) -> bool:
    """Helper pour la démo : simule le dépassement d'échéance d'un candidat."""
    db = get_database()
    expired_date = datetime.now(timezone.utc) - timedelta(days=days_in_past)
    res = await db.candidates.update_one(
        {"id": candidate_id},
        {"$set": {"retention_date": expired_date, "is_expired": True}}
    )
    if res.modified_count > 0:
        await log_action(
            action=AuditAction.SIMULATION_EXPIRATION,
            user_role=UserRole.RECRUTEUR,
            candidate_id=candidate_id,
            details=f"Simulation de péremption : date de rétention avancée au {expired_date.isoformat()}"
        )
        return True
    return False
