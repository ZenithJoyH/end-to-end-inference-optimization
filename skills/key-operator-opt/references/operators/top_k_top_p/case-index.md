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


## 20261027 Qwen3.6-35B / MetaX：接口迁移丢失 shortlist 快路径

- 完整记录：[blacklist-gap-001](../../../../../models/qwen3.6-35b-a3b/metax/20261022-qwen36-35b-mx104-stack-regression/optimize/blacklist-gap-001.md)。诊断状态completed；修复not-proven/未实施。证据reproduced，非跨平台。
- 环境：Qwen3.6-35B-A3B BF16，C550/TP2/mx-104；vLLMbc150f5，Plugin1bc0c77+本地适配，FGVe1a02b6+MetaX filter dcfa764e；Gems5.5dev/a456722a，FlagTree0.7/fe1d24f6，模型FULL_DECODE_ONLY graph；采样在模型graph外。
- 路径/shape：旧Plugin shortlist64 → 当前FGV `apply_top_k_top_p` 全词表排序；Decode FP32 contiguous[64,248320]，k20/p.95，BF16 logits转FP32后温度0.6缩放触发generalFP32 radix。
- 瓶颈证据：三臂两rank共六trace，每份64个cached64 Decode步骤、softmax实际[64,248320]；每步8次_guarded_sweep累计约7.84ms/rank。累计设备活动不是关键路径百分比，rank不相加。
- 隔离变量：当前依赖不变，黑名单/旧白名单/黑名单短程P1K/D128/C64/N64；不修改源码。输出920.39/933.43/911.52tok/s，白名单恢复1.91%，B返回漂移-0.964%；六计时轮和九预热轮全保留，预冻结8%变异/漂移条件通过。这个差异不是历史完整D1024 gap的精确分摊。
- 算子：同currentGems和primitive白名单，新FGV/旧shortlist/新FGV，两个固定seed；M64/V248320/k20/p.95/temp.6，完整filter wall约10.58/2.30/10.58ms，增加8.28ms。旧CPU validity同步计入，resetcopy不计时。
- 正确性：两输入过滤掩码差异0、保留值差异0、旧fallback0；未做新完整GPQA，不声称所有tie/边界/graph语义已验证。旧实现bool(valid.all())含CPU同步，不能直接无条件复制进库。
- 决策：生产源码、FGV MoE调优/GDN保持；原完整env/argv/cwd/黑名单/无profiler服务恢复，9667源码哈希不变。下一候选是在FGV公共接口内建立有保护shortlist并证明实际top-k backend；未实施/无新gate。
- 知识差量refined：API迁移不等于保留算法复杂度；先核验历史专项快路径和温度后的值域，再隔离白黑名单/版本。当前黑名单还会注册Gems topk，复用torch.topk时必须重新证明实现，不能假设仍为原native快路径。
- 限制：历史两目录同时变化库/编译器/采样器且无精确旧launchmanifest；仅短程同配置政策隔离与算子/trace归因，未完成修复后原workload E2E或formalGPQA。
