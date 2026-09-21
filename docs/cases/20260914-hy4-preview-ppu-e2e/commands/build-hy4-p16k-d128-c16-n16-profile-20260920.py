#!/usr/bin/env python3
"""Build the P16K phase-decomposition profile from the validated Hy4 recipe."""

from pathlib import Path


CASE_ROOT = Path(
    "/mnt/nfs/users/jinghao/hy4-preview/optimize/"
    "20260914-hy4-preview-ppu-e2e"
)
SOURCE = CASE_ROOT / "commands/run-hy4-p4k-d128-c64-n64-latest-combined-reprofile-generated-20260919.sh"
DESTINATION = CASE_ROOT / "commands/run-hy4-p16k-d128-c16-n16-scenario-entry-02-generated-20260920.sh"


def replace_exact(text: str, old: str, new: str, count: int = 1) -> str:
    actual = text.count(old)
    if actual != count:
        raise AssertionError((old, count, actual))
    return text.replace(old, new)


def main() -> None:
    if not SOURCE.is_file():
        raise FileNotFoundError(SOURCE)
    if DESTINATION.exists():
        raise FileExistsError(DESTINATION)
    text = SOURCE.read_text(encoding="utf-8")
    text = replace_exact(
        text,
        "p4k-d128-c64-n64-latest-combined-reprofile-20260919-13",
        "p16k-d128-c16-n16-scenario-entry-20260920-02",
        count=3,
    )
    text = replace_exact(
        text,
        "expected_sparse_mla_sha=dd51cddf57ab0675e85b39f061bfcc2e9f402e9476c912edcd823ca977dc0d15",
        "expected_sparse_mla_sha=b4c8104653acf593e9b6e3c35ca3376dba4f948b02e55c9493465892b933d73f",
    )
    text = replace_exact(
        text,
        "'parent_scenario=p4096-d1024-c64-n128'",
        "'parent_scenario=p16384-d1024-c64-n128'",
    )
    text = replace_exact(
        text,
        "'milestone_scenario=p4096-d128-c64-n64'",
        "'milestone_scenario=p16384-d128-c16-n16'",
    )
    text = replace_exact(
        text,
        "'workload_delta=output_1024_to_128,concurrency_same_64,requests_128_to_64'",
        "'workload_delta=input_same_16384,output_1024_to_128,concurrency_64_to_16,requests_128_to_16'",
    )
    text = replace_exact(
        text,
        "'mode=reprofile_latest_combined_candidate'",
        "'mode=capture_then_analyze_p16k_scenario_entry'",
    )
    text = replace_exact(
        text,
        "'question=rank_steady_state_prefill_decode_mixed_hotspots_after_indexer_sparse_mla_and_w8a8_moe_optimizations'",
        "'question=separate_p16k_prefill_decode_and_mixed_costs_and_identify_first_falsifiable_optimization'",
    )
    text = replace_exact(
        text,
        "'nearest_no_profiler=/mnt/nfs/users/jinghao/hy4-preview/optimize/20260914-hy4-preview-ppu-e2e/results/performance/20260919-p4k-d1k-c64-n128-current-opt-01/summary.json'",
        "'nearest_no_profiler=/mnt/nfs/users/jinghao/hy4-preview/optimize/20260914-hy4-preview-ppu-e2e/results/performance/20260920-p16k-d1k-c64-n128-scenario-entry-01'",
    )
    text = replace_exact(text, "--case 4096,128,64,64", "--case 16384,128,16,16")
    text = replace_exact(text, "timeout 14600", "timeout 10000")
    DESTINATION.write_text(text, encoding="utf-8")
    DESTINATION.chmod(0o755)
    print(DESTINATION)


if __name__ == "__main__":
    main()
