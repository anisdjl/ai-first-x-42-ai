PROJET : Atelier Nova Assistant RH
PAR : Anis
EN UNE PHRASE : Une application locale qui analyse des CV sans fuite cloud pour aider Sarah dans ses recrutements.
PALIER : Poussé
OUTILS : FastAPI, MongoDB, Ollama, Ministral 3, Nginx, uv
MÉTHODE : J'ai d'abord fourni la fiche de poste et le CV exemple pour cadrer l'extraction locale. J'ai ensuite développé les filtres RGPD et l'interface pas à pas.
BLOCAGE : La boucle d'événements asyncio bloquait les connexions MongoDB durant les tests. J'ai résolu le problème en liant le client à la boucle courante.
APPRIS :
- Le décodage contraint en JSON évite les hallucinations et garantit des réponses nettes.
- La minimisation des données s'applique dès la mémoire vive sans garder le fichier brut.
LIEN : https://github.com/anisdjl/ai-first-x-42-ai
