#!/usr/bin/env python3
"""Snapshot exact live service and private-source facts before diagnostic changes."""

import hashlib
import json
import os
import shutil
import subprocess
from pathlib import Path

CONTAINER = 'qwen3.8-flash-opt-candidate-20260919'
EVAL_CONTAINER = 'qwen38-eval-e2e-20260919'
SOURCE = '/workspace/vllm-plugin-FL-qwen38-adaptation'
PRIVATE = '/workspace/vllm-plugin-FL-qwen38-accdiag003'
CASE = Path('/mnt/nfs/users/jinghao/qwen3.8-flash/20260919-qwen38-flash-next-ppu-e2e/accuracy/acc-010-full-gpqa-dual-user-services-20260923')
OUT = CASE / 'diagnostics/accdiag-003-cache-abi-graph-output-20260923'
FILES = (
    'vllm_fl/models/qwen3_8_flash_next.py',
    'vllm_fl/compilation/graph.py',
    'vllm_fl/ops/_C_ops_registry.py',
)
ENV_KEYS = (
    'CUDA_VISIBLE_DEVICES', 'PYTHONPATH', 'VLLM_WORKER_MULTIPROC_METHOD',
    'VLLM_EXECUTE_MODEL_TIMEOUT_SECONDS', 'VLLM_FL_FLAGOS_BLACKLIST_APPEND',
    'VLLM_FL_QSA_STATIC_SCORE_COLUMNS', 'VLLM_TUNED_CONFIG_FOLDER',
    'NCCL_IB_HCA', 'NCCL_IB_GID_INDEX', 'NCCL_IB_ADDR_FAMILY',
    'NCCL_SOCKET_IFNAME', 'NCCL_SOCKET_FAMILY', 'GLOO_SOCKET_IFNAME',
)


def run(argv):
    return subprocess.run(argv, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True).stdout


def docker_exec(*argv):
    return run(['docker', 'exec', CONTAINER, *argv])


def sha(data):
    return hashlib.sha256(data).hexdigest()


def process_facts():
    found = []
    for item in os.scandir('/proc'):
        if not item.name.isdigit():
            continue
        path = Path(item.path)
        try:
            args = [s.decode(errors='replace') for s in (path / 'cmdline').read_bytes().split(b'\0') if s]
            if 'serve' not in args or '--port' not in args or '/mnt/cpfs/models/Qwen3.8-Flash-Next' not in args:
                continue
            port = args[args.index('--port') + 1]
            if port not in ('8000', '8010'):
                continue
            raw_env = (path / 'environ').read_bytes().split(b'\0')
            env = {}
            for entry in raw_env:
                if b'=' in entry:
                    key, value = entry.split(b'=', 1)
                    key = key.decode(errors='replace')
                    if key in ENV_KEYS:
                        env[key] = value.decode(errors='replace')
            stat = (path / 'stat').read_text()
            found.append({
                'port': int(port), 'host_pid': int(item.name),
                'start_ticks': int(stat[stat.rfind(')') + 2:].split()[19]),
                'argv': args, 'selected_environment': env,
                'cwd': os.readlink(path / 'cwd'),
            })
        except (FileNotFoundError, PermissionError, ProcessLookupError):
            continue
    found.sort(key=lambda x: x['port'])
    if [x['port'] for x in found] != [8000, 8010]:
        raise RuntimeError(f'expected exact two target services: {found}')
    if found[0]['selected_environment'].get('CUDA_VISIBLE_DEVICES') != '8,9,10,11,12,13,14,15':
        raise RuntimeError('8000 device set differs')
    if found[1]['selected_environment'].get('CUDA_VISIBLE_DEVICES') != '0,1,2,3,4,5,6,7':
        raise RuntimeError('8010 device set differs')
    return found


def main():
    parent = OUT.parent.resolve(strict=True)
    if parent != (CASE / 'diagnostics').resolve(strict=True):
        raise RuntimeError('diagnostics parent path changed')
    if OUT.exists():
        raise RuntimeError(f'refusing existing experiment directory {OUT}')
    if not CASE.is_dir() or not os.access(CASE, os.W_OK):
        raise RuntimeError('case root not writable')
    free = shutil.disk_usage(CASE).free
    if free < 10 * 1024**3:
        raise RuntimeError('less than 10 GiB free on case filesystem')
    inspect = json.loads(run(['docker', 'inspect', CONTAINER]))[0]
    if not inspect['State']['Running']:
        raise RuntimeError('optimization container not running')
    mounts = [{k: m.get(k) for k in ('Type', 'Source', 'Destination', 'Mode', 'RW', 'Propagation')}
              for m in inspect['Mounts']]
    if any(m['Destination'] == '/workspace' or SOURCE.startswith(m['Destination'].rstrip('/') + '/')
           for m in mounts):
        raise RuntimeError('Plugin source may be mount-backed')
    private_exists = subprocess.run(['docker', 'exec', CONTAINER, 'test', '-e', PRIVATE], check=False).returncode == 0
    if private_exists:
        raise RuntimeError('private experiment copy already exists')

    services = process_facts()
    if services[0]['argv'][:3] != services[1]['argv'][:3]:
        raise RuntimeError('unexpected argv prefix discrepancy')
    statuses = {}
    for port in (8000, 8010):
        response = run(['curl', '-fsS', '--max-time', '5', f'http://127.0.0.1:{port}/v1/models'])
        statuses[str(port)] = {'sha256': sha(response.encode()), 'model_ids': [x['id'] for x in json.loads(response)['data']]}
    evaluator_processes = run(['docker', 'top', EVAL_CONTAINER])
    if any(x in evaluator_processes for x in ('formal_accuracy.py', 'llmrun.py')):
        raise RuntimeError('formal evaluator process is active')
    git_status = docker_exec('git', '-C', SOURCE, 'status', '--short')
    git_head = docker_exec('git', '-C', SOURCE, 'rev-parse', 'HEAD').strip()
    git_diff = docker_exec('git', '-C', SOURCE, 'diff', '--binary')
    files = {}
    for rel in FILES:
        data = subprocess.run(['docker', 'exec', CONTAINER, 'sha256sum', f'{SOURCE}/{rel}'],
                              check=True, stdout=subprocess.PIPE, text=True).stdout
        files[rel] = data.split()[0]
    import_test = docker_exec('python3', '-c', 'import vllm_fl; print(vllm_fl.__file__)').strip()
    OUT.mkdir(mode=0o755)
    (OUT / 'baseline-plugin.diff').write_text(git_diff)
    facts = {
        'schema_version': 1, 'container': CONTAINER, 'image_id': inspect['Image'],
        'mounts': mounts, 'free_bytes': free, 'services': services,
        'models_endpoints': statuses, 'plugin_source': SOURCE,
        'plugin_import_test': import_test, 'plugin_git_head': git_head,
        'plugin_git_status': git_status, 'plugin_diff_sha256': sha(git_diff.encode()),
        'source_file_sha256': files, 'evaluator_formal_process_active': False,
        'private_copy_target': PRIVATE,
    }
    (OUT / 'preflight.json').write_text(json.dumps(facts, indent=2, sort_keys=True) + '\n')
    print(json.dumps({
        'out': str(OUT), 'image_id': inspect['Image'], 'mounts': mounts,
        'services': [{'port': s['port'], 'host_pid': s['host_pid'], 'start_ticks': s['start_ticks'],
                      'devices': s['selected_environment'].get('CUDA_VISIBLE_DEVICES'),
                      'pythonpath': s['selected_environment'].get('PYTHONPATH')} for s in services],
        'plugin_git_head': git_head, 'plugin_git_status': git_status,
        'plugin_import_test': import_test, 'diff_sha256': facts['plugin_diff_sha256'],
    }, sort_keys=True))


if __name__ == '__main__':
    main()
