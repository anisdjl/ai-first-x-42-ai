from fastapi import APIRouter
from app.config import settings

router = APIRouter(prefix="/api/v1/product-decisions", tags=["Décisions Produit"])

@router.get("")
async def get_product_decisions():
    """
    Retourne les 3 décisions produit RGPD / IA Act tranchées pour l'application.
    À afficher dans l'interface et à défendre lors de la démo devant le DPO.
    """
    return {
        "decision_1_conservation_fichier": {
            "titre": "Décision #1 : Devenir du fichier CV original après extraction",
            "choix": "Suppression immédiate après extraction structurée",
            "justification": settings.DECISION_1_FILE_RETENTION,
            "principe_rgpd": "Minimisation des données (Art. 5.1.c RGPD) & Privacy by Design"
        },
        "decision_2_vue_manager": {
            "titre": "Décision #2 : Visibilité des coordonnées pour le Manager",
            "choix": "Anonymisation stricte (nom, coordonnées masqués)",
            "justification": settings.DECISION_2_MANAGER_ANONYMIZATION,
            "principe_rgpd": "Recrutement anti-biais & Cloisonnement des accès selon le rôle (RBAC)"
        },
        "decision_3_duree_conservation": {
            "titre": "Décision #3 : Durée de conservation des candidatures non retenues",
            "choix": f"{settings.DEFAULT_RETENTION_DAYS} jours (6 mois) avec alerte d'expiration",
            "justification": settings.DECISION_3_RETENTION_PERIOD,
            "principe_rgpd": "Limitation de la conservation (Art. 5.1.e RGPD) sur base de l'intérêt légitime"
        }
    }
