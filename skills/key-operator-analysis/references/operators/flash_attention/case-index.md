# Flash Attention 证据卡

## Qwen3-VL / MetaX main.py 对比：先区分 native 与库内 Triton

- 后续性能证据：[op-007](../../../../../models/Qwen3-VL-30B-A3B-Instruct/metax/20261021-qwen3vl-metax-p1k-opt9/optimize/op-007-fa-main-native-micro.md)，micro reproduced/negative，18/18 shape数值与36次变化Q graph检查通过。C550物理GPU2、BF16、Q16/KV2/D128、page16；torch2.8.0+metax3.7.0.7/Triton3.6.0，candidate SHA e2f78d3。native Prefill走varlen、Decode走with_kvcache，比较完整API graph设备时间。9轮native→candidate→native保留全部；12个Decode候选为原生2.02–3.07倍耗时，4个等长Prefill为2.09–3.28倍；B64/KV1K为native66.195/main133.750μs。最大原生前后漂移0.425%，原生各角色散差≤1.38%、候选≤1.06%。候选未部署、GPU2已释放，无E2E或模型精度gate。知识差量contradicted/refined：机制和历史aggregate注释不能替代与现行native的完整调用对照；下述not_run指先前analysis-006阶段。

- case_id：20261021-qwen3vl-metax-p1k-opt9；[analysis-006](../../../../../models/Qwen3-VL-30B-A3B-Instruct/metax/20261021-qwen3vl-metax-p1k-opt9/optimize/analysis-006-main-flash-attention.md)。status：not-proven；源码与既有trace observation、CPU公式 reproduced，GPU候选未测。
- environment：Qwen3-VL-30B-A3B、MetaX、TP2/BF16/graph，Q16/KV2/D128；vLLM ee0da84、Plugin08da21c、FGV f6fdb9b加既有MoE/采样；非目标平台未测。
- operator_path：已有三阶段双rank trace 为 mcFlashAttn native Split-KV/merge；vendor Prefill走varlen、Decode走with_kvcache。库内MetaX Triton源码存在，不构成其服务命中证据。
- bottleneck_evidence：诊断trace记录原生Attention活动；无新稳态关键路径或候选性能证据。
- change：operator/improve候选分析；main.py采用原布局GQA打包、转置计算、D128自适应拆分。未修改源码，无适用guard部署或回退动作。
- results：GPU数值/graph/E2E not_run。显式num_splits只校验不使用；vendor paged-prefill cuK ABI与候选seqused要求不兼容；非因果ALiBi CPU反例为1→1.575210。无模型精度gate。
- knowledge_delta：refined。先确定native varlen/native kvcache/FlagGems三种路径；单tokenDecode原库已GQA打包，长Prefill要连同token跨度分析。不能从“GQA8”直接推导8倍KV流量收益。
- limits：候选历史1.6537仅文件注释，无当前可比结果。接入前须三路同ABI、完整调用、真实页与graph验证；本卡不支持修改默认backend或参数。

## Qwen3.6-27B / MetaX packed GQA Decode

- case_id：20261012-qwen36-27b-metax-flash-attention
- 事实主记录：[组合001](../../../../../models/Qwen3.6-27B/metax/optimize/combo-001-fa-splits-warps.md)、[结构化账本](../../../../../models/Qwen3.6-27B/metax/optimize/state.yml)。
- status：not-proven / reverted；evidence_level：算子 reproduced，阶段服务 observation，Mixed incomplete。
- environment：Qwen3.6-27B、MetaX C550、TP2 BF16、graph；vLLM bc150f502991、Plugin 8b059122e32b、FlagGems-vllm 4ea1b95b80ef 加私有 OP001 / 组合补丁。
- operator_path：Plugin default.flagos → FlagGems-vllm MetaX SplitKV；Decode 每 rank Q12/KV2/D256、GQA6、B64；packed head layout；管理器逻辑页784、真实 kernel 页16（每逻辑页49物理页）。
- bottleneck_evidence：按 worker GPU 范围切分，FA 占 Decode kernel activity 约11.9%；不是关键路径占比。
- change：operator/improve；B64 支持条件下 auto split16→8，N16 的 warps1→2；BF16/paged16/packedGQA6/D256/无CuQ，其他路径 fallback。
- operator_result：真实页16完整 graph API 在 KV1K 延迟下降18.17%，4K/16K/32K下降13.49%/11.73%/10.58%；57项实际源码 GPU/graph、34项 fallback 通过；双 rank 实际8 splits /128 threads 命中。
- end_to_end：三轮 Decode 阶段吞吐 +1.71%、TPOT −2.06%；Prefill 基本不变。候选 Mixed 固定末三预热散差18.03%超过10%，零测量轮，候选回退。原路径回退Mixed散差0.32%、输出漂移−0.11%；Decode输出漂移+0.22%。原生比较另因计划未声明全部决策指标而incomplete，描述性中位数不是comparison通过。
- correctness：CPU FP32 oracle、边界/变长/非连续布局、graph replay、服务 C8；当前50000预算正式 GPQA 158/198低于80%，没有当前正式 gate。
- regressions：N32/W1 206 spills、N32/W2 182 spills，严重负优化；N16/W2为244 regs /0 spills。小 batch 减少 splits 可退化。最初页784 guard 未命中服务，17.55%原型微测不作真实服务收益。
- knowledge_delta：contradicted/refined。日志中的逻辑页不能替代实际 KV tensor 页；资源参数收益不能相加；微测通过不能替代 Mixed 稳态准入。下一次先反向核验真实 tensor、dispatch 与 grid，再设计 shape guard。
- limits：仅该硬件、revision、dtype、packed shape 与诊断 workload；其他平台/模型未测。模型数值根因 unknown，PR experimental，未做最终四场景验收。

## Qwen3-VL / C550 固定前缀的 native kvcache batch数值分歧

- case_id：20261022-qwen3vl-metax-pr977；[diag-005](../../../../../models/Qwen3-VL-30B-A3B-Instruct/metax/20261022-qwen3vl-metax-pr977/optimize/diag-005-fixed-prefix-logits.md)。operator evidence `reproduced`，diag005当时完整模型原GPQA失败未解决；后续op006见下。
- environment：Qwen3-VL BF16/TP2，MetaX C550/mx-59，vLLMee0da84a、Plugin08da21cb、gems-opt c3c5f5ab；FV实际PR943 a1570df/MoE bbc2edded。服务GPU0/1 FULL_AND_PIECEWISE64，独立GPU2重放；native Python接口SHA a0ce682d。
- operator_path：逻辑Prefill缓存命中后的query9被MetaX阈值128归入decode；Plugin vendor.metax → `flash_attn.flash_attn_interface.flash_attn_with_kvcache`。每rank Q16/KV2/D128，page16，P233/cached224/query9，真实batch1/8。
- evidence：同实例capture off/on/off的完整logits/hidden逐位一致；目标完整9query Q与233位置K/V均相同，首层Attention末query输出rank0/1最大差1.22e-4/3.05e-5，随后logits最大差0.3125。FP64误差只作观察，不直接称语义bug。
- change：diagnostic only，未替换backend或修改数值算子；仅保留用户要求的PR943同步。A/B/A只改变batch，组件额外对照num_splits，未应用服务。
- results：按原物理页/storage/stride重建后，双rank实际C1/C8原输出逐位复现。默认num_splits0下同输入batch有差异，固定1时消除；两种batch/默认与固定1共8captures/16replays均等于未capture。默认并未与显式1/2/4完整匹配，不能推断自动实际split数。无E2E或新精度结果。
- negative/control：客户端C8可拆成1+7；跨层缓存的同一RoPE对象会覆写单层hook；varlen-only探针不命中小Prefill；重放若GPU scatter或传输stride改变，必须先拒绝，不能用它解释模型误差。
- knowledge_delta `refined`：先看缓存后真实query长度、实际接口，再抓完整Q/K/V/逻辑KV并证明探针中性；重放先逐位还原原输出，再隔离默认自动路径。单个token输入相同不足以排除其他query生成的KV差异。
- limits：仅该版本/C550/BF16/形状限域；具体自动kernel/split未知；diag005当时未测固定split模型精度/性能，随后op006结果见下；9999未动，原GPQA123/198不覆盖。

- 后续验证（2026-10-23）：[op-006](../../../../../models/Qwen3-VL-30B-A3B-Instruct/metax/20261022-qwen3vl-metax-pr977/optimize/op-006-kvcache-split1-gpqa.md)在现有Plugin MetaX kvcache调用处仅增加num_splits1，保持prefix cache/采样/gems-opt/PR943及其他配置；14个数值用例、12capture/48replay、两rank服务真实命中与capture+16replay/C8通过。唯一一轮完整GPQA 131/198=66.16分，达到64分阈值；性能和ERQA未重测，原失败仍留存，不外推跨平台或全模型batch严格不变。

- 后续knowledge_delta `refined`：当前固定split1组合已有单轮正式GPQA阈值证据；它不证明完整模型所有batch输出相同，也不证明端到端性能收益。下一步如评估保留为性能优化，仍需同配置baseline/candidate/revert和短/长KV守护，不把本次精度恢复与未经测量的加速等同。
