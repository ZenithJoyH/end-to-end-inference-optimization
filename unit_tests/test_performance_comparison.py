"""Synthetic complete run artifacts exercise comparison decisions without a GPU."""
import copy
import json
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch
import subprocess

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "evaluation/performance"))
import compare_performance as compare
import performance_plan
import vllm_perf
from test_perf_result_schema import native_result, client_fixture


class ComparisonTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.contract = {
            "schema_version": 1, "scope": "performance_only", "hypothesis": "one kernel implementation",
            "variable_paths": ["/flaggems_sha256"],
            "primary": {"metric": "output_throughput", "direction": "higher", "min_improvement": 0.05},
            "guardrails": [{"metric": "p99_ttft_ms", "direction": "lower", "max_regression": 0.1, "maximum": 100}],
            "repeats": {"min_processes": 2, "min_measured_rounds": 2, "max_relative_spread": 0.1, "max_baseline_drift": 0.1},
            "slo_min_attainment": 1,
        }
        self.contract_path = self.root / "contract.json"
        self.save(self.contract_path, self.contract)
        self.plan = {
            "schema_version": 1,
            "target": {"model": "model-a", "tokenizer": "/tokenizer", "host": "127.0.0.1", "port": 8000,
                       "endpoint": "/v1/completions", "trust_remote_code": False},
            "generation": {"seed": 42, "temperature": 0, "ignore_eos": True, "random_range_ratio": 0},
            "measurement": {"warmup_rounds": 2, "measured_rounds": 2, "timeout_s": 60,
                            "required_metrics": list(vllm_perf.REQUIRED_PERFORMANCE_METRICS) + ["request_goodput"],
                            "slo": {"ttft": 1000},
                            "warmup_stability": {"metric": "p99_ttft_ms", "window": 2, "max_relative_spread": 0.1}},
            "cases": [{"id": "short", "input_tokens": 10, "output_tokens": 10, "concurrency": 2,
                       "requests": 2, "load_mode": "finite_batch", "request_rate": None, "burstiness": 1}],
        }
        self.paths = [self.make_run(role, i) for role in compare.ROLES for i in range(2)]

    def save(self, path, value):
        path.write_text(json.dumps(value), encoding="utf-8")
        return compare.artifact(path)

    def make_run(self, role, index):
        folder = self.root / f"{role}-{index}"
        folder.mkdir()
        plan_ref = self.save(folder / "plan.json", self.plan)
        plan = performance_plan.load_plan(folder / "plan.json")
        service = dict(host="host-a", optimization_container_name="isolated", service_instance_id=f"{role}-boot-{index}",
                       model_name="model-a", base_url="http://127.0.0.1:8000/v1/chat/completions", tokenizer_path="/tokenizer",
                       mode="graph", launch_config={"tp": 1}, image_lineage="verified", mount_parity="passed")
        service.update({key: "a" * 64 for key in ("model_sha256", "tokenizer_sha256", "engine_sha256", "plugin_sha256",
                                                 "flaggems_sha256", "runtime_evidence_sha256")})
        if role == "candidate":
            service["flaggems_sha256"] = "b" * 64
        service["performance_context"] = dict(platform="synthetic", device_model="fixture", device_ids=["device-0"],
                                              driver_version="fixture", device_runtime_version="fixture", image_id="sha256:" + "c" * 64,
                                              prefix_cache_state="disabled", cache_preparation="synthetic fixture")
        command = performance_plan.build_round_command(plan, plan["cases"][0], 2143, folder / "raw.json")
        client = client_fixture(performance_plan, {arg for arg in command if arg.startswith("--")})
        refs = {"plan": plan_ref, "service": self.save(folder / "service.json", service),
                "comparison_contract": compare.artifact(self.contract_path),
                "client_probes": self.save(folder / "client-probes.json", client.pop("probes")),
                "client": self.save(folder / "client.json", client)}
        rounds = []
        for i in range(1, 5):
            raw = native_result()
            raw["duration"] = 1.0 if role == "candidate" else 2.0
            for key, count in (("request_throughput", 2), ("output_throughput", 20), ("total_token_throughput", 40), ("request_goodput", 2)):
                raw[key] = count / raw["duration"]
            raw_ref = self.save(folder / f"raw-{i}.json", raw)
            seed = 42 + 10 * 10 + 2 * 1000 + i
            stdout = f"Successful requests: 2\nBenchmark duration (s): {raw['duration']:.2f}\nTotal input tokens: 20\nTotal generated tokens: 20\n"
            validation = {"command": performance_plan.build_round_command(plan, plan["cases"][0], seed, Path(raw_ref["path"])),
                          "returncode": 0, "stdout_metrics": vllm_perf.extract_metrics(stdout), "valid": True, "errors": [],
                          "output": self.save(folder / f"output-{i}.json", {"stdout": stdout, "stderr": ""})}
            rounds.append({"case_id": "short", "round_id": i, "phase": "warmup" if i <= 2 else "measured", "seed": seed,
                           "returncode": 0, "raw_result": raw_ref, "validation": self.save(folder / f"validation-{i}.json", validation)})
        record = {"schema_version": 1, "kind": "performance_run", "status": "complete", "scope": "performance_only",
                  "inputs_verified_before": True, "inputs_verified_after": True,
                  "role": role, "run_id": folder.name, "artifacts": refs, "rounds": rounds}
        path = folder / "run-record.json"
        self.save(path, record)
        return path

    def decision(self, paths=None):
        return compare.compare(self.contract_path, paths if paths is not None else self.paths)

    def mutate_artifact(self, run_index, key, update):
        path = self.paths[run_index]
        record = compare.read_json(path)
        ref = record["artifacts"][key]
        value = compare.read_json(ref["path"])
        update(value)
        record["artifacts"][key] = self.save(Path(ref["path"]), value)
        self.save(path, record)

    def mutate_round(self, run_index, index, update):
        path = self.paths[run_index]
        record = compare.read_json(path)
        ref = record["rounds"][index]["raw_result"]
        value = compare.read_json(ref["path"])
        update(value)
        record["rounds"][index]["raw_result"] = self.save(Path(ref["path"]), value)
        self.save(path, record)

    def test_complete_comparison_passes_and_keeps_process_units(self):
        report = self.decision()
        self.assertEqual(report["status"], "passed", report)
        metric = report["cases"]["short"]["metrics"]["output_throughput"]
        self.assertEqual(metric["relative_improvement"], 1)
        self.assertEqual(metric["candidate"]["process_values"], [20, 20])
        self.assertEqual(report["changed_paths"], ["/flaggems_sha256"])

    def test_native_metadata_is_revalidated_against_frozen_plan(self):
        self.mutate_round(0, 0, lambda raw: raw.update(model_id="wrong-model", max_concurrency=999))
        report = self.decision()
        self.assertEqual(report["status"], "incomplete")
        self.assertIn("native model_id", " ".join(report["issues"]))

    def test_missing_probe_and_invented_capabilities_are_incomplete(self):
        self.mutate_artifact(0, "client_probes", lambda value: value.pop("help"))
        self.assertIn("probe", " ".join(self.decision()["issues"]))
        self.mutate_artifact(1, "client", lambda value: value.update(required_flags=[], supported_flags=[]))
        report = self.decision(self.paths[1:])
        self.assertEqual(report["status"], "incomplete")
        self.assertIn("probe evidence", " ".join(report["issues"]))

    def test_modified_runtime_identity_needs_matching_probe(self):
        self.mutate_artifact(0, "client", lambda value: value["runtime"]["source_files"][0].update(sha256="1" * 64))
        self.assertIn("runtime identity", " ".join(self.decision()["issues"]))

    def test_eager_completion_service_has_explicit_nonformal_identity(self):
        from acceptance import validate_service
        for i in range(len(self.paths)):
            self.mutate_artifact(i, "service", lambda service: service.update(
                mode="eager", base_url="http://127.0.0.1:8000/v1/completions"))
        report = self.decision()
        self.assertEqual(report["status"], "passed", report)
        record = compare.read_json(self.paths[2])
        service = compare.read_json(record["artifacts"]["service"]["path"])
        with self.assertRaises(ValueError):
            validate_service(service)

    def test_failed_validation_cannot_be_relabelled_complete(self):
        record = compare.read_json(self.paths[0])
        ref = record["rounds"][0]["validation"]
        validation = compare.read_json(ref["path"])
        validation.update(valid=False, errors=["failed admission"])
        record["rounds"][0]["validation"] = self.save(Path(ref["path"]), validation)
        self.save(self.paths[0], record)
        self.assertIn("not admitted", " ".join(self.decision()["issues"]))

    def test_malformed_top_level_and_boolean_schema_return_incomplete(self):
        self.save(self.paths[0], [])
        self.assertEqual(self.decision()["status"], "incomplete")
        for change in ({"schema_version": True}, {"primary": dict(self.contract["primary"], min_improvement=10**1000)}):
            with self.subTest(change=change), self.assertRaises(ValueError):
                compare.validate_contract(dict(self.contract, **change))

    def test_executor_artifacts_feed_comparator_without_translation(self):
        executable = self.root / "fixture-vllm"
        executable.write_text("#!" + sys.executable + "\n# synthetic; never executed\n")
        source = self.root / "vllm" / "benchmarks" / "serve.py"
        source.parent.mkdir(parents=True)
        source.write_text("# synthetic benchmark source")
        runtime = {"python_invocation": str(Path(sys.executable).absolute()),
                   "python_executable": compare.artifact(sys.executable), "python_version": "fixture Python",
                   "vllm_version": "0.12.0", "source_files": [compare.artifact(source)]}
        command = performance_plan.build_round_command(self.plan, self.plan["cases"][0], 2143, self.root / "raw.json")
        client = client_fixture(performance_plan, {arg for arg in command if arg.startswith("--")}, str(executable), runtime)
        client["executable_sha256"] = compare.artifact(executable)["sha256"]
        def benchmark(command, **kwargs):
            raw_path = Path(command[command.index("--result-dir") + 1]) / command[command.index("--result-filename") + 1]
            duration = 1.0 if "candidate" in raw_path.parent.name else 2.0
            raw = native_result()
            raw["duration"] = duration
            for key, count in (("request_throughput", 2), ("output_throughput", 20), ("total_token_throughput", 40), ("request_goodput", 2)):
                raw[key] = count / duration
            self.save(raw_path, raw)
            stdout = f"Successful requests: 2\nBenchmark duration (s): {duration:.2f}\nTotal input tokens: 20\nTotal generated tokens: 20\n"
            return subprocess.CompletedProcess(command, 0, stdout, "")
        generated = []
        with patch.object(performance_plan, "inspect_client", return_value=(client, [])), \
                patch.object(performance_plan, "_probe", return_value=client["probes"]["runtime"]), \
                patch.object(performance_plan.shutil, "which", return_value=str(executable)), \
                patch.object(performance_plan.subprocess, "run", side_effect=benchmark):
            for path in self.paths:
                source = compare.read_json(path)
                args = SimpleNamespace(config=source["artifacts"]["plan"]["path"],
                                       service_manifest=source["artifacts"]["service"]["path"],
                                       role=source["role"], run_id="linked-" + source["run_id"],
                                       output_dir=self.root / "executed", scope="performance_only",
                                       accuracy_gate=None, comparison_contract=self.contract_path, dry_run=False)
                generated.append(performance_plan.execute_plan(args))
        report = self.decision(generated)
        self.assertEqual(report["status"], "passed", report)

    def test_missing_role_duplicate_run_and_same_process_are_incomplete(self):
        self.assertEqual(self.decision(self.paths[:-1])["status"], "incomplete")
        self.assertEqual(self.decision(self.paths + [self.paths[0]])["status"], "incomplete")
        self.mutate_artifact(3, "service", lambda x: x.update(service_instance_id="candidate-boot-0"))
        self.assertIn("same service process", " ".join(self.decision()["issues"]))

    def test_changed_raw_hash_and_missing_round_are_incomplete(self):
        record = compare.read_json(self.paths[0])
        Path(record["rounds"][0]["raw_result"]["path"]).write_text("{}")
        self.assertEqual(self.decision()["status"], "incomplete")
        record["rounds"].pop()
        self.save(self.paths[0], record)
        self.assertIn("round", " ".join(self.decision()["issues"]))

    def test_changed_contract_after_measurement_is_incomplete(self):
        self.contract["primary"]["min_improvement"] = 0
        self.save(self.contract_path, self.contract)
        self.assertIn("freeze", " ".join(self.decision()["issues"]))

    def test_hardware_or_undeclared_launch_change_is_incomplete(self):
        self.mutate_artifact(2, "service", lambda x: x["performance_context"].update(device_ids=["other-device"]))
        self.assertIn("undeclared", " ".join(self.decision()["issues"]))

    def test_missing_context_is_not_accepted_from_hashes_alone(self):
        self.mutate_artifact(0, "service", lambda x: x.pop("performance_context"))
        self.assertIn("performance_context", " ".join(self.decision()["issues"]))

    def test_guardrail_and_joint_slo_fail_independently(self):
        self.mutate_round(2, 2, lambda x: x.update(p99_ttft_ms=120))
        self.mutate_round(2, 3, lambda x: x.update(p99_ttft_ms=120))
        self.mutate_round(3, 2, lambda x: x.update(p99_ttft_ms=120))
        self.mutate_round(3, 3, lambda x: x.update(p99_ttft_ms=120))
        report = self.decision()
        self.assertEqual(report["status"], "failed", report)
        self.mutate_round(2, 2, lambda x: x.update(request_goodput=1))
        report = self.decision()
        self.assertEqual(report["status"], "failed", report)
        self.assertTrue(any("SLO" in issue for issue in report["issues"]))

    def test_within_process_noise_is_incomplete(self):
        self.mutate_round(2, 2, lambda x: x.update(p99_ttft_ms=10))
        self.assertTrue(any("spread" in issue for issue in self.decision()["issues"]))

    def test_warmup_is_recomputed_not_trusted_as_a_flag(self):
        self.mutate_round(2, 0, lambda x: x.update(p99_ttft_ms=1))
        self.assertTrue(any("warmup" in issue for issue in self.decision()["issues"]))

    def test_revert_cannot_reuse_baseline_measurement_artifacts(self):
        for baseline_index, revert_index in ((0, 4), (1, 5)):
            baseline = compare.read_json(self.paths[baseline_index])
            revert = compare.read_json(self.paths[revert_index])
            revert["rounds"] = baseline["rounds"]
            self.save(self.paths[revert_index], revert)
        self.assertIn("reused", " ".join(self.decision()["issues"]))

    def test_cache_experiment_may_declare_specific_companion_state(self):
        self.contract["variable_paths"] += ["/performance_context/prefix_cache_state", "/performance_context/cache_preparation"]
        self.save(self.contract_path, self.contract)
        for path in self.paths:
            record = compare.read_json(path)
            record["artifacts"]["comparison_contract"] = compare.artifact(self.contract_path)
            self.save(path, record)
        for i in (2, 3):
            self.mutate_artifact(i, "service", lambda x: x["performance_context"].update(prefix_cache_state="warm", cache_preparation="controlled warm prefix"))
        report = self.decision()
        self.assertEqual(report["status"], "passed", report)

    def test_zero_goodput_warmup_matches_executor_failure(self):
        for i, path in enumerate(self.paths):
            self.mutate_artifact(i, "plan", lambda x: x["measurement"]["warmup_stability"].update(metric="request_goodput"))
            for j in (0, 1):
                self.mutate_round(i, j, lambda x: x.update(request_goodput=0))
        report = self.decision()
        self.assertEqual(report["status"], "incomplete", report)
        self.assertTrue(any("warmup" in issue for issue in report["issues"]))

    def test_invalid_contract_thresholds_and_broad_variable_paths_fail(self):
        changes = [dict(variable_paths=["/launch_config"]), dict(variable_paths=["/model_sha256"]),
                   dict(primary=dict(self.contract["primary"], min_improvement=float("nan"))),
                   dict(repeats=dict(self.contract["repeats"], min_processes=True))]
        for change in changes:
            with self.subTest(change=change), self.assertRaises(ValueError):
                compare.validate_contract(dict(self.contract, **change))

    def test_formal_comparison_cannot_consume_performance_only_runs(self):
        self.contract["scope"] = "formal"
        self.save(self.contract_path, self.contract)
        for path in self.paths:
            record = compare.read_json(path)
            record["artifacts"]["comparison_contract"] = compare.artifact(self.contract_path)
            self.save(path, record)
        self.assertIn("formally admitted", " ".join(self.decision()["issues"]))


if __name__ == "__main__":
    unittest.main()
