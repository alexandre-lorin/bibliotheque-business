import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import books
import sync


class SyncTests(unittest.TestCase):
    def test_explicit_sources_and_inbox_are_incremental(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / 'data').mkdir()
            (root / 'sources-locales.yaml').write_text(json.dumps({'sources': [{'path': 'source.md', 'title': 'Contexte'}]}))
            (root / 'source.md').write_text('Documentation locale explicite.\n' * 10)
            inbox = root / 'entrees'
            inbox.mkdir()
            (inbox / 'livre.txt').write_text('Exemple autorisé pour vérifier la surveillance.\n' * 10)
            (inbox / 'livre.json').write_text(json.dumps({'file': 'livre.txt', 'title': 'Livre', 'rights': 'authorized', 'evidence': 'Texte de test'}))
            with patch.object(sync, 'ROOT', root), patch('books.extract', wraps=books.extract) as extraction:
                first = sync.sync_sources()
                second = sync.sync_sources()
                self.assertTrue(first)
                self.assertFalse(second)
                self.assertEqual(extraction.call_count, 1)
                self.assertEqual(len(list((root / 'contenus' / 'imports').glob('*.md'))), 1)
                (root / 'source.md').write_text('Contexte local modifié.\n' * 10)
                self.assertTrue(sync.sync_sources())
            self.assertTrue((inbox / 'livre.txt').exists())

    def test_inbox_cannot_import_a_parent_file(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / 'sources-locales.yaml').write_text('{"sources":[]}')
            (root / 'data').mkdir()
            inbox = root / 'entrees'
            inbox.mkdir()
            (root / 'outside.txt').write_text('Texte en dehors de la zone entrante.\n' * 10)
            (inbox / 'bad.json').write_text(json.dumps({'file': '../outside.txt', 'title': 'Hors zone', 'rights': 'authorized', 'evidence': 'Test'}))
            with patch.object(sync, 'ROOT', root):
                report = sync.sync_sources()
            self.assertTrue(report[0].get('error'))
            self.assertFalse((root / 'contenus').exists())


if __name__ == '__main__':
    unittest.main()
