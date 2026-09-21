#!/usr/bin/env python3
"""Build the supported P16K prefill/decode-headroom A/B/revert runner."""

from pathlib import Path


CASE_ROOT = Path(
    "/mnt/nfs/users/jinghao/hy4-preview/optimize/"
    "20260914-hy4-preview-ppu-e2e"
)
SOURCE = CASE_ROOT / "commands/p16k-dual-partial-prefill-20260920/run.sh"
DESTINATION = CASE_ROOT / "commands/p16k-prefill-decode-headroom-20260920/run.sh"
OLD_ROOT = CASE_ROOT / "results/performance/20260920-p16k-d128-c16-n16-dual-partial-prefill-01"


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
        'run_root="${case_root}/results/performance/20260920-p16k-d128-c16-n16-dual-partial-prefill-01"',
        'run_root="${case_root}/results/performance/20260920-p16k-d128-c16-n16-prefill-decode-headroom-01"',
    )
    text = replace_exact(
        text,
        'command_root="${case_root}/commands/p16k-dual-partial-prefill-20260920"',
        'command_root="${case_root}/commands/p16k-prefill-decode-headroom-20260920"\n'
        f'baseline_run_record="{OLD_ROOT}/runs/baseline-01/run-record.json"',
    )
    text = replace_exact(
        text,
        'test -f "${parent_root}/config/service-manifest.json"',
        'test -f "${parent_root}/config/service-manifest.json"\n'
        'test -f "${baseline_run_record}"',
    )
    text = replace_exact(text, "run_config baseline baseline 2048 1 1 0\n", "")
    text = replace_exact(
        text,
        "run_config candidate candidate 4096 2 2 2048",
        "run_config candidate candidate 4096 1 1 2048",
    )
    text = replace_exact(
        text,
        '--run-record "${run_root}/runs/baseline-01/run-record.json"',
        '--run-record "${baseline_run_record}"',
    )
    text = replace_exact(
        text,
        '  "${config_dir}/service-baseline.json" "${config_dir}/service-candidate.json" \\\n',
        '  "${baseline_run_record}" "${config_dir}/service-candidate.json" \\\n',
    )
    DESTINATION.write_text(text, encoding="utf-8")
    DESTINATION.chmod(0o755)
    print(DESTINATION)


if __name__ == "__main__":
    main()
