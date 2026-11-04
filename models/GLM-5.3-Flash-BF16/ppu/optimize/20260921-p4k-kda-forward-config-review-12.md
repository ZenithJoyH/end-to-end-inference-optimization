# 20260921-p4k-kda-forward-config-review-12 P4K KDA forward 配置审计

- 状态：`rejected`
- 分类：`operator/improve`
- 正式目标场景：`P4096/D1024/C64/N128`
- 目标阶段：Prefill、Mixed

## 优化方向与瓶颈依据

当前长 Prefill 已保留 vendor `chunk_kda_with_safe_gate` 路由，实际调用
FlagGems-vllm plain-Triton `chunk_kda_fwd_infer_triton`。rank0 profile 中：

- Prefill `_kda_fwd_h_o_triton_kernel` 占 2.831%，`intra` 占 0.723%；
- Mixed `h_o` 占 1.689%，`intra` 占 0.741%；
- 两者合计分别为 3.554% 和 2.430%。

trace 显示 Prefill 每层为 `intra grid=(256,4)`、`h_o grid=(4,4)`；
16 个 Mixed wave 中 `intra grid.x=855…1077`，`h_o grid.y=20…256`。
当前 `h_o` 为 `BV=32/warps=4`（grid.x=4、block.x=128），是 KDA 中
贡献最大且仅有 4 个内置 autotune 配置的有界候选。

## 优化内容与适用边界

用两个 trace 对齐 shape 直接筛选 `h_o` 的
`BV{32,64}×warps{2,4}`：

- Prefill：1 个 4096-token 序列，对齐 `grid=(4,4)`；
- Mixed main：64 个序列，4 个长序列加 60 个 one-token cached 序列，
  合计 1077 个 chunk，对齐 `intra grid.x=1077` 与 `h_o grid.y=256`。

每个配置都要完成数值、graph capture 及两次 replay。直接调用
`h_o` kernel，不修改源码或全局 dispatch。`intra` 已对
`BK/BV/warps/stages` 的 243 个组合做内建 autotune，且其单 program
工作不随 T/N 改变；先不重复无边界全量扫描。

## 晋级与停止条件

- 数值与 graph 失败立即停止对应配置；
- 候选 `h_o` graph 中位加速需至少 1.05×，且另一 shape 不回退；
- 按 Mixed `h_o` 1.689% device share 估算端到端上限；估算收益
  低于 1% 则不改源码、不启动服务；
- 只有算子与上限门槛同时通过，才进入 P4096/D128 fresh-service A/B/R。

## 当前结果

首次 runner 在创建结果目录前因把 YAML 真实键
`op_backends` 写成 `per_op` 而被 preflight 拒绝；未运行算子、未生成结果，
已修正断言。有效轮的 graph 中位结果为：

| 配置 | Prefill | 相对 live | Mixed main | 相对 live |
|---|---:|---:|---:|---:|
| `BV32/w4` live | 0.35491 ms | 1.000× | 0.63429 ms | 1.000× |
| `BV32/w2` | 0.43341 ms | 0.819× | 0.61700 ms | 1.028× |
| `BV64/w2` | 1.11370 ms | 0.319× | 1.26358 ms | 0.502× |
| `BV64/w4` | 0.86643 ms | 0.410× | 1.01896 ms | 0.622× |

所有配置的 output/final-state 数值、graph capture 和两次 replay 都通过。
Mixed 最好的 `BV32/w2` 仅加速 1.028×，低于 1.05× 算子门槛，
同时使 Prefill 回退 18.112%。即使增加 N/shape 特化只在 Mixed 选用，
按 1.689% `h_o` device share 估算的 Mixed device-time 收益也只有
0.0460%，远低于 1% 端到端门槛。

决定拒绝，继续保留 `BV32/warps4`。调优数据库测量前后 SHA
均为 `1917ccd26c170ca3d7c76197e662a862d3bfbdb1b6da064259bf2202eca38a83`。
没有修改源码、YAML 或启动脚本，不进入服务 A/B/R；模型服务保持停止。

## 外部证据

`/mnt/nfs/users/jinghao/glm5.3-flash/optimize/e2e-opt-20260911/full-scenarios/p4096-d1024-c64-n128/operators/kda-forward-config-12/`

- 精确 shape 结果：`microbench-01/{prefill,mixed-main}/result.json`
- 结构化摘要：`microbench-01/summary.json`
- 摘要 SHA-256：`0e72902d2628bec8b6a6f43b0dae6691eaf660430dd9449ec75d937c8c6caf5b`
