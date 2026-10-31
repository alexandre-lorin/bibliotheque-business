# Bibliothèque business — moteur local

Code du moteur documentaire local, de la recherche RAG et du serveur MCP.
Le corpus, les livres, les archives, les index, les données personnelles et les
configurations de sources locales ne sont pas inclus dans ce dépôt.

Les fichiers `DEMARRER.md`, `RAG.md` et `pyproject.toml` décrivent le fonctionnement
et les dépendances. Certains documents historiques décrivent le poste original ;
leurs chemins et nombres de documents ne correspondent pas à une installation neuve.

Pour utiliser le moteur, fournir son propre corpus avec les droits nécessaires,
puis reconstruire ses index. Aucun téléchargement ni service automatique n’est
activé par la seule copie de ce dépôt.

Tests unitaires : `python -m unittest discover -s tests -v`. Les scénarios
qui nécessitent un corpus ou des dépendances optionnelles doivent être préparés
séparément.
