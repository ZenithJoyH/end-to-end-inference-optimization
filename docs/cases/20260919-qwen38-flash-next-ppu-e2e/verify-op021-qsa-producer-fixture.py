#!/usr/bin/env python3
"""Verify raw fixture integrity and optionally replay the real QSA producer."""

import argparse
import hashlib
import json
from pathlib import Path

import torch


DTYPES = {
    "bfloat16-le": torch.bfloat16,
    "float16-le": torch.float16,
    "float32-le": torch.float32,
    "int32-le": torch.int32,
    "int64-le": torch.int64,
}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(root: Path, entry: dict) -> torch.Tensor:
    path = root / entry["path"]
    if path.stat().st_size != entry["nbytes"] or sha(path) != entry["sha256"]:
        raise SystemExit(f"integrity mismatch: {path}")
    buffer = bytearray(path.read_bytes())
    value = torch.frombuffer(buffer, dtype=DTYPES[entry["dtype"]]).clone()
    expected = 1
    for extent in entry["shape"]:
        expected *= int(extent)
    if value.numel() != expected:
        raise SystemExit(f"shape/byte mismatch: {path}")
    return value.reshape(entry["shape"])


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("fixture_dir", type=Path)
    parser.add_argument("--integrity-only", action="store_true")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    root = args.fixture_dir.resolve()
    manifest_path = root / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    tensors = {name: load(root, entry) for name, entry in manifest["files"].items()}
    if manifest["estimated_raw_bytes"] != sum(e["nbytes"] for e in manifest["files"].values()):
        raise SystemExit("manifest byte total mismatch")
    page_ids = tensors["compressed_source_page_ids"]
    if page_ids.numel() != manifest["captured_cache_pages"]:
        raise SystemExit("captured page count mismatch")
    if page_ids.numel() > 1 and not bool(torch.all(page_ids[1:] > page_ids[:-1])):
        raise SystemExit("source page ids are not strictly increasing")
    table = tensors["compressed_page_table"]
    if bool((table >= manifest["captured_cache_pages"]).any()):
        raise SystemExit("compact table points outside compact cache")
    if tuple(tensors["index_q"].shape) != (4096, 4, 128):
        raise SystemExit("index_q shape mismatch")
    page_size = int(manifest["page_size"])
    if page_size != int(manifest["expected_cache_page_size"]):
        raise SystemExit("captured cache page size differs from frozen ABI")
    if tuple(tensors["compressed_k"].shape[1:]) != (page_size, 1, 128):
        raise SystemExit("compressed_k shape mismatch")
    if tuple(tensors["selected"].shape) != (4096, 2051):
        raise SystemExit("selected shape mismatch")
    requests = tensors["token_to_req"].to(torch.int64)
    active_ids = torch.unique(requests[requests >= 0], sorted=True)
    inactive = torch.ones(table.shape[0], dtype=torch.bool)
    if active_ids.numel():
        if int(active_ids[-1]) >= table.shape[0]:
            raise SystemExit("active request id exceeds compact table")
        inactive[active_ids] = False
    if bool((table[inactive] != -1).any()):
        raise SystemExit("inactive request table rows are not fully masked")
    if table.shape[1] != (manifest["static_score_columns"] + page_size - 1) // page_size:
        raise SystemExit("compact table width does not cover exact score width")
    result = {
        "schema_version": 1,
        "experiment_id": "op-021",
        "manifest_sha256": sha(manifest_path),
        "integrity": "passed",
        "producer_replay": "not_run",
        "selected_exact_match": None,
    }
    if not args.integrity_only:
        from flag_gems.fused.qsa import qsa_select_paged_tokens

        device = torch.device("cuda")
        q = tensors["index_q"].to(device)
        k = tensors["compressed_k"].to(device)
        page_table = table.to(device)
        requests = tensors["token_to_req"].to(device)
        positions = tensors["query_positions"].to(device)
        lengths = tensors["sequence_lengths"].to(device)
        expected = tensors["selected"]
        actual = torch.empty_like(expected, device=device)
        qsa_select_paged_tokens(
            q, k, page_table, requests, positions, lengths,
            manifest["token_topk"], manifest["compress_ratio"], out=actual,
            static_score_columns=manifest["static_score_columns"],
        )
        torch.cuda.synchronize()
        actual_cpu = actual.cpu()
        if not torch.equal(actual_cpu, expected):
            mismatch = int(torch.count_nonzero(actual_cpu != expected))
            raise SystemExit(f"producer replay selected mismatch: {mismatch} cells")
        result["producer_replay"] = "passed"
        result["selected_exact_match"] = True
    text = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output:
        if args.output.exists():
            raise SystemExit("refusing to overwrite verification output")
        args.output.write_text(text, encoding="utf-8")
    print(text, end="")


if __name__ == "__main__":
    main()
