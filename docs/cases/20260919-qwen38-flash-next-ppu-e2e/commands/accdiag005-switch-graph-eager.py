#!/usr/bin/env python3
"""Scoped 8000 graph/eager switch with exact identities and graph recovery."""

import argparse
import hashlib
import importlib.util
import json
import shlex
import subprocess
import time
from pathlib import Path

CASE = Path('/mnt/nfs/users/jinghao/qwen3.8-flash/20260919-qwen38-flash-next-ppu-e2e/accuracy/acc-010-full-gpqa-dual-user-services-20260923')
PREV = CASE / 'diagnostics/accdiag-003-cache-abi-graph-output-20260923'
MATCH = CASE / 'diagnostics/accdiag-004-first-divergent-token-20260923'
ROOT = CASE / 'diagnostics/accdiag-005-graph-eager-numerics-20260923'
CONTROLLER = Path('/mnt/nfs/users/jinghao/qwen3.8-flash/20260919-qwen38-flash-next-ppu-e2e/commands/accdiag003-transition-8000.py')
spec = importlib.util.spec_from_file_location('controller', CONTROLLER)
controller = importlib.util.module_from_spec(spec)
spec.loader.exec_module(controller)


def write_new(path, value):
    if path.exists():
        raise RuntimeError(f'existing receipt: {path}')
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + '\n')


def read_env(pid):
    result = {}
    for item in Path(f'/proc/{pid}/environ').read_bytes().split(b'\0'):
        if b'=' in item:
            key, value = item.split(b'=', 1)
            result[key.decode(errors='replace')] = value.decode(errors='replace')
    return result


def launch(stage, baseline, ldpath, eager):
    argv = list(baseline['argv'])
    if '--enforce-eager' in argv:
        raise RuntimeError('frozen baseline already has enforce-eager')
    if eager:
        argv.append('--enforce-eager')
    env = dict(baseline['selected_environment'])
    env.update(controller.EXTRA_ENV)
    env.pop('PYTHONPATH', None)
    env['LD_LIBRARY_PATH'] = ldpath
    source = subprocess.run(
        ['docker', 'exec', controller.CONTAINER, 'python3', '-c',
         'import vllm_fl; print(vllm_fl.__file__)'],
        check=True, capture_output=True, text=True).stdout.strip()
    if source != controller.ORIGINAL + '/vllm_fl/__init__.py':
        raise RuntimeError('source import does not resolve original Plugin')
    logfile = ROOT / f'service-8000-{stage}.log'
    if logfile.exists():
        raise RuntimeError('stage log already exists')
    cmd = 'exec ' + shlex.join(argv) + ' > ' + shlex.quote(str(logfile)) + ' 2>&1'
    command = ['docker', 'exec', '-d']
    for key, value in sorted(env.items()):
        command.extend(['--env', f'{key}={value}'])
    command.extend([controller.CONTAINER, 'bash', '-c', cmd])
    started = time.time()
    subprocess.run(command, check=True, capture_output=True, text=True)
    print(f'launched {stage}, waiting for 8000', flush=True)
    next_report = started + 30
    while time.time() - started < 1200:
        current = controller.process_facts(8000)
        if current and controller.port_ready(8000):
            if current['argv'] != argv:
                raise RuntimeError(f'{stage} argv differs from frozen argv')
            if current['selected_environment'].get('CUDA_VISIBLE_DEVICES') != '8,9,10,11,12,13,14,15':
                raise RuntimeError('8000 card assignment changed')
            if current['selected_environment'].get('PYTHONPATH'):
                raise RuntimeError('8000 private source path unexpectedly active')
            if read_env(current['host_pid']).get('LD_LIBRARY_PATH') != ldpath:
                raise RuntimeError('8000 library path differs from reference')
            return {'stage': stage, 'service': current, 'import_resolution': source,
                    'log': str(logfile), 'started_at_epoch': started,
                    'ready_at_epoch': time.time(),
                    'ld_library_path_sha256': hashlib.sha256(ldpath.encode()).hexdigest()}
        if time.time() >= next_report:
            print(f'waiting {stage}, elapsed={round(time.time() - started)}s, root_present={current is not None}', flush=True)
            next_report += 30
        time.sleep(5)
    raise TimeoutError(f'{stage} not ready in 1200s; see {logfile}')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--mode', choices=('eager', 'restore'), required=True)
    args = parser.parse_args()
    ROOT.mkdir(exist_ok=True)
    preflight = json.loads((PREV / 'preflight.json').read_text())
    matched = json.loads((MATCH / 'ldpath-matched-stage.json').read_text())
    baseline = matched['service']
    controller.check_8010(preflight)
    controller.check_evaluator_idle()
    current = controller.process_facts(8000)
    expected = baseline if args.mode == 'eager' else json.loads((ROOT / 'stage-eager.json').read_text())['service']
    if current is None or current['start_ticks'] != expected['start_ticks']:
        raise RuntimeError('8000 identity changed; refusing transition')
    if not controller.port_ready(8000):
        raise RuntimeError('8000 unhealthy before transition')
    controller.check_8000_idle()
    ref = controller.process_facts(8010)
    ldpath = read_env(ref['host_pid']).get('LD_LIBRARY_PATH')
    if not ldpath or read_env(current['host_pid']).get('LD_LIBRARY_PATH') != ldpath:
        raise RuntimeError('current 8000 and 8010 paths are not matched')
    stage = 'eager' if args.mode == 'eager' else 'restored-graph'
    receipt = ROOT / f'stage-{stage}.json'
    if receipt.exists():
        raise RuntimeError(f'{stage} already executed')
    write_new(ROOT / f'transition-to-{stage}.json',
              {'old_start_ticks': current['start_ticks'], '8010_start_ticks': ref['start_ticks'],
               'old_argv': current['argv'], 'new_argv': baseline['argv'] + (['--enforce-eager'] if args.mode == 'eager' else []),
               'ld_library_path_sha256': hashlib.sha256(ldpath.encode()).hexdigest(),
               'source': controller.ORIGINAL})
    controller.stop_exact(expected)
    try:
        next_stage = launch(stage, baseline, ldpath, eager=args.mode == 'eager')
    except Exception as exc:
        (ROOT / f'failure-{stage}.txt').write_text(f'{type(exc).__name__}: {exc}\n')
        active = controller.process_facts(8000)
        if active:
            controller.stop_exact(active, require_idle=False)
        if not controller.port_ready(8000):
            recovery = launch(f'recovery-after-{stage}', baseline, ldpath, eager=False)
            write_new(ROOT / f'recovery-after-{stage}.json', recovery)
        raise
    controller.check_8010(preflight)
    write_new(receipt, next_stage)
    print(json.dumps({'stage': stage, '8000_start_ticks': next_stage['service']['start_ticks'],
                      '8010_start_ticks': controller.process_facts(8010)['start_ticks'],
                      'receipt': str(receipt), 'log': next_stage['log']}, sort_keys=True))


if __name__ == '__main__':
    main()
