# TP allreduce：限域精度边界证据

## 编译路径补证：Python事件缺失不等于FP32修复未命中

- 案例：[accdiag-042离线续查](../../../../../models/Qwen3.8-Flash-Next/ppu/20261015-qwen38-flash-next-ppu07-master/optimize/accdiag-042-env041-same-prefix.md)，2026-10-19；status=not-proven（首数值分歧层/正式精度），evidence=observation（当前编译数据流，非新collective GPU重放）。
- 匹配环境：Qwen3.8-Flash-Next/PPU-07/TP8/hidden2560，Plugin main a696859b+PR455 3cb373b1+实例FP32，FGVLLM b4d3382/QSA M16，Gems f0aa7f12+本地i64兼容；19短请求C1/MixedC8，doc81目标778/808、Mixed起点7，首Prefill graphNONE但服务使用Torch编译图及背景FULL graph。
- 现象：8rank FP32实例绑定存在，但Python helper中的STEP>0事件为0；042实际19正常返回，C1重复exact，C1/Mixed raw logits及部分概率不同。
- 零运行变更续查：8份冻结FX图各96个FP32 branch collective（48attention/48MoE）及2个BF16 embedding；生成缓冲及cast链验证、320个AOT引用SHA通过，绑定到该次实际cache/worker/graph证据。编译后直接custom-op调用不经过Python事件，因此不能因日志0推定BF16回退。没有独立NCCL kernel trace或本轮归约两侧数值。
- 进一步边界：doc81实际输入/位置/RNG/noise相同；96个CPU top-k/top-p参考与保存概率最大误差1.49e-8，支持集/token相同，差异在采样前模型前向。没有当前层/LMhead前hidden，不能从“FP32链已在图中”推定局部数值已同，或套用旧034不同图的首差异；新HC/GEMM/状态/最终投影仍未二分。零新推理/GPU/埋点/重启/8035访问，无性能/正式gate结论。
- knowledge_delta=refined：缺Python命中时先核当前FX→最终生成buffer dtype→缓存/运行绑定；源码绑定、编译路径和边界数值是不同证据层。若采样前已不同，先用旧logits CPU参考排除后处理，再申请最窄前向边界取证，不盲目叠加FP32或直接归因新算子。

## Qwen3.8-Flash-Next / PPU TP8：相同目标行、Mixed偏移后的首差异

- 案例：[accdiag-029](../../../../../models/Qwen3.8-Flash-Next/ppu/20261015-qwen38-flash-next-ppu07-master/optimize/accdiag-029-tp-hc-boundary.md)，2026-10-18，状态not-proven（具体通信缺陷/模型症状根因未证明），证据reproduced（局部数值边界）。
- 环境：PPU-07、TP8物理8–15、BF16、graph服务；private017 i64、QSA M16保留。engine/Plugin精确树SHA及source-before/after在案例原始回执；后端具体运行时分支未知，未把源码选择链当已命中证明。
- 路径：layer0 GDN本地branch→TP allreduce→GatedResidualSimple HC combine。C1目标行数778/808，实际Mixed C8总行785/815且目标起点7、7真实Decode peers，hidden2560；观察完整目标行，不只最后token。
- 变量：诊断性观察点细分、19请求/C8/一次仅8010重载，不是性能优化或算子替换。原数学AST去除观察if后不变；新增tap/CPU同步/编译分割和新缓存仍可能影响时序/后续数值。
- 正确性观察：各rank目标本地branch C1/Mixed逐位相同，C1重复稳定；all8rank首次不同在postTP（max0.0078125），各自归约结果跨rank相同。HC其余输入/logits/weight精确相同，32份HC输出等于保存输入的FP64公式一次BF16舍入。全部624边界PT+192采样输入PT独立CPU解包、SHA核验。
- 模型端：doc81最终logits/prob有变化、同noise下一token仍相同；doc71阴性控制相同。单token评分不是60K完整轨迹，正式164/198 failed-score无gate保持。无性能测量/收益，不称修复。
- 知识差量refined：此前只能定位TP+HC区间；现在先检查通信总shape、目标行offset及累加/归约顺序，避免直接修改HC/QSA。与FP64一次舍入不相等不单独证明BF16通信bug。
- 下一最小实验：若另获GPU/请求授权，固定保存的8rank输入，单变量改变总shape、目标offset、累加dtype/实际后端，证明实现命中与归约机制；再回原长Decode/C64和原正式契约验证因果。当前授权不自动覆盖新GPU测试/服务重启。
- 限制：只本模型/PPU/短freshPrefill/C8，非其他平台；完整目标张量不是全KV/GDN历史，不把候选归约顺序或未复现视为正式修复。无独立reference证明具体设备kernel错误。

### 后续因果拆分：accdiag-030，2026-10-19

- [事实记录](../../../../../models/Qwen3.8-Flash-Next/ppu/20261015-qwen38-flash-next-ppu07-master/optimize/accdiag-030-tp-reduction-order-shape-offset.md)，状态not-proven（模型修复/60K因果）；局部机制证据reproduced。原模型不改，8rank保存输入用于独立PyNccl out-of-place/native raw22703、BF16/FP32、两point/6case/三重复共72payload+1标量/rank；实际类源码SHA、400文件SHA及完整原4输出逐位吻合已核。
- 结果：固定总shape、target row0→7精确复现607805/633283元素差异(max0.0078125)；只改N→N+7或N+7→N+15、allocation基址1row、非目标行填充值均不变。FP32对应30/33元素max1.49e-8差，最后转BF16均一致且匹配FP64一次舍入参考。没有nonfinite/canary/input/crossrank/repeat错误。
- 机制：实际通信4个ring循环顺序可逐块解释全部BF16元素，首全局分界38400，target偏移17920使首差异落在targetflat20480=row8（从0计）。逐块算术可行顺序不是kernel trace，但与独立GPU offset单变量因果/原始输出逐位复现结合，支持“位置改变分块舍入”，不是该测试中索引/错行/peer污染。
- 知识差量refined：从TP/HC边界进一步区分逻辑target offset与总shape、stride、storage offset；下一检查优先固定数据/布局拆变量及累加精度。不能凭人工rank编号ring匹配不足就认定bug，应该用已记录真实通信拓扑。
- 限制：独立comm/合成背景，原模型内部具体comm分支没有新增追踪；当前shape结论不外推其他尺寸/模型/平台。测试FP32不是已接入模型修复，无新正式gate或性能收益；旧acc015164/198仍failed-score。2个0归约环境启动错误与销毁后告警保留，不混作数值事故。下一步模型精度改动/重载须用户明确范围。

### 模型迁移反证：accdiag-031，2026-10-19

- [记录](../../../../../models/Qwen3.8-Flash-Next/ppu/20261015-qwen38-flash-next-ppu07-master/optimize/accdiag-031-model-fp32-tp-reduction.md)，status=not-proven，evidence=reproduced（局部实际模型路径）。同19请求/C8/一次8010重载，BF16显式attention/条件MLP TP改FP32归约再BF16；MoE内部自有归约不改，i64/M16保持。
- 实际all8rank FP32两侧张量与BF16 castback经720边界PT/192采样PT核验；layer0完整target postTP/HC C1-Mixed精确相同且匹配FP64一次舍入，FP32仅30/33元素max1.49e-8差。两类graph7/7、508FULL/rank、19HTTP200；无性能测量。
- 但最终doc81 logits仍max1.146484375/.9375、808概率L1=.09724（原.09232），doc71及C1重复相同。模型最终一致性目标failed，未验证长Decode/C64/正式GPQA，不宣称60K或低分修复。CPUc40eb227、Hostb884fb0e及完整SHA见事实记录。
- 知识差量refined：局部通信舍入被消除不代表模型全部数值漂移消除。下一最小检查应从已一致的layer0 post-attn之后继续找首分歧，并单列未覆盖的内部通信，而不是将剩余差异继续归因已修边界或直接叠加性能。

### MoE内部同输入归约后首差异：accdiag-033

- [记录](../../../../../models/Qwen3.8-Flash-Next/ppu/20261015-qwen38-flash-next-ppu07-master/optimize/accdiag-033-layer0-mlp-moe-boundary.md)，同19/C8、仅8010一次重载，PPU TP8/hidden2560/778、808目标行与Mixed起点7。完整8rank的MLP mix/router/topk/shared-routed局部输出/preTP均C1-Mixed同，MoE自有BF16 late TP后首次不同582781/607605元素/max.0078125；其结果跨rank相同、HC只传播。外层attention FP32 castback仍同，不能当内部MoE FP32已覆盖。
- 本次真实4ring/32旋转CPU算术可解释四份postTP全元素与每256块，支持分块舍入而非当前证据下路由/专家先变；未独立GPU重放本次MoE collective、不能把CPU拟合称kernel order实测。1536边界+192采样PT、1951文件核验及完整SHA见主记录。
- knowledge_delta=refined：检查模型显式helper之外实际拥有collective的runner，避免“局部TP精度提高等于全模型归约覆盖”。最终logits仍不同/60K因果未隔离，下一内部FP32候选未执行，无formal gate/性能结论；详见[FusedMoE证据卡](../fused_moe/case-index.md)。

- 后续[034](../../../../../models/Qwen3.8-Flash-Next/ppu/20261015-qwen38-flash-next-ppu07-master/optimize/accdiag-034-moe-internal-fp32-tp.md)仅将该MoE实例自有late归约改FP32→BF16，同19/C8/一次8010重载后局部postTP/HC与最终doc81两point logits/prob差均0；48实际dtype链、288跨033上游同值/FP64参考和1632层PT已核。证据reproduced、knowledge_delta=refined（局部候选模型迁移成功）；不代表FP32中间完全结合、其他shape/长Decode/60K/正式分数通过，未测性能、未签gate，不访问8035。精确环境及限制由FusedMoE卡和主记录维护。
