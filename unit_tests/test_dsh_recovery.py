"""Recovery decisions reject duplicate execution and false success; no SSH is run."""
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / 'scripts/dsh_recovery.py'
SPEC = importlib.util.spec_from_file_location('dsh_recovery', SCRIPT)
RECOVERY = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(RECOVERY)


def snapshot(**changes):
    value = dict(schema_version=1, task_id='trace-analysis-one', automation_allowed=True,
                 binding_verified=True, observation_verified=True, remote_state='exited',
                 writers_stopped=True, failure_class='transient_api', exit_code=1,
                 final_event='error', result_verified=False, progress_verified=False,
                 soft_deadline_exceeded=False, hard_deadline_exceeded=False,
                 recoveries_used=0, same_error_count=1, max_recoveries=2,
                 session_id=None, resume_supported=False, checkpoint_verified=False,
                 side_effects='none')
    value.update(changes)
    return value


class RecoveryTest(unittest.TestCase):
    def action(self, **changes):
        return RECOVERY.decide(snapshot(**changes))['action']

    def test_disconnect_does_not_start_duplicate_live_task(self):
        self.assertEqual(self.action(remote_state='running', writers_stopped=False,
                                    failure_class='transport', exit_code=None, final_event='none'), 'observe')
        self.assertEqual(self.action(remote_state='unknown', failure_class='transport'), 'reconcile')

    def test_soft_observation_timeout_with_progress_is_not_failure(self):
        self.assertEqual(self.action(remote_state='running', writers_stopped=False, exit_code=None,
                                    final_event='none', progress_verified=True,
                                    soft_deadline_exceeded=True), 'continue_within_budget')

    def test_no_progress_requests_inspection_not_immediate_kill(self):
        self.assertEqual(self.action(remote_state='running', writers_stopped=False, exit_code=None,
                                    final_event='none', soft_deadline_exceeded=True), 'inspect_stall')

    def test_hard_deadline_requires_stop_then_observation_before_replacement(self):
        self.assertEqual(self.action(remote_state='running', writers_stopped=False, exit_code=None,
                                    final_event='none', hard_deadline_exceeded=True), 'stop_then_reconcile')
        self.assertEqual(self.action(hard_deadline_exceeded=True), 'budget_exhausted')

    def test_zero_exit_code_with_error_or_controller_kill_is_not_success(self):
        for changes in [dict(final_event='error'), dict(final_event='completed', failure_class='controller_timeout')]:
            with self.subTest(changes=changes):
                self.assertNotEqual(self.action(exit_code=0, result_verified=True, **changes), 'accept')

    def test_supported_verified_session_is_resumed_instead_of_new_launch(self):
        self.assertEqual(self.action(session_id='session-one', checkpoint_verified=True,
                                    resume_supported=True, side_effects='checkpointed'), 'resume_existing')
        self.assertEqual(self.action(checkpoint_verified=True, resume_supported=True,
                                    side_effects='checkpointed'), 'fallback')

    def test_unknown_changes_or_live_child_blocks_replacement(self):
        self.assertEqual(self.action(side_effects='unknown'), 'reconcile')
        self.assertEqual(self.action(writers_stopped=False), 'reconcile')
        self.assertEqual(self.action(side_effects='checkpointed'), 'reconcile')
        self.assertEqual(self.action(side_effects='unknown', failure_class='none',
                                    exit_code=0, final_event='completed', result_verified=True), 'reconcile')

    def test_configuration_or_missing_executor_never_blindly_retries(self):
        for failure in ['unavailable', 'configuration', 'permission']:
            with self.subTest(failure=failure):
                self.assertEqual(self.action(failure_class=failure), 'fallback')

    def test_bounded_transient_retry_requires_no_effects(self):
        self.assertEqual(self.action(), 'retry_launch')
        self.assertEqual(self.action(recoveries_used=2), 'fallback')
        self.assertEqual(self.action(same_error_count=2), 'fallback')
        self.assertEqual(self.action(max_recoveries=0), 'fallback')

    def test_not_started_transport_error_may_retry_only_verified_empty_state(self):
        self.assertEqual(self.action(remote_state='not_started', exit_code=None,
                                    final_event='none', failure_class='transport'), 'retry_launch')
        self.assertEqual(self.action(remote_state='not_started', session_id='unexpected'), 'reconcile')

    def test_failed_test_is_not_executor_failure(self):
        self.assertEqual(self.action(failure_class='task_failure'), 'report_task_failure')

    def test_paused_changed_binding_and_unverified_observation_never_resume(self):
        self.assertEqual(self.action(automation_allowed=False), 'hold')
        self.assertEqual(self.action(binding_verified=False), 'reconcile')
        self.assertEqual(self.action(observation_verified=False), 'reconcile')

    def test_contradictory_running_state_cannot_be_retried(self):
        self.assertEqual(self.action(remote_state='running'), 'reconcile')
        self.assertEqual(self.action(remote_state='exited', exit_code=None), 'reconcile')

    def test_completed_evidence_is_collected_without_rerunning(self):
        self.assertEqual(self.action(failure_class='none', exit_code=0, final_event='completed'), 'collect_existing_result')
        self.assertEqual(self.action(failure_class='none', exit_code=0, final_event='completed',
                                    result_verified=True), 'accept')
        self.assertEqual(self.action(exit_code=0, final_event='error', result_verified=True), 'collect_existing_result')

    def test_completed_remote_task_is_collected_even_after_disconnect_and_limits(self):
        for failure in ['transport', 'transient_api']:
            for limits in [{}, dict(recoveries_used=2, same_error_count=2),
                           dict(hard_deadline_exceeded=True)]:
                with self.subTest(failure=failure, limits=limits):
                    self.assertEqual(self.action(failure_class=failure, exit_code=0,
                                                final_event='completed', **limits), 'collect_existing_result')
        self.assertEqual(self.action(failure_class='invalid_result', exit_code=0,
                                    final_event='completed'), 'fallback')
        self.assertEqual(self.action(failure_class='invalid_result', exit_code=0,
                                    final_event='completed', result_verified=True), 'reconcile')
        self.assertEqual(self.action(failure_class='none', exit_code=0, final_event='completed',
                                    result_verified=True, hard_deadline_exceeded=True,
                                    recoveries_used=2), 'accept')

    def test_existing_unverified_session_is_inspected_not_reopened(self):
        for failure in ['transport', 'transient_api', 'permission']:
            for recoveries in [0, 2]:
                with self.subTest(failure=failure, recoveries=recoveries):
                    self.assertEqual(self.action(session_id='session-existing',
                                                failure_class=failure, recoveries_used=recoveries), 'reconcile')

    def test_unverified_partial_changes_block_acceptance(self):
        for effects in ['unknown', 'checkpointed']:
            with self.subTest(effects=effects):
                self.assertEqual(self.action(side_effects=effects, failure_class='none',
                                            exit_code=0, final_event='completed',
                                            result_verified=True, checkpoint_verified=False), 'reconcile')

    def test_help_contains_a_complete_valid_snapshot_and_cli_example(self):
        result = subprocess.run([sys.executable, str(SCRIPT), '--help'], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0)
        for field in RECOVERY.FIELDS:
            self.assertIn('"' + field + '"', result.stdout)
        self.assertIn('--snapshot /absolute/path/snapshot.json', result.stdout)
        self.assertEqual(RECOVERY.decide(RECOVERY.EXAMPLE)['action'], 'retry_launch')

    def test_schema_rejects_missing_extra_nonfinite_and_wrong_types(self):
        bad = [snapshot(schema_version=True), snapshot(recoveries_used=True), snapshot(recoveries_used=-1),
               snapshot(max_recoveries=3), snapshot(same_error_count=float('nan')),
               snapshot(exit_code=False), snapshot(exit_code=float('nan')),
               snapshot(remote_state='guess'), snapshot(session_id=''), snapshot(task_id=' '),
               snapshot(progress_verified=1), snapshot(extra='ignored')]
        missing = snapshot(); missing.pop('writers_stopped'); bad.append(missing)
        for value in bad:
            with self.subTest(value=value), self.assertRaises(ValueError):
                RECOVERY.decide(value)

    def test_cli_rejects_invalid_or_duplicate_json_without_action(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'snapshot.json'
            for content in ['{"task_id":"one","task_id":"two"}', '{"bad":NaN}', json.dumps(snapshot(recoveries_used=True))]:
                path.write_text(content)
                result = subprocess.run([sys.executable, str(SCRIPT), '--snapshot', str(path)],
                                        capture_output=True, text=True)
                self.assertEqual(result.returncode, 2)
                self.assertEqual(json.loads(result.stdout)['action'], 'invalid_snapshot')
            path.write_text(json.dumps(snapshot()))
            result = subprocess.run([sys.executable, str(SCRIPT), '--snapshot', str(path)], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0)
            self.assertEqual(json.loads(result.stdout)['action'], 'retry_launch')


if __name__ == '__main__':
    unittest.main()
