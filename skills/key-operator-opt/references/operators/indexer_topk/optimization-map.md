# Sparse indexer prefill top-k 排查地图

来源：[MetaX C550 / DeepSeek-V4-Flash 证据卡](case-index.md)。证据等级 reproduced，保留平台、layout、版本与场景限制。

| 项目 | 首个检查与实验 |
|---|---|
| 信号 | 后续测量轮吞吐下降、TPOT升高，但纯decode代理间隔接近；慢窗口中新出现大量rank2 copy编译变体。 |
| 匹配键 | prefill top-k的实际导出路径、列stride、行pitch、dtype、N变化和Triton版本；不能因名字带top-k就套用sampling知识。 |
| 机制 | 上游wrapper先物化连续张量，而下游本已支持runtime stride；copy对精确stride特化，新增编译落入Mixed请求关键路径。 |
| 首查 | 校准缓存文件时钟与服务时钟，检查新变体IR和实际tensor layout，区分编译、已有kernel执行和其他资源扰动。 |
| 单变量证伪 | 预热公共kernel后，使用未见过的合法行pitch，对比原wrapper和保留view的候选；保持算法、dtype、下游kernel及其他配置不变，同时统计新copy变体。 |
| 适用条件 | 已证明下游按runtime stride寻址；当前验证条件为列stride=1且行stride>=N，其他布局继续fallback。 |
| 晋级证据 | 独立CPU参考、合法/唯一索引、padding与canary、fallback、graph capture及至少两次改变输入replay；随后冻结预热准入并保留全部目标Mixed测量轮，检查TTFT/TPOT/吞吐/错误及新增编译。 |
| 停止条件 | 下游实际要求连续布局、隐式copy仍在、数值或canary失败、graph不兼容，或目标Mixed稳定性未改善。 |
| 结论边界 | 编译产物时间线可支持关联，但不能把文件写入时长当完整编译耗时；微实验的首调倍数不能作为端到端加速。尚未跨平台迁移验证。 |
