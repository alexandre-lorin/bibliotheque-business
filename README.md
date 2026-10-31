# Business Library — Local Search Engine

A local Markdown library engine with lexical search, optional retrieval-augmented generation (RAG), and an MCP server. Search results retain source and document-type information.

**This repository contains the engine, tests and technical documentation. It does not include the original books, document corpus, archives, generated indexes or private source configuration.**

## Requirements

Python 3.11 or newer. The lexical engine uses the standard library; optional components have their own dependencies.

```sh
git clone https://github.com/alexandre-lorin/bibliotheque-business.git
cd bibliotheque-business
python3 -m venv .venv
source .venv/bin/activate
python biblio.py --help
```

For optional RAG components, review `requirements-rag.txt`, the lockfiles and [RAG.md](RAG.md) before installing them. Provide your own appropriately licensed Markdown documents, configure their sources and build your own indexes. A fresh clone does not contain the original machine's library.

## Document provenance

The engine distinguishes full local text, original method sheets and reference-only records. A reference is not evidence that its contents were downloaded or read. Preserve provenance metadata and respect each source's redistribution conditions.

## Tests

```sh
python -m unittest discover -s tests -v
```

Some recipes require optional dependencies or a prepared corpus. Historical document counts and machine-specific installation paths in validation notes describe the original environment, not a fresh checkout.

## Documentation

- [Getting started](DEMARRER.md)
- [Local retrieval and RAG](RAG.md)
- [Collection and reuse rules](DROITS.md)
- [RAG validation record](VALIDATION-RAG.md)
- [Initial validation record](VALIDATION.md)

Cloning this repository does not activate downloads, background services or global integrations.
