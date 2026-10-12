# QSA sparse GQA 实际案例证据索引

本文件只保存可复用的证据卡。Profiler activity 不是关键路径时间，
小 shape 加速不能外推到大 rows 服务场景。

## Case：20260919-qwen38-flash-next-ppu-e2e / op-015

```yaml
case_id: 20260919-qwen38-flash-next-ppu-e2e
case_link: ../../../../../models/Qwen3.8-Flash-Next/ppu/optimize/op-015-qsa-sparse-gqa-group3.md
status: not-proven
evidence_level: reproduced
environment:
  model: Qwen3.8-Flash-Next
  platform: ppu
  hardware: unknown
  engine_revision: unknown
  plugin_revision: unknown
  operator_library_revision: unknown
  mode: both
operator_path:
  stage: mixed
  impl_id: flag_gems.fused.qsa._qsa_sparse_paged_gqa_kernel
  effective_shape: q=[rows,3,256], kv=[blocks,16,1,256], indices=[rows,2051]
  dtype: bfloat16
  layout: paged KV, one KV head, non-contiguous page table covered
bottleneck_evidence: prof005 Mixed 755 calls and 7.339075s overlapping activity; production transaction rows4096
change:
  classification: operator/improve
  primary_variable: logical head tile BLOCK_M16 to literal four lanes with three valid heads
  applicability_guard: GROUP_SIZE=3, HEAD_DIM=256, TOPK=2051, BF16
results:
  operator: rows64 graph +21.659%; rows4096 graph -4.563%
  end_to_end: not run because operator gate failed
  correctness: bit-exact candidate/generic, FP32 sampled reference, graph capture plus two replays
  regressions: production rows4096 eager -4.549% and graph -4.563%
knowledge_delta:
  prior_belief: removing twelve masked logical head lanes could improve production rows4096
  outcome: contradicted
  revised_belief: BLOCK_M16 parallel mapping is better at rows4096 despite padding; rows64 cannot predict production rows
  future_first_check: benchmark both rows64 and production rows4096 before any service source change
limits: no formal model accuracy; no end-to-end candidate; only the current PPU/TP8/BF16 kernel organization
```

### 环境与实际路径

- Qwen3.8-Flash-Next，PPU，TP8，BF16，graph 服务。
- Plugin QSA 调用 FlagGems
  `_qsa_sparse_paged_gqa_kernel`；query `[rows,3,256]`，K/V
  `[blocks,16,1,256]`，logical TOPK 2051，单 KV head。
- 当前 wrapper 把 `GROUP_SIZE=3` 圆整到 `BLOCK_M=16`。
- 证据：[op-015 记录](../../../../../models/Qwen3.8-Flash-Next/ppu/optimize/op-015-qsa-sparse-gqa-group3.md)。

### 改动、结果与知识差量

- 独立 Triton 候选用字面量 `tl.arange(0,4)`，mask 第 4 lane，并从
  signature 移除 `BLOCK_M`，以避免 PPU runtime 把可调 meta 重写为 16。
- 候选通过 BF16 数值、无效 request 精确零、非连续页、graph capture
  和两次 replay。
- valid rows64 graph 提升 21.659%；valid rows4096 graph 从
  9.494234 ms 退化到 9.948200 ms，即 -4.563%，未达预冻结 +8% 门槛。
- `prior_belief`：减少 GROUP_SIZE=3 时 16-lane 的逻辑 padding 可能在生产
  rows4096 上降低完整 sparse call 成本。
- `outcome`：`contradicted_for_production_rows4096`。
- `revised_belief`：该改动只在 rows64 有效；对 rows4096，原 BLOCK_M16 的
  并行划分/设备利用率优势超过减少逻辑 lane 的收益。
- `future_first_check`：任何 QSA 头维度特化先同时测 rows64 和生产 rows4096；
  rows4096 不达完整事务门槛时不进服务。

### 适用限制

证据仅覆盖上述 PPU/TP8/BF16/QSA shape 和现有 online-softmax/dot 组织。
它不排除减少 memory traffic、改变 TOPK/block 遍历、或其他算法级 QSA
方案，但这些方案都必须重新建立生产 rows 事务基线。

## Case：20260919-qwen38-flash-next-ppu-e2e / op-022

```yaml
case_id: 20260919-qwen38-flash-next-ppu-e2e
case_link: ../../../../../models/Qwen3.8-Flash-Next/ppu/optimize/op-022-qsa-r4-complete-consumer-transaction.md
status: not-proven
evidence_level: reproduced
environment:
  model: Qwen3.8-Flash-Next
  platform: ppu
  hardware: PPU-ZW810E
  engine_revision: unknown
  plugin_revision: 3ae84180
  operator_library_revision: unknown
  mode: both
operator_path:
  stage: prefill
  impl_id: standalone R4 direct-address membership versus flag_gems.fused.qsa.qsa_sparse_paged_attention
  effective_shape: q=[4096,3,256], kv=[512,16,1,256], selected=[4096,2051]
  dtype: bfloat16
  layout: paged KV, one KV head, 8192-token direct-address membership
bottleneck_evidence: prof005 reported QSA as a major Mixed activity; exact real-P4K Prefill selected overlap gave R4 rho=0.695121889
change:
  classification: operator/improve
  primary_variable: group four rows, build a 33,644,552-byte exact membership workspace, and consume each union token once per group
  applicability_guard: rows4096, GROUP_ROWS=4, QUERY_HEADS=3, HEAD_DIM=256, TOPK=2051, exact request boundaries
results:
  operator: eager 9.950968ms to 14.746951ms; graph 9.941424ms to 14.667456ms; gains -32.5219%/-32.2212%
  end_to_end: not run because the complete Prefill transaction gate failed
  correctness: full structure, sampled FP32, eager tolerance, graph bit-exact replay, and post-timing guards passed
  regressions: stable complete-transaction regression above 32%; Mixed intentionally not run
knowledge_delta:
  prior_belief: about 69.5% selected occurrence reuse might offset exact membership construction and grouped attention cost at production rows4096
  outcome: contradicted
  revised_belief: overlap is only a K/V reuse upper bound; direct-address clear/build plus grouped execution must be included before judging net value and dominates this implementation
  future_first_check: time the full production-rows consumer transaction, including every clear/build/fallback cost, before source or service integration
limits: no Mixed timing, no installed implementation, no endpoint result, and formal accuracy remains blocked
```

### 知识差量

- `prior_belief`：真实 P4K selected 上的 R4 复用率足以支持进入服务实现。
- `outcome`：`contradicted_for_current_direct_membership_organization`。
- `revised_belief`：69.5% overlap 不是性能结论；当 32 MiB 级 workspace 清零/构建和
  grouped/fallback 全部纳入后，该实现在生产 rows 稳定退化超过 32%。
- `future_first_check`：对任何新 selected-union 方案，第一个计时必须是包含所有
  metadata 生命周期的 rows4096 完整 consumer 事务，而不是 union 率或内核子段。

## Case：20261010-minimax-m31-w8a8-ppu-tp8-e2e / fix-001 + diag-003

```yaml
case_id: 20261010-minimax-m31-w8a8-ppu-tp8-e2e
case_link: ../../../../../models/MiniMax-M3.1-W8A8/ppu/optimize/diag-003.md
status: kept
evidence_level: reproduced
environment:
  model: MiniMax-M3.1 W8A8
  platform: ppu
  hardware: PPU-ZW810E
  engine_revision: vLLM 0.24.0+empty; native sparse_attn source fefbbcb4ab1e6c4d40538d515e8bf7c247a4cc3ceb8682587b2909b3f0619460
  plugin_revision: cafe6363 plus inherited adaptations and fix-001
  operator_library_revision: PPU Triton 3.6.0; libtriton.so fd682752fda03a2f74e32fb65f9d06eac3fa94b12c172d0c87ca62771428a4c5
  mode: both
operator_path:
  stage: prefill
  impl_id: vllm.models.minimax_m3.common.ops.sparse_attn._gqa_sparse_fwd_kernel
  effective_shape: BLOCK_Q1/GQA8/D128/Kblock128/topk16; QK and PV dot M8/K128/N128
  dtype: BF16 inputs and FP32 accumulation
  layout: paged KV; PPU shared-to-MMA A operand fragment, 4 warps
bottleneck_evidence: correctness divergence first at layer0 attention despite exact QKV; standalone native H8 fails CPU oracle
change:
  classification: operator/improve
  primary_variable: existing fix-001 pads internal H8 tile to H16; diag-003 independently isolates generated A-address lane16 K bit
  applicability_guard: existing fix-001 is PPU BF16 GQA8/D128/topk16, Q1/K128, non-FP8; all other shapes retain original path
results:
  operator: A-only LLVM intervention reduces M8 matmul relativeL2 .998820 to 1.40e-7; Q176 native 1.10164 to .00191226; original reenabled reproduces failure
  end_to_end: no new throughput result; no accepted TP8 performance gain
  correctness: onehot and all128K row/column basis exact; 3 native cases and graph2 pass; existing H16 fix has full198 170/198, not a new run/currentservice rebind
  regressions: shared SSA mask8to24 also altersB and fails random; removing accelerate_matmul fails compiler lowering, not numerical proof
knowledge_delta:
  prior_belief: H8 kernel fails and H16 padding works, mechanism unknown
  outcome: refined
  revised_belief: current PPU M8 A ldmatrix K-coordinate omits lane16; lower16 repeated and upper16 lost perK32; independent A-address correction controls full native failure
  future_first_check: separate QK/PV with onehot and K-basis before blaming attention metadata; trace MMA A/B separately because shared SSA expressions can affect both
limits: current PPU BF16 M8 path only; C++ source line and installed compiler fix not provided; no new GPQA gate or E2E acceptance
```

这是正确性机制卡。实际安装的编译器未修改；IR干预仅在独立空闲PPU8诊断进程，生产TP8服务与四仓源码保留。完整命令、失败项、IR和SHA由模型实验记录及远端案例review签收。
