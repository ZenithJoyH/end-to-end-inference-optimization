# Fused MoE 实际案例证据索引

本文件只保存便于匹配和追溯的证据卡。热点复现不等于候选优化已经
有效；未实施的 config 或微基准不得写成 kept 结论。

## 快速索引

| Case | 状态 | 匹配键 | 主要知识差量 | 证据等级 |
|---|---|---|---|---|
| [20260914-hy4-preview-ppu-e2e](../../../../../docs/cases/20260914-hy4-preview-ppu-e2e/README.md) | kept | Prefill/Mixed/Decode；W8A8；E256；PPU-ZW810E；TP16；graph | 平台 warp、量化和归约特化应由 `_thead` backend 覆盖公共 fused MoE | `reproduced` |
| [20260911-glm53-flash-ppu-e2e](../../../../../docs/cases/20260911-glm53-flash-ppu-e2e/README.md) | kept | Decode cached32/cached64；BF16；E288；PPU；TP16；FULL_DECODE_ONLY | Decode config 必须按 live M 分支；M<=32 与 exact-M64 均已获得同 workload 服务收益 | `reproduced` |

## Case：20260914-hy4-preview-ppu-e2e

### 环境与路径

- 模型/平台：Hy4-preview，PPU-ZW810E，TP16，W8A8 MoE，E256/TopK8；
  主导 shape 为 M2048/H6144，本地 intermediate 128。
- 实际路径：Plugin `FlagGemsW8A8Experts -> flag_gems.fused_experts_impl`；修正后
  registrar 将顶层 API 解析到 `_thead.fused.fused_moe`，归约解析到
  `_thead.fused.moe_sum`。
- 完整证据：[案例摘要](../../../../../docs/cases/20260914-hy4-preview-ppu-e2e/README.md)、
  [优化事实状态](../../../../../models/Hy4-preview/ppu/optimize/state.yml)。

### 改动、边界与结果

- 将 PPU-ZW810E 的 M>=256 4-warp config、精确 per-token INT8 量化 kernel 和
  BF16/TopK8/H6144 固定 moe_sum tile 从公共实现迁入 `_thead/fused/`。
- 相对优化前 `5c2b9a16`，公共 `fused_moe.py` 和 `moe_sum.py` 最终 diff 为空；
  T-Head 顶层 dispatch 命中 vendor backend。
- 聚焦回归 `141/141` 通过。M2048 完整算子公共路径 `2.47939 ms`、T-Head
  backend `2.20469 ms`，加速 `1.1246x`；输出逐位一致，graph capture、两次
  replay 和 eager/replay 均逐位一致。
- 当前没有因本次代码搬迁新增端到端 A/B；已有用户远程组合候选 GPQA 为
  `91.92%`，但本项目没有原生精度产物路径。

### 知识差量

- `prior_belief`：公共 fused MoE 内加严格 device guard 足以隔离平台特化。
- `outcome`：`refined`。
- `revised_belief`：运行边界安全不等于代码分层正确；平台 config、kernel 和
  dispatch 规则必须位于 vendor backend，并由 registrar 证明命中。
- `future_first_check`：提出平台 fused MoE 特化前，先检查 vendor export 与
  registrar；微基准同时比较公共实现和顶层 vendor-dispatched API。
- `new_frontier`：若 wrapper 的临时 hook 成为可测 host 热点，再把 config/quant
  hook 设计成公共实现的显式 backend 参数，而不是把平台判断放回公共文件。

### 适用限制

算子性能只覆盖 PPU-ZW810E、W8A8、M2048/E256/TopK8/H6144/本地 I128；其他
平台和 shape 必须重测。本次证明的是架构迁移不丢失既有算子收益，不是新的端到端
收益证明。

## Case：20260911-glm53-flash-ppu-e2e

### 环境与路径

- 模型/平台：GLM-5.3-Flash-BF16，PPU-ZW810E，TP16/BF16，
  `FULL_DECODE_ONLY`，`max_num_batched_tokens=16384`。
- 场景：P1024/D1024/C64/N128，前缀缓存关闭，预热 DB 后的稳定原路径。
- 实际函数：`flag_gems.fused.fused_moe.invoke_fused_moe_triton_kernel`。
  cached32 Decode 每步有 84 个 fused-MoE kernel，对应 42 层的 GEMM1/GEMM2。
- 完整证据：[案例摘要](../../../../../docs/cases/20260911-glm53-flash-ppu-e2e/README.md)、
  [优化事实状态](../../../../../models/GLM-5.3-Flash-BF16/ppu/optimize/state.yml)。

### 瓶颈、边界与结果

- 16/16 rank trace 可解析。rank0 在 117 个 Decode marker 中，fused MoE
  占可能重叠的 device activity-duration 总和 43.59%，是稳定首热点；
  Decode 跨 rank device spread 为 1.79%。
- Plugin 现有 `_maybe_tune_large_bf16_moe_stage_config` 明确要求
  `C.size(0) >= 4096`，因此大 M 特化不覆盖 cached32 Decode。
- profile 期间 FlagGems DB SHA 不变，排除了本次热点由在线 autotune
  写库造成的竞争解释。profiler-on 吞吐只用于诊断，不是性能证据。
- M<=32 的 GEMM2 配置在多 shape/seed 微基准中位加速 2.1424×；P1K
  targeted A/B/R 吞吐从 840.963 提升到 1004.382 tok/s（+19.432%），
  P99 TTFT/TPOT 分别改善 14.569%/16.262%。
- 改用 `max_num_seqs=64` 后，live Decode 变为 cached64，fused MoE 占 rank0
  activity 53.20%。实际 M64 baseline config 与 M32 不同；保持 BM32 padding
  边界的 exact-M64 GEMM2 配置微基准中位 2.00306×，同 workload max64 服务
  吞吐从 1277.797 提升到 1513.513 tok/s（+18.447%），TTFT/TPOT 也改善。
- exact-M64 候选严格限于 PPU/BF16/E288/H4096/I128/topk8、非量化 GEMM2、
  M=64 且 incoming BM32；聚焦测试 22/22，graph capture/replay 与数值通过。
- 保留候选 reprofile 中 Decode marker span 相对优化前下降 16.018%，fused-MoE
  活动时长下降 30.617%、占比从 53.20% 降到 44.12%，证明收益进入 live graph。
- 同 shape GEMM1 的最佳 alignment-safe 配置仅 1.048522× 中位加速、
  1.036492× 最低加速，未过 1.05× 算子门槛，已停止且未改源码。

### 知识差量

- `prior_belief`：保留的 MoE 分阶段 config 能覆盖本模型的主要 MoE 路径。
- `outcome`：`refined`。
- `revised_belief`：“已开启 MoE stage config”不证明 Decode 已被特化；
  必须同时核对 stage gate、运行时有效 M 和当前 config；`max_num_seqs`
  改变会把 cached32 变为 cached64，M32 的配置不能外推到 M64。
- `future_first_check`：先从 live trace/runtime 获得 GEMM1/GEMM2 精确 shape、
  当前 config、padding 边界和热点占比，再在独立进程做有界单变量扫描。
- `confirmed`：严格 shape-gated 的 M<=32 与 exact-M64 GEMM2 分支都能在各自
  同 workload graph 服务中兑现显著吞吐收益。
- `new_frontier`：GEMM2 与 GEMM1 config 空间已收敛；只有新场景再次证明
  fused-MoE reduction 位于关键路径时，才评估高成本 split-K reduction 融合。

### 适用限制

当前证据只覆盖上述模型、PPU、TP16、BF16、E288、cached32/cached64 和固定
P1K/D1K 服务场景。activity-duration 可能重叠，不是关键路径时间或收益
上限；其他 batch、expert 数、dtype、平台和 Prefill shape 必须重新验证。
本轮为性能 milestone，沿用既有 172/198>=0.86 精度 gate，未重新运行正式精度。
