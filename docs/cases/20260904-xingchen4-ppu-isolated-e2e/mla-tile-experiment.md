# MLA head tile 单变量实验

- 分类：operator/improve。
- 前置证据：四rank短profile显示_dense_decode_kernel占kernel累计时间60.57–60.90%，400调用/rank，grid[1,64,1]、block[256,1,1]、256 registers/thread、155648 shared bytes、估计occupancy13%。
- 可证伪假设：TP4每卡H8而当前BLOCK_H64，减少无效head计算及寄存器/共享内存压力，可降低decode时间并改善端到端输出和总token吞吐。
- 主要变量：BLOCK_H 64→16。保持kernel数学、BLOCK_N64、num_warps8、原有stage2/3搜索空间、KV缓存布局、sampling及服务配置不变。
- 守护：固定sanity输出、数值reference、graph、失败请求、尾延迟和显存。GPQA按用户指示暂缓。

## 微基准

服务停止后，仅使用新容器内device0（物理PPU4）。相同case内保持baseline选定stage不变，直接调用同一个JIT kernel；覆盖page16/64、batch1/8/32/64、长度1/65/257/1024/4096/4097/16384、混合长度及非对齐分页。

预先冻结output atol=rtol=.02、LSE atol=.03/rtol=.01；小batch用FP32 reference，大batch用原实现。全部通过eager与graph capture/replay。已测大batch候选与原输出最大绝对差0；小batch两者相对reference的误差相同，最大约.00701。

| page | batch | 最大长度 | baseline ms | tile16 ms | kernel加速倍数 |
|---|---:|---:|---:|---:|---:|
| 64 | 64 | 1024 | .86700 | .20118 | 4.31 |
| 64 | 64 | 4096 | 3.01100 | .73889 | 4.08 |
| 64 | 64 | 16384 | 11.51106 | 2.86881 | 4.01 |
| 16 | 64 | 1024 | .84460 | .18635 | 4.53 |
| 16 | 64 | 4096 | 2.99787 | .68672 | 4.37 |
| 16 | 64 | 16384 | 11.46456 | 2.68578 | 4.27 |

每项为5组graph计时中位数，每组10次replay；原始记录含全部分组数据。上述不是端到端加速倍数。

## 接入与回退

仅修改新容器的`/workspace/FlagGems/src/flag_gems/fused/flash_mla_with_kvcache.py`。revision 5941cd2225798bdfa611626f34e459c42cdf2904；修改前目标文件git clean。原文件SHA256 b56bb7f1ff1a8ee27717b64f866433eb9ce81bfb34b546384cdcfe0a36d9b85e，候选 c702e786ca98dbd53737466c3882e53fe04611346653736968cc450935a0f773。

本节记录最初的实验接入：当时用`XINGCHEN4_MLA_TILE16`在H8/DQK576/DV512/SQ1/BF16/page16或64/最后一维连续时做A/B，并用一次性worker日志确认命中。不移除graph所需output/lse clone。最终PR候选已删除该环境变量和日志，扩大为有数值验证的H8/H16能力条件自动分派，详见[PR重构实验](../../../models/XingChen4-29B-A4B/ppu/optimize/experiments/20260907-mla-pr-refactor/README.md)。

复现入口统一收敛到 `models/XingChen4-29B-A4B/ppu/optimize/reproduction.md`。历史实验回退通过关闭开关；最终候选回退为反向应用补丁后按相同配置重启隔离服务。完整原文件、manifest和实验patch保存在目标环境`/workspace/e2e-artifacts/patches/mla-tile16/`，本地历史补丁为`models/XingChen4-29B-A4B/ppu/optimize/patches/mla-tile16-experimental.patch`，最终PR补丁为`models/XingChen4-29B-A4B/ppu/optimize/patches/mla-tile16.patch`。

## 当前决定

保留：已完成三场景端到端候选/回退对照及最终fresh候选主场景复测。输出和总吞吐分别提高约95.5%（1K主场景）、73.2%（4K补充）、31.9%（16K补充）；以完整无profiler结果为准，不用局部4倍代替端到端收益。每场景1轮预热、2轮稳态，范围和限制见最终报告。

## 候选服务与补充边界检查

候选eager与graph C8均通过。四worker日志确认page16、H8/D576；graph capture从B512起命中，服务吞吐按固定C64测量。边界检查额外覆盖空batch、[0,1,64,65]混合padding长度及H16非目标fallback，开关两侧输出/LSE一致（padding无效行保留原NaN行为），均完成两次graph replay。空graph按预期提示empty graph，未报错；有效行均有限。记录在新容器mla-boundary-v1.json/log。

相同短profile（P1K/D128/C64/N64，delay30/max10）下，候选四rank各400次MLA调用累计76.868–77.172ms，占24.34–25.10%；原值358.223–360.484ms、60.57–60.90%。MoE仍约92ms、通用mm仍约66.7ms，说明收益主要来自目标MLA路径。

候选trace的shared memory为98304 bytes（原155648），registers/thread仍为256、估算occupancy仍13%；不能声称寄存器或occupancy已改善。当前decode热点排序变为MoE约29–30%、MLA约25%、通用mm约21–22%，后续候选需按此重新排序。

原始候选trace在新容器`/workspace/e2e-artifacts/profiles-tile16-profile/`。带profiler的端到端时长受采集/导出干扰，未用于吞吐收益计算。23:40:31停止候选profile服务PID256223，完成边界检查后进入开关关闭的原路径回退复测。
