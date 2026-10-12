#!/usr/bin/env python3
"""Bounded C1/C9 graph-service regression for the SQLite cache repair."""

import argparse
import concurrent.futures
import hashlib
import json
import threading
import time
import urllib.request
from pathlib import Path

CASE = Path('/mnt/nfs/users/jinghao/qwen3.8-flash/20260919-qwen38-flash-next-ppu-e2e/accuracy/acc-011-full-gpqa-dual-cachefix-20260924')
BASE = None


def request(index, wave):
    payload = {
        'model': 'Qwen3.8-Flash-Next',
        'messages': [{'role': 'user', 'content': f'Question {index}: What is {17+index} plus {29+index}? Explain briefly, then give the integer.'}],
        'temperature': 1.0, 'top_p': 0.95, 'top_k': 20, 'min_p': 0.0,
        'presence_penalty': 0.0, 'repetition_penalty': 1.0,
        'max_completion_tokens': 192, 'seed': 1234,
    }
    raw = json.dumps(payload).encode()
    req = urllib.request.Request(BASE + '/v1/chat/completions', raw,
                                 headers={'Content-Type': 'application/json'})
    start = time.monotonic()
    try:
        with urllib.request.urlopen(req, timeout=600) as response:
            body = response.read()
            status = response.status
        parsed = json.loads(body)
        choice = parsed['choices'][0]
        return {'index': index, 'wave': wave, 'status': status,
                'elapsed_s': round(time.monotonic() - start, 3),
                'finish_reason': choice.get('finish_reason'),
                'completion_tokens': parsed.get('usage', {}).get('completion_tokens'),
                'content_sha256': hashlib.sha256(json.dumps(choice.get('message'), sort_keys=True).encode()).hexdigest(),
                'error': None}
    except Exception as exc:
        return {'index': index, 'wave': wave, 'status': None,
                'elapsed_s': round(time.monotonic() - start, 3),
                'finish_reason': None, 'completion_tokens': None,
                'content_sha256': None, 'error': repr(exc)}


def sample_metrics(stop, values):
    while not stop.is_set():
        try:
            with urllib.request.urlopen(BASE + '/metrics', timeout=3) as response:
                lines = response.read().decode().splitlines()
            for key in ('vllm:num_requests_running', 'vllm:num_requests_waiting'):
                current = [float(x.rsplit(' ', 1)[1]) for x in lines if x.startswith(key + '{')]
                if current:
                    values[key].append(max(current))
        except Exception:
            pass
        stop.wait(0.2)


def main():
    global BASE
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', type=int, choices=(8000, 8010), required=True)
    args = parser.parse_args()
    BASE = f'http://127.0.0.1:{args.port}'
    out = CASE / f'evaluation/minimal-port{args.port}.json'
    if out.exists():
        raise RuntimeError('minimal regression already recorded; refusing duplicate')
    results = [request(0, 'c1')]
    values = {'vllm:num_requests_running': [], 'vllm:num_requests_waiting': []}
    stop = threading.Event()
    sampler = threading.Thread(target=sample_metrics, args=(stop, values), daemon=True)
    sampler.start()
    for wave in ('c9-first', 'c9-replay'):
        with concurrent.futures.ThreadPoolExecutor(max_workers=9) as pool:
            futures = [pool.submit(request, i, wave) for i in range(9)]
            results.extend(future.result() for future in futures)
    stop.set()
    sampler.join(timeout=5)
    with urllib.request.urlopen(BASE + '/v1/models', timeout=5) as response:
        model = json.load(response)
    receipt = {'results': results,
               'peak_running': max(values['vllm:num_requests_running'], default=None),
               'peak_waiting': max(values['vllm:num_requests_waiting'], default=None),
               'model_id': model['data'][0]['id'],
               'status': ('passed' if all(x['status'] == 200 and x['error'] is None and
                                          isinstance(x['completion_tokens'], int) and x['completion_tokens'] > 0
                                          for x in results) else 'failed')}
    out.write_text(json.dumps(receipt, indent=2, sort_keys=True) + '\n')
    print(json.dumps({'status': receipt['status'], 'requests': len(results),
                      'peak_running': receipt['peak_running'],
                      'peak_waiting': receipt['peak_waiting'],
                      'errors': [x for x in results if x['error']]}, indent=2))
    if receipt['status'] != 'passed':
        raise SystemExit(1)


if __name__ == '__main__':
    main()
