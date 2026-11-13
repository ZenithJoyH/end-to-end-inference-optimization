# 用 Roofline 定位推理瓶颈并选择下一步实验

本方法供 `$inference-roofline-analysis` 消费既有时间线、硬件计数器或明确标注的估算证据，形成可证伪的优化候选。
它负责分析计算/带宽屋顶及其决策含义，不接管 Profiling Skill 的采集、有效性核验或正式性能验收。
低开销证据已足以确定方向时，不为绘图强制新增采集；缺少证据时给出有边界的补证需求并路由 `$inference-profiling`。
实际命令、现有 runner 的能力与结果语义仍以 [性能工具说明](../../../evaluation/performance/README.md#profiling-与-sglang-诊断)为准。

## 1. 先定义范围，再决定测什么

绑定既有 `experiment-id`、当前 `scenario_id`、同配置 baseline 和当前候选身份。
继承已批准的 Host、独立优化容器、工作根、资源、源码与服务边界，不因采集工具需要而扩大权限。
先读时间线，再提出最小代表性范围的计数器需求；不得对整个长服务默认开启全指标、多次 replay。

| 视图 | 必须辨认的执行状态 | 常见判断问题 |
|---|---|---|
| Prefill | 实际新增 query token、已有前缀/KV 长度、chunk、batch、实际矩阵 shape | 是大 GEMM 计算、Attention、padding，还是调度等待？ |
| Decode | 实际活跃序列数、上下文长度分布、每步新 token 数、KV 布局与精度 | 是读权重、读 KV、通信，还是 launch/主机间隙？ |
| Mixed | 每步两阶段 token 构成、batch 变化、共享 kernel、抢占与排队 | 长 Prefill 是否占住关键资源、拉长 Decode ITL？ |

服务事件、iteration/token 元数据或实际 shape 应能解释阶段边界；只看 kernel 名称不够。
NVTX 标记应位于实际提交设备工作的 worker，并通过 launch/correlation 映射到 GPU 执行。
CPU range 的持续时间不等于 GPU 时间；graph replay 也不能依靠 capture 时的 Python 调用重新归因。
混合 batch 的 GEMM 可能服务两类 token，无法独立计量时保留为 Mixed/shared，不能按 token 比例伪造两份 HBM 流量。
TTFT、TPOT/ITL 包含的排队、调度和网络成本另列，不能直接代入 kernel Roofline。

先满足稳态准入，排除模型加载、JIT、首次 allocator 行为和 graph capture；保留实际 graph 模式。
阶段专项缩减 workload 要记录与目标场景的差异及残余成本，不以短探针代表正式场景。
按 rank/worker/device 分开记录并标明覆盖；只采 rank 0 不能代表 MoE、TP/EP 通信或慢 rank。

## 2. 检查两类证据，明确能力与补证需求

检查已有两类证据是否充分：时间线确定设备关键路径、热点 shape、调用次数、主机间隙、通信及重叠；
代表性 kernel/graph/range 的硬件计数器解释受限资源，必要时覆盖热点 shape 分布与不同 rank。
以下采集说明用于定义交给 Profiling Skill 的补证任务，不意味着本分析 Skill 可自行重启服务、启动 workload 或采集。
保留原始报告、导出数据、过滤条件、工具版本、命令和采集范围；抽样热点的结果不得标成全阶段覆盖。

| 数据 | 首选依据 | 不能替代它的数据 |
|---|---|---|
| 设备 kernel/range 时间与关键路径 | 设备时间线、适用的设备计时或 profiler workload duration | CPU dispatch 时间、HTTP 时长、重叠活动时间之和 |
| HBM 读写量 | 实际 DRAM/HBM 硬件字节计数器及其范围定义 | 显存占用、分配量、张量 `numel × bytes`、global load/store 请求量 |
| 执行 FLOPs `F_exec` | 匹配指令路径的工具统计或可核验的指令语义换算 | 任意 SM 利用率、Tensor 指令数乘固定常数 |
| 算法 FLOPs `F_algo` | 实际 shape、有效工作量与算法公式 | 总参数量近似对所有模型/阶段通用套用 |
| 算力/带宽屋顶 | 同运行条件的规格上限及可选持续能力校准 | 另一个平台、精度、稀疏模式、分区或功率状态的峰值 |

### NVIDIA 的发现与采集示例

先在获准环境查询，结果留在外部产物中：

```bash
ncu --version
ncu --list-sections
ncu --query-metrics
```

候选指标示例；只有当前版本和 GPU 明确支持时才能采用，需保存实际名称、单位、聚合方式与含义：

| 候选指标 | 解释 |
|---|---|
| `dram__bytes_read.sum` / `dram__bytes_write.sum` | 被测 workload 的 DRAM 读/写字节 |
| `dram__bytes.sum` | DRAM 总字节；核实是否等于所选读写项之和 |
| `gpu__time_duration.sum` | 被测 workload 的时间；核对导出单位 |
| `dram__throughput.avg.pct_of_peak_sustained_elapsed` | 工具定义的持续峰值百分比，记录其分母口径 |

以下仅为已有 `decode` NVTX push/pop range 的命令结构示例；占位符须按已核实入口替换，不能原样执行：

```text
ncu --target-processes all --nvtx --nvtx-include "decode/" \
  --section SpeedOfLight --section MemoryWorkloadAnalysis \
  --section SpeedOfLight_RooflineChart \
  -o <外部唯一报告路径> <已核实的推理进程启动命令与参数>
```

按任务预算进一步限定 kernel/launch/range，验证子进程、rank、graph 覆盖和实际命中。
Tensor Core kernel 要选择安装版本支持且与该精度匹配的 Tensor Roofline section；普通 FP32/FP64 图不能代替它。
示例不提供任意运行中服务的自动接管或重启能力，服务调整仍按原有委派与生命周期规则执行。

其他平台先核实厂商工具、芯片和当前安装版本支持的计数器/范围/导出方式，建立同语义映射。
不把 NVIDIA 指标名、NVTX 或 CUDA replay 参数直接移植到 MetaX、PPU、Ascend、Hygon、Moore Threads。
现有项目 profiling runner 的 trace 校验不等于已经采到 FLOPs/HBM 计数器；没有原始报告时不能写“实测”。
计数器不可用、权限不足或工具不支持时，记录具体缺口、已有 trace 和替代依据；不自动安装工具或放宽权限。
可用 shape 估算 FLOPs、最低流量与设备计时提出候选，但标记 `estimated`；无法确定的项留 `unknown/incomplete`。
缺口只限制相应归因/效率声明，不阻止依据独立有效证据开展已授权实验；既有正确性与性能验收要求保持有效。

仅缺计数器时保留现有有效时间线，由主协调者派发 Profiling 的 native report 补证分支；不重新运行 trace runner 来满足 counter 请求。
原生报告单独核验指标/单位、调用范围、rank/shape、计时、graph/backend 与采集条件，并记录与旧时间线的关联依据。
相同或覆盖该需求的任务在途时引用原任务回收点；已确认能力缺口或补证无新增有效数据时返回有边界结论与重新打开条件。
去重、局部失效和原调用返回点统一见 [SOP C5](../../../docs/performance-optimization-sop.md#c5-用-roofline-连接瓶颈证据与下一步实验)，不因跨 Skill 交接启动第二份采集或重置总预算。

## 3. 统一 FLOPs、流量、时间和屋顶的口径

**FLOPs。** 一次乘加按 2 FLOPs；GEMM 的算法量约为 `2MNK`，注明 batch/层/调用次数。
Attention 按实际 query-key 对、causal mask、已有前缀与算法计算；MoE 使用实际路由、激活专家及执行 shape。
`2 × 参数量 × token` 仅作适用稠密线性层的粗估，不覆盖 Attention、稀疏路由和所有辅助操作。
同时保留 `F_algo` 与可获得的 `F_exec`；padding、重算、分块冗余和融合可能使两者不同。
指令换算要核对矩阵形状、warp/thread 计数方式、精度和稀疏语义，不能用任意固定倍数统计 Tensor FLOPs。
整数运算按其操作单位另列，不强行混成浮点 FLOPs；softmax 等特殊函数与矩阵单元也有不同上限。
PyTorch `with_flops` 是部分算子的公式估算；`profile_memory` 是分配统计，均不能补全融合 kernel 的硬件计数。

**流量。** `Q_HBM = Q_read + Q_write`，使用实际字节且统一十进制 GB/TB 或明确 GiB/TiB 换算。
权重、KV、临时张量、重复读取和写回都可能贡献流量；实际值不保证等于理论最小值。
L2/L1 命中可能使 HBM 流量小于逻辑访问量；分层 Roofline 使用各层自己的字节数和带宽。
不能把 HBM/L2/global 请求计数相加后仍称 HBM 流量，也不把 PCIe/NVLink 通信字节冒充 HBM 计数。

**时间。** FLOPs、字节数和 duration 必须属于同一 workload 范围与可比采集条件。
kernel 图使用 kernel duration；阶段视图另用该阶段完整设备窗口，计入窗口内空隙并注明是否含通信/拷贝。
跨流设备忙碌时间可用活动区间并集；阶段 elapsed 使用包含间隙的完整窗口，结合依赖关键路径解释，不能用 duration 之和代替。
跨工具/跨轮关联要验证调用身份、实际 shape、顺序、缓存和时钟一致性；无法验证时分别报告，不能拼成“实测效率”。

**屋顶。** `C` 匹配 BF16/FP16/FP8/FP32、Tensor/普通计算单元、dense/sparse、设备分区和实际资源数。
`B` 匹配 HBM 层级、设备分区与运行条件；记录来源、日期、时钟/功率设置及规格峰值或持续校准值。
可同时报告规格屋顶与经验屋顶，不用当前低效 kernel 自身的速率定义峰值；也不为校准擅自启动新 workload。
未使用稀疏计算不能采用稀疏宣传算力。不同精度/执行单元分别作图，不能把所有 FLOPs 套最高 Tensor 峰值。

## 4. 计算距离，并核对聚合的局限

对口径一致的单个 kernel 或有效 range：

```text
I_HBM = F_exec / Q_HBM                         # FLOP/Byte
P = F_exec / t                                # FLOP/s
BW = Q_HBM / t                                # Byte/s
I_ridge = C / B
P_roof = min(C, B × I_HBM)
eta_roof = P / P_roof
U_HBM = BW / B
t_lower = max(F_exec / C, Q_HBM / B)
```

只有 `F_algo` 时，可计算明确标注的算法/有用工作量 Roofline 估计，不冒充硬件执行效率。
零 FLOPs、零流量、缺失计数或只做 copy/collective 的范围不强算比值，改用适用的带宽/延迟分析。
`1/eta_roof` 只是固定工作量、固定流量及该屋顶模型下的理想加速空间，不是预期端到端加速比。
接近带宽屋顶仍可通过减少字节数改善；高执行 FLOPs 利用率也可能是在高效执行无效 padding。
效率超过 100% 时先核查单位、匹配范围、峰值、FLOPs 和 replay 条件，不直接宣称突破硬件上限。

阶段聚合使用同一设备范围内完整且不重复的 `ΣF`、`ΣQ` 和阶段 elapsed；有缺失的 copy/通信/worker 要注明。
不对各 kernel 的计算强度、带宽百分比或 Roofline 效率做算术平均，也不乘 replay 次数重复累计逻辑调用。
将高效 kernel 与阶段间隙分开；多卡分别看慢 rank、通信重叠与关键路径，不能汇总所有卡的峰值后掩盖不均衡。
异构计算单元和不同瓶颈串联时，单个阶段总量 Roofline 只是粗下界；继续分解热点与依赖，不能据此判定根因。

### 假设算例（不是设备实测）

假设匹配计算路径的 `C = 100 TFLOP/s`、`B = 2 TB/s`，且计量范围完整、没有并发归属歧义：

| 指标 | Prefill 窗口 | Decode 窗口 |
|---|---:|---:|
| `F_exec` | 10 TFLOPs | 14 GFLOPs |
| `Q_HBM` | 20 GB | 16 GB |
| `t` | 125 ms | 10 ms |
| `I_HBM` | 500 FLOP/Byte | 0.875 FLOP/Byte |
| `P` | 80 TFLOP/s | 1.4 TFLOP/s |
| `BW / B` | 8% | 80% |
| `P_roof` | 100 TFLOP/s | 1.75 TFLOP/s |
| `eta_roof` | 80% | 80% |

Prefill 的算力屋顶较低，Decode 的 HBM 屋顶较低；后者只有 1.4% 峰值算力也不代表实现低效。
两者还需分解到热点与关键路径，并通过干预实验确认；不能把“Prefill 算力受限、Decode 带宽受限”当作模型定律。
batch、chunk、上下文长度、GQA/KV 精度、前缀命中和 graph padding 都可能改变这个判断。

## 5. 从证据选择下一步实验

| 观察到的证据组合 | 优先候选与分类 | 首个可证伪实验及守护项 |
|---|---|---|
| 热点 `I < I_ridge`、HBM 接近屋顶且位于关键路径 | 减少冗余 copy/KV 搬运（`framework`）；已有更少流量实现（`operator/replace`）；融合/复用（`operator/improve`） | 固定 shape 只改一项；检查 `Q` 是否下降、完整调用是否变快；守护临时内存、数值和 Mixed ITL |
| GEMM `I > I_ridge`、计算管线接近对应屋顶 | 比较已有 backend（`operator/replace`）；减少无效工作、布局或 tile 改善（`operator/improve`） | 固定 dtype/shape 对比完整调用，核验有用/执行 FLOPs、实际命中及转换成本；守护 Decode |
| 计算和 HBM 都低，kernel 内等待高 | 并行度、依赖链、L2/shared、指令吞吐与访存并发（`operator/improve`） | 只变一个资源/布局参数，用 occupancy/stall/分层计数检验；不能直接断言 HBM 已跑满 |
| kernel 内效率高，但阶段有明显空隙或无效 padding | graph、主机同步、调度/batch 与执行组织（`framework`） | 一项配置或限域改动，核验间隙/有效 token 与原始 shape；守护 KV 容量、TTFT/ITL |
| HBM 字节随上下文显著增长，Attention 成为关键路径热点 | KV 访问 backend（`operator/replace`）或布局/融合（`operator/improve`） | 固定上下文、batch、KV dtype 比较完整调用；量化需独立数值/精度验证，不默认修改权重或 tokenizer |
| 慢 rank、collective 或通信组织支配关键路径 | 通信组织/并行布局（`framework`），已有 collective 替换（`operator/replace`） | 保持授权资源预算，隔离一项改变；记录各 rank 工作量、通信与重叠，不用 HBM 图解释全部通信 |
| 仅 Mixed 中 Decode ITL 恶化 | chunk、token 预算或调度（`framework`） | 固定混合到达序列只扫一项；共同看 TTFT、ITL、吞吐和排队，不能只优化阶段均值 |

每个方向至少保留一种竞争解释。按关键路径贡献、可消除比例、生产 shape 命中率、证据强度、成本和风险排序。
大 batch 改善权重复用可能恶化单请求时延、KV 容量或排队；短输入/缓存前缀后的 Prefill 也可能像 Decode。
算子方案返回主协调者，由其复用已有算子任务或另派 `$key-operator-opt` 并检查 SOP C4 的编译器能力候选；不从子分析反向重启调用者。框架与算子组合拆成关联实验，不相加收益。
先验证数值/dispatch 与目标 graph capture、至少两次 replay，再按既有精度触发规则和无 profiler 性能 Skill 晋级。
比较包含转换、临时张量、同步、通信与 dispatch 的完整成本，阶段专项必须回到当前目标 Mixed 验证并守护另一阶段。
保留改动后检查热点迁移；必要时 `reprofile`，并在规划复盘中更新 Roofline 假设、证据缺口和下一轮排名。

## 6. 测量扰动和落盘要求

Nsight Compute 可能多 pass replay、清缓存、控制时钟或串行 kernel，使流量与时序偏离真实服务。
graph/concurrent workload 应按实际版本选择适用的 graph/range replay；某些模式不能提供所需指令计数。
记录 replay/cache/clock、并发、JIT/graph 和预热设置；跨候选保持一致，或者将变化明确列为实验变量。
`cache-control none` 不保证 replay 状态天然等同服务现场；动态路由、KV 更新及应用重跑也要检查可复现性。
profile-on 的时间和无 profiler 正式结果分别保存，不能用采集后的加速/减速直接声明性能收益。

在同一个 `optimize/<experiment-id>.md` 及已有结构化记录的证据扩展中保存下表内容，不新增强制 YAML schema、逐 trace 文档或业务账本：

| 最小记录项 | 内容 |
|---|---|
| 绑定与范围 | scenario、baseline/candidate、服务/revision、rank/worker/device、阶段边界、shape/调用数、覆盖与采样缺口 |
| 采集依据 | 工具/版本、实际指标与单位、命令和原生报告外部路径/SHA、replay/cache/clock、预热与 graph 设置 |
| 量与口径 | `F_algo/F_exec` 来源、`Q_read/Q_write`、时间及范围、`C/B` 来源与精度/单元/分区；各项 measured/estimated/unknown |
| 计算与解释 | `I/P/BW/U_HBM/P_roof/eta`、kernel 与阶段差异、关键路径、竞争解释和可信范围；不适用值留空并解释 |
| 决策与回验 | 分类、目标机制、首个单变量实验、成功/停止条件、另一阶段守护、Mixed 与正确性/graph/正式性能证据及缺口 |

原始计数器、trace、报告和脚本留在批准的外部产物位置；只把摘要、稳定身份和链接写回项目既有记录。
未执行的采集、缺失的 rank 或不可用的计数器保持未完成，不追补虚构的 Roofline 通过结论。

## 官方资料与复核入口

- [Nsight Compute CLI](https://docs.nvidia.com/nsight-compute/NsightComputeCli/index.html)：发现 section/metrics、范围过滤与报告导出。
- [Nsight Compute Profiling Guide](https://docs.nvidia.com/nsight-compute/ProfilingGuide/)：计数器、Tensor/分层 Roofline、replay、缓存与时钟影响。
- [PyTorch Profiler](https://docs.pytorch.org/docs/stable/profiler)：部分算子 FLOPs 估算与内存分配统计边界。
- [vLLM profiling](https://docs.vllm.ai/en/stable/contributing/profiling/)：引擎采集入口；按实际安装版本核实参数与 worker/graph 行为。

以上动态入口于 2026-11-12 作为方法依据核对，不能作为目标机器已安装/已支持或已经完成测量的证明。
