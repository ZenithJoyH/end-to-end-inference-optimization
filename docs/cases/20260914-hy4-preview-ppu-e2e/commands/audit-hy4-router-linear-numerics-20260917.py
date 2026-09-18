#!/usr/bin/env python3
"""Audit numerical differences between HY4 router GEMM implementations.

This is an operator-only diagnostic.  It separates Top-K ordering changes from
actual expert-set changes and tests whether changes are explained by floating
point reduction order around the Top-8 cutoff.
"""

from __future__ import annotations

import json
import statistics
import sys
import time
from typing import Callable

import torch
import triton

from flag_gems.ops.linear import linear as flaggems_linear
from flag_gems.ops.linear import linear_kernel
from flag_gems.runtime import torch_device_fn


K, N, TOP_K = 6144, 256, 8
SHAPES = (1, 16, 64, 128, 256, 512, 1024, 2048)


def sync() -> None:
    torch_device_fn.synchronize()


def timed(fn: Callable[[], torch.Tensor], warmup: int = 4, repeats: int = 20):
    out = fn()
    for _ in range(warmup):
        out = fn()
    sync()
    samples = []
    for _ in range(repeats):
        start = time.perf_counter()
        out = fn()
        sync()
        samples.append((time.perf_counter() - start) * 1_000_000)
    return {
        "median_us": statistics.median(samples),
        "mean_us": statistics.fmean(samples),
        "min_us": min(samples),
        "max_us": max(samples),
    }, out


def topk_set(indices: torch.Tensor) -> torch.Tensor:
    return indices.sort(dim=-1).values


def route_diff(reference: torch.Tensor, candidate: torch.Tensor) -> dict[str, object]:
    ref_top9 = reference.topk(TOP_K + 1, dim=-1)
    cand_top8 = candidate.topk(TOP_K, dim=-1)
    ref_idx = ref_top9.indices[:, :TOP_K]
    cand_idx = cand_top8.indices
    position_equal = (ref_idx == cand_idx).all(dim=-1)
    set_equal = (topk_set(ref_idx) == topk_set(cand_idx)).all(dim=-1)
    order_only = (~position_equal) & set_equal
    set_changed = ~set_equal
    delta = (reference - candidate).abs()
    row_max_error = delta.max(dim=-1).values
    cutoff_margin = ref_top9.values[:, TOP_K - 1] - ref_top9.values[:, TOP_K]
    ambiguous_by_error = cutoff_margin <= 2.0 * row_max_error
    changed_rows = set_changed.nonzero(as_tuple=False).flatten()
    position_rows = (~position_equal).nonzero(as_tuple=False).flatten()
    symdiff_sizes = []
    changed_details = []
    position_details = []
    for row in position_rows.tolist():
        ref_row_idx = ref_idx[row]
        cand_row_idx = cand_idx[row]
        mismatched_positions = (ref_row_idx != cand_row_idx).nonzero(
            as_tuple=False
        ).flatten()
        position_details.append(
            {
                "row": row,
                "mismatched_positions": mismatched_positions.tolist(),
                "reference_indices": ref_row_idx.tolist(),
                "candidate_indices": cand_row_idx.tolist(),
                "reference_values_in_rank_order": reference[row]
                .index_select(0, ref_row_idx)
                .tolist(),
                "candidate_values_in_rank_order": candidate[row]
                .index_select(0, cand_row_idx)
                .tolist(),
            }
        )
    for row in changed_rows.tolist():
        ref_set = set(ref_idx[row].tolist())
        cand_set = set(cand_idx[row].tolist())
        symdiff_sizes.append(len(ref_set.symmetric_difference(cand_set)))
        changed_details.append(
            {
                "row": row,
                "reference_only": sorted(ref_set - cand_set),
                "candidate_only": sorted(cand_set - ref_set),
                "cutoff_margin": float(cutoff_margin[row].item()),
                "row_max_abs_diff": float(row_max_error[row].item()),
                "margin_le_2x_error": bool(ambiguous_by_error[row].item()),
            }
        )
    return {
        "exact_tensor": bool(torch.equal(reference, candidate)),
        "max_abs_diff": float(delta.max().item()),
        "mean_abs_diff": float(delta.mean().item()),
        "position_equal_fraction": float(position_equal.float().mean().item()),
        "set_equal_fraction": float(set_equal.float().mean().item()),
        "position_changed_rows": int((~position_equal).sum().item()),
        "order_only_rows": int(order_only.sum().item()),
        "set_changed_rows": int(set_changed.sum().item()),
        "position_changed_row_ids": position_rows.tolist(),
        "position_changed_details": position_details,
        "set_changed_row_ids": changed_rows.tolist(),
        "symmetric_difference_sizes": symdiff_sizes,
        "changed_set_rows_explained_by_error_bound": int(
            (ambiguous_by_error & set_changed).sum().item()
        ),
        "changed_details": changed_details,
        "all_rows_cutoff_margin": {
            "min": float(cutoff_margin.min().item()),
            "median": float(cutoff_margin.median().item()),
            "max": float(cutoff_margin.max().item()),
        },
    }


def error_vs_fp64(output: torch.Tensor, reference64: torch.Tensor) -> dict[str, float]:
    delta = output.cpu().double() - reference64
    return {
        "max_abs_diff": float(delta.abs().max().item()),
        "mean_abs_diff": float(delta.abs().mean().item()),
        "rmse": float(delta.square().mean().sqrt().item()),
    }


def fp64_route_match(output: torch.Tensor, reference64: torch.Tensor) -> dict[str, object]:
    out_idx = output.cpu().topk(TOP_K, dim=-1).indices
    ref_idx = reference64.topk(TOP_K, dim=-1).indices
    position_equal = (out_idx == ref_idx).all(dim=-1)
    set_equal = (topk_set(out_idx) == topk_set(ref_idx)).all(dim=-1)
    return {
        "position_equal_rows": int(position_equal.sum().item()),
        "set_equal_rows": int(set_equal.sum().item()),
        "row_count": int(output.shape[0]),
        "position_equal_by_row": position_equal.tolist(),
        "set_equal_by_row": set_equal.tolist(),
    }


def run_fixed_kernel(
    x: torch.Tensor,
    w: torch.Tensor,
    block_k: int,
    block_m: int = 64,
    block_n: int = 32,
) -> torch.Tensor:
    out = torch.empty((x.shape[0], N), device=x.device, dtype=x.dtype)
    linear_kernel.jit_function[
        (triton.cdiv(x.shape[0], block_m), triton.cdiv(N, block_n))
    ](
        x,
        w,
        w,
        out,
        x.shape[0],
        N,
        K,
        x.stride(0),
        x.stride(1),
        w.stride(0),
        w.stride(1),
        out.stride(0),
        out.stride(1),
        0,
        BIAS=False,
        BLOCK_SIZE_M=block_m,
        BLOCK_SIZE_N=block_n,
        BLOCK_SIZE_K=block_k,
        num_warps=2,
        num_stages=5,
    )
    return out


def precision_state() -> dict[str, object]:
    state: dict[str, object] = {
        "float32_matmul_precision": torch.get_float32_matmul_precision(),
    }
    try:
        state["cuda_matmul_allow_tf32"] = bool(torch.backends.cuda.matmul.allow_tf32)
    except Exception as exc:  # platform compatibility probe
        state["cuda_matmul_allow_tf32_error"] = repr(exc)
    return state


def main() -> None:
    torch.manual_seed(20260916)
    device = torch.device("cuda")
    w = torch.randn((N, K), device=device, dtype=torch.float32)
    original_precision = torch.get_float32_matmul_precision()
    try:
        original_tf32 = bool(torch.backends.cuda.matmul.allow_tf32)
    except Exception:
        original_tf32 = None

    report: dict[str, object] = {
        "shape": {"K": K, "N": N, "top_k": TOP_K},
        "seed": 20260916,
        "initial_precision_state": precision_state(),
        "shapes": {},
    }
    saved_2048 = None
    for m in SHAPES:
        x = torch.randn((m, K), device=device, dtype=torch.float32)
        fg_timing, fg_out = timed(lambda: flaggems_linear(x, w))
        native_timing, native_out = timed(lambda: torch.mm(x, w.T))
        repeated = [torch.mm(x, w.T) for _ in range(3)]
        sync()
        native_repeatable = all(torch.equal(repeated[0], item) for item in repeated[1:])
        comparison = route_diff(fg_out, native_out)
        report["shapes"][str(m)] = {
            "flaggems_timing": fg_timing,
            "native_timing": native_timing,
            "native_speedup": fg_timing["median_us"] / native_timing["median_us"],
            "native_repeatable": native_repeatable,
            "flaggems_vs_native": comparison,
        }
        if m == 2048:
            saved_2048 = (x, fg_out, native_out, comparison)
        print(
            f"M={m}: set_changed={comparison['set_changed_rows']} "
            f"order_only={comparison['order_only_rows']}",
            file=sys.stderr,
            flush=True,
        )

    assert saved_2048 is not None
    x2048, fg2048, native2048, comparison2048 = saved_2048

    precision_results: dict[str, object] = {}
    for precision in ("highest", "high", "medium"):
        try:
            torch.set_float32_matmul_precision(precision)
            timing, output = timed(lambda: torch.mm(x2048, w.T), warmup=2, repeats=10)
            precision_results[precision] = {
                "timing": timing,
                "state": precision_state(),
                "vs_flaggems": route_diff(fg2048, output),
                "vs_original_native": route_diff(native2048, output),
            }
        except Exception as exc:
            precision_results[precision] = {"error": repr(exc)}
    torch.set_float32_matmul_precision(original_precision)

    tf32_results: dict[str, object] = {}
    if original_tf32 is not None:
        for allow in (False, True):
            try:
                torch.backends.cuda.matmul.allow_tf32 = allow
                timing, output = timed(lambda: torch.mm(x2048, w.T), warmup=2, repeats=10)
                tf32_results[str(allow).lower()] = {
                    "timing": timing,
                    "state": precision_state(),
                    "vs_flaggems": route_diff(fg2048, output),
                    "vs_original_native": route_diff(native2048, output),
                }
            except Exception as exc:
                tf32_results[str(allow).lower()] = {"error": repr(exc)}
        torch.backends.cuda.matmul.allow_tf32 = original_tf32

    report["native_precision_modes_m2048"] = precision_results
    report["native_allow_tf32_m2048"] = tf32_results
    report["restored_precision_state"] = precision_state()

    reduction_results: dict[str, object] = {}
    for block_k in (32, 64, 128):
        try:
            timing, output = timed(
                lambda bk=block_k: run_fixed_kernel(x2048, w, bk),
                warmup=2,
                repeats=10,
            )
            reduction_results[str(block_k)] = {
                "timing": timing,
                "vs_flaggems": route_diff(fg2048, output),
                "vs_native": route_diff(native2048, output),
            }
        except Exception as exc:
            reduction_results[str(block_k)] = {"error": repr(exc)}
    report["fixed_block_k_m2048"] = reduction_results

    changed_rows = comparison2048["set_changed_row_ids"]
    position_rows = comparison2048["position_changed_row_ids"]
    selected = list(dict.fromkeys(changed_rows + position_rows))
    if len(selected) < 16:
        selected_set = set(selected)
        selected.extend(row for row in range(2048) if row not in selected_set)
    selected = selected[:16]
    selected_tensor = torch.tensor(selected, device=device, dtype=torch.long)
    x_sample64 = x2048.index_select(0, selected_tensor).cpu().double()
    w64 = w.cpu().double()
    fp64 = torch.mm(x_sample64, w64.T)
    fg_sample = fg2048.index_select(0, selected_tensor)
    native_sample = native2048.index_select(0, selected_tensor)
    report["fp64_audit_m2048"] = {
        "selected_rows": selected,
        "selection_prioritizes_changed_rows": True,
        "flaggems_error": error_vs_fp64(fg_sample, fp64),
        "native_error": error_vs_fp64(native_sample, fp64),
        "flaggems_route_match": fp64_route_match(fg_sample, fp64),
        "native_route_match": fp64_route_match(native_sample, fp64),
    }

    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
