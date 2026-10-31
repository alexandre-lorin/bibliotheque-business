# Tomorrow: just one order

To run from your usual terminal:

```sh
sh '/home/toubi/01 - Dev/bibliotheque-business/DEMAIN.sh'
```

This command also groups together the activations from the first delivery that you had not carried out:

1. Install `toubi-humanizer` and `toubi-bibliotheque` in the global skills folder.
2. Register the local MCP server in Codex.
3. Add the terminal command `toubi-biblio` to `~/.local/bin`.
4. Enable the user service that monitors the library every 60 seconds.

The dependencies, model and indexes are already prepared in the project folder. No admin password or new subscription is required. Identical configurations are recognized; a different existing version is kept and flagged for comparison.

Then open a new Codex round and check `/mcp`, then ask:

> Consult my library to prepare an offer and cite the passages used.

For style:

> Use our humanizer to rewrite this text in natural French.

Automatic discovery of a skill helps Codex select it; it does not guarantee that it will query the library on every message. The search skill indicates when and how to search. MCP tools make the library available in all projects using this Codex configuration.

## Verification if necessary

```sh
codex mcp get toubi-bibliotheque
systemctl --user status toubi-bibliotheque.service
toubi-biblio status
```

If `~/.local/bin` is not in your PATH, the MCP remains usable and the full command is:

```sh
'/home/toubi/01 - Dev/bibliotheque-business/.venv/bin/python' \
  '/home/toubi/01 - Dev/bibliotheque-business/rag.py' status
```

To stop monitoring only: `systemctl --user disable --now toubi-bibliotheque.service`. This preserves documents and indexes; the search remains available.

Global activation was not initiated during preparation: `~/.codex`, `~/.local/bin` and `~/.config/systemd/user` are outside the writable folders in this session. The command above performs these steps from your normal terminal.

Anna’s Archive does not require any additional activation for [keyless browser mode](ANNA-NAVIGATEUR.md). The local](ANNA-DOMAINES-OCR.md) domain detection and OCR tools are also installed; `.gl` is preferred. OCR remains experimental on the public site. The Member API remains a separate option, with no accounts, keys, or subscriptions added.
