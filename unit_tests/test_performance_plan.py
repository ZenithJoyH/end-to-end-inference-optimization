"""No vLLM installation, service, network, or accelerator is used here."""

import contextlib
import copy
import importlib.util
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch
from test_perf_result_schema import client_fixture


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("test_plan_runner", ROOT / "evaluation/performance/performance_plan.py")
PLAN = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(PLAN)


def config():
    return {"schema_version": 1,
            "target": {"model": "example", "tokenizer": "example-tokenizer", "host": "127.0.0.1",
                       "port": 8000, "endpoint": "/v1/completions"},
            "measurement": {"warmup_rounds": 1, "measured_rounds": 2, "timeout_s": 30},
            "cases": [{"id": "short", "input_tokens": 10, "output_tokens": 10,
                       "concurrency": 2, "requests": 2, "load_mode": "finite_batch"}]}


class PlanValidationTest(unittest.TestCase):
    def test_effective_defaults_and_idempotent_normalization(self):
        raw = config()
        result = PLAN.normalize_plan(raw)
        self.assertEqual(result["generation"], {"seed": 42, "temperature": 0, "ignore_eos": True, "random_range_ratio": 0})
        self.assertIsNone(result["measurement"]["warmup_stability"])
        self.assertEqual(PLAN.normalize_plan(result), result)
        self.assertNotIn("generation", raw)

    def test_invalid_contracts_fail_before_execution(self):
        edits = [
            lambda p: p.update(extra=True),
            lambda p: p["target"].update(extra=True),
            lambda p: p.update(generation={"random_range_ratio": 0.5}),
            lambda p: p.update(generation={"temperature": float("nan")}),
            lambda p: p.update(generation={"ignore_eos": 1}),
            lambda p: p["target"].update(port=True),
            lambda p: p["target"].update(endpoint="/v1/chat/completions"),
            lambda p: p["measurement"].update(required_metrics=[]),
            lambda p: p["measurement"].update(required_metrics=["made_up"]),
            lambda p: p["measurement"].update(required_metrics=["output_throughput"] * 2),
            lambda p: p["measurement"].update(timeout_s=float("inf")),
            lambda p: p["measurement"].update(warmup_rounds=0),
            lambda p: p["measurement"].update(measured_rounds=-1),
            lambda p: p["cases"][0].update(requests=False),
            lambda p: p["cases"][0].update(id="../escape"),
            lambda p: p["cases"].append(copy.deepcopy(p["cases"][0])),
            lambda p: p["cases"][0].update(load_mode="open_loop"),
            lambda p: p["cases"][0].update(request_rate=2),
            lambda p: p["cases"][0].update(load_mode="closed_loop"),
            lambda p: p["cases"][0].update(burstiness=0),
            lambda p: p["cases"][0].update(output_tokens=1),
            lambda p: p["measurement"].update(slo={"itl": 20}),
            lambda p: p["measurement"].update(slo={"ttft": -1}),
            lambda p: p["measurement"].update(warmup_stability={"metric": "output_throughput", "window": 3, "max_relative_spread": 0.05}),
        ]
        for edit in edits:
            value = config()
            edit(value)
            with self.subTest(value=value), self.assertRaises(ValueError):
                PLAN.normalize_plan(value)

    def test_duplicate_json_keys_and_nonfinite_values_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "bad.json"
            for text in ('{"seed": 1, "seed": 2}', '{"seed": NaN}'):
                path.write_text(text)
                with self.assertRaises(ValueError):
                    PLAN.read_json(path)

    def test_open_loop_slo_and_native_percentile_flags(self):
        raw = config()
        raw["cases"][0].update(load_mode="open_loop", request_rate=2.5, burstiness=0.5)
        raw["measurement"].update(required_metrics=["p95_ttft_ms", "p99_e2el_ms"], slo={"ttft": 100, "e2el": 500})
        plan = PLAN.normalize_plan(raw)
        self.assertIn("request_goodput", plan["measurement"]["required_metrics"])
        cmd = PLAN.build_round_command(plan, plan["cases"][0], 2143, Path("/tmp/result.json"))
        self.assertEqual(cmd[cmd.index("--request-rate") + 1], "2.5")
        self.assertEqual(cmd[cmd.index("--burstiness") + 1], "0.5")
        self.assertEqual(cmd[cmd.index("--metric-percentiles") + 1], "95,99")
        self.assertEqual(cmd[-3:], ["--goodput", "e2el:500", "ttft:100"])

    def test_single_token_requires_a_compatible_metric_contract(self):
        raw = config()
        raw["cases"][0]["output_tokens"] = 1
        raw["measurement"]["required_metrics"] = ["p99_ttft_ms", "output_throughput"]
        self.assertEqual(PLAN.normalize_plan(raw)["cases"][0]["output_tokens"], 1)

    def test_overflowed_warmup_median_cannot_establish_stability(self):
        check = PLAN._warmup_check([1e308, 1e308], {"metric": "p99_ttft_ms", "window": 2, "max_relative_spread": 0.05})
        self.assertEqual(check["status"], "failed")

    def test_eos_lengths_and_native_goodput_are_checked_without_reconstruction(self):
        raw = {"num_prompts": 2, "completed": 2, "failed": 0, "duration": 1.0,
               "total_input_tokens": 20, "total_output_tokens": 13, "errors": ["", ""],
               "output_lens": [3, 10], "request_throughput": 2, "output_throughput": 13,
               "total_token_throughput": 33, "request_goodput": 0}
        stdout = PLAN.NATIVE.extract_metrics("Successful requests: 2\nBenchmark duration (s): 1.00\nTotal input tokens: 20\nTotal generated tokens: 13\n")
        metrics, check = PLAN.NATIVE.validate_native_result((10, 10, 2, 2), raw, stdout,
            required_metrics=["request_goodput", "output_throughput"], ignore_eos=False, slo={"ttft": 100})
        self.assertEqual(check["errors"], [])
        self.assertEqual(metrics["request_goodput"], 0)
        raw["request_goodput"] = 3
        _, check = PLAN.NATIVE.validate_native_result((10, 10, 2, 2), raw, stdout,
            required_metrics=["request_goodput"], ignore_eos=False, slo={"ttft": 100})
        self.assertTrue(any("exceeds" in error for error in check["errors"]))

    def test_finite_but_contradictory_throughput_is_rejected(self):
        raw = {"num_prompts": 2, "completed": 2, "failed": 0, "duration": 1.0,
               "total_input_tokens": 20, "total_output_tokens": 20, "errors": ["", ""],
               "output_lens": [10, 10], "request_throughput": 2, "output_throughput": 20,
               "total_token_throughput": 40}
        stdout = PLAN.NATIVE.extract_metrics("Successful requests: 2\nBenchmark duration (s): 1.00\nTotal input tokens: 20\nTotal generated tokens: 20\n")
        for key in ("request_throughput", "output_throughput", "total_token_throughput"):
            with self.subTest(key=key):
                candidate = {**raw, key: raw[key] * 1.2}
                _, check = PLAN.NATIVE.validate_native_result((10, 10, 2, 2), candidate, stdout, required_metrics=[key])
                self.assertTrue(any(f"native {key} disagrees" in error for error in check["errors"]))


class PlanExecutionTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.plan_path, self.service_path = self.root / "plan.json", self.root / "service.json"
        self.plan_path.write_text(json.dumps(config()))
        self.service_path.write_text(json.dumps({"model_name": "example", "tokenizer_path": "example-tokenizer",
                                                "service_instance_id": "observed-process", "base_url": "http://127.0.0.1:8000/v1/chat/completions"}))
        self.args = SimpleNamespace(config=str(self.plan_path), service_manifest=str(self.service_path),
                                    role="baseline", run_id="baseline-1", output_dir=str(self.root / "results"),
                                    scope="diagnostic", accuracy_gate=None, comparison_contract=None, dry_run=False)
        self.client = {"schema_version": 1, "executable": "/test/vllm", "version": "0.12.0",
                       "supported_flags": [], "required_flags": [], "executable_sha256": None}

    def benchmark(self, command, **kwargs):
        self.assertEqual(kwargs["timeout"], 30)
        path = Path(command[command.index("--result-dir") + 1]) / command[command.index("--result-filename") + 1]
        count = int(command[command.index("--num-prompts") + 1])
        input_len = int(command[command.index("--random-input-len") + 1])
        output_len = int(command[command.index("--random-output-len") + 1])
        raw = {"num_prompts": count, "completed": count, "failed": 0, "duration": 1.0,
               "total_input_tokens": count * input_len, "total_output_tokens": count * output_len,
               "errors": [""] * count, "input_lens": [input_len] * count, "output_lens": [output_len] * count,
               "request_throughput": count, "output_throughput": count * output_len,
               "total_token_throughput": count * (input_len + output_len), "request_goodput": 0}
        raw.update({metric: 20.0 for metric in PLAN.NATIVE.SUPPORTED_PERFORMANCE_METRICS if metric.endswith("_ms")})
        raw.update(model_id="example", tokenizer_id="example-tokenizer", backend="vllm", max_concurrency=2,
                   request_rate="inf", burstiness=1)
        path.write_text(json.dumps(raw))
        stdout = (f"Successful requests: {count}\nFailed requests: 0\nBenchmark duration (s): 1.00\n"
                  f"Total input tokens: {input_len * count}\nTotal generated tokens: {output_len * count}\n")
        return subprocess.CompletedProcess(command, 0, stdout, "")

    def execute(self, side_effect=None):
        with patch.object(PLAN, "inspect_client", return_value=(copy.deepcopy(self.client), [])), \
                patch.object(PLAN.shutil, "which", return_value="/test/vllm"), \
                patch.object(PLAN.subprocess, "run", side_effect=side_effect or self.benchmark) as run:
            path = PLAN.execute_plan(self.args)
        return path, json.loads(path.read_text()), run.call_count

    def test_dry_run_has_no_subprocess_or_output_artifacts(self):
        self.args.dry_run = True
        stream = io.StringIO()
        with patch.object(PLAN.subprocess, "run") as run, patch.object(PLAN, "inspect_client") as inspect, contextlib.redirect_stdout(stream):
            self.assertIsNone(PLAN.execute_plan(self.args))
        run.assert_not_called()
        inspect.assert_not_called()
        result = json.loads(stream.getvalue())
        self.assertEqual([row["phase"] for row in result["commands"]], ["warmup", "measured", "measured"])
        self.assertEqual([row["seed"] for row in result["commands"]], [2143, 2144, 2145])
        self.assertFalse(Path(self.args.output_dir).exists())

    def test_complete_run_records_all_rounds_and_sha_bound_evidence(self):
        contract = self.root / "contract.json"
        contract.write_text('{"frozen": true}')
        self.args.comparison_contract = str(contract)
        path, record, count = self.execute()
        self.assertEqual(record["status"], "complete")
        self.assertEqual(count, 3)
        self.assertTrue(record["inputs_verified_after"])
        self.assertEqual(record["artifacts"]["comparison_contract"]["sha256"], PLAN.artifact(contract)["sha256"])
        self.assertEqual(record["warmup_check"]["short"]["status"], "not_checked")
        for row in record["rounds"]:
            for name in ("raw_result", "validation"):
                self.assertEqual(row[name], PLAN.artifact(row[name]["path"]))
            validation = PLAN.read_json(row["validation"]["path"])
            self.assertEqual(validation["command"][0], "vllm")
            self.assertEqual(validation["stdout_metrics"]["successful_requests"], 2)
            self.assertTrue(validation["valid"])
        with self.assertRaises(FileExistsError):
            PLAN.execute_plan(self.args)

    def test_failed_or_timed_out_round_is_retained_without_later_rounds(self):
        def failed(command, **kwargs):
            result = self.benchmark(command, **kwargs)
            result.returncode = 7
            return result
        path, record, count = self.execute(failed)
        self.assertEqual(record["status"], "failed")
        self.assertEqual(count, 1)
        self.assertEqual(record["rounds"][0]["returncode"], 7)
        self.assertTrue(record["rounds"][0]["raw_result"])
        self.args.run_id = "timeout"
        path, record, count = self.execute(lambda *a, **kw: (_ for _ in ()).throw(subprocess.TimeoutExpired(a[0], 30)))
        self.assertEqual(record["status"], "failed")
        self.assertEqual(count, 1)
        self.assertEqual(record["rounds"][0]["returncode"], 124)
        self.assertIsNone(record["rounds"][0]["raw_result"])
        self.assertTrue(record["rounds"][0]["validation"])

    def test_input_drift_stops_run_and_cannot_report_complete(self):
        def drift(command, **kwargs):
            result = self.benchmark(command, **kwargs)
            self.service_path.write_text(self.service_path.read_text() + "\n")
            return result
        path, record, count = self.execute(drift)
        self.assertEqual(count, 1)
        self.assertEqual(record["status"], "failed")
        self.assertFalse(record["inputs_verified_after"])
        self.assertTrue(any("SHA changed" in error for error in record["errors"]))

    def test_unstable_warmup_stops_at_budget_and_stable_warmup_advances(self):
        raw = config()
        raw["measurement"].update(warmup_rounds=3, warmup_stability={"metric": "output_throughput", "window": 3, "max_relative_spread": 0.05})
        self.plan_path.write_text(json.dumps(raw))
        seen = []
        def unstable(command, **kwargs):
            result = self.benchmark(command, **kwargs)
            path = Path(command[command.index("--result-dir") + 1]) / command[command.index("--result-filename") + 1]
            value = PLAN.read_json(path)
            seen.append(command)
            value["output_throughput"] = 10 * len(seen)
            value["duration"] = 20 / value["output_throughput"]
            value["request_throughput"] = 2 / value["duration"]
            value["total_token_throughput"] = 40 / value["duration"]
            path.write_text(json.dumps(value))
            result.stdout = result.stdout.replace("duration (s): 1.00", f"duration (s): {value['duration']:.2f}")
            return result
        path, record, count = self.execute(unstable)
        self.assertEqual(count, 3)
        self.assertEqual(record["status"], "failed")
        self.assertEqual(record["warmup_check"]["short"]["status"], "failed")
        self.assertTrue(all(row["phase"] == "warmup" for row in record["rounds"]))
        self.args.run_id = "stable"
        path, record, count = self.execute()
        self.assertEqual(count, 5)
        self.assertEqual(record["status"], "complete")
        self.assertEqual(record["warmup_check"]["short"]["status"], "passed")

    def test_no_client_creates_failed_record_without_benchmark_requests(self):
        with patch.object(PLAN.shutil, "which", return_value=None), patch.object(PLAN.subprocess, "run") as run:
            path = PLAN.execute_plan(self.args)
        run.assert_not_called()
        record = PLAN.read_json(path)
        self.assertEqual(record["status"], "failed")
        self.assertEqual(record["rounds"], [])
        self.assertTrue(record["artifacts"]["client"])

    def test_formal_gate_must_be_candidate_and_is_checked_before_and_after(self):
        self.args.role = "candidate"
        self.args.accuracy_gate = str(self.root / "gate.json")
        Path(self.args.accuracy_gate).write_text('{"test": "gate check mocked"}')
        with patch.object(PLAN, "_gate_check") as check:
            path, record, count = self.execute()
        self.assertEqual(check.call_count, 2)
        self.assertEqual(record["scope"], "formal_candidate")
        self.assertIn("accuracy_gate", record["artifacts"])
        self.args.role = "revert"
        with self.assertRaisesRegex(ValueError, "only valid for a candidate"):
            PLAN.execute_plan(self.args)

    def test_client_capability_probe_preserves_stable_identity(self):
        commands = [["vllm", "bench", "serve", "--model", "example", "--save-result"]]
        runtime = client_fixture(PLAN, [])['runtime']
        outputs = [subprocess.CompletedProcess([], 0, json.dumps(runtime), ""),
                   subprocess.CompletedProcess([], 0, "INFO startup\n0.12.0\n", ""),
                   subprocess.CompletedProcess([], 0, "INFO today\nusage: vllm bench serve --model MODEL --save-result\n", "")]
        executable = self.root / "vllm"
        executable.write_text("#!/usr/bin/python3\n")
        with patch.object(PLAN.shutil, "which", return_value=str(executable)), patch.object(PLAN.subprocess, "run", side_effect=outputs):
            client, errors = PLAN.inspect_client(commands)
        self.assertEqual(errors, [])
        self.assertEqual(client["version"], "0.12.0")
        self.assertEqual(client["supported_flags"], ["--model", "--save-result"])
        self.assertEqual(len(client["executable_sha256"]), 64)
        self.assertEqual(len(client["probes"]["help"]["output_sha256"]), 64)
        self.assertIn("output", client["probes"]["help"])
        self.assertEqual(
            client["probes"]["help"]["command"],
            [str(executable), "bench", "serve", "--help=all"],
        )

    def test_mismatched_service_fails_even_in_dry_run(self):
        self.args.dry_run = True
        service = PLAN.read_json(self.service_path)
        service["model_name"] = "different-model"
        self.service_path.write_text(json.dumps(service))
        with patch.object(PLAN.subprocess, "run") as run, self.assertRaisesRegex(ValueError, "model/tokenizer differs"):
            PLAN.execute_plan(self.args)
        run.assert_not_called()

    def test_native_workload_mismatch_stops_before_measured_rounds(self):
        for key, value in (("model_id", "wrong"), ("tokenizer_id", "wrong"), ("max_concurrency", 999),
                           ("request_rate", 5), ("burstiness", 0.2), ("input_lens", [1, 19])):
            with self.subTest(key=key):
                self.args.run_id = "mismatch-" + key
                def mismatch(command, **kwargs):
                    result = self.benchmark(command, **kwargs)
                    path = Path(command[command.index("--result-dir") + 1]) / command[command.index("--result-filename") + 1]
                    raw = PLAN.read_json(path)
                    raw[key] = value
                    path.write_text(json.dumps(raw))
                    return result
                path, record, count = self.execute(mismatch)
                self.assertEqual((record["status"], count), ("failed", 1))
                self.assertEqual(len(record["rounds"]), 1)

    def test_malformed_stdout_preserves_failed_round(self):
        def malformed(command, **kwargs):
            result = self.benchmark(command, **kwargs)
            result.stdout = result.stdout.replace("requests: 2", "requests: 1.2.3")
            return result
        path, record, count = self.execute(malformed)
        self.assertEqual((record["status"], count), ("failed", 1))
        validation = PLAN.read_json(record["rounds"][0]["validation"]["path"])
        self.assertIn("1.2.3", PLAN.read_json(validation["output"]["path"])["stdout"])

    def test_runtime_probe_binds_editable_benchmark_source_content(self):
        # Execute only a local stdlib probe against a synthetic package.
        package = self.root / "vllm"
        source = package / "benchmarks" / "serve.py"
        source.parent.mkdir(parents=True)
        (package / "__init__.py").write_text("")
        source.write_text("# before\n")
        metadata = self.root / "vllm-0.12.0.dist-info"
        metadata.mkdir()
        (metadata / "METADATA").write_text("Name: vllm\nVersion: 0.12.0\n")
        executable = self.root / "vllm-console"
        executable.write_text("#!" + sys.executable + "\n")
        with patch.dict(os.environ, {"PYTHONPATH": str(self.root)}):
            before = PLAN.runtime_from_probe(PLAN._probe(PLAN.runtime_command(executable)))
            source.write_text("# after\n")
            after = PLAN.runtime_from_probe(PLAN._probe(PLAN.runtime_command(executable)))
        self.assertEqual(before["vllm_version"], after["vllm_version"])
        self.assertNotEqual(before["source_files"], after["source_files"])

    def test_source_drift_marks_after_verification_failed(self):
        source = self.root / "serve.py"
        source.write_text("# before")
        self.client["runtime"] = {"python_executable": PLAN.artifact(sys.executable),
                                  "source_files": [PLAN.artifact(source)]}
        def changed_source(command, **kwargs):
            result = self.benchmark(command, **kwargs)
            source.write_text("# after")
            return result
        path, record, count = self.execute(changed_source)
        self.assertEqual((record["status"], count), ("failed", 1))
        self.assertFalse(record["inputs_verified_after"])

    def test_runtime_command_keeps_virtualenv_interpreter_symlink(self):
        environment = self.root / "venv"
        subprocess.run([sys.executable, "-m", "venv", "--without-pip", str(environment)],
                       check=True, capture_output=True, timeout=30)
        interpreter = environment / "bin" / "python3"
        site = Path(subprocess.run([str(interpreter), "-c", "import sysconfig; print(sysconfig.get_path('purelib'))"],
                                   check=True, capture_output=True, text=True, timeout=30).stdout.strip())
        package = site / "vllm"
        (package / "benchmarks").mkdir(parents=True)
        (package / "__init__.py").write_text("")
        source = package / "benchmarks" / "serve.py"
        source.write_text("# installed only in the synthetic virtualenv\n")
        metadata = site / "vllm-0.12.0.dist-info"
        metadata.mkdir()
        (metadata / "METADATA").write_text("Name: vllm\nVersion: 0.12.0\n")
        executable = environment / "bin" / "vllm"
        executable.write_text("#!" + str(interpreter) + "\n")
        self.assertEqual(PLAN.runtime_command(executable)[0], str(interpreter))
        with patch.dict(os.environ, {"PYTHONPATH": ""}):
            runtime = PLAN.runtime_from_probe(PLAN._probe(PLAN.runtime_command(executable)))
        self.assertEqual(runtime["python_invocation"], str(interpreter))
        self.assertIn(PLAN.artifact(source), runtime["source_files"])


if __name__ == "__main__":
    unittest.main()
