# accdiag-028：doc81同前缀C1/Mixed C8首分歧层

## 授权、问题及方法

用户2026-10-18明确授权仅8010新增窄逐层埋点并重启一次；19新请求/C<=8/0重试，保留017 i64和019 QSA PPU M16，不影响8035、不全量GPQA。方法为inference-accuracy-diagnosis + inference-accuracy-evaluation minimal-regression。原acc015164/198 failed-score/no gate保持，禁止性能叠加或签新正式gate。

027终态已观察doc81完全相同778/808token输入，在采样前raw logits C1/Mixed最大差1.67578/0.91406，808点实际prob L1=.11867；C1重复精确、noise精确、实际输入/位置/slot均核验。差异尚无逐层reference，不能归咎QSA/GDN或解释60K不收敛。本轮先定位首次逐层分歧，不改模型数学或采样参数，不以有限差异自动判算子错误。

本地inventory限定PPU-07、原connectivity脚本已通过；当前只读8010仍Host3199246/start503876115/argv5744d999，8035仍Host3460404/start503952504/argv91849d0b。旧027客户端已退出；准备前仍须核idle、累计prompt9356/generation3420、完整source树、容器image67309a95/mount-parity、私有目录无挂载覆盖、磁盘owner/路径与空间。旧STOP/markers不改，新028 runtime无继承停止标记。

## 实验隔离和观察边界

CASE=/mnt/nfs/users/jinghao/qwen3.8-flash/20261015-qwen38-flash-next-ppu07-container/accuracy/acc-015-full-gpqa-ppu07-c64-current-i64-qsa-20261018。新根CASE/diagnostics/accdiag-028-doc81-layer-first-difference-20261018/runtime-001；新未挂载私有源码/opt/qwen38-accdiag028-layers-20261018。Plugin完整字节复制027，model eb9f096d/runner c3537353、Gems i64 index15ddfe41/index_putd8422ca2和QSA M16 3bb3d083不变；只改私有observer，不改engine/权重/tokenizer/共享安装。使用既有model自定义tap扩展点，背景ACTIVE空，目标首次Prefill才启用；通用index observer在该过程中仍保持轻量地址/索引检查，不扩大到全pool数值转储。实验性诊断observer非可提交PR候选，pr_readiness=experimental。

19请求payload逐条复用027原清单，仅opaque header前缀改为accdiag028。8条C1评分→7背景原prompt/512上限Decode→4评分真实Mixed C8，总19/零隐藏warmup/0重试。评分max_tokens1、原seed1234/temp1/top_p.95/top_k20/min_p0/presence0/repetition1/stop、精确token-ID completion输入。背景正常提前结束不补位，覆盖失败不扩范围。graph两类capture7/7与至少2实际FULL回放由这19条核验。实际Mixed要求slot7、target computed0/完整固定前缀、7peer computed>=原prompt且scheduled1；仅client准入不算覆盖。

仅doc81的seq4/5/6/7/17/18逐层捕获（778/808两点各2次C1+一次Mixed），doc71是阴性评分控制，背景不转储逐层PT。8rank每目标48层10frontier：input/post-ple/attn-mixed/attn-hc-residual/attn-branch/post-attn/mlp-mixed/mlp-hc-residual/mlp-branch/output，保存全部目标token行，不含7peer张量。隐藏宽2560、HC4；每rank64GiB硬预算，准备要求至少1TiB可用（只读时约6.69TiB），超预算不丢证据伪通过。正常完整应23040层PT（6×48×10×8）+192输入/采样PT；保留完整raw logits/topkp入口/actual_probs/noise/RNG/HTTP bytes/header/token。

在线按同rank/同point/同layer/stage与第一次C1比较，首次有限逐元素差异排他写FIRST_DIFFERENCE028（全局及各rank）并保存两侧PT SHA/首坐标/max/RMSE，不自动停模型或改sampling，继续收齐固定对照。非有限/输入错位/HTTP/observer/服务故障走新FIRST_ANOMALY停止派发，在途自然取证。前者是观测差异，不等于超容差bug；必须比较C1重复是否稳定，再给出按层/阶段排序的首分歧，而非把全局跨rank最早时间当数学首层。原始PT不可覆盖，终态manifest绑定全量，首次差异两侧另复制取证；共享pool selected-state仍非全池逐层历史。

## 冻结脚本与执行门禁（执行前）

| CASE/commands脚本 | SHA256 |
|---|---|
|accdiag028-probe.py|a6a00b1ab75ef4f5feea733bd223be45ea106682d5066f2cca4b14be909c292a|
|accdiag028-deploy.py|0c3e9c29054f1daf62fe436c3f92903cfcc983dc655f5cee3b8d606569d3cd77|
|accdiag028-control.py|7e9e3e3338e7d67ed593d31e007b052153c69c9ea051a318b72555ba21424cc0|
|accdiag028-cpu-test.py|5408b0cb68eaae0dfaa8bc04fc901c3c76ba9160a7c7f51c86d7b9b7611ff902|

本地py_compile通过。先排他上传核SHA，在既有CPU容器qwen38-eval-ppu07-acc015-c64-20261018（CUDA_VISIBLE_DEVICES空、OMP/MKL1）执行`python3 CASE/commands/accdiag028-cpu-test.py CASE/commands/accdiag028-probe.py`一次；仅AST纯observer验证equal/dtype/shape/首坐标、无背景文件、切片错误/重复拒绝、首差异marker不可改、index轻量上下文恢复，非GPU/真实tap证明。之后Host `python3 CASE/commands/accdiag028-control.py --case CASE --mode prepare`一次；核PREPARED/requests/config/launch/probe与source门禁后，才`--mode restart`一次和`--mode launch`一次。重载仅向精确旧8010 API单SIGTERM，等待树自然退出；不退出不追加kill/恢复，8035不在树内且全程只读保护。旧源和launch均留存回退材料，但无自动二次重启权限。首次差异立即通知事实与路径，缺失逐份列出，不用推断补齐。

目前状态：设计及脚本冻结，未部署、未重启、0本轮模型请求；根因not-isolated。后续所有事实持续更新本文/state/README，不另起历史目录。

## CPU门禁和唯一重载已执行

14项CPU正反例全部passed、CUDA未初始化。prepare通过；PREPARED `bee344e496c6a39de5258710029068386d7175dbf80dfe71b0fb646659900630`、requests `c0a444ce409c5b1910295b568bf80bca274030a2de10d93bd5902f7642c036a5`、config `64a9b9c880e82e7602b2520dc2d6cf26b3a2c898018e28c8ffa6d248d031d992`、launch `d12b4461bfdb8b9cc3599b7b28499073b7218bc572d76bdbda9e6de9f006b0a0`、DEPLOYED `687059a67f9245a3c0d68374d4aa0216b181d786af0ad6aa14c3b911d5e2e999`。源码数学/image/mount门禁全部通过，原19 payload不变仅opaque头更新。

21:22:17.523905+08仅对8010 API3199246单SIGTERM，21:22:18.564075旧11进程树自然退出、0其他信号，8035不在树内。21:22:20.217652新8010启动一次；21:22:52唯一driver Host1430400/start504559909/argv98bd0daf启动，等待READY。旧重启权限已消耗，不再restart/launch/run/发额外请求。21:23:34只读处于权重加载阶段，尚无READY/模型请求/差异marker；加载进展不估ETA，也不将启动耗时直接判停滞。

已预存终态CPU后处理设计：脚本`CASE/commands/accdiag028-offline-audit.py` SHA `fcbea8dd4defe8b4f0a63ddd51ee67cafaa6754ec67d9abda39e9c56a7578285`，本地py_compile通过。排他上传核SHA后，仅在原客户端退出、CLIENT_FINISHED/FINISHED/FINAL_EVIDENCE/FIRST_DIFFERENCE_EVIDENCE齐全时，在现有CPU容器qwen38-eval-ppu07-acc015-c64-20261018（CUDA_VISIBLE_DEVICES空、OMP/MKL1）执行一次。只读旧PT/raw/logs、排他写runtime-001/cpu-first-layer-audit-001，不发推理/GPU测试。核全部层manifest路径/大小/原生FINAL绑定、独立CPU解包每rank各point在首次分歧前及首分歧的完整目标张量、实际输入/采样向量、API/rank0/usage/source；C1全480精确结论来自在线逐元素比较，独立CPU不冒充再次重放所有未来层。若末端异常/缺失/异步冻结未齐仅记录不自动执行或重试。

## 仅控制面就绪谓词修正；不再次重启服务

当前新8010实际Host1419056/start504556673/原argv5744d999，双graph/health已正常；all8实际runner027与runner028 hook均来自新私有028、probe a6a00b1a、steps0、无raw/RUN_STARTED/STOP。原controller继承的ready仍将实际新probe与旧`commands/accdiag027-probe.py` SHA3324比较，断言被等待循环捕获，所以0请求等待并非模型编译停滞。已及时告知用户，不把ready阻塞当模型事故，不修改任何服务/已加载probe/采样或原prepare证据。

控制面修正脚本`CASE/commands/accdiag028-client-v2.py` SHA `598deca0ea4b620cd5b4a042710ff633857e5f5b28a5e2f0c43c96bde2e31538`，本地py_compile通过，AST复用已冻结控制器方法体，只将ready预期命令probe文件修正为028；实际执行driver SHA以补充字段独立绑定，原方法体SHA/原PREPARED/requests不伪改。执行前all8新hook/0步骤/0budget/精确新API及8035再次核验。依次一次`python3 <v2> halt-waiter`，仅对精确等待客户端1430400/start504559909/argv98bd0daf单SIGTERM，要求自然退出、0模型/8035信号、无observer停止marker；保留旧DRIVER_STARTED/WAIT_STARTED/CLIENT_PID/log。随后仅一次`python3 <v2> launch`启动唯一实际发请求客户端，使用新CLIENT_LAUNCH_V2/CLIENT_PID_V2/DRIVER_STARTED_V2/WAIT_STARTED_V2，不覆盖旧原件；其后只监控、不重复启动或重试模型请求。19预算仍全未用，服务重启次数仍1；此为发请求前控制面缺陷修正，不是模型重跑/二次重载或改变采样边界。

上述等待客户端已单独退出，0模型/8035信号、0observer STOP。新唯一实际客户端1686105/start504637257/argvb8d9d400、SHA598deca0，于21:35:47.690696 READY、21:35:47.728833 RUN_STARTED；新8010仍1419056/start504556673/原argv，8035仍3460404/start503952504。bothgraph7/7、all8probe a6来源已核；运行回执明确同时绑定原方法体7e9e3e33与实际补充driver598deca0。21:36:00为5派发/4完成/0错误，doc81第一C1逐层转储已实际推进至每rank约201frontier，不是只源码中存在tap；尚无首差异或真实异常，后续只监控当前进程。

## 8035再次预期停服；用户明确仅续余13条

21:37:38.511579+08保护watch发现8035无监听，排他FIRST_ANOMALY类别health-or-protected-binding-failure；是控制面保护事件，不是模型数值异常。立即向用户通知并停止新增，已在途自然收齐6/19、0HTTP错误；seq0–5完整返回（两doc81 prompt778 C1全480frontier各rank已保存且无逐元素差异），尚无808/C8背景/Mixed。21:38:03 CLIENT_FINISHED，21:39:46 FINISHED且原实际client1686105已退出。8rank各960层PT共7680；无FIRST_DIFFERENCE028/真实observer FIRST，无新非法访问。旧FINAL SHA `7fb1766eb93bd41e5c3be3b832cd7dac8ac607a391872e7e7981160f73b34b18`、FINISHED `5738285c87256ed96f3025145079dafbd7e0208f2acf714f4ee85a51673a4ff3`、FIRST_DIFFERENCE_EVIDENCE `9a46bb281efc2b775929807f8e530d80b2379dc9df34a050e93c2132d651be41`原件保留。旧selected first-state来自这次控制面STOP，不冒充未来Mixed首差异全状态。

用户明确回复“是，预期停服；更新基准后同实例续跑剩余13条，不再重启8010”。不推定可以重发前6条或增加新19预算。新client目录同028下continuation-002，实际model/observer仍runtime-001同实例1419056、a6代码/config不变；准备时冻结当下8035（当前无监听，若已由其他任务重启则冻结新精确身份）为保护基准，后续漂移仍停止新增、不对它操作。先确认旧client已退出/旧冻结齐全、metrics prompt2948/gen6/idle、原6raw及scope完整；按原SHA复制6已完成HTTP/token为明确导入旧证据，不重新请求。仅seq6–18：2 C1评分808→7背景Decode→4Mixed评分，总新增13/C<=8/0retry，两段合计19。存在人为调度间断，不声称同一无间断运行；原C1参考PT保留、驻留observer参考索引不清空。

续跑脚本`CASE/commands/accdiag028-remaining13.py` SHA `bdedaa5b1b05ee9b43b430138d6a8ea911337d8c186a750c1064dc97857d9e87`，本地py_compile通过。排他上传后仅一次`python3 <script> prepare`→核PREPARED/范围/新保护基准→一次`launch`；不暴露restart模式、不部署/改probe。AST复用原run，仅首C1循环从0:8收紧为6:8，新增submit上限13，背景8:15/Mixed15:19保持；metadata同时记录prior6/new13/combined19。ROOT旧控制面FIRST/STOP/终态不删，未来有限FIRST_DIFFERENCE独立；全量逐层/输入/采样PT已原地不可变保存，终态新增EXTERNAL_TENSOR_EVIDENCE逐份SHA/大小绑定原observer文件及manifest，首差异两侧另复制，原冻结日志只作为旧字节前缀、后续尾部单独保存，禁止改写旧manifest。先监控异步冻结补齐，不把缺失现场补造为完整。

continuation-002 PREPARED `003cb0c9be6b98883efe0837f46457a04e03c789d9645b370cf0d17b0a9dc5f1`，requests仍c0a444ce，metrics2948prompt/6gen/idle；保护8035为当时null（当前无监听）、8010精确实例未变。IMPORTED_PRIOR_SIX明示seq0–5复制SHA核验不重发，新范围只seq6–18、cap13/combined19/C8、no_reload。

因证据分为两段，预存CPU后处理修正版`CASE/commands/accdiag028-offline-continuation.py` SHA `0d15b11cdd7e484db00a1f2965596204d2d4e40d7f9752bcd84b19511d42c0c6`（本地py_compile通过），旧fcbea8dd脚本保留但不对不完整旧运行执行。仅当续跑原进程退出、CLIENT_FINISHED/FINISHED/FIRST_DIFFERENCE_EVIDENCE/EXTERNAL_TENSOR_EVIDENCE/COMBINED_SUMMARY齐全时，在既有CPU容器（CUDA空、OMP/MKL1）执行修正版一次。R=continuation-002，O=原runtime-001/runtime；导入6旧raw+13新raw有明确收据，full layers/sampler基于外部不可变PT清单，不修改旧FINAL。独立CPU验证首分歧前与首分歧全部目标行，同dtype/shape/首坐标/元素数/max应精确相同，RMSE仅允许CPU归约线程差的1e-12复核容差。所有root来源、缺失、时序差、非全量scope写清，不把分段诊断当一次无中断C8或正式精度。

21:49:11唯一余13客户端1956496/start504717818/argv0c49ed7c、bdedaa5b启动，21:49:13 READY同8010/保护8035null。21:53:15新段13全派发/5完成/8在途/0错误（旧6独立已完成，不能把新段progress当总数）；all8层PT各2518推进。第一次排他FIRST_DIFFERENCE028原epoch1792331497.5121677：rank6/step40/doc81 prompt778/seq17/Mixedslot7，layer0 post-attn，完整7966720elements中1653765不同，maxabs0.001953125、RMSE2.4789592972650748e-5，首flat81925。两侧ref q004/current q017文件与SHA均保存，当前有限差异并非FIRST_ANOMALY，未自动停止模型。数学首分歧须按各rank层/阶段排序并独立CPU复核，而非按排他时间直接认定；本层为GDN层，post-attn还覆盖TP allreduce与HC combine，不直接归因QSA/GDN kernel。

新增只读终态审计`CASE/commands/accdiag028-post-audit.py` SHA `98766aacf0175ef9c37d07473c6523cd6bcc2b3f42b70f5787bc0e0babd077d1`，与CPU最终版`accdiag028-offline-final.py` SHA `3278b880153103f0694046718cc2f28ca4229df19b570e846ba466f4b9a90b14`均本地py_compile通过。仅在新旧客户端退出/19完整且EXTERNAL/COMBINED齐全后：Host一次post-audit（只复制已有8rank/服务日志、核旧/新冻结prefix、当前8010/8035null身份、source/metrics、tensor manifest），继而CPU容器一次offline-final。原生022 freeze的binding-after无条件listener8035会对合法null状态记录read_only_check_error；不改原件，由新的独立post报告重新核验合法null基准和source/counter，CPU最终版显式读取该补充、保留旧错误。上述是CPU/Host证据检查，无推理、无GPU微测、无新埋点/重载/补发，原两个未执行CPU版本保留不混称结果。

21:55:40.664912续跑CLIENT_FINISHED：新增13/13完成、0错误/在途，结合导入旧6总19/19；原进程仍在既有freeze中，不能提前当冻结完成。在线all8rank每个doc81 Mixed点都475个frontier不同/480，最早layer0 post-attn：778点max0.001953125/RMSE2.4789592972650748e-5，808点max0.001953125/RMSE2.5146082449500684e-5；首flat81925，两点各相同。input/post-ple/attn-mixed/attn-hc-residual/attn-branch五边界在线逐元素相同，C1重复q005/q007全480无差异；因此先收敛至GDN branch输出之后的TP allreduce→HC combine区间，而不是QSA（首QSA为layer3）或已记录GDN branch输出。此为在线结果，仍待独立CPU复核所有前序及首差异完整目标行；有限差异无容差/已知正确reference不能定算子bug。所有48层后续差异与采样向量保留，未在首次finite差异后丢后续证据，也未改变stop/seed强行对齐。

## 最终结论与证据（CPU复核完成）

本轮总19/19 HTTP成功、0错误/模型请求重试、最大并发8；实际是旧段6+用户明确余13续跑，前6没有重发。仅本轮一次8010重启，续跑没有任何服务重载/埋点或sampling修改；8035只读保护，按用户确认停服后基准为null、未对其发信号。新旧实际客户端均退出，22:00:55.299582续跑FINISHED。原生旧guard FIRST/STOP和所有终态/failed binding记录保留、不伪改。新FINISHED SHA `25587912d91a3e51fcacaa5ca83c1f0d66b1b2abf5a5cc59b268114223599d7b`，EXTERNAL_TENSOR_EVIDENCE `6e362a3b660fccba5d63fe2ea79865b2c79c59078b8dd9b7c7ef5ec2ed551e9d`，COMBINED_SUMMARY `771c0ae23521838015f34c12a75080cacf9b231679a835d86aef0a29e5011815`。

完整目标层PT **23040**（每rank2880=6×48×10），实际输入/采样PT **192**，共约244.30GiB原始张量；生成时与终态freeze逐份SHA/大小核验，外部manifest绑定，首次差异两侧另复制。不是所有未来层PT都再次独立CPU解包；独立CPU解包并逐元素验证所有rank/两point在首分歧前的五边界及首分歧（192份完整目标矩阵），以及192份输入/采样PT，所有已核项通过。全480 C1重复精确结论来自在线完整逐元素比较，不冒充第二次CPU重跑所有未来层。19完整API token均匹配rank0 non-discard采样前缀，9356prompt/3420completion与服务counter一致。当前8010仍1419056/start504556673/argv5744d999、health200、idle；source前后完全相同，017 i64/QSA M16不变，8rank实际FULL回放与两类capture证据齐全。8035当前null符合新保护基准。

终态补充`continuation-002/post-controller-audit-001/report.json` SHA `403080d6c1f681f7350f13d38ae798bdff5b22c62bb3a9b095479d0dfeed6c6a`、manifest `51c23058a913f3c653e4e9caf3939e0890d43f02873e6c559a436e00ee12397f`；CPU报告`continuation-002/cpu-first-layer-audit-001/report.json` SHA `a4a5c111d0885d323d8c94b5296d19dee30cb0cfe73cfae06cc7e6038fced15f`、manifest `d4e2c12a30a6f997d721e05d707ab423d3c4fee9fad10cbef300b7e9cccc61eb`。旧/新冻结8rank日志前缀均仍完全匹配，尾部另补，不改旧活日志原始prefix回执。

**首差异层/边界已定位并独立复核**：两个完全相同前缀（778/808）在C1重复均稳定；C1→实际Mixed C8在all8rank同为layer0的`post-attn`首次不同。此前五边界整段目标行逐元素相同，包括第0层GDN本地投影分支输出和HC残差。首不同flat81925（目标token行8、展平HC特征5），值0.01031494140625→0.01019287109375；两个point最大差0.001953125、RMSE约2.48/2.51e-5。后475个frontier均传播差异，最终raw logits与概率**精确复现027**：778 maxabs1.67578125/RMSE0.30347352，808 maxabs0.9140625/RMSE0.17299367、actual prob L1=0.11866993/max差0.05782603；同noise仍采1596/494。doc71阴性控制C1/Mixed完全一致，全部C1评分重复raw/prob/noise完全相同。96份实际采样记录均符合实际probs/noise argmax→API token，非采样错行或本轮RNG变化。

准确范围是**GDN分支输出（相同）→ TP allreduce → HC combine → post-attn（首次不同）**，仍包含TP归约本身；没有单独“归约后、combine前”的观察点，故不能只凭现有证据将其中一个认定为问题，也不能宣称本目标QSA首发（第一个目标QSA在layer3）。这只是局部执行路径差异定位，不是对所有GPQA失败排除QSA或确认HC/GDN bug。小的BF16差异可能来自shape相关算法/归约顺序等，缺独立数值reference/单变量复现和原正式scope复测，**最终算子根因与60K不收敛因果仍not-isolated**。本轮短778/808 freshPrefill、C8、有CPU同步和新缓存、存在调度间断；不等同旧完整Decode/RNG/C64负载。首selected-state在旧8035 guard时已冻结，非新首差异全KV/GDN状态；本轮保存的完整输入/逐层/logits/prob/token不受该缺口补造。

下一步若要继续分开TP归约和HC合并，需要先向用户说明更窄的观察点/必要一次8010重载与新请求预算；**当前不自动添加、不重启/全量GPQA**。正式acc015164/198 failed-score/no gate不改，未修复或宣称正式精度通过/性能收益；现有heartbeat保持PAUSED，本轮前台取证终态，等待用户方向。
