# MLA 案例驱动优化地图

本文件把实际案例转化为可执行决策。先匹配 live dispatch、stage 和每 rank shape，再使用对应条目；未匹配的维度视为未知。完整性能数字和 patch 见 [case-index.md](case-index.md)。

## 已验证的限域路径

### Dense Decode：head tile 明显大于每 rank 有效 head 数

- 证据等级：`reproduced`，限 XingChen4/PPU/BF16/H8/DQK576/DV512/SQ1/page16/64。
- 触发信号：目标 dense decode kernel 占比高，且 `padding_ratio = ceil(H_rank/BLOCK_H)×BLOCK_H/H_rank` 明显大于 1。
- 第一检查：不要只看模型全局 head 数；从实际 q shape、TP 切分和 dispatch 日志获得 `H_rank`，同时确认 kernel 的 `BLOCK_H`、grid 和 fallback。
- 首个实验：优先比较已有兼容的小 head tile；只有没有兼容路径时才新增特化。保持算法、KV layout、其他 tile/warp/stage 和服务配置不变，并用精确 shape guard 接入。
- 必须证据：目标实现命中；reference 数值；边界/非对齐 shape；fallback；eager；graph capture 与至少两次 replay；无 profiler 的同条件 baseline/candidate/revert。
- 停止条件：实际未命中、padding ratio 接近 1、小 tile 增加其他维度浪费、数值或 graph 失败、局部收益未兑现到服务阶段。
- 已知反例：共享内存下降不代表 occupancy 必然提高；XingChen4 案例中 registers 和估计 occupancy 未变。不能用 microbenchmark 加速倍数预测端到端加速。
- 来源：[XingChen4/PPU case card](case-index.md#case20260904-xingchen4-ppu-isolated-e2e)。

## 开放假设

### Dense Decode：长上下文下 sequence 维并行不足

- 证据等级：`observation`，尚无独立单变量实现结果。
- 触发信号：head padding 已合理，但长上下文下 kernel 仍占关键路径；grid 主要沿 batch/head，sequence 没有充分 split。
- 第一检查：按 context bucket 比较 kernel 时间，检查 split 数、SM 覆盖、partial output/LSE workspace 和 merge 开销；排除服务调度、KV 抢占和不同生成阶段造成的假象。
- 首个实验：先比较已有 split-KV/online-softmax backend；没有兼容实现时，再以固定 layout 的最小 split 数做原型。
- 停止条件：短/中上下文新增 merge 成本吞噬收益，workspace/graph 地址不稳定，或实际瓶颈已转移。
- 来源：[XingChen4 初始 MLA 观测](../../../../../docs/cases/20260904-xingchen4-ppu-isolated-e2e/mla-observation.md)。该案例最终验证的是 head tile，不是 sequence split。

## 每次 MLA 改动后的重新排序

1. 重新采集相同 workload 的短 profile，确认 MLA 占比和 kernel symbol 已变化。
2. 将新的累计时间映射回端到端关键路径，不能沿用改动前热点排序。
3. 若 MLA 已不再是首要可兑现瓶颈，停止继续细调并回到跨算子候选排名。
4. 把新发现的反例、适用边界和下一首个实验写回 case card；只有跨案例机制改变时才更新稳定 MLA README。
