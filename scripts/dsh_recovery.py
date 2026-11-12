#!/usr/bin/env python3
"""Recommend one recovery action from caller-verified facts; never execute it."""
from __future__ import annotations

import argparse
import json
from pathlib import Path


BOOLEAN_FIELDS = (
    'automation_allowed', 'binding_verified', 'observation_verified', 'writers_stopped',
    'result_verified', 'progress_verified', 'soft_deadline_exceeded',
    'hard_deadline_exceeded', 'resume_supported', 'checkpoint_verified',
)
ENUM_FIELDS = {
    'remote_state': {'not_started', 'running', 'exited', 'unknown'},
    'failure_class': {'none', 'transport', 'transient_api', 'controller_timeout',
                      'executor_error', 'unavailable', 'configuration', 'permission',
                      'invalid_result', 'task_failure'},
    'final_event': {'none', 'completed', 'error'},
    'side_effects': {'none', 'checkpointed', 'unknown'},
}
INTEGER_FIELDS = ('recoveries_used', 'same_error_count', 'max_recoveries')
FIELDS = {'schema_version', 'task_id', 'exit_code', 'session_id',
          *BOOLEAN_FIELDS, *ENUM_FIELDS, *INTEGER_FIELDS}
EXAMPLE = dict(
    schema_version=1, task_id='trace-analysis-one', automation_allowed=True,
    binding_verified=True, observation_verified=True, remote_state='exited',
    writers_stopped=True, failure_class='transient_api', exit_code=1,
    final_event='error', result_verified=False, progress_verified=False,
    soft_deadline_exceeded=False, hard_deadline_exceeded=False,
    recoveries_used=0, same_error_count=1, max_recoveries=2,
    session_id=None, resume_supported=False, checkpoint_verified=False,
    side_effects='none',
)


def validate(snapshot):
    """Require explicit facts: missing, misspelled and ill-typed values fail closed."""
    if not isinstance(snapshot, dict) or set(snapshot) != FIELDS:
        raise ValueError('snapshot must contain exactly the schema 1 fields')
    if type(snapshot['schema_version']) is not int or snapshot['schema_version'] != 1:
        raise ValueError('schema_version must be integer 1')
    if not isinstance(snapshot['task_id'], str) or not snapshot['task_id'].strip():
        raise ValueError('task_id must be a nonempty string')
    for field in BOOLEAN_FIELDS:
        if type(snapshot[field]) is not bool:
            raise ValueError(f'{field} must be boolean')
    for field, choices in ENUM_FIELDS.items():
        if not isinstance(snapshot[field], str) or snapshot[field] not in choices:
            raise ValueError(f'invalid {field}')
    for field in INTEGER_FIELDS:
        if type(snapshot[field]) is not int or snapshot[field] < 0:
            raise ValueError(f'{field} must be a nonnegative integer')
    if snapshot['max_recoveries'] > 2:
        raise ValueError('max_recoveries cannot exceed 2')
    if snapshot['exit_code'] is not None and type(snapshot['exit_code']) is not int:
        raise ValueError('exit_code must be integer or null')
    if snapshot['session_id'] is not None and (
        not isinstance(snapshot['session_id'], str) or not snapshot['session_id'].strip()
    ):
        raise ValueError('session_id must be nonempty string or null')


def decide(snapshot):
    """Return a recommendation, not a process check, native gate or authorization."""
    validate(snapshot)
    s = snapshot

    def answer(action, reason):
        return dict(schema_version=1, task_id=s['task_id'], action=action, reason=reason)

    if not s['automation_allowed']:
        return answer('hold', 'Human control prohibits new automated execution.')
    if not s['binding_verified'] or not s['observation_verified']:
        return answer('reconcile', 'Verify current task binding and remote observation first.')
    state = s['remote_state']
    if state == 'unknown':
        return answer('reconcile', 'Transport loss does not establish remote execution state.')
    if state == 'running':
        if s['writers_stopped'] or s['exit_code'] is not None or s['final_event'] != 'none':
            return answer('reconcile', 'Running process conflicts with stopped/terminal facts.')
        if s['hard_deadline_exceeded']:
            return answer('stop_then_reconcile', 'Total task budget expired; caller must stop only its verified execution and recheck children.')
        if s['progress_verified'] and s['soft_deadline_exceeded']:
            return answer('continue_within_budget', 'Verified progress permits continued observation within the frozen total budget.')
        if s['soft_deadline_exceeded']:
            return answer('inspect_stall', 'Inspect real progress and child activity; do not infer failure from elapsed observation time.')
        return answer('observe', 'Execution is still running; reconnect/observe it instead of launching a replacement.')
    if state == 'not_started' and (
        s['exit_code'] is not None or s['final_event'] != 'none'
        or s['session_id'] is not None or s['checkpoint_verified']
        or s['progress_verified'] or s['result_verified'] or s['side_effects'] != 'none'
    ):
        return answer('reconcile', 'Not-started state conflicts with evidence of execution.')
    if state == 'exited' and s['exit_code'] is None:
        return answer('reconcile', 'Read the remote exit receipt; a disconnected SSH client has no remote exit code.')
    if not s['writers_stopped']:
        return answer('reconcile', 'Confirm old execution and task child writers stopped before any replacement.')
    if s['failure_class'] == 'task_failure':
        return answer('report_task_failure', 'Preserve the failed workload/test evidence; changing executor cannot turn it into a pass.')
    if s['side_effects'] == 'unknown':
        return answer('reconcile', 'Inspect partial changes before accepting, resuming or replacing execution.')
    if s['side_effects'] == 'checkpointed' and not s['checkpoint_verified']:
        return answer('reconcile', 'Claimed partial-work checkpoint has not been verified.')
    if s['failure_class'] == 'invalid_result' and s['result_verified']:
        return answer('reconcile', 'Result cannot be both verified and explicitly invalid; inspect the conflicting evidence.')
    if state == 'exited' and s['result_verified']:
        if s['exit_code'] == 0 and s['final_event'] == 'completed' and s['failure_class'] == 'none':
            return answer('accept', 'Caller verified results and normal completion; this does not replace native acceptance gates.')
        return answer('collect_existing_result', 'Preserve verified artifacts despite incomplete/error termination; reconcile completion before acceptance.')
    if (state == 'exited' and s['exit_code'] == 0 and s['final_event'] == 'completed'
            and s['failure_class'] in {'none', 'transport', 'transient_api'}):
        return answer('collect_existing_result', 'Remote completion survives a later transport error; verify existing artifacts instead of rerunning work.')
    if s['hard_deadline_exceeded']:
        return answer('budget_exhausted', 'Do not reset the total budget by retrying or switching executor; replan the remaining work.')
    if s['session_id'] and not s['checkpoint_verified']:
        return answer('reconcile', 'Inspect the existing session and its artifacts before any new attempt or replacement.')
    if s['failure_class'] in {'unavailable', 'configuration', 'permission'}:
        return answer('fallback', 'Static executor/configuration/permission failure; preserve scope and permissions in the replacement.')
    if s['recoveries_used'] >= s['max_recoveries'] or s['same_error_count'] >= 2:
        return answer('fallback', 'Recovery allowance exhausted or the same error repeated twice; retain verified partial work.')
    if s['failure_class'] in {'transport', 'transient_api', 'controller_timeout', 'executor_error'}:
        if state == 'exited' and s['checkpoint_verified'] and s['resume_supported'] and s['session_id']:
            return answer('resume_existing', 'Resume only the verified existing session/checkpoint with unchanged binding and remaining budget.')
        if s['failure_class'] in {'transport', 'transient_api'} and s['side_effects'] == 'none' and not s['checkpoint_verified']:
            return answer('retry_launch', 'Transient failure with verified absence of side effects permits one bounded new attempt.')
        return answer('fallback', 'No safe supported session recovery; transfer verified state without replaying completed work.')
    if s['failure_class'] == 'invalid_result':
        return answer('fallback', 'Results are unusable after verification; transfer the bounded task and valid partial evidence.')
    if state == 'exited' and s['exit_code'] == 0 and s['final_event'] != 'error':
        return answer('collect_existing_result', 'Inspect existing outputs before restarting work; process success alone is not result validity.')
    return answer('reconcile', 'Failure facts do not establish a safe recovery class; inspect before taking action.')


def _object(pairs):
    value = {}
    for key, item in pairs:
        if key in value:
            raise ValueError(f'duplicate JSON key: {key}')
        value[key] = item
    return value


def _constant(value):
    raise ValueError(f'nonfinite JSON value: {value}')


def main(argv=None):
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=('Every schema 1 field is required; unknown fields are rejected.\n'
                'The caller must verify these facts; this tool only recommends an action.\n'
                'Full snapshot example (recommends retry_launch):\n'
                + json.dumps(EXAMPLE, indent=2)
                + '\n\nUsage: python3 scripts/dsh_recovery.py --snapshot /absolute/path/snapshot.json'),
    )
    parser.add_argument('--snapshot', type=Path, required=True, help='absolute path to caller-verified schema 1 JSON')
    args = parser.parse_args(argv)
    try:
        if not args.snapshot.is_absolute():
            raise ValueError('snapshot path must be absolute')
        snapshot = json.loads(args.snapshot.read_text(encoding='utf-8'),
                              object_pairs_hook=_object, parse_constant=_constant)
        result = decide(snapshot)
    except (OSError, UnicodeError, ValueError) as error:
        print(json.dumps(dict(schema_version=1, action='invalid_snapshot', reason=str(error)), ensure_ascii=False))
        return 2
    print(json.dumps(result, ensure_ascii=False, allow_nan=False))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
