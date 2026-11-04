# accdiag-036：更新Plugin/FlagGems-vllm后的19请求同前缀回归

状态planned；用户2026-10-19授权仅8010一次重载加载env035，固定19请求/C<=8、完整证据，保留FP32/i64/QSA M16，不访问8035、不全量GPQA。采用inference-accuracy-evaluation `minimal-regression`及inference-accuracy-diagnosis；旧acc015164/198 failed-score/no gate及性能阻塞不变，无正式/性能结论。

## 方向、假设与边界

验证env035组合升级后的C1重复与实际Mixed C8同前缀分布是否保持一致；对照034的doc71两point、doc81的778/808两point，旧034两处显式及MoE内部FP32后最终raw/prob逐位同值。升级涉及Plugin maina696859b+PR455head3cb373b1和FGVLLMb4d3382，是整组升级验证，不将差异归因某一PR/kernel。新的模型package/HC/PLE路径不盲拷旧monolith；保留env035的FP32helper实例绑定及private017 Gems i64、上游PPU QSA M16。

## 执行设计与正确性门禁

- 当前8010基线只读确认API1767049/start509637043/argv5744d999、health200；准备前再核idle/counter9356/3328及034 driver退出、源manifest和镜像/挂载/私有目录/空间/权重配置tokenizer。
- 模型和算子字节不再改：直接使用`/opt/qwen38-plugin-pr455-20261019`与`/opt/qwen38-fgvllm-main-20261019-b4d3382`；新独立`/opt/qwen38-accdiag036-env035-20261019`只保存sitecustomize/probe和cache。只通过run-scoped import hook在新进程runner加载后加观察wrapper；不改vLLM磁盘文件，不改环境安装绑定/旧源码，不热更既有进程。诊断hook不用于PR，pr_readiness=experimental。
- 仅窄采样/输入取证：12评分×all8rank实际device input IDs/positions/query/logits row/request-slot-mixed映射、完整raw logits/实际过滤prob/noise/RNG/token；背景只轻量binding/rank0采样前缀。不是旧34层/全KV/大索引状态重抓，完整证据指本轮冻结边界及全部实际HTTP/token/日志，不伪称完整全池因果。捕获同步会改变时序，不做性能推断。
- 运行时核8rank实际Plugin/FGVLLM/Gems导入与SHA、48模型MoE实例FP32绑定、真实FP32collective输入输出dtype、QSA真实vendor函数M16调用；graph两类7/7 capture及至少两次实际CUDAGraph.replay完成事件。input/prob谓词与bootstrap/controller AST先CPU验证。
- 请求照034固定原件SHA115e640c204845dd6043b255b8b91b5822377d5a2976c09b9be6a46d1c0aeb5e，仅opaque header换036；8C1评分(max1)、7背景(max512)、4Mixed评分(max1)共19，原temperature1/top_p.95/top_k20/min_p0/presence0/repetition1/seed1234/stop、token-ID prompt和completions接口不变；不追加smoke/预热/隐藏请求。继续使用已冻结027 client的request/run/launch三个方法及22的纯记录辅助，SHA/AST选取，不裸执行旧8035门禁；所有活跃guard仅8010，8035明确不访问。
- 仅对精确旧8010 API单SIGTERM，自然树退出/端口清空再唯一launch；不升级kill、不重启容器、不自动恢复。新worker启动/编译/graph失败即终止新增请求并保留现场；旧服务未退出也停止，不第二次重载。首真实异常或输入/采样取证失败停止补位、在途自然排空；首有限分布差异保存且如实报告，不为消差改采样或重发。

## 命令（执行前冻结）

远端`CASE/commands/accdiag036-control.py` SHA886e49380c41a36ff338d83ace134370d8f3d54a86c7cbd53b041b78db816056；probe SHA7d86a237078a3299582c7bee63666ae1cd762a41691901ba2926fdfe46ceb77e；sitecustomize SHAf82606e23e667327f958883270c80dedfbf8f695ed7c97d00bf170780cf29fd0；CPU脚本SHA77de500d52b232ea9bb750b46c752e00c7691fecb4dd8e84f7f89b9bb4dc4192。只用SSH stdin排他上传并核SHA，先`docker exec -e CUDA_VISIBLE_DEVICES= -e OMP_NUM_THREADS=1 -e MKL_NUM_THREADS=1 ... python3 CPU probe control site`，stdout排他保存commands/accdiag036-cpu-result.json；通过才Host control `--mode prepare`，复核launch/receipt后只各一次`--mode restart`、`--mode launch`。foreground跟进，旧heartbeat仍PAUSED，不新建监控。

## 外部证据与结论

CASE=/mnt/nfs/users/jinghao/qwen3.8-flash/20261015-qwen38-flash-next-ppu07-container/accuracy/acc-015-full-gpqa-ppu07-c64-current-i64-qsa-20261018；R=CASE/diagnostics/accdiag-036-env035-same-prefix-20261019/runtime-001。原始请求/HTTP bytes/tokens/全8rank PT/manifest和日志/服务与driver报错/源码配置/first marker在R集中保存。终态原driver退出后补日志尾并CPU审计实际C1/Mixed、分布及034匹配点；若有差异保留最早一对完整PT及token，不覆盖034或env035证据。

性能not_run；新正式gate=null。局部通过仅支持本19/C8短前缀，无60K/提前EOS/C64/全198修复结论。恢复旧034源码/原launch是回退入口，但须另获8010重载方向，不自动执行。跨平台/其他shape/长轨迹未测，保留原正式阻塞。

CPU18谓词与3脚本AST已通过，CUDA_initialized=false/0请求；bundle6e94a080。本地bundle inspect首次漏selection仅工具返回incomplete，明确minimal-regression后核验成功，非模型事故。PREPARED SHA0b9d7e014f12838fbe75013203c79b1524779f40ba775fda413f8a4dc35fd136；新PYTHONPATH仅036bootstrap、env035 Plugin、private017 Gems、新FGVLLM，旧DIAG021/旧Plugin路径已移除。CLI原字节保持（argvSHA5744d999），原采样不变、prefix cache关闭、卡8–15，独立vLLM/Triton cache，不伪装已运行模型验证。接下来只执行一次restart与launch，无8035访问。

唯一reload已执行且旧树自然退出，只单SIGTERM精确原API、未操作容器/其他服务；唯一driver949684已由launch启动，当前等待加载/编译/graph。后续绝不再执行restart/launch/run。新upstream提示旧VLLM_FL_QWEN38_FGVLLM_OPS knob未知，不能宣称新栈仍是旧QSA-only；新PR统一使用新模型调用链，HC/PLE及执行组织差异属于此次组合升级，不按某一算子归因。

终态CPU后处理执行前冻结：`CASE/commands/accdiag036-audit.py` SHA `7f42a814599faa59c83864b83014bf0ac66d9a4ae007745fad2554dd4d5aa2ce`；原driver退出且FINISHED/FINAL_EVIDENCE齐全后，在模型容器CUDA空/OMP-MKL1执行仅一次，读取旧CPU PT/原始HTTP与SHA，核12评分×all8输入/完整分布/噪声/RNG/token/实际Mixed、完整API-prefix及64组同prefix比较，保存最早完整差异pair并与034作为组合上下文比较。无推理/重载；CPU报告缺失或失败如实记，不用旧034结论替代本轮。端到端logits比较与FP32路径/graph覆盖分别判定；编译内联导致Python计数不可见时不能据源码装饰宣称实际hit，缺证保留。

## 启动失败：19请求未派发

14:00:21+08引擎报告`Worker proc VllmWorker-3 died unexpectedly`，发生在`determine_available_memory`的profile/compile阶段，最后明确rank0进度为13:58:28 Dynamo transform；随后RPC `RuntimeError: cancelled`及Engine core initialization failed是下游取消/启动失败，不是已定位的首因。没有该worker的首Python traceback，也没有当前可读driver ring中的新illegal/segfault/OOM证据；FlagTune平台包unknown configs只有AUTO fallback，不据此认定终止根因。容器running=true/OOMKilled=false、cgroup oom/oom_kill=0，仅排除这份cgroup计数中的OOM杀，不证明其他根因。

唯一driver949684已自然退出，FINISHED/FINAL_EVIDENCE齐全、无RUN_STARTED/无任何req文件，真实分发/完成**0/19**；8010无监听，旧034也已按本轮授权停止，不能说仍在服务。8rank各有implementation-loaded原件，证明新Plugin/FGVLLM/private017 i64/M16真实来源与MoE FP32实例绑定；不证明实际FP32 collective、QSA请求kernel、graph replay或精度通过。没有模型回复/token/logits PT，不能伪造或用034旧数据补齐。未二次重启、回退、访问8035或正式GPQA。

CPU终态审计已执行一次，report SHA `df01173ee258f9a33ff3935e746bcc1999b1a8cb47a3268239bc7a90fe3bacf3`，status=incomplete/HTTP2000/comparison0/CUDA_initialized=false。为补齐控制器freeze后服务追加的错误尾部，下一命令`CASE/commands/accdiag036-final.py` SHA `1b5ff32d129150eb9a8334055920d532909dfdb28eead2873c1ba38423f222b8`只复制最终日志、核source/8rank与0派发、归档现有private036编译cache（已观察约74MB，设2GiB安全上限、tar内容逐项SHA核验），保存新post-controller-audit-001，不改服务或代码、不新发推理。root_cause=not-isolated；minimal-regression=incomplete-startup-failure，不能判模型精度回退或通过。

最终Host审计已完成：`R/post-controller-audit-001/report.json` SHA **90c47847f4d9ea53346b3b5fd71561d16f3db6c402dfdd63492c00dce00ef513**，manifest **2dd63f714c6273b74e3e63ff4dfc6e78e750915cd53f488d86985b8a2e3f9e6c**。8rank各48个实际MoE FP32实例绑定、i64/M16来源SHA一致；两包全部source文件未变。全部8rank事件、完整service/client错误尾、原driver-readable日志、源码/启动/请求清单保全；2967个现有编译cache文件压缩为10,578,700 bytes的`private036-cache.tar.gz`并逐项解包哈希核对。没有权重/数据集复制或旧证据覆盖。root未隔离，worker无首个native/Python终止trace，不能将取消栈当算子根因；新probe可能影响编译路径也未排除。

终态决定：incomplete，保留env035安装及本轮原始现场，不自动二次重启/回退/修改源码/追加推理。8010无监听、模型容器仍运行、driver已退出；19条未执行，因而没有模型回复/token/logits/prob可以报告，无新gate/性能结论。需要先定位启动退出并另确认8010恢复方案才能继续同范围验证；未访问8035，旧heartbeat继续PAUSED。

## 2026-10-19用户授权的纯离线worker3定位

用户要求只基于已保存日志/编译产物区分新版本兼容性与埋点，不再次重启8010、不访问8035/GPQA。仍归同一036故障记录，按inference-accuracy-diagnosis分类startup execution-mode。仅现有archive/日志及冻结SHA匹配源码文本读取，允许CPU AST/标量地址算术与新增派生报告；不import/执行生成benchmark、不调用get_args、不做GPU测试或模型请求、不修改任何推理源码/配置/采样/埋点，不新建监控。

初步只读发现：305份Triton source/TTIR/TTGIR/LLIR/hgbin/metadata各阶段均有产物，不像明确缺失某个lowering阶段；8rank各只记录implementation-loaded/STEP0，未进入score输入/采样PT保存。最后8份Inductor独立benchmark源码对应PLE大词表TP embedding，shape indices8192×16/weight40000192×160 BF16/output8192×16×160；已生成设备二进制，但无对应.kernel_perf。约11.92GiB合成weight分配和后续benchmark执行只是值得检查的窗口，不宣称已证GPU OOM或该kernel非法访问。

对照旧034源码仍为9ce7d6ca，其成功cache也有相同大词表masked embedding最终kernel，不能简单称“大embedding是新版本新增”。新版本改变PLE计算及融合边界，同时036撤掉旧逐层custom-op诊断tap、换窄Pythonwrapper；两项对编译分段/融合选择的交互仍可能存在。源码核实新utils仍读取BLACKLIST_APPEND，所以unknown env warning不等于normal_黑名单丢失；不把FlagTune AUTO fallback/后续cancelled当根因。

执行前保存`CASE/commands/accdiag036-worker3-offline.py`，输出R/worker3-offline-001。脚本仅stdlib/AST/tar/hash和容器内stdlib读源码，核原archive SHA/2967files、305stage组、177生成Python/benchmark完成状态与8rank STEP记录，保存新旧embedding源与编译接口文本；严格白名单标量AST解释器比较8rank saved-source地址/掩码边界（不是exec生成代码、不是设备数值验证）。最终报告将分开“已排除的主动采样复制”与“尚未排除的wrapper/Dynamo或包升级/融合影响”，保留无worker exitcode/native trace的缺口，当前不实施下一轮A/B。

该离线命令执行前SHA `6120d96490322afb86ce0e33ec88956ad236b09cd750cf22a9d26acb0291bd2d`；Host python3运行一次，新增目录排他创建；原始文件不覆盖。不调用任何旧controller方法或服务端点。

首离线脚本在校验archive时因只枚举regular文件、漏掉`.cubin -> .hgbin`符号链接而KeyError，尚未执行后续源码读取/标量比较；001空目录保留。这是离线分析器的归档枚举问题，不是worker3或模型异常。修订版将归档内链接按tarfile读取目标字节核原SHA，排他保存`commands/accdiag036-worker3-offline-v2.py`，输出`worker3-offline-002`；其余只读/无GPU边界不变，执行前核SHA。

### 离线结果与归因边界

v2脚本SHA **0b92f7bd2402c116771e1731b563241c909dcc90fe5b2ad8bd32e6e1f439b104**；已完成一次。派生目录`R/worker3-offline-002`，report SHA **888505a94926df1408df5c7389bc5b9dcffd825b3c73c0ce7424b07284dde663**，manifest SHA **443b378dae4f035b486eff077737240e7a0574f4f12e1aab6ce9abe0ea07cb5f**；32份派生证据逐文件大小/SHA复核通过。原2967缓存路径（含305个cubin链接）全部核对原冻结SHA，无原件改写。

| 证据 | 支持的判断 | 不支持的判断 |
|---|---|---|
| all8各一个implementation-loaded/STEP0，48个MoE实例绑定；无HTTP/PT | 基础导入与权重加载已走过，输入/采样的大张量复制和保存尚未进入 | 不排除后续编译、wrapper、运行时接口兼容性问题 |
| 305组已保存source/TTIR/TTGIR/LLIR/hgbin/metadata完整；177生成Python AST无语法错误 | 这些已保存kernel的lowering未见缺段 | 不能排除未落盘编译任务失败或二进制执行失败 |
| 14:00:15最后8个rank的独立embedding benchmark源码、14:00:16相关二进制，0份对应kernel_perf | 最可疑窗口收敛到PLE masked gather的Inductor融合收益评估/内部benchmark；距14:00:21 worker3死亡仅数秒 | 无完成回执不能区分分配、首次launch、计时循环或未保存完成记录，更不能直接判GPU OOM/非法访问 |
| 旧034存在同尺寸embedding最终kernel；8rank×61 token边界/样例的源级标量地址及mask比较488项一致 | 新旧该段global/local vocab映射未找到标量索引回归，weight stride160与源级i64一致 | 不是GPU数值验证，不验证全部lane/实际设备输入、PLE ngram逻辑或融合前后模型语义 |
| 新窄wrapper与旧tap屏障不同 | 主动采样取证不符合事故时间线，但编译影响仍未排除 | 不能把“没有取证PT”当作“埋点对编译绝对无影响” |

`torch/_inductor/codegen/triton.py`的保存版本证明，融合/组合收益评估会生成独立`get_args` benchmark，并在调用结束后才写`.kernel_perf`。该合成weight为`40000192×160 BF16`，单份 **12,800,061,440 bytes（约11.92GiB）**；连indices/output约12,843,053,056 bytes，尚不计clone/workspace/已加载模型。`rand_strided`对浮点输入会走`torch.randn`，这属于编译期内部评估而非19条HTTP请求。这里只静态读/AST解释，未调用get_args或执行任何GPU benchmark；目前没有worker3的native退出信号/exitcode/首个trace，不能把潜在显存压力提升为已证OOM。

新版本改变PLE组织和融合边界；旧034逐层custom-op tap曾形成分段边界，新036移除它们并包装collective Python函数。后者即使forward原函数、STEP0不复制tensor，也可能改变Dynamo的函数身份/guards/融合选择。因此当前最精确结论是 **新版本计算/编译路径与诊断边界变化的交互仍未隔离**，不能单独归罪PR455、FGVLLM或采样埋点。新utils仍支持BLACKLIST_APPEND；unknown-env警告、FlagTune AUTO fallback和后续`cancelled`均没有足够首因证据。已保存驱动/cgroup信息也没有给出本次明确OOM/illegal访存证据，不等于排除它们。

建议的下一证伪实验（**未执行，需另获8010重载授权**）：固定当前包字节、FP32/i64/M16、CLI及等价冷cache，仅切换观察wrapper开/关，保留worker原始exitcode/signal/native stderr与编译期benchmark阶段，先验证startup而不发送模型请求。若无observer仍失败，再单变量缩窄内部融合benchmark/PLE路径；若仅有observer失败，再拆分collective wrapper与loader/QSA wrapper。不得一轮同时换回旧Plugin和撤埋点后就宣称归因完成。

本轮终态：offline-localized-window/root-not-isolated；新增重启0、GPU执行0、模型请求0、8035访问0、推理源码修改0。未再次检查服务端点，沿用已冻结的8010启动失败事实；无新精度gate或性能结论，旧heartbeat仍PAUSED。已完成本次只读定位，等待用户决定是否进入另行授权的单变量startup复现。
