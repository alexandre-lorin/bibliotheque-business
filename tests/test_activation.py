import tempfile
import unittest
from pathlib import Path

import activer


class ActivationTests(unittest.TestCase):
    def test_selective_skill_install_is_idempotent_and_preserves_differences(self):
        with tempfile.TemporaryDirectory() as folder:
            destination = Path(folder) / 'skills'
            first = activer.install_skills(destination)
            self.assertEqual(len(first), 2)
            second = activer.install_skills(destination)
            self.assertTrue(all('déjà' in item for item in second))
            target = destination / 'toubi-humanizer' / 'SKILL.md'
            target.write_text('Version personnelle à conserver')
            with self.assertRaises(ValueError):
                activer.install_skills(destination)
            self.assertEqual(target.read_text(), 'Version personnelle à conserver')


if __name__ == '__main__':
    unittest.main()
