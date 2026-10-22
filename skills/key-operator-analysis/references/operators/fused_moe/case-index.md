# Fused MoE 案例

## Qwen3.8-Flash-Next / PPU：TLE能力不匹配与原alignment空输入边界

- [op061主记录](../../../../../models/Qwen3.8-Flash-Next/ppu/20261015-qwen38-flash-next-ppu07-master/optimize/op-061-ppu-moe-tle-capability.md)，status=blocked；重复不支持编译为observation+真实旧IR的CPU拒绝函数复现，空输入前端失败为reproduced。PPU-07/ZW810E/TP8物理8–15、Gems f0aa7f12加既有适配，Plugin a696859b+PR455+FP32；graph服务原健康，原arg/source指纹见主记录。
- Prefill/Mixed alignment形状包括M8065、topk10/E512/int32；旧8warm期间18份仅source无成功metadata/binary，PPU真实拒绝`tle.distributed_barrier`，版本HAS_TLE/设备CUDA条件未排除。候选operator/improve只加thead门禁、原四阶段kernel AST不变；CPU7组dispatch passed，不是GPU数值或性能通过。
- 首受控GPU矩阵M0/E10/B16在第一项失败：原/候选同算式`tokens_per_thread=next_power_of_2(ceil_div(0,E))=0`，原stage1 `tl.arange(0,0)`前端拒绝，尚未执行数值kernel。首PT/日志/失败source及CPU审计可核验，原版未GPU重跑、生产caller空输入ABI未核；不是新TLE门禁回归或模型异常的证明。
- 结果：原8010自然排空后0次候选启动/0推理，非空GPU/graph/C1C8/性能not_run，无新gate；未访问8035、不自动重试或修改零边界。source和已保留FP32/i64/QSA M16/PLE保持，完整证据与SHA在主记录。
- knowledge_delta=refined：先查后端实际lowering能力与失败cache是否可复用，再排除无效试编译；原fallback也必须按自身ABI验证零/非对齐/graph，不能以“未改kernel”豁免。新候选性能贡献未量化，不把反复编译机制当所有TTFT波动的唯一原因。

用户授权后的v2补证：实际native vLLM在numel<E时压缩sorted/expert容量，零输入确实产生两份零长度buffer；只clamp输入tokens_per_thread还不足，三处launch extent均需max1，实际访存仍由原mask控制。GPU68项（含compact零buffer/M1）和5次capture各3次replay通过，空graph每次毒化count后仍写回0；83份PT SHA核验。v1首错保留、kernel AST不变，私有v2原安装/Git不改。模型仅获一次启动、当前还在编译，10短doc2/C8与性能未完成；因此只是零边界/graph的reproduced，不能称模型或性能问题解决。原始source/脚本/产物SHA仍以op061主记录为准。

v2终态补充（不改上面v1失败事实）：原controller退出，10个seq/同一短doc2全部HTTP200、完整think-end/EOS/非空final且诊断B，C1两次570完整token相同，C8 8请求真实FULL8执行；两类capture7/7和native FULL>=2成立。83PT/raw-token/source/服务与11份终态CPU审计文件通过，新8010健康保留、monitor暂停。模型独立cache已有19份四阶段MLIR（含v2源码loc），未见TLE alignment字串；原audit用Python def识别MLIR的0命中启发式不采信，补证独立保留。仅局部可保留候选、status=not-proven（性能），不是GPQA/C64/60K或性能波动解决；无独立逐rank逐步trace/新formal gate。knowledge_delta=refined：零输入ABI修复通过模型接入护栏，但消除已知编译浪费的端到端贡献仍需同契约B/C/R，不能用短doc2或产物缺失代替稳态测量。

## Qwen3.8-Flash-Next / PPU：模型外层FP32不覆盖MoE自有归约

- case_id：20261015-qwen38-flash-next-ppu07-master / accdiag-032；[事实记录](../../../../../models/Qwen3.8-Flash-Next/ppu/20261015-qwen38-flash-next-ppu07-master/optimize/accdiag-032-post-attn-moe-reduction-offline.md)，status=not-proven，evidence=observation（当前编译数据流+旧张量CPU核验，非新推理）。
- 环境/路径：PPU-07、TP8物理8–15、BF16、graph；hidden2560、512 routed experts/topk10、shared/routed intermediate640；当前私有031 model692dc3e1、engine MoERunner源码d11a841e，完整source/cache SHA在案例。MoE具体expert kernel运行时impl_id仍unknown，不按类名推定。
- 证据：显式attention TP FP32→BF16后，all8rank layer0 post-attn的48完整目标PT仍C1/Mixed/跨rank相同，最终logits仍不同。8份当前layer0生成模块显示moe_forward_shared两个输出→BF16存储sum→late TP all_reduce→mlp-branch；该内部归约不经模型外层helper，外层requires_tp_all_reduce=False。加法kernel内部FP32算术/store BF16，不混成“全程BF16加法”。
- 结果：0新模型/GPU请求/重载/埋点，保留FP32/i64/QSA M16，不访问8035；没有MoE pre/postTP实际值，不能定首差异/通信bug/60K因果，无正式gate/性能结论。旧164/198 failed-score不改。
- knowledge_delta=refined：先找collective实际拥有者与shared/routed合并顺序，而非认为外层FP32已覆盖内部；后续同时抓mix/router、两local专家、sum前后及TP前后。sum若原地复用shared buffer，shared快照必须在加法前复制，否则事后观察会误把sum当shared。
- 限制/下一步：仅778/808 freshPrefix/C8及当前源码；新窄捕获需用户先授权。完整证据路径/CPU b060c6c9、compiled6190b125、Host17b9a387见主记录；编译路径证据不是数值根因，不将MetaX性能选参卡迁移至本例。

### accdiag-033：内部边界运行时数值补证

- [事实记录](../../../../../models/Qwen3.8-Flash-Next/ppu/20261015-qwen38-flash-next-ppu07-master/optimize/accdiag-033-layer0-mlp-moe-boundary.md)，status=not-proven（修复/60K因果），evidence=reproduced（有限域首分歧）。同PPU-07 TP8/EP1、SP=false、BF16/hidden2560，C1目标778/808与Mixed总785/815、target起点7；graph服务507FULL/rank、仅19/C8/一次8010重载，外层FP32/i64/M16未改。
- 实际impl：MoERunner d11a841e→UnquantizedFusedMoEMethod d365f21f/FusedMoEKernel 78f33203→Plugin TritonExpertsFL.apply d16781c9，router compute为FusedTopKRouterFL 7d32bf00，fused_output_is_reduced=false；来源与完整SHA在主记录，未声称所有内部GEMM kernel trace已取到。
- 变量仅观察：shared/routed在原地add前独立CPU复制，32完整layer0阶段/all8rank及完整logits/prob/token。全部mix/router/topk/两local输出/preTP C1-Mixed逐位相同，48份local add等于FP64一次BF16舍入；首新差在MoE postTP（max.0078125），HC公式与当前输入精确吻合，C1重复全部相同。1536层/192采样PT及1951原始文件核验。
- CPU用本次真实4ring/32旋转解释四份postTP全部元素、每256块均有共同可行顺序，符合舍入界；未新做GPU offset消融或追踪该次kernel具体累加序，故不称实现bug已证。最终doc81 logits仍不同，808概率L1=.06714，19短评分不是60K/C64/正式精度；无性能数据/新gate，原164/198 failed-score保持。
- knowledge_delta=refined：从“compiled自有BF16可疑但内部值缺失”推进到“all8实际preTP同而postTP先变”。下一首实验只改该自有late collective FP32→BF16，避免已reduce分支二次归约，保持router/专家不变；需用户新授权重载和固定同前缀验证，未执行。CPU f55c7b66/Host ada0df29/ring87779b86可追溯；不访问8035。

### accdiag-034：MoE自有归约FP32候选的局部迁移验证

- [记录](../../../../../models/Qwen3.8-Flash-Next/ppu/20261015-qwen38-flash-next-ppu07-master/optimize/accdiag-034-moe-internal-fp32-tp.md)，status=not-proven（整体精度/60K修复）；evidence=reproduced（所测局部候选通过）。同PPU TP8/EP1/BF16/hidden2560/778、808目标与Mixed起点7，原guard/已归约互斥保持。模型shim仅给当前架构MoERunner实例绑定late BF16→FP32 collective→BF16，不改共享vLLM、router/专家或旧显式FP32/i64/M16；model9ce7d6ca，精确source/patch在主记录。
- 19/19 HTTP200/C8/一次8010重载、0额外请求/8035访问；48实际FP32 entry/output/castback、1632边界与192完整采样PT、2011文件及源/计数核验，graph两类7/7/507FULL每rank。MoE postTP/HC/output C1-Mixed完全相同、匹配FP64参考；最终doc81两个point的raw logits最大差从1.15625/.84765625到0/0，808实际prob L1从.06714148到0，doc71阴性与C1重复同值。
- 跨033/034匹配的288项上游（全targetrows）逐位同，新postTP精确等于原033八输入FP64一次BF16参考，支持局部数值漂移被此dtype变量控制；新观察点/同步/缓存可能影响fusion，但本次没有靠改变上游输入隐藏差异。attention FP32本身仍有1.49e-8末位差、cast BF16后同，不能泛称FP32完全结合。
- knowledge_delta=refined：从首边界/舍入解释推进到模型自有collective的单变量候选和最终分布一致；下一验证应换长Decode/C64/原正式范围而非继续盲目叠改router/专家/HC。只短前缀单token评分，没证明60K不收敛、正式198分数或性能；旧164/198 failed-score/no gate仍保留，长范围需新授权。CPUdce66d1d/Host78c8d912/cross02df3e5c见原件。

## Qwen3-VL / MetaX：完整表替换不等价于阶段覆盖

- case_id：20261015-qwen3vl-metax-p64k-opt3 / diag-014-opt4-opt6-gap + op-015-moe-gemm2-stage1-json
- [事实主记录](../../../../../models/Qwen3-VL-30B-A3B-Instruct/metax/20261015-qwen3vl-metax-p64k-opt3/optimize/diag-014-opt4-opt6-gap.md)
- diag014/op015历史状态：kept（阶段配置接入）、not-proven（当时的端到端性能贡献）；配置/数值/graph为reproduced。后续受控性能证据见op017/op018补充，均不升级为P64/跨平台结论。
- 环境：Qwen3-VL-30B-A3B，MetaX C550 TP2 BF16，vLLM ee0da84ab，Plugin 4d4645b→08da21cb，FlagGems-vllm f6fdb9b加私有配置补丁；graph。
- 路径：Prefill/Decode/Mixed；FlagOS完整专家算子，MetaX fused_experts_impl；w1=(128,768,2048)、w2=(128,2048,384)、topk8，连续BF16输入。
- 证据：opt4与opt6手工同workload数据有持续差距；旧精确M8..64/GEMM2 stage1覆盖变成最近M完整表，两个GEMM共享；M64/GEMM2当前stage3且BK/group/warp不同。实际原始源码5个JIT kernel AST相同，默认选参函数相同，主要变化在配置入口/选择器。
- change：诊断，未来operator/improve；primary_variable=MoE选参语义；适用边界为记录中的版本、shape和配置文件。
- 算子结果：仅CPU选择器重放，硬件共享内存用分支假设；不是GPU测速。M64结果在所列假设下不变。
- E2E结果：历史手工CSV差距，未运行MoE-only B/C/R，不签发其因果收益或恢复结论。
- 正确性：没有新实现修改或新精度gate；静态AST相同不代表模型精度通过。正式精度暂缓。
- 排除项：词表采样源回退；sort int32源码保留；路由topk_softmax两库kernel/launch相同；direct_sum两版阈值均1<<60、未开启。
- knowledge_delta：refined。先前“加载同格式JSON”不能替代“保留旧调优阶段/范围/默认路径”；后续先比较最终每阶段配置与布尔选择，再做单变量设备/端到端验证。
- 限制：Plugin与FlagGems整体版本也变化，未独立消融；旧N64 profiler不能与N128未profile结果计算收益；P64在途，累计抢占不能分配到单轮。

- 后续限域验证：[op015阶段配置接入](../../../../../models/Qwen3-VL-30B-A3B-Instruct/metax/20261015-qwen3vl-metax-p64k-opt3/optimize/op-015-moe-gemm2-stage1-json.md)。保持gems-opt、参考采样和共享PR595表，新增同格式gemm2/完整表；M65恢复行使最近M选择只改变M49..64/GEMM2 stages3→1，其余M/字段及全部GEMM1保持。CPU M0..65536全域检查；复用token alignment要求两阶段BLOCK_SIZE_M一致，不一致显式报错。
- op015结果：28组BF16/FP16完整MoE前后逐bit一致、6数学参考、10独立capture各2replay；生产TP2真实M64/GEMM1 stage3、GEMM2 stage1，双worker各16replay与17个smoke/C8通过。没有新E2E收益结论或正式精度gate，其他dtype/平台未签发通过。
- 验证反例：外部import观测hook必须幂等；仅恢复builtins.__import__仍可能由在途外层调用重复安装。初次观测启动因重复写证据失败；class sentinel与first-call保护修复后原生产范围重跑通过，产品代码未因该事件改变。失败日志保持，不混入通过身份。
- knowledge_delta补充：refined。单阶段配置可以保留标准扁平JSON兼容；先CPU证明最近M范围及BM对齐，再用实际kernel dispatch和生产graph核验，不能把“新增阶段文件”直接当作端到端性能恢复。

- [diag016后续反例](../../../../../models/Qwen3-VL-30B-A3B-Instruct/metax/20261015-qwen3vl-metax-p64k-opt3/optimize/diag-016-opt7-stage1-gap.md)：stage1接入验证通过但手工P4K opt7为867.38TPS，低于opt6的900.65和opt4的985.46；未建立stage独立因果。stage/tiling/warp耦合且实际修改只覆盖M49..64，不能推导小M8或大M收益。完整G2旧参数对照只准备在外部目录，CPU范围检查不是GPU性能证据。

- [op017受控对照](../../../../../models/Qwen3-VL-30B-A3B-Instruct/metax/20261015-qwen3vl-metax-p64k-opt3/optimize/op-017-moe-gemm2-decode-profile.md)：仅现有G2阶段表M8..64恢复BM16/BN64/BK128/group1/warp4/stage1，M7/65边界保护，G1和gems-opt/采样保持。28数值/8参考/14独立capture及双worker生产graph/C8通过；P4K B/C/R 865.38/898.64/871.04TPS，C/B+3.84%、B/R漂移+0.65%，native passed，保留candidate。M64 fullMoE0.600719→0.527316ms但stage3控制0.517507ms；M8/M32旧几何略慢，不能跨M或推导P64收益。正式精度和同键其他模型/芯片未测，knowledge_delta=refined。

- [op018 GEMM1补充](../../../../../models/Qwen3-VL-30B-A3B-Instruct/metax/20261015-qwen3vl-metax-p64k-opt3/optimize/op-018-moe-gemm1-decode-profile.md)：同一MetaX/C550/TP2/BF16/实际shape，保留op017 G2逐byte不变，仅根表G1 M8..64恢复BN64/BK128/group1/warp4/stage3，M7/65保护范围；28数值/8参考/14capture及双rank生产graph/C8通过。完整MoE graph M64 0.527608→0.460027ms，M8/M32也快；P4K B/C/R 899.66/940.41/898.50TPS（C/B+4.53%，漂移-0.13%），原生passed，保留candidate。knowledge_delta=refined，证据限域reproduced；P64、整体opt4恢复及正式GPQA未测。

- [op019大M补充](../../../../../models/Qwen3-VL-30B-A3B-Instruct/metax/20261015-qwen3vl-metax-p64k-opt3/optimize/op-019-moe-gemm1-prefill-profile.md)：同MetaX/C550/TP2/BF16及expert形状，只改G1 M4096..8192 warp8/group1，BM和小M/G2全部保持。40数值逐bit一致、8参考、18capture及双rank生产graph/C8通过；FullMoE M8192 6.75549→4.27548ms。完整P64 B/C/R 71.944/76.840/72.080TPS（+6.81%，漂移+0.19%），native passed，保留candidate；不外推其他模型/芯片/场景/正式精度，knowledge_delta=refined。

## Qwen3-VL / MetaX：PR977 未覆盖 E128 通用共享内存分支

- case_id: 20261022-qwen3vl-metax-pr977；status: reverted/not-deployed；evidence_level: reproduced。
- 来源：[案例与产物](../../../../../docs/cases/20261022-qwen3vl-metax-pr977/README.md)。mx-59/C55064KiB、独立GPU0/1、TP2形状，vLLMee0da84、Plugin08da21c、FlagGemsc3c5f5a；原FVf6fdb9b+本地MoE，对照上游bad340d（含977），候选MoE原文无943。
- operator/replace：每rank E128,w1=(128,768,2048),w2=(128,2048,384),topk8；BF16/FP16、连续布局；M0/1/8/64/65/257/1024/4096/8192，完整forward、SiLU及加权归约。
- 结果：B/R各18/18、14capture/28变化输入replay；C14/18、10capture/20replay。两dtype的M4096/8192均在GEMM1失败，实际BM128/BN128/BK64/warps8/stages4/PAIR=true，compiled metadata要求98304B而上限65536B。其余非空数值遵守原BF16.004/.016、FP16.0005/.003容差；非数值错误。
- knowledge_delta=refined：977专用修复面向E256/TP2；当前E128未命中Qwen白名单，仍进200000-byte通用启发式。检查某PR的资源修复是否可迁移，先重放当前E/N/K/topk白名单与最终dispatch，不能仅以PR标题或工作区已更新推定已修。
- 限制：原服务/四仓库/采样/gems-opt未改，未启动候选模型服务、无Prefill/Decode/Mixed性能或模型精度结论；保持停止晋级，不把通过的小M当整链可用。不是声称977引入该问题，也未修改最新代码强行通过。
