# 20261012 Qwen3.6-27B / MetaX Flash Attention

目标为mx-59上的用户源容器qwen3.6-27B、权重/public-flash/models/Qwen3.6-27B。执行SOP0.40；范围diagnostic；旧任务候选77.27%失败，经批准修复评测后FlagGems候选80.30%通过；attention_backend黑名单原生路径80.81%通过。端到端性能incomplete。

用户授权远端目录：/public-flash/jinghao/qwen3.6-27B/optimize/flash_attention/20261012-qwen36-27b-metax-flash-attention/。本地[基线](../../../models/Qwen3.6-27B/metax/baseline/README.md)、[优化总览](../../../models/Qwen3.6-27B/metax/optimize/README.md)、[单点实验](../../../models/Qwen3.6-27B/metax/optimize/op-001-metax-gqa-decode-scheduler.md)、[最终验收](../../../models/Qwen3.6-27B/metax/acceptance/README.md)为状态入口。

历史加入attention_backend后P4K/P16K/P64K吞吐退化43.62%/53.57%/72.77%，三轮中位数观察。当前代码路径已核验：Plugin AttentionFLBackend→flaggems_vllm.ops.attention→flash_api→MetaX scheduler。TP2每rank Q12/KV2/D256，16个full-attention层；48个linear-attention层不属于本Flash Attention改动。

独立优化容器从含用户未提交源码的适配状态快照复刻；Python源码指纹一致，mount_parity通过。源服务保留，使用空闲2/3卡产生新的可比基线，不能与历史0/1卡直接归因。

发现packed GQA6因query行数>4落入legacy；M16 SplitKV调度候选又暴露B1非连续输出stride误用于连续partial缓冲的问题。修复后78项原数值/graph测试通过，B64 KV1K/4K/16K完整算子调用约3.715/4.780/5.187×。证据等级reproduced仅限同进程算子A/B/revert；尚无端到端净收益结论。

下一步与完整原始证据在模型state.yml和远端case目录。未修改源服务、权重、tokenizer或vLLM；未提交、推送或创建PR。

历史原实现同契约GPQA精度二分已完成，旧任务候选198题有效但低于阈值，未签发其gate。长KV8项通过，附加M16严格容差失败的9组代表性输出与原实现bitwise相等，失败证据保留。端到端性能例外待用户明确答复；不可从算子收益宣称最终优化完成。

原路径同契约完整GPQA156/198＝78.79%同样低于80%，来源和样本完整性核验通过。候选153/198与原路径11题strict判断不同（7仅原对、4仅候选对），两分数差异未因果定位。该旧契约当时存在精度阻塞；后来按用户批准修复任务并产生新有效gate。原路径旧分数及证据保留。

2026-10-12精度根因定位：确认GPQA helper删除科学方括号损坏12题、doc171 gold C→A；同服务同seed两次原/恢复prompt均B错→C对。用户批准修复任务后完整重测，新私有评测容器/provenance、旧候选相同source，198/strict80/采样均保留；candidate04修正版评测已结束，159/198通过。源服务未改、性能未启动，完整详情进入模型optimize记录。

修正版全198终态159/198＝80.30%通过80%，门禁已issue/check且当前候选source/instance一致。12修复题净+1、其余题生成波动净+5，不能把总+6都归因评测bug。旧分数保留，监控停用，性能仍未测且源服务未改；当前模型optimize入口为事实主记录。

用户追加attention_backend黑名单精度对比已完成，见[diag-005](../../../models/Qwen3.6-27B/metax/optimize/diag-005-attention-blacklist.md)。原生路径修正版160/198＝80.81%，较FlagGems159/198净增1题、+0.51个百分点；11题错转对、10题对转错，同198题/gold/arguments相等。当前black03 exactsource/instance及完整结果验真通过，新gate issue/check passed；监控已PAUSED。单轮采样分差不证明FlagGems是低分主因，未显示明显整体提升，不开展性能、不操作源8002。

2026-10-13按用户要求继续[共同28错题定位](../../../models/Qwen3.6-27B/metax/optimize/diag-006-common-wrong-truncation-config.md)：8双截断/3单截断/17正常final错，实际30000cap是明确健康限制；采样符合modelcard、gold映射和strict提取核验无新错误，数据集doc17/106有质量疑点。两题预算配对诊断pending，不重写正式分，不改服务，不跑性能。

用户批准[diag007原生50000完整评测](../../../models/Qwen3.6-27B/metax/optimize/diag-007-native-cap50000-full-gpqa.md)已结束：158/198＝79.80%低于80，未签新gate；较原生30000少2题，length14→5但整体分数未提升。原14触顶题5本轮正确，全题9新对/11旧对，前缀分叉，精度变动原因未定位。source/instance和完整198证据验真，监控PAUSED，保持旧分数/gates，不重评/改阈值/gold/预算，不测试性能。rev002规划已在state.yml归档。

2026-10-13 FG周期终态：[组合001](../../../models/Qwen3.6-27B/metax/optimize/combo-001-fa-splits-warps.md)已精确回退并完成对照。物理页16/逻辑784纠正，算子微测−18.17%，诊断Decode+1.71%；Mixed预热18.03%超限、零测量，比较计划决策指标声明缺口另致incomplete。原路径Mixed回退散差0.32%、吞吐漂移−0.11%，原OP001 FG保留，源8002不变。50000正式精度失败不解除；候选PR experimental。知识卡见Flash Attention case-index，主记录保存九原生记录/终态SHA，不把微测作E2E收益。

2026-10-13 23:34 北京时间：[Framework001](../../../models/Qwen3.6-27B/metax/optimize/framework-001-prefill-token-budget.md)原生对照收尾。8192→4096未关闭任何已开启FG算子；Mixed TTFT下降17.21%但输出下降4.59%、TPOT增11.32%，Decode P99ITL超守护，候选不保留。原8192已恢复，九记录验真/全部轮/漂移详见事实主记录；正式精度仍未解除、无新正式验收。

2026-10-14用户改选[OP005 GDN decode最新版接入](../../../models/Qwen3.6-27B/metax/optimize/op-005-gdn-latest-routing.md)：私有FG-vLLM升级29e80363/0.3.0.dev1，保留原17项FG并新增decode两key；MTP fwd、非MTP packed。12路由及13GPU/graph矩阵已通过，MTP保留页0保护追加修复；新增prefill数值不合格未启用，runtime双rankgraph/C8验证中。旧OP004 M8编译失败/回退、正式精度失败均保留，未声称E2E收益。

OP005终态：当前新版GDN decode实例296014已通过实际FG命中、graph与同源C8绑定；原17FG保留+decode2，新prefill不合格未启用。控制器目录/Host边界错误导致一次原版回退，失败证据保留，现已修正并恢复同一新版，无重复候选C8。完整事实、patch路径/SHA及边界见OP005/state.yml；当前全量精度和端到端性能未验收。

2026-10-14发布GDN prefill上游issue [#923](https://github.com/flagos-ai/FlagGems-vllm/issues/923)：实际MetaX V-major导出与generic K-major契约区别导致此前接入转置误用，上游算术缺陷未证实。issue只引用公开源码，请求文档/校验/测试；内部诊断原稿未发布，当前模型服务未操作。

2026-10-14 [OP006](../../../models/Qwen3.6-27B/metax/optimize/op-006-gdn-prefill-vmajor-correction.md)：去掉MetaX多余转置后历史输入通过，仍有一个可复现finalstate元素超原.002/.02；完整7矩阵6通过、14graph通过。删除空段activefinalstatebitwise相等仍失败，具体BF16组块差异待定位。当前FG19与修正adapter保留，未加入gdn_prefill，服务319960恢复/同源C8绑定通过；全量GPQA与E2E无新验收。

2026-10-14 [OP007](../../../models/Qwen3.6-27B/metax/optimize/op-007-gdn-prefill-state-precision.md)：原finalstate超限由BF16中间舍入累积复现，未证实公式/布局错误；完整FP32 carry在原容差下通过9matrix/18changed graph及双rank/新C8，隔离服务376022新增gdn_prefill、原白名单不缩减。部分精度修复失败与自动调优编译取消均保留。FP32成本/模型完整50000分数未知，无正式gate/E2E收益；源8002不变，当前补丁experimental。

2026-10-14 [OP008](../../../models/Qwen3.6-27B/metax/optimize/op-008-gdn-prefill-precision-pr.md)：用户授权更新[Issue923](https://github.com/flagos-ai/FlagGems-vllm/issues/923)并创建关联[Draft PR925](https://github.com/flagos-ai/FlagGems-vllm/pull/925)，head83333ea，仅三个MetaX修复/合成测试文件。上游复现慢衰减最终状态7870元素超原容差；最终PR源码11测试、原9矩阵与18改变输入graph通过。公开文件逐字核验并附加到任务，未合并；性能与完整模型精度待验。当前同源恢复服务390234、完整FlagGems白名单保留、双rank graph与既有C8等价绑定通过；源8002不变。

2026-10-14 [OP009](../../../models/Qwen3.6-27B/metax/optimize/op-009-gdn-prefill-fp32-performance-cost.md)：全21项FlagGems不关闭，原BF16→PR925完整FP32→原BF16回退，36warm/21measured全部保留，最终恢复原正确FP32526267。Prefill总吞吐6183.139→5669.920→6233.579tok/s（−8.300%，回退漂移+.816%），meanTTFT8285.204→9031.047→8216.764ms（+9.002%，漂移−.826%），nativefailed为性能成本；Decode候选warmspread21.90%/0measured，Mixed原基线warmspread11.10%/0measured、回退已准入测量却50.73%吞吐spread，nativeincomplete，不能删异常351.367轮或算可靠Mixed比值。source8002不变，当前FP32source6ea/双rankgraph及C8等价验证通过；正式GPQA未补、PR不推送。终态results/op009-terminal-validation.json SHA54db01e6ee3572f4f875edbdf9f6b142fb0f1d43cd7d66397a95e1592c07e14e。rev008强调先恢复测量有效性，再用原容差优化FP32数据流；数值通过不意味着无E2E成本，旧BF16也存在时序波动。

[OP010](../../../models/Qwen3.6-27B/metax/optimize/op-010-gdn-prefill-fp32-hotspot-optimization.md)三阶段及回退完成：87轮/27measured、9408请求0失败；候选Prefill+2.361%/TTFT−2.333%，Decode+0.648%/TPOT−0.198%/P99ITL+1.720%。Mixed名义+18.489%，相同原版回退+16.705%，baseline散差26.781%阻止E2E归因；PrefillmeanTTFT漂移1.010247%、DecodeP99ITL2.415935%超1%，三份原生比较incomplete，未晋级。原FP32 6ea/full21/原容差恢复于756537/1792034481.9并native166/198gate重绑定/check，监控PAUSED；所有慢轮/旧ENOSPC/候选patch保留，source8002不动，不追加测试。
