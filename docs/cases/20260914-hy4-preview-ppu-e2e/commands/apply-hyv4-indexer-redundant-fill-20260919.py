#!/usr/bin/env python3
"""Remove a redundant per-block fill after verifying provider overwrite."""

from pathlib import Path


REPO = Path("/workspace/vllm-plugin-FL")
SOURCE = REPO / "vllm_fl/models/hy_v4.py"
TEST = REPO / "tests/unit_tests/models/test_hy_v4.py"


def replace_once(path: Path, old: str, new: str) -> None:
    text = path.read_text()
    assert text.count(old) == 1, (path, text.count(old))
    path.write_text(text.replace(old, new))


def main() -> None:
    replace_once(
        SOURCE,
        "    Rows are kept within one request by the caller. Batching the QK matmul,\n"
        "    weighted reduction and Top-K avoids launching the complete eager operator\n"
        "    sequence once per query token while preserving the per-row causal range.\n"
        "    \"\"\"\n"
        "    output.fill_(-1)\n"
        "    if q.shape[0] == 0 or key_end <= key_start or topk <= 0:\n",
        "    Rows are kept within one request by the caller. Batching the QK matmul,\n"
        "    weighted reduction and Top-K avoids launching the complete eager operator\n"
        "    sequence once per query token while preserving the per-row causal range.\n"
        "\n"
        "    The Indexer initializes the complete output buffer once before processing\n"
        "    chunks. The row-wise provider overwrites this block, including invalid\n"
        "    entries, so another full-block fill here is redundant.\n"
        "    \"\"\"\n"
        "    if q.shape[0] == 0 or key_end <= key_start or topk <= 0:\n",
    )
    replace_once(
        TEST,
        "    output = torch.empty((5, topk), dtype=torch.int32)\n\n"
        "    hy_v4._select_topk_block(\n",
        "    # The production Indexer initializes the complete output buffer once.\n"
        "    output = torch.full((5, topk), -1, dtype=torch.int32)\n\n"
        "    hy_v4._select_topk_block(\n",
    )
    print(SOURCE)
    print(TEST)


if __name__ == "__main__":
    main()
