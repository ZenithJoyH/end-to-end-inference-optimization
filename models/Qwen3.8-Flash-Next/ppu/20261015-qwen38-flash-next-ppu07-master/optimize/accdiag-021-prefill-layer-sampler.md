# accdiag-021：首轮Prefill逐层输出与真实采样分布取证

2026-10-18同实例后续正式结果：[acc-015](acc-015-full-gpqa-current-i64-qsa.md)完整198题164/198=82.83%<.88，failed-score/no gate；C64 doc178再次11token提前EOS，另10提前EOS、11个60K无final和12其他错答。probe021-v2/有效KV修正/i64/QSA M16源码及服务绑定全程不变，22条异常API tokens等于真实rank0采样前缀；本轮没有新的C64逐层hidden/logits/首次GPU state，不能拿此前正常C8 focus作C64因果现场。终态证据已审计冻结，rootnotisolated，monitor PAUSED；无再重启/新增埋点/复现/全量重跑，停止叠加性能优化并等待用户方向。

## runtime-002：有效KV检查修正与Mixed C8续跑（2026-10-17新增授权，执行前冻结）

### 19:08+08终态审计：局部通过，旧C64问题未复现而非根因已确认

10/10请求全部返回、8个唯一doc（0/1/2/142/144/149/155/178）全部答案匹配，HTTP200/正常stop/think-end/EOS均10；空content、reasoning-only、60K length、HTTP失败/真实超时、运行时非法访存/worker exception均未观察到。C1 doc2两次均B535且完整token相同；Mixed controls依次doc0 D601、doc1 B2571、doc2 B563、doc142 D15336、doc144 B4425、doc149 B4521、doc155 C7172。**doc178正常2164token、最终A（gold A）**，think-end248069位于zero-based1942，最后248046，未发生原24token提前EOS。18:44:55目标返回；最后doc142于19:02:01返回，client19:02:01.103284结束，driver19:04:14.343582完成冻结且error null，两原PID已退出。

原始产物完整根目录：`/mnt/nfs/users/jinghao/qwen3.8-flash/20261015-qwen38-flash-next-ppu07-container/accuracy/acc-014-full-gpqa-ppu07-c64-qsa-m16-i64-20261017/diagnostics/accdiag-021-prefill-layer-sampler-20261017/runtime-002`。目标HTTP原件`req009-doc178-response.raw.json` SHA `e05341c70cf7eb838a67fbab863f09be2f49e0426d33cadf6ef6db844d37f12e`；各seq原始request/headers/response/result全保留，10去重raw SHA和全部token长度与usage核验通过。不是GPQA198题成绩，不报告100%正式分数。

按已预存且SHA复核的CPU脚本仅运行一次、无新GPU/模型请求：`offline-mixed-audit.json` SHA `7aec611063fab2dbef7466e0cd1da860215493683ec0f4f022ee74cc4987367b`。8rank实际输入455IDs与旧题逐一相同，actualMixed C8绑定均为7Decode+455Prefill、graphNONE；384层output finite、96QSA有效KV/output/causal-index检查正常，文件SHA失败0。每rank首32步及正常EOS共33个实际采样记录、合计264条prob/noise argmax均匹配选中token；首32 EOS概率全0，正常最终EOS处count_before2163/step3246/EOS概率1，首32相邻RNG链无不一致。有效KV修正未屏蔽有效NaN/越界，CPU反例仍可检出；本轮padding也finite，不用它替代原96 fixture中的32308 padding NaN测试。

`FINAL_EVIDENCE.json` SHA `709fcdcf17e670a7eca7fc19ee6f902e958217ef587739052cd96fb6b4c9beb1`，9886项文件引用、56300647515bytes（含原件和冻结副本，不能当新增独立现场数）。`post-controller-audit-001/report.json` SHA `8d0e819b4f461eff20194a1819cb89e08730758ac9e0e285f52294d4f66393cd`：4905对runtime原/冻结manifest字节与SHA一致；8rank旧冻结日志均与终态完整原件逐字节相等，无尾部追加丢失，并再存完整日志/服务/driver输出。Host可读driver ring已保存，exit0；不保证全历史或其他服务故障归因。完整逐层取证只覆盖目标首Prefill、采样全向量只覆盖首32及EOS，其他轨迹为原生token/journal与共享pool有界last-writer，不冒充旧正式C64全程逐层因果。

19:08:25终态核验：8010仍2623908/start494912777，8035仍原保护4161238/start487889425，双health200；8010 running/waiting/KV/preemption均0，3607prompt+38423generation精确等于10份raw usage，无额外推理。新probe/模型/i64双SHA与启动时一致；8rank实际Index/IndexPut load64-before-multiply运行证据保留。此次heartbeat未发任何信号、未改服务/源码/采样，未重跑全量GPQA。

结论：观察器有效KV检查修正的本次**minimal-regression scoped passed**；原doc178 C64提前EOS在R1 C1和R2 Mixed C8均not-reproduced，**root cause仍not-isolated**。缺旧C64首Prefill hidden/logits/prob和匹配负载对照，opaque taps/新编译缓存/调试同步会改变执行边界，不能因本次正常就称采样、QSA、GDN或graph根因已确认/已修复。新诊断源码/实例无formal gate、无性能验收，不自动扩大请求或恢复性能优化。现有heartbeat在本轮终态记录后暂停，等待用户方向；原176/198历史formal保持不改写。

### 以下为18:42及更早历史进展

终态清理：产品工具已确认`qwen3-8-ppu07-gpqa-c64`状态**PAUSED**，保留原prompt/名称/周期字段，未创建新monitor。后续无自动请求、重载、修复、性能测试或全量GPQA，等待用户另行方向。

### 18:42+08在途结果（不是终态或新gate）

18:39:23 READY SHA `a564438f69cb1c6de04f2e143a73a491022378ae28ae5403f93957f33ce49673`，新API Host2623908/start494912777，8worker新probe/source确认，两类graph7/7。唯一client2712798/start494938991已启动；两C1 doc2均正常最终B/535tokens且完整序列一致，实际FULL replay每rank已超过2次。新535与R1的538不同，缓存根目录/重编译过程也不同，不能因此声称数值根因或性能收益。

10条计划请求已全部派发、截至18:42:33完成4条/2唯一doc（doc2三次及doc0一次），6在途/errors0；已完成的4条均HTTP200/正常think-end+EOS/final匹配。doc178目标原始最终回复尚未返回，不能将其在途状态报为reasoning-only。8010/8035双health200、精确绑定不变；无R2 runtime/controller FIRST_ANOMALY或DRIVER_ERROR。

目标实际request=`chatcmpl-accdiag021r2-tap-b-9154a4a3`；8rank `actual-model-input`一致：slot7，target start7/end462，computed0/scheduled455，7个peer computed=[298,307,328,547,256,404,419]且每条schedule1，**真实7Decode+455Prefill=462、graphNONE**，不是只用提交前并发数冒充Mixed。每rank610份PT已在manifest，含首Prefill逐层/状态/QSA和首32采样，后续EOS单独追加。12×8=96份QSA-after的kv_validity复读：有效KV与output nonfinite0、selected最大454/非法负数/超序列/超causal均0；本次unused padding也恰好finite，不以“本次没有padding NaN”替代CPU反例测试。

8rank各首32实际token完全一致，首token1596，EOS248046过滤后概率始终0，旧异常首token91在本轮首步概率0；实际prob/noise argmax256条均与选中token匹配。IndexFunction及IndexPutFunction在8rank均报告`verified_i64_load_before_multiply=true`和原017 SHA，输入索引仍int32不等于地址32位。当前没有出现旧24token提前EOS，但最终输出仍待返回，原C64根因仍not-isolated。

CPU容器内的一次临时只读检查在完成上述张量/health输出后因该容器不安装`ss`退出；此为检查工具缺失，不是HTTP/模型故障，未启动/重试模型请求。随后Host侧`ss`与/proc双核验确认8010新实例/8035原保护实例及health均不变。完整source-audit SHA `d7205737da57aa40cc70bedc56f24704cbb8089073d93f51b15d18bd673e801c`。只继续现有driver/client，首真实异常按原冻结规则取证，终态CPU/Host审计脚本已预存且远端SHA匹配。

### 新授权与执行前契约（以下为较早阶段）

用户明确授权修正有效KV区域检查、再次仅重载8010补Mixed C8，保留i64，首真实异常保全证据并通知，不影响8035、不跑全量GPQA。原runtime-001及其首次marker/3条响应/所有SHA保持不变。新产物为同一D下`runtime-002`，新私有目录`/opt/qwen38-accdiag021-prefill-v2-20261017`；Plugin从当前021完整复制且字节不变，仅观察器替换。该修正不改变QSA/采样/模型数学；vLLM磁盘源码、017双i64文件、019 QSA M16均保持。

新预算：最多10个新增请求/C<=8/0重试/最多1次仅8010重载，和旧3条分开计数。两条doc2 C1后，启动7个对照0/1/2/142/144/149/155，实际观察7条均Decode才提交第8条doc178；目标首Prefill必须另核验7条peer computed>0且schedule1，否则标记Mixed未覆盖，不能冒充成功。原payload/seed1234/stop/max60000不变，新增不重复opaque request ID。首真实异常停止新派发，已在途自然收集；不自动追加或重启。性能not_run、无新formal gate。

有效KV策略：完整raw key/value pages（包括未写尾部）照常保存，附有效token mask、physical page/shape/stride/storage描述、实际seq长度及selected索引。只扫描已写有效token和实际output的finite；未写padding NaN仅观察。selected<-1、超序列、超causal row、非法physical page仍异常，不能通过mask忽略错误索引。实际KV边界以computed+本次query及main.seq_lens双重核对；不固定页大小400或只按doc178长度写死。

CPU-only测试：从R1保存的8rank×12QSA文件加载真实输入，检查新策略不误报padding、输入不变；注入有效KV NaN/Inf、output NaN、selected越序列/未来/非法负数、seq绑定漂移均必须被检出。该CPU测试不创建GPU上下文，不发送推理。沿用原mock的tap不改值、概率/noise与RNG不变检查，均通过才进行prepare/重载。

当前只读核验8010 API2000737/start494732818、8035保护4161238/start487889425，均health200；8010 idle/counter1097prompt+4417generation，旧client/driver已退出。canonical BASE不变、root owner/mode700、可用8.05TB。精确原8010树才允许SIGTERM；8035/物理0–7禁止信号。保持镜像与/mnt单挂载原样。

执行副本均预存`CASE/commands/`，不覆盖旧版：`accdiag021-control-v3.py --case CASE --mode prepare`（无服务操作）→检查部署/CPU/source→同脚本`--mode restart`一次→`accdiag021-driver-v3.py --case CASE`唯一后台driver接续wait/client/freeze，无自动重启。CPU命令为现有CPU评测容器空CUDA/一线程运行`accdiag021-kv-cpu-test-v3.py --probe .../accdiag021-probe-v3.py --old-root D/runtime-001 --output D/runtime002-kv-cpu-test.json`以及原`accdiag021-cpu-test-v2.py --probe ...v3.py`；所有原始日志排他新建。

| 新脚本 | SHA256 |
|---|---|
| control-v3 | adb6360b38c3a75f31fa419113ec4284889fdc9635dcb53bc2634f2d0bbd2944 |
| deploy-v3 | 66e7f54d9dc6c71767b146b33c87da9b621b94ef3c128e0c11c2bcada5c3e0e2 |
| driver-v3 | 36e3418d156ec1fe3a59f1482b29c6a3aa7c09fd6a916b0e27013ee4dd6d4d55 |
| kv-cpu-test-v3 | 6b99434a3847df752cf48514912cf5a2f0ad43a0997c2ca96b0dc845c92fcd5c |
| probe-v3 | f7c50b23161363bcfe9a3647ea1662ee6d004661dd3c02cfcf9c361a866d84f7 |
| source-audit-v3 | 2892d967ca2b37ce4131e26849d1ec7fb1c0208e076e135a4ca70e6bbfe9ece5 |

工程状态experimental-private-instrumentation；非目标模型/平台不加载本task观察器，未做其他硬件测试。回退需另授权8010重载，不能由driver自动执行。原formal176/198历史有效但不绑定新private/实例。以下为runtime001不可变历史结论。

runtime002执行前门禁已通过：CPU回执`D/runtime002-kv-cpu-test.json` SHA `e7e895d26ee1d0c77f16a34d069c0cfb3e8eb1bab8810f698c6612f3a716b010`，96真实QSA fixture有效区域均正常、32308未写padding非有限值保留且不报，9项注入/边界反例通过；7项helper/mock检查通过。新PREPARED SHA `01d26c6d826e7ce8a9b1967d8e082c68906f7eaa6bf0df1390651adb2a2bb94f`、10请求清单 SHA `d92525dc73bff3ab5dfec17b14bc21f01a52bf622509de189e8de70de998a6d0`、launch SHA `4151a778acb2b0bad31297ffbb7d7f100e75cb1412d403ffb70ff7aee542699b`。source-audit-v3证明新Plugin450文件tree仍1865bdd3（与R1完全相同），engine/Gems/FGVLLM/019Plugin完整tree同原formal，只有新observer finite检查与Mixed绑定检查不同；017双i64和M16源码未改。精度minimal bundle SHA仍6e94a080…。此时prepare仅私有复制/配置落盘、未重启/发请求，随后按上面保存命令执行一次restart，不能自动再重载。

18:34:57+08仅向原8010 API2000737发送一次SIGTERM，精确原树自然退出，无额外KILL；18:35:00恢复启动，`stop-receipt.json`保留。唯一driver2637766/start494916753于18:35:41启动，脚本SHA36e3418d；只wait→client→freeze，无自动重载/重试。8035原4161238持续保护。原旧路径PYTHONPATH行在launch后被新的私有021-v2+017 Gems路径显式覆盖，最终实际导入由8rank来源证明，而非前面无效export行推断。monitor原ID复用ACTIVE、30min只读实质变化通知，终态暂停。

追加两份**CPU/Host只读取证**脚本，执行前预存`CASE/commands`：`accdiag021-offline-mixed-v3.py` SHA `e1b9e15b35d7e20951f6d8829a181a08ed05af63efa39ed27897437dc355afae`，现有CPU评测容器空CUDA/一线程，`--root R2 --probe CASE/commands/accdiag021-probe-v3.py`，仅在现有目标PT/回复取证后排他生成`R2/offline-mixed-audit.json`，检查8rank实际455prompt及7Decode peers、384层output、有效KV/selected边界、真实prob/noise/RNG；不重新推理/抽样。`accdiag021-terminal-audit-v3.py` SHA `6bf3ddf2e6e243245c429620054f6b69dae79501c2eeff6f0bf153e80639744f`，Host `python3 ... --root R2`，只在driver/client均退出且FINAL_EVIDENCE存在后执行，核验去重rawSHA/tokenusage/服务计数、8rank冻结日志前缀和完整追加、当前READY精确绑定/i64。排他新建post-controller-audit-001，不覆盖旧freeze；不具备重启/发请求功能。缺失最终返回或last-writer状态不冒充完整因果现场。

## 当前结论（2026-10-17 18:24+08终态审计）

已按授权仅8010重载一次、保留i64与QSA M16；3/11请求实际派发且全部完成、2唯一doc，doc178 C1正常3341token/最终A，未复现旧24token提前EOS。48层×8rank完整首轮output有限，实际输入455 IDs与旧正式相同，真实logits及首32步/正常EOS的概率/noise/RNG、完整HTTP/token和日志已冻结。首次标记确认是观察器对未写KV padding未mask，非有效QSA计算NaN证据；按计划停止新派发，Mixed C8未覆盖，minimal-regression整体incomplete而非正式精度failed。

原问题root-cause仍not-isolated，不宣称修复/全量精度通过；本轮没有重跑GPQA或新gate。8010诊断实例2000737/start494732818保留health200且idle，8035原4161238绑定及health200不变。client/driver退出，heartbeat产品确认PAUSED。若补Mixed C8，先需修正仅有效KV区域检查，再取得用户对**再次仅8010重载及新冻结小范围请求**的方向；本轮不自动执行。以下保留准备/执行记录，早期“尚未”仅代表对应时点。

## 授权、身份与边界

用户2026-10-17明确批准仅8010增加定点埋点并重启、保留64位索引修复、小范围复现、首次异常冻结完整已有证据，不影响8035、不跑全量GPQA。使用inference-accuracy-diagnosis（request/output-health）与inference-accuracy-evaluation minimal-regression；不是性能实验或新formal gate。

变更前只读核验：PPU-07/容器`qwen3.8-flash-opt-ppu07-20261015`，8010 API4022615/start487850554/argvSHA5744d99971adc1f0e9c1885acb61cd9910ccc7fd7adb84f33a11d009702c007e，health200、running/waiting0、生成计数2479000；8035保护4161238/start487889425/argvSHA91849d0b77b52d602a9ffc0ce9dbb608667ce127ce61cc8a0474883e334ffc0c，不操作其服务/容器/物理0–7。连接检查已仅限PPU-07通过（首次sandbox内Ansible RPC失败，提权后实际inventory连接验证成功）。

沿用原优化容器谱系/挂载，重新比较当前inspect与旧passed清单；不新建容器或挂载。模型为`/mnt/cpfs/models/Qwen3.8-Flash-Next`，TP8物理8–15、8010；Gems仍用私有017的index.py SHA15ddfe412f1b121c19583e0145231876a7aaf574d351ad555b4046553f1fcfa1与index_put.py SHAd8422ca29589ae93e11129578ffd881a96b90671f73037230b2bfb7b42355a01；QSA PPU M16、仅qsa/HC-PLE新覆盖禁用、原采样/graph/blacklist不变。

CASE=`/mnt/nfs/users/jinghao/qwen3.8-flash/20261015-qwen38-flash-next-ppu07-container/accuracy/acc-014-full-gpqa-ppu07-c64-qsa-m16-i64-20261017`；新D=`CASE/diagnostics/accdiag-021-prefill-layer-sampler-20261017`，R=`D/runtime-001`。控制/埋点脚本先放`CASE/commands/`并冻结SHA，私有副本位于`/opt/qwen38-accdiag021-prefill-20261017/`。不得覆盖旧freeze/gate/日志。

## 埋点设计（实验诊断，非PR候选）

沿用017观察器保留索引/清零/写回/graph/原始token证据；复制019私有Plugin到新私有021副本，仅为本服务新增有界tap，不修改vLLM磁盘源码或Gems/i64实现。复用Plugin已有custom-op/no-compile边界和ModelRunner入口；逐层tap在编译图中为保序side-effect custom op，实际不改输入张量，只在指定请求的首次Prefill、非capture执行时CPU复制。此opaque边界/CPU同步会影响fusion、时序和负载，结果仅诊断，不用于性能或声称原C64负载等价。

定点由冻结的opaque HTTP X-Request-Id及首次computed=0选择，不在模型代码嵌入doc ID/题目/答案或修改任何采样逻辑。重点捕获两个focus请求的实际device input IDs/positions/query边界/logits行映射、48层HC/PLE/attention/MLP输入输出、36层GDN卷积/门控输入和状态pre/post、12层QSA Q/K/V/选择及metadata和本请求cache页；保存每份shape/stride/dtype/绑定和SHA。实际保存范围/预算缺失必须显式记录，不能称完整逐层因果。

采样保留真实原始logits、温度/penalties后top-k/top-p入口、原生random_sample实际probs和实际exponential noise、选中token与每请求RNG前后状态；不额外抽样、不改变原概率、随机流或输出。仅首32个token或EOS步落盘完整概率/噪声，其余有界暂存用于首次异常；如实际backend不经过该原生边界则记录未覆盖并停止晋级，不用CPU重建概率冒充实际概率。

## 冻结的小范围计划

最多11个新请求、并发最多8、0重试、最多1次8010重载：C1 doc2两次（graph至少两次replay及输出一致性）→ C1 focus doc178 → 7条固定对照0/1/2/142/144/149/155先启动，确认开始Decode后再投入第8条focus doc178，形成小范围mixed C8。prompt来自原native samples逐一join，采样temperature1/top_p.95/top_k20/min_p0/presence0/repetition1/seed1234/原stop/max_tokens60000，返回完整token/prompt；不缩生成上限制造“提前EOS消失”。

首次HTTP/服务/索引/状态非有限或mismatch/异常EOS/空content/60K length/已知答案不匹配/埋点执行错误后停止新派发，已在途自然收集，不重试/自动重启。只有已保存状态/logits/概率/noise与原始回复能形成证据；未复现不能称修复，预算耗尽不自动扩C64或全量。旧176/198为历史有效formal结果；新增源码/实例后不直接绑定到本服务，不签发新gate。

状态：准备中，尚未重启或发请求。新恢复/控制命令与SHA将在执行前补入本记录；完成/失败更新同一文档/state/README。

## 执行前冻结命令与校验

5个脚本将以`scp -O`复制到`CASE/commands/`同名文件，核验后才执行。CPU/mock测试命令为`docker exec -e CUDA_VISIBLE_DEVICES= -e OMP_NUM_THREADS=1 -e MKL_NUM_THREADS=1 qwen38-eval-ppu07-acc014-c64-20261017 python CASE/commands/accdiag021-cpu-test.py --probe CASE/commands/accdiag021-probe.py`；仅证明观察函数不改值/随机流，不冒充PPU通过。随后`python3 CASE/commands/accdiag021-control.py --case CASE --mode prepare`排他创建D/R、保存实际身份/配置/清单并在未挂载私有路径复制/补入probe，**prepare不停止服务/发请求**。检查PREPARED、CPU回执与实际diff后才执行同脚本`--mode restart`一次；`accdiag021-driver.py --case CASE`只接续wait→client→freeze，无重启/重试代码，启动时保存唯一PID/start与脚本身份并拒绝重复。

| 脚本 | SHA256 |
|---|---|
| accdiag021-control.py | 38bf2598b97a28680f3e9998dc8354dade9a9ff41ea4976a8af716ca23317c1c |
| accdiag021-cpu-test.py | 1c1e447d45fc0adb8ac001d1077099c3adee7ec8b56bd1162a927abdd1135431 |
| accdiag021-deploy.py | 2e236e1205e2efef7938917d132c0ddb9c18063b9c97c6c534d2bc61be6853dc |
| accdiag021-driver.py | 0e7c2d808a5c8c96b08350db3494dfa0326650b33918549178c97105ad8e036d |
| accdiag021-probe.py | ff99ee5ea3a578be25e79bdfde2e7decb47617949bf18659505bf26d6aec66a9 |

accuracy minimal-regression bundle SHA `6e94a080dd3b64544c535e1fd4bda506f55516374d14d0f8ca6aa148bba2c7b2`，由本仓库skill_bundle.py验证；本轮不执行formal-gate。埋点文件按request/step/layer/stage排他保存，完整概率/noise只落首32步及EOS，GDN before中允许新请求未清零的旧数据且不检查未写output是否finite，以避免把未使用旧值当模型事故。

CPU mock首尝试在BF16 tap检查失败：测试隔离AST漏载`cpu`函数（以及后续noise包装需要的functools），实际probe具有这些依赖；归类test-harness错误，原`commands/accdiag021-cpu-test.log`保留，非模型事故，此时服务未重启、请求0。修正版独立`commands/accdiag021-cpu-test-v2.py` SHA `a43e8fab4b02768b4c39cd6ac4de0be1881465f9b89b2e23c2fcadf266626645`，按相同CPU-only命令运行、日志`accdiag021-cpu-test-v2.log`排他新建。probe/controller/deploy未因该测试错误修改。

修正版CPU/mock已通过7项：BF16切片/原输入不变、保存内容一致、无伪异常、noise hook幂等、选中token不变、真实prob/noise一致、RNG state不变。另在加载前静态复核发现HC.mix的residual是二元组，tap应传`hc_residual[1]`的normed Tensor（原输入已另存），不是把tuple交给Tensor schema；尚未部署/重启/推理。保留首版未执行脚本，实际执行改用以下v2：

- `accdiag021-deploy-v2.py` SHA `09143458d501b9738230dba49711224df017c67fa6da1f94652751699566d6e0`。
- `accdiag021-control-v2.py` SHA `724e60525caac5d4f8039d8b3b076ee6d81b3448382ca9070b235c71c09221c6`，同`--case CASE --mode prepare/restart`流程。
- `accdiag021-driver-v2.py` SHA `d80c6b3a909855f69e0f93b3a4dbc5adec863e1a111c0df47660e64fca56247b`，同`--case CASE`接续流程。

probe仍为ff99ee5e…，原生vLLM/Gems不变；本地全部脚本py_compile通过。上述修订仅准备期接口/测试修正，不是模型复现或第二次服务重启。

准备完成（2026-10-17 18:03:53+08）：新私有Plugin只有模型tap/末尾QSA观察器接入变动，模型SHA `eb9f096d8de0497819b8d530fea861ac41fd218e61513edc659f2ffd243d9fba`；runner仍`c3537353ca6cdf7e94d206117d0935b07ca8a5b1a3a69420b00510be926f9b28`。实际10个tap site，CPU语法通过，原i64双SHA/QSA M16/旧源码校验一致，mount_parity passed。

PREPARED SHA `96d078710f153b7619263e9ac97f4d73a53cc5ffe6445e0705faf1aea2992982`，部署回执SHA `7c0c703f31a94a6565a3223b37c1b48b3b0926158b831bc9823383b021cbfd88`；请求SHA `935ea32571931fc9de78f5b965ac73417bffc71396b4bba01409299eb649741e`，launch SHA `fa0084621e8dcdcd0b94e048d0e9f8c8a345e9149cabe3478fb862fe9864945a`，配置SHA `42ee699b6bbe347f973d8c9ce7622f392e5d27e79b4f2f351af15713809a9ede`。重载只改变私有Plugin/probe导入、诊断根与私有vLLM编译缓存，CLI/采样/Gems/TRITON kernel缓存/设备不变；记录编译/opaque tap可能改变时序/融合。下一步执行已冻结`control-v2 --mode restart`一次，先验证旧API身份、空闲和8035基准，再只对该API树发信号；失败不自动重试或动8035。

### 已执行唯一重载及后台接续

18:04:58+08只对旧API4022615发SIGTERM，18:05:01原树全部退出，仅此一个信号、未SIGKILL/未影响8035；18:05:01启动新私有副本。新API host2000737/start494732818，argvSHA仍5744d999…，就绪绑定仍须以READY/实际listener核验。18:05:36唯一driver host2013273/start494736283已启动（入口driver-v2，无重启功能），只wait→最多11请求client→freeze；未再调用任何启动器，当前模型请求0。131权重分片已加载、8rank均有probe021-runner-hooks-installed与来源SHA，18:06:50进入新缓存编译；此时尚未graph capture/READY，不能声称算子数值或复现已通过。

复用原heartbeat `qwen3-8-ppu07-gpqa-c64`，产品工具确认ACTIVE、30分钟，名称更新“Qwen3.8 PPU07 accdiag021定点取证”；只读核验当前driver/R，不启动/补发/重试/修复/重启，实质变化/首异常/终态通知、无变化安静；终态暂停。旧acc014 monitor/prompt不再用于本轮。

追加CPU-only完整源码取证脚本`commands/accdiag021-source-audit.py` SHA `d6f3686dcac8621c70e65948e0db85b20a4103c15c2e0c475cea29c9b9a8853e`。命令在模型容器内设置CUDA_VISIBLE_DEVICES空、当前新PYTHONPATH，以Python stdlib/md/find_spec检查旧Plugin/Gems/FGVLLM/engine全树与原formal source-before、私有Plugin仅模型文件变化和实际导入路径；不执行模型或GPU导入，输出新`R/source-audit.json`。该检查不新增服务/模型请求。

完整源码取证通过：原Plugin450文件tree SHA c810f8cf…、Gems12179文件256c4164…、FGVLLM1063文件f0398890…、vLLM2469文件683127c5…均与acc014 formal source-before相同。新私有Plugin450文件tree SHA `1865bdd33eafbbd71b1ebcfacaa1a3d84e91cc03f3e6f45447a6950dfffd995e`，差异集合严格仅模型文件；import解析到新Plugin/new observer与旧017 Gems/6568039 FGVLLM。安装版本torch2.10.0/vLLM0.24.0+empty/FlagTree0.7.0+ppu3.6/Gems5.5.0.dev0+g85cc5efb1.d20261015/Plugin0.0.0+g2b2fe95e2/FGVLLM0.3.0.dev1，私有Plugin/Gems无.git，包版本不能替代真实tree/SHA。18:09:08 KV容量1697538 tokens、PIECEWISE开始capture，尚无READY/CLIENT_STARTED或runtime异常；编译期间8worker仍在推进，不估ETA。

### READY与首次标记（原标记保留，不自动恢复派发）

18:09:48+08两类graph7/7、8rank probe实际来源及health/idle核验后生成READY SHA `4596ab7f0a5d9e16d97a48f3e9554bed20050c1cdc64250869d0dd2bdd2a8219`；18:09:49唯一client host2120876/start494761547启动（CLIENT_STARTED SHA `51f568789ab9839596eff3c68d619742ac5d02164c961ada3edd1c35b0c14a5a`）。完整source-audit SHA `71e3c4fbe9b3723b2dcdf21ed64b7778feabfdbce9e95efea3b2e69df6e3f7dd`。前两C1 doc2均B/538 tokens、正常think-end/stop/EOS，完整tokens一致；实际FULL replay存在，不将重编译后538与旧019的544差异当成同配置数值证明或性能收益。

18:11:18派发seq2/doc178 C1，request=`chatcmpl-accdiag021-tap-a-b78e7679`；step1081首次Prefill真实455token，graph NONE。首次排他marker为rank4/step1081/at1792231881.703678、kind observed-nonfinite，文件`runtime/rank4/focus/<request>/00001081-language_model_model_layers_3_self_attn_attn-QSA-after.pt`。现有client已停止后续派发，当前3派发/2完成/1在途、不发送Mixed C8；不自动删marker、忽略后继续或重启。

立即CPU读取首文件（map_location=cpu、weights_only=True、空CUDA、一线程）发现非有限值**只在key_pages[1]的175个和value_pages[1]的149个元素**：两页每页400tokens，长度455只用第二页0–54，bad key局部58–399、bad value56–379均在未写padding。实际page IDs62/74；QSA output未发现nonfinite。因此该首marker暂归“observer对完整未写cache页未施有效长度mask”的误报警线索，**不能认定为模型参与运算的非有限值或QSA根因**；仍须完整验证selected索引与各层输出后结论。不修改活动probe/guard以绕过停止条件。

8rank均已写610份focus PT（每rank3491928424bytes），含48层×10tap、GDN36×before/after、QSA12×before/after、实际模型输入/final和首32步sampler；仍需manifest/SHA与实际内容核验，不仅凭文件数称完整因果。初查rank0首四步真实token1596/1144/4087/5081、前三步概率1、第四步约0.65135，EOS概率0，CPU实际noise argmax与设备token一致；与原异常首token91不同，当前请求未结束，不能提前报最终答案或“已修复”。

新增CPU-only `commands/accdiag021-offline-first.py` SHA `8db0e004d75ecf95d93d98f9212dc921775e3a50d8603cdc79fe667af23975b5`，执行于现有CPU评测容器，参数`--root R`，一线程/空CUDA；只读现有PT/manifest与旧doc178 prompt IDs，排他写`R/offline-first-marker-audit.json`，检查所有被快照列入文件SHA、48层output finite、12层QSA有效/未写cache范围和selected是否越界、首32真实概率/noise与CPU top-k/top-p参考。该参考只验证保存分布，不重新采样/推理或变更模型；原始marker/文件不覆盖。

首离线统计脚本将`model-final-output`误归为`layer*-output`导致KeyError(value)，未改原始PT、未生成误导报告、无模型请求/重启。修正版`commands/accdiag021-offline-first-v2.py` SHA `0b53e0511f90b370c2992a3a711a013040b121b5dc5973b7be3a0dc9991c6dd8`仅修正文件类别筛选；以同一CPU命令运行，输出独立`offline-first-v2.log`与原计划的新报告。此为CPU分析器错误，不是模型异常；原probe/已加载源码保持不变。

### 3请求终态与CPU数据核验

18:16:10 doc178 C1自然返回，HTTP200、455prompt/3341completion、完整token数匹配usage、有1个248069/最后248046、正常stop/final A（gold A）。完整原始HTTP SHA `9e1e3d1eafd7af62520413de12da4d873c4106777d0348b5f49b5a0e14984374`，文件`req002-doc178-response.raw.json`；不像旧正式24token提前EOS，**此次C1未复现**。3/3返回健康、已知答案均匹配、零重试；client因首observer标记停后续而终态（errors0，不能将status字符串当模型失败）。Mixed C8未派发/未覆盖。18:18:23 driver冻结完成、DRIVER_FINISHED error null，无自动重载或继续请求。

CPU初审报告`offline-first-marker-audit.json` SHA `1772cefc88b51f0d59ded579bf685df8dd85ef337487886e6784ca9959a59efd`：清单列入文件SHA失败0，8rank实际input IDs均与旧正式doc178的455 IDs逐个相等；48×8=384个逐层output文件均finite，12层×8有效KV区nonfinite0/selected超出序列0，32308个nonfinite全部在未写cache padding。这确认首次告警属于观察器有效区mask缺失，不是此次QSA参与运算的NaN证据。

8rank首32步+正常EOS共264条实际概率/noise采样，CPU按保存prob/noise argmax与实际token不符0；未见采到支持集外或提前EOS。初审CPU参考出现一处step1088最大概率差0.03137869/保留集合差，继续查源码后定位到**参考操作顺序**：native先对完整原logits sort一次，再mask top-k/top-p；初审先mask非top-k再sort，会改变不稳定sort的相同logit(21.5) token1683/2781的先后顺序，在top-p边界保留不同同分token。直接按native原顺序的CPU复算该步support与概率完全一致，故不能据初审差异指控采样实现。

为全264条固化该核验，新CPU-only `commands/accdiag021-sampler-order-audit.py` SHA `54e22578d4f5330fa1c2bc5e29bd19ed0ad4081180781ee015962af81b3bdcdb`，同空CUDA/单线程评测容器、`--root R`执行，排他写`sampler-native-order-audit.json`；保留初审不覆盖。只读已有logits/prob/noise/RNG，不追加推理或重启。

native-order审计SHA `6aeeba102faa0e664ee5b5c265751944d44f0bffabad6ceb80520daaf3167194`：264条中CPU实际prob/noise argmax不符0、首32连续RNG前后链不符0。逐token标签对比仍有8条（每rank同一步count_before10）support差；进一步读取真实输入，差异只在同为logit18.75的token2725/6558（CPU保留前者、设备保留后者），两边support数均8、排序后的概率多重集最大差`2.9802322387695312e-08`。这是省略stable保证的等值logit排序选择差异，不能仅凭标签概率最大差0.0249220就判定算子数值错误；原第8步差异已由参考顺序解释，本条是同分tie选择。原始logits/prob/noise均保留，未通过改采样/seed让结果消失；也不据此断言旧C64 EOS已解释。

控制器冻结`FINAL_EVIDENCE.json` SHA `acd969ca9d70f928abba9804f4102d798db7d15f07a2632e2b16d44f9a9db0de`，10457条文件引用，运行时复制比较5202对完全一致，另rank7/events.ndjson在复制后仍有尾部追加，必须补齐，不将早期prefix当完整末尾。全部原始源仍在；driver/client原PID均已退出，8010/8035均health200且原本轮绑定不变，8010 running/waiting0、prompt1097/generation4417正好等于3份返回usage，preemption0，无监控额外推理。

追加Host CPU/std-only `commands/accdiag021-terminal-audit.py` SHA `46727fee32e574d1546b402507eb6564b3fe620ac42a620ff33d138d4f6b4073`，命令`python3 .../accdiag021-terminal-audit.py --root R`。只在两唯一进程退出且终态后执行，排他创建`R/post-controller-audit-001`；验证旧8rank冻结日志是原日志准确前缀、再复制完整8rank末尾及完整已读服务/driver日志，记录SHA/offset，其他PT复制必须与原件manifest一致。核验当前服务/保护身份、health/idle/counter及新probe/模型/i64双SHA，不发推理/信号，不覆盖旧freeze或报告。

终态审计回执`post-controller-audit-001/report.json` SHA `53d4c84ce9e8f82bf2fa7a798d83219fbd7d27aef88ae6305c6b876666216165`。5202对运行时副本的manifest字节/SHA一致；唯一rank7/events差是尾部568bytes追加，所有8rank旧副本均为当前原件准确前缀，已新冻8rank完整log及末尾，不覆盖旧freeze。总manifest所列数据56699199983bytes（含原件及冻结副本），不是只保留轻量摘要；状态选中范围/首32及EOS的采样覆盖限制如上，没有完整全程逐token层级轨迹或旧正式C64 logits。

18:24:14+08两服务identity/health、8010 idle/counter及probe/模型/i64双SHA复核通过；两原客户端/driver进程均退出，driver ring读取exit0（只称完整可读ring，不保证全部历史或归因）。doc178首32步EOS概率始终0，正常最终EOS处count_before3340、EOS概率1，8rank均一致；原正式首token91在本C1首步过滤后概率0。因此当前输入/负载下的实际分布不支持旧首token，但没有旧C64原始logits，不能区分原负载/旧状态/旧采样边界/本次opaque tap改变编译时序等影响，更不能用不同运行条件宣称根因确认。

heartbeat `qwen3-8-ppu07-gpqa-c64`已由产品工具确认PAUSED，保留本轮prompt/name/30min配置待另行授权。没有再重启/改源/补发或恢复8035；原acc014的176/198保持历史事实，不重绑到021新源码/实例。工程状态experimental instrumentation，不供PR或性能验收。
