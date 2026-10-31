# Recherche RAG locale — version 0.2

Le système retrouve des passages dans la bibliothèque, puis les fournit avec leurs sources à Codex. Codex produit la réponse. Aucun autre modèle de conversation, compte payant ou service distant n'est nécessaire à la recherche.

## Ce qui est installé dans ce dossier

- `.venv/` : environnement Python isolé, dépendances verrouillées dans `requirements-lock.txt`.
- `models/multilingual-e5-small/` : modèle d'embeddings multilingue ONNX, téléchargé à une révision précise.
- `data/rag.sqlite` : passages, index lexical FTS5, cache de vecteurs et état de l'indexation.
- `rag.py` : recherche hybride, lecture paginée et préparation de contexte.
- `mcp_server.py` : quatre outils documentaires MCP en stdio.
- `books.py` : import de livres et téléchargement explicite de copies autorisées.
- `sync.py` : indexation incrémentale et surveillance facultative.
- `DEMAIN.sh` : activation globale des skills, du MCP, de la commande terminal et de la surveillance.

La recherche et le MCP ne téléchargent pas de contenu. Une fois le modèle préparé, l'inférence utilise les fichiers locaux. La télémétrie Hugging Face et les événements de télémétrie ONNX sont désactivés dans le code de recherche. Le système n'expose aucun port réseau.

## Recherche

```sh
cd '/home/toubi/01 - Dev/bibliotheque-business'
.venv/bin/python rag.py search 'Comment expliquer le prix d’un abonnement facturé à l’année ?'
.venv/bin/python rag.py context 'Comment mener un entretien client ?' --max-chars 12000
.venv/bin/python rag.py search 'offre commerciale' --lang fr
.venv/bin/python rag.py search 'startup leadership' --include-references --source stanford
.venv/bin/python rag.py search 'annual billing' --mode semantic
.venv/bin/python rag.py status
```

Par défaut, les références seules sont exclues. Les résultats portent `document_id`, `chunk_id`, chemin, source, section, page quand elle existe, offsets de caractères, droits et canaux de récupération. Pour lire la suite : `.venv/bin/python rag.py read IDENTIFIANT --start 12000`.

Le contexte est borné en **caractères**, pas en tokens. Les scores sont des rangs de récupération, pas des probabilités de vérité. Le système peut retrouver un passage voisin sans qu'il réponde à la question : Codex doit reconnaître une preuve manquante et vérifier les informations changeantes.

## Indexation

Les Markdown restent les sources de vérité. `data/rag.sqlite` est un index dérivé séparé de l'ancien index lexical. Le découpage conserve la totalité du texte et ses offsets, avec recouvrement pour garder les transitions.

Les embeddings utilisent `intfloat/multilingual-e5-small`, révision `614241f622f53c4eeff9890bdc4f31cfecc418b3`, fichier ONNX quantifié. Les préfixes `query:` et `passage:` sont appliqués. Les entrées trop longues sont représentées par plusieurs fenêtres de 450 tokens, puis une moyenne pondérée normalisée ; elles ne sont pas simplement tronquées à 512 tokens. Ce choix est propre à cette intégration, pas une recommandation garantie du producteur.

Les candidats lexicaux et sémantiques sont fusionnés par Reciprocal Rank Fusion. Les résultats limitent la répétition d'un même document et les passages qui se chevauchent fortement. SQLite et NumPy suffisent à cette taille de bibliothèque ; il n'y a pas de serveur Qdrant supplémentaire.

La synchronisation compare les empreintes des documents et réutilise les vecteurs par contenu et version du modèle. Les lots réussis sont conservés après interruption. Un verrou sérialise les indexeurs ; WAL permet aux recherches de lire les données déjà validées. Une suppression de fichier retire uniquement ses entrées dérivées de l'index, jamais un original archivé.

```sh
.venv/bin/python sync.py
.venv/bin/python sync.py --watch --interval 60
```

`sources-locales.yaml` sélectionne trois documents centraux de projets et les deux skills originaux de cette bibliothèque. Les copies indexées des skills restent documentaires. Le système n'aspire pas les dossiers personnels ni les dépôts entiers. Modifier cette liste permet d'ajouter volontairement un Markdown de contexte ; ne pas y placer de fichiers contenant des secrets.

Pour un rafraîchissement sans surveillance : `.venv/bin/python rag.py index`. `--lexical-only` prépare les passages sans calcul vectoriel. L'ancien `python biblio.py search ...` reste utilisable sans les dépendances RAG.

## Livres et documents

Formats pris en charge : PDF avec texte, EPUB lisible, TXT, MD et HTML UTF-8. Les PDF numérisés sans texte sont signalés comme nécessitant un OCR ; aucun faux contenu n'est généré. Les numéros de page indiquent la position dans le PDF, pas nécessairement la pagination imprimée. L'EPUB suit l'ordre de lecture du livre ; ses sections sont numérotées pour le repérage, sans prétendre reproduire les numéros de chapitre de l'éditeur. Les documents signalant un chiffrement sont refusés ; aucun DRM n'est contourné. Les originaux sont archivés avec empreinte SHA-256.

```sh
.venv/bin/python books.py import '/chemin/mon-livre.epub' \
  --title 'Mon livre' --author 'Auteur' --lang fr \
  --rights personal-copy --evidence 'Copie personnelle acquise légalement ; usage local'
.venv/bin/python sync.py
```

Les droits sont déclarés à l'import, pas validés juridiquement par le programme. Ils restent joints aux passages. La possession d'une copie ne donne pas automatiquement le droit d'en redistribuer le texte ou de l'utiliser pour entraîner un modèle.

Pour déposer des documents à importer, utiliser `entrees/`, accompagné d'un fichier JSON :

```json
{
  "file": "mon-livre.pdf",
  "title": "Mon livre",
  "author": "Auteur",
  "language": "fr",
  "rights": "personal-copy",
  "evidence": "Copie personnelle acquise légalement ; usage local"
}
```

Le fichier doit se trouver dans `entrees/`. Sans cette déclaration, il n'est pas importé. Les originaux déposés ne sont pas supprimés automatiquement.

La commande `books.py download URL --title ... --rights ... --evidence ... --format pdf` télécharge une copie autorisée, avec une limite de 80 Mo. Les paramètres de liens signés ne sont pas conservés dans le catalogue.

## Recherche de livres et Anna’s Archive

**Mode navigateur sans clé : [ANNA-NAVIGATEUR.md](ANNA-NAVIGATEUR.md).** Mise à jour : [détection des domaines et OCR local](ANNA-DOMAINES-OCR.md). `.gl`, `.pk` et `.gd` ont répondu aux contrôles d'accueil ; `.gl` est préféré. La recherche reste soumise à une vérification, et l'OCR public n'est pas validé de bout en bout. Aucun téléchargement réel Anna’s Archive n'est annoncé comme réussi.

```sh
.venv/bin/python books.py search 'copywriting'
.venv/bin/python books.py anna-search 'Scientific Advertising Claude Hopkins'
```

La première commande consulte le catalogue Open Library. La seconde prépare une URL de recherche à ouvrir ; elle n'établit ni disponibilité ni droits. Des outils tiers Anna’s Archive existent déjà, notamment [YassineAta/anna-archive](https://github.com/YassineAta/anna-archive). Ce dépôt n'a pas été installé ni exécuté.

Notre commande optionnelle `books.py anna-download MD5 --title ... --rights ... --evidence ... --format epub` utilise le mécanisme d'API membre documenté par ce projet. Elle nécessite votre propre variable `ANNA_ARCHIVE_API_KEY` et un accès valide ; aucun abonnement n'est créé. La clé n'est ni imprimée ni enregistrée. Le lien signé reste en mémoire et la référence conservée est la page publique de la notice. Aucun captcha, quota ou paywall n'est contourné.

**L'API Anna’s Archive n'a pas été validée en conditions réelles** : aucun compte ou clé n'a été fourni, et la FAQ officielle n'était pas accessible lors de la préparation. Le module reste optionnel ; l'import local et le téléchargement ouvert ont été testés séparément.

## Accès Codex

Le MCP fournit `search_library`, `library_context`, `read_library_document` et `library_status`. Ils consultent les index sans importer de fichiers, télécharger de livres ou envoyer de messages. Le serveur reçoit seulement les requêtes nécessaires à la recherche locale. Les documents tiers restent des données non fiables, y compris lorsqu'ils contiennent un SKILL.md.

La configuration de projet est dans `.codex/config.toml`. Codex ne la charge que pour un projet approuvé. L'activation globale est dans [DEMAIN.md](DEMAIN.md) ; elle ne peut pas être appliquée depuis la session restreinte qui a préparé le projet.

## Sources techniques

- [Codex et MCP — documentation officielle OpenAI](https://developers.openai.com/codex/mcp/).
- [SDK MCP Python](https://py.sdk.modelcontextprotocol.io/run/).
- [Modèle multilingue E5](https://huggingface.co/intfloat/multilingual-e5-small).
- [FastEmbed](https://github.com/qdrant/fastembed).
- [API Open Library](https://openlibrary.org/developers/api).

La validation, les limites et les résultats des vérifications figurent dans `VALIDATION-RAG.md` et `data/`.
