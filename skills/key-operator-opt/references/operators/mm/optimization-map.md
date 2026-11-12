# MM 调参诊断地图

## PPU Mixed新形状导致在线搜索

| 字段 | 限域决策 |
| --- | --- |
| 信号 | 请求中大量LibTuner/default_policy/_bench，RPC约300s超时；不能只凭sample_tokens超时报采样器故障 |
| 匹配键 | FlagGems当前PPU MM/BF16/NT、多投影M20481/8198，graph服务Prefill；版本必须重查，不套用其他平台 |
| 机制 | Config bucket冷缺失后，逐raw-key/config读取benchmark缓存；114候选经合法性裁剪仍104，缺少已验证的生产搜索预算 |
| 首个检查 | CPU执行真实get_key/get_benchmark_key和prune；只读前后DB行差分，验证是否新key、namespace不一致或实际丢失，三者不能混称缓存问题 |
| 首个实验 | 冻结同初始SQL缓存之外，还要冻结kernel shape序列和实际输入hash；先用固定shape Default/有界/Default确认搜索预算，保留完整key、合法性和Expanded，再做原范围模型回归 |
| 通过证据 | 实际策略命中，原C8及C64最小回归、数值边界、FULL捕获/至少两次回放；新正式gate后才有性能晋级，不把CPU减少候选当端到端加速 |
| 停止条件 | 数值/graph/服务失败即停；禁止延长RPC、降MBT、放宽key或重复暖缓存至通过来替代因果验证 |
| 证据等级 | reproduced机制，修复/充分因果待验证；不同warmup/rep的custom协议tag碰撞是独立风险，不能夹带归因 |
| 来源 | [GLM点51证据卡](case-index.md) |

反例边界：同HTTP P4096/C8和SQL快照，真实冷M仍可为12293、28673或20481+8198，三臂无共同冷shape。候选真实104→4命中并通过C8，不足以将237.6→58.9s认定为稳态收益；原策略一轮过、回退RPC失败时先比较冷shape组数，不盲重跑到稳定。

## MetaX BF16→FP32投影：高层router primitive绕过NT vendor

| 字段 | 限域决策 |
| --- | --- |
| 信号 | FP32投影父调用下同时出现转置clone/copy与`mm_kernel_general`；不能仅按算子名认定只属MoE gate |
| 匹配键 | MetaX C550、当前Torch2.10/MACA及FlagTree3.6；BF16 x[M,K]、weight[N,K]，FP32输出；实测M4096/64、N512/1024/2048、K4096及边界layout；版本/导入必须重查 |
| 机制 | `weight.t().contiguous()`实体化与通用MM；公开ATen/vendor mm_out已替换，独立router_gemm仍可能通用，二者不能混称“MetaX已命中” |
| 首个检查 | CPU父调用、输出dtype、真实函数源SHA/注册key、Input Dims/Strides、GPU kernel；同文件可能以两个模块名导入，不以函数对象identity否定来源 |
| 首个实验 | 同X/W依次比较旧通用、无copy通用NT、公开vendor NT、FGV、native BF16-input/FP32-output；覆盖pitched、非对齐、空M/N、fake/AOT和两次changed-input graph；不得以BF16输出换速度 |
| 通过证据 | 目标模型每rank真实native op/MCBLAS命中且旧路径消失；最小模型回归、精度gate及无profiler父P32全部3轮。微测与profiler累计时长不作E2E倍率 |
| 停止条件 | 输出语义改变、fallback冒充命中、共享内存超卡限、graph/数值失败、跨阶段退化；保留原fallback与未测平台边界，不全局切换所有MM |
| 预热反例 | 新隔离Triton缓存首轮冷编译不能当稳态分母；同一窗口稳定仍可能在新rawM出现JIT。保留全部测量轮，逐轮记录编译类型，不把非copy/GEMM的新编译说成原copy复发 |
| 证据等级 | reproduced，仅该MetaX版本和模型；原镜像正式baseline缺失、第三轮残余7项shapeJIT、四场景及其他硬件尚未通过 |
| 来源 | [DeepSeek MetaX op004证据卡](case-index.md) |

该案例将后续首个检查从“prefer/vendor配置是否正确”收敛到“当前高层primitive实际调用、FP32契约和转置布局”。native并非所有shape/平台默认更快；限域数据不能替代新目标实测。M2092尾批特化仅是下一可证伪方向，不是已修复结论。


## 原始形状编译消除后仍有NT慢段

匹配本卡的MetaX C550/TP8/P32/当前FG版本：[op005证据卡](case-index.md#deepseek-v4-flash--metax去除量化等边界特化后残余nt编译仍在)。先分清FP32-output native投影与BF16-output FG NT的实际provider；前者已接入vendor不说明所有GEMM都绕过FG。

首个证伪：把新增binary的真实IR/runtime参数、tile/EVEN配置、有效M/N/K和stride与慢段对齐，再采集ConfigCache/BenchmarkCache miss、候选数量及bench_time。源码存在benchmark分支不是实际命中证明，runtime M也不代表没有合法的对齐/tile特化。

若只取消不决定算法的bounds特化，应同时核对Python launch/libentry键；shape-dependent heuristic结果仍须进入键。不得在EVEN_M依赖M且被libentry缓存时直接取消M特化，否则可能复用不带mask的tile。保留所有已准入测量轮；5%标量波动通过与完全预编译覆盖是不同范围。本卡后者仍incomplete，未获因果证据前不关闭剩余第三轮慢段。

## MetaX NT：区分候选编译、配置miss与执行配置

| 项目 | 当前限域决策 |
|---|---|
| 匹配键 | [op006证据卡](case-index.md#deepseek-v4-flash--metaxnt候选试跑与configcache分桶)的C550/TP8/BF16 dense NT N64 K4096 M<=4096、当前FG版本、graph服务Mixed |
| 信号/机制 | runtime M内核仍新增多种tile binary；Default精确M ConfigCache miss可触发每rank6次请求期benchmark，新增binary可能是未被选中的候选。缺少可选CM依赖只解释fallback，不能直接等于本次实际bench。 |
| 首个证伪 | 记录实际M/N/K/dtype/stride、Default/Expanded/CM mode、ConfigCache与raw BenchmarkCache key、命中/实际bench计数及winner；把候选与binary配置逐项匹配，rank时间重叠不求和。 |
| 候选/通过 | Default log-M有界配置选择+显式准备服务有限shape域；保持原始训练标签、实际M的LibEntry/EVEN条件。清本算子进程内cache后遍历完整域，无新binary/bench；同tile新旧及changed-input graph逐位一致，独立FP64 oracle、fresh fullGPQA及无profiler父Mixed三轮通过。 |
| 停止/范围 | 未知layout/dtype/NK/设备/显式策略不假定已准备；跨tile byte差先定位舍入与独立误差，不改正式分数阈值。NT0/cache不变与全链路0是不同结论；本卡残余index/mHC2，原镜像正式baseline缺失。 |
| 证据等级 | NT搜索机制与当前有限域修复reproduced，未transfer；旧第三轮确切M与全部31秒延迟没有当时计数，不能逆推出完整因果。 |
