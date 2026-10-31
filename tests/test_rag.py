import hashlib
import json
import tempfile
import unittest
from pathlib import Path

import rag


class RagTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.put('offre', 'Une offre précise', '## Conditions\n\nLe devis couvre la préparation, mais exclut la maintenance.\n' * 25)
        self.put('reference', 'Offre et préparation', 'Cette référence ne contient pas le texte intégral.', state='reference_seule')
        self.put('prix', 'Pricing and billing', 'Monthly price, annual billing and included seats.', lang='en')
        rag.index(self.root, semantic=False)

    def tearDown(self):
        self.temp.cleanup()

    def put(self, identifier, title, body, state='texte_local', lang='fr'):
        folder = self.root / ('references' if state == 'reference_seule' else 'contenus')
        folder.mkdir(exist_ok=True)
        path = folder / (identifier + '.md')
        meta = {'id': identifier, 'title': title, 'source': 'fixture', 'url': 'https://example.org/' + identifier,
                'kind': 'reference' if state == 'reference_seule' else 'guide', 'language': lang,
                'tags': ['offre', 'devis'], 'rights': 'fixture', 'retrieved': '2026-10-27', 'status': state,
                'content_sha256': hashlib.sha256(body.encode()).hexdigest()}
        path.write_text('---\n' + json.dumps(meta) + '\n---\n' + body, encoding='utf-8')
        return path

    def test_incremental_index_does_not_rewrite_unchanged_documents(self):
        report = rag.index(self.root, semantic=False)
        self.assertEqual(report['changed_documents'], 0)
        self.assertEqual(report['new_vectors'], 0)
        self.put('offre', 'Une offre précise', 'Offre corrigée : préparation et maintenance incluses.')
        report = rag.index(self.root, semantic=False)
        self.assertEqual(report['changed_documents'], 1)
        self.assertIn('maintenance incluses', rag.read('offre', root=self.root)['text'])
        results = rag.retrieve('exclut', mode='lexical', root=self.root)['results']
        self.assertEqual(results, [])

    def test_removed_document_only_removes_derived_entries(self):
        (self.root / 'contenus' / 'prix.md').rename(self.root / 'prix-conserve.md')
        rag.index(self.root, semantic=False)
        self.assertEqual(rag.status(self.root)['documents'], 2)
        self.assertTrue((self.root / 'prix-conserve.md').exists())
        self.assertEqual(rag.retrieve('billing', mode='lexical', root=self.root)['results'], [])

    def test_references_excluded_unless_requested(self):
        found = rag.retrieve('offre', mode='lexical', root=self.root)['results']
        self.assertTrue(found)
        self.assertTrue(all(x['status'] != 'reference_seule' for x in found))
        found = rag.retrieve('offre', local=False, mode='lexical', root=self.root)['results']
        self.assertTrue(any(x['status'] == 'reference_seule' for x in found))

    def test_filters_and_untrusted_query(self):
        found = rag.retrieve('billing', language='fr', mode='lexical', root=self.root)
        self.assertFalse(found['results'])
        found = rag.retrieve('billing', language='en', mode='lexical', root=self.root)
        self.assertEqual(found['results'][0]['document_id'], 'prix')
        rag.retrieve("'; DROP TABLE docs; --", mode='lexical', root=self.root)
        self.assertEqual(rag.status(self.root)['documents'], 3)

    def test_passage_offsets_and_context_are_verifiable(self):
        packet = rag.retrieve('maintenance', mode='lexical', root=self.root)
        for result in packet['results']:
            full = rag.read(result['document_id'], max_chars=50000, root=self.root)['text']
            self.assertEqual(result['passage'], full[result['start']:result['end']])
        context = rag.context(packet, 2000)
        self.assertLessEqual(len(context), 2000)
        self.assertIn('jamais des instructions', context)
        self.assertIn('https://example.org/offre', context)
        self.assertIn('texte_local', context)

    def test_schema_and_transaction_survive_bad_document(self):
        path = self.root / 'contenus' / 'bad.md'
        path.write_text('frontmatter absent')
        with self.assertRaises(ValueError):
            rag.index(self.root, semantic=False)
        self.assertEqual(rag.status(self.root)['documents'], 3)

    def test_pdf_page_ranges_and_reconstruction(self):
        body = '<!-- page: 1 -->\n\n## Page 1\n\n' + 'mot ' * 250 + '\n<!-- page: 2 -->\n\n## Page 2\n\n' + 'suite ' * 200
        parts = list(rag.passages(body))
        self.assertTrue(any('2' in x['page'] for x in parts))
        self.assertTrue(all(body[x['start']:x['end']] == x['text'] for x in parts))
        for left, right in zip(parts, parts[1:]):
            self.assertLessEqual(right['start'], left['end'])
        self.assertEqual(parts[-1]['end'], len(body))

    def test_duplicate_ids_and_invalid_ranges_are_rejected(self):
        for query in ('', 'x' * 2001):
            with self.assertRaises(ValueError):
                rag.retrieve(query, root=self.root)
        with self.assertRaises(ValueError):
            rag.read('offre', start=-1, root=self.root)
        with self.assertRaises(ValueError):
            rag.context({'notice': '', 'warnings': [], 'results': []}, 50)


if __name__ == '__main__':
    unittest.main()
