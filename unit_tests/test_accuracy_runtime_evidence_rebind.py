"""Restart evidence may move, while its bytes and the service stay verified."""
import json
import unittest

import test_acceptance as fixtures

gate = fixtures.gate


class RuntimeEvidenceRebindTest(unittest.TestCase):
    save = fixtures.GateTest.save
    make_rebind = fixtures.GateTest.make_rebind

    def setUp(self):
        fixtures.GateTest.setUp(self)

    def observed_restart(self):
        old_runtime = self.root / 'old-runtime.json'
        old_runtime.write_text(json.dumps({'service_instance_id': self.service['service_instance_id']}))
        old_log = self.root / 'old-log.snapshot'
        old_log.write_text('old native service evidence\n')
        self.service.update(api_pid=111, runtime_evidence_sha256=gate.sha256(old_runtime),
                            runtime_evidence_files={str(p): gate.sha256(p) for p in (old_runtime, old_log)})
        self.save('service', self.service)
        record = gate.read_json(self.record)
        record['artifacts']['service'] = self.refs['service']
        self.record.write_text(json.dumps(record))
        current, evidence, output = self.make_rebind()
        current_log = self.root / 'new-log.snapshot'
        current_log.write_text('new native service evidence\n')
        runtime = self.root / 'restart-runtime.json'
        service = gate.read_json(current)
        service.update(api_pid=222, runtime_evidence_files={str(p): gate.sha256(p) for p in (runtime, current_log)})
        current.write_text(json.dumps(service))
        self.rebind_current_refs(current, evidence)
        return current, evidence, output

    def rebind_current_refs(self, current, evidence):
        regression = self.root / 'restart-regression.json'
        record = gate.read_json(regression)
        record['service_sha256'] = gate.sha256(current)
        regression.write_text(json.dumps(record))
        binding = gate.read_json(evidence)
        binding.update(current_service=gate.artifact(current), minimal_regression=gate.artifact(regression))
        evidence.write_text(json.dumps(binding))

    def test_rebind_accepts_distinct_pids_and_immutable_evidence_locations(self):
        current, evidence, output = self.observed_restart()
        gate.rebind_gate(self.output, current, evidence, output)
        rebound = gate.check_gate(output, current)
        self.assertTrue(rebound['evaluation_reused'])
        self.assertEqual(rebound['score'], gate.read_json(self.output)['score'])
        self.assertEqual(rebound['threshold'], gate.read_json(self.output)['threshold'])

    def test_rebind_rechecks_old_and_current_runtime_evidence_bytes(self):
        current, evidence, output = self.observed_restart()
        for name in ('old-log.snapshot', 'new-log.snapshot'):
            path = self.root / name
            original = path.read_bytes()
            path.write_text('tampered\n')
            with self.subTest(name=name), self.assertRaisesRegex(ValueError, 'artifact content changed'):
                gate.rebind_gate(self.output, current, evidence, output)
            path.write_bytes(original)

    def test_rebound_gate_rechecks_evidence_on_later_consumption(self):
        current, evidence, output = self.observed_restart()
        gate.rebind_gate(self.output, current, evidence, output)
        (self.root / 'new-log.snapshot').write_text('changed after issue\n')
        with self.assertRaisesRegex(ValueError, 'artifact content changed'):
            gate.check_gate(output, current)

    def test_volatile_fields_are_validated_before_being_excluded(self):
        current, _, _ = self.observed_restart()
        service = gate.read_json(current)
        bad_values = [
            {'api_pid': True}, {'api_pid': 0}, {'api_pid': '222'},
            {'runtime_evidence_files': {}}, {'runtime_evidence_files': []},
            {'runtime_evidence_files': {'path': 'invalid'}},
            {'runtime_evidence_files': {'': 'a' * 64}},
            {'runtime_evidence_sha256': 'b' * 64},
        ]
        for changes in bad_values:
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                gate.stable_service_identity(dict(service, **changes))

    def test_source_config_container_and_device_changes_still_rejected(self):
        current, evidence, output = self.observed_restart()
        original = gate.read_json(current)
        changes = [
            {'plugin_sha256': 'b' * 64}, {'optimization_container_name': 'another-clone'},
            {'launch_config': {'tp': 8}}, {'base_url': 'http://localhost:8000/v1/chat/completions'},
            {'performance_context': dict(original['performance_context'], device_ids=['1'])},
        ]
        for change in changes:
            current.write_text(json.dumps(dict(original, **change)))
            self.rebind_current_refs(current, evidence)
            with self.subTest(change=change), self.assertRaisesRegex(ValueError, 'source/configuration/environment'):
                gate.rebind_gate(self.output, current, evidence, output)

    def test_fresh_runtime_still_requires_two_replays_with_consistent_hashes(self):
        current, evidence, output = self.observed_restart()
        runtime = self.root / 'restart-runtime.json'
        payload = gate.read_json(runtime)
        payload['graph_replays'] = 1
        runtime.write_text(json.dumps(payload))
        service = gate.read_json(current)
        service['runtime_evidence_sha256'] = gate.sha256(runtime)
        service['runtime_evidence_files'][str(runtime)] = gate.sha256(runtime)
        current.write_text(json.dumps(service))
        self.rebind_current_refs(current, evidence)
        binding = gate.read_json(evidence)
        binding['runtime_evidence'] = gate.artifact(runtime)
        evidence.write_text(json.dumps(binding))
        with self.assertRaisesRegex(ValueError, 'two replays'):
            gate.rebind_gate(self.output, current, evidence, output)


if __name__ == '__main__':
    unittest.main()
