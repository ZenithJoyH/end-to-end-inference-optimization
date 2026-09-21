#!/usr/bin/env python3
"""Capture the exact live MiniMax-M3 service and source identities."""

import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys


MODEL = Path("/mnt/cpfs/models/MiniMax-M3")
REPOSITORIES = (
    Path("/workspace/vllm-plugin-FL"),
    Path("/workspace/FlagGems-vllm"),
    Path("/workspace/FlagGems"),
)
TOKENIZER_FILES = (
    "added_tokens.json",
    "chat_template.jinja",
    "merges.txt",
    "special_tokens_map.json",
    "tokenizer_config.json",
    "tokenizer.json",
    "vocab.json",
)


def file_digest(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def digest_entries(entries):
    digest = hashlib.sha256()
    for relative, sha256, size in sorted(entries):
        digest.update(relative.encode() + b"\0")
        digest.update(str(size).encode() + b"\0")
        digest.update(sha256.encode() + b"\0")
    return digest.hexdigest()


def repository(path):
    listed = subprocess.check_output(
        ["git", "-C", str(path), "ls-files", "-co", "--exclude-standard", "-z"]
    )
    entries = []
    for raw in sorted(item for item in listed.split(b"\0") if item):
        relative = os.fsdecode(raw)
        source = path / relative
        entries.append((relative, file_digest(source), source.stat().st_size))
    return {
        "head": subprocess.check_output(
            ["git", "-C", str(path), "rev-parse", "HEAD"], text=True
        ).strip(),
        "status": subprocess.check_output(
            ["git", "-C", str(path), "status", "--short"], text=True
        ),
        "content_sha256": digest_entries(entries),
        "file_count": len(entries),
    }


def find_service():
    matches = []
    for entry in os.listdir("/proc"):
        if not entry.isdigit():
            continue
        try:
            argv = [
                item.decode(errors="replace")
                for item in Path(f"/proc/{entry}/cmdline").read_bytes().split(b"\0")
                if item
            ]
            stat = Path(f"/proc/{entry}/stat").read_text()
        except (FileNotFoundError, PermissionError, ProcessLookupError):
            continue
        if MODEL.as_posix() not in argv or "--port" not in argv:
            continue
        if argv[argv.index("--port") + 1] != "8023":
            continue
        matches.append(
            {
                "pid": int(entry),
                "start_ticks": int(stat[stat.rfind(")") + 2 :].split()[19]),
                "argv": argv,
            }
        )
    if len(matches) != 1:
        raise SystemExit(f"expected one MiniMax-M3 service on 8023, got {len(matches)}")
    return matches[0]


def model_identity():
    entries = []
    for path in sorted(MODEL.rglob("*")):
        if not path.is_file():
            continue
        relative = path.relative_to(MODEL).as_posix()
        size = path.stat().st_size
        if path.suffix == ".safetensors":
            sha256 = "size-only-not-content-hashed"
        else:
            sha256 = file_digest(path)
        entries.append((relative, sha256, size))
    return {
        "sha256": digest_entries(entries),
        "method": "sha256(sorted(relative_path,NUL,size,NUL,content_sha256_or_safetensors_size_marker,NUL)); all non-safetensors are content-hashed",
        "file_count": len(entries),
        "safetensors_count": sum(1 for relative, _, _ in entries if relative.endswith(".safetensors")),
    }


def tokenizer_identity():
    entries = []
    for relative in TOKENIZER_FILES:
        path = MODEL / relative
        entries.append((relative, file_digest(path), path.stat().st_size))
    return {"sha256": digest_entries(entries), "files": list(TOKENIZER_FILES)}


def engine_identity():
    root = Path("/usr/local/lib/python3.12/site-packages/vllm")
    entries = []
    for path in sorted(root.rglob("*.py")):
        if path.is_file():
            entries.append((path.relative_to(root).as_posix(), file_digest(path), path.stat().st_size))
    return {"sha256": digest_entries(entries), "root": str(root), "python_file_count": len(entries)}


payload = {
    "schema_version": 1,
    "service": find_service(),
    "model_identity": model_identity(),
    "tokenizer_identity": tokenizer_identity(),
    "engine_identity": engine_identity(),
    "repositories": {str(path): repository(path) for path in REPOSITORIES},
}
json.dump(payload, sys.stdout, indent=2, sort_keys=True)
sys.stdout.write("\n")
