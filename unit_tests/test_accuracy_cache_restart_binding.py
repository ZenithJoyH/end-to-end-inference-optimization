"""Cache + restart is explicit, nonchained, and never a performance proof."""
import copy
import json
import unittest

from test_accuracy_cache_binding import TuningCacheBindingTest, gate


class CacheRestartBindingTest(unittest.TestCase):
    def setUp(self):
        TuningCacheBindingTest.setUp(self)
        self.current['service_instance_id'] = 'boot-2'
        self.runtime_path = self.fixture.root/'runtime-current.json'
        observations=self.fixture.root/'observations.json'
        observations.write_text(json.dumps({'artifacts':[gate.artifact(self.fixture.root/'cache-inspection.json')]}))
        self.runtime = dict(service_instance_id='boot-2', graph_capture_completed=True, graph_replays=2,
            stable_identity_sha256=gate.content_sha256(gate.cache_restart_identity(self.current)),
            observations=gate.artifact(observations))
        self.runtime_path.write_text(json.dumps(self.runtime))
        self.current['runtime_evidence_sha256'] = gate.sha256(self.runtime_path)
        self.current_path.write_text(json.dumps(self.current))
        self.regression_path = self.fixture.root/'minimal.json'
        self.evidence.update(kind='flaggems_cache_restart')
        self.audit.update(kind='flaggems_autotune_cache_restart',
            source_service_instance_id=self.service['service_instance_id'],
            service_instance_id='boot-2', historical_row_delta_available=False,
            history_gap='Original DB bytes unavailable; only current schema/writer inspected.',
            stable_identity_sha256=gate.content_sha256(gate.cache_restart_identity(self.current)))
        self.sync()

    def sync(self):
        self.current_path.write_text(json.dumps(self.current))
        self.audit_path.write_text(json.dumps(self.audit))
        self.regression_path.write_text(json.dumps(dict(status='passed',
            service_sha256=gate.sha256(self.current_path), evidence=gate.artifact(self.runtime_path))))
        self.evidence.update(current_service=gate.artifact(self.current_path),
            current_runtime=gate.artifact(self.runtime_path), cache_audit=gate.artifact(self.audit_path),
            minimal_regression=gate.artifact(self.regression_path))
        self.evidence_path.write_text(json.dumps(self.evidence))

    def bind(self):
        return gate.cache_rebind_gate(self.fixture.output, self.current_path, self.evidence_path, self.output)

    def test_explicit_combined_receipt_preserves_original_score_and_threshold(self):
        original = self.fixture.output.read_bytes()
        result = self.bind()
        self.assertEqual(result['schema_version'], 6)
        self.assertEqual(result['score'], gate.read_json(self.fixture.output)['score'])
        self.assertEqual(result['threshold'], gate.read_json(self.fixture.output)['threshold'])
        gate.check_gate(self.output, self.current_path)
        self.assertEqual(original, self.fixture.output.read_bytes())
        with self.assertRaises(FileExistsError):
            self.bind()
        with self.assertRaises(ValueError):
            gate.cache_rebind_gate(self.output, self.current_path, self.evidence_path,
                                   self.output.with_name('chain.json'))

    def test_old_modes_remain_strict(self):
        for fn in (gate.cache_update_gate, gate.rebind_gate):
            with self.subTest(fn=fn.__name__), self.assertRaises(ValueError):
                fn(self.fixture.output, self.current_path, self.evidence_path, self.output)

    def test_changes_to_source_url_policy_device_and_args_still_rejected(self):
        original = copy.deepcopy(self.current)
        variants = [dict(plugin_sha256='d'*64),dict(flaggems_sha256='d'*64),
            dict(flaggems_vllm_installed=True,flaggems_vllm_sha256='d'*64),
            dict(host='other'),dict(optimization_container_name='other'),
            dict(performance_context=dict(original['performance_context'],device_ids=['7'])),
            dict(launch_config=dict(original['launch_config'],tp=8)),
            dict(launch_config=dict(original['launch_config'],environment={'FLAGGEMS_DB_URL':'sqlite:////other'}))]
        for variant in variants:
            self.current = dict(original,**variant)
            self.sync()
            with self.subTest(variant=variant), self.assertRaisesRegex(ValueError,'source/configuration/environment'):
                self.bind()

    def test_same_instance_not_mislabeled_as_restart(self):
        self.current['service_instance_id']=self.service['service_instance_id']
        self.sync()
        with self.assertRaisesRegex(ValueError,'fresh instance'):
            self.bind()

    def test_missing_or_false_audit_rejected(self):
        original = copy.deepcopy(self.audit)
        for changes in [dict(cache_tables_only=False),dict(manual_reset_copy_or_policy_override=True),
                        dict(after_sha256='d'*64),dict(history_gap=''),dict(historical_row_delta_available=None),
                        dict(historical_row_delta_available=True),dict(source_service_instance_id='wrong')]:
            self.audit = dict(original,**changes)
            self.sync()
            with self.subTest(changes=changes),self.assertRaises((ValueError,KeyError)):
                self.bind()

    def test_authorization_required(self):
        self.evidence.pop('authorization')
        self.evidence_path.write_text(json.dumps(self.evidence))
        with self.assertRaises(ValueError):
            self.bind()

    def test_capture_and_two_replays_current_instance_required(self):
        original=copy.deepcopy(self.runtime)
        for changes in [dict(graph_capture_completed=False),dict(graph_replays=1),dict(graph_replays=True),
                        dict(stable_identity_sha256='f'*64),dict(service_instance_id='wrong')]:
            self.runtime_path.write_text(json.dumps(dict(original,**changes)))
            self.current['runtime_evidence_sha256']=gate.sha256(self.runtime_path)
            self.sync()
            with self.subTest(changes=changes),self.assertRaisesRegex(ValueError,'two replays'):
                self.bind()

    def test_minimal_and_all_evidence_rechecked(self):
        self.bind()
        for path in [self.regression_path,self.fixture.root/'cache-inspection.json',self.runtime_path]:
            original=path.read_bytes()
            path.write_text('{}')
            with self.subTest(path=path),self.assertRaises(ValueError):
                gate.check_gate(self.output,self.current_path)
            path.write_bytes(original)
        obj=gate.read_json(self.output)
        obj['score']=1
        self.output.write_text(json.dumps(obj))
        with self.assertRaises(ValueError):
            gate.check_gate(self.output,self.current_path)


if __name__ == '__main__':
    unittest.main()
