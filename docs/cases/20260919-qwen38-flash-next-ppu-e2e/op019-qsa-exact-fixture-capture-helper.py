"""One-shot eager-only exact QSA selected-index fixture capture.

This module is copied next to ``flag_gems.fused.qsa`` by the guarded op-019
prepare script.  It intentionally performs a device synchronization and large
device-to-host copies.  Consequently every client timing from a capture run is
invalid and must never be used as performance evidence.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import sys
import time
from pathlib import Path

import torch


_SAMPLE_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,127}\Z")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _rank() -> int:
    if torch.distributed.is_available() and torch.distributed.is_initialized():
        return int(torch.distributed.get_rank())
    return int(os.environ.get("RANK", os.environ.get("LOCAL_RANK", "0")))


def _capturing() -> bool:
    fn = getattr(torch.cuda, "is_current_stream_capturing", None)
    return bool(fn is not None and fn())


def _write_raw(path: Path, tensor: torch.Tensor, dtype: torch.dtype) -> dict:
    """Write one contiguous CPU tensor as explicit little-endian raw bytes."""

    if sys.byteorder != "little":
        raise RuntimeError("op-019 raw fixture writer requires a little-endian host")
    value = tensor.detach().to(device="cpu", dtype=dtype).contiguous()
    array = value.numpy()
    if not array.dtype.isnative:
        raise RuntimeError("unexpected non-native tensor byte order")
    temporary = path.with_name(path.name + f".tmp.pid{os.getpid()}")
    with temporary.open("xb") as stream:
        stream.write(memoryview(array).cast("B"))
        stream.flush()
        os.fsync(stream.fileno())
    temporary.replace(path)
    dtype_name = "<i4" if dtype == torch.int32 else "<i8"
    return {
        "path": path.name,
        "dtype": dtype_name,
        "shape": list(value.shape),
        "nbytes": path.stat().st_size,
        "sha256": _sha256(path),
    }


def _request_metadata(requests: torch.Tensor, seq_lens: torch.Tensor) -> dict:
    """Reconstruct scheduler-equivalent run boundaries for this QSA call.

    qsa_select_paged_tokens does not receive the scheduler's query_start_loc.
    For its row-major input, consecutive nonnegative token_to_req runs are an
    equivalent boundary representation.  Negative graph padding is allowed
    only as a suffix and is excluded from query_start_loc.
    """

    req = requests.to(device="cpu", dtype=torch.int64).contiguous()
    if req.ndim != 1:
        raise RuntimeError("token_to_req must be rank one")
    valid = req >= 0
    if bool(valid.any()):
        invalid_ids = torch.nonzero(~valid, as_tuple=False).flatten()
        actual_rows = int(invalid_ids[0]) if invalid_ids.numel() else req.numel()
        if bool(valid[actual_rows:].any()):
            raise RuntimeError("negative token_to_req padding is not a suffix")
    else:
        actual_rows = 0
    active = req[:actual_rows]
    if actual_rows:
        starts_mask = torch.ones(actual_rows, dtype=torch.bool)
        starts_mask[1:] = active[1:] != active[:-1]
        starts = torch.nonzero(starts_mask, as_tuple=False).flatten().to(torch.int64)
        run_ids = active[starts]
        if bool((run_ids >= seq_lens.numel()).any()):
            raise RuntimeError("token_to_req run id exceeds sequence_lengths")
        if torch.unique(run_ids).numel() != run_ids.numel():
            raise RuntimeError("one request id appears in multiple disjoint row runs")
        boundaries = torch.cat(
            (starts, torch.tensor([actual_rows], dtype=torch.int64))
        )
    else:
        starts = torch.empty(0, dtype=torch.int64)
        run_ids = torch.empty(0, dtype=torch.int64)
        boundaries = torch.tensor([0], dtype=torch.int64)
    return {
        "actual_rows": actual_rows,
        "padding_rows": req.numel() - actual_rows,
        "request_runs": int(run_ids.numel()),
        "run_ids": run_ids,
        "query_start_loc": boundaries,
        "equivalence_conditions": {
            "row_major_contiguous_runs": True,
            "negative_padding_suffix_only": True,
            "request_id_has_one_run": True,
            "starts_at_row_zero": actual_rows == 0 or int(starts[0]) == 0,
        },
        "limitation": (
            "query_start_loc is reconstructed from same-call token_to_req run "
            "boundaries because qsa_select_paged_tokens does not receive the "
            "scheduler tensor; it is not the original scheduler object and "
            "must not be reused across calls or steps"
        ),
    }


class QSAExactFixtureCollector:
    def __init__(
        self,
        *,
        rows: int,
        positions: torch.Tensor,
        requests: torch.Tensor,
        sequence_lengths: torch.Tensor,
        arm: dict,
        claim: Path,
        request_runs: int,
    ) -> None:
        self.rows = int(rows)
        self.positions = positions
        self.requests = requests
        self.sequence_lengths = sequence_lengths
        self.arm = arm
        self.claim = claim
        self.request_runs = int(request_runs)
        self.started = time.monotonic()

    def finish(self, expanded_indices: torch.Tensor) -> Path:
        if _capturing():
            raise RuntimeError("op-019 exact capture is eager-only")
        if expanded_indices.ndim != 2 or expanded_indices.shape[0] != self.rows:
            raise RuntimeError("expected expanded selected indices [rows,width]")
        expected_width = int(self.arm.get("expected_width", 2051))
        if expanded_indices.shape[1] != expected_width:
            raise RuntimeError(
                f"expanded width mismatch: {expanded_indices.shape[1]} != {expected_width}"
            )

        # This synchronization and the following large D2H copies are expected.
        # They make the diagnostic client timing invalid by construction.
        torch.cuda.synchronize()
        selected = expanded_indices.detach().to("cpu", dtype=torch.int32).contiguous()
        requests = self.requests.detach().to("cpu", dtype=torch.int32).contiguous()
        positions = self.positions.detach().to("cpu", dtype=torch.int64).contiguous()
        seq_lens = self.sequence_lengths.detach().to(
            "cpu", dtype=torch.int32
        ).contiguous()
        if requests.shape != (self.rows,) or positions.shape != (self.rows,):
            raise RuntimeError("request/position metadata does not match rows")
        if seq_lens.ndim != 1:
            raise RuntimeError("sequence_lengths must be rank one")

        request_meta = _request_metadata(requests, seq_lens)
        if request_meta["request_runs"] != self.request_runs:
            raise RuntimeError("request-run count changed during QSA call")
        active = request_meta["actual_rows"]
        if active and bool((positions[:active] < 0).any()):
            raise RuntimeError("active request rows contain negative logical positions")

        sample_id = str(self.arm["sample_id"])
        if not _SAMPLE_RE.fullmatch(sample_id):
            raise RuntimeError("unsafe sample_id")
        output_root = Path(os.environ["VLLM_FL_QSA_FIXTURE_OUTPUT_DIR"]).resolve()
        result_dir = output_root / sample_id
        temporary = output_root / f".{sample_id}.tmp.pid{os.getpid()}"
        if result_dir.exists() or temporary.exists():
            raise RuntimeError("refusing to overwrite an existing fixture directory")
        temporary.mkdir(parents=False)

        files = {}
        files["selected"] = _write_raw(
            temporary / "selected.int32.bin", selected, torch.int32
        )
        files["token_to_req"] = _write_raw(
            temporary / "token_to_req.int32.bin", requests, torch.int32
        )
        files["logical_positions"] = _write_raw(
            temporary / "logical_positions.int64.bin", positions, torch.int64
        )
        files["query_start_loc"] = _write_raw(
            temporary / "query_start_loc.int32.bin",
            request_meta["query_start_loc"],
            torch.int32,
        )
        files["request_run_ids"] = _write_raw(
            temporary / "request_run_ids.int32.bin",
            request_meta["run_ids"],
            torch.int32,
        )
        files["seq_lens"] = _write_raw(
            temporary / "seq_lens.int32.bin", seq_lens, torch.int32
        )

        observed_phase = "mixed" if self.request_runs >= 2 else "prefill"
        expected_phase = str(self.arm["expected_phase"])
        if observed_phase != expected_phase:
            raise RuntimeError(
                f"phase mismatch: observed {observed_phase}, expected {expected_phase}"
            )
        qsa_path = Path(__file__).with_name("qsa.py")
        helper_path = Path(__file__)
        manifest = {
            "schema_version": 1,
            "experiment_id": "op-019",
            "artifact_kind": "exact-expanded-selected-fixture",
            "sample_id": sample_id,
            "expected_phase": expected_phase,
            "observed_phase": observed_phase,
            "rank": _rank(),
            "pid": os.getpid(),
            "rows": self.rows,
            "expanded_width": int(selected.shape[1]),
            "request_runs": self.request_runs,
            "actual_rows": request_meta["actual_rows"],
            "padding_rows": request_meta["padding_rows"],
            "query_start_loc_reconstruction": {
                "method": "boundaries of contiguous nonnegative token_to_req runs",
                "equivalence_conditions": request_meta["equivalence_conditions"],
                "limitation": request_meta["limitation"],
            },
            "files": files,
            "endianness": "little",
            "pickle_used": False,
            "contains_prompt_or_kv_data": False,
            "timing_valid": False,
            "timing_invalid_reason": (
                "capture synchronizes the device and copies expanded selected "
                "indices plus metadata to the host"
            ),
            "source": {
                "qsa_path": str(qsa_path),
                "qsa_sha256": _sha256(qsa_path),
                "helper_path": str(helper_path),
                "helper_sha256": _sha256(helper_path),
            },
            "arm_provenance": self.arm.get("provenance", {}),
            "elapsed_host_seconds_including_sync_and_write": (
                time.monotonic() - self.started
            ),
        }
        manifest_path = temporary / "manifest.json"
        manifest_path.write_text(
            json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        manifest_sha = _sha256(manifest_path)
        sums = [
            f"{entry['sha256']}  {entry['path']}" for entry in files.values()
        ]
        sums.append(f"{manifest_sha}  manifest.json")
        (temporary / "SHA256SUMS").write_text(
            "\n".join(sorted(sums)) + "\n", encoding="utf-8"
        )
        temporary.replace(result_dir)
        self.claim.unlink(missing_ok=True)
        print(
            json.dumps(
                {
                    "op019_fixture": str(result_dir),
                    "manifest_sha256": manifest_sha,
                    "timing_valid": False,
                },
                sort_keys=True,
            ),
            flush=True,
        )
        return result_dir


def qsa_exact_fixture_capture_begin(
    rows: int,
    logical_positions: torch.Tensor,
    token_to_req: torch.Tensor,
    sequence_lengths: torch.Tensor,
):
    if os.environ.get("VLLM_FL_QSA_FIXTURE_CAPTURE", "0") != "1":
        return None
    if _rank() != int(os.environ.get("VLLM_FL_QSA_FIXTURE_RANK", "0")):
        return None
    if _capturing():
        raise RuntimeError("op-019 exact capture is eager-only; use --enforce-eager")
    arm_path = Path(os.environ["VLLM_FL_QSA_FIXTURE_ARM_FILE"]).resolve()
    if not arm_path.is_file():
        return None
    arm = json.loads(arm_path.read_text(encoding="utf-8"))
    if int(rows) != int(arm.get("expected_rows", 4096)):
        return None

    requests = token_to_req.to(torch.int64)
    valid = requests >= 0
    starts = valid.clone()
    if requests.numel() > 1:
        starts[1:] &= requests[1:] != requests[:-1]
    request_runs = int(starts.sum(dtype=torch.int64).item())
    if not int(arm["min_request_runs"]) <= request_runs <= int(
        arm["max_request_runs"]
    ):
        return None

    claim = arm_path.with_name(
        f"{arm_path.name}.claimed.rank{_rank()}.pid{os.getpid()}"
    )
    arm_path.replace(claim)
    return QSAExactFixtureCollector(
        rows=rows,
        positions=logical_positions,
        requests=token_to_req,
        sequence_lengths=sequence_lengths,
        arm=arm,
        claim=claim,
        request_runs=request_runs,
    )

