import hashlib
import json
import tempfile
import unittest
from pathlib import Path

import biblio
from collect import Links, clean_url


class LibraryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.add('local', 'Écrire une offre', 'Cette offre traite les objections et précise le prix.\n' * 100)
        self.add('reference', 'Offre et objections de vente', 'Lien seulement.\n', status='reference_seule')
        self.add('english', 'Pricing guide', 'Pricing tiers, annual billing and fees.', language='en', source='other')
        biblio.rebuild(self.root)

    def tearDown(self):
        self.temp.cleanup()

    def add(self, identifier, title, body, status='texte_local', language='fr', source='test'):
        directory = self.root / ('references' if status == 'reference_seule' else 'contenus')
        directory.mkdir(exist_ok=True)
        meta = dict(id=identifier, title=title, source=source, url='https://example.org/' + identifier,
                    kind='reference' if status == 'reference_seule' else 'guide-source', language=language,
                    tags=['offre', 'prix'] if language == 'fr' else ['pricing'], rights='test fixture',
                    retrieved='2026-10-26', status=status, content_sha256=hashlib.sha256(body.encode()).hexdigest())
        path = directory / (identifier + '.md')
        path.write_text('---\n' + json.dumps(meta) + '\n---\n' + body, encoding='utf-8')
        return path

    def test_accent_insensitive_and_untrusted_query(self):
        self.assertEqual(biblio.search('ecrire', root=self.root)[0]['id'], 'local')
        self.assertEqual(biblio.search('"\' ; DROP TABLE documents; --', root=self.root), [])
        self.assertEqual(biblio.get_document('local', self.root)['title'], 'Écrire une offre')

    def test_filters_applied_before_limit(self):
        found = biblio.search('offre objections', limit=1, local=True, root=self.root)
        self.assertEqual(len(found), 1)
        self.assertEqual(found[0]['id'], 'local')
        found = biblio.search('pricing', source='other', language='en', root=self.root)
        self.assertEqual(found[0]['id'], 'english')
        self.assertEqual(biblio.search('pricing', language='fr', root=self.root), [])

    def test_passages_deduplicated_by_document(self):
        found = biblio.search('objections', root=self.root)
        ids = [x['id'] for x in found]
        self.assertEqual(len(ids), len(set(ids)))

    def test_context_keeps_source_state_and_budget(self):
        found = biblio.search('offre', root=self.root)
        text = biblio.context(found, 1600)
        self.assertLessEqual(len(text), 1600)
        self.assertIn('https://example.org/', text)
        self.assertIn('État :', text)
        self.assertIn('Droits :', text)
        self.assertEqual(biblio.search('???', root=self.root), [])

    def test_complete_document_retrievable(self):
        doc = biblio.get_document('local', self.root)
        self.assertEqual(doc['body'].count('Cette offre'), 100)
        with self.assertRaises(ValueError):
            biblio.get_document('missing', self.root)

    def test_rebuild_is_repeatable_and_rolls_back_on_error(self):
        before = biblio.statistics(self.root)
        self.assertEqual(biblio.rebuild(self.root), before)
        bad = self.root / 'fiches' / 'bad.md'
        bad.parent.mkdir()
        bad.write_text('document sans métadonnées', encoding='utf-8')
        with self.assertRaises(ValueError):
            biblio.rebuild(self.root)
        self.assertEqual(biblio.get_document('local', self.root)['id'], 'local')

    def test_integrity_detects_altered_content(self):
        path = self.root / 'contenus' / 'local.md'
        self.assertEqual(biblio.check(self.root), [])
        path.write_text(path.read_text(encoding='utf-8') + 'Texte ajouté.', encoding='utf-8')
        self.assertTrue(any('Empreinte invalide' in e for e in biblio.check(self.root)))

    def test_chunking_preserves_all_characters_and_terminates(self):
        for body in ('', 'a', 'abc\n' * 4000, 'z' * 10000):
            pieces = list(biblio.chunks(body))
            self.assertTrue(all(len(p) <= 2200 for p in pieces))
            if body:
                reconstructed = pieces[0]
                for piece in pieces[1:]:
                    reconstructed += piece[240:]
                self.assertEqual(reconstructed, body)

    def test_metadata_parser_does_not_save_embedded_content(self):
        parser = Links()
        parser.feed('<div data-page="{&quot;props&quot;:{&quot;title&quot;:&quot;Guide&quot;}}"></div><a href="/guide">Lire <b>le guide</b></a>')
        self.assertEqual(parser.page_data['props']['title'], 'Guide')
        self.assertEqual(parser.links, [('/guide', 'Lire le guide')])
        self.assertEqual(clean_url('https://EXAMPLE.org/guide/?tracking=1#section'), 'https://example.org/guide')


if __name__ == '__main__':
    unittest.main()
