#!/usr/bin/env python3
"""Read-only final service/source audit plus a tiny restored-8000 C1/C8 smoke."""

import concurrent.futures
import hashlib
import importlib.util
import json
import subprocess
import time
import urllib.request
from pathlib import Path

ROOT = Path('/mnt/nfs/users/jinghao/qwen3.8-flash/20260919-qwen38-flash-next-ppu-e2e/accuracy/acc-010-full-gpqa-dual-user-services-20260923/diagnostics/accdiag-003-cache-abi-graph-output-20260923')
CONTROLLER = Path('/mnt/nfs/users/jinghao/qwen3.8-flash/20260919-qwen38-flash-next-ppu-e2e/commands/accdiag003-transition-8000.py')
CONTAINER = 'qwen3.8-flash-opt-candidate-20260919'

spec = importlib.util.spec_from_file_location('controller', CONTROLLER)
controller = importlib.util.module_from_spec(spec)
spec.loader.exec_module(controller)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def request():
    payload = {'model': 'Qwen3.8-Flash-Next', 'messages': [{'role': 'user', 'content': 'Reply with A.'}],
               'temperature': 0.0, 'top_p': 0.95, 'top_k': 20, 'min_p': 0.0,
               'presence_penalty': 0.0, 'repetition_penalty': 1.0, 'max_tokens': 16,
               'stream': False}
    req = urllib.request.Request('http://127.0.0.1:8000/v1/chat/completions',
                                 data=json.dumps(payload).encode(),
                                 headers={'Content-Type': 'application/json'}, method='POST')
    started = time.monotonic()
    with urllib.request.urlopen(req, timeout=120) as response:
        body = json.loads(response.read())
    choice = body['choices'][0]
    if not (choice['message'].get('content') or choice['message'].get('reasoning') or
            choice['message'].get('reasoning_content')):
        raise RuntimeError('empty smoke response')
    return {'finish_reason': choice.get('finish_reason'), 'completion_tokens': body.get('usage', {}).get('completion_tokens'),
            'elapsed_seconds': round(time.monotonic() - started, 3)}


def main():
    preflight = json.loads((ROOT / 'preflight.json').read_text())
    restored = json.loads((ROOT / 'stage-restored-original.json').read_text())
    controller.check_8010(preflight)
    controller.check_evaluator_idle()
    current = controller.process_facts(8000)
    if current is None or current['start_ticks'] != restored['service']['start_ticks']:
        raise RuntimeError('restored 8000 identity changed')
    if current['selected_environment'].get('PYTHONPATH') not in (None, '', '/workspace/vllm-plugin-FL-qwen38-adaptation'):
        raise RuntimeError('restored 8000 imports a private source')
    if current['selected_environment'].get('CUDA_VISIBLE_DEVICES') != '8,9,10,11,12,13,14,15':
        raise RuntimeError('restored 8000 device group changed')
    if not controller.port_ready(8000):
        raise RuntimeError('restored 8000 is unhealthy')
    controller.check_8000_idle()
    baselines = preflight['source_file_sha256']
    private = '/workspace/vllm-plugin-FL-qwen38-accdiag003'
    original = '/workspace/vllm-plugin-FL-qwen38-adaptation'
    hashes = {}
    for relative in baselines:
        for label, base in (('private', private), ('original', original)):
            output = subprocess.check_output(['docker', 'exec', CONTAINER, 'sha256sum', f'{base}/{relative}'], text=True)
            actual = output.split()[0]
            if actual != baselines[relative]:
                raise RuntimeError(f'{label} source drift: {relative}: {actual}')
            hashes[f'{label}/{relative}'] = actual
    smoke_c1 = [request(), request()]
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
        smoke_c8 = list(pool.map(lambda _: request(), range(8)))
    controller.check_8010(preflight)
    controller.check_8000_idle()
    output = {'8000_start_ticks': current['start_ticks'],
              '8010_start_ticks': controller.process_facts(8010)['start_ticks'],
              'restored_import': restored['import_resolution'], 'source_hashes': hashes,
              'c1': smoke_c1, 'c8': smoke_c8, 'completed_at_epoch': time.time(),
              'status': 'passed'}
    path = ROOT / 'final-audit.json'
    if path.exists():
        raise RuntimeError('final audit already exists')
    path.write_text(json.dumps(output, indent=2, sort_keys=True) + '\n')
    print(json.dumps({'status': output['status'], 'c1': len(smoke_c1), 'c8': len(smoke_c8),
                      '8000_start_ticks': output['8000_start_ticks'],
                      '8010_start_ticks': output['8010_start_ticks'], 'receipt': str(path)}))


if __name__ == '__main__':
    main()
