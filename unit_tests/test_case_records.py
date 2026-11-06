import json
import hashlib
from pathlib import Path
import sys
import tempfile
import unittest
import zipfile
import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import case_records as records


class CaseRecordsTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.case = self.root / 'case-tp8'
        self.identity = dict(case_id='case-tp8', model='model', platform='ppu', host='host',
                             baseline_id='anchor-001', topology='TP8:device0-device7')
        records.init_case(self.case, self.identity)

    def test_cases_are_separate_and_init_never_overwrites(self):
        with self.assertRaises(FileExistsError): records.init_case(self.case, self.identity)
        other = self.root / 'case-tp16'
        records.init_case(other, dict(self.identity, case_id='case-tp16', topology='TP16'))
        self.assertNotEqual(records.summary(self.case / 'optimize/state.yml')['identity'],
                            records.summary(other / 'optimize/state.yml')['identity'])

    def test_renderer_preserves_manual_prose_and_requires_managed_boundaries(self):
        state = self.case / 'optimize/state.yml'
        readme = state.with_name('README.md')
        readme.write_text('Human decision before\n' + readme.read_text() + '\nHuman notes after\n')
        records.render(state, readme)
        self.assertTrue(readme.read_text().startswith('Human decision before'))
        self.assertTrue(readme.read_text().endswith('Human notes after\n'))
        readme.write_text('Entirely manual document')
        with self.assertRaises(ValueError): records.render(state, readme)
        self.assertEqual(readme.read_text(), 'Entirely manual document')

    def test_summary_bounds_runtime_details_and_full_view_preserves_them(self):
        state = self.case / 'optimize/state.yml'
        value = records.load(state)
        value['current'].update(
            status='paused-manual', next_action='Wait for explicit human resume.',
            candidate={'revision': 'candidate-1', 'captured_output': 'x' * 10000},
            active_service={'cmdline': ['arg'] * 5000},
            latest_planning='plan-083', blocking_reason='b' * 5000)
        state.write_text(yaml.safe_dump(value))
        original = state.read_bytes()
        view = records.summary(state)
        self.assertLess(len(json.dumps(view)), 3000)
        self.assertEqual(view['current']['status'], 'paused-manual')
        self.assertEqual(view['current']['next_action'], 'Wait for explicit human resume.')
        self.assertEqual(view['current']['latest_planning'], 'plan-083')
        self.assertEqual(view['current']['candidate']['state_pointer'], '/current/candidate')
        self.assertTrue(view['current']['blocking_reason']['truncated'])
        self.assertIn('active_service', view['details']['omitted_current_fields'])
        self.assertEqual(view['details']['state'], str(state.resolve()))
        self.assertEqual(records.summary(state, full=True)['current'], value['current'])
        self.assertEqual(state.read_bytes(), original)

    def test_renderer_does_not_replace_long_human_decisions_with_summary_preview(self):
        state = self.case / 'optimize/state.yml'
        value = records.load(state)
        value['current']['next_action'] = 'Preserve this decision. ' * 100
        state.write_text(yaml.safe_dump(value))
        records.render(state, state.with_name('README.md'))
        self.assertIn(value['current']['next_action'], state.with_name('README.md').read_text())

    def test_archived_detail_is_addressable_and_hash_checked(self):
        state = self.case / 'optimize/state.yml'
        value = records.load(state)
        detail = {'status': 'failed', 'rounds': [{'throughput': 12.5, 'reason': 'slow'}]}
        value['experiments'] = [{'experiment_id': 'op-001', 'document': 'op-001.md',
                                 'decision': 'reverted', 'result': detail}]
        archive = self.root / 'details.yml'
        archive.write_text(yaml.safe_dump(value))
        value['experiments'][0]['result'] = {'$external_record': {
            'path': str(archive), 'sha256': hashlib.sha256(archive.read_bytes()).hexdigest(),
            'pointer': '/experiments/0/result'}}
        state.write_text(yaml.safe_dump(value))
        self.assertEqual(records.read_detail(state, '/experiments/0/result'), detail)
        self.assertEqual(records.read_detail(state, '/experiments/0/result/rounds/0/throughput'), 12.5)
        self.assertEqual(records.read_detail(state, '/experiments/0/decision'), 'reverted')
        with self.assertRaises(ValueError): records.read_detail(state, '/experiments/0/result/missing')
        archive.write_text('tampered')
        with self.assertRaisesRegex(ValueError, 'checksum mismatch'):
            records.read_detail(state, '/experiments/0/result')

    def test_detail_pointer_escaping_and_invalid_paths(self):
        state = self.case / 'optimize/state.yml'
        value = records.load(state)
        value['current']['a/b~c'] = [3]
        state.write_text(yaml.safe_dump(value))
        self.assertEqual(records.read_detail(state, '/current/a~1b~0c/0'), 3)
        for pointer in ('current', '/current/~2', '/current/a~1b~0c/1', '/current/a~1b~0c/-1'):
            with self.assertRaises(ValueError): records.read_detail(state, pointer)

    def test_archived_navigation_summary_cannot_override_frozen_facts(self):
        state = self.case / 'optimize/state.yml'
        value = records.load(state)
        result = {'status': 'failed', 'count': 1, 'reason': 'slow'}
        value['experiments'] = [{'experiment_id': 'op-001', 'document': 'op-001.md', 'result': result}]
        archive = self.root / 'details.yml'
        archive.write_text(yaml.safe_dump(value))
        ref = {'path': str(archive), 'sha256': hashlib.sha256(archive.read_bytes()).hexdigest(),
               'pointer': '/experiments/0/result'}
        value['experiments'][0]['result'] = {'$external_record': ref, 'status': 'failed'}
        state.write_text(yaml.safe_dump(value))
        self.assertEqual(records.read_detail(state, '/experiments/0/result/status'), 'failed')
        for extra in ({'status': 'passed'}, {'count': True}, {'invented_status': 'passed'}):
            value['experiments'][0]['result'] = {'$external_record': ref, **extra}
            state.write_text(yaml.safe_dump(value))
            before = state.read_bytes()
            with self.assertRaisesRegex(ValueError, 'immutable archived summary differs.*create a new receipt'):
                records.read_detail(state, '/experiments/0/result')
            self.assertEqual(state.read_bytes(), before)

    def test_export_restore_checks_hashes_and_never_overwrites(self):
        (self.case / 'weights.bin').write_bytes(b'not a record')
        archive = self.root / 'backup.zip'
        records.export_records(self.case, archive)
        destination = self.root / 'restored'
        records.restore_records(archive, destination)
        self.assertFalse((destination / 'weights.bin').exists())
        for p in self.case.rglob('*.yml'):
            self.assertEqual(p.read_bytes(), (destination / p.relative_to(self.case)).read_bytes())
        with self.assertRaises(ValueError): records.restore_records(archive, destination)
        bad = self.root / 'bad.zip'
        with zipfile.ZipFile(bad, 'w') as z:
            z.writestr('manifest.json', json.dumps({'../escape.md': 'a' * 64}))
            z.writestr('records/../escape.md', 'unsafe')
        with self.assertRaises(ValueError): records.restore_records(bad, self.root / 'unsafe')
        self.assertFalse((self.root / 'unsafe').exists())

    def test_legacy_identity_ambiguity_is_visible_and_not_rewritten(self):
        state = self.root / 'legacy.yml'
        original = 'schema_version: 3\ncase_id: old\nactive_case_id: new\nstatus: paused\n'
        state.write_text(original)
        self.assertTrue(any('differs' in w for w in records.summary(state)['warnings']))
        with self.assertRaises(ValueError): records.render(state, self.root / 'legacy.md')
        self.assertEqual(state.read_text(), original)

    def test_invalid_metrics_and_duplicate_experiments_are_rejected(self):
        state = self.case / 'optimize/state.yml'
        value = records.load(state)
        value['experiments'] = [dict(experiment_id='op-001')] * 2
        state.write_text(yaml.safe_dump(value))
        with self.assertRaises(ValueError): records.load(state)
        value['experiments'] = []
        value['metrics'] = [dict(scenario_id='s', role='candidate', metric='tpot', value=float('nan'),
                                 unit='ms', scope='probe')]
        state.write_text(yaml.safe_dump(value))
        with self.assertRaises(ValueError): records.load(state)

    def test_corrupt_and_aliased_archives_are_rejected_before_writes(self):
        for i, (name, digest) in enumerate([
                ('record.md', '0' * 64),
                ('a/./record.md', hashlib.sha256(b'record').hexdigest())]):
            archive = self.root / f'bad-{i}.zip'
            with zipfile.ZipFile(archive, 'w') as z:
                z.writestr('manifest.json', json.dumps({name: digest}))
                z.writestr('records/' + name, b'record')
            destination = self.root / f'restore-{i}'
            with self.assertRaises(ValueError): records.restore_records(archive, destination)
            self.assertFalse(destination.exists())


if __name__ == '__main__': unittest.main()
