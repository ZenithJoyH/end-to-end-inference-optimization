"""Model wrapper contract tests; subprocesses are synthetic, with no device use."""

import contextlib
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
    "model_perf_wrapper", ROOT / "models/XingChen4-29B-A4B/ppu/optimize/tools/standard_perf.py"
)
WRAPPER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(WRAPPER)
SOURCE = ROOT / "test/perf_test/vllm_perf.py"


class ModelPerfWrapperTest(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.output = Path(self.temporary.name) / "new-output"
        self.argv = [
            "--runner", str(SOURCE), "--model", "test-model", "--tokenizer", "/external/tokenizer",
            "--host", "127.0.0.1", "--port", "18000", "--max-model-len", "100000",
            "--output-dir", str(self.output), "--service-manifest", "/external/service.json",
            "--performance-only",
        ]

    def test_known_source_matrix_and_historical_rounds_are_preserved(self):
        plan = WRAPPER.build_plan(WRAPPER.parser().parse_args(self.argv))
        cases = [(case["input_tokens"], case["output_tokens"], case["concurrency"], case["requests"]) for case in plan["cases"]]
        self.assertEqual(cases, [
            (1024, 1024, 64, 128), (4096, 1024, 64, 128),
            (16384, 1024, 64, 128), (32768, 1024, 64, 128), (65536, 1024, 64, 128),
        ])
        self.assertEqual((plan["measurement"]["warmup_rounds"], plan["measurement"]["measured_rounds"]), (1, 2))
        self.assertEqual(plan["generation"]["seed"], 42)
        self.assertEqual(plan["generation"]["temperature"], 0)
        self.assertTrue(plan["generation"]["ignore_eos"])
        self.assertTrue(plan["target"]["trust_remote_code"])
        self.assertTrue(all(case["load_mode"] == "finite_batch" and case["request_rate"] is None for case in plan["cases"]))

    def test_historical_supplemental_workload_and_source_order(self):
        args = WRAPPER.parser().parse_args(self.argv + [
            "--input-lengths", "16384", "4096", "--output-length", "256",
            "--concurrency", "32", "--requests", "32",
        ])
        cases = WRAPPER.build_plan(args)["cases"]
        self.assertEqual([(case["input_tokens"], case["output_tokens"], case["concurrency"], case["requests"]) for case in cases], [
            (4096, 256, 32, 32), (16384, 256, 32, 32),
        ])

    def test_unknown_or_oversized_workloads_fail_before_shared_runner(self):
        for extra in (["--input-lengths", "999"], ["--output-length", "0"], ["--requests", "-1"],
                      ["--concurrency", "0"], ["--max-model-len", "2047"]):
            with self.subTest(extra=extra), patch.object(WRAPPER.subprocess, "run") as run, \
                    contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
                WRAPPER.main(self.argv + extra)
            run.assert_not_called()
            self.assertFalse(self.output.exists())

    def test_unknown_runner_is_not_executed(self):
        marker = Path(self.temporary.name) / "should-not-exist"
        unknown = Path(self.temporary.name) / "unknown.py"
        unknown.write_text(f"from pathlib import Path\nPath({str(marker)!r}).touch()\nDEFAULT_TEST_CASES = [(1, 1, 1, 1)]\n")
        with self.assertRaisesRegex(ValueError, "SHA"):
            WRAPPER.read_source_cases(unknown)
        self.assertFalse(marker.exists())

    def test_scope_and_gate_cannot_be_mixed_or_reused_for_revert(self):
        formal = [value for value in self.argv if value != "--performance-only"]
        for argv in (formal, self.argv + ["--accuracy-gate", "/external/gate.json"],
                     formal + ["--accuracy-gate", "/external/gate.json", "--role", "revert"]):
            with self.subTest(argv=argv), patch.object(WRAPPER.subprocess, "run") as run, \
                    contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
                WRAPPER.main(argv)
            run.assert_not_called()

    def test_dry_run_delegates_validation_without_output_artifacts(self):
        result = subprocess.CompletedProcess([], 0, json.dumps({"effective_plan": {}, "commands": []}), "")
        with patch.object(WRAPPER.subprocess, "run", return_value=result) as run, contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(WRAPPER.main(self.argv + ["--dry-run"]), 0)
        self.assertEqual(run.call_count, 1)
        self.assertIn("--dry-run", run.call_args.args[0])
        self.assertFalse(self.output.exists())

    def test_plan_is_saved_before_execution_and_shared_failure_is_propagated(self):
        observed = []

        def execute(command, **kwargs):
            plan = json.loads(Path(command[command.index("--config") + 1]).read_text())
            observed.append(plan)
            if "--dry-run" in command:
                self.assertFalse(self.output.exists())
                return subprocess.CompletedProcess(command, 0, json.dumps({"effective_plan": plan, "commands": []}), "")
            self.assertTrue((self.output / "wrapper-plan.json").is_file())
            self.assertEqual(command[command.index("--scope") + 1], "performance_only")
            self.assertIn("--comparison-contract", command)
            return subprocess.CompletedProcess(command, 7)

        with patch.object(WRAPPER.subprocess, "run", side_effect=execute), contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(WRAPPER.main(self.argv + ["--comparison-contract", "/external/comparison.json"]), 7)
        self.assertEqual(observed[0], observed[1])
        metadata = json.loads((self.output / "wrapper-plan.json").read_text())
        self.assertEqual(metadata["source_runner_sha256"], WRAPPER.SOURCE_RUNNER_SHA256)
        self.assertNotIn("formal_accuracy_passed", metadata)

    def test_shared_preflight_failure_leaves_no_output(self):
        result = subprocess.CompletedProcess([], 2, "", "manifest does not match\n")
        with patch.object(WRAPPER.subprocess, "run", return_value=result) as run, \
                contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(WRAPPER.main(self.argv), 2)
        self.assertEqual(run.call_count, 1)
        self.assertFalse(self.output.exists())

    def test_existing_output_is_not_overwritten(self):
        self.output.mkdir()
        marker = self.output / "previous-result"
        marker.write_text("keep")
        with patch.object(WRAPPER.subprocess, "run") as run, contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
            WRAPPER.main(self.argv)
        run.assert_not_called()
        self.assertEqual(marker.read_text(), "keep")

    def test_mismatched_acceptance_tools_is_rejected(self):
        args = WRAPPER.parser().parse_args(self.argv + ["--acceptance-tools", self.temporary.name])
        with self.assertRaisesRegex(ValueError, "sibling"):
            WRAPPER.shared_runner(args)


if __name__ == "__main__":
    unittest.main()
