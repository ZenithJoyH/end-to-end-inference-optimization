#!/usr/bin/env python3
"""Extend the retained T-Head HQ4 sparse-MLA path through SQ4096."""

from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path


REPO = Path("/workspace/FlagGems-vllm")
SOURCE = REPO / "src/flaggems_vllm/runtime/backend/_thead/fused/flashmla_sparse.py"
TEST = REPO / "tests/test_thead_hy4_ops.py"
CASE = Path(
    "/mnt/nfs/users/jinghao/hy4-preview/optimize/"
    "20260914-hy4-preview-ppu-e2e"
)
PATCH = CASE / "commands/flaggems-vllm-hy4-sparse-mla-sq4096-20260919.patch"
RECORD = CASE / "results/operator/sparse-mla-sq4096-source-apply-20260919-11.json"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: expected one match, found {count}")
    return text.replace(old, new, 1)


def main() -> int:
    before = {"source": sha256(SOURCE), "test": sha256(TEST)}
    source = replace_once(
        SOURCE.read_text(),
        "_HQ4_PREFILL_MAX_SQ = 2048",
        "_HQ4_PREFILL_MAX_SQ = 4096",
        "source max SQ",
    )
    test = TEST.read_text()
    test = replace_once(
        test,
        '@pytest.mark.parametrize("sq", [1, 64, 65, 72, 127, 128, 2048])',
        '@pytest.mark.parametrize(\n'
        '    "sq", [1, 64, 65, 72, 127, 128, 2048, 3072, 4096]\n'
        ')',
        "specialization SQ matrix",
    )
    test = replace_once(
        test,
        '@pytest.mark.parametrize("sq", [384, 512])',
        '@pytest.mark.parametrize("sq", [384, 512, 3072])',
        "graph SQ matrix",
    )
    test = replace_once(
        test,
        "lengths.copy_(torch.arange(1, sq + 1, device=\"cuda\", dtype=torch.int32))",
        "lengths.copy_(\n"
        "        torch.arange(1, sq + 1, device=\"cuda\", dtype=torch.int32).clamp_(\n"
        "            max=2048\n"
        "        )\n"
        "    )",
        "graph capped lengths",
    )
    SOURCE.write_text(source)
    TEST.write_text(test)

    diff = subprocess.check_output(
        [
            "git",
            "-C",
            str(REPO),
            "diff",
            "--binary",
            "--",
            str(SOURCE.relative_to(REPO)),
            str(TEST.relative_to(REPO)),
        ],
        text=True,
    )
    PATCH.write_text(diff)
    after = {"source": sha256(SOURCE), "test": sha256(TEST)}
    RECORD.parent.mkdir(parents=True, exist_ok=True)
    RECORD.write_text(
        json.dumps(
            {
                "status": "applied_pending_validation",
                "repository": str(REPO),
                "branch": subprocess.check_output(
                    ["git", "-C", str(REPO), "branch", "--show-current"],
                    text=True,
                ).strip(),
                "before_sha256": before,
                "after_sha256": after,
                "patch": str(PATCH),
                "change": "extend T-Head HQ4 sparse MLA from SQ2048 through SQ4096",
            },
            indent=2,
            sort_keys=True,
        )
        + "\n"
    )
    print(RECORD.read_text(), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
