import os
from pydantic import BaseModel

class Settings(BaseModel):
    OLLAMA_URL: str = os.getenv("OLLAMA_URL", "http://localhost:11434")
    OLLAMA_MODEL: str = os.getenv("OLLAMA_MODEL", "ministral-3:3b")
    MONGO_URI: str = os.getenv("MONGO_URI", "mongodb://localhost:27017")
    MONGO_DB_NAME: str = os.getenv("MONGO_DB_NAME", "atelier_nova_hr")
    DEFAULT_RETENTION_DAYS: int = 180  # 6 mois pour vivier candidat

    # Décisions Produit RGPD & IA Act officielles
    DECISION_1_FILE_RETENTION: str = (
        "Suppression immédiate du fichier CV brut dès que l'extraction structurée est terminée. "
        "Garantit la minimisation absolue des données (Privacy by Design)."
    )
    DECISION_2_MANAGER_ANONYMIZATION: str = (
        "Anonymisation stricte pour le rôle Manager (nom, email, téléphone masqués, remplacés par un identifiant anonyme). "
        "Élimine les biais cognitifs et discriminatoires au recrutement."
    )
    DECISION_3_RETENTION_PERIOD: str = (
        "Conservation de 6 mois maximum pour les candidatures non retenues (vivier), "
        "fondée sur l'intérêt légitime (recrutement prévisible). Alerte automatique à l'échéance."
    )

settings = Settings()
