#!/usr/bin/env python3
"""Build recovery for the valid bounded full-prefix profiling traces."""

from pathlib import Path


CASE_ROOT = Path(
    "/mnt/nfs/users/jinghao/hy4-preview/optimize/"
    "20260914-hy4-preview-ppu-e2e"
)
SOURCE = CASE_ROOT / "commands/recover-hy4-p4k-d128-c64-n64-full-prefix-profile-stop-20260919.sh"
DESTINATION = CASE_ROOT / "commands/recover-hy4-p4k-d16-c16-n16-full-prefix-profile-stop-20260919.sh"


def main() -> None:
    assert SOURCE.is_file(), SOURCE
    assert not DESTINATION.exists(), DESTINATION
    text = SOURCE.read_text()
    old = "p4k-d128-c64-n64-full-prefix-reprofile-20260919-09"
    new = "p4k-d16-c16-n16-full-prefix-hit-profile-20260919-11"
    assert text.count(old) == 3, text.count(old)
    text = text.replace(old, new)
    old_gzip = "| sort -z | xargs -0 gzip -t"
    assert text.count(old_gzip) == 1, text.count(old_gzip)
    text = text.replace(old_gzip, "| sort -z | xargs -0 -n1 -P16 gzip -t")
    DESTINATION.write_text(text)
    DESTINATION.chmod(0o755)
    print(DESTINATION)


if __name__ == "__main__":
    main()
