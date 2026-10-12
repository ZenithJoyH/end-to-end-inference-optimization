#!/usr/bin/env python3
"""Verify FULL graph recovery, fixed short trajectories, and C1/C8 health."""

import concurrent.futures
import importlib.util
import json
import time
from pathlib import Path

BASE = Path('/mnt/nfs/users/jinghao/qwen3.8-flash/20260919-qwen38-flash-next-ppu-e2e/commands')
spec = importlib.util.spec_from_file_location('short_probe', BASE / 'accdiag004-no-logprob-probe.py')
probe = importlib.util.module_from_spec(spec)
spec.loader.exec_module(probe)
spec2 = importlib.util.spec_from_file_location('smoke', BASE / 'accdiag003-final-audit.py')
smoke = importlib.util.module_from_spec(spec2)
spec2.loader.exec_module(smoke)
spec3 = importlib.util.spec_from_file_location('switch', BASE / 'accdiag005-switch-graph-eager.py')
switch = importlib.util.module_from_spec(spec3)
spec3.loader.exec_module(switch)

ROOT = probe.CASE / 'diagnostics/accdiag-006-full-decode-vs-piecewise-20260923'
DOC_IDS = (89, 140, 168)


def check():
    preflight = json.loads((probe.PREV / 'preflight.json').read_text())
    stage = json.loads((ROOT / 'stage-early-recovery-full.json').read_text())
    probe.controller.check_8010(preflight)
    probe.controller.check_evaluator_idle()
    current = probe.controller.process_facts(8000)
    if not current or current['start_ticks'] != stage['service']['start_ticks']:
        raise RuntimeError('8000 recovery identity changed')
    if current['argv'] != stage['service']['argv']:
        raise RuntimeError('8000 recovery argv changed')
    argv = current['argv']
    mode = json.loads(argv[argv.index('--compilation-config') + 1])['cudagraph_mode']
    if mode != 'FULL_AND_PIECEWISE' or '--enforce-eager' in argv:
        raise RuntimeError('8000 is not restored FULL_AND_PIECEWISE graph')
    if not probe.controller.port_ready(8000):
        raise RuntimeError('8000 unhealthy')
    ref = probe.controller.process_facts(8010)
    if switch.read_env(current['host_pid']).get('LD_LIBRARY_PATH') != switch.read_env(ref['host_pid']).get('LD_LIBRARY_PATH'):
        raise RuntimeError('8000/8010 library paths differ again')
    probe.controller.check_8000_idle()
    return current['start_ticks'], ref['start_ticks']


def main():
    identity = check()
    out = ROOT / 'final-audit'
    out.mkdir(exist_ok=False)
    cases = probe.prompts()
    comparisons = []
    for doc_id in DOC_IDS:
        payload = {'model': 'Qwen3.8-Flash-Next', 'messages': cases[doc_id]['messages'],
                   'temperature': 0.0, 'top_p': 0.95, 'top_k': 20, 'min_p': 0.0,
                   'presence_penalty': 0.0, 'repetition_penalty': 1.0,
                   'max_tokens': 64, 'seed': 1234, 'stream': False}
        hashes = []
        for repeat in (1, 2):
            if check() != identity:
                raise RuntimeError('service identity drifted')
            status, body, elapsed = probe.post(8000, payload)
            if status != 200:
                raise RuntimeError(f'doc{doc_id} status={status}')
            choice = body['choices'][0]
            msg = choice['message']
            text = (msg.get('reasoning') or msg.get('reasoning_content') or '') + '\0' + (msg.get('content') or '')
            digest = probe.sha(text)
            hashes.append(digest)
            (out / f'doc{doc_id}-repeat{repeat}.json').write_text(
                json.dumps({'body': body, 'elapsed_seconds': elapsed, 'text_sha256': digest},
                           ensure_ascii=False, indent=2) + '\n')
        baseline = json.loads((probe.CASE / 'diagnostics/accdiag-005-graph-eager-numerics-20260923/probe-restored-graph' /
                               f'doc{doc_id}-port8000-repeat1.json').read_text())['text_sha256']
        comparisons.append({'doc_id': doc_id, 'two_replays_identical': hashes[0] == hashes[1],
                            'same_as_pre_piecewise_full_graph': hashes[0] == baseline})
    if check() != identity:
        raise RuntimeError('identity drifted before C1/C8')
    c1 = [smoke.request(), smoke.request()]
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
        c8 = list(executor.map(lambda _: smoke.request(), range(8)))
    if check() != identity:
        raise RuntimeError('identity drifted after C1/C8')
    result = {'status': 'passed' if all(r['two_replays_identical'] and r['same_as_pre_piecewise_full_graph'] for r in comparisons) else 'trajectory_changed',
              '8000_start_ticks': identity[0], '8010_start_ticks': identity[1],
              'probe_comparisons': comparisons, 'c1': c1, 'c8': c8,
              'completed_at_epoch': time.time()}
    (out / 'summary.json').write_text(json.dumps(result, indent=2, sort_keys=True) + '\n')
    print(json.dumps({'status': result['status'], '8000_start_ticks': identity[0],
                      '8010_start_ticks': identity[1], 'probes': comparisons,
                      'c1_count': len(c1), 'c8_count': len(c8),
                      'receipt': str(out / 'summary.json')}, sort_keys=True))


if __name__ == '__main__':
    main()
