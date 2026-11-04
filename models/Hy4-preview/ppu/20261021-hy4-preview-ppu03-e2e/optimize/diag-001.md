# diag-001 当前 P4K/C64 日志与 batch budget 诊断

本轮只读分析用户 service.log 和当前安装源码、指标，回答 8192 是否优先；不重启、修改参数、发推理请求或开始精度。当前现场已由用户启动8010服务，并运行P4096/D1024/C64/N128；不同于此前8011验证实例。

执行前控制：`/workspace/.hy4-preview-migration-20261018-01/perf-20261021-01/commands/snapshot_perf_diag001.py` SHA `1c216057f94b6063a43b0e4b2e9d5f71934b0356b3b673bf1f8fa59ed8d19b5b`。只在既有案例根新建 `service-log-diag-001` 保存日志快照、源码摘录、GET metrics和当前源清单。

## 当前事实与结论

证据截止 **2026-10-22T18:08:24.622658+08:00**。优化容器`hy4-preview-perf-20261021-01`中用户已重启到端口8010，API实际stdout指向指定`service.log`。当前参数2048、TP16、maxlen100000、FULL_AND_PIECEWISE、capture最大512、prefixOFF。启动日志两类capture均10/10完成；这不替代当前实例16rank两次replay验证。原8011验证结果仅作历史保留。用户当前客户端P4096/D1024/C64/N128、random/ignore_eos，进程仍运行；本Agent没有启动、停止、重跑或混入流量。

源码guard通过：FGV45e14232（原fw002一文件补丁）、FG3ba1d1d9、Plugin env031和默认thead.yaml均与上轮冻结内容相同；原fw001批量range补丁仍未部署。没有代码或库版本变化。

## 阶段视图

| 日志窗口（10月22日，北京时间） | 现场现象 | 解释边界 |
|---|---|---|
| 16:31:27–17:42:28 | 257个吞吐样本、64次prompt记账脉冲，128个generation为0；Running由2逐步到64 | 首波请求准入/Prefill慢，不能把pulse当真实chunk边界 |
| 17:42:38–17:46:08 | 22个连续样本，Running64、Waiting0、prompt记账0，generation243.2–249.6 token/s | Decode主导窗口的日志观测，未用scheduler逐步证明纯Decode |
| 17:46:28–18:04:58 | 69个样本、16次prompt记账脉冲，35个generation为0，其余多为6.2/6.3，最高12.5 token/s | 新Prefill加入与Decode输出停顿高度相关；不证明每个0窗口设备空闲 |

当前KV容量347280token，日志最高93.2%；metrics采样preemptions=0。早期KV仅1.8%时已有停顿，不能把主要问题归为KV耗尽。后续使用率高仍是调大budget的重要守护。快照无ERROR或Traceback；启动时vllm._C/环境变量警告不能直接归因为稳态慢。

## 源码给出的优化方向

当前`vllm_fl/dispatch/backends/flaggems/impl/bf16_indexer.py` SHA仍为`954b3049ed829fd69547fb76ae0f043da0cffa74a5b70885283ddf8097abb8a4`：79–81行把范围转CPU list；84–114行按每个query token循环。范围<=2048时逐行arange/where/copy；范围>2048时逐行matmul、BF16加权归约及TopK。加大token预算不消除这些循环。优先优化无须排名的索引批量构造，再把P4K后半段评分/TopK按有界query-row块组织，分别验证请求边界、causal mask、BF16计算顺序、输出整数索引与临时显存。**尚未测量本轮各支路耗时占比**，旧trace和P1K B/C/R只增强机制证据，不能冒充当前P4K归因。

旧fw001在P1K/C8同参B/C/R曾使Mixed输出10.212→49.416→10.159token/s，但候选未安装，Decode比较incomplete；只覆盖全部range<=2048的完整索引支路。当前P4K含排序支路，不能承诺旧4.84倍，也不能将其与fw002去JIT效果相加。

当前`vllm/v1/cudagraph_dispatcher.py:272–281`在单步num_tokens超过max capture size时返回NONE。配置上限512并不覆盖所有2048/8192-token Prefill；实际步数/命中率仍需有界取证。NONE仅表示该步不replay graph，不表示所有编译失效。按用户既有要求保留capture<=512，本轮不改变。

## 8192判断及下一轮

8192是安装版vLLM0.24.0按显存>=70GiB、非A100等条件选择的API默认之一（`engine/arg_utils.py:2375–2418`），不是HY4/PPU实测最优值。它可能减少Prefill分块、提高单步矩阵利用率，但不能自动提高上述逐行实现的效率，单个Mixed步可能更长、Decode ITL更差。

旧C8/N8对照Mixed输出10.2022→10.1746token/s，TTFT59.58→77.52s；无独立revert、Decode预热未稳，故不能外推当前C64无收益。旧KV容量347152→308701token（约-11.1%）仅为历史观察；本轮64×(4096+1024)=327680token的驻留上界已接近当前347280。若新版8192仍减小容量，可能增加容量等待/抢占，但必须新启动测量，不能把旧容量当现值。

建议顺序：先定位并减少Prefill逐行开销；随后固定源码，以同一workload和稳态准入做2048→8192→2048回退，观察总完成时间、TTFT/TPOT/ITL、KV和实际graph路径。8192是合理候选，现证据不足以直接采用。测试若仍有价值，应提前冻结预算、全部保留测量轮，不因首轮慢临时删除。当前用户benchmark保持运行，本轮只完成分析，不开启新测试或精度。

指标陷阱：iteration_tokens histogram在首次输出记账包含整段prompt，不能据>4096桶认定实际scheduler batch突破2048；prompt0/generation0也不能当作设备空闲或精确Prefill/Decode阶段。最终客户端汇总尚未完成，当前周期日志不作为同参正式性能结果。

## 记录与证据

review-003已写入state，保留旧实验的回退/未完整结论。新归因仍属observation；下轮需要性能Skill的targeted/checkpoint及必要的bounded profiling，当前完整精度禁令保持。无模型源码、两个库、启动脚本、capture列表或服务状态变更。

外部根：`/workspace/.hy4-preview-migration-20261018-01/perf-20261021-01/service-log-diag-001`。

- 日志快照SHA `a29ac180efa93076592e93312b66461ab86f49144b8844efe7532f5ceae00c3f`，830125字节。
- 源清单`source-state.json`、`source-excerpts.json`、启动器、现有客户端、两次metrics和`process.json`由`receipt.json`绑定。
- 本地仅保存本摘要、结构化结论及外部路径；完整日志不进入项目目录。
