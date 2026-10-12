#!/usr/bin/env python3
"""Small read-only inference probe; writes evidence only in the case directory."""

import glob
import hashlib
import json
import time
import urllib.request
from pathlib import Path

ROOT = Path('/mnt/nfs/users/jinghao/qwen3.8-flash/20260919-qwen38-flash-next-ppu-e2e/accuracy/acc-010-full-gpqa-dual-user-services-20260923')
OUT = ROOT / 'diagnostics/accdiag-002-greedy-cross-port-20260923'
DOC_IDS = (17, 30, 89, 140, 160, 168)
PORTS = (8000, 8010)


def digest(value):
    return hashlib.sha256(value.encode('utf-8')).hexdigest()


paths = glob.glob(str(ROOT / 'results/**/samples_gpqa_diamond_generative_cot_*.jsonl'), recursive=True)
if len(paths) != 1:
    raise RuntimeError(paths)
cases = {}
for line in open(paths[0], encoding='utf-8'):
    row = json.loads(line)
    if row.get('filter') == 'strict-match' and row['doc_id'] in DOC_IDS:
        packed = row['arguments']['gen_args_0']
        cases[row['doc_id']] = {
            'messages': json.loads(packed['arg_0'][0]),
            'prompt_hash': row['prompt_hash'],
        }
if set(cases) != set(DOC_IDS):
    raise RuntimeError(sorted(cases))

OUT.mkdir(parents=True, exist_ok=False)
results = []
for doc_id in DOC_IDS:
    case = cases[doc_id]
    payload = {
        'model': 'Qwen3.8-Flash-Next',
        'messages': case['messages'],
        'temperature': 0.0,
        'top_p': 0.95,
        'top_k': 20,
        'min_p': 0.0,
        'presence_penalty': 0.0,
        'repetition_penalty': 1.0,
        'max_tokens': 64,
        'seed': 1234,
        'stream': False,
    }
    for port in PORTS:
        for repeat in (1, 2):
            request = urllib.request.Request(
                f'http://127.0.0.1:{port}/v1/chat/completions',
                data=json.dumps(payload, ensure_ascii=False).encode('utf-8'),
                headers={'Content-Type': 'application/json'},
                method='POST',
            )
            started = time.monotonic()
            record = {'doc_id': doc_id, 'port': port, 'repeat': repeat,
                      'prompt_hash': case['prompt_hash'],
                      'request_sha256': digest(json.dumps(payload, sort_keys=True, ensure_ascii=False))}
            try:
                with urllib.request.urlopen(request, timeout=180) as response:
                    body = json.loads(response.read())
                    record['http_status'] = response.status
                choice = body['choices'][0]
                message = choice['message']
                record.update({
                    'finish_reason': choice.get('finish_reason'),
                    'content': message.get('content'),
                    'reasoning': message.get('reasoning') or message.get('reasoning_content'),
                    'usage': body.get('usage'),
                })
                record['text_sha256'] = digest((record['reasoning'] or '') + '\0' + (record['content'] or ''))
            except Exception as exc:
                record['error'] = f'{type(exc).__name__}: {exc}'
            record['elapsed_seconds'] = round(time.monotonic() - started, 3)
            (OUT / f'doc{doc_id}-port{port}-repeat{repeat}.json').write_text(
                json.dumps(record, ensure_ascii=False, indent=2) + '\n', encoding='utf-8'
            )
            results.append(record)

summary = []
for doc_id in DOC_IDS:
    rows = [r for r in results if r['doc_id'] == doc_id]
    by_port = {p: [r for r in rows if r['port'] == p] for p in PORTS}
    summary.append({
        'doc_id': doc_id,
        'within_8000_identical': by_port[8000][0].get('text_sha256') == by_port[8000][1].get('text_sha256'),
        'within_8010_identical': by_port[8010][0].get('text_sha256') == by_port[8010][1].get('text_sha256'),
        'cross_port_identical': by_port[8000][0].get('text_sha256') == by_port[8010][0].get('text_sha256'),
        'errors': [r['error'] for r in rows if 'error' in r],
        'completion_tokens': {str(p): [r.get('usage', {}).get('completion_tokens') for r in by_port[p]] for p in PORTS},
    })
(OUT / 'summary.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps(summary, ensure_ascii=False))
