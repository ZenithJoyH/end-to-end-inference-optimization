#!/usr/bin/env python3
"""Bind acc-011 run-003 to exact host-visible model service instances."""

import hashlib
import importlib.util
import json
import subprocess
import time
from pathlib import Path

CASE = Path('/mnt/nfs/users/jinghao/qwen3.8-flash/20260919-qwen38-flash-next-ppu-e2e/accuracy/acc-011-full-gpqa-dual-cachefix-20260924')
SOURCE = CASE / 'commands/acc011-switch-services.py'
spec = importlib.util.spec_from_file_location('switch', SOURCE)
switch = importlib.util.module_from_spec(spec)
spec.loader.exec_module(switch)


def main():
    if (CASE / 'services/host-preflight-run003.json').exists():
        raise RuntimeError('run-003 preflight already exists')
    switch.assert_evaluator_idle()
    expected = json.loads((CASE / 'services/services-runtime.json').read_text())['replicas']
    findings = []
    for saved in expected:
        port = saved['port']
        actual = switch.process(port)
        if actual is None or not switch.healthy(port):
            raise RuntimeError(f'port{port} unavailable')
        switch.assert_idle(port)
        if (actual['pid'], actual['start_ticks'], actual['argv']) != (
            saved['pid'], saved['start_ticks'], saved['argv']
        ):
            raise RuntimeError(f'port{port} process identity changed')
        for key in ('CUDA_VISIBLE_DEVICES', 'PYTHONPATH', 'FLAGGEMS_DB_URL'):
            if actual['env'][key] != saved['selected_environment'][key]:
                raise RuntimeError(f'port{port} {key} changed')
        if hashlib.sha256(actual['env']['LD_LIBRARY_PATH'].encode()).hexdigest() != saved['selected_environment']['LD_LIBRARY_PATH']:
            raise RuntimeError(f'port{port} LD_LIBRARY_PATH changed')
        findings.append({'port': port, 'pid': actual['pid'],
                         'start_ticks': actual['start_ticks'],
                         'argv_sha256': hashlib.sha256(json.dumps(actual['argv']).encode()).hexdigest(),
                         'private_source': actual['env']['PYTHONPATH'],
                         'cache_url': actual['env']['FLAGGEMS_DB_URL']})
    private = json.loads((CASE / 'evidence/cachefix-preparation.json').read_text())
    current_sha = subprocess.check_output([
        'docker', 'exec', switch.CONTAINER, 'sha256sum',
        '/opt/qwen38-acc011-cachefix-20260924/FlagGems/src/flag_gems/utils/models/sql.py'],
        text=True).split()[0]
    if current_sha != private['sql_private_sha256']:
        raise RuntimeError('private source drift')
    receipt = {'checked_epoch': time.time(), 'replicas': findings,
               'private_sql_sha256': current_sha,
               'freshness_requirement_seconds': 300}
    path = CASE / 'services/host-preflight-run003.json'
    path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + '\n')
    print(json.dumps(receipt, indent=2, sort_keys=True))


if __name__ == '__main__':
    main()
