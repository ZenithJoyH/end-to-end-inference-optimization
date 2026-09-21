#!/usr/bin/env python3
"""Apply the P16K cached-prefill sparse-MLA hybrid across two repositories."""

from __future__ import annotations

import difflib
import hashlib
import json
import subprocess
from pathlib import Path


FGV = Path("/workspace/FlagGems-vllm")
PLUGIN = Path("/workspace/vllm-plugin-FL")
FGV_SOURCE = FGV / "src/flaggems_vllm/runtime/backend/_thead/fused/flashmla_sparse.py"
FGV_INIT = FGV / "src/flaggems_vllm/runtime/backend/_thead/fused/__init__.py"
FGV_TEST = FGV / "tests/test_thead_hy4_ops.py"
PLUGIN_SOURCE = PLUGIN / "vllm_fl/dispatch/backends/flaggems/impl/mla_sparse.py"
PLUGIN_TEST = PLUGIN / "tests/unit_tests/dispatch/test_flaggems_mla_sparse.py"
CASE = Path(
    "/mnt/nfs/users/jinghao/hy4-preview/optimize/"
    "20260914-hy4-preview-ppu-e2e"
)
FGV_PATCH = CASE / "commands/flaggems-vllm-hy4-p16k-cached-prefill-hybrid-20260921.patch"
PLUGIN_PATCH = CASE / "commands/plugin-hy4-p16k-cached-prefill-hybrid-20260921.patch"
RECORD = CASE / "results/operator/p16k-cached-prefill-hybrid-source-apply-20260921-01.json"

EXPECTED = {
    FGV_SOURCE: "b4c8104653acf593e9b6e3c35ca3376dba4f948b02e55c9493465892b933d73f",
    FGV_INIT: "0ebc5f6cc45fab4fb8c98daad771da2d5021e7ca8728e4ad2091fdaf88f5fb5e",
    FGV_TEST: "d3124477a608f55e49d206a41e52413dd5f3f7965d00a4d81e525a2d6ea40ece",
    PLUGIN_SOURCE: "617ae91a8ab88ec16be8d08e224a497944dea0faabb574659acb3aa6522da198",
    PLUGIN_TEST: "8f7611001d25248cb0f897532fe2ec0140326a968f8200e440e3c7f7c5375737",
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: expected one match, found {count}")
    return text.replace(old, new, 1)


def patch_text(path: Path, before: str, after: str, repo: Path) -> str:
    relative = str(path.relative_to(repo))
    return "".join(
        difflib.unified_diff(
            before.splitlines(keepends=True),
            after.splitlines(keepends=True),
            fromfile=f"a/{relative}",
            tofile=f"b/{relative}",
        )
    )


HYBRID_FUNCTION = r'''
def flash_mla_sparse_cached_prefill_fwd(
    q: torch.Tensor,
    kv: torch.Tensor,
    indices: torch.Tensor,
    sm_scale: float,
    d_v: int = 512,
    attn_sink: Optional[torch.Tensor] = None,
    topk_length: Optional[torch.Tensor] = None,
) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
    """Use native score-selected MLA plus grouped full-prefix overwrite.

    This entry point is selected by the Plugin only for cached-prefill or
    mixed batches. Initial full-prefix chunks and small-SQ Decode retain the
    regular T-Head implementation.
    """
    if not (
        _can_use_thead_hq4_prefill(
            q, kv, indices, d_v, attn_sink, topk_length
        )
        and q.shape[0] >= _FULL_PREFIX_MIN_SQ
    ):
        return flash_mla_sparse_fwd(
            q,
            kv,
            indices,
            sm_scale,
            d_v=d_v,
            attn_sink=attn_sink,
            topk_length=topk_length,
        )

    from flash_mla import flash_mla_sparse_fwd as native_sparse_mla

    assert attn_sink is not None
    assert topk_length is not None
    sq = q.shape[0]
    skv = kv.shape[0]
    num_groups = triton.cdiv(sq, _FULL_PREFIX_GROUP_SIZE)
    group_flags = torch.empty(
        (num_groups,), device=q.device, dtype=torch.int32
    )
    legacy_lengths = torch.empty_like(topk_length)
    _classify_full_prefix_groups[(num_groups,)](
        indices,
        topk_length,
        group_flags,
        legacy_lengths,
        indices.stride(0),
        sq,
        TOPK=_SPLITK_TOPK,
        GROUP_SIZE=_FULL_PREFIX_GROUP_SIZE,
        BLOCK=_FULL_PREFIX_CLASSIFY_BLOCK,
        num_warps=4,
        num_stages=1,
    )
    output, max_logits, lse = native_sparse_mla(
        q=q,
        kv=kv,
        indices=indices,
        sm_scale=sm_scale,
        d_v=d_v,
        attn_sink=attn_sink,
        topk_length=legacy_lengths,
    )
    _flash_mla_sparse_full_prefix_grouped[(num_groups,)](
        q,
        kv,
        indices,
        attn_sink,
        topk_length,
        group_flags,
        output,
        max_logits,
        lse,
        q.stride(0),
        q.stride(1),
        kv.stride(0),
        indices.stride(0),
        output.stride(0),
        output.stride(1),
        max_logits.stride(0),
        lse.stride(0),
        sq,
        skv,
        SM_SCALE=sm_scale,
        HQ=_SPLITK_HQ,
        DV=_SPLITK_DV,
        BDP=_SPLITK_BDP,
        BK=32,
        GROUP_SIZE=_FULL_PREFIX_GROUP_SIZE,
        BH=_FULL_PREFIX_GROUP_SIZE * _SPLITK_HQ,
        num_warps=4,
        num_stages=1,
    )
    return output, max_logits, lse


'''


FGV_TEST_APPEND = r'''

def test_hy4_cached_prefill_sparse_mla_hybrid_graph_replay():
    from flaggems_vllm.runtime.backend._thead.fused.flashmla_sparse import (
        flash_mla_sparse_cached_prefill_fwd,
    )

    sq = 512
    q, kv, _, lengths, sinks = _sparse_inputs(sq)
    rows = torch.arange(sq, device="cuda", dtype=torch.int64)[:, None]
    positions = torch.arange(2048, device="cuda", dtype=torch.int64)[None, :]
    indices = ((positions * 4051 + rows * 7919) % 2048).to(torch.int32)[:, None]
    lengths.fill_(2048)
    scale = 576**-0.5
    expected = flaggems_vllm.flash_mla_sparse_fwd(
        q, kv, indices, scale, attn_sink=sinks, topk_length=lengths
    )
    actual = flash_mla_sparse_cached_prefill_fwd(
        q, kv, indices, scale, attn_sink=sinks, topk_length=lengths
    )
    for actual_tensor, expected_tensor in zip(actual, expected):
        torch.testing.assert_close(
            actual_tensor, expected_tensor, atol=2e-2, rtol=2e-2
        )

    graph = torch.cuda.CUDAGraph()
    with torch.cuda.graph(graph):
        captured = flash_mla_sparse_cached_prefill_fwd(
            q, kv, indices, scale, attn_sink=sinks, topk_length=lengths
        )
    graph.replay()
    q.add_(0.01)
    graph.replay()
    torch.cuda.synchronize()
    expected = flaggems_vllm.flash_mla_sparse_fwd(
        q, kv, indices, scale, attn_sink=sinks, topk_length=lengths
    )
    for actual_tensor, expected_tensor in zip(captured, expected):
        torch.testing.assert_close(
            actual_tensor, expected_tensor, atol=2e-2, rtol=2e-2
        )
'''


PLUGIN_HELPERS = r'''

def _resolve_thead_cached_prefill_sparse_mla_fwd():
    try:
        from flaggems_vllm.runtime.backend._thead.fused import (
            flash_mla_sparse_cached_prefill_fwd,
        )
    except (ImportError, ModuleNotFoundError):
        return None
    return flash_mla_sparse_cached_prefill_fwd


def _should_use_thead_cached_prefill_hybrid(q, attn_metadata) -> bool:
    """Select only cached/mixed prefill; preserve initial prefix and Decode."""
    return (
        getattr(current_platform, "vendor_name", None) == "thead"
        and q.ndim == 3
        and q.shape[0] > 64
        and attn_metadata.max_query_len > 1
        and attn_metadata.max_seq_len > attn_metadata.max_query_len
    )
'''


PLUGIN_METHOD = r'''
    def _forward_bf16_kv(
        self,
        q: torch.Tensor,
        kv_c_and_k_pe_cache: torch.Tensor,
        topk_indices: torch.Tensor,
        attn_metadata: FlashMLASparseMetadata,
    ) -> torch.Tensor:
        hybrid = _resolve_thead_cached_prefill_sparse_mla_fwd()
        if hybrid is None or not _should_use_thead_cached_prefill_hybrid(
            q, attn_metadata
        ):
            return super()._forward_bf16_kv(
                q, kv_c_and_k_pe_cache, topk_indices, attn_metadata
            )

        topk_indices, topk_length = triton_convert_req_index_to_global_index(
            attn_metadata.req_id_per_token,
            attn_metadata.block_table,
            topk_indices,
            BLOCK_SIZE=attn_metadata.block_size,
            NUM_TOPK_TOKENS=topk_indices.shape[1],
            return_valid_counts=True,
        )
        num_tokens = q.shape[0]
        kv_c_and_k_pe_cache = kv_c_and_k_pe_cache.view(
            -1, 1, kv_c_and_k_pe_cache.shape[-1]
        )
        attn_sink = self._sinks_for_query(
            q, head_dim=1, kernel_heads=q.shape[1]
        )
        topk_indices = topk_indices.view(num_tokens, 1, -1)
        output, _, _ = hybrid(
            q=q,
            kv=kv_c_and_k_pe_cache,
            indices=topk_indices,
            sm_scale=self.softmax_scale,
            d_v=self.kv_lora_rank,
            attn_sink=attn_sink,
            topk_length=topk_length,
        )
        return output

'''


PLUGIN_TEST_APPEND = r'''

def test_thead_cached_prefill_hybrid_metadata_guard(monkeypatch):
    from types import SimpleNamespace

    monkeypatch.setattr(
        mla_sparse, "current_platform", SimpleNamespace(vendor_name="thead")
    )
    q = SimpleNamespace(ndim=3, shape=(2048, 4, 576))
    initial = SimpleNamespace(max_query_len=2048, max_seq_len=2048)
    cached = SimpleNamespace(max_query_len=2048, max_seq_len=16384)
    decode = SimpleNamespace(max_query_len=1, max_seq_len=16384)
    assert not mla_sparse._should_use_thead_cached_prefill_hybrid(q, initial)
    assert mla_sparse._should_use_thead_cached_prefill_hybrid(q, cached)
    assert not mla_sparse._should_use_thead_cached_prefill_hybrid(q, decode)
    mla_sparse.current_platform.vendor_name = "nvidia"
    assert not mla_sparse._should_use_thead_cached_prefill_hybrid(q, cached)
'''


def main() -> int:
    if RECORD.exists() or FGV_PATCH.exists() or PLUGIN_PATCH.exists():
        raise RuntimeError("output record or patch already exists")
    actual = {path: sha256(path) for path in EXPECTED}
    mismatches = {
        str(path): {"expected": EXPECTED[path], "actual": actual[path]}
        for path in EXPECTED
        if actual[path] != EXPECTED[path]
    }
    if mismatches:
        raise RuntimeError(f"source identity mismatch: {mismatches}")

    before = {path: path.read_text() for path in EXPECTED}
    after = dict(before)

    after[FGV_SOURCE] = replace_once(
        after[FGV_SOURCE],
        "\ndef flash_mla_sparse_fwd(\n",
        "\n" + HYBRID_FUNCTION + "def flash_mla_sparse_fwd(\n",
        "FlagGems-vllm hybrid function",
    )
    after[FGV_INIT] = replace_once(
        after[FGV_INIT],
        "    flash_mla_sparse_fwd,\n",
        "    flash_mla_sparse_cached_prefill_fwd,\n    flash_mla_sparse_fwd,\n",
        "FlagGems-vllm fused export import",
    )
    after[FGV_INIT] = replace_once(
        after[FGV_INIT],
        '    "flash_mla_sparse_fwd",\n',
        '    "flash_mla_sparse_cached_prefill_fwd",\n    "flash_mla_sparse_fwd",\n',
        "FlagGems-vllm fused __all__",
    )
    after[FGV_TEST] = after[FGV_TEST].rstrip() + "\n" + FGV_TEST_APPEND

    after[PLUGIN_SOURCE] = replace_once(
        after[PLUGIN_SOURCE],
        "import torch\nfrom vllm.logger import init_logger\n",
        "import torch\nfrom vllm.logger import init_logger\n"
        "from vllm.platforms import current_platform\n",
        "Plugin platform import",
    )
    after[PLUGIN_SOURCE] = replace_once(
        after[PLUGIN_SOURCE],
        "    FlashMLASparseMetadataBuilder,\n)",
        "    FlashMLASparseMetadataBuilder,\n"
        "    triton_convert_req_index_to_global_index,\n)",
        "Plugin conversion import",
    )
    after[PLUGIN_SOURCE] = replace_once(
        after[PLUGIN_SOURCE],
        "\n\nclass MLASparseFLMetadataBuilder",
        PLUGIN_HELPERS + "\n\nclass MLASparseFLMetadataBuilder",
        "Plugin hybrid helpers",
    )
    after[PLUGIN_SOURCE] = replace_once(
        after[PLUGIN_SOURCE],
        "    def _bf16_flash_mla_kernel(\n",
        PLUGIN_METHOD + "    def _bf16_flash_mla_kernel(\n",
        "Plugin BF16 cached-prefill dispatch",
    )
    after[PLUGIN_TEST] = after[PLUGIN_TEST].rstrip() + "\n" + PLUGIN_TEST_APPEND

    for path, content in after.items():
        path.write_text(content)

    FGV_PATCH.write_text(
        "".join(
            patch_text(path, before[path], after[path], FGV)
            for path in (FGV_SOURCE, FGV_INIT, FGV_TEST)
        )
    )
    PLUGIN_PATCH.write_text(
        "".join(
            patch_text(path, before[path], after[path], PLUGIN)
            for path in (PLUGIN_SOURCE, PLUGIN_TEST)
        )
    )
    subprocess.run(["git", "-C", str(FGV), "diff", "--check"], check=True)
    subprocess.run(["git", "-C", str(PLUGIN), "diff", "--check"], check=True)

    result = {
        "status": "applied_pending_validation",
        "repositories": {
            "FlagGems-vllm": {
                "branch": subprocess.check_output(
                    ["git", "-C", str(FGV), "branch", "--show-current"], text=True
                ).strip(),
                "head": subprocess.check_output(
                    ["git", "-C", str(FGV), "rev-parse", "HEAD"], text=True
                ).strip(),
                "patch": str(FGV_PATCH),
            },
            "vllm-plugin-FL": {
                "branch": subprocess.check_output(
                    ["git", "-C", str(PLUGIN), "branch", "--show-current"], text=True
                ).strip(),
                "head": subprocess.check_output(
                    ["git", "-C", str(PLUGIN), "rev-parse", "HEAD"], text=True
                ).strip(),
                "patch": str(PLUGIN_PATCH),
            },
        },
        "before_sha256": {str(path): actual[path] for path in EXPECTED},
        "after_sha256": {str(path): sha256(path) for path in EXPECTED},
        "guard": (
            "thead and q rows >64 and max_query_len>1 and "
            "max_seq_len>max_query_len; exact operator shape guard in FlagGems-vllm"
        ),
        "fallback": "existing FlagGems-vllm T-Head sparse MLA",
    }
    RECORD.parent.mkdir(parents=True, exist_ok=True)
    RECORD.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(RECORD.read_text(), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
