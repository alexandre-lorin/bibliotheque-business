import hashlib
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

from pypdf import PdfWriter

import books


class BookTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)

    def tearDown(self):
        self.temp.cleanup()

    def test_text_import_keeps_original_and_deduplicates(self):
        path = self.root / 'exemple.txt'
        raw = ('Un exemple de document autorisé pour vérifier son import.\n' * 10).encode()
        path.write_bytes(raw)
        args = (path, 'Exemple', 'Toubi', 'authorized', 'Exemple rédigé pour le test')
        first = books.import_file(*args, root=self.root)
        second = books.import_file(*args, root=self.root)
        self.assertFalse(first['duplicate'])
        self.assertTrue(second['duplicate'])
        originals = list((self.root / 'archives' / 'imports').glob('*'))
        self.assertEqual(len(originals), 1)
        self.assertEqual(hashlib.sha256(originals[0].read_bytes()).digest(), hashlib.sha256(raw).digest())

    def test_epub_spine_order_is_used_without_extracting_archive_paths(self):
        path = self.root / 'exemple.epub'
        with zipfile.ZipFile(path, 'w') as z:
            z.writestr('META-INF/container.xml', '<container><rootfiles><rootfile full-path="OPS/book.opf"/></rootfiles></container>')
            z.writestr('OPS/book.opf', '<package xmlns="http://www.idpf.org/2007/opf"><manifest><item id="a" href="a.xhtml"/><item id="b" href="b.xhtml"/></manifest><spine><itemref idref="b"/><itemref idref="a"/></spine></package>')
            z.writestr('OPS/a.xhtml', '<html><p>Premier fichier.</p><script>ne pas importer</script></html>')
            z.writestr('OPS/b.xhtml', '<html><p>Premier chapitre.</p></html>')
        text, details = books.extract(path)
        self.assertLess(text.index('Premier chapitre'), text.index('Premier fichier'))
        self.assertNotIn('ne pas importer', text)
        self.assertEqual(details['sections'], 2)

    def test_html_carriage_returns_keep_valid_hash_and_reimport_identity(self):
        import biblio
        path = self.root / 'source.html'
        path.write_bytes(('<p>Texte fourni avec retour chariot.\rSuite du texte.</p>' * 12).encode())
        args = (path, 'Exemple', 'Toubi', 'authorized', 'Texte de test')
        first = books.import_file(*args, root=self.root)
        second = books.import_file(*args, root=self.root)
        self.assertEqual(first['id'], second['id'])
        self.assertTrue(second['duplicate'])
        self.assertEqual(biblio.check(self.root), [])

    def test_epub_encrypted_and_pdf_without_text_are_rejected(self):
        epub = self.root / 'drm.epub'
        with zipfile.ZipFile(epub, 'w') as z:
            z.writestr('META-INF/encryption.xml', '<encryption/>')
        with self.assertRaises(ValueError):
            books.extract(epub)
        writer = PdfWriter()
        writer.add_blank_page(width=100, height=100)
        pdf = self.root / 'scan.pdf'
        with pdf.open('wb') as f:
            writer.write(f)
        with self.assertRaisesRegex(ValueError, 'OCR'):
            books.extract(pdf)

    def test_epub_font_encryption_ignored_but_text_encryption_rejected(self):
        for target in ('font.otf', 'chapter.xhtml'):
            epub = self.root / ('font.epub' if target == 'font.otf' else 'text.epub')
            with zipfile.ZipFile(epub, 'w') as z:
                z.writestr('META-INF/container.xml', '<container><rootfile full-path="book.opf"/></container>')
                z.writestr('META-INF/encryption.xml', '<encryption><CipherReference URI="' + target + '"/></encryption>')
                z.writestr('book.opf', '<package xmlns="http://www.idpf.org/2007/opf"><manifest>'
                           '<item id="font" href="font.otf" media-type="font/otf"/>'
                           '<item id="text" href="chapter.xhtml" media-type="application/xhtml+xml"/>'
                           '</manifest><spine><itemref idref="text"/></spine></package>')
                z.writestr('chapter.xhtml', '<p>Texte lisible du chapitre.</p>')
                z.writestr('font.otf', b'not-a-readable-font')
            if target == 'font.otf':
                text, _ = books.extract(epub)
                self.assertIn('Texte lisible', text)
            else:
                with self.assertRaises(ValueError):
                    books.extract(epub)

    def test_rights_and_anna_access_are_explicit(self):
        path = self.root / 'sample.txt'
        path.write_text('texte ' * 100)
        with self.assertRaises(ValueError):
            books.import_file(path, 'Titre', 'Auteur', 'unknown', '', root=self.root)
        with self.assertRaises(ValueError):
            books.anna_url('marketing', 'https://example.org')
        with self.assertRaises(ValueError):
            books.anna_download('invalid', 'https://annas-archive.li', 'TEST_ABSENT_KEY')
        self.assertIn('q=marketing', books.anna_url('marketing'))

    def test_signed_download_parameters_are_not_persisted(self):
        raw = ('Document de test autorisé.\n' * 20).encode()
        with patch('books.get_bytes', return_value=raw):
            result = books.download('https://example.org/book.txt?token=test-only',
                                    'Exemple', 'Auteur', 'authorized', 'Test local', root=self.root)
        document = (self.root / result['path']).read_text()
        self.assertNotIn('token=', document)
        self.assertNotIn('test-only', document)
        self.assertIn('https://example.org/book.txt', document)


if __name__ == '__main__':
    unittest.main()
