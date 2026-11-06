"""Cancellation regressions without lm-eval, model requests or accelerator use."""
import contextlib
import io
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
import time
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "evaluation/accuracy"))
import acceptance
import formal_accuracy
import llmrun
import llmrun_parallel
import process_control
import test_acceptance as fixtures


class InterruptedOutput(io.StringIO):
    def __next__(self):
        raise KeyboardInterrupt


def child(return_code=0, interrupted=False):
    process = Mock(pid=123456)
    process.stdout = InterruptedOutput() if interrupted else io.StringIO("")
    process.poll.return_value = None
    process.wait.return_value = return_code
    return process


class AccuracyCancellationTest(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.real_group_exists = process_control._group_exists
        # Mocked Popen handles have no real process groups. The integration
        # tests run the unpatched helper in a separate local Python process.
        groups = patch.object(process_control, "_group_exists", return_value=False)
        groups.start()
        self.addCleanup(groups.stop)

    def test_formal_cancellation_never_retries_or_publishes_completed_record(self):
        fixture = fixtures.GateTest("test_original_runner_unchanged")
        fixture.setUp()
        self.addCleanup(fixture.doCleanups)
        cfg = dict(fixture.cfg, output_root=str(self.root / "outputs"),
                   eval_max_retries=1, retry_delay=0, progress_score_interval=0)
        config = self.root / "input.json"
        config.write_text(json.dumps(cfg))
        args = SimpleNamespace(config=config, contract=fixture.root / "contract.json",
            service_manifest=fixture.root / "service.json",
            evaluation_inspect=fixture.root / "evaluation_inspect.json",
            preflight_only=False, capture_provenance=None)
        runner = formal_accuracy.load_runner()
        process = child(interrupted=True)  # Child may handle SIGINT and exit 0.
        with patch.object(formal_accuracy, "load_runner", return_value=runner), \
             patch.object(formal_accuracy, "collect_provenance", return_value=fixture.provenance), \
             patch.object(runner, "configure_environment"), \
             patch.object(runner, "probe_service", return_value=(True, "synthetic")), \
             patch.object(runner, "build_command", return_value=["lm_eval"]), \
             patch.object(runner, "report_result") as report, \
             patch.object(process_control.subprocess, "Popen", return_value=process) as launch, \
             patch.object(process_control.os, "killpg") as send_signal, \
             contextlib.redirect_stdout(io.StringIO()), self.assertRaises(KeyboardInterrupt):
            formal_accuracy.run(args)
        self.assertEqual(launch.call_count, 1)
        report.assert_not_called()
        send_signal.assert_called_once_with(process.pid, signal.SIGINT)
        self.assertTrue(process.stdout.closed)
        self.assertEqual(list((self.root / "outputs").rglob("run-record.json")), [])
        self.assertEqual(acceptance.sha256(formal_accuracy.RUNNER), acceptance.RUNNER_SHA256)

    def test_normal_failure_still_retries_in_all_entrypoints(self):
        original = formal_accuracy.load_runner()
        original.run_streaming = process_control.run_streaming
        for name, runner in (("formal", original), ("maintained", llmrun),
                             ("parallel", llmrun_parallel)):
            with self.subTest(entrypoint=name):
                output = self.root / name
                output.mkdir()
                cfg = dict(eval_max_retries=1, retry_delay=0, progress_score_interval=0,
                           progress_interval=0, limit=0, task="synthetic", eval_model="fixture",
                           output_root=str(output))
                build = "build_shard_command" if name == "parallel" else "build_command"
                validate = "validate_shard" if name == "parallel" else "report_result"
                with patch.object(runner, build, return_value=["synthetic-command"]), \
                     patch.object(runner, "probe_service", return_value=(True, "synthetic")), \
                     patch.object(runner, validate, return_value=True), \
                     patch.object(process_control.subprocess, "Popen", side_effect=[child(1), child(0)]) as launch, \
                     contextlib.redirect_stdout(io.StringIO()):
                    result = (runner.run_shard(cfg, 0, "model", "unused") if name == "parallel"
                              else runner.run_task(cfg, "synthetic", output))
                self.assertTrue(result)
                self.assertEqual(launch.call_count, 2)

    def test_maintained_and_sharded_cancellation_do_not_retry(self):
        for name, runner in (("maintained", llmrun), ("parallel", llmrun_parallel)):
            with self.subTest(entrypoint=name):
                output = self.root / name
                output.mkdir()
                cfg = dict(eval_max_retries=1, retry_delay=0, progress_score_interval=0,
                           progress_interval=0, limit=0, task="synthetic", eval_model="fixture",
                           output_root=str(output))
                build = "build_shard_command" if name == "parallel" else "build_command"
                with patch.object(runner, build, return_value=["synthetic-command"]), \
                     patch.object(process_control.subprocess, "Popen", return_value=child(interrupted=True)) as launch, \
                     patch.object(process_control.os, "killpg"), \
                     contextlib.redirect_stdout(io.StringIO()), self.assertRaises(KeyboardInterrupt):
                    if name == "parallel":
                        runner.run_shard(cfg, 0, "model", "unused")
                    else:
                        runner.run_task(cfg, "synthetic", output)
                self.assertEqual(launch.call_count, 1)

    def test_cancel_cleans_evaluator_and_sidecar_and_escalates_if_needed(self):
        process = child(interrupted=True)
        process.wait.side_effect = [subprocess.TimeoutExpired("synthetic", 5),
                                    subprocess.TimeoutExpired("synthetic", 5), 0]
        sidecar = child()
        sidecar.pid += 1
        with patch.object(process_control.subprocess, "Popen", side_effect=[process, sidecar]), \
             patch.object(process_control.os, "killpg") as send_signal, \
             self.assertRaises(KeyboardInterrupt):
            process_control.run_streaming(["synthetic"], self.root / "run.log", ["sidecar"])
        signals = [call.args for call in send_signal.call_args_list]
        self.assertIn((sidecar.pid, signal.SIGINT), signals)
        self.assertEqual([sig for pid, sig in signals if pid == process.pid],
                         [signal.SIGINT, signal.SIGTERM, signal.SIGKILL])
        sidecar.wait.assert_called()
        self.assertTrue(process.stdout.closed)

    def test_interrupted_child_exit_code_is_not_a_retryable_failure(self):
        for sig in (signal.SIGINT, signal.SIGTERM):
            with self.subTest(signal=sig), \
                 patch.object(process_control.subprocess, "Popen", return_value=child(-sig)), \
                 patch.object(process_control.os, "killpg"), self.assertRaises(KeyboardInterrupt):
                process_control.run_streaming(["synthetic"], self.root / "run.log")

    def test_shared_cancellation_blocks_new_processes_and_retry_delays(self):
        cancellation = process_control.Cancellation()
        cancellation.cancel()
        with patch.object(process_control.subprocess, "Popen") as launch:
            with self.assertRaises(KeyboardInterrupt):
                cancellation.start(["synthetic"])
            with self.assertRaises(KeyboardInterrupt):
                cancellation.sleep(3600)
        launch.assert_not_called()

    def test_sigint_between_process_creation_and_registration_is_cleaned(self):
        process = child()

        def launch(*args, **kwargs):
            # Popen has created its child but has not returned the handle yet.
            os.kill(os.getpid(), signal.SIGINT)
            return process

        previous_handler = signal.getsignal(signal.SIGINT)
        with patch.object(process_control.subprocess, "Popen", side_effect=launch) as popen, \
             patch.object(process_control.os, "killpg") as send_signal, \
             self.assertRaises(KeyboardInterrupt):
            process_control.run_streaming(["synthetic"], self.root / "run.log")
        self.assertEqual(popen.call_count, 1)
        send_signal.assert_called_once_with(process.pid, signal.SIGINT)
        process.wait.assert_called()
        self.assertTrue(process.stdout.closed)
        self.assertIs(signal.getsignal(signal.SIGINT), previous_handler)

    def test_permission_denied_probe_requires_later_proof_of_group_exit(self):
        with patch.object(process_control.os, "killpg", side_effect=[
                PermissionError("transient liveness permission"), ProcessLookupError()]):
            self.assertTrue(self.real_group_exists(child()))
            self.assertFalse(self.real_group_exists(child()))

    def test_persistent_permission_denied_probes_cannot_claim_cleanup(self):
        def signal_or_probe(pid, sig):
            if sig == 0:
                raise PermissionError("cannot verify group exit")

        with patch.object(process_control, "_group_exists", self.real_group_exists), \
             patch.object(process_control.os, "killpg", side_effect=signal_or_probe) as signals, \
             patch.object(process_control.time, "monotonic", side_effect=range(0, 100, 6)), \
             self.assertRaises(subprocess.TimeoutExpired):
            process_control._reap(child())
        self.assertEqual([call.args[1] for call in signals.call_args_list],
                         [0, signal.SIGTERM, 0, signal.SIGKILL, 0])

    def test_permission_denied_sending_a_real_signal_remains_an_error(self):
        with patch.object(process_control.os, "killpg", side_effect=PermissionError("denied")), \
             self.assertRaises(PermissionError):
            process_control._signal_group(child(), signal.SIGTERM)

    @unittest.skipUnless(os.name == "posix", "process-group cancellation uses POSIX signals")
    def test_real_parallel_ctrl_c_cleans_all_children_before_executor_shutdown(self):
        # Only local sleeping Python processes are launched. No evaluator or API.
        harness = '''
import sys
from pathlib import Path
sys.path.insert(0, sys.argv[1])
import llmrun_parallel as runner
root = Path(sys.argv[2])
cfg = dict(eval_max_retries=1, retry_delay=0, progress_score_interval=0,
           progress_interval=0, limit=0, task="synthetic", eval_model="fixture",
           output_root=str(root), shards=[0, 1])
def command(cfg, model, url, shard, output):
    return [sys.executable, "-c", "import os,sys,time; from pathlib import Path; Path(sys.argv[1]).write_text(str(os.getpid())); time.sleep(60)", str(root / f"child-{shard}.pid")]
runner.build_shard_command = command
try:
    runner.run_shards(cfg, [("a", "unused"), ("b", "unused")])
except KeyboardInterrupt:
    print("CANCELLED", flush=True)
    sys.exit(130)
raise SystemExit("unexpected successful completion")
'''
        controller = subprocess.Popen([sys.executable, "-c", harness,
            str(ROOT / "evaluation/accuracy"), str(self.root)], stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT, text=True, start_new_session=True)
        children = []
        try:
            deadline = time.monotonic() + 10
            pid_files = [self.root / f"child-{i}.pid" for i in range(2)]
            while not all(path.is_file() and path.stat().st_size for path in pid_files):
                if controller.poll() is not None or time.monotonic() > deadline:
                    self.fail("parallel fixture did not start both local children")
                time.sleep(0.02)
            children = [int(path.read_text()) for path in pid_files]
            controller.send_signal(signal.SIGINT)
            output, _ = controller.communicate(timeout=10)
            self.assertEqual(controller.returncode, 130, output)
            self.assertIn("CANCELLED", output)
            self.assertNotIn("attempt 2", output)
            for pid in children:
                with self.assertRaises(ProcessLookupError):
                    os.kill(pid, 0)
        finally:
            if controller.poll() is None:
                controller.kill()
            controller.communicate(timeout=5)
            for path in self.root.glob("child-*.pid"):
                if path.stat().st_size:
                    try:
                        os.killpg(int(path.read_text()), signal.SIGKILL)
                    except ProcessLookupError:
                        pass

    @unittest.skipUnless(os.name == "posix", "process-group cancellation uses POSIX signals")
    def test_cancel_reaps_group_when_leader_exits_but_descendant_ignores_signals(self):
        grandchild = '''
import os, signal, sys, time
from pathlib import Path
signal.signal(signal.SIGINT, signal.SIG_IGN)
signal.signal(signal.SIGTERM, signal.SIG_IGN)
Path(sys.argv[1]).write_text(str(os.getpid()))
time.sleep(60)
'''
        leader = '''
import os, signal, subprocess, sys, time
from pathlib import Path
signal.signal(signal.SIGINT, lambda *args: sys.exit(0))
Path(sys.argv[1]).write_text(str(os.getpid()))
# Inherit stdout: leaving this descendant alive would also hold the pipe open.
subprocess.Popen([sys.executable, "-c", sys.argv[3], sys.argv[2]])
time.sleep(60)
'''
        harness = '''
import sys
from pathlib import Path
sys.path.insert(0, sys.argv[1])
from process_control import run_streaming
root = Path(sys.argv[2])
try:
    run_streaming([sys.executable, "-c", sys.argv[3], str(root / "leader.pid"),
                   str(root / "grandchild.pid"), sys.argv[4]], root / "run.log")
except KeyboardInterrupt:
    print("CANCELLED", flush=True)
    sys.exit(130)
raise SystemExit("unexpected successful completion")
'''
        controller = subprocess.Popen([sys.executable, "-c", harness,
            str(ROOT / "evaluation/accuracy"), str(self.root), leader, grandchild],
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, start_new_session=True)
        try:
            pid_files = [self.root / name for name in ("leader.pid", "grandchild.pid")]
            deadline = time.monotonic() + 10
            while not all(path.is_file() and path.stat().st_size for path in pid_files):
                if controller.poll() is not None or time.monotonic() > deadline:
                    self.fail("descendant fixture did not reach readiness")
                time.sleep(0.02)
            leader_pid, grandchild_pid = [int(path.read_text()) for path in pid_files]
            controller.send_signal(signal.SIGINT)
            output, _ = controller.communicate(timeout=20)
            self.assertEqual(controller.returncode, 130, output)
            self.assertIn("CANCELLED", output)
            with self.assertRaises(ProcessLookupError):
                os.killpg(leader_pid, 0)
            with self.assertRaises(ProcessLookupError):
                os.kill(grandchild_pid, 0)
        finally:
            # Also covers a regression that leaves stdout open and times out.
            leader_file = self.root / "leader.pid"
            if leader_file.is_file() and leader_file.stat().st_size:
                try:
                    os.killpg(int(leader_file.read_text()), signal.SIGKILL)
                except ProcessLookupError:
                    pass
            if controller.poll() is None:
                controller.kill()
            controller.communicate(timeout=5)


if __name__ == "__main__":
    unittest.main()
