# op-009-fused-moe-drain-block-m

- 实验 ID：`op-009-fused-moe-drain-block-m`；分类：`operator/improve`；原记录状态：`complete`。
- 来源：[state.yml](state.yml) 同 ID 条目；本次为历史记录整理，没有重跑评测。

## 优化方向与瓶颈依据

优化方向由实验名标识：fused moe drain block m。历史条目没有单列的场景、阶段和瓶颈数值保持待核验，不补造。

## 优化内容与适用边界

The first service transition completed the restart but its after-process serializer formed a circular reference; the empty artifact and recovery evidence were preserved, service-38 was recovered without another restart, and service-39 then restored the retained op008 plus exact-M64 config. Screen summary SHA-256 37ea863f932a8119d0c8222e440a3b645f23b81a5cd86c814b225b701ce152d4.

## 正确性与路径命中

已记录验证结论见下方原始结果及外部证据。未单列的最小回归、完整精度或 graph 检查保持待核验，不由性能通过推定精度通过。

## 性能效果

Changing only BLOCK_SIZE_M 32 to 16 improved the complete MoE pair by 18.98%, 18.65%, 17.97%, and 18.41% at M40/M48/M56/M63 with bitwise-equal BF16 output and graph capture plus two replays. The same-config P4096/D128/C64/N64 service milestone improved output throughput only 0.344%, below the pre-frozen 1% threshold; all guards passed but the candidate was rejected.

保留原记录的单位与结论边界；缺失的同 workload baseline/candidate/revert、波动及守护项不补算。

## 决定、风险与回退

- 原决定：`rejected_and_reverted_insufficient_end_to_end_gain`。
- 回退与风险以外部原始契约为准；本次未部署或执行回退。
- 继承的正式精度阻塞不会因补文档而解除。

## 外部证据

- `/mnt/nfs/users/jinghao/qwen3.8-flash/20260919-qwen38-flash-next-ppu-e2e/microbench/fused-moe-drain-batch-002/result.json`
- `/mnt/nfs/users/jinghao/qwen3.8-flash/20260919-qwen38-flash-next-ppu-e2e/configs/moe-bm16-decode-drain-02/config-summary.json`
- `/mnt/nfs/users/jinghao/qwen3.8-flash/20260919-qwen38-flash-next-ppu-e2e/performance/p4k-d128-moe-drain-screen-summary-01.json`
- `/mnt/nfs/users/jinghao/qwen3.8-flash/20260919-qwen38-flash-next-ppu-e2e/transitions/moe-drain-revert-service-39/moe-drain-revert-service-39-raw.json`
