#!/usr/bin/env python3
"""Ajouter trois manuels business OpenStax, avec licence lue dans le PDF exact."""
import io
import json
import tempfile
from pathlib import Path

from pypdf import PdfReader

import biblio
from books import get_bytes, import_file

BOOKS = [
    ('Principles of Marketing', 'Maria Gomez Albrecht, Mark Green, Linda Hoffman — OpenStax',
     'https://assets.openstax.org/oscms-prodcms/media/documents/Principles_Marketing-WEB.pdf'),
    ('Introduction to Business', 'Lawrence J. Gitman et al. — OpenStax',
     'https://assets.openstax.org/oscms-prodcms/media/documents/IntroductionToBusiness-OP_8D04gAa.pdf'),
    ('Business Ethics', 'Stephen M. Byars, Kurt Stanberry — OpenStax',
     'https://assets.openstax.org/oscms-prodcms/media/documents/BusinessEthics-OP.pdf'),
]


def main():
    records = []
    for title, author, url in BOOKS:
        print('Téléchargement : ' + title, flush=True)
        try:
            raw = get_bytes(url)
            reader = PdfReader(io.BytesIO(raw))
            front = '\n'.join(p.extract_text() or '' for p in reader.pages[:6])
            if 'Attribution-NonCommercial-ShareAlike' in front:
                rights = 'cc-by-nc-sa'
            elif 'Attribution 4.0' in front:
                rights = 'cc-by'
            else:
                raise ValueError('Licence non reconnue dans les premières pages du fichier')
            with tempfile.TemporaryDirectory(prefix='toubi-openstax-') as folder:
                path = Path(folder) / 'manuel.pdf'
                path.write_bytes(raw)
                record = import_file(path, title, author, rights, url + ' — notice de licence des premières pages du PDF exact archivé',
                                     'en', url, 'openstax')
            records.append({'title': title, 'license_in_pdf': rights, 'url': url, **record})
            print(json.dumps(records[-1], ensure_ascii=False), flush=True)
        except Exception as exc:
            record = {'title': title, 'error': type(exc).__name__, 'notice': 'Aucun contournement ; import non effectué.'}
            records.append(record)
            print(json.dumps(record), flush=True)
    (biblio.ROOT / 'data' / 'enrichissement-openstax.json').write_text(json.dumps(records, ensure_ascii=False, indent=2) + '\n')


if __name__ == '__main__':
    main()
