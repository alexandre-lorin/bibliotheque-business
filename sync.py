#!/usr/bin/env python3
"""Actualiser les index et les sources locales explicitement sélectionnées."""
import argparse
import hashlib
import json
import sys
import time

import biblio
import rag
from books import import_file

ROOT = biblio.ROOT


def sync_sources():
    config = ROOT / 'sources-locales.yaml'
    if not config.exists():
        return []
    sources = json.loads(config.read_text())['sources']
    reports = []
    for item in sources:
        path = (ROOT / item['path']).resolve()
        if not path.is_file() or path.suffix.lower() != '.md':
            reports.append({'path': item['path'], 'error': 'Markdown absent'})
            continue
        text = path.read_text(encoding='utf-8')
        identifier = 'contexte-' + hashlib.sha256(str(path).encode()).hexdigest()[:16]
        destination = ROOT / 'contenus' / 'contexte-toubi' / (identifier + '.md')
        meta = {'id': identifier, 'title': item['title'], 'source': item.get('source', 'contexte-toubi'), 'url': path.as_uri(),
                'kind': item.get('kind', 'contexte-local'), 'language': 'fr', 'tags': item.get('tags', ['toubi', 'projets', 'catalogue', 'contexte']),
                'rights': 'Documentation locale de Toubi ; usage local', 'status': 'texte_local',
                'retrieved': time.strftime('%Y-%m-%d', time.gmtime(path.stat().st_mtime)),
                'content_sha256': hashlib.sha256(text.encode()).hexdigest(), 'original_path': str(path)}
        content = '---\n' + json.dumps(meta, ensure_ascii=False) + '\n---\n' + text
        if not destination.exists() or destination.read_text(encoding='utf-8') != content:
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_text(content, encoding='utf-8')
            reports.append({'path': item['path'], 'updated': identifier})
    # Les entrées attendent un sidecar déclarant leur provenance avant import.
    inbox = ROOT / 'entrees'
    inbox.mkdir(exist_ok=True)
    cache_path = ROOT / 'data' / 'inbox-state.json'
    cache = json.loads(cache_path.read_text()) if cache_path.exists() else {}
    changed_cache = False
    for sidecar in sorted(inbox.glob('*.json')):
        try:
            record = json.loads(sidecar.read_text())
            file = (inbox / record['file']).resolve()
            if not file.is_relative_to(inbox.resolve()):
                raise ValueError('Le fichier doit se trouver dans entrees/')
            stat = file.stat()
            key = hashlib.sha256((sidecar.read_text() + str(stat.st_mtime_ns) + str(stat.st_size)).encode()).hexdigest()
            previous = cache.get(sidecar.name, {})
            if previous.get('key') == key and (ROOT / previous.get('path', 'missing')).is_file():
                continue
            result = import_file(file, record['title'], record.get('author', 'Non renseigné'),
                                 record['rights'], record['evidence'], record.get('language', 'fr'), record.get('url'), root=ROOT)
            cache[sidecar.name] = {'key': key, 'path': result['path']}
            changed_cache = True
            if not result['duplicate']:
                reports.append(result)
        except Exception:
            reports.append({'manifest': sidecar.name, 'error': 'Import non effectué ; vérifier fichier, format et déclaration de droits.'})
    if changed_cache:
        cache_path.write_text(json.dumps(cache, indent=2) + '\n')
    return reports


def fingerprint():
    values = []
    for folder in ('contenus', 'fiches', 'references'):
        for path in sorted((ROOT / folder).rglob('*.md')):
            stat = path.stat()
            values.append(f'{path}:{stat.st_mtime_ns}:{stat.st_size}')
    return hashlib.sha256('\n'.join(values).encode()).hexdigest()


def once():
    reports = sync_sources()
    current = fingerprint()
    state = ROOT / 'data' / 'sync-state.json'
    previous = json.loads(state.read_text()).get('fingerprint') if state.exists() else None
    if current == previous and rag.status().get('missing_vectors') == 0 and 'error' not in rag.status():
        return {'changed': False, 'sources': reports}
    biblio.rebuild()
    result = rag.index()
    state.write_text(json.dumps({'fingerprint': current, 'updated': rag.utcnow()}, indent=2) + '\n')
    return {'changed': True, 'sources': reports, 'index': result}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--watch', action='store_true')
    p.add_argument('--interval', type=int, default=60)
    a = p.parse_args()
    if a.interval < 15:
        p.error('Intervalle minimum : 15 secondes')
    while True:
        try:
            print(json.dumps(once(), ensure_ascii=False), flush=True)
        except Exception as exc:
            print(type(exc).__name__ + ' : synchronisation non terminée, relancer pour reprendre.', file=sys.stderr, flush=True)
            if not a.watch:
                return 1
        if not a.watch:
            return 0
        time.sleep(a.interval)


if __name__ == '__main__':
    sys.exit(main())
