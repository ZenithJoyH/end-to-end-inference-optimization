#!/usr/bin/env python3
"""Frozen six-doc short probe after matching 8000's library path to 8010."""

import glob
import hashlib
import importlib.util
import json
import time
import urllib.request
from pathlib import Path

CASE = Path('/mnt/nfs/users/jinghao/qwen3.8-flash/20260919-qwen38-flash-next-ppu-e2e/accuracy/acc-010-full-gpqa-dual-user-services-20260923')
PREV = CASE / 'diagnostics/accdiag-003-cache-abi-graph-output-20260923'
ROOT = CASE / 'diagnostics/accdiag-004-first-divergent-token-20260923'
CONTROLLER = Path('/mnt/nfs/users/jinghao/qwen3.8-flash/20260919-qwen38-flash-next-ppu-e2e/commands/accdiag003-transition-8000.py')
DOC_IDS = (17, 30, 89, 140, 160, 168)
spec = importlib.util.spec_from_file_location('controller', CONTROLLER)
controller = importlib.util.module_from_spec(spec)
spec.loader.exec_module(controller)


def sha(text):
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


def check_identity():
    preflight = json.loads((PREV / 'preflight.json').read_text())
    matched = json.loads((ROOT / 'ldpath-matched-stage.json').read_text())
    controller.check_8010(preflight)
    controller.check_evaluator_idle()
    current = controller.process_facts(8000)
    if current is None or current['start_ticks'] != matched['service']['start_ticks']:
        raise RuntimeError('8000 no longer matches the library-path stage')
    if not controller.port_ready(8000):
        raise RuntimeError('8000 is unhealthy')
    controller.check_8000_idle()
    return current['start_ticks'], controller.process_facts(8010)['start_ticks']


def prompts():
    paths = glob.glob(str(CASE / 'results/**/samples_gpqa_diamond_generative_cot_*.jsonl'), recursive=True)
    if len(paths) != 1:
        raise RuntimeError(paths)
    result = {}
    for line in open(paths[0], encoding='utf-8'):
        row = json.loads(line)
        if row.get('filter') == 'strict-match' and row['doc_id'] in DOC_IDS:
            result[row['doc_id']] = {'messages': json.loads(row['arguments']['gen_args_0']['arg_0'][0]),
                                     'prompt_hash': row['prompt_hash']}
    if set(result) != set(DOC_IDS):
        raise RuntimeError(f'incomplete prompts: {sorted(result)}')
    return result


def post(port, payload):
    req = urllib.request.Request(f'http://127.0.0.1:{port}/v1/chat/completions',
        data=json.dumps(payload, ensure_ascii=False).encode(),
        headers={'Content-Type': 'application/json'}, method='POST')
    start = time.monotonic()
    with urllib.request.urlopen(req, timeout=180) as response:
        body = json.loads(response.read())
        status = response.status
    return status, body, round(time.monotonic() - start, 3)


def main():
    identity = check_identity()
    cases = prompts()
    out = ROOT / 'probe-ldpath-matched'
    out.mkdir(exist_ok=False)
    rows = []
    for doc_id in DOC_IDS:
        payload = {'model': 'Qwen3.8-Flash-Next', 'messages': cases[doc_id]['messages'],
                   'temperature': 0.0, 'top_p': 0.95, 'top_k': 20, 'min_p': 0.0,
                   'presence_penalty': 0.0, 'repetition_penalty': 1.0,
                   'max_tokens': 64, 'seed': 1234, 'stream': False}
        for port in (8000, 8010):
            for repeat in (1, 2):
                if check_identity() != identity:
                    raise RuntimeError('service identity drifted')
                status, body, elapsed = post(port, payload)
                choice = body['choices'][0]
                message = choice['message']
                text = (message.get('reasoning') or message.get('reasoning_content') or '') + '\0' + (message.get('content') or '')
                record = {'doc_id': doc_id, 'port': port, 'repeat': repeat,
                          'prompt_hash': cases[doc_id]['prompt_hash'], 'request_sha256': sha(json.dumps(payload, ensure_ascii=False, sort_keys=True)),
                          'http_status': status, 'finish_reason': choice.get('finish_reason'),
                          'completion_tokens': body.get('usage', {}).get('completion_tokens'),
                          'reasoning': message.get('reasoning') or message.get('reasoning_content'),
                          'content': message.get('content'), 'text_sha256': sha(text),
                          'elapsed_seconds': elapsed}
                (out / f'doc{doc_id}-port{port}-repeat{repeat}.json').write_text(json.dumps(record, ensure_ascii=False, indent=2) + '\n')
                rows.append(record)
    if check_identity() != identity:
        raise RuntimeError('service identity changed after probe')
    summary = []
    for doc_id in DOC_IDS:
        records = {(r['port'], r['repeat']): r for r in rows if r['doc_id'] == doc_id}
        before_8000 = json.loads((PREV / 'probe-graph-revert' / f'doc{doc_id}-port8000-repeat1.json').read_text())
        before_8010 = json.loads((PREV / 'probe-graph-revert' / f'doc{doc_id}-port8010-repeat1.json').read_text())
        summary.append({'doc_id': doc_id,
                        'within_8000_identical': records[(8000, 1)]['text_sha256'] == records[(8000, 2)]['text_sha256'],
                        'within_8010_identical': records[(8010, 1)]['text_sha256'] == records[(8010, 2)]['text_sha256'],
                        'cross_port_identical': records[(8000, 1)]['text_sha256'] == records[(8010, 1)]['text_sha256'],
                        '8000_same_as_before_match': records[(8000, 1)]['text_sha256'] == before_8000['text_sha256'],
                        '8010_same_as_before_match': records[(8010, 1)]['text_sha256'] == before_8010['text_sha256']})
    receipt = {'8000_start_ticks': identity[0], '8010_start_ticks': identity[1],
               'completed_at_epoch': time.time(), 'rows': summary}
    (out / 'summary.json').write_text(json.dumps(receipt, indent=2, sort_keys=True) + '\n')
    print(json.dumps(receipt, sort_keys=True))


if __name__ == '__main__':
    main()
