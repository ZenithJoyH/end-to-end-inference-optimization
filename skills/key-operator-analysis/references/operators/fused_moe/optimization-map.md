# Fused MoE 案例驱动优化地图

本文件只收录由实际端到端案例约束的可执行决策。先匹配 live dispatch、
stage、有效 M、expert 数、dtype 和 graph 模式；未匹配维度均视为未知。

## 开放假设

### Decode：大 M stage config 不覆盖稳定 small-M 主路径

- 证据等级：热点与 gate 边界为 `reproduced`；候选收益为 `not-proven`。
- 匹配范围：GLM-5.3-Flash-BF16、PPU、TP16、E288、cached32、
  `FULL_DECODE_ONLY`；实际函数为
  `flag_gems.fused.fused_moe.invoke_fused_moe_triton_kernel`。
- 触发信号：分阶段 trace 显示 Decode 中 fused MoE 是稳定首热点，但
  当前 stage 特化的运行时 gate 排除了实际 Decode M。
- 第一检查：从 trace 和运行函数确认 GEMM1/GEMM2 精确 shape、layout、
  当前 config 和每步调用数；不从模型配置或大 M gate 反推。
- 首个实验：在独立进程中复制 trace 证明的两个 stage shape，记录当前
  config，然后一次只更改 config 做有界扫描。
- 微基准晋级门槛：BF16 reference `allclose`、eager、graph capture 与
  两次 replay 全部通过；GEMM1/GEMM2 至少一个完整 stage 提升
  `>=5%`。
- 服务晋级方式：只为精确支持的 PPU/BF16/E288/small-M shape 增加
  Plugin guard，其他 shape 保留原路径；然后做无 profiler 的 P1K
  3+3 A/B/R。
- 端到端门槛：output throughput `>=+3%`，P99 TTFT 和 P99 TPOT
  的回退分别不超过 5%。
- 停止条件：实际 dispatch/stage 与推断不一致；数值不等价；graph capture
  或 replay 失败；完整候选的 stage 收益不足 5%；对齐、dispatch 或服务
  开销抵消 kernel 收益；端到端门槛失败。
- 来源：[GLM5.3/PPU case card](case-index.md#case20260911-glm53-flash-ppu-e2e)。

## 每次 Fused MoE 改动后的重新排序

1. 重新采集相同 workload 的短 profile，确认目标 config 和 kernel 真实命中。
2. 分开 GEMM1、GEMM2、align/routing 和 collective，不把重叠的 activity-duration
   相加为端到端收益上限。
3. 若 Fused MoE 已不再是首要可兑现瓶颈，停止继续扫描 config，回到
   跨算子候选排名。
4. 只有候选通过微基准与无 profiler 服务 A/B/R，才可从开放假设
   升级为已验证限域路径。
