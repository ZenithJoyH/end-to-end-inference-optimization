#!/usr/bin/env python3
"""Precisely restore 8000's missing library search path from untouched 8010."""

import hashlib
import importlib.util
import json
import os
import shlex
import subprocess
import time
from pathlib import Path

CASE = Path('/mnt/nfs/users/jinghao/qwen3.8-flash/20260919-qwen38-flash-next-ppu-e2e/accuracy/acc-010-full-gpqa-dual-user-services-20260923')
PREV = CASE / 'diagnostics/accdiag-003-cache-abi-graph-output-20260923'
ROOT = CASE / 'diagnostics/accdiag-004-first-divergent-token-20260923'
CONTROLLER = Path('/mnt/nfs/users/jinghao/qwen3.8-flash/20260919-qwen38-flash-next-ppu-e2e/commands/accdiag003-transition-8000.py')
spec = importlib.util.spec_from_file_location('controller', CONTROLLER)
controller = importlib.util.module_from_spec(spec)
spec.loader.exec_module(controller)


def read_environment(pid):
    result = {}
    for item in Path(f'/proc/{pid}/environ').read_bytes().split(b'\0'):
        if b'=' in item:
            key, value = item.split(b'=', 1)
            result[key.decode(errors='replace')] = value.decode(errors='replace')
    return result


def write_new(path, value):
    if path.exists():
        raise RuntimeError(f'receipt already exists: {path}')
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + '\n')


def launch(baseline, matched_ld):
    env = dict(baseline['selected_environment'])
    env.update(controller.EXTRA_ENV)
    env.pop('PYTHONPATH', None)
    env['LD_LIBRARY_PATH'] = matched_ld
    imported = subprocess.run(
        ['docker', 'exec', controller.CONTAINER, 'python3', '-c',
         'import vllm_fl; print(vllm_fl.__file__)'],
        check=True, text=True, capture_output=True).stdout.strip()
    if imported != controller.ORIGINAL + '/vllm_fl/__init__.py':
        raise RuntimeError(f'original source import mismatch: {imported}')
    logfile = ROOT / 'service-8000-ldpath-matched.log'
    if logfile.exists():
        raise RuntimeError('launch log already exists')
    cmd = 'exec ' + shlex.join(baseline['argv']) + ' > ' + shlex.quote(str(logfile)) + ' 2>&1'
    argv = ['docker', 'exec', '-d']
    for key, value in sorted(env.items()):
        argv.extend(['--env', f'{key}={value}'])
    argv.extend([controller.CONTAINER, 'bash', '-c', cmd])
    start = time.time()
    subprocess.run(argv, check=True, capture_output=True, text=True)
    print('launched matched-path 8000, waiting for readiness', flush=True)
    next_report = start + 30
    while time.time() - start < 1200:
        current = controller.process_facts(8000)
        if current and controller.port_ready(8000):
            actual_ld = read_environment(current['host_pid']).get('LD_LIBRARY_PATH')
            if actual_ld != matched_ld:
                raise RuntimeError('new service did not inherit matched LD_LIBRARY_PATH')
            if current['selected_environment'].get('CUDA_VISIBLE_DEVICES') != '8,9,10,11,12,13,14,15':
                raise RuntimeError('new service changed device group')
            if current['selected_environment'].get('PYTHONPATH'):
                raise RuntimeError('new service uses a private source path')
            return {'service': current, 'log': str(logfile), 'import_resolution': imported,
                    'started_at_epoch': start, 'ready_at_epoch': time.time(),
                    'ld_library_path_sha256': hashlib.sha256(matched_ld.encode()).hexdigest()}
        if time.time() >= next_report:
            print(f'waiting elapsed={round(time.time() - start)}s, root_present={current is not None}', flush=True)
            next_report += 30
        time.sleep(5)
    raise TimeoutError(f'8000 not ready in 1200s; see {logfile}')


def main():
    preflight = json.loads((PREV / 'preflight.json').read_text())
    restored = json.loads((PREV / 'stage-restored-original.json').read_text())
    expected = restored['service']
    ROOT.mkdir(exist_ok=True)
    receipt = ROOT / 'ldpath-matched-stage.json'
    if receipt.exists():
        raise RuntimeError('matched stage already exists')
    controller.check_8010(preflight)
    controller.check_evaluator_idle()
    current = controller.process_facts(8000)
    if current is None or current['start_ticks'] != expected['start_ticks']:
        raise RuntimeError('8000 is not the restored stage')
    if not controller.port_ready(8000):
        raise RuntimeError('8000 unhealthy before change')
    controller.check_8000_idle()
    ref = controller.process_facts(8010)
    old_ld = read_environment(current['host_pid']).get('LD_LIBRARY_PATH')
    matched_ld = read_environment(ref['host_pid']).get('LD_LIBRARY_PATH')
    if not old_ld or not matched_ld or old_ld == matched_ld:
        raise RuntimeError('library path difference is absent or unavailable')
    if '\n' in matched_ld or '\0' in matched_ld:
        raise RuntimeError('invalid reference library path')
    write_new(ROOT / 'ldpath-transition-preflight.json',
              {'8000_start_ticks': current['start_ticks'], '8010_start_ticks': ref['start_ticks'],
               '8000_ld_library_path': old_ld, '8010_ld_library_path': matched_ld,
               'source': controller.ORIGINAL, 'argv': expected['argv']})
    controller.stop_exact(expected)
    try:
        new = launch(expected, matched_ld)
    except Exception as exc:
        (ROOT / 'ldpath-launch-failure.txt').write_text(f'{type(exc).__name__}: {exc}\n')
        active = controller.process_facts(8000)
        if active:
            controller.stop_exact(active, require_idle=False)
        if not controller.port_ready(8000):
            recovery = controller.launch('recovery-after-ldpath-match', 'original', preflight)
            write_new(ROOT / 'ldpath-recovery.json', recovery)
        raise
    controller.check_8010(preflight)
    write_new(receipt, new)
    print(json.dumps({'status': 'ready', '8000_start_ticks': new['service']['start_ticks'],
                      '8010_start_ticks': controller.process_facts(8010)['start_ticks'],
                      'import_resolution': new['import_resolution'], 'receipt': str(receipt)}))


if __name__ == '__main__':
    main()
