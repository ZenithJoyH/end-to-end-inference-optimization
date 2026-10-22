# Sampling 证据卡

## 20261021 Qwen3-VL / MetaX C550

- 完整记录：[op005](../../../../../models/Qwen3-VL-30B-A3B-Instruct/metax/20261021-qwen3vl-metax-p1k-opt9/optimize/op-005-sampling-local-histogram.md)。状态kept，证据reproduced。
- 环境：Qwen3-VL-30B-A3B-Instruct，TP2，C550，graph服务；vLLMee0da84，Plugin08da21c加既有采样适配，FVf6fdb9b加既有MoE/采样，FlagGems gems-opt/c3c5f5ab2，FlagTree3.6.0。具体SHA/补丁见案例。
- 路径：Plugin通用FlagGems适配 → FlagGems-vllm MetaX `apply_top_k_top_p`；FP32 contiguous，热点M64/V151936，temperature0.7使实际请求走radix。采样位于Decode并由Mixed验证。
- 瓶颈：双rank阶段trace实际命中；rank0 histogram64次累计81.156ms，MoE仍为前置最大设备累计项。累计时长不作关键路径。
- 唯一保留变量：`_guarded_hist`用masked局部整数histogram代替逐桶比较，原8轮4bit排序及浮点/RNG不变；沿用原metadata/fallback范围。
- 算子：M64非BF16完整采样7.528→6.470ms，speedup1.1635×；不是模型加速比。
- E2E：P1024/D1024/C64/N128，3warm+2measure，中位B1455/C1510/R1485tok/s；+3.76%vsB、+1.67%vsR，B/R漂移2.06%。全部计时轮保留，128/128成功，守护通过；不声明稳定孤立3.8%。
- 正确性：47组输入/129过滤对拍逐位通过，5算子capture/20变化输入replay；三个TP2实例graph及请求回归通过。正式GPQA按用户要求未跑。
- 反例：计数跳过仅约3%完整算子收益；桶分组16未加速M64且M1回归约24%，均未保留。
- 知识差量：refined/contradicted。逻辑工作量不足以排序候选；先证实际BF16/radix分支和hist/sweep占比，再测完整算子和E2E。小收益必须同时展示回退漂移。
- 限制：单C550/当前版本/单P1K；无其他平台、正式精度、四场景验收或长期容量结论。源码已回写，生产9999须下次重启导入。
