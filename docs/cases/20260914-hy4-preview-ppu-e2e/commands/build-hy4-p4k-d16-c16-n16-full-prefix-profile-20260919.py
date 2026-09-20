#!/usr/bin/env python3
"""Build a bounded P4K profile that still exercises SQ2048 chunked prefill."""

from __future__ import annotations

from pathlib import Path


CASE_ROOT = Path(
    "/mnt/nfs/users/jinghao/hy4-preview/optimize/"
    "20260914-hy4-preview-ppu-e2e"
)
SOURCE = (
    CASE_ROOT
    / "commands/run-hy4-p4k-d128-c64-n64-full-prefix-reprofile-generated-20260919.sh"
)
DESTINATION = (
    CASE_ROOT
    / "commands/run-hy4-p4k-d16-c16-n16-full-prefix-profile-generated-20260919.sh"
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
        "p4k-d128-c64-n64-full-prefix-reprofile-20260919-09",
        "p4k-d16-c16-n16-full-prefix-hit-profile-20260919-10",
        count=3,
    )
    text = replace_exact(
        text,
        "'milestone_scenario=p4096-d128-c64-n64'",
        "'milestone_scenario=p4096-d16-c16-n16'",
    )
    text = replace_exact(
        text,
        "'workload_delta=output_1024_to_128,concurrency_same_64,requests_128_to_64'",
        "'workload_delta=output_1024_to_16,concurrency_64_to_16,requests_128_to_16'",
    )
    text = replace_exact(
        text,
        "'mode=reprofile_after_full_prefix_sparse_mla_grouping'",
        "'mode=bounded_hit_profile_after_c64_trace_export_failure'",
    )
    text = replace_exact(
        text,
        "'question=verify_full_prefix_grouping_hits_in_real_p4k_chunked_prefill_and_measure_sparse_mla_hotspot_migration'",
        "'question=verify_full_prefix_grouped_kernel_hits_for_real_sq2048_chunked_prefill_with_reduced_trace_pressure'",
    )
    text = replace_exact(text, "--case 4096,128,64,64", "--case 4096,16,16,16")
    text = replace_exact(text, "--runs 2", "--runs 1")
    DESTINATION.write_text(text)
    DESTINATION.chmod(0o755)
    print(DESTINATION)


if __name__ == "__main__":
    main()
