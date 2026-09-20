#!/usr/bin/env python3
"""Build the narrow SQ320-480 crossover benchmark from the SQ65 sweep."""

from pathlib import Path


CASE_ROOT = Path(
    "/mnt/nfs/users/jinghao/hy4-preview/optimize/"
    "20260914-hy4-preview-ppu-e2e"
)
SOURCE = CASE_ROOT / "commands/benchmark-hy4-sparse-mla-full-prefix-threshold-20260919.py"
DESTINATION = CASE_ROOT / "commands/benchmark-hy4-sparse-mla-full-prefix-threshold384-20260919.py"


def replace_exact(text: str, old: str, new: str, *, count: int = 1) -> str:
    actual = text.count(old)
    assert actual == count, (old, count, actual)
    return text.replace(old, new)


def main() -> None:
    assert SOURCE.is_file(), SOURCE
    assert not DESTINATION.exists(), DESTINATION
    text = SOURCE.read_text()
    text = replace_exact(
        text,
        "for sq in (96, 128, 256, 384, 512):",
        "for sq in (320, 352, 384, 416, 448, 480):",
    )
    text = replace_exact(text, "impl._FULL_PREFIX_MIN_SQ = 65", "impl._FULL_PREFIX_MIN_SQ = 384")
    text = replace_exact(
        text,
        '"candidate": "lower_full_prefix_grouping_threshold_to_sq65"',
        '"candidate": "lower_full_prefix_grouping_threshold_to_sq384"',
    )
    DESTINATION.write_text(text)
    DESTINATION.chmod(0o644)
    print(DESTINATION)


if __name__ == "__main__":
    main()
