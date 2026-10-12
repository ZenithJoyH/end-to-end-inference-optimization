#!/usr/bin/env python3
"""Fixed short GPQA trajectory probe for accdiag-003 service stages."""

import argparse
import glob
import hashlib
import json
import time
import urllib.request
from pathlib import Path

CASE = Path('/mnt/nfs/users/jinghao/qwen3.8-flash/20260919-qwen38-flash-next-ppu-e2e/accuracy/acc-010-full-gpqa-dual-user-services-20260923')
ROOT = CASE / 'diagnostics/accdiag-003-cache-abi-graph-output-20260923'
ORIGINAL = CASE / 'diagnostics/accdiag-002-greedy-cross-port-20260923'
DOC_IDS = (17, 30, 89, 140, 160, 168)


def digest(text):
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--stage', required=True)
    args = parser.parse_args()
    receipt = json.loads((ROOT / f'stage-{args.stage}.json').read_text())
    if receipt['service']['port'] != 8000:
        raise RuntimeError('stage receipt is not for port 8000')
    out = ROOT / f'probe-{args.stage}'
    out.mkdir(exist_ok=False)
    paths = glob.glob(str(CASE / 'results/**/samples_gpqa_diamond_generative_cot_*.jsonl'), recursive=True)
    if len(paths) != 1:
        raise RuntimeError(paths)
    cases = {}
    for line in open(paths[0], encoding='utf-8'):
        row = json.loads(line)
        if row.get('filter') == 'strict-match' and row['doc_id'] in DOC_IDS:
            cases[row['doc_id']] = {
                'messages': json.loads(row['arguments']['gen_args_0']['arg_0'][0]),
                'prompt_hash': row['prompt_hash'], 'target': row['target'],
            }
    if set(cases) != set(DOC_IDS):
        raise RuntimeError(sorted(cases))
    results = []
    for doc_id in DOC_IDS:
        case = cases[doc_id]
        payload = {
            'model': 'Qwen3.8-Flash-Next', 'messages': case['messages'],
            'temperature': 0.0, 'top_p': 0.95, 'top_k': 20, 'min_p': 0.0,
            'presence_penalty': 0.0, 'repetition_penalty': 1.0,
            'max_tokens': 64, 'seed': 1234, 'stream': False,
        }
        request_data = json.dumps(payload, ensure_ascii=False).encode('utf-8')
        for port in (8000, 8010):
            for repeat in (1, 2):
                record = {'stage': args.stage, 'doc_id': doc_id, 'port': port,
                          'repeat': repeat, 'prompt_hash': case['prompt_hash'],
                          'target': case['target'],
                          'request_sha256': digest(json.dumps(payload, ensure_ascii=False, sort_keys=True))}
                request = urllib.request.Request(
                    f'http://127.0.0.1:{port}/v1/chat/completions',
                    data=request_data, headers={'Content-Type': 'application/json'}, method='POST',
                )
                start = time.monotonic()
                try:
                    with urllib.request.urlopen(request, timeout=180) as response:
                        body = json.loads(response.read())
                        record['http_status'] = response.status
                    choice = body['choices'][0]
                    message = choice['message']
                    record['finish_reason'] = choice.get('finish_reason')
                    record['content'] = message.get('content')
                    record['reasoning'] = message.get('reasoning') or message.get('reasoning_content')
                    record['usage'] = body.get('usage')
                    record['text_sha256'] = digest((record['reasoning'] or '') + '\0' + (record['content'] or ''))
                except Exception as exc:
                    record['error'] = f'{type(exc).__name__}: {exc}'
                record['elapsed_seconds'] = round(time.monotonic() - start, 3)
                (out / f'doc{doc_id}-port{port}-repeat{repeat}.json').write_text(
                    json.dumps(record, ensure_ascii=False, indent=2) + '\n', encoding='utf-8'
                )
                results.append(record)
    summary = []
    for doc_id in DOC_IDS:
        rows = [r for r in results if r['doc_id'] == doc_id]
        by_port = {p: [r for r in rows if r['port'] == p] for p in (8000, 8010)}
        first = {p: by_port[p][0] for p in (8000, 8010)}
        old_path = ORIGINAL / f'doc{doc_id}-port8000-repeat1.json'
        old = json.loads(old_path.read_text()) if old_path.exists() else {}
        old_ref_path = ORIGINAL / f'doc{doc_id}-port8010-repeat1.json'
        old_ref = json.loads(old_ref_path.read_text()) if old_ref_path.exists() else {}
        summary.append({
            'doc_id': doc_id,
            'within_8000_identical': first[8000].get('text_sha256') == by_port[8000][1].get('text_sha256'),
            'within_8010_identical': first[8010].get('text_sha256') == by_port[8010][1].get('text_sha256'),
            'cross_port_identical': first[8000].get('text_sha256') == first[8010].get('text_sha256'),
            '8000_same_as_pre_restart': first[8000].get('text_sha256') == old.get('text_sha256'),
            '8010_same_as_original_reference': first[8010].get('text_sha256') == old_ref.get('text_sha256'),
            'errors': [r['error'] for r in rows if 'error' in r],
        })
    (out / 'summary.json').write_text(json.dumps({'stage': args.stage, 'rows': summary}, indent=2) + '\n')
    print(json.dumps({'stage': args.stage, 'rows': summary}))


if __name__ == '__main__':
    main()
