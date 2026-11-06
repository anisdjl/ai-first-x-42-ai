# Registre simplifié

À remplir pendant le build. La fiche décrit ce qui est réellement construit,
limites comprises.

**Application :** Atelier Nova - Assistant RH Local (Souverain & Air-Gapped)  
**Équipe :** Anis & Co  
**Palier atteint :** Palier 3 (Poussé - Vision, Échéances, Droit à l'oubli, Audit RGPD, Portabilité, RBAC)  

| Rubrique | À renseigner | Votre réponse |
| --- | --- | --- |
| **Finalité** | Pourquoi l'application traite ces données. | Traitement d'aide au recrutement pour le poste de Développeur Python confirmé chez Atelier Nova : extraction objective des compétences techniques et parcours, synthèse d'adéquation au poste, sans score automatisé, sans classement et sans verdict unilatéral (IA Act compliant). |
| **Personnes et données** | Qui est concerné, quelles données sont gardées, lesquelles sont écartées. | **Personnes concernées :** Candidats ayant postulé au poste.<br>**Données gardées :** Compétences, expériences, formation/diplômes, langues, liens professionnels, et coordonnées de contact (stockées de façon séparée).<br>**Données strictement écartées et purgées :** Âge, date de naissance, situation matrimoniale/familiale, enfants, nationalité, religion, santé, loisirs/hobbies personnels non professionnels. |
| **Base légale** | Laquelle, et pourquoi. Le consentement n'est pas la réponse par défaut. | **Mesures précontractuelles (Art. 6.1.b RGPD)** pour l'instruction de la candidature déposée.<br>**Intérêt légitime (Art. 6.1.f RGPD)** pour la constitution temporaire d'un vivier de recrutement pour des besoins prévisibles à court terme. (Pas de consentement par défaut car déséquilibre candidat/employeur). |
| **Accès et destinataires** | Qui voit quoi, selon son rôle. | **Recruteur (Sarah) :** Accès complet aux fiches, possibilité de révéler les coordonnées de contact pour entretien, droit de suppression totale (oubli).<br>**Manager :** Accès aux compétences et synthèses sous forme **anonymisée** (`CANDIDAT-XX`). Coordonnées masquées (anti-biais cognitif). Suppression bloquée par contrôle côté code (403 Forbidden). |
| **Stockage et localisation** | Où vivent les fichiers, la base, l'index, les copies éventuelles. | **100% Local (Air-Gapped) :** Base de données MongoDB sur `localhost:27017`. Modèle d'inférence `ministral-3:3b` hébergé localement sur Ollama (`localhost:11434`). Zéro envoi vers le Cloud, zéro API externe. Le fichier CV brut est détruit de la mémoire dès l'extraction achevée (Décision #1). |
| **Durée et suppression** | Combien de temps, et comment l'effacement se fait. | **Durée :** 6 mois (180 jours) maximum pour le vivier (Décision #3). Alerte automatique d'échéance dans le système.<br>**Suppression :** Bouton de suppression totale immédiate (Droit à l'oubli Art. 17 RGPD) supprimant le candidat de MongoDB et du cache. L'événement est archivé dans le log sans données personnelles. |
| **Sécurité** | Contrôle d'accès, chiffrement si pertinent, journaux maîtrisés. | - RBAC strict appliqué dans les contrôles API backend (pas seulement masquage UI).<br>- Isolation réseau complète (fonctionne Wi-Fi coupé).<br>- Journal d'audit d'accès (`import`, `consultation`, `export`, `effacement`) horodaté avec identifiant anonyme et **zéro contenu de CV loggé**. |
