from pydantic import BaseModel
from typing import List

class CriteriaItem(BaseModel):
    id: str
    label: str
    is_mandatory: bool = True

class JobPosting(BaseModel):
    titre: str = "Développeur ou développeuse Python confirmé(e)"
    entreprise: str = "Atelier Nova"
    description: str = "Éditeur logiciel de gestion de production industrielle à Nantes."
    missions: List[str] = [
        "Faire évoluer le backend du logiciel, écrit en Python.",
        "Concevoir et maintenir les API utilisées par l'application et les terminaux d'atelier.",
        "Écrire les tests et participer à la revue de code.",
        "Participer à la mise en production et au suivi en exploitation.",
        "Accompagner les développeurs moins expérimentés."
    ]
    criteres_explicites: List[CriteriaItem] = [
        CriteriaItem(id="python_backend", label=">= 5 ans backend Python", is_mandatory=True),
        CriteriaItem(id="django_fastapi", label="Django ou FastAPI en production", is_mandatory=True),
        CriteriaItem(id="api_rest", label="Conception d'API REST", is_mandatory=True),
        CriteriaItem(id="postgresql", label="PostgreSQL / BDD relationnelle", is_mandatory=True),
        CriteriaItem(id="tests_git", label="Tests automatisés (pytest) et Git", is_mandatory=True),
        CriteriaItem(id="anglais", label="Anglais technique écrit", is_mandatory=True),
        CriteriaItem(id="docker_ci", label="Docker & Intégration continue (Plus)", is_mandatory=False),
        CriteriaItem(id="gestion_industrie", label="Logiciels gestion / industrie (Plus)", is_mandatory=False),
        CriteriaItem(id="mentorat_junior", label="Accompagnement développeurs juniors (Plus)", is_mandatory=False),
    ]
