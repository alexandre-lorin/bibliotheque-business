# Full texts added on October 27 2026

107 additional documents, approximately 7,64 million characters extracted.
This count concerns the texts present, not the conference links.

| Collection | Documents | Content |
|---|---:|---|
| MIT OpenCourseWare | 64 | 12 transcriptions of New Enterprises and 52 supports of New Enterprises, Entrepreneurial Sales, Entrepreneurial Marketing |
| Stanford | 34 | 33 full lectures/interviews and an excerpt on the beginnings of NVIDIA |
| Virginia Tech | 2 | Fundamentals of Business, 4th Edition (2023), 448 PDF pages; Strategic Management (2020), 352 PDF pages |
| Gutenberg Classics | 3 | My Life and Work; Autobiography of Andrew Carnegie; The Art of Getting Money |
| Books provided by Toubi | 4 | $100M Offers; $100M Lost Chapters; The Personal MBA; third party comment from Ben Preston |

Examples Stanford: Reid Hoffman, Live Life in Permanent Beta; Jensen Huang,
First-Principles Thinking; Brian Chesky, Managing Through Crisis and Uncertainty;
Eric Yuan, Winning a Crowded Market ; Eric Ries, Evangelizing for the Lean Startup;
Steve Blank, Entrepreneurship Strengthens a Nation; How Instagram Scaled.

The books provided were located in the Downloads folder expressly indicated
by Toubi. Their file names prove neither editorial authenticity nor rights
of redistribution. Ben Preston's commentary is identified as a work
third party, not attributed to Alex Hormozi.

Originals remain in `archives/` and downloads from Toubi remain in
their original location. EPUBs are extracted in the order of the summary of
internal reading. AZW3 Lost Chapters was converted to EPUB with mobi 0.4.1,
without decryption; the original AZW3 is also archived. For PDFs,
page numbers denote the pages of the file, not necessarily the pagination
printed. The tables and illustrations are not reconstructed.

## Origin and limits

MIT: https://ocw.mit.edu/courses/15-390-new-enterprises-spring-2013/
and the other two courses saved in `enrich_sources.py`. The OCW license
includes exceptions for third-party elements; keep the original notices.
2002's marketing notes are a historical document, not a state of the current market.

Virginia Tech: https://doi.org/10.21061/fundamentalsofbusiness4e and
https://doi.org/10.21061/strategicmanagement. The licenses of their editions
respective are recorded in the metadata.

Stanford: transcripts directly published by STVP or GSB. Old PDFs
WordPress returned 404: current pages and their printable view allowed
to recover the text. An official transcript may contain errors.
These documents remain under copyright; no open license is asserted.
The success of a speaker does not prove the universal effectiveness of his advice.

Gutenberg: historical English editions, records preserved. These works
bear witness to their time; their advice does not constitute current facts.

OpenStax rejections and network failures are not counted as imports.
No additional books have been uploaded to Anna’s Archive.

## RAG access

Searchable sources are `livres-toubi`, `stanford-transcripts`, `mit-ocw`,
`virginia-tech` and `gutenberg-business`. Example:

```sh
.venv/bin/python rag.py search 'Comment construire une offre avec une équation de valeur ?' --source livres-toubi
.venv/bin/python rag.py search 'Comment comprendre les besoins des clients avant de développer le produit ?' --source stanford-transcripts
```

After a new import, launch `.venv/bin/python sync.py`.
Web collection remains explicit: `enrich_sources.py` uses a bounded selection
in `sources-completes.json`, not unlimited crawl. Virginia Tech imports
and personnel of this delivery are recorded separately in `data/`.

Reports: `data/enrichissement-bilan.json`,
`data/enrichissement-sources-completes.json`,
`data/enrichissement-stanford-actuel.json`, `data/imports-livres-toubi.json`,
`data/import-hormozi-lost-chapters.json`.

## Upcoming relevant books

Selection to acquire or provide as a personal copy: The Lean Startup (Eric
Ries), SPIN Selling (Neil Rackham), Influence (Robert Cialdini), Made to Stick
(Chip and Dan Heath), The Copywriter's Handbook (Robert Bly). They appear in the
[official Kaufman listing](https://personalmba.com/best-business-books/).
These five books are not downloaded and are not shown as available
in the base. Eric Ries' conference is available in full text.

For unencrypted MOBI/AZW3: the isolated local converter is in `.venv-books/`,
with dependencies locked in `requirements-books.txt`. He is called by
`books.py import` ; protected formats are not decrypted.
