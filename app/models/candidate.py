from typing import List, Optional, Dict
from pydantic import BaseModel, Field
from datetime import datetime

class ContactInfo(BaseModel):
    nom: Optional[str] = None
    email: Optional[str] = None
    telephone: Optional[str] = None
    ville: Optional[str] = None

class ExperienceItem(BaseModel):
    poste: str = ""
    entreprise: str = ""
    ville: Optional[str] = None
    periode: str = ""
    missions: List[str] = []
    technologies: List[str] = []

class EducationItem(BaseModel):
    diplome: str = ""
    etablissement: str = ""
    annee: Optional[str] = None

class LanguageItem(BaseModel):
    langue: str = ""
    niveau: str = ""

class CandidateExtracted(BaseModel):
    """Faits strictement extraits du CV (Zéro hallucination, données sensibles purgées)."""
    experiences: List[ExperienceItem] = []
    competences: List[str] = []
    formation: List[EducationItem] = []
    langues: List[LanguageItem] = []
    liens_professionnels: List[str] = []

class CandidateSummary(BaseModel):
    """Déductions et avis du modèle IA au regard de la fiche de poste."""
    ce_qui_correspond: List[str] = []
    ce_qui_manque: List[str] = []
    a_verifier_en_entretien: List[str] = []

class CandidateInDB(BaseModel):
    id: str
    anonymous_id: str
    source_filename: str
    created_at: datetime
    retention_date: datetime
    is_expired: bool = False
    
    # Coordonnées séparées (Stockées à part)
    contact: ContactInfo
    
    # Faits extraits
    extracted_data: CandidateExtracted
    
    # Déductions IA (Palier 2)
    summary: Optional[CandidateSummary] = None
    interview_questions: List[str] = []
    criteria_evaluation: Dict[str, str] = {}
    
    # Transparence & Explicabilité
    prompt_context_extraction: Optional[str] = None
    prompt_context_analysis: Optional[str] = None

class CandidatePublic(BaseModel):
    id: str
    anonymous_id: str
    source_filename: str
    created_at: datetime
    retention_date: datetime
    is_expired: bool
    
    # Si le rôle est "manager", contact est None / masqué
    contact: Optional[ContactInfo] = None
    
    extracted_data: CandidateExtracted
    summary: Optional[CandidateSummary] = None
    interview_questions: List[str] = []
    criteria_evaluation: Dict[str, str] = {}
