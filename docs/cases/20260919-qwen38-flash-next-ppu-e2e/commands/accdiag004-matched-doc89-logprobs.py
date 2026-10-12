#!/usr/bin/env python3
"""Doc89 first-token probabilities after restoring matched library paths."""

import glob
import hashlib
import importlib.util
import json
import urllib.request
from pathlib import Path

CASE = Path('/mnt/nfs/users/jinghao/qwen3.8-flash/20260919-qwen38-flash-next-ppu-e2e/accuracy/acc-010-full-gpqa-dual-user-services-20260923')
PREV = CASE / 'diagnostics/accdiag-003-cache-abi-graph-output-20260923'
ROOT = CASE / 'diagnostics/accdiag-004-first-divergent-token-20260923'
CONTROLLER = Path('/mnt/nfs/users/jinghao/qwen3.8-flash/20260919-qwen38-flash-next-ppu-e2e/commands/accdiag003-transition-8000.py')
spec = importlib.util.spec_from_file_location('controller', CONTROLLER)
controller = importlib.util.module_from_spec(spec)
spec.loader.exec_module(controller)


def sha(text):
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


def check():
    before = json.loads((PREV / 'preflight.json').read_text())
    stage = json.loads((ROOT / 'ldpath-matched-stage.json').read_text())
    controller.check_8010(before)
    controller.check_evaluator_idle()
    current = controller.process_facts(8000)
    if not current or current['start_ticks'] != stage['service']['start_ticks']:
        raise RuntimeError('matched 8000 identity changed')
    if not controller.port_ready(8000):
        raise RuntimeError('8000 unhealthy')
    controller.check_8000_idle()


def main():
    check()
    paths = glob.glob(str(CASE / 'results/**/samples_gpqa_diamond_generative_cot_*.jsonl'), recursive=True)
    if len(paths) != 1:
        raise RuntimeError(paths)
    rows = [json.loads(line) for line in open(paths[0], encoding='utf-8')]
    samples = [row for row in rows if row.get('filter') == 'strict-match' and row['doc_id'] == 89]
    if len(samples) != 1:
        raise RuntimeError(f'doc89 count={len(samples)}')
    payload = {'model': 'Qwen3.8-Flash-Next',
               'messages': json.loads(samples[0]['arguments']['gen_args_0']['arg_0'][0]),
               'temperature': 0.0, 'top_p': 0.95, 'top_k': 20, 'min_p': 0.0,
               'presence_penalty': 0.0, 'repetition_penalty': 1.0,
               'max_tokens': 64, 'seed': 1234, 'stream': False,
               'logprobs': True, 'top_logprobs': 5}
    out = ROOT / 'doc89-matched-logprobs'
    out.mkdir(exist_ok=False)
    manifest = {'prompt_hash': samples[0]['prompt_hash'],
                'request_sha256': sha(json.dumps(payload, sort_keys=True, ensure_ascii=False)),
                '8000_start_ticks': controller.process_facts(8000)['start_ticks'],
                '8010_start_ticks': controller.process_facts(8010)['start_ticks']}
    (out / 'manifest.json').write_text(json.dumps(manifest, indent=2, sort_keys=True) + '\n')
    result = {}
    for port in (8000, 8010):
        result[port] = []
        for repeat in (1, 2):
            check()
            req = urllib.request.Request(f'http://127.0.0.1:{port}/v1/chat/completions',
                data=json.dumps(payload, ensure_ascii=False).encode(),
                headers={'Content-Type': 'application/json'}, method='POST')
            with urllib.request.urlopen(req, timeout=180) as response:
                body = json.loads(response.read())
                if response.status != 200:
                    raise RuntimeError(f'{port} status={response.status}')
            (out / f'port{port}-repeat{repeat}.json').write_text(json.dumps(body, indent=2, ensure_ascii=False) + '\n')
            choice = body['choices'][0]
            msg = choice['message']
            text = (msg.get('reasoning') or msg.get('reasoning_content') or '') + '\0' + (msg.get('content') or '')
            lp = (choice.get('logprobs') or {}).get('content') or []
            no_lp = json.loads((ROOT / 'probe-ldpath-matched' / f'doc89-port{port}-repeat1.json').read_text())
            result[port].append({'text_sha256': sha(text), 'same_as_no_logprobs': sha(text) == no_lp['text_sha256'],
                                 'logprobs': lp, 'completion_tokens': body.get('usage', {}).get('completion_tokens')})
    check()
    a, b = result[8000][0]['logprobs'], result[8010][0]['logprobs']
    if len(a) != 64 or len(b) != 64:
        raise RuntimeError(f'logprob coverage mismatch: {len(a)}, {len(b)}')
    first = next((i for i in range(64) if a[i]['bytes'] != b[i]['bytes']), None)
    detail = None
    if first is not None:
        detail = {'zero_based_index': first, 'one_based_index': first + 1,
                  '8000': {'chosen': a[first]['token'], 'chosen_logprob': a[first]['logprob'],
                           'top': [{'token': x['token'], 'logprob': x['logprob']} for x in a[first]['top_logprobs']]},
                  '8010': {'chosen': b[first]['token'], 'chosen_logprob': b[first]['logprob'],
                           'top': [{'token': x['token'], 'logprob': x['logprob']} for x in b[first]['top_logprobs']]}}
    summary = {'manifest': manifest, 'first_divergent_token': detail,
               '8000_repeat_identical': result[8000][0]['text_sha256'] == result[8000][1]['text_sha256'],
               '8010_repeat_identical': result[8010][0]['text_sha256'] == result[8010][1]['text_sha256'],
               '8000_same_as_no_logprobs': result[8000][0]['same_as_no_logprobs'],
               '8010_same_as_no_logprobs': result[8010][0]['same_as_no_logprobs']}
    (out / 'summary.json').write_text(json.dumps(summary, indent=2, ensure_ascii=False, sort_keys=True) + '\n')
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))


if __name__ == '__main__':
    main()
