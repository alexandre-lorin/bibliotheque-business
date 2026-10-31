# Validation locale — 26 octobre 2026

## État livré

- 3 442 entrées Markdown indexées.
- 296 textes complets sous MIT : 53 fichiers de skills et 243 guides ou documents associés.
- 24 fiches originales en français.
- 3 122 références de sources, articles, cours et conférences, sans leur texte intégral.
- 23 sources dans le catalogue éditorial, plus les fiches de Toubi.
- 3 056 489 caractères de textes tiers complets ; les autres caractères comptés dans les statistiques sont des fiches et métadonnées de références.

Les références comprennent notamment le catalogue public de Y Combinator et 2 485 URL de conférences ou podcasts Stanford issues du sitemap. Les titres Stanford sont inférés des URL. Les pages individuelles et transcriptions n'ont pas été lues ou téléchargées. Leurs liens peuvent devenir indisponibles.

## Vérifications effectuées

`python -m unittest discover -s tests -v` : neuf tests réussis sur le vrai moteur SQLite FTS5 local. Ils couvrent recherche sans accents, filtres, déduplication des passages, lecture intégrale, bornage du contexte et conservation des sources, reconstruction répétée, transaction annulée sur document invalide, détection d'une altération et découpage sans perte.

Les collecteurs ont été exécutés sur les sources réelles. L'import des archives MIT, la récupération des métadonnées YC et le sitemap Stanford ont abouti. Les rapports de collecte conservent révisions, dates, empreintes, volumes et erreurs. Certains catalogues dynamiques ne livrent pas leurs contenus via des liens HTML : aucune couverture exhaustive n'est annoncée pour Bpifrance, Really Good Emails ou les sources à accès variable.

`python biblio.py check` : cohérence des identifiants, absence de doublons d'URL, présence des licences associées et empreintes des textes importés vérifiées.

Lint Ruff : réussi, règles E4/E7/E9/F/I. Python standard uniquement pour l'exécution. Aucun vérificateur de types spécifique n'est configuré pour ce petit projet.

Les deux nouveaux skills passent le `quick_validate.py` officiel de `skill-creator`. Leur installation sélective dans `.agents/skills/` du projet a réussi. Les consignes originales et leurs copies locales sont identiques. Aucun skill tiers collecté n'a été activé.

Le [humanizer a été appliqué à cinq exemples](EVALUATION-HUMANIZER.md), puis relu dans cette session. Cette vérification illustre ses consignes ; elle n'est pas une évaluation indépendante de qualité rédactionnelle.

## Audit de la structure

Les Markdown restent la source de vérité. L'index SQLite est dérivé et peut être reconstruit. La recherche ne lance aucun appel réseau et ne charge pas le corpus entier dans le contexte de l'agent. Les extraits conservent source, état et droits ; les documents tiers sont signalés comme données documentaires non fiables.

La collecte est explicite et bornée, ne contourne pas les refus et ne supprime pas les archives. Les contenus sélectionnés dans les archives sont lus sans exécuter les commandes qu'ils contiennent. Les révisions amont nouvelles peuvent ajouter des versions distinctes ; la taille n'est donc pas une mesure du nombre de sujets uniques.

Un dépôt Git a été initialisé avant l'écriture du projet. Aucun commit, aucune publication et aucun changement des projets actifs n'ont été effectués. Les catalogues centraux et la documentation des skills ont été complétés.

## Limites

La bibliothèque n'est pas une collecte exhaustive du web ni un corpus d'entraînement validé. Les textes tiers sont principalement en anglais. La recherche est lexicale, sans traduction automatique ni embeddings. Les références ne prouvent pas une lecture ou une performance business. Les informations changeantes doivent être revérifiées à la source.

Les skills sont installés localement, mais pas globalement : `~/.codex/skills` est hors des emplacements autorisés en écriture dans cette session. La commande d'installation globale est fournie dans [DEMARRER.md](DEMARRER.md). La découverte automatique des skills doit être constatée au prochain tour dans le dossier approprié ; leur présence sur disque ne prouve pas qu'une session déjà ouverte les a chargés.
