
# Architecture

L'application doit tourner entièrement en local. Le modèle de langage utilisé est ministral 
# Besoins utilisateurs

Nous construisons un copilot RH afin d'aider les responsables des ressources humaines à gérer un processus de recrutement avec des candidats.

Il doit pouvoir :
- charger les cv des candidats et structurer les données sur les candidats en base de donnée:
    - infos nécessaires pour la fiche du candidat: expériences, compétences, formation, langues, liens professionnels, disponibilité du candidat (les stocker et rendre dans une fiche), pas d'infos absentes du CV, ni d'infos inutles
    - infos de contact (les stocker séparément), les rendre visibles pour contacter l'utilisateur
    - informations sans rapport avec le poste (ne pas les conserver)
- le CV est stocké dans la db
- consulter la liste des candidats et pour chacun sa fiche
- charger une fiche de poste
- poser des questions à un chatbot sur les candidats et la fiche de poste
- effacer toutes les données d'un candidat et celles créées par l'application à son sujet, ainsi que son CV

L'application doit pouvoir lui fournir :
- une fiche sur chaque candidat
- un résumé du profil des candidats basé sur leur CV
- des questions à poser aux candidats lors de l'entretien basées sur leur CV et la fiche de poste

- L'application doit fonctionner sans LLM externe, tout doit être local.




