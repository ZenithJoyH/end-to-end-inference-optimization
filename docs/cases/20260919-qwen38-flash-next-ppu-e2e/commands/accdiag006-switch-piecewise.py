#!/usr/bin/env python3
"""Precisely switch only 8000 FULL decode graph to PIECEWISE and back."""

import argparse
import copy
import hashlib
import importlib.util
import json
from pathlib import Path

BASE = Path('/mnt/nfs/users/jinghao/qwen3.8-flash/20260919-qwen38-flash-next-ppu-e2e/commands')
spec = importlib.util.spec_from_file_location('switch', BASE / 'accdiag005-switch-graph-eager.py')
switch = importlib.util.module_from_spec(spec)
spec.loader.exec_module(switch)

CASE = switch.CASE
ROOT = CASE / 'diagnostics/accdiag-006-full-decode-vs-piecewise-20260923'
switch.ROOT = ROOT


def change_decode_mode(baseline):
    changed = copy.deepcopy(baseline)
    argv = changed['argv']
    if argv.count('--compilation-config') != 1:
        raise RuntimeError('expected exactly one compilation-config argument')
    index = argv.index('--compilation-config') + 1
    config = json.loads(argv[index])
    if config.get('cudagraph_mode') != 'FULL_AND_PIECEWISE':
        raise RuntimeError('unexpected original graph mode')
    config['cudagraph_mode'] = 'PIECEWISE'
    argv[index] = json.dumps(config, separators=(',', ':'))
    return changed


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--mode', choices=('piecewise', 'restore'), required=True)
    args = parser.parse_args()
    ROOT.mkdir(exist_ok=True)
    preflight = json.loads((switch.PREV / 'preflight.json').read_text())
    graph = json.loads((switch.ROOT.parent / 'accdiag-005-graph-eager-numerics-20260923' / 'stage-restored-graph.json').read_text())
    baseline = graph['service']
    piecewise = change_decode_mode(baseline)
    switch.controller.check_8010(preflight)
    switch.controller.check_evaluator_idle()
    current = switch.controller.process_facts(8000)
    expected = baseline if args.mode == 'piecewise' else json.loads((ROOT / 'stage-piecewise.json').read_text())['service']
    if not current or current['start_ticks'] != expected['start_ticks']:
        raise RuntimeError('8000 identity changed')
    if not switch.controller.port_ready(8000):
        raise RuntimeError('8000 unhealthy')
    switch.controller.check_8000_idle()
    ref = switch.controller.process_facts(8010)
    ldpath = switch.read_env(ref['host_pid']).get('LD_LIBRARY_PATH')
    if not ldpath or switch.read_env(current['host_pid']).get('LD_LIBRARY_PATH') != ldpath:
        raise RuntimeError('8000/8010 library paths are not matched')
    stage = 'piecewise' if args.mode == 'piecewise' else 'restored-full'
    receipt = ROOT / f'stage-{stage}.json'
    if receipt.exists():
        raise RuntimeError('stage already exists')
    target = piecewise if args.mode == 'piecewise' else baseline
    switch.write_new(ROOT / f'transition-to-{stage}.json',
                     {'old_start_ticks': current['start_ticks'], '8010_start_ticks': ref['start_ticks'],
                      'old_argv': current['argv'], 'new_argv': target['argv'],
                      'ld_library_path_sha256': hashlib.sha256(ldpath.encode()).hexdigest(),
                      'source': switch.controller.ORIGINAL})
    switch.controller.stop_exact(expected)
    try:
        next_stage = switch.launch(stage, target, ldpath, eager=False)
    except Exception as exc:
        (ROOT / f'failure-{stage}.txt').write_text(f'{type(exc).__name__}: {exc}\n')
        active = switch.controller.process_facts(8000)
        if active:
            switch.controller.stop_exact(active, require_idle=False)
        if not switch.controller.port_ready(8000):
            recovery = switch.launch(f'recovery-after-{stage}', baseline, ldpath, eager=False)
            switch.write_new(ROOT / f'recovery-after-{stage}.json', recovery)
        raise
    switch.controller.check_8010(preflight)
    switch.write_new(receipt, next_stage)
    print(json.dumps({'stage': stage, '8000_start_ticks': next_stage['service']['start_ticks'],
                      '8010_start_ticks': switch.controller.process_facts(8010)['start_ticks'],
                      'receipt': str(receipt), 'log': next_stage['log']}, sort_keys=True))


if __name__ == '__main__':
    main()
