#!/usr/bin/env python3
"""Caller-owned execution journal and native evidence gates; no workload launcher."""
from __future__ import annotations

import argparse
from contextlib import contextmanager
import fcntl
import hashlib
import json
import math
import os
from pathlib import Path
import tempfile
import time
import uuid

from skill_bundle import inspect_bundle, validate_selection, verify_bundle
from project_gates import validate_check, run_check, source_files, validate_plan, output_files

ROOT = Path(__file__).resolve().parents[1]


def read(path):
    return json.loads(Path(path).read_text())


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write(path, value):
    path = Path(path)
    with tempfile.NamedTemporaryFile('w', dir=path.parent, delete=False, encoding='utf-8') as f:
        json.dump(value, f, ensure_ascii=False, indent=2, allow_nan=False)
        f.write('\n')
        temporary = Path(f.name)
    temporary.replace(path)


@contextmanager
def locked(directory):
    with (Path(directory) / '.lock').open('a') as handle:
        fcntl.flock(handle, fcntl.LOCK_EX)
        yield


def absolute_file(value):
    if not isinstance(value, (str, Path)):
        raise ValueError('existing absolute evidence file required')
    path = Path(value)
    if not path.is_absolute() or not path.is_file():
        raise ValueError(f'expected existing absolute file: {value}')
    return str(path.resolve())


def verify_context(record):
    for path, expected in {**record['context'], **record.get('completed_evidence', {})}.items():
        if sha(path) != expected:
            raise ValueError(f'context changed; revalidate, do not refresh hashes: {path}')
    verify_bundle(record['skill_dir'], record['bundle'])


def checks(spec, phase):
    result = []
    for check in spec[phase]:
        value = run_check(ROOT, check, spec['scope'])
        result.append(value)
        if value['status'] != 'passed':
            raise ValueError(f"native {phase} check did not pass: {value}")
    return result


def claim(record, release=False):
    spec = record['spec']
    resources = spec.get('resources', [])
    if not resources:
        return
    registry = Path(spec['lease_registry'])
    registry.mkdir(parents=True, exist_ok=True)
    with locked(registry):
        path = registry / 'claims.json'
        claims = read(path) if path.exists() else {}
        for resource in resources:
            owner = claims.get(resource)
            if owner and owner['token'] != record['token']:
                raise ValueError(f'resource already claimed: {resource}; owner={owner["run_id"]}')
        for resource in resources:
            if release:
                claims.pop(resource, None)
            else:
                claims[resource] = {'token': record['token'], 'run_id': spec['run_id'],
                                    'owner': spec['owner'], 'run_dir': record['run_dir']}
        write(path, claims)


def begin(spec_path, directory):
    spec = read(spec_path)
    if spec.get('schema_version') != 1:
        raise ValueError('unsupported run specification')
    for key in ('run_id', 'owner', 'capability_id', 'selection'):
        if not isinstance(spec.get(key), str) or not spec[key].strip():
            raise ValueError(f'explicit {key} required')
    if not isinstance(spec.get('scope'), dict) or not spec['scope']:
        raise ValueError('explicit target scope required')
    if not isinstance(spec.get('context_files'), list) or not spec['context_files']:
        raise ValueError('freeze service/request/contract files in context_files')
    context = {absolute_file(p): sha(p) for p in spec['context_files']}
    for phase in ('before', 'after'):
        if not isinstance(spec.get(phase), list) or not spec[phase]:
            raise ValueError(f'at least one native {phase} gate required')
        for check in spec[phase]: validate_check(check)
    validate_plan(spec)
    for field in ('budget_seconds', 'stall_seconds'):
        value = spec.get(field, 0)
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value < 0:
            raise ValueError(f'{field} must be finite and nonnegative (0=unset)')
    resources = spec.get('resources', [])
    if not isinstance(resources, list) or any(not isinstance(x, str) or not x.strip() for x in resources):
        raise ValueError('resources must be exact, nonempty canonical resource IDs')
    if len(set(resources)) != len(resources):
        raise ValueError('duplicate resource IDs')
    if resources and not Path(spec.get('lease_registry', '')).is_absolute():
        raise ValueError('resource claims require an explicit shared absolute lease_registry')
    if not Path(spec['skill_dir']).is_absolute():
        raise ValueError('skill_dir must be absolute')
    skill_dir = Path(spec['skill_dir']).resolve()
    bundle = inspect_bundle(skill_dir)
    validate_selection(bundle, spec['selection'], spec['capability_id'])
    directory = Path(directory)
    if not directory.is_absolute():
        raise ValueError('run-dir must be an explicit approved absolute path')
    # A unique directory prevents accidental replay and evidence overwrite.
    directory.mkdir(parents=False, exist_ok=False)
    with locked(directory):
        now = time.time()
        record = {'schema_version': 1, 'spec': spec, 'run_dir': str(directory.resolve()),
                  'token': uuid.uuid4().hex, 'skill_dir': str(skill_dir), 'bundle': bundle,
                  'context': context, 'started_at': now, 'last_progress_at': now,
                  'completed_units': 0, 'observations': [], 'state': 'preflight',
                  'implementation': {str(p): sha(p) for p in
                      [Path(__file__).resolve(), Path(__file__).with_name('project_gates.py').resolve(),
                       Path(__file__).with_name('skill_bundle.py').resolve()]}}
        record['context'].update(record['implementation'])
        record['context'].update({str(p.resolve()): sha(p) for p in source_files(ROOT)})
        write(directory / 'run.json', record)
        try:
            claim(record)
            record['before_results'] = checks(spec, 'before')
            verify_context(record)
            record['state'] = 'ready'
        except Exception as exc:
            record['state'] = 'preflight_failed'
            record['reason'] = str(exc)
            # No workload is launched by begin, so its own acquired claims are safe
            # to release. A conflicting owner's claims are never removed.
            try: claim(record, release=True)
            except ValueError: pass
            write(directory / 'run.json', record)
            raise
        write(directory / 'run.json', record)
        return record


def decision(record, now=None):
    now = time.time() if now is None else now
    reasons = []
    try: verify_context(record)
    except (OSError, ValueError) as exc: reasons.append(str(exc))
    if record['state'] == 'verified' and not reasons:
        try: checks(record['spec'], 'after')
        except Exception as exc: reasons.append(f'native evidence no longer verifies: {exc}')
    spec = record['spec']
    if record['state'] == 'preflight':
        reasons.append('preflight_interrupted: inspect the owner process; close this run before planning another')
    if record['state'] in ('ready', 'running'):
        if spec.get('budget_seconds', 0) and now - record['started_at'] >= spec['budget_seconds']:
            reasons.append('budget_exhausted: caller must stop or explicitly plan a new bounded run')
        if spec.get('stall_seconds', 0) and now - record['last_progress_at'] >= spec['stall_seconds']:
            reasons.append('progress_review_due: verify live progress before classifying a stall')
        errors = [x.get('error_signature') for x in record['observations'][-2:]]
        if len(errors) == 2 and errors[0] and errors[0] == errors[1]:
            reasons.append('repeated_error: isolate one hypothesis or change method before retrying')
    return {'status': 'incomplete' if reasons or record['state'] != 'verified' else 'passed',
            'state': record['state'], 'run_id': spec['run_id'], 'scope': spec['scope'],
            'completed_units': record['completed_units'], 'review_reasons': reasons,
            'last_observation': record['observations'][-1:]}


def update(directory, operation, *, evidence=None, completed=None, error=None, note=None):
    directory = Path(directory)
    with locked(directory):
        path = directory / 'run.json'
        record = read(path)
        if operation == 'check': return decision(record)
        if operation == 'release':
            if record['state'] not in ('verified', 'failed', 'preflight_failed'):
                raise ValueError('close the run before releasing resource ownership')
            proof = absolute_file(evidence)
            if not note or not Path(proof).stat().st_size:
                raise ValueError('release needs a reason and current resource inspection evidence')
            claim(record, release=True)
            record['release'] = {'evidence': proof, 'sha256': sha(proof), 'reason': note}
        elif operation == 'fail':
            if record['state'] not in ('preflight', 'ready', 'running'):
                raise ValueError('run is already terminal')
            record.update(state='failed', reason=note or 'caller reported failure')
        else:
            if record['state'] not in ('ready', 'running'):
                raise ValueError('run is already terminal')
            verify_context(record)
            if operation == 'observe':
                proof = absolute_file(evidence)
                if type(completed) is not int or completed < record['completed_units']:
                    raise ValueError('completed units must be a monotonic integer')
                if completed > record['completed_units']:
                    record['last_progress_at'] = time.time()
                record['completed_units'] = completed
                record['observations'].append({'at': time.time(), 'evidence': proof,
                    'sha256': sha(proof), 'completed_units': completed,
                    'error_signature': error, 'note': note})
                record['state'] = 'running'
            elif operation == 'finish':
                try:
                    outputs = {absolute_file(p): sha(p) for p in output_files(ROOT, record['spec'])}
                    record['after_results'] = checks(record['spec'], 'after')
                    if any(sha(p) != expected for p, expected in outputs.items()):
                        raise ValueError('native receipts changed during verification')
                except Exception as exc:
                    record['last_verification_error'] = str(exc)
                    write(path, record)
                    raise
                verify_context(record)
                record.update(state='verified', finished_at=time.time(), completed_evidence=outputs)
            else:
                raise ValueError('unsupported operation')
        write(path, record)
        return decision(record)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('operation', choices=['begin', 'observe', 'check', 'finish', 'fail', 'release'])
    p.add_argument('--run-dir', required=True, type=Path)
    p.add_argument('--spec', type=Path)
    p.add_argument('--evidence')
    p.add_argument('--completed', type=int)
    p.add_argument('--error-signature')
    p.add_argument('--note')
    args = p.parse_args()
    try:
        if args.operation == 'begin':
            if not args.spec: raise ValueError('--spec required')
            result = decision(begin(args.spec, args.run_dir))
        else:
            result = update(args.run_dir, args.operation, evidence=args.evidence,
                            completed=args.completed, error=args.error_signature, note=args.note)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        # A successful begin/observe is control progress, never formal acceptance.
        return 2 if result['review_reasons'] else 0
    except Exception as exc:
        print(json.dumps({'status': 'incomplete', 'reason': str(exc)}, ensure_ascii=False))
        return 2


if __name__ == '__main__': raise SystemExit(main())
