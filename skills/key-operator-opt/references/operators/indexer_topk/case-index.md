# Sparse indexer prefill top-k 案例证据

## DeepSeek-V4-Flash W8A8 / MetaX C550 / 2026-10-23

- 状态：op-002 kept；证据等级 reproduced，仅当前平台与版本。
- [实验主记录](../../../../../models/DeepSeek-V4-Flash-W8A8/metax/20261022-thinking-gpqa-metax103/optimize/op-002.md)，[波动定位](../../../../../models/DeepSeek-V4-Flash-W8A8/metax/20261022-thinking-gpqa-metax103/optimize/fw-002.md)。原始产物路径、SHA、完整结果与失败尝试以主记录为准。
- 环境：DeepSeek-V4-Flash W8A8，8×C550，vLLM 0.24.0 empty，Plugin a696859b…，FlagGems 8200f71f…加当前任务补丁，FlagTree 317a0249…。服务 FULL_DECODE_ONLY；独立算子 eager 与 graph 均验证。
- 路径：prefill/mixed，实际导出函数来自 `flag_gems/runtime/backend/_metax/fused/top_k_per_row_prefill.py`。输入是 sparse indexer 的 logits，不是词表采样。生产证据包含动态行 stride 的 rank2 copy IR；完整每 rank shape 分布未做 profiler 采集。独立测试为 FP32、M=1/4/17/64、N=512…16384、top-512，覆盖行 padding、offset 和列 stride=2。
- 瓶颈：原第三轮额外耗时集中在第二批补入的 Mixed 窗口。校准共享盘时钟后，253 个新 copy 变体均落在该窗口；IR 将动态行 stride 固化为常量。同一慢种子在未改服务中重放恢复正常，排除固定输入必然变慢的解释。
- 修改：operator/improve；只改变 wrapper 的物化条件。`stride(1)==1` 且 `stride(0)>=N` 时沿用原 view，下游 kernel 已接收 runtime stride；其他布局保持原 contiguous fallback。Triton kernel AST、选择算法和 dtype 不变。
- 算子结果：预热公共 kernel 后，24 个未见 stride 的原实现生成24个新 copy，候选为0。此结果是编译机制复现，不是端到端加速倍数。
- 端到端：关闭 prefix cache 的 P32768/D1024/C64/N128 三轮均128/128成功、无新增编译、无非法访问/OOM，吞吐 spread 从历史12.913%变为新组1.0385%。这是稳定性验证，不以旧单个慢轮计算总体加速。
- 正确性：8个独立布局/shape 对照 CPU top-k，值一致、索引唯一且合法、padding/canary通过；capture后更换输入的两次replay通过；5个仓库测试及10个模型最小请求通过。未新增完整GPQA，未做四场景最终验收。
- 知识差量 refined：不必要的连续化不仅增加读写，也可能按精确 stride 产生新 JIT 变体，在已跑过多轮的 Mixed 阶段制造长停顿。未来先关联慢窗口、缓存变体和实际 layout，再尝试最窄的 view 保留条件。
- 限制：未测其他平台、任意内部 stride 或新编译器版本；缓存写入时间不是完整编译关键路径时长；原 micro01 超时原因未单变量确定。原始0.20.2镜像对照属于另一项整栈比较，不用于归因本补丁的独立收益。
