# Textes complets ajoutés le 27 octobre 2026

107 documents supplémentaires, environ 7,64 millions de caractères extraits.
Ce décompte concerne les textes présents, pas les liens de conférences.

| Collection | Documents | Contenu |
|---|---:|---|
| MIT OpenCourseWare | 64 | 12 transcriptions de New Enterprises et 52 supports de New Enterprises, Entrepreneurial Sales, Entrepreneurial Marketing |
| Stanford | 34 | 33 conférences/entretiens complets et un extrait sur les débuts de NVIDIA |
| Virginia Tech | 2 | Fundamentals of Business, 4e édition (2023), 448 pages PDF ; Strategic Management (2020), 352 pages PDF |
| Classiques Gutenberg | 3 | My Life and Work ; Autobiography of Andrew Carnegie ; The Art of Money Getting |
| Livres fournis par Toubi | 4 | $100M Offers ; $100M Lost Chapters ; The Personal MBA ; commentaire tiers de Ben Preston |

Exemples Stanford : Reid Hoffman, Live Life in Permanent Beta ; Jensen Huang,
First-Principles Thinking ; Brian Chesky, Managing Through Crisis and Uncertainty ;
Eric Yuan, Winning a Crowded Market ; Eric Ries, Evangelizing for the Lean Startup ;
Steve Blank, Entrepreneurship Strengthens a Nation ; How Instagram Scaled.

Les livres fournis ont été repérés dans le dossier Downloads expressément indiqué
par Toubi. Leurs noms de fichiers ne prouvent ni authenticité éditoriale ni droits
de redistribution. Le commentaire de Ben Preston est identifié comme ouvrage
tiers, pas attribué à Alex Hormozi.

Les originaux restent dans `archives/` et les téléchargements de Toubi restent à
leur emplacement initial. Les EPUB sont extraits dans l'ordre du sommaire de
lecture interne. L'AZW3 Lost Chapters a été converti en EPUB avec mobi 0.4.1,
sans déchiffrement ; l'original AZW3 est également archivé. Pour les PDF, les
numéros de page désignent les pages du fichier, pas nécessairement la pagination
imprimée. Les tableaux et illustrations ne sont pas reconstitués.

## Provenance et limites

MIT : https://ocw.mit.edu/courses/15-390-new-enterprises-spring-2013/
et les deux autres cours enregistrés dans `enrich_sources.py`. La licence OCW
comporte des exceptions pour des éléments tiers ; conserver les notices originales.
Les notes de marketing de 2002 sont un document historique, pas un état du marché actuel.

Virginia Tech : https://doi.org/10.21061/fundamentalsofbusiness4e et
https://doi.org/10.21061/strategicmanagement. Les licences de leurs éditions
respectives sont enregistrées dans les métadonnées.

Stanford : transcriptions directement publiées par STVP ou GSB. Les anciens PDF
WordPress ont renvoyé 404 : les pages actuelles et leur vue imprimable ont permis
de récupérer le texte. Une transcription officielle peut contenir des erreurs.
Ces documents restent sous copyright ; aucune licence ouverte n'est affirmée.
La réussite d'un intervenant ne prouve pas l'efficacité universelle de ses conseils.

Gutenberg : éditions anglaises historiques, notices conservées. Ces ouvrages
témoignent de leur époque ; leurs conseils ne constituent pas des faits actuels.

Les refus OpenStax et les échecs réseau ne sont pas comptés comme des imports.
Aucun livre supplémentaire n'a été téléchargé sur Anna’s Archive.

## Accès RAG

Les sources recherchables sont `livres-toubi`, `stanford-transcripts`, `mit-ocw`,
`virginia-tech` et `gutenberg-business`. Exemple :

```sh
.venv/bin/python rag.py search 'Comment construire une offre avec une équation de valeur ?' --source livres-toubi
.venv/bin/python rag.py search 'Comment comprendre les besoins des clients avant de développer le produit ?' --source stanford-transcripts
```

Après un nouvel import, lancer `.venv/bin/python sync.py`.
La collecte web reste explicite : `enrich_sources.py` utilise une sélection bornée
dans `sources-completes.json`, pas un crawl illimité. Les imports Virginia Tech
et personnels de cette livraison sont consignés séparément dans `data/`.

Rapports : `data/enrichissement-bilan.json`,
`data/enrichissement-sources-completes.json`,
`data/enrichissement-stanford-actuel.json`, `data/imports-livres-toubi.json`,
`data/import-hormozi-lost-chapters.json`.

## Prochains livres pertinents

Sélection à acquérir ou fournir en copie personnelle : The Lean Startup (Eric
Ries), SPIN Selling (Neil Rackham), Influence (Robert Cialdini), Made to Stick
(Chip et Dan Heath), The Copywriter's Handbook (Robert Bly). Ils figurent dans la
[liste officielle de Kaufman](https://personalmba.com/best-business-books/).
Ces cinq livres ne sont pas téléchargés et ne sont pas présentés comme disponibles
dans la base. La conférence d'Eric Ries est, elle, disponible en texte complet.

Pour MOBI/AZW3 non chiffré : le convertisseur local isolé est dans `.venv-books/`,
avec dépendances verrouillées dans `requirements-books.txt`. Il est appelé par
`books.py import` ; les formats protégés ne sont pas déchiffrés.
