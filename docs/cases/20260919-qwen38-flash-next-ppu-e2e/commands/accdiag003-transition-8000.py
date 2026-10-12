#!/usr/bin/env python3
"""Precisely switch only the 8000 TP8 service for accdiag-003."""

import argparse
import json
import os
import shlex
import signal
import subprocess
import time
import urllib.error
import urllib.request
from pathlib import Path

CONTAINER = 'qwen3.8-flash-opt-candidate-20260919'
EVAL_CONTAINER = 'qwen38-eval-e2e-20260919'
ORIGINAL = '/workspace/vllm-plugin-FL-qwen38-adaptation'
PRIVATE = '/workspace/vllm-plugin-FL-qwen38-accdiag003'
OUT = Path('/mnt/nfs/users/jinghao/qwen3.8-flash/20260919-qwen38-flash-next-ppu-e2e/accuracy/acc-010-full-gpqa-dual-user-services-20260923/diagnostics/accdiag-003-cache-abi-graph-output-20260923')
STAGES = {'baseline-private', 'baseline-private-r2', 'original-restart-control', 'cache-abi', 'cache-revert', 'graph-view', 'graph-revert', 'restored-original'}
EXTRA_ENV = {'NCCL_DEBUG': 'INFO', 'NCCL_IB_DISABLE': '1', 'PYTHONDONTWRITEBYTECODE': '1'}


def run(argv, *, check=True):
    return subprocess.run(argv, check=check, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)


def port_ready(port):
    try:
        with urllib.request.urlopen(f'http://127.0.0.1:{port}/v1/models', timeout=3) as response:
            if response.status != 200:
                return False
            body = json.loads(response.read())
            return any(x.get('id') == 'Qwen3.8-Flash-Next' for x in body.get('data', []))
    except (OSError, urllib.error.URLError, ValueError):
        return False


def process_facts(port):
    found = []
    for entry in os.scandir('/proc'):
        if not entry.name.isdigit():
            continue
        path = Path(entry.path)
        try:
            argv = [x.decode(errors='replace') for x in (path / 'cmdline').read_bytes().split(b'\0') if x]
            if 'serve' not in argv or '--port' not in argv or '/mnt/cpfs/models/Qwen3.8-Flash-Next' not in argv:
                continue
            if argv[argv.index('--port') + 1] != str(port):
                continue
            stat = (path / 'stat').read_text()
            env_items = (path / 'environ').read_bytes().split(b'\0')
            env = {}
            for item in env_items:
                if b'=' in item:
                    key, value = item.split(b'=', 1)
                    key = key.decode(errors='replace')
                    if key in ('CUDA_VISIBLE_DEVICES', 'PYTHONPATH'):
                        env[key] = value.decode(errors='replace')
            found.append({'port': port, 'host_pid': int(entry.name),
                          'start_ticks': int(stat[stat.rfind(')') + 2:].split()[19]),
                          'argv': argv, 'selected_environment': env})
        except (FileNotFoundError, PermissionError, ProcessLookupError):
            continue
    if len(found) > 1:
        raise RuntimeError(f'multiple target service roots for port {port}: {found}')
    return found[0] if found else None


def check_8010(preflight):
    current = process_facts(8010)
    expected = next(x for x in preflight['services'] if x['port'] == 8010)
    if current is None or current['start_ticks'] != expected['start_ticks']:
        raise RuntimeError('untouched 8010 reference identity changed')
    if not port_ready(8010):
        raise RuntimeError('8010 reference is not healthy')


def check_evaluator_idle():
    output = run(['docker', 'top', EVAL_CONTAINER]).stdout
    if any(name in output for name in ('formal_accuracy.py', 'llmrun.py')):
        raise RuntimeError('formal evaluator process is active')


def check_8000_idle():
    try:
        with urllib.request.urlopen('http://127.0.0.1:8000/metrics', timeout=4) as response:
            text = response.read().decode(errors='replace')
    except (OSError, urllib.error.URLError) as exc:
        raise RuntimeError(f'cannot verify 8000 request count: {exc}') from exc
    for name in ('vllm:num_requests_running', 'vllm:num_requests_waiting'):
        entries = [line for line in text.splitlines() if line.startswith(name + '{')]
        if not entries or any(float(line.rsplit(' ', 1)[1]) != 0 for line in entries):
            raise RuntimeError(f'{name} is nonzero or unavailable')


def launch(stage, source, preflight):
    baseline = next(x for x in preflight['services'] if x['port'] == 8000)
    env = {k: v for k, v in baseline['selected_environment'].items() if v is not None}
    env.update(EXTRA_ENV)
    env.pop('PYTHONPATH', None)
    if source == 'private':
        env['PYTHONPATH'] = PRIVATE
    imported = run(['docker', 'exec', *[item for key, value in env.items() for item in ('--env', f'{key}={value}')],
                    CONTAINER, 'python3', '-c', 'import vllm_fl; print(vllm_fl.__file__)']).stdout.strip()
    expected_import = (PRIVATE if source == 'private' else ORIGINAL) + '/vllm_fl/__init__.py'
    if imported != expected_import:
        raise RuntimeError(f'import resolution mismatch: {imported} != {expected_import}')
    logfile = OUT / f'service-8000-{stage}.log'
    if logfile.exists():
        raise RuntimeError(f'launch log already exists: {logfile}')
    cmd = 'exec ' + shlex.join(baseline['argv']) + ' > ' + shlex.quote(str(logfile)) + ' 2>&1'
    argv = ['docker', 'exec', '-d']
    for key, value in sorted(env.items()):
        argv.extend(['--env', f'{key}={value}'])
    argv.extend([CONTAINER, 'bash', '-c', cmd])
    start = time.time()
    run(argv)
    print(f'launched stage={stage}, waiting for port 8000', flush=True)
    next_report = start + 30
    while time.time() - start < 1200:
        current = process_facts(8000)
        if current and port_ready(8000):
            if current['selected_environment'].get('CUDA_VISIBLE_DEVICES') != '8,9,10,11,12,13,14,15':
                raise RuntimeError('new 8000 device binding differs')
            if source == 'private' and current['selected_environment'].get('PYTHONPATH') != PRIVATE:
                raise RuntimeError('new 8000 private Python path not inherited')
            return {'stage': stage, 'source': source, 'started_at_epoch': start,
                    'ready_at_epoch': time.time(), 'log': str(logfile),
                    'import_resolution': imported, 'service': current}
        if time.time() >= next_report:
            print(f'waiting stage={stage}, elapsed={round(time.time() - start)}s, service_root_present={current is not None}', flush=True)
            next_report += 30
        time.sleep(5)
    raise TimeoutError(f'8000 did not become ready within 1200s; see {logfile}')


def stop_exact(expected, *, require_idle=True):
    current = process_facts(8000)
    if current is None or current['start_ticks'] != expected['start_ticks']:
        raise RuntimeError('8000 root PID/start tick no longer matches expected stage')
    if require_idle:
        check_8000_idle()
    os.kill(current['host_pid'], signal.SIGTERM)
    print(f'sent TERM only to 8000 host_pid={current["host_pid"]}', flush=True)
    start = time.time()
    while time.time() - start < 180:
        if process_facts(8000) is None and not port_ready(8000):
            return
        time.sleep(3)
    raise TimeoutError('8000 did not release after TERM; no replacement launched')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--from-stage', required=True)
    parser.add_argument('--to-stage', choices=sorted(STAGES), required=True)
    args = parser.parse_args()
    preflight = json.loads((OUT / 'preflight.json').read_text())
    if args.from_stage == 'original':
        expected = next(x for x in preflight['services'] if x['port'] == 8000)
    else:
        old = json.loads((OUT / f'stage-{args.from_stage}.json').read_text())
        expected = old['service']
    if args.to_stage == 'baseline-private' and args.from_stage != 'original':
        raise RuntimeError('baseline-private must start from original')
    if args.to_stage != 'restored-original' and args.from_stage == 'original' and args.to_stage != 'baseline-private':
        raise RuntimeError('diagnostic stages require baseline-private first')
    if (OUT / f'stage-{args.to_stage}.json').exists():
        raise RuntimeError('target stage receipt already exists')
    if args.to_stage != 'restored-original' and not (OUT / 'private-prepared.json').exists():
        raise RuntimeError('private source copy has not been verified')
    if args.to_stage in ('baseline-private', 'baseline-private-r2', 'cache-abi', 'cache-revert'):
        model_file = f'{PRIVATE}/vllm_fl/models/qwen3_8_flash_next.py'
        current_sha = run(['docker', 'exec', CONTAINER, 'sha256sum', model_file]).stdout.split()[0]
        baseline_sha = preflight['source_file_sha256']['vllm_fl/models/qwen3_8_flash_next.py']
        if args.to_stage == 'cache-abi':
            expected_sha = json.loads((OUT / 'cache-abi-source-receipt.json').read_text())['modified_sha256']
        else:
            expected_sha = baseline_sha
        if current_sha != expected_sha:
            raise RuntimeError(f'private model source hash mismatch for {args.to_stage}: {current_sha}')
    if args.to_stage in ('graph-view', 'graph-revert'):
        model_file = f'{PRIVATE}/vllm_fl/models/qwen3_8_flash_next.py'
        current_model_sha = run(['docker', 'exec', CONTAINER, 'sha256sum', model_file]).stdout.split()[0]
        expected_model_sha = preflight['source_file_sha256']['vllm_fl/models/qwen3_8_flash_next.py']
        if current_model_sha != expected_model_sha:
            raise RuntimeError('model source has not been reverted before graph test')
        graph_file = f'{PRIVATE}/vllm_fl/compilation/graph.py'
        current_graph_sha = run(['docker', 'exec', CONTAINER, 'sha256sum', graph_file]).stdout.split()[0]
        expected_graph_sha = (json.loads((OUT / 'graph-view-source-receipt.json').read_text())['modified_sha256']
                              if args.to_stage == 'graph-view' else
                              preflight['source_file_sha256']['vllm_fl/compilation/graph.py'])
        if current_graph_sha != expected_graph_sha:
            raise RuntimeError(f'private graph source hash mismatch for {args.to_stage}: {current_graph_sha}')
    check_8010(preflight)
    check_evaluator_idle()
    source = 'original' if args.to_stage in ('original-restart-control', 'restored-original') else 'private'
    transition = {'from_stage': args.from_stage, 'to_stage': args.to_stage,
                  'expected_start_ticks': expected['start_ticks'],
                  'source': source, 'started_at_epoch': time.time()}
    (OUT / f'transition-{args.from_stage}-to-{args.to_stage}.json').write_text(
        json.dumps(transition, indent=2, sort_keys=True) + '\n'
    )
    stop_exact(expected)
    try:
        receipt = launch(args.to_stage, source, preflight)
    except Exception as exc:
        # Do not strand the original service when a diagnostic relaunch fails.
        (OUT / f'failure-{args.to_stage}.txt').write_text(f'{type(exc).__name__}: {exc}\n')
        current = process_facts(8000)
        if current is not None:
            try:
                stop_exact(current, require_idle=False)
            except Exception as cleanup_exc:
                raise RuntimeError(f'{exc}; automatic restoration unsafe: {cleanup_exc}') from exc
        if not port_ready(8000):
            recovery = launch(f'recovery-after-{args.to_stage}', 'original', preflight)
            (OUT / f'recovery-after-{args.to_stage}.json').write_text(json.dumps(recovery, indent=2, sort_keys=True) + '\n')
        raise
    (OUT / f'stage-{args.to_stage}.json').write_text(json.dumps(receipt, indent=2, sort_keys=True) + '\n')
    print(json.dumps({'stage': args.to_stage, 'source': source,
                      'host_pid': receipt['service']['host_pid'],
                      'start_ticks': receipt['service']['start_ticks'],
                      'import': receipt['import_resolution'],
                      'log': receipt['log']}, sort_keys=True), flush=True)


if __name__ == '__main__':
    main()
