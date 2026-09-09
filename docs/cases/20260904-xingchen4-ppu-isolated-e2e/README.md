# XingChen4-29B-A4B / PPU-01：隔离吞吐优化

状态：`completed_performance_only`，决定：保留，证据等级：`reproduced`（同模型同机、多轮及回退）。用户明确暂缓GPQA，本轮进行性能优化并保留轻量正确性护栏。最终数字和复现入口见 [优化报告](../../../models/XingChen4-29B-A4B/ppu/acceptance/optimization-summary.md)，逐阶段历史见 [throughput-results.md](throughput-results.md)。

## 对象与边界

性能测量时，新容器 `xingchen4-e2e-20260904` 使用物理PPU4–7，四卡映射下容器内为0–3。2026-09-06按用户要求改为映射全部16张PPU；2026-09-07最终PR候选服务改用空闲PPU8–11，避开占用PPU1–4的受保护服务，宿主机端点仍为 `127.0.0.1:18000`。原容器 `xingchen4-24-new` 和其他服务未被本任务停止或重启。映射证据见[设备映射修复](../../../models/XingChen4-29B-A4B/ppu/optimize/experiments/20260906-all-ppu/README.md)，最终服务与复测见[PR重构实验](../../../models/XingChen4-29B-A4B/ppu/optimize/experiments/20260907-mla-pr-refactor/README.md)。

模型 `/mnt/cpfs/models/XingChen4-29B-A4B/`，BF16、TP4、最大上下文100000。2026-09-06按用户明确授权改为整个`/mnt:/mnt:rw`；本任务未修改权重或tokenizer。vLLM实际安装版本0.24.0+empty；Plugin revision f91f4ed08e1cfef0e0efe1380a7721928eccc033，FlagGems revision 5941cd2225798bdfa611626f34e459c42cdf2904。只修改调优容器FlagGems MLA文件，原Plugin已有5个脚本改动原样保留；vLLM、原服务和模型未修改。环境与镜像身份归档在 [baseline](../../../models/XingChen4-29B-A4B/ppu/baseline/baseline-manifest.yml)，最终配置和挂载状态归档在 [acceptance](../../../models/XingChen4-29B-A4B/ppu/acceptance/optimization-summary.md)。

## 测量协议

用户指定的13个评测文件直接复制到本仓库test，逐文件hash见 [导入清单](../../../test/IMPORT_MANIFEST.md)。使用复制的vllm_perf.py，wrapper参数化目标、固定种子、保存并核验结果。

| 用途 | 输入/输出tokens | 并发 | 请求/轮 |
|---|---:|---:|---:|
| 原脚本默认主场景 | 1024/1024 | 64 | 128 |
| 中输入补充 | 4096/256 | 64 | 64 |
| 长输入补充 | 16384/256 | 32 | 32 |

各3轮，首轮预热、后两轮稳态，报告稳态中位数及范围。固定随机token、长度比0、temperature0、ignore_eos、流式completions、无限到达速率及并发上限。seed按输入长度/并发/轮次确定，跨配置逐轮相同，同配置不同轮次不复用prompt。graph、prefix cache、TP4、内存比例0.8和batched-token预算8192一致。详见 [performance-config.yml](../../../models/XingChen4-29B-A4B/ppu/acceptance/performance-config.yml)。

主指标为输出和总token吞吐；未指定绝对提升门槛，客观报告差异。错误、超时、输出健康、数值和graph为护栏，尾延迟及资源取舍显式披露。32K/64K完整矩阵、真实业务流量及长时间稳定性未覆盖。

## 瓶颈与单变量改动

实际短profile显示每rank MLA decode占GPU kernel累计时间60.57–60.90%；H8使用BLOCK_H64。针对H8/BF16/DQK576/DV512/SQ1/page16或64，选择同一数学实现的BLOCK_H16配置，保持BLOCK_N64、warps8和stage2/3搜索不变，分类为operator/improve。

page16、B64、S1024/4096/16384微基准耗时约为原实现1/4。worker命中日志和候选profile证明接入：400次MLA/rank累计从358–360ms降到约77ms，共享内存155648→98304bytes。寄存器256和估计occupancy13%没有变化。profiler只用于归因，与无profiler吞吐分账。最终实现按shape、dtype和layout自动分派，不含实验环境变量。见 [观测](mla-observation.md)、[实现实验](mla-tile-experiment.md)、[PR重构实验](../../../models/XingChen4-29B-A4B/ppu/optimize/experiments/20260907-mla-pr-refactor/README.md) 和 [补丁](../../../models/XingChen4-29B-A4B/ppu/optimize/patches/mla-tile16.patch)。

## 正确性与回退

原路径及候选eager/graph可运行，候选和回退均通过C8 sanity。微基准覆盖batch1/8/32/64、混合与非对齐长度、page16/64；最终重构额外覆盖空batch、零长度padding、H8/H16小head路径、H32 fallback和两次graph replay。预定output atol/rtol=.02、LSE atol=.03/rtol=.01，全部通过。最终性能与精度状态见模型/平台目录的 [验收总结](../../../models/XingChen4-29B-A4B/ppu/acceptance/optimization-summary.md) 和 [精度记录](../../../models/XingChen4-29B-A4B/ppu/acceptance/accuracy-result.md)。

历史A/B阶段曾用环境变量选择候选和原路径；最终PR候选已删除该开关，符合能力条件时自动选择BH16，其余输入自动回到BH64。最终回退方式是反向应用补丁并用相同配置重启隔离服务。GPQA按用户指令停止，部分缓存保留，不声称全量精度通过。

## 实验与下一步

| 实验 | 主要变量 | 处理 |
|---|---|---|
| P1K/D256/C32探索 | 无性能改动 | 保留历史，不与默认主场景混算 |
| 初始基线三轮 | 原路径 | 进程有先前评测历史，另以fresh revert复核 |
| MLA微基准和边界 | head tile64→16 | 数值/graph通过，进入端到端验证 |
| 候选及回退三场景 | 同一单变量 | 保留全部轮次与波动 |
| 最终fresh候选主场景 | 同一单变量复现 | 与fresh revert预先配对 |

候选保留后不再叠加第二项主要变量，后续按新热点排序：

| 排名 | 分类 | 候选与依据 | 首个实验/暂缓理由 |
|---|---|---|---|
| 1 | framework | prefill/decode批处理；长输入及TTFT波动 | 单变量调整batched-token预算，需防止尾延迟换吞吐 |
| 2 | operator/replace | MoE约29–30% | 先同shape比较已有实现并做数值/graph对照 |
| 3 | operator/improve | 剩余MLA约25%、通用mm约21–22% | 核对shape和预期端到端收益后再投入 |

## 复盘与限制

实际kernel命中、head padding和shape比静态文档更能支撑决策。已记录容器设备重编号、安装元数据与实际源码revision不一致、并发峰值一秒桶语义、不同进程历史导致基线差异。失败启动、editable安装失败和早期数据均保留。

单机同模型结果只作为该场景复现证据，不形成所有MLA通用BH16规则。SOP不新增通用性能规则；本案例已提炼为 [MLA 证据卡](../../../skills/key-operator-analysis/references/operators/mla_attention/case-index.md#case20260904-xingchen4-ppu-isolated-e2e) 和 [MLA 优化地图](../../../skills/key-operator-analysis/references/operators/mla_attention/optimization-map.md)。知识差量是：tile 判断应使用 TP 后每 rank 的有效 head 数并先量化 head padding ratio；occupancy 改善和通用 BH16 规则均未被证明。完整性能数字仍以本案例为准。

标签：XingChen4、MoE、MLA、mHC、mixed、decode、operator/improve、PPU-ZW810E、TP4、BF16、graph、throughput。

## 2026-09-06 本地规则对照

执行时精确 SOP 版本未冻结，保留为未知。schema 1 baseline 和历史性能数字不追认为通过当前 schema 2/0.12 门禁；新要求的镜像谱系、规范化挂载 diff 与绑定正式精度 gate 尚缺。此次仅修复本地工具，没有连接远端或复测模型；后续正式实验需重新取得当前运行证据。

## 2026-09-07 PR重构

最终FlagGems候选把实验开关改为运行时能力判断：`SQ=1`、每rank head数不超过16、DQK576、DV512、BF16、page16/64且Q末维连续时使用BH16，其他输入保留BH64。H8/H16数值与graph通过，H32 fallback通过；XingChen4 TP4 graph服务C8为8/8。固定P1024/D1024/C64/N128、同一空闲PPU8–11的candidate/revert复测中，输出吞吐和总吞吐中位数均提升73.15%。revert两轮波动较大，因此结论限于明显正收益的性能研究，未声明容量或统计置信度。最终源码、测试、补丁SHA及未测范围见[PR重构实验](../../../models/XingChen4-29B-A4B/ppu/optimize/experiments/20260907-mla-pr-refactor/README.md)。
