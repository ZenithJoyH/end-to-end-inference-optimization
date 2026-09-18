#!/usr/bin/env python3
"""Build the C64 Hy4 current-stack reprofile from the validated C32 recipe."""

from __future__ import annotations

from pathlib import Path


CASE_ROOT = Path(
    "/mnt/nfs/users/jinghao/hy4-preview/optimize/"
    "20260914-hy4-preview-ppu-e2e"
)
SOURCE = (
    CASE_ROOT
    / "commands/run-hy4-p4k-d128-c32-n32-scaled-mm-reprofile-generated-20260916.sh"
)
DESTINATION = (
    CASE_ROOT
    / "commands/run-hy4-p4k-d128-c64-n64-current-stack-reprofile-generated-20260917.sh"
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
        "p4k-d128-c32-n32-scaled-mm-reprofile-20260916-07",
        "p4k-d128-c64-n64-current-stack-reprofile-20260917-08",
        count=3,
    )
    text = replace_exact(
        text,
        "expected_plugin_sha=7c1843727800a6e1bc5252c28aaf33f0801da672442aa4ad145c7ce613ec6ea2",
        "expected_plugin_sha=7e42a416fcf72c091a5dabfcdde11f292bf73b25cf9ca0cd09f5848cc89c845e",
    )
    text = replace_exact(
        text,
        "expected_scaled_mm_config_sha=2b44781bbbb28f76f20f522ae8a52067c595cf7bfdd48ee02d92516eed65e220",
        "expected_scaled_mm_config_sha=2b44781bbbb28f76f20f522ae8a52067c595cf7bfdd48ee02d92516eed65e220\n"
        "expected_fused_moe_sha=d7a1fbf37fe0ac92d493abdac957b00a4d3f20da865e58d30fcd2bb298a27641\n"
        "expected_moe_sum_sha=7419f5d69971ddfb85507e6adb0671d1120334c1f85a11f0ab09872f19b8b8a2",
    )
    text = replace_exact(
        text,
        'test "$(sha256sum "${flaggems_repo}/src/flag_gems/runtime/backend/_thead/tune_configs.yaml" | awk \'{print $1}\')" = "${expected_scaled_mm_config_sha}"',
        'test "$(sha256sum "${flaggems_repo}/src/flag_gems/runtime/backend/_thead/tune_configs.yaml" | awk \'{print $1}\')" = "${expected_scaled_mm_config_sha}"\n'
        'test "$(sha256sum "${flaggems_repo}/src/flag_gems/fused/fused_moe.py" | awk \'{print $1}\')" = "${expected_fused_moe_sha}"\n'
        'test "$(sha256sum "${flaggems_repo}/src/flag_gems/fused/moe_sum.py" | awk \'{print $1}\')" = "${expected_moe_sum_sha}"',
    )
    text = replace_exact(
        text,
        "printf 'plugin_sha256=%s\\nsparse_mla_sha256=%s\\nscaled_mm_config_sha256=%s\\n' \"${expected_plugin_sha}\" \"${expected_sparse_mla_sha}\" \"${expected_scaled_mm_config_sha}\" >\"${service_dir}/source-identities.txt\"",
        "printf 'plugin_sha256=%s\\nsparse_mla_sha256=%s\\nscaled_mm_config_sha256=%s\\nfused_moe_sha256=%s\\nmoe_sum_sha256=%s\\n' \"${expected_plugin_sha}\" \"${expected_sparse_mla_sha}\" \"${expected_scaled_mm_config_sha}\" \"${expected_fused_moe_sha}\" \"${expected_moe_sum_sha}\" >\"${service_dir}/source-identities.txt\"",
    )
    text = replace_exact(
        text,
        "'milestone_scenario=p4096-d128-c32-n32'",
        "'milestone_scenario=p4096-d128-c64-n64'",
    )
    text = replace_exact(
        text,
        "'workload_delta=output_1024_to_128,concurrency_64_to_32,requests_128_to_32'",
        "'workload_delta=output_1024_to_128,concurrency_same_64,requests_128_to_64'",
    )
    text = replace_exact(
        text,
        "'question=measure_hotspot_migration_at_higher_concurrency_and_verify_scaled_mm_tile_hits'",
        "'question=measure_post_native_router_hotspot_migration_at_target_concurrency_and_rank_sparse_mla_moe_scaled_mm_communication'",
    )
    text = replace_exact(
        text,
        "hy4_4096in_1024out_c64_n128_20260916_155355.csv",
        "hy4_4096in_1024out_c64_n128_20260917_132531.csv",
    )
    text = replace_exact(text, "VLLM_EXECUTE_MODEL_TIMEOUT_SECONDS=3600", "VLLM_EXECUTE_MODEL_TIMEOUT_SECONDS=7200")
    text = replace_exact(text, "--case 4096,128,32,32", "--case 4096,128,64,64")
    text = replace_exact(text, "--timeout 3600", "--timeout 7200")
    text = replace_exact(text, "timeout 7400", "timeout 14600")
    DESTINATION.write_text(text)
    DESTINATION.chmod(0o755)
    print(DESTINATION)


if __name__ == "__main__":
    main()
