# 20260921-p4k-mhc-post-provider-review-14 P4K mHC post provider 审计

- 状态：`rejected`
- 分类：`operator/replace`
- 正式目标场景：`P4096/D1024/C64/N128`
- 目标阶段：Prefill、Mixed

## 优化方向与瓶颈依据

rank0 profile 中 `mhc_post_kernel_hc_mult_4` 占 Prefill 3.389%、Mixed
3.570%。当前 thead 顺序是 `[flagos, reference]`，且 `mhc_post`
不在 FlagOS blacklist，因此 live provider 是 FlagGems 专用 HC4 Triton kernel。
它对 `BLOCK_H/warps/stages` 已按 H=4096 内置 autotune，剩余的有界候选是
vLLM native/reference 的 `bmm` 组合实现是否在大 M 反而更快。

## 优化内容与适用边界

对 trace 真实 `M=4096/12769/16384`、HC4、H4096、BF16 residual/x 和
FP32 mix tensor，直接比较当前 FlagGems 与 Plugin reference provider。每个 shape
独立进程，覆盖 eager、graph capture 及两次 replay。不改 YAML 或源码。

## 晋级与停止条件

- 数值及 graph 必须通过；
- reference 在三个大 M 中位加速均需至少 1.05×；
- 按 Mixed 3.570% device share 估算的端到端收益需至少 1%；
- 否则保留 FlagGems，不改 YAML、不启动服务。

## 当前结果

三个 exact shape 的 eager/graph 数值均通过，最大绝对误差为
`6.1035e-5`，并且完成 graph capture 后两次 replay。graph 中位结果：

| Tokens | FlagGems live | reference | reference / FlagGems |
|---|---:|---:|---:|
| 4096 | 0.14586 ms | 2.92986 ms | 0.0498× |
| 12769 | 0.44783 ms | 8.99417 ms | 0.0498× |
| 16384 | 0.56785 ms | 11.53079 ms | 0.0492× |

reference 在三个大 M 均约慢 20 倍，明确不具备替换价值。决定拒绝并
保留 FlagGems HC4 kernel。调优数据库测量前后 SHA 均为
`1917ccd26c170ca3d7c76197e662a862d3bfbdb1b6da064259bf2202eca38a83`。
没有修改源码、YAML 或启动脚本，不进入服务 A/B/R；服务保持停止。

## 外部证据

`/mnt/nfs/users/jinghao/glm5.3-flash/optimize/e2e-opt-20260911/full-scenarios/p4096-d1024-c64-n128/operators/mhc-post-provider-14/`

- 精确 shape 结果：`microbench-01/tokens-{4096,12769,16384}/result.json`
- 结构化摘要：`microbench-01/summary.json`
- 摘要 SHA-256：`cce61b8dbc7e3427e11169c98012ec7355a85c13ada76d5cf064d1c4dbfb18bc`
