#!/usr/bin/env python3
"""Run bounded diagnostic profiling rounds with native benchmark validation.

Configure profiling on the target server before running this client. Trace
paths refer to files visible to this process, not an inferred remote directory.
Profiled timings are for diagnosis and are never formal performance results.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path
import re
import sys
import uuid

sys.path.insert(0, str(Path(__file__).resolve().parent))
import vllm_perf


def parse_case(value):
    try:
        case = tuple(int(part) for part in value.split(','))
    except ValueError as exc:
        raise argparse.ArgumentTypeError('case requires INPUT,OUTPUT,CONCURRENCY,REQUESTS') from exc
    if len(case) != 4 or any(n <= 0 for n in case) or case[1] <= 1:
        raise argparse.ArgumentTypeError('case requires four positive integers and output length > 1')
    return case


def parse_args(argv=None, engine='vllm'):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--model', required=True)
    parser.add_argument('--tokenizer', required=True)
    parser.add_argument('--host', default='127.0.0.1')
    parser.add_argument('--port', type=int, default=8010 if engine == 'vllm' else 30000)
    parser.add_argument('--endpoint', choices=['/v1/completions'] if engine == 'vllm' else ['/generate'],
                        default='/v1/completions' if engine == 'vllm' else '/generate')
    parser.add_argument('--case', action='append', type=parse_case, help='INPUT,OUTPUT,CONCURRENCY,REQUESTS; repeatable')
    parser.add_argument('--runs', type=int, default=3 if engine == 'vllm' else 2)
    parser.add_argument('--warmup-rounds', type=int, default=2 if engine == 'vllm' else 1)
    parser.add_argument('--seed', type=int, default=42)
    parser.add_argument('--timeout', type=float, default=3600)
    parser.add_argument('--no-profile', action='store_true', help='Diagnostic benchmark only; no formal gate')
    parser.add_argument('--profile-runs', choices=['all', 'first', 'last'], default='last')
    parser.add_argument('--profile-dir', help='Directory of server trace files visible to this client')
    parser.add_argument('--output-dir', default='benchmark_results')
    parser.add_argument('--dry-run', action='store_true')
    args = parser.parse_args(argv)
    args.case = args.case or [(4096, 1024, 64, 64)]
    if not 0 <= args.warmup_rounds < args.runs or not 0 < args.port <= 65535:
        parser.error('require 0 <= warmup-rounds < runs and a valid port')
    if not 0 <= args.seed < 2**32 or not math.isfinite(args.timeout) or args.timeout <= 0:
        parser.error('invalid seed or timeout')
    if any(args.seed + c[0]*10 + c[2]*1000 + args.runs >= 2**32 for c in args.case):
        parser.error('derived per-round seed exceeds the client range')
    if not args.no_profile and not args.profile_dir:
        parser.error('--profile-dir is required to verify new traces for requested profiling')
    return args


def build_common_args(args):
    return ['vllm', 'bench', 'serve', '--backend', 'vllm', '--model', args.model,
            '--tokenizer', args.tokenizer, '--endpoint', args.endpoint, '--host', args.host,
            '--port', str(args.port), '--dataset-name', 'random', '--random-range-ratio', '0',
            '--temperature', '0', '--ignore-eos', '--request-rate', 'inf', '--seed', str(args.seed)]


def should_profile_run(run_id, total_runs, profile_runs_mode, warmup_rounds=2):
    if run_id <= warmup_rounds:
        return False
    return (profile_runs_mode == 'all' or
            run_id == (warmup_rounds + 1 if profile_runs_mode == 'first' else total_runs))


def trace_snapshot(directory):
    if directory is None:
        return {}
    root = Path(directory)
    if not root.is_dir():
        raise ValueError('profile-dir must be an existing, locally visible trace directory')
    result = {}
    for path in sorted(root.rglob('*')):
        if path.is_file() and (path.name.endswith('.json') or path.name.endswith('.json.gz')):
            stat = path.stat()
            result[str(path.resolve())] = (stat.st_mtime_ns, stat.st_size)
    return result


def new_trace_artifacts(before, after):
    result = []
    for name, signature in after.items():
        if signature[1] <= 0 or before.get(name) == signature:
            continue
        # A newly written benchmark JSON or a truncated export is not trace
        # evidence, even if the caller accidentally shares output directories.
        from trace_to_summary import load_trace, aggregate_events
        try:
            aggregate_events(load_trace(name))
        except (OSError, ValueError, TypeError):
            continue
        digest = hashlib.sha256()
        with Path(name).open('rb') as stream:
            for chunk in iter(lambda: stream.read(1024 * 1024), b''):
                digest.update(chunk)
        result.append({'path': name, 'sha256': digest.hexdigest(), 'size': signature[1]})
    return result


def json_safe(value):
    """Keep invalid metric evidence readable without producing invalid JSON."""
    if isinstance(value, float) and not math.isfinite(value):
        return {"invalid_number": str(value)}
    if isinstance(value, dict):
        return {key: json_safe(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [json_safe(item) for item in value]
    return value


def run_diagnostic(args, engine='vllm'):
    if engine == 'sglang':
        import sglang_perf as backend
        common = backend.build_common_args(args)
    else:
        backend = vllm_perf
        common = build_common_args(args)
    planned = []
    for case in args.case:
        for run_id in range(1, args.runs + 1):
            profiled = not args.no_profile and should_profile_run(run_id, args.runs, args.profile_runs, args.warmup_rounds)
            planned.append((case, run_id, profiled, common + (['--profile'] if profiled else [])))
    if args.dry_run:
        # No backend import with GPU dependencies, subprocess, output dir or request.
        print(json.dumps({'engine': engine, 'scope': 'diagnostic', 'rounds': [
            {'case': case, 'run_id': i, 'profile_requested': p, 'common_command': cmd,
             'seed': args.seed+case[0]*10+case[2]*1000+i}
            for case, i, p, cmd in planned]}, indent=2))
        return 0
    if not args.no_profile:
        trace_snapshot(args.profile_dir)
    label = re.sub(r'[^A-Za-z0-9_.-]+', '_', args.model).strip('_') or 'model'
    out = Path(args.output_dir).resolve() / label / f'diagnostic-{uuid.uuid4().hex}'
    out.mkdir(parents=True, exist_ok=False)
    report = {'schema_version': 1, 'engine': engine, 'scope': 'diagnostic', 'status': 'running',
              'configuration': vars(args), 'rounds': [], 'summaries': [], 'errors': []}
    (out / 'plan.json').write_text(json.dumps(report['configuration'], indent=2))
    csv_path = out / 'rounds.csv'
    rows_by_mode = {}
    try:
        for case, run_id, profiled, cmd in planned:
            trace_before = trace_snapshot(args.profile_dir) if profiled else {}
            metrics = backend.run_once(case, run_id, str(out), cmd, timeout_s=args.timeout)
            phase = 'warmup' if run_id <= args.warmup_rounds else 'measured'
            row = {'case': case, 'run_id': run_id, 'phase': phase, 'profile_requested': profiled,
                   'valid': metrics.get('valid') is True, 'metrics': metrics}
            if profiled:
                row['traces'] = new_trace_artifacts(trace_before, trace_snapshot(args.profile_dir))
                if not row['traces']:
                    report['errors'].append('profiling requested but no new/changed nonempty trace was observed')
            report['rounds'].append(row)
            backend.append_csv(backend.format_result(case, metrics, f'{phase}-{run_id}-profile={profiled}'),
                               str(csv_path), backend.CSV_COLUMNS)
            if not row['valid']:
                report['status'] = 'failed'
                report['errors'].append(f'case {case}, round {run_id} failed')
                break
            if phase == 'measured':
                rows_by_mode.setdefault((case, profiled), []).append(metrics)
        else:
            report['status'] = 'incomplete' if report['errors'] else 'complete'
            # A profiled measurement and an unprofiled measurement cannot share
            # one mean. The warmup measurements never enter either group.
            for (case, profiled), rows in rows_by_mode.items():
                report['summaries'].append({'case': case, 'profile_requested': profiled,
                                            'measured_rounds': len(rows), 'metrics': backend.average_metrics(rows)})
    except Exception as exc:
        report['status'] = 'failed'
        report['errors'].append(f'{type(exc).__name__}: {exc}')
    finally:
        with (out / 'diagnostic.json').open('x') as stream:
            json.dump(json_safe(report), stream, indent=2, allow_nan=False)
        print(f'Diagnostic evidence: {out / "diagnostic.json"}')
    return {'complete': 0, 'failed': 1, 'incomplete': 2}[report['status']]


def main(argv=None, engine='vllm'):
    args = parse_args(argv, engine)
    try:
        code = run_diagnostic(args, engine)
    except (OSError, ValueError) as exc:
        print(f'ERROR: {exc}', file=sys.stderr)
        code = 1
    if code:
        raise SystemExit(code)


if __name__ == '__main__':
    main()
