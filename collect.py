#!/usr/bin/env python3
"""Collecte bornée : sources MIT en texte intégral, autres sites en références."""
import gzip
import hashlib
import io
import json
import re
import tarfile
import time
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from html import unescape
from html.parser import HTMLParser
from pathlib import PurePosixPath
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin, urlsplit, urlunsplit
from urllib.request import Request, urlopen
from urllib.robotparser import RobotFileParser

from biblio import ROOT, rebuild

AGENT = 'ToubiBusinessLibrary/1.0'
TODAY = datetime.now(timezone.utc).date().isoformat()
MAX_BYTES = 25_000_000
ROBOTS = {}
LAST = {}
EVENTS = []


def fetch(url):
    parts = urlsplit(url)
    if parts.scheme != 'https' or not parts.hostname:
        raise ValueError('HTTPS requis')
    request = Request(url, headers={'User-Agent': AGENT, 'Accept': '*/*'})
    try:
        with urlopen(request, timeout=25) as response:
            body = response.read(MAX_BYTES + 1)
            if len(body) > MAX_BYTES:
                raise ValueError('Réponse trop volumineuse')
            return body
    except HTTPError as exc:
        raise RuntimeError(f'HTTP {exc.code} pour {url}') from None
    except URLError as exc:
        raise RuntimeError(f'Réseau indisponible pour {url}: {exc.reason}') from None


def permitted_fetch(url):
    parts = urlsplit(url)
    origin = f'{parts.scheme}://{parts.netloc}'
    if origin not in ROBOTS:
        robot = RobotFileParser()
        # Une erreur robots interdit la collecte, sauf robots.txt réellement absent.
        try:
            raw = fetch(origin + '/robots.txt').decode('utf-8', errors='replace')
            if '<html' in raw.lower():
                raise RuntimeError('robots.txt renvoie du HTML')
            robot.parse(raw.splitlines())
            ROBOTS[origin] = robot
        except RuntimeError as exc:
            if 'HTTP 404 ' in str(exc):
                robot.parse([])
                ROBOTS[origin] = robot
            else:
                raise
    robot = ROBOTS[origin]
    if not robot.can_fetch(AGENT, url):
        raise RuntimeError('Accès robots refusé : ' + url)
    delay = max(1, robot.crawl_delay(AGENT) or robot.crawl_delay('*') or 0)
    time.sleep(max(0, LAST.get(origin, 0) + delay - time.monotonic()))
    try:
        return fetch(url)
    finally:
        LAST[origin] = time.monotonic()


def clean_url(url):
    parts = urlsplit(url)
    return urlunsplit((parts.scheme.lower(), parts.netloc.lower(), parts.path.rstrip('/') or '/', '', ''))


def write_doc(meta, body, folder):
    identifier = meta.get('id') or meta['source'] + '-' + hashlib.sha256(meta['url'].encode()).hexdigest()[:12]
    meta = {**meta, 'id': identifier, 'retrieved': TODAY}
    if meta['status'] == 'texte_local':
        meta['content_sha256'] = hashlib.sha256(body.encode()).hexdigest()
    path = ROOT / folder / meta['source'] / (identifier + '.md')
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text('---\n' + json.dumps(meta, ensure_ascii=False) + '\n---\n' + body, encoding='utf-8')
    return identifier


ALIASES = {
    'copywriting': 'rédaction écriture conversion vente titres accroches',
    'copy-editing': 'révision correction style réécriture naturel français',
    'customer-research': 'recherche client entretiens objections besoins verbatim',
    'humanizer': 'humaniser naturel voix style français réponse réécriture',
    'emails': 'email courriel séquence fidélisation',
    'cold-email': 'prospection email commercial démarchage',
    'offers': 'offre valeur prix garantie objections',
    'pricing': 'tarification prix abonnement monétisation',
    'content': 'contenu éditorial rédaction distribution',
    'sales': 'vente commercial prospection',
    'ads': 'publicité acquisition annonce',
    'seo': 'référencement recherche visibilité',
    'launch': 'lancement produit distribution',
    'onboarding': 'activation prise en main accueil',
    'cro': 'conversion optimisation page formulaire',
    'retention': 'rétention fidélisation abonnement',
    'brand': 'marque voix identité positionnement',
    'referral': 'recommandation parrainage bouche-à-oreille',
}


def tags_for(value):
    tags = set(re.findall(r'[a-zA-ZÀ-ÿ0-9]+', value.lower()))
    for term, aliases in ALIASES.items():
        if term in value.lower():
            tags.update(aliases.split())
    return sorted(tags)


def collect_repo(repo, source):
    # On fige d'abord la révision : archive, URL et licence désignent le même état.
    head = json.loads(fetch(f'https://api.github.com/repos/{repo}/commits/main'))
    sha = head['sha']
    archive_url = f'https://codeload.github.com/{repo}/tar.gz/{sha}'
    archive = fetch(archive_url)
    records = []
    with tarfile.open(fileobj=io.BytesIO(archive), mode='r:gz') as tar:
        members = tar.getmembers()
        licenses = [m for m in members if m.isfile() and len(PurePosixPath(m.name).parts) == 2 and PurePosixPath(m.name).name in ('LICENSE', 'LICENSE.md', 'LICENSE.txt')]
        if len(licenses) != 1:
            raise RuntimeError('Licence racine ambiguë : ' + repo)
        license_text = tar.extractfile(licenses[0]).read().decode('utf-8')
        if 'MIT License' not in license_text or 'Permission is hereby granted' not in license_text:
            raise RuntimeError('Licence MIT non confirmée : ' + repo)
        license_path = ROOT / 'licences' / (source + '.txt')
        license_path.parent.mkdir(exist_ok=True)
        license_path.write_text(license_text, encoding='utf-8')
        for member in members:
            parts = PurePosixPath(member.name).parts[1:]
            if not member.isfile() or not parts or member.size > 2_000_000:
                continue
            relative = '/'.join(parts)
            if not relative.endswith('.md'):
                continue
            if source == 'marketingskills' and not relative.startswith('skills/'):
                continue
            if source == 'humanizer-source' and relative not in ('SKILL.md', 'README.md'):
                continue
            body = tar.extractfile(member).read().decode('utf-8')
            headings = re.findall(r'^#\s+(.+)', body, re.MULTILINE)
            title = headings[0] if headings else relative
            skill = parts[1] if source == 'marketingskills' and len(parts) > 2 else 'humanizer'
            meta = dict(title=title, source=source,
                        url=f'https://github.com/{repo}/blob/{sha}/{relative}',
                        kind='skill-source' if relative.endswith('SKILL.md') else 'guide-source',
                        language='en', tags=tags_for(skill + ' ' + relative),
                        rights='MIT — conserver la notice de licence',
                        license_file=license_path.relative_to(ROOT).as_posix(),
                        revision=sha, upstream_path=relative, status='texte_local')
            records.append(write_doc(meta, body, 'contenus'))
    archive_path = ROOT / 'archives' / f'{source}-{sha}.tar.gz'
    archive_path.parent.mkdir(exist_ok=True)
    archive_path.write_bytes(archive)
    return dict(source=source, repository=repo, revision=sha, url=archive_url,
                archive=archive_path.relative_to(ROOT).as_posix(),
                sha256=hashlib.sha256(archive).hexdigest(), documents=len(records),
                retrieved=TODAY)


class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []
        self.href = None
        self.text = []
        self.page_data = None

    def handle_starttag(self, tag, attrs):
        attributes = dict(attrs)
        if 'data-page' in attributes:
            self.page_data = json.loads(attributes['data-page'])
        if tag == 'a':
            self.href = attributes.get('href')
            self.text = []

    def handle_data(self, data):
        if self.href:
            self.text.append(data)

    def handle_endtag(self, tag):
        if tag == 'a' and self.href:
            self.links.append((self.href, ' '.join(' '.join(self.text).split())))
            self.href = None


def reference(source, url, title, language='en', title_origin='anchor'):
    url = clean_url(url)
    tags = tags_for(urlsplit(url).path + ' ' + title)
    meta = dict(title=unescape(title), source=source, url=url, kind='reference',
                language=language, tags=tags,
                rights='Non déterminés pour le contenu intégral — lien et métadonnées uniquement',
                status='reference_seule', title_origin=title_origin,
                verification='URL découverte ; contenu individuel non lu')
    body = (f"# {meta['title']}\n\nSource : [{source}]({url})\n\n"
            f"Thèmes de recherche inférés du titre ou de l’URL : {', '.join(tags)}.\n\n"
            'Référence documentaire uniquement. Le texte, la vidéo et sa transcription ne sont pas stockés localement. '
            'Ouvrir la source avant d’en tirer une affirmation ou une synthèse. '
            'La découverte du lien ne confirme ni son accessibilité individuelle ni ses performances commerciales.\n')
    return write_doc(meta, body, 'references')


def sitemap(source, url, contains, language='en', limit=4000):
    raw = permitted_fetch(url)
    if raw[:2] == b'\x1f\x8b':
        raw = gzip.decompress(raw)
    tree = ET.fromstring(raw)
    if tree.tag.endswith('sitemapindex'):
        raise ValueError('Utiliser un sitemap de pages, pas un index : ' + url)
    count = 0
    for element in tree.iter():
        if not element.tag.endswith('}loc') and element.tag != 'loc':
            continue
        target = element.text or ''
        if urlsplit(target).netloc != urlsplit(url).netloc:
            continue
        if not any(part in urlsplit(target).path for part in contains):
            continue
        slug = urlsplit(target).path.rstrip('/').split('/')[-1]
        title = slug.replace('-', ' ').replace('_', ' ').strip().capitalize()
        reference(source, target, title, language, 'slug — titre inféré, non vérifié')
        count += 1
        if count >= limit:
            break
    return count


def page_links(source, url, contains, language='en', limit=500):
    parser = Links()
    parser.feed(permitted_fetch(url).decode('utf-8', errors='replace'))
    seen = set()
    for href, title in parser.links:
        target = clean_url(urljoin(url, href))
        if urlsplit(target).netloc != urlsplit(url).netloc or target in seen:
            continue
        if not title or len(title) < 8 or not any(p in urlsplit(target).path for p in contains):
            continue
        reference(source, target, title, language)
        seen.add(target)
        if len(seen) >= limit:
            break
    return len(seen)


def yc_library(source, url, contains=None, language='en', limit=4000):
    parser = Links()
    parser.feed(permitted_fetch(url).decode('utf-8', errors='replace'))
    seen = set()
    def walk(value):
        if isinstance(value, dict):
            # Seules les métadonnées titre/slug sont conservées, jamais le corps.
            slug, title = value.get('slug'), value.get('title')
            if isinstance(slug, str) and isinstance(title, str) and re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9-]+', slug):
                target = clean_url(urljoin(url + '/', slug))
                if target not in seen and len(seen) < limit:
                    reference(source, target, title, language, 'titre fourni par le catalogue YC')
                    seen.add(target)
            for key, child in value.items():
                if key not in ('content', 'body', 'transcript', 'description', 'html'):
                    walk(child)
        elif isinstance(value, list):
            for child in value:
                walk(child)
    walk((parser.page_data or {}).get('props', {}))
    return len(seen)


def main():
    # Les erreurs sont enregistrées sans contourner les blocages ni changer d'identité.
    data = ROOT / 'data'
    data.mkdir(exist_ok=True)
    archive_manifests = []
    for repo, source in [('coreyhaines31/marketingskills', 'marketingskills'), ('blader/humanizer', 'humanizer-source')]:
        try:
            record = collect_repo(repo, source)
            archive_manifests.append(record)
            print(json.dumps(record, ensure_ascii=False), flush=True)
        except Exception as exc:
            EVENTS.append(dict(source=source, error=str(exc)))
            print(source, str(exc), flush=True)
    jobs = [
        ('marketingexamples', sitemap, ('https://marketingexamples.com/sitemap.xml', ['/content/', '/copywriting/', '/sales/', '/seo/', '/ads/', '/brand/', '/landing-page/', '/retention/', '/referral/', '/social/', '/creative/'], 'en')),
        ('yc-library', yc_library, ('https://www.ycombinator.com/library', ['/library/'], 'en')),
        ('stanford', sitemap, ('https://stvp.stanford.edu/sitemap.xml', ['/av/'], 'en')),
        ('swiped', page_links, ('https://swiped.co/', ['/file/'], 'en')),
        ('copythat', page_links, ('https://www.copythatshow.com/', ['/'], 'en')),
        ('bpifrance-creation', page_links, ('https://bpifrance-creation.fr/webinaires', ['/webinaire', '/encyclopedie/'], 'fr')),
        ('acquisition', page_links, ('https://www.acquisition.com/training', ['/training/'], 'en')),
        ('growthunhinged', page_links, ('https://www.growthunhinged.com/', ['/p/'], 'en')),
    ]
    def run(job):
        source, function, args = job
        try:
            count = function(source, *args)
            return dict(source=source, references=count, retrieved=TODAY)
        except Exception as exc:
            return dict(source=source, error=str(exc), retrieved=TODAY)
    # Un seul job par domaine ; délais robots respectés à l'intérieur de chaque job.
    with ThreadPoolExecutor(max_workers=4) as pool:
        for result in pool.map(run, jobs):
            EVENTS.append(result)
            print(json.dumps(result, ensure_ascii=False), flush=True)
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    (data / f'collecte-{stamp}.json').write_text(json.dumps(dict(archives=archive_manifests, events=EVENTS), ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(rebuild(), ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
