#!/usr/bin/env python3
"""Build the larger Hy4 profiling command from the validated C16 recipe."""

from __future__ import annotations

from pathlib import Path


CASE_ROOT = Path(
    "/mnt/nfs/users/jinghao/hy4-preview/optimize/"
    "20260914-hy4-preview-ppu-e2e"
)
SOURCE = CASE_ROOT / "commands/run-hy4-p4k-d64-c16-full-range-reprofile-20260916.sh"
DESTINATION = (
    CASE_ROOT
    / "commands/run-hy4-p4k-d128-c32-n32-scaled-mm-reprofile-generated-20260916.sh"
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
        "p4k-d64-c16-n16-full-range-reprofile-20260916-05",
        "p4k-d128-c32-n32-scaled-mm-reprofile-20260916-07",
    )
    text = replace_exact(
        text,
        "hy4-p4k-d64-c16-full-range-reprofile-20260916-05",
        "hy4-p4k-d128-c32-n32-scaled-mm-reprofile-20260916-07",
        count=2,
    )
    text = replace_exact(
        text,
        "expected_plugin_sha=bc567ade22696146200042e8e29745535c86fa2dc9479051c2d2f7892ed3c9f3",
        "expected_plugin_sha=7c1843727800a6e1bc5252c28aaf33f0801da672442aa4ad145c7ce613ec6ea2",
    )
    text = replace_exact(
        text,
        "expected_sparse_mla_sha=680eff6be15e259d36036f82958fb383ba1acc781bee1046caa246ae99e4f4fc",
        "expected_sparse_mla_sha=680eff6be15e259d36036f82958fb383ba1acc781bee1046caa246ae99e4f4fc\n"
        "expected_scaled_mm_config_sha=2b44781bbbb28f76f20f522ae8a52067c595cf7bfdd48ee02d92516eed65e220",
    )
    text = replace_exact(
        text,
        'test "$(sha256sum "${flaggems_repo}/src/flag_gems/runtime/backend/_thead/fused/flashmla_sparse.py" | awk \'{print $1}\')" = "${expected_sparse_mla_sha}"',
        'test "$(sha256sum "${flaggems_repo}/src/flag_gems/runtime/backend/_thead/fused/flashmla_sparse.py" | awk \'{print $1}\')" = "${expected_sparse_mla_sha}"\n'
        'test "$(sha256sum "${flaggems_repo}/src/flag_gems/runtime/backend/_thead/tune_configs.yaml" | awk \'{print $1}\')" = "${expected_scaled_mm_config_sha}"',
    )
    text = replace_exact(
        text,
        'git -C "${flaggems_repo}" status --short --branch >"${service_dir}/flaggems-status.txt"',
        'git -C "${flaggems_repo}" status --short --branch >"${service_dir}/flaggems-status.txt"\n'
        'printf \'plugin_sha256=%s\\nsparse_mla_sha256=%s\\nscaled_mm_config_sha256=%s\\n\' "${expected_plugin_sha}" "${expected_sparse_mla_sha}" "${expected_scaled_mm_config_sha}" >"${service_dir}/source-identities.txt"',
    )
    text = replace_exact(
        text,
        "'milestone_scenario=p4096-d64-c16-n16'",
        "'milestone_scenario=p4096-d128-c32-n32'",
    )
    text = replace_exact(
        text,
        "'workload_delta=output_1024_to_64,concurrency_64_to_16,requests_128_to_16'",
        "'workload_delta=output_1024_to_128,concurrency_64_to_32,requests_128_to_32'",
    )
    text = replace_exact(
        text,
        "'phase_boundary=execute_new_cached_markers'",
        "'phase_boundary=execute_new_cached_markers_with_chunked_prefill_continuation_caveat'",
    )
    text = replace_exact(
        text,
        "'question=verify_full_range_bypass_removes_prefill_indexer_qk_topk_and_preserves_copy_sync_elimination'",
        "'question=measure_hotspot_migration_at_higher_concurrency_and_verify_scaled_mm_tile_hits'",
    )
    text = replace_exact(
        text,
        "hy4_4096in_1024out_c64_n128_20260916_082820.csv",
        "hy4_4096in_1024out_c64_n128_20260916_155355.csv",
    )
    text = replace_exact(text, "VLLM_EXECUTE_MODEL_TIMEOUT_SECONDS=1800", "VLLM_EXECUTE_MODEL_TIMEOUT_SECONDS=3600")
    text = replace_exact(text, "--case 4096,64,16,16", "--case 4096,128,32,32")
    text = replace_exact(text, "--timeout 1800", "--timeout 3600")
    text = replace_exact(text, "timeout 3700", "timeout 7400")
    DESTINATION.write_text(text)
    DESTINATION.chmod(0o755)
    print(DESTINATION)


if __name__ == "__main__":
    main()
