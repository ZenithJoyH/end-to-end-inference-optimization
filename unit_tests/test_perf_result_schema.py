"""Regression fixtures follow vLLM v0.11.0/v0.12.0 generation result fields.

Sources: https://github.com/vllm-project/vllm/blob/v0.11.0/vllm/benchmarks/serve.py
and https://github.com/vllm-project/vllm/blob/v0.12.0/vllm/benchmarks/serve.py
Fixtures are synthetic; these tests do not execute vLLM or validate a device.
"""

import contextlib
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "perf_result_schema", ROOT / "evaluation/performance/vllm_perf.py"
)
PERF = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(PERF)
CASE = (10, 10, 2, 2)
STDOUT = (
    "Successful requests: 2\nBenchmark duration (s): 1.23\n"
    "Total input tokens: 20\nTotal generated tokens: 20\n"
)


def native_result(*, legacy=False):
    result = {
        "model_id": "model-a", "tokenizer_id": "/tokenizer", "backend": "vllm",
        "max_concurrency": 2, "request_rate": "inf", "burstiness": 1,
        "num_prompts": 2,
        "completed": 2,
        "duration": 1.234,
        "total_input_tokens": 20,
        "total_output_tokens": 20,
        "errors": ["", ""],
        "input_lens": [10, 10],
        "output_lens": [10, 10],
        "request_throughput": 2 / 1.234,
        "output_throughput": 20 / 1.234,
        "total_token_throughput": 40 / 1.234,
        "mean_ttft_ms": 40.001,
        "median_ttft_ms": 40.002,
        "p99_ttft_ms": 49.1,
        "mean_tpot_ms": 3.1,
        "median_tpot_ms": 3.2,
        "p99_tpot_ms": 5.1,
        "mean_itl_ms": 3.3,
        "median_itl_ms": 3.4,
        "p99_itl_ms": 6.1,
    }
    if not legacy:
        result["failed"] = 0
    return result


def client_fixture(plan_module, flags, executable="/fixture/vllm", runtime=None):
    """Synthetic client evidence; never interpreted as target hardware checks."""
    flags = sorted(flags)
    runtime = runtime or {"python_invocation": "/fixture/python",
                          "python_executable": {"path": "/fixture/python", "sha256": "e" * 64},
                          "python_version": "fixture Python", "vllm_version": "0.12.0",
                          "source_files": [{"path": "/fixture/vllm/benchmarks/serve.py", "sha256": "f" * 64}]}
    client = {"schema_version": 1, "version": "0.12.0", "executable": executable,
              "executable_sha256": "d" * 64, "required_flags": flags, "supported_flags": flags,
              "runtime": runtime, "probes": {}}
    for name, command, output in (
        ("version", [executable, "--version"], "0.12.0\n"),
        ("help", [executable, "bench", "serve", "--help=all"], "usage: " + " ".join(flags)),
        ("runtime", [runtime["python_invocation"], "-c", plan_module.RUNTIME_PROBE, runtime["python_invocation"]], json.dumps(runtime)),
    ):
        client["probes"][name] = {"command": command, "returncode": 0, "output": output,
                                  "output_sha256": hashlib.sha256(output.encode()).hexdigest()}
    return client


class NativeSchemaTest(unittest.TestCase):
    def test_malformed_and_duplicate_stdout_cannot_be_read_as_success(self):
        for value in ("2oops", "1.2.3", "nan", "inf", "2\nSuccessful requests: 2"):
            with self.subTest(value=value):
                stdout = STDOUT.replace("requests: 2", "requests: " + value)
                _, report = self.validate(native_result(), stdout)
                self.assertTrue(report["errors"])

    def test_timeout_and_exec_failure_keep_invalid_round_evidence(self):
        for error, code in ((subprocess.TimeoutExpired(["vllm"], 1, output=b"partial", stderr=b"waiting"), 124),
                            (FileNotFoundError("missing client"), 127)):
            with self.subTest(error=error), tempfile.TemporaryDirectory() as folder, \
                    patch.object(PERF.subprocess, "run", side_effect=error) as run, \
                    contextlib.redirect_stdout(io.StringIO()):
                metrics = PERF.run_once(CASE, 1, folder, ["vllm"], timeout_s=1)
                self.assertFalse(metrics["valid"])
                self.assertEqual(metrics["returncode"], code)
                self.assertEqual(run.call_args.kwargs["timeout"], 1)
                report = json.loads(next(Path(folder).glob("*.validation.json")).read_text())
                output = json.loads(Path(report["output_path"]).read_text())
                self.assertFalse(report["valid"])
                self.assertTrue(report["errors"])
                self.assertEqual(report["stdout_metrics"], PERF.extract_metrics(output["stdout"]))
                self.assertEqual(len(list((Path(folder) / "error_logs").glob("*.json"))), 1)

    def validate(self, raw, stdout=STDOUT):
        return PERF.validate_native_result(CASE, raw, PERF.extract_metrics(stdout))

    def test_both_documented_schemas_preserve_native_metrics(self):
        for legacy in (False, True):
            with self.subTest(legacy=legacy):
                raw = native_result(legacy=legacy)
                raw["future_optional_field"] = {"ignored": True}
                metrics, report = self.validate(raw)
                self.assertEqual(report["errors"], [])
                self.assertNotEqual(report["schema"], "unknown")
                self.assertEqual(metrics["failed_requests"], 0)
                self.assertEqual(metrics["mean_ttft_ms"], 40.001)
                self.assertIsNone(metrics["peak_output_throughput"])

    def test_missing_failed_needs_complete_legacy_evidence(self):
        for field, value in (
            ("errors", None), ("errors", [""]), ("errors", ["", "timeout"]),
            ("output_lens", [10]), ("output_lens", [0, 20]),
            ("output_lens", [9, 11]), ("completed", 1), ("num_prompts", 3),
        ):
            with self.subTest(field=field, value=value):
                raw = native_result(legacy=True)
                raw[field] = value
                metrics, report = self.validate(raw)
                self.assertTrue(report["errors"])
                self.assertIsNone(metrics["failed_requests"])
        raw = native_result(legacy=True)
        del raw["errors"]
        _, report = self.validate(raw)
        self.assertEqual(report["schema"], "unknown")

    def test_explicit_failed_count_is_never_ignored(self):
        for value in (1, None, False, "0"):
            with self.subTest(value=value):
                raw = native_result()
                raw["failed"] = value
                _, report = self.validate(raw)
                self.assertTrue(any("native failed" in error for error in report["errors"]))

    def test_stdout_and_native_completion_evidence_must_agree(self):
        for stdout in (
            STDOUT.replace("requests: 2", "requests: 1"),
            STDOUT.replace("tokens: 20", "tokens: 19"),
            STDOUT.replace("1.23", "2.00"),
            STDOUT + "Failed requests: 1\n",
        ):
            with self.subTest(stdout=stdout):
                _, report = self.validate(native_result(legacy=True), stdout)
                self.assertTrue(report["errors"])

    def test_missing_or_nonfinite_required_metrics_fail(self):
        for key in PERF.REQUIRED_PERFORMANCE_METRICS:
            for value in (None, float("nan"), float("inf"), -1, True, "1.0"):
                with self.subTest(key=key, value=value):
                    raw = native_result()
                    raw[key] = value
                    _, report = self.validate(raw)
                    self.assertTrue(any(key in error for error in report["errors"]))
            raw = native_result()
            del raw[key]
            _, report = self.validate(raw)
            self.assertTrue(any(key in error for error in report["errors"]))

    def test_oversized_counts_and_fractional_slo_count_are_invalid(self):
        raw = native_result()
        raw["total_input_tokens"] = 10**1000
        _, report = self.validate(raw)
        self.assertTrue(report["errors"])
        raw = native_result()
        raw["request_goodput"] = 0.5 / raw["duration"]
        _, report = PERF.validate_native_result(CASE, raw, PERF.extract_metrics(STDOUT),
                                                required_metrics=["request_goodput"], slo={"ttft": 100})
        self.assertTrue(any("integer request count" in error for error in report["errors"]))

    def test_single_token_output_has_explicit_unsupported_diagnostic(self):
        _, report = PERF.validate_native_result((10, 1, 2, 2), native_result(), {})
        self.assertTrue(any("output_len > 1" in error for error in report["errors"]))

    def test_counts_only_result_cannot_produce_summary(self):
        raw = native_result()
        for key in PERF.REQUIRED_PERFORMANCE_METRICS:
            del raw[key]
        with tempfile.TemporaryDirectory() as directory:
            def benchmark(cmd, **kwargs):
                path = Path(cmd[cmd.index("--result-dir") + 1]) / cmd[cmd.index("--result-filename") + 1]
                path.write_text(json.dumps(raw), encoding="utf-8")
                return subprocess.CompletedProcess(cmd, 0, STDOUT, "")

            csv_path = Path(directory) / "rounds.csv"
            with patch.object(PERF.subprocess, "run", side_effect=benchmark), \
                    contextlib.redirect_stdout(io.StringIO()):
                summary, failed = PERF.run_test_case(CASE, str(csv_path), directory, ["vllm"])
            self.assertIsNone(summary)
            self.assertTrue(failed)
            self.assertNotIn("SUMMARY", csv_path.read_text())
            reports = [json.loads(path.read_text()) for path in Path(directory).glob("*.validation.json")]
            self.assertEqual(len(reports), PERF.RUNS)
            self.assertTrue(all(not report["valid"] and report["errors"] for report in reports))

    def test_legacy_run_uses_json_metrics_without_requiring_stdout_metric_labels(self):
        with tempfile.TemporaryDirectory() as directory:
            def benchmark(cmd, **kwargs):
                self.assertEqual(cmd[cmd.index("--percentile-metrics") + 1], "ttft,tpot,itl")
                self.assertEqual(cmd[cmd.index("--metric-percentiles") + 1], "99")
                path = Path(cmd[cmd.index("--result-dir") + 1]) / cmd[cmd.index("--result-filename") + 1]
                path.write_text(json.dumps(native_result(legacy=True)), encoding="utf-8")
                return subprocess.CompletedProcess(cmd, 0, STDOUT, "")

            with patch.object(PERF.subprocess, "run", side_effect=benchmark), \
                    contextlib.redirect_stdout(io.StringIO()):
                metrics = PERF.run_once(CASE, 1, directory, ["vllm"])
            self.assertTrue(metrics["valid"])
            self.assertEqual(metrics["p99_itl_ms"], 6.1)


if __name__ == "__main__":
    unittest.main()
