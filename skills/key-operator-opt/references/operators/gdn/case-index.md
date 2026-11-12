# GDN 案例证据

## Qwen3.6-27B / MetaX C550 / 20261014

- case：[摘要](../../../../../docs/cases/20261012-qwen36-27b-metax-flash-attention/README.md)；[OP007事实主记录](../../../../../models/Qwen3.6-27B/metax/optimize/op-007-gdn-prefill-state-precision.md)。status kept-diagnostic；evidence reproduced。
- environment：vLLM bc150f50、Plugin8b059122、FG-vLLM29e80363私有、FlagGems7599dd13；MetaX C550/TP2、graph；实际源码SHA与服务绑定在OP007。
- path：Prefill `default.flagos`→runtime._metax.fused.gdn_chunk→precisionWY/H；H8/HV24/K128/V128，非方形96/80，V-major，BF16 QKV/beta（附加FP32 beta）、FP32 g/state。MTP fwd/非MTP packed路由不变。
- bottleneck：前轮profiling收敛GDN热点；本轮处理接入正确性阻塞，不测吞吐。分类operator/improve；主要变量是中间精度链。仅MetaX BF16选择新WY；非FP32 inverse旧beta*K/调优保留，其他平台generic未改。
- results：固定原输入，CPU显式BF16舍入重建GPU超限元素至9e-9；FP64块公式与递推相等。原点error .002556→5.4e-8；9矩阵/18changed-input graph/双rank真实FG precisionWY/C8通过。OP007阶段当时未测model fullGPQA/E2E；后续DIAG010对同私有6ea取得166/198（cap50000/strict80%），OP010只补缩减三阶段性能，不是公共PR925整理版的直接精度证据。source8002不动。
- negative：转置曾属adapter错误；独立stage探针不复现完整入口，invalid；weighted-RHS-only原7通过而两慢衰减case失败，已回退；完整48配置FP32调优在编译阶段精确取消，incomplete、非性能或数值失败。所有原始证据保留。
- knowledge_delta refined：FP32 state存储不能推出FP32中间精度；先解析ABI，随后固定量化后输入，做FP64等价公式与逐舍入消融；慢衰减多chunk是必要反例。
- limits：仅本环境/矩阵/冻结.002/.02；不证明所有上游shape数学缺陷，不证明旧GPQA低分由该state误差导致，不声称性能增益。FP32 compute/临时量成本、其他平台/dtype/模型待测，补丁experimental。

## OP009 全FlagGems FP32成本 / 20261014

- [事实与完整轮记录](../../../../../models/Qwen3.6-27B/metax/optimize/op-009-gdn-prefill-fp32-performance-cost.md)：C550/TP2 BF16 graph64，全部21项FG，P1024/D1/C64/N128，只有MetaX两文件从BF16改PR925 FP32/IEEE/有限tile。稳态3角色/各3measured，总吞吐6183.139→5669.920→6233.579tok/s，−8.3003%；meanTTFT+9.0021%；回退各决策指标漂移<1%。evidence reproduced，仅此完整修复/缩减Prefill的成本，不是所有FP32算法通用代价。
- Decode候选3warm散差21.9008%/0measured；Mixed旧基线6warm散差11.1034%/0measured，原BF16回退测量712.453/351.367/712.774tok/s，spread50.7271%。全部保留，三阶段整体incomplete；不能以稳态中位隐藏长尾，也不能把候选不稳定单因果归于FP32数值。
- 原FP32源码6ea最终恢复，PR925仍Draft；本周期结束时未有同源正式GPQA或四场景验收，后续DIAG010只为私有6ea建立166/198 gate，不是PR925整理版86cf的直接分数。本例新增性能证据取代此前“FP32成本未测”的边界，但只限上述Prefill，不外推长输入/其他硬件/dtype。

## OP010 正确FP32 WY资源优化 / 20261015三阶段回退完成

- [主记录](../../../../../models/Qwen3.6-27B/metax/optimize/op-010-gdn-prefill-fp32-hotspot-optimization.md)：MetaX C550/TP2/graph64，原6ea→candidateb7a→原6ea，全21FG/FP32 IEEE/V-major和原.002/.02。原GPQA166/198可同源rebind，candidate没有新正式gate。
- 基线trace Prefill WY5.39%/H6.1–6.3%/O~3.5% GPU活动worksum；WY256regs/thread、48KiBshared。只改MetaX WY输出列tile32/CTA顺序，BF16K=V128/BT64 guard，其他shape原FG路径。
- R1数值9/18通过，N8完整调用仅+1.84%<5%门槛，拒绝安装；R2原9矩阵/18changedgraph再次通过，三组完整输出/state bitwise相等，N8完整调用耗时−13.77%（micro回退漂移3.85%仍保留）。实际双rank各96tiledWY/190graph，92regs/thread、24KiBshared，4warps实际256threads，不假设通用warp32；未证明spill或所有shape性能。
- 三角色/三阶段87轮全部保存、27measured、9408请求0失败、9原生check_run通过。Prefill模型吞吐仅+2.361%<3%、TTFT−2.333%；原FP32回退meanTTFT漂移1.010247%>1%。Decode吞吐+0.648%、TPOT−0.198%、P99ITL+1.720%，原版回退P99ITL漂移2.415935%>1%。
- Mixed baselineTPS514.692/572.813/668.099，spread26.781%；candidate中位678.723，原版回退668.501，后者比baseline也+16.705%。不能把candidate名义+18.489%当可靠E2E收益，不能事后换用有利baseline或删除慢轮。三个原生比较均incomplete，候选撤回，正确FP32/full21/166gate恢复，监控暂停。
- negative/knowledge_delta refined：NFS ENOSPC旧失败/部分Prefill、Stream创建阻塞/v3僵尸guard失误、R1微测拒绝项均保留。空闲GPU隔离后9/18 graph通过，但driver等待根因unknown；固定末尾warm窗口通过仍不能替代全部measured散差和回退检验。资源/单kernel/单阶段改善不能推出Mixed收益；下一步先取完整Mixed执行/shape证据再做高成本kernel方案。
- limits：仅此C550/源码/缩减P1K三阶段；不合并OP009成本/其他source或四场景，不归因数值导致共同波动，补丁experimental且当前未启用。


## 当前脚本20FG / packed decode真实ABI校准 / 20261015–16

- [案例](../../../../../docs/cases/20261015-qwen36-27b-metax-fg20-e2e/README.md)、[OP002主记录](../../../../../models/Qwen3.6-27B/metax/20261015-qwen36-27b-metax-fg20-e2e/optimize/op-002-gdn-packed-decode-warps4.md)。vLLMbc150f50/0.20.2、Pluginb8f2734、FG-vLLMde2298b+5保留文件/整体cb45、FlagGems7599dd13；C550/TP2/graph64。精确20FG白名单，native attention是本例输入事实，不能与旧全21FG比较累计收益。
- 三阶段基线：PF total5693.825tok/s、D output950.095tok/s、M output704.178tok/s。两rank profile按mcGraphLaunch correlation分离各54个B64 graph，其中GDN packed约20.1% kernel-work。不是端到端占比；Mixed64迭代窗口未覆盖第二cohort插入，不足以解释P99ITL1.49s。
- runtime cache IR证明：H8/HV24/K=V128，mixed/a/b/bias BF16、A_log/state FP32、indices I32，QKV行stride8192（逻辑5120）、state行stride401408（逻辑393216）、head16384。相邻Z/非SSM区域不可写。proxy biasFP32/I64/contiguous微测不能冒充真实模型配置，不能按shape相同认定ABI相同。
- 旧proxy BV16W1/BV32W4分别完整调用快11.14%/13.46%，组合BV16W4反而慢8.93%，均未安装进模型。真实ABI复验同W4代码：15case各8step/两组变化输入graph、原.002/.02及相邻区域保护通过；原W1实际256regs/12spills，W4为140regs/0spills。真实B32快7.90%、B64快8.29%；B8原fallback慢1.34%计时波动，B/R微漂移均<0.4%。证据numerical SHA3d6d6275、micro SHA3d2009c6。
- evidence reproduced/scoped，仅证明所列矩阵正确与完整调用微测；W4不是逐位一致。模型三阶段freshB/C/R已完成，87轮/27measured/9408请求0失败，Decode输出+1.3902%、Mixed+1.3316%低于冻结2%门槛，原代码/服务回退。PF观测+0.6609%并非decode特化的直接收益。全部延迟guard5%/spread10%/B-R漂移1%通过，最大漂移0.8287%；回退Mixed慢轮659.458tok/s仍保留，最大P99TPOT测量spread9.2236%。没有正式GPQA gate，不保留新实现。移除spill不能直接推出足够模型收益；不相加两个独立配置加速比。


## 当前20FG / Mixed稳定性与Decode重复JIT / 20261016

- [FW002最终事实与诊断](../../../../../models/Qwen3.6-27B/metax/20261015-qwen36-27b-metax-fg20-e2e/optimize/framework-002-mixed-batch-overlap.md)。MetaX C550/TP2/graph64、vLLM0.20.2、Plugin b8f2734/原98f36、FG-vLLM de2298b+5私有/整体cb45；FP32 V-major中间链及.002/.02保持，完整20FG。status reverted/incomplete；full调优机制reproduced，GDN重复JIT为strong historical observation，未做新因果A/B。
- 前置FG full小整数新N在线16配置调优在完整Mixed两ranktrace复现额外~1.5s preprocess；私有固定FG full分支数值194/16graphreplay通过，作为共同前置建立新B/C/R，Mixed基线3测spread0.1794%。这不是GDN数学或FP32计算变慢，也不是full独立端到端加速比。
- Plugin metadata hoist数值14prefix+5真实FA输出逐位相等，模型实际去除逐层integercopy，三阶段87轮/27测/9408请求0失败。PF+0.5804%通过，D观察+0.2495%但基线meanTTFT13.4452%spread不完整；Mixed+0.2646%<2%失败，P99E2EL+0.7622%仍在5%guard内。全部B/R决策指标最大漂移0.998445%<1%，原Plugin/full/四repo/source18002恢复；微测或消除copy不保证可保留E2E收益。
- Decode milestone P1K/D512/C64/N64第7轮，64请求16ms内发出，初期cohort由1+7+8…变为1+1+7+8…，2.203s输出gap内出现H kernel新编译，source→binary0.616s；r1暖轮有3次、r2-r6和r8/r9无新H编译。9个cache目录对应完全相同lowered source与binary。FP32 H已prune到BK32/BV16/W4/stages3，仍把未参与kernel数学的N_BUCKET/SKEW_BUCKET作为constexpr/key，导致相同设备代码重复编译的强证据。cache证据已按SHA归档，sourceSHA2c7ac0f4/binarySHAbe205867。
- knowledge_delta refined：固定吞吐末3暖轮通过仍可能漏掉运行中的稀有批次key；先比较编译产物与key/运行期CPU停顿，而非先换精度或tile。FP32有限配置仍可能保留冗余key；拟将key规范化作为独立优化变量，不把它当已验证修复。记录节点clock与共享FSmtime偏差，本例约202s，不能直接混合mtime对齐。
- limits：历史r7无ranktrace、精确bucket二元组未知，不能把平均TTFT多出的~0.92s全部等同0.616s后端编译；CPU/driver/GC剩余份额未拆。离线审计没有新请求或数值变更，不证明数值缺陷或已修复，也没有当前20FG正式198gate/四场景验收。单FP32配置适用边界不外推BF16多配置调优、其他平台或长期服务。
