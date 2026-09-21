"""Bounded, one-shot capture of the real QSA producer input transaction.

Diagnostic only: this helper synchronizes the device and copies tensors to the
host.  It must be armed only in an isolated eager service; capture-run timings
are invalid by construction.
"""

from __future__ import annotations

import hashlib
import json
import math
import os
import re
import sys
import time
from pathlib import Path

import torch


_SAMPLE_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,127}\Z")
_DTYPES = {
    torch.bfloat16: "bfloat16-le",
    torch.float16: "float16-le",
    torch.float32: "float32-le",
    torch.int32: "int32-le",
    torch.int64: "int64-le",
}


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


def _write_raw(path: Path, tensor: torch.Tensor) -> dict:
    if sys.byteorder != "little":
        raise RuntimeError("op-021 requires a little-endian host")
    if tensor.dtype not in _DTYPES:
        raise RuntimeError(f"unsupported fixture dtype: {tensor.dtype}")
    value = tensor.detach().to("cpu").contiguous()
    payload = value.view(torch.uint8).numpy()
    temporary = path.with_name(path.name + f".tmp.pid{os.getpid()}")
    with temporary.open("xb") as stream:
        stream.write(memoryview(payload).cast("B"))
        stream.flush()
        os.fsync(stream.fileno())
    temporary.replace(path)
    return {
        "path": path.name,
        "dtype": _DTYPES[value.dtype],
        "shape": list(value.shape),
        "nbytes": path.stat().st_size,
        "sha256": _sha256(path),
    }


def _request_runs(requests: torch.Tensor) -> tuple[int, int, torch.Tensor]:
    req = requests.to(device="cpu", dtype=torch.int64).contiguous()
    valid = req >= 0
    invalid = torch.nonzero(~valid, as_tuple=False).flatten()
    actual_rows = int(invalid[0]) if invalid.numel() else req.numel()
    if bool(valid[actual_rows:].any()):
        raise RuntimeError("negative token_to_req padding is not a suffix")
    active = req[:actual_rows]
    if active.numel() == 0:
        return actual_rows, 0, torch.empty(0, dtype=torch.int64)
    starts = torch.ones(actual_rows, dtype=torch.bool)
    starts[1:] = active[1:] != active[:-1]
    run_ids = active[starts]
    if torch.unique(run_ids).numel() != run_ids.numel():
        raise RuntimeError("one request id appears in multiple row runs")
    return actual_rows, int(run_ids.numel()), run_ids


class QSAProducerFixtureCollector:
    def __init__(
        self,
        *,
        q: torch.Tensor,
        k_cache: torch.Tensor,
        page_table: torch.Tensor,
        token_to_req: torch.Tensor,
        query_positions: torch.Tensor,
        sequence_lengths: torch.Tensor,
        token_topk: int,
        compress_ratio: int,
        static_score_columns: int | None,
        arm: dict,
        claim: Path,
        actual_rows: int,
        request_runs: int,
        run_ids: torch.Tensor,
    ) -> None:
        self.q = q
        self.k_cache = k_cache
        self.page_table = page_table
        self.token_to_req = token_to_req
        self.query_positions = query_positions
        self.sequence_lengths = sequence_lengths
        self.token_topk = int(token_topk)
        self.compress_ratio = int(compress_ratio)
        self.static_score_columns = static_score_columns
        self.arm = arm
        self.claim = claim
        self.actual_rows = actual_rows
        self.request_runs = request_runs
        self.run_ids = run_ids
        self.started = time.monotonic()

    def finish(self, selected: torch.Tensor) -> Path:
        if _capturing():
            raise RuntimeError("op-021 is eager-only")
        rows = int(self.q.shape[0])
        expected_width = self.token_topk + self.compress_ratio - 1
        if tuple(selected.shape) != (rows, expected_width):
            raise RuntimeError("selected output shape does not match producer ABI")
        if self.q.dtype != torch.bfloat16 or self.k_cache.dtype != torch.bfloat16:
            raise RuntimeError("expected BF16 index Q and compressed K cache")
        if self.q.ndim != 3 or tuple(self.q.shape[1:]) != (4, 128):
            raise RuntimeError(f"unexpected index Q shape: {tuple(self.q.shape)}")
        expected_ratio = int(self.arm["expected_compress_ratio"])
        if self.compress_ratio != expected_ratio:
            raise RuntimeError(
                f"unexpected compression ratio: {self.compress_ratio} != {expected_ratio}"
            )
        expected_page_size = int(self.arm["expected_cache_page_size"])
        expected_cache_tail = (expected_page_size, 1, int(self.q.shape[2]))
        if self.k_cache.ndim != 4 or tuple(self.k_cache.shape[1:]) != expected_cache_tail:
            raise RuntimeError(
                "unexpected compressed K cache shape: "
                f"{tuple(self.k_cache.shape)}; expected [blocks, "
                f"{expected_page_size}, 1, {self.q.shape[2]}]"
            )
        if self.page_table.ndim != 2 or self.page_table.dtype != torch.int32:
            raise RuntimeError("compressed page table must be rank-2 int32")

        torch.cuda.synchronize()
        table_cpu = self.page_table.detach().to("cpu", dtype=torch.int32).contiguous()
        seq_cpu = self.sequence_lengths.detach().to("cpu").contiguous()
        req_cpu = self.token_to_req.detach().to("cpu", dtype=torch.int32).contiguous()
        pos_cpu = self.query_positions.detach().to("cpu").contiguous()
        q_cpu = self.q.detach().to("cpu").contiguous()
        selected_cpu = selected.detach().to("cpu", dtype=torch.int32).contiguous()

        page_size = int(self.k_cache.shape[1])
        capacity = int(table_cpu.shape[1]) * page_size
        columns = capacity if self.static_score_columns is None else int(self.static_score_columns)
        if columns <= 0 or columns > capacity:
            raise RuntimeError("invalid static_score_columns for captured table")
        table_columns = math.ceil(columns / page_size)
        active_ids = self.run_ids.to(dtype=torch.int64)
        if active_ids.numel() and (
            int(active_ids.min()) < 0 or int(active_ids.max()) >= table_cpu.shape[0]
        ):
            raise RuntimeError("active request id is outside compressed page table")

        # Retain only pages reachable by active requests within the exact static
        # score-width prefix.  Preserve request ids, densely remap physical page
        # ids, and fill every unreachable table cell with -1.
        compact_table = torch.full(
            (table_cpu.shape[0], table_columns), -1, dtype=torch.int32
        )
        referenced = (
            table_cpu.index_select(0, active_ids)[:, :table_columns].reshape(-1)
            if active_ids.numel()
            else torch.empty(0, dtype=torch.int32)
        )
        source_pages = torch.unique(referenced[referenced >= 0], sorted=True)
        max_pages = int(self.arm["max_cache_pages"])
        if source_pages.numel() > max_pages:
            raise RuntimeError("referenced compressed-cache pages exceed arm budget")
        if source_pages.numel() and int(source_pages[-1]) >= self.k_cache.shape[0]:
            raise RuntimeError("compressed page table references an out-of-range page")
        mapping = {int(page): dense for dense, page in enumerate(source_pages.tolist())}
        for req_id in active_ids.tolist():
            row = table_cpu[int(req_id), :table_columns]
            remapped = torch.full_like(row, -1)
            for source, dense in mapping.items():
                remapped[row == source] = dense
            compact_table[int(req_id)] = remapped

        estimated = (
            q_cpu.numel() * q_cpu.element_size()
            + source_pages.numel() * self.k_cache[0].numel() * self.k_cache.element_size()
            + compact_table.numel() * compact_table.element_size()
            + req_cpu.numel() * req_cpu.element_size()
            + pos_cpu.numel() * pos_cpu.element_size()
            + seq_cpu.numel() * seq_cpu.element_size()
            + selected_cpu.numel() * selected_cpu.element_size()
            + source_pages.numel() * source_pages.element_size()
        )
        if estimated > int(self.arm["max_total_bytes"]):
            raise RuntimeError(
                f"fixture byte budget exceeded: {estimated} > {self.arm['max_total_bytes']}"
            )
        if source_pages.numel():
            # Avoid accelerator index_select: the active FlagGems path first
            # materializes the complete multi-GiB cache and can OOM.  Copy
            # each already-bounded one-page view to host, then join on CPU.
            compact_pages = [
                self.k_cache[int(page) : int(page) + 1]
                .detach()
                .to("cpu")
                .contiguous()
                for page in source_pages.tolist()
            ]
            compact_k = torch.cat(compact_pages, dim=0)
        else:
            compact_k = torch.empty(
                (0, *self.k_cache.shape[1:]), dtype=self.k_cache.dtype
            )

        sample_id = str(self.arm["sample_id"])
        if not _SAMPLE_RE.fullmatch(sample_id):
            raise RuntimeError("unsafe sample_id")
        root = Path(os.environ["VLLM_FL_QSA_PRODUCER_OUTPUT_DIR"]).resolve()
        case_root = Path(os.environ["VLLM_FL_QSA_PRODUCER_CASE_ROOT"]).resolve()
        if os.path.commonpath((str(root), str(case_root))) != str(case_root):
            raise RuntimeError("fixture output escapes the user-specified case root")
        if root == case_root or not root.is_dir() or not os.access(root, os.W_OK):
            raise RuntimeError("fixture output must be a writable case subdirectory")
        result_dir = root / sample_id
        temporary = root / f".{sample_id}.tmp.pid{os.getpid()}"
        if result_dir.exists() or temporary.exists():
            raise RuntimeError("refusing to overwrite a fixture")
        disk = os.statvfs(root)
        free_bytes = disk.f_bavail * disk.f_frsize
        if free_bytes < estimated + 16 * 1024 * 1024:
            raise RuntimeError("insufficient free space for atomic fixture write")
        temporary.mkdir(parents=False)
        files = {
            "index_q": _write_raw(temporary / "index_q.bfloat16.bin", q_cpu),
            "compressed_k": _write_raw(temporary / "compressed_k.bfloat16.bin", compact_k),
            "compressed_page_table": _write_raw(
                temporary / "compressed_page_table.int32.bin", compact_table
            ),
            "compressed_source_page_ids": _write_raw(
                temporary / "compressed_source_page_ids.int32.bin",
                source_pages.to(torch.int32),
            ),
            "token_to_req": _write_raw(temporary / "token_to_req.int32.bin", req_cpu),
            "query_positions": _write_raw(temporary / "query_positions.raw.bin", pos_cpu),
            "sequence_lengths": _write_raw(
                temporary / "sequence_lengths.raw.bin", seq_cpu
            ),
            "selected": _write_raw(temporary / "selected.int32.bin", selected_cpu),
        }
        observed_phase = "mixed" if self.request_runs >= 2 else "prefill"
        if observed_phase != self.arm["expected_phase"]:
            raise RuntimeError("captured request phase does not match arm")
        qsa_path = Path(__file__).with_name("qsa.py")
        manifest = {
            "schema_version": 1,
            "experiment_id": "op-021",
            "artifact_kind": "real-qsa-producer-input-fixture",
            "sample_id": sample_id,
            "rank": _rank(),
            "rows": rows,
            "actual_rows": self.actual_rows,
            "request_runs": self.request_runs,
            "observed_phase": observed_phase,
            "token_topk": self.token_topk,
            "compress_ratio": self.compress_ratio,
            "expected_cache_page_size": expected_page_size,
            "static_score_columns": columns,
            "page_size": page_size,
            "source_cache_pages": int(self.k_cache.shape[0]),
            "captured_cache_pages": int(source_pages.numel()),
            "compact_table_columns": table_columns,
            "estimated_raw_bytes": int(estimated),
            "files": files,
            "endianness": "little",
            "pickle_used": False,
            "contains_prompt_text": False,
            "contains_token_ids": False,
            "contains_model_weights": False,
            "contains_synthetic_request_activations": True,
            "timing_valid": False,
            "timing_invalid_reason": "device synchronization and D2H fixture copies",
            "source": {
                "qsa_path": str(qsa_path),
                "qsa_sha256": _sha256(qsa_path),
                "helper_path": str(Path(__file__).resolve()),
                "helper_sha256": _sha256(Path(__file__).resolve()),
            },
            "arm_provenance": self.arm.get("provenance", {}),
            "elapsed_host_seconds_including_sync_and_write": time.monotonic() - self.started,
        }
        manifest_path = temporary / "manifest.json"
        manifest_path.write_text(
            json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        sums = [f"{entry['sha256']}  {entry['path']}" for entry in files.values()]
        sums.append(f"{_sha256(manifest_path)}  manifest.json")
        (temporary / "SHA256SUMS").write_text(
            "\n".join(sorted(sums)) + "\n", encoding="utf-8"
        )
        temporary.replace(result_dir)
        self.claim.unlink(missing_ok=True)
        print(json.dumps({"op021_fixture": str(result_dir), "timing_valid": False}), flush=True)
        return result_dir


def qsa_producer_fixture_capture_begin(
    q: torch.Tensor,
    k_cache: torch.Tensor,
    page_table: torch.Tensor,
    token_to_req: torch.Tensor,
    query_positions: torch.Tensor,
    sequence_lengths: torch.Tensor,
    token_topk: int,
    compress_ratio: int,
    static_score_columns: int | None,
):
    if os.environ.get("VLLM_FL_QSA_PRODUCER_CAPTURE", "0") != "1":
        return None
    if _rank() != int(os.environ.get("VLLM_FL_QSA_PRODUCER_RANK", "0")):
        return None
    if _capturing():
        raise RuntimeError("op-021 capture requires --enforce-eager")
    arm_path = Path(os.environ["VLLM_FL_QSA_PRODUCER_ARM_FILE"]).resolve()
    if not arm_path.is_file() or int(q.shape[0]) != 4096:
        return None
    arm = json.loads(arm_path.read_text(encoding="utf-8"))
    if int(q.shape[0]) != int(arm["expected_rows"]):
        return None
    actual_rows, runs, run_ids = _request_runs(token_to_req)
    minimum, maximum = int(arm["min_request_runs"]), int(arm["max_request_runs"])
    if not minimum <= runs <= maximum:
        return None
    claim = arm_path.with_name(f"{arm_path.name}.claimed.rank{_rank()}.pid{os.getpid()}")
    arm_path.replace(claim)
    return QSAProducerFixtureCollector(
        q=q,
        k_cache=k_cache,
        page_table=page_table,
        token_to_req=token_to_req,
        query_positions=query_positions,
        sequence_lengths=sequence_lengths,
        token_topk=token_topk,
        compress_ratio=compress_ratio,
        static_score_columns=static_score_columns,
        arm=arm,
        claim=claim,
        actual_rows=actual_rows,
        request_runs=runs,
        run_ids=run_ids,
    )
