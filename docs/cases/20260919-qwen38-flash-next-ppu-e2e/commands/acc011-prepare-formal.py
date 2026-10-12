#!/usr/bin/env python3
"""Freeze acc-011 dual-service formal GPQA contract from the acc-010 bundle."""

import hashlib
import json
import shutil
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

ROOT = Path('/mnt/nfs/users/jinghao/qwen3.8-flash/20260919-qwen38-flash-next-ppu-e2e')
OLD = ROOT / 'accuracy/acc-010-full-gpqa-dual-user-services-20260923'
CASE = ROOT / 'accuracy/acc-011-full-gpqa-dual-cachefix-20260924'
MODEL_CONTAINER = 'qwen3.8-flash-opt-candidate-20260919'
EVAL_CONTAINER = 'qwen38-eval-e2e-20260919'
PRIVATE = '/opt/qwen38-acc011-cachefix-20260924/FlagGems'


def run(argv, output=None):
    result = subprocess.run(argv, check=True, capture_output=True)
    if output is not None:
        if output.exists():
            raise RuntimeError(f'output already exists: {output}')
        output.write_bytes(result.stdout)
    return result.stdout


def write_new(path, data):
    if path.exists():
        raise RuntimeError(f'output already exists: {path}')
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + '\n')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def model(port):
    with urllib.request.urlopen(f'http://127.0.0.1:{port}/v1/models', timeout=10) as response:
        body = json.load(response)
    if not any(item.get('id') == 'Qwen3.8-Flash-Next' for item in body.get('data', [])):
        raise RuntimeError(f'wrong model on {port}')
    return body


def idle(port):
    with urllib.request.urlopen(f'http://127.0.0.1:{port}/metrics', timeout=10) as response:
        lines = response.read().decode().splitlines()
    for key in ('vllm:num_requests_running', 'vllm:num_requests_waiting'):
        values = [float(line.rsplit(' ', 1)[1]) for line in lines if line.startswith(key + '{')]
        if not values or any(value != 0 for value in values):
            raise RuntimeError(f'{port} not idle: {key}={values}')


def main():
    if (CASE / 'evaluation/PREPARED').exists() or (CASE / 'bundle').exists():
        raise RuntimeError('acc-011 formal already prepared')
    if (CASE / 'evaluation/minimal-port8000.json').exists() is False or (CASE / 'evaluation/minimal-port8010.json').exists() is False:
        raise RuntimeError('minimal regression evidence missing')
    for port in (8000, 8010):
        receipt = json.loads((CASE / f'services/port{port}-ready.json').read_text())
        if receipt['import'] != PRIVATE + '/src/flag_gems/utils/models/sql.py':
            raise RuntimeError(f'wrong source on {port}')
        if json.loads((CASE / f'evaluation/minimal-port{port}.json').read_text())['status'] != 'passed':
            raise RuntimeError(f'minimal regression failed on {port}')
        write_new(CASE / f'services/models-{port}.json', model(port))
        idle(port)
    top = run(['docker', 'top', EVAL_CONTAINER]).decode()
    if any(name in top for name in ('formal_accuracy.py', 'llmrun.py', 'lm_eval')):
        raise RuntimeError('evaluator already active')
    run(['docker', 'inspect', MODEL_CONTAINER], CASE / 'evidence/model-container.inspect.json')
    run(['docker', 'inspect', EVAL_CONTAINER], CASE / 'evidence/evaluator.inspect.json')
    shutil.copytree(OLD / 'bundle', CASE / 'bundle')
    shutil.copy2(OLD / 'commands/dual-service-proxy.py', CASE / 'commands/dual-service-proxy.py')

    fingerprint_script = str(ROOT / 'commands/op023_source_fingerprint.py')
    run(['docker', 'exec', MODEL_CONTAINER, 'python3', fingerprint_script,
         '--output', str(CASE / 'evidence/source.original.json')])
    original = json.loads((CASE / 'evidence/source.original.json').read_text())
    code = ('import json,runpy; m=runpy.run_path(' + repr(fingerprint_script) + '); '
            'print(json.dumps(m["repo_record"](' + repr(PRIVATE) + ')))')
    private = json.loads(run(['docker', 'exec', MODEL_CONTAINER, 'python3', '-c', code]))
    write_new(CASE / 'evidence/source.private.json', private)

    old_manifest = json.loads((OLD / 'services/service-manifest.prototype.json').read_text())
    repos = original['repositories']
    if (repos['/workspace/vllm-plugin-FL-qwen38-adaptation']['content_sha256'] != old_manifest['plugin_sha256']
        or repos['/workspace/FlagGems-vllm']['content_sha256'] != old_manifest['flaggems_vllm_sha256']):
        raise RuntimeError('Plugin or FlagGems-vllm drifted since acc-010')
    runtime = {'schema_version': 1, 'replicas': []}
    for port in (8000, 8010):
        current = json.loads((CASE / f'services/port{port}-ready.json').read_text())
        runtime['replicas'].append({'port': port, 'pid': current['pid'],
                                    'start_ticks': current['start_ticks'],
                                    'argv': current['argv'],
                                    'selected_environment': current['env'],
                                    'flag_gems_import': current['import']})
    write_new(CASE / 'services/services-runtime.json', runtime)
    manifest = old_manifest
    manifest['flaggems_sha256'] = private['content_sha256']
    manifest['service_instance_id'] = 'pending-proxy-runtime'
    manifest['runtime_evidence_sha256'] = '0' * 64
    manifest['launch_config']['replicas'] = runtime['replicas']
    manifest['launch_config']['flag_gems_cache_fix'] = {
        'private_source': PRIVATE, 'patch_sha256': sha(CASE / 'evidence/flag_gems_sql.patch'),
        'cache_urls': {str(port): runtime['replicas'][i]['selected_environment']['FLAGGEMS_DB_URL']
                       for i, port in enumerate((8000, 8010))},
        'journal_mode': 'WAL',
    }
    manifest['performance_context']['cache_preparation'] = (
        'Two TP8 graph replicas, same private FlagGems SQLite lock fix, separate WAL DB snapshots, prefix caching disabled.'
    )
    write_new(CASE / 'services/service-manifest.prototype.json', manifest)

    old_config = json.loads((OLD / 'evaluation/llm-config.json').read_text())
    config = dict(old_config)
    config.update({'eval_model': 'Qwen3.8-Flash-Next-dual-cachefix-20260924',
                   'output_root': str(CASE / 'results'),
                   'cache_root': '/tmp/qwen38-acc011-full-gpqa-cache-20260924',
                   'run_id': 'acc011-full-gpqa-dual-cachefix-20260924'})
    if {k: v for k, v in config.items() if k not in ('eval_model', 'output_root', 'cache_root', 'run_id')} != {
        k: v for k, v in old_config.items() if k not in ('eval_model', 'output_root', 'cache_root', 'run_id')
    }:
        raise RuntimeError('unexpected accuracy-config drift')
    write_new(CASE / 'evaluation/llm-config.json', config)

    repo = CASE / 'bundle/repo'
    for number in (1, 2):
        run(['docker', 'exec', EVAL_CONTAINER, 'python3',
             str(repo / 'evaluation/accuracy/formal_accuracy.py'),
             '--config', str(CASE / 'evaluation/llm-config.json'),
             '--evaluation-inspect', str(CASE / 'evidence/evaluator.inspect.json'),
             '--capture-provenance', str(CASE / f'evaluation/task-provenance-{number}.json')],
            CASE / f'evaluation/provenance-{number}.log')
    first = CASE / 'evaluation/task-provenance-1.json'
    second = CASE / 'evaluation/task-provenance-2.json'
    if first.read_bytes() != second.read_bytes():
        raise RuntimeError('task provenance unstable')
    provenance = json.loads(first.read_text())
    contract = {'schema_version': 3, 'task': 'gpqa_diamond_generative_cot',
                'metric': 'exact_match,strict-match', 'expected_samples': 198,
                'expected_doc_ids': list(range(198)),
                'dataset_revision': provenance['dataset_revision'],
                'task_provenance': {'path': str(first), 'sha256': sha(first)},
                'threshold': 0.88}
    write_new(CASE / 'evaluation/contract.json', contract)
    paths = [CASE / path for path in ('evaluation/llm-config.json',
              'evaluation/task-provenance-1.json', 'evaluation/task-provenance-2.json',
              'evaluation/contract.json', 'evidence/evaluator.inspect.json',
              'services/services-runtime.json', 'services/service-manifest.prototype.json',
              'evidence/source.private.json')]
    (CASE / 'evaluation/prepared.SHA256SUMS').write_text(''.join(f'{sha(path)}  {path}\n' for path in paths))
    (CASE / 'evaluation/PREPARED').write_text(time.strftime('%Y-%m-%dT%H:%M:%S%z') + '\n')
    print(json.dumps({'status': 'prepared', 'task': contract['task'],
                      'expected_samples': contract['expected_samples'],
                      'threshold': contract['threshold'],
                      'flag_gems_sha256': private['content_sha256'],
                      'replicas': [{'port': x['port'], 'pid': x['pid'],
                                    'start_ticks': x['start_ticks']} for x in runtime['replicas']],
                      'config': str(CASE / 'evaluation/llm-config.json')}, indent=2))


if __name__ == '__main__':
    main()
