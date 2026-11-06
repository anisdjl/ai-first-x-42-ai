# Atelier Nova - Assistant RH Local (Souverain & RGPD)

Backend haute performance et conforme RGPD / IA Act pour le recrutement chez **Atelier Nova**.  
L'application fonctionne à **100% en local (Air-Gapped)** avec **FastAPI**, **MongoDB** et **Ollama (ministral-3:3b)**.

---

## 🚀 Démarrage Rapide (Makefile)

```bash
# 1. Vérifier qu'Ollama et le modèle ministral-3:3b sont prêts
make ollama-check

# 2. Installer les dépendances avec uv
make install

# 3. Lancer MongoDB et le serveur FastAPI (port 8000)
make run

# 4. Exécuter la suite complète de tests (RGPD, RBAC, extraction)
make test
```

L'API est accessible sur : **`http://localhost:8000`**  
Documentation Swagger interactive : **`http://localhost:8000/docs`**

---

## 📡 Documentation des Endpoints pour le Frontend

### 1. Candidats (Palier 1 & 2)
* **`POST /api/v1/candidates/upload`** : Upload d'un fichier CV (Markdown, PDF, Image scannée PNG/JPG).
* **`POST /api/v1/candidates/batch-import?directory_path=...`** : Import en masse d'un dossier avec tolérance aux pannes (une erreur n'arrête pas l'import).
* **`GET /api/v1/candidates?user_role=recruteur|manager`** : Liste des candidats. Si `role=manager`, les profils sont anonymisés (`CANDIDAT-01`) et les coordonnées masquées.
* **`GET /api/v1/candidates/{id}?user_role=recruteur|manager`** : Fiche détaillée (Faits extraits + Déductions IA séparées).
* **`GET /api/v1/candidates/{id}/contact?user_role=recruteur`** : Révèle le nom, email, téléphone pour contact d'entretien. *(Renvoie `403 Forbidden` pour le rôle Manager)*.
* **`DELETE /api/v1/candidates/{id}?user_role=recruteur`** : Droit à l'oubli total (suppression BDD + index + cache). *(Renvoie `403 Forbidden` pour le rôle Manager)*.

### 2. Transparence, Explicabilité & Q&A (Palier 2)
* **`GET /api/v1/candidates/{id}/prompt-context`** : Permet d'inspecter le prompt exact envoyé au modèle (qui ne reçoit que des profils nettoyés).
* **`GET /api/v1/comparator`** : Tableau comparatif sur les critères explicites de la fiche de poste (sans score global ni classement).
* **`POST /api/v1/chat`** : Chat en langage naturel sur le vivier (*« Qui a déjà travaillé avec des API ? »*).
* **`GET /api/v1/job-posting`** : Consultation de la fiche de poste et critères d'évaluation.

### 3. Conformité DPO & RGPD (Palier 3)
* **`GET /api/v1/candidates/{id}/notice`** : Texte de mention d'information prêt à envoyer au candidat (Art. 13).
* **`GET /api/v1/candidates/{id}/export`** : Export de portabilité complet en JSON (Art. 20).
* **`GET /api/v1/audit/logs`** : Journal d'audit d'accès (`import`, `consultation`, `export`, `effacement`) sans données sensibles de CV.
* **`GET /api/v1/audit/expirations`** : Tableau de bord de suivi des durées de rétention (alerte si > 6 mois).
* **`POST /api/v1/candidates/{id}/simulate-expiry`** : Déclenche la péremption d'un profil pour la démonstration devant le DPO.
* **`GET /api/v1/product-decisions`** : Les 3 décisions produit officielles et leurs justifications juridiques.

---

## 🛡️ Les 3 Décisions Produit (RGPD & IA Act)

1. **Décision #1 (Conservation du fichier brut) :** Suppression immédiate après extraction structurée pour garantir la minimisation absolue des données (*Privacy by Design*).
2. **Décision #2 (Vue Manager) :** Anonymisation stricte pour le Manager afin d'éviter tout biais cognitif et discriminatoire lors de la présélection technique.
3. **Décision #3 (Durée de conservation) :** 6 mois maximum pour le vivier candidat non retenu, fondé sur l'intérêt légitime (Art. 6.1.f RGPD), avec alerte automatique à l'échéance.

---

## 🎯 Les 4 Preuves pour la Démo

1. **Couper le Wi-Fi :** Importer un CV en direct (fonctionne 100% hors-ligne grâce à Ollama + MongoDB en local).
2. **Supprimer un candidat :** Montrer sa disparition immédiate de la liste, de la base et du Q&A.
3. **Transparence & RBAC :**
   - Montrer l'inspection du prompt (`/prompt-context`).
   - Basculer sur le rôle Manager : prouver l'anonymisation et le blocage 403 Forbidden sur la suppression.
   - Simuler une date d'échéance dépassée (`/simulate-expiry`) et montrer l'alerte.
   - Montrer le journal d'audit (`/audit/logs`) après suppression.
4. **Schéma & Registre :** Montrer `carte-cycle-de-vie.md` et `registre-simplifie.md`.
