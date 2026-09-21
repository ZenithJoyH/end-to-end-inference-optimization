#!/usr/bin/env python3
"""Apply op-019 exact fixture capture with source SHA and anchor guards."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from pathlib import Path


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{label}: expected exactly one anchor, got {count}")
    return text.replace(old, new, 1)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--qsa", required=True)
    parser.add_argument("--helper", required=True)
    parser.add_argument("--artifact-dir", required=True)
    parser.add_argument("--expected-sha256", required=True)
    args = parser.parse_args()

    qsa = Path(args.qsa).resolve()
    helper_source = Path(args.helper).resolve()
    artifact = Path(args.artifact_dir).resolve()
    helper_target = qsa.with_name("qsa_exact_fixture_capture.py")
    if artifact.exists() or helper_target.exists():
        raise SystemExit("artifact directory or helper target already exists")
    if sha(qsa) != args.expected_sha256:
        raise SystemExit("qsa.py SHA mismatch; refusing to patch unknown source")
    artifact.mkdir(parents=True)
    backup = artifact / "qsa.py.before"
    shutil.copy2(qsa, backup)
    shutil.copy2(helper_source, helper_target)

    text = qsa.read_text(encoding="utf-8")
    text = replace_once(
        text,
        "import torch\n",
        "import torch\n\n"
        "from .qsa_exact_fixture_capture import qsa_exact_fixture_capture_begin\n",
        "import",
    )
    start = text.index("def qsa_select_paged_tokens(")
    end = text.find("\ndef ", start + 1)
    if end < 0:
        end = len(text)
    before, function, after = text[:start], text[start:end], text[end:]
    if "sequence_lengths" not in function.split("):", 1)[0]:
        raise SystemExit("sequence_lengths is absent from qsa_select_paged_tokens signature")
    function = replace_once(
        function,
        "    block_topk = token_topk // compress_ratio\n",
        "    block_topk = token_topk // compress_ratio\n"
        "    fixture_collector = qsa_exact_fixture_capture_begin(\n"
        "        rows, query_positions, token_to_req, sequence_lengths\n"
        "    )\n",
        "collector-begin",
    )
    expand_anchor = "        expand_qsa_block_indices(\n"
    if function.count(expand_anchor) != 1:
        raise SystemExit("expand_qsa_block_indices anchor is not unique")
    final_return = function.rfind("    return out\n")
    if final_return < 0:
        raise SystemExit("collector-finish: final return anchor is missing")
    function = (
        function[:final_return]
        + "    if fixture_collector is not None:\n"
        + "        fixture_collector.finish(out)\n"
        + function[final_return:]
    )
    qsa.write_text(before + function + after, encoding="utf-8")

    manifest = {
        "qsa_path": str(qsa),
        "helper_path": str(helper_target),
        "before_sha256": sha(backup),
        "patched_sha256": sha(qsa),
        "helper_sha256": sha(helper_target),
        "backup_path": str(backup),
        "prepare_script_sha256": sha(Path(__file__).resolve()),
    }
    manifest_path = artifact / "patch-manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(manifest, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()

