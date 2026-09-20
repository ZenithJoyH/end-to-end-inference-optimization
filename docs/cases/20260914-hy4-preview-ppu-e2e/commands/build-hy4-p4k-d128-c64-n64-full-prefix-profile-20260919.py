#!/usr/bin/env python3
"""Build the Hy4 full-prefix sparse-MLA reprofile from the C64 recipe."""

from __future__ import annotations

from pathlib import Path


CASE_ROOT = Path(
    "/mnt/nfs/users/jinghao/hy4-preview/optimize/"
    "20260914-hy4-preview-ppu-e2e"
)
SOURCE = (
    CASE_ROOT
    / "commands/run-hy4-p4k-d128-c64-n64-current-stack-reprofile-generated-20260917.sh"
)
DESTINATION = (
    CASE_ROOT
    / "commands/run-hy4-p4k-d128-c64-n64-full-prefix-reprofile-generated-20260919.sh"
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
        "p4k-d128-c64-n64-current-stack-reprofile-20260917-08",
        "p4k-d128-c64-n64-full-prefix-reprofile-20260919-09",
        count=3,
    )
    text = replace_exact(
        text,
        "expected_plugin_commit=38f350b13fc15f08eb4641e1d6d1980ba3fc16aa",
        "expected_plugin_commit=f7d1aaa9935dd8d613376601504a793b11ee34e0",
    )
    text = replace_exact(
        text,
        "expected_plugin_sha=7e42a416fcf72c091a5dabfcdde11f292bf73b25cf9ca0cd09f5848cc89c845e",
        "expected_plugin_sha=7e65f86944f8720145d1edaa6c35c56072cf37ce55692630d32be5b3631204ed",
    )
    text = replace_exact(
        text,
        "expected_thead_yaml_sha=7566eaddc29f026c131c9083a097bae150a3a975746bed4354f47da1e198b69b",
        "expected_thead_yaml_sha=26786312078a91de20cf34f7830d1bb2de3c662b09fa10b19a212df09c4f595e",
    )
    text = replace_exact(
        text,
        "expected_flaggems_commit=5c2b9a1618c36651f96108d56f076361965f2d53",
        "expected_flaggems_commit=0e02755770011d517c8de591bf91998bbcf30ad1",
    )
    text = replace_exact(
        text,
        "expected_sparse_mla_sha=680eff6be15e259d36036f82958fb383ba1acc781bee1046caa246ae99e4f4fc",
        "flaggems_vllm_repo=/workspace/FlagGems-vllm\n"
        "expected_flaggems_vllm_commit=a26a90258de8bcad0a5d831f38b52f755c6a73b0\n"
        "expected_sparse_mla_sha=a080001e1bc1110ef6327a55659a724a297386e8075d1a3bf58a36a175ecdb67",
    )
    text = replace_exact(
        text,
        "expected_fused_moe_sha=d7a1fbf37fe0ac92d493abdac957b00a4d3f20da865e58d30fcd2bb298a27641",
        "expected_fused_moe_sha=ebf2ec697ee40f62472622604e9af2146b0109346cea32faca022cd5973edfba",
    )
    text = replace_exact(
        text,
        "expected_moe_sum_sha=7419f5d69971ddfb85507e6adb0671d1120334c1f85a11f0ab09872f19b8b8a2",
        "expected_moe_sum_sha=1d56ffe67db83c9fbc21bf73d2df4818d25cd6f44c689e60902fb7386c412651",
    )
    text = replace_exact(
        text,
        'test "$(sha256sum "${flaggems_repo}/src/flag_gems/runtime/backend/_thead/fused/flashmla_sparse.py" | awk \'{print $1}\')" = "${expected_sparse_mla_sha}"',
        'test "$(git -C "${flaggems_vllm_repo}" rev-parse HEAD)" = "${expected_flaggems_vllm_commit}"\n'
        'test "$(sha256sum "${flaggems_vllm_repo}/src/flaggems_vllm/runtime/backend/_thead/fused/flashmla_sparse.py" | awk \'{print $1}\')" = "${expected_sparse_mla_sha}"',
    )
    text = replace_exact(
        text,
        'git -C "${flaggems_repo}" diff --check',
        'git -C "${flaggems_repo}" diff --check\n'
        'git -C "${flaggems_vllm_repo}" diff --check',
    )
    text = replace_exact(
        text,
        'git -C "${flaggems_repo}" status --short --branch >"${service_dir}/flaggems-status.txt"',
        'git -C "${flaggems_repo}" status --short --branch >"${service_dir}/flaggems-status.txt"\n'
        'git -C "${flaggems_vllm_repo}" status --short --branch >"${service_dir}/flaggems-vllm-status.txt"',
    )
    text = replace_exact(
        text,
        "printf 'plugin_sha256=%s\\nsparse_mla_sha256=%s\\nscaled_mm_config_sha256=%s\\nfused_moe_sha256=%s\\nmoe_sum_sha256=%s\\n' \"${expected_plugin_sha}\" \"${expected_sparse_mla_sha}\" \"${expected_scaled_mm_config_sha}\" \"${expected_fused_moe_sha}\" \"${expected_moe_sum_sha}\" >\"${service_dir}/source-identities.txt\"",
        "printf 'plugin_sha256=%s\\nflaggems_vllm_commit=%s\\nsparse_mla_sha256=%s\\nscaled_mm_config_sha256=%s\\nfused_moe_sha256=%s\\nmoe_sum_sha256=%s\\n' \"${expected_plugin_sha}\" \"${expected_flaggems_vllm_commit}\" \"${expected_sparse_mla_sha}\" \"${expected_scaled_mm_config_sha}\" \"${expected_fused_moe_sha}\" \"${expected_moe_sum_sha}\" >\"${service_dir}/source-identities.txt\"",
    )
    text = replace_exact(
        text,
        "'question=measure_post_native_router_hotspot_migration_at_target_concurrency_and_rank_sparse_mla_moe_scaled_mm_communication'",
        "'question=verify_full_prefix_grouping_hits_in_real_p4k_chunked_prefill_and_measure_sparse_mla_hotspot_migration'",
    )
    text = replace_exact(
        text,
        "'mode=reprofile'",
        "'mode=reprofile_after_full_prefix_sparse_mla_grouping'",
    )
    text = replace_exact(
        text,
        '"${expected_flaggems_commit}" "${expected_sparse_mla_sha}" "${profiler_config}" >"${service_dir}/launch-result.txt"',
        '"${expected_flaggems_commit}" "${expected_sparse_mla_sha}" "${profiler_config}" >"${service_dir}/launch-result.txt"\n'
        'printf \'flaggems_vllm_commit=%s\\n\' "${expected_flaggems_vllm_commit}" >>"${service_dir}/launch-result.txt"',
    )
    DESTINATION.write_text(text)
    DESTINATION.chmod(0o755)
    print(DESTINATION)


if __name__ == "__main__":
    main()
