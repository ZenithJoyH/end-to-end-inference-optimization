"""Local failure-path regressions; no evaluator package or model requests."""
import contextlib
import io
import json
from pathlib import Path
import sys
import unittest
from types import SimpleNamespace
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "evaluation/accuracy"))
import acceptance as gate
import formal_accuracy
import test_acceptance as fixtures
from test_accuracy_provenance import result_payload


class AccuracyFailureTest(unittest.TestCase):
    def setUp(self):
        self.fixture = fixtures.GateTest("test_original_runner_unchanged")
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        self.root = self.fixture.root
        self.runner = formal_accuracy.load_runner()
        self.cfg = dict(self.fixture.cfg, output_root=str(self.root / "outputs"))
        self.config_path = self.root / "input-config.json"
        self.config_path.write_text(json.dumps(self.cfg))
        self.args = SimpleNamespace(
            config=self.config_path, service_manifest=self.root / "service.json",
            contract=self.root / "contract.json",
            evaluation_inspect=self.root / "evaluation_inspect.json",
            preflight_only=False, capture_provenance=None,
        )

    @contextlib.contextmanager
    def external_work(self, task):
        with patch.object(formal_accuracy, "load_runner", return_value=self.runner), \
             patch.object(formal_accuracy, "collect_provenance", return_value=self.fixture.provenance) as collect, \
             patch.object(self.runner, "configure_environment"), \
             patch.object(self.runner, "probe_service", return_value=(True, "ready")) as probe, \
             patch.object(self.runner, "run_task", side_effect=task) as evaluate, \
             contextlib.redirect_stdout(io.StringIO()):
            yield collect, probe, evaluate

    def test_serialization_failure_leaves_no_output_and_allows_retry(self):
        path = self.root / "new-artifact.json"
        with self.assertRaises(ValueError):
            gate.write_new(path, {"written_first": True, "invalid": float("nan")})
        self.assertFalse(path.exists(), "failed serialization must not reserve a corrupt artifact")
        gate.write_new(path, {"valid": True})
        self.assertEqual(gate.read_json(path), {"valid": True})
        with self.assertRaises(FileExistsError):
            gate.write_new(path, {"valid": False})
        self.assertEqual(gate.read_json(path), {"valid": True})

    def test_invalid_results_do_not_publish_an_evaluated_record(self):
        def task(cfg, task_name, run_dir):
            task_dir = run_dir / task_name
            task_dir.mkdir()
            result = result_payload(cfg, self.fixture.provenance)
            result["n-samples"][task_name]["effective"] = 1
            (task_dir / "results_invalid.json").write_text(json.dumps(result))
            (task_dir / f"samples_{task_name}_invalid.jsonl").write_text(
                (self.root / "samples.jsonl").read_text())
            return True  # Native runner checks score presence/sample structure only.

        with self.external_work(task), self.assertRaisesRegex(ValueError, "198 original and effective"):
            formal_accuracy.run(self.args)
        self.assertEqual(list((self.root / "outputs").rglob("run-record.json")), [])
        self.assertEqual(list((self.root / "outputs").rglob("health-review.template.json")), [])
        self.assertEqual(len(list((self.root / "outputs").rglob("results_invalid.json"))), 1)

    def test_write_failure_leaves_no_partial_output_or_temporary_file(self):
        path = self.root / "failed-write.json"
        with patch.object(gate.os, "fsync", side_effect=OSError("simulated write failure")), \
             self.assertRaisesRegex(OSError, "simulated write failure"):
            gate.write_new(path, {"valid": True})
        self.assertFalse(path.exists())
        self.assertEqual(list(self.root.glob(".failed-write.json.*.tmp")), [])
        gate.write_new(path, {"valid": True})
        self.assertEqual(gate.read_json(path), {"valid": True})

    def test_failed_score_preserves_results_without_completed_record(self):
        def task(cfg, task_name, run_dir):
            task_dir = run_dir / task_name
            task_dir.mkdir()
            (task_dir / "results_low_score.json").write_text(json.dumps(
                result_payload(cfg, self.fixture.provenance, score=0.1)))
            (task_dir / f"samples_{task_name}_low_score.jsonl").write_text(
                (self.root / "samples.jsonl").read_text())
            return True

        with self.external_work(task), self.assertRaisesRegex(ValueError, "below the frozen minimum"):
            formal_accuracy.run(self.args)
        self.assertEqual(list((self.root / "outputs").rglob("run-record.json")), [])
        self.assertEqual(len(list((self.root / "outputs").rglob("results_low_score.json"))), 1)

    def test_fractional_or_boolean_integer_config_rejected_before_external_work(self):
        for change in ({"limit": 0.9}, {"expected_samples": 198.9}, {"num_concurrent": True},
                       {"timeout": "60"}, {"api_max_retries": -1}, {"eval_max_retries": -1}):
            with self.subTest(change=change):
                self.config_path.write_text(json.dumps(dict(self.cfg, **change)))
                self.args.capture_provenance = self.root / (next(iter(change)) + "-unexpected-provenance.json")
                with self.external_work(lambda *args: True) as (collect, probe, evaluate):
                    with self.assertRaisesRegex(ValueError, "integer"):
                        formal_accuracy.run(self.args)
                    collect.assert_not_called()
                    probe.assert_not_called()
                    evaluate.assert_not_called()

    def test_gate_rejects_invalid_integer_values_in_effective_config(self):
        for change in ({"limit": False}, {"expected_samples": 198.0}, {"timeout": 1.9},
                       {"api_max_retries": -1}):
            with self.subTest(change=change), self.assertRaisesRegex(ValueError, "integer"):
                gate.validate_config(dict(self.cfg, **change), self.fixture.service)

    def test_research_service_accepts_supported_modes_and_endpoints_without_mutation(self):
        for mode in ("eager", "graph"):
            for endpoint in ("/v1/completions", "/v1/chat/completions"):
                service = dict(self.fixture.service, mode=mode,
                               base_url="http://127.0.0.1:8000" + endpoint)
                before = json.dumps(service, sort_keys=True)
                with self.subTest(mode=mode, endpoint=endpoint):
                    gate.validate_service(service, formal=False)
                    self.assertEqual(json.dumps(service, sort_keys=True), before)

    def test_formal_gate_keeps_graph_and_chat_requirements(self):
        for change, message in (({"mode": "eager"}, "graph"),
                                ({"base_url": "http://127.0.0.1:8000/v1/completions"}, "chat/completions")):
            service = dict(self.fixture.service, **change)
            with self.subTest(change=change):
                with self.assertRaisesRegex(ValueError, message):
                    gate.validate_service(service)
                self.fixture.save("service", service)
                record = gate.read_json(self.fixture.record)
                record["artifacts"]["service"] = self.fixture.refs["service"]
                self.fixture.record.write_text(json.dumps(record))
                with self.assertRaisesRegex(ValueError, message):
                    gate.issue_gate(self.fixture.record, self.fixture.health, self.fixture.output)
                self.assertFalse(self.fixture.output.exists())

    def test_research_service_still_requires_valid_identity_and_supported_endpoint(self):
        for change in ({"mode": "unknown"}, {"base_url": "http://127.0.0.1:8000/generate"},
                       {"model_sha256": "unknown"}, {"mount_parity": "failed"},
                       {"image_lineage": "unverified"}, {"launch_config": {}},
                       {"base_url": "http://user:secret@127.0.0.1:8000/v1/completions"},
                       {"base_url": "http://127.0.0.1:8000/v1/completions?model=other"}):
            service = {**self.fixture.service, "mode": "eager", **change}
            with self.subTest(change=change), self.assertRaises(ValueError):
                gate.validate_service(service, formal=False)


if __name__ == "__main__":
    unittest.main()
