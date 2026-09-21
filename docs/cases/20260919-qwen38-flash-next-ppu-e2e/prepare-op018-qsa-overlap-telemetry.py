#!/usr/bin/env python3
"""Apply the one-shot op-018 FlagGems telemetry with exact source guards."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from pathlib import Path


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def replace_once(text: str, old: str, new: str, label: str) -> str:
    if text.count(old) != 1:
        raise SystemExit(f"{label}: expected exactly one anchor, got {text.count(old)}")
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
    helper_target = qsa.with_name("qsa_overlap_telemetry.py")
    if artifact.exists() or helper_target.exists():
        raise SystemExit("artifact directory or helper target already exists")
    if sha(qsa) != args.expected_sha256:
        raise SystemExit("qsa.py SHA mismatch; refusing to patch an unknown source")
    artifact.mkdir(parents=True)
    backup = artifact / "qsa.py.before"
    shutil.copy2(qsa, backup)
    shutil.copy2(helper_source, helper_target)
    text = qsa.read_text()
    text = replace_once(
        text,
        "import torch\n",
        "import torch\n\nfrom .qsa_overlap_telemetry import qsa_overlap_telemetry_begin\n",
        "import",
    )
    start = text.index("def qsa_select_paged_tokens(")
    end = text.find("\ndef ", start + 1)
    if end < 0:
        end = len(text)
    before, function, after = text[:start], text[start:end], text[end:]
    function = replace_once(
        function,
        "    block_topk = token_topk // compress_ratio\n",
        "    block_topk = token_topk // compress_ratio\n"
        "    overlap_collector = qsa_overlap_telemetry_begin(\n"
        "        rows, query_positions, token_to_req\n"
        "    )\n",
        "collector-begin",
    )
    topk_anchor = (
        "        _, blocks = torch.topk(\n"
        "            logits, block_topk, dim=-1, largest=True, sorted=True\n"
        "        )\n"
    )
    if topk_anchor not in function:
        topk_anchor = (
            "        _, blocks = torch.topk(logits, block_topk, dim=-1, "
            "largest=True, sorted=True)\n"
        )
    # Merely verify the real compressed TopK insertion point.  The metric is
    # computed from the expanded effective token sets after the loop.
    if function.count(topk_anchor) != 1:
        raise SystemExit("topk anchor is not unique")
    # qsa_select_paged_tokens also has an early empty-row return.  Instrument
    # only the final return after every TopK/expand chunk has populated out.
    final_return = function.rfind("    return out\n")
    if final_return < 0:
        raise SystemExit("collector-finish: final return anchor is missing")
    function = (
        function[:final_return]
        + "    if overlap_collector is not None:\n"
        + "        overlap_collector.finish(out)\n"
        + function[final_return:]
    )
    qsa.write_text(before + function + after)
    manifest = {
        "qsa_path": str(qsa),
        "helper_path": str(helper_target),
        "before_sha256": sha(backup),
        "patched_sha256": sha(qsa),
        "helper_sha256": sha(helper_target),
        "backup_path": str(backup),
    }
    (artifact / "patch-manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n"
    )
    print(json.dumps(manifest, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
