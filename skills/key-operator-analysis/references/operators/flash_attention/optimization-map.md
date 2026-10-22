# Flash Attention 优化地图

来源：[MetaX packed GQA 证据卡](case-index.md)。本页为限域诊断规则，不是跨平台默认参数。

| 信号 / 匹配键 | 机制与首个实验 | 通过证据 / 停止条件 | 等级 |
|---|---|---|---|
| GQA打包/转置/Split-KV候选宣称更快；C550/BF16/Q16-KV2-D128/page16 | 固定每rank输入，native Prefill varlen与Decode kvcache分别对完整候选API测graph；保留merge、全部轮次及native回测 | 数值、变化输入replay、稳态通过后仍慢即不部署；不能用历史aggregate或主kernel局部计时覆盖负结果 | micro reproduced：[Qwen3-VL op007](case-index.md)，18shape全部负收益，E2E未测 |
| 已安装FlagGems但trace出现mcFlashAttn；Qwen3-VL/D128/GQA8 | 先分清native varlen Prefill、native kvcache Decode与库内Triton；检查ABI，再做native/库内/候选三路完整API对照 | 无真实命中或paged长度元数据不兼容即停止；packed heads与token tile一起计算，未测不得归因8倍KV收益 | observation：[Qwen3-VL分析006](case-index.md)；候选GPU未测 |
| paged KV 日志页长与候选 guard 命中不一致；需核对 engine/backend revision | 从运行 tensor shape、block table、kernel block size 和 reshape 反向区分逻辑/物理页；按真实映射生成 micro 输入 | 双 rank 实际 dispatch、grid、threads 命中；未命中即停止模型性能比较 | reproduced：本案784→49×16 |
| C550 / BF16 / packed GQA6 / D256 / N16，单 warp 出现 spills | 固定 splits/tile，仅比较 warps；再独立固定 warps 比较 splits，最后测组合，不相加百分比 | 编译资源、FP32、边界、fallback、graph 和完整调用计时；小 batch 退化则缩小 guard | reproduced：本案 W2 去除 spill；N32 负优化 |
| 实际 K 较小但 scheduler 使用大 maxK | 按 batch 分层比较2/4/8/16 splits，保留 merge/copy 开销；小 batch 更依赖 splits 填充设备 | 实际 shape、原/候选/回退同计时；maxK 与 K 不同本身不足以推广少拆分 | reproduced：本案 B16 长 KV 少拆分退化 |
| 独立 graph 探针 queue 创建超时，服务无请求却占设备 | 先检查同设备进程/运行时队列资源；只在授权的专用设备与精确所属服务上隔离 | 隔离后可复现才继续；无精确所属身份不取消进程，不把0测量超时归因 kernel | observation：本案 MACA queue 冲突 |
| kernel 更快，阶段收益小或 Mixed 慢轮 | 以同计划 baseline/candidate/revert、预冻结稳态规则检验阶段与 Mixed；所有轮保留 | 候选未通过准入、无 measured、漂移超限即 incomplete / 回退；健康恢复不证明数值根因 | reproduced：本案 micro18.17%，Mixed18.03%散差失败 |

后续第一步是核对当前服务实际页映射和执行路径。测量前逐项核对比较契约的主指标/guard均已在计划required_metrics中声明；本案缺口不得事后补绑。任何新候选仍须正式精度 gate 与原始四场景验收；该案例没有支持放宽门槛或外推默认配置。
