#!/usr/bin/env python3
"""Add an opt-in T-Head native sparse-MLA path for pure Decode."""

from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path


REPO = Path("/workspace/vllm-plugin-FL")
GENERIC = REPO / "vllm_fl/dispatch/backends/flaggems/impl/mla_sparse.py"
THEAD = REPO / "vllm_fl/dispatch/backends/vendor/thead/impl/mla_decode.py"
TEST = REPO / "tests/unit_tests/dispatch/test_flaggems_mla_sparse.py"
CASE = Path(
    "/mnt/nfs/users/jinghao/hy4-preview/optimize/"
    "20260914-hy4-preview-ppu-e2e"
)
PATCH = CASE / "commands/plugin-hy4-native-decode-sparse-mla-20260920.patch"
RECORD = CASE / "results/operator/plugin-native-decode-sparse-mla-apply-20260920-01.json"


def sha256(path: Path) -> str | None:
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() else None


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: expected one match, found {count}")
    return text.replace(old, new, 1)


THEAD_SOURCE = '''# Copyright (c) 2026 BAAI. All rights reserved.

"""T-Head-only native sparse MLA helper for pure Decode batches."""

from __future__ import annotations

from typing import Optional

import torch


def native_sparse_mla_decode(
    q: torch.Tensor,
    kv: torch.Tensor,
    indices: torch.Tensor,
    sm_scale: float,
    attn_sink: Optional[torch.Tensor],
    topk_length: Optional[torch.Tensor],
) -> torch.Tensor | None:
    """Run the PPU native kernel only for its validated HY4 Decode shape."""
    if not (
        q.device.type == "cuda"
        and q.dtype == torch.bfloat16
        and q.ndim == 3
        and q.shape[1:] == (4, 576)
        and kv.device == q.device
        and kv.dtype == torch.bfloat16
        and kv.ndim == 3
        and kv.shape[1:] == (1, 576)
        and indices.device == q.device
        and indices.dtype == torch.int32
        and indices.shape == (q.shape[0], 1, 2048)
        and topk_length is not None
        and topk_length.device == q.device
        and topk_length.dtype == torch.int32
        and topk_length.shape == (q.shape[0],)
        and attn_sink is not None
        and attn_sink.device == q.device
        and attn_sink.dtype == torch.float32
        and attn_sink.shape == (4,)
    ):
        return None

    from flash_mla import flash_mla_sparse_fwd

    output, _, _ = flash_mla_sparse_fwd(
        q=q,
        kv=kv,
        indices=indices,
        sm_scale=sm_scale,
        d_v=512,
        attn_sink=attn_sink,
        topk_length=topk_length,
    )
    return output


__all__ = ["native_sparse_mla_decode"]
'''


def main() -> int:
    if THEAD.exists():
        raise RuntimeError(f"candidate file already exists: {THEAD}")
    before = {"generic": sha256(GENERIC), "thead": None, "test": sha256(TEST)}

    generic = GENERIC.read_text()
    generic = replace_once(
        generic,
        "from typing import TYPE_CHECKING, ClassVar\n\nimport torch\n",
        "import os\nfrom typing import TYPE_CHECKING, ClassVar\n\nimport torch\n"
        "from vllm.platforms import current_platform\n",
        "imports",
    )
    generic = replace_once(
        generic,
        "logger = init_logger(__name__)\n\n\ndef _resolve_flash_mla_sparse_fwd():",
        '''logger = init_logger(__name__)


def _thead_native_decode_enabled() -> bool:
    if getattr(current_platform, "vendor_name", None) != "thead":
        return False
    return os.environ.get(
        "VLLM_FL_THEAD_NATIVE_SPARSE_MLA_DECODE", "0"
    ).lower() in ("1", "true", "yes")


def _resolve_flash_mla_sparse_fwd():''',
        "T-Head opt-in resolver",
    )
    generic = replace_once(
        generic,
        "        self._validate_sinks(sinks, num_heads)\n        self.sinks = sinks\n",
        "        self._validate_sinks(sinks, num_heads)\n"
        "        self.sinks = sinks\n"
        "        self._use_thead_native_decode = False\n",
        "instance decode flag",
    )
    generic = replace_once(
        generic,
        '''        return super().forward_mqa(q, kv_c_and_k_pe_cache, attn_metadata, layer)
''',
        '''        previous = self._use_thead_native_decode
        self._use_thead_native_decode = (
            _thead_native_decode_enabled() and attn_metadata.max_query_len == 1
        )
        try:
            return super().forward_mqa(
                q, kv_c_and_k_pe_cache, attn_metadata, layer
            )
        finally:
            self._use_thead_native_decode = previous
''',
        "Decode-only metadata guard",
    )
    generic = replace_once(
        generic,
        '''        topk_indices = topk_indices.view(num_tokens, 1, -1)
        output, _, _ = _resolve_flash_mla_sparse_fwd()(
''',
        '''        topk_indices = topk_indices.view(num_tokens, 1, -1)
        if self._use_thead_native_decode:
            from vllm_fl.dispatch.backends.vendor.thead.impl.mla_decode import (
                native_sparse_mla_decode,
            )

            output = native_sparse_mla_decode(
                q,
                kv_c_and_k_pe_cache,
                topk_indices,
                self.softmax_scale,
                attn_sink,
                topk_length,
            )
            if output is not None:
                return output

        output, _, _ = _resolve_flash_mla_sparse_fwd()(
''',
        "native Decode dispatch",
    )

    tests = TEST.read_text()
    tests += '''

def test_thead_native_decode_is_opt_in_and_platform_guarded(monkeypatch):
    monkeypatch.setattr(
        mla_sparse, "current_platform", ModuleType("fake_platform")
    )
    mla_sparse.current_platform.vendor_name = "thead"
    monkeypatch.delenv("VLLM_FL_THEAD_NATIVE_SPARSE_MLA_DECODE", raising=False)
    assert not mla_sparse._thead_native_decode_enabled()
    monkeypatch.setenv("VLLM_FL_THEAD_NATIVE_SPARSE_MLA_DECODE", "1")
    assert mla_sparse._thead_native_decode_enabled()
    mla_sparse.current_platform.vendor_name = "nvidia"
    assert not mla_sparse._thead_native_decode_enabled()
'''

    GENERIC.write_text(generic)
    THEAD.write_text(THEAD_SOURCE)
    TEST.write_text(tests)

    diff = subprocess.check_output(
        [
            "git",
            "-C",
            str(REPO),
            "diff",
            "--binary",
            "--",
            str(GENERIC.relative_to(REPO)),
            str(THEAD.relative_to(REPO)),
            str(TEST.relative_to(REPO)),
        ],
        text=True,
    )
    new_file_diff = subprocess.run(
        [
            "git",
            "diff",
            "--no-index",
            "--binary",
            "/dev/null",
            str(THEAD.relative_to(REPO)),
        ],
        cwd=REPO,
        text=True,
        stdout=subprocess.PIPE,
        check=False,
    )
    if new_file_diff.returncode not in (0, 1):
        raise RuntimeError("failed to generate new-file patch")
    PATCH.write_text(diff + new_file_diff.stdout)
    after = {
        "generic": sha256(GENERIC),
        "thead": sha256(THEAD),
        "test": sha256(TEST),
    }
    RECORD.parent.mkdir(parents=True, exist_ok=True)
    RECORD.write_text(
        json.dumps(
            {
                "status": "applied_pending_validation",
                "repository": str(REPO),
                "branch": subprocess.check_output(
                    ["git", "-C", str(REPO), "branch", "--show-current"],
                    text=True,
                ).strip(),
                "head": subprocess.check_output(
                    ["git", "-C", str(REPO), "rev-parse", "HEAD"], text=True
                ).strip(),
                "before_sha256": before,
                "after_sha256": after,
                "patch": str(PATCH),
                "activation_env": "VLLM_FL_THEAD_NATIVE_SPARSE_MLA_DECODE=1",
                "guard": "T-Head plus max_query_len=1 plus HY4 HQ4/DQK576/TOPK2048 BF16 shape",
            },
            indent=2,
            sort_keys=True,
        )
        + "\n"
    )
    print(RECORD.read_text(), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
