# op-003-fused-moe-block-m-service

- 实验 ID：`op-003-fused-moe-block-m-service`；分类：`operator/improve`；原记录状态：`complete`。
- 来源：[state.yml](state.yml) 同 ID 条目；本次为历史记录整理，没有重跑评测。

## 优化方向与瓶颈依据

优化方向由实验名标识：fused moe block m service。历史条目没有单列的场景、阶段和瓶颈数值保持待核验，不补造。

## 优化内容与适用边界

Experimental source hooks were fully reverted. The retained mechanism is vLLM's supported VLLM_TUNED_CONFIG_FOLDER with an exact 1..4096 map; only M64 differs from get_default_config. The upstream adaptation's latest formal GPQA score was already 170/198 (85.86%), below its frozen 88% threshold, so this performance case must not invent a passing formal gate. Run a candidate-versus-revert minimal regression on the exact M64 path before P1K formal closure, retain the inherited accuracy blocker, and defer a new full formal run until it can answer a concrete gate question.

## 正确性与路径命中

已记录验证结论见下方原始结果及外部证据。未单列的最小回归、完整精度或 graph 检查保持待核验，不由性能通过推定精度通过。

## 性能效果

A/B/R passed. Candidate versus A improved median output throughput 2.53% from 570.53 to 584.94 tok/s. Candidate versus independent revert R improved throughput 3.35%, median/P99 TPOT 3.53%/3.29%, median ITL 3.85%, and median/P99 E2E 3.21%/3.11%; P99 TTFT regressed 0.75% and P99 ITL regressed 1.22%, both within the 5% guard. Revert-versus-A drift stayed below 1% for throughput, P99 TTFT, P99 TPOT, P99 ITL, and P99 E2E. Restored candidate graph replay produced the same canonical SHA-256 54f05e02051a882c0b45503581c97389e987c8e8b7be6bd7a227e544b7d9cbf7.

保留原记录的单位与结论边界；缺失的同 workload baseline/candidate/revert、波动及守护项不补算。

## 决定、风险与回退

- 原决定：`retain_p1k_candidate_pending_minimal_accuracy_regression_and_long_scenarios`。
- 回退与风险以外部原始契约为准；本次未部署或执行回退。
- 继承的正式精度阻塞不会因补文档而解除。

## 外部证据

- `/mnt/nfs/users/jinghao/qwen3.8-flash/20260919-qwen38-flash-next-ppu-e2e/configs/moe-bm16-decode-only-01/E=512,N=80,device_name=thead.json`
- `/mnt/nfs/users/jinghao/qwen3.8-flash/20260919-qwen38-flash-next-ppu-e2e/patches/op-002-revert-plugin-hooks-use-tuned-folder-01/config-summary.json`
- `/mnt/nfs/users/jinghao/qwen3.8-flash/20260919-qwen38-flash-next-ppu-e2e/manifests/candidate-maxseq64-bt4096-moe-bm16-service-comparison-08.json`
- `/mnt/nfs/users/jinghao/qwen3.8-flash/20260919-qwen38-flash-next-ppu-e2e/smoke/moe-bm16-tuned-config-graph-01/canonical.json`
- `/mnt/nfs/users/jinghao/qwen3.8-flash/20260919-qwen38-flash-next-ppu-e2e/performance/moe-bm16-tuned-config-mixed-candidate-01/run-record.json`
- `/mnt/nfs/users/jinghao/qwen3.8-flash/20260919-qwen38-flash-next-ppu-e2e/performance/moe-bm16-revert-mixed-01/run-record.json`
- `/mnt/nfs/users/jinghao/qwen3.8-flash/20260919-qwen38-flash-next-ppu-e2e/manifests/candidate-maxseq64-bt4096-moe-bm16-service-comparison-10.json`
- `/mnt/nfs/users/jinghao/qwen3.8-flash/20260919-qwen38-flash-next-ppu-e2e/smoke/moe-bm16-restored-graph-02/canonical.json`
