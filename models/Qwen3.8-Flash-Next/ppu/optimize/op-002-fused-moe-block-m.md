# op-002-fused-moe-block-m

- 实验 ID：`op-002-fused-moe-block-m`；分类：`operator/improve`；原记录状态：`complete`。
- 来源：[state.yml](state.yml) 同 ID 条目；本次为历史记录整理，没有重跑评测。

## 优化方向与瓶颈依据

优化方向由实验名标识：fused moe block m。历史条目没有单列的场景、阶段和瓶颈数值保持待核验，不补造。

## 优化内容与适用边界

原条目未独立说明实现边界，需从下方证据核验后补充；不能据此推定为通用实现。

## 正确性与路径命中

已记录验证结论见下方原始结果及外部证据。未单列的最小回归、完整精度或 graph 检查保持待核验，不由性能通过推定精度通过。

## 性能效果

Decode M64 BLOCK_SIZE_M 32 to 16 improved the full GEMM1+activation+GEMM2 pair by 18.15% with bitwise-equal BF16 output and graph replay stability. Prefill M4096 and M4153 BLOCK_SIZE_M 128 to 64 regressed about 5.0%, so the Prefill override is rejected.

保留原记录的单位与结论边界；缺失的同 workload baseline/candidate/revert、波动及守护项不补算。

## 决定、风险与回退

- 原决定：`retain_decode_only_candidate_reject_prefill_variant`。
- 回退与风险以外部原始契约为准；本次未部署或执行回退。
- 继承的正式精度阻塞不会因补文档而解除。

## 外部证据

- `/mnt/nfs/users/jinghao/qwen3.8-flash/20260919-qwen38-flash-next-ppu-e2e/microbench/fused-moe-block-m-001/result.json`
