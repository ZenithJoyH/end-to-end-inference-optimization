#!/usr/bin/env python3
"""Rows64 falsification for an integrated QSA producer -> R4 transaction.

This experiment deliberately captures exactly one graph.  At the beginning of
the captured transaction a one-program device kernel copies ``phase`` to
``phase_used`` and flips ``phase``.  Staging reads only ``phase_used``.  The
target PPU capture records without executing the transaction (proven by the
first blocked smoke), so capture is seeded with A and leaves phase=A; three
consecutive replays with no external input writes naturally execute A/B/A.  The staged Q enters the real
``qsa_select_paged_tokens`` producer; its selected buffer is consumed by both
the current generic sparse attention and the op-019 R4 candidate.

The script is correctness-only.  It does not patch FlagGems or a service and
does not produce a performance claim.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import inspect
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from types import ModuleType

import numpy as np
import torch
import triton
import triton.language as tl

from flag_gems.fused.qsa import (
    qsa_select_paged_tokens,
    qsa_sparse_paged_attention,
)


EXPERIMENT_ID = "op-020-qsa-producer-integrated-r4-rows64"
ROWS = 64
INDEX_HEADS = 4
INDEX_HEAD_DIM = 128
QUERY_HEADS = 3
HEAD_DIM = 256
PAGE_SIZE = 16
TOKEN_TOPK = 2048
COMPRESS_RATIO = 4
TOPK = TOKEN_TOPK + COMPRESS_RATIO - 1
SEQUENCE_LENGTH = 4096
SCORE_COLUMNS = SEQUENCE_LENGTH // COMPRESS_RATIO
TOKEN_BUCKET = 8192
ATOL = 0.05
RTOL = 0.05


class ExperimentBlocker(RuntimeError):
    """A preflight incompatibility that makes this experiment invalid."""


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _tensor_sha(tensor: torch.Tensor) -> str:
    array = tensor.detach().to("cpu").contiguous().view(torch.uint8).numpy()
    return hashlib.sha256(memoryview(array).cast("B")).hexdigest()


def _load_op019(path: Path) -> ModuleType:
    path = path.resolve()
    if not path.is_file():
        raise ExperimentBlocker(f"op019 module is missing: {path}")
    spec = importlib.util.spec_from_file_location("op019_r4_impl", path)
    if spec is None or spec.loader is None:
        raise ExperimentBlocker(f"cannot load op019 module: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    expected = {
        "GROUP_ROWS": 4,
        "QUERY_HEADS": QUERY_HEADS,
        "HEAD_DIM": HEAD_DIM,
        "PAGE_SIZE": PAGE_SIZE,
        "TOPK": TOPK,
        "TOKEN_BUCKET": TOKEN_BUCKET,
    }
    mismatches = {
        name: (getattr(module, name, None), value)
        for name, value in expected.items()
        if getattr(module, name, None) != value
    }
    if mismatches:
        raise ExperimentBlocker(f"op019 constant/ABI mismatch: {mismatches}")
    if not hasattr(module, "qsa_sparse_paged_attention_group4_direct"):
        raise ExperimentBlocker("op019 R4 candidate callable is missing")
    return module


def _validate_producer_abi() -> dict[str, object]:
    signature = inspect.signature(qsa_select_paged_tokens)
    required = {
        "q",
        "k_cache",
        "page_table",
        "token_to_req",
        "query_positions",
        "sequence_lengths",
        "token_topk",
        "compress_ratio",
        "out",
        "static_score_columns",
    }
    missing = sorted(required - set(signature.parameters))
    if missing:
        raise ExperimentBlocker(
            "qsa_select_paged_tokens ABI lacks required parameters: "
            + ", ".join(missing)
        )
    source = inspect.getsourcefile(qsa_select_paged_tokens)
    source_path = Path(source).resolve() if source else None
    return {
        "signature": str(signature),
        "source_path": str(source_path) if source_path else None,
        "source_sha256": (
            _sha256(source_path) if source_path and source_path.is_file() else None
        ),
    }


@triton.jit
def _set_phase_kernel(phase_ptr, VALUE: tl.constexpr):
    tl.store(phase_ptr, VALUE)


@triton.jit
def _advance_phase_kernel(phase_ptr, phase_used_ptr):
    phase = tl.load(phase_ptr)
    tl.store(phase_used_ptr, phase)
    tl.store(phase_ptr, 1 - phase)


@triton.jit
def _stage_index_q_kernel(
    q_a_ptr,
    q_b_ptr,
    phase_ptr,
    staged_ptr,
    numel,
    BLOCK: tl.constexpr,
):
    offsets = tl.program_id(0) * BLOCK + tl.arange(0, BLOCK)
    mask = offsets < numel
    phase = tl.load(phase_ptr)
    a = tl.load(q_a_ptr + offsets, mask=mask, other=0.0)
    b = tl.load(q_b_ptr + offsets, mask=mask, other=0.0)
    tl.store(staged_ptr + offsets, tl.where(phase == 0, a, b), mask=mask)


def _set_phase(phase: torch.Tensor, value: int) -> None:
    if value not in (0, 1):
        raise ValueError("phase must be 0 (A) or 1 (B)")
    _set_phase_kernel[(1,)](phase, VALUE=value, num_warps=1)


def _advance_phase(phase: torch.Tensor, phase_used: torch.Tensor) -> None:
    _advance_phase_kernel[(1,)](phase, phase_used, num_warps=1)


def _stage_index_q(
    q_a: torch.Tensor,
    q_b: torch.Tensor,
    phase_used: torch.Tensor,
    staged: torch.Tensor,
) -> None:
    if q_a.shape != q_b.shape or staged.shape != q_a.shape:
        raise ValueError("Q staging tensors must have identical shapes")
    block = 256
    _stage_index_q_kernel[(triton.cdiv(q_a.numel(), block),)](
        q_a,
        q_b,
        phase_used,
        staged,
        q_a.numel(),
        BLOCK=block,
        num_warps=4,
    )


@dataclass
class Workload:
    index_q_a: torch.Tensor
    index_q_b: torch.Tensor
    staged_index_q: torch.Tensor
    phase: torch.Tensor
    phase_used: torch.Tensor
    compressed_k: torch.Tensor
    compressed_table: torch.Tensor
    token_to_req: torch.Tensor
    query_positions: torch.Tensor
    sequence_lengths: torch.Tensor
    sparse_q: torch.Tensor
    main_k: torch.Tensor
    main_v: torch.Tensor
    main_table: torch.Tensor
    query_start_loc: torch.Tensor
    selected: torch.Tensor
    generic_output: torch.Tensor
    candidate_output: torch.Tensor
    membership: torch.Tensor
    group_base: torch.Tensor
    overflow: torch.Tensor
    write_count: torch.Tensor


def _randn(
    shape: tuple[int, ...], seed: int, device: torch.device
) -> torch.Tensor:
    torch.manual_seed(seed)
    return torch.randn(shape, dtype=torch.bfloat16, device=device)


def _make_workload(device: torch.device) -> Workload:
    # One long request gives sixteen complete consecutive R4 groups.  Late
    # positions expose the whole 1024-column compressed domain, so independent
    # A/B queries can materially alter the real producer's TopK result.
    token_to_req = torch.zeros(ROWS, dtype=torch.int32, device=device)
    query_positions = torch.arange(
        SEQUENCE_LENGTH - ROWS,
        SEQUENCE_LENGTH,
        dtype=torch.int64,
        device=device,
    )
    sequence_lengths = torch.tensor(
        [SEQUENCE_LENGTH], dtype=torch.int32, device=device
    )
    query_start_loc = torch.tensor([0, ROWS], dtype=torch.int32, device=device)

    compressed_pages = SCORE_COLUMNS // PAGE_SIZE
    compressed_table = torch.arange(
        compressed_pages, dtype=torch.int32, device=device
    ).reshape(1, -1)
    compressed_k = _randn(
        (compressed_pages, PAGE_SIZE, 1, INDEX_HEAD_DIM), 20200901, device
    )
    index_q_a = _randn((ROWS, INDEX_HEADS, INDEX_HEAD_DIM), 20200902, device)
    index_q_b = _randn((ROWS, INDEX_HEADS, INDEX_HEAD_DIM), 20200903, device)

    main_pages = SEQUENCE_LENGTH // PAGE_SIZE
    main_table = torch.arange(
        main_pages, dtype=torch.int32, device=device
    ).reshape(1, -1)
    main_k = _randn((main_pages, PAGE_SIZE, 1, HEAD_DIM), 20200904, device)
    main_v = _randn((main_pages, PAGE_SIZE, 1, HEAD_DIM), 20200905, device)
    sparse_q = _randn((ROWS, QUERY_HEADS, HEAD_DIM), 20200906, device)

    group_slots = triton.cdiv(ROWS, 4) + 1
    return Workload(
        index_q_a=index_q_a,
        index_q_b=index_q_b,
        staged_index_q=torch.empty_like(index_q_a),
        phase=torch.zeros(1, dtype=torch.int32, device=device),
        phase_used=torch.empty(1, dtype=torch.int32, device=device),
        compressed_k=compressed_k,
        compressed_table=compressed_table.contiguous(),
        token_to_req=token_to_req,
        query_positions=query_positions,
        sequence_lengths=sequence_lengths,
        sparse_q=sparse_q,
        main_k=main_k,
        main_v=main_v,
        main_table=main_table.contiguous(),
        query_start_loc=query_start_loc,
        selected=torch.empty((ROWS, TOPK), dtype=torch.int32, device=device),
        generic_output=torch.empty_like(sparse_q),
        candidate_output=torch.empty_like(sparse_q),
        membership=torch.empty(
            (group_slots, TOKEN_BUCKET), dtype=torch.int32, device=device
        ),
        group_base=torch.empty(group_slots, dtype=torch.int32, device=device),
        overflow=torch.empty(group_slots, dtype=torch.int32, device=device),
        write_count=torch.empty(
            (ROWS, QUERY_HEADS), dtype=torch.int32, device=device
        ),
    )


def _select(workload: Workload, q: torch.Tensor) -> torch.Tensor:
    result = qsa_select_paged_tokens(
        q,
        workload.compressed_k,
        workload.compressed_table,
        workload.token_to_req,
        workload.query_positions,
        workload.sequence_lengths,
        TOKEN_TOPK,
        COMPRESS_RATIO,
        out=workload.selected,
        static_score_columns=SCORE_COLUMNS,
    )
    if result.data_ptr() != workload.selected.data_ptr():
        raise ExperimentBlocker("producer did not honor the supplied selected out buffer")
    return result


def _generic(workload: Workload) -> torch.Tensor:
    return qsa_sparse_paged_attention(
        workload.sparse_q,
        workload.main_k,
        workload.main_v,
        workload.selected,
        workload.main_table,
        workload.token_to_req,
        out=workload.generic_output,
    )


def _candidate(workload: Workload, op019: ModuleType) -> torch.Tensor:
    return op019.qsa_sparse_paged_attention_group4_direct(
        workload.sparse_q,
        workload.main_k,
        workload.main_v,
        workload.selected,
        workload.main_table,
        workload.token_to_req,
        workload.query_positions,
        workload.query_start_loc,
        workload.membership,
        workload.group_base,
        workload.overflow,
        workload.write_count,
        out=workload.candidate_output,
    )


def _transaction(workload: Workload, op019: ModuleType) -> None:
    _advance_phase(workload.phase, workload.phase_used)
    _stage_index_q(
        workload.index_q_a,
        workload.index_q_b,
        workload.phase_used,
        workload.staged_index_q,
    )
    _select(workload, workload.staged_index_q)
    _generic(workload)
    _candidate(workload, op019)


def _expected_structure(selected: torch.Tensor, group_slots: int) -> dict[str, np.ndarray]:
    selected_np = selected.to("cpu").numpy()
    membership = np.zeros((group_slots, TOKEN_BUCKET), dtype=np.int32)
    group_base = np.full(group_slots, -1, dtype=np.int32)
    overflow = np.zeros(group_slots, dtype=np.int32)
    for base in range(0, ROWS, 4):
        group_id = base // 4
        group_base[group_id] = base
        for row in range(base, min(base + 4, ROWS)):
            valid = selected_np[row][selected_np[row] >= 0]
            if np.unique(valid).size != valid.size:
                overflow[group_id] = 1
            for token in valid.tolist():
                if token >= TOKEN_BUCKET:
                    overflow[group_id] = 1
                else:
                    membership[group_id, token] |= 1 << (row - base)
    return {
        "membership": membership,
        "group_base": group_base,
        "overflow": overflow,
    }


def _snapshot(workload: Workload) -> dict[str, torch.Tensor]:
    return {
        "phase": workload.phase.detach().cpu().clone(),
        "phase_used": workload.phase_used.detach().cpu().clone(),
        "staged_index_q": workload.staged_index_q.detach().cpu().clone(),
        "selected": workload.selected.detach().cpu().clone(),
        "membership": workload.membership.detach().cpu().clone(),
        "group_base": workload.group_base.detach().cpu().clone(),
        "overflow": workload.overflow.detach().cpu().clone(),
        "write_count": workload.write_count.detach().cpu().clone(),
        "generic_output": workload.generic_output.detach().cpu().clone(),
        "candidate_output": workload.candidate_output.detach().cpu().clone(),
    }


def _assert_snapshot(
    snapshot: dict[str, torch.Tensor], expected_q: torch.Tensor, expected_phase: int
) -> dict[str, object]:
    if snapshot["phase_used"].tolist() != [expected_phase]:
        raise AssertionError(
            f"phase_used mismatch: {snapshot['phase_used'].tolist()} != "
            f"[{expected_phase}]"
        )
    if snapshot["phase"].tolist() != [1 - expected_phase]:
        raise AssertionError(
            f"advanced phase mismatch: {snapshot['phase'].tolist()} != "
            f"[{1 - expected_phase}]"
        )
    torch.testing.assert_close(snapshot["staged_index_q"], expected_q.cpu(), atol=0, rtol=0)
    selected = snapshot["selected"]
    if selected.shape != (ROWS, TOPK) or selected.dtype != torch.int32:
        raise AssertionError("producer selected shape/dtype mismatch")
    selected_np = selected.numpy()
    duplicate_rows = 0
    for row in selected_np:
        valid = row[row >= 0]
        duplicate_rows += int(np.unique(valid).size != valid.size)
    if duplicate_rows:
        raise AssertionError(f"producer emitted duplicates in {duplicate_rows} rows")
    valid = selected_np[selected_np >= 0]
    if valid.size == 0 or int(valid.max()) >= TOKEN_BUCKET:
        raise AssertionError("selected is empty or exceeds direct-address domain")

    expected = _expected_structure(selected, snapshot["membership"].shape[0])
    for name in ("membership", "group_base", "overflow"):
        actual = snapshot[name].numpy()
        if not np.array_equal(actual, expected[name]):
            mismatch = int(np.count_nonzero(actual != expected[name]))
            raise AssertionError(f"full {name} mismatch: {mismatch} cells")
    if not bool(torch.all(snapshot["write_count"] == 1)):
        raise AssertionError("candidate did not write every row/head exactly once")
    if not bool(torch.isfinite(snapshot["generic_output"]).all()):
        raise AssertionError("generic output has NaN/Inf")
    if not bool(torch.isfinite(snapshot["candidate_output"]).all()):
        raise AssertionError("candidate output has NaN/Inf")
    torch.testing.assert_close(
        snapshot["candidate_output"].float(),
        snapshot["generic_output"].float(),
        atol=ATOL,
        rtol=RTOL,
    )
    difference = (
        snapshot["candidate_output"].float() - snapshot["generic_output"].float()
    ).abs()
    return {
        "phase_used": expected_phase,
        "phase_after_transaction": 1 - expected_phase,
        "staged_index_q_sha256": _tensor_sha(snapshot["staged_index_q"]),
        "selected_sha256": _tensor_sha(selected),
        "membership_sha256": _tensor_sha(snapshot["membership"]),
        "group_base_sha256": _tensor_sha(snapshot["group_base"]),
        "overflow_sha256": _tensor_sha(snapshot["overflow"]),
        "write_count_sha256": _tensor_sha(snapshot["write_count"]),
        "generic_output_sha256": _tensor_sha(snapshot["generic_output"]),
        "candidate_output_sha256": _tensor_sha(snapshot["candidate_output"]),
        "max_abs_candidate_vs_generic": float(difference.max().item()),
        "mean_abs_candidate_vs_generic": float(difference.mean().item()),
        "full_membership_cells_checked": int(snapshot["membership"].numel()),
        "full_group_slots_checked": int(snapshot["group_base"].numel()),
        "duplicate_rows": duplicate_rows,
        "selected_max": int(valid.max()),
    }


def _run_eager(
    workload: Workload, op019: ModuleType, q: torch.Tensor
) -> tuple[dict[str, torch.Tensor], dict[str, object]]:
    if q.data_ptr() == workload.index_q_a.data_ptr():
        phase = 0
    elif q.data_ptr() == workload.index_q_b.data_ptr():
        phase = 1
    else:
        raise ValueError("eager Q must be the frozen A or B tensor")
    _set_phase(workload.phase, phase)
    _transaction(workload, op019)
    torch.cuda.synchronize()
    snapshot = _snapshot(workload)
    summary = _assert_snapshot(snapshot, q, phase)
    return snapshot, summary


def _changed_selected_rows(a: torch.Tensor, b: torch.Tensor) -> int:
    changed = 0
    for row in range(ROWS):
        a_valid = a[row][a[row] >= 0].sort().values
        b_valid = b[row][b[row] >= 0].sort().values
        changed += int(not torch.equal(a_valid, b_valid))
    return changed


def _assert_ab_precondition(
    eager_a: dict[str, torch.Tensor], eager_b: dict[str, torch.Tensor]
) -> dict[str, int | float]:
    changed_rows = _changed_selected_rows(eager_a["selected"], eager_b["selected"])
    if changed_rows < ROWS // 4:
        raise ExperimentBlocker(
            f"synthetic A/B producer changes only {changed_rows}/{ROWS} selected rows"
        )
    changed_groups = int(
        torch.any(eager_a["membership"] != eager_b["membership"], dim=1).sum().item()
    )
    if changed_groups < 8:
        raise ExperimentBlocker(
            f"synthetic A/B changes only {changed_groups} complete membership groups"
        )
    if torch.equal(eager_a["generic_output"], eager_b["generic_output"]):
        raise ExperimentBlocker("eager generic A/B outputs are bit-identical")
    changed_cells = int(
        torch.count_nonzero(eager_a["selected"] != eager_b["selected"]).item()
    )
    return {
        "changed_selected_rows": changed_rows,
        "changed_selected_row_fraction": changed_rows / ROWS,
        "changed_selected_cells": changed_cells,
        "changed_membership_groups": changed_groups,
    }


def _assert_graph_matches_eager(
    graph_snapshot: dict[str, torch.Tensor],
    eager_snapshot: dict[str, torch.Tensor],
) -> None:
    for name in (
        "phase",
        "phase_used",
        "staged_index_q",
        "selected",
        "membership",
        "group_base",
        "overflow",
        "write_count",
    ):
        torch.testing.assert_close(
            graph_snapshot[name], eager_snapshot[name], atol=0, rtol=0
        )
    for name in ("generic_output", "candidate_output"):
        torch.testing.assert_close(
            graph_snapshot[name].float(),
            eager_snapshot[name].float(),
            atol=ATOL,
            rtol=RTOL,
        )


def _assert_exact_same(a: dict[str, torch.Tensor], b: dict[str, torch.Tensor]) -> None:
    for name in a:
        torch.testing.assert_close(a[name], b[name], atol=0, rtol=0)


def _capture_one_graph(workload: Workload, op019: ModuleType) -> torch.cuda.CUDAGraph:
    # Compile both phase setter variants and all transaction kernels before
    # capture. This PPU records without executing the captured transaction, as
    # proven by the first blocked smoke. Seed A (0) and require capture to leave
    # it unchanged so the first three replays are A/B/A. Only the self-advancing
    # transaction is captured; there is exactly one graph.
    for phase in (0, 1, 0):
        _set_phase(workload.phase, phase)
        _transaction(workload, op019)
    torch.cuda.synchronize()
    _set_phase(workload.phase, 0)
    torch.cuda.synchronize()
    graph = torch.cuda.CUDAGraph()
    with torch.cuda.graph(graph, capture_error_mode="thread_local"):
        _transaction(workload, op019)
    torch.cuda.synchronize()
    capture_phase = workload.phase.detach().cpu().tolist()
    if capture_phase != [0]:
        raise ExperimentBlocker(
            "capture unexpectedly executed or mutated the seeded phase A: "
            f"phase={capture_phase}"
        )
    return graph


def _run_graph_aba(
    workload: Workload,
    op019: ModuleType,
    eager_a: dict[str, torch.Tensor],
    eager_b: dict[str, torch.Tensor],
) -> tuple[dict[str, dict[str, torch.Tensor]], dict[str, dict[str, object]]]:
    graph = _capture_one_graph(workload, op019)
    snapshots: dict[str, dict[str, torch.Tensor]] = {}
    summaries: dict[str, dict[str, object]] = {}
    for label, phase, expected_q, eager in (
        ("graph_a1", 0, workload.index_q_a, eager_a),
        ("graph_b", 1, workload.index_q_b, eager_b),
        ("graph_a2", 0, workload.index_q_a, eager_a),
    ):
        # No phase/input mutation is allowed between captured replays.  The
        # first captured kernel advances the device-resident phase itself.
        graph.replay()
        torch.cuda.synchronize()
        snapshots[label] = _snapshot(workload)
        summaries[label] = _assert_snapshot(
            snapshots[label], expected_q, phase
        )
        _assert_graph_matches_eager(snapshots[label], eager)
    _assert_exact_same(snapshots["graph_a1"], snapshots["graph_a2"])
    if torch.equal(snapshots["graph_a1"]["selected"], snapshots["graph_b"]["selected"]):
        raise AssertionError("single graph replay did not change producer selected A -> B")
    if torch.equal(
        snapshots["graph_a1"]["membership"], snapshots["graph_b"]["membership"]
    ):
        raise AssertionError("single graph replay did not rebuild membership A -> B")
    return snapshots, summaries


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


@torch.inference_mode()
def run(args: argparse.Namespace) -> dict[str, object]:
    if not torch.cuda.is_available():
        raise ExperimentBlocker("torch.cuda PPU-compatible accelerator API is unavailable")
    producer_abi = _validate_producer_abi()
    op019 = _load_op019(args.op019_module)
    device = torch.device("cuda:0")
    workload = _make_workload(device)

    eager_a, eager_a_summary = _run_eager(workload, op019, workload.index_q_a)
    eager_b, eager_b_summary = _run_eager(workload, op019, workload.index_q_b)
    ab_precondition = _assert_ab_precondition(eager_a, eager_b)
    graph_snapshots, graph_summaries = _run_graph_aba(
        workload, op019, eager_a, eager_b
    )

    snapshots = {
        "eager_a": eager_a,
        "eager_b": eager_b,
        **graph_snapshots,
    }
    args.snapshot_output.parent.mkdir(parents=True, exist_ok=True)
    if args.snapshot_output.exists():
        raise ExperimentBlocker(f"snapshot output already exists: {args.snapshot_output}")
    torch.save(snapshots, args.snapshot_output)

    return {
        "experiment_id": EXPERIMENT_ID,
        "status": "passed",
        "scope": "rows64_correctness_only",
        "script_sha256": _sha256(Path(__file__).resolve()),
        "op019_module_path": str(args.op019_module.resolve()),
        "op019_module_sha256": _sha256(args.op019_module.resolve()),
        "producer_abi": producer_abi,
        "shape": {
            "rows": ROWS,
            "index_q": list(workload.index_q_a.shape),
            "compressed_k": list(workload.compressed_k.shape),
            "selected": list(workload.selected.shape),
            "sparse_q": list(workload.sparse_q.shape),
            "main_kv": list(workload.main_k.shape),
            "membership": list(workload.membership.shape),
            "sequence_length": SEQUENCE_LENGTH,
            "query_position_range": [SEQUENCE_LENGTH - ROWS, SEQUENCE_LENGTH - 1],
            "static_score_columns": SCORE_COLUMNS,
        },
        "method": {
            "graph_capture_count": 1,
            "graph_replay_order": ["A", "B", "A"],
            "graph_replay_count": 3,
            "phase_update": "captured one-program phase_used copy and phase flip",
            "external_phase_updates_during_replay": False,
            "captured_transaction": [
                "internal_phase_advance",
                "phase_driven_index_q_stage",
                "real_qsa_select_paged_tokens",
                "current_generic_sparse_attention",
                "op019_workspace_clear_and_full_membership_build",
                "op019_r4_candidate_with_exact_fallback",
            ],
            "selected_is_written_inside_graph": True,
            "membership_is_rebuilt_inside_graph": True,
            "two_graph_fallback_used": False,
            "performance_measured": False,
            "service_or_source_modified": False,
        },
        "ab_precondition": ab_precondition,
        "eager": {"A": eager_a_summary, "B": eager_b_summary},
        "graph": graph_summaries,
        "snapshots_path": str(args.snapshot_output.resolve()),
        "snapshots_sha256": _sha256(args.snapshot_output.resolve()),
        "promotion_allowed": False,
        "next_gate": "rows4096 real producer fixture correctness before any timing",
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--op019-module", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--snapshot-output", type=Path, required=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.output.exists():
        raise SystemExit(f"output already exists: {args.output}")
    try:
        payload = run(args)
    except ExperimentBlocker as exc:
        payload = {
            "experiment_id": EXPERIMENT_ID,
            "status": "blocked",
            "scope": "rows64_correctness_only",
            "script_sha256": _sha256(Path(__file__).resolve()),
            "blockers": [str(exc)],
            "performance_measured": False,
            "service_or_source_modified": False,
        }
        _write_json(args.output, payload)
        print(json.dumps(payload, indent=2, sort_keys=True))
        raise SystemExit(3)
    _write_json(args.output, payload)
    print(json.dumps(payload, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
