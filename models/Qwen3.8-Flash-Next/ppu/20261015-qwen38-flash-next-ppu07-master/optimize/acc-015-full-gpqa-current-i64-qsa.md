# acc-015：同实例 i64 + QSA M16 + probe021-v2 全量GPQA

2026-10-18终态：正式198题已完整完成，strict-match **164/198=82.83%<88%**，判定failed-score，无gate。11条提前EOS、11条60K截断，共22空final，另12条有正文但答案错误；无真实HTTP超时或新非法访问证据。14:23终态审计通过、原heartbeat已产品确认PAUSED，服务未改，等待用户方向。以下运行中快照保留为历史，不表示当前仍在评测。

## 冻结契约

PPU-07，模型容器qwen3.8-flash-opt-ppu07-20261015，8010/TP8物理8–15。精确task gpqa_diamond_generative_cot，198唯一doc/limit0/C64，exact_match,strict-match阈值0.88；temperature1/top_p.95/top_k20/min_p0/presence0/repetition1/max_gen_toks60000，evaluator seed42、API默认seed1234/原stop；API retries3/eval retries0/timeout7200。return_token_ids/return_prompt_text保留。新规定镜像评测容器qwen38-eval-ppu07-acc015-c64-20261018、新UUID/容器本地SQLite缓存，不复用旧响应或分数。

09:02:44只读：8010 API2623908/start494912777/argvSHA5744d999、8035保护4161238/start487889425/argvSHA91849d0b原绑定health200，running/waiting0，prompt53903/generation1614690与旧终态一致，无其他GPQA进程；用户目录规范路径不变、root/mode0700、空闲7435GiB。i64及QSA M16保留，实际Plugin为private021-v2，不用旧019 manifest冒充。

## 执行前命令与证据

CASE=/mnt/nfs/users/jinghao/qwen3.8-flash/20261015-qwen38-flash-next-ppu07-container/accuracy/acc-015-full-gpqa-ppu07-c64-current-i64-qsa-20261018。

预存本地/tmp/acc015-20261018-controller.py→CASE/commands/acc015.py，SHA9e0a2b7dafca8426d8965e742508c32d61fdd04453e2cb127465630469a8a247；source probe /tmp/acc015-20261018-source.py→CASE/commands/source_probe.py，SHA44f3d9a691816487446416a4b40e134d76befbe1ccf90017071061562527ec16。本地py_compile通过，控制器无模型停止/重启代码。

初始部署精确断言CASE不存在，再以0700创建CASE/commands，只传入上述控制文件和预存部署脚本；不覆盖旧目录。部署脚本复制同版本旧bundle（formal d345525c、acceptance06e4a035、sample_validation9799f2df、原test/Accuracy_test/llmrun.py82cf6e83，与当前仓库一致）并核验；不改旧bundle或评测实现。

预存执行：python3 CASE/commands/acc015.py --mode prepare，仅准备新eval容器/真实source/current service/image/mount/graph证据、两次无推理provenance与schema3契约、--preflight-only。通过后复用原30min heartbeat并执行--mode launch一次，唯一子进程--mode run调用维护formal_accuracy.py包装原始runner。正式运行不自动重复，native API3/eval0重试不变。

## 证据限制与终态规则

旧observer仍在accdiag021/runtime002，保留accdiag022 STOP_DISPATCH/8rank first-state，不清除、不当本轮异常。新CASE冻结journal byte/inode和非journal旧file size/mtime及marker SHA，仅取新窗口和新增/变化文件；旧快照原样保存。本轮无新GPU首次state冻结能力、无C64逐层hidden/logits全向量；native lm-eval INFO包含完整解析后的API response/token IDs，不称wire bytes。需新埋点/重启先告用户并等授权。

继续收集全部错答/空final/length，不因单题异常重跑。终态核验198唯一题、真实模型/配置/源码/服务前后绑定：有效score>=.88才由acceptance工具签发gate；低分failed、故障/证据不足incomplete。保存native results/samples、raw API对象/token、日志和gate或失败证据；去重doc不拿多filter行数代进度，None→TIMEOUT占位与真实HTTP错误分开。复用monitor仅实质进展/首次异常/停滞/终态通知，终态暂停，无依据不估ETA。旧176/198及局部128不替代本轮结果。

## 已启动与初始核查

部署/prepare均成功，无失败正式尝试。PREPARED09:08:13，SHA`98e9bf8dd1830c827afff5683614754f6b7d28fbfd4ac23cc62bf39b973226cd`；两次provenance完全一致，SHA`c39228d57fd391a9f723496f54fa2fb3f0d7aeb17810a2edf63559152dc63523`，dataset_revision `content-sha256:167548b01bcfd7d38d0eb80bb01bd1e6dded4d3aa14b41a4bdba0beb5423dadc`与旧固定198题内容一致；offline cache提示只是来源说明，未改数据。

当前service manifest SHA`726697214582e7607bf42012ce6f78dadbe3776dd64598e1b615b6c942e32c4b`，实际source-before `8d139ffc3918b172386773f8525c5050ecabd49dc04dd2f8e61f6ad503b58773`，完整Plugin/Gems/FGVLLM/installed vLLM树与accdiag022冻结组合一致；新observer byte boundary SHA`9bd5233bb51960ce32e6449b81c419f313fc45a297391f075c18c49313d20469`。config SHA`c7f49d4063f0950b97bae87508fb2b054a291d7f744ba37fc09761317c86b30e`，contract SHA`e3802be664084e7500a3a0295c20b7f1b1d59e171435c7257d101dedd31f605b`。accuracy Skill完整bundle `6e94a080dd3b64544c535e1fd4bda506f55516374d14d0f8ca6aa148bba2c7b2`，receipt位于CASE/evidence/accuracy-skill-bundle.json；本地inspect显式selection=formal-gate验证通过。首次仅漏填selection的bundle工具调用为CPU元数据检查，无评测或模型请求，随后显式模式通过，不作为正式失败尝试。

原heartbeat在启动前更新同ID`qwen3-8-ppu07-gpqa-c64`、新name Qwen3.8 PPU07 acc015 full GPQA C64、产品确认ACTIVE，保留原30min、同会话，只读/实质变化通知、禁止重复launch。09:09:24仅一次--mode launch，唯一controller Host3314096/start500159093，FORMAL_STARTED09:09:26/198/C64；native evaluator Host3317628与helper3317630属于同一次原生runner进程链，无第二个正式评测。UUID`c4dbee4b69d94b35b6e5a31f98763835`，native初始缓存命中0、remaining198，原始结果根CASE/results/Qwen3.8-Flash-Next-ppu07-acc015-c64-current-i64-qsa/c4dbee4b69d94b35b6e5a31f98763835/。

09:10:53双health200、8035原argv SHA不变，8010 running64/waiting0/preemptions0、prompt78657/generation1633895；已从native INFO日志观察2个不同API响应ID，均非空content/stop/完整token记录，无HTTP/客户端错误。这里只报API响应，不把未映射缓存响应或多filter行数当完成唯一题数。native metadata显示do_sample=False警告；已只读核验实际openai-chat-completions `_create_payload`会pop该不支持的字段并原样保留temperature1/其他gen_kwargs，不因此把服务当greedy或更改配置。helper排除None的子集计分不能代正式结果。

当前result=incomplete/running、score/gate null；等待原native正式完成，不新增推理/重启/代码/采样修改或重跑。记录保留埋点同步及继承旧freeze的环境限制，不能把本轮测量当无诊断环境或性能结果。

## 2026-10-18 09:40首轮heartbeat：新提前EOS，正式评测继续

09:40:22已103个native API响应、10空final，全部finish stop、2–99tokens、无think-end且末token248046，不是length60000或日志中的网络超时。09:41只读按旧正式198题的完整user-content与本轮返回prompt_text精确匹配，105响应→105唯一doc，无未匹配/歧义/重复doc；10空final对应doc76/77/78/86/92/98/101/102/109/110，token数2/99/24/14/14/4/5/57/5/2。最早native UTC日志01:12:29，即09:12:29+08，doc76/id chatcmpl-a4d6757a9c0a88a2。prompt455的异常在本轮映射为doc86，不能凭长度当作doc178。

已即时通知用户出现新提前EOS，正式评测按预冻结规则继续，不停/不重跑。helper completed100、matched90、strict86/90排除了None，不能作为正式分数。09:40 running64/waiting0/preemption0/KV39.96%，双服务原绑定health200，controller/eval/helper均在、无HTTP/客户端错误，暂无最终results/samples；已耗时约31分钟，不估ETA。

首异常保全仅CPU读取已有日志：本地预存/tmp/acc015-output-snapshot-001.py，部署到CASE/commands/acc015-output-snapshot-001.py后核SHA，再执行`python3 CASE/commands/acc015-output-snapshot-001.py`一次，排他新建CASE/diagnostics/output-health-001，保存native日志固定前缀、10条完整解析API对象/原始native日志行/token、当前新observer byte窗口与索引/状态/原始采样前缀及SHA，不发推理、不改任何模型或marker。实际冻结晚于原响应，不称在09:12数值偏离时已抓GPU现场；旧accdiag022 STOP/state保留且继承快照不冒充本轮。脚本及执行SHA在执行回执补记。

### 首异常快照执行回执与机制边界

CPU脚本SHA`7213acba3a1a6648c4abce6ba7d6942b1403e8422658e8b0b6c493d9a800a522`远端与本地一致，唯一执行成功。09:42:43快照105响应/105唯一doc，映射参考旧同一198题native samples的完整user-content，逐条唯一匹配本轮returned prompt_text，无未映射/歧义/重复；进度不是多filter行数，也没有排除None。输出目录CASE/diagnostics/output-health-001，report SHA`439ac094a006fc79ceab196c0a87b3b35b46a2ec88de2285733f1ac2331b3adc`、manifest SHA`f97e4eb69726e858dcbbd8f303c748098f4460f2d30cd1a1e3d6afdc34d630c3`；33文件、固定日志窗口1215585476bytes，逐文件SHA/大小独立复核无不一致。包含原始native日志行、10条完整解析API response/prompt/token、当前8rank新增窗口和service新窗口；不含新GPU state或C64 hidden/logits全向量。另保留rank-1旧CPU诊断日志（新窗口为空），不计入8TP覆盖。

最早异常doc76/id`chatcmpl-a4d6757a9c0a88a2`，实际engine后缀`-ab33dac6`；全8rank首Prefill step82530、slot63/computed0、63个peer computed>0，643prompt+63Decode=706tokens/graphNONE；step82531实际采样[271,248046]，reasoning仅两个换行、无think-end/content。10条完整API tokens逐token等于rank0 non-discard已采样前缀，另一个post-sampler198尾token不称已发出。各rank新anomaly均10条`EOS-without-final-token-prefix`，不是新index/state故障；旧FIRST/STOP不覆盖、不清除。其余异常回复中出现模板/表格片段（如doc77系统角色模板、doc101的`|im_start|`），不等同于题目已得到答案但解析器漏取，底层偏离仍not-isolated。

模型generic真实路径本轮首次跨20972：全8rank step81702，epoch1792285781.5779（09:09:41.5779+08），gather index22630/row stride102400，i64 offset2317312000、反事实signed i32=-1977655296；byte区间[9269255680,9269648896)合法。当前快照各rank gather/scatter max分别26584/28912/28912/28912/28912/28912/28912/28912，max28912的i64 offset2960588800、反事实i32=-1334378496，byte区间[11842362880,11842756096)在27751628800bytes storage内，effective_address_bits64且verified_i64_before_multiply=true。各文件按读取时点先后冻结，max不同不作rank数值分歧。首次异常doc76首Prefill实际generic index26046，同样i64 offset2667110400、地址合法、clear index0，无operator-post mismatch。

packed本来i64的真实device indices最大25752/25752/26580/26580/26580/26580/26580/26580，与generic分开；全部8rank invalid/nonfinite/mismatch0，parse errors0。当前源码四关键SHA再核不变（probe f7c50b23、Gems index15ddfe41/index_putd8422ca2、QSA M16 3bb3d083）。因此本轮已覆盖大索引，同时仍有提前EOS；不能以反事实i32_overflow=true认定新非法访问，也不能只因未报索引/状态错就排除所有GDN/graph数值路径。无新全逐层/logits/GPU首次state，机制归因尚不闭环，需在正式终态后由用户决定是否新的受控定位；本轮不自动扩展或改服务。

09:44:10仍running64/waiting0/preemption0/KV44.2142%，prompt124181/generation2567249持续推进，无CLIENT_ERROR/FINAL_SUMMARY/FINISHED，native最终results/samples尚未生成。双服务身份/health正常，正式分数仍pending、无gate，旧helper86/90不得冒充当前正式得分。首次提前EOS与首次大索引跨界已通知；继续同一ACTIVE heartbeat和唯一原生正式进程，不中断/重试/重跑/新增推理/重启/修改埋点。

## 2026-10-18 10:12监控：doc178再次提前EOS

10:11:50只读核验162个native API响应，完整user-content精确匹配162唯一doc，无歧义/重复/解析错误；空final增至11，新增doc178/id `chatcmpl-8f85dd6b74f696cb`，原始native UTC01:46:10（09:46:10+08），11tokens/finish stop、无248069、末248046，reasoning为`|\n\nThe problem is to find the best algorithm`，content null。不是60K截断或真实HTTP超时。已即时告知用户；当前native正式分数仍pending，不能从helper排除None后的分母报告正式分数。

双服务原PID/start/argv SHA均不变且health200；controller/evaluator/helper在，8010 running36/waiting0/preemption0/KV52.3557%，prompt133618/generation3261446。最近formal日志10:09:59，空闲7431GiB，暂无CLIENT_ERROR/exit/FINAL_SUMMARY/FINISHED/results/samples，进度在推进，不估ETA。

执行前预存CPU-only证据补冻脚本`/tmp/acc015-output-snapshot-002-doc178.py`→`CASE/commands/acc015-output-snapshot-002-doc178.py`，SHA `82248e4ef6c77174e9de1b7345358498ef1192e60e744b24cf467c11ac363387`。它断言原001 freezer SHA不变，只以透明的三个常量/筛选替换生成排他新目录`CASE/diagnostics/output-health-002-doc178`，冻结现有日志固定前缀、doc178解析API/原始native行/完整tokens、8rank已有新窗口、实际Prefill/采样前缀/索引状态及manifest；不覆盖001、不改marker、不发推理或操作服务。只执行一次`python3 CASE/commands/acc015-output-snapshot-002-doc178.py`，旧首次state已继承、没有新的GPU逐层/logit现场等限制不变。执行与SHA核验回执随后追加。

### doc178补冻回执

唯一CPU补冻成功，快照10:13:14，仍162响应/162唯一doc。`output-health-002-doc178/report.json` SHA `9589249180f49b67a77d28646d73db9b98b81f2d0fc8dfb8fa6ddc8d809ccecb`，manifest SHA `f0e34770899214d483842a5dcb5615a3b67fbd72cc96b1d1b84227593695f468`；15文件、固定日志窗口2188834086bytes，独立重算逐文件SHA/大小无不一致。原001与正式进程/源码/旧marker均未改。

doc178 engine ID `chatcmpl-8f85dd6b74f696cb-9728c428`，全8rank首Prefill step97433、slot63/computed0、63peer computed>0、455prompt+63Decode=518tokens、graphNONE。实际完整API tokens `[91,271,760,3377,369,310,1423,279,1786,11767,248046]` 与rank0 non-discard采样前缀逐token一致，额外post-sampler尾198不是已发出API token。这是模型已采样出不相关文本并提前EOS，非单纯评分器漏提取或最终答案被reasoning parser藏住；首个数值偏离位置仍未知。

每rank该step共108次GDN gather/clear/scatter记录（36层×3），索引/地址/storage均合法且i64实现核验通过；各层实际gather索引范围911–30580，clear0。当前整轮8rank generic gather/scatter最大32884、stride102400，i64元素偏移3367321600，对照signed-i32=-927645696，byte[13469294080,13469687296)位于27751628800bytes storage内；packed原生i64实际device最大32775。8rank均EOS异常11条，索引invalid/nonfinite/state mismatch0，日志解析错误0。反事实i32_overflow不是新非法访问；不能以未报错排除未捕获的QSA/GDN/graph数值问题。

probe f7c50b23、index15ddfe41、index_putd8422ca2、QSA M16 3bb3d083实际源SHA再次核验一致。首次查QSA时误用不带`src/.../runtime/backend`的路径导致只读文件检查失败，随后在私有仓库定位实际`src/flaggems_vllm/runtime/backend/_thead/fused/qsa_attention.py`并核对SHA，无运行环境修改；容器无rg时只读pathlib定位，不是模型故障。没有本轮新GPU首次state、C64逐层hidden/logits，已有共享池last-writer与延迟日志冻结不能补成完整因果现场；首次症状通知未等待CPU校验完成。正式评测仍按原契约继续，分数/gate pending，不自动重启/新增推理/重跑。

## 2026-10-18 10:40监控：178/198返回，20条继续生成

10:40:17精确prompt_text内容映射178个API响应→178唯一doc，无重复/歧义/未映射/解析错误，较上轮新增16题返回。已耗时5451秒（约91分钟）；未返回doc为27/48/64/69/71/79/81/88/90/94/115/121/127/130/145/147/162/164/185/186，与running20相符，不把在途无content当reasoning-only终态。11条提前EOS空final保持不变（含doc178），目前无完成的60K length cap，未见真实HTTP/网络超时或客户端错误。

8010与8035原PID/start/argv SHA和health200均不变，原controller/evaluator/helper仍在；waiting0/preemption0/KV47.9395%，prompt133618/generation3698891，较10:11 generation增加437445，服务和8rank日志持续推进。formal日志最新10:39:35，空闲7428.6GiB；exit/CLIENT_ERROR/FINAL_SUMMARY/FINISHED和最终results/samples均未出现，仅有native progress_score。仍无正式分数/gate，helper排除None的局部分数不采用，无依据不估ETA。

只读扫描从已冻结002各rank end_byte之后到本次固定EOF的新窗口，8rank新增anomaly/invalid/nonfinite/mismatch均0，完整行解析错误0；最后step按顺序读取为126285/126289/126293/126296/126300/126303/126307/126310，非同步采样不当rank分歧。generic gather/scatter最大仍32884，row stride102400、i64偏移3367321600、反事实signed-i32=-927645696，byte[13469294080,13469687296)在storage27751628800内；packed原i64设备索引最大32775，独立记录。probe/index/index_put/QSA四实际SHA再核一致。未产生新异常，不重复拷贝约GB现场，不改001/002或旧STOP/state；本轮仍无新GPU首次state/C64完整逐层logits。仅继续原正式198题及ACTIVE heartbeat，无重启/停止/补发/重跑/代码或采样修改。

## 2026-10-18 11:10监控：193/198返回，首次60K截断

11:10:04核验193响应精确映射193唯一doc，无重复/歧义/未映射/解析错误；5个在途doc130/145/147/185/186。原11提前EOS未增加；新增8条60000tokens/length/content null、无think-end，doc48/64/69/71/79/81/88/94，首次doc48/native UTC03:06:04（11:06:04+08），response `chatcmpl-a729106b26888353`，完整token数量与usage一致。空final合计19；该8条是长度上限截断，不是HTTP网络超时，未见真实HTTP/客户端错误。已立即通知用户新增输出异常，继续原正式评测。

原8010/8035精确绑定health200，原controller/evaluator/helper均在；running5/waiting0/preemption0/KV15.5759%，prompt133618/generation3953289持续推进；formal日志最近11:08:57，空闲7428.2GiB，尚无exit/CLIENT_ERROR/FINAL_SUMMARY/FINISHED及最终results/samples，分数/gate pending。

按精度定位流程仅CPU保全已存在产物。执行前预存`/tmp/acc015-output-snapshot-003-length.py`→`CASE/commands/acc015-output-snapshot-003-length.py`，SHA `32e81693d6e05311d9dea7151f5c6f2e40a9c54b8fbdfba04dc29006ac65ffd9`；断言原001 freezer SHA不变，透明替换新排他目录与length筛选，保存执行时已有的60K原始native行/完整解析API与token、8rank现有窗口及service日志固定前缀和manifest，不覆盖001/002、不发推理/改marker/改模型。仅执行一次`python3 CASE/commands/acc015-output-snapshot-003-length.py`；旧首次state继承、无新GPU首次state或完整C64逐层logits等限制不变。补冻结果另记，不将输出健康单独当正式阈值结论，不自动重启/修复/重跑。

### 60K截断补冻回执：194/198返回

唯一补冻成功，11:11:40快照194个API响应→194唯一doc，无未匹配/重复；未返回145/147/185/186。003 report SHA `01e8bb6d31c44f1bb1fbc53daff5fd8a605599e38a4c7a17ddda8c0f22f282fd`，manifest SHA `172e4c389ecaee0fb890f2f0d3abaeaf311af2860bed51bd87d15f3e08b587b6`，29文件、固定日志窗口3192373599bytes，独立逐文件SHA/大小复核通过。8条60K完整API token各自逐token等于rank0实际non-discard采样前缀，无额外采样尾，均无think-end/EOS/content；原始native日志行及完整解析response已保全，不称HTTP wire bytes。11条提前EOS仍原数，合计19空final。

8rank现有新窗口均invalid/nonfinite/mismatch0、EOS anomaly11、解析错误0，generic32884/stride102400/i64地址storage合法、packed32775不变；probe/index/index_put/QSA实际四SHA再次一致。没有新GPU首次state、C64完整hidden/logits，不能凭该快照闭合长推理根因或把截断归因于i64修复。11:11:54只读running4/waiting0、generation3958857推进，elapsed7348秒（约122分钟），暂无exit/FINAL_SUMMARY/FINISHED/native results/samples。score/gate仍null，保持原heartbeat ACTIVE，继续原评测收集剩余4条，不重启/补发/重跑/改源码或sampling。

## 2026-10-18终态核验：164/198，failed-score

本heartbeat标称11:46唤醒，实际远端只读核查时间14:19:27+08，不能将检查时间写成早先通知时刻。控制器已自然生成FINAL_SUMMARY/FINISHED；原controller/evaluator/helper均退出。原生结果时间03:28:37UTC（11:28:37+08），FINISHED epoch1792294136.3879538，score `0.8282828282828283`、164/198、阈值.88，verdict failed-score、gate null。exit1是低于冻结阈值，不是服务异常或重复失败尝试；native日志尾明确`FAIL: candidate score is below the frozen threshold`。双服务原PID/start/argvSHA仍在、health200，8010 running/waiting/KV/preemptions均0。

初步独立解析396原生filter行，strict-match/flexible-extract各198唯一doc、完整0..197，无重复doc/filter或跨filter原始doc/resps/target/arguments冲突。strict正确164、错误34；native timeout字段22是content None经评测器转为TIMEOUT占位，尚需结合完整API区分，不当22个网络超时。source-before/after JSON完整相等。原始结果及samples位于本CASE/results/Qwen3.8-Flash-Next-ppu07-acc015-c64-current-i64-qsa/c4dbee4b69d94b35b6e5a31f98763835/gpqa_diamond_generative_cot/Qwen3.8-Flash-Next/，文件时间戳`2026-10-18T03-28-37.926982`。旧176/198不替代本轮，也不能仅凭两次分数差认定某单变量导致回退。

终态CPU审计执行前预存`/tmp/acc015-terminal-audit-001.py`→`CASE/commands/acc015-terminal-audit-001.py`，SHA `e3eab49bd312c1e69f9768048b6c72956886b797a489f3a0d4fbff669d7837e8`。仅一次执行`python3 CASE/commands/acc015-terminal-audit-001.py`，排他新建`CASE/diagnostics/terminal-audit-001`。调用现有维护版校验原生provenance/config/doc/filter、核验frozen-inputs引用与observer-manifest全部文件SHA，保存已存在的22条异常解析API/原始native行/完整token、读取既有rank0采样前缀，CPU-only重新计算当前source指纹及精确服务身份；不推理、不重启、不改模型/marker，不签发低分gate。审计完成再追加准确SHA/输出分类及缺口，随后暂停原heartbeat、等待用户方向；正式阈值失败期间不叠加性能优化。

### 终态审计回执与最终决定

唯一CPU审计成功，report时间14:23:48+08；`CASE/diagnostics/terminal-audit-001/report.json` SHA `5ba94de8898eefa73d4ec9b2d28cb7f5a9cfc25d1d54fd308d3073c3a59cfe6b`，manifest SHA `2e6e31d0bada2e3bcdc675d5d664af6d97fd6deddbf727c835abd20e990827c2`。新46文件18222430bytes独立SHA/大小复验通过，控制器冻结的83份observer证据逐文件SHA均通过。已有native results/samples的task、metadata、seed42、sampling、C64/8010、limit null、新UUID缓存、原始及处理后198题内容指纹、两filter完整性全部通过维护版校验；不是排除None的helper子集分数。旧176/198仅历史比较：本轮少12题正确，但服务源码/埋点及历史负载不同，不能直接当作某一个修改的因果效果。

结果SHA `a0e39f5e0a7eae1935b5aa1d2704774dc6661c54486c9c029020f70887422993`，samples SHA `69a22ae740e45394a32b20f07fdab4e07840fb4f783c265b0ceaa5b91fadd521`。FINAL_SUMMARY SHA `cf9a647ad23be5b171bf9e34474928db30d259319f9e1ddde22024e77f559c01`，FINISHED SHA `8058f651d1ffef4c661f9efe592014ad7952a0037b91031cd7bebfe0bf8c8abe`，observer-manifest SHA `f2f1120aa4c397ae26cf8ce4771ffd598774e221700a7a436f8c7ffc56a4a800`；native正式完整日志SHA `33fcb215aa489d503140bf79fe24c7c3463c26b6e7e798fe010e43d8db4822cc`。真实结束11:28:56.387954、从FORMAL_STARTED到FINISHED8370.2677秒（2小时19分30秒），native评测8339.2256秒；晚于唤醒才执行的只读检查时间不冒充终态发生时间。

198个API响应精确一对一绑定198唯一doc，完整API usage与token长度一致；prompt79715/completion2372851精确等于本轮服务counter增量。22条空final均有完整原生API解析对象与token，并逐token匹配rank0 non-discard实际采样前缀：

- 提前EOS11题：76/77/78/86/92/98/101/102/109/110/178；2–99tokens，无think-end、末248046，post-sampler额外198不是API输出。doc178仍为11tokens，不把另一个455prompt的doc86当178。
- 60000token/length11题：48/64/69/71/79/81/88/94/145/147/185；全部无think-end/EOS，只有reasoning。后3条不在旧003快照中，终态审计已补冻它们的原始native日志行/完整解析API/token；不能用旧8caps覆盖数代替最终11。
- 另12题有最终正文但strict错误：13/17/30/85/89/90/106/113/130/160/167/171。共34错误=22无final+12其余错误。

native samples中的`timeout=22`或`<TIMEOUT>`是content None映射占位，不是网络超时；样本工具本身返回empty0/truncations0仅因为该字段层缺失，不得用它否认API层已核验的22空final/11length。原始INFO响应行是解析后的对象而非HTTP wire bytes。完整正式日志无真实HTTP/客户端异常，8rank各11条EOS-without-final-token-prefix，generic gather/scatter最大32884、stride102400/i64偏移3367321600、反事实i32=-927645696，byte[13469294080,13469687296)在storage27751628800内；packed原i64最大32775，invalid/state mismatch/nonfinite均0。仍不能排除尚未观测的逐层数值或执行路径错误。

当前完整Plugin/Gems/FGVLLM/installed-vLLM/模型及tokenizer指纹经原CPU source_probe重新计算，与source-before/source-after逐项相等；current JSON SHA `67356df76badd719e8e013723a1b3d2da42980f46c8ad962e291e6c617e3428a`不同仅为序列化缩进/排序，结构相等而非改写旧文件。原8010 API2623908/start494912777与8035保护4161238/start487889425/两argvSHA不变，health200，原controller/evaluator/helper均已退出，8010 idle。本轮始终保留017 i64+QSA M16+probe021-v2；无重启/新推理/修复/重跑。

最终判定为**有效完整正式结果failed-score**，不是缺证incomplete，也不签发低分gate。失败回执为`CASE/FINAL_SUMMARY.json`及本节审计；无run-record/gate符合维护工具仅为通过分数生成记录的设计。依inference-accuracy-diagnosis冻结证据、停止叠加性能优化，根因not-isolated；旧observer first-state/STOP继承不变，缺新GPU首次state/C64全逐层hidden-logits，不宣称完整逐层因果现场或某算子已定责。需要新的埋点/重启/复现时先向用户说明范围并等待方向。

原自动化`qwen3-8-ppu07-gpqa-c64`已通过产品automation_update确认**PAUSED**，保留原名称/prompt/30min/目标会话，不删除证据、不继续自动评测或修复。等待用户方向。
