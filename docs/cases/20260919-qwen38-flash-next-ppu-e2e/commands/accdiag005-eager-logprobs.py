#!/usr/bin/env python3
"""Compare eager token probabilities with matched graph on the same cards."""

import argparse
import json
import urllib.request
from pathlib import Path

import importlib.util

BASE = Path('/mnt/nfs/users/jinghao/qwen3.8-flash/20260919-qwen38-flash-next-ppu-e2e/commands')
spec = importlib.util.spec_from_file_location('stage_probe', BASE / 'accdiag005-short-probe.py')
stage_probe = importlib.util.module_from_spec(spec)
spec.loader.exec_module(stage_probe)


def first_diff(a, b):
    return next((i for i, (x, y) in enumerate(zip(a, b)) if x['bytes'] != y['bytes']), None)


def token_detail(index, a, b):
    if index is None:
        return None
    return {'one_based_index': index + 1,
            'a': {'chosen': a[index]['token'],
                  'top': [{'token': x['token'], 'logprob': x['logprob']} for x in a[index]['top_logprobs']]},
            'b': {'chosen': b[index]['token'],
                  'top': [{'token': x['token'], 'logprob': x['logprob']} for x in b[index]['top_logprobs']]}}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--doc-id', type=int, choices=stage_probe.DOC_IDS, required=True)
    args = parser.parse_args()
    identity = stage_probe.check('eager')
    case = stage_probe.probe.prompts()[args.doc_id]
    payload = {'model': 'Qwen3.8-Flash-Next', 'messages': case['messages'],
               'temperature': 0.0, 'top_p': 0.95, 'top_k': 20, 'min_p': 0.0,
               'presence_penalty': 0.0, 'repetition_penalty': 1.0,
               'max_tokens': 64, 'seed': 1234, 'stream': False,
               'logprobs': True, 'top_logprobs': 5}
    out = stage_probe.ROOT / f'eager-logprobs-doc{args.doc_id}'
    out.mkdir(exist_ok=False)
    results = {}
    for port in (8000, 8010):
        results[port] = []
        for repeat in (1, 2):
            if stage_probe.check('eager') != identity:
                raise RuntimeError('service identity changed')
            req = urllib.request.Request(f'http://127.0.0.1:{port}/v1/chat/completions',
                data=json.dumps(payload, ensure_ascii=False).encode(),
                headers={'Content-Type': 'application/json'}, method='POST')
            with urllib.request.urlopen(req, timeout=180) as response:
                if response.status != 200:
                    raise RuntimeError(f'port{port} status={response.status}')
                body = json.loads(response.read())
            (out / f'port{port}-repeat{repeat}.json').write_text(json.dumps(body, ensure_ascii=False, indent=2) + '\n')
            choice = body['choices'][0]
            msg = choice['message']
            text = (msg.get('reasoning') or msg.get('reasoning_content') or '') + '\0' + (msg.get('content') or '')
            lp = (choice.get('logprobs') or {}).get('content') or []
            prior = json.loads((stage_probe.ROOT / 'probe-eager' / f'doc{args.doc_id}-port{port}-repeat1.json').read_text())
            results[port].append({'text_sha256': stage_probe.probe.sha(text),
                                  'same_as_no_logprobs': stage_probe.probe.sha(text) == prior['text_sha256'],
                                  'logprobs': lp})
    if stage_probe.check('eager') != identity:
        raise RuntimeError('service identity changed after probe')
    eager8000 = results[8000][0]['logprobs']
    eager8010 = results[8010][0]['logprobs']
    graph_dir = stage_probe.probe.ROOT / f'doc{args.doc_id}-matched-logprobs'
    graph = json.loads((graph_dir / 'port8000-repeat1.json').read_text())
    graph_choice = graph['body']['choices'][0] if 'body' in graph else graph['choices'][0]
    graph8000 = (graph_choice.get('logprobs') or {}).get('content') or []
    if any(len(x) != 64 for x in (eager8000, eager8010, graph8000)):
        raise RuntimeError('incomplete 64-token logprob coverage')
    summary = {'doc_id': args.doc_id, 'prompt_hash': case['prompt_hash'],
               '8000_start_ticks': identity[0], '8010_start_ticks': identity[1],
               '8000_same_as_no_logprobs': results[8000][0]['same_as_no_logprobs'],
               '8010_same_as_no_logprobs': results[8010][0]['same_as_no_logprobs'],
               '8000_repeat_identical': results[8000][0]['text_sha256'] == results[8000][1]['text_sha256'],
               '8010_repeat_identical': results[8010][0]['text_sha256'] == results[8010][1]['text_sha256'],
               'eager_8000_vs_graph_8000': token_detail(first_diff(eager8000, graph8000), eager8000, graph8000),
               'eager_8000_vs_graph_8010': token_detail(first_diff(eager8000, eager8010), eager8000, eager8010)}
    (out / 'summary.json').write_text(json.dumps(summary, indent=2, ensure_ascii=False, sort_keys=True) + '\n')
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))


if __name__ == '__main__':
    main()
