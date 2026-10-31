# Demain : une seule commande

À exécuter depuis votre terminal habituel :

```sh
sh '/home/toubi/01 - Dev/bibliotheque-business/DEMAIN.sh'
```

Cette commande regroupe aussi les activations de la première livraison que vous n'aviez pas effectuées :

1. Installer `toubi-humanizer` et `toubi-bibliotheque` dans le dossier global de skills.
2. Enregistrer le serveur MCP local dans Codex.
3. Ajouter la commande terminal `toubi-biblio` dans `~/.local/bin`.
4. Activer le service utilisateur qui surveille la bibliothèque toutes les 60 secondes.

Les dépendances, le modèle et les index sont déjà préparés dans le dossier du projet. Aucun mot de passe administrateur ni nouvel abonnement n'est requis. Les configurations identiques sont reconnues ; une version différente existante est conservée et signalée pour comparaison.

Ouvrir ensuite un nouveau tour Codex et vérifier `/mcp`, puis demander :

> Consulte ma bibliothèque pour préparer une offre et cite les passages utilisés.

Pour le style :

> Utilise notre humanizer pour réécrire ce texte en français naturel.

La découverte automatique d'un skill aide Codex à le sélectionner ; elle ne garantit pas qu'il interrogera la bibliothèque à chaque message. Le skill de consultation indique quand et comment rechercher. Les outils MCP rendent la bibliothèque disponible dans tous les projets utilisant cette configuration Codex.

## Vérification si nécessaire

```sh
codex mcp get toubi-bibliotheque
systemctl --user status toubi-bibliotheque.service
toubi-biblio status
```

Si `~/.local/bin` n'est pas dans votre PATH, le MCP reste utilisable et la commande complète est :

```sh
'/home/toubi/01 - Dev/bibliotheque-business/.venv/bin/python' \
  '/home/toubi/01 - Dev/bibliotheque-business/rag.py' status
```

Pour arrêter uniquement la surveillance : `systemctl --user disable --now toubi-bibliotheque.service`. Cela conserve les documents et les index ; la recherche reste disponible.

L'activation globale n'a pas été lancée pendant la préparation : `~/.codex`, `~/.local/bin` et `~/.config/systemd/user` sont hors des dossiers autorisés en écriture dans cette session. La commande ci-dessus réalise ces étapes depuis votre terminal normal.

Anna’s Archive ne nécessite aucune activation supplémentaire pour le [mode navigateur sans clé](ANNA-NAVIGATEUR.md). Les outils de [détection de domaines et d'OCR local](ANNA-DOMAINES-OCR.md) sont installés aussi ; `.gl` est préféré. L'OCR reste expérimental sur le site public. L'API membre reste une option distincte, sans compte, clé ou abonnement ajouté.
