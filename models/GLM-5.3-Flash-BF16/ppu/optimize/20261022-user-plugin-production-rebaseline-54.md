# 点54：基于用户当前Plugin版本接续优化

状态：当前源码原生单次198题/C64全量GPQA为173/198＝87.3737%≥86%；P1K三阶段各8预热+3测量于20:17:37全部完成，21:12:48原生33轮及当前完整身份独立审计通过。768个测量请求、全部2816个含预热请求均成功，全部冻结稳定性指标≤5%；`glm-plugin`终态监控已删除。完整最小回归CPU126、C1/C8、三16K、11答案、C64 64/64、FULL捕获与多token请求及16worker无TileLang/hook的证据保留，不重复执行。用户源码、index、实例和原参数未变；当前只有稳态入口基线，没有新ABR收益或四场景验收。

## 优化方向与瓶颈依据

分类为当前版本恢复验证与框架诊断。目标仍是P1024/D1024/C64/N128；点53的Prefill/Decode/Mixed基线完整保留，但属于旧内容SHA`529cd814…`，不改绑为新版本。开始时观察Plugin SHA`1ecb0ef3…`、API仍为旧实例；17:29完整回归已核验新实例`3318148:537692913`加载当前源码，见下文。

先冻结当前三库源码、Git状态/index、镜像/挂载/权重/tokenizer、原启动脚本和生产DB事实，再对精确任务服务重载。MBT32768、maxseq64、TP16/BF16、maxlen80000、FULL_DECODE_ONLY、关闭前缀缓存及原脚本均保持不变。不加临时MM策略/观测hook，不改vLLM、权重或tokenizer，不提交推送。

## 优化内容与适用边界

当前用户修改涉及vendor/thead Sparse MLA可选SDK可用性和Python调用ABI探测、对应测试；现有thead配置仍prefer flagos。这里只审查和验证，不收敛或覆盖用户代码，不将SDK导入/签名检查当作设备数值或graph通过。之后根据当前稳态Decode/Mixed的主机、设备和通信占比选择一个最窄Plugin/FGV候选，不优先调整MBT、不复用旧无收益合批策略。

## 正确性与路径命中

显式调用精度技能`minimal-regression`：当前MLA契约测试、原P4096/D16/C1/C8、固定smoke/C8、16383/16384/16385边界、11明确答案、C64/N64和FULL捕获/多token回放；核对16worker无TileLang及临时hook、真实默认实现命中。

源码改变，不复用旧173/198 gate。最小回归通过后按原198题/C64/seed42/temp1/top_p.95/maxgen60000/strict≥.86正式契约评测；独立UUID，无补充、best-of或自动重试到过线。原始manifest/分数不改。正常DB写入按已批准缓存更新流程记录前后SHA，不清、复制或回退生产DB。

## 性能效果

模式`baseline`，当前版本三阶段基线完成并原生复验；收益未知。Prefill P1024/D1/C64/N64、Decode P1024/D1024/C64/N64、父Mixed P1024/D1024/C64/N128，各8预热+3测量。末3预热主要吞吐spread分别0.3535%/0.4223%/1.8662%，测量全部约定指标≤5%，没有丢慢轮。下表spread定义为三轮最大减最小再除以中位数。

| 阶段与指标 | 测量1 | 测量2 | 测量3 | 中位数 | spread |
|---|---:|---:|---:|---:|---:|
| Prefill 总token吞吐（token/s） | 12294.5726 | 12310.5876 | 12332.7094 | 12310.5876 | 0.3098% |
| Prefill P99 TTFT（ms） | 5326.6578 | 5319.3264 | 5309.9709 | 5319.3264 | 0.3137% |
| Decode 输出吞吐（token/s） | 1172.6918 | 1157.7877 | 1155.2764 | 1157.7877 | 1.5042% |
| Decode P99 TTFT（ms） | 5351.2642 | 5395.1724 | 5403.6535 | 5395.1724 | 0.9710% |
| Decode P99 TPOT（ms） | 52.5249 | 53.1791 | 53.2918 | 53.1791 | 1.4421% |
| Decode P99 ITL（ms） | 50.8824 | 51.6673 | 51.7241 | 51.6673 | 1.6291% |
| Mixed 输出吞吐（token/s） | 1160.0685 | 1148.8500 | 1144.3914 | 1148.8500 | 1.3646% |
| Mixed P99 TTFT（ms） | 5345.1899 | 5343.4247 | 5338.5994 | 5343.4247 | 0.1233% |
| Mixed P99 TPOT（ms） | 53.8223 | 54.2035 | 54.5941 | 54.2035 | 1.4239% |
| Mixed P99 ITL（ms） | 51.3512 | 52.1977 | 52.0138 | 52.0138 | 1.6275% |

所有请求吞吐、总/输出token吞吐与P99 E2EL等完整三轮值均在state同条目保留。P99中位数是“每轮P99的中位数”，不是合并请求P99；TTFT/TPOT/ITL仍含网络、调度、采样和跨阶段残余开销，不是纯设备时间。原生验证覆盖全部33轮的计数、token长度、命令/客户端/输入产物SHA及原始输出。旧点53源码不同，不与本轮混算精确收益；没有candidate/revert，不能证明回退漂移改善或长期稳定，四场景正式验收尚未执行。

## planning54：下一轮候选（只规划，未启动）

证据截止21:12:48。当前候选与本轮scenario-entry baseline均为用户Plugin`1ecb0ef3…`/FGV`ba76c1df…`/FG`1a6197b7…`和同一实例；不是未优化anchor，累计收益未知。依赖顺序为公共PR454路径与KPool/SQL修复→H4与物理索引融合→用户Plugin修改→本轮完整回归/新原生173分gate/三阶段基线。点51冷MM因果实验及OOM失败保留、限4诊断策略未保留；点52融合保留且只证明相应OOM/内存改善；点53旧版本基线保留但不改绑。本点没有新增Agent源码补丁。

阶段判断：Prefill约5.3s TTFT、Decode约53ms TPOT、Mixed约54ms TPOT均为稳定的客户端代理事实，但主机、设备kernel、TP16通信、KV及实际batch shape占比仍未知，不足以直接决定改哪一个算子。Mixed与Decode请求数不同，差值不作为严格干扰因果或收益。

1. **框架方向：稳态逐token主机开销与graph提交间隙。** 首个证伪步骤为当前P1K Decode及父Mixed的代表性稳态trace，关联API/Engine/16worker，把CPU元数据准备、同步、graph提交、设备与collective分开，按墙钟关键路径而不是16rank时间求和。若可消除部分不足以支撑≥3%净收益或覆盖/命中不充分，停止该方向。真实瓶颈成立后才选择最窄Plugin扩展；风险为worker生命周期和graph兼容，保持vLLM只读、原MBT/参数不变，只回退新增自有补丁。
2. **算子方向：实际H4 Sparse MLA或融合索引路径。** 仅在上述trace证明其占关键路径后，冻结真实shape/dtype/stride/KPool宽度，分开评估现有flagos/vendor替换（operator/replace）或当前FGV kernel单变量改进（operator/improve）。用户SDK可用性/签名探测不等于生产切换vendor，旧micro加速不等于当前端到端收益。首个证伪是完整调用设备对照；数值边界、实际命中、FULL capture/两次replay不通过或无净设备收益即停止。注意attention/索引/cache ABI与多平台fallback风险，必要时触发新完整精度gate。

下一步只提出`inference-profiling capture/analyze`，本monitor不执行。后续实现必须调用最小回归，再用无profiler `targeted` 完成同配置Mixed A/B/R及Prefill/Decode守护：吞吐≥3%，P99 TTFT/TPOT/ITL退化≤5%，测量spread≤5%，回退漂移≤3%；再决定单目标formal晋级。尚不自动部署或启动候选。冷MM限4/启动调参、MBT调整、旧41阈值与42合批、未归因MoE/mHC调优暂缓；新trace完成、2个候选有结果、热点迁移或任一回归时再复盘。规划技能促使本轮保留“归因未知”和旧失败边界，而非按历史kernel加速比选改动。

## 决定、风险与回退

用户当前源码是新的工作起点。所有用户dirty/index保留，保存恢复归档但不擅自回退。仅重载明确任务的8011 API及其子进程；遇源码漂移、忙碌/归属不符、数值或graph回归失败停止晋级，保存首次失败，不盲重试或覆盖。新源码验证完成后才定位并实施进一步性能改动。

## 外部证据

终态只读审计执行前保存点51根`commands/point54-baseline-final-audit-v1.py`，SHA`a132fa391182471bef13c51bd40e2fee699986b2e3194e4472bf1a871159478d`。只复验既有33轮原生证据与当前源/index、实例/参数、唯一安装、镜像挂载、权重/tokenizer/thead/DB及health；从原schema3保存新的显式缓存审计绑定，不改旧manifest或分数，不发模型请求、不改服务。结果另存本轮`final-readonly-audit-v1.json`，不覆盖正式精度审计。

21:12:48审计通过：`steady-p1k-01/final-readonly-audit-v1.json` SHA`7f906a972b3bced4d7e191fd5d766edf2e42ea3053d07e230828a468e1f51028`；completion SHA`4ef682e91feddbe875068e0b50ac5e1722085b972e2f0dbd061d6e6be4e7b983`。Mixed原生run-record SHA`939e039707256a1ac45a8c1e5f8980a20dcb1f1c4c95706e67c644e038706c54`。三库及vLLM源码、Git/index、argv/env、权重/tokenizer/thead/脚本、镜像/挂载/网络/唯一安装均未变；API仍`3318148:537692913`，health200且空闲，控制器已退出。DB整轮及当前均为`5f343e67…`，没有清理/复制/回退；新的同实例显式schema5 gate SHA`948c2d34c0d392ba6b675a00ba7ace438aebe0ee7f5a6bc73b03c6801d1edbda`复用本点原生173/198，不是新评测。`glm-plugin`已由工具确认删除，服务保留运行，无新增请求、源码或参数变更、提交推送。下方各时点为完整保留的过程记录。

唯一新根：`/mnt/nfs/users/jinghao/glm5.3-flash/optimize/e2e-opt-20260911/resume-20261022-point54-user-plugin`，使用前已核验规范路径、owner/权限、可用空间及根不存在。脚本、快照、原始结果和完整日志只保留远端；对应SHA写回state。无history目录。

执行前保存点51根`commands/point54-control-v1.py`，SHA`a9f9fd16069f07123bb6d0f863d4fb2bb6c4eb8731bf192cf5c63dbf5028e305`，语法校验通过。prepare仅归档当前三库（含Git/index）并核验镜像挂载和运行事实；run复用既有生产最小回归函数，先当前CPU MLA契约，再精确重载空闲的旧API，原脚本启动及全部最小回归。此命令不自动派发GPQA或性能；后续各自先冻结新命令与契约。

17:23:03零生成准备通过，freeze SHA`c04a0a09…`，源码及index保持一致；三库含Git/dirty归档已保存`source-snapshots/`，完整SHA写在state。`glm-plugin`唯一heartbeat每30分钟只读跟进，不变安静、不重复启动，终态审计后删除。准备阶段尚未停止服务或执行回归请求。

17:24:52唯一派发PID2087187/start537690230，126/126当前CPU测试通过，日志SHA`c504279f…`；这不是设备或整模通过。当前控制器继续原服务重载与整模回归，未启动新GPQA或性能，不将旧173/198用于新代码。

17:28进度：旧精确API于17:25:17退出；原脚本17:25:19重载，17:27:54健康就绪，新实例`3318148:537692913`已核验当前Plugin SHA`1ecb0ef3…`和原argv/env，C1及C8通过，剩余smoke、三16K、11答案、C64与最终审计进行中。

新正式编排先保存点51根`commands/point54-formal-v1.py`，SHA`4299d3d2076d37b12a3b6924a154fe03f8ca1a6d1b748e9ab2f4ed4356c80c46`，仅在完整最小回归通过后才允许prepare。复用原生wrapper/原始runner，198题/64并发/seed42/60K/strict≥.86；两次provenance与preflight零生成，另行唯一dispatch。终态从真实run-record签发source gate，再保存同实例DB前后审计/schema5当前绑定并原生check；不能因DB正常变化反复重跑，其他稳定身份不放宽。此时尚未执行正式prepare或生成请求。

17:29:23完整最小回归终态通过，`completion.json`及`production/final-audit.json`保留全部原始请求/结果、FULL捕获和默认实现首次命中；16worker无TileLang与临时hook。三库内容及index、原argv/env、权重/tokenizer/thead和启动脚本校验未变。DB正常写入后SHA`5f343e67…`，不清理/回退。未新增或覆盖Plugin代码，尚无新身份GPQA分数或稳态收益。

17:32:18正式零生成准备通过：两次provenance相同（SHA`c3c31ea3…`）、原生preflight与完整accuracy bundle校验通过，freeze SHA`d42f53fa…`。17:34:28唯一派发PID2302630/start537747789，初始服务manifest SHA`d34db997…`、最小回归completion SHA`e9f42b4f…`；当前score为pending，不能使用旧173/198。`glm-plugin`同一monitor已更新到本轮正式跟进，不新建重复监控。

17:35:27只读确认原生`generate_until`已开始，独立UUID `92ebe2b58ad54c908982a32faa41446b`，effective config/frozen inputs已落盘，控制器身份一致、health200，无formal.exit/completion/failure；不是仅准备或派发状态。当前分数未出，不读原始题面作为进度证据。

若当前正式有效通过且现场身份/空闲核实，按用户本轮“继续性能优化”授权，接续本页已声明的新版本P1K三阶段基线；必须先另存唯一子目录、命令SHA、计划/比较契约和dry-run，不能直接调用旧点53控制器或改绑其结果。该后续仍不修改源码/参数、不开启新候选/profile，完整三阶段终态后给出下1–3个可证伪方向；遇低分、身份或正确性失败则停止性能晋级并按精度定位流程处理。

17:58:32只读检查：原生进度171/198，控制器PID/start与唯一派发一致，API仍为`3318148:537692913`、health200；formal.exit、completion、failure及原生结果文件尚未出现，分数待定。日志末1MiB未见Traceback/OOM/CUDA error/EngineDeadError/RPC timeout关键词。保持当前评测运行，未派发额外请求；本次仅进度和精确进程健康检查，不替代终态源码/数据审计。

18:25只读终态观察：formal.exit=0，原生173/198达到86%阈值，当前实例health200，正式期间稳定身份及DB字节未变化；source schema3 gate和显式schema5绑定完整保留，没有补充或best-of。新命令先保存点51根`commands/point54-baseline-v1.py`，SHA`bdbf497368bd4c1f5b8371dd2d919f8c1f48ff75cfe577c2ba6ed628c18e1241`：audit零生成复验原生198题各filter/provenance、当前身份/安装/健康；prepare在唯一`steady-p1k-01`冻结计划和三项dry-run；通过后才唯一dispatch原Prefill/Decode/Mixed基线。每阶段独立从本点原schema3 gate审计当前DB绑定，role仍为baseline；全部3轮约定指标极差≤5%，只允许预热不稳且健康空闲时继续其余预声明阶段，其他错误保留并停止。MBT/启动参数/三库均不改，未执行新性能请求。

18:32独立终态审计通过，`formal-gpqa-01/final-readonly-audit-v1.json` SHA`1f4fcfbf3ae6f4edc8013c07d238266b29c2909b7d3847684737470f8f753b8f`。198唯一题与strict-match/flexible-extract全部396行及冻结来源复验通过；5个timeout标记、0空输出/乱码/显式截断，只作健康观察，精度仍达标。当前源/index、argv/env、模型/tokenizer/thead、唯一安装、镜像挂载及实例未变，health200/空闲；DB仍为`5f343e67…`。

18:32:34零生成prepare完成，`steady-p1k-01/freeze.json` SHA`5b721d7a7d15a0710cc5be1093a633db08f1c78e3b0c82db9f8b820847a9c9ab`；原生三项dry-run逐一核对P/D/C/N、固定长度random、temp0/ignore_eos、8+3和5%准入，完整计划/比较SHA写在state。19:35:49唯一派发PID566467/start538475883，仍为同一模型服务，无重启/改库/清缓存。14400秒是规划预算，1800秒为原生单轮超时；全部轮次保留。`glm-plugin`同一30分钟监控已更新为只读跟进这轮基线，三阶段终态及当前审计完成后删除，不自动加跑profile或安装候选。

19:37:03只读确认控制器start ticks一致，Prefill前两轮原生validation文件已生成，尚无completion/failure；服务health200，Decode/Mixed尚未开始。监控没有额外派发请求。

19:41:20只读进度：Prefill完整8预热+3测量已完成，独立用维护版比较器复验原生11轮与汇总一致，run-record SHA`178bc4a306b568c3b699069b104a4ddc862922e08caf64fea71e0c29056b27cc`。测量总token吞吐三轮为12294.5726/12310.5876/12332.7094 token/s，中位数12310.5876，极差0.3098%；P99 TTFT三轮5326.6578/5319.3264/5309.9709 ms，中位数5319.3264，极差0.3137%；P99 E2EL中位数5319.3263 ms、极差0.3137%，请求吞吐中位数12.0103 req/s、极差0.3098%。末3预热吞吐极差0.3535%，全部约定指标≤5%；完整三轮数值保存在state。DB字节未变，同一控制器与API存活、health200，无completion/failure；Decode/Mixed尚无完成结果。仅Prefill入口基线及客户端代理数据，不是新收益或纯设备时长，未追加请求。

20:15:19只读进度：Decode亦完成原生8预热+3测量，独立维护版`check_run`复验并确认汇总逐轮相等，run-record SHA`c8937a8bb3e0192233e7d2fd741d61d8d674388867c49c5a1cb385b30fb167aa`。输出吞吐三轮1172.6918/1157.7877/1155.2764 token/s，中位数1157.7877、极差1.5042%；总token吞吐三轮2345.3837/2315.5754/2310.5527、中位数2315.5754 token/s；P99 TTFT三轮5351.2642/5395.1724/5403.6535 ms、中位数5395.1724、极差0.9710%；P99 TPOT三轮52.5249/53.1791/53.2918 ms、中位数53.1791、极差1.4421%；P99 ITL三轮50.8824/51.6673/51.7241 ms、中位数51.6673、极差1.6291%。P99 E2EL中位数56595.5538 ms、极差1.4876%；末3预热输出吞吐极差0.4223%，全部约定指标≤5%，完整三轮记录见state。Mixed已有9/11个validation但没有完成结果，不能以阶段计数宣称稳态通过或三阶段完成。控制器PID566467/start538475883继续运行；API PID3318148属于容器PID命名空间，已在容器内核对start537692913及health200（不把宿主同PID不存在误判为服务退出）。本轮仍是部分入口基线，未做新ABR、回退漂移或纯设备阶段计时；未发任何额外模型请求或修改用户源码、参数、生产DB。
