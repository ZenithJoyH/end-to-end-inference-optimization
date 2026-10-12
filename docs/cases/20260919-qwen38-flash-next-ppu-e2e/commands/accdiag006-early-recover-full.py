#!/usr/bin/env python3
"""Stop only the stalled accdiag-006 controller, then restore original FULL graph."""

import importlib.util
import json
import os
import signal
import time
from pathlib import Path

BASE = Path('/mnt/nfs/users/jinghao/qwen3.8-flash/20260919-qwen38-flash-next-ppu-e2e/commands')
spec = importlib.util.spec_from_file_location('switch', BASE / 'accdiag005-switch-graph-eager.py')
switch = importlib.util.module_from_spec(spec)
spec.loader.exec_module(switch)

ROOT = switch.CASE / 'diagnostics/accdiag-006-full-decode-vs-piecewise-20260923'
switch.ROOT = ROOT
TARGET_ARGV = ['python3', str(BASE / 'accdiag006-switch-piecewise.py'), '--mode', 'piecewise']


def find_controller():
    found = []
    for item in os.scandir('/proc'):
        if not item.name.isdigit():
            continue
        try:
            argv = [part.decode(errors='replace') for part in
                    (Path(item.path) / 'cmdline').read_bytes().split(b'\0') if part]
            if argv == TARGET_ARGV:
                stat = (Path(item.path) / 'stat').read_text()
                found.append({'pid': int(item.name),
                              'start_ticks': int(stat[stat.rfind(')') + 2:].split()[19])})
        except (FileNotFoundError, PermissionError, ProcessLookupError):
            continue
    if len(found) != 1:
        raise RuntimeError(f'expected one exact diagnostic controller, got {found}')
    return found[0]


def main():
    preflight = json.loads((switch.PREV / 'preflight.json').read_text())
    baseline = json.loads((switch.CASE / 'diagnostics/accdiag-005-graph-eager-numerics-20260923/stage-restored-graph.json').read_text())['service']
    switch.controller.check_8010(preflight)
    switch.controller.check_evaluator_idle()
    if switch.controller.process_facts(8000) is not None or switch.controller.port_ready(8000):
        raise RuntimeError('8000 unexpectedly active; refusing duplicate launch')
    ref = switch.controller.process_facts(8010)
    ldpath = switch.read_env(ref['host_pid']).get('LD_LIBRARY_PATH')
    if not ldpath:
        raise RuntimeError('8010 library path unavailable')
    stalled = find_controller()
    receipt = ROOT / 'early-recovery-preflight.json'
    switch.write_new(receipt, {'stalled_controller': stalled,
                               '8010_start_ticks': ref['start_ticks'],
                               '8000_root_absent': True, '8000_port_ready': False,
                               'recovery_argv': baseline['argv']})
    os.kill(stalled['pid'], signal.SIGTERM)
    for _ in range(30):
        proc = Path(f'/proc/{stalled["pid"]}')
        if not proc.exists():
            break
        try:
            stat = (proc / 'stat').read_text()
        except FileNotFoundError:
            break
        fields = stat[stat.rfind(')') + 2:].split()
        if fields[0] == 'Z' and int(fields[19]) == stalled['start_ticks']:
            break
        time.sleep(1)
    else:
        raise RuntimeError('stalled diagnostic controller did not exit after TERM')
    if switch.controller.process_facts(8000) is not None or switch.controller.port_ready(8000):
        raise RuntimeError('8000 appeared during controller shutdown; refusing launch')
    restored = switch.launch('early-recovery-full', baseline, ldpath, eager=False)
    switch.controller.check_8010(preflight)
    switch.write_new(ROOT / 'stage-early-recovery-full.json', restored)
    print(json.dumps({'status': 'restored_full_graph',
                      '8000_start_ticks': restored['service']['start_ticks'],
                      '8010_start_ticks': switch.controller.process_facts(8010)['start_ticks'],
                      'receipt': str(ROOT / 'stage-early-recovery-full.json')}))


if __name__ == '__main__':
    main()
