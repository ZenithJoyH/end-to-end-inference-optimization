#!/usr/bin/env python3
"""Frozen GPQA short logprob probe; abort on service identity drift."""

import argparse
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


def service_preflight():
    original = json.loads((PREV / 'preflight.json').read_text())
    restored = json.loads((PREV / 'stage-restored-original.json').read_text())
    controller.check_8010(original)
    controller.check_evaluator_idle()
    current = controller.process_facts(8000)
    if current is None or current['start_ticks'] != restored['service']['start_ticks']:
        raise RuntimeError('8000 service no longer matches restored original')
    if not controller.port_ready(8000):
        raise RuntimeError('8000 is not healthy')
    controller.check_8000_idle()
    with urllib.request.urlopen('http://127.0.0.1:8010/metrics', timeout=4) as response:
        metrics = response.read().decode(errors='replace')
    for name in ('vllm:num_requests_running', 'vllm:num_requests_waiting'):
        values = [float(line.rsplit(' ', 1)[1]) for line in metrics.splitlines()
                  if line.startswith(name + '{')]
        if not values or any(value != 0 for value in values):
            raise RuntimeError(f'8010 {name} nonzero or unavailable')
    ref = controller.process_facts(8010)
    return {'8000_start_ticks': current['start_ticks'],
            '8010_start_ticks': ref['start_ticks'],
            '8000_argv_sha256': sha(json.dumps(current['argv'], sort_keys=True)),
            '8010_argv_sha256': sha(json.dumps(ref['argv'], sort_keys=True))}


def prompt_for(doc_id):
    paths = glob.glob(str(CASE / 'results/**/samples_gpqa_diamond_generative_cot_*.jsonl'), recursive=True)
    if len(paths) != 1:
        raise RuntimeError(f'unexpected formal samples: {paths}')
    found = []
    with open(paths[0], encoding='utf-8') as file:
        for line in file:
            row = json.loads(line)
            if row.get('filter') == 'strict-match' and row.get('doc_id') == doc_id:
                found.append(row)
    if len(found) != 1:
        raise RuntimeError(f'doc {doc_id} strict-match count={len(found)}')
    row = found[0]
    return json.loads(row['arguments']['gen_args_0']['arg_0'][0]), row['prompt_hash']


def post(port, payload):
    request = urllib.request.Request(f'http://127.0.0.1:{port}/v1/chat/completions',
        data=json.dumps(payload, ensure_ascii=False).encode('utf-8'),
        headers={'Content-Type': 'application/json'}, method='POST')
    start = time.monotonic()
    with urllib.request.urlopen(request, timeout=180) as response:
        body = json.loads(response.read())
        status = response.status
    return status, body, round(time.monotonic() - start, 3)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--doc-id', type=int, choices=DOC_IDS, required=True)
    parser.add_argument('--repeats', type=int, choices=(1, 2), default=2)
    args = parser.parse_args()
    identity = service_preflight()
    messages, prompt_hash = prompt_for(args.doc_id)
    payload = {'model': 'Qwen3.8-Flash-Next', 'messages': messages,
               'temperature': 0.0, 'top_p': 0.95, 'top_k': 20, 'min_p': 0.0,
               'presence_penalty': 0.0, 'repetition_penalty': 1.0,
               'max_tokens': 64, 'seed': 1234, 'stream': False,
               'logprobs': True, 'top_logprobs': 5}
    previous_summary = json.loads((PREV / 'probe-graph-revert' / 'summary.json').read_text())
    if args.doc_id not in {int(x['doc_id']) for x in previous_summary['rows']}:
        raise RuntimeError('doc missing from prior probe')
    ROOT.mkdir(exist_ok=True)
    out = ROOT / f'doc{args.doc_id}'
    out.mkdir(exist_ok=False)
    manifest = {'doc_id': args.doc_id, 'prompt_hash': prompt_hash,
                'request_sha256': sha(json.dumps(payload, ensure_ascii=False, sort_keys=True)),
                'repeats': args.repeats, 'identity': identity, 'started_at_epoch': time.time()}
    (out / 'manifest.json').write_text(json.dumps(manifest, indent=2, sort_keys=True) + '\n')
    summaries = []
    for port in (8000, 8010):
        for repeat in range(1, args.repeats + 1):
            if service_preflight() != identity:
                raise RuntimeError('service identity drifted during probe')
            status, body, elapsed = post(port, payload)
            choice = body['choices'][0]
            message = choice['message']
            text = (message.get('reasoning') or message.get('reasoning_content') or '') + '\0' + (message.get('content') or '')
            logprobs = (choice.get('logprobs') or {}).get('content') or []
            raw = {'http_status': status, 'body': body, 'elapsed_seconds': elapsed}
            (out / f'port{port}-repeat{repeat}.json').write_text(json.dumps(raw, ensure_ascii=False, indent=2) + '\n')
            prior = json.loads((PREV / 'probe-graph-revert' / f'doc{args.doc_id}-port{port}-repeat1.json').read_text())
            summaries.append({'port': port, 'repeat': repeat, 'http_status': status,
                              'finish_reason': choice.get('finish_reason'),
                              'completion_tokens': body.get('usage', {}).get('completion_tokens'),
                              'logprob_entries': len(logprobs), 'text_sha256': sha(text),
                              'same_text_as_no_logprobs': sha(text) == prior.get('text_sha256'),
                              'elapsed_seconds': elapsed})
    if service_preflight() != identity:
        raise RuntimeError('service identity changed after probe')
    (out / 'summary.json').write_text(json.dumps({'manifest': manifest, 'rows': summaries}, indent=2, sort_keys=True) + '\n')
    print(json.dumps({'doc_id': args.doc_id, 'rows': summaries, 'evidence': str(out)}, sort_keys=True))


if __name__ == '__main__':
    main()
