# 20261021-sparse-mla-small-head-dual-backend-51 公共Sparse MLA小head与双backend

- 状态：04 SQL反射修复及测试已验证并保留；临时H4候选仍未保留，C8复现RPC超时、16worker请求内大量MM调参待进一步单变量验证。临时六文件/index已精确回退、8011停止；无新gate/性能。最新终态见下文，早期执行记录保留。
- 分类：operator/improve（FGV小H4存储通路），关联operator/replace（现有vendor dispatch）；当前是点50 OOM修复接续，不开启新的性能优化。

## 优化方向与瓶颈依据

点50真实C64 Prefill SQ20172的H4被物化成H64，Query/输出各1.23 GiB，输出分配OOM；最大token dummy profile未执行该attention。旧PPU native算子直接处理H4。用户授权保持PR454公共模型并让vendor/flagos成为清晰独立的实现。上轮正式0/198且全timeout、无gate，失败证据保留，不复用历史分数。

## 优化内容与适用边界

编码前按实际FGV仓库AGENTS/workflow冻结以下契约；其引用的`optimization.md`/`deep_opt.md`不存在，记录缺失、不伪称读取。workflow末尾conv1d旧任务输入不属于用户本轮Sparse MLA任务。以下是正确性/显存修复，非G6性能交付。

| 项目真相 | 冻结内容 |
| --- | --- |
| API/范围 | 既有`flaggems_vllm.flash_mla_sparse_fwd`，非单一ATen；当前源码/同库CPU FP32参考为契约，PPU TP16 BF16公共GLM路径 |
| Editable/read-only | FGV现有Sparse MLA实现/追加测试；Plugin既有mla adapter和thead backend/register_ops及追加测试。原参考/既有测试/benchmark/导出/vLLM/FG/权重/launcher不变 |
| Build/validation | Python源码无构建安装；py_compile、原CPU/新单测、两个provider独立FP32 oracle及graph；预检/单GPU验证各900s，模型readiness3600s，失败保留不盲重试 |
| Benchmark/active | 本轮先显存正确性：H4、SQ1/8/17及大SQ20172；原H64/128守护。现有benchmark入口保留未改，设备速度/端到端验收not_run，不据局部分配变化声称加速 |
| Autotune | 沿用已有`@triton.autotune`：H4只选择BH16/BK64/4warps/2stages，H64/128保持原2项BH64配置及原key。明确豁免：本次不将既有硬编码triton autotuner迁到NVIDIA YAML/libtuner，以免扩大原大head路径；非PPU/NVIDIA硬件未验 |
| Profiler/fallback | 使用真实调用/分配和graph覆盖证据，无profiler timing；FGV生产无Torch compute fallback，选中实现报错原样传播，不执行第二kernel |

| 数值与Torch参考 | 契约 |
| --- | --- |
| Input/dtype/layout | 连续BF16 Q[SQ,H,DQK]、KV[SKV,1,DQK]；int32 indices[SQ,1,K]与可选lengths[SQ]，FP32 sink[H]；H4/64/128、DQK512/576、DV512。其他dtype/layout保持原拒绝 |
| Output/alias/acc | BF16 output[SQ,H,512]新存储，max_logits/lse FP32[SQ,H]；FP32 dot/softmax累加，PV的BF16 cast位置保持原实现，无新alias/out承诺 |
| 边界/异常 | SQ0、K非对齐、无效indices/length0、sink±inf按原契约；全无有效key output0/max=-inf/lse=+inf。任意NaN、训练/反向/complex/integer结果不扩展支持，保留原路径 |
| 参考/容差 | 同库独立Torch FP32 attention只在测试；rtol0.03/atol0.003；native辅助LSE可能计数底不同，公共模型只消费output、不进行跨provider辅助值混用 |

| 实现路径 | 条件与机制 | 验证边界 |
| --- | --- | --- |
| empty | SQ0分配既有空输出、无launch | shape/dtype |
| small | H4、masked真实storage、BH16 ordinary kernel | 独立oracle/invalid/sink/graph/显存 |
| general | H64/128原autotune/TLE能力guard | 原路径/配置守护，不加新平台特判 |
| unsupported | 其他库内head/dtype/layout沿用断言；Plugin按provider能力保留旧补齐兼容 | 非目标路由回归 |
| external | thead既有native库懒加载，单独vendor注册，common adapter只消费其attention output | 缺依赖可导入/strict失败传播/真实命中/graph |

FGV：复用现有ordinary Triton数值链，为H4增加head维masked load/store与小tile，不物化HBM H64；H64/H128既有候选、数值和TLE guard不变。优先不新增kernel副本或全局策略。Tile内部必要padding不等于生成H64存储。

Plugin：公共模型/config/processor、metadata/索引语义继续复用。选算子通过现有OperatorBinding/OpManager及vendor backend边界，不把native伪装成flagos，不恢复旧PPU模型/后端类树；vendor依赖懒加载和能力检查留在已有平台backend。已选实现执行错误按原strict/fallback语义传播。不在通用模型增加thead判断。非H4输入保留原支持/补齐行为。

原MBT32768/maxseq64/TP16/BF16/maxlen80000/FULL_DECODE_ONLY/prefix disabled、权重/tokenizer/vLLM/FlagGems/启动脚本不变。先分别证明两个provider实际命中、数值和graph；默认选择不得未经验证切换。profile预算缺口本轮不夹带广泛重写，若消除HBM padding仍OOM，冻结首错后再限域定位，不能盲降MBT。

## 正确性与路径命中

预冻结minimal-regression：CPU导入/注册/缺vendor依赖、strict/fallback与非目标默认；独立FP32 CPU softmax oracle，H4/BF16/DQK512和576/DV512，SQ1/8/17、topk非对齐/无效indices/有效长度、sink、zero-token及H64/H128原路径；rtol0.03/atol0.003沿用点50预冻结Sparse MLA契约。两个provider各capture/至少两次改变Q/KV/indices/valid_length的replay、输出填毒/边界保护。大SQ20172只做显存/有效行守护，不用巨型CPU参考张量。

硬件算子回归通过后，实际安装目录运行Plugin相关CPU集，原FULL模型C1/C8、精确P16383/16384/16385、11明确答案、C64短生成及graph capture/多token回放、16Worker无TileLang。最小回归不代替正式GPQA；高风险路径及既有正式失败要求新198题/C64/seed42/60K/strict>=.86正式gate，独立新缓存、无补充/best-of。尚未派发任何评测。

## 性能效果

not_run。只可报告算子分配显存，不把本轮正确性探针或历史vendor收益宣称为端到端提升；正式四场景及全峰值归因未完成。

## 执行记录

2026-10-21 17:58:06唯一派发`commands/validate-v1.py`，PID1358345/start529249638。安装前后全文件与index语义核验通过，仅替换6个既有文件（Plugin 3 runtime/1 test；FGV 1 runtime/1 test），不改stage。CPU原生421 passed/17 gpu deselected、78.76s，原生`CPU.xml`/`CPU.log`；FGV独立CPU参考/小head动态graph及大head守护检查中。未发模型请求，未改变交付脚本和参数。

18:00:25原生`operator.xml`确认11 passed/417 deselected、19.43s。18:02:53唯一派发`commands/dual-control-v1.py`（9a06daab…，PID1459109/start529278340），其probe bd95fadb…；`dual-provider-v1.json`证明两个实际impl（glm5.flaggems/vendor.thead）、公共metadata/物理索引/真实FGV cache writer、B1/B8独立CPU FP32 output oracle及每组2次动态Q/KV/索引/block table/slot改变后的填毒graph replay通过，无TileLang。SQ20172/TOPK128两provider输出存储均82624512 B＝78.796875 MiB，相对旧H64输出1260.75 MiB为1/16；adapter探针峰值增量分别579633152/580894720 B，包含索引转换等工作区，不把它等同整模峰值。该 synthetic case不等同真实GPQA topk2048/C64验收，尚不能宣布原OOM已闭环。

已保存下一整模`commands/model-control-v1.py`，SHA428f8809…；只按vendor显式per-op环境→flagos原默认环境顺序，各做原C1/C8/三16K边界/11答案及额外P4096/D16/C64/N64短正确性守护、FULL capture/多token回放、16worker无TileLang。readiness每角色3600s，MBT及交付脚本不改。仅切换算子policy、不加旧PPU路径。失败只停匹配本轮日志/实例的目标服务并恢复本轮6文件和index语义；原点50基线已知C64失败，恢复后保持OFF不伪称健康。此控制器不启动正式GPQA或性能测试。

18:08:07该控制器已唯一派发，PID1566145/start529309665，`model01/dispatched.json`留存。前置零请求核验全树/index一致、目标无服务接管，vendor开始加载权重。既有heartbeat `glm-performance-20261018`已更新为本轮只读跟进（30min，未变安静、终态审计后暂停），禁止重复启动或自行派发正式评测。当前`pr_readiness=provisional`：整模/新正式精度、非PPU硬件及最终style review未完成。只读固定ruff0.14.0检查发现新增测试2处import排序及两个测试文件需格式化；运行回归期间不热改源码，留作下一次受控test-only清理，不冒称PR已就绪。

整模阶段更新：vendor实际16worker日志命中`vendor.thead`，FULL decode 11/11 capture完成；18:11:28 `minimal.json`通过C1/C8及三档原16K边界，`semantic.json`11答案通过。随后C64/P4096/D16/N64首批长耗时，尚无c64/final-audit回执，flagos整模尚未开始。18:12:38起有60s shared-memory-broadcast等待警告；18:15:12只读PPU-SMI每卡92315–92316 MiB、瞬时util0%，16worker主线程R态。没有原生首错/CPU栈，不能据此归因为OOM、kernel hang、调参或DB。本轮继续既定900s客户端限时、不补发或降MBT，异常保留后停止晋级；最小整模整体仍incomplete、新正式GPQA未启动。pytest/style的整理仅在本地准备，安装目录未再次变动，原始SHA不改写。

## 终态与下一步（2026-10-21 18:21:59）

本轮minimal-regression **failed**：18:16:38 EngineCore报`TimeoutError: RPC call to sample_tokens timed out.`，API随后HTTP500；不是900s客户端先超时。日志未见OOM或非法访问，也没有worker内部异常/CPU栈，不能确定是native、FGV、调参、DB或通信。失败dump的实际`total_num_scheduled_tokens=4096`、`num_running_reqs=2`；虽然客户端配置C64，但尚未达到稳定64驻留，不能把失败归因为“64并发”或假设失败shape是32768。

控制器终止晋级，未运行flagos整模、新GPQA或性能。`model01/rollback-completion.json`确认仅本点6文件精确恢复到pre51公共repair08源码，原stage/index语义不动，服务OFF。该基线仍带点50已知C64精度运行阻塞，**不是恢复到可用版本，更没有恢复旧PPU模型路径**。新候选只保留在`commands/candidate-v1.tgz`（SHA4de1884b…）及原生测试证据，不声称当前安装已启用H4通路。

`commands/terminal-audit-v1.py`（SHA28ea7c36…）零模型请求执行；`terminal-audit-v1.json`确认两库完整文件/链接/HEAD/index语义、三库及vLLM内容身份、唯一Plugin/FGV各1份editable安装、权重/tokenizer/thead/交付脚本、镜像谱系/挂载一致，目标API不存在、health拒绝连接。DB合法调参写入记录实际SHA，不删除或恢复DB。既有monitor已PAUSED，未新建重复监控。无提交推送，所有失败证据保留。

按`inference-accuracy-diagnosis`冻结gate-blocking问题`point51-model01-vendor-P4096-first-step-RPC`。下一首个证伪实验应复现原P4096早期step并在RPC超时前采集真实worker CPU栈和调用边界，保持原MBT/graph/采样；先确认耗时落在何处，再按单变量比较provider或修复，不盲重跑整轮C64、不延长超时掩盖、不添加新性能优化。算子/子图通过只证明H4计算及紧凑存储可行，完整整模修复与新198题gate仍未完成。

## RPC诊断接续01（用户要求定位原因）

本轮仅`inference-accuracy-diagnosis`，不实现新修复或性能优化。重新只读核验PPU-13连接/三库HEAD及原回退终态；16卡均1 MiB且无运行设备进程，未发现用户接管。候选6文件按原archive原样临时重现，原vendor policy/TP16/BF16/MBT32768/maxseq64/FULL/关闭前缀缓存保持。先只发与失败相同token IDs、seed42/temperature0/ignore_eos/D16的P4096 C1/N1，不额外预热该shape，检查单请求是否足以复现；不能把成功直接解释成C64因果，因为共享调参DB已经历上一轮合法写入，需记录实际DB SHA。

诊断机制：现有sitecustomize经新解释器只读探测为None；在远端`rpc-diagnosis-01`外部目录提供仅标准库的sitecustomize，临时PYTHONPATH仅用于faulthandler原生watchdog每20s输出CPU栈（不使用外部SIGUSR2，避免未知SDK信号覆盖），保留原WorkerFL/模型/设备调用，无数值hook或额外GPU同步，不落永久Plugin文件。通过当前worker PID/start_ticks及hook登记证明16-rank覆盖，按请求相对时间写阶段marker，watchdog独立采样；它不是设备profiler或无profiler性能证据，Decode/Mixed覆盖不作要求。请求900s限时，RPC约300s前取证；结束只停匹配本轮日志/实例的服务，精确回退6文件/index到pre51公共基线并保持OFF。不运行全量GPQA或C64重试、不删除/重建调参DB、不提交推送，沿用本点同一文档和结构化条目。

01未发任何模型请求：18:36:35 Worker5意外退出，随后EngineCore在`determine_available_memory`取消；无原P4096复现。18:36:50 `rpc-diagnosis-01/final-audit.json`确认原完整源码/index/身份恢复、服务OFF。16份worker栈中11份完整落在FGV `utils/models/sql.py:86 build_sql_model_by_db → AutoBase.prepare(engine)`，其余5份SQLAlchemy采样截断/不完整，不能称16份完整FGV调用链；调用方为多模态dummy profile中的`silu_and_mul_with_clamp`。cgroup oom/oom_kill均0、失败窗口内未发现内核segfault/OOM记录；额外启动退出原因仍未知，不归为原RPC根因。

只读CPU反事实：`commands/rpc-sql-probe-v1.py`（67c74595…）提取当前FGV方法AST，不导入FGV/Torch/GPU；源DB只读备份为`rpc-diagnosis-01/sql-readonly-snapshot.db`。实际方法反射1022表/映射1022类/10222 SQL、5.679680s；仅在该CPU进程中限定目标表的对照为1表/1类/12 SQL、0.022277s。目标schema/PK/首行配置相同，原DB前后SHA均97a4bee3…，真实SQL源8a7bac14…未改。证据`sql-probe-v1.json`确认FGV独立缓存仍存在全库反射，先前只修FlagGems另一份实现；**这还不足以解释原300s RPC**，不把CPU查表比值冒充端到端收益。

诊断接续02已保存并唯一派发`commands/rpc-diag-control-v2.py`（1234d347…、PID1640540），独立`rpc-diagnosis-02`保留01失败。仅将观察方式改为无线程faulthandler SIGUSR2（cfa84df6…），startup不创建watchdog；发送请求前要求16个当前PID/start_ticks登记和实际完整栈均可用，之后按请求相对时间采样。仍只原P4096 C1/N1、原MBT/FULL和相同候选，无修复/GPQA/性能，结束精确回退并保持OFF。该变化用于排除观察工具影响，不能未经对照认定watchdog导致01退出。

02于21:31完成原FULL capture/health，但初始化前注册的signal没有向目标文件输出frames，16文件仅阶段marker；安全guard在生成请求前停止，0模型请求，不是原RPC复现。21:32:03最终完整恢复审计通过，源码/index和OFF恢复。早期hook未生效机制尚未确定，不擅自归为SDK改写或FD关闭。

诊断03于21:39:39唯一派发`commands/rpc-diag-control-v3.py`（476816a9…、PID1862318/start530578869）与后置hook e1964a29…，独立`rpc-diagnosis-03`。临时标准库Python profile只等待原Worker的`compile_or_warm_up_model`返回，之后立即关闭profile、打开新栈FD并注册信号；不改Worker类/计算函数。请求前除16个PID/start/真实frames外，增加FD链接必须指向该worker栈文件的硬检查。继续相同P4096单请求，原numerical/MBT/FULL不变，结束精确回退OFF；01/02原失败保留。既有30min heartbeat已切至03，只读且未变安静，禁止重复派发/扩展流量/实现修复/跑性能，终态审计后暂停。

## RPC诊断03结果（2026-10-21 21:44）

请求前16个真实worker的PID/start_ticks、后置注册、栈FD链接和信号输出均通过，FULL capture/health已通过；仅发送一次原P4096/D16/C1/N1请求，HTTP200、4096输入/16输出、非空，耗时48.844897s。**原model01的RPC超时在此单请求下未复现**；该耗时包含冷路径与观测，不是稳态性能测量，不改变原整模failed或签发gate。

`rpc-diagnosis-03/stack-inventory.json`与`analysis-v1.json`逐份SHA核验16 worker原始栈：

| 请求相对采样 | 实际16-worker路径 | 含义 |
| --- | --- | --- |
| 1s | 全16个FGV `gather_state_rows → libentry → get_config → SQL AutoBase.prepare` | 查询配置却反射整个DB，首个数据移动算子触发 |
| 10s | 全16个FGV `gather_rows → libentry → get_config → SQL AutoBase.prepare` | 另一数据移动算子也触发，不能仅按单次查表估计整体开销 |
| 30s | 全16个FlagGems `_thead/ops/mm.py → libentry.default_policy → bench → do_bench` | 当前MM配置缓存未命中，执行在线候选benchmark；部分顶层在device synchronize |

实际`FlagGems/utils/libentry.py:1022–1025`只在benchmark配置缓存无条目时调用`_bench`；1245–1247遍历候选；MM1829从既有`mm_kernel_ppu`进入。该栈不是Sparse MLA native函数卡住的直接证据，也不应把benchmark中的device synchronize自动解释为死锁。采样点不能给出各阶段独占时间或排除未采到的设备/通信异常。

已确认两个冷路径成本：**FGV独立缓存全库反射遗漏**与**FlagGems PPU MM在线调参**。前者真实CPU反事实10222→12 SQL、schema/PK/首行配置等价，证明存在可消除的查表浪费；后者请求内真实命中候选benchmark，不是猜测。当前不能把两者直接写成原300s RPC的充分根因：本次只有C1，原失败dump为4096 token/2 running且客户端C64；多轮合法调参使DB从97a4bee3…变为09d30961…，未重置缓存，也没有同冷态单变量对照。原超时的因果定位仍未完全闭环。

分析命令`commands/rpc-analysis-v1.py` SHA3de7e36f15a3f2c792c214d5f71eabc732f50b3b3b1a2f58590fd5a62ef6f560，执行前已保存并校验；只读已有栈与JSON、零模型请求，产物`rpc-diagnosis-03/analysis-v1.json` SHA5864dd417584705a293f63ca75b561c47558fdf8a86f02b97c657ba3671cafd4。01/02失败、03原始请求/栈/回执均保留，不合并冒充一次成功回归。

21:44:29 `rpc-diagnosis-03/final-audit.json`确认完整pre51两库文件/链接/HEAD/index语义、FlagGems/vLLM及权重/tokenizer/thead/脚本、唯一editable安装各1、镜像/挂载一致；本点6文件精确回退，候选未保留，目标8011服务OFF。DB仅保留合法调参写入、不回退/删除。monitor已PAUSED，无新生产SQL/MM修复、完整GPQA、性能、提交或推送。

下一步建议（本诊断未执行）：先将FGV查表限定目标表并验证已有配置完全等价，再控制MM缓存/shape和预热状态，对原早期step做带栈同配置对照；若仍超时，再根据真实栈分开定位设备或通信。不能跳过因果对照直接盲跑完整C64或延长RPC超时。

## SQL修复及接续诊断04（用户已批准，执行前冻结）

用户“可以，请先修复然后在继续定位吧”授权修复FGV遗漏并继续原RPC定位。沿用点51同一实验，新增远端子目录`sql-repair-04`，不删除前轮。先仅改FGV既有`utils/models/sql.py`的`AutoBase.prepare`，使用目标表过滤的reflection_options，复用已经验证的FlagGems思路；新增device-independent测试。保留缺表/无主键返回None、外键必要关联、原名称/字段/主键/Config与benchmark值、缓存失效与异常行为，不增加平台分支、不改SQL存储/DB内容或kernel。

验证顺序：原方法/修复方法CPU结构反例、普通与多key配置/benchmark重载、缺表/无PK/外键/特殊表名及pool缓存；实际调参DB只读备份等价性。通过后保留SQL小补丁，仅临时重现原点51六文件H4候选+vendor policy，以原FULL/MBT单次服务先P4096 C1，再C8及原C64短守护逐步定位，全部保留，首次运行失败停止不盲重跑。请求期16worker CPU信号栈，加外部限域SQL反射/MM候选benchmark事件用于证明修复命中及剩余耗时；不将观测耗时当稳态性能。MM配置/调参策略本轮保持，不能同时改以掩盖因果。

结束停止本轮精确实例、恢复临时六文件；SQL等价验证失败则SQL也精确恢复，否则仅保留已验证SQL修复和测试，服务OFF。完整源码/index/唯一安装/权重/镜像挂载重新核验。新198题GPQA与性能本轮不自动启动，旧gate不能证明新身份。正式超时充分根因只有同路径原范围及边界验证后才能声称闭环；非PPU/其他SQL方言未测如实保留。

04 CPU阶段：`sql-repair-tools-v1.py`（473842cc…）全树/index保护、`sql-prepare-v1.py`（8eddf458…）核验原服务OFF、16卡空闲、镜像/挂载/唯一安装及原完整身份。FGV仅1个runtime/1个新增测试；SQL源8a7bac14…→6490ece2…，测试ae2e9cea…。原方法10项中7 pass/3结构反例失败（含外键测试排除noise的断言），首次工具误预期2个失败在安装前停止、证据保留；`sql-validate-v2.py`（836a5a85…）仅复用原生XML纠正编排断言，不重跑原基线，修复后实际安装目录原生10 pass。`SQL-installed-audit.json`确认源码/index/唯一安装/静态身份，服务仍OFF。

`sql-equivalence-v1.py`（b863864b…）使用当前真实DB只读备份，提取原归档与实际安装方法AST，比较全部1024表/63175行的列、类型、主键、nullable及所有行摘要，全部等价；原DB前后SHA09d30961…一致、零写入。表数从先前1022增至1024属上一轮合法调参状态，不混写成同一冷缓存。23.499s为整套CPU等价验证耗时，不是端到端收益或原超时修复证明。

下一模型命令`sql-diag-control-v1.py` SHA9233999dc575febb2fa6ff6396b5bb1ff2b79ecb1c2b0fb5febcdcd85675b7cd、外部hook be701305…，执行前已保存。临时hook在原warmup返回后挂SQL反射结果/表集合和PPU MM `_bench`入出事件（上限每worker2000事件），不改策略、不新增tensor同步或数值路径；保留16worker真实信号栈与FD硬检查。P4096/D16 C1→C8→C64各一次，任何原生失败停止，不盲重试；都成功才接续原C1/C8/三16K/11答案最小回归。最终只保留SQL小补丁，临时H4六文件回退并保持OFF。

04模型编排首轮`model01`于22:19:20派发，但保存的六文件补丁内含大测试，传入docker的单个argv超限（E2BIG），**在源码写入、服务启动及任何模型请求前失败**，原生failure保留，SQL修复未回退。`sql-repair-tools-v2.py`（ca155737…）仅将同一精确变更命令保存为带SHA的外部文件再执行，guard/代码/参数/采样均不变；`sql-diag-control-v2.py`（522fa738…）在核验前轮applied=false且无service.log及当前SQL-only完整源码后，于22:22:19唯一派发`model02`，PID2740492/start530834878。既有30min只读heartbeat已更新，严禁重复派发。模型层仍未验证，不把工具失败当模型RPC复现。

## 04最终结果与剩余问题（2026-10-21 22:32）

模型实际FULL capture 11/11、16worker后置观测/FD/真实栈/修复SQL SHA均通过。P4096/D16/C1一次2.757177s完成，随后同参数C8一次于22:30:29复现`RPC call to sample_tokens timed out`，8/8 HTTP500、诊断总时长300.758294s。不是900s客户端先超时；日志未观察OOM/非法访问。不继续C64或原semantic/16K完整最小回归，不派发GPQA/性能。

| 实际证据 | 结果与边界 |
| --- | --- |
| SQL修复实际命中 | 16/16 worker反射结果均只包含所查目标表。C1每rank3次，共0.015012–0.018410s；C8每rank5次，共0.028972–0.035208s。不存在已观测调用的全库扫描，修复有效但不足以解决RPC |
| C8 MM事件 | 每rank至少995次已完成候选benchmark，累计129.126740–129.867025s；每worker2000事件上限均触及，**只能作为下界**，不是全部300s耗时归因，更不能将16rank时间相加作为端到端 |
| MM实际shape | `M=20481`，首9组不同K/N形状各104次候选测试；例如K4096/N512、128、1536、2048、160以及K768/N4096。不是同一次native MLA调用一直不返回 |
| 信号栈 | C8第5/15/30/60/120/240秒全部16个worker落在`mm_kernel_ppu → default_policy → bench → do_bench`；第1秒为Triton编译。**180秒全部已推进到`index → nonzero → to/copy`，更正早期commentary把180秒也算作MM的描述** |
| 现有策略源码 | MM959–978：既有`libtuner`，key含FUSE_ADDMM/B_TRANSPOSED/aiu_load_mask/M/N/K，M/N/K有现成bucket策略，不能误称“raw M精确key”。warmup20ms/rep100ms，逐候选benchmark在请求内真实触发；本轮没有修改MM策略或数值kernel |

当前已确认：FGV全库反射这一独立浪费已修复；**剩余失败已复现并收敛到请求内大量PPU MM在线搜索/编译路径**。采样显示计算在推进，不能称一个kernel永久卡死，也没有证据把责任归到H4 Sparse MLA数学实现。至少约129s调参成本是直接事件证据；记录上限后其他调参/设备/索引等成本仍未精确分解，不能宣布MM是全部300s的唯一充分原因。要证明充分因果，仍需冻结初始缓存、只改MM调参策略的同路径A/B及恢复对照，不能靠重复请求把缓存暖到通过。

`commands/sql-diag-analysis-v1.py` SHAe038dc1b…只读分析原始事件/请求/栈并核验inventory逐文件SHA；产物`sql-repair-04/model02-analysis-v1.json` SHA3af146a9b730c7f0bcf2c56da24d4fe67514a8a873a9451103774a5dc14be7c1，完整原始结果/上限/失败保留。因CPU观测及已有缓存合法变化，C1的2.76s不得与上轮48.84s计算稳态收益。

22:30:35终态`sql-repair-04/final-audit.json` SHA4ef93e13…核验完整源码/index、vLLM/FG、权重/tokenizer/thead/脚本、唯一Plugin/FGV各1份、原镜像/挂载一致。临时H4六文件精确恢复，**仅保留FGV SQL 1 runtime/1 test**；Plugin源仍59ae4b57…、FGV新源aec7a80258523ea4d4c0e693cf6b357ef4f57acfa99b6619df10b76e3a81c402、FG仍1a6197b7…，服务OFF、monitor PAUSED。DB合法调参写入后SHA239ed14b…，不删除、回退或掩盖其变化。不是恢复到已通过C64的可用服务，旧精度不得绑定。本轮未提交推送。

保留决定：SQL查表等价修复可保留；整体minimal-regression仍failed，H4组合未晋级，正式精度gate缺失、性能仍blocked。当前SQLAlchemy2/SQLite及PPU命中有效；其他SQL方言/硬件未验，black/isort/flake8/ruff原环境均未安装，未热改源码/依赖，不宣称完整PR就绪。下一优先候选为复用既有策略/缓存限制请求内MM搜索预算，或隔离DB快照下预调优真实batch bucket；不能降低MBT、延长RPC或削弱cache key来掩盖问题。

## MM缓存/候选定位05（用户要求继续定位，先只读）

保持04已保留SQL修复、H4未安装、服务OFF，新增远端`mm-cache-diagnosis-05`取证子目录。先读取实际MM/gemm_utils/libentry/FlagTune调用链和前后DB只读副本：核对ConfigCache策略化key、BenchmarkCache raw key及协议版本、候选剪枝与104次测试来源、混合批次M20481及其他shape的未命中边界。CPU复用实际方法与真实记录metadata，不跑GPU/模型，不改搜索策略、参数、kernel或DB。若静态/CPU机制已足以明确下一最小对照，先报告其证据和边界，不用盲重跑整模替代分析。

## 05只读定位结果（2026-10-21 23:04）

本轮`inference-accuracy-diagnosis`配合`key-operator-analysis`，复用现有源文件的方法AST、真实前后缓存副本和04原生事件，不运行模型/GPU，也不修改安装库或生产DB。当前MM c46e0cc1…、gemm_utils a064d72b…、libentry e8f38aa0…与预检一致，源码快照`readonly-sources-v1.tgz` SHA40fe3a47…；完整证据在`mm-cache-diagnosis-05`。

### 已确认的触发链

1. **不是缓存反复失效。** 相同表命名空间下，ConfigCache 299→318，新增19个winner、删除0；BenchmarkCache 30631→32671，新增2040条、删除0。完成的19组都正常落库，未完成的一组只有64条候选记录、还没有winner。
2. **新Config bucket冷未命中。** 原库已有M20480的11组结果；实际M20481映射21504、M8198映射9216，均为原来未命中的bucket。只改M20480→20481、其余flags/N/K/4个BF16 dtype完全相同的CPU查表对照，11/11从命中变为未命中。这确认缓存冷缺失的边界，而非假设“DB坏了”。
3. **每个新projection搜索仍很宽。** 原生`_ppu_mm_configs`生成114个候选；实际`_prune_gemm_configs`只做合法性/资源过滤，记录的10种shape均剩104个，与前9个真实事件组各104次完全吻合。正常Default空间本身就很大，不能仅把104次归因成意外打开了Expanded。
4. **一次请求批次就触发多个冷组。** 行级差分得到20个新raw-key组：M20481完成11组，每组104条；M8198完成8组，每组104条，另M8198/K1536/N4096在64条时中断。合计`19×104+64=2040`。20ms warmup+100ms rep对应约244.8s名义测量预算，尚不包含编译等开销；这是协议预算推算，**不是实测独占时间或端到端收益**。04已有16rank栈/至少995次/rank事件和300s RPC，是同一机制的运行证据。
5. **多rank各自开始搜索。** 真实16worker均测了至少995项，数据库却只保留每个raw-key/config一行；当前锁仅是各进程的缓存/数据库读写保护，没有整段搜索的跨rankownership。不能把16个rank耗时相加成端到端时间，也不未经验证就引入跨rank广播/等待协议。

ConfigCache与BenchmarkCache不能混为一谈：前者对M/N/K使用bucket，后者保留raw值和协议。只要前者命中，就会跳过在线搜索；**不是每个新的raw M都会重调**。本例是新的Config bucket未命中，且raw BenchmarkCache对应标签也没有，才进入逐候选`_bench`。邻近M只差1token的事实不授权直接放宽key：不同尾块/mask/性能仍须验证，不能为了命中率破坏正确缓存边界。

### 独立发现：协议缓存标记风险

实际LibTuner构造器在20/100等显式warmup/rep下生成`do_bench`闭包，随后把它作为custom回调，缓存协议记为`('custom_do_bench', -1, -1)`；20/100与25/50实际闭包参数不同，但标记及命名空间hash e01184d8f339相同。CPU执行原构造器（仅父类分配/注册/cache对象使用test double），真实数据库也确为该tag。该问题是**独立的测量协议隔离风险**，不能用来替代本次新bucket未命中的直接证据；本轮没有修复它，后续应单独处理，避免与MM搜索预算改动混成一个变量。

### 证据与结论边界

命令执行前均已保存：`mm-prepare-v1.py` SHA60574154…；`mm-cache-probe-v3.py` SHA2518455b…；`mm-cache-delta-v1.py` SHA4fa50fc9…；`mm-neighbor-finalize-v1.py` SHA8eaa967a…。probe v1未执行，v2的CPU构造器fixture缺少schema常量而失败，`probe-v2-failure.json`保留；v3补齐依赖后通过，非模型重试。CPU张量为actual Torch meta，仅用于真实dtype key计算，无GPU分配/launch。

`cache-probe-v3.json` SHA86be662a…、`cache-delta-v1.json` SHAbe31b929…保留全部键/表/shape对照；before04快照088b82c8…、after04只读快照e8b74460…均未改变。23:04:10 `final-audit.json` SHA45cb7821…再次通过完整源码/index、唯一安装/权重/tokenizer/thead/脚本/镜像挂载，生产DB SHA239ed14b…仍未变，API不存在、服务OFF。SQL修复保留，H4未安装；现有heartbeat保持PAUSED，本轮前台CPU完成，无新GPQA/gate/性能或提交推送。

**诊断决定：新bucket冷未命中→大候选空间请求内搜索已确认，不是缓存反复丢失，更没有新证据证明Sparse MLA数学错误。** 原RPC全部耗时和修复充分性仍需同初始缓存的MM策略单变量模型A/B及原范围回归。下一首选应复用现有Default/Expanded边界，验证较小的生产Default候选空间或有界冷miss策略，完整搜索留离线/Expanded；保留keys和合法性检查。不优先改MBT、延长RPC、清库或不停补预热。

知识差量`refined`：将“MM在调参”进一步分解为Config bucket缺失、raw benchmark标签、默认合法候选数量、前后持久化、跨rank重复和协议tag六个独立检查；以后先用原始key与只读前后行差分区分冷未命中/namespace不匹配/缓存失效，再决定最小对照。仅限本FlagGems/PPU/BF16及实际M/N/K，不外推其他硬件或宣称数值kernel优化/正式通过。

## MM策略因果对照06（执行前冻结）

用户“请继续”后，在同一点51新增远端`mm-policy-diagnosis-06`。以05确认的新bucket冷miss为假设，先做临时有界策略诊断，不直接保留生产修复。仅通过现有LibTuner的Default policy边界，在外部进程内hook中把主`mm_kernel_ppu`的BF16/NT/非融合/M>4096冷miss候选限制为**原合法剪枝结果的前4个**。缓存命中、其他shape/算子、Expanded、原kernel、key、剪枝和20/100 benchmark协议均不改；不修复独立协议tag问题。该前4策略只用于证伪请求内宽搜索是否控制RPC，不宣称性能最优。

先CPU测试作用域/原有fallback/4项上限；真实PPU对各配置分别做FP32 oracle、非对齐与bucket边界及动态graph两次回放。通过后冻结baseline/candidate/revert：每角色从同一个before04快照SHA088b82c8…派生独立可写DB，启动前逐字SHA相同，生产DB不改。原MBT32768/FULL_DECODE_ONLY及H4六文件/SQL固定，原P4096/D16/C1后C8各一次，同token IDs/seed42/temp0/ignore_eos。默认策略与临时有界策略是主要变量；记录实际batch shape，异步成批差异不能静默视为完全相同。startup仍原策略，warmup返回后才激活限域hook，三个角色均相同观测开销。

baseline/revert只有已知sample_tokens约300s RPC可作为预声明诊断结果安全结束本角色后继续；数值、graph、OOM/非法访问或其他异常停止全部。不重试、不暖到通过、不降低MBT或延长RPC；每角色保留所有请求和事件，增加预冻结事件上限避免上次2000条截断。candidate通过三臂后才允许接续原C64及原最小/semantic/三16K矩阵，禁止自动全量GPQA/性能。最后精确停止自有实例，六文件恢复SQL-only、服务OFF，复核源码/index/镜像挂载/唯一安装/权重和生产DB不变。外部策略不修改已安装库文件，不自动部署，不签发新gate。

06准备于23:26:27完成，freeze SHAabee6de0…、CPU14项通过；设备控制器4069042/start531219694在首个脚本导入时因显式canonical backend import重复注册`aten.unbind_copy.int`失败，未执行MM/模型，四个测试DB仍0字节，`device-failure-audit.json`通过SQL-only/OFF全树核验。失败保留。恢复`device-recovery-01`仅改为从`sys.modules`复用FlagGems实际loader已加载、源路径精确匹配的MM模块，不重新执行后端init；新`mm-policy-device-recover-v1.py` SHAd30d0e99…和设备v2执行前保存，策略、23-shape矩阵、oracle/误差/graph门槛不变。不是MM数值失败或模型重试。

对照限制预先明确：独立role **SQL调参DB**的起始字节严格相同；Triton编译cache仍共享、未清空/回退。必须结合revert及实际batch-shape/搜索事件判断，不能声称所有编译缓存也严格同态，更不从冷请求诊断耗时计算稳态性能收益。

本次规划复盘`point51_after_SQL04_MM05_causal_validation`：04 SQL等价修复保留、但C8失败；05仅确认缓存/搜索机制，未改MM；06尚待真实对照。当前组合没有新的同配置稳态测量或正式gate，累计性能未知，历史加速比不相加。Prefill证据是新MM bucket搜索，Decode只有下游sample_tokens RPC症状，Mixed真实异步batch触发冷bucket；先做06策略因果证伪，若不足再按剩余栈分开定位编译/index-copy/collective，独立协议tag问题排在主故障之后。数值/graph/意外服务错误即停；不先做跨rank调参ownership或更多MBT调整。下一复盘触发为06终态与原范围回归决策。

23:31:34真实设备恢复验证完成：4个候选各23组（原生20组+3边界），92项FP32独立oracle通过；每配置固定地址、输入更新的动态graph两次回放，共8次通过，无TileLang导入。`device-validation.json`明确链接恢复命令/v2源码及4份原生结果SHA，不覆盖原导入失败；完整静态身份/源码/生产DB审计仍SQL-only/OFF。现在允许唯一派发模型三臂，**尚未证明模型修复、C64/语义回归或新精度通过**。

23:33:49三臂已唯一派发，控制器PID26257/start531263933，`commands/mm-policy-control-v2.py` SHA6f4f9e71…，`run-dispatched.json`/freeze SHAabee6de0…绑定。本轮先仅完成C1/C8三臂，不自动派发C64/原完整最小回归；三臂分析后决定其下一步。既有30min heartbeat已更新至本精确根并ACTIVE，只读、不变安静、禁止重复派发，终态恢复审计后暂停。只读分析`commands/mm-policy-analysis-v1.py` SHA1770b4ea…执行前保存，终态后才允许读取既有事件，不发模型请求。

23:37:55只读进度核验：baseline已通过原FULL capture/readiness及16worker观测硬检查，原C1 HTTP200/`C1-result.json passed`；同body C8正在执行、无终态结果，candidate/revert尚未启动，controller/failure/restore-failure均无新异常。不能据此提前声称缩短搜索后的模型修复或收益。

### 06只读跟进连接阻塞（2026-10-22 00:06）

本次heartbeat未取得任何新远端结果。受限沙箱中的本地Ansible RPC未启动；以控制面权限重做精确PPU-13连接检查后，raw `hostname`返回`no available gateway`，现有playbook却给出成功退出；独立只读shell检查同样返回该网关文字、模块JSON反序列化失败。**不得把退出码0或Ansible绿色回执当作连接成功。** 未切换Host、未绕过网关或修改连接配置。

因此控制器存活、三臂结果、恢复源码/index、8011健康及生产DB未变目前全部未核验，不能把旧23:37:55进度推断成当前仍运行、完成或失败。未执行终态分析、未派发额外模型请求、未改库/DB/服务或重启控制器。保留原实验状态与92项/8回放已验证范围，精度gate/性能仍无新结论。既有30min heartbeat保持ACTIVE，等待连接恢复后只读续查；未确认终态前不以完成名义停用，也不将网关故障记为MM候选失败。

03:35复查仍返回同一网关错误。距23:33:49派发已约14497秒，超过原14400秒**计划窗口**；这不证明控制器仍在运行或实际测试超预算，因为所有后续远端结果均未取得。恢复是否完成依然未知，因此一次性提示用户检查PPU-13网关访问；不盲目停止、重启或恢复源码，既有只读监控继续，未产生新模型结论。

## 06断网后结果取回与当前审计（2026-10-22 09:40）

PPU-13实际hostname已重新核验，用户“当前机器已经可以连接，请继续”后只读取既有结果，没有重放三臂。原控制器已在**昨晚23:54:03**完成并退出；断网后的4h计划窗口消逝是失去观测，不是本实验跑了一夜或已超时的证据。

| 原生角色 | C1诊断耗时 | C8结果/诊断wall | 真实冷M与搜索 | 每rank已完成benchmark数/耗时 |
| --- | ---: | --- | --- | --- |
| baseline原策略 | 2.295s，通过 | 8/8通过，237.634s | M12293、11组，每组104配置 | 1142–1144次，141.607–142.652s |
| candidate临时前4策略 | 2.183s，通过 | 8/8通过，58.937s | M28673、11组，每组4配置；16rank共176次策略命中 | 39–44次，5.302–6.044s |
| revert原策略 | 2.238s，通过 | 8/8 HTTP500，300.728s，sample_tokens RPC timeout | M20481/8198、17组已进入，每组104配置 | 1755–1761次，220.911–222.347s |

以上均为带观测的**冷路径诊断**，不是稳态端到端性能。三臂起始SQL DB字节一致，但异步接纳产生不同M，冷shape交集为0；同一HTTP C8并不冻结设备batch。因此不能将237.6→58.9s算成严格优化加速比，亦不能宣称完整RPC修复。所有rank事件均未触10万上限，旧原生数据不丢弃；rank间会复用并发写入的少量benchmark缓存，故完成次数略有差别，不能将各rank耗时相加为端到端。

当前只读全树/index、唯一安装、权重/tokenizer/thead/脚本/镜像挂载审计通过，Plugin59ae4b57…、FGVaec7a802…、FG1a6197b7…仍为SQL-only原身份，H4六文件已恢复、API不存在/8011关闭、master DB239ed14b…未变。`commands/mm-policy-resume-audit-v1.py` SHA370a4fec…执行前保存；`resume-final-audit-v1.json` SHAe42fdbc1…、`analysis-v1.json` SHAe1084e5d…及`resume-completion-v1.json`保留，零模型请求/零安装库变更。06终态审计后既有monitor已PAUSED，不再等待一个已经结束的控制器。无C64、原完整minimal、GPQA/gate、性能或提交推送新结论。

知识差量`refined`：原策略是否越过RPC窗口，与请求接纳造成的一组或多组冷M投影有关；相同SQL起点不足以让异步整模三臂成为同shape对照。下一首个证伪应固定kernel shape序列及输入内容hash，再核对Default/前4/Default，不靠更多重复HTTP流量暖到通过。

## 固定shape对照07与条件式原范围回归（执行前冻结）

沿用点51，在新远端子目录`mm-fixed-shape-07`，先只用单PPU0固定原失败M20481/8198、各11组真实N/K，共22组BF16/NT/非融合输入，三臂严格同shape序列、seed及输入内容SHA；每角色SQL DB仍从before04同快照独立派生，master DB不动。原策略/同一临时前4策略/原策略比较冷搜索预算，数学kernel、keys、合法性剪枝、20/100协议和Expanded均不改，Triton编译cache共享限制保留。固定shape的冷调用/benchmark耗时不能冒充稳态性能，单PPU不能冒充TP16模型通过。

三角色均需FP32独立oracle（rtol .01/atol .125/relative RMS≤.01）、实际policy scope/相同冷key覆盖和每角色两次动态graph回放通过，才自动接续新实例的原P4096 C1/C8→原smoke/C8和16383/16384/16385边界→11明确答案→原P4096/D16/C64/N64一次。该模型仅临时安装原H4六文件+原06外部候选hook，复用既有回归帮助函数，不新增生产MM源码/环境开关，不组合其他优化，不自动派发GPQA或性能；MBT32768/FULL_DECODE_ONLY/TP16/BF16/前缀关闭和交付脚本不变。首次数值/graph/服务失败停止，不盲重试。

控制器`commands/mm-fixed-control-v1.py` SHAb3cafe54…、设备脚本2c7ea13b…、精确PID/start_ticks/argv/scriptSHA清理c84e245a…及CPU清理测试488e3717…执行前保存。清理单测覆盖无进程、自有子进程、过期ticks不杀、argv不匹配不杀，先通过才可派发；每GPU阶段和整模前重新核验16卡空闲，不争抢共享任务。仅清理本轮注册的设备子进程，任何清理/恢复失败保留并停止闭环，不声称已恢复。最终源码/index精确回到SQL-only、master DB不变、服务OFF；候选不自动部署。原06失败/负证据完整保留，不建history。

07准备v1被CPU归属测试拦住，`cleanup-validation.log`保留：SIGTERM后stat尚非Z而cmdline先清空，误报接管；prepared/dispatch均不存在，三份初始DB原样，**零GPU/模型请求**。v2仅修复观测竞态：空argv时最多100ms重新查ticks/Z，无证据不视为已退出，也不向不匹配argv发送信号；真实argv不匹配仍拒绝。新controller SHA7029ffc8…、cleanup dba1c082…执行前保存，原4项native fixture保持；`freeze-v2.json`保存原freeze SHA并要求22-shape/oracle不变，仅复用已创建且未使用的同SHA DB，旧工具/失败/未运行`model-regression-01`不覆盖，模型接续放新`model-regression-02`。这不是MM或模型数值失败，不允许因此丢测量或改变参数。完整精度方法bundle6e94a080…/回执f0d42f77…冻结`e2e/accuracy: minimal-regression`，随外部命令保存。

10:04:37准备v2原4项CPU归属fixture全过，原生`cleanup-validation-v2.json`明确零GPU/模型请求；16卡各1MiB且SQL-only/OFF审计通过。`prepared-v2.json`绑定freeze SHA865a3c3d…、条件式model02 freeze SHAc1ceab20…。同版本唯一派发控制器PID222972/start535048728，`dispatched-v2.json`/`controller-v2.log`留远端；既有30min monitor切到07并ACTIVE，不建第二个监控。当前仅开始固定shape阶段，尚无任何新设备或模型通过结论。

07首次只读进度：baseline已输出8/22组原生shape检查记录，尚无该角色最终result、candidate/revert尚未开始，未出现failure/cleanup-failure回执。仅表示部分设备检查已执行，不代表整个三臂、动态graph、TP16模型、C64或正式精度通过；后续由同一控制器及已有monitor接续。

### 07固定shape三臂结果与模型启动进度（2026-10-22 10:16只读）

`fixed-comparison.json`已通过，三个原生result SHA分别611f4361…/ade74a46…/35c22d7d…，独立读取与控制器记录一致；22组shape及输入内容SHA、初始SQL快照和冷key覆盖相同。Triton编译cache仍共享，不宣称所有cache同态。

| 角色 | 每组合法/选取配置 | 实际benchmark数 | benchmark耗时总和 | 冷调用耗时总和 |
| --- | --- | ---: | ---: | ---: |
| baseline原策略 | 104/104 | 2288 | 289.837s | 302.076s |
| candidate前4 | 104/4 | 88 | 11.662s | 12.401s |
| revert原策略 | 104/104 | 2288 | 289.953s | 302.659s |

三臂共66组FP32 oracle均过，最大relative RMS .0016633；每臂固定地址更新输入的动态graph回放2次全部通过，无TileLang导入。由原→限4→原可确认：**Default冷bucket在线配置搜索是该固定shape序列高耗时的直接原因**，不再受06不同M的混淆。但这里是单PPU串行22组冷调用的诊断总和，不能把302秒直接等同TP16某次请求的300秒RPC窗口，也不构成稳态端到端收益、唯一RPC根因或充分修复证明。

10:16:24控制器原PID/start仍匹配存活，`model-regression-02/apply_h4.json`存在，模型按原TP16/BF16/MBT32768/FULL_DECODE_ONLY/前缀关闭启动；服务日志处于worker初始化阶段。C1/C8、三16K边界、11明确答案及C64均尚无完成回执，`model-result.json`/failure/restore-failure/completion均无；因此模型有效性及最终SQL-only/OFF恢复审计仍待定。此轮状态查询只读，未追加请求或重启，既有monitor接续，不签发新gate或继续性能晋级。

### 07模型回归终态：C64索引转换OOM（2026-10-22 10:37核验）

本轮10:23:48已结束，不再等待控制器。原P4096/D16 C1/C8通过；smoke/C8、原文输入16383/16384/16385各D8边界、11/11明确答案通过，实际FULL decode 11/11档捕获并产出多token。16worker各有22次前4策略实际命中（M20481/8198），最大事件数208，未触10万上限，不是候选未命中。

但必要P4096/D16/C64/N64回归**失败**。首个原生ERROR为10:23:39 TP2：公共`forward_mqa → _convert_request_to_physical_indices → torch.remainder → FlagGems pointwise_dynamic._alloc_output → torch.empty_like`申请**544MiB**失败；该卡仅余220.37MiB，进程95.67GiB、PyTorch allocated90.85GiB、reserved-unallocated3.40GiB。全部16rank均有OOM，客户端HTTP500；没有本轮`sample_tokens RPC timed out`记录。这里证明的是分配失败位置与当前C64服务失败的直接原因，不是remainder数值kernel错误或已确认碎片为唯一根因。仍须分析索引形状、中间张量存活/峰值及分配器；不能把OOM前的某一栈当完整峰值归因。

因此，MM固定shape冷搜索机制确认、前4变量可显著降低该冷路径开销，但**不是完整模型修复**；原RPC在本轮未以同症状重现，C64被新的显存问题阻断。保留原06/07全部失败，不以C8或66组oracle掩盖必要C64失败，不签发新gate、不恢复性能晋级、不自动更改MBT/allocator/显存水位或追加测试。

`model-regression-02/failure.json`、根`failure.json`及原生service/stacks保留；`model-regression-02/completion.json`/根`completion.json`明确model_passed=false。控制器停止精确自有实例，六文件/index语义回到SQL-only、H4/外部策略不保留、服务OFF；10:23根`final-audit.json` SHA96d6123f…通过。已保存零推理终态审计命令`commands/mm07-terminal-audit-v1.py` SHAc26ebe07…后执行，10:37:51 `terminal-current-audit-v1.json` SHAd0e95a14…再次通过三库全树/index、唯一安装、镜像/挂载、权重/tokenizer/thead/脚本及master DB239ed14b…不变核验，零模型请求/源码服务变更。当前Plugin59ae4b57…/FGVaec7a802…/FG1a6197b7…，不宣称该SQL-only版本已通过C64。

本轮监控已按最新heartbeat终态规则**删除**，不再轮询已退出的控制器。下一安全范围仅为既有C64索引转换形状/张量存活/峰值与MM事件的只读分析，尚未派发新复现、修复、正式GPQA或性能测试；无提交推送。

## 决定、风险与回退

源、优化容器镜像/挂载和私有唯一安装先重新核验，确认当前目标无用户接管及设备空闲。变更前完整归档两库源码/HEAD/index/原dirty，FlagGems和vLLM只读；仅SHA匹配的本点文件可替换/回退，不覆盖无关修改。失败保存首个原生异常，停止晋级，源码回退到本轮前公共repair08身份；该身份已知C64失败，恢复源码不冒称服务可用或已通过精度。不得擅自恢复整套旧PPU执行路径。无提交/推送授权。

## 外部证据

用户工作根下唯一目录：`/mnt/nfs/users/jinghao/glm5.3-flash/optimize/e2e-opt-20260911/resume-20261021-point51-sparse-mla-small-head`。命令/源码归档、测试、日志和gate留远端，本地只保留本MD/结构化账本/总览，不建history。
