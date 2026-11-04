# acc-019 当前完整thead MoE入口的C64全量GPQA

- 状态：2026-10-23已完成并通过终态CPU证据审计；正式结果`failed-score`：174/198＝87.8787878788%＜88%，无gate。原controller/evaluator/helper均自然退出，当前BF16 8010健康空闲；monitor已删除。
- 执行前保存本轮专用CPU-only审计`CASE/commands/acc019-terminal-audit-001.py`，SHA `f9aa3f1ce47fe3040286c5e6e8fa4a3d81e334f6704738dcc902deb4cddc50e3`。拟仅一次执行`PYTHONDONTWRITEBYTECODE=1 python3 CASE/commands/acc019-terminal-audit-001.py`，排他创建`CASE/diagnostics/cpu-terminal-audit-001`；只读核原生provenance/396双filter行、187已返回完整API对象、50条真实客户端timeout、11占位doc、manifest/源码/实例并复制已有产物，补冻summary/FINISHED及日志尾部。任何核验失败保留原件，不运行模型或重新评测。
- 启动历史：2026-10-22 18:29唯一launch，2026-10-23 01:37:26原controller完成冻结并自然退出；单轮198逻辑题、0新smoke、0服务重启。
- 类型：`formal-gate`，覆盖eng-066完整`fused_experts_impl`入口及当前保留组合；不是性能测试。
- 用户授权：复用当前8010，C64单轮198题；BF16和现有修复不变；不重启、不访问8035、不提交或推送。

## 优化方向与依据

eng066同实例已完成2C1＋8C8短doc2最小回归及CPU终态审计。8rank原生入口栈证明Plugin apply实际调用FGVLLM thead `fused_experts_impl`，两类capture各7/7、C8前native FULL1145；这些证据只能证明短题范围，不继承旧acc018的176/198 gate。本轮按新授权验证完整模型精度。

## 冻结范围与边界

- 当前容器`qwen3.8-flash-opt-ppu07-20261015`，8010/TP8物理8–15，Host API1693692/start537709560，argv SHA `c146e2da4762690185e9b3573c5f48796a5cb42aa2037de0d08d9ada40595010`。
- 三库加载`/opt/vllm-plugin-FL`、`/opt/FlagGems`、`/opt/FlagGems-vllm`；开关`VLLM_FL_USE_FLAGGEMS_VLLM=1`，既有bootstrap和cache不变。保留BF16、i64/randn、PLE i64+CTA、QSA M16、MoE主机边界修复、normal_/index_select黑名单及pin047。
- `gpqa_diamond_generative_cot`，198唯一doc、limit0、C64、`exact_match,strict-match >= 0.88`。温度1/top_p.95/top_k20/min_p0/presence0/repetition1/max60000，seed42/API原seed与stop不变，API retries3/eval retries0/timeout7200，返回完整token与prompt。
- 新规定flageval评测容器、独立UUID/SQLite响应缓存；只复制既有数据集，不借旧答案。维护formal wrapper调用原始runner；两次新provenance相等和preflight通过后才单次launch。没有新smoke/重启/额外推理。
- 新formal没有逐层、Q/K、状态或logits张量取证；现有一次性入口记录来自同实例启动期，不当逐题trace。native INFO保存完整解析API对象/token，不是HTTP wire bytes。按新服务日志byte/inode窗口判断本轮异常。

## 正确性与路径命中

新检查已确认当前精确API和8010listener一致、health200且running/waiting0，prompt3210/generation5801（既有10请求）。将重新绑定当前源码、三repo HEAD/index、engine、model/tokenizer元数据及graph/入口原件。weights采用文件名/大小/mtime清单和配置内容SHA，非重新读取全部权重字节。

当前正式分数、正确数和gate均待本轮原生结果；不能用helper排除None的子集分数或多filter行数代替198唯一题。真实HTTP/网络超时、空final/None占位、60K length分别记录。低分或证据无效只冻结分析，不自动重跑/修复/切回FP32。

## 性能效果

不测性能，不以本轮耗时推断吞吐收益；旧perf060结论不自动适用于完整MoE新路径。

## 决定、风险与回退

只启动唯一完整评测客户端。正式终态需核198唯一doc/每filter一次、原始内容一致、source/服务前后一致和原生results/samples/gate（或失败回执）。保存完整日志与SHA；完成后结束monitor并保持8010不停止。现有回退备份保留，本轮无自动恢复授权。

## 外部证据与执行入口

远端CASE：`/mnt/nfs/users/jinghao/qwen3.8-flash/20261015-qwen38-flash-next-ppu07-container/accuracy/acc-019-full-gpqa-ppu07-c64-thead-full-moe-20261022`。

执行前保存`CASE/commands/acc019.py`，依次仅一次`--mode prepare`、核验后仅一次`--mode launch`；launch产生唯一`--mode run`进程。脚本没有模型启动/停止/重启分支。

- controller SHA：`52034c96d1bdf049ea8c5881b64cf3b04db7c78268bc426476f635e654fd06db`。
- CPU source probe SHA：`b52e4d46bdbdde6939892ed219e8f9210d090e86f88ddb629412f620cb6721cb`。
- 运输归档SHA：`ee4c6b9bc02a3e26534fa9309e46d2d796bb695d4d0302ac90fb90cd6b252e51`，21份维护工具/Skill文件。
- 本地Skill：`inference-accuracy-evaluation` / `formal-gate`，完整bundle SHA `804b60f96089a5f37ee76d40c1ba11405ed8e61b45940786b52e52ed7b91edfb`。
- 当前最小回归原件：`engineering/eng-066-thead-full-moe-entry-20261022/model-regression-001`；本轮新增记录不改原件。

准备回执SHA `28c6750b5a9a0cfe602be4e8012e1e50d1c2690319093e80a8e78246f8ea7239`；两次provenance SHA `c39228d57fd391a9f723496f54fa2fb3f0d7aeb17810a2edf63559152dc63523`与旧数据内容相符；新contract SHA `bc9f4ae6a0316cf347574491d28b0bf79e49f394d86a0c01b13d054ec9b00efa`，service manifest SHA `6ee852c75f802ad8a63cb994ea2a6e0460b789ed7916e53d187ce66dcaa21975`，source-before SHA `93e0f898563bbfeec3232abc6b73caa93302d1b9de49d4d662c04cc5e84a9490`。

新monitor `qwen3-8-ppu07-moe-c64-gpqa`已由产品确认ACTIVE，每30分钟，只在实质结果、完成、失败、明显停滞或需处理时通知；原eng066 monitor仍已删除，不重复。审查已将可变JIT编译产物从稳定源码指纹移出，必需metrics缺失不会当0，终态freeze失败不会报告完成passed。

## 唯一正式评测已启动

`CLIENT_LAUNCH` epoch1792664950.1926794；Host controller3724689/start538077673，argv SHA `33999ef93d6a89f09a241b702792dcf9277c77e74573141f959693fc439bb3e1`。`FORMAL_STARTED` epoch1792664951.76688（18:29:11+08），原生日志18:29:27开始198逻辑请求、concurrency64、timeout7200，缓存命中0。当前无CLIENT_ERROR，8010health200/preemption0，尚无终态分数；不把派发/在途当完成。

后续只能监控已有进程，禁止再次执行prepare/launch/run，不增加请求或重启。终态正式结果位于`CASE/results/`，原生解析API/token日志`CASE/evaluation/formal-run.log`，服务新窗口起点在`CASE/evidence/service-log-boundary.json`。

本地全仓记录校验受到其他模型/历史过程材料的既有错误阻塞，未为本任务修改无关记录；acc019的YAML、文档链接和当前范围另外检查。

## 运行中首次真实客户端API超时（2026-10-22）

`acc019-client-api-timeout`：原生日志首次UTC12:29:27（北京时间20:29:27）出现`asyncio.TimeoutError`分支的API timeout，正好达到原7200秒时限；截至UTC13:10:02有20条超时日志事件，不是20个已确认失败doc，也不是空content转成TIMEOUT。已保存174个去重完整正常API响应，24个服务请求仍运行；同一8010health200/waiting0/preemption0，服务新窗口无NaN/非法访存/RPC错误，source与评测工具SHA保持。尚无results/samples/FINAL_SUMMARY/FINISHED，未判正式精度失败或通过。

按`inference-accuracy-diagnosis`仅保全已有证据，不复现、不更改超时或重试契约、不启动新请求或恢复服务。原runner的eval_retries0表示整轮只执行一次，不等于禁用适配器既定max_retries3；不能把日志事件、服务running或response ID直接当唯一题数。超时不证明网络断连或MoE/kernel错误；无本轮完整逐层/state/logits及未返回token现场。

执行前保存CPU-only冻结命令为`CASE/commands/acc019-first-timeout-freeze.py`，SHA `02eb2523b169bfc0f5f6602f0b02653509dacb1177f35852be136addc48acb7b`；拟仅一次执行`python3 CASE/commands/acc019-first-timeout-freeze.py`，排他创建`CASE/diagnostics/first-timeout-evidence-001`，复制已有日志有界前缀/服务新窗口、配置/manifest/API适配器源码及已返回完整token解析审计。原件不改、不执行原controller；冻结结果待回读。监控继续ACTIVE，等原评测自然收尾。

首次CPU复制工具在创建子目录时因`diagnostics`父目录尚不存在而失败，未创建快照；原脚本保留，不是模型/评测故障。SFTP传输亦未成功，随后SSH排他原样传输并核SHA。仅修正父目录创建，另存`CASE/commands/acc019-first-timeout-freeze-v2.py`（SHA `c3343d736e1c796f9aa6a05454e8fdb34c44696c138c4d4c56825ccfec0ec558`），执行前记录其唯一CPU保全调用；不修改v1或模型，不追加推理。

21:20+08，v2已完成保全：`CASE/diagnostics/first-timeout-evidence-001`的23份文件全部SHA/大小一致，所有源日志前缀和byte/inode新窗口回读匹配；manifest SHA `56e57879a265f03e100e92f486badb24a32de3e8376e30b4a8b6b5dd3905b84f`。174完整响应的token/usage、prompt IDs/text、非空final、think-end与EOS均核验正常；20条客户端超时事件另存，原错误及工具v1失败历史保留。保存的是原生解析API对象/token和已有完整日志前缀，不是HTTP wire，也没有未返回请求的完整token或逐层/state/logits。

冻结的实际`api_models.py`确认`ClientTimeout(total=7200)`，异步`stop_after_attempt(max_retries)`配置3代表最多3次总尝试，指数退避；这是原客户端既定行为，不是monitor新增重试。首批8条timeout同时出现在20:29:27，不能按错误行映射到doc或假设已知唯一失败题数。冻结时原controller/API身份未变、health200，仍无FINISHED/FINAL_SUMMARY。已通知首次真实超时，后续同一事件无实质变化不重复通知；继续只读等待原评测终态，不改超时/采样/服务或自动修复。

## 终态：174/198低于阈值，证据完整，保留当前BF16服务

原生`exact_match,strict-match=0.8787878787878788`，独立逐题核得174/198（87.8788%），低于预冻结0.88；至少175题正确才能达标。结论为`failed-score`，没有run-record或accuracy-gate，不能把187份已返回回答的子集分数替代198题正式分数。`FINAL_SUMMARY.json`与`FINISHED`齐全、无freeze_error；原controller及原formal wrapper/lm_eval/helper均已退出。实际lm-eval定制版本0.4.8、datasets4.8.5与本轮冻结provenance一致，维护工具核验其原生schema/任务metadata、dataset内容、seed、生成参数、独立缓存UUID和198个处理后doc SHA通过。396行中strict-match/flexible-extract各198，每个(doc,filter)恰一次，同题原始doc/resps/target/arguments完全一致；非正式helper尾部matched=0不影响已验证的原生结果，也不被拿来计分。

187份完整解析API对象均能通过prompt及原始content一一映射到187个唯一doc：174题strict正确、13题正常回答但strict错误；全部非空final、finish=stop、完整token/usage/prompt IDs一致，think-end248069及末EOS248046/248044齐全。最长已返回43704 token，没有已返回的60K length、空final或Unicode replacement异常。另11题为原生`<TIMEOUT>`且usage=null：doc32、48、71、88、90、121、127、130、145、147、185。这11题没有返回完整API对象/token，无法判断其未返回生成是否曾达到60K或提前EOS；不把缺失写成正常。

原客户端累计50条真实`ClientTimeout(total=7200)`错误，最终有11条`Single request failed`异常转None警告；适配器随后把这11个失败任务写为TIMEOUT占位。50是超时尝试事件数，11是最终占位唯一题数，二者均不能替代HTTP总尝试数。本轮无wire捕获，不能补报未观察到的HTTP错误状态码，也不能将客户端total timeout归因为网络断开。完整服务新byte/inode窗口没有NaN、非法访存或RPC错误，服务保持同实例健康，尚未证明BF16或完整MoE导致数值回退。

本轮专用CPU审计命令按上述SHA仅执行一次成功，原88个manifest成员大小/SHA、原终态日志副本及其源前缀/新窗口均一致；另存93份已有原件/日志前缀，补齐原manifest生成后才出现的FINAL_SUMMARY、FINISHED和controller尾部，未改原件。新增`diagnostics/cpu-terminal-audit-001/`内100个文件及93条source prefix均独立回读通过；完整187份解析API对象/token另存`parsed-API-objects.jsonl`。三canonical `/opt`源码、三repo HEAD/index、engine、bootstrap、模型/tokenizer元数据source-before/source-after/当前完全相等；同一Host API1693692/start537709560/argv SHA c146e2da绑定，health200、running/waiting/KV/preemptions均0，BF16、既有PLE/QSA/Gems/MoE修复全部保留。沿用eng066的all8实际入口及capture/replay短题证据，仍无本轮逐题/逐层QK、state、logits或逐rank kernel trace。

原始证据（均相对本页CASE）：

- 原生results：`results/Qwen3.8-Flash-Next-ppu07-acc019-c64-full-moe/671ace879860406e8f4efeaa2ef4d829/gpqa_diamond_generative_cot/Qwen3.8-Flash-Next/results_2026-10-22T17-37-15.773821.json`，SHA `6441924f5d9d1cdc522a7f21042c93272e436feaf3fb3589b9bf4df4b31daba0`。
- 同目录samples：`samples_gpqa_diamond_generative_cot_2026-10-22T17-37-15.773821.jsonl`，SHA `ea1f0583bb9b1a740e6d61354dc061fdb39c8a55faff1684f1662fb83682afb3`。
- 原summary SHA `66508e546b44f81f64d1c9c9fee33a00d37967841a76c92755746e63418b2a2a`，原manifest SHA `b880002cf9fb4a37810ba5f31361e57441ea9aa8226425e13c26e2b052cf21a1`；原终态日志在`diagnostics/terminal-evidence-001/`。
- CPU审计`diagnostics/cpu-terminal-audit-001/report.json` SHA `454578fe95a9f52e70c555d04fbb843c81d6317815fa022213c0946f2974e712`；manifest SHA `37f1b8f36b07388eec48cbe43cc4b028453b7cfeb7db42fd3a4380d2e5165f85`；回执`AUDIT_FINISHED.json` SHA `a4529558490dcd535ba4bb1118065f76e50f7196019e5ca2815109922c9496f7`。

按`inference-accuracy-diagnosis`冻结`acc019-formal-score-below-threshold`，分类为有效正式低分伴请求超时观察；原因未隔离、没有复现/代码修复/回退或FP32对照，不恢复性能优化。历史acc018176/198和acc017177/198的软件组合不同，不能直接归因为BF16或MoE单一变化。monitor `qwen3-8-ppu07-moe-c64-gpqa`已由产品工具确认`deleteStatus=deleted`。保留当前BF16 8010等待用户方向，无额外推理/GPU测试/源码改动/8035访问/提交推送；旧acc015/016及eng066最小回归结论保持原样。

## 11题超时的已有证据定位（2026-10-23，只读分析）

用户另行授权仅分析既有证据，判断与完整`fused_experts_impl`切换的关系。使用本地`inference-accuracy-diagnosis`，调用链收敛到具体MoE后按`key-operator-analysis`核对真实来源、配置和编译产物。没有重启/重跑/新推理/GPU工作、源码/采样/缓存变更、8035访问或提交推送。以下是CPU日志/样本/源码分析，不是新增性能测量或有效B/C/R结果；原正式结论仍为`failed-score`，不签gate。

### 直接触发机制：单次API总时限，不是已证明的网络断连或服务崩溃

冻结的`diagnostics/first-timeout-evidence-001/api_models.py`（SHA `493c667142263338f93894adf5638403269081b8329579eac1a64eda70383720`）显示：先取得C64 semaphore，再进入最多3次总尝试的重试循环；`ClientTimeout(total=7200)`覆盖每次HTTP请求及完整响应体读取，不包括客户端等待semaphore的时间，但包括服务排队/生成/传输。第一个超时恰在首批请求开始7200秒后。`sent request`日志位于`session.post`返回headers之后，不是可靠的派发起点，不能据此补造各题完整重试时间线。

`asyncio.gather(return_exceptions=True)`等待所有任务后，将11个最终异常转成None，后续再写成`<TIMEOUT>`。50条真实超时事件和11个最终占位doc不是同一种计数；占位也不表示收到空content。11题均缺完整返回对象/token，无法确定各次尝试已生成多少token、是否达到60K或提前EOS。服务日志持续生成到尾段，终态同实例健康空闲、preemption0，新窗口无NaN/非法访存/RPC错误；没有服务整体挂死的正证据，也不能仅凭这些日志彻底排除网络或主机侧贡献。

### 这些题原本已是长推理，新的超时不是11个全新困难题

按198个处理后`doc`内容逐题核对，acc018与acc019完全相等。以原生strict行去重，11题的旧响应如下（token为旧轮次实际返回usage，不是推测本轮未返回长度）：

| doc | acc018 completion tokens | 旧finish | 旧strict正确 |
|---:|---:|---|---:|
| 32 | 58262 | stop | 0 |
| 48 | 43741 | stop | 1 |
| 71 | 60000 | length | 0 |
| 88 | 60000 | length | 0 |
| 90 | 60000 | length | 0 |
| 121 | 60000 | length | 0 |
| 127 | 60000 | length | 0 |
| 130 | 60000 | length | 0 |
| 145 | 60000 | length | 0 |
| 147 | 60000 | length | 0 |
| 185 | 49542 | stop | 1 |

8题旧轮次已达到60K上限，另外3题也用了约4.4万–5.8万token。旧60K题doc164本轮反而43704 token正常stop且答对，不能把旧9个空final占位和新11个真实超时当作同一异常。

198题strict转移为：172题均正确、20题均错误、4题对→错、2题错→对。4个丢分题中48/185本轮超时，21/186正常返回但答错；81/164变正确。因此176→174的净变化在计数上对应48/185两个原正确长题超时，另外两对得失相抵；这不是数值等价证明，也不能把其他答案变化归为某个kernel的数值错误。

### 切换后生成变慢：相邻短题与正式日志提供相互支持

最接近的旧入口记录是`environment/env-065-flaggems-vllm-routing-20261022/model-regression-001`（记S），新完整入口为`engineering/eng-066-thead-full-moe-entry-20261022/model-regression-001`（记F）。两者使用同一doc2、原seed/采样、2C1后8C8；取第二C1，排除首C1的首次JIT影响：

| 已有记录 | S：分步入口 | F：完整thead入口 |
|---|---:|---:|
| 第二C1返回token | 517 | 580 |
| dispatch至完整返回 | 25.2552 s | 84.1167 s |
| token/上述总时长 | 20.4710 token/s | 6.8952 token/s |
| C8整批返回token/整批时长 | 5124 / 221.5134 s | 4641 / 212.0799 s |
| C8整批折算 | 23.1318 token/s | 21.8833 token/s |

C1归一速度约低66.3%，但C8整批折算只低约5.4%；C8原生service日志还会因在途数量变化出现不同窗口速率。输出长度/序列也不同，这些不是固定token稳态性能验收，不能泛称全部场景慢3倍。它们仍表明：慢速尾段在GPQA及重试之前已出现，不能仅用本轮重试或7200秒设置解释。

S/source-after与F/source-before比较：FGVLLM_src、native_graph、model_metadata、tokenizer和weights清单相等；Plugin仅路由实现和对应测试不同；Gems另有common_slot_mapping、alignment及导出清退。后者是旧路径清理，不能静默称为完全单变量A/B。已核实际S为Plugin `TritonExpertsFL`分步调用FGVLLM通用alignment/invoke，F则all8真实Plugin apply栈进入FGVLLM thead完整`fused_experts_impl`，不是仅包级导入差异。

正式服务日志也支持明显慢速：按`Avg prompt throughput=0`、`Waiting=0`、`generation throughput>0`筛选，驻留64请求时，acc018的78个窗口中位979.1 token/s，本轮290窗口中位345.6；驻留1请求时旧24窗口中位20.4，本轮124窗口中位6.9。未筛prompt处理的所有C64窗口中位则为703.75与339.2，两种口径不混用。日志是约10秒聚合、请求长度/时序不同、历史环境也有差异，且旧单请求集合包含少量短护栏窗口；仅作诊断观察，不是同配置性能收益或纯GPU时间。

以本轮尾段约6.9 token/s作量级估计，60K生成约需8696秒，已超过单次7200秒；这说明原有长推理在新慢速路径下容易超时，不是对11题实际未返回长度/各次耗时的复原。187个已返回对象中最长43704 token，已有成功长响应耗时约6872秒，接近时限。服务生成计数还包含未成功返回的尝试，不能将它们当成保存下来的API token或据此恢复11题内容。

### 已定位的实现差异与尚未隔离的成本

旧Plugin分步路径调用vLLM的`try_get_optimal_moe_config`。旧acc018和更近的S日志均明确提示目标`E=512,N=80,device_name=thead.json`不存在，实际用vLLM默认配置；不能因为Plugin目录有其他E/N配置文件就声称命中。F完整实现调用thead库内自己的选择器，`get_moe_configs`直接返回None，不读上述vLLM配置。

对本轮plain BF16的小M，源码可确定的默认差异如下；BM/BN/BK是tile参数，不是请求数：

| M / GEMM | 旧vLLM默认 BM/BN/BK/GROUP/warps/stages | 完整thead默认 |
|---|---|---|
| M1 / GEMM1 | 16/64/128/1/4/4 | 16/256/64/8/4/4 |
| M1 / GEMM2 | 16/64/128/1/4/4 | 16/128/32/8/4/4 |
| M64 / GEMM1 | 32/64/128/1/4/3 | 16/256/64/8/4/4 |
| M64 / GEMM2 | 32/64/128/1/4/3 | 16/128/32/8/4/4 |

完整实现还引入受可用内存门禁控制的权重转置缓存（最多4项，`permute_copy`生成转置），不同小M的naive/GEMV/SiLU融合分支及独立GEMM2选参。多层权重与小缓存可能产生重复转置成本，但缺少实际内存门禁状态/命中率/每步执行计时，不能宣布它就是唯一根因。既有pin047只约束生成的Inductor配置，不会把两套手写MoE选参强制变成相同配置。

来源证据位于F的`cpu-terminal-audit-001/compiled-and-source/15-fused_moe_utils.py`（SHA `e787cdb8e5f09ef9d41d194bc2c9b563ad6445bd4323210225af1d5103f8fe6b`）及`06-fused_moe.py`（SHA `807d12ce829343bcd4ef72e809d5c772dd9be4095db6e77adcaacd7810ca0f7e`）。本实例既有Triton缓存中存在17份vendor `fused_moe_kernel`、2份`fused_moe_gemv_kernel`和1份`_permute_copy_kernel_3d`编译元数据，支持实际实现家族发生变化；数量是编译变体，不是执行频次、逐题trace或成本占比。旧源码/运行日志和原raw/token均保留，本次不重新编译或执行kernel。

### 诊断结论与停止边界

直接失败机制已确认是客户端单次7200秒total timeout及原生异常占位转换。最有力的已有解释是**完整MoE入口改变了实际实现和选参，生成速度回退，叠加原本长推理使请求超时；原客户端重试又增加了重复计算/整轮尾部耗时**。相邻第二C1、全量服务日志、旧长题分布三者支持与入口切换存在明显关联。服务崩溃、NaN/非法访存、BF16重新变化或11个新数值错误均没有正证据。

尚未完成严格因果隔离：历史组合不完全一致、温度1输出不同、没有同配置B/C/R、每kernel trace/计时、转置缓存状态或11题未返回token。故将“完整MoE性能回退为强嫌疑/主要解释”与“具体tile/转置/分支根因未证实、数值差异未隔离”分别记录。不能仅延长timeout就宣称修复，也不在本授权下回退入口、补测或埋点。当前保持BF16及完整入口服务原状，等待用户方向；本次知识增量仅记录在本案例，不把未隔离的性能归因推广为通用PPU结论。

复核方法：原生samples按文件物理换行解析（不使用会拆开合法U+2028/U+2029的`str.splitlines()`），以strict/doc去重并比较doc内容和usage；S/F的`events.ndjson`按seq匹配dispatch/complete；服务日志使用上述冻结筛选条件，源码只做文本/AST与SHA核对。一次临时样本读取曾因Unicode分隔符误拆行而JSON解析失败，随后按维护工具的物理换行规则只读重读通过；不是原生样本损坏或模型故障，未修改任何原件。

## MoE选参与转置缓存继续定位：执行前记录

用户继续要求分析具体回退位置，仍不重启或重跑全量GPQA，不访问8035。本次继续采用更窄的CPU-only已有证据分析，不发任何新推理/GPU测试或修改生产源码。拟排他保存`CASE/commands/acc019-moe-config-transpose-analysis-001.py`，SHA `e3fc651a13aaa8aa3dbff7e2074e95c25819c8d918619d501669d8bb114f9b24`，仅执行一次`PYTHONDONTWRITEBYTECODE=1 python3 CASE/commands/acc019-moe-config-transpose-analysis-001.py`。排他输出`CASE/diagnostics/moe-config-transpose-analysis-001`，拒绝覆盖或重复目录；读取冻结源码/graph wrapper、原S/F私有Triton缓存的metadata/IR及模型配置/权重文件头，纯CPU隔离AST重放selector和4项缓存（不导入torch、不执行permute kernel），保存输入SHA、配置矩阵、条件流量估算与限制。已有原件、当前服务和缓存均不改。

### 阶段结果：首要嫌疑收敛至4项全局转置缓存，选参是第二独立变量

上述CPU脚本已按SHA排他传输、仅执行一次成功，报告`diagnostics/moe-config-transpose-analysis-001/report.json` SHA `a0ee43eed3f8d951b71c3440035d5418f44252c2ee6259c0cb1ba07694555144`，manifest SHA `1e33b386aef86dbb90a19cbebd1b4ceffb8933b5ccd0e397663772bd1a87ded8`，`FINISHED.json`齐全；报告/manifest、6份Host输入及75份容器侧来源的SHA/文件头均独立回读通过。容器来源包括现有源码、IR/metadata、模型配置/index和仅文件头的权重元数据，不读取全量权重字节。本阶段没有生产函数替换或GPU执行。

**缓存容量/生命周期机制已CPU复现，不再只是看到源码后的泛泛猜测：** `_thead/ops/fused_moe.py:1667–1707`的`_TRANSPOSE_CACHE_MAX=4`是整个模块共享的4个张量条目，不是每层4个，也不是4组所有专家层；每层先访问w1再w2，miss时对完整`(E,N,K)`调用`permute_copy`，满时按插入顺序弹出。模型配置为48个语言层、512专家、topk10、H2560、I640/TP8，推导每rank w1=(512,160,2560)、w2=(512,2560,80)。原始safetensors文件头确认未切分的gate_up=(512,1280,2560)、down=(512,2560,640)，与该TP推导和旧日志N80一致；未伪称读取了当前进程的Tensor shape。

隔离执行冻结`_transposed_view`函数AST，仅把import/张量复制换成纯CPU对象mock，保留原key、weakref、容量与淘汰流程。96个稳定存活权重对象按48层顺序轮转，三轮均96次查找/96次copy miss、最终4项；相邻步没有复用收益。因此“再预热几轮就缓存住所有层”被此机制反例否定。模拟不包含真实内存门禁/驱动/graph对象，不称实际进程miss计数。

每rank每层w1为400MiB、w2为200MiB；如果全部48层每步都miss且复制执行，则每步复制payload为28.125GiB、仅读原权重＋写转置结果就有56.25GiB逻辑流量，还未计GEMM读和临时访存。这是带条件的静态流量模型，不是实测带宽/时间。仅将缓存改成能存全部96项也不是无代价修复：会额外长期保留约28.125GiB/rank，可能破坏当前显存/KV预算；不在本任务中修改上限。

**转置实际分支证据比上轮更强：** 原S缓存14个generic GEMM变体均保留`stride_bn`运行时参数、`stride_bk=1`被特化；F缓存17个vendor GEMM和2个GEMV变体均反过来，`stride_bn=1`被特化、`stride_bk`为运行时参数。结合host转置view的stride `(K*N,1,N)`，支持这批实际编译变体使用转置权重，而不是只有一份孤立permute编译产物。F变体从17:38的启动阶段一直延续到本轮GPQA18:30/18:32/18:35的新shape；不能仅用“可能一直被10GiB门禁禁用”解释已有产物。1份permute kernel本身编译时间17:38:47，同一kernel支持多shape，不表示只有一次转置。

**Graph边界必须保留：** native `CUDAGraphWrapper`在capture时执行runnable，之后直接`entry.cudagraph.replay()`；FULL replay不会每token重新执行Python缓存查找或`mem_get_info`。如果层间miss发生于capture，发出的整权重复制kernel可能作为graph节点每步重放，所以“Python只capture一次”不等于“权重只复制一次”。但当前没有保存graph节点dump、命中率/门禁状态或逐kernel计时；IR不能证明具体FULL graph内96个copy节点全部存在，也不能直接给出实际复制频率/成本比例。首要嫌疑为**缓存容量不匹配导致复制无法跨层保留，可能把重复全权重转换固定进graph**，尚未达到性能因果confirmed。

### 选参的具体不匹配与反证

CPU提取并重放旧vLLM默认函数和当前vendor默认函数（无生产模块import），保存M1/2/4/8/12/13/16/32/64/128/512/1024/4096/8192及G1/G2矩阵。默认函数所注释的历史PPU sweep不等于已对本模型TP后的I80验证。具体Decode路径：

| 条件 | 旧分步 | 当前完整入口 | 机制观察 |
|---|---|---|---|
| M1 G1，实际N160/K2560 | BM16/BN64/BK128 | BM16/BN256/BK64 | N方向旧3×64=192列槽，新1×256=256列槽；有效占比83.3%→62.5%，K迭代20→40，但不是耗时比 |
| M1 G2，实际N2560/K80 | BN64/BK128 | BN128/BK32 | K填充反而128→96，不能说所有新tile都更差 |
| M8 G2 | 通用MMA | naive且80 routed rows、N2560，满足vendor GEMV guard | M1 routed rows10不满足；可解释C1/C8分支不同，但未独立量化 |
| M64 G1，融合后每半N80 | 旧非融合BN64处理总N160 | 融合SiLU、gate/up双accumulator，每半BN256 | 每半N有效占比仅31.25%；BM32→16又可能减少expert行填充，需完整调用比较 |

新小M G1编译metadata的shared为104448B（102KiB），旧M1 generic G1为61440B（60KiB），旧M64 generic为49152B（48KiB）。资源占用增大是可核验事实，是否减少PPU驻留、是否成为耗时主因尚未测。新G2 metadata为27648B（27KiB），并非整体资源都增加。GROUP8在M64/E512稀疏专家分布下不保证权重复用；不能只从BK循环数或tile填充推导端到端加速比。

当前M1/8是naive、不融合SiLU；M13起才可进入alignment＋融合G1。direct_sum阈值仍1<<60，没有开启，不能把新增atomic归约当此轮根因。BF16权重/激活和TP归约未改变，TLE平台/零extent修复也不在本次新增路径差异之中；不回退已有修复来“排查”。

### 当前优先级、反证与后续验证边界

1. **优先隔离转置缓存。** 当前已有CPU复现、实际转置布局IR和数量级足够大的条件流量。最窄后续设备实验应保持完整入口、路由与所有修复，只对比原样转换/关闭转换（或明确预算的一次性预转换），先完整MoE数值和changed-input graph，再交错短固定shape计时；不能同时恢复旧tile，否则无法分辨贡献。本轮未执行这些GPU实验，也未申请或执行重启。
2. **再隔离MoE配置。** 在转置策略相同后，才比较旧G1选参/当前G1，保持G2与共享alignment BM兼容；小M含M1/8/12/13/64，大M另测Prefill。M8的GEMV和M64的SiLU融合须独立记账，不能把旧新配置字典相同视为所有kernel相同。
3. 当前阶段只确认缓存机制和配置/布局差异，性能贡献仍`not-proven`，正式精度仍174/198 failed-score、无新gate。不得自动放宽7200秒、补跑GPQA、实现修复/回退、做在线probe或签发性能收益。

知识差量`refined`：先前只知道“完整入口改变了tile与转置”；现在确认4项模块级缓存无法容纳96个稳定权重、单步条件复制量达28.125GiB/rank、现有全部MoE变体为转置布局，同时区分FULL graph的Python执行一次和device copy可能重复。下一首个证伪从泛调tile收敛为单变量转置策略；不更新稳定README或宣称所有PPU模型都存在此问题。当前服务/源码原样保留。

后续用户明确授权的[op067独立算子/graph对照](op-067-moe-transpose-ab.md)已完成：固定选参/修复、只在新微测进程开/关自动转置，两组B/C/R稳定复现额外成本；数值/graph和完整CPU审计通过。该证据把冷缓存单层完整算子的转置策略代价从嫌疑升级为限域reproduced，但没有当前模型graph节点/在线切换、端到端或新GPQA，仍不能宣布本轮11超时已解决；acc019原分数/gate/服务不改。
