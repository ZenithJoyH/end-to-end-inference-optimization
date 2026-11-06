"""Accuracy cache policy and the narrow accuracy-to-performance transition."""
import copy
import json
import unittest

import test_acceptance as fixtures
import test_accuracy_failures as failures
import acceptance as gate
import formal_accuracy


class PrefixCacheTest(unittest.TestCase):
    def setUp(self):
        self.fixture = fixtures.GateTest()
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)

    def test_new_gate_requires_observed_enabled_cache(self):
        original = copy.deepcopy(self.fixture.service)
        for change in (
            {"enable_prefix_caching": False},
            {"enable_prefix_caching": 1},
            {"launch_args": []},
            {"launch_args": ["--enable-prefix-caching", "--no-enable-prefix-caching"]},
            {"launch_args": ["--enable-prefix-caching", "--enable-prefix-caching=False"]},
        ):
            service = copy.deepcopy(original)
            service["launch_config"].update(change)
            with self.subTest(change=change), self.assertRaisesRegex(ValueError, "enabled prefix cache"):
                gate.validate_accuracy_prefix_cache(service)
        service = copy.deepcopy(original)
        service["performance_context"]["prefix_cache_state"] = "disabled"
        with self.assertRaises(ValueError):
            gate.validate_accuracy_prefix_cache(service)
        self.fixture.save("service", service)
        record = gate.read_json(self.fixture.record)
        record["artifacts"]["service"] = self.fixture.refs["service"]
        self.fixture.record.write_text(json.dumps(record))
        with self.assertRaises(ValueError):
            gate.issue_gate(self.fixture.record, self.fixture.output)

    def test_preflight_rejects_disabled_cache_before_service_requests(self):
        fixture = failures.AccuracyFailureTest()
        fixture.setUp()
        self.addCleanup(fixture.doCleanups)
        service = copy.deepcopy(fixture.fixture.service)
        service["launch_config"]["enable_prefix_caching"] = False
        fixture.fixture.save("service", service)
        fixture.args.preflight_only = True
        with fixture.external_work(lambda *args: True) as (_, probe, evaluate):
            with self.assertRaisesRegex(ValueError, "enabled prefix cache"):
                formal_accuracy.run(fixture.args)
            probe.assert_not_called()
            evaluate.assert_not_called()

    def test_transition_reuses_score_and_rechecks_evidence(self):
        f = self.fixture
        current, evidence, output = f.make_performance_binding()
        original = f.output.read_bytes()
        with self.assertRaises(ValueError):
            gate.rebind_gate(f.output, current, evidence, output)
        gate.performance_bind_gate(f.output, current, evidence, output)
        result = gate.check_gate(output, current)
        self.assertEqual(result["schema_version"], 7)
        self.assertEqual(result["score"], gate.read_json(f.output)["score"])
        self.assertEqual(f.output.read_bytes(), original)
        with self.assertRaises(ValueError):
            gate.performance_bind_gate(output, current, evidence, output.with_name("chained.json"))
        (f.root / "prefix-cache-comparison.json").write_text("{}")
        with self.assertRaises(ValueError):
            gate.check_gate(output, current)

    def test_transition_rejects_unrelated_changes(self):
        f = self.fixture
        current, evidence, output = f.make_performance_binding()
        original = gate.read_json(current)
        changes = [
            {"plugin_sha256": "b" * 64},
            {"launch_config": dict(original["launch_config"], tp=8)},
            {"base_url": "http://127.0.0.1:9000/v1/chat/completions"},
            {"performance_context": dict(original["performance_context"], device_ids=["2"])},
        ]
        for change in changes:
            current.write_text(json.dumps(dict(original, **change)))
            with self.subTest(change=change), self.assertRaisesRegex(ValueError, "source/configuration/environment"):
                gate.performance_bind_gate(f.output, current, evidence, output)

    def test_transition_rejects_failed_equivalence_and_missing_evidence(self):
        f = self.fixture
        current, evidence, output = f.make_performance_binding()
        comparison_path = f.root / "prefix-cache-comparison.json"
        original = gate.read_json(comparison_path)
        for changes in ({"status": "failed"}, {"source_service_sha256": "b" * 64},
                        {"current_result": {"path": "/missing-prefix-result", "sha256": "a" * 64}}):
            comparison_path.write_text(json.dumps(dict(original, **changes)))
            binding = gate.read_json(evidence)
            binding["prefix_cache_regression"] = gate.artifact(comparison_path)
            evidence.write_text(json.dumps(binding))
            with self.subTest(changes=changes), self.assertRaises((ValueError, OSError)):
                gate.performance_bind_gate(f.output, current, evidence, output)


if __name__ == "__main__":
    unittest.main()
