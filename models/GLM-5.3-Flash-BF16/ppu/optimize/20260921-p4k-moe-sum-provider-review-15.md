# 20260921-p4k-moe-sum-provider-review-15 P4K MoE sum provider 审计

- 状态：`rejected`
- 分类：`operator/replace`
- 正式目标场景：`P4096/D1024/C64/N128`
- 目标阶段：Prefill、Mixed

## 优化方向与瓶颈依据

rank0 profile 中 `moe_sum_kernel` 占 Prefill 1.507%、Mixed 1.613%。
thead YAML 的 `moe_sum` 顺序是 `[flagos,vendor,reference]`，Plugin 的
FlagOS adapter 实际调用通用 `flag_gems.moe_sum`。FlagGems-vllm 已存在
thead 专用 multi-token `_thead_moe_sum_mt_kernel`，但当前 Plugin 未接入。

这比重写 GEMM2+sum 融合更窄：候选复用已有仓库边界和 kernel，
只需先证明它在 P4K live shape 有足够收益。

## 优化内容与适用边界

在 `M=4096/12769/16384`、topk8、H4096、BF16 连续输入上比较：

1. 当前 `flag_gems.moe_sum`；
2. `flaggems_vllm.runtime.backend._thead.fused.moe_sum.moe_sum`。

候选 libtuner 使用生产 DB 的完整副本，不写入正式
`TunedConfig_thead_triton_3_6.db`。每个 shape 独立进程，覆盖数值、
eager、graph capture 及两次 replay。本轮不改 Plugin 或算子源码。

## 晋级与停止条件

- 数值、graph 及路径必须通过；
- 候选在三个大 M 均需至少 1.05×；
- 按 Mixed 1.613% device share 估算的端到端收益需至少 1%，
  即 sum 本身约需 2.65× 以上；
- 通过后才设计最窄 Plugin dispatch 并做 P4096/D128 A/B/R；
- 否则保留当前 FlagGems 路径，不修改源码、不启动服务。

## 当前结果

三个 shape 均通过 eager 和 graph 数值检查，两个实现均成功
capture 并 replay 两次：

| M | 通用 FlagGems graph | thead multi-token graph | thead/通用速度比 |
|---:|---:|---:|---:|
| 4096 | 0.13895 ms | 0.14122 ms | 0.98393× |
| 12769 | 0.42730 ms | 0.43213 ms | 0.98881× |
| 16384 | 0.54763 ms | 0.55371 ms | 0.98901× |

thead 候选在三组精确 shape 全部略慢，最差约 1.61%，不满足
1.05× 算子门槛；按 Mixed 1.6125% device share 估算，它不但不会
带来 1% 端到端收益，反而最多回退约 0.0263%。因此拒绝接入，
继续使用当前通用 `flag_gems.moe_sum`。

本轮未改 Plugin、FlagGems、FlagGems-vllm、thead YAML 或启动脚本，
也未启动模型服务。生产 DB 测前测后 SHA-256 均为
`1917ccd26c170ca3d7c76197e662a862d3bfbdb1b6da064259bf2202eca38a83`。

## 外部证据

`/mnt/nfs/users/jinghao/glm5.3-flash/optimize/e2e-opt-20260911/full-scenarios/p4096-d1024-c64-n128/operators/moe-sum-provider-15/`

- 汇总 SHA-256：`e0d0fbea5fc1a2c106c645cb14a1c9425b6bfb9418d6de064092d53faec4a9d0`
