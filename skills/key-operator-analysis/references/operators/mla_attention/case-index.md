# MLA 实际案例证据索引

本文件只保存便于匹配和追溯的证据卡。案例目录保存摘要，环境、命令、patch、结果和回退追溯到其链接的模型/平台事实主记录；原始大产物按记录的外部位置查阅。不同案例的性能百分比不能脱离 workload 直接比较。

## 快速索引

| Case | 状态 | 匹配键 | 主要知识差量 | 证据等级 |
|---|---|---|---|---|
| [20260914-hy4-preview-ppu-e2e](../../../../../docs/cases/20260914-hy4-preview-ppu-e2e/README.md) | SQ2048 精确 tile kept；后续 tile/Split-K rejected；Indexer row-range candidate 待端到端复测 | sparse MLA；SQ2048/H4；DQK576/DV512；topk2048；BF16；PPU；TP16；blocked prefill Indexer | 单 kernel grid 已充足时 Split-K 的 merge/workspace 会反噬；Indexer 可直接用 row-range TopK 去掉 dense causal mask | `reproduced`（MLA），Indexer 仅 `microbenchmark` |
| [20260911-glm53-flash-ppu-e2e](../../../../../docs/cases/20260911-glm53-flash-ppu-e2e/README.md) | sparse-index candidate rejected；原 native MLA kept | sparse prefill；H4；DQK512/DV512；topk2048；BF16；PPU；TP16 | 辅助索引 kernel 的 3.55x–4.54x 不足以预测端到端收益；必须测完整服务关键路径 | `reproduced`，限当前模型/平台/shape |
| [20260904-xingchen4-ppu-isolated-e2e](../../../../../docs/cases/20260904-xingchen4-ppu-isolated-e2e/README.md) | kept；正式模型精度暂缓 | dense decode；per-rank H8；DQK576/DV512；BF16；page16/64；PPU；graph | tile 判断必须使用 TP 后每 rank 有效 head 数；先检查 head padding ratio | `reproduced`，限当前模型/平台/shape |
| [20260903-imported-deepseek-v4-flash-w8a8](../../../../../docs/cases/20260903-imported-deepseek-v4-flash-w8a8/README.md) | 原案例 kept；本项目未复测 | sparse prefill HKV1；sparse decode low-grid；KV FP8；MetaX；TP8 | Prefill 的 KV 重读与 Decode 的 grid 不足是不同机制；split 数必须包含 merge 和服务成本 | `observation` |
| [20260903-imported-glm-5-2-w8a8](../../../../../docs/cases/20260903-imported-glm-5-2-w8a8/README.md) | 原案例 kept；本项目未复测 | mixed prefill；per-rank H4；TP16；节点内 8 rank packing；MetaX | low-grid 时通信换计算粒度可能有净收益，但阈值由拓扑、M 和完整通信成本共同决定 | `observation` |

## Case：20260914-hy4-preview-ppu-e2e

### 环境与路径

- 模型/平台：Hy4-preview，PPU-ZW810E，TP16/BF16，FULL_DECODE_ONLY。
- revision：vLLM 0.24.0+empty；Plugin 基线 `38f350b`，当前 Indexer
  candidate 为未提交工作区；FlagGems 基线 `5c2b9a`，当前 sparse MLA wrapper
  candidate 为未提交工作区。
- 阶段和实现：P4K Mixed workload；Plugin Indexer 生成 top-k 索引，实际进入
  FlagGems T-Head `triton_flash_mla_sparse_fwd`。
- 核心 shape：SQ2048、per-rank HQ4、DQK576、DV512、topk2048、BF16。
- 完整证据：[案例摘要](../../../../../docs/cases/20260914-hy4-preview-ppu-e2e/README.md)、
  [优化状态与实验台账](../../../../../models/Hy4-preview/ppu/optimize/state.yml)。

### 瓶颈、改动和结果摘要

- 初始 profile 中 generic sparse MLA 约占设备 kernel 时间 20%–22%。对上述精确
  shape 保留 `BK32/BH4/4 warps/1 stage` 后，两个缩减 P4K 场景的无 profiler
  baseline/candidate/revert 输出吞吐分别提高 1.218% 和 1.291%。
- 继续扫描 `BK16`、`BH1/BH2`、8 warps 和 2 stages 均慢于保留实现。SQ2048
  Split-K 的完整调用把 stage1、merge 和 workspace 分配全部计入；最佳 all-2048
  组合仍只有原路径的 0.901x，并需要约 32.125 MiB workspace，因此回退。
- Indexer block TopK 原路径先创建 `[rows,key_width]` dense boolean causal mask，
  再调用通用 `torch.topk`。candidate 改为已有 row-range provider，并把 provider
  返回的行内相对索引转换为 request-relative 索引；代表 shape 微基准提高
  1.093x–1.543x，单元测试 6/6 通过。该变化尚未完成服务端到端复测，不能计入
  当前累计收益。

### 知识差量

- `prior_belief`：SQ2048、H4 的 Sparse MLA 可能仍可通过 sequence Split-K 增加
  并行度；Indexer 的 dense mask 可能只是次要 host/device 辅助成本。
- `outcome`：`refined`。
- `revised_belief`：决定 Split-K 前应先计算现有单 kernel grid；当 SQ 维已经提供
  足够并行块时，额外 split 的 merge 和 partial workspace 可能主导净损失。
  Indexer 若已有支持逐行有效区间的设备 TopK provider，应优先直接表达 row range，
  避免物化 dense causal mask。
- `future_first_check`：记录原 kernel grid、设备并行规模以及完整
  `stage1 + merge + workspace` 时间；Split-K 从 2-way 开始。Indexer 先检查 provider
  的索引坐标系、tie 语义和 graph 兼容性，再做无 profiler Mixed workload A/B/R。
- `contradicted_or_unproven`：SQ2048 Split-K 并非自动受益；微基准中的 Indexer
  1.093x–1.543x 尚不能外推为端到端收益。
- `new_frontier`：先完成 Indexer candidate 的 P4096/D1024/C64/N64 无 profiler
  复测，再按相同配置重新 profile；若热点迁移，再重新排序，不继续盲扫 sparse MLA tile。

### 适用限制

MLA 结论仅覆盖上述 PPU、BF16、TP16 和精确 shape；父场景 P4K/C64 的正式
baseline/acceptance 尚未完整闭环。Indexer 目前只有算子微基准和单元测试证据，
服务 graph、模型级正确性及端到端收益均待用户复测。

## Case：20260904-xingchen4-ppu-isolated-e2e

### 环境与路径

- 模型/平台：XingChen4-29B-A4B，PPU-ZW810E，TP4/BF16。
- revision：vLLM 0.24.0+empty；Plugin `f91f4ed08e1cfef0e0efe1380a7721928eccc033`；FlagGems `5941cd2225798bdfa611626f34e459c42cdf2904`。
- 阶段和实现：单 token dense decode；Plugin `forward_mqa` 实际进入 FlagGems `_dense_decode_kernel`。
- 有效 shape：每 rank H8、DQK576、DV512、SQ1、page16/64、最后一维连续。
- 完整证据：[案例摘要](../../../../../docs/cases/20260904-xingchen4-ppu-isolated-e2e/README.md)、[瓶颈观测](../../../../../docs/cases/20260904-xingchen4-ppu-isolated-e2e/mla-observation.md)、[单变量实验](../../../../../docs/cases/20260904-xingchen4-ppu-isolated-e2e/mla-tile-experiment.md)、[补丁](../../../../../models/XingChen4-29B-A4B/ppu/optimize/history/patch-mla-tile16-pr.md)。

### 瓶颈、改动和结果摘要

- 四 rank profile 中 MLA 各 400 次，累计约 358–360 ms，占 GPU kernel 累计时间约 60.6%–60.9%；`BLOCK_H=64` 处理实际 H8。
- 唯一主要变量为 `BLOCK_H 64→16`；保持算法、KV layout、`BLOCK_N=64`、8 warps 和 stage 搜索不变。最终PR候选用运行时shape/dtype/layout guard自动接入，不需要模型或环境变量开关。
- 相同 profile 下 MLA 累计降至约 77 ms；shared memory 从 155648 降至 98304 bytes。registers/thread 仍为 256，估计 occupancy 仍为 13%，因此证据不支持“occupancy 改善”这一解释。
- 微基准在已测 B64、S1024/4096/16384 上约 4.0–4.5 倍；端到端三类 workload 的吞吐均提高，但具体百分比只属于本案例，不能作为其他 MLA 场景预期值。
- 数值、eager、graph capture/两次 replay、混合与非对齐长度、空 batch、零长度 padding、H8/H16小head路径和H32 fallback已覆盖。正式 GPQA 按该案例当时的用户指示暂缓，因此不能标记模型级精度通过。

### 知识差量

- `prior_belief`：MLA dense decode 优化通常围绕上下文 split、访存和 Tensor Core/带宽平衡；全局 head 数可能暗示较充分的 head 并行度。
- `outcome`：`refined`。
- `revised_belief`：dispatch 和 tile 选择必须首先查看 TP 后每 rank 的有效 head 数。全局 H 较大并不保证单 rank kernel 没有严重 head padding；低 H 下先消除 tile 内无效 head 工作，可能比直接实现 split-KV 更低风险。
- `future_first_check`：记录实际命中 kernel、`H_rank`、`BLOCK_H` 和 `padding_ratio = ceil(H_rank/BLOCK_H)×BLOCK_H/H_rank`；若 ratio 明显大于 1，先对已有兼容小 tile 做单变量 A/B。
- `contradicted_or_unproven`：共享内存下降已观测，但 occupancy 未变化；不能把收益归因于 occupancy。局部约 4 倍不能外推为端到端加速。BH16 不是通用最优值。
- `new_frontier`：应用 tile 后必须重新 profile；本案例热点转移到 MoE、剩余 MLA 和通用 mm。长上下文 sequence split 仍是开放假设，未被本实验验证。

### 适用限制

当前证据只覆盖列出的 PPU、BF16、dense decode 和 shape guard。其他平台、dtype、TP、模型、32K/64K、真实业务 workload 与长稳均需重新验证。复用的是诊断顺序和实验设计，不是参数或收益数字。

## Case：20260911-glm53-flash-ppu-e2e

### 环境与路径

- 模型/平台：GLM-5.3-Flash-BF16，PPU-ZW810E，TP16/BF16，
  FULL_DECODE_ONLY，`max_num_batched_tokens=16384`。
- 阶段和 shape：sparse prefill，per-rank H4、DQK512/DV512、topk2048；
  主要 token 数为 4096/12401/16384。
- 实现：Plugin thead backend 调用预编译 `flash_mla` sparse kernel；其前置
  vLLM Triton 索引转换默认 `BLOCK_N=128`。
- 完整证据：[案例摘要](../../../../../docs/cases/20260911-glm53-flash-ppu-e2e/README.md)、
  [优化事实与实验台账](../../../../../models/GLM-5.3-Flash-BF16/ppu/optimize/state.yml)。

### 瓶颈、改动和结果摘要

- 16-rank trace 中 native sparse MLA 稳定为第一热点；rank0 主 kernel
  约 2.922 s，前置索引转换的大 prefill shape 约 264.961 ms。
- 预编译主 kernel 未暴露 tile/warp。首个可证伪变量只将索引转换
  `BLOCK_N 128→1024`，并以 token≥4096、topk=2048 和显式环境开关保护。
- 三个主 shape 的索引转换微基准分别提升 3.547x/4.462x/4.542x；
  output/valid-count exact 一致，graph capture + 两次 replay 通过。
- 两场景无 profiler baseline/candidate/revert 的输出吞吐却分别为
  -0.041%/-0.005%，比较器 `failed`；补丁精确回退，未加入保留组合。

### 知识差量

- `prior_belief`：trace 中累计约 265 ms 且可获得 3.5x 以上微基准收益的
  MLA 辅助 kernel，可能形成可测的 prefill/TTFT 改善。
- `outcome`：`refined`。
- `revised_belief`：即使辅助 kernel 的数值和 graph 验证完整，只要它不在
  请求级关键路径上形成足够占比，局部倍数仍可能完全被调度、主 kernel 和
  通信覆盖；进入生产前必须用无 profiler A/B/R 验证。
- `future_first_check`：先估算该辅助 kernel 在完整请求关键路径中的可兑现
  绝对时间，而不只看 profiler 累计时间；保留最小收益门槛和快速回退。
- `contradicted_or_unproven`：BN1024 不是可迁移默认值；`out=` 预分配是否有
  收益未验证，且本轮端到端上限已使其降级。
- `new_frontier`：同一 trace 的 general mm 有多个累计更大的明确 shape 族，
  下一步应先比较已有实现，而不是继续细调 sparse-index 外围。

### 适用限制

反例只覆盖上述 PPU、BF16、TP16、topk2048、两个冻结服务 workload。
它支持“局部辅助 kernel 必须回到端到端验证”的方法，不证明其他模型或
更高占比场景中的索引转换都没有优化价值。

## Case：20260903-imported-deepseek-v4-flash-w8a8

### 环境、路径和结果边界

- 模型/平台：DeepSeek-V4-Flash-W8A8-INT8，8× MetaX C550 64GB，TP8，KV FP8；vLLM 0.20.2 + vllm-plugin-FL + FlagGems。精确代码 revision 与 Sparse MLA `impl_id` 未记录。
- 阶段和 shape：Prefill Sparse MLA 的 HKV=1、Q head 多；Decode Sparse MLA 的单 split grid 小于 SM 数。其余有效 shape、layout 和 graph/eager 覆盖不完整。
- 原案例保留了 Prefill `BH32/BK16`，以及 Decode split-topk `S=4 + merge`；`S=8` 虽然 microbenchmark 更快但服务更慢。数字和结论尚未在本项目独立复测。
- 完整来源：[导入案例摘要](../../../../../docs/cases/20260903-imported-deepseek-v4-flash-w8a8/README.md)。缺少原始 trace、patch、正式精度和同条件独立重复，因此不能升级为 `reproduced`。

### 知识差量

- `prior_belief`：Sparse MLA 可统一围绕更大的 tile 或更多 split 提升并行度。
- `outcome`：`refined`，历史观察级。
- `revised_belief`：Prefill 应先检查 Q-head tile 是否导致 HKV1 的重复 KV 读取及 shared-memory 上限；Decode 应先检查真实 grid/SM 覆盖及 split 后 merge 成本。两者不能共享同一参数方向。
- `future_first_check`：分别记录 Prefill 的 Hq/Hkv、BH/BK、KV 读取与 shared memory，以及 Decode 的 grid、SM 数、split 数、partial workspace 和 merge 时间；完整调用和服务阶段共同决定保留值。
- `contradicted_or_unproven`：split 数和局部 kernel 收益不是单调的；`S=4`、`BH32/BK16` 不是可迁移默认值。

## Case：20260903-imported-glm-5-2-w8a8

### 环境、路径和结果边界

- 模型/平台：GLM-5.2 W8A8，MetaX，TP16；精确加速卡型号、代码 revision、Sparse MLA `impl_id` 和完整 shape 未记录。
- 阶段和 shape：Mixed Prefill 下单 rank H4；原案例以 8 个节点内 rank 做两次 all-to-all，将 query head 聚合到 H32 计算 Sparse MLA 后恢复布局，并只在原环境的 M≥512 分支启用。
- 原文按 78 层估算节省时间，但没有足以在本项目分离通信、kernel 与端到端贡献的原始产物；M=512 不是跨平台阈值。
- 完整来源：[导入案例摘要](../../../../../docs/cases/20260903-imported-glm-5-2-w8a8/README.md)。本项目未独立复测或完成正式精度。

### 知识差量

- `prior_belief`：为算子增加通信通常会抵消单 kernel 的并行度收益。
- `outcome`：`refined`，历史观察级。
- `revised_belief`：当 TP 后每 rank head/grid 过小时，节点内聚合可能以可控通信换取更大的计算粒度；是否成立取决于拓扑带宽、同步、M bucket、层数和两次重排的完整成本。
- `future_first_check`：先排除无通信的小 tile 或 sequence split 能否解决 low-grid，再用单一 M bucket 比较 `原路径` 与 `pack → Sparse MLA → restore` 的完整调用，并从实测交点推导 guard。
- `contradicted_or_unproven`：通信一定是负优化这一先验被原案例削弱，但尚不足以形成通用结论；H32、8 rank 与 M≥512 均只能作为历史候选点。
