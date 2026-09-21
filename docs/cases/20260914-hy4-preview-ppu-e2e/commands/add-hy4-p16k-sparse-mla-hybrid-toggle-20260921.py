#!/usr/bin/env python3
"""Add a process-stable default-on A/B toggle for the P16K hybrid."""

from __future__ import annotations

import difflib
import hashlib
import json
from pathlib import Path


REPO = Path("/workspace/vllm-plugin-FL")
SOURCE = REPO / "vllm_fl/dispatch/backends/flaggems/impl/mla_sparse.py"
TEST = REPO / "tests/unit_tests/dispatch/test_flaggems_mla_sparse.py"
CASE = Path(
    "/mnt/nfs/users/jinghao/hy4-preview/optimize/"
    "20260914-hy4-preview-ppu-e2e"
)
PATCH = CASE / "commands/plugin-hy4-p16k-cached-prefill-hybrid-toggle-20260921.patch"
RECORD = CASE / "results/operator/p16k-cached-prefill-hybrid-toggle-apply-20260921-01.json"
EXPECTED = {
    SOURCE: "7810fb520ab14f4f7c12fadc33d5a32524bc39973bde7c65454fa65cd3dba786",
    TEST: "0c58f8b986a84307985e350eca4360d25d054c9fb411f962ee8e187d28a4478a",
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: expected one match, found {count}")
    return text.replace(old, new, 1)


def main() -> int:
    if PATCH.exists() or RECORD.exists():
        raise RuntimeError("output already exists")
    actual = {path: sha256(path) for path in EXPECTED}
    if actual != EXPECTED:
        raise RuntimeError(f"source identity mismatch: {actual}")
    before_source = SOURCE.read_text()
    before_test = TEST.read_text()
    source = replace_once(
        before_source,
        "from typing import TYPE_CHECKING, ClassVar\n",
        "import os\nfrom functools import lru_cache\nfrom typing import TYPE_CHECKING, ClassVar\n",
        "toggle imports",
    )
    source = replace_once(
        source,
        "\ndef _should_use_thead_cached_prefill_hybrid(q, attn_metadata) -> bool:\n",
        '''
@lru_cache(maxsize=1)
def _thead_cached_prefill_hybrid_enabled() -> bool:
    return os.environ.get(
        "VLLM_FL_THEAD_CACHED_PREFILL_SPARSE_MLA_HYBRID", "1"
    ).lower() in ("1", "true", "yes")


def _should_use_thead_cached_prefill_hybrid(q, attn_metadata) -> bool:
''',
        "toggle helper",
    )
    source = replace_once(
        source,
        '''    return (
        getattr(current_platform, "vendor_name", None) == "thead"
''',
        '''    return (
        _thead_cached_prefill_hybrid_enabled()
        and getattr(current_platform, "vendor_name", None) == "thead"
''',
        "toggle guard",
    )
    test = before_test.rstrip() + r'''


def test_thead_cached_prefill_hybrid_default_on_toggle(monkeypatch):
    monkeypatch.delenv(
        "VLLM_FL_THEAD_CACHED_PREFILL_SPARSE_MLA_HYBRID", raising=False
    )
    mla_sparse._thead_cached_prefill_hybrid_enabled.cache_clear()
    assert mla_sparse._thead_cached_prefill_hybrid_enabled()
    monkeypatch.setenv(
        "VLLM_FL_THEAD_CACHED_PREFILL_SPARSE_MLA_HYBRID", "0"
    )
    mla_sparse._thead_cached_prefill_hybrid_enabled.cache_clear()
    assert not mla_sparse._thead_cached_prefill_hybrid_enabled()
    mla_sparse._thead_cached_prefill_hybrid_enabled.cache_clear()
'''
    SOURCE.write_text(source)
    TEST.write_text(test)
    relative_source = str(SOURCE.relative_to(REPO))
    relative_test = str(TEST.relative_to(REPO))
    diff = "".join(
        difflib.unified_diff(
            before_source.splitlines(keepends=True),
            source.splitlines(keepends=True),
            fromfile=f"a/{relative_source}",
            tofile=f"b/{relative_source}",
        )
    )
    diff += "".join(
        difflib.unified_diff(
            before_test.splitlines(keepends=True),
            test.splitlines(keepends=True),
            fromfile=f"a/{relative_test}",
            tofile=f"b/{relative_test}",
        )
    )
    PATCH.write_text(diff)
    RECORD.parent.mkdir(parents=True, exist_ok=True)
    result = {
        "status": "applied_pending_validation",
        "env": "VLLM_FL_THEAD_CACHED_PREFILL_SPARSE_MLA_HYBRID",
        "default": "1",
        "before_sha256": {str(path): actual[path] for path in EXPECTED},
        "after_sha256": {str(path): sha256(path) for path in EXPECTED},
        "patch": str(PATCH),
    }
    RECORD.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(RECORD.read_text(), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
