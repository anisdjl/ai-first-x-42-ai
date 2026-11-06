import httpx
import json
import logging
from typing import Dict, Any, Tuple, List
from app.config import settings

logger = logging.getLogger(__name__)

SYSTEM_PROMPT_EXTRACTION = """Tu es un assistant RH technique strict, conforme au RGPD et à l'IA Act européen.
Ta mission est d'extraire UNIQUEMENT les faits professionnels pertinents d'un CV technique.

RÈGLES D'OR RGPD & MINIMISATION :
1. PURGE TOTALE DES DONNÉES SENSIBLES / INUTILES : Tu dois TOTALEMENT IGNORER et NE PAS EXTRAIRE :
   - Âge, date de naissance, situation de famille, statut marital, enfants
   - Nationalité, origine, religion, opinions politiques, santé
   - Hobbies, centres d'intérêt personnels et loisirs hors sujet
2. SÉPARATION DES COORDONNÉES : Place nom, email, téléphone et ville dans l'objet 'contact'.
3. ZÉRO HALLUCINATION : Si une information est absente, laisse une liste vide [] ou null. N'invente AUCUNE technologie ni entreprise.
4. FORMAT DE SORTIE : Réponds STRICTEMENT avec un objet JSON valide suivant ce format :
{
  "contact": {
    "nom": "string ou null",
    "email": "string ou null",
    "telephone": "string ou null",
    "ville": "string ou null"
  },
  "experiences": [
    {
      "poste": "string",
      "entreprise": "string",
      "ville": "string ou null",
      "periode": "string",
      "missions": ["string"],
      "technologies": ["string"]
    }
  ],
  "competences": ["string"],
  "formation": [
    {
      "diplome": "string",
      "etablissement": "string",
      "annee": "string ou null"
    }
  ],
  "langues": [
    {
      "langue": "string",
      "niveau": "string"
    }
  ],
  "liens_professionnels": ["string"]
}"""

SYSTEM_PROMPT_ANALYSIS = """Tu es un assistant d'aide à la décision pour recruteur, conforme à l'IA Act.
INTERDICTION FORMELLE :
- Ne génère AUCUN score numérique (ex: pas de 8/10).
- Ne fais AUCUN classement de candidats.
- Ne rends AUCUN verdict d'embauche unilatéral (ex: pas de 'Recommandé / Refusé'). L'humain décide seul.

Ta mission est de fournir une synthèse factuelle et transparente du profil au regard des exigences du poste.

FORMAT DE SORTIE : Réponds STRICTEMENT avec un JSON valide :
{
  "ce_qui_correspond": ["points forts alignés avec les missions et compétences demandées"],
  "ce_qui_manque": ["éléments de la fiche de poste non retrouvés dans le profil"],
  "a_verifier_en_entretien": ["questions clés ou doutes techniques à éclaircir lors de l'échange"],
  "criteria_evaluation": {
    "python_backend": "Conforme (ex: 7 ans) / Partiel / Non mentionné",
    "django_fastapi": "Conforme / Partiel / Non mentionné",
    "api_rest": "Conforme / Partiel / Non mentionné",
    "postgresql": "Conforme / Partiel / Non mentionné",
    "tests_git": "Conforme / Partiel / Non mentionné",
    "anglais": "Conforme (ex: B2) / Non mentionné",
    "docker_ci": "Conforme / Non mentionné",
    "gestion_industrie": "Conforme / Non mentionné",
    "mentorat_junior": "Conforme / Non mentionné"
  },
  "interview_questions": [
    "Question technique 1 personnalisée selon le parcours",
    "Question technique 2 personnalisée",
    "Question 3 sur l'organisation ou les missions"
  ]
}"""

async def call_ollama(messages: List[Dict[str, Any]], format_json: bool = True, images: List[str] = None) -> str:
    url = f"{settings.OLLAMA_URL}/api/chat"
    payload = {
        "model": settings.OLLAMA_MODEL,
        "messages": messages,
        "stream": False,
        "options": {
            "temperature": 0.1,
            "num_predict": 2048
        }
    }
    if format_json:
        payload["format"] = "json"

    async with httpx.AsyncClient(timeout=120.0) as client:
        try:
            resp = await client.post(url, json=payload)
            resp.raise_for_status()
            data = resp.json()
            return data.get("message", {}).get("content", "")
        except httpx.HTTPError as e:
            logger.error(f"Erreur d'appel Ollama : {e}")
            raise RuntimeError(f"Ollama injoignable ou en erreur : {str(e)}")

async def extract_cv_text(cv_text: str) -> Tuple[Dict[str, Any], str]:
    """Extrait les faits minimisés du CV texte (Markdown/PDF textuel)."""
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT_EXTRACTION},
        {"role": "user", "content": f"Voici le texte brut du CV à extraire :\n\n{cv_text}"}
    ]
    prompt_context = f"[SYSTEM]\n{SYSTEM_PROMPT_EXTRACTION}\n\n[USER]\nVoici le texte brut du CV à extraire :\n\n{cv_text}"
    content = await call_ollama(messages, format_json=True)
    try:
        data = json.loads(content)
        return data, prompt_context
    except json.JSONDecodeError:
        # Fallback nettoyage markdown json
        cleaned = content.strip().strip("```json").strip("```").strip()
        return json.loads(cleaned), prompt_context

async def extract_cv_vision(image_base64: str) -> Tuple[Dict[str, Any], str]:
    """Extrait un CV image scanné via les capacités Vision de ministral-3."""
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT_EXTRACTION},
        {
            "role": "user",
            "content": "Voici l'image scannée du CV. Extrais rigoureusement les informations demandées au format JSON :",
            "images": [image_base64]
        }
    ]
    prompt_context = f"[SYSTEM]\n{SYSTEM_PROMPT_EXTRACTION}\n\n[USER (VISION)]\nImage scannée (base64 transmise au modèle vision local)"
    content = await call_ollama(messages, format_json=True)
    try:
        data = json.loads(content)
        return data, prompt_context
    except json.JSONDecodeError:
        cleaned = content.strip().strip("```json").strip("```").strip()
        return json.loads(cleaned), prompt_context

async def analyze_profile(extracted_facts: Dict[str, Any], job_posting_text: str) -> Tuple[Dict[str, Any], str]:
    """Synthèse & explicabilité du profil par rapport au poste (sans score ni classement)."""
    facts_str = json.dumps(extracted_facts, indent=2, ensure_ascii=False)
    user_prompt = (
        f"Voici la fiche de poste :\n{job_posting_text}\n\n"
        f"Voici la fiche nettoyée du candidat (faits uniquement, zéro données personnelles non pertinentes) :\n{facts_str}\n\n"
        f"Produis l'analyse structurée demandée au format JSON strict."
    )
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT_ANALYSIS},
        {"role": "user", "content": user_prompt}
    ]
    prompt_context = f"[SYSTEM]\n{SYSTEM_PROMPT_ANALYSIS}\n\n[USER]\n{user_prompt}"
    content = await call_ollama(messages, format_json=True)
    try:
        data = json.loads(content)
        return data, prompt_context
    except json.JSONDecodeError:
        cleaned = content.strip().strip("```json").strip("```").strip()
        return json.loads(cleaned), prompt_context

async def ask_chat_pool(query: str, candidates_facts: List[Dict[str, Any]], job_posting_text: str) -> str:
    """Chat Q&A sur les profils nettoyés en local."""
    system_prompt = (
        "Tu es l'assistant RH local d'Atelier Nova. Tu réponds aux questions du recruteur sur le vivier de candidats.\n"
        "RÈGLES :\n"
        "- Base tes réponses UNIQUEMENT sur les fiches nettoyées fournies ci-dessous.\n"
        "- Cite précisément les candidats concernés par leur identifiant.\n"
        "- Ne produis aucun classement global, score ou jugement éliminatoire.\n"
        "- Sois concis, factuel et précis."
    )
    pool_data = []
    for c in candidates_facts:
        pool_data.append({
            "identifiant": c.get("anonymous_id"),
            "competences": c.get("extracted_data", {}).get("competences", []),
            "experiences": [
                f"{exp.get('poste')} chez {exp.get('entreprise')} ({exp.get('periode')}) : {', '.join(exp.get('missions', []))}"
                for exp in c.get("extracted_data", {}).get("experiences", [])
            ],
            "langues": c.get("extracted_data", {}).get("langues", [])
        })

    user_msg = (
        f"Fiche de poste : {job_posting_text[:500]}...\n\n"
        f"Données nettoyées des candidats disponibles :\n{json.dumps(pool_data, ensure_ascii=False, indent=1)}\n\n"
        f"Question du recruteur : {query}"
    )

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_msg}
    ]
    answer = await call_ollama(messages, format_json=False)
    return answer
