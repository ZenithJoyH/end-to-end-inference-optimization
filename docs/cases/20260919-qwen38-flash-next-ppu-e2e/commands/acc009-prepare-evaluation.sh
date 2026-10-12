#!/usr/bin/env bash
set -euo pipefail

case_dir=/mnt/nfs/users/jinghao/qwen3.8-flash/20260919-qwen38-flash-next-ppu-e2e/accuracy/acc-009-full-gpqa-dual-qsa-unbounded-20260922
repo=${case_dir}/bundle/repo
eval_dir=${case_dir}/evaluation
test -f "${case_dir}/services/READY"
test ! -e "${eval_dir}/PREPARED"

python3 "${repo}/evaluation/accuracy/formal_accuracy.py" \
  --config "${eval_dir}/llm-config.json" \
  --evaluation-inspect "${case_dir}/evidence/evaluator.inspect.json" \
  --capture-provenance "${eval_dir}/task-provenance-1.json" \
  > "${eval_dir}/provenance-1.log" 2>&1
python3 "${repo}/evaluation/accuracy/formal_accuracy.py" \
  --config "${eval_dir}/llm-config.json" \
  --evaluation-inspect "${case_dir}/evidence/evaluator.inspect.json" \
  --capture-provenance "${eval_dir}/task-provenance-2.json" \
  > "${eval_dir}/provenance-2.log" 2>&1
cmp "${eval_dir}/task-provenance-1.json" "${eval_dir}/task-provenance-2.json"

python3 - "${eval_dir}/task-provenance-1.json" "${eval_dir}/contract.json" <<'PY'
import hashlib, json, sys
from pathlib import Path
provenance_path = Path(sys.argv[1])
contract_path = Path(sys.argv[2])
provenance = json.loads(provenance_path.read_text())
payload = {
    'schema_version': 3,
    'task': 'gpqa_diamond_generative_cot',
    'metric': 'exact_match,strict-match',
    'expected_samples': 198,
    'expected_doc_ids': list(range(198)),
    'dataset_revision': provenance['dataset_revision'],
    'task_provenance': {
        'path': str(provenance_path),
        'sha256': hashlib.sha256(provenance_path.read_bytes()).hexdigest(),
    },
    'threshold': 0.88,
}
contract_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + '\n')
PY

sha256sum "${eval_dir}/llm-config.json" "${eval_dir}/task-provenance-1.json" \
  "${eval_dir}/task-provenance-2.json" "${eval_dir}/contract.json" \
  "${case_dir}/evidence/evaluator.inspect.json" > "${eval_dir}/prepared.SHA256SUMS"
date -Iseconds > "${eval_dir}/PREPARED"
