#!/usr/bin/env python3
"""Build exact-process recovery for the Indexer-body reprofile."""

from pathlib import Path


CASE_ROOT = Path(
    "/mnt/nfs/users/jinghao/hy4-preview/optimize/"
    "20260914-hy4-preview-ppu-e2e"
)
SOURCE = CASE_ROOT / "commands/recover-hy4-p4k-d16-c16-n16-full-prefix-profile-stop-20260919.sh"
DESTINATION = CASE_ROOT / "commands/recover-hy4-p4k-d16-c16-n16-indexer-body-profile-stop-20260919.sh"


def main() -> None:
    assert SOURCE.is_file(), SOURCE
    assert not DESTINATION.exists(), DESTINATION
    text = SOURCE.read_text()
    old = "p4k-d16-c16-n16-full-prefix-hit-profile-20260919-11"
    new = "p4k-d16-c16-n16-indexer-body-reprofile-20260919-12"
    assert text.count(old) == 3, text.count(old)
    DESTINATION.write_text(text.replace(old, new))
    DESTINATION.chmod(0o755)
    print(DESTINATION)


if __name__ == "__main__":
    main()
