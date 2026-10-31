#!/usr/bin/env python3
"""Collecte explicite et bornée de cours, transcriptions et livres sélectionnés.

Aucun lancement automatique. Les originaux sont conservés ; sync.py indexe ensuite.
"""
import hashlib
import html
import json
import re
import tempfile
import zipfile
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin

import biblio
from books import extract, get_bytes, html_text, import_file
from collect import write_doc

ROOT = biblio.ROOT
COURSES = [
    ('15-390-new-enterprises-spring-2013', '15.390-spring-2013',
     'New Enterprises', 'William Aulet, Howard Anderson, Matt Marx'),
    ('15-387-entrepreneurial-sales-spring-2015', '15.387-spring-2015',
     'Entrepreneurial Sales', 'Lou Shipley, Kirk Arnold, Dennis Hoffman'),
    ('15-835-entrepreneurial-marketing-spring-2002', '15.835-spring-2002',
     'Entrepreneurial Marketing', 'Jin Gyo Kim'),
]
BOOKS = [
    (7213, 'My Life and Work (1922)', 'Henry Ford, Samuel Crowther'),
    (17976, 'Autobiography of Andrew Carnegie (1920)', 'Andrew Carnegie ; éd. John C. Van Dyke'),
    (8581, 'The Art of Money Getting (1880)', 'P. T. Barnum'),
]


class DivBlocks(HTMLParser):
    """Capturer uniquement les sous-arbres div portant la classe sélectionnée."""
    def __init__(self, class_name):
        super().__init__(convert_charrefs=False)
        self.class_name = class_name
        self.depth = 0
        self.current = []
        self.blocks = []

    def handle_starttag(self, tag, attrs):
        if self.depth:
            if tag == 'div':
                self.depth += 1
            self.current.append(self.get_starttag_text())
        elif tag == 'div' and self.class_name in (dict(attrs).get('class') or '').split():
            self.depth = 1
            self.current = []

    def handle_endtag(self, tag):
        if not self.depth:
            return
        if tag == 'div':
            self.depth -= 1
        if self.depth:
            self.current.append('</' + tag + '>')
        else:
            self.blocks.append(''.join(self.current))
            self.current = []

    def handle_data(self, data):
        if self.depth:
            self.current.append(data)

    def handle_entityref(self, name):
        self.handle_data('&' + name + ';')

    def handle_charref(self, name):
        self.handle_data('&#' + name + ';')


def transcript_text(page, gsb=False):
    parser = DivBlocks('description' if gsb else 'su-media-transcript')
    parser.feed(page)
    texts = [html_text(block) for block in parser.blocks]
    if gsb:
        texts = [text for text in texts if text.lstrip().startswith('Full Transcript')]
    if not texts or len(max(texts, key=len)) < 1000:
        raise ValueError('Transcription complète non trouvée ; page non importée')
    return max(texts, key=len)


def import_stanford(url):
    raw = get_bytes(url)
    page = raw.decode('utf-8')
    title = title_from_page(page)
    gsb = 'www.gsb.stanford.edu' in url
    if not gsb:
        match = re.search(r'href="(/node/\d+/printable/print)"', page)
        if not match:
            raise ValueError('Aucun lien officiel de transcription')
        raw = get_bytes(urljoin(url, match[1]))
        page = raw.decode('utf-8')
    text = transcript_text(page, gsb)
    captions = re.findall(r'href="([^"]+\.srt)"', page)
    transcript_url = url if gsb else urljoin(url, captions[0]) if captions else url
    speakers = re.findall(r'href="(?:https://stvp.stanford.edu)?/people/[^\"]+"[^>]*>(.*?)</a>', page, re.S)
    author = ', '.join(dict.fromkeys(html_text(x) for x in speakers)) or 'Intervenants indiqués dans la transcription'
    sha = hashlib.sha256(raw).hexdigest()
    archived = ROOT / 'archives' / 'sources' / (sha + '.html')
    archived.parent.mkdir(parents=True, exist_ok=True)
    archived.write_bytes(raw)
    identifier = 'stanford-transcript-' + hashlib.sha256(url.encode()).hexdigest()[:16]
    path = ROOT / 'contenus' / 'stanford-transcripts' / (identifier + '.md')
    duplicate = path.exists()
    meta = {
        'id': identifier, 'title': title, 'author': author, 'source': 'stanford-transcripts',
        'url': transcript_url, 'event_url': url, 'kind': 'transcription-conference',
        'status': 'texte_local', 'language': 'en',
        'tags': ['conférence', 'transcription', 'entrepreneuriat', 'business',
                 *re.findall(r'[^\W_]+', title.lower())],
        'rights': 'Copyright Stanford et ayants droit ; transcription proposée publiquement '
                  'par la source. Consultation locale ; aucune licence ouverte ni permission '
                  'de redistribution affirmée.',
        'original_file': archived.relative_to(ROOT).as_posix(), 'original_sha256': sha,
        'quality_note': 'Transcription officielle publiée ; erreurs de transcription possibles. '
                        'Témoignage/opinion à dater, sans garantie de résultat.',
    }
    write_doc(meta, text, 'contenus')
    return {'id': identifier, 'title': title, 'author': author, 'url': url,
            'path': path.relative_to(ROOT).as_posix(), 'characters': len(text),
            'duplicate': duplicate}


def title_from_page(page):
    match = re.search(r'<title>(.*?)</title>', page, re.S)
    if not match:
        raise ValueError('Titre source absent')
    return html.unescape(match[1].split('|')[0]).strip()


def save_pdf(raw, title, author, url, source, kind, evidence, archive=None):
    """Texte intégral du PDF, sans transformer une mise à disposition en licence."""
    with tempfile.TemporaryDirectory(prefix='toubi-sources-') as folder:
        path = Path(folder) / 'source.pdf'
        path.write_bytes(raw)
        text, details = extract(path)
    if len(text.strip()) < 150:
        raise ValueError('PDF sans texte exploitable : OCR non effectué')
    sha = hashlib.sha256(raw).hexdigest()
    original = ROOT / 'archives' / 'sources' / (sha + '.pdf')
    original.parent.mkdir(parents=True, exist_ok=True)
    if not original.exists():
        original.write_bytes(raw)
    identifier = source + '-' + hashlib.sha256(url.encode()).hexdigest()[:16]
    destination = ROOT / 'contenus' / source / (identifier + '.md')
    duplicate = destination.exists()
    meta = {
        'id': identifier, 'title': title, 'author': author, 'url': url,
        'source': source, 'kind': kind, 'status': 'texte_local', 'language': 'en',
        'tags': ['business', 'entrepreneuriat', 'vente', 'marketing',
                 *re.findall(r'[^\W_]+', title.lower())],
        'rights': evidence, 'rights_evidence': evidence,
        'original_file': original.relative_to(ROOT).as_posix(),
        'original_sha256': sha, 'extraction': details,
        'quality_note': 'Texte extrait du PDF ; tableaux et illustrations non reconstitués. '
                        'Propos historiques ou opinions, pas preuve de performance.',
    }
    if archive:
        meta['course_archive'] = archive
    write_doc(meta, text, 'contenus')
    return {'id': identifier, 'title': title, 'source': source, 'kind': kind,
            'duplicate': duplicate, 'characters': len(text), 'pages': details.get('pages'),
            'path': destination.relative_to(ROOT).as_posix(), 'url': url}


def import_course(slug, name, title, author):
    base = 'https://ocw.mit.edu/courses/' + slug + '/'
    archive = ROOT / 'archives' / (name + '.zip')
    if not archive.exists():
        archive.write_bytes(get_bytes(base + name + '.zip'))
    results = []
    with zipfile.ZipFile(archive) as bundle:
        names = set(bundle.namelist())
        # Sélection uniquement depuis la rubrique notes, pas les lectures externes.
        note_page = bundle.read('pages/lecture-notes/index.html').decode()
        allowed = {'static_resources/' + Path(x).name for x in
                   re.findall(r'href="([^"]+\.pdf)"', note_page)}
        # Certaines pages ne lient que les fiches de ressource.
        resource_pages = {x.removeprefix('../../') for x in
                          re.findall(r'href="([^"]+resources/[^\"]+/index.html)"', note_page)}
        for page_name in sorted(names):
            if not page_name.startswith('resources/') or not page_name.endswith('/index.html'):
                continue
            page = bundle.read(page_name).decode()
            transcript = re.search(r'data-transcriptlink\s*=\s*"([^"]+\.pdf)"', page)
            if transcript:
                files = [transcript[1]]
                kind = 'transcription-conference'
            elif page_name in resource_pages:
                files = re.findall(r'href="([^"]+\.pdf)"', page)
                kind = 'cours-notes'
            else:
                continue
            seen = set()
            for link in files:
                member = 'static_resources/' + Path(link).name
                if member not in names or member in seen:
                    continue
                seen.add(member)
                if not transcript and allowed and member not in allowed:
                    continue
                try:
                    result = save_pdf(
                        bundle.read(member), title + ' — ' + title_from_page(page), author,
                        base + Path(member).name, 'mit-ocw', kind,
                        'MIT OpenCourseWare, CC BY-NC-SA 4.0 sauf éléments tiers signalés ; '
                        'conserver notices et exceptions du PDF. https://ocw.mit.edu/terms/',
                        archive.relative_to(ROOT).as_posix())
                    results.append(result)
                except Exception as exc:
                    results.append({'url': base + Path(member).name, 'error': str(exc)})
    return results


def main():
    report = {'courses': [], 'talks': [], 'books': [], 'errors': []}
    for course in COURSES:
        try:
            items = import_course(*course)
            report['courses'].extend(items)
            print(course[2], len(items), 'ressources', flush=True)
        except Exception as exc:
            report['errors'].append({'source': course[0], 'error': str(exc)})
    config = json.loads((ROOT / 'sources-completes.json').read_text())
    for url in config['stanford_urls']:
        try:
            item = import_stanford(url)
            report['talks'].append(item)
            print('Stanford', item['title'], item['characters'], 'caractères', flush=True)
        except Exception as exc:
            report['errors'].append({'url': url, 'error': str(exc)})
    for number, title, author in BOOKS:
        url = f'https://www.gutenberg.org/cache/epub/{number}/pg{number}.txt'
        try:
            with tempfile.TemporaryDirectory(prefix='toubi-book-') as folder:
                path = Path(folder) / 'book.txt'
                path.write_bytes(get_bytes(url))
                item = import_file(path, title, author, 'public-domain',
                                   f'Project Gutenberg #{number}, édition anglaise historique ; '
                                   'domaine public USA. Auteurs et éditeur décédés depuis plus de 70 ans ; '
                                   'conserver la notice Gutenberg du fichier.', 'en', url, 'gutenberg-business')
            report['books'].append({'title': title, 'url': url, **item})
            print('Livre', title, flush=True)
        except Exception as exc:
            report['errors'].append({'url': url, 'error': str(exc)})
    target = ROOT / 'data' / 'enrichissement-sources-completes.json'
    target.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    print('Rapport :', target.relative_to(ROOT), flush=True)


if __name__ == '__main__':
    main()
