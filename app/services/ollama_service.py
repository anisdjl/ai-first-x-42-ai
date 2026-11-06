import httpx
import json
import logging
import re
from typing import Dict, Any, Tuple, List, Union
from app.config import settings

logger = logging.getLogger(__name__)

def strip_markdown(text: str) -> str:
    """Supprime tout balisage markdown (astérisques, dièses, puces, backticks, tirets)."""
    if not isinstance(text, str):
        return ""
    # Retire le gras (**), italique (*), titres (#), code (`), tildes (~)
    text = re.sub(r'[*_#`~]', '', text)
    # Retire les préfixes de listes markdown (ex: "- ", "* ", "1. ")
    text = re.sub(r'^\s*([-*•]|\d+\.)\s*', '', text)
    # Nettoie les espaces multiples
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def truncate_chars(text: str, max_chars: int = 120) -> str:
    """Nettoie le markdown et tronque proprement à max_chars caractères."""
    clean = strip_markdown(text)
    if len(clean) <= max_chars:
        return clean
    # Coupe au dernier mot complet
    truncated = clean[:max_chars].rsplit(' ', 1)[0]
    return truncated + "..."

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

SYSTEM_PROMPT_ANALYSIS = """Tu es un assistant technique d'aide au recrutement chez Atelier Nova, conforme à l'IA Act.
INTERDICTIONS FORMELLES :
- AUCUN score chiffré, AUCUN classement, AUCUN verdict unilatéral (l'humain décide seul).
- AUCUN FORMAT MARKDOWN : Interdiction stricte d'utiliser du gras (**), de l'italique (*), des dièses (#) ou des tirets dans les textes.
- AUCUN BAVARDAGE : Réponses courtes, précises, percutantes et factuelles.

CONTRAINTES DE LONGUEUR ET CONTENU :
1. 'ce_qui_correspond' : 2 à 4 éléments. MAXIMUM 120 caractères par puce (texte brut).
2. 'ce_qui_manque' : 2 à 4 éléments. MAXIMUM 120 caractères par puce (texte brut).
3. 'a_verifier_en_entretien' : 2 à 4 éléments. MAXIMUM 120 caractères par puce (texte brut).
4. 'interview_questions' : EXACTEMENT 3 À 5 QUESTIONS MAXIMUM. Directes, techniques, courtes, en texte brut sans puces ni astérisques."""

# Schéma JSON pour constrained decoding avec Ollama
ANALYSIS_JSON_SCHEMA = {
    "type": "object",
    "properties": {
        "ce_qui_correspond": {
            "type": "array",
            "items": {"type": "string"},
            "maxItems": 4
        },
        "ce_qui_manque": {
            "type": "array",
            "items": {"type": "string"},
            "maxItems": 4
        },
        "a_verifier_en_entretien": {
            "type": "array",
            "items": {"type": "string"},
            "maxItems": 4
        },
        "criteria_evaluation": {
            "type": "object",
            "properties": {
                "python_backend": {"type": "string"},
                "django_fastapi": {"type": "string"},
                "api_rest": {"type": "string"},
                "postgresql": {"type": "string"},
                "tests_git": {"type": "string"},
                "anglais": {"type": "string"},
                "docker_ci": {"type": "string"},
                "gestion_industrie": {"type": "string"},
                "mentorat_junior": {"type": "string"}
            }
        },
        "interview_questions": {
            "type": "array",
            "items": {"type": "string"},
            "maxItems": 5
        }
    },
    "required": ["ce_qui_correspond", "ce_qui_manque", "a_verifier_en_entretien", "criteria_evaluation", "interview_questions"]
}

async def call_ollama(messages: List[Dict[str, Any]], format_type: Union[str, dict] = "json", images: List[str] = None) -> str:
    url = f"{settings.OLLAMA_URL}/api/chat"
    payload = {
        "model": settings.OLLAMA_MODEL,
        "messages": messages,
        "stream": False,
        "options": {
            "temperature": 0.1,
            "num_predict": 1500
        }
    }
    if format_type:
        payload["format"] = format_type

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
    content = await call_ollama(messages, format_type="json")
    try:
        data = json.loads(content)
        return data, prompt_context
    except json.JSONDecodeError:
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
    content = await call_ollama(messages, format_type="json")
    try:
        data = json.loads(content)
        return data, prompt_context
    except json.JSONDecodeError:
        cleaned = content.strip().strip("```json").strip("```").strip()
        return json.loads(cleaned), prompt_context

async def analyze_profile(extracted_facts: Dict[str, Any], job_posting_text: str) -> Tuple[Dict[str, Any], str]:
    """
    Synthèse & questions d'entretien :
    - Contrainte decoding via ANALYSIS_JSON_SCHEMA (max 5 questions, max 4 items/section)
    - Nettoyage strict anti-markdown et limitation à 120 caractères par puce.
    """
    facts_str = json.dumps(extracted_facts, indent=2, ensure_ascii=False)
    user_prompt = (
        f"Voici la fiche de poste :\n{job_posting_text}\n\n"
        f"Voici la fiche nettoyée du candidat :\n{facts_str}\n\n"
        f"Produis la synthèse (max 120 car./puce, sans markdown) et exactement 3 à 5 questions courtes."
    )
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT_ANALYSIS},
        {"role": "user", "content": user_prompt}
    ]
    prompt_context = f"[SYSTEM]\n{SYSTEM_PROMPT_ANALYSIS}\n\n[USER]\n{user_prompt}"
    content = await call_ollama(messages, format_type=ANALYSIS_JSON_SCHEMA)
    
    try:
        raw_data = json.loads(content)
    except json.JSONDecodeError:
        cleaned = content.strip().strip("```json").strip("```").strip()
        raw_data = json.loads(cleaned)

    # Post-traitement strict des contraintes
    final_correspond = [truncate_chars(x, 120) for x in raw_data.get("ce_qui_correspond", []) if x][:4]
    final_manque = [truncate_chars(x, 120) for x in raw_data.get("ce_qui_manque", []) if x][:4]
    final_verifier = [truncate_chars(x, 120) for x in raw_data.get("a_verifier_en_entretien", []) if x][:4]
    
    # Questions : strictement entre 1 et 5 questions, texte brut sans markdown
    raw_questions = raw_data.get("interview_questions", [])
    final_questions = [strip_markdown(q) for q in raw_questions if q and strip_markdown(q)][:5]
    if len(final_questions) == 0:
        final_questions = [
            "Pouvez-vous décrire un projet backend complexe en Python que vous avez mené ?",
            "Comment gérez-vous la conception et la version des API REST en production ?",
            "Quelle est votre approche des tests automatisés avec pytest ?"
        ]

    sanitized_data = {
        "ce_qui_correspond": final_correspond,
        "ce_qui_manque": final_manque,
        "a_verifier_en_entretien": final_verifier,
        "criteria_evaluation": raw_data.get("criteria_evaluation", {}),
        "interview_questions": final_questions
    }
    return sanitized_data, prompt_context

async def ask_chat_pool(query: str, candidates_facts: List[Dict[str, Any]], job_posting_text: str) -> str:
    """Chat Q&A sur les profils nettoyés en local (précis, court, direct)."""
    system_prompt = (
        "Tu es l'assistant RH local d'Atelier Nova. Tu réponds aux questions du recruteur sur le vivier de candidats.\n"
        "RÈGLES STRICTES DE RÉPONSE :\n"
        "- Base tes réponses UNIQUEMENT sur les fiches nettoyées fournies ci-dessous.\n"
        "- Rends une réponse COURTE ET PRÉCISE (maximum 3 à 4 phrases ou 3 puces directes).\n"
        "- Cite expressément les identifiants des candidats (ex: CANDIDAT-01).\n"
        "- Aucun score chiffré, aucun classement.\n"
        "- Zéro bavardage inutile, va droit au but."
    )
    pool_data = []
    for c in candidates_facts:
        pool_data.append({
            "identifiant": c.get("anonymous_id"),
            "competences": c.get("extracted_data", {}).get("competences", [])[:10],
            "experiences": [
                f"{exp.get('poste')} chez {exp.get('entreprise')} ({exp.get('periode')})"
                for exp in c.get("extracted_data", {}).get("experiences", [])[:3]
            ],
            "langues": c.get("extracted_data", {}).get("langues", [])
        })

    user_msg = (
        f"Fiche de poste : {job_posting_text[:350]}...\n\n"
        f"Vivier nettoyé :\n{json.dumps(pool_data, ensure_ascii=False)}\n\n"
        f"Question du recruteur : {query}"
    )

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_msg}
    ]
    answer = await call_ollama(messages, format_type="")
    # Nettoie un éventuel surplus de markdown
    return strip_markdown(answer)
