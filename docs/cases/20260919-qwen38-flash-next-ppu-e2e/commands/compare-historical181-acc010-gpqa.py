#!/usr/bin/env python3
"""Read-only, bounded provenance and item-outcome comparison."""

import glob
import json
import re
from pathlib import Path

OLD_ROOT = Path('/mnt/nfs/users/jinghao/qwen3.8-flash/04-runs/Qwen3.8-Flash-Next-alt-test-c64-maxgen60000')
NEW_ROOT = Path('/mnt/nfs/users/jinghao/qwen3.8-flash/20260919-qwen38-flash-next-ppu-e2e/accuracy/acc-010-full-gpqa-dual-user-services-20260923')


def load(root):
    paths = glob.glob(str(root / '**/samples_gpqa_diamond_generative_cot_*.jsonl'), recursive=True)
    if len(paths) != 1:
        raise RuntimeError((str(root), paths))
    rows = [json.loads(line) for line in open(paths[0], encoding='utf-8')]
    filters = sorted({r.get('filter') for r in rows})
    rows = {r['doc_id']: r for r in rows if r.get('filter') == 'strict-match'}
    return rows, filters, paths[0]


old, old_filters, old_path = load(OLD_ROOT)
new, new_filters, new_path = load(NEW_ROOT)
ids = sorted(set(old) & set(new))
if len(ids) != 198:
    raise RuntimeError((len(old), len(new), len(ids)))


def good(row):
    return bool(row.get('exact_match'))


def capped(row):
    return bool(row.get('timeout')) or (row.get('usage') or {}).get('completion_tokens', 0) >= 60000


def response(row):
    value = row.get('filtered_resps') or []
    return value[0] if value else None


summary = {
    'old_samples': old_path,
    'new_samples': new_path,
    'old_filters': old_filters,
    'new_filters': new_filters,
    'old_correct': sum(good(old[i]) for i in ids),
    'new_correct': sum(good(new[i]) for i in ids),
    'same_prompt_hash': sum(old[i].get('prompt_hash') == new[i].get('prompt_hash') for i in ids),
    'same_target_hash': sum(old[i].get('target_hash') == new[i].get('target_hash') for i in ids),
    'same_doc_hash': sum(old[i].get('doc_hash') == new[i].get('doc_hash') for i in ids),
    'old_caps': [i for i in ids if capped(old[i])],
    'new_caps': [i for i in ids if capped(new[i])],
    'old_wrong_new_correct': [i for i in ids if not good(old[i]) and good(new[i])],
    'old_correct_new_wrong': [i for i in ids if good(old[i]) and not good(new[i])],
    'both_wrong': [i for i in ids if not good(old[i]) and not good(new[i])],
    'same_extracted_letter': sum(response(old[i]) == response(new[i]) for i in ids),
}
print(json.dumps(summary, ensure_ascii=False, sort_keys=True))
for i in summary['old_caps']:
    content = (old[i].get('resps') or [['']])[0][0]
    markers = list(re.finditer(r'the best answer is\s*\(?([ABCD])\)?', content, re.I))
    print(json.dumps({
        'historical_60k_doc_id': i,
        'old_correct': good(old[i]),
        'old_timeout_flag': old[i].get('timeout'),
        'old_content_chars': len(content),
        'final_marker_count': len(markers),
        'last_marker_position_fraction': round(markers[-1].start() / len(content), 4) if markers and content else None,
        'old_extracted': response(old[i]),
    }, ensure_ascii=False, sort_keys=True))
for i in summary['old_correct_new_wrong']:
    print(json.dumps({
        'doc_id': i,
        'target_old': old[i].get('target'),
        'target_new': new[i].get('target'),
        'old_answer': response(old[i]),
        'new_answer': response(new[i]),
        'old_cap': capped(old[i]),
        'new_cap': capped(new[i]),
        'old_timeout_flag': old[i].get('timeout'),
        'new_timeout_flag': new[i].get('timeout'),
        'old_response_prefix': str((old[i].get('resps') or [['']])[0][0])[:90],
        'new_response_prefix': str((new[i].get('resps') or [['']])[0][0])[:90],
        'old_tokens': (old[i].get('usage') or {}).get('completion_tokens'),
        'new_tokens': (new[i].get('usage') or {}).get('completion_tokens'),
    }, ensure_ascii=False, sort_keys=True))
