#!/usr/bin/env python3
"""Exact, reversible graph-output non-owning CUDA view experiment."""

import argparse
import difflib
import hashlib
import json
import os
import tempfile
from pathlib import Path

ROOT = Path('/mnt/nfs/users/jinghao/qwen3.8-flash/20260919-qwen38-flash-next-ppu-e2e/accuracy/acc-010-full-gpqa-dual-user-services-20260923/diagnostics/accdiag-003-cache-abi-graph-output-20260923')
TARGET = Path('/workspace/vllm-plugin-FL-qwen38-accdiag003/vllm_fl/compilation/graph.py')
BACKUP = ROOT / 'graph-before-view.py'
RECEIPT = ROOT / 'graph-view-source-receipt.json'
DIFF = ROOT / 'graph-view-generated.patch'

OLD = '''# FL-specific: platform-agnostic weak_ref_tensors
def weak_ref_tensors(tensor: Any) -> Any:
    try:
        from vllm.utils.torch_utils import weak_ref_tensors
        return weak_ref_tensors(tensor)
    except Exception:
        return tensor
'''

NEW = '''# FL-specific: PPU CUDA tensors need non-owning graph-output views. The
# installed vLLM weak_ref_tensors is an identity fallback on this runtime.
def _non_owning_tensor_view(tensor: torch.Tensor) -> torch.Tensor:
    if tensor.numel() == 0:
        return tensor
    storage = tensor.untyped_storage()
    metadata = {
        "nbytes": storage.nbytes(),
        "data_ptr": storage.data_ptr(),
        "size": tensor.shape,
        "stride": tensor.stride(),
        "dtype": tensor.dtype,
        "device": tensor.device,
        "storage_offset": tensor.storage_offset(),
    }
    non_owning_storage = torch._C._construct_storage_from_data_pointer(
        metadata["data_ptr"], metadata["device"], metadata["nbytes"]
    )
    return torch._C._construct_CUDA_Tensor_From_Storage_And_Metadata(
        metadata, non_owning_storage
    )


def weak_ref_tensors(tensor: Any) -> Any:
    if isinstance(tensor, torch.Tensor) and tensor.device.type == "cuda":
        return _non_owning_tensor_view(tensor)
    if isinstance(tensor, list):
        return [weak_ref_tensors(value) for value in tensor]
    if isinstance(tensor, tuple):
        return tuple(weak_ref_tensors(value) for value in tensor)
    try:
        from vllm.sequence import IntermediateTensors
        if isinstance(tensor, IntermediateTensors):
            return IntermediateTensors({
                key: weak_ref_tensors(value)
                for key, value in tensor.tensors.items()
            })
        from vllm.utils.torch_utils import weak_ref_tensors as upstream
        return upstream(tensor)
    except Exception:
        return tensor
'''


def sha(data):
    return hashlib.sha256(data).hexdigest()


def atomic_write(path, text):
    mode = path.stat().st_mode
    fd, tmp = tempfile.mkstemp(prefix='.accdiag003-', dir=path.parent)
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as file:
            file.write(text)
        os.chmod(tmp, mode)
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--mode', choices=('check', 'apply', 'revert'), required=True)
    args = parser.parse_args()
    expected = json.loads((ROOT / 'preflight.json').read_text())['source_file_sha256']['vllm_fl/compilation/graph.py']
    before = TARGET.read_text(encoding='utf-8')
    if args.mode == 'revert':
        receipt = json.loads(RECEIPT.read_text())
        if sha(before.encode()) != receipt['modified_sha256']:
            raise RuntimeError('modified graph source drifted; refusing revert')
        original = BACKUP.read_text(encoding='utf-8')
        if sha(original.encode()) != expected:
            raise RuntimeError('backup hash mismatch')
        atomic_write(TARGET, original)
        print(json.dumps({'mode': 'revert', 'restored_sha256': sha(original.encode())}))
        return
    if sha(before.encode()) != expected or before.count(OLD) != 1:
        raise RuntimeError('private graph source differs from frozen baseline')
    after = before.replace(OLD, NEW)
    compile(after, str(TARGET), 'exec')
    diff = ''.join(difflib.unified_diff(before.splitlines(keepends=True), after.splitlines(keepends=True),
                                        fromfile='a/vllm_fl/compilation/graph.py',
                                        tofile='b/vllm_fl/compilation/graph.py'))
    if args.mode == 'check':
        print(json.dumps({'mode': 'check', 'baseline_sha256': expected,
                          'modified_sha256': sha(after.encode()), 'diff_sha256': sha(diff.encode()),
                          'changed_lines': len(diff.splitlines())}))
        return
    if BACKUP.exists() or RECEIPT.exists() or DIFF.exists():
        raise RuntimeError('graph patch evidence already exists')
    BACKUP.write_text(before, encoding='utf-8')
    DIFF.write_text(diff, encoding='utf-8')
    atomic_write(TARGET, after)
    receipt = {'baseline_sha256': expected, 'modified_sha256': sha(after.encode()),
               'generated_diff_sha256': sha(diff.encode()), 'target': str(TARGET),
               'backup': str(BACKUP)}
    RECEIPT.write_text(json.dumps(receipt, indent=2, sort_keys=True) + '\n')
    print(json.dumps({'mode': 'apply', **receipt}, sort_keys=True))


if __name__ == '__main__':
    main()
