# analysis002：1K/1K 稳态静态优化候选

用户2026-10-21明确：不重点优化初轮，主目标为稳态端到端性能；随后选择“暂不提供GPU，先做静态分析”。本轮遵循该范围，不启动新GPU探针、压测或精度任务，不修改生产源码，不提交/推送。已有独立18144服务已停止，readiness等待已取消。新容器保留用于将来验证；当前源容器及其启动脚本不变。

## 当前事实与阶段边界

当前源qwen3vl-p64k-opt-20261015；FlagGems gems-opt/c3c5f5ab2，FGV f6fdb9b加既有MoE/采样，Plugin08da21c加通用采样adapter，vLLMee0da84。当前MoE原文件SHA faeeead6...，PR943收敛版没有回写，不能把它当作当前性能变量。sampler默认temperature0.7、topk20、topp0.8。原blacklist mm,mm_out,layer_norm,log_softmax保持，禁止以新增关闭FlagGems来优化。

模型48层；H2048、128experts、topk8、完整I768，TP2后每rank I384。每rank w1=(128,768,2048)、w2=(128,2048,384)。attention整模32Q/4KV heads、head_dim128，TP2理论16Q/2KV heads；实际attention backend与kernel未运行取证，保持unknown。

| 阶段 | 当前证据 | 不能据此推出 |
| --- | --- | --- |
| Prefill | opt9后两轮SUMMARY meanTTFT3200.09ms，P99 10151.92ms | 含排队/网络/调度，非纯Prefill设备时长 |
| Decode | medianITL39.46ms，meanTPOT50.71ms，P99TPOT66.62ms | 没有当前trace，不能断言MoE/采样/通信谁占主导 |
| Mixed | 三轮941.46/1005/1069.49tok/s，历史SUMMARY1037.24取后两轮 | 没有预先稳态准入与完整原生结果，不能追认新基线或算因果收益 |

第一轮高TTFT只作为历史现象，不列为当前优化目标。后两轮吞吐差幅约6.2%，也不能靠剔除较慢轮获得收益。当前没有新性能结果，旧sort优化1357TPS与opt9不是单变量系列，不能直接计算本轮退化贡献。

## 已核对的采样调用链

vLLM Sampler对FP32 logits做temperature除法 → TopKTopPSampler.forward_native → Plugin通用`vllm_fl/ops/sampler.py` wrapper → `dispatch/backends/flaggems/impl/sampler.py` → FlagGems-vllm包级已绑定MetaX `apply_top_k_top_p`。不支持metadata才走原native_filter；M>64也在不支持范围。库内部引用FlagGems sort的histogram/sweep及FlagGems softmax/cumsum。源码路径证明实现关系，不能替代本轮worker命中和profile占比。

主要源码锚点（均容器/workspace下；原文和SHA见远端static-source-audit）：

- `FlagGems-vllm/src/flaggems_vllm/runtime/backend/_metax/ops/top_k_top_p.py:44`，`_count_bf16`；:86/:109为guarded hist/sweep；:140 `_sorted_values`；:321 public入口；:273稳定threshold/ties mask。
- `FlagGems/src/flag_gems/ops/sort.py:111`，global histogram；:159 sweep；:258 radix_sort；:383默认4bit选择。
- `vllm/vllm/v1/sample/sampler.py:228` temperature；`vllm/vllm/v1/sample/ops/topk_topp_sampler.py:135`过滤调用。
- `FlagGems-vllm/.../_metax/ops/fused_moe.py:625` retained表；:2570附近align；:2590融合与配置；:2665 GEMM2选择。

## 优先级1：跳过最终不会使用的 BF16 计数更新

**源码事实**：`_count_bf16`对每个256元素block计算非精确BF16元素数bad，随后无条件atomic_max(invalid,bad)，并对每个有效元素无条件atomic_add到BF16 counts。`_sorted_values`随后无条件做counts前缀和。只要全批次任意bad>0，global invalid非零，后续guarded radix执行，而`_expand_counted`不执行；此时BF16 counts/prefix不参与排序输出。

M64/V151936时，此计数kernel有38016个CTA，语义上有9723904个元素级计数更新机会，并共享一个invalid标记。编译器可能聚合原子操作，所以这不是实测硬件指令数或时间。FP32温度除法通常破坏BF16精确表示，说明该路径值得观察；**未采实际logits/invalid，不能声称当前每一步必然走radix**。

**最小候选**：block bad==0时才构建BF16 counts；bad>0时只更新invalid，不写该block的counts。invalid在调用前清零，因此全精确BF16输入可省掉bad=0的global atomic_max。保留所有后续既有FlagGems和radix路径。

```python
# 候选逻辑示意；未写入产品代码。
if bad != 0:
    tl.atomic_max(invalid, bad, sem="relaxed")
else:
    # 原有raw/key转换与counts atomic_add
    ...
```

**静态等价性条件**：若所有block均bad=0，counts与原路径完全相同、invalid仍为0；若任一block bad>0，global invalid最终仍非零，原radix路径独立于counts，跳过这些计数不影响输出。kernel完成后才读取invalid，不增加host同步。NaN按既有比较进入radix，Inf/signedzero行为由既有判断保留。没有降低dtype、改变top-k/top-p、改变RNG或关闭FlagGems。该推理只覆盖源码数据依赖，不能替代编译/并发/graph/GPU数值验证。

**首个证伪**：冻结其余全部参数，仅改这一kernel；M1/7/8/32/63/64、V尾部、全精确BF16、temperature-scaled FP32、同batch/同block混合输入、NaN/Inf/±0、重复阈值、k/p边界，完整过滤输出mask与原实现逐位对照；capture+变化输入至少两次replay。采实际guard分布及GPU时间，完整采样graph≥5%改善且支持shape不明显退化后进入同P1K/D256/C64/N128 milestone；再回父目标P1K/D1024/C64/N128 B/C/R，主吞吐≥2%、P99TTFT/TPOT/ITL≤10%退化、spread/漂移≤8%。任何mask/graph差异立即停。**收益unknown，没有部署候选。**

## 优先级2：保持4bit/8passes，比较 sweep 的桶分组

当前values-only sweep参数TILE_R=8，16bins拆成gridR=2，每个组都load相同输入tile；M64/V151936有75个N tile，因此每pass9600CTA、8pass共76800CTA。候选TILE_R=16并把gridR设1时为38400CTA，消除一组重复输入load，保持4bit、8passes、排序和tie数学不变。

静态逻辑读取请求从622329856B变311164928B；输出请求都为311164928B。两者合计逻辑请求可下降约1/3。这里没有测缓存命中/DRAM流量/运行时间；CTA串行bin循环翻倍、寄存器/占用率与decoupled-lookback进度可能抵消，必须检查实际编译资源和死锁边界。原FlagGems sweep仍是实际实现；不引入另一个vendor backend或torch fallback。

首个实验仅单一TILE_R/对应grid一致变化，完整values-only sort+mask逐位oracle及变化输入graph；固定路由/data交错B/C/R微测，之后再走相同Mixed契约。任何编译/进度/数值或E2E回退即停止。该候选与优先级1分开测量，不合并归因。

**不优先做8bit/4passes**：保持TILE_R8时，256bins意味着gridR32；每pass153600CTA、4passes614400CTA，反而是当前8倍。逻辑输入请求约4.98GB（当前0.62GB），status16倍；global histogram也把16bin循环扩大为256bin。不能从pass减半推出更快。此外`_hist_prefix`把bin范围硬编码为16，8bit方案还需同步调整prefix与scratch布局，不能直接改一个bit参数。后续只有重新设计hist/sweep数据复用并获得证据时再考虑。

## 优先级3：小K时缩小 softmax/cumsum 的有效范围

当前topk20后仍在V151936全行上执行softmax/cumsum，存在大零区域的工作。但top-k threshold会保留所有边界ties，存活数量可能超过20；top-p的CDF舍入和stable tie截断也必须一致。不能简单切最后20个元素。若前两个候选仍留下显著CDF热点，再设计带设备端tie范围guard和原fallback的紧凑实现；先证明概率/累计边界与原输出mask，再谈性能，不能直接近似。

## 暂缓方向与原因

- MoE已有当前G1/G2分阶段参数，SiLU已融合。M64共512routed rows、平均每专家4，BM16存在padding；均匀且token内topk不重复的解析模型给出期望padding约3.94倍，**不是真实路由、实际FLOPs或可兑现收益**。此前同shape BM8编译失败；两轮tile搜索完整MoE最好约1.03×，未过5%门槛。获得新trace前，不重复大范围tile/stage搜索，不更改当前参数。
- 已有maxseq64/graph64；增加maxseq会越过当前采样M<=64范围，并改变graph/配置覆盖。先核实shape和backend，不能当成无成本吞吐提升。
- P1K/C64并发理论KV上界约131072tokens；此前记录KV562992仅为历史参考，当前服务未就绪所以不填写运行时容量。没有当前抢占证据，不优先提高显存预算。
- 去掉M constexpr只影响新shape/JIT及warmup，不作为本轮稳态首选；buffer缓存或一般Python重构也先等host-gap证据。保持sampling/gems-opt/MoE/blacklist和vLLM源码。

## 当前结论与恢复入口

资源限制下，本轮只完成代码事实、形状预算和候选排序。当前Prefill/Decode/Mixed设备热点、guard命中率和净吞吐收益均unknown。未执行新的GPU正确性、graph、profiling或性能对照，不宣称优化完成或PR-ready。

提供两张独占卡后：重新核对host/source/card → 新role/run-id启动（旧baseline失败证据不可覆盖）→ graph/C8及固定shape预热 → 无profiler稳态入口baseline和三阶段trace → 按当前热点证伪优先级1 → 单变量B/C/R及必要回退 → 验证后才回写当前容器。正式GPQA继续按用户暂缓指令，不签验收gate。

源与独立容器四仓库源码、HEAD及工作区状态均与初始快照一致。审计回执：`/public-flash/jinghao/qwen3-VL/20261021-qwen3vl-metax-p1k-opt9/results/static-source-audit.json`，SHA256 `2ef431eefa051c7d65b821ec836b1568304b5965b834364b78e71dfe9aac11c8`。纯CPU形状/逻辑流量计算：远端`commands/static-metrics.json`，SHA256 `f52408192f3de16f7d45da8832177ba851be75e971682267ca450ebc22a82e90`。
