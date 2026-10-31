#!/usr/bin/env python3
"""Fiches originales et catalogue éditorial. Ne télécharge aucun texte tiers."""
import json

from collect import ROOT, TODAY, reference, write_doc

# Conseils opérationnels originaux : aucun résultat chiffré ni citation attribuée.
FICHES = [
('brief-copywriting', 'Préparer un brief de copywriting', 'copywriting brief cible rédaction', '''Une page convaincante commence par des informations fiables sur l'offre et le lecteur.

Renseigner : qui achète et dans quelle situation ; quel problème déclenche la recherche ; comment la personne le traite aujourd'hui ; ce que le produit fait réellement ; les éléments qui permettent de le croire ; les limites ; l'action attendue.

Séparer les faits fournis, les hypothèses à vérifier et les formulations proposées. Demander seulement les informations qui changeraient le texte. Une page peut être rédigée avec des zones à compléter clairement identifiées, sans transformer ces zones en promesses.

Livrable utile : un paragraphe de contexte, une proposition principale, les preuves disponibles, les objections et un appel à l'action. Le brief sert de référence lors de la révision : chaque bénéfice doit pouvoir être relié à une fonction ou à une preuve réelle.

Écueil : rédiger une belle introduction avant de savoir ce que le lecteur doit comprendre ou faire.'''),
('voix-naturelle', 'Écrire naturellement en français', 'humaniser voix naturel français style réécriture', '''Donner l'information dès qu'elle est utile. Nommer l'objet, choisir un verbe précis et garder les détails qui rendent la phrase vérifiable.

Retirer les annonces telles que « il convient de souligner » lorsque la phrase suivante suffit. Réduire les abstractions successives et les transitions qui ne relient aucune idée précise. Ne pas remplacer les mots usuels par des synonymes rares pour donner du relief.

Une voix ne se résume pas à une liste de mots interdits : elle comprend un registre, une relation au lecteur et une manière de choisir les détails. Les exemples de l'auteur sont plus utiles qu'une consigne « sois humain ». Sans exemples, choisir un registre adapté et annoncer seulement ce qui est effectivement connu.

Préserver les réserves, chiffres, conditions et opinions. Ne pas ajouter d'expériences personnelles ou de fautes volontaires. Une bonne révision peut laisser un texte déjà naturel intact.

Skill local : `toubi-humanizer`, dans `../codex-skills/skills/toubi-humanizer/SKILL.md`.'''),
('entretien-client', 'Mener un entretien client utile au message', 'customer research recherche client entretien verbatim besoins', '''Chercher un épisode récent plutôt qu'une opinion générale. Demander à la personne de raconter la dernière fois où le problème s'est posé : ce qui l'a déclenché, ce qu'elle a essayé, ce qui a bloqué et comment elle a choisi une solution.

Questions possibles : « Que s'est-il passé juste avant votre recherche ? » ; « Comment faisiez-vous auparavant ? » ; « Qu'est-ce qui vous a fait hésiter ? » ; « Quel détail vous a rassuré ? ».

Garder les mots exacts seulement avec une provenance et les droits nécessaires. Dans une synthèse, distinguer citation, reformulation et interprétation. Regrouper les observations par situation et type de client ; une remarque isolée ne décrit pas tout le marché.

Livrable : déclencheurs, alternatives, résultats recherchés, objections et vocabulaire récurrent, chacun relié aux entretiens concernés. Les citations publiques et témoignages commerciaux demandent une autorisation adaptée.

Écueil : expliquer longuement son produit ou demander « achèteriez-vous ? », puis traiter la réponse comme une vente.'''),
('proposition-valeur', 'Formuler une proposition de valeur', 'value proposition positionnement promesse bénéfice', '''Écrire une phrase qui permet au lecteur de comprendre à qui sert le produit, ce qu'il permet et pourquoi il mérite une place parmi les solutions envisagées.

Brouillon possible : « Pour [situation précise], [produit] permet de [résultat concret] grâce à [mécanisme réel]. » Ce canevas aide à préciser la pensée ; la phrase finale peut être plus simple.

Tester séparément compréhension, intérêt et crédibilité. Une personne peut comprendre la promesse et ne pas avoir ce besoin, ou vouloir le résultat sans croire au mécanisme. Les corrections seront différentes.

Comparer le message aux alternatives effectivement utilisées : un tableur, une agence ou le fait de ne rien changer peuvent être plus pertinents qu'un concurrent direct.

Livrable : une proposition principale, une explication du mécanisme et une preuve disponible. Éviter les superlatifs sans critère de comparaison et les résultats plus larges que le produit.'''),
('offre', 'Construire une offre claire', 'offers offre valeur garantie périmètre résultat', '''Décrire le résultat visé, ce qui est livré, ce que le client doit fournir, les délais, le prix et les exclusions. Préciser les conditions de réussite et les étapes de la prestation.

Une offre devient plus facile à évaluer lorsque le lecteur voit le travail inclus et la décision attendue. Ajouter des bonus n'a d'intérêt que s'ils retirent un obstacle réel ; une pile de livrables peut augmenter la confusion.

Une garantie doit être réalisable et conforme aux engagements que l'entreprise accepte réellement. Écrire ses conditions avant de rédiger son slogan. Ne pas inventer une rareté, une date limite ou une valeur monétaire attribuée aux bonus.

Livrable : fiche d'offre avec destinataire, bénéfice attendu, périmètre, calendrier, prix, responsabilités, limites et prochaine étape.

Validation : faire reformuler l'offre par un lecteur cible et relever ce qu'il croit inclus. Corriger les écarts avant de chercher une formulation plus persuasive.'''),
('landing-page', 'Organiser une page de vente', 'landing page copywriting conversion accueil structure', '''Faire suivre au lecteur une progression qui répond à ses questions : de quoi s'agit-il, est-ce pour moi, comment cela fonctionne-t-il, pourquoi le croire, quelles sont les conditions et comment avancer ?

Le premier écran peut réunir une proposition claire, un aperçu concret et une action principale. Les sections suivantes développent les questions nécessaires à la décision ; leur ordre dépend du niveau de connaissance et du risque perçu.

Montrer des exemples d'usage et des preuves directement reliées aux affirmations. Placer les conditions importantes à proximité de l'action concernée. Une FAQ répond à de vraies hésitations ; elle ne compense pas une offre incompréhensible.

Livrable : plan de page avec une idée principale par section, la preuve associée et les informations manquantes. Relire sur mobile et vérifier que chaque lien mène à l'action annoncée.

Écueil : copier la structure d'un concurrent dont le public, le prix ou le canal d'acquisition diffère.'''),
('titres', 'Écrire des titres et accroches précis', 'headline titres accroches hooks publicité', '''Un titre aide le lecteur à reconnaître un sujet qui le concerne. Partir d'une situation, d'un résultat concret ou d'un problème identifié plutôt que d'un adjectif valorisant.

Produire des variantes qui changent réellement l'angle : problème rencontré, usage du produit, différence utile ou question traitée. Modifier seulement les synonymes crée peu d'apprentissage.

Pour chaque variante, vérifier si le texte tient sa promesse. Une accroche trop large attire parfois des lecteurs auxquels le contenu ne répond pas. Préserver les limites et ne pas introduire un gain chiffré absent des preuves.

Livrable : plusieurs angles avec public visé, promesse et élément qui permet de la soutenir. Choisir selon l'objectif de la page ou du canal, pas selon la seule impression de punch.

Si le titre doit être testé, définir une mesure liée à l'objectif final : le clic seul ne dit pas si les visiteurs comprennent ou achètent.'''),
('appels-action', 'Rendre un appel à l’action compréhensible', 'CTA appel action boutons formulaire conversion', '''Nommer ce qui se passe après le clic : consulter une démo, demander un devis ou créer un compte. Le libellé doit correspondre à l'action réelle et à l'engagement demandé.

Ajouter à proximité les précisions qui lèvent une hésitation : étapes suivantes, documents à préparer ou conditions d'essai, si elles sont connues. Ne pas annoncer « sans carte bancaire » ou « réponse immédiate » sans l'avoir vérifié.

Une page peut avoir plusieurs actions lorsque les situations le justifient ; hiérarchiser clairement celle qui correspond au parcours principal. Éviter les actions secondaires qui interrompent la compréhension.

Livrable : libellé, destination, conditions affichées et état après action. Vérifier le comportement réel du formulaire, les erreurs, le clavier et le message de confirmation.

Écueil : améliorer seulement le texte du bouton alors que la destination ou le résultat annoncé ne fonctionne pas.'''),
('objections', 'Traiter les objections avec des éléments vérifiables', 'objection prix confiance risque achat vente', '''Regrouper les objections par nature : besoin, adéquation, confiance, coût, effort de changement ou moment de la décision. Ne pas répondre à toutes avec une remise ou une promesse plus forte.

Pour chacune, conserver la formulation observée, le contexte et la réponse que l'offre permet réellement. Si le produit ne répond pas au besoin, le reconnaître aide à qualifier la demande.

Une objection de confiance appelle parfois un exemple, une démonstration ou une condition contractuelle. Une objection d'effort peut demander une explication de l'installation ou des étapes de reprise. Une objection de prix peut révéler une valeur mal comprise ou une mauvaise adéquation budgétaire.

Livrable : tableau « objection observée / contexte / réponse / preuve / limite ». Ajouter une FAQ seulement si elle aide la décision et rend les conditions plus claires.

Écueil : présenter une inquiétude inventée comme un retour client fréquent.'''),
('preuves', 'Organiser les preuves commerciales', 'preuve evidence témoignage cas client crédibilité', '''Relier chaque affirmation importante à un élément consultable : fonctionnement démontré, retour client autorisé, mesure documentée ou condition contractuelle.

Une étude de cas doit distinguer situation initiale, intervention, résultat observé, période et limites d'attribution. Une amélioration observée après une intervention ne suffit pas à prouver que celle-ci en est la seule cause.

Tenir un registre avec l'affirmation, sa source, la date de vérification, le périmètre couvert et les droits de publication. Si une preuve manque, réduire la promesse ou la présenter comme un objectif à vérifier.

Livrable : banque de preuves consultable lors de la rédaction. Conserver les originaux sans les mélanger aux phrases commerciales proposées.

Écueil : transformer un témoignage singulier en résultat garanti, supprimer une condition ou reprendre un logo sans autorisation adaptée.'''),
('email-prospection', 'Préparer un email de prospection ciblé', 'cold email prospection vente courriel acquisition', '''Choisir une raison observable de contacter ce destinataire. Relier cette observation à un problème plausible, présenté comme une hypothèse lorsque le contexte ne le confirme pas.

Un email peut contenir le motif du contact, une proposition concrète, une preuve disponible et une demande simple. La personnalisation consiste à rendre la proposition pertinente, pas à ajouter une phrase sur un détail privé.

Ne pas prétendre avoir testé un service, échangé avec une équipe ou reçu une recommandation si ce n'est pas vrai. Ne pas inventer le temps économisé ou les revenus possibles. Adapter la formulation et le canal aux règles applicables à la prospection.

Livrable : brouillon, observation publique source, hypothèse de besoin et action demandée. La préparation d'un email n'autorise pas son envoi.

Évaluation : observer les réponses et leur qualité, les objections et l'adéquation des rendez-vous ; ne pas optimiser uniquement le taux d'ouverture.'''),
('sequence-email', 'Construire une séquence d’emails', 'emails email sequence onboarding fidélisation', '''Définir le déclencheur, le destinataire, l'objectif et les conditions d'arrêt de la séquence. Chaque message doit apporter une information ou une aide différente.

Pour une prise en main : expliquer l'action utile, aider à la réaliser, puis répondre aux obstacles observés. Pour une vente : préciser l'offre, montrer une preuve et traiter les questions qui empêchent la décision. Le nombre de messages et leur espacement dépendent du contexte.

Prévoir les exclusions : personne ayant déjà accompli l'action, répondu, refusé ou demandé à ne plus être contactée. Un changement de statut doit éviter les messages devenus incohérents.

Livrable : pour chaque message, déclencheur, contenu, action, condition d'arrêt et source des affirmations. Relire l'ensemble pour retirer les répétitions.

Écueil : programmer une urgence répétée ou annoncer une disponibilité qui ne correspond pas à l'état réel de l'offre.'''),
('tarification', 'Clarifier une page de prix', 'pricing tarification prix HT TTC abonnement annuel', '''Permettre au lecteur de calculer ce qu'il paiera dans sa situation. Expliciter la devise, les taxes, l'unité de facturation, la périodicité, l'engagement et les limites de chaque formule.

Si un montant mensuel correspond à une facture annuelle, l'indiquer près du prix. Distinguer l'essai gratuit, la garantie de remboursement et une formule gratuite : ces mécanismes n'impliquent pas les mêmes conditions.

Comparer les formules selon des différences utiles pour les clients, sans masquer les restrictions importantes. Pour une tarification à l'usage, préciser les éléments qui font varier la facture et les moyens de contrôler la consommation.

Livrable : tableau lisible accompagné d'exemples de calcul validés par les conditions réelles de l'offre. Les exemples restent indicatifs si le tarif dépend d'un devis.

Écueil : annoncer une économie sans référence de comparaison ou supprimer des frais pour rendre le prix plus attirant.'''),
('positionnement', 'Définir un positionnement exploitable', 'positioning positionnement concurrence différenciation marque', '''Identifier le client pour lequel une différence du produit compte réellement. Décrire les alternatives qu'il utiliserait en l'absence du produit et la raison de changer.

Une caractéristique différente ne suffit pas : préciser son effet sur l'usage, puis la situation où cet effet devient utile. Une spécialisation peut rendre une offre plus lisible si elle correspond à des besoins observés.

Rassembler entretiens, retours de vente, usages et raisons de départ. Distinguer l'analyse des faits établis : une carte de positionnement est une hypothèse de travail, pas une étude de marché à elle seule.

Livrable : cible prioritaire, situation, alternatives, différences, valeur associée et preuves. Utiliser ce document pour garder les pages, emails et démonstrations cohérents.

Écueil : choisir une formule ambitieuse qui pourrait être celle de n'importe quel concurrent.'''),
('strategie-contenu', 'Choisir une stratégie de contenu', 'content strategy stratégie éditoriale distribution sujets', '''Relier chaque contenu à une question du public et à un objectif de l'activité : faire comprendre un problème, comparer des options, faciliter l'usage ou préparer une décision.

Choisir les sujets à partir des conversations client, recherches, objections et retours de support. Préciser ce que l'entreprise peut apporter de distinct : expérience documentée, démonstration, données propres ou méthode réellement appliquée.

Prévoir la distribution avant de rédiger. Un même sujet peut devenir un guide, une démonstration et un email, à condition que chaque format serve son contexte.

Livrable : sujet, public, question, angle, preuve disponible, canal, action attendue et responsable de mise à jour. Le calendrier vient ensuite.

Écueil : publier beaucoup sur des thèmes éloignés de l'offre ou reprendre les affirmations d'un concurrent sans les vérifier.'''),
('analyse-publicite', 'Étudier une publicité sans inventer sa performance', 'swipe file publicité copywriting analyse annonce', '''Observer ce qui est visible : public visé, situation, accroche, promesse, mécanisme, preuve, objection traitée, offre et appel à l'action.

Séparer cette observation de l'interprétation. « Cette publicité utilise un témoignage » est visible ; « ce témoignage augmente les ventes » demande des données. La présence prolongée d'une publicité ou son archivage n'établit pas sa rentabilité.

Noter la source, la date d'observation et le contexte accessible. Extraire un principe à tester plutôt que recopier une création. Respecter les droits sur le texte, les images et les personnes.

Livrable : fiche « observation / hypothèse de mécanisme / adaptation possible / test ». Pour l'adaptation, remplacer la preuve et les détails par ceux du produit concerné.

Écueil : conserver une formule spectaculaire tout en perdant les conditions qui la rendaient crédible dans l'annonce d'origine.'''),
('experience-conversion', 'Préparer une expérience de conversion', 'ab testing expérience test conversion mesure hypothèse', '''Écrire une hypothèse causale limitée : un obstacle observé, une modification et l'effet attendu sur une action mesurable. Garder une version de référence et préciser la population concernée.

Choisir une mesure principale et des garde-fous adaptés : qualité des demandes, remboursements, erreurs ou satisfaction selon le parcours. Définir avant le lancement les conditions d'arrêt et la méthode d'analyse.

Le besoin d'échantillon dépend des taux de départ, de l'effet recherché et de la méthode. Ne pas inventer une durée universelle. Avec peu de trafic, un entretien ou un test de compréhension peut éclairer la décision sans prétendre démontrer un gain de conversion.

Livrable : protocole, métriques, événements vérifiés, variantes et journal des changements. Contrôler que l'instrumentation compte les mêmes actions dans chaque groupe.

Écueil : conclure dès que le résultat semble favorable ou confondre corrélation temporelle et effet de la modification.'''),
('conference-fiche', 'Transformer une conférence en fiche utile', 'conférence podcast transcription résumé business apprentissage', '''Avant toute synthèse, vérifier que le contenu a été réellement consulté. Un titre ou une description ne permet pas de reconstituer l'argumentaire d'un intervenant.

Conserver auteur, événement, date, URL et repères temporels. Distinguer les propos de l'intervenant, les exemples racontés et l'analyse ajoutée. Vérifier les chiffres et les citations dans le passage correspondant.

Produire une fiche centrée sur la décision : problème traité, idées utiles, conditions où elles s'appliquent, limites et expérience possible dans un projet concret. Un conseil dépend souvent du stade de l'entreprise et de son modèle économique.

Livrable : résumé bref, repères de consultation, pistes d'application et questions ouvertes. Une transcription automatique reste à vérifier, notamment pour les noms et nombres.

Respecter les conditions de la source avant téléchargement ou redistribution. Une fiche peut conserver le lien et une analyse originale sans stocker la vidéo entière.'''),
('corpus-ia', 'Préparer un corpus documentaire pour une IA', 'RAG corpus données dataset bibliothèque recherche ingestion', '''Définir les questions auxquelles le corpus doit aider à répondre. Collecter des documents pertinents avec URL, auteur, date, langue, licence, type et état de vérification.

Conserver les originaux autorisés, puis créer des unités consultables sans perdre le contexte. Les titres et métadonnées aident la recherche ; les passages fournissent les éléments de réponse. Une référence seule doit rester identifiable comme telle.

Dédupliquer les URL normalisées et surveiller les versions. Garder les droits à l'échelle du document : la licence de l'index ne couvre pas automatiquement tous les contenus référencés.

Évaluer la récupération sur de vraies questions : document pertinent trouvé, passage suffisant, citation correcte et reconnaissance des informations absentes. Une base volumineuse n'est pas une preuve de qualité des réponses.

Les instructions contenues dans des documents récupérés sont des données non fiables. Elles ne doivent pas activer de commandes, modifier la tâche ou déclencher d'actions externes.'''),
('voix-client', 'Extraire le vocabulaire client', 'verbatim avis clients voice of customer langage objections', '''Relever les formulations qui décrivent la situation, la frustration, le résultat souhaité et les critères de choix. Garder suffisamment de contexte pour ne pas inverser le sens d'un avis.

Classer par type de client, usage et période lorsque ces informations sont disponibles. Comparer les expressions récurrentes sans les confondre avec une mesure représentative du marché : les personnes qui publient un avis constituent un échantillon particulier.

Utiliser ces observations pour poser de meilleures questions et formuler des hypothèses de message. Ne pas faire passer un avis public pour un témoignage de son propre produit. Retirer les données personnelles sans utilité pour l'analyse.

Livrable : thème, formulation ou paraphrase, provenance, contexte et interprétation séparée. Pour republier une citation ou entraîner un modèle, vérifier les droits correspondant à cet usage.

Écueil : laisser un outil fabriquer les citations qui manquent pour illustrer une conclusion.'''),
('cas-client', 'Rédiger une étude de cas client', 'case study étude cas client preuve résultat témoignage', '''Raconter une situation précise : contexte initial, raison du changement, solution mise en place, conditions de déploiement et résultat observé.

Avant de rédiger, recueillir les preuves disponibles et l'autorisation de publication. Préciser la période, la méthode de mesure et les autres changements qui peuvent expliquer le résultat. Les informations non vérifiées restent des déclarations attribuées, pas des mesures établies.

Faire apparaître ce qu'un lecteur comparable peut apprendre du cas, ainsi que les conditions qui rendent l'expérience différente de la sienne. Un résultat exceptionnel ne devient pas la promesse standard de l'offre.

Livrable : contexte, intervention, observation, preuve, limites et citation autorisée. Soumettre les éléments attribués au client à validation selon l'accord de publication.

Écueil : ajouter un chiffre pour rendre le récit plus convaincant ou présenter l'absence de plainte comme une satisfaction démontrée.'''),
('qualification', 'Qualifier une opportunité commerciale', 'sales vente qualification besoin budget décision découverte', '''Comprendre le problème, son importance, les personnes concernées, les solutions déjà essayées et la manière dont la décision se prend.

Demander ce qui justifie d'agir maintenant et ce qui pourrait empêcher le projet. Le budget peut être inconnu au début ; chercher les contraintes et les critères plutôt que forcer une réponse artificielle.

Partager une reformulation du besoin et vérifier que le client s'y reconnaît. Distinguer la demande exprimée de la solution proposée. Si le besoin dépasse le périmètre de l'offre, le signaler avant d'engager du travail.

Livrable : situation, enjeu, contraintes, décideurs, critères, prochaines étapes et inconnues. Chaque engagement doit avoir un responsable et un état réel.

Écueil : transformer un échange positif en intention d'achat confirmée ou considérer un rendez-vous comme un revenu acquis.'''),
('revue-texte', 'Faire une revue finale de texte commercial', 'révision copy editing qualité vérification publication', '''Relire d'abord le sens : le lecteur comprend-il le produit, le destinataire et l'action attendue ? Vérifier ensuite si les preuves soutiennent les affirmations et si les conditions sont visibles.

Contrôler prix, unités, taxes, dates, durées, liens, noms et résultats cités. Les mentions légales ou réserves nécessaires ne doivent pas disparaître sous prétexte de fluidité.

Relire le rythme à voix haute si utile. Retirer les répétitions et formulations génériques qui n'aident pas la décision. Garder les termes du client lorsqu'ils sont compréhensibles et adaptés au contexte.

Livrable : texte final, éventuels points bloquants et éléments à vérifier avant publication. Un brouillon relu ne vaut pas validation des faits manquants.

Pour la dernière passe stylistique, utiliser `toubi-humanizer`. Pour une page, vérifier aussi le rendu réel et le comportement des actions.'''),
('mesure-business', 'Relier un indicateur à une décision business', 'metrics mesure business acquisition rétention revenu indicateurs', '''Choisir un indicateur parce qu'il aide à décider : améliorer un canal, comprendre une perte de clients ou vérifier la qualité d'une offre.

Définir numérateur, dénominateur, période, population et source. Pour des revenus, distinguer montant facturé, encaissé, récurrent et marge. Pour l'acquisition, garder le coût et la qualité des clients dans le même périmètre d'analyse.

Comparer des cohortes ou périodes réellement comparables. Documenter les changements de prix, de canal ou de mesure qui peuvent expliquer un écart. Une moyenne globale peut masquer des situations très différentes.

Livrable : fiche d'indicateur avec définition, calcul, source, limites et décision associée. Conserver les données brutes nécessaires à la vérification sans collecter d'informations personnelles inutiles.

Écueil : afficher des chiffres décoratifs ou attribuer au marketing un résultat dont les causes n'ont pas été examinées.'''),
]

SOURCES = [
('openstax', 'OpenStax — Introduction to Business', 'https://openstax.org/details/books/introduction-business', 'en', 'Manuel complet de 744 pages importé depuis le PDF officiel ; licence lue dans le fichier archivé.', 'texte_local', 'CC BY 4.0 de l’édition PDF archivée ; autres éditions à vérifier'),
('marketingskills', 'Marketing Skills — Corey Haines', 'https://github.com/coreyhaines31/marketingskills', 'en', 'Guides et skills marketing complets, sous licence MIT.', 'texte_local', 'MIT'),
('humanizer-source', 'Humanizer — source de référence', 'https://github.com/blader/humanizer', 'en', 'Skill tiers conservé comme document de comparaison ; notre version reste séparée.', 'texte_local', 'MIT'),
('marketingexamples', 'Marketing Examples', 'https://marketingexamples.com/', 'en', 'Exemples commentés de rédaction, pages et acquisition.', 'reference_seule', 'À vérifier avant réutilisation du contenu'),
('swiped', 'Swipe-Worthy', 'https://swiped.co/', 'en', 'Exemples de publicités et lettres de vente à analyser.', 'reference_seule', 'À vérifier avant réutilisation du contenu'),
('reallygoodemails', 'Really Good Emails', 'https://reallygoodemails.com/', 'en', 'Galerie d’emails par usage ; exemples à consulter à la source.', 'reference_seule', 'À vérifier avant réutilisation du contenu'),
('copythat', 'Copy That!', 'https://www.copythatshow.com/', 'en', 'Guides de copywriting et ressources d’apprentissage.', 'reference_seule', 'À vérifier avant réutilisation du contenu'),
('copyhackers', 'Copyhackers', 'https://copyhackers.com/', 'en', 'Ressources sur les messages et la conversion ; accès variable.', 'reference_seule', 'À vérifier avant réutilisation du contenu'),
('yc-library', 'Y Combinator Library', 'https://www.ycombinator.com/library', 'en', 'Conseils et vidéos pour les fondateurs.', 'reference_seule', 'À vérifier avant réutilisation du contenu'),
('stanford', 'Stanford eCorner', 'https://stvp.stanford.edu/ecorner', 'en', 'Conférences et podcasts d’entrepreneuriat. Transcriptions non téléchargées.', 'reference_seule', 'À vérifier avant réutilisation du contenu'),
('saastr', 'SaaStr', 'https://www.saastr.com/', 'en', 'Contenus SaaS et vente B2B. Collecte automatisée limitée par le site lors de cette session.', 'reference_seule', 'À vérifier avant réutilisation du contenu'),
('acquisition', 'Acquisition.com — formations', 'https://www.acquisition.com/training', 'en', 'Cours sur les offres, les prospects et la croissance.', 'reference_seule', 'À vérifier avant réutilisation du contenu'),
('growthunhinged', 'Growth Unhinged', 'https://www.growthunhinged.com/', 'en', 'Analyses de croissance et positionnement ; accès variable.', 'reference_seule', 'À vérifier avant réutilisation du contenu'),
('lenny', 'Lenny’s Newsletter', 'https://www.lennysnewsletter.com/', 'en', 'Source produit et croissance ; accès variable, pas de contenu intégral collecté.', 'reference_seule', 'À vérifier avant réutilisation du contenu'),
('bpi-big', 'BIG — Bpifrance', 'https://big.bpifrance.fr/', 'fr', 'Conférences et ateliers francophones ; replays à consulter dans la plateforme.', 'reference_seule', 'À vérifier avant réutilisation du contenu'),
('bpifrance-creation', 'Bpifrance Création — webinaires', 'https://bpifrance-creation.fr/webinaires', 'fr', 'Replays sur la création et le développement commercial.', 'reference_seule', 'À vérifier avant réutilisation du contenu'),
('bpifrance-universite', 'Bpifrance Université', 'https://www.bpifrance-universite.fr/webinaires-bpifrance-universite/', 'fr', 'Webinaires et supports ; compte gratuit nécessaire pour certains contenus.', 'reference_seule', 'À vérifier avant réutilisation du contenu'),
('hopkins', 'Scientific Advertising — Claude Hopkins', 'https://www.loc.gov/item/23009362/', 'en', 'Édition de 1923 référencée par la Library of Congress. Texte non téléchargé.', 'reference_seule', 'Domaine public selon la notice de cette édition'),
('fineweb', 'FineWeb 2', 'https://huggingface.co/datasets/HuggingFaceFW/fineweb-2', 'mul', 'Corpus web généraliste massif ; filtrage thématique nécessaire. Non téléchargé.', 'reference_seule', 'Vérifier la carte et les droits des contenus'),
('commonpile', 'Common Pile', 'https://www.commonpile.org/', 'en', 'Corpus massif de textes ouverts et du domaine public ; non spécialisé business. Non téléchargé.', 'reference_seule', 'Droits à vérifier par sous-corpus'),
('amazon-reviews', 'Amazon Reviews 2023', 'https://huggingface.co/datasets/McAuley-Lab/Amazon-Reviews-2023', 'en', 'Avis clients pour la recherche. Le producteur ne garantit pas une licence globale sur les avis. Non téléchargé.', 'reference_seule', 'Droits non établis pour un usage commercial'),
('adparaphrase', 'AdParaphrase', 'https://huggingface.co/datasets/cyberagent/AdParaphrase', 'ja', 'Paires de textes publicitaires et préférences humaines. Non téléchargé.', 'reference_seule', 'CC BY-NC-SA 4.0 — non commercial'),
('persuasion', 'Anthropic Persuasion', 'https://huggingface.co/datasets/Anthropic/persuasion', 'en', 'Données d’étude de persuasion, incluant des textes générés. Non téléchargé.', 'reference_seule', 'CC BY-NC-SA 4.0 — non commercial'),
('ted', 'TED — conditions de réutilisation', 'https://www.ted.com/about/our-organization/our-policies-terms/ted-talks-usage-policy', 'en', 'Vérifier les restrictions avant toute collecte ou réutilisation de conférences TED.', 'reference_seule', 'Restrictions propres à TED ; aucun contenu collecté'),
]


def main():
    for slug, title, tags, body in FICHES:
        write_doc(dict(id='toubi-' + slug, title=title, source='toubi',
                       url='local://toubi/' + slug, kind='fiche-originale', language='fr',
                       tags=tags.split(), rights='Rédaction originale pour Toubi — aucun droit sur les sources tierces',
                       status='fiche_originale', verification='Conseils rédactionnels originaux, non évalués comme résultats business'),
                  '# ' + title + '\n\n' + body + '\n', 'fiches')
    records = []
    for source, title, url, language, note, state, rights in SOURCES:
        reference(source, url, title, language, 'catalogue éditorial')
        records.append(dict(id=source, title=title, url=url, language=language, note=note,
                            collection=state, rights=rights, retrieved=TODAY))
    (ROOT / 'SOURCES.yaml').write_text(json.dumps(dict(updated=TODAY, sources=records), ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    lines = ['# Sources', '', 'Catalogue éditorial. Le détail du volume réellement collecté se trouve dans `data/stats.json`.', '',
             '| Source | Usage | Accès local | Droits |', '|---|---|---|---|']
    for x in records:
        lines.append(f"| [{x['title']}]({x['url']}) | {x['note']} | {x['collection']} | {x['rights']} |")
    (ROOT / 'SOURCES.md').write_text('\n'.join(lines) + '\n', encoding='utf-8')
    print(f'{len(FICHES)} fiches originales ; {len(records)} sources documentées.')


if __name__ == '__main__':
    main()
