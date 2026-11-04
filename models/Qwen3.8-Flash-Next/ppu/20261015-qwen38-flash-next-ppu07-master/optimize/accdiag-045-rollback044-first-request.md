# accdiag-045：回退044新增埋点后的首请求NaN隔离

后续用户授权的纯离线来源分析见[accdiag-046](accdiag-046-offline-cache-compile-state.md)：全8输入/RNG一致，400AOTkeys/825共同ELF代码段相同，但AOT内调优选择不同，Q/K RMSNorm归约block32/64优先suspected；缺doc71层与初始state，仍不能确认1.1875根因。046没有新模型/GPU请求/重启/埋点，不改本轮原始两请求或“首NaN未复现、跨043仍有raw差异”的结论。

2026-10-19用户授权：先回退044本轮新增埋点，仅重启8010一次，2条同前缀请求，保留FP32归约/i64修复/QSA M16，保存完整证据，不访问8035、不全量GPQA。按inference-accuracy-diagnosis与e2e/accuracy minimal-regression（显式2请求诊断范围）执行；旧164/198 failed/no gate不变，不签新formal gate/性能结论。

## 冻结对照、边界和停止规则

044首条doc71 prompt343/C1/max1在all8rank raw248320项及概率全NaN，第二条同payload/实际输入/位置/选行/seed/RNG/noise有限，但与043有限reference raw max3.7832。doc81/38层状态未覆盖，异常不能归因具体算子。本轮只撤销新增44观察：7个38层HC/MLP tap、MoE/router实例wrapper、late归约边界观察和44bootstrap；保留043既有层/LM-head观察及原FP32/helper，**不关闭所有旧诊断**，不升级任何软件或修改数学路径。

新private `/opt/qwen38-accdiag045-rollback044-20261019`完整复制043 Plugin源码与probe043/probe042/bootstrap原字节，必须逐文件等于043冻结manifest（模型ab9b1bfb、helperedab4737）。新fresh私有编译/cache与readonly017 TuningDB备份，避免复用044可变缓存；缓存/服务新实例仍是变量，不能以撤销后恢复直接确认044具体tap根因。Gems env041/三处i64与FGVLLM b4d3382/QSA M16、vLLM/权重/tokenizer/CLI/graph/显存配置保持。当前目标容器qwen3.8-flash-opt-ppu07-20261015、PPU-07/8010/物理8–15；8035和物理0–7完全不查询/操作。

当前预期API3170010/start512161050/argv5744d999，prompt686/completion2且idle，操作前重新核验。精确单SIGTERM及原树自然退出/8–15资源门禁后仅一次启动，不升级kill、不重启容器、不二次恢复；身份/来源漂移则停止。所有新脚本先保存在CASE/commands并核SHA，再prepare→restart→唯一launch各一次。旧044原始证据与代码保留，不覆盖或删除。

CASE=/mnt/nfs/users/jinghao/qwen3.8-flash/20261015-qwen38-flash-next-ppu07-container/accuracy/acc-015-full-gpqa-ppu07-c64-current-i64-qsa-20261018；R=CASE/diagnostics/accdiag-045-rollback044-first-request-20261019/runtime-001。只从044已冻结seq0/1取两条doc71同prefix/payload（仅opaque header改045），串行C1、最高2请求、0重试、无额外smoke/warmup；原seed1234/temp1/top_p.95/top_k20/min_p0/presence0/repetition1/stop/max_tokens1/返回完整tokenIDs保持。就绪后第一条是本实例第一条真实HTTP推理，第二条紧随其后；不发第三条、C8/Mixed/doc81或正式GPQA。

为隔离“仅首条NaN”，已知非有限raw/prob marker只保全/通知，不取消预冻结唯一第二条；仅在实际当前8010健康、首条HTTP正常返回、且marker严格为已知actual-sampler-invalid/nonfinite logits/prob时可继续第二条。网络/HTTP失败、非法内存访问、身份变化、输入/observer/其他异常立即停止，不重试/续发。原marker不删除/不改写；两条后自然freeze/退出，无自动修复。若第一次已失败且第二条未能发出，诚实记incomplete，不追加预算。

保存两条原始request/HTTP bytes、完整token与usage、all8实际input/position/query/logits-row、完整logits/prob/noise/RNG及impl绑定、完整可读日志/编译archive/SHA。两条预算不覆盖C8或至少两次实际graph replay，不额外扩范围补门禁，整体不宣称通用minimal-regression/正式精度通过。仅CPU对比045首/次、044首/次与043有限参考；没有新逐层状态，不称捕获首NaN算子。证据齐全且原driver退出后排他终态审计，写回同一记录/state/README；未复现仅是回退支持证据，需进一步受控再启用或机制闭环才确认根因。

执行前状态为planned；以下为冻结计划，实际终态见末节。旧heartbeat保持PAUSED，前台跟进，不创建重复monitor。

## 执行前冻结

只读核验当前8010 API3170010/start512161050/argv5744d999、health200/running0/waiting0、counter686/2，044原driver已终态，installed与private044源未漂移；未查询8035。脚本在CASE/commands排他上传再执行：`accdiag045-control.py` SHAa60d6014d32f726848c4087e50ec3330b49d224308efa509b5ee3e9af01d9c44；CPU/复制入口`accdiag045-prepare.py` SHA65c94688ace09e314fa74e24136d136efe45ef48d5fbb3ce82658e47d26b1929。control复用SHA冻结042原生request/restart/唯一launch（其guard只8010），自有run严格最多2条串行、无watch后台额外流量，已知nonfinite marker原件不改、只允许预冻结第二条；其他first/stop绝不清除或绕过。prepare先核精确新R与旧REF/PREV不同、请求343token和payload一致、再复制原043整树和bootstrap/probe原字节，未恢复44实例wrapper；不触碰旧源/证据。新launch原CLI保持、只改run路径/cache并清除DIAG044_CONFIG。精度bundle6e94a080dd3b64544c535e1fd4bda506f55516374d14d0f8ca6aa148bba2c7b2、显式minimal-regression；本地脚本编译通过。

prepare已通过：483个Plugin Python文件精确等于043冻结整树，模型ab9b1bfb/helperedab4737；三个旧bootstrap/probe原SHA相同，newprivate无probe044，CPU_CUDA_initialized=false。deployment d27a7af7f80b0048d5e3ff9bdd122f4a5f7fbe979c35c2a54b48cfc30a70e2ef；requests3ec0d255102b92c035c2092df0fb5e5919d4985fbda77a62a35c8b556d741a51；PREPARED276a292ac8c01e0d82ec54ae348ddad651189d8fd1c48fafa32d2200b5ac3627；launch a01600d05fd9dabd43718a8b193abd07bf493a8e347dd8538a01c009bd001389；CPU回执6c4ff7579920bb47aac61e2516282c08dd89e5ee8f0c81f5fa46617393b0c562。即将唯一control `--mode restart`，成功后唯一`--mode launch`；未授权任何第二重启或第三请求。

唯一restart已成功（ONLY8010_RELOADED_PENDING_READY）、原044树单SIGTERM后自然退出；唯一launch返回driver Host3394748，目前只监控其ready→固定2→freeze，不再restart/launch/run。终态前CPU脚本预存：`CASE/commands/accdiag045-audit.py` SHAdbb5b6f2b2af4348b8682aea302ea4679b91f63951f104d8b0529ec28bb69ae3，仅原driver退出/FINISHED/FINAL齐全后CPU一次写cpu-prefix-audit-001，核本轮32PT与043/044旧参考共96PT、实际输入/seed/RNG/noise、全logits/prob/token/原manifest；合法masked -Inf不误判NaN。随后`accdiag045-host-final.py` SHA331ebf37d4b24997d607f4aaac10d21479baa1c7ac99e500096da51c546d5430一次写post-controller-audit-001、补8rank及service/client日志尾、逐成员核compile archive/FX dtype且拒绝任何diag044_tap遗留。均不发推理/信号或访问8035，不把CPU审计当新模型测试。缺失/失败明确记incomplete，不重推理补证。

## 终态：两条逐位一致，首请求NaN未复现

2026-10-19 21:57:25+08 READY，21:57:57两请求完成，21:58:59控制器自然完成冻结退出。当前8010 API Host3385225/start513345302/argvSHA5744d999；原driver3394748/start513348022已退出。两条均doc71同343token前缀、串行C1/max_tokens1、HTTP200、finish_reason=length且各返回完整token `[1596]`；这里length是预冻结单token探针上限，不是60K不收敛。本轮共686 prompt/2 completion，0重试/额外预热/追加请求，唯一一次重启未重复。22:11:08+08终态health200/running0/waiting0/preemption0，保持本实例运行，未访问8035。

- 全8rank两次raw logits各248320项均有限（NaN/+Inf为0）；完整采样概率非有限为0、sum1，noise有限正数，实际prob/noise argmax均1596。无FIRST_ANOMALY。
- **首条与第二条在全部8rank的完整raw logits、actual_probs逐位一致，different=0/max_abs=0；实际input_ids/positions/query_start_loc/logits_indices/seed/RNG/noise也一致。** 该结果不是仅凭token相同推断。
- 全8rank与043的两条有限参考对比，输入/seed/RNG/noise一致，但每份raw有244308项不同、max_abs=1.1875；actual_probs逐位相同。与044的有限第二条raw247305项不同、max_abs=4.0625，actual_probs仍同；044第一条仍248320NaN，旧证据不改写。因此撤销044后首NaN未复现，但跨实例/编译缓存的前向logits差异仍存在，不能宣称数值完全恢复或38层根因已明。
- 全8运行时原48MoE FP32 helper来源与SHA核验，源码before/after相同，483Plugin文件仍精确043，无044实例hook/自定义tap遗留。各rank冻结FX为96条f32归约分支+2条bf16 embedding分支（静态站点数，非调用次数）；安装Gems i64和QSA M16关键SHA未变。两类graph capture各7/7；**实际replay计数0，两条fresh C1/max1不覆盖C8/两次replay**，未为补门禁追加请求。
- CPU一次核验本轮32份输入/采样PT与043/044参考共96PT，原始冻结96文件及原始HTTP/token绑定SHA通过；Host一次补齐8rank日志尾部、service/client完整可读日志，编译archive12656成员逐份SHA/size通过，无失败。原始reply q0 SHAa62f6855e529d14d16b900f61c16eab61a204e505376b8d680af990f7b02ad1a，q1 SHA2a23eb5eb16000aad52edf2577ee479c1d22d31b6cee12f9c603581e99f928f5；archive SHAa9092cb2a76efab5de9485e610a977534d29c524de8a8a57be03d036d28d7c86。

证据仍在上述R：`cpu-prefix-audit-001/report.json` SHA1f8c2f657aa563d3e3525b3d80373b7794eb85d8a69788edeedbfe02f51e64b3、manifest000feb9e3d9ab9c37227010e1bbf96234fafa5ea6c603ffeb548aed037b8d483；`post-controller-audit-001/report.json` SHA00e7aa615a1453ccbb17830fa5c34c13820537f0d87fa0789ede35b1b371fbfe、manifesta1ff7c7e28502275e8a45adec509f0a7471b67b9f8bb9a3f719c07bd7092b8d3。提取跨参考摘要时一次SSH `python -c`引用失败，仅shell工具错误，无远端脚本执行或模型影响；改用本地只读stdin脚本读取已有报告成功，未重执行审计或推理。

判定`rollback-first-request-NaN-not-reproduced-two-C1-only`，原非有限事件的根因置信度仍unconfirmed。仅支持044诊断变体关联，不能从移除后恢复确认具体tap因果：新服务/cache/编译也变化，未重新启用做反向验证，且没有新逐层/hidden/KV现场。本轮限定两条C1隔离完成，但通用minimal-regression因C8/实际replay范围未覆盖记incomplete，不签formal gate/性能结论。旧acc015164/198 failed/no gate及性能阻塞不变。保留FP32/i64/M16和原证据，旧heartbeat维持PAUSED；不自动追加、恢复埋点、重启或全量GPQA，进一步实验需新方向。
