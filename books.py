#!/usr/bin/env python3
"""Importer PDF/EPUB/MOBI/AZW3/TXT/MD/HTML, garder originaux et provenance."""
import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
import zipfile
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlencode, urlsplit
from urllib.request import Request, urlopen

import biblio

ROOT = biblio.ROOT
MAX_BYTES = 80_000_000
RIGHTS = ['public-domain', 'cc0', 'cc-by', 'cc-by-sa', 'cc-by-nc-sa', 'authorized', 'personal-copy']


class TextHTML(HTMLParser):
    def __init__(self):
        super().__init__()
        self.out = []
        self.skip = 0

    def handle_starttag(self, tag, attrs):
        if tag in ('script', 'style'):
            self.skip += 1
        elif tag in ('p', 'div', 'br', 'li', 'h1', 'h2', 'h3', 'section') and not self.skip:
            self.out.append('\n')

    def handle_endtag(self, tag):
        if tag in ('script', 'style'):
            self.skip = max(0, self.skip - 1)
        elif tag in ('p', 'div', 'li', 'h1', 'h2', 'h3', 'section') and not self.skip:
            self.out.append('\n')

    def handle_data(self, text):
        if not self.skip:
            self.out.append(text)

    def text(self):
        return re.sub(r'\n{3,}', '\n\n', ''.join(self.out)).strip()


def html_text(raw):
    parser = TextHTML()
    parser.feed(raw)
    return parser.text()


def extract(path):
    suffix = path.suffix.lower()
    if path.stat().st_size > MAX_BYTES:
        raise ValueError('Fichier de plus de 80 Mo : import refusé')
    if suffix in ('.mobi', '.azw3'):
        worker = ROOT / '.venv-books' / 'bin' / 'python'
        if not worker.is_file():
            raise ValueError('Convertisseur Kindle non installé dans .venv-books')
        with tempfile.TemporaryDirectory(prefix='toubi-kindle-') as folder:
            target = Path(folder) / 'converted'
            result = subprocess.run(
                [str(worker), str(ROOT / 'kindle_convert.py'), str(path.resolve()), str(target)],
                capture_output=True, timeout=120)
            if result.returncode:
                raise ValueError('Conversion Kindle impossible ; format non reconnu ou chiffré')
            outputs = list(Path(folder).glob('converted.*'))
            if len(outputs) != 1:
                raise ValueError('Sortie Kindle absente ou ambiguë')
            text, details = extract(outputs[0])
        return text, {**details, 'source_format': suffix[1:], 'converter': 'mobi-0.4.1'}
    if suffix == '.pdf':
        from pypdf import PdfReader
        with path.open('rb') as handle:
            reader = PdfReader(handle)
            if reader.is_encrypted:
                raise ValueError('PDF chiffré : utiliser un export autorisé non chiffré')
            count = len(reader.pages)
        if shutil.which('pdftotext'):
            # Le texte extrait ne transite pas par stdout de l'outil appelant.
            result = subprocess.run(['pdftotext', '-layout', str(path.resolve()), '-'], capture_output=True, timeout=180, check=True)
            parts = result.stdout.decode('utf-8').split('\f')
            if parts and not parts[-1].strip():
                parts.pop()
        else:
            reader = PdfReader(str(path))
            parts = [page.extract_text() or '' for page in reader.pages]
        text = '\n\n'.join(f'<!-- page: {n} -->\n\n## Page {n}\n\n{part.strip()}' for n, part in enumerate(parts, 1))
        if sum(len(p.strip()) for p in parts) < max(100, count * 20):
            raise ValueError('PDF sans couche texte suffisante : OCR requis, aucun faux texte généré')
        return text, {'format': 'pdf', 'pages': count, 'extractor': 'pdftotext' if shutil.which('pdftotext') else 'pypdf'}
    if suffix == '.epub':
        with zipfile.ZipFile(path) as archive:
            if sum(x.file_size for x in archive.infolist()) > 150_000_000:
                raise ValueError('EPUB décompressé trop volumineux')
            references = None
            if 'META-INF/encryption.xml' in archive.namelist():
                encryption = ET.fromstring(archive.read('META-INF/encryption.xml'))
                references = {e.attrib.get('URI', '') for e in encryption.iter()
                              if e.tag.endswith('}CipherReference') or e.tag == 'CipherReference'}
                if not references:
                    raise ValueError('EPUB avec déclaration de chiffrement vide ou invalide')
            container = ET.fromstring(archive.read('META-INF/container.xml'))
            package = next(e.attrib['full-path'] for e in container.iter() if e.tag.endswith('rootfile'))
            document = ET.fromstring(archive.read(package))
            base = Path(package).parent
            manifest = {e.attrib['id']: e.attrib['href'] for e in document.iter() if e.tag.endswith('}item')}
            if references is not None:
                fonts = {(base / e.attrib['href']).as_posix() for e in document.iter()
                         if e.tag.endswith('}item')
                         and ('font' in e.attrib.get('media-type', '')
                              or 'opentype' in e.attrib.get('media-type', ''))
                         and Path(e.attrib['href']).suffix.lower() in ('.ttf', '.otf', '.woff', '.woff2')}
                # Les polices ne sont ni lues ni déchiffrées. Le texte doit rester lisible.
                if not references or not references.issubset(fonts):
                    raise ValueError('EPUB avec contenu chiffré : fournir une copie lisible')
            chapters = []
            for e in document.iter():
                if e.tag.endswith('}itemref'):
                    target = (base / manifest[e.attrib['idref']]).as_posix()
                    text = html_text(archive.read(target).decode('utf-8-sig'))
                    if text:
                        chapters.append(f'## Section EPUB {len(chapters) + 1}\n\n' + text)
            return '\n\n'.join(chapters), {'format': 'epub', 'sections': len(chapters), 'extractor': 'epub-spine-html'}
    if suffix in ('.txt', '.md', '.html', '.htm'):
        text = path.read_text(encoding='utf-8-sig')
        return html_text(text) if suffix in ('.html', '.htm') else text, {'format': suffix[1:], 'extractor': 'utf8'}
    raise ValueError('Format non pris en charge : PDF, EPUB, MOBI, AZW3, TXT, MD ou HTML attendu')


def import_file(path, title, author, rights, evidence, language='fr', url=None, source='livres', root=ROOT):
    path = Path(path)
    if rights not in RIGHTS or not title.strip() or not evidence.strip():
        raise ValueError('Titre, droits déclarés et provenance des droits sont requis')
    raw = path.read_bytes() if path.stat().st_size <= MAX_BYTES else None
    if raw is None:
        raise ValueError('Fichier trop volumineux')
    text, details = extract(path)
    if len(text.strip()) < 100:
        raise ValueError('Contenu trop court ou extraction vide')
    content_hash = hashlib.sha256(text.encode()).hexdigest()
    identifier = 'livre-' + content_hash[:20]
    existing = root / 'contenus' / 'imports' / (identifier + '.md')
    if existing.exists():
        return {'id': identifier, 'duplicate': True, 'path': existing.relative_to(root).as_posix()}
    # read_text relit les fins de ligne en mode universel : même empreinte à la relecture.
    # L'identifiant historique reste fondé sur l'extraction pour les réimports identiques.
    text = text.replace('\r\n', '\n').replace('\r', '\n')
    content_hash = hashlib.sha256(text.encode()).hexdigest()
    original_hash = hashlib.sha256(raw).hexdigest()
    archived = root / 'archives' / 'imports' / (original_hash + path.suffix.lower())
    archived.parent.mkdir(parents=True, exist_ok=True)
    if not archived.exists():
        archived.write_bytes(raw)
    meta = {'id': identifier, 'title': title, 'author': author, 'source': source,
            'url': url or 'local://imports/' + identifier, 'kind': 'livre', 'language': language,
            'tags': ['livre', 'book', *re.findall(r'[^\W_]+', title.lower())],
            'rights': rights + ' — voir rights_evidence ; déclaration à respecter',
            'rights_code': rights, 'rights_evidence': evidence, 'rights_verification': 'déclarés à l’import',
            'status': 'texte_local', 'retrieved': datetime.now(timezone.utc).date().isoformat(),
            'content_sha256': content_hash, 'original_sha256': original_hash,
            'original_file': archived.relative_to(root).as_posix(), 'extraction': details}
    existing.parent.mkdir(parents=True, exist_ok=True)
    # Les originaux demeurent archivés ; l'index ne reçoit que le texte extrait.
    existing.write_text('---\n' + json.dumps(meta, ensure_ascii=False) + '\n---\n' + text, encoding='utf-8')
    return {'id': identifier, 'duplicate': False, 'path': existing.relative_to(root).as_posix(),
            'characters': len(text), 'extraction': details}


def get_bytes(url, limit=MAX_BYTES):
    parts = urlsplit(url)
    if parts.scheme != 'https' or parts.username or parts.password:
        raise ValueError('URL HTTPS publique requise, sans identifiants')
    if parts.hostname in ('localhost', '127.0.0.1', '::1'):
        raise ValueError('Hôte local refusé pour le téléchargement')
    with urlopen(Request(url, headers={'User-Agent': 'ToubiLibrary/0.2 (local research)'}), timeout=90) as response:
        data = response.read(limit + 1)
    if len(data) > limit:
        raise ValueError('Téléchargement trop volumineux')
    return data


def download(url, title, author, rights, evidence, language='en', source='livres', suffix=None, source_url=None, root=ROOT):
    if rights not in RIGHTS or not evidence.strip():
        raise ValueError('Droits et leur provenance requis avant téléchargement')
    extension = suffix or Path(urlsplit(url).path).suffix.lower()
    if extension not in ('.pdf', '.epub', '.txt', '.md', '.html'):
        raise ValueError('Extension inconnue ; préciser --format')
    raw = get_bytes(url)
    with tempfile.TemporaryDirectory(prefix='toubi-livre-') as folder:
        path = Path(folder) / ('document' + extension)
        path.write_bytes(raw)
        # Ne jamais enregistrer les paramètres d'un lien signé de téléchargement.
        public_url = source_url or url.split('?', 1)[0].split('#', 1)[0]
        return import_file(path, title, author, rights, evidence, language, public_url, source, root=root)


def catalog_search(query, limit=10):
    url = 'https://openlibrary.org/search.json?' + urlencode({'q': query, 'limit': min(25, max(1, limit)), 'fields': 'key,title,author_name,first_publish_year,isbn'})
    data = json.loads(get_bytes(url, 2_000_000))
    return [{'title': x.get('title'), 'authors': x.get('author_name', []),
             'year': x.get('first_publish_year'), 'url': 'https://openlibrary.org' + x['key'],
             'notice': 'Notice bibliographique ; les droits du texte restent à vérifier.'} for x in data.get('docs', [])]


def anna_url(query, base='https://annas-archive.gl'):
    parts = urlsplit(base)
    if parts.scheme != 'https' or not re.fullmatch(r'annas-archive\.[a-z]+', parts.hostname or ''):
        raise ValueError('Domaine Anna’s Archive HTTPS attendu')
    return base.rstrip('/') + '/search?' + urlencode({'q': query})


def anna_download(md5, base, key_env, **metadata):
    if metadata.get('rights') not in RIGHTS or not metadata.get('evidence', '').strip():
        raise ValueError('Droits et provenance requis avant de consulter l’API')
    if not re.fullmatch('[a-fA-F0-9]{32}', md5):
        raise ValueError('MD5 invalide')
    anna_url('', base)  # Validation de l'hôte.
    key = os.environ.get(key_env)
    if not key:
        raise ValueError(f'Clé absente dans la variable {key_env}. Aucun compte ni abonnement créé.')
    # La clé reste en mémoire, jamais dans les manifests ou messages d'erreur.
    endpoint = base.rstrip('/') + '/dyn/api/fast_download.json?' + urlencode({'md5': md5, 'key': key})
    try:
        response = json.loads(get_bytes(endpoint, 1_000_000))
        target = response.get('download_url')
        if not target:
            raise ValueError('Pas de lien fourni par le compte')
        return download(target, source_url=base.rstrip('/') + '/md5/' + md5.lower(), **metadata)
    except Exception:
        raise RuntimeError('Téléchargement Anna’s Archive non effectué. Vérifier accès, quota, droits et disponibilité ; aucun contournement ni nouvel essai automatique.') from None


def main():
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest='command', required=True)
    search = sub.add_parser('search')
    search.add_argument('query')
    search.add_argument('--limit', type=int, default=10)
    anna = sub.add_parser('anna-search')
    anna.add_argument('query')
    anna.add_argument('--base', default='https://annas-archive.gl')
    domains = sub.add_parser('anna-domains')
    domains.add_argument('--refresh', action='store_true', help='Consulter aussi les annuaires publics de domaines')
    browser_session = sub.add_parser('anna-browser-session')
    browser_session.add_argument('--base', default='auto')
    browser_session.add_argument('--text-captcha-ocr', action='store_true')
    browser_search = sub.add_parser('anna-browser-search')
    browser_search.add_argument('query')
    browser_search.add_argument('--base', default='auto')
    browser_search.add_argument('--limit', type=int, default=10)
    browser_search.add_argument('--headed', action='store_true')
    browser_search.add_argument('--wait-seconds', type=int)
    browser_search.add_argument('--manual-captcha', action='store_true', help='Ouvrir le navigateur et attendre une validation manuelle, sans enregistrement')
    browser_search.add_argument('--text-captcha-ocr', action='store_true', help='Proposer une réponse OCR locale au CAPTCHA textuel reconnu, une seule fois')
    browser_download = sub.add_parser('anna-browser-download')
    browser_download.add_argument('target')
    browser_download.add_argument('--base', default='auto')
    browser_download.add_argument('--title', required=True)
    browser_download.add_argument('--author', default='Non renseigné')
    browser_download.add_argument('--rights', choices=RIGHTS, required=True)
    browser_download.add_argument('--evidence', required=True)
    browser_download.add_argument('--lang', default='fr')
    browser_download.add_argument('--format', choices=['pdf', 'epub', 'txt', 'md', 'html'])
    browser_download.add_argument('--headed', action='store_true')
    browser_download.add_argument('--wait-seconds', type=int)
    browser_download.add_argument('--manual-captcha', action='store_true')
    browser_download.add_argument('--text-captcha-ocr', action='store_true')
    for name in ('import', 'download', 'anna-download'):
        q = sub.add_parser(name)
        q.add_argument('target')
        q.add_argument('--title', required=True)
        q.add_argument('--author', default='Non renseigné')
        q.add_argument('--rights', choices=RIGHTS, required=True)
        q.add_argument('--evidence', required=True, help='URL de licence ou provenance de votre autorisation')
        q.add_argument('--lang', default='fr')
        q.add_argument('--source', default='livres')
        if name != 'import':
            q.add_argument('--format', choices=['pdf', 'epub', 'txt', 'md', 'html'])
        if name == 'anna-download':
            q.add_argument('--base', default='https://annas-archive.gl')
            q.add_argument('--key-env', default='ANNA_ARCHIVE_API_KEY')
    a = p.parse_args()
    try:
        if a.command == 'search':
            result = catalog_search(a.query, a.limit)
        elif a.command == 'anna-search':
            result = {'url': anna_url(a.query, a.base), 'notice': 'Recherche à ouvrir dans le navigateur ; disponibilité et droits non vérifiés.'}
        elif a.command == 'anna-domains':
            import anna_domains
            result = anna_domains.check(a.refresh)
        elif a.command == 'anna-browser-session':
            import asyncio

            import anna_browser
            asyncio.run(anna_browser.session(a.base, text_captcha_ocr=a.text_captcha_ocr))
            return 0
        elif a.command in ('anna-browser-search', 'anna-browser-download'):
            import anna_browser
            if a.command == 'anna-browser-search':
                result = anna_browser.search(a.query, a.base, a.limit, a.headed, a.wait_seconds, a.manual_captcha, a.text_captcha_ocr)
            else:
                result = anna_browser.download(a.target, a.base, a.headed, a.wait_seconds, a.manual_captcha, a.text_captcha_ocr,
                                               title=a.title, author=a.author, rights=a.rights, evidence=a.evidence,
                                               language=a.lang, suffix='.' + a.format if a.format else None)
            print(json.dumps(result, ensure_ascii=False, indent=2))
            return 0 if result['status'] in ('catalog_ready', 'downloaded_imported') else 2
        else:
            kw = {'title': a.title, 'author': a.author, 'rights': a.rights, 'evidence': a.evidence, 'language': a.lang, 'source': a.source}
            if a.command == 'import':
                result = import_file(a.target, **kw)
            else:
                kw['suffix'] = '.' + a.format if a.format else None
                result = anna_download(a.target, a.base, a.key_env, **kw) if a.command == 'anna-download' else download(a.target, **kw)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    except Exception as exc:
        # Les erreurs réseau peuvent inclure un lien signé ; ne pas les afficher.
        print(str(exc) if isinstance(exc, (ValueError, RuntimeError)) else 'Import ou accès réseau impossible ; aucun contenu ajouté.', file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
