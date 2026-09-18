# Fused MoE 实际案例证据索引

本文件只保存便于匹配和追溯的证据卡。热点复现不等于候选优化已经
有效；未实施的 config 或微基准不得写成 kept 结论。

## 快速索引

| Case | 状态 | 匹配键 | 主要知识差量 | 证据等级 |
|---|---|---|---|---|
| [20260911-glm53-flash-ppu-e2e](../../../../../docs/cases/20260911-glm53-flash-ppu-e2e/README.md) | Decode 热点已复现；small-M 候选未开始 | Decode cached32；BF16；E288；PPU；TP16；FULL_DECODE_ONLY | 保留的 `M>=4096` stage 特化不覆盖 P1K 稳定 Decode 主路径 | 热点/边界 `reproduced`；收益 `not-proven` |

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
- 小 M GEMM1/GEMM2 config 扫描未实施，没有微基准或端到端收益结论。

### 知识差量

- `prior_belief`：保留的 MoE 分阶段 config 能覆盖本模型的主要 MoE 路径。
- `outcome`：`refined`。
- `revised_belief`：“已开启 MoE stage config”不证明 Decode 已被特化；
  必须同时核对 stage gate 和运行时有效 M。
- `future_first_check`：先从 trace/runtime 获得 GEMM1/GEMM2 精确 shape 和
  当前 config，再在独立进程做有界单变量扫描。
- `contradicted_or_unproven`：不支持“大 M config 也会自动加速小 M”；
  小 M 最优参数和端到端可兑现收益仍未证明。
- `new_frontier`：在不改变 Prefill 路径的前提下，为 BF16/E288 的精确
  small-M Decode stage 增加 shape-gated config。

### 适用限制

当前证据只覆盖上述模型、PPU、TP16、BF16、E288、cached32 和固定
P1K/D1K 服务场景。activity-duration 可能重叠，不是关键路径时间或收益
上限；其他 batch、expert 数、dtype、平台和 Prefill shape 必须重新验证。
