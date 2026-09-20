#!/usr/bin/env bash
set -euo pipefail

evaluator=flageval_llmeval-jinghao
run_dir=/mnt/nfs/users/jinghao/hy4-preview/optimize/20260914-hy4-preview-ppu-e2e/results/accuracy/formal-gate-20260918-f7d1aaa-a26a902-01

curl -fsS --max-time 5 http://127.0.0.1:8010/v1/models >/dev/null
test ! -e "${run_dir}/formal-wrapper.pid"
test ! -e "${run_dir}/formal-wrapper.log"
test ! -e "${run_dir}/formal-wrapper.exit.code"

docker exec "${evaluator}" bash -lc "
  set -euo pipefail
  run_dir='${run_dir}'
  if ps -eo pid,args | awk -v self=\"\$\$\" '
    \$1 != self && \$0 ~ /[f]ormal_accuracy.py.*formal-gate-20260918-f7d1aaa-a26a902-01/ { found=1 }
    END { exit !found }
  '; then
    echo 'matching formal evaluation is already running' >&2
    exit 1
  fi
  nohup bash -lc '
    set +e
    python \"${run_dir}/bundle/evaluation/accuracy/formal_accuracy.py\" \\
      --config \"${run_dir}/llm_config.json\" \\
      --contract \"${run_dir}/contract.json\" \\
      --service-manifest \"${run_dir}/service-manifest.json\" \\
      --evaluation-inspect \"${run_dir}/evaluation-inspect.json\"
    rc=\$?
    printf \"%s\\n\" \"\$rc\" >\"${run_dir}/formal-wrapper.exit.code\"
    date --iso-8601=seconds >\"${run_dir}/formal-wrapper.finished-at.txt\"
    exit \"\$rc\"
  ' >\"${run_dir}/formal-wrapper.log\" 2>&1 </dev/null &
  printf '%s\n' \"\$!\" >\"${run_dir}/formal-wrapper.pid\"
  date --iso-8601=seconds >\"${run_dir}/formal-wrapper.started-at.txt\"
"

test -s "${run_dir}/formal-wrapper.pid"
cat "${run_dir}/formal-wrapper.pid"
