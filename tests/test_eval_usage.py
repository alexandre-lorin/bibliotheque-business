import hashlib
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

SPEC = importlib.util.spec_from_file_location(
    'eval_usage_tools', Path(__file__).resolve().parents[1] / 'evaluation-usage' / 'outils.py')
TOOLS = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(TOOLS)


class BlindExportTests(unittest.TestCase):
    def test_exports_preserve_bodies_and_key_and_refuse_overwrite(self):
        with tempfile.TemporaryDirectory() as folder:
            run = Path(folder)
            for condition, body in [('temoin', b'Corps temoin\n'), ('rag', b'Corps documentaire\n')]:
                path = run / 'C01' / condition
                path.mkdir(parents=True)
                (path / 'reponse.md').write_bytes(body)
            TOOLS.mix(run)
            key = json.loads((run / 'prive' / 'cle.json').read_text())
            self.assertEqual({key['C01'][label]['condition'] for label in ('A', 'B')}, {'temoin', 'rag'})
            for label in ('A', 'B'):
                raw = (run / 'aveugle' / ('C01-' + label + '.md')).read_bytes()
                condition = key['C01'][label]['condition']
                self.assertEqual(raw, (run / 'C01' / condition / 'reponse.md').read_bytes())
                self.assertEqual(hashlib.sha256(raw).hexdigest(), key['C01'][label]['sha256'])
            with self.assertRaises(ValueError):
                TOOLS.mix(run)

    def test_incomplete_pair_does_not_create_blind_outputs(self):
        with tempfile.TemporaryDirectory() as folder:
            run = Path(folder)
            path = run / 'C01' / 'temoin'
            path.mkdir(parents=True)
            (path / 'reponse.md').write_text('Réponse')
            with self.assertRaises(FileNotFoundError):
                TOOLS.mix(run)
            self.assertFalse((run / 'aveugle').exists())
