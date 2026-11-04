# accdiag-016 GDN 状态索引、清零、写回与 graph 首异常取证

后续当前服务与修复状态以[accdiag-017](accdiag-017-index-i64-fix.md)为准：用户已批准后实施i64地址修复并仅恢复8010，新局部受控回归运行中、monitor ACTIVE；下面的“退出/暂停”仅描述14:17旧事件，不表示当前恢复失败。旧128结果与大索引首次捕获均保留。

- 局部128请求终态：12:48完成128/128，全部正常，generic最大20536、20972未覆盖；原冻结和结论不改写。
- 后续新事件（14:17）：用户另行授权的一次全量GPQA [acc-013](acc-013-full-gpqa-c64-diagv3.md)在同一实例首Prefill实际generic index23520/stride102400触发i32地址溢出保护，8rank状态已保全，服务退出；执行前guard不是新device非法访问，reasoning-only因果仍未隔离。本轮原采样前缀/事件日志在旧runtime002继续追加，但新的正式证据/起始offset与失败回执属于acc013，不能把旧FINISHED当它的结束。8010现已退出、monitor PAUSED，不自动重启或重跑。下文较早记录为历史快照。
- 分类：accuracy-diagnosis / execution-mode；Prefill、Decode、Mixed 状态生命周期，非性能优化。
- 授权：用户2026-10-16要求继续受控定位，保留首次异常索引、边界、原始回复及token；禁止全量GPQA，需要加埋点或重启先告知。
- 范围：PPU-07，`qwen3.8-flash-opt-ppu07-20261015`，8010，TP8物理卡8–15；0–7/8035属于其他任务，不触碰。

## 方向与既有证据

原acc-012因TP7非法访问结束，旧驱动指向 `_index_jit_function`；Python在GDN boolean clear后的nonzero同步点报错，不证明nonzero是首故障。此前188小池及84项N6000微测通过；N22000资源门禁未分配。24请求C1→C8→C1与128请求局部C64均未复现原模型症状，后者有客户端日志事故造成的分发间断。旧127/198故障污染结果不改写，无有效gate，性能晋级仍阻塞。

本轮先核查服务身份、负载及当前源码，对GDN gather→clear→recurrent/chunk→scatter与graph metadata的生命周期逐项列出不变量和取证缺口，不盲目再发同样负载。用户未批准加埋点或重启前，不修改源码/运行环境，不附加调试器，不发送新推理或GPU测试。

## 取证内容与适用边界

待确认具体挂点后冻结：rank/layer/step、request→slot及复用generation、真实state索引与mask、shape/stride/storage_offset/storage大小、读写地址上下界、graph capture/replay key与persistent buffer身份。区分允许的padding NULL索引和真实请求非法索引；不能把整个包含padding的buffer简单判负即报错。

需按Prefill gather前/后、clear后、state计算后、scatter前/后与Decode graph replay逐段检查，明确每种路径的active mask、更新语义、布局及别名。设备异步非法访问后不能指望再成功读回索引，因此首次故障前的有界快照/环形证据和首次异常排他保存必须先设计；graph中的Python hook并不随replay再次执行，不能用capture日志冒充每步数据。

原始API请求/response bytes、完整token IDs、usage、finish/stop、think-end/EOS和完整服务日志分别保留；空content→TIMEOUT占位不当作真实HTTP超时。首异常停止新补位，已在途只收集不重试。确切请求scope/数量在获准取证方式后再冻结，不擅自沿用全量198或增加负载。

## 正确性与路径命中

本阶段只读，无新的最小回归、graph命中或数值通过声明。需要加埋点/重启时，先给出最小改动、graph影响、开销、回退和请求上限，由用户确认；vLLM源码保持只读。不能以无异常或算子小测通过宣称问题修复。

## 性能效果

不测性能，不计算加速比；任何同步/取证版本不作为正式稳态性能结果。

## 决定、风险与回退

当前服务保持运行；已有heartbeat保持暂停。只读审计完成后报告能证明与不能证明的边界，若缺内部状态证据则等待埋点/重启方向，不自动实施。没有代码修改因此无运行时回退动作。

## 外部证据

- 既有冻结：正式case的 `diagnostics/accdiag-015-c64-churn-large-index-20261015/terminal-freeze-001/`，report SHA `10eef46d1d79921fce2217c18b468a2f644f91633476192de600af2ba2662b29`。
- 本轮目录：`/mnt/nfs/users/jinghao/qwen3.8-flash/20261015-qwen38-flash-next-ppu07-container/accuracy/acc-012-full-gpqa-ppu07-c64-master-20261015/diagnostics/accdiag-016-gdn-state-graph-20261016`，仅CPU取证产物，无新模型请求。

## 只读取证执行前记录

09:33–09:35复核8010仍为API1290447/start ticks477285377，health200、running0/waiting0/KV0/preemptions0；累计prompt57509、generation1357285与上一轮冻结完全相同。Plugin939600b/FlagGems85cc5ef/FG-vLLM5865ed5及已知工作区修改保持；模型源码SHA3ae84180、runner2df8aa58、上游GDN97faa7ee与旧快照相符。没有推理请求或GPU操作。

将只读CPU脚本保存到 `case/commands/accdiag016-readonly-audit.py`，SHA `1e4c6dbea50e3accfedbb165056c35bfc5adbf2c571c7898cadcdba759e5a0e0`；命令 `python3 case/commands/accdiag016-readonly-audit.py --case case --container qwen3.8-flash-opt-ppu07-20261015 --api-pid 1290447 --start-ticks 477285377`。脚本核验实例/空闲，排他创建上文诊断目录，保存当前源码、相关index/packed已有编译缓存文本、固定前缀完整服务日志及SHA清单，不导入Torch、不分配GPU、不修改缓存或服务。已有缓存可能跨历史实例/硬件，不将缓存存在当作当前故障launch命中。AST检查通过。

补充CPU地址分析脚本保存为 `case/commands/accdiag016-address-audit.py`，SHA `a0ad155110eb165ea4787f09cf4bc4061afdc664ae1bdd3905f75570abb7e44c`；命令 `python3 case/commands/accdiag016-address-audit.py --case case --container qwen3.8-flash-opt-ppu07-20261015`。仅读已冻结IR、4份已存在的LLVM文本和正确路径的T-Head `nonzero_numpy.py`，计算i32/i64地址差异，写新 `cpu-address-analysis-001/`；不执行kernel，不修改模型源码或覆盖旧证据。AST检查通过。

## 只读结果：地址位宽假设升级为具体机制证据

09:38:10快照保留516份相关缓存文本、13个当前源码文件（14个请求路径中最初错误拼写的`nonzero.py`不存在，补充已保存实际`nonzero_numpy.py`），原始服务日志633703字节及活动恢复日志939592字节固定前缀。与先前快照重合的9个源码SHA全部相同。report SHA `93dfe336fc7f3fa249ede5df9624475d45a2ad1598ea5813c03bf354935b4d62`，manifest SHA `e144b494855deb67206a3d5ee9251333c8f175a6f7e47da67ae7b4f0fee022f9`，归档SHA `92b21ff0700783ecab29b1f2070d3c1f1eb2f20e1d404a6548975c640f3e2f6a`。服务仍是原实例，health200、idle，累计token不变。

当前Gems通用`index.py`与`index_put.py`生成器均直接计算`cur_index * input_stride`，未先提升索引。已冻结的PPU rank4/单索引IR包含39份i32 gather、14份i64 gather、12份i32 scatter、26份i64 scatter。它们包括历史实例及先前微测，数量不是调用次数，也不能按mtime直接判定线上命中。抽查保全4份完整LLVM；i32 gather在LLVM仍是`mul i32`之后`sext`，并非仅TTIR打印形式或已经自动修复的i64乘法。

CPU按整数语义计算：

| row stride（元素） | 首个行起始乘法i32溢出的索引 | 示例索引 | 正确i64偏移（元素） | i32乘法后符号扩展偏移（元素） |
|---|---:|---:|---:|---:|
| 98304 | 21846 | 32893 | 3233513472 | -1061453824 |
| 102400 | 20972 | 32893 | 3368243200 | -926724096 |

FP32下该示例地址相差−17179869184字节（−16GiB）。更高的索引如50210可绕回正偏移，因此该条件下可能是错误位置读写而不一定立即非法访问。索引`<num_states`本身并不足以排除此乘法溢出；需要同时检查地址计算位宽与完整storage边界。这是**给定i32索引与stride条件下的机制/算术证明，不是原线上故障的最小复现**。

原driver保全了`_index_jit_function`、寄存器中的`0x19000=102400`/`0x18000=98304`/`0x10576=66934`；形态与padded FP32 GDN state兼容，但未完成故障二进制ABI反解，不把寄存器值直接当成已实测tensor metadata。故障scheduler dump含3个新请求及多个超过20972的block ID（例如50210/32893/22497）；尚未证明其cache-group→GDN layer映射，更未拿到对应GPU索引tensor或唯一fault launch hash。驱动只显示末尾反汇编片段，不能据此反推全部地址指令。

因此把“高block-ID地址位宽”提升为首个待验证变量，**不先改清零逻辑、不先归因graph**。此前N6000微测未跨此边界，N22000又未分配，均不能否证本假设；但也不能凭此断言原始reasoning乱码一定源于它。

地址分析原生报告 `cpu-address-analysis-001/report.json` SHA `a0f9de8f03c61d922d528b07df0e5031a08ebb566444a445a43d2d17d5e920e2`，manifest SHA `cfeb71fac227393c9ba9114d30ccc8f4fceaf827da616e81a8cc5b75dfaa8964`，保留4份LLVM、完整driver异常和原scheduler dump。

## 四条路径的取证位置与不能混淆的语义

| 路径 | 当前源码事实 | 需要捕获的不变量 |
|---|---|---|
| Prefill gather | 上游GDN1513：`ssm_state[prefill_state_indices]`；非连续输入可能落到通用generator | 原始GPU indices、dtype、group/layer、真实storage/stride/offset、i32与i64地址差；不能只看index范围 |
| fresh-state clear | 上游GDN1514清零的是gather出的临时state，不是直接把全局pool都清掉 | `prefill_has_initial_state`与请求顺序一致；false行全零、true行与gather输入相同；先gather后clear的故障边界分别记录 |
| Prefill scatter | 上游GDN1532把chunk final state写回同一pool索引 | index与gather逐项相同、无不允许的有效slot重复；写回值/布局与源相符，相邻padding/其他state不改变 |
| Decode graph | 模型shim1670–1700调用packed原地更新；Gems kernel先转i64且跳过`idx<=0`或`idx>=NUM_STATES`；metadata builder复制real indices并把padding填NULL0 | real slot越界不能被NULL padding掩盖；每次replay的device内容而非capture值；pointer/generation及request→slot一致 |

runner Mamba allocation通过`as_strided`按page组织conv/SSM等子view，row stride不必等于逻辑state元素数。因此不能用contiguous proxy、只有shape的记录或逻辑`numel()`作为合法存储边界。GraphWrapper仅在debug模式比较传入args的pointer，不能代替内部metadata/state的逐步值证明。缺少KV-zeroer接线仍是独立静态缺口，不证明本次清零失败。

## 下一阶段方案：需先批准，尚未部署

为取得用户要求的“首次异常索引/边界”，需要任务私有Plugin/Gems诊断埋点，并**仅重启8010一次**使所有8个worker加载；当前运行进程不能靠修改磁盘源码得到可靠、一致的热更新。vLLM、权重、tokenizer、采样和其他服务保持不动。实施前保存当前diff/真实import/源码SHA与启动参数，准备去掉诊断补丁后恢复原启动的回退；不在本阶段同时加i64修复，避免把观察与修复混成一个变量。

计划内容（实施前还需冻结具体实现、显存上限和请求清单）：

1. Plugin每步记录request ID/slot generation、KV group、rank/layer/step及graph descriptor，跟踪batch重排/完成/补位，不只记录doc ID。Gems/模型边界记录真实index/mask、shape/stride/storage_offset/storage字节数和原始地址计算位宽。
2. Prefill gather前保存完整小索引/mask及可重建地址边界；若发现越界或i32/i64地址不同，先排他冻结现场并停止新派发，不为了复现非法访问故意继续危险读写。按首次可疑slot保存必要state输入/输出，不逐步复制整个pool。
3. graph内部使用预分配的有界设备证据/异常flag，外部step journal关联每次实际replay；普通Python hook只在capture执行，不能冒充replay取证。区分真实请求和NULL0 padding；duplicate slot、fresh mask错配、pointer复用代次及相邻区域保护分别检查。调试同步会改变时序，单列此限制，不拿调试版测速。
4. 客户端保存精确payload、原始HTTP bytes、完整返回token IDs、think-end/EOS/finish/stop；为服务崩溃场景另设计rank0已采样token前缀的增量保全，不依赖请求成功结束才落盘。若故障导致完整回复根本不存在，报告实际前缀/HTTP失败，不伪造最终回复或token。
5. 总请求上限拟保持128（包含C1/C8控制），最高C64持续补位；具体scope/SHA及控制顺序在实施前冻结，不超过用户先前128范围。首次异常停止新补位、在途仅取证、不重试、不自动恢复服务、不重跑198题。没有内存余量则停止本阶段，不减服务显存或侵占其他卡。

当前未部署埋点、未重启、未发请求或GPU微测；原heartbeat保持暂停。等待用户确认上述埋点/8010诊断重启范围。机制证据已增强，但原故障launch、reasoning-only因果与graph复用根因仍未隔离。即使后续局部修复通过，也须另行获得原正式契约的有效gate才能恢复正式性能优化。

## 用户批准后的实施契约（部署前冻结）

用户随后明确批准仅8010加诊断埋点并重启，总请求≤128/并发≤64，不影响其他服务、不跑全量GPQA。09:48复核仍为原API实例、idle及累计token不变；目标容器只有8010的推理进程，唯一mount是`/mnt→/mnt`。因此代码复制到容器私有`/opt/qwen38-accdiag016-20261016/{plugin,gems}`，不覆盖原代码和site-packages，原已有修改逐文件保留；以仅该服务的PYTHONPATH选择私有副本。vLLM源码、模型/采样/graph参数不变；Gems生成代码和vLLM编译缓存改为任务私有目录，冷编译成本及诊断同步不作为性能结果。

埋点归属：Plugin模型shim包围原GDN core并注册实际pool/metadata；Plugin runner记录step/request绑定和原sampler返回的token前缀；Gems仅在packed wrapper前后插入预分配的只读状态/索引取证kernel，不修改原更新kernel。通用gather/scatter在其真实generator入口记录实际operands，危险地址在原kernel执行前冻结并拒绝执行；不是i64修复，也不故意制造非法访问。预分配证据≤64MiB/rank、首次状态冻结≤128MiB/rank，低余量停止；graph捕获中不初始化counter或CPU同步，实际replay计数由设备取证kernel更新。state快照覆盖每层最大有效index的前后整行；首次异常额外保留实际可疑/目标请求及有界选中行，不声称完整pool或全部中间张量。

原采样seed1234/temperature1/top_p.95/top_k20/min_p0/presence0/repetition1/stop/max60000保持。总128由C1同一控制请求两次、C8固定8目标、C64持续补位118组成。C64选择前轮102条较长背景和8目标早晚两次（102+16），将长背景前置以增加活跃长请求/高block-ID覆盖，属于显式到达顺序差异；不与前轮或正式负载等同。0重试，8小时停止补位预算、请求HTTP超时7200秒，首异常停止补位，在途只取证，服务异常不自动重启。

执行文件保存到`case/commands/`：`accdiag016-controller.py` SHA `537776a47f5519a44c8ecfc8742d9001d7522a4306548ff989f2223a2cf26a15`；`accdiag016-diag.py` SHA `34a398bf6c51bde0e1d9924de93002ca1a342fd329b314e85fe36a41a0fe4a6a`；模型副本`accdiag016-model.py` SHA `2c36d1c3334d910c50be8c54e5337808fe8f2f02e3e01d7107a532875b3a184f`；runner副本`accdiag016-runner.py` SHA `c3537353ca6cdf7e94d206117d0935b07ca8a5b1a3a69420b00510be926f9b28`；Gems wrapper副本`accdiag016-gems.py` SHA `c26c35115ce84f61a5d8c7999982d3cf8b46bd0448354717768d28efe8b7732d`。AST五文件及真实bounds函数的两种stride溢出边界/i64对照通过，硬件验证尚未执行。

控制器先`--mode prepare`（校验原实例/空闲/其他8035 listener不变、复制源码、冻结请求清单），再`--mode restart`（仅对身份校验的8010 API发SIGTERM，等待其已记录后代退出，不按进程名杀、不动容器和其他服务），准备与ready产物排他保存到`.../runtime-001/`。readiness后才`--mode start-client`启动唯一`--mode run`客户端；重复marker拒绝再次运行，所有请求共享同一128计数。每一步均带`--case`原正式case绝对路径。重启或首次请求前若检查失败，保留证据并停止，不扩大范围。

prepare已完成：128请求清单SHA `9247cf98f91645b5b4d8513117d106248fb96da03ef9efbca793a60ea6743c2f`，原源码复制逐文件SHA一致后才覆盖私有副本的3个入口文件。CPU导入预检确认diag、Plugin和Gems均解析到`/opt/qwen38-accdiag016-20261016`，未执行GPU算子，原8010未动。

重启前补充graph descriptor/runtime mode/graph object ID及非有限flag冻结字段，保留旧模块而新增`case/commands/accdiag016-diag-v2.py` SHA `119920bb3a6bef7904798be482a899380942d7196378bcd3310dd1eee816b9df`。AST通过；执行`docker cp`仅更新尚未启用的私有`/opt/qwen38-accdiag016-20261016/diag016.py`，保存`runtime-001/PRELAUNCH_UPDATE.json`说明superseded SHA34a398bf→119920bb。没有采样/索引语义改动或额外请求；worker安装日志将记录实际模块SHA。

10:09仅8010旧树已退出，新API Host PID501780已启动，启动日志显示私有Plugin路径及原FULL_AND_PIECEWISE/TP8/seed0/prefix-cache false；T-Head native-extension缺失告警与原服务相同，不是副本引入的新fallback。原控制器在docker exec -d返回后立即读尚未建立的service-diag.log，触发FileNotFoundError结束等待；这是控制器日志创建竞态，不是模型异常，不重复启动或重启。原失败脚本保留。

就绪接续脚本`case/commands/accdiag016-wait-ready.py` SHA `8cacd70c4b4c865085b0e618c0b3aeeb92f30657a62ea38f224c03a8a82c12a5`，AST通过；命令`python3 case/commands/accdiag016-wait-ready.py --case case`。仅只读等待现有新实例，核对8 worker实际埋点SHA与8035不变后写READY/service-identity；无kill/launch/restart/推理能力，不会使总重启数变成2。原controller事件写入readiness-controller-incident.json，客户端尚未启动，推理请求0。

CPU钩子测试`case/commands/accdiag016-cpu-hook-test.py` SHA `59c8c884f33ba79b371397e14c72175ba85bdaeb1ca00a19918463b532cfdb70`，AST通过。以私有diag导入路径、独立`runtime-001/cpu-hook-preflight/`证据根运行，CPU小padded pool上用fake generator核验gather/clear/scatter/padding及执行前拒绝越界；mock掉CUDA同步/捕获查询，并断言无CUDA context初始化。测试故意产生的FIRST_ANOMALY位于cpu-hook-preflight，不是模型运行异常，不与真正runtime目录合并。

就绪门禁进一步按真实生命周期收紧：model类注册发生在TP初始化前，安装header可能落在rank-1共享日志；每rank的`device-evidence-buffer`只有模型wrapper和Gems wrapper实际命中才能产生，故结合该证据与runner实际模块SHA核验8 worker，而非要求model注册header出现在rankN。只读接续v2 `case/commands/accdiag016-wait-ready-v2.py` SHA `6bb100466c61748056f1c960c0800ffbafad4afaf1693f4725ae9e2f3f55cdf1`，保留旧检查器文件/marker；仅对其marker内PID核对完整命令后结束旧只读checker，接续v2，不停止或重启模型实例。请求数仍0。

## CPU预检失败：诊断代码自身异常，模型请求尚未启动

CPU hook test在预期的非法index拦截分支发现`TypeError: event() got multiple values for argument 'kind'`：`anomaly()`调用`event('anomaly', kind=kind, ...)`与原event形参kind冲突。它发生在写FIRST_ANOMALY/STOP标记后、完整state冻结前，因此该版本不能满足首异常状态保全要求；这是我编写的诊断日志bug，不能计作模型、HTTP或GPU异常。此前AST/bounds自检未覆盖该错误分支，测试执行顺序欠妥：应在停原服务前完成完整CPU hook测试。现在不启动任何推理客户端。

修正仅将日志函数形参改为event_name，新增外部`case/commands/accdiag016-diag-v3.py` SHA `e044c58d75f5716006310e247ae3e3f31e4d7c2effdd88811ff42c53acc914d9`，**不替换已加载worker内存，不热更新，不再次重启**。验证入口`case/commands/accdiag016-verify-cpu-v3.py` SHA `fce610e56051c7f4cc9e862f7d30127200c8d48a1d1df13a1ecc6725966dae3e`，AST通过；命令`python3 case/commands/accdiag016-verify-cpu-v3.py --case case`。它在独立CPU进程显式加载外部v3模块，独立cpu-hook-v3证据根保留stdout/stderr及预期人工越界的索引/状态，检查0 CUDA context；不改变当前服务或消耗模型请求额度。

当前实例已加载v2，若v3 CPU验证通过，仍须向用户报告需第二次仅8010重启，获确认后才继续；不把第一次冷启动当新模型故障，不自动恢复/重启。旧只读checker仅可按自身marker PID/完整argv验证后停止；无其他客户端、无正式GPQA。

v3 CPU验证exit0，gather/clear/scatter、邻接padding保护、危险index前拦截及预期人工异常的完整索引/状态文件保存均通过，断言无CUDA context；它不是设备/模型精度通过。回执`runtime-001/cpu-hook-v3/report.json` SHA `793fe3fa503ccaec5c080956a7c8482402097fa6012ea1dc4a2dac4a5a69d3d4`，完整stdout SHA `738157da9b80e36a10534771a2b400b4e42d5859dcb83dfc2a9e3902b511aa6b`、stderr为空。v3只位于外部commands，运行worker仍为119920bb版本，没有热更新。

已按marker/完整argv精确结束Host PID543940的旧只读checker，不是服务进程；v2 checker文件已准备但**未启动**。`CLIENT_BLOCKED.json`明确0派发，`RUN_STARTED`不存在。8035 listener与重启前完全一致，回执`other-listener-after-block.json`。新8010身份API501780/start ticks483237290、Engine513455及8TP worker存活；10:18:33前日志已完成FULL decode graph 7/7 capture，尚未完成本轮HTTP请求或两次真实控制replay，不能用capture当最小回归通过。服务仍保留，monitor保持暂停，不自行再次重启。

本轮执行中止点为**诊断观察器预检失败后等待额外重启授权**，不是模型复现失败/修复。没有正式198题、没有新分数/gate，旧故障污染127/198不动，性能仍blocked。对执行顺序的修正：今后必须在停止正常实例之前跑完实际异常保全分支的CPU测试，不能只以AST和边界算术自检放行重启。

最后只读核验：服务日志10:18:36明确Application startup complete，8010 `/health`返回200；客户端仍未启动。当前健康不等于取证版已通过，仍须修正observer后重新加载并执行原控制范围。

## 第二次仅8010重启：用户明确批准后执行

### 13:22终态回执：128/128正常结束，20972边界not-covered

本轮于2026-10-16 **12:48:18.729635+08:00**自然结束，开始10:43:02.797862，耗时7515.931773秒（2小时5分15.932秒）。原生FINISHED/progress一致：128派发/128完成/0错误/0在途，seq0–127逐条唯一，**110唯一doc**；范围为2条C1、8条C8、118条C64请求，不是正式198题，不产生新分数/gate。客户端已退出，但未留独立OS exit.code，不能补报exit0。

按inference-accuracy-diagnosis冻结原始证据并验证，而非把“本轮无异常”当作精度通过：

- 128份原始HTTP bytes与result SHA全部匹配，全部HTTP200、reasoning和最终content非空、finish_reason=stop、think-end248069存在、末EOS248046，完整API token数与usage逐份一致；错误、reasoning-only、空最终、length/60K cap均0，completion_tokens为243–54740。
- 两条C1 doc2完整tokens相同，均B/441tokens。C64早晚目标16/16正常。最后seq18/doc90为D/54184tokens、think-end位置53909；seq24/doc118为C/54740tokens、think-end位置54496；字母仅描述输出，不作正式评分。前面13:16阶段只先取到doc90长度，最终最长以doc118的54740为准。
- 8rank逐日志全量扫描：gather/scatter真实int32最大均**20536**，clear最大20；packed decode已记录的实际device indices最大**18856**（该路径原本i64），selected max也18856。实际generic索引距20972还有436，**危险边界未覆盖**，不能排除i32乘法溢出假设。
- 最大generic现场仍step28986、`layers.1.linear_attn` gather、pool shape[87529,6,128,128]、stride[102400,16384,128,1]、FP32、storage_offset1920元素、storage35851878400字节。index20536对应i32/i64行偏移均2102886400元素，字节地址差0，行区间[8411553280,8411946496)合法。不是溢出或非法访问的复现。
- 每rank6696个operator-post已检查行无mismatch；index/storage/overflow、设备非法索引/nonfinite、anomaly均0。每rank75046条FULL batch-binding记录，最终step75112，8worker诊断SHA均e044c58d；日志解析错误0。完整device indices仅在变化时记录，各rank180条，另74866条为null/未重复记录，不把null当空索引或独立覆盖。
- 全局/各rank FIRST_ANOMALY、STOP及first-state均未生成：无首次异常，故没有对应触发态dump，不能声称已得到首次异常完整状态。共享pool的有界last-writer快照仍不是36层独立state；rank0前缀仍为post-sampler/pre-bookkeeping，discard行未必发出，完整API token以各raw为准。

有效终态证据目录：

`/mnt/nfs/users/jinghao/qwen3.8-flash/20261015-qwen38-flash-next-ppu07-container/accuracy/acc-012-full-gpqa-ppu07-c64-master-20261015/diagnostics/accdiag-016-gdn-state-graph-20261016/terminal-freeze-002/`

其中`runtime-002/`保存128raw/128result、全部8rank日志及rank-1注册日志、原始采样前缀、FINISHED/progress/请求清单、客户端日志和完整当前服务日志固定前缀；`source/`保存实际私有4入口，`commands/`保留复现/冻结命令。311条manifest、2204608649字节，第二次独立逐文件SHA复核全部通过。`report.json`、`response-audit.json`、`rank-audit.json`及`manifest.json`的SHA如下：

| 产物 | SHA256 |
|---|---|
| report.json | e2bf24cd11569aa356d6504c7a34f497ed4ee024832e4c496e50245d8cfc65fc |
| manifest.json | 9e14e4b75f72709f6cdd978914ed4ae974cf817c16267b298c304bf52f104597 |
| response-audit.json | 60a30cc968fd9ea4d1e7ce51679b910716a23cee24721ec6247d887a10e0f0bb |
| rank-audit.json | e7cb2052750555002ab1768fac4daa9bf60064d7937f22a7783828bad3e72a9c |

首版freeze-001文件保留；其汇总helper对可空actual_indices处理错误导致无完整回执，不计为模型异常。有效回执来自freeze-002/v2；v2未改变任何运行源码/埋点，只做文件复制和CPU离线汇总。原Plugin327/Gems11433个源码文件SHA全部不变，私有4入口SHA均与本轮部署记录一致。

13:21:41服务仍API1325804/start483425629、health200、running0/waiting0/KV0/preemption0，累计prompt49133/generation1432467；只读冻结零推理请求/零重启。完整服务日志没有实际ERROR/Traceback/非法访问，宽泛关键词命中的仅启动期vllm._C缺失WARNING；旧11:11:56广播等待提示后一直推进。未单独采集host-wide driver/kernel日志，无新fault dump，不冒称完整全机驱动日志。0–7/8035未操作。

结论：**局部未复现，根因not-isolated，20972危险generic边界not-covered**。没有模型修复，也不能由debug同步及不同负载下正常结果推出原异常消失。原acc012故障污染127/198与无有效gate不改写，正式性能继续blocked。已通过产品工具确认原heartbeat `qwen3-8-ppu07-gpqa-c64` **PAUSED**；8010保留当前实例，等待用户方向，不扩128请求、不追加GPU测试、不恢复/重启服务、不改代码、不重跑全量GPQA。

### 13:16终态发现及证据冻结执行前记录

原客户端于12:48:18.729635自然写入FINISHED，原生progress为128派发/128完成/0错误/0在途；客户端PID已退出，API1325804/start483425629保持不变、health200、running/waiting0。无FIRST_ANOMALY/STOP/CLIENT_FAILED。两条最后返回为seq18/doc90最终D、54184 tokens和seq24/doc118最终C，均正常stop；具体完整token及8rank终态边界由下述冻结核验，不以早期126快照替代。

只复制已有证据的终态脚本预先保存为`case/commands/accdiag016-terminal-freeze.py`，SHA `770314f7e4b3a6e5427b881cb618d32c15a245a2e84eb1e8f6a2583a14d42507`，AST通过。执行命令`python3 case/commands/accdiag016-terminal-freeze.py --case case`，新建排他目录`diagnostics/accdiag-016-gdn-state-graph-20261016/terminal-freeze-001`，逐文件固定字节前缀复制原始HTTP/token、全部rank日志、完整当前服务日志及命令/源码并计算SHA；不导入GPU框架、不发推理请求、不修改或重启服务。独立全机driver/kernel日志未采集，不能称完整host-wide driver dump；无异常时不补造first-state文件。待冻结与校验完成后写终态回执并暂停原heartbeat，不扩请求范围。

首版冻结完成文件复制后，在离线rank汇总遇到`actual_indices: null`抛出TypeError；这表示该步未重复记录完整device indices，不是空索引，更不是模型/HTTP异常。保留freeze-001与原脚本，不冒充完整回执。兼容该字段并分别统计完整device indices和selected index的v2脚本为`case/commands/accdiag016-terminal-freeze-v2.py`，SHA `07003b7740bc1d2f164ac5e4d3b51f2a8766500856dc9cac4ab1f471a369de6b`，AST通过；执行`python3 case/commands/accdiag016-terminal-freeze-v2.py --case case`，另建排他`terminal-freeze-002`，不覆盖第一次或改变模型运行。

### 12:47 heartbeat：126完成，doc90/118仍生成，目标16/16正常

12:46:09全部已完成126份raw SHA和token数量与usage一致、108唯一doc，均有最终正文、正常think-end/stop/末EOS248046，空最终/HTTP错误/length/60K cap均0，最长完成47597 tokens。12:47:04原progress仍128派发/126完成/2在途/error0，无FINISHED/CLIENT_FAILED/FIRST_ANOMALY/STOP/first-state，不能提前冻结为全部完成。最后两条seq18/doc90和seq24/doc118仍由原客户端自然收集；rank0 FULL graph batch2的computed tokens为53987/54035（包含prompt和已计算上下文，**不是已结束API completion_tokens**），采样前缀仍推进，不能将正在reasoning且尚未结束的请求判为reasoning-only故障，不估ETA。

C64最后目标late doc155(seq123)已于12:22:25正常返回28029 tokens，think-end位置27746、末EOS248046，故8目标早晚16/16均有最终正文；本轮不是正式GPQA，不计新分数/gate。

逐rank全量日志扫描仍generic最大20536、packed decode18856，row stride102400及i32/i64偏移/合法storage边界沿用原最大现场，未跨20972。每rank6696个operator-post，边界/已检查状态mismatch/device flag仍0；rank日志12:46:50–12:47:04持续更新、step73982–74149，rank0原sampler前缀推进，无新增错误，仍仅旧广播等待提示。共享pool last-writer限制继续适用，未复现不等于修复。

8010 API1325804/start483425629、客户端1382210/start483440925未变、health200，running2/waiting0、KV约4.94%、preemption0，证据约2.4GiB。其他8035旧PID2941880也已退出，当前监听PID3466314，仅只读观察，不推断外部换实例原因；本任务未操作任何其他服务。本轮没有重启、改源码、追加推理或GPU测试，继续原heartbeat直到既有两请求自然终态再冻结和暂停，不自动扩128范围或重跑正式GPQA。

### 12:16 heartbeat：113完成、15在途，仍未触达20972

只读核验至12:16:57，progress为128派发/113完成/15在途/error0，开始以来约1小时33分54秒；113 raw SHA及token数量与usage逐份一致，96唯一doc，全部有最终正文、think-end、stop和末EOS248046，空最终、HTTP错误、length/60K cap均0，最长已完成31389 tokens。全局/各rank首次异常及STOP/first-state无记录，FINISHED/CLIENT_FAILED仍未产生。

8rank日志逐份扫描：generic int32 gather/scatter最大20536、row stride102400，i32/i64行偏移2102886400相同、地址差0，storage边界沿用已保存最大现场；packed decode最大18856。每rank6696个operator-post未新增，所检查行及设备flag无异常；日志和采样仍推进到12:16:10–21，step52963–53077。未跨20972，不能排除大索引位宽缺陷或宣称原故障修复。

C64 early doc1(seq72)已于11:48:19正常输出16306 tokens，late doc142(seq120)于11:59:09正常输出14028 tokens；各有think-end→EOS，早晚目标现完成15/16，只余late doc155(seq123)。全部未完seq为10/11/12/13/14/15/16/18/24/26/27/30/40/42/123，仍由原客户端自然收集。

8010 API1325804/start483425629与客户端1382210/start483440925未变、health200，12:16:44 running15/waiting0、KV约23.10%、preemption0；证据约2.0GiB，最近完整结果12:14:12，运行与token继续更新。服务日志无新错误，仍仅11:11:56原广播等待提示。其他8035原PID986018已退出，当前监听PID2941880，发生在本次只读观测前；本任务没有停止/重启/修改它，原因不推断，历史“前后身份一致”只描述最初reload时刻，不当作最新事实。0–7未操作，8010未重启、源码/采样/请求范围不变，保持同一只读monitor ACTIVE；待原客户端终态再冻结并暂停，不提前扩范围或复跑正式GPQA。

### 11:46 heartbeat：全部请求已分发，generic最大20536但尚未跨边界

按批准范围只读核验，未重启、改码、加请求或执行GPU测试。11:46:09原生progress为128派发/90完成/38在途/error0；90份raw SHA、完整token数与usage逐份校验通过，75唯一doc，无异常。随后健康汇总为91个完成/37在途，91份均有最终正文、think-end、stop及末EOS248046，length/60K cap均0；第91份的SHA未在前一90份快照内重复核验，不把两次快照混成同一时刻。全部128已派发，此后只能自然收集现有请求，不补发或扩范围。

8rank完整日志扫描均见generic gather/scatter最大**20536**，距离20972阈值**436**，尚未触达。最大现场为step28986、`language_model.model.layers.1.linear_attn` gather、int32 index20536，pool shape[87529,6,128,128]、stride[102400,16384,128,1]、storage_offset1920元素、storage35851878400字节。该行i64/i32行起始偏移都为2102886400元素，地址差0；字节区间[8411553280,8411946496)落在storage内。此为实际合法近边界输入，不是溢出或旧fault的复现。packed decode观察最大18856，未跨20972；不与generic路径混同。

每rank6696条operator-post记录中已检查行无gather/clear/scatter mismatch；index/storage/overflow、device非法索引/nonfinite均无报警。全局及8rank FIRST_ANOMALY/STOP/first-state均不存在，未发生需要冻结的实际首异常。原唯一一次11:11:56广播等待提示没有新增，8rank日志继续推进到11:46:42–50、step35846–35912，rank0采样前缀11:46:42更新，不构成停滞证据。

API1325804/start483425629、客户端1382210/start483440925及其他8035 PID986018/start483326215均在；8010 health200，11:46:09 running38/waiting0、KV约27.72%、preemption0。证据目录约1.5GiB，最近完整回复11:44:08，后续仍有新回复。C64早晚目标已完成13/16，尚缺early doc1(seq72)、late doc142(seq120)/doc155(seq123)；其余已完成目标最终字母正常（142D/144B/149B/155C/151B/0D/1B/2B，仅输出观察，非正式评分）。无空最终、真实HTTP错误、length截断或非法访问，不以此宣称修复/排除大索引假设。继续现有monitor等37在途结束；终态若仍未跨20972按not-covered冻结并暂停，不扩大范围。

### 用户追加监控重点：20972边界及首异常完整取证

用户明确要求继续监控既有负载，重点检查是否触达20972，保全首次异常证据并告知，禁止重启与全量GPQA。已通过产品工具更新同一heartbeat（保留30分钟/ACTIVE与原通知偏好，非新建），加强首次边界跨越、危险generic guard、reasoning-only和设备异常的通知/取证核验。分别统计generic int32 gather/scatter、原本i64的packed decode实际索引、scheduler block IDs，不能将后两者越界值冒充危险generic路径触发；不为触达目标扩充原128请求或改动服务。

11:18:53只读快照：派发82/128、完成18（13唯一doc、其中C64完成8）、在途64、error0。全部已完成raw SHA/完整token数量与usage匹配、最终content非空、无length cap；8rank边界、状态mismatch/nonfinite均未报警、无首次异常标记。实际generic gather/scatter最大9290，packed decode已观察最大5503，尚未达到20972；仍不能否证该条件缺陷。API1325804/start483425629、客户端1382210/start483440925和8035 PID986018/start483326215未变，health200/running64/waiting0/KV约13.28%/preemption0，rank日志及采样前缀继续推进。未新增模型请求、重启、埋点或GPU测试；本轮仍非正式分数/gate。

现有埋点/客户端在首次异常时自动排他冻结并停止补位；heartbeat在检查发现后通知。冻结需核验实际写成的索引/mask/shape/stride/storage、请求/slot/graph绑定、有界state文件/manifest、原始HTTP与token或崩溃前实际前缀、完整错误日志及SHA；若部分缺失或异步尚未写完，明确报告并只读取证，不声称共享last-writer快照等于全部层完整状态，也不补造不存在的最终回复。达到128终态仍未触达边界则记录not-covered并暂停监控，不自动扩范围。

### 11:16 heartbeat：早期C64目标0/151正常完成

只读核验全部当前raw/result与8rank记录，未发送请求或变更运行。现派发79/128、完成15（10唯一doc，其中C64完成5）、在途64、error0。新增seq71/doc0为811 tokens、seq70/doc151为1197 tokens，均有最终正文/think-end/stop/末EOS248046；新增背景seq51/doc92为1385 tokens且同样正常。所有15份raw SHA、token数量与usage一致，空最终、HTTP错误、60K length、真实FIRST_ANOMALY均0；不能将剩余在途判为已正常完成。

各rank当前1404个operator-post未发现已检查行的gather/clear/scatter mismatch，index/storage/overflow与device非有限flag无异常。实际gather最大index7057，尚未跨20972位宽边界。8rank日志推进至11:16:22–25，rank0采样前缀11:16:22更新，先前60秒广播提示没有新增，不能据此称停滞或证明具体编译原因。

API1325804/start483425629、客户端1382210/start483440925、其他8035 PID986018/start483326215均符合记录；health200，running64/waiting0、KV约10.10%、preemption0。证据约516MiB，最近结果11:15:51、服务日志11:16:25；原128请求计划SHA未变、无FINISHED/CLIENT_FAILED。继续既有只读monitor，仍无修复/正式gate，不重启、不加请求、不重跑全量GPQA。

### 11:13只读进展核验：控制完成，C64运行中

11:14:24补充原始HTTP逐份核验：新增C64 seq60/doc113和seq73/doc2完成，当前派发76、完成12（9唯一doc）、在途64、error0。12份raw SHA均与result一致、完整token数与usage一致、最终content非空、think-end存在、stop及末EOS248046正常；C64仅完成2条，其他在途仍待取证，不提前判定全部正常。

按inference-accuracy-diagnosis只读核验，未改服务、客户端或请求。API仍1325804/start483425629，health200，唯一客户端1382210存在。开始10:43:02，至11:13:19约30分17秒；C8最后doc142于11:10:55正常返回后进入C64，累计派发74、完成10（8唯一doc，2条doc2重复C1）、在途64、error0。未分发的54条仍在既有清单内，不额外补发/重试。

10份完成结果均有最终content、stop、think-end和末EOS248046，token数与usage一致（312–19480），无reasoning-only、60K length、HTTP/client错误；8目标包括142/144/149/155/151均在C8正常结束。C64尚无完整响应，不能把64条正在推理的请求算作正常完成。runtime及8 rank FIRST_ANOMALY/STOP均不存在。

逐rank流式扫描：每rank已记录864个operator-post，gather/clear/scatter已检查部分无mismatch；所有记录的index/storage/i32-overflow异常与device flags均0。当前实际int32 gather最大index5007，stride102400，仍未触达20972起的i32乘法溢出边界，因此**不能以当前未报警否证大索引假设**。共享pool快照的last-writer限制继续保留。

11:11:56服务记录一次shared-memory broadcast block等待60秒提示，但之后8rank日志均推进至11:13:17–19，step约20559–20578，rank0采样token前缀更新至11:13:17.395，故当前不是持续无推进或已确认非法访问；不以该提示推定编译或具体根因。11:12:20服务指标running12/waiting0/KV约1.10%/preemption0为较早独立采样，客户端在途64包括API侧等待/尚未被engine接纳请求，两者不可混同。保留原日志，继续现有只读heartbeat，不估ETA、不重启、不重跑全量GPQA。

### 已加载并进入C8的运行事实

本轮交接前最后核验：已分发10、完成5、在途5、error0，阶段仍C8；FIRST_ANOMALY与CLIENT_FAILED均不存在。下文4完成是较早快照，不是终态。

本次旧8010树正常退出，新API1325804/start483425629于10:40:29启动，10:42:33完成startup；两类graph均7/7 capture，8 rank实际模块SHA均为e044c58d且有runner/device-buffer证据，原Plugin/Gems源码逐文件SHA未变。READY SHA `878e8d7345b01effac06a442255f24b0b21d9854cad905c8b1056aeebf11d3f2`，8035在本次前后均986018/start483326215，未操作其他服务。

唯一客户端Host1382210于10:43:02.797862启动，`--mode run`，原128清单无变化。两条C1 doc2均有最终B、stop、441 tokens；完整token IDs逐项相同，think-end位置346、末token248046。已看到FULL实际graph对象/descriptor和设备执行计数变化，不能仅用capture或Python hook替代replay。随后C8分发固定8题；最近核验合计分发10、完成4、在途6、error0，C8已完成doc0/doc2且正文正常。无首次异常标记、空最终或length cap；health200，running6/waiting0、KV约0.72%、preemption0。未开始C64阶段、未越过i32高索引边界，不宣称问题修复。

实际prefill记录覆盖36个GDN层，输入shape[87529,6,128,128]、stride[102400,16384,128,1]、FP32，索引int32；目前最大已见gather索引571（远低于20972溢出边界）。多个层确实共享同一个pool pointer；v3 BUFFERS按pool指针复用，因此device counter汇总同pool多次执行，`layer`标签是首次注册层，selected pre/post仅保留该pool最后写入的执行，**不是36层各自的独立快照**。修正之前“每层selected快照”的预期描述，不改运行代码/不新增重启；prefill generic hooks的逐层operand/bounds记录及freeze内按各层实际metadata选择state row仍保留。后续归因必须按真实索引/最后执行映射解释共享buffer，不能拿label直接指认layer0损坏。

已更新原heartbeat `qwen3-8-ppu07-gpqa-c64` 为本轮runtime-002只读监控、ACTIVE、30分钟，只报实质进展/异常/终态，禁止重启、追加请求和全量GPQA。当前minimal-regression仍incomplete（C8/C64待完成），无正式分数/gate，原故障污染127/198不变，根因仍not-isolated。

首个控制脚本在任何变更前因8035与runtime-001旧记录PID不一致而拒绝：旧PID528147，当前986018/start483326215；8010仍501780/start483237290，runtime-002尚未创建。此前“8035未变”的表述仅依据摘要中的最近快照，实际旧文件不同，以当前只读事实更正。该服务已独立换实例，不归因本轮；不操作它。新增`accdiag016-reload-v3-current-binding.py`仅将保护基准绑定本次操作前的8035精确PID/start/argv SHA，之后必须保持一致；保留原拒绝脚本。其他服务的历史变化不作为8010模型异常。

执行前控制脚本AST通过，SHA `640ba20579d08e858c179d842a5350e1dba4fdabc9aa3c5fda20cf754c0db7ad`；本地py_compile因默认缓存目录沙箱不可写而未完成，改用不写缓存的AST检查，不属于远端服务异常。

实际执行修订控制文件`case/commands/accdiag016-reload-v3-current-binding.py` SHA `07fed6cdf9aff13d96baadcb0ccf4f4eb13635229bc129029f9d2f6d65d27983`，AST通过，模式与上述restart→wait→start-client相同，其他参数不变。

用户明确允许再次仅重启8010加载修正版埋点。重新通过PPU-07 connectivity-check；当前API501780/start483237290、health200、running/waiting0、prompt/generation累计0，8035仍API986018。原runtime-001无RUN_STARTED、无模型请求，旧CPU人工异常不作为模型异常。本轮另建`runtime-002`，原128请求清单逐字节复用SHA9247cf98f91645b5b4d8513117d106248fb96da03ef9efbca793a60ea6743c2f，包含10条控制和118条C64，不增加额度。

新控制文件`case/commands/accdiag016-reload-v3.py`在执行前保存并核对SHA。命令依次为`python3 case/commands/accdiag016-reload-v3.py --case case --mode restart`、`--mode wait`、就绪后才`--mode start-client`。它核验原源码和3个私有入口SHA、v3 CPU回执、空闲零请求及8035身份；保存启动脚本后仅SIGTERM精确8010树，等待其退出，不强杀、不操作容器和其他服务；排他marker拒绝重复重启。新日志路径`runtime-002/service-diag.log`，预先检查日志存在后再读取，修正旧readiness竞态。v3仅修正event形参冲突，无状态算法/i64修复。8 worker实测v3 SHA和device buffer后才发请求，首次异常停止补位、在途仅取证、无重试或自动重启。CPU回归不代替设备/模型精度验证；本轮结果仍仅minimal-regression/controlled-diagnosis，无正式分数或gate。
