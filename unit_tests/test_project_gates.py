import json
import subprocess
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import project_gates as gates
import test_performance_comparison as performance_fixture
import test_acceptance as accuracy_fixture


class NativeAdapterTests(unittest.TestCase):
    scope = {'model': 'model-a', 'host': 'host-a'}

    def fixture(self, cls):
        value = cls()
        value.setUp()
        self.addCleanup(value.doCleanups)
        return value

    def test_native_performance_and_tampered_output(self):
        f = self.fixture(performance_fixture.ComparisonTest)
        check = {'kind': 'performance', 'contract': str(f.contract_path), 'records': list(map(str, f.paths))}
        self.assertEqual(gates.run_check(ROOT, check, self.scope)['status'], 'passed')
        check['kind'] = 'performance-run'
        self.assertEqual(gates.run_check(ROOT, check, self.scope)['status'], 'passed')
        with self.assertRaises(ValueError): gates.run_check(ROOT, check, dict(self.scope, model='different-model'))
        (f.root / 'baseline-0/raw-3.json').write_text('{}')
        with self.assertRaises(ValueError): gates.run_check(ROOT, check, self.scope)
        check['kind'] = 'performance'
        self.assertEqual(gates.run_check(ROOT, check, self.scope)['status'], 'incomplete')

    def test_native_accuracy_gate_and_stale_service(self):
        f = self.fixture(accuracy_fixture.GateTest)
        accuracy_fixture.gate.issue_gate(f.record, f.output)
        check = {'kind': 'accuracy', 'manifest': str(f.root / 'service.json'), 'gate': str(f.output)}
        self.assertEqual(gates.run_check(ROOT, check, self.scope)['status'], 'passed')
        f.service['service_instance_id'] = 'another-boot'
        f.save('service', f.service)
        with self.assertRaises(ValueError): gates.run_check(ROOT, check, self.scope)

    def test_formal_cannot_be_downgraded_to_performance_only(self):
        f = self.fixture(performance_fixture.ComparisonTest)
        check = {'kind': 'performance', 'contract': str(f.contract_path), 'records': list(map(str, f.paths))}
        service = str(f.root / 'candidate-0/service.json')
        spec = {'capability_id': 'e2e/performance', 'selection': 'formal', 'scope': self.scope,
                'context_files': [str(f.contract_path), service],
                'before': [{'kind': 'accuracy', 'manifest': service, 'gate': str(f.root / 'gate.json')}], 'after': [check]}
        with self.assertRaisesRegex(ValueError, 'formal comparison contract'): gates.validate_plan(spec)
        spec['selection'] = 'targeted'
        gates.validate_plan(spec)
        spec['context_files'] = [service]
        with self.assertRaisesRegex(ValueError, 'freeze contract'): gates.validate_plan(spec)

    def test_service_preflight_supports_nonformal_eager_identity(self):
        f = self.fixture(accuracy_fixture.GateTest)
        f.service.update(mode='eager', base_url='http://127.0.0.1:8000/v1/completions')
        f.save('service', f.service)
        result = gates.run_check(ROOT, {'kind': 'service', 'manifest': str(f.root / 'service.json')}, self.scope)
        self.assertEqual(result['status'], 'passed')

    def test_journal_cli_wraps_native_runs_end_to_end(self):
        f = self.fixture(performance_fixture.ComparisonTest)
        service = str(f.root / 'baseline-0/service.json')
        spec = dict(schema_version=1, run_id='native-fixture', owner='test',
            capability_id='e2e/performance', selection='targeted', scope=self.scope,
            skill_dir=str(ROOT / 'skills/inference-performance-evaluation'),
            context_files=[service, str(f.contract_path)],
            before=[dict(kind='service', manifest=service)],
            after=[dict(kind='performance', contract=str(f.contract_path), records=list(map(str, f.paths)))])
        spec_path = f.root / 'step.json'
        spec_path.write_text(json.dumps(spec))
        run = f.root / 'journal'
        command = [sys.executable, '-B', str(ROOT / 'scripts/agent_step.py')]
        result = subprocess.run(command + ['begin', '--run-dir', str(run), '--spec', str(spec_path)],
                                cwd=f.root, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(json.loads(result.stdout)['status'], 'incomplete')
        result = subprocess.run(command + ['finish', '--run-dir', str(run)], cwd=f.root, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(json.loads(result.stdout)['status'], 'passed')
        (f.root / 'baseline-0/raw-3.json').write_text('{}')
        result = subprocess.run(command + ['check', '--run-dir', str(run)], cwd=f.root, capture_output=True, text=True)
        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
        self.assertEqual(json.loads(result.stdout)['status'], 'incomplete')
