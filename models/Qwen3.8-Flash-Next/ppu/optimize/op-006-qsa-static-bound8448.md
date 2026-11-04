# op-006-qsa-static-bound8448

- 实验 ID：`op-006-qsa-static-bound8448`；分类：`framework_plus_operator/improve`；当前状态：`rejected_rolled_back_after_formal_accuracy`。
- 来源：[state.yml](state.yml) 同 ID 条目；本次为历史记录整理，没有重跑评测。

## 优化方向与瓶颈依据

优化方向由实验名标识：qsa static bound8448。历史条目没有单列的场景、阶段和瓶颈数值保持待核验，不补造。

## 优化内容与适用边界

Retain for the four frozen formal workloads only, behind explicit VLLM_FL_QSA_STATIC_SCORE_COLUMNS=8448 opt-in. The bound covers the maximum compressed visible width for P32768+D1024, but it is not a production-general claim for arbitrary longer requests. Plugin and FlagGems patches passed focused GPU tests, py_compile, graph smoke, path-hit, and strict independent revert. Formal accuracy remains blocked by inherited GPQA 170/198 versus 88%.

## 正确性与路径命中

已记录验证结论见下方原始结果及外部证据。未单列的最小回归、完整精度或 graph 检查保持待核验，不由性能通过推定精度通过。

## 性能效果

Universal score bound 8448 preserved exact effective selection sets, downstream BF16 output, graph capture, and two replays. It improved complete QSA transactions by 1.555x for P4K Prefill and 1.329x for P4K Decode, with P32K Decode at 1.325x. In exact P4K Mixed A/R, candidate versus independent clean revert improved median output and total-token throughput 7.002%, reduced duration 6.544%, and improved median TTFT/TPOT/ITL/E2E by 15.04%/6.41%/2.01%/6.63%; P99 TTFT/TPOT/ITL/E2E improved 15.56%/6.42%/15.21%/8.71%. Revert drift versus scenario-entry throughput was 0.78%, and all latency drift stayed below 1%.

保留原记录的单位与结论边界；缺失的同 workload baseline/candidate/revert、波动及守护项不补算。

## 决定、风险与回退

- 原决定 `retain_performance_abr_pending_formal_accuracy` 已被 [rb-001](rb-001-qsa-score-bound-rollback.md) 取代。
- `acc-008` 在 bound8448 下为 167/198、19 个 60K 截断；同契约 `acc-009` 移除边界后为 174/198、8 个截断。该边界对正式 GPQA 范围有负面影响，已从当前候选与未来启动契约中撤销。
- 当前服务不设置 `VLLM_FL_QSA_STATIC_SCORE_COLUMNS`，运行时使用完整 `capacity`；历史性能收益保留为历史配置证据，不再计入当前组合。
- 回退后仍为 174/198，正式精度阻塞尚未解除。

## 外部证据

- `/mnt/nfs/users/jinghao/qwen3.8-flash/20260919-qwen38-flash-next-ppu-e2e/microbench/qsa-static-bound-universal-004/result.json`
- `/mnt/nfs/users/jinghao/qwen3.8-flash/20260919-qwen38-flash-next-ppu-e2e/patches/op-006-qsa-static-bound-08`
- `/mnt/nfs/users/jinghao/qwen3.8-flash/20260919-qwen38-flash-next-ppu-e2e/manifests/candidate-maxseq64-bt4096-qsa-bound8448-moe-bm16-service-24.json`
- `/mnt/nfs/users/jinghao/qwen3.8-flash/20260919-qwen38-flash-next-ppu-e2e/performance/p4k-qsa-static-bound8448-mixed-candidate-summary-02.json`
- `/mnt/nfs/users/jinghao/qwen3.8-flash/20260919-qwen38-flash-next-ppu-e2e/performance/p4k-qsa-static-bound8448-revert-02/run-record.json`
- `/mnt/nfs/users/jinghao/qwen3.8-flash/20260919-qwen38-flash-next-ppu-e2e/performance/p4k-qsa-static-bound8448-candidate-revert-summary-01.json`
