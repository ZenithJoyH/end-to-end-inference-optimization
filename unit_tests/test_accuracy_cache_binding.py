"""Explicit cache evolution must not weaken default source/config binding."""
import copy
import json
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import test_acceptance as fixtures
import acceptance as gate


class TuningCacheBindingTest(unittest.TestCase):
    def setUp(self):
        self.fixture = fixtures.GateTest(methodName='test_issue_check_and_changed_service_rejected')
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        f = self.fixture
        self.service = copy.deepcopy(f.service)
        self.service['launch_config'].update(
            flaggems_db_sha256='b' * 64,
            environment={'FLAGGEMS_DB_URL': 'sqlite:////private/tuning.db'})
        before = f.root / 'runtime-before.json'
        before.write_text(json.dumps({'cache_sha256': 'b' * 64}))
        self.service['runtime_evidence_sha256'] = gate.sha256(before)
        f.save('service', self.service)
        record = gate.read_json(f.record)
        record['artifacts']['service'] = f.refs['service']
        f.record.write_text(json.dumps(record))
        gate.issue_gate(f.record, f.output)
        self.current = copy.deepcopy(self.service)
        self.current['launch_config']['flaggems_db_sha256'] = 'c' * 64
        runtime = f.root / 'runtime-current.json'
        runtime.write_text(json.dumps({'cache_sha256': 'c' * 64}))
        self.current['runtime_evidence_sha256'] = gate.sha256(runtime)
        self.current_path = f.root / 'current-service.json'
        self.current_path.write_text(json.dumps(self.current))
        inspection = f.root / 'cache-inspection.json'
        inspection.write_text(json.dumps({'fixture_only': True, 'tables': ['kernel_config']}))
        self.audit_path = f.root / 'cache-audit.json'
        self.audit = dict(status='passed', kind='flaggems_autotune_cache',
            service_instance_id=self.current['service_instance_id'],
            cache_url='sqlite:////private/tuning.db', before_sha256='b' * 64,
            after_sha256='c' * 64,
            stable_identity_sha256=gate.content_sha256(gate.tuning_cache_identity(self.current)),
            cache_tables_only=True, manual_reset_copy_or_policy_override=False,
            inspection=gate.artifact(inspection))
        self.audit_path.write_text(json.dumps(self.audit))
        self.evidence = dict(schema_version=1, kind='flaggems_tuning_cache_update',
            authorization='User authorizes verified normal tuning-cache writes, not code/config changes',
            source_service=f.refs['service'], current_service=gate.artifact(self.current_path),
            before_runtime=gate.artifact(before), current_runtime=gate.artifact(runtime),
            cache_audit=gate.artifact(self.audit_path))
        self.evidence_path = f.root / 'cache-evidence.json'
        self.evidence_path.write_text(json.dumps(self.evidence))
        self.output = f.root / 'cache-bound-gate.json'

    def bind(self):
        return gate.cache_update_gate(self.fixture.output, self.current_path, self.evidence_path, self.output)

    def test_explicit_update_preserves_score_and_original_bytes(self):
        original = self.fixture.output.read_bytes()
        with self.assertRaises(ValueError):
            gate.check_gate(self.fixture.output, self.current_path)
        result = self.bind()
        self.assertEqual(result['schema_version'], 5)
        self.assertEqual(result['score'], gate.read_json(self.fixture.output)['score'])
        gate.check_gate(self.output, self.current_path)
        self.assertEqual(original, self.fixture.output.read_bytes())
        with self.assertRaises(ValueError):
            gate.cache_update_gate(self.output, self.current_path, self.evidence_path,
                                   self.output.with_name('chain.json'))
        with self.assertRaises(FileExistsError):
            self.bind()

    def test_source_instance_configuration_url_and_device_are_still_strict(self):
        for key, value in [('plugin_sha256', 'd' * 64), ('model_sha256', 'd' * 64),
                           ('service_instance_id', 'boot-2'), ('host', 'other-host'),
                           ('flaggems_vllm_installed', True),
                           ('performance_context', dict(self.current['performance_context'], device_ids=['1']))]:
            changed = copy.deepcopy(self.current)
            changed[key] = value
            self.current_path.write_text(json.dumps(changed))
            with self.subTest(key=key), self.assertRaises(ValueError):
                self.bind()
        for key, value in [('tp', 8), ('environment', {'FLAGGEMS_DB_URL': 'sqlite:////other.db'}),
                           ('flaggems_db_sha256', None)]:
            changed = copy.deepcopy(self.current)
            changed['launch_config'][key] = value
            self.current_path.write_text(json.dumps(changed))
            with self.subTest(key=key), self.assertRaises(ValueError):
                self.bind()

    def test_missing_authorization_or_audit_and_tampered_refs_rejected(self):
        for key in ('authorization', 'source_service', 'current_service', 'before_runtime', 'current_runtime', 'cache_audit'):
            changed = dict(self.evidence)
            changed.pop(key)
            self.evidence_path.write_text(json.dumps(changed))
            with self.subTest(key=key), self.assertRaises((ValueError, KeyError)):
                self.bind()
        self.evidence_path.write_text(json.dumps(self.evidence))
        self.audit_path.write_text('{}')
        with self.assertRaises(ValueError):
            self.bind()

    def test_consistent_hashes_do_not_allow_forged_cache_audit(self):
        for key, value in [('after_sha256', 'd' * 64), ('cache_tables_only', False),
                           ('manual_reset_copy_or_policy_override', True),
                           ('stable_identity_sha256', 'f' * 64), ('cache_tables_only', 1)]:
            self.audit_path.write_text(json.dumps(dict(self.audit, **{key: value})))
            evidence = dict(self.evidence, cache_audit=gate.artifact(self.audit_path))
            self.evidence_path.write_text(json.dumps(evidence))
            with self.subTest(key=key, value=value), self.assertRaises(ValueError):
                self.bind()

    def test_check_reverifies_raw_results_runtime_and_verdict(self):
        self.bind()
        original = self.output.read_text()
        obj = json.loads(original)
        obj['score'] = 1
        self.output.write_text(json.dumps(obj))
        with self.assertRaises(ValueError):
            gate.check_gate(self.output, self.current_path)
        self.output.write_text(original)
        (self.fixture.root / 'runtime-current.json').write_text('{}')
        with self.assertRaises(ValueError):
            gate.check_gate(self.output, self.current_path)


if __name__ == '__main__':
    unittest.main()
