# Hy4-preview / PPU 优化实验索引

结构化事实入口：[state.yml](state.yml)。本页只维护当前组合、累计证据边界和
优化点索引；每个方向、实现、效果、正确性、决定及外部证据都记录在对应的
`<experiment-id>.md`，不再按日期把多个优化点堆叠在 README 中。

## 当前快照（2026-09-21）

| 项目 | 当前结论 |
|---|---|
| 正式目标 | `P16384/D1024/C64/N128` |
| 当前 milestone | `P16384/D128/C16/N16`；只用于缩短反馈周期 |
| 最新保留候选 | cached-prefill sparse MLA hybrid：full-prefix grouped + cached-prefill native + small-SQ split-K |
| milestone 结果 | output throughput `12.9728 -> 13.5640 -> 12.9755 tok/s`，候选 `+4.558%`，比较通过 |
| 守护项 | P99 TTFT/TPOT/ITL 均改善约 `4.5%`；baseline/revert 漂移 `0.0208%` |
| 精度边界 | 2026-09-19 正式 GPQA `92.93%` 只绑定旧冻结身份，不覆盖当前候选 |
| 源码与服务 | 最新候选未提交、未推送；服务停止，8010 空闲 |
| 晋级条件 | 当前源码精度 gate + 正式 P16K 父场景 profiler-off A/B/revert |

## 记录规则

- 一个优化点只使用一个稳定 experiment-id 和一个 Markdown；后续 profiling、
  正确性、性能与回退结论持续追加到同一文件。
- profiling 或组合 checkpoint 可以证明命中和热点迁移，但不创建每个 trace/run
  的独立文档，也不把 profiler-on 时间当作正式收益。
- `retained` 只表示在相应边界内保留；`rejected`、`unsupported`、`reverted` 和
  `superseded` 同样保留记录。
- 不相加局部加速比；累计收益只采用同配置组合测量。缩减 milestone 不冒充父场景。
- 旧 `optimize/history/` 已清空并移除；隔离基线已归入 `baseline/`。

## 2026-09-14 至 2026-09-15

| 优化点 | 分类 | 状态与决定 |
|---|---|---|
| [Indexer 分块 Top-K](20260914-indexer-topk-batch.md) | `operator/improve` | 保留；P4K scout `20.768x`，比较元数据不完整，限 milestone |
| [max-num-batched-tokens 4096](20260914-mbt4096-scout.md) | `framework` | 拒绝并回退；吞吐仅 `+0.195%` 且 P99 ITL 约翻倍 |
| [mm_out 黑名单](20260915-mm-out-blacklist.md) | `operator/replace` | 保留；后续 profile 中 general MM 命中数降为 0 |
| [HQ4 BK64/BH4 tile](20260915-sparse-mla-hq4-tile.md) | `operator/improve` | 后被 BK32 范围方案取代 |
| [Indexer copy/sync 归因](20260915-indexer-copy-sync-attribution.md) | `diagnostic` | 完成；根因是小 DtoH 引发 host stream drain |
| [small-SQ sparse MLA Split-K](20260915-sparse-mla-small-sq-split-k.md) | `operator/improve` | 保留 SQ<=64；拒绝 SQ128 |
| [Indexer metadata cache](20260915-indexer-metadata-cache.md) | `framework` | 保留后被 builder shim 取代 |
| [SQ2048 sparse MLA BK32](20260915-sparse-mla-sq2048-bk32.md) | `operator/improve` | 保留并扩展；两个缩减场景约 `+1.2%–1.3%` |
| [组合后热点迁移](20260915-post-combination-reprofile.md) | `diagnostic` | 完成；确认 mm_out、metadata、Split-K 命中 |

## 2026-09-16 至 2026-09-18

| 优化点 | 分类 | 状态与决定 |
|---|---|---|
| [SQ2048 tile/Split-K 深挖](20260916-sparse-mla-sq2048-followup.md) | `operator/improve` | 拒绝；最好仅 `0.901x` 且增加 workspace |
| [Indexer row-range Top-K](20260916-indexer-row-range-topk.md) | `operator/improve` | 保留；代表 shape `1.093x–1.543x` |
| [Indexer metadata builder shim](20260916-indexer-metadata-builder-shim.md) | `framework` | 保留；目标路径 pageable DtoH 清零 |
| [BK32 覆盖 128<=SQ<=2048](20260916-sparse-mla-bk32-range.md) | `operator/improve` | 保留；算子 `1.030x–1.185x` |
| [Indexer full-range 快路径](20260916-indexer-full-range-fast-path.md) | `operator/improve` | 保留；算子 `8.462x–12.665x` |
| [Indexer exact pointwise](20260916-indexer-exact-pointwise.md) | `operator/improve` | 保留精确融合；拒绝改变 Top-K 的完全融合 |
| [scaled MM Prefill tiles](20260916-scaled-mm-prefill-tiles.md) | `operator/improve` | 组合保留；设备活动理论上限约 `1.28%` |
| [fused MoE 4-warp](20260916-fused-moe-4warp.md) | `operator/improve` | 当时保留，后被 padding/tile 方案取代 |
| [native router FP32 MM](20260916-router-native-mm.md) | `operator/replace` | 正式精度 gate 后保留；wrapper `2.78x–11.46x` |
| [精确 per-token INT8 quant](20260916-w8a8-exact-quant.md) | `operator/improve` | 保留并迁入 FlagGems-vllm |
| [T-Head moe_sum 分派](20260916-moe-sum-dispatch.md) | `operator/replace` | 保留并迁入 FlagGems-vllm |
| [sparse-index BLOCK_N=2048](20260916-sparse-index-blockn2048.md) | `operator/improve` | 保留；M2048 `4.616x`，热点占比受限 |
| [GEMM2 atomic direct-sum](20260916-gemm2-direct-sum.md) | `operator/improve` | 性能、确定性均失败，回退 |
| [Indexer prefix translate](20260917-indexer-prefix-translate.md) | `operator/improve` | 低风险保留；消除 nonzero 同步链 |
| [vLLM 专用算子迁入 FlagGems-vllm](20260918-flaggems-vllm-migration.md) | `operator/replace` | 保留并推送；Plugin 同步切换调用 |
| [T-Head fused MoE vendor 重构](20260918-thead-fused-moe-vendor-refactor.md) | `operator/improve` | 保留并推送；公共实现恢复无平台特例 |

## 2026-09-19

| 优化点 | 分类 | 状态与决定 |
|---|---|---|
| [full-prefix sparse MLA grouping](20260919-full-prefix-sparse-mla-grouping.md) | `operator/improve` | 保留 SQ>=384；TLE 与索引排序拒绝 |
| [Indexer Top-K 翻译链融合](20260919-indexer-topk-translation-fusion.md) | `operator/improve` | 保留；旧四段 kernel 在新 trace 消失 |
| [Indexer score buffer 复用](20260919-indexer-score-buffer-reuse.md) | `operator/improve` | 保留；完整 block `1.051x–1.059x` |
| [Indexer paged-cache gather](20260919-indexer-paged-cache-gather.md) | `operator/replace` | 保留；代表长度约 `2.65x–2.70x` |
| [Indexer 运行时重采](20260919-indexer-runtime-reprofile.md) | `diagnostic` | 完成；Mixed/Decode-labeled wall 降 `28.54%/36.37%` |
| [删除重复 output.fill_](20260919-indexer-redundant-fill.md) | `operator/improve` | 保留；低风险小收益 |
| [Indexer layout probes](20260919-indexer-layout-probes.md) | `operator/improve` | 收益不足或退化，拒绝 |
| [W8A8 MoE padding/tiles](20260919-w8a8-moe-padding-tiles.md) | `operator/improve` | 保留；完整 MoE `1.19570x` |
| [SiLU×Up+quant 融合](20260919-silu-up-quant-fusion.md) | `operator/improve` | 完整 MoE 仅 `1.0015x`，回退 |
| [full-prefix 扩展到 SQ4096](20260919-sparse-mla-sq4096-range.md) | `operator/improve` | 保留但 mbt=2048 下不激活 |
| [steady-state token-budget sweep](20260919-max-batched-tokens-sweep.md) | `framework` | 所有候选违反吞吐/ITL 联合门槛，保持 2048 |
| [动态 Mixed token budget](20260919-dynamic-mixed-token-budget.md) | `framework` | 未进入实际 Scheduler 构造链，回退 |

2026-09-19 当前组合的维护版 P4K checkpoint 为 `P4096/D1024/C64/N128`：
measured output throughput 中位数 `316.273 tok/s`、轮间 spread `0.123%`。
这是组合 checkpoint，不用于把收益分摊到上述单项；当时最新源码身份也没有匹配
该结果的正式精度 gate。

## 2026-09-20 至 2026-09-21

| 优化点 | 分类 | 状态与决定 |
|---|---|---|
| [Decode MLA 结构探针](20260920-sparse-mla-structural-probes.md) | `operator/improve` | sink/exp2 改写退化；whole-batch native 不成立 |
| [pure Decode native MLA](20260920-native-decode-sparse-mla.md) | `operator/replace` | E2E 仅 `+0.196%`，回退 |
| [scaled MM int32 offset](20260920-scaled-mm-int32-offset.md) | `operator/improve` | 热点上限过小，拒绝 |
| [AllReduce 暴露时间归因](20260920-collective-critical-path.md) | `framework/diagnostic` | 完成；约 96% 活动未被其他 device kernel 隐藏 |
| [PCCl protocol sweep](20260920-pccl-protocol-sweep.md) | `framework` | 消息大小间收益冲突，保持默认 |
| [P16K scenario entry 与 profile](20260920-p16k-scenario-entry-and-profile.md) | `framework/diagnostic` | 完成阶段视图；正式父场景仍待验证 |
| [双 partial-prefill](20260920-p16k-dual-partial-prefill.md) | `framework` | runtime 不支持，拒绝 |
| [Prefill/Decode headroom](20260920-p16k-prefill-decode-headroom.md) | `framework` | 吞吐仅 `+0.82%` 且 P99 ITL 约 `+91%`，回退 |
| [cached-prefill sparse MLA hybrid](20260921-p16k-cached-prefill-sparse-mla-hybrid.md) | `operator/replace` | milestone `+4.558%`，待精度与父场景门禁 |

## 累计边界与下一步

- 当前组合包含多个跨仓库候选；其局部算子加速比、profile 占比和 checkpoint
  趋势不能相加。
- 2026-09-19 的正式 GPQA `92.93%` 是历史冻结身份的有效 gate；当前 hybrid
  源码必须重新绑定或重跑精度。
- 下一轮先对当前 hybrid 重新分解 Prefill、Decode、Mixed，确认 Indexer、
  cached-prefill graph/调度和通信哪个成为新上限。
- 在继续叠加高风险改动或宣布 P16K 完成前，必须补当前源码精度 gate，并完成
  `P16384/D1024/C64/N128` profiler-off A/B/revert。
