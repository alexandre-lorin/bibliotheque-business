# Local RAG search — version 0.2

The system finds passages in the library, then provides them with their sources to Codex. Codex produces the answer. No other chat templates, paid accounts, or remote services are needed to search.

## What is installed in this folder

- `.venv/`: Isolated Python environment, dependencies locked in `requirements-lock.txt`.
- `models/multilingual-e5-small/`: ONNX multilingual embeddings template, uploaded at specific revision.
- `data/rag.sqlite`: passages, FTS5 lexical index, vector cache and indexing status.
- `rag.py`: hybrid search, paginated reading and context preparation.
- `mcp_server.py`: four MCP documentary tools in studio.
- `books.py`: import of books and explicit download of authorized copies.
- `sync.py`: incremental indexing and optional monitoring.
- `DEMAIN.sh`: global activation of skills, MCP, terminal command and surveillance.

Search and MCP do not download content. Once the model is prepared, inference uses local files. Hugging Face telemetry and ONNX telemetry events are disabled in the search code. The system does not expose any network ports.

## Search

```sh
cd '/home/toubi/01 - Dev/bibliotheque-business'
.venv/bin/python rag.py search 'Comment expliquer le prix d’un abonnement facturé à l’année ?'
.venv/bin/python rag.py context 'Comment mener un entretien client ?' --max-chars 12000
.venv/bin/python rag.py search 'offre commerciale' --lang fr
.venv/bin/python rag.py search 'startup leadership' --include-references --source stanford
.venv/bin/python rag.py search 'annual billing' --mode semantic
.venv/bin/python rag.py status
```

By default, references alone are excluded. The results include `document_id`, `chunk_id`, path, source, section, page when it exists, character offsets, rights and recovery channels. To read more: `.venv/bin/python rag.py read IDENTIFIANT --start 12000`.

The context is limited to **characters**, not tokens. The scores are recovery ranks, not truth probabilities. The system can find a neighboring passage without answering the question: Codex must recognize missing evidence and check the changing information.

## Indexing

Markdowns remain the sources of truth. `data/rag.sqlite` is a derived index separate from the old lexical index. Trimming preserves all of the text and its offsets, with overlap to keep the transitions.

Embeddings use `intfloat/multilingual-e5-small`, revision `614241f622f53c4eeff9890bdc4f31cfecc418b3`, quantized ONNX file. The `query:` and `passage:` prefixes are applied. Entries that are too long are represented by several windows of 450 tokens, then a normalized weighted average; they are not simply truncated to 512 tokens. This choice is specific to this integration, not a guaranteed recommendation from the producer.

Lexical and semantic candidates are merged by Reciprocal Rank Fusion. The results limit repetition of the same document and heavily overlapping passages. SQLite and NumPy are sufficient for this library size; there is no additional Qdrant server.

Synchronization compares document fingerprints and reuses vectors by content and model version. Successful batches are retained after interruption. A lock serializes the indexers; WAL allows searches to read already validated data. A file deletion only removes its derived entries from the index, never an archived original.

```sh
.venv/bin/python sync.py
.venv/bin/python sync.py --watch --interval 60
```

`sources-locales.yaml` selects three central project documents and the two original skills from this library. The indexed copies of the skills remain documentary. The system does not vacuum personal files or entire repositories. Modifying this list allows you to voluntarily add a context Markdown; do not place files containing secrets there.

For unattended cooling: `.venv/bin/python rag.py index`. `--lexical-only` prepares passages without vector calculation. The old `python biblio.py search ...` remains usable without RAG dependencies.

## Books and documents

Supported formats: PDF with text, readable EPUB, TXT, MD and HTML UTF-8. Scanned PDFs without text are flagged as requiring OCR; no fake content is generated. Page numbers indicate position in the PDF, not necessarily printed pagination. The EPUB follows the reading order of the book; its sections are numbered for reference purposes, without claiming to reproduce the publisher's chapter numbers. Documents indicating encryption are refused; no DRM is bypassed. The originals are archived with SHA-256 fingerprint.

```sh
.venv/bin/python books.py import '/chemin/mon-livre.epub' \
  --title 'Mon livre' --author 'Auteur' --lang fr \
  --rights personal-copy --evidence 'Copie personnelle acquise légalement ; usage local'
.venv/bin/python sync.py
```

Rights are declared upon import, not legally validated by the program. They remain attached to the passages. Possession of a copy does not automatically grant the right to redistribute the text or use it to train a model.

To submit documents to import, use `entrees/`, accompanied by a JSON file:

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

The file should be located in `entrees/`. Without this declaration, it is not imported. Submitted originals are not automatically deleted.

The `books.py download URL --title ... --rights ... --evidence ... --format pdf` command downloads an authorized copy, with a limit of 80 MB. Signed link settings are not preserved in the catalog.

## Book Search and Anna’s Archive

**Keyless browser mode: [ANNA-NAVIGATEUR.md](ANNA-NAVIGATEUR.md).** Updated: [domain detection and local OCR](ANNA-DOMAINES-OCR.md). `.gl`, `.pk`, and `.gd` responded to welcome checks; `.gl` is preferred. Search remains subject to verification, and public OCR is not validated end-to-end. No actual Anna’s Archive downloads are reported as successful.

```sh
.venv/bin/python books.py search 'copywriting'
.venv/bin/python books.py anna-search 'Scientific Advertising Claude Hopkins'
```

The first command consults the Open Library catalog. The second prepares a search URL to open; it establishes neither availability nor rights. Third-party Anna’s Archive tools already exist, including [YassineAta/anna-archive](https://github.com/YassineAta/anna-archive). This repository has not been installed or run.

Our optional command `books.py anna-download MD5 --title ... --rights ... --evidence ... --format epub` uses the member API mechanism documented by this project. It requires your own variable `ANNA_ARCHIVE_API_KEY` and valid access; no subscription is created. The key is neither printed nor saved. The signed link remains in memory and the reference kept is the public page of the notice. No captcha, quota or paywall is bypassed.

**The Anna’s Archive API has not been validated in real conditions**: no account or key was provided, and the official FAQ was not accessible during preparation. The module remains optional; local import and open download were tested separately.

## Codex access

The MCP provides `search_library`, `library_context`, `read_library_document`, and `library_status`. They browse indexes without importing files, downloading books, or sending messages. The server only receives queries necessary for local search. Third-party documents remain unreliable data, including when they contain a SKILL.md.

The project configuration is in `.codex/config.toml`. Codex only charges it for an approved project. The global activation is in [DEMAIN.md](DEMAIN.md) ; it cannot be applied from the restricted session which prepared the project.

## Technical sources

- [Codex and MCP — official OpenAI](https://developers.openai.com/codex/mcp/) documentation.
- [MCP Python SDK](https://py.sdk.modelcontextprotocol.io/run/).
- [Multilingual model E5](https://huggingface.co/intfloat/multilingual-e5-small).
- [FastEmbed](https://github.com/qdrant/fastembed).
- [Open Library API](https://openlibrary.org/developers/api).

Validation, limitations, and verification results are provided in `VALIDATION-RAG.md` and `data/`.
