# accdiag-034：仅MoE自有late TP改FP32→BF16

2026-10-20后续正式组合验收：[acc-017](acc-017-full-gpqa-ple-fixed.md#终态177198通过正式阈值7条60k问题仍存在)保留当前MoE FP32归约与i64/QSA M16/051 PLE，177/198（89.39%）通过0.88阈值，原生gate核验通过。仍7条60K reasoning-only，旧同前缀数值结果不改，不将组合分数归因于单项归约修复。

2026-10-19用户明确授权：仅将033确认的MoE内部TP归约改FP32后cast BF16，仅8010一次重载、固定19请求/C<=8，保留现有FP32/i64/QSA M16、完整证据，不访问8035、不全量GPQA。模式inference-accuracy-diagnosis + e2e/accuracy minimal-regression，bundle6e94a080；高风险数值候选，当前正式164/198 failed-score/no gate不改、不做性能。

## 执行前设计与门禁

- 参考033：8rank各自完整preTP C1/Mixed相同、postTP首差异max.0078125，CPU真实环逐步BF16舍入可解释；最终doc81 raw差1.15625/.84765625、808概率L1=.0671414826。原033模型9500834c/probe3cf33790保留不改。
- 当前8010基线API1170040/start509488080/argv5744d999、idle且counter9356/3596，033 driver已退出；执行前再次完整身份/source/镜像挂载/private隔离/空间核验。连接检查最初沙箱Ansible RPC工具失败，正常权限下限定PPU-07重查已passed，无目标变更，不作为模型事故。
- 选择模型shim而非通用collective：Qwen3_8FlashNextSparseMoeBlock构造后仅为其self.experts这个MoERunner实例绑定late-reduce方法，公共MoERunner源码/其他模型/共享安装不改。BF16且原late条件（非SP、TP或EP>1、fused_output尚未reduce）时cast FP32→原tensor_model_parallel_all_reduce→cast回原BF16→原truncation；early-reduced/SP/TP1与非BF16交给保存的原bound method，不重复归约，不捕获后端执行异常。幂等绑定，框架ABI/source SHA固定核验；其他模型未绑实例保持原路径。不按Host/端口/题目/模型路径选择数学分支。
- private新真实副本`/opt/qwen38-accdiag034-moe-fp32-20261019`从033复制，不改旧副本/engine/Gems/FGVLLM。原显式attention/MLP FP32 helper和QSA/i64字节保持；私有新cache隔离。回退为033私有源码和原launch配置，但不自动执行第二次重载；启动失败/真正异常停新增请求并保留现场，需用户方向。
- 沿用033范围/采样/19payload/零重试，只换opaque034header。8C1、7背景max512、4实际Mixed单token评分；目标slot7+7真实Decode须现场核验。无额外smoke/GPU微测/正式GPQA/隐藏预热。CPU覆盖BF16正例、FP32/FP16/非连续/empty/truncation/SP/TP1/pre-reduced fallback、幂等/原函数异常及无输入修改后，才唯一8010重载和唯一driver。两类graph各7/7、all8至少2实际FULL replay。
- 保留原32阶段/六doc81layer0全目标行，增加内部MoE FP32 entry/output两阶段（34×6×8=1632PT）和192实际输入/完整logits/prob/noise/RNG；首有限差/原始HTTP/token/全rank日志/SHA排他保存。增加两tap只用于证明确实先cast再归约，math不依赖诊断开关。背景轻量、共享pool不是全历史状态，不扩48层或19预算。

## 成功/停止及结论边界

分别报告局部目标（all8实际FP32 entry/reduced/BF16 castback且postTP/HC/output C1-Mixed与FP64参考）、最终目标（12评分完整raw/prob/noise及C1重复/doc71阴性与033对照）；token相同不等于分布相同。任何仍有差异如实failed/未证实，不能继续叠改；源/请求/实际Mixed不匹配记incomplete。不做正式gate或性能结论，不把短前缀一致当60K/C64不收敛已修复。

远端CASE=/mnt/nfs/users/jinghao/qwen3.8-flash/20261015-qwen38-flash-next-ppu07-container/accuracy/acc-015-full-gpqa-ppu07-c64-current-i64-qsa-20261018；D=CASE/diagnostics/accdiag-034-MoE-FP32-TP-20261019；R=D/runtime-001。命令在CASE/commands排他保存并在执行前记SHA。当前仅planned，尚未修改/重启/发新请求；heartbeat维持PAUSED，前台跟进。

执行前命令：`accdiag034-deploy.py` SHA `6f5f9dfb3cab8b4bbbf63555e2047f57635fa03258af901fd6f8ff60557ebad8`，`accdiag034-probe.py` `bbb3adf10b3fdd67867ca6a6810a710930344eab08ace5b314c5ebc655102c5a`，`accdiag034-control.py` `c47bc0ff1c19b6a11c0d9a42997e6d243024e42d03b05f4b29de2ecfafc229c1`，CPU test `f35e92e0de56a7ea9133aefeb86932682977fee26ad6c61a2a76e350fe8c7206`。先在模型容器CUDA_VISIBLE_DEVICES空/OMP-MKL1执行cpu-test参数依次为probe/deploy/033model，报告D/cpu-tests-001；其只mock/AST/CPUcompile、不发送推理。通过后Host control依次各一次`--mode prepare`（私有clone/plan/source/launch）、`--mode restart`（只精确原8010 SIGTERM，退出门禁/设备8–15检查后launch）、`--mode launch`（唯一driver自然wait→19/freeze）；任何第二次reload/新client须另获方向，失败不自动重启。

CPU57项已通过、CUDA_initialized=false；torch CPU compile期间设备可用性探测报CUDA不可用warning（可见设备0），不是GPU测试或模型故障。待实际graph验证，不将CPUcompile当设备通过。

终态后处理预存：`accdiag034-offline-audit.py` SHA `4f37881303b27c58fd831527b79168131641b57440eb4699e2d542b6cc4f3cb9`（19已返回/driver退出/FINISHED和FINAL_EVIDENCE齐全后CPU eval容器CUDA空/OMP-MKL1执行一次，核1632边界/192采样、实际FP32 entry/reduced/castback、原033对照与token/source/counter）；`accdiag034-host-final.py` SHA `4add231d3948508ef7a70682f3333048ce3e66425759fe0d7d9fb125a33c88ee`（Host只核8010/原manifest并补日志尾）。无8035访问、无额外推理或模型操作，产物排他新增，不覆盖原件。

PREPARED已生成SHA `769159df4adb811e83818fe5564dde9d59a289fdacf82359f9918a539a331974`，plan `115e640c204845dd6043b255b8b91b5822377d5a2976c09b9be6a46d1c0aeb5e`、launch `c646e22c2738f91a97d0afdd008836d185f657a90097607878161a91bf26e50b`。实际model `9ce7d6ca9e2f8581abd9ab28034d7524a9e2abbf8a182425cbd71d88da97ed34`，patch `b8deacbffb9bec2b963a408f7012a7a2696f93fe1133a2b84a4eae4c7800c61b`，runner c3537353不变；完整diff已复核，仅两新helper及目标构造器绑定，source/镜像/挂载/私有隔离门禁通过。旧8010仍idle9356/3596。接下来唯一reload，失败不再自动重载。

唯一reload已完成（ONLY8010_RELOADED_PENDING_READY）；唯一driver11:29:21+08 Host1778501/start509638760已启动，自然等待8010加载/编译/graph，再执行19。后续不再调用restart/launch/run，不重试、不触碰8035；当前尚无READY/模型请求，不将日志container PID当Host API身份。

补充终态CPU反事实审计（执行前冻结）：`accdiag034-cpu-cross033.py` SHA `32e422379beffd196fb22ac49897779ce0a2138d41c467371dad907574be6279`，仅在主CPU与Host报告已生成后CPU eval容器执行一次，新目录R/cpu-cross033-audit-001。核033/034匹配的4seq×8rank×9个preTP阶段完整目标张量/独立SHA，比较034postTP与033原8rank输入的FP64一次BF16参考，单列跳过FP32末位差后的首BF16 post-attn分歧。只读旧数据/新增报告，不改服务/埋点/请求，不把CPU参考当GPU重放；原19预算不变。

11:33:53+08 READY，实际新8010 API1767049/start509637043/原argv5744d999，两类graph7/7、8rank实际新probe来源已核。CPU57 report SHA `75100815091f8a7a0d309c4bd6a1c7d4469f641c944aa0a649cae95d326b1f13`、READY `c34090ec12ff0a71e8118b3673325f9b1c5db9e32f8e64e7e7c5ea507f56fa77`。11:35:40已19真实完成/0在途/errors0，FINISHED/FINAL_EVIDENCE生成、原driver退出；没有post-attn有限差marker/运行异常。主CPU与Host审计已各启动一次，仅核既有证据；尚未根据marker缺失宣布完整一致性通过。

## 最终结果：本轮同前缀logits与概率差异消除

`minimal-regression=passed`，严格限于冻结19/C<=8/短freshPrefix与当前诊断实例。19/19 HTTP200、0错误/重试/额外请求、max1评分及max512背景为原设计，非60K输出测试；原始HTTP/token/usage/实际rank0前缀全部匹配，9356prompt/3328generation与服务counter一致。只一次8010单SIGTERM重载、0其他服务访问；driver1778501退出，8010候选健康idle，未自动回退或续跑。

| 相同prefix的C1与Mixed对照 | 033（内部BF16 TP） | 034（内部FP32→BF16） |
|---|---:|---:|
| doc81 778最终raw logits max abs | 1.15625 | 0（逐位相同） |
| doc81 808最终raw logits max abs | .84765625 | 0（逐位相同） |
| doc81 808实际过滤概率L1 | .06714148260653019 | 0（完整向量相同） |
| MoE postTP最大差，两point | .0078125 | 0 |

- 12个评分请求所存PT的4组C1重复和4组C1/Mixed，完整raw logits/过滤后prob/实际noise逐位一致，下一token1596/4543/1596/494也同；doc71阴性不变。不是仅据下一token判一致。
- all8rank六doc81首Prefill中48份实际内部FP32输入/输出、BF16castback独立CPU核验；pre.float()==entry，reduced.bfloat16()==post，实际bound方法源SHA为本候选9ce7d6ca。6×34×8=1632层目标PT及192输入/采样PT均逐份解包/有限/SHA校验通过，实际Mixed4评分均slot7+7Decode peers，graphNONE首Prefill。
- all8两point post-attn后全部所存阶段（含MoE FP32 intermediate）C1/Mixed同值，MoE postTP跨rank相同且精确匹配8输入FP64sum最后BF16一次舍入；48份MLP HC在线输出与其保存输入的FP64公式一致。原attention FP32 reduced仍保留30/33元素max1.49e-8差，但BF16 castback/HC已同；不能宣称所有FP32中间值都逐位不变。
- 两类graph7/7 capture、all8实际FULL replay507；源前后不变、已有显式FP32 helper AST保持，private017 i64及QSA M16保持，shared engine/Gems/FGVLLM/启动共享脚本未改。

### 单变量归因补证

CPU跨033反事实审计288项（4seq×8rank×9个preTP阶段）完整目标行逐位一致，包括post-attn/mix/entry/router/两local输出/sum；034的所有32份对应postTP精确等于033原8rank输入的FP64一次BF16参考。结合033同输入BF16后不同、034仅此数学路径提高精度后局部及最终分布相同，支持本范围的批次位置数值漂移由MoE内部BF16归约舍入引入，而非通过改变router/专家局部输入掩盖。

没有新非法访存/HTTP错误/非有限/输入错位/observer异常；没有FIRST_POST_ATTN_DIFFERENCE034，因此不能伪造新异常state。原全局FIRST_DIFFERENCE034为已知attention FP32末位差，其reference/current/marker仍按原件保留。1632层PT、192完整logits/prob/noise/RNG/input PT、19raw HTTP/token、全8rank及service/driver日志、源与请求SHA均保全；不是全48层/全KV历史状态。

### 原生证据

R=上述runtime-001，原件不覆盖：

- `cpu-boundary-audit-001/report.json` SHA `dce66d1daad7dd77f0ce3d6b1eb7be2b833b6c8db924c975ee87e33f9b30afbd`，manifest `c83782cccfa5d7cae11fd35399d4c110944b632fbfe636b7f78f2ef215d5a2bc`。
- `post-controller-audit-001/report.json` SHA `78c8d9127f5bdcc925c45af1751d3d7368069418e7638b9a325d0b8301ee68b0`，manifest `b877170b04d9352db64855545176ec458e7d836f6403981ebaed7e4e42c612b0`；2011个原manifest文件核验，唯一活service日志追加仅在原前缀SHA相同后另冻完整尾部。
- `cpu-cross033-audit-001/report.json` SHA `02df3e5c0fb5e9457ffaaa872f53b254bdb207367a611a1397c88d0c80a680c9`，manifest `3c21bfc42c0b528a88fdd00a918e91aea5fe00bd67de1f83a06c6ea9ab7b1815`。
- FINAL_EVIDENCE `33c12924d78b58e9cef9e78ac39efcca6a1775bc682218f90a96f46fcf6f6ecb`、FINISHED `67c3cc7aac7247b06a26de9c12fa778a20773fb610d356892761c729eaa08333`，READY/requests/model/patch/命令SHA见上文。

## 决策、限制与下一步

当前8010保留034私有诊断候选，不自动做第二次重载/追加推理/修改共享start-model.sh。回退入口为033原私有目录与原launch，若需要先核新实例并另获重载方向，不能对旧PID操作。跨平台硬件、其他shape/dtype的GPU数值/graph、量化/EP/SP与非目标模型仅CPU/静态边界或未测，不宣称硬件全通过；PR准备experimental，未提交/推送。

本轮消除了**所测短同前缀C1/Mixed**差异，但没有重跑60K/C64长轨迹和正式198题；短评分think-end/EOS实际prob均0，不能据此解释其长序列概率或恢复原11个length cap/提前EOS。旧acc015164/198 failed-score/no gate不改、正式性能仍阻塞。只保留局部修复证据与下一验证建议，长Decode/C64/全量GPQA须用户另给范围，不自动扩大。

knowledge_delta=refined：从033“内部同输入、BF16归约后先变”推进到“仅提高该实际拥有者的归约精度，288项相同上游/参考补证且最终logits/prob批次差消除”。下次需先枚举模型外层和runner内部collective所有权，再用真实FP32两侧及最终分布验证，不能以一处helper或同token代全模型覆盖。总体低分/60K根因仍not-isolated，无新formal gate或性能收益。

收尾复核：三份报告/manifest原SHA仍一致，内容5/10/2文件逐份重哈希（无self-entry）；全8rank实际IndexFunction/IndexPutFunction的i64验证及两源码SHA再次核验。当前8010原READY身份/argv不变、health200、running/waiting/preemption均0、counter9356/3328未新增推理；原driver退出、没有8035访问。state YAML范围/19-C8/一次重载/result0差值字段校验与git diff --check通过，未提交/推送。前台终态，不恢复旧heartbeat或自动扩大评测。
