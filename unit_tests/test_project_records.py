import importlib.util
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('records', ROOT / 'scripts/check-project-records.py')
records = importlib.util.module_from_spec(spec)
spec.loader.exec_module(records)


class RecordsTest(unittest.TestCase):
    def test_duplicate_yaml_is_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'state.yml'
            path.write_text('schema_version: 3\nstatus: passed\nstatus: failed\n')
            with self.assertRaisesRegex(ValueError, 'duplicate'):
                records.load_state(path)

    def test_explicit_document_alias_and_duplicate_ids(self):
        state = {'experiments': [{'experiment_id': 'op-001-name', 'document': 'op-001.md'}]}
        self.assertEqual(records.point_links(state), {'op-001-name': 'op-001.md'})
        state['experiments'] *= 2
        with self.assertRaises(ValueError):
            records.point_links(state)

    def test_missing_document_and_new_process_file_are_errors(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            optimize = root / 'models/model/platform/optimize'
            optimize.mkdir(parents=True)
            (optimize / 'state.yml').write_text('schema_version: 3\nexperiments:\n  - experiment_id: op-001\n')
            (optimize / 'README.md').write_text('[point](op-001.md)')
            (optimize / 'run.sh').write_text('true')
            history = optimize / 'history'
            history.mkdir()
            (history / 'old.sh').write_text('true')
            errors, _ = records.check(root)
            self.assertTrue(any('missing op-001.md' in s for s in errors))
            self.assertTrue(any('run.sh' in s for s in errors))
            self.assertFalse(any('old.sh' in s for s in errors))
            self.assertTrue(any('new history directory' in s for s in errors))
            (optimize / 'op-001.md').write_text('# existing point')
            errors, _ = records.check(root)
            self.assertFalse(any('missing op-001.md' in s for s in errors))


if __name__ == '__main__':
    unittest.main()
