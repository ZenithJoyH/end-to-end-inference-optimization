#!/usr/bin/env python3
"""Rerun exactly the 30K-truncated GPQA occurrences with a 60K output cap."""

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib
import json
import os
from pathlib import Path
import re
import time
import urllib.error
import urllib.request


ANSWER_PATTERNS = (
    re.compile(r"best answer is\s*(?:\*\*)?\(?([ABCD])\)?", re.I),
    re.compile(r"answer is\s*(?:\*\*)?\(?([ABCD])\)?", re.I),
)


def sha256_path(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def extract_answer(text):
    for pattern in ANSWER_PATTERNS:
        matches = pattern.findall(text)
        if matches:
            return f"({matches[-1].upper()})"
    return "[invalid]"


def atomic_json(path, value):
    path = Path(path)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    os.replace(temporary, path)


def load_manifest(aggregate_path, max_tokens, server_max_model_len, experiment_id):
    aggregate = json.loads(Path(aggregate_path).read_text(encoding="utf-8"))
    rows = []
    sources = []
    for run in aggregate["runs"]:
        seed = int(run["seed"])
        samples_path = Path(run["samples"]["path"])
        if sha256_path(samples_path) != run["samples"]["sha256"]:
            raise ValueError(f"source sample checksum mismatch: {samples_path}")
        sources.append({"seed": seed, "path": str(samples_path), "sha256": run["samples"]["sha256"]})
        seen = set()
        for line in samples_path.open(encoding="utf-8"):
            sample = json.loads(line)
            if sample.get("filter") != "strict-match":
                continue
            usage = sample.get("usage") or {}
            if usage.get("completion_tokens") != 30000:
                continue
            doc_id = int(sample["doc_id"])
            if doc_id in seen:
                raise ValueError(f"duplicate strict row seed={seed} doc_id={doc_id}")
            seen.add(doc_id)
            prompt_tokens = int(usage["prompt_tokens"])
            if prompt_tokens + max_tokens > server_max_model_len:
                raise ValueError(
                    f"request exceeds server limit seed={seed} doc_id={doc_id}: "
                    f"{prompt_tokens}+{max_tokens}>{server_max_model_len}"
                )
            argument = sample["arguments"]["gen_args_0"]["arg_0"][0]
            rows.append({
                "request_id": f"seed-{seed}-doc-{doc_id}",
                "seed": seed,
                "doc_id": doc_id,
                "messages": json.loads(argument),
                "target": sample["target"],
                "prompt_tokens_30k_run": prompt_tokens,
                "original_exact_match": sample["exact_match"],
                "original_filtered_response": sample["filtered_resps"][0],
                "original_response_sha256": hashlib.sha256(sample["resps"][0][0].encode()).hexdigest(),
                "doc_hash": sample["doc_hash"],
                "prompt_hash": sample["prompt_hash"],
                "target_hash": sample["target_hash"],
            })
    rows.sort(key=lambda row: (row["seed"], row["doc_id"]))
    if len(rows) != 64:
        raise ValueError(f"expected 64 truncated occurrences, got {len(rows)}")
    return {
        "schema_version": 1,
        "experiment_id": experiment_id,
        "source_aggregate": {"path": str(aggregate_path), "sha256": sha256_path(aggregate_path)},
        "source_samples": sources,
        "selection": "strict-match rows whose native usage.completion_tokens equals 30000",
        "request_count": len(rows),
        "unique_doc_count": len({row["doc_id"] for row in rows}),
        "request": {
            "model": "MiniMax-M3",
            "max_tokens": max_tokens,
            "temperature": 1,
            "top_p": 0.95,
            "top_k": 20,
            "stop": ["</s>"],
            "seed": "preserve each source run request seed",
        },
        "server_max_model_len": server_max_model_len,
        "max_prompt_tokens": max(row["prompt_tokens_30k_run"] for row in rows),
        "max_prompt_plus_generation": max(row["prompt_tokens_30k_run"] + max_tokens for row in rows),
        "rows": rows,
    }


def request_once(base_url, max_tokens, spec):
    payload = {
        "model": "MiniMax-M3",
        "messages": spec["messages"],
        "max_tokens": max_tokens,
        "temperature": 1,
        "top_p": 0.95,
        "top_k": 20,
        "seed": spec["seed"],
        "stop": ["</s>"],
    }
    request = urllib.request.Request(
        base_url,
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
    )
    started = time.time()
    try:
        with urllib.request.urlopen(request, timeout=14400) as response:
            result = json.load(response)
        text = result["choices"][0]["message"]["content"]
        usage = result.get("usage") or {}
        extracted = extract_answer(text)
        return {
            "request_id": spec["request_id"],
            "seed": spec["seed"],
            "doc_id": spec["doc_id"],
            "status": "success",
            "elapsed_seconds": time.time() - started,
            "target": spec["target"],
            "extracted": extracted,
            "exact_match": float(extracted == spec["target"]),
            "original_exact_match": spec["original_exact_match"],
            "original_filtered_response": spec["original_filtered_response"],
            "prompt_tokens": usage.get("prompt_tokens"),
            "completion_tokens": usage.get("completion_tokens"),
            "total_tokens": usage.get("total_tokens"),
            "finish_reason": result["choices"][0].get("finish_reason"),
            "response_sha256": hashlib.sha256(text.encode()).hexdigest(),
            "response": text,
            "doc_hash": spec["doc_hash"],
            "prompt_hash": spec["prompt_hash"],
            "target_hash": spec["target_hash"],
        }
    except Exception as error:
        body = None
        if isinstance(error, urllib.error.HTTPError):
            body = error.read().decode(errors="replace")
        return {
            "request_id": spec["request_id"],
            "seed": spec["seed"],
            "doc_id": spec["doc_id"],
            "status": "error",
            "elapsed_seconds": time.time() - started,
            "error_type": type(error).__name__,
            "error": str(error),
            "http_body": body,
        }


def summarize(manifest, result_rows):
    successful = [row for row in result_rows if row["status"] == "success"]
    summary = {
        "schema_version": 1,
        "experiment_id": manifest["experiment_id"],
        "diagnostic_only": True,
        "formal_gate": False,
        "request_count": len(result_rows),
        "successful": len(successful),
        "errors": len(result_rows) - len(successful),
        "empty_outputs": sum(not row.get("response") for row in successful),
        "truncated_at_60000": sum(row.get("completion_tokens") == 60000 for row in successful),
        "original_correct": sum(row["original_exact_match"] for row in successful),
        "new_correct": sum(row["exact_match"] for row in successful),
        "recovered_wrong_to_correct": sum(
            row["original_exact_match"] == 0 and row["exact_match"] == 1 for row in successful
        ),
        "regressed_correct_to_wrong": sum(
            row["original_exact_match"] == 1 and row["exact_match"] == 0 for row in successful
        ),
        "completion_tokens": {
            "min": min((row["completion_tokens"] for row in successful), default=None),
            "max": max((row["completion_tokens"] for row in successful), default=None),
            "sum": sum((row["completion_tokens"] for row in successful), 0),
        },
        "per_seed": {},
    }
    for seed in sorted({row["seed"] for row in result_rows}):
        selected = [row for row in result_rows if row["seed"] == seed]
        okay = [row for row in selected if row["status"] == "success"]
        summary["per_seed"][str(seed)] = {
            "requests": len(selected),
            "successful": len(okay),
            "errors": len(selected) - len(okay),
            "truncated_at_60000": sum(row.get("completion_tokens") == 60000 for row in okay),
            "original_correct": sum(row["original_exact_match"] for row in okay),
            "new_correct": sum(row["exact_match"] for row in okay),
        }
    return summary


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--aggregate", required=True)
    parser.add_argument("--output-root", required=True)
    parser.add_argument("--base-url", default="http://127.0.0.1:8023/v1/chat/completions")
    parser.add_argument("--experiment-id", default="accdiag-003-gpqa-truncated-60k")
    parser.add_argument("--max-tokens", type=int, default=60000)
    parser.add_argument("--server-max-model-len", type=int, default=65536)
    parser.add_argument("--concurrency", type=int, default=64)
    args = parser.parse_args()

    root = Path(args.output_root)
    root.mkdir(parents=True, exist_ok=True)
    if any((root / name).exists() for name in ("manifest.json", "progress.json", "results.json", "summary.json", "responses")):
        raise SystemExit(f"refusing to overwrite evaluator artifacts in {root}")
    (root / "responses").mkdir()
    manifest = load_manifest(
        args.aggregate, args.max_tokens, args.server_max_model_len, args.experiment_id
    )
    atomic_json(root / "manifest.json", manifest)
    atomic_json(root / "progress.json", {
        "status": "running", "completed": 0, "total": len(manifest["rows"]), "errors": 0,
    })

    results = []
    started = time.time()
    with ThreadPoolExecutor(max_workers=args.concurrency) as pool:
        futures = {
            pool.submit(request_once, args.base_url, args.max_tokens, spec): spec
            for spec in manifest["rows"]
        }
        for future in as_completed(futures):
            row = future.result()
            results.append(row)
            atomic_json(root / "responses" / f"{row['request_id']}.json", row)
            atomic_json(root / "progress.json", {
                "status": "running",
                "completed": len(results),
                "total": len(manifest["rows"]),
                "errors": sum(item["status"] == "error" for item in results),
                "elapsed_seconds": time.time() - started,
                "last_request_id": row["request_id"],
                "last_update_unix": time.time(),
            })

    results.sort(key=lambda row: (row["seed"], row["doc_id"]))
    atomic_json(root / "results.json", {"schema_version": 1, "rows": results})
    summary = summarize(manifest, results)
    atomic_json(root / "summary.json", summary)
    atomic_json(root / "progress.json", {
        "status": "complete" if summary["errors"] == 0 else "complete_with_errors",
        "completed": len(results),
        "total": len(manifest["rows"]),
        "errors": summary["errors"],
        "elapsed_seconds": time.time() - started,
        "last_update_unix": time.time(),
    })


if __name__ == "__main__":
    main()
