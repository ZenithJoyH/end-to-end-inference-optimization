# 沐曦 C550 / C588 推理优化经验

截至 2026-11-05，下面的结论来自本项目的模型实验与独立硬件探针。用于选择当前场景的第一个对照实验。生成模型仍按 P1K、P4K、P16K、P32K 依次优化，每个场景分开看 Prefill、Decode 和 Mixed。文中的百分比均属于所链接案例的原始契约。

## 如何选择第一个实验

| 当前信号 | 先验证什么 | 何时换方向 |
|---|---|---|
| P1K 在更换镜像、采样实现或 MoE 配置后明显变慢，轮间有长停顿 | 同机同卡按实际动态 batch、dtype 和采样路径预热，固定准入条件，测旧→新→旧的全部稳态轮次 | 原路径回退漂移超过预算，先恢复可比基线。候选变化落在漂移内时，保留原假设为未证实 |
| P16K/P32K 排队，GPU 看似还有 KV 余量 | 记录每 rank 可用 KV blocks、下一条完整 prompt 所需页数、Running/Waiting 及抢占。只改变有效 blocks 并恢复，比较长输入和短输入哨兵 | Running 随容量变化时优先查预算与接纳。若为 OOM，另查 allocator 中跨层未释放的临时张量 |
| Decode 的 TPOT/ITL 变差 | 复现真实采样参数，看每步 sort、histogram、sweep 或 MoE 在两个阶段的命中次数与实际 shape。Prefill 单测做另一阶段的守护 | 真实调用很少，或完整调用在当前 revision 不占优，就停止该特化。胜出的候选回到当前场景 Mixed 验证 |
| 相同 TP 在 C550 和 C588 上表现不同 | 先列物理卡、die、跨机方式、rank 与 NUMA 映射，再用时间线确认慢处是主机发射、拷贝、collective 还是设备计算 | 微探针可验证某条链路有上限。只有同机单变量能改变模型稳态指标，才将该机制归因为模型瓶颈 |

## 已有证据与反例

**1. 动态 shape 的首次编译可以掩盖稳态差异。** C550 上，Qwen3.6-35B 加齐实际采样 shape 的预热后，P1K 总吞吐旧/新/旧为 2907.06 / 2982.58 / 2892.56 tok/s，新 MoE 配置相对首旧提升 2.60%。Qwen3-VL 在同机复测采样实现得到 3045.66 / 3046.84 / 3071.25 tok/s，当前路径相对首旧只高 0.04%，回切漂移为 0.84%。两个案例支持复用相同的热态测量方法，收益方向仍由当前模型实测决定。BGE-M3 给出了停止条件的实例：1K embedding 对照中原路径两次测量漂移 69.63%，该轮只能记录诊断结果。[Qwen3.6-35B 配置对照](../models/Qwen3.6-35B-A3B/metax/20261104-qwen36-mx59-main-config-001/README.md) · [Qwen3-VL 热态对照](../models/Qwen3-VL-30B-A3B-Instruct/metax/20261105-qwen3vl-opt16-hot1k-mx59-001/README.md) · [BGE-M3 漂移反例](cases/20261105-bge-m3-mx59-base-1k/README.md)

**2. 长上下文先区分 KV 接纳不足与临时张量滞留。** MiniMax-M3 在 C550 的 P32K、N4 缩减对照中，仅将 KV blocks 从 1212 降至 743，Running 众数从 4 降至 2，总吞吐从 2604.33 降至 1757.69 tok/s，恢复后为 2600.78 tok/s。即使 KV 使用率约 70%，剩余页数也可能容不下下一条完整 prompt。另一类问题见 DeepSeek-V4-Flash：C550 上保持 KV 预算固定，将 headpack 临时缓冲的通信排到可安全复用缓冲的流上，压力探针每 rank 的 pending 从 2752 MiB 降到 0，后续 16K/32K 服务复测完成。前例支持在容量受限时调整 KV 预算，后例支持在跨层 pending 增长时检查 stream 与缓冲生命周期。[MiniMax 同机缩容与恢复](cases/20261104-minimax-m3-metax-comm-kv-diagnosis/README.md) · [DeepSeek 同预算修复](../models/DeepSeek-V4-Flash-W8A8/metax/20261022-thinking-gpqa-metax103/optimize/fw-005.md)

**3. Decode 值得查采样，但先证明走的是哪条路径。** Qwen3-VL 的实际服务使用 temperature=0.7、top_k=20、top_p=0.8，greedy 请求无法复现 radix sort 热点。验证 CTA 计数上界后，将直方图累加从 int64 改为 int32。C550 的 P1K/D1K/C64/N128 上，输出吞吐旧/新/旧为 1133.59 / 1357.26 / 1130.62 tok/s，候选高 19.73%，P99 TPOT 降低 16.53%。这笔结果限于该随机采样路径和已固定的 MoE 配置，完整模型精度当时暂缓。复用时先取实际 logits 的行数、词表宽度和采样参数，并验证 ties、特殊值和变化输入的 graph replay。[采样算子与服务对照](../models/Qwen3-VL-30B-A3B-Instruct/metax/20261013-qwen3vl-metax-flaggems-e2e-opt1/optimize/op-005-flaggems-sort-sampling.md)

**4. MoE 与 Attention 的旧调优要和当前主线重比。** MoE 按每 rank 的 M、expert 路由和 dtype 分开看 GEMM1、GEMM2，再测完整 MoE。Qwen3.6-35B 的 PR1067 候选数值和 graph 检查通过，但相对受测主线，M64 集中路由的完整 MoE 慢 9.70%，M8192 非快路径的 GEMM1 慢 13.96%，应在算子层停止晋级。Qwen3.6-27B 的 GQA 候选在 B64/K1K 的完整 API 降时 17.55%，但 Mixed 缺少候选测量，最终回退。两例说明为什么值得保留失败记录，以及为什么不能直接复制 tile、splits 或 warps。[MoE 主线对照](../models/Qwen3.6-35B-A3B/metax/20261104-qwen36-mx59-pr1067-verification-001/README.md) · [GQA 组合回退](../models/Qwen3.6-27B/metax/optimize/combo-001-fa-splits-warps.md)

**5. Attention splits 也可能改变模型质量。** 在 C550 的 Qwen3-VL 同契约试验中，split=1 两轮 GPQA 均为 131/198（66.16%），split=16 两轮均为 120/198（60.61%），低于 64% 门槛。一个可复现窗口里，固定采样噪声后，logits 差异仍使 top-p 候选集合从 2 变为 1。调整分片或归约顺序时，应把它当作高风险数值改动，先对齐 logits、候选集合和首处分叉 token，再做正式精度评测。这个窗口解释了一个具体分叉，无法单独解释所有错题。[分片对照和定位记录](../models/Qwen3-VL-30B-A3B-Instruct/metax/20261024-qwen3vl-metax-fixed-splits/optimize/op-001-fixed-kvcache-splits.md)

**6. C588 的 die 数与主机带宽要分别量。** 同为 TP2，历史比较中 C550 使用两张物理卡，C588 使用同一模组的两个 die。C588-5 独立探针中，同模组两个 die 同时访问本地 Host 内存，合计 H2D/D2H 约 30/34 GB/s；特定跨 NUMA 缓冲放置使 D2H 合计降到约 2.1 GB/s。遇到主机供给间隙时，同时核对 rank 的 CPU 亲和性、实际内存落点和拷贝重叠，再以绑定前/后/恢复的同机模型结果判断是否保留。微探针支持带宽与放置效应，模型收益及硬件、驱动各自贡献仍待受控验证。历史 P64K 可作长上下文诊断，正式目标沿用项目的四个场景。[五模型拓扑对照](cases/20261104-metax-models-c588-c550-overview/README.md) · [C588 同模组及 NUMA 探针](cases/20261105-metax-pcie-c588-bottleneck/README.md)
