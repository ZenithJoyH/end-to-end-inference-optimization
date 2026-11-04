# op-004-qsa-existing-dot-replacement

- 实验 ID：`op-004-qsa-existing-dot-replacement`；分类：`operator/replace`；原记录状态：`complete`。
- 来源：[state.yml](state.yml) 同 ID 条目；本次为历史记录整理，没有重跑评测。

## 优化方向与瓶颈依据

优化方向由实验名标识：qsa existing dot replacement。历史条目没有单列的场景、阶段和瓶颈数值保持待核验，不补造。

## 优化内容与适用边界

Rejected before service integration. This isolates the operator implementation from score-column narrowing and confirms that BLOCK_H=16 padding on the PPU is not a useful replacement for the current four-head scalar scorer. Candidate service-19 restored the exact 4096 plus M64 BM16 configuration after the isolated run.

## 正确性与路径命中

已记录验证结论见下方原始结果及外部证据。未单列的最小回归、完整精度或 graph 检查保持待核验，不由性能通过推定精度通过。

## 性能效果

With score width fixed at 20000, the existing Qwen4 tl.dot scorer preserved effective selected-token sets, downstream BF16 sparse output, graph capture, and two replays. It nevertheless slowed the complete selection+sparse transaction by 22.40% at rows64 and 29.85% at rows4096; graph replay showed the same regression. Rows1 was neutral to slightly slower.

保留原记录的单位与结论边界；缺失的同 workload baseline/candidate/revert、波动及守护项不补算。

## 决定、风险与回退

- 原决定：`rejected_slower_than_current_scalar_path`。
- 回退与风险以外部原始契约为准；本次未部署或执行回退。
- 继承的正式精度阻塞不会因补文档而解除。

## 外部证据

- `/mnt/nfs/users/jinghao/qwen3.8-flash/20260919-qwen38-flash-next-ppu-e2e/microbench/qsa-dot-replacement-002/result.json`
- `/mnt/nfs/users/jinghao/qwen3.8-flash/20260919-qwen38-flash-next-ppu-e2e/microbench/qsa-dot-replacement-002.failed-001.log`
