#!/usr/bin/env python3
"""Build a comparable P4K/C64 reprofile for the latest combined Hy4 candidate."""

from pathlib import Path


CASE_ROOT = Path(
    "/mnt/nfs/users/jinghao/hy4-preview/optimize/"
    "20260914-hy4-preview-ppu-e2e"
)
SOURCE = CASE_ROOT / "commands/run-hy4-p4k-d128-c64-n64-full-prefix-reprofile-generated-20260919.sh"
DESTINATION = CASE_ROOT / "commands/run-hy4-p4k-d128-c64-n64-latest-combined-reprofile-generated-20260919.sh"


def replace_exact(text: str, old: str, new: str, count: int = 1) -> str:
    actual = text.count(old)
    assert actual == count, (old, count, actual)
    return text.replace(old, new)


def main() -> None:
    assert SOURCE.is_file(), SOURCE
    assert not DESTINATION.exists(), DESTINATION
    text = SOURCE.read_text(encoding="utf-8")
    text = replace_exact(
        text,
        "p4k-d128-c64-n64-full-prefix-reprofile-20260919-09",
        "p4k-d128-c64-n64-latest-combined-reprofile-20260919-13",
        count=3,
    )
    text = replace_exact(
        text,
        "expected_plugin_sha=7e65f86944f8720145d1edaa6c35c56072cf37ce55692630d32be5b3631204ed",
        "expected_plugin_sha=e4f9d10105a398480aff14e7302da9f0376a01a3ebd620a31cb7eab0f7907822\n"
        "expected_indexer_vendor_sha=c9e2df80e774f3829fc088dbace607a10442d9b79a88c3aeb00e95eafc6a3ba9",
    )
    text = replace_exact(
        text,
        "expected_sparse_mla_sha=a080001e1bc1110ef6327a55659a724a297386e8075d1a3bf58a36a175ecdb67",
        "expected_sparse_mla_sha=dd51cddf57ab0675e85b39f061bfcc2e9f402e9476c912edcd823ca977dc0d15\n"
        "expected_flaggems_vllm_fused_moe_sha=d8e6ab2c703ddcb1e1c34f9569110363a38cc791d3876133ad51d54056717f3f",
    )
    text = replace_exact(
        text,
        'test "$(sha256sum "${plugin_repo}/vllm_fl/models/hy_v4.py" | awk \'{print $1}\')" = "${expected_plugin_sha}"',
        'test "$(sha256sum "${plugin_repo}/vllm_fl/models/hy_v4.py" | awk \'{print $1}\')" = "${expected_plugin_sha}"\n'
        'test "$(sha256sum "${plugin_repo}/vllm_fl/dispatch/backends/vendor/thead/impl/hyv4_indexer.py" | awk \'{print $1}\')" = "${expected_indexer_vendor_sha}"',
    )
    text = replace_exact(
        text,
        'test "$(sha256sum "${flaggems_vllm_repo}/src/flaggems_vllm/runtime/backend/_thead/fused/flashmla_sparse.py" | awk \'{print $1}\')" = "${expected_sparse_mla_sha}"',
        'test "$(sha256sum "${flaggems_vllm_repo}/src/flaggems_vllm/runtime/backend/_thead/fused/flashmla_sparse.py" | awk \'{print $1}\')" = "${expected_sparse_mla_sha}"\n'
        'test "$(sha256sum "${flaggems_vllm_repo}/src/flaggems_vllm/runtime/backend/_thead/ops/fused_moe.py" | awk \'{print $1}\')" = "${expected_flaggems_vllm_fused_moe_sha}"',
    )
    text = replace_exact(
        text,
        "printf 'plugin_sha256=%s\\nflaggems_vllm_commit=%s\\nsparse_mla_sha256=%s\\nscaled_mm_config_sha256=%s\\nfused_moe_sha256=%s\\nmoe_sum_sha256=%s\\n' \"${expected_plugin_sha}\" \"${expected_flaggems_vllm_commit}\" \"${expected_sparse_mla_sha}\" \"${expected_scaled_mm_config_sha}\" \"${expected_fused_moe_sha}\" \"${expected_moe_sum_sha}\" >\"${service_dir}/source-identities.txt\"",
        "printf 'plugin_sha256=%s\\nindexer_vendor_sha256=%s\\nflaggems_vllm_commit=%s\\nsparse_mla_sha256=%s\\nflaggems_vllm_fused_moe_sha256=%s\\nscaled_mm_config_sha256=%s\\nlegacy_flaggems_fused_moe_sha256=%s\\nmoe_sum_sha256=%s\\n' \"${expected_plugin_sha}\" \"${expected_indexer_vendor_sha}\" \"${expected_flaggems_vllm_commit}\" \"${expected_sparse_mla_sha}\" \"${expected_flaggems_vllm_fused_moe_sha}\" \"${expected_scaled_mm_config_sha}\" \"${expected_fused_moe_sha}\" \"${expected_moe_sum_sha}\" >\"${service_dir}/source-identities.txt\"",
    )
    text = replace_exact(
        text,
        "'mode=reprofile_after_full_prefix_sparse_mla_grouping'",
        "'mode=reprofile_latest_combined_candidate'",
    )
    text = replace_exact(
        text,
        "'question=verify_full_prefix_grouping_hits_in_real_p4k_chunked_prefill_and_measure_sparse_mla_hotspot_migration'",
        "'question=rank_steady_state_prefill_decode_mixed_hotspots_after_indexer_sparse_mla_and_w8a8_moe_optimizations'",
    )
    text = replace_exact(
        text,
        "'nearest_no_profiler=/mnt/nfs/users/jinghao/hy4-preview/test/benchmark_results/hy4/hy4_4096in_1024out_c64_n128_20260917_132531.csv'",
        "'nearest_no_profiler=/mnt/nfs/users/jinghao/hy4-preview/optimize/20260914-hy4-preview-ppu-e2e/results/performance/20260919-p4k-d1k-c64-n128-current-opt-01/summary.json'",
    )
    DESTINATION.write_text(text, encoding="utf-8")
    DESTINATION.chmod(0o755)
    print(DESTINATION)


if __name__ == "__main__":
    main()
