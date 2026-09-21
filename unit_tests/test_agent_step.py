"""Journal invariants; native validator integration is tested separately."""
import json
from pathlib import Path
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import agent_step as step


class JournalTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        self.skill = self.root / 'skill'
        self.skill.mkdir()
        (self.skill / 'SKILL.md').write_text('fixture skill')
        (self.skill / 'interface.json').write_text(json.dumps(dict(schema_version=1,
            capability_id='fixture/test', interface_version='1.0.0', selector='mode',
            operations=['single'], result_contract='fixture/v1', resources=['SKILL.md'])))
        self.context = self.root / 'service.json'
        self.context.write_text('{"service": "current"}')
        self.evidence = self.root / 'progress.txt'
        self.evidence.write_text('completed=1')
        self.spec = dict(schema_version=1, run_id='one', owner='test', capability_id='fixture/test',
            selection='single', scope={'model': 'model-a'}, skill_dir=str(self.skill),
            context_files=[str(self.context)], before=[{'kind': 'fixture'}], after=[{'kind': 'fixture'}],
            budget_seconds=120, stall_seconds=60, resources=['host-a/device-0'],
            lease_registry=str(self.root / 'leases'))
        for name in ('validate_check', 'validate_plan'):
            value = patch.object(step, name)
            value.start(); self.addCleanup(value.stop)
        value = patch.object(step, 'run_check', return_value={'status': 'passed'})
        self.native = value.start(); self.addCleanup(value.stop)
        value = patch.object(step, 'source_files', return_value=[])
        value.start(); self.addCleanup(value.stop)
        value = patch.object(step, 'output_files', return_value=[self.evidence])
        value.start(); self.addCleanup(value.stop)
        self.run = self.root / 'run'

    def begin(self, path=None):
        spec = self.root / 'spec.json'
        spec.write_text(json.dumps(self.spec))
        return step.begin(spec, path or self.run)

    def test_missing_or_wrong_mode_cannot_create_run(self):
        for choice in ('', 'guess'):
            self.spec['selection'] = choice
            with self.assertRaises(ValueError): self.begin()
            self.assertFalse(self.run.exists())

    def test_failed_preflight_releases_only_own_claim(self):
        self.native.return_value = {'status': 'incomplete'}
        with self.assertRaises(ValueError): self.begin()
        self.assertEqual(step.read(self.run / 'run.json')['state'], 'preflight_failed')
        self.assertEqual(step.read(self.root / 'leases/claims.json'), {})

    def test_native_failure_and_later_tamper_never_pass(self):
        self.begin()
        self.native.return_value = {'status': 'incomplete'}
        with self.assertRaises(ValueError): step.update(self.run, 'finish')
        self.assertEqual(step.read(self.run / 'run.json')['state'], 'ready')
        self.native.return_value = {'status': 'passed'}
        self.assertEqual(step.update(self.run, 'finish')['status'], 'passed')
        self.native.side_effect = ValueError('original output was changed')
        self.assertEqual(step.update(self.run, 'check')['status'], 'incomplete')
        with self.assertRaises(ValueError): step.update(self.run, 'observe', evidence=str(self.evidence), completed=1)

    def test_completed_receipt_replacement_is_detected(self):
        self.begin()
        self.assertEqual(step.update(self.run, 'finish')['status'], 'passed')
        self.evidence.write_text('another formally valid receipt')
        self.assertEqual(step.update(self.run, 'check')['status'], 'incomplete')

    def test_frozen_context_and_full_bundle_are_rechecked(self):
        self.begin()
        self.context.write_text('new service')
        self.assertEqual(step.update(self.run, 'check')['status'], 'incomplete')
        with self.assertRaises(ValueError): step.update(self.run, 'finish')
        self.context.write_text('{"service": "current"}')
        (self.skill / 'new-resource.py').write_text('changed implementation')
        self.assertEqual(step.update(self.run, 'check')['status'], 'incomplete')

    def test_elapsed_time_is_not_a_stall_if_units_advance(self):
        self.begin()
        step.update(self.run, 'observe', evidence=str(self.evidence), completed=1)
        record = step.read(self.run / 'run.json')
        record['started_at'] = 0
        record['last_progress_at'] = 80
        record['spec']['budget_seconds'] = 0
        result = step.decision(record, now=100)
        self.assertEqual(result['review_reasons'], [])
        self.assertEqual(result['status'], 'incomplete')
        self.assertIn('progress_review_due', step.decision(record, now=150)['review_reasons'][0])
        record['spec']['budget_seconds'] = 90
        self.assertIn('budget_exhausted', step.decision(record, now=100)['review_reasons'][0])
        with self.assertRaises(ValueError): step.update(self.run, 'observe', evidence=str(self.evidence), completed=0)

    def test_repeated_error_requires_review(self):
        self.begin()
        for _ in range(2):
            result = step.update(self.run, 'observe', evidence=str(self.evidence), completed=0, error='oom')
        self.assertTrue(any('repeated_error' in x for x in result['review_reasons']))

    def test_claim_survives_failure_until_explicit_inspected_release(self):
        self.begin()
        self.spec['run_id'] = 'two'
        with self.assertRaises(ValueError): self.begin(self.root / 'second')
        claims = step.read(self.root / 'leases/claims.json')
        self.assertEqual(claims['host-a/device-0']['run_id'], 'one')
        step.update(self.run, 'fail', note='process stopped')
        self.assertTrue(step.read(self.root / 'leases/claims.json'))
        with self.assertRaises(ValueError): step.update(self.run, 'release')
        step.update(self.run, 'release', evidence=str(self.evidence), note='checked exact process and device')
        self.assertEqual(step.read(self.root / 'leases/claims.json'), {})
        self.begin(self.root / 'third')

    def test_interrupted_preflight_can_be_closed_but_not_replayed(self):
        self.begin()
        record = step.read(self.run / 'run.json')
        record['state'] = 'preflight'
        step.write(self.run / 'run.json', record)
        self.assertIn('preflight_interrupted', step.update(self.run, 'check')['review_reasons'][0])
        step.update(self.run, 'fail', note='confirmed initializer exited')
        step.update(self.run, 'release', evidence=str(self.evidence), note='confirmed no workload started')
        self.assertEqual(step.read(self.root / 'leases/claims.json'), {})

    def test_unique_directory_prevents_replay(self):
        self.begin()
        with self.assertRaises(FileExistsError): self.begin()


if __name__ == '__main__': unittest.main()
