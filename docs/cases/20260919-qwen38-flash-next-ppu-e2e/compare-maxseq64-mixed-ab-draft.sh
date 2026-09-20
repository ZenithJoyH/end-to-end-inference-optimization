#!/usr/bin/env bash
set -euo pipefail

# The frozen contract requires baseline/candidate/revert and two independent
# service instances for each role. Override these IDs only with runs bound to
# the same mixed plan and comparison contract.
case_root=/mnt/nfs/users/jinghao/qwen3.8-flash/20260919-qwen38-flash-next-ppu-e2e
performance_root=${case_root}/performance
contract=${case_root}/commands/performance/perf-max-seqs-comparison.json
comparison_tool=${case_root}/commands/performance/compare_performance.py

baseline_run_1=${BASELINE_RUN_1:-maxseq32-mixed-baseline-01}
baseline_run_2=${BASELINE_RUN_2:-maxseq32-mixed-baseline-02}
candidate_run_1=${CANDIDATE_RUN_1:-maxseq64-mixed-candidate-01}
candidate_run_2=${CANDIDATE_RUN_2:-maxseq64-mixed-candidate-02}
revert_run_1=${REVERT_RUN_1:-maxseq32-mixed-revert-01}
revert_run_2=${REVERT_RUN_2:-maxseq32-mixed-revert-02}
output=${COMPARISON_OUTPUT:-${performance_root}/maxseq64-mixed-comparison.json}

records=(
  "${performance_root}/${baseline_run_1}/run-record.json"
  "${performance_root}/${baseline_run_2}/run-record.json"
  "${performance_root}/${candidate_run_1}/run-record.json"
  "${performance_root}/${candidate_run_2}/run-record.json"
  "${performance_root}/${revert_run_1}/run-record.json"
  "${performance_root}/${revert_run_2}/run-record.json"
)

test -f "${contract}"
test -f "${comparison_tool}"
test ! -e "${output}"
for record in "${records[@]}"; do
  test -f "${record}"
done

python3 "${comparison_tool}" \
  --contract "${contract}" \
  --run-record "${records[0]}" \
  --run-record "${records[1]}" \
  --run-record "${records[2]}" \
  --run-record "${records[3]}" \
  --run-record "${records[4]}" \
  --run-record "${records[5]}" \
  --output "${output}"
