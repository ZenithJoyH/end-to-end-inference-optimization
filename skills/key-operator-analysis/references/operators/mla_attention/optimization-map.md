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

### Sparse Prefill：HKV 很小且 Q-head tile 导致重复读取 KV

- 证据等级：`observation`，来自未在本项目复测的 DeepSeek 历史案例。
- 触发信号：Sparse Prefill 中 HKV=1 或很小，Q head 较多；profile 或访存分析显示同一 KV 被多个过小的 Q-head tile 重复读取。
- 第一检查：确认实际 Prefill 实现、每 rank Hq/Hkv、BH/BK、KV dtype/dequant 位置、shared-memory 上限和读取次数；不要从模型配置推断运行 tile。
- 首个实验：只增大一个 Q-head tile 或调整一组 BH/BK，在不改变算法和 layout 的前提下比较完整 Sparse MLA 调用；扫描上限由目标设备 shared memory 和编译约束决定。
- 必须证据：目标实现命中；KV 读取/调用时间下降；数值、边界 shape、fallback、eager/graph 通过；服务 Prefill/TTFT 有净收益。
- 停止条件：更大 tile 触发 shared-memory/register 压力、合法性约束、重复 dequant 或服务收益消失。
- 来源：[DeepSeek 导入 case card](case-index.md#case20260903-imported-deepseek-v4-flash-w8a8)。原案例的 `BH32/BK16` 只是历史观测点。

### Sparse Decode：单 split grid 小于设备并行能力

- 证据等级：`observation`，来自未在本项目复测的 DeepSeek 历史案例。
- 触发信号：Decode Sparse MLA 的有效 batch/head grid 明显小于 SM/核心并行能力，head tile padding 已不是首要问题。
- 第一检查：记录实际 grid、SM 数、上下文长度桶、top-k、partial output/LSE workspace、merge kernel 和 graph 地址稳定性。
- 首个实验：固定 workload 与其他 tile，从最小可行 split 开始一次只增加 split 数；测量 `主 kernel + merge + workspace/copy` 的完整调用，并同步查看服务 TPOT/吞吐。
- 停止条件：merge、workspace、同步或 graph 成本吞噬收益；短/中上下文回归；局部 kernel 更快但服务阶段变慢。
- 来源：[DeepSeek 导入 case card](case-index.md#case20260903-imported-deepseek-v4-flash-w8a8)。原案例中 S=8 microbenchmark 优于 S=4、但服务更慢，是 split 非单调的反例。

### Mixed Prefill：TP 后每 rank query head 过少

- 证据等级：`observation`，来自未在本项目复测的 GLM 历史案例。
- 触发信号：Mixed Prefill 的 Sparse MLA 在 TP 后每 rank head/grid 很小；无通信的小 tile 或已有 backend 仍不能提供足够并行度。
- 第一检查：量化每 rank H、M bucket、节点内拓扑带宽、两次布局变换/all-to-all 成本、层数复用和 graph 支持；先确认通信不会跨越低带宽边界。
- 首个实验：固定一个 M bucket，仅比较原路径与 `pack heads → Sparse MLA → restore` 的完整调用；从多个 M 点寻找实测交点，而不是沿用历史阈值。
- 必须证据：rank 数据映射和输出严格等价；collective 与目标 kernel 均真实命中；无死锁；eager/graph、服务 Mixed Prefill 和端到端指标通过。
- 停止条件：通信/同步大于计算收益、只有均匀模拟输入获益、跨节点流量出现、graph 不稳定或非目标 M 回归。
- 来源：[GLM 导入 case card](case-index.md#case20260903-imported-glm-5-2-w8a8)。H4→H32、8 rank 和 M≥512 只用于建立候选，不是复用配置。

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
