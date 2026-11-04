# acc-012：PPU-07 当前 master 候选单服务 C64 全量 GPQA

后续accdiag-015局部终态（2026-10-15 23:05 +08冻结）：128请求/120唯一doc原始响应完整，均有最终content、无非法访问/真实HTTP错误/60K截断，8目标早晚16响应正常。存在客户端日志恢复的调度间断，大池FP32未覆盖，原模型根因未隔离、未修复，不生成正式gate或重计本轮分数。完整证据和限制见 [accdiag-015-c64-large-index.md](accdiag-015-c64-large-index.md)；原正式故障污染127/198不变。

后续诊断终态（2026-10-15 20:58 +08）：用户授权的恢复及局部C1→C8→C1已完成24/24请求，8唯一doc均有最终答案、未复现非法访问，C1前后8条完整token/message一致。原C64持续更替及高block-ID未覆盖，未定位根因、未修复、不重算本轮正式分数或签发gate；原故障污染127/198保持不变。证据冻结与限制见 [accdiag-014-state-zero.md](accdiag-014-state-zero.md)；heartbeat已暂停，8010保留运行，等待用户下一步方向。

## acc-012正式终态：服务故障（2026-10-15 17:20 +08:00）

后续用户已明确授权恢复8010及局部复现；新实例于17:43就绪，状态清零微测通过，8题局部客户端运行中。见 [accdiag-014当前记录](accdiag-014-state-zero.md)。以下是原正式运行终态，不表示当前恢复服务仍不可用；旧正式分数和失败证据不变，不重跑全量GPQA。

17:00:25 TP7 报告非法内存访问，17:00:28 executor 检测其退出并关闭服务，17:00:38 API退出；本次正式运行约2小时2分钟后以执行失败结束。17:20只读检查8010拒绝连接，原API/Engine/TP worker/evaluator/helper/controller已退出，两个容器仍running且OOMKilled=false（不能以此排除进程级或设备级问题）。`CLIENT_ERROR.log`及`evaluation/exit.code` code1存在，FINISHED/FINAL_SUMMARY缺失。控制器结束绑定检查在 `prepare_v2.py:35` 断言 `rows=[]` 失败。没有人为停止、重启或改动服务。

原生结果已写出 strict-match **127/198 = 64.14%**，低于0.88；原生samples按JSONDecoder.raw_decode解析完整396个JSON对象，每filter恰好198个唯一doc_id，不能按物理行或多filter合计计数。样本SHA `5f3ef13395dbed9783ced0a8cb1aaf1fbd25edc115c659e66467dcdd1b73d10c`。原生timeout标签61，其中35个此前已确认是content=None占位，另26个请求在服务退出后失败；不能称为61次真实网络超时。该分数是故障污染的原生观察值，不能当作模型在完整健康服务上的有效formal-gate；不签发通过gate，不恢复性能优化。终态helper的matched0/strict0/0也不是正式得分。

故障堆栈：GDN `qwen_gdn_linear_attn.py:1514` 的 `initial_state[~prefill_has_initial_state,...]=0` → FlagGems `ops/index_put.py:310` → THead `nonzero_numpy.py:212 count.item()` → `torch.AcceleratorError: illegal memory access`。堆栈明确实际命中Gems路径，但异步错误可能在后续同步才上报，首个非法访问kernel尚未隔离；崩溃前还有不支持 `tle.distributed_barrier` 的编译配置失败，暂不将其或此前KV-zero接线缺口定为根因。此次故障与35个reasoning-only异常的因果关系仍未知，分别记录。

按 inference-accuracy-diagnosis 冻结失败证据；CPU-only脚本 `[case]/commands/accdiag014-freeze-failure.py`，SHA `6358940241d57c354e8c9533c5a7e7747ceb50a734a535b59333b4ac17989225`，执行 `python3 [case]/commands/accdiag014-freeze-failure.py`，向新目录 `[case]/diagnostics/accdiag-014-service-failure-20261015/freeze-001/` 排他保存原日志/样本/配置副本、manifest/report，不覆盖正式产物，不创建FINISHED或伪造gate。该操作不发推理请求、不导入GPU栈、不改源码。

17:28:46 +08:00证据冻结成功，`freeze-001/report.json` SHA `f971ce2823b05e1ef35a5eb253e04f5b7044d90eb7cc2a309f5bbd4b9be76616`；manifest逐项记录原文件路径、大小、mtime、SHA和冻结副本。重新确认172个API返回全部stop、35个null最终content，最长52008 tokens，未见60K length cap。原生结果 `results/Qwen3.8-Flash-Next-ppu07-acc012-c64/6b6899a093b14fe7a4de2acfd8630e90/gpqa_diamond_generative_cot/Qwen3.8-Flash-Next/results_2026-10-15T09-00-42.191783.json`，同目录 `samples_gpqa_diamond_generative_cot_2026-10-15T09-00-42.191783.jsonl`；均相对于上文正式case根目录。没有run-record/gate，不创建替代回执。

原定C1→C8→C1要求“完整终态且原服务健康空闲、身份不变”，现已失败，故不自动恢复或启动复现。原heartbeat已通过产品工具确认为PAUSED。需要用户明确恢复/干预方向后再进行带精确回退的算子/状态路径诊断；局部结果不得改写本轮正式分数。

用户已启动服务并明确要求 64 并发、全量 GPQA。模式 `formal-gate`，strict-match 阈值仍为 0.88，198 个唯一问题，不使用旧双服务代理，不复用旧响应缓存，不修改/重启模型。

## 当前配置与范围

目标 `PPU-07`、`qwen3.8-flash-opt-ppu07-20261015`、8010、TP8/物理卡8–15、80K 上下文、BF16、FULL_AND_PIECEWISE graph。服务日志显示 prefix caching 关闭，decode FULL 与 mixed PIECEWISE graph 均完成捕获，运行前预检时健康且空闲。运行前重新捕获代码内容、实际导入/版本、模型文件清单、tokenizer 和服务 PID/start ticks，不沿用旧精度 gate。

沿用历史冻结生成配置：temperature=1、top_p=0.95、top_k=20、min_p=0、presence_penalty=0、repetition_penalty=1、max_gen_toks=60000；evaluator seed42、API timeout7200秒、API retries3、eval retries0。单客户端并发上限64、limit0、任务 `gpqa_diamond_generative_cot`。并发不代表任何时候恰好64个请求在运行。

## 方法与产物

使用本地 `inference-accuracy-evaluation`，bundle SHA `6e94a080dd3b64544c535e1fd4bda506f55516374d14d0f8ca6aa148bba2c7b2`；原始 runner SHA `82cf6e8304cb6f9eb8ca48fe4055f6bbb2054a7b6a90d56de3d6b7a08e90c61e`，由维护版 `formal_accuracy.py` 包装执行。规定镜像 `harbor.baai.ac.cn/flageval/flageval-llmeval:v1` 新建独立评测容器 `qwen38-eval-ppu07-acc012-c64-20261015`，只绑定 `/mnt` 和 Host 网络，无加速卡分配。若缺少 GPQA 数据缓存，只从同机既有评测容器读取复制原始数据，不复制响应/得分缓存或修改其进程。

远端唯一目录：`/mnt/nfs/users/jinghao/qwen3.8-flash/20261015-qwen38-flash-next-ppu07-container/accuracy/acc-012-full-gpqa-ppu07-c64-master-20261015`。`commands/` 保存控制脚本和 tar bundle，`bundle/` 保留 runner 相对路径，`services/` 保存当前实例 manifest，`evaluation/` 保存配置/契约/两次 provenance/预检及正式日志，`results/` 保存原生样本与结果。所有原始大产物均远端保存。

评测前采集两次实际 task/dataset provenance 并逐字一致后冻结，再执行 `--preflight-only`。正式客户端拒绝重复启动，结束后复核实例和源码未变；仅有效完整且达到阈值时签发 gate，不足则记录 failed，不重跑挑分。样本按 doc_id 去重并核对各 filter，不能用原始多 filter 行数冒充题数。

## 状态、监控与限制

当前 `running`。2026-10-15 14:59:05 +08:00 原生 runner 已启动唯一的一次正式运行（eval retries0），有效命令确认 `num_concurrent=64`、原生成参数及 `--seed 42`。UUID `6b6899a093b14fe7a4de2acfd8630e90`；原生输出在 `results/Qwen3.8-Flash-Next-ppu07-acc012-c64/6b6899a093b14fe7a4de2acfd8630e90/` 下，task 子目录保存 `lm_eval.log`、`progress_score.log` 和最终 samples/results。完整分数尚未产生。

heartbeat `qwen3-8-ppu07-gpqa-c64` 每30分钟只读检查，有实质进度、失败、明显停滞、完成或需要用户处理时通知，无变化保持安静。不得由监控重新启动/停止服务或评测器，终态暂停。没有可靠唯一题证据时不报完成数，无可靠依据不估 ETA。

两次 provenance 逐字一致，preflight passed。服务 manifest SHA `9940c0f854b7aa64f955dba842db16f5a063475b20bdf6855b13cf1977ddd7b7`，contract SHA `878e6497b0233043bd59d7bf4143125332e341ea94e11e5c4e73d0e0ff8ddd11`。准备初版因 import 日志混入 JSON 而退出，未启动正式 evaluator；改用单行显式 marker 后继续，初版日志保留为 `prepare.log`，成功准备日志为 `prepare-v2.log`。真正执行的是 `commands/source_probe_v2.py` / `prepare_v2.py` / `run_formal_v2.py`，SHA 分别为 `103726f81c6b08e0be1a3897e75077351e563d9e2349fb20fd8705a86f7ebf0c` / `3dc746f0abea1b81fd40cbcea02e0ca78960ba862d5c92350f219fe259a3386b` / `143c11cdef51cb2210c07b85bd2184bc270b2414f64d69b3ac00136cc3f2acaa`。没有重复正式运行。

原生 evaluator 14:59:12 +08:00 确认 cached requests0、remaining198，并进入 concurrent API 阶段（并发64、7200秒请求超时）。task 自带 `do_sample=False` 的提示不等于本次 temperature 被改为0：已只读核对规定镜像 `/app/lm_eval/models/openai_completions.py` 第143–159行，请求构造先移除 do_sample，再取显式 temperature=1，其他 gen_kwargs 透传。没有为该提示更改任务、参数或重跑。

首批尚无完成时，服务在15:00:13和15:01:13出现 `No available shared memory broadcast block found in 60 seconds`，并有 index_select 新 shape 的编译相关警告；/health仍200、evaluator进程存活，未见本轮新的异常堆栈。此时 metrics running/waiting 尚为0，不能声称设备已稳定运行64请求，也不能把构建context的198/198进度当成已完成题数。记录为首批长耗时待观察，不估ETA，不自动停止或重复评测。

15:02:51 +08:00 再查确认全部 TP worker 仍在，容器内出现多个活跃 `ppu-llc` 编译子进程，卡8–15已有占用；这是首次真实输入仍有 JIT 工作的直接证据，不仅凭 shm warning 推断死锁。/health200，尚未产生有效分数；监控继续跟进首次输出、编译是否持续和新增异常。未触碰其他卡组或服务。

首轮 heartbeat 于15:22–15:23 +08:00 只读检查确认已越过初始编译，API、EngineCore、8个TP worker及唯一 evaluator/score helper均存活；服务实际running64、waiting0，/health200，持续有HTTP200答复和非零generation throughput。15:22:49的原生 `progress_score.log` 为 `completed=60/198, matched=60, timeouts=0, strict=58/60 (96.67%)`。该 helper 按冻结prompt/gen_kwargs生成唯一cache key并匹配doc_id，确认本次60个key均匹配；不是把构建context的198/198或多filter行数当成完成数。此为阶段分数，不是完整GPQA分数，正式score/gate仍无。

截至15:23:45读取到的完整原生API返回对象按response id去重共63个，全部finish_reason=stop，completion_tokens范围243–5696，空最终content0、length finish0、>=60000 token0；62个包含固定best-answer短语，单个短语不匹配仅作格式观察，不判定其分数。63个API response诊断不替代60个已核验唯一题计数。没有发现本轮ERROR/Traceback/HTTP4xx/5xx行；尚未经历请求7200秒超时窗口，只能说当前未观察到超时，不推断后续不会发生。lm_eval.log最近更新时间15:23:13，阶段计分最近15:22:49，客户端无CLIENT_ERROR/FINISHED。已耗时约24分48秒，不估ETA；heartbeat继续active。

第二轮 heartbeat 于15:52–15:54 +08:00 发现新的输出健康异常，评测仍在进行。15:52:59实测服务/EngineCore/8 worker及唯一 evaluator/score helper均存活、health200、running64/waiting0，API进程的start ticks与argv仍绑定原manifest；没有ERROR/Traceback/HTTP4xx/5xx等新错误。native日志最近更新15:52:45、progress_score最近15:51:57，尚无FINISHED、FINAL_SUMMARY、CLIENT_ERROR或最终samples/results。

原生阶段计分15:51:57显示completed130、matched102、strict99/102（97.06%）。此时completed与matched已分离，不能把该97%视为整轮精度。额外只读用pyarrow读取评测容器缓存中的198条原始题目，重算逐题内容SHA并全部核对冻结provenance，再重建prompt/gen_kwargs cache key（不执行模型请求）；SQLite以mode=ro、PRAGMA query_only读取。15:54:42得到138个唯一doc_id、138条cache记录、未知key0，其中106条字符串、32条非字符串响应。临时strict匹配为103/106，但排除了32条无文本项，明确只属可解析字符串子集，不代表138题或全198题得分。

同一时刻原生API返回对象按response id去重138个，其中32个最终message.content为None，32个都有非空reasoning、这些空最终content项finish_reason均stop；不是整个回复连reasoning都空。其completion_tokens跨度2–6500，不能统一说成只生成2 tokens。此前15:52:59完整诊断的134个返回全部stop、completion_tokens最大15476，没有length finish、>=60000 token或超时；不把两个不同快照的范围混成对之后所有返回的保证。该异常既不能被HTTP200/stop掩盖，也不能由helper忽略None后的高阶段分数证明精度通过。已通知用户“只有reasoning、无最终content”，不改parser/算子/评测器，不中断或重跑；约56分钟耗时，继续只读监控终态和原生样本。正式score/gate仍未生成，performance不获准进入formal。

本轮绑定当前 FlagGems master + 4个必要模型扩展、normal_ fallback、用户后来安装的 FlagTree0.7.0；先前130项算子测试与历史175/198均不能代替本轮结果。模型身份采用当前实际权重文件清单（名称/大小/mtime）及 config/index 内容，不对约360GB权重逐字节重算；具体方法随 manifest 引用证据明确保留。未执行任何性能评测，不声明性能改进或最终优化验收。

## accdiag-013：空最终 content / 异常 reasoning（运行中只读定位）

用户明确要求定位32题只有reasoning的原因且不中断评测。使用 `inference-accuracy-diagnosis`，分类 `request/output-health`；正式结果仍未产生，不预判最终gate。仅分析原始返回、CPU端缓存/源码和只读metrics，不补发请求、不改parser/采样/源码、不重启、不重跑。首次空最终content见原生API第80个返回，2026-10-15 15:31:42 +08:00；此前79个没有空最终content，后续正常与异常返回交错，不能据此单独证明槽位复用或特定算子根因。

计划在当前远端case的 `diagnostics/accdiag-013-null-final-20261015/` 新建只读分析脚本及不可覆盖快照，冻结最初32个异常response ID、原始response和log行号/hash，记录当前缓存中能独立匹配的doc集合。原始API没有doc_id、token_ids，因此不能在缺少一一对应证据时把异步response序号当作doc_id；新出现的异常与原32个分开记录。同步保存当前解析器/停止条件源码切片及其SHA。不修改既有正式目录文件、日志、SQLite或服务。

诊断脚本远端保存为当前case的 `commands/accdiag013-readonly.py`，执行命令 `python3 <case>/commands/accdiag013-readonly.py`，SHA-256 `ab8720ed537f8a4f50f3fbc7a5160f2e0476acb29feb0692e4de2ce143e146d2`。脚本仅使用日志字面值解析、Arrow内存映射、SQLite `mode=ro/query_only`、源码文本读取和新诊断目录排他写入；不执行pickle反序列化、模型generation或GPU算子，若输出目录已存在则拒绝重跑覆盖。

### 已查明的边界

16:14:56 +08:00 成功冻结证据：API去重返回156个；缓存198条原题SHA全部匹配冻结provenance，156个唯一doc_id、未知key0、33条非字符串值。最初32个API异常单独保存为 `cohort-first32-responses.json`（SHA `5d50bfa033fbf763e10b57c483a575595d36b2a389304cd3223f4caf5577504c`），新增异常另存 `additional-empty-responses.json`，不变更原32的定义。总报告 `report.json` SHA `9587eb6d5ba94d991bf972ba8bb7bca7db2621a1a16f14a431ee64246fee3558`；`response-index.json` 保存异步response顺序、log行号、逐行SHA、停止原因和token数；`cache-doc-snapshot.txt` 保存独立doc集合及prompt/cache摘要；`parser-and-stop-sources.jsonl` 保存当前vLLM源码及SHA。原生日志前缀2933922字节，SHA `8c48c0dee28046bebaadec4134c87560476da9560fb1d66afd639a0df759001f`，不对仍在追加的整个日志声称固定SHA。

最初32个全部有非空reasoning、content=None、finish_reason=stop；completion_tokens 2–6500，13个不超过100，12个含Unicode替换字符。完整reasoning中按实际strict短语 `answer is\s*[\(\[]?([ABCDEFGHIJ])` 检查命中0；人工核对可见乱码/无关文本、未完成推导以及循环重复，不能解释为32个正确答案被评测漏取。例如response `chatcmpl-b5bf938733f6648c` 只生成2 tokens、reasoning="We"；`chatcmpl-929367761043910c` 6477 tokens，尾部大量 `WAIT!!!`；`chatcmpl-842b3757c1cf3619` 6500 tokens，尾部循环重复相同Step问题。这些只是输出异常证据，不反向推定具体GPU数值或算子已定位。

8个异常明确stop_reason=248044，当前tokenizer对应 `<|endoftext|>`；generation_config把248046 `<|im_end|>` 和248044均设为EOS。另24个stop_reason=None；当前 `v1/core/sched/utils.py:104` 对主EOS终止恰好不设置stop_reason，因此与主EOS提前结束一致，不能把None当成未结束或超时。32个都不是length finish，不是60K输出上限，也没有实际API超时报错证据。没有原始token_ids，24个末token不能逐条直接验证。

当前 `--reasoning-parser qwen3` 实际使用新版 `Qwen3ParserReasoningAdapter → Qwen3Parser → ParserEngine`，不是旧文件名 `qwen3_reasoning_parser.py`。`parser/qwen3.py` 默认REASONING状态，`</think>`使其转CONTENT；`parser/engine/parser_engine.py` 非流式解析每次reset，最后 `"".join(content_parts) or None`。因此EOS之前没有产生可解析的最终正文时，API可以正常stop但content=None。API日志已是解析后文本，think标记会被解析器消耗；**不能仅因reasoning里不含 `</think>` 就声称原始模型绝未生成该token**，也可能刚闭合思考即EOS。无原始token/logit证据时，解析器兼容性、生成异常与detokenization异常不能全部从根因候选中排除。

评测器 `/app/lm_eval/models/openai_completions.py:162` 仅返回 `message.content`，不读取reasoning；空值已经存在于服务API，不是strict filter制造。另 `/app/lm_eval/models/api_models.py` 第763–769行会把None转换为 `<TIMEOUT>`（文件SHA `493c667142263338f93894adf5638403269081b8329579eac1a64eda70383720`）。所以本轮最终样本若出现timeout标签，必须对照原始stop/HTTP日志分为“空最终content占位”与真实网络超时；不能仅凭该标签归咎请求超时。当前score helper又会跳过非字符串缓存，97%左右子集分数仍不可当整体精度。未修改任何评测取值或重算替代正式分数。

新增第33个异常 `chatcmpl-b397ffd9410a8785` 于16:04:22返回13970 tokens，reasoning末尾明确有 `Conclusion: The best answer is B.`，content仍None。这是独立的“答案文本留在reasoning/未进入最终正文”例子；不代表最初32个也有隐藏答案，也不据此判断该B是否正确。其原始对象另存，没有把reasoning拼进content或用于官方评分。

### 尚未确定的根因及下一步

当前33个缓存空最终值的doc_id全部在142–194范围，而前79个API返回没有空最终正文、其后正常与异常交错。这支持优先检查持续并发中新请求加入、状态槽位初始化/复用、Prefill与Decode混合的metadata/cache/graph路径，而不支持“一启动整个tokenizer/权重就完全错误”的简单解释。但doc_id不是API完成序号，当前日志缺请求关联ID，不能逐个将异步response ID映射到null缓存doc，也未完成实际派发顺序/slot/rank证明；不能直接宣布缓存串扰或某个index/QSA/GDN算子是根因。当前KV约59%、preemptions_total=0、health200；没有证据表明显存抢占引起本次异常。

精度定位结论为 `suspected-not-isolated`，只完成生成/解码—解析—评测边界定位，不是根因修复。当前master FlagGems、FlagTree0.7、持续并发状态和graph执行尚未被同配置单变量对照分开；旧130项测试使用的FlagTree0.6.2a1不能证明当前0.7组合无误，亦不能凭升级时间就归咎编译器。按用户限制不在线加埋点、不补发请求、不切fallback、不改sampling或EOS、不改源码、不重启。待原评测终态并冻结后，首个证伪实验应保持原prompt/seed/sampling、同一持续请求更替负载，对比失败/健康请求的原始token流及新请求初始状态；再由第一处张量分歧选择单变量state/graph或master/compiler对照。任何修复仍须最小复现、并发/graph边界回归及原198题正式契约重验。

最后16:17:24 +08:00只读确认health200、evaluator及helper进程存活，FINISHED/FINAL_SUMMARY/CLIENT_ERROR均未出现。当前正式评测继续、heartbeat保持active，未中断或重复执行。精度gate仍pending，不更新acceptance为通过。

### 状态/缓存/graph路径续查计划（用户2026-10-15追加指令）

继续只读审计当前实际Plugin、Gems、vLLM源码及已有日志；运行中不加埋点、不发模型请求、不执行GPU单测、不改状态或graph。不使用ptrace、调试器或直接读取GPU状态。受控复现必须等原正式评测终态并冻结证据后开始，不以本次静态分析冒充复现结论。

先保存当前源码快照，远端新增 `diagnostics/accdiag-013-state-graph-audit-20261015/`，脚本为 `commands/accdiag013-state-audit.py`，SHA-256 `5f97c4f5fa390f99871606e58c86fda603307ea98094c1d5de11e4a29b305680`，命令 `python3 <case>/commands/accdiag013-state-audit.py`。仅文本读取、git只读状态、health/metrics及新证据目录排他写入；不导入推理栈。审计重点：新请求has_initial_state及QSA/PLE/GDN初始化、batch row移动/slot/block复用、standard/common slot producer所有权与stream fence、FULL/PIECEWISE graph输入地址/值更新与padding、源码静态分支和实际命中证据的区别。

续查发现WorkerFL与上游GPUWorker的KV-zero初始化调用存在差异。补充只读AST/源码快照脚本 `commands/accdiag013-kvzero-static.py`（SHA `8aec495e26e5182f95820791ae6efb16807b1d29f5c378a98ab5238c67113721`），命令 `python3 <case>/commands/accdiag013-kvzero-static.py`，只向上述审计目录的 `kvzero-static-001/` 新增证据，不执行提取出的函数或任何受控复现。具体缺口与本轮乱码的因果关系仍待原评测结束后验证。

### 评测终态后的受控复现顺序与启动门禁

用户本次明确授权“等跑完后再做受控复现”。原heartbeat继续30分钟检查，先前“正式终态即暂停”改为：先完成正式结果/失败证据冻结与通知，再按以下门禁衔接诊断；诊断完成、证据不完整或需要修改代码/重启时暂停并报告。不创建重复monitor。

1. **硬门禁**：FINISHED及正式exit/FINAL_SUMMARY齐全；原生198唯一题和服务绑定可验证；原evaluator/score helper/控制器均已退出；服务running=0、waiting=0；实例与源码仍是冻结候选；无其他客户端/用户新任务占用。门禁不满足仅只读等候或报告，不能靠杀进程、清缓存或重启来满足。正式分数低于阈值可进入精度诊断，不签发通过gate。
2. **先离线后API**：对已冻结样本/原始返回/缓存进行doc-ID关联核验，保存prompt、采样、seed、stop、response/token hash；不将reasoning重计为官方答案。离线检查KV-zero调用链、GDN初态mask和batch-row映射，不导入或操作正在服务的GPU对象。
3. **无重启、小范围A/B/A**：先冻结8条请求的版本化清单：4条本轮null目标（142、144、149、155）、1条reasoning有答案但content空的对照（151）、3条从冻结缓存按doc_id升序选取的可核验字符串回复对照（不按答案对错选）。采用原prompt、temperature1/top_p.95/top_k20/min_p0/penalties0和1、API seed1234、max_tokens60000及原stop；按C1→C8→C1各运行相同8条，精确记录派发/完成/服务指标。每臂一次，不循环挑结果、不启动formal入口。若实际已无法核验该题/请求身份或有并发外来负载，则停止并报告。若需请求扩展返回token IDs，先记录其仅响应证据变更及对照，不能伪称原API已经记录raw token流。
4. **按结果决定下一步**：C1/C8未复现不排除原C64持续更替负载；可准备不超过128请求的C64局部cohort，但先冻结父场景差异、目标分发顺序及一次性启动/停止条件，不能重跑正式198题、不能把局部cohort称原正式进程/完整负载。需要改代码、启用运行时埋点、重启、切compiler/Gems或直接GPU单测时先报告方案并停在该边界，不由heartbeat自动执行。

上述是未来条件满足后的诊断计划，当前未执行任何API复现、GPU测试或改动；原正式进程/输出不因此失效或被替换。后续启动脚本仍须执行前归档、拒绝重复，复现结果写回同一issue，必要时按本地accuracy minimal-regression方法冻结范围。

### 状态/缓存/graph只读续查结果

16:30:28保存25个实际源码文件，Plugin HEAD仍939600b、Gems仍85cc5ef，既有dirty状态保持；模型源码SHA `3ae84180f7b5f4d70886c98f1d1afcf2255f8f7223a110397ec4894cf81a9a59`，Runner `2df8aa58559ae7f9a3576ebcd234b42c864f5054fdff8897110dd60b26cb8bc0`。远端 `source-audit.tar.gz` SHA `60123dd426a88a3c9ccb48023b17e6efa8b1c86a3400d9f0fc26bede341e13c9`，只含源码及白名单状态，下载校验后本地离线分析。16:39:43补充 `kvzero-static-001/report.json` SHA `3867adaae1c364c4ca241ff6006ea58e3389f10c8063263f62ac65fe6aaeaeec`；该脚本仅解析AST，不执行提取方法，不是受控复现。

**发现一个具体接线缺口，尚未证明为本轮根因**：实际 `/workspace/vllm-plugin-FL-qwen38-adaptation/vllm_fl/worker/worker.py:677` 的 `WorkerFL.initialize_from_config()` 仅调用connector初始化和 `self.model_runner.initialize_kv_cache()`；WorkerFL直接继承WorkerBase，不继承上游GPU Worker。上游 `/usr/local/lib/python3.12/site-packages/vllm/v1/worker/gpu_worker.py:614` 在缓存配置要求时还调用 `_init_kv_zero_meta()`。本机 `KVCacheConfig.needs_kv_cache_zeroing` 等于 `has_mamba_layers`，本模型包含GDN/PLE MambaSpec。Plugin worker目录中 `_init_kv_zero_meta` 仅见Runner定义、没有调用点；而Runner第1208行 `_zero_block_ids` 通过 `hasattr(self, "_kv_block_zeroer")` 判断，无对象就静默不执行。Worker源码SHA `a8de1780d1b41bf4889c26f3d593e6ec54e91a5f61996ce64b4d79f2a97efa24`，上游Worker SHA `271c3e2eaab7f1ca36fcd7c8e1620db9db4705f46ba5b3257dd6a3937f56b7df`。

该缺口针对**新分配/复用的attention KV块**，不是“GDN/PLE整个状态从未清零”的证明。反证和边界必须同时保留：Runner第7320–7327行首次分配使用 `torch.zeros`；GDN prefill第1513–1514行先gather，再把 `~prefill_has_initial_state` 对应行置0；PLE第3050行通过 `torch.where` 屏蔽无初态状态；QSA sparse kernel对无效K/V读取使用mask和other=0。上游KVBlockZeroer自身也跳过MambaSpec，只处理FullAttentionSpec类。这些保护意味着“没有接上清零钩子→必然读取脏缓存→本轮乱码”的链条**尚未成立**；不能凭这一个源码缺口直接上线修复或宣布根因。原始GPU状态、实际物理块复用、stale read/NaN以及第一层分歧均未采集。

| 路径 | 当前静态证据 | 仍需终态后验证 |
|---|---|---|
| 新请求/row复用 | InputBatch.add_request重写计数和block row；remove清除旧row；condense搬移token历史、计数和所有group的row；block table每步H2D提交 | 用相同request ID追踪row/physical slot、prefill initial mask与state写回，不能把batch row等同物理state slot |
| PLE ngram上下文 | `_prepare_ngram_context:3565` 每轮先将真实和padding行填EOS，再按当前num_computed读取CPU历史；新请求end=0会保留EOS | async分支在CPU历史放-1、GPU input_ids另行修复，而ngram仍读CPU；当前日志未证明async实际开启，不能先定为现网问题 |
| GDN/PLE初态 | context length>0生成has_initial；GDN先gather后mask清零再scatter；PLEwhere清零且scatter跳过null slot | master实际index/gather/zero/scatter在真实stride/复用slot与FlagTree0.7上的数值及路径命中 |
| common-slot graph | Wrapper SHA `811289ae…`，仍保留T-Head replay后的current_stream.synchronize；graph key是block table对象和请求数，kernel读取动态query/position/table值并清padding row | 当前运行的每rank实际指针和值、FULL↔PIECEWISE切换及请求更替时是否一致；不能仅以静态代码或旧微测证明 |
| model graph | GraphWrapper SHA `ba78ed0a…`；FULL decode metadata使用持久state-index buffer并将padding设NULL_BLOCK_ID；常规地址断言只在DEBUG且仅检查显式Tensor args | metadata/hidden cache mutation和shared graph pool的实际依赖；这与历史诊断曾拒绝的weak-ref/cache-ABI补丁不是新的因果结果 |

现有测试覆盖的边界不足以替代整服务复用：`test_runner_ngram`有CPU的end=0重复填充；common-slot测试仅小batch替换row及changed-input replay；GDN decode测试用小状态池、3行，改变indices做12次replay。这些测试有价值，但没有验证当前TP8、C64持续进出、真实页池复用以及Worker KV-zero生命周期。当前未重跑任何这些测试。

16:43:59 +08:00再查health200、running30/waiting0、KV70.75%、preemptions0；API start ticks仍476053037，FINISHED/FINAL_SUMMARY/CLIENT_ERROR仍无。不能用198减running推算唯一完成题数；最新独立doc核验快照仍是16:14:56的156题。没有更改或中断模型/评测，也没有触碰其他卡组。

原heartbeat `qwen3-8-ppu07-gpqa-c64` 已通过产品工具确认更新为ACTIVE、保持30分钟及无变化安静：正式运行时仍严格只读；终态先冻结/报告原始结果，满足上述空闲和身份门禁后才衔接无重启C1→C8→C1局部复现；诊断完成、需要改代码/重启或证据门禁不满足时暂停并报告。不新建重复任务，不自动修复KV-zero缺口，不重跑正式GPQA。该计划并不保证离线客户端退出后立即占有服务；须重新确认用户或其他任务没有接管。

### heartbeat 2026-10-15 16:49 +08:00

正式评测仍运行，FORMAL_STARTED起已耗时6651秒（约1小时51分）。重新校验198条Arrow原题的内容SHA与冻结provenance全部一致，重建cache key并通过只读SQLite核验171个唯一doc_id、未知key0；136条字符串、35条非字符串。只抽取已归档且SHA一致的 `commands/accdiag013-readonly.py` 中 `cache_code` 字面量进行CPU只读核查，没有再次运行会建立诊断目录的脚本主体，也没有发起模型请求。

API日志按response ID去重171个，全部finish_reason=stop，35个content为空且reasoning非空；completion_tokens 2–47609，length finish0、>=60000 token0。相对16:14:56冻结的156返回，新增15个返回、2个空最终content，缓存非字符串集合新增doc197/191；异步response与doc的逐项对应尚不能确认，不能把集合新增顺序当作一一映射。新增response `chatcmpl-b83d582876d354dc`（lm_eval.log第506行、16:17:26、13661 tokens、stop_reason248044）及 `chatcmpl-a9f45f7bd606a5c0`（第548行、16:49:11、32286 tokens、stop_reasonNone）均为明显乱码/重复reasoning、没有固定best-answer短语，不归入之前doc151的“reasoning有答案文本”类别。原始内容仍保留于native日志，不覆盖最初32个冻结样本。

原生progress最近16:47:32记录completed170、matched136、strict127/136（93.38%），排除了34个非字符串；稍后171条缓存已含35个非字符串。该子集分数不代表171题或198题精度，正式结果/gate仍未生成。初次宽泛搜索ERROR匹配到的是旧INFO响应正文中的字符串，已排除；按原生日志severity字段复查，lm_eval/formal-run均ERROR/CRITICAL0、实际API失败事件0，服务HTTP4xx/5xx0。没有把输出中的错误单词当作服务异常，也没有把None转TIMEOUT占位算成网络超时。

API start ticks仍476053037，EngineCore与8个TP worker、原evaluator/score helper及Host控制器存活。health200、实际running27/waiting0、KV69.35%、preemptions0，最近generation throughput283.5 tokens/s；native日志16:49:14、progress16:47:32、service.log16:49:49更新。FINISHED、FINAL_SUMMARY、CLIENT_ERROR及正式exit均未出现，未见停滞。正式运行未终态且服务不空闲，受控复现门禁不满足，保持延期，不暂停heartbeat，不修改/重启/停止或重复启动任何进程。
