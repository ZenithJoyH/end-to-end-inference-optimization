#!/usr/bin/env python3
"""Compare only inference-relevant live service environment variables."""

import hashlib
import importlib.util
import json
from pathlib import Path

CASE = Path('/mnt/nfs/users/jinghao/qwen3.8-flash/20260919-qwen38-flash-next-ppu-e2e/accuracy/acc-010-full-gpqa-dual-user-services-20260923')
PREV = CASE / 'diagnostics/accdiag-003-cache-abi-graph-output-20260923'
ROOT = CASE / 'diagnostics/accdiag-004-first-divergent-token-20260923'
CONTROLLER = Path('/mnt/nfs/users/jinghao/qwen3.8-flash/20260919-qwen38-flash-next-ppu-e2e/commands/accdiag003-transition-8000.py')
spec = importlib.util.spec_from_file_location('controller', CONTROLLER)
controller = importlib.util.module_from_spec(spec)
spec.loader.exec_module(controller)

PREFIXES = ('VLLM_', 'TORCH_', 'PYTORCH_', 'TRITON_', 'CUDA_', 'NCCL_', 'FLAG', 'PPU_')
EXACT = {'PYTHONPATH', 'LD_PRELOAD', 'OMP_NUM_THREADS', 'GLOO_SOCKET_IFNAME', 'LD_LIBRARY_PATH'}
SENSITIVE = ('KEY', 'TOKEN', 'SECRET', 'PASSWORD', 'CREDENTIAL')


def environment(pid):
    values = {}
    for item in Path(f'/proc/{pid}/environ').read_bytes().split(b'\0'):
        if b'=' not in item:
            continue
        key, value = item.split(b'=', 1)
        name = key.decode(errors='replace')
        if name.startswith(PREFIXES) or name in EXACT:
            value = value.decode(errors='replace')
            values[name] = (hashlib.sha256(value.encode()).hexdigest()
                            if any(word in name for word in SENSITIVE) else value)
    return values


def main():
    preflight = json.loads((PREV / 'preflight.json').read_text())
    restored = json.loads((PREV / 'stage-restored-original.json').read_text())
    controller.check_8010(preflight)
    current = controller.process_facts(8000)
    if not current or current['start_ticks'] != restored['service']['start_ticks']:
        raise RuntimeError('8000 identity changed')
    ref = controller.process_facts(8010)
    a, b = environment(current['host_pid']), environment(ref['host_pid'])
    diff = {key: {'8000': a.get(key), '8010': b.get(key)}
            for key in sorted(a.keys() | b.keys()) if a.get(key) != b.get(key)}
    result = {'8000_start_ticks': current['start_ticks'], '8010_start_ticks': ref['start_ticks'],
              'filtered_diff': diff, 'filtered_variable_count': len(a.keys() | b.keys())}
    ROOT.mkdir(exist_ok=True)
    path = ROOT / 'environment-diff.json'
    if path.exists():
        raise RuntimeError('environment diff already exists')
    path.write_text(json.dumps(result, indent=2, sort_keys=True) + '\n')
    print(json.dumps(result, sort_keys=True))


if __name__ == '__main__':
    main()
