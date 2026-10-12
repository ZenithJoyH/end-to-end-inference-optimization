#!/usr/bin/env python3
"""Exact, reversible QSA/PLE custom-op cache ABI experiment on a private copy."""

import argparse
import difflib
import hashlib
import json
import os
import tempfile
from pathlib import Path

ROOT = Path('/mnt/nfs/users/jinghao/qwen3.8-flash/20260919-qwen38-flash-next-ppu-e2e/accuracy/acc-010-full-gpqa-dual-user-services-20260923/diagnostics/accdiag-003-cache-abi-graph-output-20260923')
TARGET = Path('/workspace/vllm-plugin-FL-qwen38-accdiag003/vllm_fl/models/qwen3_8_flash_next.py')
BACKUP = ROOT / 'model-before-cache-abi.py'
RECEIPT = ROOT / 'cache-abi-source-receipt.json'
DIFF = ROOT / 'cache-abi-generated.patch'


def sha(data):
    return hashlib.sha256(data).hexdigest()


def replace_once(text, old, new, count=1):
    actual = text.count(old)
    if actual != count:
        raise RuntimeError(f'expected {count} exact matches, found {actual}: {old[:80]!r}')
    return text.replace(old, new)


def build(text):
    text = replace_once(text,
        '                value,\n                attn_output,\n                encoded_layer_name,\n',
        '                value,\n                self.kv_cache,\n'
        '                self.indexer.raw_key_cache.kv_cache,\n'
        '                self.indexer.compressed_key_cache.kv_cache,\n'
        '                attn_output,\n                encoded_layer_name,\n', count=2)
    qsa_sig_old = (
        'def qwen3_8_flash_next_qsa_with_output(\n'
        '    hidden_states: torch.Tensor,\n    positions: torch.Tensor,\n'
        '    query: torch.Tensor,\n    key: torch.Tensor,\n    value: torch.Tensor,\n'
        '    output: torch.Tensor,\n'
    )
    qsa_sig_new = qsa_sig_old.replace(
        '    output: torch.Tensor,\n',
        '    main_kv_cache: torch.Tensor,\n    raw_state_cache: torch.Tensor,\n'
        '    compressed_key_cache: torch.Tensor,\n    output: torch.Tensor,\n',
    )
    text = replace_once(text, qsa_sig_old, qsa_sig_new)
    text = replace_once(text,
        '    if not isinstance(layer, Qwen3_8FlashNextQSAAttention):\n'
        '        raise TypeError(f"{layer_name} is not a Qwen3.8-Flash-Next QSA owner")\n'
        '    layer._run_qsa(\n',
        '    if not isinstance(layer, Qwen3_8FlashNextQSAAttention):\n'
        '        raise TypeError(f"{layer_name} is not a Qwen3.8-Flash-Next QSA owner")\n'
        '    # The declared cache arguments alias the existing bound cache storages.\n'
        '    del main_kv_cache, raw_state_cache, compressed_key_cache\n'
        '    layer._run_qsa(\n')
    qsa_fake_old = qsa_sig_old.replace('def qwen3_8_flash_next_qsa_with_output(',
                                       'def qwen3_8_flash_next_qsa_with_output_fake(')
    qsa_fake_new = qsa_sig_new.replace('def qwen3_8_flash_next_qsa_with_output(',
                                       'def qwen3_8_flash_next_qsa_with_output_fake(')
    text = replace_once(text, qsa_fake_old, qsa_fake_new)
    text = replace_once(text,
        '    del hidden_states, positions, query, key, value, output, layer_name\n',
        '    del hidden_states, positions, query, key, value\n'
        '    del main_kv_cache, raw_state_cache, compressed_key_cache\n'
        '    del output, layer_name\n')
    text = replace_once(text,
        '    op_name="qwen3_8_flash_next_qsa_with_output",\n'
        '    op_func=qwen3_8_flash_next_qsa_with_output,\n'
        '    mutates_args=["output"],\n',
        '    op_name="qwen3_8_flash_next_qsa_with_output",\n'
        '    op_func=qwen3_8_flash_next_qsa_with_output,\n'
        '    mutates_args=["main_kv_cache", "raw_state_cache", "compressed_key_cache", "output"],\n')
    text = replace_once(text,
        '        torch.ops.vllm.qwen3_8_flash_next_ple_short_conv(\n'
        '            normalized,\n            conv_output,\n',
        '        torch.ops.vllm.qwen3_8_flash_next_ple_short_conv(\n'
        '            normalized,\n            self.kv_cache[0],\n            conv_output,\n')
    ple_sig_old = (
        'def qwen3_8_flash_next_ple_short_conv(\n'
        '    inputs: torch.Tensor,\n    output: torch.Tensor,\n'
    )
    ple_sig_new = ple_sig_old.replace('    output: torch.Tensor,\n',
                                      '    conv_state_cache: torch.Tensor,\n    output: torch.Tensor,\n')
    text = replace_once(text, ple_sig_old, ple_sig_new)
    text = replace_once(text,
        '    layer = get_forward_context().no_compile_layers[layer_name]\n'
        '    result = layer._short_conv(inputs)\n',
        '    layer = get_forward_context().no_compile_layers[layer_name]\n'
        '    del conv_state_cache  # Declared alias of the existing bound state cache.\n'
        '    result = layer._short_conv(inputs)\n')
    ple_fake_old = ple_sig_old.replace('def qwen3_8_flash_next_ple_short_conv(',
                                       'def qwen3_8_flash_next_ple_short_conv_fake(')
    ple_fake_new = ple_sig_new.replace('def qwen3_8_flash_next_ple_short_conv(',
                                       'def qwen3_8_flash_next_ple_short_conv_fake(')
    text = replace_once(text, ple_fake_old, ple_fake_new)
    text = replace_once(text,
        '    op_name="qwen3_8_flash_next_ple_short_conv",\n'
        '    op_func=qwen3_8_flash_next_ple_short_conv,\n'
        '    mutates_args=["output"],\n',
        '    op_name="qwen3_8_flash_next_ple_short_conv",\n'
        '    op_func=qwen3_8_flash_next_ple_short_conv,\n'
        '    mutates_args=["conv_state_cache", "output"],\n')
    compile(text, str(TARGET), 'exec')
    return text


def atomic_write(path, data):
    mode = path.stat().st_mode
    fd, tmp = tempfile.mkstemp(prefix='.accdiag003-', dir=path.parent)
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as file:
            file.write(data)
        os.chmod(tmp, mode)
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--mode', choices=('check', 'apply', 'revert'), required=True)
    args = parser.parse_args()
    preflight = json.loads((ROOT / 'preflight.json').read_text())
    expected = preflight['source_file_sha256']['vllm_fl/models/qwen3_8_flash_next.py']
    before = TARGET.read_text(encoding='utf-8')
    if args.mode == 'revert':
        receipt = json.loads(RECEIPT.read_text())
        if sha(before.encode()) != receipt['modified_sha256']:
            raise RuntimeError('modified private source drifted; refusing revert')
        original = BACKUP.read_text(encoding='utf-8')
        if sha(original.encode()) != expected:
            raise RuntimeError('backup hash mismatch')
        atomic_write(TARGET, original)
        print(json.dumps({'mode': 'revert', 'restored_sha256': sha(original.encode())}))
        return
    if sha(before.encode()) != expected:
        raise RuntimeError('private source differs from frozen baseline')
    after = build(before)
    diff = ''.join(difflib.unified_diff(before.splitlines(keepends=True),
                                        after.splitlines(keepends=True),
                                        fromfile='a/vllm_fl/models/qwen3_8_flash_next.py',
                                        tofile='b/vllm_fl/models/qwen3_8_flash_next.py'))
    if args.mode == 'check':
        print(json.dumps({'mode': 'check', 'baseline_sha256': expected,
                          'modified_sha256': sha(after.encode()), 'diff_sha256': sha(diff.encode()),
                          'changed_lines': len(diff.splitlines())}))
        return
    if BACKUP.exists() or RECEIPT.exists() or DIFF.exists():
        raise RuntimeError('source patch evidence already exists')
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
