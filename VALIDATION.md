# Local validation — 26 October 2026

## Delivered status

- 3 442 indexed Markdown entries.
- 296 complete texts under MIT: 53 skills files and 243 guides or associated documents.
- 24 original sheets in French.
- 3 122 references to sources, articles, courses and conferences, without their full text.
- 23 sources in the editorial catalog, plus the files from Toubi.
- 3 056 489 complete third-party text characters; the other characters counted in the statistics are reference files and metadata.

References include the Y Combinator public catalog and 2 485 URL of Stanford conferences or podcasts taken from the sitemap. Stanford titles are inferred from URLs. Individual pages and transcripts have not been read or downloaded. Their links may become unavailable.

## Verifications carried out

`python -m unittest discover -s tests -v`: Nine tests passed on real local SQLite FTS5 engine. They cover search without accents, filters, deduplication of passages, full reading, context bounding and conservation of sources, repeated reconstruction, transaction canceled on invalid document, detection of an alteration and lossless cutting.

The collectors were run on the actual sources. Import of MIT archives, recovery of YC metadata and Stanford sitemap was successful. Collection reports retain revisions, dates, fingerprints, volumes and errors. Some dynamic catalogs do not deliver their content via HTML links: no exhaustive coverage is announced for Bpifrance, Really Good Emails or sources with variable access.

`python biblio.py check`: consistency of identifiers, absence of duplicate URLs, presence of associated licenses and fingerprints of imported texts verified.

Lint Ruff: passed, rules E4/E7/E9/F/I. Standard Python only for execution. No specific type checkers are configured for this small project.

The two new skills pass the official `quick_validate.py` of `skill-creator`. Their selective installation in `.agents/skills/` of the project was successful. The original instructions and their local copies are identical. No collected third-party skills have been activated.

The [humanizer was applied to five examples](EVALUATION-HUMANIZER.md), then reread in this session. This verification illustrates its instructions; it is not an independent assessment of editorial quality.

## Audit of the structure

Markdowns remain the source of truth. The SQLite index is derived and can be rebuilt. The search does not initiate any network calls and does not load the entire corpus into the agent context. Excerpts retain source, status and rights; Third-party documents are flagged as unreliable document data.

The collection is explicit and limited, does not bypass refusals and does not delete archives. The contents selected in the archives are read without executing the commands they contain. New upstream revisions may add separate versions; size is therefore not a measure of the number of unique subjects.

A Git repository was initialized before writing the project. No commits, releases, or changes to active projects have been made. The central catalogs and skills documentation have been completed.

## Limits

The library is not an exhaustive collection of the web nor a validated training corpus. Third-party texts are mainly in English. The search is lexical, without automatic translation or embeddings. References do not prove reading or business performance. Changing information should be double-checked at the source.

The skills are installed locally, but not globally: `~/.codex/skills` is outside the write-authorized locations in this session. The global installation command is provided in [START.md](DEMARRER.md). The automatic discovery of skills must be noted during the next round in the appropriate file; their presence on disk does not prove that an already open session loaded them.
