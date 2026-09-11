# MLA 实际案例证据索引

本文件只保存便于匹配和追溯的证据卡。案例目录保存摘要，环境、命令、patch、结果和回退追溯到其链接的模型/平台事实主记录；原始大产物按记录的外部位置查阅。不同案例的性能百分比不能脱离 workload 直接比较。

## 快速索引

| Case | 状态 | 匹配键 | 主要知识差量 | 证据等级 |
|---|---|---|---|---|
| [20260904-xingchen4-ppu-isolated-e2e](../../../../../docs/cases/20260904-xingchen4-ppu-isolated-e2e/README.md) | kept；正式模型精度暂缓 | dense decode；per-rank H8；DQK576/DV512；BF16；page16/64；PPU；graph | tile 判断必须使用 TP 后每 rank 有效 head 数；先检查 head padding ratio | `reproduced`，限当前模型/平台/shape |
| [20260903-imported-deepseek-v4-flash-w8a8](../../../../../docs/cases/20260903-imported-deepseek-v4-flash-w8a8/README.md) | 原案例 kept；本项目未复测 | sparse prefill HKV1；sparse decode low-grid；KV FP8；MetaX；TP8 | Prefill 的 KV 重读与 Decode 的 grid 不足是不同机制；split 数必须包含 merge 和服务成本 | `observation` |
| [20260903-imported-glm-5-2-w8a8](../../../../../docs/cases/20260903-imported-glm-5-2-w8a8/README.md) | 原案例 kept；本项目未复测 | mixed prefill；per-rank H4；TP16；节点内 8 rank packing；MetaX | low-grid 时通信换计算粒度可能有净收益，但阈值由拓扑、M 和完整通信成本共同决定 | `observation` |

## Case：20260904-xingchen4-ppu-isolated-e2e

### 环境与路径

- 模型/平台：XingChen4-29B-A4B，PPU-ZW810E，TP4/BF16。
- revision：vLLM 0.24.0+empty；Plugin `f91f4ed08e1cfef0e0efe1380a7721928eccc033`；FlagGems `5941cd2225798bdfa611626f34e459c42cdf2904`。
- 阶段和实现：单 token dense decode；Plugin `forward_mqa` 实际进入 FlagGems `_dense_decode_kernel`。
- 有效 shape：每 rank H8、DQK576、DV512、SQ1、page16/64、最后一维连续。
- 完整证据：[案例摘要](../../../../../docs/cases/20260904-xingchen4-ppu-isolated-e2e/README.md)、[瓶颈观测](../../../../../docs/cases/20260904-xingchen4-ppu-isolated-e2e/mla-observation.md)、[单变量实验](../../../../../docs/cases/20260904-xingchen4-ppu-isolated-e2e/mla-tile-experiment.md)、[补丁](../../../../../models/XingChen4-29B-A4B/ppu/optimize/patches/mla-tile16.patch)。

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
