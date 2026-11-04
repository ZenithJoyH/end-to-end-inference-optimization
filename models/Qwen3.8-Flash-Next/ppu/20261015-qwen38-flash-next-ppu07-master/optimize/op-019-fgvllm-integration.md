# op-019：新增FlagGems-vllm HC/PLE/QSA算子接入

2026-10-20后续正式组合验收：[acc-017](acc-017-full-gpqa-ple-fixed.md#终态177198通过正式阈值7条60k问题仍存在)实际QSA PPU M16及后续051 PLE/FP32/i64组合177/198（89.39%）通过0.88阈值，原生gate核验通过。仍7条60K reasoning-only，不改旧op019局部性能/分数，不以本轮证明所有新增算子独立通过或端到端收益。

2026-10-18后续组合正式结果：[acc-015](acc-015-full-gpqa-current-i64-qsa.md)在当前probe021-v2实例完整198题164/198=82.83%<.88，failed-score，无gate；22空final（11提前EOS/11个60K）和另12错答，原始响应/token/8rank日志/源码服务绑定已核验保全。旧acc014176/198只属旧实例/源码组合，不覆盖当前组合；分数差不是QSA单变量归因。本轮未改HC/PLE开关或QSA源码、不重启，8035不动，监控已暂停；停止叠加性能优化，根因not-isolated，等待用户方向。

2026-10-17终态补充：[acc014](acc-014-full-gpqa-qsa-m16-i64.md)全量198题strict176/198=88.89%>=0.88，当前QSA-only M16+i64带诊断环境的gate已签发且实时绑定复验PASS；没有HC/PLE或无埋点精度/性能结论。仍有6题60K截断及1题提前EOS、共7条空最终回复，真实HTTP超时0、未见非法访问，根因未隔离。正式阈值通过不改写原003局部doc32失败或证明症状修复；完整证据已冻结，heartbeat PAUSED，等待用户方向，无新修复/重启/推理。

acc014运行中更新（2026-10-17 15:17）：首次确认doc178 reasoning-only、24token后直接EOS、无think-end/最终content，8rank状态及原始返回/token/日志已冻结校验；与rank0实际采样前缀一致。当前没有非法内存访问或已记录的invalid/mismatch/nonfinite，不能归因QSA或i64/缓存/graph。详见[acc014完整记录](acc-014-full-gpqa-qsa-m16-i64.md)。正式评测继续，分数/gate未终态，不追加测试/修复/重启。

2026-10-17后续：用户已授权在当前QSA M16+i64同一8010实例运行一次[acc-014全量GPQA](acc-014-full-gpqa-qsa-m16-i64.md)，14:13:54正式启动、C64/198题、原采样；不重启、不改源码、不操作8035。003局部doc32答错、无性能结果的事实保持不变；新分数/gate独立记录，不能用本轮启动反称局部通过。

## 范围、授权与门禁

用户2026-10-16授权将env-018新增算子接入当前模型链路，保留64位索引修复，先受控精度/性能验证，禁止直接全量GPQA，**需要重启8010时先报告并等待确认**。仅PPU-07优化容器、8010/TP8物理8–15；0–7/8035不可操作。精度模式`minimal-regression`，性能模式`targeted`、diagnostic例外（原正式gate仍无效），不签精度gate或宣称正式性能通过。

### 2026-10-16后续明确授权执行（当前）

用户已确认“按这个范围仅重载8010做基线和候选对照”，保留i64，总生成请求<=99、并发<=8、首次异常保留raw/token/完整日志，不影响8035/不全量GPQA。仅本轮允许baseline-off→candidate-on两次重载；任何首次异常停止后续派发/阶段，已在途自然取证，禁止重试/自动第三次恢复。旧PAUSED monitor不恢复旧工作负载，可按本轮范围单独只读跟进。

预检17:38+08：8010原API2235393/start484916288空闲running0/waiting0、原2627674客户端已退出；8035 PID1948536/start484833646仍原身份；实际镜像与单/mnt bind、lineage/parity回执匹配。物理8–15仅本任务8worker占用，每卡约13.4GiB空闲，不操作0–7。原生vLLM0.24.0 bench serve当前源码`ready_check_timeout_sec`默认0、`num_warmups`默认0，只在显式开启时发送额外test/warmup；本计划不启用，72性能请求预算成立，运行前仍保存CLI/源码SHA。99预算包括所有实际生成流量，GET健康不计生成请求。

执行先行门禁：新增远端`commands/op019-operator-minimal.py` SHA `2e91f25ccf4efcabaf5f84e26b322fd04abc8b73a03356ba5e87da759a86d7a6`，通过`commands/op019-run-micro.py` SHA `5ac7a2adc0a10ae85c3f7cdc0e89f08db75fd6f0e694f8c6784d8310abb8a47e`执行（`python3 <BASE>/commands/op019-run-micro.py`）。排他创建`<op019>/execution-001/operator-minimal-001`，核对两服务身份、空闲、旧客户端退出、镜像挂载及i64双SHA，仅物理8且显存上限2%做已有上游测试的真实函数调用：HC BF16/FP16非对齐与H2560；PLE gate/norm、NULL0 prefill/decode与状态mask、QSA store及稀疏GQA3 CPU reference；小graph replay。不启动模型推理/修改服务/改源码，保留数值失败张量和完整trace，出现首个算子异常立即结束，不继续重载。测试仅用cfg.QUICK_MODE替换上游pytest runner配置导入，计算reference和kernel均原始真实代码；不把它当模型通过。

本轮方法bundle：accuracy/minimal-regression `6e94a080dd3b64544c535e1fd4bda506f55516374d14d0f8ca6aa148bba2c7b2`；performance/targeted `872b65dd0e7a4e8c5b342c37b1c34729f14154d1e68be01ed60938d5b22dc8d1`。QSA现有知识没有stable README，已按现有optimization-map/case-index核对：小rows收益不能外推生产rows，不采用历史数值替代本次验证。

执行前读真实conv test发现inputs返回(args,kwargs)，已在**尚未执行**的本地检查入口修正解包并保持BF16 conv原2e-2容差；最终micro入口SHA为`316f7c54ed02957e29a4ec3ab3abd6ab7c97cad8ce8c96449f0160c43ce4606b`，取代上段草案SHA，未产生设备异常或重试。

### 本轮首次数值异常：已停止，不重载服务（2026-10-16 17:55）

前18项真实PPU检查通过：HC BF16/FP16（rows1/3/8、H257/513/2560）、PLE gate BF16/FP32（H33/2560）、state gather/scatter、QSA store、PLE NULL0 ragged prefill/decode及PLE fusion graph刷新。第19项`QSA-sparse-GQA3-invalid-and-graph2`在首次数值比较时失败，**尚未进入该QSA的graph2**。Q=[5,3,256] BF16、KV=[8,16,1,256]、logical indices=[5,33]（int32、-1..63）、非连续物理page table和一个invalid request；调用官方`qsa_sparse_paged_attention`，用该官方仓库`benchmark/qwen4_references.py::sparse_reference`在CPU计算独立参考。2676/3840元素（69.7%）超出预设atol0.03/rtol0.02，最大绝对误差1.0859375、最大相对误差2880，当前仅观察一次，不能据此宣布根因confirmed。

按用户“首次异常”停止规则和inference-accuracy-diagnosis，未启动后续微测/模型/性能客户端、未修代码/改开关/重试/缩范围：本轮**模型请求0/99、重载0/2**。8010仍2235393/start484916288、8035仍1948536/start484833646，launcher退出回执核验两者argv SHA不变；i64双SHA已核验。没有新的模型reasoning-only或HTTP/token回复可报告，因为没有模型请求。无本轮非法内存访问日志，只有数值assert；这也不能替代旧GDN边界/输出因果定位。

原始目录`<op019 evidence>/execution-001/operator-minimal-001`：run.log SHA `3d121b320f46c1750554287ba6a30c729fd3c2d1e19a5ce9ebd0fcae76629ff5`，FIRST_ANOMALY.json SHA `8db87f9cfe17c6fd0b0fcec4b951e7dc2c8364a4678a5b6ad3eeaf00edc72c69`，完整trace SHA `11179cb53fb98888d36113adc20819a1027c6cf118cc858ca96a80b7c76beef5`，report SHA `f91ce773c8e6e9186c9c34ca03c57f3534e6ec91b7057ed98b3385f155750dff`，exit回执SHA `e7460cb556ee15f17665b4cf37706164c0d89ba0021fa15a0a27bd6f81a4ebb8`。

**证据缺口必须保留：**异常取证只筛上游文件的traceback帧，而本次QSA assert位于本地runner，`saved_tensor_keys=[]`，原始Q/K/V/indices输出张量未落盘，进程现已退出。不能用seed重建冒充首次原始tensor，未自动重跑；raw脚本/seed/源SHA/完整日志保留，后续受控定位必须调用前保存输入和索引、返回后保存输出，再做assert。本次不宣称完整数值现场或已知编译器问题已复现。

只读源核验确认6个位置参数及softmax_scale默认1/sqrt256与CPU reference匹配；新实现实际选择`BLOCK_M=max(8,next_power_of_2(GROUP_SIZE))`，GQA3进入M8，非NVIDIAlaunch配置为N16/warps4/stages2。与既有PPU BF16 M8 A-ldmatrix错误机制卡相符，可列suspected，但没有M8/M16单变量与实际张量/基向量证明，不能升为confirmed，也不能归因此前未用新库的GPQA错误。小cache索引不触达20972，本次异常与017 i64修复路径分开。

仅复制既有证据的冻结入口`commands/op019-freeze-first.py` SHA `f862d76131954339ec2e6e2264a571e7eca4500c8259548c30de87588ab42514`，命令`python3 <BASE>/commands/op019-freeze-first.py`：排他目录`execution-001/first-failure-freeze-001`，保存首异常原文件、旧8010完整服务日志固定前缀、已安装QSA/参考源码、i64源码及本轮专用编译缓存，并做SHA清单；只读核验原实例/idle/health，不运行任何算子/请求/编译或重载。缓存未生成则明确缺失，不能捏造。此动作不恢复任何heartbeat。

本轮结论：`minimal-regression=failed-operator-prerequisite`，模型/graph-service/端到端性能均not_run、无formal gate，组合候选不得加载或晋级。HC/PLE局部通过不代表完整HC/PLE-only组合通过。等待用户决定仅QSA保全输入的受控定位，或另行冻结去掉QSA的组合范围，不自动使用剩余99请求预算。

冻结实际成功：`execution-001/first-failure-freeze-001/FROZEN.json` SHA `46e60cfb7e6a5d62c890972b599c54ff55e5aa375a106ca3041e31c80a309778`，325份原文件/编译产物逐项SHA。triton cache存在并已复制，gems cache未生成如实记录；完整日志与旧8010服务日志固定前缀已保存，但首次数值张量缺口不被此回执补齐。最终health8010=200、running0/waiting0，8010/8035实例argv及i64源码再次核验不变，后台无新客户端或monitor，仍模型请求0/99、重载0/2、无额外算子重测。`git diff --check`及本案例state/README生成通过。

## 方向与工程设计

### 用户确认8035预期停服后续跑：同一8010、零重启（当前）

用户最新确认旧8035停服为预期操作，要求更新保护基准、**不要再重启8010**、保留i64、继续小范围精度/性能、首次异常取证、禁止全量GPQA。只读现状8035已由其他任务重新启动为PID4161238/start487889425/argvSHA91849d0b77b52d602a9ffc0ce9dbb608667ce127ce61cc8a0474883e334ffc0c；采用当前实例而不是把历史停服误写成当前仍无listener。8010仍4022615/start487850554/argvSHA5744d99971adc1f0e9c1885acb61cd9910ccc7fd7adb84f33a11d009702c007e，health200/running0/waiting0/prompt与generation累计0，旧driver退出，未发生任何模型调用；旧保护事件与回执不改写。一次误把旧只读audit脚本当作支持--help调用，因排他目录已存在在第一条mkdir即拒绝，未写文件/发请求/操作服务；不再执行该入口。

新独立产物`<op019>/service-qsa-002`，仅更新保护/控制器，不改服务源码/env/argv/缓存/采样。沿用已冻结11精度+条件36性能的47调用/C<=8/零重试预算及所有停止规则；requests SHA仍56a7f88d34dcdbdb929da91bcf969b3ea5b81d9221cf3d86565b262b24aec8c5。旧001实际0条，不重复旧请求。两个证据链接明确指向实际仍运行的`service-qsa-001/runtime`与`service-qsa-001/service-diag.log`，不是伪造新observer实例；终态复制原始文件并列SHA。其他服务仅只读守护，若新的8035实例再次变化则停止本客户端后续派发，不操作该服务。权限不包括再次恢复/重启8010或全量GPQA。

续跑控制`<BASE>/commands/op019-qsa-resume-control.py` SHA77665c6f9d45f13fb5872c7712a95b67749841a9bb5bdf9e97176d6c5e84907f，命令`python3 <BASE>/commands/op019-qsa-resume-control.py --mode prepare`，仅排他创建002、复制字节相同的请求/计划/维护runner、核对源码/i64/身份/挂载；wait/client复用已冻结旧client函数，**新入口没有restart模式**。实际普通Python INFO未输出groups日志，旧wait的日志字符串断言无法作为准入依据：新wait保存8worker实际白名单环境（qsa/thead/private019/017i64）、private019 runner-hook来源SHA、两类7/7 capture与当前源码SHA；已验证vendor导出对象/算子数值证据另列引用，不冒充在线函数指针检查。前两条C1及原observer实际replay/i64记录补运行证据；若缺失则incomplete，不因已设置环境或CPU路由测试宣称服务命中/性能收益。

续跑driver`<BASE>/commands/op019-qsa-resume-driver.py` SHAa20392612112ff1abfadba463dfce3ff2ea08844bff9a942d16b00f2a0b6987f，仅wait→原11请求→budget probe→维护版三计划，精度异常不发性能；独立排他DRIVER_STARTED，无服务控制命令。启动器`<BASE>/commands/op019-qsa-resume-start.py` SHA71bef84992c84d73838c12195dfdd4379f2b3d6aa41d0e4e20ac9d1daa2aba96，命令`python3 <BASE>/commands/op019-qsa-resume-start.py`，只Popen一次新driver。传输前检查新文件/目录不存在，scp -O保存并核验SHA；prepare通过后记录回执再仅调用一次start。终态保存完整可读driver ring buffer（host-wide、不擅自归因）、服务log、8rank已有state/日志、raw/token与文件SHA，数据缺失/last-writer限制如实记录。测量只允许当前候选绝对诊断值，无baseline/revert/加速比/正式gate。调用本地accuracy minimal-regression、performance targeted及diagnosis，正式精度阻塞不被本轮局部结果解除。

prepare已成功，PREPARED SHA`ede0874f9d26bd57d9a38e46f1b58df325e1570272b0d59cf37c891732f9194e`。同一8010 idle/累计生成0，保护8035当前实例、源码/i64与镜像/挂载均匹配；新请求与性能计划逐字复制，旧001文件未改。下一动作仅一次`python3 <BASE>/commands/op019-qsa-resume-start.py`，绝不调用旧restart或旧失败driver入口。

002的唯一driver247006/start487971110已在wait停止（2026-10-16T23:18:05+08），CLIENT_STARTED/模型raw均不存在。控制器误把`/proc/worker/environ`缺少全部白名单键当作实际worker配置差异；实际8worker model-hooks均记录private019 model与private017 Gems，runner-hooks来源/observer SHA匹配，API启动环境完整，不能用不可得的worker environ伪造“已证明每worker变量”或直接认定加载错误。完整002回执、首marker、服务/driver日志保留，此为pre-request控制校验问题，不是模型错误。另静态确认native benchmark默认ready-check600秒且num_warmups是必传参数，旧“函数默认0”探针不成立，尚未执行性能/额外请求。

纠正后的新入口单独`service-qsa-003`：`commands/op019-qsa-resume-control-v3.py` SHA`72790091b05964370ff68e43b7e69f0ec167b9203d268d24aef3be7ae67e457b`、driver-v3 SHA`c37de8b9bbe8b81fb16d85dd8959d0aa7f83617f0d81a17d0af7a292269a5746`、start-v3 SHA`a4436a23dd2be3525b7035d80a14d283f16cd76325e9c69d617c915395a1297a`。命令依次`python3 <BASE>/commands/op019-qsa-resume-control-v3.py --mode prepare`、prepare成功记录后一次`python3 <BASE>/commands/op019-qsa-resume-start-v3.py`。仍11+条件36/47、C8、0重试、0重启；prepare核验002终态/客户端未启/累计生成0。v3 ready检查API实际环境+8worker真实model/Gems/runner hooks，缺失worker environ明确列missing，QSA live函数指针/独立kernel hit尚未观察，不以这部分声明完整路径晋级。

维护版性能三文件保持SHA不变；仅新003/bin/vllm为透明Python CLI入口，调用同一个安装的`vllm.entrypoints.cli.main.main`，只为`bench serve`显式追加`--ready-check-timeout-sec 0 --num-warmups 0`，不改vLLM/benchmark源码、不实现测量逻辑；通过新进程PATH选择，冻结wrapper SHA/原生source SHA/实际命令与CLI能力。三轮外部预热仍按原计划，不加隐藏生成请求；如CLI不支持或计数/健康不一致则incomplete停后续阶段，不自动加请求。002控制失败0请求，003不是重复模型试验。

003 prepare成功，回执SHA`f115bc3cb99c72a9b2810ac0768d41aee28ad06949e4b7be4ca1c7d3fd8e1d1f`；下一动作仅一次冻结start-v3，same8010/no-restart、旧002保留，预算不变。

003唯一driver已启动PID322510/start487993787，READY SHA`6bf9f4117717d736262518acb9e2730e7ad5962fd60ebabe220413f9bdaf6672`，客户端323254/start487993942。23:22:41+08已派发2/完成1，首C1 doc2最终B正确、HTTP200/544完整token、finish=stop、think-end1/EOS248046，第二条在途；当前没有模型异常marker。沿用原heartbeat `qwen3-8-ppu07-gpqa-c64`，产品工具已更新ACTIVE/30分钟/只读现有003、仅实质变化或异常/终态通知，不启动任何客户端或服务。无新重启/源码改动/全量GPQA，精度与性能仍未完成。

23:23:25+08已进入C8，10派发/2完成/8在途/errors0。两次C1均B/544tokens且完整token序列相同，正常think-end/EOS/stop；8rank实际记录均验证IndexFunction、IndexPutFunction先提升i64，每rank已有>1500条FULL graph binding/replay记录。服务私有Triton缓存出现新库`_qsa_sparse_paged_gqa_kernel`（首C1编译mtime23:21:55及此前capture批次）及_store/_compress产物，构成新库编译路径补充证据，但不是逐rank在线函数指针或各请求kernel执行计数证明；不据此冒充正式命中/性能通过。性能尚未派发，继续原唯一客户端。

本地本轮Python语法、YAML/README生成和git diff --check通过；全仓`validate-local --records`未通过，报既有跨模型缺失链接及大量历史process artifact路径规则错误（含既有Qwen38旧commands），本轮未创建此类本地原始脚本/日志，不为通过检查删除或改写无关记录。此限制不代替远端模型回归结果。

23:24:26+08最后快照11派发/4完成/7在途，4条均匹配冻结答案且最终content、token与stop健康，errors0/无首异常marker/8010 health200；不把4条请求当4唯一题（含同doc2重复）。继续原客户端，性能尚未开始，monitor保持ACTIVE。

### 23:56 heartbeat：10/11完成，仅doc32在途，尚无首次模型异常

本次严格只读，无新远端脚本/生成请求/服务操作。已派发11，按seq核验10份原始响应SHA与usage/完整token一致，覆盖**8唯一doc**（0/1/2/142/144/149/151/155；doc2含三次调用）；10条均匹配冻结答案、HTTP200、非空最终content、finish=stop、think-end一次、terminal248046，无空输出/length/真实HTTP错误。最后完成doc142在23:44:33，14581 completion tokens；doc155为12025。唯一未完成seq10/doc32仍生成，不能把其流式/内部状态没有最终答案当作已完成reasoning-only事故。23:54:57 rank0 batch-binding的computed_tokens=22728含prompt，不作最终completion_tokens或ETA；随后8rank步数持续增加，非只凭progress.json久未更新判停滞。

两端绑定与当前保护基准一致：8010 API4022615/start487850554、8035 PID4161238/start487889425，argvSHA均匹配；原driver322510和client323254存活，未重启/重复启动。8010health200/running1/waiting0/preemption0，23:53:55 KV0.01366235、累计generation63753；服务log仍推进（23:55平均生成13.2token/s仅运行观察、非性能测量），严格ERROR/illegal/device fault匹配0，client与observer FIRST_ANOMALY/STOP未出现。空间约8.12TB可用。

8rank实际index-address-implementation均验证两个generic类提升i64，当前文件SHA与冻结值相同；private019 adapter、PPU QSA、observer SHA也未变。已记录generic gather/scatter max均740，row stride102400，i64/i32 offset同75776000，byte范围[303111680,303504896)合法且小于storage27372339200；packed device实际max597，**20972边界not-covered**。每rank约24803–24851条FULL graph replay/binding记录，已记录operator mismatch/invalid/nonfinite均0；大量未变indices以None省略，不冒充独立完整索引快照，pool last-writer限制仍保留。没有观察到新的非法访存，但不能据本轮小负载宣布旧故障/reasoning-only已修复。

accuracy minimal-regression仍incomplete/running；performance targeted三场景均not_run，须原doc32结束且全部11通过后由**已有driver**按冻结预算继续，heartbeat不代发、不补请求、不改cap/采样、不重跑全量GPQA。原heartbeat保持ACTIVE，仅本次4→10完成的实质进展通知；没有terminal marker，不暂停现有监控，不签formal gate或报告全量分数。

00:24:54+08（2026-10-17）只读复核：仍11派发/10完成/8唯一doc、仅seq10/doc32在途，无新完成或阶段切换。既有10份raw SHA与usage/token再次核验正常；doc32八rank computed_tokens已推进至46228–46314（逐rank非原子读取、含prompt，非最终usage），每rank FULL记录47353–47439；状态/索引mismatch、nonfinite、invalid及严格服务ERROR/非法访问均0，client/observer首marker与终态回执均未出现。generic740/packed597未变，20972仍未覆盖；i64两个源码及observer SHA不变。原两服务PID/start/argv及唯一driver/client均匹配、health200/running1/waiting0/preemption0，00:23:49 KV0.02766887/累计generation87298、00:24:46服务log仍更新，约8.12TB可用。性能仍not_run。未发任何新请求/脚本或重启，按用户仅实质变化通知要求本次保持安静，继续原ACTIVE heartbeat，不估ETA、不把在途无最终答案当作已完成reasoning-only。

### 003终态：doc32正常输出但答A而非标准B，停止性能验证（2026-10-17）

全部11请求/9唯一doc已完成；10请求匹配（去重8/9，仅定向子集，不是正式strict-match分数）。唯一失败seq10/doc32原始完成于00:34:07.927737+08，排他FIRST_ANOMALY时间00:34:07.930810+08、SHA`16d75e34733e8e0da60461a5f83b7198e0887551b15fd6ca2f38e113e2ced784`。该题HTTP200、53126 completion tokens、finish=stop、stop_reason=null、最终正文明确`The best answer is A.`，冻结gold是B；原生strict-match样本gold `(B)`、同一prompt逐字匹配、原samples SHA与冻结SHA再次核验，排除本次doc/gold错配。完整reasoning177905字符，think-end在53067/EOS248046在53125（零基），**不是reasoning-only、60K截断或真实HTTP超时**。

首异常已有client执行停止规则；该题是最后在途请求，不存在后续补发。ACCURACY_FINISHED SHA`08264105faf77b0568f423785c7745838c50ac4d3c8991f47cb617e3db6c9e74`，状态stopped-on-first-anomaly，原driver因accuracy-client exit1停止，性能budget probe和三场景均未执行。VALIDATION_FINISHED于00:34:20.999654+08落盘，SHA`1bde73a85abae5f8bbeec6009c8633ccf1748375f209694b21d1fc379ff9e371`；driver322510/client323254现均退出，11/47实际请求、0重试、003零重启，不使用剩余36预算。required minimal-regression按冻结的全匹配规则未通过；不签formal gate、不能将定向子集比例与0.88正式阈值比较，也不宣称端到端性能收益。

原始目录（R）为`/mnt/nfs/users/jinghao/qwen3.8-flash/20261015-qwen38-flash-next-ppu07-container/operators/op-019-fgvllm-integration-20261016/service-qsa-003`。首错误原件`R/req010-doc032-response.raw.json` SHA`fc621712f52d2a92a6566969758da96b401a79ff728d50a978d7b9b543be5bb8`、同前缀request/result、11份raw响应/完整API token和client-events/accuracy-client.log均保留。11份raw SHA、usage/token数、think-end/EOS和非空最终content全部核验一致；总95412输出token等于服务累计，11份HTTP200/stop、0空最终/截断/网络失败，两次C1 544token完整一致。doc32 rank0 post-sampler/pre-bookkeeping的非discard序列53127个，其中前53126个与API**逐个相同**；另1个尾token198记录于API终态之后，不在API返回中，不把采样日志和已发出token混同或认作parser损坏。

`R/terminal-evidence/`保存约532888155字节：8个TP rank完整既有journals及rank-1导入hooks、服务完整固定前缀、原始首marker、就绪/绑定/精度回执、全部当时可读host driver ring buffer（非完整历史/非自动因果归因）。driver日志SHA`141044322a4b3a0f8a0ac1698c9533d4a92b51df4d191af9bdf903bb2b019659`。独立重验receipt列出的76个不可变文件，SHA/缺失均0；服务live链接继续追加health INFO、driver.log在manifest后追加终态打印，因此这些mutable引用不要求旧hash恒等，冻结副本实际hash均通过，未改旧manifest掩盖差异。

**取证边界：**本次只触发客户端答案不匹配，没有触发GPU/状态observer异常；冻结runtime目录是9份日志，**没有first-state张量或逐rank state manifest/逐层快照**。不能把这些日志称为完整因果状态现场，不补造tensor或重新推理。8rank均结束于step54709、各54702条FULL graph记录，已记录generic gather/scatter max740、stride102400、packed实际max597，正确i64字节边界合法；20972仍not-covered。全部已记录mismatch/invalid/nonfinite与冻结服务严格ERROR/非法访问均0，i64两实现命中/SHA保留。两服务PID/start/argv仍匹配，8010health200/running0/waiting0/KV0/preemption0，8035未操作。

分类为`scoped-answer-mismatch`，原始答复与gold不符已确认；**QSA M16/i64/graph造成此语义错误的根因未隔离**。本轮没有同配置baseline/revert，不归因旧017的60K空最终，也不把输出健康改善视为旧非法访存/精度问题已修复。按精度定位流程冻结并停止候选晋级/后续性能；保留当前健康8010/i64，不自动回退、重启、追加请求或全量GPQA。终态记录完成后暂停原heartbeat，等待用户方向。

00:58:43+08当前9份生效相关源码SHA与终态binding-after一致（含i64两文件、observer、Plugin model/adapter、QSA common/PPU/导出与测试）；未改服务或代码。产品工具已确认原`qwen3-8-ppu07-gpqa-c64`为**PAUSED**，保留原prompt/周期/通知偏好，不创建重复监控。仅本地同一state/实验文档/README更新，无进一步推理、GPU微测、重启、修复或性能阶段。

### 用户授权一次仅8010重载及小范围模型/性能回归（历史，2026-10-16）

上方003续跑已在2026-10-17 00:34终态，见以下终态核验；旧启动授权不再作为继续派发或重启的依据。

仅启用`VLLM_FL_QWEN38_FGVLLM_OPS=qsa`，不叠加HC/PLE；保留private017 Gems/i64及observer，不改GDN算法/权重/采样/blacklist，使用已验证private019 Plugin和PPU QSA库。用户明确仅一次8010重启，8035/0–7保护、禁止全量GPQA，首次异常保全并告知。现8010仍2235393/start484916288；8035已由其他任务新起PID3611426/start487728689/argvSHA91849d0b77b52d602a9ffc0ce9dbb608667ce127ce61cc8a0474883e334ffc0c，采用当前事实，不使用历史1948536。独立新证据`<op019>/service-qsa-001`，命令在BASE/commands冻结，重启仅精确8010进程树，禁止容器重启或自动第二次恢复。

accuracy=`minimal-regression`（bundle6e94a080...）；performance=`targeted`（bundle872b65dd...），用户当前指令构成既有accuracy blocker下的诊断性性能例外，不签gate。总预算**47新生成请求/C<=8/0重试**：两次C1 doc2→C8上限的9唯一题142/144/149/155/151/0/1/2/32，原采样temperature1/top_p.95/top_k20/min_p0/presence0/repetition1、seed1234/stop/max60000不改，返回原始token IDs/prompt text。固定请求与旧原生samples strict-match gold逐prompt核验，保存配置/payload/gold来源SHA后才停旧服务；本轮仅报告冻结子集的答案匹配，不冒充正式score。doc32保留60K风险，不改上限规避。首HTTP/输出空/非预期length/异常EOS/token缺失/错误答案/状态异常即停止补位，已在途自然取证；客户端logger/资源/绑定问题单独分类，不冒充模型事故。

精度全部通过才执行维护版`evaluation/performance/vllm_perf.py`，不另造benchmark：Prefill P4096/D1、Decode P256/D256、Mixed P4096/D128，每场景N2/C2、3固定warmup+3measured（每场景12，合36），temperature0/ignore_eos/seed42/random_range_ratio0。各映射父P4K正式场景，D/N/C缩减且Decode用短P，只报告client代理，不当纯设备时间；固定短输出的length不是GPQA异常。最后2预热主吞吐spread<=10%准入、全部3测量轮保留、波动>10%标incomplete，不追加预热/删慢轮。原已运行服务未冻结同配置prefix禁用且用户仅一次重启，**本轮只测新实例绝对指标，不输出加速比/比较通过**，无baseline/revert/独立实例复测的限制明确保留。四正式场景均未验收。

新启动沿用已存在launch-service.sh，改Plugin导入为private019、qsa组、诊断root/log写入本轮，保留SDK/NCCL/Gems/i64与旧cache选择；CLI核验支持后追加`--no-enable-prefix-caching`，用实际argv/runtime确认false。该配置差异禁止混用旧性能。image/mount/源码/原服务idle/两端身份和资源门禁通过后才仅停8010、启动一次；启动前保存脚本/SHA、原进程树/回退配置与原日志前缀。先等待8worker/graph capture/实际导入与i64证据，再发C1两次验证replay。首次异常保存原始HTTP bytes、完整已返回token/finish/stop/usage、rank日志/selected state manifest和服务/driver可得错误；未返回回复/共享pool last-writer或driver取证权限缺失时如实标missing，不称完整因果现场。性能原生详细结果/输出文本和日志全留存，原生接口不返回完整API token时不伪造，以rank采样证据标明边界。异常后不自动重启/修代码/扩范围，先报告等待方向。

执行前冻结控制入口`commands/op019-qsa-service.py` SHA `02e5e9e400458b48a5b1ea09e29f95ea93281d8ee382e7869f9856f23aea2506`，分模式命令均为`python3 /mnt/nfs/users/jinghao/qwen3.8-flash/20261015-qwen38-flash-next-ppu07-container/commands/op019-qsa-service.py --mode <prepare|restart|wait|client>`。prepare仅新建service-qsa-001、核验旧原生gold/prompt、实际安装源码/镜像挂载、CLI帮助、生成启动脚本与三份性能计划；**prepare通过并记录launch/request SHA后**才可restart。restart排他RESTART_STARTED并保存精确旧8010子树，只对start_ticks匹配的该树TERM，超时残余才定向TERM/KILL，不用pkill/全容器/其他服务信号；资源8–15归零才detach一次启动，不自动恢复。wait最长3600s只读health/8rank hook/capture/实际qsa组、runtime prefix状态；无ready不发流量。client排他CLIENT_STARTED，前述11题最多C8、0重试、原raw请求/响应及完整API token取证，后台15秒只读健康/身份/observer检查，不叠加推理。原始observer写入新runtime，只last-writer pool快照不伪称逐层独立状态。

维护性能三文件只复制原文件，不另写benchmark：vllm_perf.py SHA `d7bac00f99827943cf63eac9cd557c1730bd5e9dcae74dfd1c9c31463a3a2187`，performance_plan.py SHA `ef4838ec42d8fabb2d1e1042790098ab81b546583909c6a1691e5aa3fad18d4b`，compare_performance.py SHA `b8c8e58bcc3217af7450bc4930758a7c6e47f2a51eb5dab0655206bf2d711c5b`；在新service目录tools保存并验SHA，先dry-run留命令再执行，具体命令就绪后补记。尚未启动benchmark或新模型流量。所有新脚本先test不存在后scp -O保存，源码/服务修改仅限上述授权。

prepare已完成11请求与9唯一doc的prompt/gold逐字对齐、原实例/镜像挂载/源码快照与新启动脚本，但`CUDA_VISIBLE_DEVICES=''`运行vLLM CLI help非零返回，尚未停止原服务/发请求；prepare-ERROR.log保留，该次CLI stdout因check_output异常未落盘，不能称完整CLI现场，也不能推定模型或设备故障。v2入口另存`commands/op019-qsa-service-v2.py` SHA `a0d60ce6063237694bdc0057b1c3c8f73ed54668b1e302d9c75719bcb9096fef`，只用`--mode preflight`续做CLI核验（不重新prepare/覆盖before/requests/launch），采用原服务private017 PYTHONPATH、DNN_VENDOR=thead、单物理8可见，仅CLI帮助不初始化模型/发推理请求，完整CLI stdout无论成败先落盘。成功后冻结性能计划/PREPARED，之后restart/wait/client均使用该v2入口，不扩大47预算或再启服务。

22:56:45+08 preflight已成功，PREPARED.json SHA `8112d648ade382abe0d31ae482e46bf1cb48b310c7dbf837c234acf342b87555`，launch-service.sh SHA `4120cf8d8c6693b38236b90bfbc48ff36d44b2026b3a4b2fdfa6459a299e06e5`，requests.json SHA `56a7f88d34dcdbdb929da91bcf969b3ea5b81d9221cf3d86565b262b24aec8c5`；9唯一doc/11调用的旧原生gold/prompt均逐字对齐，CLI完整帮助确认prefix负向参数受支持。下一动作是唯一一次`python3 <BASE>/commands/op019-qsa-service-v2.py --mode restart`；成功后仅一次wait/client，不复用旧99计划或formal runner。原8035当前基准3611426/start487728689，若漂移仅暂停本任务，不操作其他服务。

唯一restart已返回ONLY8010_LAUNCHED，旧树信号回执与新LAUNCHED.json保留；不再调用restart。新串行控制`commands/op019-qsa-validation-driver.py` SHA `275d36b65abd37425eced87898a45ef7bf3392d8b30b2affd69b2114ec779eb0`，命令`python3 <BASE>/commands/op019-qsa-validation-driver.py`，通过一次Popen(start_new_session=True)后台执行，stdout/err写service-qsa-001/driver.log；DRIVER_STARTED排他拒绝重复、核验controller/三维护runner SHA。它只按wait→client（11准确请求）→budget probe→3性能计划执行，不含任何服务停止/启动逻辑。8worker/graph不就绪时不发请求；第一异常/accuracy失败/吞吐预热不稳定或native结果失败则停止后续阶段，不重试/补预算。其他8035仅只读身份守护。

性能每阶段的原生命令在driver执行前写`<stage>-command.json`，统一：`docker exec -w <R> -e CUDA_VISIBLE_DEVICES=8 -e DNN_VENDOR=thead -e PYTHONPATH=<private019-plugin>:<private017-gems/src>:<private017> <container> python3 <R>/tools/vllm_perf.py --config <R>/perf-<stage>.json --service-manifest <R>/service-manifest.json --role candidate --run-id op019-qsa-<stage>-001 --scope diagnostic --client-probe-timeout 120 --output-dir <R>/performance`，先同命令追加`--dry-run`；只跑prefill/decode/mixed三项，不用原生示例默认矩阵。发性能前inspect原生benchmark函数默认`ready_check_timeout_sec=0/num_warmups=0`并保存source SHA，防止隐藏生成流量超出47；不满足则不跑benchmark。客户端只加载tokenizer/HTTP，不发设备算子微测。

driver结束时仅复制已有service/log/全部runtime目录至terminal-evidence、列SHA，读取可得dmesg相关错误及上下文（host-wide、不能未经PID/时间归因），保留原R目录，不声称未返回HTTP/有界pool状态完整。性能仅原生详细结果保存文本/长度，未返回API token不补造；无formal gate、no-speedup。后台driver只运行一次，heartbeat仅可读其状态，不得再启动任何客户端/服务。

唯一detach启动入口`commands/op019-qsa-start-validation.py` SHA `9129e78af5ca6f4bbe5e063ab1fd1a5d892ef99ffce599f74712c8e85b589510`，命令`python3 <BASE>/commands/op019-qsa-start-validation.py`：排他DRIVER_DISPATCHED/driver.log、Popen一份已冻结driver、保存PID/start_ticks；只允许一次，后续只读既有进程，不调用旧accdiag017 start-client或重新wait/client。原服务固定前缀中已有10条同类native extension unavailable警告，新日志同类警告属于既有fallback环境而非首次模型事故；已保留两边完整日志，后续strictERROR/worker异常仍按首异常停止。

### 本轮首个保护异常：8035绑定消失，模型验证未开始（终态）

唯一driver4118889/start487877218实际执行wait后，于`2026-10-16T15:02:46.212687+00:00`（23:02:46+08）排他记录FIRST_ANOMALY.json。根证据wait.log：`other()`读取8035无监听而assert，wrapper marker分类validation-driver-or-measurement；这是**保护端点identity drift/执行门禁失败，不是QSA数值/非法访问或模型精度下降**。此时新8010已完成PIECEWISE/FULL各7/7 capture、API健康200，但READY未签、CLIENT_STARTED不存在、raw request0、performance目录未创建，**新生成请求0/47、模型精度incomplete、性能not_run**。不因服务启动成功宣称模型实际QSA命中/graph replay/精度已验证。

stop-receipt.json显示唯一实际信号为22:57:55+08向旧8010 API2235393发送SIGTERM15，子树自然退出，无额外TERM/KILL，无8035信号。可得dmesg只读上下文中8035 PID3611426于23:02:19+08出现exit defgi记录；后续8035仍无监听。未发现本次查看的最后300行有OOM/killed-process/illegal匹配，**此有限观察不能证明8035退出原因**，不能未经证据声称一定由其他任务主动重启或完全排除间接影响。不操作/恢复该服务，不更新原冻结before.json来静默接受漂移。

driver已退出，VALIDATION_FINISHED.json SHA `4a5869afaf6d9f9d4a0f7e63815cca0a023f8593376d421f52e4ef44193a97c8`，状态stopped-or-incomplete-no-auto-recovery，50份文件SHA、9份已有runtime文件已保存terminal-evidence，driver上下文读取exit0。没有推理请求，因此没有模型原始回复/token可保存，明确not-applicable而非缺失的成功样本；无state异常marker时不虚构完整逐层状态。新8010当前Host API4022615（容器2308555），仅HTTP health200证明存活；未第二次重启/续发client/跑GPQA。先前旧heartbeat本轮仅替换为此driver只读范围并短暂ACTIVE，发现终态已通过产品工具PAUSED确认，未重复监控或派发。

补充仅只读取证入口`commands/op019-qsa-postguard-audit.py` SHA `a8d593f704dcd0fd62acc9cfae4d113bb34bcdf067e54032889861ca4c8e1b16`，命令`python3 <BASE>/commands/op019-qsa-postguard-audit.py`：排他postguard-audit-001，保存新API精确身份/白名单环境、i64双SHA、捕获完成行、原信号回执和可得host driver与8035 PID/OOM上下文；不读完整环境、不操作服务、不生成推理或续跑，dmesg是host-wide且退出因果仍未证实。等待用户确认8035预期状态/允许重新绑定保护基准后再讨论**无需再次重启8010**的继续验证；不自动恢复旧driver或修改已冻结证据。

postguard-audit-001/report.json已生成，SHA `380faa2bd03d1e4c2d283b05b85345e71043339cbf13579d236ead5e2dc5cf02`。新API白名单环境中的qsa-only/PPU8–15/private019 Plugin/private017 Gems及i64双文件SHA均核验；health200，raw0，performance未开始。capture完成仅证明启动捕获，不证明实际请求重放或答案正确。当前最终结论`minimal-regression=incomplete-before-client`、`targeted-performance=not_run`，不是模型回归失败分数。状态/README写回及git diff --check通过；后续需用户确认保护端点变化，当前不继续任何运行。

### 用户授权PPU后端QSA最小M16实现（2026-10-16）

用户明确平头哥BLOCK_M最小16，要求新增该算子的PPU backend特化。仍仅修改本容器私有FlagGems-vllm源码及必要候选适配器，不重启8010/不动8035/不跑GPQA，保留private017 index/index_put双SHA。设计复用现有`runtime.replace_customized_ops → _thead.fused`，通用public ABI和非PPU原最小8不变；抽取共享private wrapper允许backend提供minimum16，single与split都传递该值，不复制Triton kernel，不新增环境变量/进程全局monkeypatch。GQA>16仍按next_power_of_2保留合法大tile，不强制截断成16。公共可选参数/out/gate/workspace/validation均复用，不吞错误。

修改前入口`commands/op019-qsa-thead-prepare.py`先保存两服务当前身份/argv、容器镜像/挂载、FlagGems-vllm git revision/dirty状态与涉及文件、候选adapter和i64双SHA，排他证据`<op019>/diagnostics/qsa-thead-backend-001`。仅`docker cp`将现有源码复制到此目录供补丁和回退，不修改安装/运行源、不发请求；原服务与输入不变。准确script SHA与部署/测试命令在执行前补记，未冻结前不做变更。本轮accuracy=minimal-regression/operator-only，沿用已冻结四fixture与同容差，另加split2/gate/empty/strided与路由CPU检查，目标graph两次replay；不把算子通过作为模型gate或性能通过。

prepare入口SHA `f56ab0e0b37f5bc1ee8ca2612e0d6bb52be0fbe4d97f7137d5d9ba876c5556e7`，命令`python3 /mnt/nfs/users/jinghao/qwen3.8-flash/20261015-qwen38-flash-next-ppu07-container/commands/op019-qsa-thead-prepare.py`。连接检查首次本地RPC受沙箱限制失败；相同inventory/唯一Host权限放开后Ansible成功ok3/failed0，不把普通SSH退出码当该检查通过。候选adapter当前从`flaggems_vllm.ops.qwen4`取函数，绕过包级vendor替换；本轮将该候选改为公共`flaggems_vllm`导出，不改现有在线Plugin或开关。

首prepare在读取旧8035 PID时保护性退出，未创建证据/未改安装文件或执行GPU。22:30只读确认8035无监听、历史PID已退出、物理0–7无计算进程，这是其他任务在本轮任何变更前的状态，禁止自动恢复或操作。v2保存该真实缺席基准，8010仍原实例/8worker；入口`commands/op019-qsa-thead-prepare-v2.py` SHA `37a71c893cae8653a21823f8d20179ca649a892d21cd205d1a5ea45c40fc5c52`，命令`python3 <BASE>/commands/op019-qsa-thead-prepare-v2.py`。不追杀旧PID、不将8035原本缺席写作本轮故障。

目标仓库AGENTS/workflow已完整读取；`optimization.md`不存在，不编造其内容。当前workflow末尾conv1d任务是仓库模板，与本用户明确QSA修复不同，采用用户范围。编码前冻结三表如下（本轮是限域正确性修复，不做性能验收）：

| 项目真相 | 冻结内容 |
|---|---|
| API/任务 | 既有`qsa_sparse_paged_attention`，用户指定PPU最小M16 |
| Editable | 共享private wrapper、_thead/fused/qsa_attention.py及其导出、新路由测试、未加载候选adapter |
| Read-only | 三个Triton kernel、旧4fixture/CPU oracle、i64双文件、在线Plugin/服务 |
| Build/validation | Python AST/compile、black/isort/flake8可用项；精确命令/SHA运行前记录；CPU路由及PPU oracle+graph2 |
| Active set | BF16/GQA3/D256、4旧冻结fixture；split2/gate/empty/strided；大GQA仅路由检查 |
| Benchmark/aggregation | not_run，不比较错误M8性能，不宣称speedup；数值误差逐case不混合 |
| Timeout/profiler | 小范围前台验证预算20min、无额外模型负载，不启profiler |
| Autotune | correctness floor豁免，不增加NVIDIA配置/调优；通用最小8和原N/warps/stages保持，PPU最小16 |
| Fallback | 无Torch计算fallback，沿用原validation和显式异常 |

| 对齐契约 | 冻结内容 |
|---|---|
| Reference | 已冻结官方CPU sparse_reference及FP64 oracle，不是新的Torch通用API |
| Input/output | 既有签名/shape/stride/out别名/gate/workspace ABI不变；BF16验证，其他dtype未新增支持承诺 |
| Dtype/accumulation | BF16输入输出、kernel FP32累计；不改cast/归约/scale/NaN语义 |
| 边界 | invalid request精确零、重复/无效selected、空rows、非连续stride、out与gate检查；异常沿用 |
| Unsupported | CPU执行原NotImplementedError；无backward/autograd新增支持；非PPU硬件未测 |
| Torch仅参考 | CPU oracle和测试copy/compare允许；生产仅metadata和empty分配，不引入torch计算 |

| 路径 | 条件/实现 | 验证/风险 |
|---|---|---|
| early/error | 共用原private helper validation/empty return | CPU错误及PPU空rows |
| PPU special | vendor公共导出→_thead wrapper→共用single/split，floor16 | constexpr命中、4fixture、split/gate/stride、graph2 |
| generic | public wrapper→共用helper，floor8 | CPU模拟launch保持旧选择，不在PPU重跑已知错误M8 |
| large GQA | max(16,next_power_of_2(group)) | CPU路由GQA32不截断；硬件未知 |
| unsupported/external | 原显式异常；无新增外部计算库 | 不吞运行异常，不扩大范围 |

准备回执SHA `cfeadfd35f39cd734004bec17d14155f8347d3f596258a44dbf0e11c30861530`，FlagGems-vllm main6568039工作区干净、image/mount符合历史回执，PPU库在容器私有/opt不共享。补丁通过本地apply_patch生成，部署前SHA冻结：common QSA `89c0bb3e47fedfb7ef73512ceff6fe4d464863a296e874eadb411a54342efb42`，thead fused导出 `3a39c83ff755767fd0a0cc200853c6d3e9ead5030153387e3232a2272a43c87a`，thead QSA `3bb3d08342ac47415c62c5c11b2d88b85aa8fe9701d48890b5a8751b88db895a`，候选adapter `2e1d9e8eae27decbcd2d81064baedfe629b0fccb71b13b1dd44afb5bf9ee19e6`，新增路由测试 `4b66d865be871bcd8e153b4e92ad54f37e1bdd0d80451835e4e623950ea00ba4`。helper只引入private`min_block_m`，公共generic默认8、PPU传16并透传split；三个JIT kernel逐AST相等。大group允许>16，不以硬设16截断合法头组。

部署入口`commands/op019-qsa-thead-deploy.py` SHA `8c4bf8dacac58d17b6db7dac67fcc477f8cc626a1cf20a3e8e93fdfa73462ce0`，PPU检查`commands/op019-qsa-thead-validate.py` SHA `bfc06b9f8d08ef51e9819f4009930d8e0512f3aad4a09e63e71b87234ab91084`。命令`python3 <BASE>/commands/op019-qsa-thead-deploy.py`；先排他`mkdir <evidence>/candidate`，scp -O五个候选文件至该目录、两入口至BASE/commands并核验SHA。部署先校验所有旧文件SHA/新增文件不存在、两服务保护基准/8010 idle/i64，写DEPLOY_STARTED和candidate.patch，再docker cp五文件（不pip安装/重启）。先`python3 -m pytest -q tests/test_qsa_attention.py --collect-only`，再同入口执行14项CPU路由（generic/the ad×group3/16/32×single/split，public ABI/导出/CPU错误）；运行在CUDA_VISIBLE_DEVICES为空，仅模拟launch元数据、不冒充硬件。目标容器black/isort/flake8和本地同工具均缺失，不擅自装依赖；AST检查已过，style完整CI记not_run。

CPU通过后仅物理8、allocator2%、空闲及4GiB headroom门禁、独立cache执行PPU检查；4旧冻结BF16输入→split2→gate→非连续stride→empty（无kernel）→warm/capture/两次改变输入与索引的replay，最多16次QSA API事务/0模型请求，原atol.03/rtol.02不变。调用前保存完整输入/索引/gate/workspace及stride/storage，输出落盘再判定，验证公共导出实际来自_thead且两个attention kernel的BLOCK_M>=16。首异常保存输出/日志并停止，无自动恢复/重启/补发；有异常仅冻结现有cache，不继续性能。通过也仅operator-only，无模型gate/性能宣称。缓存原始产物在`/opt/qwen38-op019-qsa-thead-20261016`及对应证据目录保存。回退保留before快照与patch，仅用户后续授权时原样恢复受影响文件，不碰Gems/i64/在线Plugin。

部署v1在**全文件precheck、任何docker cp之前**发现上游已有`tests/test_qsa_attention.py`，保护性退出；仓库仍clean、QSA仍原cf6be...，无测试/设备请求/安装改动。保留DEPLOY_STARTED/candidate.patch草案，不覆盖原测试。仅将新增测试改名`tests/test_qsa_thead_attention.py`（内容SHA仍4b66d...），v2入口`commands/op019-qsa-thead-deploy-v2.py` SHA `e78768940044ab4b54e3deddd69de574f92473ea21103b5bb98d0df43b62976b`，命令`python3 <BASE>/commands/op019-qsa-thead-deploy-v2.py`；新marker DEPLOY_V2_STARTED、补丁candidate-v2.patch，旧草案保留。collect/CPU命令只将文件名替换为test_qsa_thead_attention.py，其余scope/源补丁/输入/容差/设备预算不变。新测试文件需在上游CI显式选择，未更改tools/select_tests全局策略，pr_readiness暂experimental。

实际v2成功：14 tests collected/14 passed，4963条为旧pytest assertion rewrite针对Python3.12的DeprecationWarning，不是模型/GPU异常；PPU共12次QSA API事务（11条存档含1capture enqueue，另1empty无kernel），10份实际数值输出全finite/0超容差，最大绝对误差0.0078125。四冻结输入single、split2/gate/所有输入末维stride2、empty、warm/capture/two changed-input replays均通过；实际function module为`flaggems_vllm.runtime.backend._thead.fused.qsa_attention`，两个attention kernel记录M16。相同random输出SHA与旧M16对照逐位相同。COMPLETED.json SHA `0820843867635d1c32f780449aa12a3c5abf10bdaafb4dd7fb5dc222550fa4c1`，两种cache存在者已复制归档，源码已安装在原editable私有路径供新进程使用，但未重启/加载在线8010。

最终CPU核验入口`commands/op019-qsa-thead-finalize.py` SHA `1333729b31db1552e79104a4103e2d68f97942c0ae5bf0cc8a31ac8eb0331cb3`，命令`python3 <BASE>/commands/op019-qsa-thead-finalize.py`。只校验五个安装源码SHA、12事务/保存输入输出SHA、实际M16和完整缓存清单；CPU空设备验证**真实**新库vendor函数与**真实**候选selected_cached_op对象相同，仅stub vLLM注册入口（不启动引擎/不模拟kernel或vendor分发），不初始化GPU；保存VERIFIED.json并执行目标仓库git diff --check。不会重发任何算子/模型调用，不启动monitor或GPQA。

最终核验成功：VERIFIED.json SHA `dfa9a6064d52ef879eb5a169264ba4eeb929c7d8eec7894cc589102e6fb1e925`，125份文件/缓存逐SHA，实际安装五文件与候选相同，metadata测得generic group3仍M8、PPU为M16且large-group32不截断；真实候选selected_cached_op对象与真实PPU公共导出相同。CPU空设备import出现device_info能力查询fallback和cudaGetDeviceCount driver-shutting-down **UserWarning**，`torch.cuda.is_initialized=False`、未发射kernel且8010最终health200；不将空设备探测warning误报为服务/设备事故。目标仓库git diff --check通过；black/isort/flake8未安装记not_run，未擅自装环境。原测试未改，最终FlagGems-vllm dirty恰为common wrapper、thead fused导出、新thead QSA、新路由测试；候选Plugin仅adapter改变、在线Plugin/i64仍原SHA。

本次交付`limited/operator-fix`：PPU特化源码已进入当前editable安装，对新Python进程从`flaggems_vllm.qsa_sparse_paged_attention`调用生效，single/split均floor16；通用入口默认8不变，无torch compute fallback或kernel复制。按最小回归技能完成14项CPU路由+12事务PPU有界验证，完整输入/索引/输出/编译产物保留。**在线8010未加载此新组合**，仍017原实例；无新的TP8模型请求、精度分数/gate、性能数字或重启。8035本轮变更前已不监听，之后维持缺席，卡0–7未操作；不将此状态归因本补丁。用户要求的后端特化实现已完成，进一步重载8010/模型回归需先报告取得方向；不自动重用旧两次重载/99请求计划、恢复heartbeat或GPQA。pr_readiness=experimental（非PPU硬件/FP16/生产rows/TOPK/模型回归及CI选测/格式工具未覆盖），既有正式精度blocker不被operator pass解除。

### QSA-only M8/M16受控定位：执行前冻结（用户最新授权）

仅诊断QSA，不恢复旧99请求/两次重载流程，不改安装源码/当前Plugin或i64修复，不重启8010，不影响8035，不恢复heartbeat，不发模型请求或全量GPQA。21:50+08只读预检两服务身份/argv不变、8010 idle、物理卡8有约13.4GiB空闲且只有本任务worker，实际QSA与i64双SHA不变。限定物理卡8、进程allocator上限2%，4份**新**CPU冻结输入（random-unique33、random-duplicate33、basis-k0-top16、basis-k16-top16），Q[5,3,256]/KV[8,16,1,256] BF16，原非连续table/invalid request。不得称这些张量为先前17:55缺失的原现场。

新证据目录`<op019 evidence>/diagnostics/qsa-m8-m16-001`、私有非安装副本`/opt/qwen38-op019-qsa-m8m16-20261016`均排他创建。复制真实上游QSA，仅wrapper的`block_m=max(8,...)`与`max(16,...)`一行差异，kernel AST完全相同。CPU FP64独立reference与官方CPU reference交叉检查，冻结完整Q/K/V/indices/table/requests及valid/physical-page映射并重新加载校验SHA。每份按M8→M16→M8，另M8/M16各一次capture与两次改变输入/索引的replay，共最多20次QSA API事务（含capture enqueue，不等同20个实际执行kernel），零模型请求/重载。每次调用**前**保存实际GPU输入的CPU完整副本及stride/storage/pointer、初始out，输出保存后比较atol.03/rtol.02；M8数值异常先排他保存首次证据，再仅完成已冻结M16/M8对照，M16失败、输出不稳定、非法访问/nonfinite或服务身份变化停止，不自动重试/修复。M8数值通过/失败均不能代替模型精度。

执行入口`<BASE>/commands/op019-qsa-m8m16.py` SHA `dcb0c2428f73e850109dc1351e599f0ad9e13c00d03e9e069a23ceb9262c9cc4`；host控制`<BASE>/commands/op019-qsa-m8m16-host.py` SHA `985d72d8e1fbe98b11fc4f64347ef65c33ce6873c5ae2f3fea31e1a564fe73bc`；命令`python3 /mnt/nfs/users/jinghao/qwen3.8-flash/20261015-qwen38-flash-next-ppu07-container/commands/op019-qsa-m8m16-host.py`。传输前检查两文件与目标目录不存在，`scp -O`保存远端执行副本后核验SHA。host控制先核对镜像/挂载历史回执、两服务和i64/source，再CPU prepare→GPU run，专用Triton/Gems缓存隔离；首次编译对象asm与全缓存、完整run日志、8010既有服务日志固定前缀和文件SHA清单归档。任何缺失如实记录，不声称模型raw/token（本轮零模型请求）。

首个host预检在创建证据目录/私有副本/任何GPU上下文之前停止：显存解析错误地在卡号行找Memory-Usage，实际显存值在下一行，因此`mem=None`触发assert；这是控制脚本问题，不是OOM/模型/算子异常。21:59只读ppu-smi确认卡8仍84886/98304MiB、仅2250796 worker，其余服务不变。保留远端原脚本，修正入口另存`commands/op019-qsa-m8m16-host-v2.py` SHA `7a00436e1c6485a554a6b15545cd2e79012ff9e9b8d9387cf433f53e2aaa0b46`，命令`python3 <BASE>/commands/op019-qsa-m8m16-host-v2.py`。仅改预检选取Memory行，不改变任何数值输入/范围/实现/容差；原诊断目录尚未创建、GPU调用0，重新核验后执行冻结范围，不掩盖预检错误。

设备对照已于22:00+08结束，20事务，零重载/模型请求；两随机fixture M8失败、M16通过、切回M8逐位重现，graph两次replay同结论。首次数值marker时间22:00:47.028765+08，完整调用前tensor与输出已落盘，不再有旧runner帧筛选缺口。170份原始文件/4个编译配置，`EVIDENCE_MANIFEST.json` SHA `fd40286cf9548d74b7201389f3597d0800df8f3fe69d9f1a2ac251c0a612fa59`，包含专用缓存、TTIR/TTGIR/LLVMIR及hgbin/cubin。EXIT确认8010/8035与所有原source SHA不变、8010 idle。

下一步仅CPU核验现有证据：`commands/op019-qsa-verify.py` SHA `9a75738926feb1d604a87dc70aa93bccfff86bcebb2d587cca7e65428cd9f6a5`；命令`docker exec -e CUDA_VISIBLE_DEVICES= qwen3.8-flash-opt-ppu07-20261015 python3 <BASE>/commands/op019-qsa-verify.py`，排他写`diagnostics/qsa-m8-m16-001/verification-001.json`。逐170文件SHA、20输入快照/完整映射、18实际评估输出、M8重开与graph/eager逐位一致、单行source差异与4个实际编译constexpr核验，不导入QSA/初始化GPU，不修改既有证据/服务或追加计算请求。缺失/失败如实保留，不补造。

### QSA-only结论：M8数值失败可重现，M16局部通过，未部署

CPU核验成功，`verification-001.json` SHA `1c6d0a76f87f24fed8646e90694066e7b7a109c0ee44826eccd27c726596aa54`。170原文件SHA、20次调用前完整输入/索引/映射快照及输出SHA全部一致，18份实际输出完成数值评估；另两份capture仅保存不将未执行capture输出当结果。4个实际编译配置涵盖M8/M16×TOPK16/33，runtime记录确认GQA3、D256、N16、warps4/stages2；两副本只有wrapper第683行`max(8,...)→max(16,...)`差异，kernel AST与JIT body hash相同。保存源码、launch metadata、TTIR/TTGIR/LLVMIR、hgbin/cubin与Triton完整缓存；Gems cache本轮未生成，如实记录。

| 新冻结输入 | M8 mismatches/3840 | M8 max abs / relativeL2(FP64) | M16 mismatches/3840 | M16 max abs / relativeL2(FP64) |
|---|---:|---:|---:|---:|
| random-unique33 | 2684 | 0.96484375 / 0.78415958 | 0 | 0.0078125 / 0.00238617 |
| random-duplicate33 | 2671 | 1.61328125 / 0.82242131 | 0 | 0.0078125 / 0.00240228 |
| basis-k0-top16 | 0 | 0 / 0.00148642 | 0 | 0 / 0.00148642 |
| basis-k16-top16 | 0 | 0.0234375 / 0.01535798 | 0 | 0 / 0.00148642 |

M8→M16→M8每fixture两次M8输出逐位相同，排除本次一次性随机波动；M8/M16各capture一次、两次replay使用不同完整输入及索引，同fixture各graph输出与eager逐位一致。因此本次不是graph专属故障；重复索引和非重复索引两组均复现差异，不能只归因duplicate处理。18份已评估输出均finite、invalid request行精确零，所有输入调用后未变。basis-k16虽有系统偏差，但仍在冻结容差内，不能把这两份弱基向量测试说成全K onehot证明。

首次新异常`FIRST_NUMERICAL_ANOMALY.json`原时间`2026-10-16T14:00:47.028765+00:00`（22:00:47+08），对应`calls/000-random-unique33-m8-eager0/inputs-before.pt`、`BEFORE.json`、`output.pt`及`builds/m8-f116492f2b51/`。这是本次完整保全的新现场，不补写旧17:55缺失张量。调用日志无非法访问/OOM/traceback，未出现nonfinite；仅可说本轮小算子未观察到，非旧服务故障已修复。

**根因置信度：**当前PPU/Triton3.6.0、BF16/GQA3/D256小QSA的M8 tile编译/执行分支为`reproduced-single-variable`，M16可作为后续限域绕行候选；具体A-fragment/ldmatrix缺陷仍`suspected-not-causally-isolated`，未做QK/PV拆分、全K基向量或A-only编译地址干预，不照搬MiniMax机制结论。无production rows/TOPK2051/长上下文、模型回归/精度gate或性能测量，不归因此前未启用新库的GPQA错误；本轮小cache索引不覆盖20972，不替代i64模型边界证据。

结束回执8010/8035身份/argv、active/candidate源码、安装QSA及i64双SHA均不变，8010health成功/running0/waiting0；本轮模型请求0、服务重载0、未安装M16/启用新候选或恢复heartbeat。设备工作已结束，等待用户下一步方向；不自动使用旧99预算、不追加请求/重启/全量GPQA。知识差量为`refined`：新QSA导入先冻结原始tensor并显式检查实际BLOCK_M，M8失败→M16通过→M8重现可先隔离tile路径，但不足以确认底层编译器地址机制或正式模型精度。

分类operator/replace，子组HC、PLE、QSA分别显式实验开关，可独立二分；默认关闭保持旧模型/非目标路径。当前模型局部Torch组合和FlagGems扩展作为reference；通过模型内最窄调用边界接入官方FlagGems-vllm 6568039，不改vLLM/权重/tokenizer，不复制算子kernel或新增通用dispatch体系。关键索引null=0、padding、has_initial_state、无spec decode、FP32归约/BF16舍入、输出别名、kv原地更新及graph workspace语义逐项核对。不吞运行错误；不支持shape保留原正确路径，导入/能力错误显式报告。

GDN实现与gather/clear/scatter暂不替换，FlagGems private017 index/index_put先提升int64的两个SHA必须保持。PLE新状态IO的原始NULL/write_mask语义与GDN状态索引区分。QSA先接入cache写入、pool压缩及sparse attention，selection/topk与动态score范围保留，不恢复旧static score columns。只有API/语义可匹配的函数进入对应组，不为凑齐导出强行改架构。

## 验证计划与停止条件

先在新私有Plugin副本落补丁，旧运行副本只读；做AST、接口与CPU路由/契约检查，不把mock当PPU精度。当前旧受控客户端16:48检查仍120派发/118完成/2在途，原tail8尚待，禁止与其叠加模型或GPU算子负载。GPU数值、graph capture/replay与模型受控验证要在原请求排空且单独加载候选后执行；加载候选需要8010重启，必须先报告并等待用户确认，不自动停止/重启或恢复heartbeat。

拟受控端到端上限120新请求（baseline/candidate合计、零重试、C<=8），执行前进一步冻结原生runner配置/SHA：精度baseline8、candidate8+8重复，共24，固定历史8目标/原采样seed1234/max60000/stop；性能每角色3个小场景、每场景warmup1+measure3、每轮N4/C4，共48/角色、合计96。Prefill P4096/D1、Decode P256/D256、Mixed P4096/D128，映射P4K正式场景、与正式D1024/C64/N128差异明确；TTFT/TPOT只作客户端代理，guard输出健康/错误/状态、两次graph replay及FP32状态边界。稳态不满足则incomplete，不删慢首轮。没有同配置baseline或需要改变debug同步/服务参数时先报告，不跨配置计算加速。追加或revert重启另需方向。本计划尚未发请求，最终配置须在运行前冻结；不会使用formal198题入口。

## 当前状态与证据

接入准备阶段原始快照（已被上文首次数值失败替代）：源为`/opt/qwen38-accdiag017-i64-20261016/plugin`，目标私有`/opt/qwen38-op019-fgvllm-20261016/plugin`，Gems保持private017。远端证据目录`/mnt/nfs/users/jinghao/qwen3.8-flash/20261015-qwen38-flash-next-ppu07-container/operators/op-019-fgvllm-integration-20261016`。没有新端到端性能数字、模型精度结果或模型命中新路径证明。

准备入口`commands/op019-prepare.py` SHA `cebe3c08669fad34b0e97d99ff735d38e74a60371fc5021d06266af1dbdbbc8c`，命令`python3 <script>`：新建唯一证据目录/私有Plugin副本（不复制git/pycache），保存所有Python源码SHA及model-before.py，原运行源码和Gems保持只读，不发请求或停止进程。

prepare已完成，model-before SHA仍`2c36d1c3334d910c50be8c54e5337808fe8f2f02e3e01d7107a532875b3a184f`。QSA/PLE state已有CachedOp→FlagGemsBackend入口，复用这些入口选择新库，不绕过通用registry；HC/PLE新融合在模型的原custom-op边界接入，HC额外提供fake schema以保护torch.compile。只读导出候选副本backend作本地补丁：`docker cp <container>:/opt/qwen38-op019-fgvllm-20261016/plugin/vllm_fl/dispatch/backends/flaggems/flaggems.py <evidence>/backend-before.py`，不改运行源。

待执行CPU契约检查：先检查`commands/op019-{model,backend,adapter,cpu-contract}.py`不存在，再用`scp -O`分别保存本地补丁与检查脚本；在容器内运行`python3 <BASE>/commands/op019-cpu-contract.py`，stdout/stderr单独保存在本实验`cpu-contract-001.json/.log`。只导入CPU torch，以stub替代新库和vLLM注册工具，使用真实torch.library schema/custom-op/fake注册测试路由，不调用GPU、模型API或改生效路径。HC比较提取的旧类与新类，不能证明真实融合kernel数值。失败保留日志、不掩盖。初始四文件SHA依次为model `c28634fa07b816c2c2e87daea2258247cd8996c5603d9f4377d1daecb059f779`、backend `4e910e10532146befc5bfa3fd42e58ebe9dc99d18f7740e957a8e4b815bd3363`、adapter `636a28e5390c9cdb2ab1ae8b9543172abb8439c5b341ea5507740fce3aa997c9`、检查脚本 `7edb8c89a6bf4b2caa94a6c02009f1de7dcc18fd1af2ff3e62c6e7b3f32856bd`。必要PLE限制为三份norm的group_size均等于hidden_size、eps相等、prefill/decode状态与输入dtype相等，NULL显式使用当前模型0而非上游默认-1。

CPU检查001实际exit=0、41项通过，真实torch.library四个schema/fake成功，未初始化加速器；model AST只改GroupedGemmaRMSNorm、GatedResidualSimple、PLELayer三个类，GDN类不变。这里HC上游执行函数是CPU stub，**不能证明真实PPU融合kernel保持舍入/数值或graph正确**；上游融合内部FP32累计与旧Torch中间BF16舍入的差异必须实测。

待执行部署入口`commands/op019-deploy-private.py` SHA `66a2bfe0fc627cafb73793f7493ab24ff79446b5cfe7d43eb4d2c307c86b2d15`，`python3 <BASE>/commands/op019-deploy-private.py`：先验证CPU报告、PREPARED所有Python SHA、8010/8035实例及argv、私有目标不在生效PYTHONPATH/挂载中、旧model与i64双SHA；排他创建DEPLOY_STARTED，只docker cp三文件到新私有Plugin，写candidate.patch、完整Python SHA与DEPLOYED_PRIVATE.json，再核验旧source/i64/两服务身份未变。不修改安装依赖/旧Plugin/Gems/observer，不重启、不发请求。若失败保留原始错误，不能假定候选已部署完整。

私有部署已完成；DEPLOYED_PRIVATE.json SHA `916ba8835114f652e3cf100c5e26fd70d907e8e1b925c7b44f4c07b5b248dd2e`，candidate.patch SHA `bf4349b291f3895f3030fe42534fd6099f0199920ad65a27e30fa79d8ae498ca`。两个原进程身份/argv不变，旧model及i64双SHA不变；新副本仍不在活动PYTHONPATH，零重启/零GPU数值测试/零新模型请求，pr_readiness=experimental-not-hardware-validated。

## 加载前发现旧017终态异常（与新算子未生效区分）

只读检查发现旧客户端2627674已自然退出，17:02:53+08终态`stopped-on-anomaly`，120派发/120完成/errors0/inflight0，尾部seq120..127八条未发送。首次输出异常seq10/doc32，HTTP200，60000 completion tokens，finish_reason=length，content=None，191706字符reasoning，think-end位置为空、terminal token561；原始response SHA `7b23ee33ae3f6b838b1a2ebda13478cd8dc928071c509f342259d498370df2b6`。这是60K上限截断导致的reasoning-only观察，不是网络TIMEOUT，不是本次新库回归；不能直接断言与旧非法访存同因、或i64修复已解决输出健康。需要按inference-accuracy-diagnosis保全旧证据，并将新算子hardware validation继续标not_run。

拟执行现有证据冻结`commands/op019-preload-incident.py` SHA `1a93a22a55a8253a12dc8375b43ec80e5b563b48ed630d0a9da00500011860cf`，命令`python3 <BASE>/commands/op019-preload-incident.py`：目标新排他目录`<op019 evidence>/preload-old017-incident-001`，复制已有120条raw request/response/result、marker/固定服务前缀/身份/配置；逐rank0–7读取、复制、SHA和边界汇总原始events（合计约1.93GB），提取原已存在rank0 sampled prefix，核验60000 API token及唯一序号；不发请求、不触碰源码/服务或rank-1人工微测，不补缺失状态。若保存的selected state仅last-writer或driver日志未取，明确缺口而不宣称完整因果证据。先核对磁盘空间，再执行；不复用原目录。

冻结已成功，report SHA `813fbf0f58fe3eaf04bc86bab022540eaada7a41e6a66d4dcadb7ab8cefb800c`。120份完成结果对应110唯一doc，119份非空最终输出，1份空最终/60K length；完整60000 API token中think-end和两类EOS均0，最后561。8rank generic gather/scatter最大18736、stride102400、i64/i32 offset均1918566400、storage边界合法；模型generic20972边界仍not-covered，未发tail8，不能以算子微测代替。此前服务错误粗搜匹配了ModuleNotFoundError等WARNING文字，不作新增服务故障结论。

补充冻结证据复核`commands/op019-incident-verify.py` SHA `637d96bd47657c90f07cf855f37474686feb0bd14c8569a050311a0b3193918f`，`python3 <BASE>/commands/op019-incident-verify.py`只读新冻结副本，保存verification-001.json，核对全部raw SHA/API token数、rank0原始post-sampler序列与API、8rank packed实际索引/invalid/nonfinite/operator mismatch、固定服务日志严格ERROR/非法访存。零额外请求，不改已有报告。

首次复核脚本遇到部分既有device observation的`actual_indices=None`而TypeError退出，尚未签verification；这是**只读分析脚本错误**，非模型/HTTP或设备异常，不改原日志。修正版另存`commands/op019-incident-verify-v2.py` SHA `17436910b30047e7749fbafe1f3eba8d565bbb9f026900ad916b473f6f19c9dd`，同样`python3 <BASE>/commands/op019-incident-verify-v2.py`，对None显式计missing而不是捏造索引或零状态。原脚本和原始冻结report保留。

v2复核exit0，verification-001.json SHA `2b9a0d5dcb599942afb317c88ed6018ebe6000aea1f40a81eb14dd8a13afac76`。全部120 raw SHA/usage/token数一致，doc32实际rank0非discard采样序列60000个token与API逐个一致，排除仅parser把已有think-end漏掉的解释（原API也无think-end/EOS）。8rank实际已记录packed max18729，与generic18736分别报告，均未跨20972；已记录invalid/nonfinite/operator mismatch均0，固定服务前缀无严格ERROR/非法访问匹配。每rank75165条device observation的actual_indices为None（记录可能去重，未在本次复核重建），不把它们冒充独立完整索引采样，不把无已记录异常外推为所有状态正确。完整原始events已保存可继续离线分析；新路径依然未启用。

远端准备过程有一次独立只读SSH不存在检查连接超时，其他SCP/实际部署回执及CPU检查成功且身份二次核验；不把连接超时当服务/模型异常，未重发任何推理。最终本地state校验、README生成和git diff --check通过。

## 需用户确认的加载范围（尚未执行）

仅8010/物理8–15按顺序两次重载：先私有019新接入开关全部关闭，建立匹配基线；再同一源码/配置启用`hc,ple,qsa`候选。保留017 i64 Gems和现有诊断语义，不动8035/容器本身/共享源码。两角色均在CLI支持核验后显式`--no-enable-prefix-caching`，核验实际runtime关闭；因此不能用当前缺少显式flag的旧服务直接充当精确性能基线。新证据根/缓存各自隔离，记录缓存准备差异；不得把debug同步耗时当生产性能。

为保证预热和新异常哨兵，拟将上文初始120请求预算内的草案细化为**99新请求/C<=8/0重试**：精度原8目标加doc32，共9，baseline一次、candidate两次（27请求）；性能Prefill P4096/D1、Decode P256/D256、Mixed P4096/D128，每角色每场景N2/C2，固定3预热+3测量（36请求/角色，合计72）。原9题payload/seed/采样/stop/max60000不改；doc32含历史60K风险，保留raw/token，不借改温度或缩上限规避。性能用维护版vllm_perf，末2预热窗口主指标(max-min)/median<=10%且无编译/错误，所有3测量轮均保留，波动<=10%；不稳定则incomplete，不追加预热/丢慢首轮。两角色只改变新算子组开关，其余服务/工作负载/观测条件相同。尚未生成原生runner最终配置或发送请求，必须执行前冻结SHA；本草案取代初始N4/单预热方案，不扩大120上限。

先做有界PPU算子reference/alias/mask/null及graph两次replay检查，再发模型最小回归，精度/输出健康异常时停止补位、仅保存已在途原始证据并报告；是否继续性能需据异常分类判断，不以旧60K截断单独假造正式精度失败。无相同配置baseline或无回退/独立重复证据时，性能结论保持局部诊断/incomplete，不宣称正式加速。若需第三次重启进行组间二分、revert或故障恢复，先另报用户，不自行执行。
