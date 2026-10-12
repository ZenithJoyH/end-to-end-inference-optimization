#!/usr/bin/env python3
"""Create a byte-identical private Plugin copy; do not touch live services."""

import hashlib
import json
import subprocess
from pathlib import Path

CONTAINER = 'qwen3.8-flash-opt-candidate-20260919'
SOURCE = '/workspace/vllm-plugin-FL-qwen38-adaptation'
PRIVATE = '/workspace/vllm-plugin-FL-qwen38-accdiag003'
OUT = Path('/mnt/nfs/users/jinghao/qwen3.8-flash/20260919-qwen38-flash-next-ppu-e2e/accuracy/acc-010-full-gpqa-dual-user-services-20260923/diagnostics/accdiag-003-cache-abi-graph-output-20260923')


def run(*args, env=None):
    return subprocess.run(args, check=True, capture_output=True, text=True, env=env).stdout.strip()


def dexec(*args):
    return run('docker', 'exec', CONTAINER, *args)


def file_sha(path):
    return dexec('sha256sum', path).split()[0]


def main():
    facts = json.loads((OUT / 'preflight.json').read_text())
    if facts['container'] != CONTAINER or facts['plugin_source'] != SOURCE:
        raise RuntimeError('preflight identity mismatch')
    if (OUT / 'private-prepared.json').exists():
        raise RuntimeError('private copy already recorded')
    if subprocess.run(['docker', 'exec', CONTAINER, 'test', '-e', PRIVATE]).returncode == 0:
        raise RuntimeError('private target already exists')
    current = {rel: file_sha(f'{SOURCE}/{rel}') for rel in facts['source_file_sha256']}
    if current != facts['source_file_sha256']:
        raise RuntimeError('baseline source changed since preflight')
    dexec('cp', '-a', SOURCE, PRIVATE)
    copied = {rel: file_sha(f'{PRIVATE}/{rel}') for rel in current}
    if copied != current:
        raise RuntimeError('private copy file hash mismatch')
    imported = run('docker', 'exec', '--env', f'PYTHONPATH={PRIVATE}', CONTAINER,
                   'python3', '-c', 'import vllm_fl; print(vllm_fl.__file__)')
    if imported != f'{PRIVATE}/vllm_fl/__init__.py':
        raise RuntimeError(f'private import did not resolve: {imported}')
    status = dexec('git', '-C', PRIVATE, 'status', '--short')
    if status != facts['plugin_git_status'].strip():
        raise RuntimeError('private git status differs from original')
    receipt = {'source': SOURCE, 'private': PRIVATE, 'source_sha256': current,
               'private_sha256': copied, 'import_path': imported,
               'git_status_sha256': hashlib.sha256(status.encode()).hexdigest()}
    (OUT / 'private-prepared.json').write_text(json.dumps(receipt, indent=2, sort_keys=True) + '\n')
    print(json.dumps({'private': PRIVATE, 'import_path': imported,
                      'file_hashes_equal': copied == current, 'git_status_equal': True}, sort_keys=True))


if __name__ == '__main__':
    main()
