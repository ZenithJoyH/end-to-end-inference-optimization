#!/usr/bin/env python3
"""Apply the temporary op-021 capture hook with exact source guards."""

import argparse
import hashlib
import json
import os
import shutil
from pathlib import Path


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{label}: expected one anchor, got {count}")
    return text.replace(old, new, 1)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--qsa", required=True, type=Path)
    parser.add_argument("--helper", required=True, type=Path)
    parser.add_argument("--artifact-dir", required=True, type=Path)
    parser.add_argument("--expected-sha256", required=True)
    args = parser.parse_args()
    qsa = args.qsa.resolve()
    helper_source = args.helper.resolve()
    artifact = args.artifact_dir.resolve()
    helper_target = qsa.with_name("qsa_producer_fixture_capture.py")
    if artifact.exists() or helper_target.exists():
        raise SystemExit("artifact directory or helper target already exists")
    if sha(qsa) != args.expected_sha256:
        raise SystemExit("qsa.py SHA mismatch; refusing to patch unknown source")

    text = qsa.read_text(encoding="utf-8")
    text = replace_once(
        text,
        "import torch\n",
        "import torch\n\nfrom .qsa_producer_fixture_capture import (\n"
        "    qsa_producer_fixture_capture_begin,\n)\n",
        "import",
    )
    start = text.index("def qsa_select_paged_tokens(")
    end = text.find("\ndef ", start + 1)
    if end < 0:
        end = len(text)
    before, function, after = text[:start], text[start:end], text[end:]
    required = ("q", "k_cache", "page_table", "token_to_req", "query_positions",
                "sequence_lengths", "token_topk", "compress_ratio", "static_score_columns")
    signature = function.split(") ->", 1)[0]
    missing = [name for name in required if name not in signature]
    if missing:
        raise SystemExit(f"producer ABI mismatch; missing {missing}")
    begin_anchor = "    if not rows:\n        return out\n"
    function = replace_once(
        function,
        begin_anchor,
        "    fixture_collector = qsa_producer_fixture_capture_begin(\n"
        "        q, k_cache, page_table, token_to_req, query_positions,\n"
        "        sequence_lengths, token_topk, compress_ratio, static_score_columns,\n"
        "    )\n"
        + begin_anchor,
        "collector-begin",
    )
    final_return = function.rfind("    return out\n")
    if final_return < 0:
        raise SystemExit("final return anchor is absent")
    function = (
        function[:final_return]
        + "    if fixture_collector is not None:\n"
        + "        fixture_collector.finish(out)\n"
        + function[final_return:]
    )
    patched = before + function + after

    artifact.mkdir(parents=True)
    backup = artifact / "qsa.py.before"
    shutil.copy2(qsa, backup)
    temporary = qsa.with_name(f".{qsa.name}.op021.tmp.pid{os.getpid()}")
    temporary.write_text(patched, encoding="utf-8")
    manifest = {
        "qsa_path": str(qsa),
        "helper_path": str(helper_target),
        "backup_path": str(backup),
        "before_sha256": sha(backup),
        "patched_sha256": sha(temporary),
        "helper_sha256": sha(helper_source),
        "prepare_script_sha256": sha(Path(__file__).resolve()),
    }
    path = artifact / "patch-manifest.json"
    path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    # The rollback manifest is durable before either live path changes.  The
    # exact-state revert supports both intermediate states if this process is
    # interrupted between the two atomic replacements.
    helper_temporary = helper_target.with_name(
        f".{helper_target.name}.op021.tmp.pid{os.getpid()}"
    )
    shutil.copy2(helper_source, helper_temporary)
    os.replace(helper_temporary, helper_target)
    os.replace(temporary, qsa)
    if sha(qsa) != manifest["patched_sha256"] or sha(helper_target) != manifest["helper_sha256"]:
        raise SystemExit("post-apply source SHA mismatch")
    print(json.dumps(manifest, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
