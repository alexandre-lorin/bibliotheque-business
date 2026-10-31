# RAG Validation — 27 October 2026

Version 0.2. Installation in `/home/toubi/01 - Dev/bibliotheque-business`, without modifying the global Codex configuration or enabling user services during preparation.

Later added 27 October: [Keyless Anna’s Archive browser mode](ANNA-NAVIGATEUR.md), Playwright and Chromium installed. The course tests use the real browser with a local server; the tested public domain `.li` is parked and the actual download from Anna's Archive remains uncommitted. The detailed report below describes the initial RAG delivery; the full suite now includes browser testing.

Added following: [domain checking and OCR local](ANNA-DOMAINES-OCR.md). Homes `.gl`, `.pk` and `.gd` have been verified with Chromium; `.gl` is preferred. OCR `ddddocr` and Python 3.12 are isolated in `.venv-ocr/`. The suite features 51 tests, including actual OCR on an original image and its submission on a local form, domain selection after failure and session recovery. A proposal on public CAPTCHA was not accepted; standalone resolution and download from Anna's Archive are therefore not validated.

## Corpus and cover

3 449 Markdown documents: 296 complete third-party guides and skills files, an OpenStax manual of 744 pages, 24 original French files, five selected local documents and 3 123 references without full text.

8 352 passages are indexed and vectorized, with zero missing vectors. The updated numbers are in `data/stats.json` and `data/rag-status-final.json`. The context preserves sources, rights, offsets and PDF pages when they exist. Conference titles from URLs remain inferred metadata, not transcripts.

The three central project files and the two original skills are explicitly selected in `sources-locales.yaml`. No general browsing of `/home/toubi`, no automatic import of repositories or personal files.

## Installation completed

Local Python environment 3.14.8, FastEmbed 0.9.1, MCP 2.3.0, ONNX Runtime 1.31.1, NumPy 2.5.4 and pypdf 6.21.2. Transitive versions are preserved in `requirements-lock.txt`; Ruff and PyYAML are used for validation.

The quantized multilingual E5 model is installed at the revision specified in `RAG.md`. The files have been fingerprinted. CPU inference with four threads; no additional conversation models are initiated in Ollama and no GPU is required.

The indexes of the first delivery are preserved. The new RAG index is separate, derived from Markdown, with vector cache and transactional writing. A second real sync returned `changed: false` and did not recalculate any vectors.

## Functional checks

- **25 tests passed**: old lexical engine tests, incremental indexing, updating and removing derived entries, filters, exclusion of default references, offsets, context bounding, transactions, imports, encryption, absence of OCR text, EPUB ordering, retention of originals, deduplication and incremental monitoring.
- **Lint Ruff succeeded** and Python syntax compilation; shell check `sh -n DEMAIN.sh` successful.
- **SQLite and File Integrity**: License checks and Markdown fingerprints, vector size, FTS coverage and model fingerprints passed. Report `data/rag-integrity.json`.
- **Actual embeddings**: finished outputs of 384 dimensions, unit standards, French and English entries, as well as text extending beyond the model window. Long passages are aggregated by windows instead of simply truncated. Report `data/embedding-real-check.json`.
- **Search with blocked Python connections**: real model loading and semantic recovery successful, without lexical fallback warning. This monitoring does not capture all native traffic on the system. Report `data/offline-retrieval-check.json`.
- **Real MCP stdio**: an SDK client launches the real server from `/tmp`, initializes the session, lists the four tools, searches, reads a document and prepares a context. No cloud accounts or calls. Report `data/mcp-smoke-final.json`.
- **Real CLI codex**: the server configuration has been parsed with reading overrides, without global writing. This check does not prove loading into a new Codex conversation. The project configuration remains subject to the trust placed in the project.
- **Skills**: the two original skills pass the official validator of the skill-creator; local copies and consistent sources. Global automatic discovery remains to be seen after activation.

Details and logs are kept in `data/`. Unit tests for some network import cases use a controlled response; they are not presented as validation of the Anna’s Archive API.

## Recovery assessment

Twenty French and English questions have been defined for this corpus, with expected documents. This is a local game prepared by the author of the integration, without independent evaluation and without measuring the final answers from Codex.

| Fashion | Document expected in the first 5 | In the first 8 | MRR on the first 8 |
|---|---:|---:|---:|
| Lexical | 19/20 | 19/20 | 0,925 |
| Semantics | 20/20 | 20/20 | 0,8708 |
| Hybrid | 19/20 | 19/20 | 0,9 |

Hybrid fusion is therefore not demonstrated to be superior in this game. It remains the default mode available, with explicit lexical and semantic modes. The recovery score is not a probability of truth.

The first evaluation pass showed a failure on the natural rewrite. The two original skills, until then accessible outside the index, were then added to the documentary corpus; the previous report is preserved in `data/evaluation-rag-avant-skills-originaux.json`. The table above concerns the enriched corpus: it is not a measurement on a game that has remained blind to all improvements. No general gain in agent performance is announced.

## Books and external access

*Introduction to Business* has been downloaded from the official OpenStax PDF. The license notice for this edition says CC BY 4.0. The PDF of 744 pages and its imprint are archived; 2 305 039 characters were extracted with `pdftotext`. This license is not extrapolated to other editions of the site.

Downloads of *Principles of Marketing* and *Business Ethics* failed with HTTP errors. No bypasses or false imports. The report is in `data/enrichissement-openstax.json`.

An actual bibliographic search via Open Library was successful. TXT, EPUB import and refusal of PDF without text are tested; OpenStax PDF validates the actual download and extraction journey. No OCR installed or advertised as available.

The Anna’s Archive member API is **optional and not validated in real conditions**. No accounts, keys, subscriptions or quotas have been used. The official FAQ was inaccessible; The integration relies on the third-party project documentation referenced in `RAG.md`. No promises of availability and no circumvention of restrictions.

## Global activation remaining

The single command is in `DEMAIN.md` and `DEMAIN.sh`. It brings together the activations of the first delivery and the RAG: two skills, global MCP, command `toubi-biblio` and synchronization user service. Existing different versions are retained.

This command was not applied: `~/.codex`, `~/.local/bin` and `~/.config/systemd/user` are outside the write-enabled folders during preparation. The service is therefore not announced as started. Its activation and loading of tools in a new Codex session remains to be seen from the usual terminal.

The activation script and its syntax are checked; the complete systemd installation and global registration journey remains unexecuted. No personal configurations were overwritten, no secrets posted or saved, no commits or releases.
