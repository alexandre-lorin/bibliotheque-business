#!/usr/bin/env python3
"""Petit jeu de récupération déclaré à l'avance ; ne mesure pas la qualité des réponses."""
import json
import time

import rag


def matches(result, case):
    return (result['document_id'] in case['expected_ids']
            or any(part in result.get('upstream_path', '') or part in result['source'] for part in case['expected_paths']))


def main():
    cases = json.loads((rag.ROOT / 'eval_queries.json').read_text())
    report = {'notice': 'Jeu local de 20 questions préparées pour ce corpus, non indépendant. Pertinence par documents attendus ; pas de mesure de réponse finale.',
              'model': rag.MODEL_KEY, 'index': rag.status(), 'runs': []}
    for mode in ('lexical', 'semantic', 'hybrid'):
        rows = []
        for case in cases:
            start = time.monotonic()
            packet = rag.retrieve(case['query'], mode=mode, limit=8, max_per_document=1)
            positions = [n for n, x in enumerate(packet['results'], 1) if matches(x, case)]
            rows.append({'query': case['query'], 'first_expected_rank': min(positions) if positions else None,
                         'hit_at_5': any(n <= 5 for n in positions), 'hit_at_8': bool(positions),
                         'seconds': round(time.monotonic() - start, 4), 'warnings': packet['warnings'],
                         'documents': [x['document_id'] for x in packet['results']]})
        report['runs'].append({'mode': mode, 'questions': len(rows),
                               'hit_at_5': sum(x['hit_at_5'] for x in rows),
                               'hit_at_8': sum(x['hit_at_8'] for x in rows),
                               'mrr_at_8': round(sum(1 / x['first_expected_rank'] if x['first_expected_rank'] else 0 for x in rows) / len(rows), 4),
                               'rows': rows})
        print(json.dumps({k: v for k, v in report['runs'][-1].items() if k != 'rows'}), flush=True)
    (rag.ROOT / 'data' / 'evaluation-rag.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')


if __name__ == '__main__':
    main()
