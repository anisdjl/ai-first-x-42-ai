# Carte du cycle de vie des données (Data Lifecycle)

Ce document décrit le trajet réel d'un CV au sein de l'application **Atelier Nova Assistant RH**, les copies créées à chaque étape, leur localisation, et les droits d'accès associés.

```mermaid
flowchart TD
    subgraph S0["0. Réception du CV"]
        A["Fichier source (.pdf / .md / scan image)"]
    end

    subgraph S1["1. Import & Parsing (En Mémoire)"]
        B["Lecture en flux mémoire (RAM)"]
        C["Purge immédiate du fichier brut en RAM (Décision #1)"]
    end

    subgraph S2["2. Extraction & Analyse (Modèle Local)"]
        D["Appel local Ollama (ministral-3:3b)"]
        E["Extraction structurée & minimisation (Faits uniquement)"]
        F["Génération synthèse & questions (Déductions séparées)"]
    end

    subgraph S3["3. Stockage & Ségrégation (MongoDB Local)"]
        G["Coordonnées de contact (Nom, email, tél, ville)"]
        H["Fiche technique nettoyée (Expériences, compétences, etc.)"]
        I["Déductions IA explicables + Prompt context"]
    end

    subgraph S4["4. Accès & Rôles (RBAC)"]
        J["Sarah (Recruteuse) : Accès complet + Contact + Suppression"]
        K["Manager : Profil anonymisé, Coordonnées masquées, Suppression bloquée"]
    end

    subgraph S5["5. Effacement & Fin de cycle"]
        L["Droit à l'oubli (Art. 17 RGPD) ou Péremption (6 mois)"]
        M["Suppression irréversible dans MongoDB"]
        N["Journal d'audit : Événement tracé SANS contenu de CV"]
    end

    A --> B
    B --> D
    D --> E
    E --> C
    E --> F
    E --> H
    D --> G
    F --> I
    G -.-> J
    H --> J
    H --> K
    I --> J
    I --> K
    J --> L
    L --> M
    L --> N
```

---

## Tableau de traçabilité des copies et localisations

| Étape | Copie créée | Support / Emplacement | Données présentes | Durée de vie | Accès autorisé |
|---|---|---|---|---|---|
| **1. Réception** | Fichier importé | Disque local de la machine RH | CV brut d'origine (pouvant contenir âge, photo, etc.) | Temporaire (upload) | Recruteur uniquement |
| **2. Import** | Buffer binaire | RAM applicative (FastAPI) | Données brutes en mémoire tampon | Quelques millisecondes (détruit dès l'extraction) | Processus backend |
| **3. Modèle IA** | Prompt éphémère | RAM / VRAM locale (Ollama / ministral-3:3b) | Texte brut du CV (Air-gapped, zéro réseau) | Durée de l'inférence (~5-8s) | Modèle local |
| **4. Stockage Contact** | Document JSON isolé | MongoDB local (`collection: candidates.contact`) | Nom, prénom, email, téléphone, ville | 6 mois max ou jusqu'à demande d'oubli | **Recruteur uniquement** (403 pour le Manager) |
| **5. Stockage Technique** | Document JSON structuré | MongoDB local (`collection: candidates.extracted_data`) | Expériences, compétences, diplômes, langues, liens pro | 6 mois max ou jusqu'à demande d'oubli | Recruteur et Manager (anonymisé) |
| **6. Audit** | Log d'événement | MongoDB local (`collection: audit_logs`) | Timestamp, Rôle, Action (`import`, `effacement`, etc.), ID | 1 an (obligation de traçabilité) | DPO et Administrateur (**Zéro texte de CV**) |
| **7. Effacement** | **Aucune copie résiduelle** | Purge complète | Données écrasées en BDD | 0 seconde | Action irréversible |
