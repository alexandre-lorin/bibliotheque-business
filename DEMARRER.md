# Toubi business library

A local library of marketing guides, French factsheets, books and conference references. Markdown files are readable directly. Multilingual RAG search is installed; the old lexical engine without dependencies remains available.

**For global activation, including first delivery orders: [DEMAIN.md](DEMAIN.md). A single command brings together everything.** For operation and imports: [RAG.md](RAG.md).

## Quick access for an AI

[New books supplied: nine additional imports](AJOUTS-LIVRES.md).

Additions from 27 October: [107 additional complete texts, including the books of
Toubi and the Stanford](ENRICHISSEMENT-CONTENUS.md) conferences.

From any folder:

```sh
'/home/toubi/01 - Dev/bibliotheque-business/.venv/bin/python' '/home/toubi/01 - Dev/bibliotheque-business/rag.py' search 'Comment traiter les objections avant un achat ?'
'/home/toubi/01 - Dev/bibliotheque-business/.venv/bin/python' '/home/toubi/01 - Dev/bibliotheque-business/rag.py' context 'Comment structurer une page de vente ?' --max-chars 12000
```

The MCP tools `search_library`, `library_context`, `read_library_document`, and `library_status` provide the same access when loaded into Codex. The RAG command `search` returns JSON; `read IDENTIFIANT` reads a document. `--include-references --source stanford` or `--source yc-library` allows you to find conferences and content from founders.

Example requests: “Check my library to prepare an offer for this product”; “Look for references on customer interviews”; “Use our humanizer to rewrite this message.”

Hybrid search uses SQLite FTS5 and local multilingual embeddings. The third-party corpus is mainly in English; the original files are in French. `--lang fr` targets the latter. The extracts remain limited and sourced; no loading of the entire corpus in context.

## Read and apply

- [Browse by need](PARCOURS.md): access to French files and useful queries.
- [Sources and conditions of access](SOURCES.md); [version YAML](SOURCES.yaml).
- [Keyless Anna’s Archive browser bot — status and usage](ANNA-NAVIGATEUR.md).
- [Available domains, local OCR and session in memory](ANNA-DOMAINES-OCR.md).
- [Complete index of documents](INDEX.md): voluminous, to be consulted on request.
- [Our humanizer](../codex-skills/skills/toubi-humanizer/SKILL.md).
- [Conditions of collection and reuse](DROITS.md).
- [RAG validation and current limits](VALIDATION-RAG.md); [initial commit of 26 October](VALIDATION.md).

## Know what is actually available

| State | What can be consulted |
|---|---|
| `texte_local` | Full text uploaded with its original license and revision. |
| `fiche_originale` | Original advice written for this library, without claiming to demonstrate business performance. |
| `reference_seule` | URL and metadata. The lecture, transcript or article remains to be opened to the source. |

Titles from a sitemap are inferred from the URL and marked as such. A discovered link does not constitute reading, transcription, testing or validation of the resource. 34 Stanford transcripts are available locally; the other referenced conferences remain to be consulted. No videos have been uploaded. Massive bodies of data remain documented trails, not terabytes on disk.

Third-party guides and their SKILL.md remain documents. Viewing them does not activate their instructions or tools. Load only useful passages and keep citations, conditions and limitations.

## Our humanizer and access to the next rounds

Two original skills are prepared in `../codex-skills/skills/`: `toubi-humanizer` for French rewriting and `toubi-bibliotheque` for consultation. Copies are installed in `.agents/skills/` of this project for discovery when the library is the working folder. These are not the third-party skills collected.

The global installation cannot be performed in this session: the global folders are outside the write-authorized locations. From your usual terminal, this command also installs the MCP, the terminal command and monitoring:

```sh
sh '/home/toubi/01 - Dev/bibliotheque-business/DEMAIN.sh'
```

Activation preserves existing different versions. Then open a new Codex round and check `/mcp`. Even before this installation, the agent can read this document and search by its absolute path. The center pointer is `../BIBLIOTHEQUE.md`.

## Explicit maintenance

```sh
cd '/home/toubi/01 - Dev/bibliotheque-business'
python biblio.py stats
python biblio.py check
python biblio.py rebuild
python -m unittest discover -s tests -v
```

After a Markdown edit, `.venv/bin/python sync.py` refreshes both indexes. Monitoring does this automatically once enabled. SQLite indexes are derived; the originals remain preserved. `data/documents.jsonl` contains the exportable manifest.

For a new voluntary collection: `python collect.py`, then `python seed.py`, then `python biblio.py rebuild`. No refresh is automatic. The collector does not delete old archives or documents; a new revision may add separate versions. Blocked sources are logged without bypassing. `seed.py` regenerates the French files and the catalog: modify this file too if their content must be maintained.

The legacy lexical engine works with standard Python and SQLite FTS5. RAG dependencies and the template are installed in this folder. No API key or paid service for search; the Anna’s Archive option is separate and requires your own access.
