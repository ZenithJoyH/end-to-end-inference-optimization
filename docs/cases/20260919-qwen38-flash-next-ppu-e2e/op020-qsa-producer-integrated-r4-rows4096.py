#!/usr/bin/env python3
"""Correctness-only rows4096 real-producer -> op019 R4 consumer gate.

Each invocation consumes one immutable op021 Prefill or Mixed producer fixture.
It validates every raw file, replays the real producer, feeds its selected
indices to both the current generic sparse consumer and the op019 R4 candidate,
and captures exactly one internally self-advancing A/B/A graph.  No timing is
performed and no installed source or service is modified.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import inspect
import json
import math
import sys
from dataclasses import dataclass
from pathlib import Path
from types import ModuleType

import numpy as np
import torch
import triton
import triton.language as tl

from flag_gems.fused.qsa import qsa_select_paged_tokens, qsa_sparse_paged_attention


EXPERIMENT_ID = "op-020-qsa-producer-integrated-r4-rows4096"
ROWS = 4096
INDEX_HEADS = 4
INDEX_HEAD_DIM = 128
QUERY_HEADS = 3
HEAD_DIM = 256
PRODUCER_PAGE_SIZE = 1600
CONSUMER_PAGE_SIZE = 16
TOKEN_TOPK = 2048
COMPRESS_RATIO = 4
SELECTED_WIDTH = TOKEN_TOPK + COMPRESS_RATIO - 1
TOKEN_BUCKET = 8192
GROUP_ROWS = 4
ATOL = 0.05
RTOL = 0.05
MAX_FIXTURE_BYTES = 64 * 1024 * 1024

PHASE_CONTRACT = {
    "prefill": {
        "sample_id": "op021-p4k-prefill-producer-001",
        "manifest_sha256": "e9765fa23ae19d487c9c7773c3f0b5ea65e5870012eb6ab4cacf7be9efcaeabd",
        "static_score_columns": 1024,
        "request_runs": 1,
        "captured_cache_pages": 1,
        "shape_target": {
            "rho": 0.695122,
            "union_max": 3460,
            "union_p99": 3292,
            "union_p90": 3036,
            "union_p50": 2052,
        },
    },
    "mixed": {
        "sample_id": "op021-p4k-mixed-producer-001",
        "manifest_sha256": "4d066545ab78ea30d340ce9a76db0325dfd4acee15b14c46fd719790779a037e",
        "static_score_columns": 1056,
        "request_runs": 2,
        "captured_cache_pages": 2,
        "shape_target": {
            "rho": 0.694798,
            "union_max": 3400,
            "union_p99": 3292,
            "union_p90": 3056,
            "union_p50": 2048,
        },
    },
}

DTYPES = {
    "bfloat16-le": torch.bfloat16,
    "float16-le": torch.float16,
    "float32-le": torch.float32,
    "int32-le": torch.int32,
    "int64-le": torch.int64,
}
EXPECTED_FILE_KEYS = {
    "index_q",
    "compressed_k",
    "compressed_page_table",
    "compressed_source_page_ids",
    "token_to_req",
    "query_positions",
    "sequence_lengths",
    "selected",
}


class ExperimentBlocker(RuntimeError):
    """The fixture or live ABI cannot support a trustworthy experiment."""


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _tensor_sha(tensor: torch.Tensor) -> str:
    value = tensor.detach().to("cpu").contiguous().view(torch.uint8).numpy()
    return hashlib.sha256(memoryview(value).cast("B")).hexdigest()


def _load_raw(root: Path, entry: dict) -> torch.Tensor:
    relative = Path(str(entry["path"]))
    if relative.is_absolute() or relative.name != str(relative):
        raise ExperimentBlocker(f"unsafe raw fixture path: {relative}")
    path = root / relative
    if not path.is_file():
        raise ExperimentBlocker(f"raw fixture is missing: {path}")
    if path.stat().st_size != int(entry["nbytes"]):
        raise ExperimentBlocker(f"raw fixture size mismatch: {path}")
    if _sha256(path) != str(entry["sha256"]):
        raise ExperimentBlocker(f"raw fixture SHA mismatch: {path}")
    dtype_name = str(entry["dtype"])
    if dtype_name not in DTYPES:
        raise ExperimentBlocker(f"unsupported fixture dtype: {dtype_name}")
    payload = bytearray(path.read_bytes())
    value = torch.frombuffer(payload, dtype=DTYPES[dtype_name]).clone()
    shape = tuple(int(extent) for extent in entry["shape"])
    if value.numel() != math.prod(shape):
        raise ExperimentBlocker(f"raw fixture shape/byte mismatch: {path}")
    return value.reshape(shape)


@dataclass
class Fixture:
    phase: str
    root: Path
    manifest: dict
    manifest_sha256: str
    tensors: dict[str, torch.Tensor]
    run_ids: list[int]
    run_starts: list[int]
    remapped_requests: torch.Tensor


def _request_runs(requests: torch.Tensor) -> tuple[list[int], list[int], torch.Tensor]:
    req = requests.to(torch.int64).contiguous()
    if req.shape != (ROWS,) or bool((req < 0).any()):
        raise ExperimentBlocker("rows4096 fixture must have 4096 active request rows")
    boundary = torch.ones(ROWS, dtype=torch.bool)
    boundary[1:] = req[1:] != req[:-1]
    starts = torch.nonzero(boundary, as_tuple=False).flatten().tolist()
    run_ids = [int(req[index]) for index in starts]
    if len(set(run_ids)) != len(run_ids):
        raise ExperimentBlocker("one request id appears in multiple row runs")
    remapped = torch.empty(ROWS, dtype=torch.int32)
    full_starts = starts + [ROWS]
    for new_id, (begin, end) in enumerate(zip(full_starts[:-1], full_starts[1:])):
        remapped[begin:end] = new_id
    return run_ids, full_starts, remapped


def load_fixture(root: Path, phase: str) -> Fixture:
    contract = PHASE_CONTRACT[phase]
    root = root.resolve()
    manifest_path = root / "manifest.json"
    if not manifest_path.is_file():
        raise ExperimentBlocker(f"manifest is missing: {manifest_path}")
    manifest_sha = _sha256(manifest_path)
    if manifest_sha != contract["manifest_sha256"]:
        raise ExperimentBlocker(
            f"{phase} manifest SHA mismatch: {manifest_sha} != "
            f"{contract['manifest_sha256']}"
        )
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    exact_fields = {
        "schema_version": 1,
        "experiment_id": "op-021",
        "artifact_kind": "real-qsa-producer-input-fixture",
        "sample_id": contract["sample_id"],
        "rank": 0,
        "rows": ROWS,
        "actual_rows": ROWS,
        "request_runs": contract["request_runs"],
        "observed_phase": phase,
        "token_topk": TOKEN_TOPK,
        "compress_ratio": COMPRESS_RATIO,
        "expected_cache_page_size": PRODUCER_PAGE_SIZE,
        "page_size": PRODUCER_PAGE_SIZE,
        "static_score_columns": contract["static_score_columns"],
        "captured_cache_pages": contract["captured_cache_pages"],
        "compact_table_columns": math.ceil(
            contract["static_score_columns"] / PRODUCER_PAGE_SIZE
        ),
        "endianness": "little",
        "pickle_used": False,
        "contains_prompt_text": False,
        "contains_token_ids": False,
        "contains_model_weights": False,
        "contains_synthetic_request_activations": True,
        "timing_valid": False,
    }
    mismatches = {
        key: (manifest.get(key), expected)
        for key, expected in exact_fields.items()
        if manifest.get(key) != expected
    }
    if mismatches:
        raise ExperimentBlocker(f"{phase} manifest contract mismatch: {mismatches}")
    if set(manifest.get("files", {})) != EXPECTED_FILE_KEYS:
        raise ExperimentBlocker("fixture file-key set differs from schema")
    estimated_raw_bytes = int(manifest["estimated_raw_bytes"])
    if estimated_raw_bytes > MAX_FIXTURE_BYTES:
        raise ExperimentBlocker(
            f"fixture exceeds 64 MiB safety bound: {estimated_raw_bytes}"
        )
    if estimated_raw_bytes != sum(
        int(entry["nbytes"]) for entry in manifest["files"].values()
    ):
        raise ExperimentBlocker("manifest raw byte total mismatch")

    tensors = {
        name: _load_raw(root, entry) for name, entry in manifest["files"].items()
    }
    expected_shapes = {
        "index_q": (ROWS, INDEX_HEADS, INDEX_HEAD_DIM),
        "compressed_k": (
            contract["captured_cache_pages"],
            PRODUCER_PAGE_SIZE,
            1,
            INDEX_HEAD_DIM,
        ),
        "token_to_req": (ROWS,),
        "query_positions": (ROWS,),
        "selected": (ROWS, SELECTED_WIDTH),
        "compressed_source_page_ids": (contract["captured_cache_pages"],),
    }
    bad_shapes = {
        name: (tuple(tensors[name].shape), shape)
        for name, shape in expected_shapes.items()
        if tuple(tensors[name].shape) != shape
    }
    if bad_shapes:
        raise ExperimentBlocker(f"fixture tensor shape mismatch: {bad_shapes}")
    expected_dtypes = {
        "index_q": torch.bfloat16,
        "compressed_k": torch.bfloat16,
        "compressed_page_table": torch.int32,
        "compressed_source_page_ids": torch.int32,
        "token_to_req": torch.int32,
        "selected": torch.int32,
    }
    bad_dtypes = {
        name: (tensors[name].dtype, dtype)
        for name, dtype in expected_dtypes.items()
        if tensors[name].dtype != dtype
    }
    if bad_dtypes:
        raise ExperimentBlocker(f"fixture tensor dtype mismatch: {bad_dtypes}")
    if tensors["query_positions"].dtype not in (torch.int32, torch.int64):
        raise ExperimentBlocker("query_positions must be int32/int64")
    if tensors["sequence_lengths"].dtype not in (torch.int32, torch.int64):
        raise ExperimentBlocker("sequence_lengths must be int32/int64")

    page_ids = tensors["compressed_source_page_ids"]
    if bool((page_ids < 0).any()):
        raise ExperimentBlocker("source compressed page ids contain a negative value")
    if page_ids.numel() > 1 and not bool(torch.all(page_ids[1:] > page_ids[:-1])):
        raise ExperimentBlocker("source compressed page ids are not strictly increasing")
    table = tensors["compressed_page_table"]
    table_columns = math.ceil(contract["static_score_columns"] / PRODUCER_PAGE_SIZE)
    if table.ndim != 2 or table.shape[1] != table_columns:
        raise ExperimentBlocker("compact compressed table has the wrong width")
    if bool((table < -1).any()) or bool((table >= contract["captured_cache_pages"]).any()):
        raise ExperimentBlocker("compact table references outside compact K cache")
    run_ids, run_starts, remapped = _request_runs(tensors["token_to_req"])
    if len(run_ids) != contract["request_runs"]:
        raise ExperimentBlocker("request-run count differs from frozen manifest")
    if run_ids and max(run_ids) >= table.shape[0]:
        raise ExperimentBlocker("request id exceeds compact table")
    active = torch.zeros(table.shape[0], dtype=torch.bool)
    active[run_ids] = True
    if bool((table[~active] != -1).any()):
        raise ExperimentBlocker("inactive compressed-table rows are not masked")
    if tensors["sequence_lengths"].ndim != 1:
        raise ExperimentBlocker("sequence_lengths must be rank one")
    if run_ids and max(run_ids) >= tensors["sequence_lengths"].numel():
        raise ExperimentBlocker("request id exceeds sequence_lengths")

    expected_sums = {
        f"{entry['sha256']}  {entry['path']}" for entry in manifest["files"].values()
    }
    expected_sums.add(f"{manifest_sha}  manifest.json")
    sums_path = root / "SHA256SUMS"
    if not sums_path.is_file() or set(sums_path.read_text().splitlines()) != expected_sums:
        raise ExperimentBlocker("SHA256SUMS does not exactly cover fixture files")
    return Fixture(
        phase=phase,
        root=root,
        manifest=manifest,
        manifest_sha256=manifest_sha,
        tensors=tensors,
        run_ids=run_ids,
        run_starts=run_starts,
        remapped_requests=remapped,
    )


def _load_op019(path: Path) -> ModuleType:
    path = path.resolve()
    if not path.is_file():
        raise ExperimentBlocker(f"op019 module is missing: {path}")
    spec = importlib.util.spec_from_file_location("op019_r4_rows4096_impl", path)
    if spec is None or spec.loader is None:
        raise ExperimentBlocker(f"cannot load op019 module: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    expected = {
        "GROUP_ROWS": GROUP_ROWS,
        "QUERY_HEADS": QUERY_HEADS,
        "HEAD_DIM": HEAD_DIM,
        "PAGE_SIZE": CONSUMER_PAGE_SIZE,
        "TOPK": SELECTED_WIDTH,
        "TOKEN_BUCKET": TOKEN_BUCKET,
    }
    mismatches = {
        name: (getattr(module, name, None), value)
        for name, value in expected.items()
        if getattr(module, name, None) != value
    }
    if mismatches:
        raise ExperimentBlocker(f"op019 constant/ABI mismatch: {mismatches}")
    return module


def _validate_live_abi() -> dict[str, object]:
    producer = inspect.signature(qsa_select_paged_tokens)
    required = {
        "q", "k_cache", "page_table", "token_to_req", "query_positions",
        "sequence_lengths", "token_topk", "compress_ratio", "out",
        "static_score_columns",
    }
    missing = sorted(required - set(producer.parameters))
    if missing:
        raise ExperimentBlocker(f"producer ABI lacks required fields: {missing}")
    sparse = inspect.signature(qsa_sparse_paged_attention)
    return {"producer": str(producer), "generic_sparse": str(sparse)}


@triton.jit
def _set_phase_kernel(phase_ptr, VALUE: tl.constexpr):
    tl.store(phase_ptr, VALUE)


@triton.jit
def _advance_phase_kernel(phase_ptr, phase_used_ptr):
    phase = tl.load(phase_ptr)
    tl.store(phase_used_ptr, phase)
    tl.store(phase_ptr, 1 - phase)


@triton.jit
def _stage_q_kernel(a_ptr, b_ptr, phase_used_ptr, out_ptr, numel, BLOCK: tl.constexpr):
    offsets = tl.program_id(0) * BLOCK + tl.arange(0, BLOCK)
    mask = offsets < numel
    phase = tl.load(phase_used_ptr)
    a = tl.load(a_ptr + offsets, mask=mask, other=0.0)
    b = tl.load(b_ptr + offsets, mask=mask, other=0.0)
    tl.store(out_ptr + offsets, tl.where(phase == 0, a, b), mask=mask)


def _set_phase(phase: torch.Tensor, value: int) -> None:
    _set_phase_kernel[(1,)](phase, VALUE=value, num_warps=1)


def _advance_phase(phase: torch.Tensor, phase_used: torch.Tensor) -> None:
    _advance_phase_kernel[(1,)](phase, phase_used, num_warps=1)


def _stage_q(a: torch.Tensor, b: torch.Tensor, phase_used: torch.Tensor, out: torch.Tensor) -> None:
    block = 256
    _stage_q_kernel[(triton.cdiv(a.numel(), block),)](
        a, b, phase_used, out, a.numel(), BLOCK=block, num_warps=4
    )


@dataclass
class Workload:
    fixture: Fixture
    index_q_a: torch.Tensor
    index_q_b: torch.Tensor
    staged_index_q: torch.Tensor
    phase: torch.Tensor
    phase_used: torch.Tensor
    compressed_k: torch.Tensor
    compressed_table: torch.Tensor
    producer_requests: torch.Tensor
    query_positions: torch.Tensor
    sequence_lengths: torch.Tensor
    selected: torch.Tensor
    captured_selected_cpu: torch.Tensor
    sparse_q: torch.Tensor
    main_k: torch.Tensor
    main_v: torch.Tensor
    main_table: torch.Tensor
    consumer_requests: torch.Tensor
    query_start_loc: torch.Tensor
    generic_output: torch.Tensor
    candidate_output: torch.Tensor
    membership: torch.Tensor
    group_base: torch.Tensor
    overflow: torch.Tensor
    write_count: torch.Tensor


def _randn(shape: tuple[int, ...], seed: int, device: torch.device) -> torch.Tensor:
    torch.manual_seed(seed)
    return torch.randn(shape, dtype=torch.bfloat16, device=device)


def make_workload(fixture: Fixture, device: torch.device) -> Workload:
    tensors = fixture.tensors
    q_a = tensors["index_q"].to(device)
    # Sign inversion preserves the exact captured magnitude distribution while
    # forcing an independently ranked real-producer control input.
    q_b = -q_a
    phase_seed = 20202101 if fixture.phase == "prefill" else 20202111
    sparse_q = _randn((ROWS, QUERY_HEADS, HEAD_DIM), phase_seed, device)
    main_blocks = TOKEN_BUCKET // CONSUMER_PAGE_SIZE
    main_k = _randn(
        (main_blocks, CONSUMER_PAGE_SIZE, 1, HEAD_DIM), phase_seed + 1, device
    )
    main_v = _randn(
        (main_blocks, CONSUMER_PAGE_SIZE, 1, HEAD_DIM), phase_seed + 2, device
    )
    num_requests = len(fixture.run_ids)
    main_table = torch.arange(main_blocks, dtype=torch.int32, device=device).expand(
        num_requests, -1
    ).contiguous()
    starts = torch.tensor(fixture.run_starts, dtype=torch.int32, device=device)
    group_slots = triton.cdiv(ROWS, GROUP_ROWS) + num_requests
    return Workload(
        fixture=fixture,
        index_q_a=q_a,
        index_q_b=q_b,
        staged_index_q=torch.empty_like(q_a),
        phase=torch.zeros(1, dtype=torch.int32, device=device),
        phase_used=torch.empty(1, dtype=torch.int32, device=device),
        compressed_k=tensors["compressed_k"].to(device),
        compressed_table=tensors["compressed_page_table"].to(device),
        producer_requests=tensors["token_to_req"].to(device),
        query_positions=tensors["query_positions"].to(device),
        sequence_lengths=tensors["sequence_lengths"].to(device),
        selected=torch.empty((ROWS, SELECTED_WIDTH), dtype=torch.int32, device=device),
        captured_selected_cpu=tensors["selected"].clone(),
        sparse_q=sparse_q,
        main_k=main_k,
        main_v=main_v,
        main_table=main_table,
        consumer_requests=fixture.remapped_requests.to(device),
        query_start_loc=starts,
        generic_output=torch.empty_like(sparse_q),
        candidate_output=torch.empty_like(sparse_q),
        membership=torch.empty(
            (group_slots, TOKEN_BUCKET), dtype=torch.int32, device=device
        ),
        group_base=torch.empty(group_slots, dtype=torch.int32, device=device),
        overflow=torch.empty(group_slots, dtype=torch.int32, device=device),
        write_count=torch.empty((ROWS, QUERY_HEADS), dtype=torch.int32, device=device),
    )


def _producer(workload: Workload) -> torch.Tensor:
    result = qsa_select_paged_tokens(
        workload.staged_index_q,
        workload.compressed_k,
        workload.compressed_table,
        workload.producer_requests,
        workload.query_positions,
        workload.sequence_lengths,
        TOKEN_TOPK,
        COMPRESS_RATIO,
        out=workload.selected,
        static_score_columns=workload.fixture.manifest["static_score_columns"],
    )
    if result.data_ptr() != workload.selected.data_ptr():
        raise ExperimentBlocker("producer did not honor supplied selected out buffer")
    return result


def _generic(workload: Workload) -> torch.Tensor:
    return qsa_sparse_paged_attention(
        workload.sparse_q,
        workload.main_k,
        workload.main_v,
        workload.selected,
        workload.main_table,
        workload.consumer_requests,
        out=workload.generic_output,
    )


def _candidate(workload: Workload, op019: ModuleType) -> torch.Tensor:
    return op019.qsa_sparse_paged_attention_group4_direct(
        workload.sparse_q,
        workload.main_k,
        workload.main_v,
        workload.selected,
        workload.main_table,
        workload.consumer_requests,
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
    _stage_q(
        workload.index_q_a,
        workload.index_q_b,
        workload.phase_used,
        workload.staged_index_q,
    )
    _producer(workload)
    _generic(workload)
    _candidate(workload, op019)


def _expected_structure(workload: Workload, selected: torch.Tensor) -> dict[str, np.ndarray]:
    selected_np = selected.numpy()
    starts = workload.fixture.run_starts
    group_slots = workload.membership.shape[0]
    membership = np.zeros((group_slots, TOKEN_BUCKET), dtype=np.int32)
    group_base = np.full(group_slots, -1, dtype=np.int32)
    overflow = np.zeros(group_slots, dtype=np.int32)
    for request, (begin, end) in enumerate(zip(starts[:-1], starts[1:])):
        for base in range(begin, end, GROUP_ROWS):
            group_id = base // GROUP_ROWS + request
            group_base[group_id] = base
            for row in range(base, min(base + GROUP_ROWS, end)):
                valid = selected_np[row][selected_np[row] >= 0]
                if np.unique(valid).size != valid.size:
                    overflow[group_id] = 1
                in_bucket = valid[valid < TOKEN_BUCKET]
                membership[group_id, in_bucket] |= 1 << (row - base)
                if in_bucket.size != valid.size:
                    overflow[group_id] = 1
    return {"membership": membership, "group_base": group_base, "overflow": overflow}


def _shape_metrics(workload: Workload, selected: torch.Tensor) -> dict[str, object]:
    values = selected.numpy()
    positions = workload.fixture.tensors["query_positions"].numpy()
    requests = workload.fixture.remapped_requests.numpy()
    starts = workload.fixture.run_starts
    row_sizes = np.count_nonzero(values >= 0, axis=1).astype(np.int64)
    denominator = int(row_sizes.sum())
    covered = 0
    union_sizes: list[int] = []
    fallback_rows = 0
    for request, (begin, end) in enumerate(zip(starts[:-1], starts[1:])):
        for base in range(begin, end, GROUP_ROWS):
            count = min(GROUP_ROWS, end - base)
            ids = np.arange(base, base + count)
            eligible = (
                count == GROUP_ROWS
                and np.all(requests[ids] == request)
                and np.all(positions[ids] == positions[base] + np.arange(GROUP_ROWS))
                and np.all(positions[ids] >= 0)
            )
            if eligible:
                flattened = np.concatenate([values[row][values[row] >= 0] for row in ids])
                covered += int(row_sizes[ids].sum())
                union_sizes.append(int(np.unique(flattened).size))
            else:
                fallback_rows += count
    if not union_sizes or denominator == 0:
        raise ExperimentBlocker("fixture has no eligible R4 shape evidence")
    ordered = sorted(union_sizes)

    def nearest(q: float) -> int:
        return int(ordered[int(math.floor((len(ordered) - 1) * q + 0.5))])

    union_sum = int(sum(union_sizes))
    metrics = {
        "selected_nonnegative_occurrences": denominator,
        "covered_occurrences": covered,
        "union_sum": union_sum,
        "rho": (covered - union_sum) / denominator,
        "eligible_full_groups": len(union_sizes),
        "fallback_rows": fallback_rows,
        "union_max": max(union_sizes),
        "union_p99": nearest(0.99),
        "union_p90": nearest(0.90),
        "union_p50": nearest(0.50),
    }
    target = PHASE_CONTRACT[workload.fixture.phase]["shape_target"]
    checks = {
        "rho_within_3pp": abs(metrics["rho"] - target["rho"]) <= 0.03,
    }
    for name in ("union_max", "union_p99", "union_p90", "union_p50"):
        checks[f"{name}_within_5pct"] = abs(metrics[name] - target[name]) <= 0.05 * target[name]
    if not all(checks.values()):
        raise ExperimentBlocker(
            f"{workload.fixture.phase} shape-similarity window failed: "
            f"metrics={metrics}, target={target}, checks={checks}"
        )
    metrics["target"] = target
    metrics["checks"] = checks
    metrics["status"] = "passed"
    return metrics


def _sample_rows(workload: Workload) -> list[int]:
    rows: set[int] = {0, ROWS - 1}
    for begin, end in zip(workload.fixture.run_starts[:-1], workload.fixture.run_starts[1:]):
        rows.update((begin, (begin + end - 1) // 2, end - 1))
        rows.update(range(begin, min(begin + GROUP_ROWS + 1, end)))
        rows.update(range(max(begin, end - GROUP_ROWS - 1), end))
    return sorted(rows)[:32]


def _fp32_reference(
    workload: Workload, selected: torch.Tensor, row_ids: list[int]
) -> torch.Tensor:
    reference = torch.zeros(
        (len(row_ids), QUERY_HEADS, HEAD_DIM),
        dtype=torch.bfloat16,
        device=workload.sparse_q.device,
    )
    requests = workload.consumer_requests.cpu()
    selected_rows = selected[row_ids].long()
    table = workload.main_table.cpu()
    scale = HEAD_DIM**-0.5
    for output_row, source_row in enumerate(row_ids):
        request = int(requests[source_row])
        tokens = selected_rows[output_row]
        pages = torch.div(tokens.clamp_min(0), CONSUMER_PAGE_SIZE, rounding_mode="floor")
        offsets = tokens.clamp_min(0) % CONSUMER_PAGE_SIZE
        valid = (tokens >= 0) & (pages < table.shape[1])
        physical = table[request, pages.clamp(0, table.shape[1] - 1)]
        valid &= (physical >= 0) & (physical < workload.main_k.shape[0])
        if not bool(valid.any()):
            continue
        p = physical[valid].to(workload.sparse_q.device)
        o = offsets[valid].to(workload.sparse_q.device)
        keys = workload.main_k[p, o, 0].float()
        vals = workload.main_v[p, o, 0].float()
        for head in range(QUERY_HEADS):
            scores = torch.matmul(keys, workload.sparse_q[source_row, head].float()) * scale
            reference[output_row, head] = torch.matmul(
                torch.softmax(scores, dim=0), vals
            ).to(torch.bfloat16)
    return reference


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
    workload: Workload,
    snapshot: dict[str, torch.Tensor],
    expected_q: torch.Tensor,
    expected_phase: int,
    require_captured_selected: bool,
    check_fp32: bool,
) -> dict[str, object]:
    if snapshot["phase_used"].tolist() != [expected_phase]:
        raise AssertionError("phase_used is not the expected A/B state")
    if snapshot["phase"].tolist() != [1 - expected_phase]:
        raise AssertionError("internal phase did not advance")
    torch.testing.assert_close(snapshot["staged_index_q"], expected_q.cpu(), atol=0, rtol=0)
    selected = snapshot["selected"]
    if require_captured_selected and not torch.equal(selected, workload.captured_selected_cpu):
        mismatch = int(torch.count_nonzero(selected != workload.captured_selected_cpu))
        raise AssertionError(f"real producer A differs from captured selected: {mismatch} cells")
    selected_np = selected.numpy()
    duplicate_rows = sum(
        int(np.unique(row[row >= 0]).size != np.count_nonzero(row >= 0))
        for row in selected_np
    )
    valid = selected_np[selected_np >= 0]
    if duplicate_rows or valid.size == 0 or int(valid.max()) >= TOKEN_BUCKET:
        raise AssertionError(
            f"selected producer contract failed: duplicates={duplicate_rows}, "
            f"max={int(valid.max()) if valid.size else None}"
        )
    expected = _expected_structure(workload, selected)
    for name in ("membership", "group_base", "overflow"):
        actual = snapshot[name].numpy()
        if not np.array_equal(actual, expected[name]):
            mismatch = int(np.count_nonzero(actual != expected[name]))
            raise AssertionError(f"full {name} mismatch: {mismatch} cells")
    if not bool(torch.all(snapshot["write_count"] == 1)):
        raise AssertionError("not every row/head has exactly one candidate writer")
    torch.testing.assert_close(
        snapshot["candidate_output"].float(),
        snapshot["generic_output"].float(),
        atol=ATOL,
        rtol=RTOL,
    )
    fp32_rows: list[int] = []
    if check_fp32:
        fp32_rows = _sample_rows(workload)
        reference = _fp32_reference(workload, selected, fp32_rows).cpu()
        torch.testing.assert_close(
            snapshot["generic_output"][fp32_rows].float(),
            reference.float(), atol=ATOL, rtol=RTOL,
        )
        torch.testing.assert_close(
            snapshot["candidate_output"][fp32_rows].float(),
            reference.float(), atol=ATOL, rtol=RTOL,
        )
    delta = (snapshot["candidate_output"].float() - snapshot["generic_output"].float()).abs()
    return {
        "phase_used": expected_phase,
        "selected_sha256": _tensor_sha(selected),
        "membership_sha256": _tensor_sha(snapshot["membership"]),
        "group_base_sha256": _tensor_sha(snapshot["group_base"]),
        "overflow_sha256": _tensor_sha(snapshot["overflow"]),
        "generic_output_sha256": _tensor_sha(snapshot["generic_output"]),
        "candidate_output_sha256": _tensor_sha(snapshot["candidate_output"]),
        "full_membership_cells_checked": snapshot["membership"].numel(),
        "full_group_slots_checked": snapshot["group_base"].numel(),
        "sampled_fp32_rows": fp32_rows,
        "duplicate_rows": duplicate_rows,
        "selected_max": int(valid.max()),
        "max_abs_candidate_vs_generic": float(delta.max().item()),
        "mean_abs_candidate_vs_generic": float(delta.mean().item()),
    }


def _run_eager(
    workload: Workload, op019: ModuleType, phase: int
) -> tuple[dict[str, torch.Tensor], dict[str, object]]:
    _set_phase(workload.phase, phase)
    _transaction(workload, op019)
    torch.cuda.synchronize()
    snapshot = _snapshot(workload)
    expected_q = workload.index_q_a if phase == 0 else workload.index_q_b
    summary = _assert_snapshot(
        workload, snapshot, expected_q, phase,
        require_captured_selected=(phase == 0), check_fp32=True,
    )
    return snapshot, summary


def _ab_precondition(a: dict[str, torch.Tensor], b: dict[str, torch.Tensor]) -> dict[str, object]:
    changed_rows = 0
    for row in range(ROWS):
        av = a["selected"][row][a["selected"][row] >= 0].sort().values
        bv = b["selected"][row][b["selected"][row] >= 0].sort().values
        changed_rows += int(not torch.equal(av, bv))
    changed_groups = int(torch.any(a["membership"] != b["membership"], dim=1).sum())
    changed_cells = int(torch.count_nonzero(a["selected"] != b["selected"]))
    if changed_rows < ROWS // 4 or changed_groups < 8:
        raise ExperimentBlocker(
            f"A/B producer difference too small: rows={changed_rows}, groups={changed_groups}"
        )
    if torch.equal(a["generic_output"], b["generic_output"]):
        raise ExperimentBlocker("eager generic A/B outputs are bit-identical")
    return {
        "changed_selected_rows": changed_rows,
        "changed_selected_row_fraction": changed_rows / ROWS,
        "changed_selected_cells": changed_cells,
        "changed_membership_groups": changed_groups,
    }


def _assert_graph_matches_eager(
    actual: dict[str, torch.Tensor], eager: dict[str, torch.Tensor]
) -> None:
    for name in (
        "phase", "phase_used", "staged_index_q", "selected", "membership",
        "group_base", "overflow", "write_count",
    ):
        torch.testing.assert_close(actual[name], eager[name], atol=0, rtol=0)
    for name in ("generic_output", "candidate_output"):
        torch.testing.assert_close(actual[name].float(), eager[name].float(), atol=ATOL, rtol=RTOL)


def _assert_exact_same(a: dict[str, torch.Tensor], b: dict[str, torch.Tensor]) -> None:
    for name in a:
        if torch.equal(a[name], b[name]):
            continue
        left = a[name]
        right = b[name]
        mismatched = int(torch.count_nonzero(left != right))
        if left.is_floating_point():
            delta = (left.float() - right.float()).abs()
            detail = (
                f", max_abs={float(delta.max().item())}, "
                f"mean_abs={float(delta.mean().item())}"
            )
        else:
            detail = ""
        raise AssertionError(
            f"A1/A2 bit-exact mismatch in {name}: "
            f"{mismatched}/{left.numel()} elements{detail}"
        )


def _capture_one_graph(workload: Workload, op019: ModuleType) -> torch.cuda.CUDAGraph:
    for phase in (0, 1, 0):
        _set_phase(workload.phase, phase)
        _transaction(workload, op019)
    torch.cuda.synchronize()
    # Calibrated rows64 behavior: this PPU records capture without executing it.
    _set_phase(workload.phase, 0)
    torch.cuda.synchronize()
    graph = torch.cuda.CUDAGraph()
    with torch.cuda.graph(graph, capture_error_mode="thread_local"):
        _transaction(workload, op019)
    torch.cuda.synchronize()
    capture_phase = workload.phase.detach().cpu().tolist()
    if capture_phase != [0]:
        raise ExperimentBlocker(
            f"capture mutated seeded phase A; calibrated PPU semantics changed: {capture_phase}"
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
        # Intentionally no phase/input write between graph replays.
        graph.replay()
        torch.cuda.synchronize()
        snapshot = _snapshot(workload)
        summaries[label] = _assert_snapshot(
            workload, snapshot, expected_q, phase,
            require_captured_selected=(phase == 0), check_fp32=False,
        )
        _assert_graph_matches_eager(snapshot, eager)
        snapshots[label] = snapshot
    _assert_exact_same(snapshots["graph_a1"], snapshots["graph_a2"])
    if torch.equal(snapshots["graph_a1"]["selected"], snapshots["graph_b"]["selected"]):
        raise AssertionError("single graph did not change producer selected A -> B")
    if torch.equal(snapshots["graph_a1"]["membership"], snapshots["graph_b"]["membership"]):
        raise AssertionError("single graph did not rebuild membership A -> B")
    return snapshots, summaries


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


@torch.inference_mode()
def run(args: argparse.Namespace) -> dict[str, object]:
    if not torch.cuda.is_available():
        raise ExperimentBlocker("torch.cuda PPU-compatible API is unavailable")
    fixture = load_fixture(args.fixture, args.phase)
    abi = _validate_live_abi()
    op019 = _load_op019(args.op019_module)
    workload = make_workload(fixture, torch.device("cuda:0"))
    eager_a, eager_a_summary = _run_eager(workload, op019, 0)
    shape_similarity = _shape_metrics(workload, eager_a["selected"])
    eager_b, eager_b_summary = _run_eager(workload, op019, 1)
    ab = _ab_precondition(eager_a, eager_b)
    _graph_snapshots, graph_summaries = _run_graph_aba(
        workload, op019, eager_a, eager_b
    )
    return {
        "experiment_id": EXPERIMENT_ID,
        "status": "passed",
        "phase": args.phase,
        "scope": "rows4096_real_producer_consumer_correctness_only",
        "script_sha256": _sha256(Path(__file__).resolve()),
        "op019_module_path": str(args.op019_module.resolve()),
        "op019_module_sha256": _sha256(args.op019_module.resolve()),
        "fixture": {
            "root": str(fixture.root),
            "manifest_sha256": fixture.manifest_sha256,
            "raw_file_sha256": {
                name: entry["sha256"] for name, entry in fixture.manifest["files"].items()
            },
            "rows": fixture.manifest["rows"],
            "actual_rows": fixture.manifest["actual_rows"],
            "request_runs": fixture.manifest["request_runs"],
            "producer_page_size": fixture.manifest["page_size"],
            "static_score_columns": fixture.manifest["static_score_columns"],
            "captured_cache_pages": fixture.manifest["captured_cache_pages"],
            "captured_selected_sha256": _tensor_sha(workload.captured_selected_cpu),
            "producer_exact_replay_in_harness": True,
        },
        "abi": abi,
        "consumer_synthetic_main_kv": {
            "page_size": CONSUMER_PAGE_SIZE,
            "token_domain": TOKEN_BUCKET,
            "note": "op019 standalone consumer ABI; distinct from producer page_size=1600",
        },
        "shape_similarity": shape_similarity,
        "ab_precondition": ab,
        "eager": {"A": eager_a_summary, "B": eager_b_summary},
        "graph": graph_summaries,
        "method": {
            "graph_capture_count": 1,
            "graph_replay_order": ["A", "B", "A"],
            "graph_replay_count": 3,
            "internal_phase_advance": True,
            "external_input_writes_between_replays": False,
            "two_graph_fallback_used": False,
            "full_membership_reconstructed_each_snapshot": True,
            "performance_measured": False,
            "service_or_source_modified": False,
        },
        "promotion_allowed": False,
        "next_gate": "separate Prefill/Mixed rows4096 full-transaction timing only after both correctness runs pass",
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--phase", choices=tuple(PHASE_CONTRACT), required=True)
    parser.add_argument("--fixture", type=Path, required=True)
    parser.add_argument("--op019-module", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
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
            "phase": args.phase,
            "script_sha256": _sha256(Path(__file__).resolve()),
            "blockers": [str(exc)],
            "error_type": type(exc).__name__,
            "message": str(exc),
            "performance_measured": False,
            "service_or_source_modified": False,
        }
        _write_json(args.output, payload)
        print(json.dumps(payload, indent=2, sort_keys=True))
        raise SystemExit(3)
    except AssertionError as exc:
        payload = {
            "experiment_id": EXPERIMENT_ID,
            "status": "failed",
            "phase": args.phase,
            "script_sha256": _sha256(Path(__file__).resolve()),
            "error_type": type(exc).__name__,
            "message": str(exc),
            "performance_measured": False,
            "service_or_source_modified": False,
        }
        _write_json(args.output, payload)
        print(json.dumps(payload, indent=2, sort_keys=True))
        raise SystemExit(1)
    except Exception as exc:
        # KeyboardInterrupt and SystemExit inherit directly from BaseException
        # and intentionally bypass this structured ordinary-failure receipt.
        payload = {
            "experiment_id": EXPERIMENT_ID,
            "status": "failed",
            "phase": args.phase,
            "script_sha256": _sha256(Path(__file__).resolve()),
            "error_type": type(exc).__name__,
            "message": str(exc),
            "performance_measured": False,
            "service_or_source_modified": False,
        }
        _write_json(args.output, payload)
        print(json.dumps(payload, indent=2, sort_keys=True))
        raise SystemExit(1)
    _write_json(args.output, payload)
    print(json.dumps(payload, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
