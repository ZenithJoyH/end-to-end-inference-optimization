#!/usr/bin/env python3
"""Derive the P16K cached-prefill hybrid A/B/revert runner from a frozen runner."""

from pathlib import Path


CASE_ROOT = Path(
    "/mnt/nfs/users/jinghao/hy4-preview/optimize/"
    "20260914-hy4-preview-ppu-e2e"
)
SOURCE = CASE_ROOT / "commands/p16k-dual-partial-prefill-20260920/run.sh"
DESTINATION = CASE_ROOT / "commands/p16k-cached-prefill-hybrid-20260921/run.sh"


def replace_once(text: str, old: str, new: str) -> str:
    if text.count(old) != 1:
        raise RuntimeError(f"expected one occurrence, found {text.count(old)}: {old!r}")
    return text.replace(old, new, 1)


def main() -> None:
    text = SOURCE.read_text(encoding="utf-8")
    text = replace_once(
        text,
        "20260920-p16k-d128-c16-n16-dual-partial-prefill-01",
        "20260921-p16k-d128-c16-n16-cached-prefill-hybrid-01",
    )
    text = replace_once(
        text,
        "commands/p16k-dual-partial-prefill-20260920",
        "commands/p16k-cached-prefill-hybrid-20260921",
    )
    text = replace_once(
        text,
        'test -f "${command_root}/build-service-manifest.py"\n',
        'test -f "${command_root}/build-service-manifest.py"\n'
        'test -f "${command_root}/acceptance.py"\n'
        'test -f "${command_root}/sample_validation.py"\n'
        'test -f "${command_root}/verify_accuracy.py"\n',
    )
    text = replace_once(
        text,
        'cp -a "${parent_root}/bundle/evaluation/performance" "${run_root}/bundle/evaluation/"\n',
        'cp -a "${parent_root}/bundle/evaluation/performance" "${run_root}/bundle/evaluation/"\n'
        'mkdir -p "${run_root}/bundle/evaluation/accuracy"\n'
        'cp "${command_root}/acceptance.py" "${run_root}/bundle/evaluation/accuracy/acceptance.py"\n'
        'cp "${command_root}/sample_validation.py" "${run_root}/bundle/evaluation/accuracy/sample_validation.py"\n'
        'cp "${command_root}/verify_accuracy.py" "${run_root}/bundle/evaluation/accuracy/verify_accuracy.py"\n',
    )
    text = replace_once(
        text,
        "  local threshold=$6\n",
        "  local threshold=$6\n  local hybrid_enabled=$7\n",
    )
    text = replace_once(
        text,
        "nohup env CUDA_VISIBLE_DEVICES=0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15 \\\n",
        "nohup env CUDA_VISIBLE_DEVICES=0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15 "
        "VLLM_FL_THEAD_CACHED_PREFILL_SPARSE_MLA_HYBRID='${hybrid_enabled}' \\\n",
    )
    text = replace_once(
        text,
        "    printf 'service_log_startup_complete=%s\\n' \"$(grep -c 'Application startup complete' \"${service_dir}/service.log\" || true)\"\n",
        "    printf 'service_log_startup_complete=%s\\n' \"$(grep -c 'Application startup complete' \"${service_dir}/service.log\" || true)\"\n"
        "    printf 'cached_prefill_hybrid_enabled=%s\\n' \"${hybrid_enabled}\"\n"
        "    printf 'cached_prefill_hybrid_hit_logs=%s\\n' \"$(grep -c 'Using T-Head cached-prefill native/grouped sparse MLA hybrid' \"${service_dir}/service.log\" || true)\"\n",
    )
    text = replace_once(
        text,
        "/workspace/vllm-plugin-FL/vllm_fl/worker/scheduler_fl.py' | sha256sum",
        "/workspace/vllm-plugin-FL/vllm_fl/worker/scheduler_fl.py "
        "/workspace/vllm-plugin-FL/vllm_fl/dispatch/backends/flaggems/impl/mla_sparse.py' | sha256sum",
    )
    for option in (
        "--max-num-batched-tokens \"${mbt}\" \\\n",
        "--max-num-partial-prefills \"${partial}\" \\\n",
        "--max-long-partial-prefills \"${long_partial}\" \\\n",
        "--long-prefill-token-threshold \"${threshold}\" \\\n",
    ):
        text = replace_once(text, f"    {option}", "")
    text = replace_once(
        text,
        "    --flaggems-sha256 \"${fg_sha}\" \\\n",
        "    --flaggems-sha256 \"${fg_sha}\" \\\n"
        "    --hybrid-enabled \"${hybrid_enabled}\" \\\n",
    )
    text = replace_once(
        text,
        "run_config baseline baseline 2048 1 1 0\n"
        "run_config candidate candidate 4096 2 2 2048\n"
        "run_config revert revert 2048 1 1 0\n",
        "run_config baseline baseline 2048 1 1 0 0\n"
        "run_config candidate candidate 2048 1 1 0 1\n"
        "run_config revert revert 2048 1 1 0 0\n\n"
        "test \"$(grep -c 'Using T-Head cached-prefill native/grouped sparse MLA hybrid' \"${service_root}/baseline/service.log\" || true)\" -eq 0\n"
        "test \"$(grep -c 'Using T-Head cached-prefill native/grouped sparse MLA hybrid' \"${service_root}/candidate/service.log\" || true)\" -gt 0\n"
        "test \"$(grep -c 'Using T-Head cached-prefill native/grouped sparse MLA hybrid' \"${service_root}/revert/service.log\" || true)\" -eq 0\n",
    )
    text = replace_once(
        text,
        'docker exec "${container}" python3 "${comparator}" \\\n',
        'docker exec -e PYTHONPATH="${run_root}/bundle/evaluation/accuracy" '
        '"${container}" python3 "${comparator}" \\\n',
    )
    DESTINATION.parent.mkdir(parents=True, exist_ok=True)
    if DESTINATION.exists() and "cached-prefill-hybrid-01" not in DESTINATION.read_text(
        encoding="utf-8"
    ):
        raise FileExistsError(DESTINATION)
    DESTINATION.write_text(text, encoding="utf-8")
    DESTINATION.chmod(0o755)


if __name__ == "__main__":
    main()
