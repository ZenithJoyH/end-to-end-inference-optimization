# accdiag-052：PLE修复后10请求最小回归通过，CPU证据审计完成

2026-10-20后续正式组合验收：[acc-017](acc-017-full-gpqa-ple-fixed.md#终态177198通过正式阈值7条60k问题仍存在)同8010/Ple051＋当前FP32/i64/QSA M16组合177/198（89.39%）通过0.88阈值，198题与gate绑定核验通过；仍有7条60K reasoning-only，不推定全部旧症状已修复。本记录原10请求结果不改，非重新执行052；原8010保持运行、heartbeat已暂停。

## 目标与范围

用户要求基于修复后验证模型推理是否正常。本轮按本地inference-accuracy-evaluation `minimal-regression`，覆盖051的PLE早i64＋CTA同步修复模型集成，不做正式全量GPQA，不签formal gate。沿用PPU-07、qwen3.8-flash-opt-ppu07-20261015、模型Qwen3.8-Flash-Next、8010/物理8–15；不访问8035或物理0–7。用户上一轮明确不重启服务，本轮没有明确解除该限制；先只读预检，需要启动加载修复时先告知并等待方向。

## 当前预检

inventory及connectivity-check限定PPU-07通过。只读`ss -H -ltnp 'sport = :8010'`无listener；优化容器running，镜像sha256:67309a951e945ef8ac95e73511b7d17175b6b930a2d7f6899a1436c3d39730bc。没有推理请求可以发送至现有实例。

容器原FlagGems-vllm目录`/opt/qwen38-fgvllm-main-20261019-b4d3382/src/flaggems_vllm/ops/qwen4/ple_conv.py` SHA163ebcd33074941a65ba8767ad518a4cf38073833f4617d1e59edfe60bc4e03b，仍为修复前源码；经过051及合并测试211项验证的私有实现为`/opt/qwen38-accdiag051-ple-cta-sync-20261020/fgvllm/src/flaggems_vllm/ops/qwen4/ple_conv.py` SHA2f273afafdfd1a991dd0138b0d330d001cf0cd17bdcb96b83a22a5f3929140c0。不能把私有算子测试通过当已被模型加载，也不能把旧实例或旧分数绑定到新修复。

本轮0源码/配置更改、0启动/停止/重启、0模型请求、0GPU测试、0新远端脚本；未访问8035。结果`incomplete-service-not-running-and-fix-not-model-loaded`，不是模型推理失败或修复通过。旧acc016故障污染incomplete、acc015 failed-score及无gate不改，性能仍blocked；监控继续PAUSED。

## 待确认的最窄后续

请求仅恢复8010一次，选择已测试的051私有PLE实现并保留attention/MoE FP32、Gems i64/randn、QSA M16、normal_/index_select黑名单及固定调优，不更新其他仓库、不加新埋点，不操作其他服务。获得方向后先冻结独立回归配置、命令/身份/SHA/请求清单，核8–15资源/镜像挂载/实际依赖；执行有限两条C1＋8请求C8最小回归，检查模型最终回复、完整token、原始错误及graph capture/实际两次replay。采样和请求内容复用案例既有版本化样本，具体payload和预算在执行前冻结；此处只是待授权计划，没有启动或发送。首次异常保全原始输入/回复/token/现有状态/完整日志，停止新增请求，不自动重启或全量GPQA；没有模型级精度/性能结论。

## 用户授权一次8010启动与10条请求

用户随后明确允许仅启动8010一次加载已验证PLE，保留FP32/i64/QSA M16，2C1＋8请求C8，保存raw回复/token/完整异常；不访问8035、不全量GPQA。本授权替代本实验上一阶段的“等待启动”状态，不扩大到自动重启/重试/额外预热或其他服务。Skill使用minimal-regression，服务启动前后及实际graph replay重新绑定，不套用旧gate/旧replay。

只读核8–15均无计算进程、8010无listener。复用047 runtime006启动shell，argv不变、固定调优/缓存/黑名单不改，只在PYTHONPATH增加051私有fgvllm/src、将DIAG047配置fgvllm根改为同一私有副本、日志/root指向052独立目录。现有观察器源码不改，score_requests/prompt_lengths置空以不触发旧343token/C1专用的重型QK/状态取证；保留原source/FP32/QSA、batch-binding、rank0实际采样前缀和graph replay事件，不宣称本轮有逐层或全state数值现场。PLE调用链已静态核为Plugin gpu/ple_layer.py直接from flaggems_vllm import ple_short_conv_，各prefill/decode函数均调用该符号。

冻结请求复用acc014/diagnostics/accdiag-021-prefill-layer-sampler-20261017/runtime-002/requests.json的原10项：doc2两次C1，C8为0/1/2/142/144/149/155/178，总8唯一doc/10请求。消息与采样不变：temperature1/top_p.95/top_k20/min_p0/presence0/repetition1/seed1234/max_tokens60000/原stop，return_token_ids及prompt保持；只更换X-Request-Id为accdiag052-q000..009，零重试、零隐藏HTTP预热。启动前准备核source src树除PLE外字节完全相同、原critical FP32/Gems/QSA/观察器SHA和模型metadata/tokenizer/131权重文件inventory不漂移，镜像与挂载一致、目录空间和资源通过；CPU准备不发推理。

唯一控制器CASE/commands/accdiag052-control.py SHA70da9777b2831c4c5d247980cd93cbedacfaf08b4d1ec93c5b0aa05c104b2ee5，产物R=CASE/diagnostics/accdiag-052-ple-fixed-model-20261020/runtime-001。先保存并核SHA、执行`python3 CASE/commands/accdiag052-control.py --mode prepare`，通过后只执行一次`--mode run`，排他SERVICE_START_ATTEMPT marker拒绝重复。run先仅启动已停8010一次；1800秒启动预算，失败保留原退出code/log且不自动再次启动。READY须all8实际implementation-loaded/现有probe/critical SHA/QSA M16/FP32 MoE绑定一致，native PIECEWISE/FULL capture各7/7、精确API argv/env及health/models。然后2C1顺序完整输出，核重复token与all8>=2实际graph replay后才并行8C8；HTTP timeout7200、无自动API重试，不为覆盖追加请求。

原始request字节、HTTP status/headers及流式body（异常也留已收到前缀）、完整已返回token/prompt、final/reasoning/finish/stop/think-end/EOS和日志全部保留R。首次输出/HTTP/既有observer异常停止新增派发，在途自然取证；不停止服务。终态只CPU复制已有runtime/log/配置/raw为独立快照并哈希，不将仍追加的服务日志称封闭文件；缺失响应/未捕获state如实记。10条通过也不代表原60K/正式GPQA/大索引问题全解决，不签模型gate，不恢复性能优化；此次不改kernel、不升级组件。

### CPU准备通过，拟执行唯一启动

prepare已通过：source src树唯一差异PLE；原critical、模型metadata/tokenizer及131权重inventory一致，镜像挂载及8–15空闲检查通过。PREPARED SHA49018b3ce0c56dd352636487a9383c7e20f9c25856ed3faa7d37e6adb00cd996；requests SHAf9ebae101bc43d3fe817d8185519e428c67bac44fd8a8e8c8cbb1479e15f0f71、launch SHAfe56dac53cc7901aee063ecb65293b3bfe52b9b3e961123b660c153ae2156a34、cfg SHA3a11bad9e8b8f68d0b4ad92eb0f96f4bc571be8534f8ec4f1e7c3cfec0118992。原argv含尾NUL的SHA5744d999规范已CPU核对，避免误判身份。

source-before的versions是在docker继承PYTHONPATH下收集，FlagGems metadata显示旧g85cc5efb1，**不能作为服务有效版本**；启动shell明确unset后重设。另以实际启动PYTHONPATH做CPU find_spec/metadata核验，实际Gems根为/opt/qwen38-flaggems-master-20261019-f0aa7f12/src、版本5.5.0.dev0+gf0aa7f121.env041，FGVLLM根051私有副本、Plugin根047私有副本正确；关键i64/randn/FP32/QSA字节检查仍一致。该差异是继承元数据上下文，不升级/回退安装，也不静默修订已冻结source-before原件。

仅为完整捕获driver stdout/stderr而新增CPU启动包装器CASE/commands/accdiag052-launch.py SHA08402bff4e9b1494dda862d63a4d1c1a7adeda5d2cf8f92e9534b3721bbc121d；先保存核SHA，执行`python3 CASE/commands/accdiag052-launch.py`一次，包装器排他DRIVER_LAUNCH并保存干净环境CPU解析、唯一PID/start_ticks，后台调用已冻结control.py --mode run、日志R/driver.log。它不发送推理或重复启动；只有原控制器按READY→2C1→8C8推进。SERVICE_START_ATTEMPT尚未存在，CPU prepare不消耗一次服务启动授权；后续只读监控这个唯一进程，不再launch或recover。

### 唯一启动成功，C1通过，C8在途

包装器只执行一次；唯一driver Host593321/start519643219，SERVICE_START_ATTEMPT at1792480606.4174242仅一份。READY at1792480752.5088062（15:19:12+08），API Host593716/start519643298/原argvSHA5744d999；all8运行implementation来自051 FGVLLM、047 Plugin、env041 Gems，critical SHA/实际FP32 MoE bindings/QSA M16与原有probe核验，native graph PIECEWISE/FULL各7/7。源码/埋点未更改，只切换已验证库副本和本轮配置日志。观察到本轮启动新生成047 cache下1份PLE state LLIR，含barrier与051 source-path，后续CPU审计要核i64数据流并归档；不能以旧AOT模型cache复用日志单独宣称PLE修复命中。

两C1 doc2均正常最终B、finish=stop、562tokens，完整API序列完全一致；all8实际graph replay>=2已由新运行事件验证后，原driver一次派发8个C8。最近快照4真实HTTP完成（另有C8 doc2 B508、doc0 D613），其余6在途、waiting0、preemption0，没有FIRST_ANOMALY/DRIVER_ERROR或非法访存。10全部已派发不等于10完成；不再新增/重试请求。C1结果content采用“The best answer is B”，原控制器answer字段仅识别“The correct answer is”故为空；这是诊断性答案抽取覆盖限制，不是空content/reasoning-only或HTTP错误。原raw/result不改，终态仅CPU基于真实final文本核对答案，与formal strict filter/精度gate明确区分。

完整精度Skill bundle SHA6e94a080dd3b64544c535e1fd4bda506f55516374d14d0f8ca6aa148bba2c7b2、回执SHAf0d42f77d615206c593d11458a5403e8296b9b0ccff1606b08b4e2df69f2a0d1保存R/SKILL_BUNDLE.json。首次仅inspect传capability未传selection的工具调用返回incomplete且未写文件，随后显式minimal-regression成功；没有因此改变测试模式或重新请求模型。仅前台只读监控原driver/8010，旧heartbeat保持PAUSED。

为终态准备一次CPU-only审计脚本CASE/commands/accdiag052-audit.py SHA659e6af7e3bde0a7395cf278e5d1f429e7d3e9d560701d43d01ef401760c0dec；先保存核SHA，只有FINISHED/FINAL_SUMMARY存在且原driver退出/僵尸后，执行`python3 CASE/commands/accdiag052-audit.py`一次。该脚本不发推理/GPU、不改模型或controller：校验冻结manifest、10份raw request/response/usage完整token、与同payload旧021的prompt IDs/text、rank0 non-discard采样前缀/未发API surplus，逐rank实际batch最大8；诊断性抽取best/correct-answer与gold对照而不重计formal分数。复制本启动以来现有PLE state cache模块、IR/metadata/binary并核乘前sext/64位地址乘法和CTA barrier，记录共享cache非逐rank指令trace/无模型大index现场的限制；补冻终态service/driver日志和health/metrics，保存新cpu-audit-001/report/manifest。实际已只读看到3份新state LLIR，均含sext i32→i64、409600 byte row-offset的mul nsw i64和barrier.cta.sync，指向051源码；这是本模型启动产生的编译佐证，不能把它当每rank每步或10486以上实际索引的动态追踪。若审计失败保留原工具/中间结果，不自动重试或重启服务。

### 15:36:29快照与有界后台监控

7真实HTTP完成/5唯一doc：seq0/1 doc2各B562，seq2doc0 D613、seq3doc1 B2285、seq4doc2 B508、seq6doc144 B5847、seq9doc178 A2683，均非空final/think-end/末EOS/finishstop、无HTTP错误/lengthcap。doc178 think-end位置2258、末248046，本次C8未复现提前EOS；这不是C64或全部历史问题已解决。已完成的prompt IDs/text与同payload旧021逐份相等。剩seq5doc142、seq7doc149、seq8doc155仍在长推理，rank0前缀持续推进，不以未返回正文判reasoning-only；running3/waiting0/preemption0，KV1.9%，无FIRST_ANOMALY/DRIVER_ERROR。不得在7/10时宣称整轮通过，也不把7请求当7唯一题。

按最小回归Skill的长任务监控方法，复用原heartbeat qwen3-8-ppu07-gpqa-c64，保留原30分钟频率、当前线程，更新为本052既有进程只读监控并恢复ACTIVE（产品工具确认）；不新建重复任务，不恢复旧acc016正式评测。保存prompt精确绑定R/driver/API/SHA/预算，禁止prepare/run/launch/重启/新请求/8035；仅实质进展/首异常/完成/需处理通知，无变化安静。终态只在健康通过、10份响应齐全、原driver退出且无旧cpu-audit目录时允许已冻结CPU审计一次，否则只读取证并报告缺失，不自动修复/重试；最后暂停heartbeat。监控能继续本轮有限任务，不扩大成任何正式GPQA或性能授权。完整结果尚未出来，暂记minimal incomplete，等待原3请求自然返回。

交接前最后只读快照新增seq5/doc142已正常stop完成13347tokens、issues=[]，累计8真实HTTP/6唯一doc，无FIRST_ANOMALY/DRIVER_ERROR；仅seq7/doc149与seq8/doc155仍在途。旧7/10为较早窗口，不能继续当最新进度；仍无FINISHED，不能宣称整轮通过。自动监控继续读取当前原件，不以prompt内旧日期快照替代运行事实。

## 终态：10请求回归通过，原8010保持运行

2026-10-20 16:10只读核查确认原driver593321已退出；FINAL_SUMMARY于15:40:13、FINISHED于15:40:14自然写出。固定10请求全部HTTP200完成、8唯一doc，无补发/重试/隐藏预热。两条C1 doc2均B562且完整token序列相同；随后8C8均非空最终答案、finish=stop、有think-end248069、末EOS248046；没有真实HTTP超时/失败、60K截断、提前EOS、非法内存访问或FIRST_ANOMALY。8010仍API593716/start519643298/原argvSHA5744d999，health200、running0/waiting0/KV0/preemption0，未再次启动或停止。源指纹前后完全相同；所有8rank冻结日志与终态live文件逐字相等，没有丢尾。

| C8 doc | 诊断性最终答案 | completion tokens |
|---|---|---:|
| 0 | D | 613 |
| 1 | B | 2285 |
| 2 | B | 508 |
| 142 | D | 13347 |
| 144 | B | 5847 |
| 149 | B | 14926 |
| 155 | C | 14977 |
| 178 | A | 2683 |

加两条C1共10/10答案与冻结gold相符（8/8唯一doc）。此为CPU对final文本的诊断性best/correct-answer抽取，不是正式GPQA strict-match分数；原controller的answer=null字段及raw/result均原样保留，没有重计/改写正式评分。doc178正常think-end位置2258、最终A，没有复现旧提前EOS；不由C8推断C64问题解决。

健康终态、10完整响应、原driver退出、API身份与controller/audit SHA核验后，仅执行预存`CASE/commands/accdiag052-audit.py`一次（SHA659e6af7e3bde0a7395cf278e5d1f429e7d3e9d560701d43d01ef401760c0dec），没有发推理/GPU测试或改服务。`R/cpu-audit-001/report.json`通过：10份raw SHA/usage/完整token和同payload旧021 prompt IDs/text均通过；完整API token逐条等于rank0 non-discard前缀，EOS后各多一条采样不是已发API输出。8rank实际model batch最大均8，PIECEWISE/FULL capture各7/7，终态采样日志可证实际replay每rank至少16000（下界，不当精确总次数）。请求合计prompt3607/completion56310，服务计数相符。

3份本实例启动后生成的PLE state编译模块已复制到`R/cpu-audit-001/compiled-PLE/`，`compiled-PLE-proof.json`核验051源码路径、乘前sext i32→i64、409600-byte row stride的i64乘法及CTA barrier。实际PLE SHA仍2f273afa；all8实际依赖来源、FP32 attention/MoE、env041 Gems i64/randn、QSA M16、normal_/index_select黑名单和固定调优保留。共享cache编译佐证不是每rank每步kernel trace，本轮没有证明实际模型触达PLE row10486以上或generic20972边界，也没有新增完整逐层/QK/logits/state现场。

完整服务日志关键词审查另保留启动期兼容性观察：15:17:40–42 FlagTune平台模型包的子配置含不支持的`configs` key，`mul/scalar`与`mul/broadcast_2d`显示AUTO default fallback；另有原生`vllm._C`不可导入warning。它们发生于READY之前，不是本轮HTTP失败、非法访存或PLE修复回退证据，也不能宣称所有自动调优backend命中；未下载替换配置、清缓存或重启处理。请求运行约1261.56秒仅是本次带观察器最小回归耗时，不作为性能指标。

补充只读终态复核12份当前关键源码SHA均一致；完整服务日志56条error关键词匹配中40条为上述原生导入warning、16条为上述FlagTune启动fallback，无未分类异常关键词。首次补充分类命令括号SyntaxError在Python解析阶段即退出、未访问容器或服务；修正后只读核验，不是CPU审计/模型重跑。当前案例三阶段YAML、唯一experiment ID及各优化文档链接检查通过；仓库全量记录检查仍有其他案例链接及既存过程材料迁移失败，未修改无关记录，不宣称全仓检查通过。

证据全部位于R（上文完整远端绝对目录）：原始`reqNNN-docXXX-request.raw.json`/`response.raw.json`/headers/result、`terminal-evidence-001/`、`cpu-audit-001/responses-and-token-audit.json`、编译副本及`service-final.log`/`driver-final.log`/metrics。CPU审计30份文件独立SHA/大小复核通过，全部8rank冻结日志与live终态一致。关键回执：

- FINAL_SUMMARY SHA `4a2959430c9307c54f1fac4cafb65da5be35815605cd04bc5f5318a49d7548ac`。
- FINISHED SHA `1f77d015c6ffbe081e28d77ae51a40cc4c980b3e3a52dfc478d8b6ba1ad9f2f1`；原manifest SHA `efa857f1f15e2835c3b7d9e57574aaa8b231968e2e19e9338328762f98f5211a`。
- CPU report SHA `9d0c12990e722164be0102e5a3e985d36be1f74d2e3021ccaac79752073120a7`；CPU manifest SHA `f2e710fd37bc595d4aaf2d792f12ab00cdef8f9168352bd5ff8e1acc49b83e1e`。
- source-before/source-after同SHA `ddc2b4481d7f3462369f5edc263501fd7e6bd3d4b0f2cae4339eb01eef0bbca1`。

结论：`minimal-regression passed`，只绑定本次固定2C1＋8C8和已验证PLE组合。历史acc016故障污染38/198 incomplete、acc015164/198 failed-score/no gate均不改；原C64/60K/旧043 logits差异没有由本轮排除，不能宣称正式模型精度或性能验收通过。未访问8035/其PID/health/物理0–7，未更新PR或再次改kernel。既有30分钟heartbeat已由产品确认PAUSED，保留8010运行，等待用户下一步方向，不自动全量GPQA或追加请求。
