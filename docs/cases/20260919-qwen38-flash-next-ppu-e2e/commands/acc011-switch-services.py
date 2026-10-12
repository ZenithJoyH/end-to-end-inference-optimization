#!/usr/bin/env python3
"""Precisely recover/switch only acc-011 Qwen TP8 replicas onto private FlagGems."""

import argparse
import hashlib
import json
import os
import shlex
import signal
import subprocess
import time
import urllib.request
from pathlib import Path

CONTAINER = 'qwen3.8-flash-opt-candidate-20260919'
EVAL_CONTAINER = 'qwen38-eval-e2e-20260919'
MODEL = '/mnt/cpfs/models/Qwen3.8-Flash-Next'
PRIVATE = Path('/opt/qwen38-acc011-cachefix-20260924')
CASE = Path('/mnt/nfs/users/jinghao/qwen3.8-flash/20260919-qwen38-flash-next-ppu-e2e/accuracy/acc-011-full-gpqa-dual-cachefix-20260924')
ENV_KEYS = ('CUDA_VISIBLE_DEVICES', 'LD_LIBRARY_PATH', 'VLLM_WORKER_MULTIPROC_METHOD',
            'VLLM_EXECUTE_MODEL_TIMEOUT_SECONDS', 'GLOO_SOCKET_IFNAME', 'NCCL_DEBUG',
            'NCCL_IB_DISABLE', 'NCCL_IB_HCA', 'NCCL_IB_GID_INDEX',
            'NCCL_IB_ADDR_FAMILY', 'NCCL_SOCKET_IFNAME', 'NCCL_SOCKET_FAMILY',
            'VLLM_FL_FLAGOS_BLACKLIST_APPEND', 'PYTHONDONTWRITEBYTECODE')


def run(argv):
    return subprocess.run(argv, check=True, capture_output=True, text=True)


def write_new(path, data):
    if path.exists():
        raise RuntimeError(f'receipt already exists: {path}')
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + '\n')


def process(port):
    matches = []
    for entry in os.scandir('/proc'):
        if not entry.name.isdigit():
            continue
        path = Path(entry.path)
        try:
            argv = [x.decode(errors='replace') for x in (path / 'cmdline').read_bytes().split(b'\0') if x]
            if 'serve' not in argv or '--port' not in argv or MODEL not in argv:
                continue
            if argv[argv.index('--port') + 1] != str(port):
                continue
            stat = (path / 'stat').read_text()
            env = dict(x.decode(errors='replace').split('=', 1) for x in
                       (path / 'environ').read_bytes().split(b'\0') if b'=' in x)
            matches.append({'pid': int(entry.name),
                            'start_ticks': int(stat[stat.rfind(')') + 2:].split()[19]),
                            'argv': argv, 'env': {k: env.get(k) for k in ENV_KEYS + ('PYTHONPATH', 'FLAGGEMS_DB_URL')}})
        except (FileNotFoundError, PermissionError, ProcessLookupError):
            continue
    if len(matches) > 1:
        raise RuntimeError(f'multiple service roots on {port}')
    return matches[0] if matches else None


def healthy(port):
    try:
        with urllib.request.urlopen(f'http://127.0.0.1:{port}/v1/models', timeout=5) as resp:
            body = json.load(resp)
        return any(x.get('id') == 'Qwen3.8-Flash-Next' for x in body.get('data', []))
    except (OSError, ValueError):
        return False


def assert_idle(port):
    with urllib.request.urlopen(f'http://127.0.0.1:{port}/metrics', timeout=5) as resp:
        lines = resp.read().decode().splitlines()
    for key in ('vllm:num_requests_running', 'vllm:num_requests_waiting'):
        values = [float(line.rsplit(' ', 1)[1]) for line in lines if line.startswith(key + '{')]
        if not values or any(value != 0 for value in values):
            raise RuntimeError(f'{port} not idle: {key}={values}')


def assert_evaluator_idle():
    top = run(['docker', 'top', EVAL_CONTAINER]).stdout
    if any(name in top for name in ('formal_accuracy.py', 'llmrun.py', 'lm_eval')):
        raise RuntimeError('formal evaluator still active')
    for item in os.scandir('/proc'):
        if not item.name.isdigit():
            continue
        try:
            argv = [x.decode(errors='replace') for x in
                    (Path(item.path) / 'cmdline').read_bytes().split(b'\0') if x]
        except (FileNotFoundError, PermissionError, ProcessLookupError):
            continue
        if any(x.endswith('/dual-service-proxy.py') for x in argv):
            raise RuntimeError('dual-service proxy is active')


def validate_launch_reference(ref):
    if ref is None or not healthy(8010):
        raise RuntimeError('8010 reference absent or unhealthy')
    assert_idle(8010)
    argv = ref['argv']
    def arg(key):
        return argv[argv.index(key) + 1]
    if (arg('--tensor-parallel-size'), arg('--max-model-len'),
        arg('--max-num-seqs'), arg('--max-num-batched-tokens')) != ('8', '80000', '32', '4096'):
        raise RuntimeError('8010 launch shape differs from acc-010')
    if ref['env']['CUDA_VISIBLE_DEVICES'] != '0,1,2,3,4,5,6,7':
        raise RuntimeError('8010 card assignment changed')
    if ref['env']['PYTHONPATH'] or ref['env']['FLAGGEMS_DB_URL']:
        raise RuntimeError('8010 is no longer original source/cache')
    if not ref['env']['LD_LIBRARY_PATH']:
        raise RuntimeError('8010 LD_LIBRARY_PATH missing')


def candidate_env(ref, port):
    env = {k: v for k, v in ref['env'].items() if k in ENV_KEYS and v is not None}
    env['CUDA_VISIBLE_DEVICES'] = ('8,9,10,11,12,13,14,15' if port == 8000
                                   else '0,1,2,3,4,5,6,7')
    env['PYTHONPATH'] = str(PRIVATE / 'FlagGems/src')
    env['FLAGGEMS_DB_URL'] = f'sqlite:///{PRIVATE}/caches/port{port}.db'
    env['PYTHONDONTWRITEBYTECODE'] = '1'
    return env


def launch(ref, port):
    env = candidate_env(ref, port)
    imported = run(['docker', 'exec', *[part for k, v in env.items() for part in ('--env', f'{k}={v}')],
                    CONTAINER, 'python3', '-c',
                    'import flag_gems; import flag_gems.utils.models.sql as s; print(s.__file__)']).stdout.strip()
    expected = str(PRIVATE / 'FlagGems/src/flag_gems/utils/models/sql.py')
    if imported != expected:
        raise RuntimeError(f'private SQL import mismatch: {imported}')
    argv = list(ref['argv'])
    argv[argv.index('--port') + 1] = str(port)
    log = CASE / 'services' / f'port{port}-cachefix.log'
    if log.exists():
        raise RuntimeError(f'launch log already exists: {log}')
    command = 'exec ' + shlex.join(argv) + ' > ' + shlex.quote(str(log)) + ' 2>&1'
    launch_cmd = ['docker', 'exec', '-d']
    for key, value in sorted(env.items()):
        launch_cmd.extend(['--env', f'{key}={value}'])
    launch_cmd.extend([CONTAINER, 'bash', '-c', command])
    started = time.time()
    run(launch_cmd)
    print(f'port{port} launch dispatched', flush=True)
    while time.time() - started < 1200:
        current = process(port)
        if current and healthy(port):
            if current['argv'] != argv or current['env']['PYTHONPATH'] != env['PYTHONPATH'] or current['env']['FLAGGEMS_DB_URL'] != env['FLAGGEMS_DB_URL']:
                raise RuntimeError(f'port{port} runtime identity mismatch')
            return {'port': port, 'pid': current['pid'], 'start_ticks': current['start_ticks'],
                    'argv': argv, 'env': {k: (hashlib.sha256(v.encode()).hexdigest() if k == 'LD_LIBRARY_PATH' else v)
                                          for k, v in env.items()},
                    'import': imported, 'log': str(log), 'ready_epoch': time.time()}
        time.sleep(5)
    raise TimeoutError(f'port{port} did not become ready within 1200s; inspect {log}')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--mode', choices=('launch8000', 'switch8010'), required=True)
    args = parser.parse_args()
    prepared = json.loads((CASE / 'evidence/cachefix-preparation.json').read_text())
    private_sql_sha = run(['docker', 'exec', CONTAINER, 'sha256sum',
                           str(PRIVATE / 'FlagGems/src/flag_gems/utils/models/sql.py')]).stdout.split()[0]
    if prepared['sql_private_sha256'] != private_sql_sha:
        raise RuntimeError('private SQL source drift')
    assert_evaluator_idle()
    if args.mode == 'launch8000':
        ref = process(8010)
        validate_launch_reference(ref)
        if process(8000) or healthy(8000):
            raise RuntimeError('8000 is no longer absent')
        write_new(CASE / 'services/launch8000-preflight.json',
                  {'port8000_absent': True, 'port8010_pid': ref['pid'],
                   'port8010_start_ticks': ref['start_ticks'], 'source_argv': ref['argv'],
                   'source_env': {k: (hashlib.sha256(v.encode()).hexdigest() if k == 'LD_LIBRARY_PATH' and v else v)
                                  for k, v in ref['env'].items()}})
        receipt = launch(ref, 8000)
        write_new(CASE / 'services/port8000-ready.json', receipt)
        if process(8010)['start_ticks'] != ref['start_ticks'] or not healthy(8010):
            raise RuntimeError('8010 changed during 8000 launch')
    else:
        old = process(8010)
        frozen = json.loads((CASE / 'services/launch8000-preflight.json').read_text())
        ready8000 = json.loads((CASE / 'services/port8000-ready.json').read_text())
        if old is None or old['start_ticks'] != frozen['port8010_start_ticks']:
            raise RuntimeError('8010 identity changed since 8000 preparation')
        new8000 = process(8000)
        if new8000 is None or new8000['start_ticks'] != ready8000['start_ticks'] or not healthy(8000):
            raise RuntimeError('candidate 8000 changed or unhealthy')
        assert_idle(8000)
        assert_idle(8010)
        write_new(CASE / 'services/switch8010-preflight.json',
                  {'old_pid': old['pid'], 'old_start_ticks': old['start_ticks'],
                   'new8000_start_ticks': new8000['start_ticks']})
        os.kill(old['pid'], signal.SIGTERM)
        for _ in range(60):
            if process(8010) is None and not healthy(8010):
                break
            time.sleep(3)
        else:
            raise RuntimeError('8010 did not stop; no duplicate launch')
        receipt = launch(old, 8010)
        write_new(CASE / 'services/port8010-ready.json', receipt)
        if process(8000)['start_ticks'] != ready8000['start_ticks'] or not healthy(8000):
            raise RuntimeError('8000 changed during 8010 switch')
    print(json.dumps(receipt, indent=2, sort_keys=True), flush=True)


if __name__ == '__main__':
    main()
