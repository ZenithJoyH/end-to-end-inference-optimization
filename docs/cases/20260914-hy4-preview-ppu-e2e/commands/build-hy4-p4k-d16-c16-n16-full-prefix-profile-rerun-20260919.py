#!/usr/bin/env python3
"""Correct the bounded P4K hit profile to one warmup plus one measured run."""

from __future__ import annotations

from pathlib import Path


CASE_ROOT = Path(
    "/mnt/nfs/users/jinghao/hy4-preview/optimize/"
    "20260914-hy4-preview-ppu-e2e"
)
SOURCE = (
    CASE_ROOT
    / "commands/run-hy4-p4k-d16-c16-n16-full-prefix-profile-generated-20260919.sh"
)
DESTINATION = (
    CASE_ROOT
    / "commands/run-hy4-p4k-d16-c16-n16-full-prefix-profile-rerun-generated-20260919.sh"
)


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
        "p4k-d16-c16-n16-full-prefix-hit-profile-20260919-10",
        "p4k-d16-c16-n16-full-prefix-hit-profile-20260919-11",
        count=3,
    )
    text = replace_exact(text, "--runs 1", "--runs 2")
    DESTINATION.write_text(text)
    DESTINATION.chmod(0o755)
    print(DESTINATION)


if __name__ == "__main__":
    main()
