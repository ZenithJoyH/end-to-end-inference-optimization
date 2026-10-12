#!/usr/bin/env python3
"""Matched-env first-divergence logprobs for the other cross-port probes."""

import argparse
import glob
import importlib.util
import json
import urllib.request
from pathlib import Path

BASE = Path('/mnt/nfs/users/jinghao/qwen3.8-flash/20260919-qwen38-flash-next-ppu-e2e/commands')
spec = importlib.util.spec_from_file_location('doc89_probe', BASE / 'accdiag004-matched-doc89-logprobs.py')
probe = importlib.util.module_from_spec(spec)
spec.loader.exec_module(probe)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--doc-id', type=int, choices=(140, 168), required=True)
    args = parser.parse_args()
    probe.check()
    paths = glob.glob(str(probe.CASE / 'results/**/samples_gpqa_diamond_generative_cot_*.jsonl'), recursive=True)
    if len(paths) != 1:
        raise RuntimeError(paths)
    samples = [json.loads(line) for line in open(paths[0], encoding='utf-8')]
    matches = [row for row in samples if row.get('filter') == 'strict-match' and row['doc_id'] == args.doc_id]
    if len(matches) != 1:
        raise RuntimeError(f'doc{args.doc_id} count={len(matches)}')
    payload = {'model': 'Qwen3.8-Flash-Next',
               'messages': json.loads(matches[0]['arguments']['gen_args_0']['arg_0'][0]),
               'temperature': 0.0, 'top_p': 0.95, 'top_k': 20, 'min_p': 0.0,
               'presence_penalty': 0.0, 'repetition_penalty': 1.0,
               'max_tokens': 64, 'seed': 1234, 'stream': False,
               'logprobs': True, 'top_logprobs': 5}
    out = probe.ROOT / f'doc{args.doc_id}-matched-logprobs'
    out.mkdir(exist_ok=False)
    rows = {}
    for port in (8000, 8010):
        rows[port] = []
        for repeat in (1, 2):
            probe.check()
            req = urllib.request.Request(f'http://127.0.0.1:{port}/v1/chat/completions',
                data=json.dumps(payload, ensure_ascii=False).encode(),
                headers={'Content-Type': 'application/json'}, method='POST')
            with urllib.request.urlopen(req, timeout=180) as response:
                if response.status != 200:
                    raise RuntimeError(f'port{port} status={response.status}')
                body = json.loads(response.read())
            (out / f'port{port}-repeat{repeat}.json').write_text(json.dumps(body, indent=2, ensure_ascii=False) + '\n')
            choice = body['choices'][0]
            msg = choice['message']
            text = (msg.get('reasoning') or msg.get('reasoning_content') or '') + '\0' + (msg.get('content') or '')
            lp = (choice.get('logprobs') or {}).get('content') or []
            no_lp = json.loads((probe.ROOT / 'probe-ldpath-matched' / f'doc{args.doc_id}-port{port}-repeat1.json').read_text())
            rows[port].append({'text_sha256': probe.sha(text),
                               'same_as_no_logprobs': probe.sha(text) == no_lp['text_sha256'],
                               'logprobs': lp})
    probe.check()
    a, b = rows[8000][0]['logprobs'], rows[8010][0]['logprobs']
    if len(a) != 64 or len(b) != 64:
        raise RuntimeError(f'logprob coverage mismatch: {len(a)}, {len(b)}')
    first = next((i for i in range(64) if a[i]['bytes'] != b[i]['bytes']), None)
    detail = None
    if first is not None:
        detail = {'one_based_index': first + 1,
                  '8000': {'chosen': a[first]['token'],
                           'top': [{'token': x['token'], 'logprob': x['logprob']} for x in a[first]['top_logprobs']]},
                  '8010': {'chosen': b[first]['token'],
                           'top': [{'token': x['token'], 'logprob': x['logprob']} for x in b[first]['top_logprobs']]}}
    summary = {'doc_id': args.doc_id, 'prompt_hash': matches[0]['prompt_hash'],
               'first_divergent_token': detail,
               '8000_repeat_identical': rows[8000][0]['text_sha256'] == rows[8000][1]['text_sha256'],
               '8010_repeat_identical': rows[8010][0]['text_sha256'] == rows[8010][1]['text_sha256'],
               '8000_same_as_no_logprobs': rows[8000][0]['same_as_no_logprobs'],
               '8010_same_as_no_logprobs': rows[8010][0]['same_as_no_logprobs']}
    (out / 'summary.json').write_text(json.dumps(summary, indent=2, ensure_ascii=False, sort_keys=True) + '\n')
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))


if __name__ == '__main__':
    main()
