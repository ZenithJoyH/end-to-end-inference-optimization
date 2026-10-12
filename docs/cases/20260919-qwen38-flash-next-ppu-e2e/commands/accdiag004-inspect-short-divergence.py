#!/usr/bin/env python3
"""Compare immutable accdiag-003 short responses before another online probe."""

import json
from pathlib import Path

BASE = Path('/mnt/nfs/users/jinghao/qwen3.8-flash/20260919-qwen38-flash-next-ppu-e2e/accuracy/acc-010-full-gpqa-dual-user-services-20260923/diagnostics')
ROOT = BASE / 'accdiag-003-cache-abi-graph-output-20260923'
STAGES = {
    'private_r2': ROOT / 'probe-baseline-private-r2',
    'cache_abi': ROOT / 'probe-cache-abi',
    'cache_revert': ROOT / 'probe-cache-revert',
    'graph_view': ROOT / 'probe-graph-view',
    'graph_revert': ROOT / 'probe-graph-revert',
}


def load(stage, doc, port):
    row = json.loads((STAGES[stage] / f'doc{doc}-port{port}-repeat1.json').read_text())
    if row.get('error') or row.get('http_status') != 200:
        raise RuntimeError(f'bad existing probe: {stage}/{doc}/{port}')
    return (row.get('reasoning') or '') + '\0' + (row.get('content') or '')


def compare(a, b):
    prefix = 0
    for x, y in zip(a, b):
        if x != y:
            break
        prefix += 1
    return {'identical': a == b, 'common_prefix_chars': prefix,
            'a_chars': len(a), 'b_chars': len(b),
            'a_near': a[max(prefix - 12, 0):prefix + 32],
            'b_near': b[max(prefix - 12, 0):prefix + 32]}


def main():
    out = []
    for doc in (17, 30, 89, 140, 160, 168):
        baseline = load('private_r2', doc, 8000)
        reference = load('private_r2', doc, 8010)
        candidate = load('cache_abi', doc, 8000)
        view = load('graph_view', doc, 8000)
        out.append({'doc_id': doc,
                    'baseline_8000_vs_8010': compare(baseline, reference),
                    'cache_abi_vs_baseline': compare(candidate, baseline),
                    'graph_view_vs_baseline': compare(view, baseline)})
    path = ROOT / 'short-first-divergence.json'
    if path.exists():
        raise RuntimeError('comparison receipt already exists')
    path.write_text(json.dumps(out, indent=2, ensure_ascii=False) + '\n')
    print(json.dumps(out, ensure_ascii=False))


if __name__ == '__main__':
    main()
