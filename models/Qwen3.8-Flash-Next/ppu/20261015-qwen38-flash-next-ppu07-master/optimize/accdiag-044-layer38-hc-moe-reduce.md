# accdiag-044：第38层HC mix/router/专家与内部TP归约

2026-10-19后续反向隔离见[accdiag-045](accdiag-045-rollback044-first-request.md)：仅撤044新增观察、保持043原字节与FP32/i64/M16并一次8010重载后，固定两C1首NaN未复现，all8完整logits/prob逐位相同/token1596；但与043参考raw仍max1.1875（与本轮044有限第二条max4.0625）。这仅加强044诊断变体关联，cache/新实例也是变量，无再启用/机制证据，不确认具体tap根因；本文件首NaN现场和failed结论不改。045无C8/两次实际replay，不替代本轮未覆盖的doc81/38层内部或原正式精度。

2026-10-19用户明确授权仅8010补充第38层窄埋点并重启一次，复用19请求/C<=8，保留FP32归约/i64/QSA M16、保存首次差异完整证据、不访问8035、不全量GPQA。按inference-accuracy-diagnosis及e2e/accuracy minimal-regression执行。旧acc015164/198 failed/no gate/性能阻塞保持，不签新正式gate或性能结论。

**终态：唯一授权重启已使用，仅完成2/19，首条C1 doc71全部8rank的logits/概率均NaN，客户端按既定异常门禁停止；第二条同前缀恢复有限值但与043参考logits仍不同。doc81/Mixed与第38层内部张量均not-covered，本轮不能回答原38层首差根因。** 原始2请求/完整token/32PT/完整日志和编译产物已保全，CPU与Host审计完成。8010保留本轮同实例、health200/idle但数值回归未通过，未自动恢复/重启/补剩余17条；FP32/i64/QSA M16源保持，不访问8035/全量GPQA，等待用户新方向。

## 假设、边界与计划

043在doc81两个前缀/all8rank定位首个完整目标区间差异layer38/output-block row254-channel1407、1BF16ULP；末token后续层及LM-head前hidden/logits不同，但38层MLP HC mix/router/专家及FP32内部中间值未存，具体kernel根因unknown。本轮仅观察，不做数值修复；有界参数化诊断根据opaque请求映射和结构layer38选择，不能变成按GPQA答案或题号特化的模型计算。

目标PPU-07，容器qwen3.8-flash-opt-ppu07-20261015，8010 TP8物理8–15；8035和物理0–7完全不查询/操作。新私有`/opt/qwen38-accdiag044-layer38-20261019`复刻当前数学基线Plugin，保留043层/LM-head观察，追加layer38 HC mix输入/输出、router logits/topk、共享/路由专家输出以及FP32 cast-in→allreduce→castback各边界。优先现有custom-op与model-owned MoE实例hook，不改vLLM安装、Gems/FGVLLM、权重/tokenizer、共享脚本、算法/采样或其他模型默认。必须核实际MoE ABI及函数来源；数学等价CPU/AST证明与反例通过后才重启。观察屏障/同步可能改变融合，未复现不是修复、边界差异不是算子错误。

只执行一次精确当前8010 SIGTERM，原树自然退出及卡8–15资源门禁后唯一启动；原优化容器不重启，不升级kill。当前预期API2199565/start511947447/argv5744d999、counter9356/3596，执行前重新核验；源漂移/非空闲/身份不符则停止，不追杀历史PID。新脚本先排他保存在CASE/commands并核SHA，再prepare→restart→唯一launch。

CASE=/mnt/nfs/users/jinghao/qwen3.8-flash/20261015-qwen38-flash-next-ppu07-container/accuracy/acc-015-full-gpqa-ppu07-c64-current-i64-qsa-20261018；R=CASE/diagnostics/accdiag-044-layer38-hc-moe-reduce-20261019/runtime-001。payload复用043的19条，仅opaqueheader044：8C1评分max1、7背景max512、4实际Mixed评分max1，0重试、无额外smoke/warmup，原seed1234/temp1/top_p.95/top_k20/min_p0/penalties0与1/stop/tokenIDs不变。六doc81目标完整层内张量（778/808各C1两次/Mixed一次）；背景仅原轻量metadata/采样前缀。全部实际Mixed须slot7/7真实Decode/完整freshprefix；两类graph7/7及all8至少2真实replay。有限首差冻结并通知、仍完成预冻结19；真实HTTP/非有限/输入绑定/observer异常停补位、在途自然取证，禁止自动重启或追加。

层内完整目标区间张量逐份保存并SHA，first marker排他记录原时刻、stage/8rank/请求slot/shape/stride/storage与两侧完整reference/current；保留19原始HTTP bytes/完整token/96完整logits-prob-noise-RNG、完整可读日志与编译产物。逐rank预算043边界4GiB+新增层内2GiB，Host自由空间门禁96GiB；超预算明确incomplete，不删证据。共享专家/路由专家合并后的输出不是每个expert内部GEMM张量，缺失不夸称全内部因果。

终态等待唯一driver退出、CLIENT_FINISHED/FINISHED/FINAL_EVIDENCE完整后CPU离线审计：首差/HC输入到输出/路由值/专家合并、全8rank preTP→FP32sum→BF16数值对照、首差行与末行、hidden/logits分布关系；不发推理/GPU测试。先区分舍入/shape差异与实现错误，只有独立reference及单变量闭环才确认根因。不叠加修复、重新正式精度或再次埋点/重载；结束更新同一记录/state/README。前台监控，旧heartbeat保持PAUSED。

状态planned；尚未本轮重启或发请求。回退为043源码/启动配置，未授权自动回退重载。

## 执行前脚本冻结与实现审查

当前MoERunner/router ABI纯AST重核SHA分别d11a841e/f182f307，与034一致；改用静态读取避免CPU禁卡条件下vLLM包导入探测设备失败（一次工具导入失败，不是8010/模型事故，未发推理）。仅新private模型追加7个layer38 HC/MLP tap、去除新增tap后的AST与043逐字结构相等；043旧边界保留。第38层model-owned runner/router实例wrapper观察不改opaque专家调用，保存shared/routed返回值，不称每个expert内部GEMM输出。原tp_reduction.py字节不变；仅该实例late方法插入观察阶段、仍执行同一原guard/FP32cast/allreduce/BF16cast/trunc，CPU覆盖45组dtype/guard/trunc等价情况。其他47个MoE实例与attention/helper调用不变，实际绑定在新load后另记，不用旧implementation-loaded日志冒充新窄方法来源。

新增19个完整目标区域stage：HC input/block/injection/residual/mixed/next-injection，MoE entry，router input/logits/topk weights/IDs，shared/routed local，preTP BF16、TP input/output FP32、postTP BF16、post-trunc、MLP return。相同opaque前缀reference按all8rank比较完整区域；首差后仍保留该层各阶段完整目标区域，便于离线8rank归约参考，不改原19调度或重试。有限首差marker不阻止固定19自然完成；真正异常遵循原停止补位规则。

`CASE/commands/accdiag044-{control,probe,deploy,cpu,sitecustomize}.py`执行前排他上传、编译并核SHA：control a52c56627ececb4cb386a695fc0e883e8c7392dfa2bc8e8f325c9a7873a05157；probe1d9ffe727daf881697c9c83e61d6380acad78eff5dcaf95a8f2bdb89851f94f9；deployecc32f50fdef47d514b0ee203e7125bb0da5148bcf0b29a1e76a25007f600a3a；CPUf6cca407c41b0e070f04a5cf57edd619c7a3827a65e8cb79dcaef19573ca0e32；bootstrap84397548ae7e0948c76de05b3a6564be51e02ef6513a5c85ddff2063ebc57c3d。固定accuracy bundle6e94a080dd3b64544c535e1fd4bda506f55516374d14d0f8ca6aa148bba2c7b2，显式mode minimal-regression。控制器冻结复用042 request/run/launch与043 payload，prepare→restart→launch各至多一次；只监听/health/metrics8010、不查询8035，0额外warmup。新的私有目录/缓存、完整启动脚本与回退路径保存到R，旧树与源容器不动。

准备检查纠正（尚未重启/发请求）：原control的机械生成误把R保留为旧043目录，`not R.exists()`在任何写入前正确拒绝，旧证据未改、044目录/private均未创建；原脚本保留不覆盖。新`accdiag044-control-v2.py` SHA6049bc3298c7d504dad72b88cb792b093602cc9e70ded0d9d9ba9a6f34c2eef9，精确R改为044；`accdiag044-cpu-v2.py` SHA2eaa3cd051467cedd21aeac9b7ad1f4129e2194a074e97750c2ab8bb3afe2bcc新增R/PREV隔离断言。后续唯一prepare/restart/launch/run只用v2入口，不再执行原control。此为控制脚本路径检查拒绝，不是模型/HTTP错误，不计作本轮重启或请求。

v2 prepare已通过：CPU59项/其中45组late归约等价、CUDA_initialized=false，回执e4d64298b5d06a1f853f479a4b29b2dc5af493b5156e9d867d1d8fb0663b386d；deployment7d294df46e71ac74e29a8ce9be26dfe8dfe73e88dadd4f5882472230ea38890d，模型7f07d15e7e4e5a618e6f62f0c2d789ee0a67b3b4f2fe9856dd0694f0dec412f2。PREPARED b88620bf957325b6dac777066a4d891cc10bd05bdeafa62e4d2d538bb75a2a3c，requests8e9fd284eeb9ba2fcbb11679d0fbcaa6f3752e55e34052df5901533be2dabbd4；仅旧043 Plugin model.py新增观察语句，helper/Gems/FGVLLM字节保持。完整launch-service.sh已冻结/语法检查通过，原CLI/卡8–15/graph/显存/QSA-only/blacklist不变，仅private、诊断配置与独立cache变更，PYTHONPATH无旧Gems覆盖。接下来v2 `--mode restart`唯一一次、成功后v2 `--mode launch`唯一一次；失败不重复/升级kill，不新增模型请求。

唯一restart已成功执行（ONLY8010_RELOADED_PENDING_READY），旧043 API2199565单SIGTERM后原树自然退出；唯一launch已返回Host driver3175772，新服务/控制器完整身份以R原件为准。目前等待本次8worker/两类graph/真实窄hook来源门禁，不得再执行restart/launch/run或修改已加载脚本/源码。前台只监控原进程，首次异常先通知、仅继续取证。

终态后处理脚本预存（不加载到服务）：`CASE/commands/accdiag044-audit.py` SHA39269b3b1a2e05368952e19eaa8734bfaffe534f20fdb1536011cd237a937ca3，仅FINISHED/FINAL齐全且原driver退出后CPU/CUDA_VISIBLE_DEVICES空/OMP-MKL1执行一次，排他写`cpu-internal-audit-001/`。核7056旧边界+192输入采样+912新增内部PT/64组分布，以及608组层内C1比较；全8rankFP32输入对FP64求和、FP32顺序/树参考和gamma7误差包络、castback/trunc、实际head选行；包络内不等于已证明collective实现正确。`accdiag044-host-final.py` SHA4b0d1a6e7fb11291bec7f74a34b696f5f1a2e98ac741a41eafa575baa65da424在CPU报告后仅一次核绑定/来源/冻结文件、补8rank完整日志尾、核编译archive逐成员与FXdtype，不发推理/信号/访问8035。任何审计工具失败保留ERROR，不自动重推理或改模型。

## 首次异常与提前终态（尚待失败范围CPU核验）

最新只读快照于21:12:36+08返回，原始标记保留实际18:39时刻，不用晚收到快照的时间冒充首异常时间。READY18:39:11+08，新API3170010/start512161050/原argv5744d999，两类capture7/7、all8窄hook与critical来源已确认；首次实际C1 doc71 seq0于18:39:41.250338+08/rank6/step1触发actual-sampler-invalid（invalid-probabilities/invalid-raw-logits）。客户端自然停止新增，仅已派发seq0/1两条返回、errors0；CLIENT_FINISHED18:39:43 status stopped-first-marker，FINISHED18:40:46 error=null/FINAL_EVIDENCE齐全，不代表数值通过。

doc81与Mixed均未执行，层边界/内部PT均0，故19阶段定位not-covered；不得宣称捕获layer38完整现场、把先前043层差当本轮，或推定旧低分根因已确认。已立即向用户报告非有限采样事实与范围缺失，不补发剩余17条/不再重启或改已加载probe。与新埋点/编译时序的关系suspected，不能未经对照认定模型固有错误或某个算子故障。

原完整19审计前提不满足，不执行。另存失败范围CPU脚本`accdiag044-failure-audit.py` SHA8f7b6aadfe56089bcc6fffcbe61aa1dfe4f4c92fc017d76f8cb460e87dacaa34，只读原2请求/32输入采样PT及frozen SHA，排他写cpu-failure-audit-001；随后`accdiag044-host-failure-final.py` SHAc6f0ff6d3241467314bde04fa4ddfeda17753992c1278f0226b61e8b2a556ad2绑定该失败报告、补全8rank和service日志、核编译缓存与当前8010身份，排他写post-controller-audit-001。两者仅CPU/Host取证，无新推理/信号/8035访问；原正常范围审计脚本保留未执行，不覆盖旧记录。

CPU失败范围审计已核全部32PT/113原始文件：seq0所有8rank的248320个raw logits及概率均NaN，token0；seq1同前缀所有8rank恢复有限值、token1596。两条HTTP200、finish length（原max1）、prompt343各/输出1各，总686prompt/2completion；不是网络超时/60K问题。报告8138bb5106e15626e05c63e2021af575bc88887f34dc5cefe9c938328c2a28cb，manifestd85688b16d54888b6c41cdc2046d0e8c501fcd23818a0330970965a68643a67f，CUDA_initialized=false。Host补全日志/12984编译成员SHA、全8rank FX96f32 branch+2bf16 embedding，未回退成BF16分支归约；archive0d5daa7dc4917b67b508a54daa5d528704b6a23c9faf584d261dac4350ad2d04。Host报告085505c0757add0c69749a4901ddde874890e6eb1e8c4cd17187646333bdea3d，manifest9a3d5b17cc6df35f91c1798b6d5ca419c7a99a944dac0482ddda712eeea82c03；源前后相同，原driver退出、8010精确当前实例health200/running0/waiting0/preemption0，health绿不代表数值通过。

另预存仅CPU同前缀对照`CASE/commands/accdiag044-same-prefix-audit.py` SHA1d32b8583b28bd18d71a45e50126bf5f940798dcec0bb7786a2accc300b1ca1e，排他写cpu-same-prefix-audit-001；只读旧043首条有限reference与本轮两条的实际输入、位置/选行、seed/RNG/noise及logits，不运行模型/新增埋点/重启。用于区分稳定有限舍入与首请求时序问题，不以两次先后现象证明初始化因果。

## 同前缀离线对照与最终判定

48份旧/新输入及采样PT逐份SHA/尺寸核验。全8rank：044 seq0与seq1 payload、实际input IDs/positions/query/logits-row、initial seed、RNG-before与实际exponential-noise均相同，但前者raw/prob全NaN、后者有限。因此不能用提示变化、目标行偏移或采样随机性解释本轮两条差异；NaN已在采样前raw logits出现。043 seq0有限reference与044 seq1也具有上述相同输入/RNG条件，raw logits有247334项不同/max3.783203125；过滤后概率与token1596相同不等于前向分布或hidden正确，不称第二条“恢复正确”。两次C1对照没有Mixed、没有60K，不推断推理不收敛或原GPQA错误已解决。

同前缀报告`R/cpu-same-prefix-audit-001/report.json` SHA6b61a3064c2e7583b979d7c9907ef0e4da3c3b8db2cead36666da73a53c58851，manifest0c03f9cdf5b35e9a603e518597cd366514e9a9e226933b540ae18de66b8d7b0f，CUDA_initialized=false、新模型执行0。首次异常原件`R/runtime/FIRST_ANOMALY.json`及首rank6 sampler PT SHA d987c27f5e2bc03923ba5bab3cd08b3c7957bce73844289e560554b30f5b58fe保留；seq0 raw HTTP SHA7baab7a103154383b31214f29845adf5d5a575b353e4f3144bc0d382eb8ba0d2，seq1 ad850953e7ace859078ec95de536fbcfcd3d3cf08a497308066e48aa73288f7e。

判定：minimal-regression **failed（nonfinite前向）**，原第38层诊断范围**incomplete/not-covered**，非正式精度/性能结论。新增诊断变体相对043引入了更大的数值异常，但观察屏障/实例wrapper/编译缓存/初始化及内存时序一起变化，未有撤销再启用的单变量闭环，`root_cause_confidence=unconfirmed`，不能点名HC、MoE、TP、QSA、i64或编译器根因。首条doc71不在六doc81逐层focus内，故**没有首NaN层/内部状态/PT**，这是明确证据缺口，不用043旧张量补造现场。仅能保全已产生的原始HTTP/完整token/actual-input及全logits-prob-noise-RNG/完整可读日志与编译产物；没有“完整内部因果现场”。

下一步优先隔离新增诊断变体（例如先回退本轮新增38层tap/late wrapper但保留FP32/i64/M16，在明确的新短scope验证首条行为），如需要再次8010重载或增加首请求前向探针必须向用户申请，**当前不执行**。不把首/次请求现象自动归为冷启动问题，也不以追加warmup绕过异常。旧heartbeat保持PAUSED、服务未自动停止或回退，无新gate。`pr_readiness=experimental-debug-only`；本轮MoE内部not-covered，`operator_knowledge_delta=none`，不修改算子稳定结论或声称正式性能可恢复。
