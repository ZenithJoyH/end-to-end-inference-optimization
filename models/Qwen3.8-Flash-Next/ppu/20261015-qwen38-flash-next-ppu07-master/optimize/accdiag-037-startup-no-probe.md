# accdiag-037：固定env035、关闭模型诊断埋点的单次启动对照

状态terminal-failed-startup-with-model-probe-off；原始SIGSEGV已核，纯单变量A/B因外部取证工具的早期干扰而incomplete。用户2026-10-19授权仅8010一次启动/重载，固定当前Plugin/FGVLLM及FP32/i64/QSA M16，仅关闭模型诊断埋点；保留worker原始退出信号、完整日志和编译产物。不访问8035、不发送任何生成请求、不全量GPQA、不自动重试/回退。按inference-accuracy-diagnosis的execution-mode定位，不是accuracy minimal-regression或正式性能测试；旧acc015164/198 failed-score/no gate与性能阻塞不变。

## 假设与门禁

- 对照036启动显存探测/profile-compile中的worker3退出。固定Plugin a696859b+PR4553cb373b1及本地FP32 helper、FGVLLMb4d3382、017 Gems i64、PPU QSA M16；核全部源文件SHA与036 before、模型/config/tokenizer、容器镜像/挂载/设备和原CLI字节。
- 已只读确认8010无监听，故不发SIGTERM、不停止容器、不访问其他服务。若执行前发现8010重新出现或原036相关活进程则拒绝启动，不擅自停止。
- PYTHONPATH移除036bootstrap，unset DIAG036/021及旧DIAG016变量；保留3个实际包路径，无sitecustomize/probe导入。诊断代码旧文件不删除、不修改模型/依赖源文件。
- 使用独立空私有037 vLLM/Triton cache，对照036原冷cache；保留FlagGems缓存/DB原设置并记录其内容指纹。目录路径、新进程地址、已有共享tuning缓存的热度和外部退出跟踪时序仍是归因限制，启动成功不等于埋点唯一根因。
- 仅原graph服务启动/capture；不做请求、replay验证、smoke、精度或性能评测。就绪需health200、原CLI与API身份、日志两类graph capture及零请求计数；启动失败/时间预算90分钟均只取证，不停止/重试。成功后保留服务。

## 原始退出信号保存

容器未安装strace。已在该容器用无模型`/bin/true`子进程确认PTRACE_TRACEME/CONT可用，未调用GPU。采用独立stdlib/ctypes进程监护程序，只跟踪新启动树fork/vfork/exec/exit和信号投递，不跟踪syscall、不读tensor、不注入Python模型hook、不修改vLLM。捕获kernel exit-event原始wait status（在vLLM reap之前）及最终waitpid、signal/siginfo、各被跟踪子进程身份；真实信号原样转发，不吞异常、不追加重启。进程外ptrace仍可能改变调度时序，明确不称完全无观察影响。成功后监护进程可随服务继续被动保存未来退出，不做后台推理。

执行前冻结`CASE/commands/accdiag037-proc-watch.py`与`accdiag037-control.py`。先无模型fork/信号fixture验证退出码37和SIGUSR1能完整保留，再prepare核SHA/空端口/不重复标记，唯一launch。原始产物集中`CASE/diagnostics/accdiag-037-startup-no-probe-20261019/runtime-001`（R37）。输出service.log、process-watch/events.ndjson、preflight/source/launch/READY或STARTUP_FAILED、完整编译cache清单和归档/SHA。没有worker退出时明确“无退出信号可报告”，不补造；跟踪缺失明确记incomplete。

执行前脚本SHA：process-watch **3ba720aacb8cc0fdd91b849a3a9ccd6f5ecc45241daf83d18a128a6cb6dfde44**；controller **632cc4d2463f8782a5dd8cc7d424cb26721aff90f4ec212ce36e48a227595857**。本地AST通过；首次本地py_compile因系统Python试写workspace外bytecode缓存被拒，不是远端模型故障，改为不写文件的AST检查。PPU-07 inventory及connectivity三项通过（首次沙箱内Ansible RPC未启动，提权重跑预检通过）；不把SSH退出码替代连接验证。脚本SSH stdin排他上传，核SHA后执行无GPU fixture；controller仅prepare→唯一launch，monitor只GET8010 health/metrics和读自产物。

无模型fixture已捕获实际exit37、SIGUSR1(raw status10)和父进程exit0。首prepare在SDK envsetup banner+JSON的stdout解析处失败，尚无LAUNCH_ONCE/模型进程；source-before及launch文件保留，PRIVATE037 cache仍空。此为CPU预检工具解析错误，不是启动复现。修正`accdiag037-control-v2.py` SHA **aa08310a33689f889eda975c43a79f3fd839a289b6781a52f93bce7b84bce65b**，新增显式complete_prepare仅核已有源/launch/fixture、带sentinel重收CPU import检查并排他写PREPARED，不覆盖或重建目录，不改模型路径/CLI。核通过后才唯一launch，0模型请求预算不变。

PREPARED SHA **f61210db3ca482c8df33f887c8e1017b478506cd33dd59cb863eaaf5100250f9**；launch SHA **32b0ec1e93a2e2e8c254e7def431c6a3c46e1f88e84d5f2252697ba118929aac**；source-before **efbbb570d82414824459262a1de97c4036c523d4908db7a169eea2cfad0ff0e9**。全部Plugin647/FGVLLM1061文件与036相同，critical4项FP32/i64/M16及权重/config/tokenizer一致；mount_parity passed、sitecustomize spec=null、3包spec明确指向原固定私有目录。冷cache及日志路径之外，CLI完全同字节；共享tuning/gems保留、仅metadata记录不宣称回滚到036前热度。

唯一launch已执行，Host monitor2005306；LAUNCH_ONCE原件排他保存。8010原本无监听，因此发送停止信号0。此后只监控既有启动树和产物，不再执行launch/prepare或任何推理；process watcher运行于模型进程外。

### 外部退出监护干扰（不是模型异常）

14:41:58后启动无推进。只读限定本次Docker exec启动树确认：7个worker主线程futex等待，各2个辅助线程为T(job-control stopped)、TracerPid0；rank3已进入PG初始化且辅助线程正常。外部watcher早期收到子进程initial SIGSTOP可能先于parent fork-event，将unknown child初始stop误按真实信号转发，造成job-control状态残留；该机制与现场一致，故本轮**不再视为干净的observer-off A/B**，不把停滞归因新版本/模型，也不因rank3尚未死亡称启动通过。无模型fixture只覆盖了简单fork，未覆盖多线程spawn竞态，是取证工具覆盖缺口。

正常恢复由工具造成的暂停，不重新启动服务：执行前保存`CASE/commands/accdiag037-resume-owned-stops.py`，逐进程核Host/NSpid/start_ticks与原监护事件匹配、当前TracerPid是本watcher，排他冻结线程状态/事件前缀后，仅对本次启动树中确有未跟踪T线程的进程发送SIGCONT。不发SIGTERM/KILL/STOP，不改模型/依赖/埋点，不访问其他启动树或8035，不重发请求，不重复launch。回执单列此操作及对照无效限制。若SIGCONT后仍异常，只保存现场，不自动重新加载或替换监护器。

## 决策

首次暂停解除脚本SHA **acc5983fc0e891147371024a35006114671bc745b703e152d2338407e4d1aa8b**，仅7个精确worker SIGCONT，随后all8 NCCL Init COMPLETE，证明先前停滞确与外部监护有交互，不作模型故障。为避免ptrace再次干扰后续线程，先无GPU验证Host Linux process-connector事件：自己的CPU子进程exit37记录raw9472/parent_notification17，未访问其他服务。下一执行副本：`accdiag037-kernel-exit-watch.py` SHA **0f36f2fc947326ab5d50053038677e60f2b5fd2b97739acd5f433b2aa84e3ca6**，仅内存过滤原精确启动树及其后代并保存kernel原始exit_code，不暂停或修改模型；`accdiag037-detach-own-ptrace.py` SHA **7b93b26f1d806a6c9a8e7a2d486a301682e4448b0e4fc5b920bccfe014876373**，先确认被动collector READY，再只SIGTERM本任务自建ptrace watcher2005293（不是API或worker），由Linux自动detach，核原树TracerPid0后SIGCONT残留T线程。先保存线程/日志前缀与回执，模型启动次数仍1、模型终止/停止信号0；若身份/退出不满足即拒绝，不升级kill。模型源码/CLI/无hook条件不变，但经历暂停，结论保留measurement-invalid-for-clean-AB限制。collector仅保留本任务tgid，不查询8035。

被动collector2273977已READY并捕获本任务外部watcher在14:53:59原始SIGTERM15；该项是主动移除工具，**不是模型事故**。移除回执`ptrace-removal-001/receipt.json`记录16个原树进程解除残留停止、全部原start_ticks相符，模型重启0/终止信号0。14:54:36已进入模型层初始化，14:54:44 Dynamo transform8.52s，14:54:56 Cache graph compile range(1,8192)，无模型worker致命信号。此前辅助线程停止污染初始化时序，不以本轮耗时评估启动性能或宣称干净A/B。之后不再更改监护方法/模型配置，仅既有被动取证和等待。

### 关闭模型hook后仍启动失败（首次真实模型异常已通知）

14:55:12 Engine报告VllmWorker-3死亡；kernel实际退出事件14:55:13.240403+08（event接收时间，精确kernel_timestamp_ns原件保留）首先记录Host2026192/容器2822365/TP3，raw wait status139 = SIGSEGV11 + core flag，随后其余7rank同raw139。这不是早先主动移除工具的SIGTERM15，不是GPU非法访存的直接证明。`service.log`含8段原生`Segfault encountered`，顶部`hgiFoutputSubEntryValidate`→`_foutputEntryValidate`→`_foutputParseFormattedOutput`→`foutputFlush`→`_synchronizeUser`→`hgCtxSynchronize`→`cudaDeviceSynchronize`，比036只见cancelled更接近原始故障边界。具体造成异常格式输出/状态的kernel或主机内存问题仍未隔离，不把同步点当首个坏kernel。

被动collector已自然结束、tree-complete，8010无监听；无生成请求、未出现READY/graph验收。已通知用户后仅冻结，不自动恢复/重新加载/做GPU试验。收尾脚本`CASE/commands/accdiag037-finalize.py` SHA **d9fbbd304f426a8df972c7ae36986d526f50e37aba3b485a1b2c7ef04e843953**执行前冻结：核8rank原始退出/全部已退出和空端口，停止仅本任务Host等待monitor（旧monitor不认识替换后的kernel FINISHED），复用冻结controller中只读freeze函数核源/归档cache，再补齐kernel全部原始事件、工具干扰回执、完整native/service日志及SHA。系统core策略由systemd-coredump承接，core flag不等于已存在物理core；不导出可能含权重/巨量运行内存的core文件。任何归档预算/核验失败如实记，绝不重试模型。

## 已核验终态证据

R37完整绝对路径：`/mnt/nfs/users/jinghao/qwen3.8-flash/20261015-qwen38-flash-next-ppu07-container/accuracy/acc-015-full-gpqa-ppu07-c64-current-i64-qsa-20261018/diagnostics/accdiag-037-startup-no-probe-20261019/runtime-001`。

- `FINAL_SUMMARY.json` SHA **24cc9034a5a751f011e29beb9ca2ff242c5f3b79fb450a296d66a253ec8a7258**；`post-startup-audit-001/report.json` SHA **4aee7555f51cec6df01315b8d162fa3fec737cfe6b3520ef9326a06b07d3fbf5**；该目录manifest SHA **53f265704606586b62e2df6b3b63351b82fbd78a55ffa49de608807e1bf8ad2a**，24份派生文件大小/SHA独立复核通过。
- `terminal-evidence/private037-cache.tar.gz` **6,426,454 bytes**、SHA **0b2d1dbb60692ad9ad14b6af8f4e771060c3ace11087287d25ab3baf7d6cf568**，全部1692缓存路径（逻辑48,849,088 bytes）解包逐项SHA通过；原始私有cache不删除。8份最新PLE embedding benchmark源码保存，仍0份对应kernel_perf完成回执；与036可疑窗口一致，但不是指认首个坏kernel的充分证据。torch保存源码明确使用`os.path.splitext(mod.__file__)[0]+'.kernel_perf'`，后缀判断已核。
- `post-startup-audit-001/service.log`含完整8段Segfault原生栈及后续取消/引擎失败；`kernel-exit-watch--events.ndjson`及FINISHED含被动内核原始退出、首TP3/all8 raw139、fork/exec映射及终态。core标记不冒充已收集物理core或全内存现场。
- Plugin647/FGVLLM1061源文件与before完全一致，FP32 helper、i64 index/index_put、QSA M16及模型/config/tokenizer SHA未变。模型诊断bootstrap未在PYTHONPATH，sitecustomize spec=null；无新模型取证hook、请求、replay或精度结果。目标容器running=true/OOMKilled=false，cgroup oom/oom_kill仍0；这不排除GPU侧错误。
- 8010无监听，8worker已退出；被动collector已自然退出，等待monitor仅由本任务收尾清理（非模型），没有遗留后台评测/重试。一次模型launch；停止/终止API或worker信号0，工具造成暂停的SIGCONT及只终止自建watcher/monitor均有独立回执，不能遗漏或混成模型事故。无8035访问，旧heartbeat仍PAUSED。

结论：**关闭模型诊断hook后仍观察到编译阶段原生SIGSEGV，不能仅归因采样/模型埋点；具体上游算子、PPU运行时或编译输入问题尚未隔离。**早期ptrace干扰已明确披露，所以不宣称完成干净observer-off/on因果二分，也不据此将新版本兼容问题定为已确认。最窄新增已证边界是PPU formatted-output flush/parse的同步崩溃。下一安全工作可仅基于本轮保存的native stack/embedding benchmark与生成IR继续离线定位；新启动/改配置/设备复现仍须另获用户方向。formal gate=null，性能不得恢复。

若复现退出，按原始信号及最后编译阶段与036对照，不把cancelled当首因；若启动成功，仅支持“当前包在无模型诊断hook条件下可完成本次启动”，仍需反向复现才能确认观察器因果。任何进一步推理/重新启用hook/编译配置二分都需用户新方向。原始证据不覆盖，无formal gate/性能结论。

## 继续定位：仅离线saved IR与地址证明（2026-10-19）

用户要求继续查原因；沿用inference-accuracy-diagnosis，并按key-operator-analysis共享方法区分编译期输入生成与模型embedding kernel。当前是启动(profile/compile)阶段，不是请求Prefill/Decode或性能实验。范围仅已冻结037 archive/native日志、当前相关源文本+SHA、stdlib CPU标量/AST分析，不重启/恢复8010，不访问8035，不发推理或GPU测试，不修改推理源码/黑名单。

新线索：archive中`HTQ7PPNV5RXVQTFC7DA6S65WRYMVQ7EDEDEECFGVXQBMB5LU5OJA/randn_kernel`为BF16输出、N:i64，直接debugloc指向private017 FlagGems `ops/randn.py`。TTIR/TTGIR/LLVM均保留`pid*2048`的i32乘法/左移，off_0..3仍i32；比较mask时才signed-extend为i64，指针GEP也signed-extend旧i32。对benchmark weight40000192×160（N6400030720、grid3125015），block1048576/lane0/store0的正确offset2147483648会wrap为-2147483648，`offset<N`依然true，BF16地址是分配base之前4294967296 bytes。不是RNG counter特意wrap的语义：该N的Philox i4最大1600007679仍未溢出，出问题的是后面×4的输出地址。

明确区分两层结论：保存IR可证明大N时`randn`地址存在缺陷；实际导致hggc foutput native SIGSEGV的因果尚未闭环。randn LLVM本身没有printf/assert调用，不能直接说它在输出消息；负偏移写可能污染邻接设备内存，但没有现场allocator/printf buffer地址证明污染了哪块内存。上游大PLE融合benchmark的新调用路径可能触发这个已有缺陷，不等于PR455/QSA本体出错。normal_黑名单不自动排除单独注册的randn路径。

执行前拟冻结`CASE/commands/accdiag037-offline-randn-address.py`，排他输出`R37/offline-randn-address-001`：核原037/036 archive SHA及原manifest；保存相关IR/source与行号/哈希，提取8rank benchmark args/call链与缺失kernel_perf；严格CPU源级地址表达式解释和LLVM signed-extension证据，比较i32/i64参考及完整区间计数（不分配64亿元素、不exec生成模块、不import torch/triton）。校验现有index/i64/M16仍同SHA，只读CPU source capture；报告算法缺陷confirmed-static、事故因果strong-suspect/not-device-verified。任何后续修复、GPU最小复现、换黑名单或服务再启动均不在本轮执行。

该CPU脚本执行前SHA **3f88edc61d1f6caa5cbc27018cb7384ebf84732f56fb58c9308626cffdfaeca5**；原始stage文件逐项核SHA，随机标量选择固定seed37019、4096样例及边界×lane×4stores，总约16600个scalar检查（最终以实际report为准），只做Python整数算术。另保存PPU compiler源码与sanitize_overflow=true：randn LLVM未见printf/assert不代表最终PPU二进制绝无后续sanitizer诊断，不能声称全部推导的负偏移写已真实执行。该区别及无allocator现场会在结论中保留。

### 离线结果：明确的randn地址缺陷，事故因果强嫌疑

已一次完成，无GPU执行/推理/重启/8035访问/推理源码变更。`offline-randn-address-001/report.json` SHA **ce9ea21648f24a112b66f0ba70dba92ab31b43d7053d89cc9dc87b04cb3f662a**，manifest SHA **a355e519066ef3fd3532a958bd352ef0f15b36580c3a3388f652a4bfcf365912**；30份派生文件大小/SHA全部复核，原1692缓存路径逐项核验。CPU地址表达式检查**16600项**支持同一32位wrap机制，其中5616个采样地址的mask允许负偏移；不是算子正确性“通过”，也不是已执行修复的GPU回归。

源文件`/opt/qwen38-accdiag017-i64-20261016/gems/src/flag_gems/ops/randn.py` SHA **f0c89b53d3a8445146580575b96f294a73edda18a98e622c9ed3543e74eff7d8**，第97行`off_0 = tl.program_id(0) * BLOCK * 4 + tl.arange(0, BLOCK)`、后续off_1..3均未提前升i64。主证据是事故时保存的TTIR285–312、TTGIR288–319与LLVM1277/1282/1284等位置，全部保留i32乘法/左移与后置signed-extend；不是仅从当前源码推断旧进程行为。

| 地址边界 | 原保存实现 | i64数学参考（未在设备运行） |
|---|---|---|
| weight/N | BF16 `[40000192,160]` / 6400030720元素 | 同shape |
| BLOCK/UNROLL/grid | 512/4/3125015 | 同配置 |
| block1048576、lane0、store0 | i32 offset=-2147483648，`offset<N`为true | offset=2147483648，在合法区间 |
| BF16字节地址相对base | -4294967296 bytes（base之前4GiB） | +4294967296 bytes |
| RNG i4最大值 | 1600007679，仍在i32正范围 | 问题不是此shape下Philox counter wrap，而是输出地址乘4 |

该完整grid在IR语义下可划分成2147483648个正常前段地址、2147483648个负地址、2105063424个wrap后的重复正地址；这是区间数学证明，不声称硬件最终真的执行了全部错误写（PPU后端可能报错/拦截）。仅把N或最终GEP转64位不足以修复，必须在program-id乘法之前提升输出offset计算。RNG流/布局需保持不变并单独验证。

调用链证据：8rank的Inductor融合benchmark `get_args()`都请求该大BF16weight；`torch/_dynamo/testing.py:462`浮点rand_strided调用torch.randn，Gems registry1535单独注册`randn`（1536为randn_like），所以normal_黑名单不覆盖它。N:i64/BF16的Gems randn缓存落于14:55:07，embedding相关编译产物至14:55:08，14:55:12起原生Segfault；8个embedding benchmark都无kernel_perf完成回执。尚无精确kernel launch序列/输入指针取证，不把cache命中直接冒充逐次执行证明。

更强的交叉证据：036带模型probe失败时保存的同一randn TTIR与037**逐字节一致**，SHA **4c37047adba41b7d10a4b4b86b365c2e0538ae882f10fae346aa9f2a13f29229**。037早期外部ptrace干扰仍使整次启动A/B不干净，但这个编译期地址缺陷在两份冻结IR中独立存在，不依赖取证tensor复制或新hook。既有FP32 helper、index/index_put i64和QSA M16四项SHA再次核相同；这是另一个算子的遗漏，不是旧GDN索引修复丢失。

置信度分开记录：**randn大N地址缺陷=confirmed-static；它触发本次worker/foutput崩溃=strong-suspect，尚未设备闭环。**randn LLVM中无printf/assert调用；PPU metadata的sanitize_overflow=true只证明选项，不足以还原最终二进制的报错/保护行为。没有allocator/printf缓冲区地址，不能确认哪块设备内存被覆盖；formatted-output解析崩溃可能为后续症状，也可能还有独立运行时问题。OOM/具体PR本体/QSA错误仍不直接成立。

下一首选证伪（未实施）：只修randn输出地址为乘加前i64，先受控验证大N边界/未命中部分/小shape/RNG及GPU保护，再仅一次8010 startup验证，同版本同CLI且不加载模型probe、只使用被动kernel退出记录。可用单独randn fallback作为交叉对照，但不得同时改算子与黑名单后宣称单变量。修改/设备测试/服务重载须等用户方向；本轮未改代码或启动任何GPU测试。无formal gate/性能结论，旧164/198失败保留。算子知识增量仅该静态缺陷与证伪计划，尚未完成设备验证，不建立通用平台结论。
