#!/usr/bin/env python3
"""Build a bounded runtime-hit profile for the new HY4 Indexer body code."""

from pathlib import Path


CASE_ROOT = Path(
    "/mnt/nfs/users/jinghao/hy4-preview/optimize/"
    "20260914-hy4-preview-ppu-e2e"
)
SOURCE = CASE_ROOT / "commands/run-hy4-p4k-d16-c16-n16-full-prefix-profile-rerun-generated-20260919.sh"
DESTINATION = CASE_ROOT / "commands/run-hy4-p4k-d16-c16-n16-indexer-body-reprofile-generated-20260919.sh"


def replace_all(text: str, old: str, new: str, *, minimum: int = 1) -> str:
    actual = text.count(old)
    assert actual >= minimum, (old, minimum, actual)
    return text.replace(old, new)


def main() -> None:
    assert SOURCE.is_file(), SOURCE
    assert not DESTINATION.exists(), DESTINATION
    text = SOURCE.read_text()
    text = replace_all(
        text,
        "p4k-d16-c16-n16-full-prefix-hit-profile-20260919-11",
        "p4k-d16-c16-n16-indexer-body-reprofile-20260919-12",
        minimum=3,
    )
    text = replace_all(
        text,
        "expected_plugin_sha=7e65f86944f8720145d1edaa6c35c56072cf37ce55692630d32be5b3631204ed",
        "expected_plugin_sha=55251044f881615ba92119e59bb969841b2d384f1fed3b3ab3da3908a15a3235",
    )
    text = replace_all(
        text,
        "expected_sparse_mla_sha=a080001e1bc1110ef6327a55659a724a297386e8075d1a3bf58a36a175ecdb67",
        "expected_sparse_mla_sha=dd51cddf57ab0675e85b39f061bfcc2e9f402e9476c912edcd823ca977dc0d15",
    )
    plugin_sha_line = (
        "expected_plugin_sha=55251044f881615ba92119e59bb969841b2d384f1fed3b3ab3da3908a15a3235\n"
    )
    text = replace_all(
        text,
        plugin_sha_line,
        plugin_sha_line
        + "expected_plugin_hyv4_indexer_sha="
        + "c9e2df80e774f3829fc088dbace607a10442d9b79a88c3aeb00e95eafc6a3ba9\n",
    )
    plugin_check = (
        'test "$(sha256sum "${plugin_repo}/vllm_fl/models/hy_v4.py" '
        '| awk \'{print $1}\')" = "${expected_plugin_sha}"\n'
    )
    text = replace_all(
        text,
        plugin_check,
        plugin_check
        + 'test "$(sha256sum "${plugin_repo}/vllm_fl/dispatch/backends/vendor/'
        + 'thead/impl/hyv4_indexer.py" | awk \'{print $1}\')" = '
        + '"${expected_plugin_hyv4_indexer_sha}"\n',
    )
    text = replace_all(
        text,
        "mode=bounded_hit_profile_after_c64_trace_export_failure",
        "mode=bounded_runtime_hit_profile_after_indexer_body_optimization",
    )
    text = replace_all(
        text,
        "question=verify_full_prefix_grouped_kernel_hits_for_real_sq2048_chunked_prefill_with_reduced_trace_pressure",
        "question=verify_indexer_translation_pointwise_and_direct_paged_gather_runtime_hit_and_hotspot_reduction",
    )
    DESTINATION.write_text(text)
    DESTINATION.chmod(0o755)
    print(DESTINATION)


if __name__ == "__main__":
    main()
