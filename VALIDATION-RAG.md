# Validation RAG — 27 octobre 2026

Version 0.2. Installation dans `/home/toubi/01 - Dev/bibliotheque-business`, sans modification de la configuration globale de Codex ni activation de service utilisateur pendant la préparation.

Ajout ultérieur du 27 octobre : [mode navigateur Anna’s Archive sans clé](ANNA-NAVIGATEUR.md), Playwright et Chromium installés. Les essais du parcours utilisent le vrai navigateur avec un serveur local ; le domaine public `.li` testé est parqué et le téléchargement réel depuis Anna’s Archive reste non validé. Le bilan détaillé ci-dessous décrit la livraison RAG initiale ; la suite complète inclut désormais les tests du navigateur.

Ajout suivant : [vérification des domaines et OCR local](ANNA-DOMAINES-OCR.md). Les accueils `.gl`, `.pk` et `.gd` ont été vérifiés avec Chromium ; `.gl` est préféré. L'OCR `ddddocr` et Python 3.12 sont isolés dans `.venv-ocr/`. La suite comporte 51 tests, dont l'OCR réel sur une image originale et sa soumission sur un formulaire local, la sélection de domaine après panne et la reprise de session. Une proposition sur le CAPTCHA public n'a pas été acceptée ; la résolution et le téléchargement autonomes depuis Anna’s Archive ne sont donc pas validés.

## Corpus et couverture

3 449 documents Markdown : 296 guides et fichiers de skills tiers complets, un manuel OpenStax de 744 pages, 24 fiches françaises originales, cinq documents locaux sélectionnés et 3 123 références sans texte intégral.

8 352 passages sont indexés et vectorisés, avec zéro vecteur manquant. Les nombres actualisés se trouvent dans `data/stats.json` et `data/rag-status-final.json`. Le contexte conserve les sources, droits, offsets et pages PDF lorsqu'elles existent. Les titres de conférences issus des URL restent des métadonnées inférées, pas des transcriptions.

Les trois fichiers centraux de projets et les deux skills originaux sont sélectionnés explicitement dans `sources-locales.yaml`. Aucun parcours général de `/home/toubi`, aucune importation automatique des dépôts ou fichiers personnels.

## Installation réalisée

Environnement Python 3.14.8 local, FastEmbed 0.9.1, MCP 2.3.0, ONNX Runtime 1.31.1, NumPy 2.5.4 et pypdf 6.21.2. Les versions transitives sont conservées dans `requirements-lock.txt` ; Ruff et PyYAML servent à la validation.

Le modèle E5 multilingue quantifié est installé à la révision indiquée dans `RAG.md`. Les empreintes des fichiers ont été vérifiées. Inférence CPU avec quatre threads ; aucun modèle de conversation supplémentaire n'est lancé dans Ollama et aucun GPU n'est requis.

Les index de la première livraison sont conservés. Le nouvel index RAG est séparé, dérivé des Markdown, avec cache vectoriel et écriture transactionnelle. Une seconde synchronisation réelle a renvoyé `changed: false` et n'a recalculé aucun vecteur.

## Vérifications fonctionnelles

- **25 tests réussis** : anciens tests du moteur lexical, indexation incrémentale, mise à jour et retrait d'entrées dérivées, filtres, exclusion des références par défaut, offsets, bornage du contexte, transactions, imports, chiffrement, absence de texte OCR, ordre EPUB, conservation des originaux, déduplication et surveillance incrémentale.
- **Lint Ruff réussi** et compilation syntaxique Python ; contrôle shell `sh -n DEMAIN.sh` réussi.
- **Intégrité SQLite et fichiers** : contrôles de licences et empreintes Markdown, taille des vecteurs, couverture FTS et empreintes du modèle réussis. Rapport `data/rag-integrity.json`.
- **Embeddings réels** : sorties finies de 384 dimensions, normes unitaires, entrées françaises et anglaises, ainsi qu'un texte dépassant la fenêtre du modèle. Les passages longs sont agrégés par fenêtres au lieu d'être simplement tronqués. Rapport `data/embedding-real-check.json`.
- **Recherche avec connexions Python bloquées** : chargement du modèle réel et récupération sémantique réussis, sans avertissement de repli lexical. Ce contrôle ne constitue pas une capture de tout le trafic natif du système. Rapport `data/offline-retrieval-check.json`.
- **MCP stdio réel** : un client du SDK lance le vrai serveur depuis `/tmp`, initialise la session, liste les quatre outils, recherche, lit un document et prépare un contexte. Aucun compte ou appel cloud. Rapport `data/mcp-smoke-final.json`.
- **Codex CLI réel** : la configuration du serveur a été parsée avec des overrides de lecture, sans écriture globale. Ce contrôle ne prouve pas le chargement dans une nouvelle conversation Codex. La configuration de projet reste soumise à la confiance accordée au projet.
- **Skills** : les deux skills originaux passent le validateur officiel du skill-creator ; copies locales et sources cohérentes. La découverte automatique globale reste à constater après activation.

Les détails et journaux sont conservés dans `data/`. Les tests unitaires de certains cas d'import réseau utilisent une réponse contrôlée ; ils ne sont pas présentés comme une validation de l'API Anna’s Archive.

## Évaluation de récupération

Vingt questions françaises et anglaises ont été définies pour ce corpus, avec documents attendus. Il s'agit d'un jeu local préparé par l'auteur de l'intégration, sans évaluation indépendante et sans mesure des réponses finales de Codex.

| Mode | Document attendu dans les 5 premiers | Dans les 8 premiers | MRR sur les 8 premiers |
|---|---:|---:|---:|
| Lexical | 19/20 | 19/20 | 0,925 |
| Sémantique | 20/20 | 20/20 | 0,8708 |
| Hybride | 19/20 | 19/20 | 0,9 |

La fusion hybride n'est donc pas démontrée supérieure sur ce jeu. Elle reste le mode par défaut disponible, avec les modes lexical et sémantique explicites. Le score de récupération n'est pas une probabilité de vérité.

Le premier passage d'évaluation a montré un échec sur la réécriture naturelle. Les deux skills originaux, jusque-là accessibles hors de l'index, ont ensuite été ajoutés au corpus documentaire ; le rapport antérieur est conservé dans `data/evaluation-rag-avant-skills-originaux.json`. Le tableau ci-dessus porte sur le corpus enrichi : ce n'est pas une mesure sur un jeu resté aveugle à toutes les améliorations. Aucun gain général de performance de l'agent n'est annoncé.

## Livres et accès externes

*Introduction to Business* a été téléchargé depuis le PDF officiel d'OpenStax. La notice de licence de cette édition indique CC BY 4.0. Le PDF de 744 pages et son empreinte sont archivés ; 2 305 039 caractères ont été extraits avec `pdftotext`. Cette licence n'est pas extrapolée aux autres éditions du site.

Les téléchargements de *Principles of Marketing* et *Business Ethics* ont échoué avec des erreurs HTTP. Aucun contournement ni faux import. Le rapport est dans `data/enrichissement-openstax.json`.

Une recherche bibliographique réelle via Open Library a réussi. L'import TXT, EPUB et les refus de PDF sans texte sont testés ; le PDF OpenStax valide le parcours réel de téléchargement et d'extraction. Aucun OCR installé ou annoncé comme disponible.

L'API membre Anna’s Archive est **optionnelle et non validée en conditions réelles**. Aucun compte, clé, abonnement ou quota n'a été utilisé. La FAQ officielle était inaccessible ; l'intégration s'appuie sur la documentation du projet tiers référencé dans `RAG.md`. Aucune promesse de disponibilité et aucun contournement de restriction.

## Activation globale restante

La commande unique est dans `DEMAIN.md` et `DEMAIN.sh`. Elle regroupe les activations de la première livraison et du RAG : deux skills, MCP global, commande `toubi-biblio` et service utilisateur de synchronisation. Les versions différentes existantes sont conservées.

Cette commande n'a pas été appliquée : `~/.codex`, `~/.local/bin` et `~/.config/systemd/user` sont hors des dossiers autorisés en écriture pendant la préparation. Le service n'est donc pas annoncé comme démarré. Son activation et le chargement des outils dans une nouvelle session Codex restent à constater depuis le terminal habituel.

Le script d'activation et sa syntaxe sont vérifiés ; le parcours complet d'installation systemd et d'enregistrement global reste non exécuté. Aucune configuration personnelle n'a été remplacée, aucun secret affiché ou enregistré, aucun commit ni publication.
