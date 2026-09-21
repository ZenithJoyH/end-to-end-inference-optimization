#!/usr/bin/env python3
"""Add one-time runtime hit evidence for the cached-prefill hybrid."""

from __future__ import annotations

import difflib
import hashlib
import json
from pathlib import Path


REPO = Path("/workspace/vllm-plugin-FL")
SOURCE = REPO / "vllm_fl/dispatch/backends/flaggems/impl/mla_sparse.py"
CASE = Path(
    "/mnt/nfs/users/jinghao/hy4-preview/optimize/"
    "20260914-hy4-preview-ppu-e2e"
)
PATCH = CASE / "commands/plugin-hy4-p16k-cached-prefill-hybrid-hit-log-20260921.patch"
RECORD = CASE / "results/operator/p16k-cached-prefill-hybrid-hit-log-apply-20260921-01.json"
EXPECTED = "e317d87b8f23956a6bc3d8af4bee4a40eba74e355195634e3e35cc134aa231c2"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    if PATCH.exists() or RECORD.exists():
        raise RuntimeError("output already exists")
    if digest(SOURCE) != EXPECTED:
        raise RuntimeError(f"source identity mismatch: {digest(SOURCE)}")
    before = SOURCE.read_text()
    anchor = '''        topk_indices, topk_length = triton_convert_req_index_to_global_index(
'''
    replacement = '''        logger.info_once(
            "Using T-Head cached-prefill native/grouped sparse MLA hybrid."
        )
        topk_indices, topk_length = triton_convert_req_index_to_global_index(
'''
    if before.count(anchor) != 1:
        raise RuntimeError(f"expected one anchor, found {before.count(anchor)}")
    after = before.replace(anchor, replacement, 1)
    SOURCE.write_text(after)
    relative = str(SOURCE.relative_to(REPO))
    PATCH.write_text(
        "".join(
            difflib.unified_diff(
                before.splitlines(keepends=True),
                after.splitlines(keepends=True),
                fromfile=f"a/{relative}",
                tofile=f"b/{relative}",
            )
        )
    )
    RECORD.parent.mkdir(parents=True, exist_ok=True)
    RECORD.write_text(
        json.dumps(
            {
                "status": "applied_pending_service_hit",
                "before_sha256": EXPECTED,
                "after_sha256": digest(SOURCE),
                "patch": str(PATCH),
                "message": "Using T-Head cached-prefill native/grouped sparse MLA hybrid.",
            },
            indent=2,
        )
        + "\n"
    )
    print(RECORD.read_text(), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
