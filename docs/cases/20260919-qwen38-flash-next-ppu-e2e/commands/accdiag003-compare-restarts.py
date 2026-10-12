#!/usr/bin/env python3
"""Read-only comparison of original, zero-code restarts, and cache-ABI A/B/revert."""

import json
from pathlib import Path

CASE = Path('/mnt/nfs/users/jinghao/qwen3.8-flash/20260919-qwen38-flash-next-ppu-e2e/accuracy/acc-010-full-gpqa-dual-user-services-20260923')
ROOT = CASE / 'diagnostics/accdiag-003-cache-abi-graph-output-20260923'
STAGES = {
    'original': CASE / 'diagnostics/accdiag-002-greedy-cross-port-20260923',
    'private_r1': ROOT / 'probe-baseline-private',
    'private_r2': ROOT / 'probe-baseline-private-r2',
    'original_restart': ROOT / 'probe-original-restart-control',
    'cache_abi': ROOT / 'probe-cache-abi',
    'cache_revert': ROOT / 'probe-cache-revert',
    'graph_view': ROOT / 'probe-graph-view',
    'graph_revert': ROOT / 'probe-graph-revert',
}
rows = []
for doc_id in (17, 30, 89, 140, 160, 168):
    hashes = {}
    for stage, directory in STAGES.items():
        for port in (8000, 8010):
            path = directory / f'doc{doc_id}-port{port}-repeat1.json'
            hashes[f'{stage}_{port}'] = json.loads(path.read_text())['text_sha256']
    rows.append({
        'doc_id': doc_id,
        'original_vs_r1_8000': hashes['original_8000'] == hashes['private_r1_8000'],
        'r1_vs_r2_8000': hashes['private_r1_8000'] == hashes['private_r2_8000'],
        'original_vs_r2_8000': hashes['original_8000'] == hashes['private_r2_8000'],
        'original_vs_original_restart_8000': hashes['original_8000'] == hashes['original_restart_8000'],
        'private_r2_vs_cache_abi_8000': hashes['private_r2_8000'] == hashes['cache_abi_8000'],
        'original_restart_vs_cache_abi_8000': hashes['original_restart_8000'] == hashes['cache_abi_8000'],
        'cache_abi_vs_revert_8000': hashes['cache_abi_8000'] == hashes['cache_revert_8000'],
        'private_r2_vs_revert_8000': hashes['private_r2_8000'] == hashes['cache_revert_8000'],
        'cache_revert_vs_graph_view_8000': hashes['cache_revert_8000'] == hashes['graph_view_8000'],
        'graph_view_vs_revert_8000': hashes['graph_view_8000'] == hashes['graph_revert_8000'],
        'private_r2_vs_graph_revert_8000': hashes['private_r2_8000'] == hashes['graph_revert_8000'],
        '8010_stable_all_stages': len({hashes[f'{stage}_8010'] for stage in STAGES}) == 1,
    })
print(json.dumps(rows, sort_keys=True))
