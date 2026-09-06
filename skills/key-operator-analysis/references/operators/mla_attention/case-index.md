# MLA 实际案例证据索引

本文件只保存便于匹配和追溯的证据卡。环境、命令、patch、完整结果和回退以链接的案例目录为准；不同案例的性能百分比不能脱离 workload 直接比较。

## 快速索引

| Case | 状态 | 匹配键 | 主要知识差量 | 证据等级 |
|---|---|---|---|---|
| [20260904-xingchen4-ppu-isolated-e2e](../../../../../docs/cases/20260904-xingchen4-ppu-isolated-e2e/README.md) | kept；正式模型精度暂缓 | dense decode；per-rank H8；DQK576/DV512；BF16；page16/64；PPU；graph | tile 判断必须使用 TP 后每 rank 有效 head 数；先检查 head padding ratio | `reproduced`，限当前模型/平台/shape |

## Case：20260904-xingchen4-ppu-isolated-e2e

### 环境与路径

- 模型/平台：XingChen4-29B-A4B，PPU-ZW810E，TP4/BF16。
- revision：vLLM 0.24.0+empty；Plugin `f91f4ed08e1cfef0e0efe1380a7721928eccc033`；FlagGems `5941cd2225798bdfa611626f34e459c42cdf2904`。
- 阶段和实现：单 token dense decode；Plugin `forward_mqa` 实际进入 FlagGems `_dense_decode_kernel`。
- 有效 shape：每 rank H8、DQK576、DV512、SQ1、page16/64、最后一维连续。
- 完整证据：[案例摘要](../../../../../docs/cases/20260904-xingchen4-ppu-isolated-e2e/README.md)、[瓶颈观测](../../../../../docs/cases/20260904-xingchen4-ppu-isolated-e2e/mla-observation.md)、[单变量实验](../../../../../docs/cases/20260904-xingchen4-ppu-isolated-e2e/mla-tile-experiment.md)、[补丁](../../../../../models/XingChen4-29B-A4B/ppu/patches/mla-tile16.patch)。

### 瓶颈、改动和结果摘要

- 四 rank profile 中 MLA 各 400 次，累计约 358–360 ms，占 GPU kernel 累计时间约 60.6%–60.9%；`BLOCK_H=64` 处理实际 H8。
- 唯一主要变量为 `BLOCK_H 64→16`；保持算法、KV layout、`BLOCK_N=64`、8 warps 和 stage 搜索不变，并用 shape guard 和显式开关接入。
- 相同 profile 下 MLA 累计降至约 77 ms；shared memory 从 155648 降至 98304 bytes。registers/thread 仍为 256，估计 occupancy 仍为 13%，因此证据不支持“occupancy 改善”这一解释。
- 微基准在已测 B64、S1024/4096/16384 上约 4.0–4.5 倍；端到端三类 workload 的吞吐均提高，但具体百分比只属于本案例，不能作为其他 MLA 场景预期值。
- 数值、eager、graph capture/两次 replay、混合与非对齐长度、空 batch、零长度 padding 和 H16 fallback 已覆盖。正式 GPQA 按该案例当时的用户指示暂缓，因此不能标记模型级精度通过。

### 知识差量

- `prior_belief`：MLA dense decode 优化通常围绕上下文 split、访存和 Tensor Core/带宽平衡；全局 head 数可能暗示较充分的 head 并行度。
- `outcome`：`refined`。
- `revised_belief`：dispatch 和 tile 选择必须首先查看 TP 后每 rank 的有效 head 数。全局 H 较大并不保证单 rank kernel 没有严重 head padding；低 H 下先消除 tile 内无效 head 工作，可能比直接实现 split-KV 更低风险。
- `future_first_check`：记录实际命中 kernel、`H_rank`、`BLOCK_H` 和 `padding_ratio = ceil(H_rank/BLOCK_H)×BLOCK_H/H_rank`；若 ratio 明显大于 1，先对已有兼容小 tile 做单变量 A/B。
- `contradicted_or_unproven`：共享内存下降已观测，但 occupancy 未变化；不能把收益归因于 occupancy。局部约 4 倍不能外推为端到端加速。BH16 不是通用最优值。
- `new_frontier`：应用 tile 后必须重新 profile；本案例热点转移到 MoE、剩余 MLA 和通用 mm。长上下文 sequence split 仍是开放假设，未被本实验验证。

### 适用限制

当前证据只覆盖列出的 PPU、BF16、dense decode 和 shape guard。其他平台、dtype、TP、模型、32K/64K、真实业务 workload 与长稳均需重新验证。复用的是诊断顺序和实验设计，不是参数或收益数字。
