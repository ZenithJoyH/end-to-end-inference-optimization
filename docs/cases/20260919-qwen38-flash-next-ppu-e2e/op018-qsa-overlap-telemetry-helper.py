"""One-shot eager-only telemetry for QSA selected-token set overlap."""

from __future__ import annotations

import json
import os
import time
from pathlib import Path

import torch


GROUP_ROWS = (2, 4, 8, 16)


def _rank() -> int:
    if torch.distributed.is_available() and torch.distributed.is_initialized():
        return int(torch.distributed.get_rank())
    return int(os.environ.get("RANK", os.environ.get("LOCAL_RANK", "0")))


def _capturing() -> bool:
    fn = getattr(torch.cuda, "is_current_stream_capturing", None)
    return bool(fn is not None and fn())


def _unique_count(values: torch.Tensor) -> torch.Tensor:
    ordered = torch.sort(values, dim=-1).values
    unique = ordered >= 0
    unique[..., 1:] &= ordered[..., 1:] != ordered[..., :-1]
    return unique.sum(dim=-1, dtype=torch.int64)


class QSAOverlapCollector:
    def __init__(self, *, rows, positions, requests, arm, claim, request_runs):
        self.rows = int(rows)
        self.positions = positions
        self.requests = requests
        self.arm = arm
        self.claim = claim
        self.request_runs = int(request_runs)
        self.started = time.monotonic()

    def finish(self, expanded_indices: torch.Tensor) -> Path:
        if expanded_indices.ndim != 2 or expanded_indices.shape[0] != self.rows:
            raise RuntimeError("op-018 expected expanded QSA indices [rows, width]")
        selected = expanded_indices.to(torch.int32)
        positions = self.positions.to(torch.int64)
        requests = self.requests.to(torch.int64)
        device = selected.device
        row_set_sizes = _unique_count(selected)
        base_row_eligible = (positions >= 0) & (requests >= 0)
        denominator = (row_set_sizes * base_row_eligible).sum(dtype=torch.int64)
        eligible_rows = base_row_eligible.sum(dtype=torch.int64)

        row_ids = torch.arange(self.rows, device=device, dtype=torch.int64)
        starts_request = torch.ones(self.rows, device=device, dtype=torch.bool)
        if self.rows > 1:
            starts_request[1:] = requests[1:] != requests[:-1]
        request_start = torch.cummax(
            torch.where(starts_request, row_ids, -1), dim=0
        ).values
        offset = row_ids - request_start

        packed = [denominator, eligible_rows]
        candidate_counts = {}
        width = selected.shape[1]
        for group_rows in GROUP_ROWS:
            starts = row_ids[(offset % group_rows) == 0]
            gather = starts[:, None] + torch.arange(
                group_rows, device=device, dtype=torch.int64
            )[None, :]
            in_bounds = gather[:, -1] < self.rows
            safe = gather.clamp_max(max(self.rows - 1, 0))
            group_req = requests[safe]
            group_pos = positions[safe]
            expected_pos = group_pos[:, :1] + torch.arange(
                group_rows, device=device, dtype=torch.int64
            )[None, :]
            eligible = (
                in_bounds
                & (group_req == group_req[:, :1]).all(dim=1)
                & (group_pos == expected_pos).all(dim=1)
                & (group_pos >= 0).all(dim=1)
                & (group_req >= 0).all(dim=1)
            )
            union_sizes = _unique_count(
                selected[safe].reshape(-1, group_rows * width)
            )
            a_sizes = row_set_sizes[safe].sum(dim=1, dtype=torch.int64)
            reusable = torch.clamp_min(a_sizes - union_sizes, 0)
            packed.extend(
                (
                    (reusable * eligible).sum(dtype=torch.int64),
                    (a_sizes * eligible).sum(dtype=torch.int64),
                    eligible.sum(dtype=torch.int64),
                    (~eligible).sum(dtype=torch.int64),
                )
            )
            candidate_counts[group_rows] = int(starts.numel())

        host = [int(value) for value in torch.stack(packed).cpu().tolist()]
        total = host[0]
        all_eligible_rows = host[1]
        cursor = 2
        groups = {}
        rhos = []
        for group_rows in GROUP_ROWS:
            numerator, covered, eligible_groups, rejected_groups = host[cursor : cursor + 4]
            cursor += 4
            rho = numerator / total if total else None
            coverage = covered / total if total else None
            union = covered - numerator
            dense_membership_cells = group_rows * union
            grouped_rho = numerator / covered if covered else None
            mask_density = (
                covered / dense_membership_cells if dense_membership_cells else None
            )
            if rho is not None:
                rhos.append(rho)
            groups[str(group_rows)] = {
                "candidate_segment_aligned_groups": candidate_counts[group_rows],
                "eligible_groups": eligible_groups,
                "rejected_or_tail_groups": rejected_groups,
                "full_group_count": eligible_groups,
                "ungrouped_eligible_rows": all_eligible_rows
                - eligible_groups * group_rows,
                "A_R_sum_row_cardinalities": covered,
                "U_R_sum_group_union_cardinalities": union,
                "reusable_token_occurrences": numerator,
                "covered_token_occurrences": covered,
                "all_eligible_row_token_occurrences": total,
                "rho": rho,
                "rho_grouped": grouped_rho,
                "coverage": coverage,
                "dense_membership_cells_R_times_U": dense_membership_cells,
                "false_or_masked_cells": dense_membership_cells - covered,
                "mask_density": mask_density,
                "tail_policy": "tail rows below R save zero and remain in denominator",
            }

        sample_id = str(self.arm["sample_id"])
        output_dir = Path(os.environ["VLLM_FL_QSA_OVERLAP_OUTPUT_DIR"])
        output_dir.mkdir(parents=True, exist_ok=True)
        result_path = output_dir / f"{sample_id}.rank{_rank()}.json"
        if result_path.exists():
            raise RuntimeError(f"refusing to overwrite result: {result_path}")
        result = {
            "schema_version": 2,
            "experiment_id": "op-018",
            "sample_id": sample_id,
            "expected_phase": self.arm["expected_phase"],
            "observed_phase": "mixed" if self.request_runs >= 2 else "prefill",
            "rank": _rank(),
            "pid": os.getpid(),
            "rows": self.rows,
            "expanded_width": width,
            "request_runs": self.request_runs,
            "group_rows": groups,
            "metric": "rho=sum_group(a-u)/sum_all_eligible_rows_cardinality(T_i)",
            "eligibility": (
                "request-segment/query_start_loc start; same token_to_req; "
                "consecutive nonnegative logical_positions"
            ),
            "raw_gate_fraction": 0.12,
            "raw_gate_any_r_passed": any(rho >= 0.12 for rho in rhos),
            "artifact_scope": "diagnostic_only_not_performance_timing",
            "large_host_tensor_copy": False,
            "host_counter_values": len(host),
            "elapsed_host_seconds_including_sync": time.monotonic() - self.started,
        }
        temporary = result_path.with_suffix(result_path.suffix + ".tmp")
        temporary.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
        temporary.replace(result_path)
        self.claim.unlink(missing_ok=True)
        return result_path


def qsa_overlap_telemetry_begin(rows, logical_positions, token_to_req):
    if os.environ.get("VLLM_FL_QSA_OVERLAP_TELEMETRY", "0") != "1":
        return None
    if _rank() != int(os.environ.get("VLLM_FL_QSA_OVERLAP_RANK", "0")):
        return None
    arm_path = Path(os.environ["VLLM_FL_QSA_OVERLAP_ARM_FILE"])
    if not arm_path.is_file() or rows < int(
        os.environ.get("VLLM_FL_QSA_OVERLAP_MIN_ROWS", "1024")
    ):
        return None
    if _capturing():
        raise RuntimeError("op-018 telemetry is eager-only; use --enforce-eager")
    arm = json.loads(arm_path.read_text())
    transitions = (token_to_req[1:] != token_to_req[:-1]).sum(dtype=torch.int64)
    request_runs = 1 + int(transitions.item()) if rows else 0
    if not int(arm["min_request_runs"]) <= request_runs <= int(
        arm["max_request_runs"]
    ):
        return None
    claim = arm_path.with_name(
        f"{arm_path.name}.claimed.rank{_rank()}.pid{os.getpid()}"
    )
    arm_path.replace(claim)
    return QSAOverlapCollector(
        rows=rows,
        positions=logical_positions,
        requests=token_to_req,
        arm=arm,
        claim=claim,
        request_runs=request_runs,
    )
