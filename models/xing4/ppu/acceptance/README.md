# xing4：PPU隔离吞吐优化结果

Agent 结构化事实入口：[state.yml](state.yml)。

当前运行环境更新（2026-09-06）：用户要求映射全部GPU后，调优容器已扩展为暴露全部16张PPU，`/mnt`完整读写映射保留。容器内服务选卡应使用`CUDA_VISIBLE_DEVICES=4,5,6,7`；历史四卡映射环境的0–3配置不再适用于当前容器。此次映射变更不构成新性能测量，详情见[设备映射修复](../optimize/history/20260906-all-ppu.md)。下文性能结果仍对应原测量环境。

2026-09-04至09-05，PPU-01，4×PPU-ZW810E，TP4/BF16/graph。结论：保留本次MLA head tile优化；三组已测随机token场景的输出和总token吞吐均提高。GPQA按用户要求暂缓，本报告不代表正式模型精度验收或全业务场景达标。

## 端到端结果

每个配置3轮：1轮预热、2轮稳态。下表是两轮稳态中位数（两点时等于均值），单位tokens/s。输入、输出token总数逐轮核验，输出与总吞吐的相对增幅相同，是因为同一case固定token数量、使用同一真实墙钟时长。

| 输入/输出、并发/请求数 | 输出吞吐：原路径 → 优化 | 总吞吐：原路径 → 优化 | 提升 |
|---|---:|---:|---:|
| 1024/1024，C64/N128 | 809.12 → 1582.19 | 1618.25 → 3164.38 | +95.5% |
| 4096/256，C64/N64 | 231.04 → 400.17 | 3927.70 → 6802.95 | +73.2% |
| 16384/256，C32/N32 | 41.59 → 54.86 | 2703.56 → 3566.05 | +31.9% |

| 场景 | 原路径稳态输出范围 | 优化稳态输出范围 |
|---|---:|---:|
| 1024/1024，C64/N128 | 795.45–822.80 | 1510.79–1653.59 |
| 4096/256，C64/N64 | 212.13–249.95 | 399.94–400.41 |
| 16384/256，C32/N32 | 41.59–41.60 | 54.85–54.87 |

主场景采用预先确定的fresh revert与最终fresh candidate配对。初始基线757.01、首次候选1337.59 tok/s均保留在历史记录，但没有选择较慢的初始基线放大最终收益。4K原路径波动较大；即比较其最快稳态轮与候选最慢稳态轮，候选仍提高约60%。只有两轮稳态，尚不足以建立统计置信区间。首次候选稳态1311.72–1363.46、最终候选1510.79–1653.59 tok/s，进程间差异尚未归因。若跨候选阶段采用最低稳态值，对比原路径最快稳态822.80，仍有约59.4%提升；最终95.5%来自预先选定的fresh进程配对，而非所有运行都能保证的增幅。

## 延迟和资源取舍

表中为“逐轮指标的中位数”，不是合并全部请求后重算的分位数。完整P50/P95/P99在紧凑测量JSON和远端原生JSON中。

| 场景 | mean TTFT，s | TTFT P99，s | TPOT P99，ms | E2E P99，s |
|---|---:|---:|---:|---:|
| 1024/1024，C64/N128 | 3.611 → 3.038 | 7.682 → 6.093 | 77.13 → 40.67 | 85.498 → 46.171 |
| 4096/256，C64/N64 | 17.977 → 14.762 | 35.082 → 28.117 | 264.38 → 151.30 | 71.364 → 40.928 |
| 16384/256，C32/N32 | 70.683 → 67.737 | 136.033 → 128.936 | 706.99 → 547.15 | 196.861 → 149.269 |

TTFT具有明显轮间/进程间波动，首次候选mean TTFT由初始基线4.081s变为5.191s；不能据吞吐提高宣称所有延迟都改善。长输入case混合prefill/decode，不能把其输出吞吐解释为纯decode速度。

资源单点快照：基线每卡94828MiB（约92.61GiB）、功耗188/199/193/191W；首次候选每卡94665MiB（约92.45GiB）、功耗253/267/267/258W。均100%设备利用率；容器CPU约6核、内存约40GiB，配额32核/256GiB。显存近似，瞬时功耗升高。这些是单点采样，不是连续峰值/均值，不能推算每token能耗。已采样KV抢占0；未完成独立数小时长稳和完整网络/CPU/功耗连续采样。

## 实际改动与归因

分类：**operator/improve**。唯一主要变量是MLA dense decode的BLOCK_H从64改成16，缩小小head输入的无效计算；保留kernel数学、KV布局、BLOCK_N64、warps8和stage2/3搜索。最终PR候选在BF16、每rank head数1–16、DQK576、DV512、SQ1、page16/64且q最后一维连续时自动启用，其他shape走原实现。当前xing4 TP4服务实际为H8/page16。

修改仅在新容器 `/workspace/FlagGems/src/flag_gems/fused/flash_mla_with_kvcache.py`。四worker日志证明实际命中。相同短profile中每rank400次MLA累计耗时358–360ms→约77ms，占GPU kernel累计时间约60.6%→约25%；共享内存155648→98304bytes，寄存器256和估计occupancy13%没有改善。MoE约92ms和通用mm约66.7ms基本保持，支持收益主要来自目标MLA路径。profile端到端数字因采集/导出干扰未用于上表。

微基准B64/page16/S1024、4096、16384的kernel加速约4.53、4.37、4.27倍；这些局部倍数没有当作端到端倍数。详见[MLA实验](../../../../docs/cases/20260904-xing4-ppu-isolated-e2e/mla-tile-experiment.md)。

## 测量与正确性

用户指定的13个评测文件已直接复制到本项目[test目录](../../../../test/IMPORT_MANIFEST.md)，核验字节一致。实际性能工具为复制的 `test/perf_test/vllm_perf.py`，底层调用当前镜像 `vllm bench serve`；case wrapper参数化目标、种子和产物路径。

协议：随机固定长度token、temperature0、ignore_eos、流式 `/v1/completions`、无限到达速率并受配置并发限制；每配置3轮，首轮预热。seed=42+输入长度×10+并发×1000+轮次，跨配置同轮一致，各轮prompt不同。graph、prefix cache、batched-token预算8192、内存比例0.8、最大模型长度100000一致。冷启动、预热、无profiler稳态和profile分开。

完整核验本轮保存的8组、24轮原生结果，共2112个请求，全部完成、failed=0，每轮input/output token总数匹配预定数量。该计数包含预热和早期主场景历史，不包含sanity、微基准和profile。

原路径和候选eager/graph可运行，固定8并发sanity通过。算子数值门槛在实验前冻结：output atol/rtol=.02，LSE atol=.03/rtol=.01；小batch对FP32 reference、大batch对原实现，测试全部通过。覆盖batch1/8/32/64、混合/非对齐长度、page16/64、空batch、零长度padding、H8/H16小head路径、H32 fallback及至少两次graph replay。已测大batch候选与原输出差0，小batch最大reference误差约.00701且两者相同。这不构成全量模型精度或logits等价证明。

[性能配置](/Users/baai/Documents/ChatGPT/端到端推理优化/.cache/model-record-archives/20261102-record-reconciliation-01/files/models/XingChen4-29B-A4B/ppu/acceptance/performance-config.yml)、[精度配置与正确性护栏](/Users/baai/Documents/ChatGPT/端到端推理优化/.cache/model-record-archives/20261102-record-reconciliation-01/files/models/XingChen4-29B-A4B/ppu/acceptance/accuracy-config.yml)、[正式精度状态](accuracy-result.md)、[完整数值与raw文件SHA256](../optimize/performance-measurements.json)。32K/64K原脚本完整矩阵、真实业务数据、其他dtype/TP/硬件、100K上下文极限及长期稳定性未覆盖。

## PR 准备状态

2026-09-07 已将FlagGems实验补丁整理为shape自动分派的最终候选，移除`XINGCHEN4_MLA_TILE16`、一次性PID日志和`Autotuner.fn`依赖，`pr_readiness=ready_for_review`。主记录为[PR重构实验](../optimize/history/20260907-mla-pr-refactor.md)；未改Plugin或vLLM。

| 范围 | 已有证据 | 尚需处理 |
|---|---|---|
| PPU、BF16、TP4 每 rank H8 的目标路径 | 最终源码重新完成micro、graph、C8和同设备candidate/revert；主指标+73.15% | revert轮间波动较高；未形成持续容量结论 |
| 边界与 graph | H8/H16、page16/64、非对齐、空输入、H32 fallback及两次graph replay | 其他dtype/DQK/DV/page、模型调用方和长期worker生命周期未实测 |
| 平台选择及配置 | 按SQ/H_rank/DQK/DV/page/dtype/stride自动选择；TLE优先级不变 | 非PPU平台只证明保持fallback代码，未做硬件性能验证 |
| 最终代码与版本 | 本地最终patch含实现和测试，远端源码/test SHA及BH16缓存命中已核对 | 上游pytest在PPU被模块级NVIDIA reference条件skip；上游CI仍需执行 |

最终补丁已在目标PPU硬件重新验证；正式GPQA仍按用户指示暂缓，因此`ready_for_review`不等于正式模型精度通过。

## 历史环境与服务操作记录

本节记录测量时环境及后续恢复操作，不是当前进程快照。下述四卡暴露和容器内 0–3 编号属于旧环境；2026-09-06 的全卡映射以[设备映射修复记录](../optimize/history/20260906-all-ppu.md)为准。再次执行前重新核验运行事实，不能沿用本节 PID、容器 ID 或选卡编号。

- 目标模型 `/mnt/cpfs/models/XingChen4-29B-A4B/`，served name `teleai-flagos`；2026-09-06按用户明确授权改为整个`/mnt:/mnt:rw`，本任务未改权重、tokenizer、量化或采样语义。权重revision未知，配置/tokenizer指纹见案例preflight。
- 原 `xingchen4-24-new` 是容器名。调优环境先基于相同基础镜像，2026-09-06再从已验证候选保存快照`xingchen4-e2e-tile16:mnt-remap-20260906`并重建；当前容器ID为`970dab52d71d...`，整个`/mnt`读写映射。旧模型目录只读容器以停止状态保留用于回退。
- vLLM实际安装0.24.0+empty，wheel revision未知；Plugin f91f4ed08e1cfef0e0efe1380a7721928eccc033，FlagGems 5941cd2225798bdfa611626f34e459c42cdf2904。原Plugin已有5处脚本改动原样保留，未修改Plugin或vLLM。
- 驱动2.1.1-rbd225，HGGC13.0，PPU-SMI1.28。历史测量容器private IPC、bridge、16GiB shm、256GiB内存/32核配额，只暴露物理PPU4–7设备；该旧映射下容器内CUDA_VISIBLE_DEVICES为0,1,2,3，不能用于之后的全卡映射容器。
- 性能验收时的优化服务标签为`tile16-final`。该进程在闲置约33小时后于2026-09-06 09:10:20出现无上游worker根因日志的EngineCore unexpected exit；挂载重建后恢复为`mnt-remap-final`、容器内API PID32，仍使用`XINGCHEN4_MLA_TILE16=1`、graph、无profiler及宿主机`127.0.0.1:18000`。重建后C8为8/8，四worker命中优化，两个服务health均通过。
- 原容器`xingchen4-24-new`、8000端口、PPU0–3没有被本任务停止或重启，未对原服务发送生成/benchmark；2026-09-06调整期间health仍为200。独立GPQA容器的评测进程已按指令停止。

最终核验确认两个服务 health 正常、候选源码 SHA256 匹配、四个 worker 命中 tile16/page16、C8 固定输出通过，且没有遗留 benchmark、profile 或 GPQA 进程。一次性的 PID、容器 ID 和逐条命令输出不在项目中长期保存。测量期间共用宿主机，但设备与源码/缓存隔离；没有测量原业务SLO，因此不把health检查解释为完整业务性能证明。

## 复现和回退

复现条件和安全检查见 [历史复现说明](../optimize/history/reproduction.md)。历史上候选→原路径已完成三场景回退复测；未来复测必须基于当前适配容器重新创建优化容器，重新解析设备、端口和进程，不执行绑定旧 PID 或容器状态的一次性脚本。

[PR说明](../optimize/history/patch-mla-tile16-pr.md)记录该改动；baseline SHA256 `b56bb7f1ff1a8ee27717b64f866433eb9ce81bfb34b546384cdcfe0a36d9b85e`，最终源码SHA256 `45eaf0e7342dcf9bfd0987dacb11dea6572d948b2334805639e50840b7d450c9`，最终测试SHA256 `cda6ae24958760777c19f95abb9699111bf7c77512780891bf2738439cf6e40c`。patch 文件不再保存在模型目录，最终实现以目标源码 revision 和 SHA 为准；未提交或推送代码。

原始性能JSON/CSV、逐请求输出、命令、日志、trace均保留在新容器 `/workspace/e2e-artifacts/`；精确目录和原生JSON hash列在[多轮性能记录](../optimize/performance-measurements.json)，未把完整日志或trace加入项目。关键trace目录为profiles-profile-decode-v2和profiles-tile16-profile。

## 结论与后续

在以上三个随机token场景保留优化，证据等级 `reproduced`（同模型同机、多轮及回退），不宣称全局最优、业务SLO达标或正式精度通过。下一步优先单变量检查prefill/decode批处理预算及TTFT；其次比较MoE已有实现（候选profile约29–30%）；然后评估剩余MLA/mm。当前不叠加未经验证的第二项改动。

案例[核心记录](../../../../docs/cases/20260904-xing4-ppu-isolated-e2e/README.md)保留关键失败、探索性数据和复测决策；一次性操作脚本已在结论提取后清理。知识库仅增加本平台/shape的局部证据，不把单次案例升级为通用SOP性能规则。

## 2026-09-06 挂载调整

用户明确授权将整个`/mnt`读写映射到调优容器。当时核验挂载为`Source=/mnt, Destination=/mnt, RW=true`，候选源码 SHA、worker 命中和 C8 sanity 均保持；没有重跑完整性能矩阵。该调整发生在性能测试之后，不改变前述历史测量口径，一次性容器替换过程和状态 dump 不长期保留。
