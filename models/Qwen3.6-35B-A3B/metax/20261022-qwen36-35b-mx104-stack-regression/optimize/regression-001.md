# regression-001 整理、editable安装及Plugin迁移完整回归

## 优化方向与瓶颈依据

本轮仅验证已保留变更是否退化，不增加性能优化。对照为最初用户优化好的Plugin d1653d9及FGV普通安装环境，不能用sampler修复前的release/0.2冒充整体基线。源verify容器保留，以当前有效writable层快照复刻A/B私有容器，核验谱系和挂载。

## 优化内容与适用边界

同Host/GPU0,1/TP2/权重/tokenizer/graph/启动配置、独立私有缓存、prefix cache关闭。基线只在私有A容器恢复经SHA核验的原Plugin、安装metadata和FGV包；候选B保持当前代码。vLLM源码不修改。

## 正确性与路径命中

使用本地inference-accuracy-evaluation formal-gate流程。完整GPQA198题，首先A1采集参考分数，其threshold0仅为指标采集下界，不签业务质量gate。候选测量前按用户确认规则冻结绝对threshold=A1原生精确分数。所有身份和原始结果留远端，不能引用本地旧优化历史分数。

## 性能效果

性能baseline-01已尝试：P1K完成4预热+3正式，P4K完成4预热后稳定性不达标停止，P16K/P32K未测；整套incomplete。候选完整精度未通过后，正式性能阻塞，不能判定性能迁移退化。四场景P1K/P4K/P16K/P32K均D1K/C64/N128。每角色两独立服务实例，每实例每场景4预热+3正式，后三预热吞吐spread<=5%，正式spread<=10%，baseline/revert drift<=5%。主吞吐允许下降5%，mean/p99 TTFT/TPOT/ITL各允许上升5%；E2EL报告但无自行添加SLO。使用非零temperature覆盖采样路径。所有正式测量轮保留；证据不完整或不稳记incomplete。

## 决定、风险与回退

候选完整精度147/198低于冻结门槛160/198，当前不通过，正在诊断，根因未定；性能incomplete。本轮结论范围是迁移回归，不是相对未优化anchor的累计性能收益。源容器不修改；只停止本轮服务。原失败和中间结果保留，不放宽阈值。

## 外部证据

远端根：/public-flash/jinghao/qwen3.6-35B/20261022-qwen36-35b-mx104-stack-regression。创建、恢复、启动、取证、评测命令在执行前保存其commands目录。原始结果、失败证据和诊断保存在该目录；以下按时间保留过程记录。

## 启动参考核对

已在浏览器读取用户提供的[飞书启动总结](https://chitu-ai.feishu.cn/wiki/ElUGwY9zsiBCwrk5pWfcE5Q0nue)35B MoE段落：TP2、BF16、max_model_len67584、MBT8192、max_num_seqs64、显存比例0.9、prefix cache关闭、FULL_DECODE_ONLY/max_capture64及MetaX MoE/路由/连续KV环境。文档对16K建议MBT32768，未给32K值；本轮迁移回归拟统一MBT8192，避免混入新调参。完整精度上下文以实际198题格式化prompt加65536预算核验后冻结。容器复刻保持源容器配置和挂载，不采用文档另一套docker run映射。

## 准备阶段核验

镜像谱系和两容器挂载均通过。源码/安装起点四包5,754文件一致；A容器已恢复原Plugin d1653d9及FGV普通安装，优化MoE安装字节未变，B保留当前release/0.2+editable候选。原容器继续空闲保留。恢复脚本首轮在写入前因发行包名`.`/`-`规范化不同停止，按相同包名规范化后逐项版本/依赖完全匹配并成功恢复。

模型35文件含21分片完整SHA稳定。GPQA两次provenance相同，最长格式化prompt2891（doc127）；统一context69632满足68427需求。lm-eval seed42，原生API adapter HTTP seed1234，两组一致。首次非login-shell启动缺MACA_PATH在模型加载前失败，采用容器既有login环境显式冻结后重试，失败日志保留。未修改vLLM或目标算子源码。正式精度和性能仍未测。

## 当前正式回归进度

基线baseline-01-r2已就绪，TP0/TP1实际MetaXTopKTopPSampler、shortlist=true，每rank30个MacaGDN，11个已capture graph并连续两次replay，临时代理与profile hook全部移除。C8共8/8 HTTP200、非空、算术正确、零截断。source-provenance/runtime-evidence/service-manifest已按当前进程绑定；manifest SHA9ed837c5ce3db8443e3ba72b60088dd757f1137f2241f977aee1d322ee7bf270。

A1全量GPQA198正式原生流程已启动，run_id=e6f7f0aee0584edbbc4e32626ffcb811，2026-10-22 14:49:39 UTC原生progress显示21/198、0超时；中间分数不作最终结论。后台有限作业jobs/accuracy-a1-full-001，完整性能尚未测，baseline-01原生dry-run通过。候选精度阈值仍等待A1首个完整有效结果。

用户明确要求每小时检查一次，heartbeat qwen35b=ACTIVE，rrule HOURLY/1已核验。仅有重要阶段完成、失败或需要用户操作时通知，整体结束/取消/人工暂停/无法安全继续时停用。此前未获授权的15分钟调度被自动审批拒绝，未创建；得到每小时明确授权后才成功创建本监控。可恢复执行入口为远端continuation.json，记录实际作业、已完成dry-run和后续六实例顺序。

### 执行覆盖边界

原基线MoE通过旧Plugin call_op/default.flagos接入FlagGems通用fused_moe；两rank日志确认align/invoke/SiLU/sum=default.flagos、routing=vendor.metax。FGV在实际worker中未加载，虽然普通安装包276文件和优化MoE字节已核验。因此本轮不把该服务结果作为FGV未启用tile/pipeline/完整融合内核的运行覆盖；候选同配置的实际路径仍需重新取证。

API进程的冻结环境完整核验；worker使用setproctitle，/proc初始环境区已缺失多数条目且存在已核实OpenCV库路径前缀，未把缺失条目伪造成Python os.environ实测。实际worker类、graph模式、rank、源码路径和hash由RPC核验。vLLM、优化逻辑及模型未新增修改。

本地记录校验：当前stack-regression案例无检查器报错；全项目检查仍因其他既有/并发案例的记录和过程产物问题未通过，未修改这些材料。此检查不承担模型精度或性能验收。最新A1原生进度为30/198（2026-10-22 14:51:59 UTC），正式结论仍待完整结果。

2026-10-22 23:25（Asia/Shanghai）现场复核：A1原生最新进度120/198，strict103/120=85.83%，0超时；这是中间分数，候选阈值仍未冻结。作业PID/starttime匹配，服务仍有32请求并持续生成，未停滞。候选完整精度未开始，性能正式run-record数量0，仅baseline dry-run通过。因此目前无成对完整结果，尚不能判定迁移是否退化。小时监控qwen35b仍存在。

2026-10-22 23:47（Asia/Shanghai）小时监控：A1原生最新进度190/198，strict155/190=81.58%，0超时；作业PID/starttime匹配、尚无完整run-record/result。日志有达到65536生成预算的length结束，作为输出健康观察保留，不另设精度失败门槛。候选完整精度与正式性能未开始，继续等待首个完整有效基线分数，无成对退化结论；本轮静默监控。

2026-10-23 00:50（Asia/Shanghai）小时监控：A1完整198题已于10月22日23:58结束，原生strict exact_match=160/198=0.8080808080808081。原生verify_run重新核验全部唯一题目、任务/配置/服务及结果/样本SHA通过；run-record SHA99dd3845707b2ef5d92ade3393a1cf245f5e59f2c9db5f43783bc5e4dd104202。原生progress最终显示matched0/strict0/0属展示问题，未作为分数来源；正式分数来自验证通过的results与samples。A1只作参考校准，不签质量gate。

候选精度门槛已按用户确认规则冻结为同一精确分数，reference-calibration.json SHA f2fccb6d4b93861501b0e50610930d2a98c69f5cb221af1322dc957d943c17b6。候选完整评测尚未运行，不能宣布精度未退化。

同一baseline-01-r2服务的新鲜核验通过：API/两worker实例未变、四包实际源内容不变、shortlist开启、无profile/hook/graph代理残留。随后按已成功dry-run的相同输入启动四场景基线性能有限作业performance-baseline-01-real-001，仍为4预热+3正式/场景，全部28轮。当前尚无完整性能结果或成对比较。

## 性能基线未达稳态与后续精度推进

2026-10-23 01:54（Asia/Shanghai）核验发现baseline-01于01:17停止，原生状态failed、项目结论incomplete：P1K完成4预热+3正式，P4K完成4预热后未满足最后3轮吞吐spread<=5%而停止，P16K/P32K未测。11轮均128/128成功，输入/输出token总数符合契约，原生逐轮校验和所有输入/输出SHA通过；未丢弃、追加或改写旧轮次。P4K最后三预热输出吞吐1178.0521/987.9129/1202.9669 token/s，spread18.2550%。

P1K三正式轮中位数：输出1500.2497 token/s；mean/p99 TTFT1941.0504/3740.8579 ms，mean/p99 TPOT40.6883/42.1124 ms，mean/p99 ITL40.6883/40.2542 ms，mean/p99 E2EL43565.1357/45333.9474 ms。输出spread7.9215%，mean/p99 TTFT49.2006%/40.4823%，p99 TPOT14.2012%，因此不能以P1K局部吞吐接近认定稳定。上述均为单实例3轮观测，非正式B/C/R比较。

初步只读诊断未发现该服务的benchmark窗口错误/抢占日志，检查的triton/vLLM私有cache目录未发现同期写入；当前Host CPU负载低、显存充足，但这些检查不能排除历史调度干扰或其他未覆盖缓存。波动主要见于TTFT和首波延迟，根因尚未定位，不把它归为迁移退化，也不直接放宽5%门槛或反复挑稳定窗口。

为推进独立的完整精度，在保留全部性能失败证据后仅停止本案例baseline-01-r2服务（精确PID/starttime和子进程核验，端口关闭/无残留通过），同一冻结launch v2已启动candidate-01。有限控制作业candidate-01-accuracy-after-incomplete-001负责ready→graph/C8→manifest→A1实测分数阈值冻结→完整198题→原生gate。候选精度和后续性能有独立状态；性能仍须先解决重复性，再对所有比较角色以同一有效契约重新采集，未宣称最终通过。

性能证据performance/baseline-01/incomplete-summary.json SHA0ee79cabda9da4a1736f8e376760948e4beee6997cd41a807fd146353d040189；控制脚本commands/advance-candidate-after-baseline-incomplete-v2.py SHAa0a6a18f4e8f9ccb0fec67d8a1aed43c455a9213447d9842312934e022847ad4。小时监控qwen35b保留并已更新当前阶段，不能重新启动已停止的旧性能run。

候选candidate-01已完成ready、两rank graph两次replay、原始图对象恢复、8/8 C8算术及源码/运行路径核验；同一冻结服务manifest与A1除声明变量Plugin内容/容器名外的稳定字段一致。候选完整198题已进入执行，自动原生gate签发仅在冻结0.8080808080808081门槛通过后执行。当前控制作业仍运行，未测出候选完整分数。

2026-10-23 02:50（Asia/Shanghai）小时监控：candidate-01原生最新完成140/198、107题strict匹配、0超时；当前分数为中间观察，不能与A1完整分数作正式退化判定。有限控制作业PID/starttime匹配，服务32请求持续生成，尚无candidate完整run-record或gate。继续已有作业，不追加请求、不修改门槛或服务参数；性能重复性问题状态未变，本轮静默。

## 完整精度失败与诊断（2026-10-23 04:14 Asia/Shanghai）

候选完整198题于03:16结束，原生strict exact_match=147/198=0.7424242424242424，低于冻结160/198=0.8080808080808081，净少13题/6.5657个百分点。有限控制作业exit1，原生验证最后的score_check明确拒绝，未生成成功run-record或candidate gate。当前决定为blocked-by-accuracy；正式性能和新性能优化均不推进。没有改评分、门槛、模型、vLLM、Plugin/Gems优化逻辑或冻结服务参数。

已使用本地inference-accuracy-diagnosis Skill冻结事故accuracy-regression-001；分类为verified_score_regression_root_cause_unresolved，gate_blocking=true。事故路径accuracy-diagnosis/accuracy-regression-001/incident.json，SHA8012b5b5ee206c067fff70c06aee6155ce4b5b928da7203db0a3a0ad1dfe606e。调用原始冻结acceptance.verify_run_record对内存中的失败记录核验，全部输入、provenance、服务、198唯一题目和每组396条strict/flex样本行检查后，仅在最后候选低于门槛处触发预期异常；未修改工具、发布伪记录或降低阈值。原始results SHA8bca1b48f4747b95c7eabf6e5a4c426c66987f6ce9a0c2e8cf014a0395478ed4，samples SHA03b35d5a239e15b199f16a79a3575aac5089eb86cca34ffb7ceb6b7b6c66faff。

逐题核对两组198题doc、prompt、目标答案、生成参数完全一致；strict结果134题均对、26题从对变错、13题从错变对、25题均错。两组所有完整生成文本不同，不能用换题或最终progress的0/0显示问题解释，也不能单凭分数下降就断定某个源码改动是根因。原生flexible-extract分数方向相反，冻结验收只使用strict exact_match，未换指标。

最小复现选取短的discordant doc13，另保存doc139及反例doc129完整原始样本，均仅留远端。通过同一evaluator原生OpenAIChatCompletion._create_payload恢复请求，原生HTTP seed1234、temperature1、top_p0.95、top_k20、65536预算、stop保持不变；lm-eval seed42单独记录。序列化prompt实际是单元素list中的JSON chat串，首版纯准备脚本因未支持该包装而在发请求前停止；v2显式解包后完成，失败脚本保留。未缩短生成预算，C1相对完整C32属于预声明诊断差异。

B candidate-01三次同请求均HTTP200、生成2831 tokens，完整文本SHA均为dcf9643435e8296f6a41fe67b4984ca85b7ec72252dd06d7897f093cd59f05e3，前后两rank RPC成功、无hook/proxy。该C1请求可重复，尚不能解释C32完整分数差。随后归档并启动唯一有限作业jobs/accuracy-repro-bab-001，按相同冻结配置切换原A revert-01→候选B candidate-01-r2，每臂graph/C8/manifest验证后同请求三次。只通过精确PID/starttime停止当前服务；源verify容器、GPU2/3未操作。控制器commands/run-accuracy-reproducer-bab-001.py SHA9938c57472ad2769bfd41f730dd959d683aec4540dd5f1453f4afb3f02c94105。

根因置信度unresolved，无源码修复、无精度恢复声明。B/A/B若C1不区分环境，再扩大到忠实C8/C32 cohort并定位首个实际执行差异；不得依据单次短样本宣布解决。最终必须有单变量/重新启用证明、机制证据、相关graph/C8/rank边界回归及保持原门槛的新完整198题原生gate，才能恢复正式性能。FGV在A/B实际worker中都未加载，安装归并与editable一致性不能冒充FGV内核运行覆盖。

小时监控qwen35b继续ACTIVE，仅通知重要阶段/失败；continuation.json改为精度诊断并以实际current_job为准，旧full控制器不重放。所有11轮性能失败证据继续保留；精度恢复后另行解决原基线重复性，若改稳态契约则对全部角色/场景同契约重跑。

原A revert-01的graph/C8及manifest通过，三次同请求也均生成2831 tokens、stop结束，全文与初始B三次完全相同；原A summary SHA26f9a60bc24c8b67555805ab890c0ea4f95c48d81f4b53431d64deb2b9eaa019。C1六次目前未复现A/B差异；有限控制器已精确停止A并启动candidate-01-r2，处于candidate_reenabled_loading，PID/starttime身份匹配、无结束回执，等待第三臂。源verify容器仍运行保留。采样器constructor/forward/forward_native/filter及GDN forward的运行时字节码指纹在已存A/B两rank快照中一致，未覆盖的helper/批处理执行差异仍需检查；旧call_op与新CachedOp结构差异不等于内核数值差异证明。

本地三阶段schema4、精确门槛/无gate、九条incomplete性能指标和实验文档链接核验通过。全项目记录检查仍报告其他既有/并发案例的缺失链接和过程产物问题；未修改这些材料，此检查不承担模型精度或性能验收。

## C1完成与固定C8诊断（2026-10-23 05:04 Asia/Shanghai）

有限作业accuracy-repro-bab-001已exit0。B candidate-01、原A revert-01、重新启用B candidate-01-r2各三次，共九次同请求全文完全一致，均为2831生成tokens，九次输出SHA仍为dcf9643435e8296f6a41fe67b4984ca85b7ec72252dd06d7897f093cd59f05e3。比较回执bab-controller-001/comparison.json SHA20c7df8ae25dc97b46ee1a5d55315f17b49f185a6494b89d616429149fbd1521；重新启用B summary SHA71e42d2a3d30d6030e57032d407117e5e9eef073e354be890c7aa6b5a2b25d6c。三臂原生回执/输出SHA逐项重验、当前B精确PID/starttime及空闲原生metrics通过。结论仅为C1未复现，完整147/198失败和无gate状态不变。

静态源码明确shortlist支持batch8–64，C1未覆盖此分支。A/B的_use_shortlist_filter、_supports_shortlist和普通filter函数AST一致，shortlist实现文件SHA同为bed706146946a24aa457002d9d5997b9d87e1e227b4e75298f85ba1d2aef1227；采样文件差异主要含生命周期接入，未据此认定代码导致精度下降。静态支持条件、已加载采样器对象不等于本组请求实际shortlist内核计数，后续机制归因仍需命中证明。

在任何C8流量前冻结plan：保留初始doc13/139/129，再按max(A_tokens,B_tokens)从其余discordant pairs取最短5题，tie按doc_id，得到[13,139,129,121,92,29,44,49]。各题原生prompt、HTTP seed1234、temperature1、top_p0.95、top_k20、65536预算、stop完全保持；每臂3次完整重复、每次并发8，三臂共72请求。C8的题组/并发与原198题C32不同，仅用于诊断，不评分签gate。plan路径accuracy-diagnosis/accuracy-regression-001/c8-cohort-001/plan.json，SHA5c15a2d11f64f902ae745dff8d4e89fae1435d868b089592ceff127e28848354。

唯一有限作业accuracy-repro-c8-bab-001已启动，服务顺序candidate-01-r2→revert-01-r2→candidate-01-r3。后两臂只用原精确停止器、冻结launch v2、graph/C8及manifest核验，源码/参数保持不变。控制器commands/run-accuracy-c8-bab-001.py SHA66e95150a529753f62bf61208214508ce35a5875babb0a58c811d8e6d7e47859；请求入口commands/run-accuracy-c8-arm-001.py SHA04e8480580038940658c8f746d138c74ef86bae584c37e5ec5a42bb88b244b99。每组原生metrics必须观察到8个running请求，保留所有响应、token/finish、前后两rank取证；请求/身份/并发证据失败即停止后续且无重试覆盖。全部重复及三臂输出都保留，不挑有利轮次。

当前处于C8 candidate-initial，作业精确身份匹配。若C8臂内不稳，先定位固定cohort的调度/批量与数值随机性；若出现稳定A/B区别，再做实际执行边界单变量二分；若仍一致，预声明原始first32 cohort推进C32。根因继续unresolved，不改strict指标或门槛，不以诊断恢复代替新完整198题正式gate，正式性能保持阻塞。小时监控已切到本作业，旧C1命令不重放。

05:08中间观察：C8初始B已完成首组8/8请求，原生metrics实际max_running=8，receipt SHA8314527beff86bd2d8a12a4b49c4b0cea6d46d3168c322caaaf20fd59b929b75；第二组推进中，当前共12/24请求落盘。只确认诊断流量与真实并发成立，不对尚未完成的臂内/臂间结果作结论。三阶段schema4、生成README下一步、无gate/精确门槛、实验链接和九条原性能incomplete指标重新核验通过。

## C8原环境也有波动与同题批大小诊断（2026-10-23 06:06 Asia/Shanghai）

C8 B/A/B有限作业已exit0，72响应、9组原生并发回执及各臂前后两rank快照/SHA逐项核验通过。每组实际max_running均8；同组请求发出时间跨度1.27–2.01ms。所有8题在每臂的三次重复中各有3个不同全文，原环境A也不例外，尚未形成稳定A/B差异。comparison SHA0616dc8d2941566db4c636a6d7715612b5d3482c2533569ccefe4f015f0d5e3b；分类batch_seeded_repeatability_variance_observed_not_causal_proof，根因仍未定位。

为区分全文差异是否影响冻结strict指标，在同一evaluator离线使用原生RegexFilter→TakeFirstFilter→exact_match_fn，严格复用原results中的filter_list及ignore_case/ignore_punctuation。先对原A/B各198题逐题重算，全部单题指标与原样本一致且总数精确160/147，再对全部72个C8诊断输出记分。固定8题三轮答对数分别为初始B[7,8,6]、原A[6,7,6]、重启B[7,6,6]。因此旧环境自身也有并发strict得分波动；这只是固定8题的诊断证据，不能据此认定完整少13题已被随机性解释，更不能替代198题gate、换指标或选最好一次。报告c8-cohort-001/verified-native-diagnostic.json SHAb3258d2da7c565af56c2ab9bdee076d111c8b2337d508deb4ebab11acd8d3082；核验脚本commands/verify-c8-native-diagnostic-001.py SHA8fb2682824a27ac7c6fa4d86ff1e7575267283d4213511a9da25097b96b2f94a。

下一单变量诊断固定doc13同一原生请求/seed，分别用C1、C7、C8的相同prompt副本，每个批大小三组，共48响应；不向HTTP请求加入copy_index，不改变采样参数或65536预算，不重启当前candidate-01-r3、不修改调度器。请求准入仍使用与上一诊断相同的barrier自由提交。执行前冻结homogeneous-batch-001/plan.json SHA61d30d5bbbf4cf68d1522a91aa426c994c195fee7f435b1c254eab502c5ca227，有限作业accuracy-repro-homogeneous-001，入口commands/run-accuracy-homogeneous-batch-001.py SHAe650e62ecfd9f74440a35bd856abf4f186ffb4bf2335846412671dbeac0c232f。计划明确这仍是模型批大小/构成边界诊断，不是shortlist单算子的隔离证明，也不是正式精度。

当前中间观察：C1三次均为原2831tokens的相同全文；C7前两组实际并发7、7份同prompt/同seed的输出各有6种全文，后续尚未完成。按源码静态条件，C7低于shortlist下限8，故下一步应检查实际RNG/数值与请求位置，而不能只围绕shortlist归因；仍需实际shape/命中证据。原生random_sample源码对每个请求generator执行exponential_后取probs/q的argmax，已只读核对，未改vLLM。原生pause/resume/is_paused接口仅作只读发现，未调用暂停；如后续使用固定队列准入，必须单独预声明并确保恢复，不把接口存在当作批次已固定证明。

完整候选147/198<160/198、无gate、正式性能阻塞均保持。continuation/小时监控转到同题矩阵，旧C8作业不重放；结果须保留全部组、验证真实并发和两rank路径，然后再决定RNG组件对照、固定准入或C32诊断。源verify容器、GPU2/3、模型/优化逻辑/冻结启动参数均未变。

### 同题矩阵完成、RNG参考及原生概率观测

同题48响应/9组矩阵已exit0且全部原始输出SHA、实际C1/C7/C8回执通过；summary SHA87ff588b17a0526620d63d1c233b24d665edfb165fe3293ddbc4244c8e41fd10。C1共1种全文，C7的21响应共11种、每组各6种；C8的24响应共19种、三组分别6/7/6种。既没有去掉重复或较慢输出，也未修改请求seed或预算。尚不能用批大小差异隔离某一个算子。

在矩阵完全结束、当前服务身份/空闲核验后，仅空闲GPU0和CPU执行原生RNG组件参考：FP32、vocab248320、seed1234、batch1/7/8，每项三次，分别创建独立同seed生成器填充连续行view的exponential_；另将实际vLLM文件中的random_sample函数AST原样在只含torch的namespace执行，输入各行完全相同的均匀概率。CPU和CUDA各项都满足行间随机数一致、重复间一致、同概率采样token一致；未复现“同seed因行offset产生不同随机数”的组件假设。报告native-rng-probe-001.json SHAc975375ff67d1cfaff8b12fbde5f5ad5be4e37855f18f60b66d69fc144602d1c；执行前后两rank只读快照通过。该参考进程未加载模型或FlagGems注册，不等价于服务实际generator状态、算子dispatch或整个采样器通过。

06:20已启动唯一有限作业accuracy-repro-logprobs-001，仍用candidate-01-r3，同题C7三组共21请求；只增加原生logprobs=true/top_logprobs20观测字段，原prompt、seed1234、temp1/top_p0.95/top_k20、65536预算和stop保持。plan homogeneous-logprobs-001/plan.json SHAff246ee734356ce01ddd1ab40e76efafc7e3d88f192e608f8c8b4e7e3436fe51，入口commands/run-homogeneous-logprobs-001.py SHAee2c3ad1933da0e3e6c68c0cbdee74a09e4565d27ac434a53091b5115334bb1e。计划要求保存全部响应、核验真实C7和两rank路径，并比较首个分歧token、step0及同一步报告的raw top20分布。

API logprobs有限精度、可能是过滤前概率，观测字段也可能改变时序；相同报告值不等于精确logits或RNG状态相同，不能直接凭显示值认定根因。当前分类仍为完整分数回归待定位，并发重复性问题在旧/新路径都存在。下一步在真实服务内继续区分generator/offset与模型数值路径，所有诊断均不能签发gate。小时监控及continuation已转到新作业；正式精度门槛和性能阻塞保持。

本轮结束前原生logprobs诊断已完成14/21响应、两组C7，第三组进行中，作业PID/starttime匹配、尚无result/summary，未对局部概率作结论；源verify容器仍运行保留。当前三阶段schema4/README、无gate/精确门槛、实验链接及原9条incomplete性能指标核验通过。小时监控继续观察本唯一作业。

## 准入相关重复性复现与原A/候选B配对（2026-10-23）

自由准入C7 logprobs三组21响应已全部完成、SHA/实际并发/前后两rank及进程一致性核验通过，summary SHA7513f08612cc5ff62ef1f98d7d2ffe21dbe1b7e0cbca3228eb54874fdf907699。18个锚点对中17个在首个生成token的报告raw logprobs已不同，首步最大差0.7874298095703125；17个全文不同的对，首个token分歧在索引257–301。实际/server_info的model_config.logprobs_mode为raw_logprobs；本机vLLM Sampler.forward先计算raw logprobs，再做温度/惩罚及RNG，故观测不能仅由随机数不同解释，但仍不是精确logits或首个不同模型层的证据。

在同一candidate-01-r3、同一rank实例/源码/启动参数/HTTP请求字节下，预声明三组C7受控准入：原生pause mode=keep、clear_cache=false，7份请求都提交并保持暂停2秒，再由finally resume并验未暂停。全部admin命令/回执先归档；每组三个暂停状态检查与恢复检查均通过，实际running=7。21响应不仅全文完全相同（各2907生成tokens），整个报告logprobs序列也逐字相同。summary SHA03a83734abce73aa7b11be572b3b92ac6878e60ca1cc2ede35d299a3cbb88d22。最大running、暂停和提交时序本身未证明设备上精确prefill batch shape，未据此声称内核命中。

随后撤销准入控制，用原自由barrier方式重启用三组C7，HTTP请求字节仍完全相同：21响应出现14种全文，16/18锚点对首步报告概率再次不同。summary SHA5a2994a905af84c226ae005bb9b7a2a1cf7ab6750978478791b1cc5457650b13。自由→排队→自由共63响应完整核验，分别有8/1/14种全文、9/1/14种完整报告概率序列。准入条件对该C7重复性现象的控制已复现；尚未隔离具体数值实现，也未解释完整198题少13题，更不能把排队诊断当原rolling-C32业务精度gate。

循环汇总admission-parity-001/admission-cycle-verified.json SHA2f08ce6d581c17064e9f8bce5af325a1d0da3a6c3fc46eb5cb7f424b8c412aa9。代码/模型/优化逻辑/冻结启动参数均未修改，服务已恢复未暂停，无权重、sleep或cache-reset接口调用。原147/198失败、160/198精确门槛、无gate及正式性能阻塞保持。

为比较迁移前后而非只比较准入方式，已启动唯一有限控制作业accuracy-admission-parity-001：当前B candidate-01-r3受控C8→原A revert-01-r3受控C7/C8→重新启用B candidate-01-r4受控C7/C8，每项3组，新114响应；B初始受控C7引用全部既有21响应。所有case用同一原生请求体及采样预算，按各自C7/C8比较全文和完整报告raw logprobs。原A/新B切换仅用精确PID/starttime停止器、原冻结launch v2、graph/C8/manifest核验。每组finally恢复，恢复失败只精确停止本案例服务，不影响源verify或GPU2/3。

配对plan SHA cb500a547ad9b39338dc695bd9d790223d214c529fa5278bdc2fea177ee144f5；控制器commands/run-admission-parity-001.py SHA7cfd6a672c5a28edc8c23e11f22c91ce251cce09e48bce5252df245e39e177de。初始B C8已完成两组/16响应，控制器身份匹配，余项运行中。C8只增加shortlist适用批大小边界，未把静态支持当执行计数。单题配对即使完全一致，也不是完整198题验收；如下一步需要改变正式精度workload/并发/契约，须先形成可审核方案并取得用户授权，不悄悄换成新gate或挑最好完整重跑。小时监控/continuation及三阶段状态已切到当前唯一作业。

本轮结束前，初始B受控C8三组/24响应已完成且控制器核验通过，已按精确停止器结束B并进入原A revert-01-r3加载；控制器PID/starttime匹配，无最终result。源verify容器仍运行保留。新114请求未全部完成，尚无原A/候选B配对结论；不重放当前自动控制器。


## 受控配对完成与异题 C32 前置诊断（2026-10-23）

既有配对作业已退出0，comparison SHA83b939a6e62a2635e78ffe13901f8ee80e3983340cdd2d8625398b3a720b0918。C7和C8各自的原A、候选B及重新启用B均只有一种全文及一种完整报告logprobs序列；只覆盖doc13的同题复制，完整147/198失败未解除。现服务candidate-01-r4，原生is_paused=false。

执行前预声明：先独立核验全部135响应（新114、复用全部初始B C7的21响应）、admin恢复回执和两rank；再通过规定评测容器原生payload builder冻结原集合doc0..31，当前B受控C32三轮共96请求。请求不增加logprobs，原prompt/seed1234/temp1/top_p.95/top_k20/65536预算/stops不变。队列顺序/精确设备shape仍未证明；此实验检验异题重复性，不能冒充原rolling-C32完整门禁，也不改变任何正式契约或160/198门槛。若重复性不足，不扩张成完整198题挑分重跑；若可重复，下一步先冻结原A/重新启用B配对，再形成完整198方案。必要的正式workload/并发/契约变化须单独获得用户授权。

远端唯一执行清单：`/public-flash/jinghao/qwen3.6-35B/20261022-qwen36-35b-mx104-stack-regression/commands/first32-queued-001-execution-plan.json`，SHA27d1a3d8d9a6773b3b9692f2b7b7adf73c752af9744aa471dde5011e4c03e44b。脚本均先归档并核验SHA后执行：

- `/public-flash/jinghao/qwen3.6-35B/20261022-qwen36-35b-mx104-stack-regression/commands/prepare-first32-queued-001.py`，SHA1e70689ae8ecddbf3dc47d5a88dc3717f2fcbf5d11b33d38e48ad0d217073b58。
- `/public-flash/jinghao/qwen3.6-35B/20261022-qwen36-35b-mx104-stack-regression/commands/run-first32-queued-001.py`，SHAa946b90bac4faa5a5a5173154aa3866dd7813d4d1d6f6ced63a1add5a964d672。
- `/public-flash/jinghao/qwen3.6-35B/20261022-qwen36-35b-mx104-stack-regression/commands/verify-admission-parity-002.py`，SHA0172ec6407fca2ebe1be84a07c031b18ccc9e8bcf79e173aab9ce3727a4b9727。

三轮C32已退出0，96响应已保存；summary SHA1133554550019bfe58b69748b317a4b9a9977e27980ba8298dfca4e524887148，仅2/32题全文三次相同，未扩大A/B或full198。新增原生离线核验命令先归档：`/public-flash/jinghao/qwen3.6-35B/20261022-qwen36-35b-mx104-stack-regression/commands/verify-first32-native-001.py`，SHA89d72b258fbec62c07f9cd8bfcb8aa550b9fa1905b7c62b43ba318c21e7ccc46；通过规定eval容器python3执行，不发送生成流量。

原生离线评分已核验96响应、三组真实C32、两rank与全部恢复回执，strict答对[26,25,24]；报告SHA98325b4bddb155a933abd09120c29da0250fbcbcaabe122e4bf69da1dc3f3692。当前profiler=null，实际worker在profile()会拒绝未启用profiler。准备仅临时增加原生profiler配置的审阅草案；不启动、不停服务、不发送生成。准备命令`/public-flash/jinghao/qwen3.6-35B/20261022-qwen36-35b-mx104-stack-regression/commands/prepare-execution-profile-proposal-001.py`，SHAf29048a020150e1802e29a8440dfc563d07a3889abcd069a3bc718b8b2574dc2，归档后host python3执行。

配置草案首轮独立进程未传MACA_PATH/HOME，平台插件导入记录TypeError，虽配置类返回valid，不能据此宣称诊断服务/实际profiler已就绪；不影响现有服务。保留首轮证据，使用原launch的完整冻结环境做纯配置校验，命令`/public-flash/jinghao/qwen3.6-35B/20261022-qwen36-35b-mx104-stack-regression/commands/validate-profile-config-frozen-env-001.py`，SHA2fd7801bc8e7c2f9160f396d82eb1afb460198d6540c13dffe9a4e0114863ed1，归档后host python3执行。

### 下一步审阅方案：只临时开启原生 profiler

这是精度定位的执行路径取证，不是新的性能优化，也不调整正式精度的 workload、过滤器或阈值。当前 `/server_info` 实测 `profiler_config.profiler=null`；原生 `gpu_worker.py:846` 的 `profile()` 会拒绝未配置的服务。原生 pause keep 仅停止调度，API客户端已开始、暂停保持2秒及最大running32，均不足以证明引擎入队顺序和设备执行形状。异题32的预声明诊断已经否定“仅这样排队即可获得可重复完整评测”的外推，因此不扩大成完整198题重跑。

待用户授权的唯一启动差异为追加一个 `--profiler-config` 参数：

```json
{"profiler":"torch","torch_profiler_dir":"/public-flash/jinghao/qwen3.6-35B/20261022-qwen36-35b-mx104-stack-regression/profiling/accuracy-execution-001/traces","torch_profiler_with_stack":false,"torch_profiler_record_shapes":true,"torch_profiler_with_memory":false,"torch_profiler_use_gzip":true,"ignore_frontend":true,"delay_iterations":0,"max_iterations":128,"warmup_iterations":0}
```

只操作专用B容器与GPU0/1。使用精确PID/starttime停止当前服务，按原argv/env加上述观测配置启动新诊断实例；验证graph capture、两次replay和C8。用已冻结first32原始请求执行两轮，每轮只采前128个engine iteration，生成参数/65536预算完全不变，保留全部64响应。两rank必须各有新产生、非空、可解析trace；按原生 `execute_context_N(T)_generation_N(T)` 标注区分Prefill/Decode/Mixed，缺少形状/调用链证据时明确incomplete，不把图回放的静态支持当作内核命中。Profiler会扰动时序，trace本身不能证明未观测服务的数值根因，采集时长不能作性能收益。

任一身份、请求、恢复或导出失败即停止后续采集、保留所有结果；使用精确停止器恢复原冻结启动配置，重新做graph/C8/manifest，不签发或rebind精度gate。源verify、GPU2/3、vLLM/Plugin/Gems源码、模型、正式精度与性能契约均不改。该临时启动参数例外必须先获用户授权；当前仅准备草案和配置类校验，没有启用profiler、没有切换服务。


### 用户已授权临时 profiler 取证并恢复

用户直接回复“允许临时取证并恢复（推荐）”，仅例外允许追加已审阅profiler配置；正式精度/性能契约和160/198门槛不变。原生配置类已在完整冻结Maca环境校验，无平台插件导入错误；这仍不是实际capture成功证据。授权记录与工具执行前归档：

- `/public-flash/jinghao/qwen3.6-35B/20261022-qwen36-35b-mx104-stack-regression/environment/profile-001-authorization.json`，SHA730941388a6064602fa59fa74a7ae5262a2fae3b76d68f7e52f59e25b1eb49bf。
- `/public-flash/jinghao/qwen3.6-35B/20261022-qwen36-35b-mx104-stack-regression/environment/launch-config-profile-001.json`，SHA77eef9d759b40a7391a8f401f894147a63bbb6ddeed5648efd1a106b19119ad6。
- `/public-flash/jinghao/qwen3.6-35B/20261022-qwen36-35b-mx104-stack-regression/commands/launch-service-profile-001.py`，SHA40b0a8e5c1d7d9f86d3cc13c4b101015d8051127b1e216ce51d807f4e5249822。
- `/public-flash/jinghao/qwen3.6-35B/20261022-qwen36-35b-mx104-stack-regression/commands/qualify-service-profile-001.py`，SHA3366213b5c8a4046e95eb6fd7b0237f0a175630d7eb383f4f5c158fc6af36c11。
- `/public-flash/jinghao/qwen3.6-35B/20261022-qwen36-35b-mx104-stack-regression/commands/create-service-manifest-profile-001.py`，SHAcfbca49c5d421709cd4198f80d2602cabff5ba683962f59e685fa6a10bbfe1f6。
- `/public-flash/jinghao/qwen3.6-35B/20261022-qwen36-35b-mx104-stack-regression/commands/run-accuracy-execution-profile-001.py`，SHA3b72d1bd9f85925f63f9865e6ca51e6e48d4acc4c27ac205da16a02c1ebdaaf2。

唯一执行清单`/public-flash/jinghao/qwen3.6-35B/20261022-qwen36-35b-mx104-stack-regression/commands/profile-001-execution-plan.json`，SHA44f384a4eaf194791943d3981d03a97ef861ff459df52aa70a69ccfc2e26531b。有限作业`accuracy-execution-profile-001`自动按candidate-01-r4→r5观测→r6原参数恢复，独立派生工具不覆盖冻结原件。两轮每轮原first32请求、前128 worker steps，所有HTTP字节与采样预算不变；第一轮原生profiler表在第二轮前另存唯一副本，四份trace须证明两rank和Prefill/Decode覆盖。失败保留证据并进入精确恢复，不选择性补跑。


最新进展（2026-10-23T03:12:17.161836+00:00）：受控同题C7/C8的原A、候选B、重启B全文与完整报告概率序列全部一致，独立核验135响应、90组管理命令回执。该结果未推广到异题：固定doc0..31的三轮C32共96响应全部有效，原生strict答对26/25/24，仅2/32题全文可重复。完整候选147/198仍低于160/198；根因未定，正式性能继续阻塞。

用户已明确授权临时仅增加原生profiler配置并恢复。有限作业accuracy-execution-profile-001已启动：candidate-01-r4按精确绑定停止，candidate-01-r5正加载；两轮固定C32各采前128 worker steps，结束或失败后finally恢复candidate-01-r6原冻结参数并重验graph/C8/源码与真实路径。当前无trace通过声明，不改任何优化源码、模型、采样参数或门槛，源verify及GPU2/3保留。原生工具未覆盖；独立profiler脚本、授权、配置和执行清单全部先归档并核验SHA。


临时观测实际启动核验（2026-10-23T03:16:05.317017+00:00）：candidate-01-r5已通过graph两次replay、C8和完整manifest核验，manifest SHA7ee808dbab8ececaf6a9334e386eb321e30b2a807a90b1f4ba69f56fa556fc93，qualification SHAb3d0bbd50870d22f9b3949f27131ba1fe9e75aba040e2ecc5a1a5fd4b4a9cd3e。控制器PID/starttime匹配，原生start_profile返回200、pause/resume恢复回执通过，当前未暂停，真实running32/waiting0。首轮已出现两个rank命名trace文件，但64请求尚未完成、完整trace有效性/第二轮/原配置恢复仍待有限控制器完成；不得据文件存在宣称采集或回归通过。小时监控保持ACTIVE并更新为此唯一作业。


### 首轮观测的阶段标记接口差异与剩余一轮（预声明）

首轮trace实际包含Plugin WorkerFL.annotate_profile生成的`execute_new_N_cached_N`，并非vLLM原生`execute_context_N(T)_generation_N(T)`。我在校验器里预设了原生标记，未先核对Plugin的覆盖实现；这是证据解析接口不匹配，不是模型或采集失败。原控制器/plan不覆盖、不改写，待其完成当前32请求后按原停止条件自动退出incomplete并恢复r6，保留该原生失败回执。当前源代码核对WorkerFL worker.py:778–791/845–848说明标记覆盖execute_model，step由原生profiler维护。初步读取两trace各128个CPU Plugin迭代标记，分别new24/cached0一次、new8/cached24一次、new0/cached32共126次；两rank均有126个mcGraphLaunch、GDN chunk和packed-decode kernel、shape事件。new/cached不能直接当Prefill/Decode token数，必须结合graph/GDN/tensor形状；mixed只作new/cached代理，缺口明确保留。

初读每rank还各观察到`_prepare_candidates`和`_scatter_candidates`128次；实际shortlist源码先topk64后prepare、安全性检查、softmax/cumsum、scatter。这支持本观测窗口shortlist实际执行，不能由此证明完整198精度或所有shape覆盖。最终须由完整32响应、进程/恢复和两rank源代码指纹校验后归档，当前不把初读冒充最终通过。

新的独立解析器只修正实际Plugin标记接口，并检查128步/rank、真实设备/shape/graph/GDN，保留旧失败。只有第一作业已恢复r6、错误恰为标记不匹配且首轮32响应全部有效时，才启动剩余一轮32请求，使用同一用户已授权profiler配置与同一请求字节；不重跑第一轮，不挑分，不扩大64请求上限。后续独立服务r7→原配置r8恢复，仍精确停止并graph/C8/manifest，原计划和工具均不覆盖。

- `/public-flash/jinghao/qwen3.6-35B/20261022-qwen36-35b-mx104-stack-regression/commands/verify-plugin-profile-capture-001.py`，SHAe52c55e7b33512159363dd13fa496d9923ef5024cf5a42eb6d0fcff4fc1f3ca7。
- `/public-flash/jinghao/qwen3.6-35B/20261022-qwen36-35b-mx104-stack-regression/commands/launch-service-profile-002.py`，SHAa643ebe7c5ecd728cdaed2d3cfbbc2b5d2f1d25b7125777b5bcb553130103149。
- `/public-flash/jinghao/qwen3.6-35B/20261022-qwen36-35b-mx104-stack-regression/commands/run-accuracy-execution-profile-002.py`，SHA06d007c15944e9aa3e943e00e2505bb6fe3de1ea33bc01237f509c619da54a4a。

唯一执行清单`/public-flash/jinghao/qwen3.6-35B/20261022-qwen36-35b-mx104-stack-regression/commands/profile-002-execution-plan.json`，SHAc6008b57d1f082851771e294190377beb1f67fb3a4b1833c5708a1f52c045732；当前仅归档，第一控制器仍在运行时不执行后续变更。

为避免等待小时轮询空档，追加一次性有限依赖控制（非重复automation）：只观察第一作业精确PID/starttime与原生result；等其全部32请求完成且原配置r6恢复通过，独立校验首轮实际Plugin标记后才派发剩余一轮32请求。若第一作业已成功完成64则不再启动；其他错误/超时/身份变化均停止、不扩大请求数。原current_job仍由第一控制器持有，pending_profile_followup单独记录，不并发打流量或手工切服务。命令`/public-flash/jinghao/qwen3.6-35B/20261022-qwen36-35b-mx104-stack-regression/commands/run-profile-followup-001.py` SHAc80c80ed36e51a36f02720316f5da396717c2482df2a490fe72abe2e6529f090；唯一执行清单`/public-flash/jinghao/qwen3.6-35B/20261022-qwen36-35b-mx104-stack-regression/commands/profile-followup-001-execution-plan.json` SHA021d7d2874e874e07fa7ff7b1db0bf90cf0ae33c748c3bdeb7a7939754780b59，先归档后执行。


### 第一控制器真实失败位置与共享盘时钟核验

第一作业已退出2，全部32请求完成，原冻结配置r6恢复/graph/C8/manifest通过（restoration SHA0c1a58eb45b358d09a88b1c603afc0b40fae9f9d439ba10df5dc28a545337acf）。实际先失败于`mtime >= host_capture_start-2`，capture-error SHAeca38cb246ba71bca51ccfd9f4c600d8b701de410fcdab72a535c2ade5f545d1；此前提到的Plugin阶段标记是独立的下一处不匹配，并非此原生失败的实际第一位置。有限followup的严格错误分类守护因此退出2，没有启动额外流量或服务，错误与原作业均保留。

五份同进程先归档的start/resume/stop命令及回执显示，共享盘mtime相对Host时钟约-214.79..-214.83秒；原生trace文件名导出epoch在capture窗口内，baseTimeNanoseconds+CPU事件ts与Host start/stop吻合，两trace含正确worker PID94237/94238，初始trace inventory为空。不能把不同时钟域的mtime直接比较，也不能通过改文件时间来凑通过。新解析器交叉要求：新文件/原生导出时间、原生CPU事件epoch窗口、实际rank/PID、从该轮命令/回执测得且spread<1秒的文件时钟偏差、归一化mtime窗口、128个实际Plugin标记、设备/shape/graph/GDN以及全部32响应。若任一失败仍不启动剩余采集；不是放宽精度或性能契约。旧mtime失败与stage-guard失败不可改写为成功。

- `/public-flash/jinghao/qwen3.6-35B/20261022-qwen36-35b-mx104-stack-regression/commands/verify-plugin-profile-capture-001-v2.py`，SHA729be22578907717cc940c8e63c7118f1df8f3aae4fcc55644c24ddd9e88e6d4。
- `/public-flash/jinghao/qwen3.6-35B/20261022-qwen36-35b-mx104-stack-regression/commands/run-accuracy-execution-profile-002-v2.py`，SHA85802b978112234214b2434c1b2b0722ae98fa4874c263938bf7b385a54f3d62。

新唯一执行清单`/public-flash/jinghao/qwen3.6-35B/20261022-qwen36-35b-mx104-stack-regression/commands/profile-002-execution-plan-v2.json`，SHA184812c62c502af142bc4e32757d3e4a1c9d85d3936c499e48f70f208d4a5dbf。先只读校验第一轮；通过后仍仅执行第二轮32请求，使用原已批准profile配置，r6→r7→r8原配置恢复；第一轮不重跑、总计仍64，不新增任何模型/优化/正式契约变更。

首轮独立校验已通过，plugin-phase-verification-v2.json SHA95e7aeec077b89350bd9338fe7cf5d44b2bc3119ae3340dde067ca573dcaab50，全部32响应、两rank正确PID/原生时钟/新文件/128步及源码指纹均验证，shortlist prepare/scatter每rank各128次。只派发剩余32；不重复已完成的校验器。执行前进一步按实际trace区分CPU user_annotation与镜像GPU标注，只计CPU128步，避免重复计数。新控制器`/public-flash/jinghao/qwen3.6-35B/20261022-qwen36-35b-mx104-stack-regression/commands/run-accuracy-execution-profile-002-v3.py` SHA86a0196567f2d41c3301ee058427974ccc94b2c92e371b040d1218b094664677；唯一执行清单`/public-flash/jinghao/qwen3.6-35B/20261022-qwen36-35b-mx104-stack-regression/commands/profile-002-execution-plan-v3.json` SHA4e5b9b2da6de56419eb1e8b9ad4081a32dd058fbf552b76c95c6de2c229cf1b9。未执行的002旧版保留，不覆盖。

第二轮控制器002在启动前错误引用了仅允许r5的001启动器，被实例守护拒绝；capture-error SHA810338f1e84e22946dccda14cac373a1e87467380889ae2831b9db42903f8ec6。r7目录从未创建、未发送任何第二轮请求；finally原配置r8已恢复/graph/C8/manifest通过，全部旧失败保留。已修正实际command AST常量为独立002启动器（允许r7），而非只修正EXPECTED字典；执行前结构检查两处launcher引用均为正确002路径。新增唯一控制器`/public-flash/jinghao/qwen3.6-35B/20261022-qwen36-35b-mx104-stack-regression/commands/run-accuracy-execution-profile-003.py` SHA0ff20f4e60b256ec982e37562fcd6fb3aca31bf345c91335b20e8b664deac1c9；执行清单`/public-flash/jinghao/qwen3.6-35B/20261022-qwen36-35b-mx104-stack-regression/commands/profile-003-execution-plan.json` SHAcaa933ab093c39cf8101448ffe5c693535469ed2fdd7458b566b87de421f496d，强制检查前一失败仅启动引用错误、0请求及恢复通过后，仍只发剩余32，r8→真实首次创建r7→r9原配置恢复；不重复首轮，总数不扩大。


最新状态（2026-10-23T03:55:38.580896+00:00）：首轮32响应与两rank各128步已由plugin-phase-verification-v2.json独立核验（SHA95e7aeec077b89350bd9338fe7cf5d44b2bc3119ae3340dde067ca573dcaab50），每rank shortlist准备/散射各128、graph126、GDN chunk60/packed-decode3780，实际采样优化命中仅属于此观测窗口。共享盘mtime与Host有约214.8秒时钟偏差，已用新文件/原生export、trace base+CPU ts、正确rank/PID和每轮管理回执校准交叉验证，未改任何文件时间或阈值。原001时钟失败、followup守护退出、002错启动器0请求均保留；r6和r8原配置恢复/graph/C8/源码路径验证已通过。

唯一活动作业accuracy-execution-profile-003已启动，真实首次创建r7且控制器身份匹配，目前服务加载/资格核验中；它只采剩余第二轮32，finally恢复r9原冻结配置，累计授权上限64不扩大，首轮不重跑。当前尚无第二轮/最终r9恢复通过声明。完整候选147/198仍低于160/198，无gate，正式性能继续阻塞，小时监控ACTIVE已切003；不重放旧失败或启动额外客户端。


### 两轮已完成，合并核验与原配置最终恢复

003原生退出0，两轮累计64请求全部完成、四rank trace已产生。最终r9原冻结配置恢复/graph/C8/源码与路径核验通过：manifest SHA639856ed77790b150fb42323e88c1af52a82e1d9726f48aa722d56c83f721565、qualification SHA4a2228b673657371da50989922aed6226257d196e2e195e04b2625586e3c6503；003 summary SHA69ff91d57fa5a91e0574fd33b2871cc2afac21694ac767374e37e50b230b9e32。第二轮实际新请求接纳分组23/9，第一轮24/8，后续均126个new0/cached32；这个事实已否定仅pause+全部客户端开始+2秒保持即可固定异题执行分组的假设。它不是完整少13题根因证明，也不能把cached当纯decode token数。

执行前归档只读合并校验：核验全部64输出/请求字节/原生strict分数、四trace/rank/阶段与采样kernel；再次用原生无观测RPC读当前r9，验证profiler=None、无hook与原r4全部稳定manifest字段一致，不新增模型流量。

- `/public-flash/jinghao/qwen3.6-35B/20261022-qwen36-35b-mx104-stack-regression/commands/score-profile64-native-001.py`，SHAdffd10186fc1771de3e88fbd664707df397aaf783f301a8a14fd84fe8b4b58e2。
- `/public-flash/jinghao/qwen3.6-35B/20261022-qwen36-35b-mx104-stack-regression/commands/verify-compare-profile64-001.py`，SHAb7db7a75c4cb101e24979f026a993eb15cf9c7271960662c7025e139fb86efb2。

唯一执行清单`/public-flash/jinghao/qwen3.6-35B/20261022-qwen36-35b-mx104-stack-regression/commands/profile64-comparison-execution-plan.json`，SHA6805511bdfb7b794d9bdcd1a6356f462f9b9947aef4d49857c7980b46eca2476。正式198题160/147及160/198门槛不变，旧失败不覆盖，未签gate或运行正式性能。


## 两轮取证/恢复最终核验与规划复盘 regression-planning-001

证据截止2026-10-23T06:00:21.307938+00:00。综合报告`/public-flash/jinghao/qwen3.6-35B/20261022-qwen36-35b-mx104-stack-regression/accuracy-diagnosis/accuracy-regression-001/profile-comparison-001/comparison.json` SHA4763b4ce64797265b702f1eb3bb35f899cea5d968a63d6a9a2fb474ab0e48734：两轮64响应、4份rank trace、全部管理命令/恢复回执、原HTTP字节和源文件校验通过；同32题仅4题全文相同、28题不同，原生strict分别24/32和26/32（仅诊断，原完整160/147逐题再次重现）。两个rank各128步都执行shortlist准备/散射各128次；后126步各有graph replay、packedGDN。实际新请求分组24/8→23/9，采样topk输入首batch24→23，embedding8192+2980→8192+2979，表明现准入控制没有固定执行分组；new/cached不是纯阶段token计数，具体doc归属/完整少13题根因未定。

最终服务candidate-01-r9恢复原launch v2，profiler=None，fresh RPC无hooks/proxy；与原r4除instance/runtime证据外全部manifest字段相同。fresh runtime SHA8a217f4baef2921b29c3a85df2e153871075704062e16dbc04298d57f79eb7a5，native offline scoring SHAbfe54ca2709629b5b7bbd6e84ebb8a2f2de0772147e12e1e92bb156fec1d143f，最终restoration SHAc4c0c2a659717671db2067c955873aba0640816afbcab358db86bc0eb1fefe03。没有重跑首轮或超出64请求，旧001时钟/阶段接口失败、followup守护失败、002启动引用0请求失败均保留。FGV两rank仍未加载，editable安装一致性不代表其内核覆盖。

复盘结论：保留原整理/editable/release0.2/采样生命周期组合，未在回归中叠加优化逻辑；完整147/198<160/198，门禁失败与正式性能阻塞不变；四正式场景均无有效累计A/B收益。首要下一步是只读核对原生入队确认和实际请求状态推进，准备可审核的确定准入/完整198方案；现R9日志未见Added/Received，不能臆造队列回执。第二方向只读对比A/B实际加载函数/dispatch及partial-prefill/cache/generator边界；不能用RNG单独解释此前RNG前raw概率差异。无稳定A/B区分不归因迁移，不改采样数值实现；任何必要正式workload/并发/契约或新启动观测参数变化必须明确方案并获相应授权，不能默改C1或挑最好完整重跑。两轮profiler授权已完成，不自动追加第三轮。小时监控继续后续只读诊断与方案准备，状态不变安静。

两轮授权范围已完成，无活动取证/评测作业。归档仅状态checkpoint命令`/public-flash/jinghao/qwen3.6-35B/20261022-qwen36-35b-mx104-stack-regression/commands/checkpoint-profile-completed-plan-001.py` SHA61f763bac55603d64e74faf413567f8eb0ee7eacdde91727b2c26c82a9ec4e17，host python3执行：current_job置null、003转last_completed_job，旧失败followup转historical、pending清空；保留旧文件和所有原始回执，next_actions改为本次复盘只读路径/完整198方案准备，不自动新增profile/正式试分。


### 原生发送确认与状态推进只读审计（执行前归档）

不再采集profile或发送生成请求。独立命令 `/public-flash/jinghao/qwen3.6-35B/20261022-qwen36-35b-mx104-stack-regression/commands/audit-admission-state-paths-001.py`，SHA55111719cccd1947f7421fb2db05da3fe7a34fec11da6a35bb3f7eae930308eb，先保存后执行；只读核验continuation/r9精确身份、已有两rank加载回执与A/B磁盘源码，外部新建轻量审计报告，不改服务或优化代码。必须区分frontend send完成与scheduler入队确认；不得仅凭Added日志推定设备batch固定。


### 有序准入审阅草案（只做CPU dry-run，不执行服务或请求）

只读审计已完成，报告`/public-flash/jinghao/qwen3.6-35B/20261022-qwen36-35b-mx104-stack-regression/accuracy-diagnosis/accuracy-regression-001/admission-source-audit-001.json`，SHA8fd84df02b6551808f60c588c6ad1f6ba2ef914a11c287140f8890a9ced3cdd6。实际版本`AsyncEngineArgs.enable_log_requests=False`，当前argv未开启，Added/Received均0；更关键的是，Added在`await add_request_async`之后，但该await仅等待ZMQ发送，不是scheduler.add_request返回。Core的ADD与UTILITY走顺序输入队列，因此“逐请求Added发送回执→同frontend/engine的is_paused utility回执”可作为待运行验证的FIFO屏障方案，不能把单条Added等同已入scheduler，更不能等同固定设备batch。

A/B实际加载的ModelRunner源文件分别SHA65b0ee22dd76307f13ec863fa67d2c070f38edfcd25304e90987f1fde556032b与86950f1d3ba43a271a05a14b5ae80e35c89d9ae6f922ac2f0a3130385350ec39，均与各两rank既有回执吻合；`_update_states/_prepare_inputs/_sample/_bookkeeping_sync/_is_all_reqs_chunked_prefill`五个方法AST一致，实际sampler.forward代码指纹也一致。Plugin与native都对partial-prefill丢弃样本执行generator offset回退4；这是源码同一性，尚未实测MetaX实际RNG offset消耗/回退不变量。上述证据不排除其他路径，也不证明迁移无精度影响或解释13题差值。

执行前归档：

- CPU-only协议守护模拟`commands/ordered-admission-dryrun-001.py`，SHA529ba7e3c26480785b86a9bb757c042374638e680f52dd2ddd8b369699a87cfb；对应结果SHA d9347f8a32e0f1c11b74393080f16b9a52b888e482cdb75bc4dc254bed25a097。只验证合成32/198请求及旧日志/错误PID/错序/不完整屏障等失败守护，0真实网络/模型请求；不证明native runner适配或实际队列/设备行为。
- 草案生成命令`commands/prepare-ordered-admission-proposal-001.py`，SHAca7d8fe1d444b988f1c206a0896591c5cabfcdd096f5f63ff3f8b3848b062bde。远端在同CASE新建ordered-admission-001/plan.json与launch-config.draft.json，仅原配置末尾加`--enable-log-requests`，其他argv/env不变，不启用profile、不切服务。

待审阅范围：仅B/GPU0/1临时开启原生请求日志；固定原doc0..31两轮共64诊断请求，原body字节与seed/temp/top_p/top_k/65536预算全部不变，以唯一X-Request-Id匹配新日志，逐项等发送回执、最后等待同引擎utility屏障后resume。任一异常停止下一轮、保留全部结果，finally恢复原冻结配置并重做graph/C8/manifest。新旧实例使用新目录和精确PID/starttime。该草案不请求替换正式198协议，也不签gate；原147<160失败保留。必要新启动日志flag超出此前“仅profile配置/64请求”的已结束授权，须用户明确同意才执行。

完整198后续设计也保留原生formal_accuracy→原llmrun、原task/filter/C32/65536/精确160/198门槛：先有受控区别和合理修复/回退，再执行预声明的完整一次；若确需将rollingC32改成有序waves32×6+6，必须先完成原生transport适配的CPU验证并另获明确授权。当前合成198 dry-run不是该适配实现，不能由此直接重跑挑分或宣称正式可复现。

草案已生成：ordered-admission-001/plan.json SHA7bf9bf7d9f8b0bf83f5a34531222a066506582d28a1e42608c87032688cd355d；launch-config.draft.json SHAde8f5163d1a76d2c0774bbaa20e76b06e38e47448135763f34f136505b786111。两者均未授权、未执行服务或请求。仅状态checkpoint命令`commands/checkpoint-ordered-admission-proposal-001.py` SHA c45c174fb154e5a20d97db22d8f1f56fbd4609f233db980f0ae011b75749e00b，执行前归档：current_job仍null、r9原服务不变；进入待明确授权状态，不重放已完成任务或反复发送相同问题。

仅状态checkpoint已完成，continuation SHA6c6392f9dca2a77ca3d9edb5d836de481357d74a3c886d8e097f32666f2c1976，phase=accuracy_diagnosis_ordered_admission_proposal_awaiting_authorization，current_job=null；candidate-01-r9精确身份已再次只读核验，未切换服务、未发送生成，正式精度/性能结果不变。当前新增规划仅写optimize视图，未签发/改写acceptance结论。


### 用户已授权原生日志有序准入取证并恢复（执行前）

用户直接回复“允许临时日志取证并恢复（推荐）”。授权记录environment/ordered-admission-001-authorization.json SHA511f65bd3bb936aa0ccdd1a072ec47fd06ab909efecf9fc3db2872fb4c35dfc0；原草案保留authorization_received=false，执行只接受独立新授权allowed=true。范围仍只B/GPU0/1、原first32两轮64，logger-only r10→原配置r11恢复，另原graph/C8资格验证；无第三轮/profile/正式协议变更/gate。

额外只读核对实际InputProcessor会将外部ID追加8位随机hex；解析器严格匹配外部ID及该原生suffix（不改随机化env），并校验API PID/新inode-offset/重复/提前响应。原计划中的唯一X-Request-Id仍只用于回执关联，body字节不改。当前server_info JSON原生端点已只读核实DP1/TP2/PP1，执行时重新核验单API/单EngineCore PID及此配置，不把源码FIFO推理说成直接读取队列内容或设备shape证明。

所有工具独立派生，不覆盖冻结原件；启动器/资格器只允许r10或r11新实例，恢复manifest沿用冻结原版（安全名称检查支持新编号）。真正controller AST与两份嵌套启动程序均CPU核验，避免只检查EXPECTED字典。CPU结果execution-cpu-validation-001.json SHAb23bd18d5990bc9d53ce36911e97eb3d2c7b6bebc290f00c2f2d7e10d757c06d，0真实请求。

归档工具：

- `commands/stop-service-admission-001.py`，SHAbf17bda8b442936638de0b2065e2ea7ee8c57c722ea41a426aeb01470eac390b。
- `commands/create-service-manifest-admission-001.py`，SHA170113909c37989652ec38bd5a7beb42bbdad27a315b06e493cb7e32a579c6fc。
- `commands/launch-service-admission-restore-001.py`，SHA72440df20830ddbf26b534216dc88cf5af7942f4b991f247523440471a2205b7。
- `commands/qualify-service-admission-001.py`，SHA79011aa87c42afe02d7098da95e7c60ae1424f82bd45a6ff52e9753c953ec12e。
- `commands/launch-service-admission-001.py`，SHAa9fc2c0f8a895e5daa4b236ed3f7c919d13d369fe53083c652cdac2fcb585f90。
- `commands/qualify-service-admission-restore-001.py`，SHAb05d013413b1f2f9145a752041c5faa90ff5887c6cf06082eae6e6b56e614b8c。
- `commands/qwen35_ordered_log_receipts.py`，SHAa7535c4cc8859981dc54b7a8500608b86c2897b2f8a5e893b4fe2541ef7cf7bb。
- `commands/run-ordered-admission-001.py`，SHAd094075b59daa7394f4d1a23cc3e6a2e18316512aa60b858e01e9871d281b7a2。
- `commands/check-ordered-parser-local.py`，SHAa67138e2115224679b7e3faa68c82aa932dd8ee0dab6d9d2b693453875d4441d。

唯一执行清单`/public-flash/jinghao/qwen3.6-35B/20261022-qwen36-35b-mx104-stack-regression/commands/ordered-admission-001-execution-plan.json`，SHAee546e889f5ed88a29db7ffbeeb37a02c99582b54ee24a0770790e92f055691b，原生后台入口run-background-job-v2，唯一job=accuracy-ordered-admission-001，真实command=['python3', '-B', '-u', '/public-flash/jinghao/qwen3.6-35B/20261022-qwen36-35b-mx104-stack-regression/commands/run-ordered-admission-001.py']。先归档/核验全部SHA再启动；控制器finally精确停止并恢复原配置。

最新运行状态（2026-10-23T06:35:53.229150+00:00）：唯一有限job accuracy-ordered-admission-001已启动，原生launch/command SHA分别506c1255af54600b493d4b5fc3362f60c0494beffa9137001b4dd05afe68a6da、6b9279a45f39e248d3725d39da81e1fa4835d12eacbb5b81bbdc132aabfd8095；外层PID/starttime核验存活，native result尚无。r9精确停止后，r10原生日志实例已启动，launch SHA112f41c22f061018eaf1fc8afd2b7bd841014d76010cb8b369d18ef809e35162，当前加载/尚未资格核验；0份正式诊断输出。控制器自动两轮64/最后恢复r11原参数，不手工并行切换。不能宣称64已完成、队列/设备形状固定、恢复已过或完整精度恢复；147<160及性能阻塞不变。小时监控已更新唯一job与新授权，不再重复索要同一许可。


### 日志单引擎前缀守护失败，0诊断输入与原配置恢复

001有限控制器原生退出2（result SHA7e251d4cc229cb0620fae370590b1e2ca2bbb38fd8854239f5bb2fcd331fa739）。r10已通过graph两replay/rank、C8八个短请求及完整manifest（SHA2a88ca8ad9fee2aa151dded531ae82ece8a6951c036aeadf2fb0e51768dd2696），但我在validate_ingress预设`EngineCore_DP0`，实际DP1日志前缀是`EngineCore`。diagnostic-error SHA223452db43f17460998f6070e43b35dbad1125a864d295d5c1d2f13e4e148ed4；API PID集合正确，错误只是engine regex无匹配。尚未创建任何cohort、未提交doc0..31诊断请求（不是所有流量为0：资格检查8请求已完成），64诊断预算未消耗。旧失败和工具不覆盖。

finally已恢复r11原参数，graph/C8/manifest和稳定字段比较通过：restoration SHA99df8db54f13a38bce0ac8ac3dc05da585ea2ab917303844a544366fa3d95524；r11 manifest SHAeeb812bd0d54790646eef03c632f90b22f50ccc757c53ac41e330e16e0934229、qualification SHAb8922459fa6ee7c6a54366f7f0dd63d4c6c37075887fc1fb16c9c92cb0f08c58。原生/server_info JSON再次核验profilerNone、prefix_cacheFalse、DP1/TP2/PP1。修正regex已在既有r10日志CPU验证：单API与单EngineCore，原先DP0匹配为空；不通过放宽DP数/身份条件凑通过。

准备新的独立002控制器而非重放001，启动前必须验证旧作业exit2、精确错误SHA、0cohort/0诊断输入以及原参数恢复通过；仅修正观察层原生前缀，原授权、请求与64上限不变，不重试任何已提交诊断请求，不新增轮次。新实例r11→r12日志→r13原参数恢复。真正controller AST、两份嵌套启动配置、实例与恢复路由都已CPU核对。执行前归档：

- `commands/launch-service-admission-002.py`，SHA68dfbd1b6bb3f25f960b4f9e79b04ba395d2d364258d9ed87b6689b78458410c。
- `commands/launch-service-admission-restore-002.py`，SHA696d0f5a44e576921bdb9e90faaaec9351f14067467f41103f9bf0a549c9de8e。
- `commands/qualify-service-admission-002.py`，SHA6ac582ed720777c03068378e17db8b3ef17602ff7c951daf99daf042cfde0e0a。
- `commands/qualify-service-admission-restore-002.py`，SHA271081cc804a6fc53a16682a4aa51442610ca05b41839db9899594c00badfe84。
- `commands/stop-service-admission-002.py`，SHA97101251639a7109af348b97d05ea378796aa5857d8a7875f5c8f414de38531f。
- `commands/run-ordered-admission-002.py`，SHA6ce83f196cbd93786b61ab4df56aa235fbbdac040f949de30057a09e8714bdac。
- `accuracy-diagnosis/accuracy-regression-001/ordered-admission-001/execution-cpu-validation-002.json`，SHAc3c6d131a03feb184fbdafed6c806a108aa140bc4db146d021cfb18976954b3a。

唯一执行清单`commands/ordered-admission-002-execution-plan.json` SHA5490a6de0f1bc0a54ba2c60594f6064e55e389c7f80f4a4baad8050d52dcf57f，job=accuracy-ordered-admission-002。先归档、核验SHA和前置失败/恢复条件，再执行。未消费的64请求授权继续有效，范围没有扩展；不声称完整精度恢复或正式性能通过。

最新（2026-10-23T06:46:10.160553+00:00）：002启动native launch/command SHA263a246a676f45411e486541379452da13390e656c98c87dda38d0e4b6c8fecc、86580fc481646de0842f1806abbdb3f1c6b63692a86e63994640b4b966f469c5，精确PID/starttime核验存活；phase loading、r12 launch SHA13ea6d8af8a5a52b0240adf5a75c88587257d0eadbd4df8dc3e80d46d30beb65，native result尚无、0cohort。旧001不重放，r11恢复已过，新job finally将恢复r13，64诊断授权不扩大。

并行只读扩展静态审计：相同两份ModelRunner源SHA（A65b0ee.../B86950f...）各110方法，102方法AST一致，8方法不同：__init__、_model_forward、load_model、profile_cudagraph_memory、capture_model、_allocate_kv_cache_tensors、_reshape_kv_cache_tensors、_update_hybrid_attention_mamba_layout。差异涉及graph-runtime钩子/准备、CachedOp prewarm、MetaX晚安装patch、cache_dtype_str属性fallback及NPU条件分支。此前五个状态/采样方法一致不能推广整个ModelRunner；当前仅静态定位候选，未证明哪个分支实际造成数值差异，不改任何优化代码、不归因迁移。


首轮真实有序准入已到达（2026-10-23T06:48:30.461908+00:00）：r12 graph两replay/rank+C8通过，qualification SHAb3eaddc83ab3592dd0bb4474049cab15b76cf760b0a3955ea1fb92c7fd1031ef，完整源码/实际加载manifest SHA78c1a567f1da5f6689f83a704a86dcb934a3e11ad3936402c256ff6609ff2ef1。单API/单EngineCore、DP1/TP2/PP1/profilerNone检查通过，ingress-preconditions SHA60dbff71cf65f1e0a948ded9d6d47bd3878e698335ada8d869d28d472f9e9a88。首轮32个精确ID/PID/fresh-log发送回执均已产生，独立逐项SHA引用核验通过；admission-receipt SHAe3eba71411f0448c738511b18f345bb89dd0b8cec46d9b25ab4595b243de8a10，随后原生is_paused utility屏障SHAbc45cd0b66ae9a9bdd60ce83c52459a0234a5029aac71414c025e5f119d0db40返回成功，再resume及unpaused通过（SHAb5a75a86ead45624cc3f7cebe3f37b5fa422a9fe425595bc82cc3e6d53a7467d/ad8f804583b6b23df7b9c8bf775176b1380d5c8467c834551c9771f4146472a7）。前两rank snapshot SHA f2da13bb360fd9ffe343e64d09332ddba21bb8138e3d1a687d0537e514624c87，无profiler/hooks。

当前10/32响应已完成，后续输出与第二轮和r13恢复均待唯一002控制器继续，不能把此部分证据冒充全部64/实际设备shape固定/完整198恢复。这里只支持源码推导的同frontend/engine FIFO屏障已完成，没有直接读取scheduler queue内容。原完整147<160门禁失败及性能阻塞保持，小时监控将只观察002，不再启动新任务或重放001。


### 日志64完成后的独立只读/CPU核验准备（执行前归档）

2026-10-23T07:11:23Z原生002精确进程仍匹配，native result尚无：cohort0已32/32、cohort1为26/32；07:15:34Z/07:16:54Z为32+30响应，两组各32发送回执与屏障均存在，尚未全部64或恢复，按正常运行处理，不追加流量、不发送重复状态通知。

准备两份新核验脚本，绝不重放诊断或旧控制器。只有002原生exit0、summary completed、全部64与r13恢复通过后才可执行。独立检查64原body字节/seed/预算、每题ID/PID/日志inode-offset/原生8hex后缀/原始日志行SHA和发送顺序、全部pause/is_paused屏障/resume回执、真实C32、两rank前后源码与无hooks、原配置与稳定manifest。随后仅read-only fresh runtime RPC及原evaluator内CPU原生strict过滤/指标离线评分，并逐题重现旧完整160/147；不签gate/不运行性能、不追加模型请求。完整5754源文件清单用于覆盖运行期新增的已安装函数引用，不能仅用C8时已引用的子集冒充全部源码。

- `commands/score-ordered64-native-001.py`，SHA79dd0626120feeb7aecea6c758bb1dc776150b1c52ac4ac75ea7df22ef6faa20。原生score函数AST与冻结旧scorer完全相同，仅响应输入路径/报告scope更换。
- `commands/verify-ordered-admission64-001.py`，SHAf849bdce115c7d57510bf3c37e787caf0efaba78ff50b5cffbf1bf5987e4630d。
- `commands/ordered64-independent-verification-plan-001.json`，SHA73c0597016245b80dd88a5ed8e860e11512bbe03a11dc7030e5ab8e8bbab6757。

新核验产物将只写ordered-admission-001/execution-002/independent-verification-001/，不覆盖任何原始结果。不把源码支持的FIFO屏障称为直接读取scheduler queue或设备shape；文本一致也只属于两轮固定32、不是完整198恢复或迁移无退化证明。若控制器partial/失败，以上完整64入口不执行，按实际已提交范围独立报告，禁止补跑。


## 两轮有序日志64完成、原配置恢复与独立原生核验

002原生退出0（result SHA50ab1917c77f2d21e4bd33f6330cd09e3c46920003c516c1052ca54b08b45ef7）；两组均32/32 HTTP成功、stop结束、实际max_running32。独立报告`/public-flash/jinghao/qwen3.6-35B/20261022-qwen36-35b-mx104-stack-regression/accuracy-diagnosis/accuracy-regression-001/ordered-admission-001/execution-002/independent-verification-001/verification.json` SHA cba51202c395edc8e54fcc0e8dc7225962b2c0dc6235a9833e55b26a7d2b2275。全部64原body/参数、64条精确ID/PID/fresh-log偏移与实际原生日志行SHA、发送顺序、两组原生pause/is_paused utility屏障/resume/unpaused、两rank前后PID/源指纹/无hooks均通过；源码引用与完整冻结安装清单一致。

两轮32/32题全文完全一致、0题变化；原生strict分别25/32、25/32，native-strict-scores SHA f59dd517944529fd443dec25898a176ddcd39d0e5fd0b05bb5b8cacc4343df62。原evaluator内同一原生filter/metric代码SHA与既有结果完全一致，逐题再次精确重现旧完整160/198与147/198。相较此前异题pause+2秒等待仅2/32全文可重复，逐条发送回执+原生同引擎屏障在这个B/固定32范围获得重复性；尚未直接读取scheduler队列/设备prefill shape，也没有A/B数值差异或完整少13题因果证明，不能推广全198或签gate。

最终r13恢复原launch-v2（无enable-log-requests/profiler），graph两replay/rank、C8、完整manifest/代码加载与r11全部稳定字段一致：restoration SHA c02a5098b3180b90934f11feff1a09e47c8ed8bc56891d1e3225b037a9fb7b63，manifest SHA86ac5e1b962827abad7203d047f89e621622d66b247a55e65f63c2a9aa241f04，qualification SHAaced61366eba76bf66646c13df694f36cb327a644c1c4e961915e4b6bd4c2e7c。新的只读fresh RPC SHA9055f8c1adf3250bb91920493e70b8b83ad92fa6ea43d38e765431919c90bfcd，精确API PID/starttime、profilerNone/no hooks/proxy与unpaused再次通过。两rank FGV仍未加载，editable安装字节一致不能冒充FGV内核覆盖；本日志轮未采kernel trace，不把前两profile窗口shortlist命中外推成当前全64内核逐次证明。

旧001前缀守护0诊断输入退出和r11恢复证据完整保留；新002实际仅两轮64、无请求重试或第三轮。临时日志授权已全部完成，正式147<160门禁失败及性能incomplete不变。

### 完整198后续仅只读/CPU规划：原生入口与绑定约束

原生结果已核对backend=`openai-chat-completions`、batch_size1、num_concurrent32、timeout7200、max_retries3；实际类OpenAIChatCompletion继承LocalChatCompletion，最终继承TemplateAPI。实际文件`/app/lm_eval/models/api_models.py` SHA493c667142263338f93894adf5638403269081b8329579eac1a64eda70383720；`openai_completions.py` SHA83cb3d92d08feaf919b91562a3aeab5055b52873eed729845f37c33a2370e38e。generate_until通过通用`-len(context)`键和gen_kwargs分组Collator，再由get_batched_requests生成所有task、semaphore32滚动并发，末尾恢复原始结果顺序。此处先前按注释写成“prompt字符长度降序”，已由下述真实JsonChatStr/198请求CPU核验纠正：本任务context是单字段NamedTuple，len均为1，相同gen_kwargs下实际保持输入次序。chat backend会把batch_size>1改回1，所以不能只设置batch_size32就声称固定32 wave。实际OpenAIChatCompletion payload是max_completion_tokens65536（非LocalChatCompletion的max_tokens），默认HTTP seed1234，stops/温度等与冻结输入一致；不能按相近类名换builder。

下一步可在不发生成的CPU mock中，从同一native runner/client恢复全部198的payload与原生collation顺序，评估最窄transport扩展，保留native task/filter/parse/cache/result映射以及精确160/198门槛。目前尚无该native-adapter实现或CPU通过，已有合成198 state-machine不等于原生适配。若要改rolling32为固定waves32×6+6，必须预声明顺序、尾6/fallback、原生retry行为、全量A/B/回退测量和失败处理，再获明确授权。

另一个必须解决的边界：若正式198服务追加日志flag，其launch identity与原无日志服务不同；原gate工具只允许纯重启重绑定，不能静默把“日志flag下的gate”重绑给恢复无日志服务，也不能因为它是观测开关就忽略差异。完整精度/正式性能的参数与gate生命周期必须在可审阅方案中明确，未经新协议/启动策略授权，不跑正式198、重绑gate或正式性能。继续只读分析8个不同ModelRunner方法/实际dispatch，未有稳定A/B区分前不改采样数值实现。

仅状态checkpoint命令`commands/checkpoint-ordered64-verified-planning-001.py` SHA44548607dcecb7085afe2d3ca730d2d527f341ddf281ec10cc340a718e2dc23c，执行前归档：002转last_completed_job，current_job清空，临时日志剩余授权请求数0，进入只读/CPU完整198方案规划，不自动追加任何模型流量。

### 原生198 transport 的 CPU 可行性核验（执行前，零模型请求）

准备独立命令`/public-flash/jinghao/qwen3.6-35B/20261022-qwen36-35b-mx104-stack-regression/commands/native198-transport-cpu-001.py`，SHA0d3762843acf882dd9abc3efccafb3d9df74ff155b26124d959ff1dfa6b5a0fc。只在专用eval容器的独立CPU进程中执行，隐藏设备并禁止socket连接；不初始化模型，不操作当前r13服务，不修改任何原生源码、冻结工具或正式契约。原始198题内容只保存在远端案例。

从A/B已核验样本恢复真实`Instance/JsonChatStr`参数，调用当前实际`OpenAIChatCompletion.generate_until`、payload builder、parse、cache及Collator。先用fake HTTP跑原生rolling路径，再用只覆盖batch/session层的CPU原型跑32×6+6，比较全部198个原生aiohttp JSON body哈希、synthetic sentinel输出/usage/cache映射；模拟缺发送回执和屏障失败，检查不重复发送、不启动下一wave。该原型没有live日志/utility driver、CLI注册或正式gate接入，不是已可用的原生评测适配，也不运行新的精度分数。

新发现的只读边界待CPU验证：保存的`arg_0`来自`JsonChatStr`这个单字段NamedTuple，其`len`为1；不能把`TemplateAPI`的通用`-len(context)`注释直接解释为本次实际prompt字符降序。原生evaluator另有可选`sort_by_tokens`，冻结runner未传该选项；需要同时保留入口顺序与实际post顺序证据。历史完整198未捕获HTTP wire bytes，因此CPU仅能证明重建native serializer的逐题一致性，不能倒推出历史wire字节已核验。

CPU核验已完成，原生exit0，`commands/native198-transport-cpu-001-native-result.json` SHA4bb3215066bc7074a8a74e3c847381837a1125c9418c17f2385ced603956ffc6，执行清单SHA3488d1009159575bae9b906474e61fb9ff9d1b36250f5e69ad0a37397d6cf443。报告`accuracy-diagnosis/accuracy-regression-001/native198-transport-cpu-001/report.json` SHA3710f807b1af3e6cb7b3dbc531677df3b2fcbd36371a73c4c60192659a4130e3：A/B全部198保存参数相同；原生rolling与transport原型的198个aiohttp默认JSON序列化哈希、synthetic输出/usage/cache/回填次序完全一致，模拟异序完成，原型wave为32×6+6，未padding尾6或改C1。缺第10个发送回执/第1组屏障失败时分别只模拟提交10/32个，原生max_retries3仍保留但失败闩锁阻止二次wire提交，未开始下一wave。没有连接尝试和模型请求，没有新分数。

六个真实native模块SHA独立复核，原文件未改。`JsonChatStr`的JSON round-trip与样本保存器一致；实际198的输入/post顺序均doc0..197，所有context长度1而prompt字符长度不同。evaluator/simple_evaluate/CLI的`sort_by_tokens`默认None，冻结runner未传该参数。该结果纠正排序理解，不解释原少13题。独立原型只继承原生generate_until、builder、create_message、parse，native cache仍在原amodel_call执行；模拟失败后generate_until会把整组返回TIMEOUT，因此live接入还必须有独立失败sidecar和停止守护，不能把该行为误签正式完成。

仍未实现live sender日志/精确身份/utility driver、原生CLI注册与provenance/失败sidecar。只读还确认冻结`acceptance.py`明确要求model_type=openai-chat-completions，`formal_accuracy.py`固定调用python -m lm_eval；不能静默换同名registry类、加入未记录sitecustomize，或改冻结验收器放行新的client。后续先准备独立、显式命名的transport适配与CPU CLI/来源核验，再给出正式工具版本/契约的具体差异。启动/gate方案必须写清：日志开启与关闭是不同身份；若后续获准使用日志launch做正式评测，所有A/B/revert与性能需同launch，恢复无日志后旧gate失效，不能静默重绑。新协议是否进入正式验收、是否保留日志launch仍未获授权，也未执行。

仅状态checkpoint命令`commands/checkpoint-native198-cpu-001.py` SHA660d614fc17283d4e80c2e705f0b1df1c0b82c33a2f0fe52251554e5c16c2d1e，执行前归档；先校验continuation原SHA与CPU报告全部引用，保存旧continuation独立快照，再追加CPU证据并纠正旧next_actions中r9/排序的过时描述。current_job仍null、r13服务与phase不变；不会启动任何模型作业。

checkpoint首次误在Host执行，在第17行核对eval容器内`/app/lm_eval/...`时FileNotFound guard退出1，尚未写备份或continuation。保留该失败事实；校验continuation原SHA和备份未创建后，以相同已归档脚本字节改用`docker exec qwen36-35b-regression-eval-20261022 python3 -B <上述checkpoint绝对路径>`执行，使用正确文件命名空间。该修正不重跑CPU198或任何模型请求。

### 用户新授权：相同有序准入下的异题B/A/B对照及条件性单变量回退

用户明确要求“继续在相同的有序准入条件下对比 base 和当前容器，稳定复现差异后做单变量回退，定位具体原因”，允许临时日志取证后恢复，禁止修改vLLM源码和精度门槛。该新授权覆盖后续诊断，不再受前次已完成64请求授权的剩余0限制；正式评测协议仍未变更。授权记录`environment/ordered-bab-001-authorization.json` SHAdbfe9de81de8c00b0542ec2787cd2f6178868581eecb6da50a4eaea707750615。

首个预声明有限矩阵：当前r13→B candidate-01-r14→A revert-01-r4→重新启用B candidate-01-r15→原配置B candidate-01-r16。每个诊断实例均使用原first32 doc0..31、每臂两轮，共192诊断请求；四个新实例各原graph两replay/rank+C8资格，共32短请求另记。沿用已实际验证的暂停keep/clear_cache=false、逐条精确fresh Added发送回执、同引擎utility屏障、resume/unpaused协议。body字节及sampling不变，同repeat各臂外部ID也一致；不得加入logprobs、padding或C1替代。唯一服务启动例外仍为`--enable-log-requests`，所有源码与模型保持原状。

同臂两次全文一致、B重新启用一致且A/B不同，才构成进入单变量定位的稳定差异；仍需原生strict比较和机制证据，不能只凭文本差异解释原完整少13题。有效但不重复的输出全部保留并按预声明矩阵完成；身份、请求、回执或资格失败则停止后续臂。无论完成或失败，finally精确停止本矩阵服务并恢复r16原launch-v2，再核验graph/C8/所有稳定manifest字段与r13一致；原147/198失败和160/198门槛保持，不签gate或运行正式性能。

独立派生命令均在`/public-flash/jinghao/qwen3.6-35B/20261022-qwen36-35b-mx104-stack-regression/commands/`：`run-ordered-bab-001.py` SHA6bb0de797c6e569528998e18de2fc3d3ca5085ee99b4e4e6c20a828c5d5f200c；`launch-service-ordered-bab-001.py` SHAf9ae135be553126966bb44c5d4a17bfc5d9975965af844729aa87dad7addc562；`qualify-service-ordered-bab-001.py` SHA6ae7504121cdb16a4e5a829ac785252677efdc3dcf7426fd763024c00539c035；恢复launch SHA1beae14a6b5dcf81cf41841cff573ae363a57032aa42563f3e39a8b260a01658、恢复qualify SHAd1535c5842cd1f1dcc080b5c7314a44001b605cdb80509c88b440bca3e622fbf；stop SHA4cbe3e96526aeca817ef65587c618102c72b9d2e668068903e1a78498d165f8f。只扩大精确实例白名单，原始冻结工具不覆盖。

CPU已执行实际控制器orchestration AST的五种模拟：正常三臂、A资格失败、B第二轮失败、原服务停止前失败、停止后失败；均无重叠服务、停止后续臂并恢复原配置，测试未调用实际服务。报告`commands/ordered-bab-001-cpu-validation.json` SHAac6ed1b1e10d6213a8ddfa9cb25cdd9da154e48c045f182fc6b481adcf494615；同时校验派生脚本的真实调用路径、内嵌代码和精确实例guard。完整执行清单由独立prepare命令校验所有工具SHA及32个body指纹与既有64请求一致后生成，再通过原后台入口启动唯一job `accuracy-ordered-bab-001`。

完成状态checkpoint已执行，continuation SHA81d4086a9bb5ad780cf7ead8c783ce7871afc623c8b2714237c0b37f023fc419；phase=accuracy_diagnosis_ordered_admission_verified_readonly_planning，current_job=null，last_completed_job=002，r13原配置不变，临时日志剩余授权请求数0。小时跟进继续只读/CPU方案准备，未自动追加任何模型流量或正式评测。

本轮新授权执行准备命令 `commands/prepare-ordered-bab-001.py` SHA09f0ce54e70395affccc69ac48c36b761064e96db22851c5bfe0ab83137e566b，执行前已归档；仅生成独立执行清单、核验32个原body指纹和工具SHA，不发模型请求。上段SHA81d408...及“剩余0”是旧64完成时的历史checkpoint，现已由新用户授权覆盖后续192诊断矩阵；本轮以新job/原生回执为准。

执行清单已原生生成，`commands/ordered-bab-001-execution-plan.json` SHA246d89a17f9abb6afa6dd4a81547cf9c2d50eb28d5b536bbb91d1a6f6f833ac7；32个body SHA与旧已核验64逐题完全一致。唯一job=accuracy-ordered-bab-001，原后台入口使用清单中已保存的 `python3 -B -u <CASE>/commands/run-ordered-bab-001.py` 启动，不重放任何旧控制器。

新作业已启动（2026-10-23T09:28:39.708884+00:00）：native launch SHA97a2aede4566108805da8726d6733dd5997551b646f1aee8100e8cdf75ecf809、command SHAd9b8fa05c49ea29c999c431859ad387018635406f4ac63c24606ea091fa0a1ba；精确PID/starttime+cmdline核验通过，native result尚无。第一B实例r14处于loading，launch SHA4fa45ecb4d2fff395dbd6bfa09700e4f4e58afd0fe89ef54e96366f7e8ce5301。小时监控已更新新授权与唯一作业，不再把旧授权已用尽当本轮阻塞；finally恢复尚待执行。

### 新192完成后的独立核验准备（尚未执行）

原控制器native0、全部192和r16原配置恢复通过后，才允许独立核验器执行。逐臂校验同角色原manifest、全部Added日志行/偏移/顺序、同引擎屏障、原body字节、实际C32、两rank前后源引用（A/B分别对各自完整包清单），再用原生strict离线评分并逐题重现旧160/147。最后fresh RPC和PID/starttime核验r16无日志/profiler/hooks/paused；这不追加模型请求、不改gate。partial/失败作业不得执行完整192入口或补跑；结果写独立新目录。

- `/public-flash/jinghao/qwen3.6-35B/20261022-qwen36-35b-mx104-stack-regression/commands/score-ordered192-native-001.py` SHA87dbb9297444ea8156d255f9985fc6147658ba7af8f5e52f3b4e379b9abe0abb。
- `/public-flash/jinghao/qwen3.6-35B/20261022-qwen36-35b-mx104-stack-regression/commands/verify-ordered-bab192-001.py` SHA7c7ac5608e75521116036cf8ad5de9c54c9ad3b934ad30c7de0b7892b3a48ef9。
- `/public-flash/jinghao/qwen3.6-35B/20261022-qwen36-35b-mx104-stack-regression/commands/ordered-bab192-independent-verification-plan-001.json` SHA39c5ca3c06dd6ef580b63a4f17c4002473dabe785bae406455119c04b6742578。

评分函数AST与旧原生scorer完全一致；两份脚本AST检查通过。新增六组角色/路径与数量检查，输出每题三臂两次文本指纹、原生strict、稳定A/B差异及正反向答案变化，保留不稳定项，不按结果挑样本或签完整gate。

最新partial（2026-10-23T09:35:19.271048+00:00）：r14 graph/C8资格SHA03483bfcefbed7a10532c058f469f4c208c93891f02f2d0b7fcccede898c1e9a、完整manifest SHA17cdbbaa52c281a348a109375636aaf9c76ce4018dc4dfe6bcb5ddfbe180e895通过。首轮32条Added引用逐项SHA核验，admission SHA c4bc9d27454452beae9bdfe99423e4c11de403723b8d73127bb912d9fbf21e6d，同引擎屏障SHA5c3178b2adf7f479380efe8dc3d5e5ac9fa433ec9ba30d84bb3b8c2c158b9398、resume SHA66c927bd37d09ffe19f97391027e394b4eb44807548f0906ae7331bf219a4ae9、unpaused SHA436c57d2551aa7588f32c016bf4ca164107988033cd70de313a949b7252526fc已产生。19/32响应成功，其他组未开始；精确job身份存活、无native result/错误。不能把partial当192完成或稳定A/B差异；不改活动controller/continuation，等待原finally恢复。

例行只读检查（2026-10-23T09:38:20.492648+00:00）：原唯一job精确PID/starttime/cmdline与所有冻结工具SHA通过；首轮24/32成功响应、32Added与屏障SHA未变，其他组未开始，native result与错误均无。正常进行，无新A/B结论，不重放、不改活动continuation或服务；保持小时监控安静。

### 有序BAB001未完成：64已完成、清单采集失败，恢复核验待补

原生exit2/result SHA6efd555c3a1100d5e98514eedbf9d8b103327e0705a4780bb998acf10ce2c086；B-r14两轮64成功且32/32文本重复，A-r4 graph/C8过但manifest内collector退出1，尚无A诊断输入。finally已启动r16原argv（无日志/profiler）且graph/C8过，manifest同collector错误，不能宣称完整恢复核验已过。当前r16精确PID/starttime存活、unpaused。保留所有失败，不运行全192核验器/不重放控制器。

先执行只读观察器 `commands/inspect-manifest-failure-001.py` SHA251f014ef70bf253c6800010fdf9658dc83206ee02e1af21477f8d20298b4d6a：调用原工具全部前置守护，在collector调用处保存原生stderr/stdout后立即终止，禁止写manifest；0新模型请求、源码/服务均不修改。先查明真实错误，不放宽源码一致性要求。

底层原生错误已复现：collector RuntimeError missing package vllm，观察报告SHAd7687b4b13ccec269b762bb8294931b1f8050ca64cb0dea49299096dcb87b2f9。默认cwd=/public-flash/jinghao下存在无__init__.py的vllm目录，被python -c当前目录查找先选为namespace，遮蔽editable finder；finder仍正确映射/workspace/vllm/vllm，SHAfc3e7a182298b204d01f3ef60d484b795bbe7f83d2a246fa7a8de4896b1cc149。只读对照加-P去除当前目录后正确得到实际包__init__。更正前面口头“服务启动目录”：服务真实cwd是/workspace，服务vllm console入口与collector -c的sys.path[0]机制不同；并非修改服务工作目录。

独立派生manifest仅给采集器Python增加-P，所有原始源码/元数据/运行路径守护保留，不修改服务argv、安装、vLLM或模型。先补r16完整manifest与fresh RPC、原稳定字段一致性，再独立核验已有B64/原生strict；无新请求、不补跑A、不覆盖旧错误。执行前归档：
- `commands/create-service-manifest-safe-path-v3.py` SHAd31696cdec63a3f946185cb153bdbc796570987bec89e01273ab0f5468e66761。
- `commands/create-service-manifest-admission-safe-path-002.py` SHAdaef0cb0d5efce25e57359c801f26ef81a5ff1878f786f18eb3c4bb3c98603cf。
- `commands/score-ordered-bab-partial64-native-001.py` SHA8e7dab1bee665e91b61da3a9d66e9f5c4d4ce3a925253d0ef0992c77b9c71576。
- `commands/recover-and-verify-ordered-bab-partial64-001.py` SHAd3fc0c66e77620b2a704550d2c4be17f0e539f3e56aa106748a0455743b46bdd。
- `commands/ordered-bab-partial-recovery-plan-001.json` SHA84c73233d9958015b4c2da6ffc85f25a839ae3bf401e57a33f1979bf9df17f6c。

部分64和r16恢复已独立核验：report SHA0fabefc4b2b24ae690fa7a53b7bae9a3f334749adf69ed7182b99dc4ecead480，原生strict25/32两次、32全文重复且与前次B64也全同，旧198逐题重现160/147；restoration SHA777dab72eb7219acd0e15a9d1b39f7eda2c691046a012a846dd855b99ad223b8。r16 manifest SHA2adcca55fd154a61984868a9571901582b6db3efd319dc01389ca6b73cc64d85，全部稳定字段与r13相同；fresh RPC无hooks/profiler，原argv和unpaused通过。恢复过程0新增生成/0重启，旧失败原样保留。

预声明接续原未执行的A/B128：r16→A-r5两轮32→B-r17两轮32→finally原B-r18；不重跑已完成B64，合计仍192，采样/body/同repeat请求ID/有序协议不变。新三个实例各graph/C8另24资格请求，旧已24，额外服务切换资格与原诊断数分开。只改变observer collector的-P，vLLM/Plugin/Gems/模型/冻结服务argv和精确160/198均未变。旧001 native2/A0/B2零请求/部分64核验及恢复通过为启动硬条件。实际AST正常/资格失败/请求失败/stop前后5个CPU场景通过。执行前归档：
- `/public-flash/jinghao/qwen3.6-35B/20261022-qwen36-35b-mx104-stack-regression/commands/launch-service-ordered-bab-remaining-001.py` SHAbdb7bc7fde9d1a3ad6f6e83989481d2bb9160fe30ed5287382407dafcbc33344。
- `/public-flash/jinghao/qwen3.6-35B/20261022-qwen36-35b-mx104-stack-regression/commands/qualify-service-ordered-bab-remaining-001.py` SHAa364fc43f8cfa8f2cb04c1e897e1c37bf5a9e6b79fe9cfefdc29dd532ffd4f43。
- `/public-flash/jinghao/qwen3.6-35B/20261022-qwen36-35b-mx104-stack-regression/commands/launch-service-ordered-bab-remaining-restore-001.py` SHA134c3b39fb4a6aece183c74eb92a057c661f1ff1ddb461377814100bfdbde4b8。
- `/public-flash/jinghao/qwen3.6-35B/20261022-qwen36-35b-mx104-stack-regression/commands/qualify-service-ordered-bab-remaining-restore-001.py` SHA54e852628776044dfaee3cae6f69ceace9a408c6c704f1472ab4f5027c010356。
- `/public-flash/jinghao/qwen3.6-35B/20261022-qwen36-35b-mx104-stack-regression/commands/stop-service-ordered-bab-remaining-001.py` SHA26857f39bffe5b71238963aab2a07b960b62f968380059c535c488a5d92784ac。
- `/public-flash/jinghao/qwen3.6-35B/20261022-qwen36-35b-mx104-stack-regression/commands/run-ordered-bab-remaining-001.py` SHA4689786a088a4fdd99a2c02bdd15d5c4d85427d87c53a704d204df44d88ead81。
- `/public-flash/jinghao/qwen3.6-35B/20261022-qwen36-35b-mx104-stack-regression/commands/ordered-bab-remaining-001-cpu-validation.json` SHAb243b0dc516b7d9f5892a406e2f85961f38583fcdf92f39cc95ee4d8b472669f。
- `/public-flash/jinghao/qwen3.6-35B/20261022-qwen36-35b-mx104-stack-regression/commands/prepare-ordered-bab-remaining-001.py` SHAb74268a9451c4bf00b938a0bc901ec8bd7e1927a9550c980366a52e5aec59291。

接续执行清单`commands/ordered-bab-remaining-001-execution-plan.json` SHAddfe1a237527fc31c2ec7ab82634405289e658001348bba20e17d5894af2ec83已冻结；唯一job accuracy-ordered-bab-remaining-001使用保存的python3 -B -u commands/run-ordered-bab-remaining-001.py，经原后台工具启动。旧B64只引用，A/B剩余128从未提交，不扩大诊断矩阵。

接续完成后的独立全192核验工具已派生：原B64读取旧目录，A/B128读取remaining新目录，逐臂原native发送/并发/源码证据全部检查；只接受remaining native0、r18恢复，旧native2及partial64证据保持，原评分函数不变。旧原001全192核验器不适用于此次接续，不执行。执行前归档：
- `/public-flash/jinghao/qwen3.6-35B/20261022-qwen36-35b-mx104-stack-regression/commands/score-ordered-bab-combined192-native-001.py` SHAb063b8f017aa8095cb60ef93ab6183bd6e7fcfb5b38707b8e50d0f24e832755d。
- `/public-flash/jinghao/qwen3.6-35B/20261022-qwen36-35b-mx104-stack-regression/commands/verify-ordered-bab-combined192-001.py` SHAf8e969c2b851261c3593ba24bd91d22f85ca09714de2f214f50b0e8ee1082e85。
- `/public-flash/jinghao/qwen3.6-35B/20261022-qwen36-35b-mx104-stack-regression/commands/ordered-bab-combined192-verification-plan-001.json` SHA747e5370354079c9064022dcd11e3531129a4a06a15b585f32cf46efc57021ab。

接续已启动并跨过旧错误点（2026-10-23T11:47:50.489737+00:00）：唯一remaining001精确PID/starttime/cmdline通过，native launch SHA74067da548d92b95e2288f41a1332e35308d422dec2445db6e3a2818de794023、command SHA963324f1cd5f99d9fc36c9a998045eb5f73b6ee513cc2616bf72c500df1fb0d3，native result尚无。当前A-r5 graph/C8与完整manifest通过，manifest SHAfb7c865e5ffb5434494eabb61f1db03038c531f5fb15d61da79b226410372e11、资格SHA8b75391f9db6e14345eba7be99afc73ce98b5a7ab35db073ef730182ab4e0574；首轮32Added、1/32响应，B2未开始。旧B64保留并引用；没有稳定A/B结论或单变量回退。监控已改为新唯一job/新全192核验plan，旧001与旧全192校验器不重放。

例行检查（2026-10-23T11:50:15.683707+00:00）：remaining001精确进程和全部冻结工具/plan SHA核验通过，A首轮19/32成功，32条Added引用SHA通过，utility/resume/unpaused回执齐全；其他组未开始、无native result/错误。正常进行，未重放或切服务，不提前比较部分分数或启动单变量回退；监控保持安静。


## 有序B/A/B全192独立通过：未复现稳定差异，继续原失分题诊断

remaining001原生exit0，result SHA ff731dda9cb69cd2e6d6df9bf1d459b3fbe11450be17d23afaf2860edb62b938。独立核验verification SHA96d4db976123c3ef06228466cf3afb13ba4f64188edfaef465e07f00903c86d2：所有192响应/Added/同engine utility/原body/两rank源清单/原配置恢复通过；32题六次全文均一致，原生strict六轮均25/32；原完整160/147逐题再次重现，native score SHA7a43eb04a5f4576d3f0112dfe5e7c88d14ed0a078d25b6b34cef962f6011f751。当前r18原配置已恢复，无日志/profiler/hooks，FGV两rank未加载。此为固定32诊断，不是198恢复；没有稳定A/B区别，故单变量数值回退尚未开始。

按用户持续有序A/B授权预声明 ordered-loss-001：固定原完整评测中全部26道A对B错题，加逆向13题中按doc ID最前6题，合并后按ID升序发送。同C32/seed1234/temp1/p.95/k20/65536/stops和精确有序准入，每臂两轮，B-r19→A-r6→B-r20，finally B-r21恢复，共192诊断+32资格请求。选择在流量前冻结，与此前doc0..31是不同样本组合；保留所有旧结果，不把本轮评分与原32或正式198混算。覆盖全部原26失分题，7道逆向题未纳入；不宣称恢复原rolling32时间线，不改变原正式评测协议。native198 CPU恢复payload与原first32逐题字典一致，历史198 wire未捕获，不声称原wire SHA。全部结果保留；回执/身份/请求失败停止后续并finally恢复，无自动重试。仅稳定各臂+B重新启用一致且A/B不同后才进入已授权单变量回退。五个真实controller AST生命周期CPU模拟通过，非硬件通过。以下新工具执行前归档，旧工具不覆盖：
- `/public-flash/jinghao/qwen3.6-35B/20261022-qwen36-35b-mx104-stack-regression/commands/launch-service-ordered-loss-001.py` SHAdff53d93af6b46caebc52edb96d7850b2578b63f2f02d6a8688283025ddf7b8a。
- `/public-flash/jinghao/qwen3.6-35B/20261022-qwen36-35b-mx104-stack-regression/commands/qualify-service-ordered-loss-001.py` SHA5c0f898437593fdfafc0622ff0aae3bbdb2567c226f49c37b45c036b45c60c0d。
- `/public-flash/jinghao/qwen3.6-35B/20261022-qwen36-35b-mx104-stack-regression/commands/launch-service-ordered-loss-restore-001.py` SHA14ebce78a1c538c27280a78f0a4b2ec03dd92547c0e24c7dc0e8be4a24d3209e。
- `/public-flash/jinghao/qwen3.6-35B/20261022-qwen36-35b-mx104-stack-regression/commands/qualify-service-ordered-loss-restore-001.py` SHAf28a167af0fb1e22f7ae583bfc4f47720665e0b09f85758d0a53b7f30c10a6b1。
- `/public-flash/jinghao/qwen3.6-35B/20261022-qwen36-35b-mx104-stack-regression/commands/stop-service-ordered-loss-001.py` SHAddc8c89e17547f4e76b67e1f2f70da9d4dbcae5a0a62a3dcab34ad9ffb340a91。
- `/public-flash/jinghao/qwen3.6-35B/20261022-qwen36-35b-mx104-stack-regression/commands/run-ordered-loss-001.py` SHAffa485de28e60f6458069b8eace713f24a1c5ea9cbe41af041bf184666d2c7dc。
- `/public-flash/jinghao/qwen3.6-35B/20261022-qwen36-35b-mx104-stack-regression/commands/ordered-loss-001-cpu-validation.json` SHA4fcbde58a29671d6707100a1373673ca3ca69b79b4a1d7bc52109aee070a31e5。
- `/public-flash/jinghao/qwen3.6-35B/20261022-qwen36-35b-mx104-stack-regression/commands/prepare-ordered-loss-001.py` SHAc613619b58a86e501f7b3a1611d34aa363237c7288de506f78c4d184ec31ce3a。

执行计划已冻结：commands/ordered-loss-001-execution-plan.json SHA8ffa4abbf792baacd4983298ed788a34a6ad60a3cdc4ee86d3ce09f054f12a93；selection SHA4399632492a4d76f0027018efbffbce88916c0a81acd9251c56cc77733537efc。选择32题[1,4,8,12,13,22,25,28,29,31,32,44,45,48,49,60,66,71,74,78,85,90,97,100,121,126,127,130,139,142,174,182]；prepare 0请求。即将仅执行plan.command一次，后台job唯一目录accuracy-ordered-loss-001。

新组192完成后的独立核验已预备，不提前执行：必须native0/summary completed/r21原配置恢复通过。非连续doc ID按冻结列表逐条配对Added、payload、文本/strict和原32对照，禁止把数组索引当doc ID。原生score函数AST不变，只改输入范围；不会增加生成请求。仅完整通过后运行以下独立新入口，旧32或combined192验证器不适用本组，不重放。
- `/public-flash/jinghao/qwen3.6-35B/20261022-qwen36-35b-mx104-stack-regression/commands/score-ordered-loss192-native-001.py` SHA488e0e3e468fd5a7a88fef18ab1711f55b3d511683cae6330ad13563092a06b5。
- `/public-flash/jinghao/qwen3.6-35B/20261022-qwen36-35b-mx104-stack-regression/commands/verify-ordered-loss192-001.py` SHA531ead9efa5469ef09306e47755c18b57c149edb55226ecc4eda25120850011f。
- `/public-flash/jinghao/qwen3.6-35B/20261022-qwen36-35b-mx104-stack-regression/commands/ordered-loss192-independent-verification-plan-001.json` SHA462480b4d8e27ddfe19a273e533bccbcb04bc2ec165593d04e04f9812633a5de。

新有限作业已启动并再次核验（2026-10-23T14:03:06.817951+00:00）：job=accuracy-ordered-loss-001，native launch SHA530aee224921fb090d6edf186e8f61a94dab68e5a7b82618be7b6204b2c266c9、command SHAd5c0ec69b2318cfecd1d1e8aca8fce694504dfcbc7f6785a804f88f568268346；精确PID/starttime+cmdline通过，native result尚无、无错误。当前B-r19 graph/C8/manifest通过，manifest SHA999ab9e8befca7e6ac1388ce71b86e8e14345557cc4c50e7ff06e67756954b21、qualification SHA88d10d66fa0c43cecf0279f1c538b3f70fa381ae9fd9ae3f2160282add8e300e，首轮进行中，尚无诊断输出。控制器自动继续A/B和r21恢复，不手动切换。小时监控更新为此唯一job；所有旧192已完成，不能重放。

小时只读检查（2026-10-23T14:06:02.487003+00:00）：当前唯一ordered-loss001精确PID/starttime/cmdline、launch/command/plan/selection SHA均通过；B-r19首轮32Added引用与实际冻结doc顺序核验、resume/unpaused通过，admission SHA f1ec3c02594afa9fa25e42de419e0b3f25a6484fb63b557629faba2892c460f5，10/32响应成功，其余组尚未开始。无native result/错误，未创建独立全192验证输出。属于正常partial进度，保持安静、不重放；当前无新稳定A/B区别或精度恢复结论。未修改活动控制器continuation，未发新模型请求/服务变更。

用户查询最新状态（2026-10-23T14:09:25.915368+00:00，北京时间22:09）：当前第一B首轮12/32响应完成，均HTTP成功；其余5轮尚未开始。精确后台进程、native launch/command SHA核验通过，无原生完成回执/错误；此为进度，不是原生strict分数。新的26失分题组尚无A/B比较，单变量回退未开始，继续唯一现有job。

小时只读检查（2026-10-23T15:05:29.279334+00:00）：唯一ordered-loss001精确后台进程及launch/command/plan/controller SHA通过，已自动进入A-r6。B两轮64全部HTTP成功，两cohort receipt SHA36ce92263a7759b954ca2e95ade21c24be024897afffae1767394579f2f47508、6c91bece2319f786eefda38a276e3c59f05f2df8272bd65640b688a43db13656，输出引用SHA/两组各32Added引用/冻结doc顺序/原生unpaused与max_running32均核验。A首轮18/32成功，32Added/有序屏障已通过，admission SHA92f0e7487895d8bc6716eee9f737bb5cfbe9a4bfec16d970831bc6ffac081999。A manifest SHA4341a45d5ade92aebadf1e6f560d305760079d90ec21de80dd55bb02ce8cdcfb，qualification SHAe7ac21d8298bfaf893f018c63f5b0b206e95cf85077fb7eeeabf43c30478e094。合计82/192仍partial，未执行全192独立评分/核验，不据部分输出宣布差异；正常进行，无新用户操作，保持安静。

用户状态查询（2026-10-23T15:38:23.948876+00:00）：唯一job精确PID/starttime/cmdline、launch/command SHA再次通过。B64全部与A首轮32完成，A第二轮27/32，合计123/192；无native最终回执或错误，B重新启用待控制器。新增只读部分文本/body核验：每份实际文本重算SHA，引用request文件SHA与冻结body SHA逐项一致。B两轮32题全文全部相同，A首轮32题与两份B全文全部相同，A第二轮已有27份也逐题一致。尚非全192验证、未计算本组strict分数，也缺重新启用B复现及finally原配置恢复；未复现当前已可比较范围的稳定A/B差异，单变量回退未开始。保持原完整147/198门禁失败，不产生新生成或重启。

小时只读检查（2026-10-23T16:07:04.391703+00:00，北京时间10月24日00:07）：当前唯一job精确PID/starttime/cmdline及launch/command/plan/controller SHA核验通过，自动进入重新启用B-r20。B64、A64四cohort完整HTTP成功，输出引用SHA、各组32Added引用/冻结doc顺序/unpaused和max_running32核验通过；A第二轮receipt SHA21bc9fd25ccebc717568ac24fa252c97db4117a36b078e3d5ca5ef4db84891cb。B重新启用首轮27/32成功、32Added已通过，admission SHA469a27cb5c616a5e272bac33425e468be205c3259954d897612a99f16836b395。r20 manifest SHAcb8d921530d9acf96a4b63924bfc430d6cfe7f35100c328d26690dc7a7bcf1e6、qualification SHAf0601fb178f328b94b077a660dba2e9404fd4517ed30fdc519fd7ab8607d7254。合计155/192仍partial，无native结果/错误或最终恢复，不运行完整核验器；无新用户操作，保持安静并等待唯一既有控制器。


## 原26失分题有序B/A/B192独立完成：六轮24/32、全文全部一致

ordered-loss001原生exit0，result SHA5d8d6fb984afc306074677c66b5b482885a6bb47177bcfa6fe1fe3eb23611b52。预归档verify-ordered-loss192-001.py已执行成功，verification SHA9a9658a4acbfc88d05808d0cb79f68e9dd0f4eb79c3830b3590a1bb548d2ec43：192响应/Added exactID、PID/inode-offset/原始日志行SHA/原body/原生pause-utility-resume/实际C32/两rank源清单全部通过。32题六份全文逐题完全一致，stableAB0、unstable0；native strict六轮均24/32，评分 SHA80c5d40e7bb6d98ad209a861b373facc688bd0afb74a73e95acedf549dc9a1f3，原生filter/metric代码未变，原198逐题再次重现160/147。原26失分题每臂均19对7错，6道逆向controls均5对1错；每轮同1题到length预算（总6响应），原样保留并纳入原生strict，未放宽健康/评分规则。

r21恢复原launch-v2，无日志/profiler/hooks且unpaused，全部稳定manifest字段与r18相等；restoration SHA1a58cdd4bc147cd294f99f448db2fe199b0b2944f822b3c07ae84b1aedde957d，manifest SHAa15c0cc661e12c6ba61b60f8df226089fef2c6e01fd06408bd55f16c86f5eb1f，qualification SHA41ce13023f06a101c73a28b9df990819f137f3daec17239b5d4e92184bc34e13，fresh runtime SHA019b203377a260ef8d4e1c0fb66195970495ddaf0a018ab733912219a0a78388。FGV两rank仍未加载，安装一致性不扩大为内核覆盖。

结论：这一覆盖全部原26失分题的固定有序组合也未复现base/当前容器稳定区别，没有证据支持开始单变量数值回退。与既有free/queued/free及profile分组差异结合，准入/执行分组是有证据的重复性边界；原完整少13题的具体因果仍未确认，不能据小样本宣布迁移无退化或正式精度恢复。原147<160、无gate、禁止正式candidate性能均保持。不再自动扩大样本或重放旧B/A/B；下一阶段只读/CPU形成原生完整198可审核方案，具体处理transport/失败/provenance/日志launch与gate生命周期，任何正式协议变化仍需用户授权。

执行前归档状态checkpoint：`/public-flash/jinghao/qwen3.6-35B/20261022-qwen36-35b-mx104-stack-regression/commands/checkpoint-ordered-loss-verified-001.py` SHAc58be0604ec42e93d48c67c92db1e21a51527fb9854c1984486af98d929a4bff。仅核验并清除已完成current_job、记录独立结果，不运行模型/重启/源码变更。

执行前归档只读交叉复核：`/public-flash/jinghao/qwen3.6-35B/20261022-qwen36-35b-mx104-stack-regression/commands/compare-ordered-cohorts-readonly-001.py` SHA814af9708602ac29ad8cfc3a333e63aea6b8509c8682b75b834906f70279ca2b。比较两份已核验192报告共有10题的原body、全文及原生strict，并逐角色核对两个cohort的所有稳定manifest/launch字段；0新生成，不把不同32题集合的总分直接比较，不把执行上下文敏感性等同具体算子根因。

只读交叉复核完成，report SHA0a13844b50e393d538087210fb5590d6a0ee23b7958d30c7e56e3c288da8e76f：两组已独立通过的有序C32 cohort共有10题[1,4,8,12,13,22,25,28,29,31]，同题body SHA相等，各角色两组所有稳定manifest/launch字段一致；跨cohort10题全文均变，strict翻转题[8,13,22]。同cohort内A/B六份全文仍全等。这增加cohort组成/执行上下文敏感性证据，但不证明精确设备shape、具体算子或原完整13题因果。0新生成。

规划复盘regression-planning-001已同步：当前累计四正式场景均无有效A/B收益，prefill/mixed准入分组与raw概率差异仍是定位线索，decode shortlist/GDN/graph旧窗口覆盖不外推全198。第一优先只读/CPU把实际native198 transport/CLI/provenance/失败处理及日志launch/gate绑定方案做具体；第二只读归纳共同上下文敏感性，必要新采集先具体限额方案；第三代码单变量回退等待稳定AB，不能盲回退。没有新full198门禁，性能测量仍阻塞。不自动新增诊断轮或重放旧控制器。

状态checkpoint完成，continuation SHA63da39551dfcf737f472d3bcf28287d85f706d4207489bce9b2353fa641a35ed；phase=accuracy_diagnosis_ordered_loss_verified_readonly_planning/current_job=null/last_completed_job=accuracy-ordered-loss-001，有意无待接管作业。结论产物SHA db05b2e8ec3666662a3a575853e81baec7c9c0943d96cfff9d706727989b05a1。


### native198入口与门禁边界CPU审计（执行前归档）

只读确认远端continuation仍63da39551dfcf737f472d3bcf28287d85f706d4207489bce9b2353fa641a35ed、无job、原r21恢复；实际冻结formal wrapper SHAd345525c44a289ce5d92f63f065c5d9e40750d069e0ef7a5b39f17fa258aa6bc、acceptance SHAb6f5efcc7fc492e29a6df1c37248bcdcc090fa892b3a3b996b1cee393be4ef8b，原llmrun仍82cf6e...。正式wrapper明确调用原lm_eval模块；当前guard只接受openai-chat-completions、cfg endpoint必须等于service manifest；stable identity只排除实例/runtime，日志flag仍属launch身份。不能经HTTP proxy换endpoint、隐藏registry覆盖、model alias或日志参数忽略来冒充旧formal gate。

预归档 `/public-flash/jinghao/qwen3.6-35B/20261022-qwen36-35b-mx104-stack-regression/commands/native198-cli-cpu-audit-001.py` SHA1b5fc48fcb4aa5ca3073e4e6afc907be36ada1b023f17403f157d7bb3b43d8f2；计划执行 `docker exec qwen36-35b-regression-eval-20261022 python3 -B /public-flash/jinghao/qwen3.6-35B/20261022-qwen36-35b-mx104-stack-regression/commands/native198-cli-cpu-audit-001.py`。全程CPU/假HTTP/socket拒绝联网，重用SHA绑定prototype的AST前缀且严格停在旧产物mkdir前，不重放任何模型请求或原报告写入。检查真实registry独立alias、不覆盖原backend、原runner build_command/实际CLI解析、现有formal guard拒绝新alias和日志/无日志稳定身份差异。成功不等于live adapter或正式协议就绪。

CPU审计已原生退出0，report SHAb9e788fc5fe2409ff67019d8797d7a4c47be16401a181c5d301857f17630cf45。实际原runner构造命令/原生CLI解析了独立alias，seed四项42、C32/timeout7200/max_retries3/原gen_kwargs保留；registry原openai-chat-completions指针未覆盖，native generate_until/builder/create_message/parse继承不变，假198的payload/parse/cache/usage/顺序及32x6+6和故障case再次通过。原backend config通过冻结acceptance，而新alias被现有formal guard明确拒绝；日志r20与恢复r21的stable identity仅launch_config不同，不能rebind。0网络尝试/0真实模型请求/0服务操作。该结果只说明CLI/guard边界清楚，live ordered driver、explicit CLI模块、失败/provenance sidecar及正式协议绑定仍未实现，不宣称formal ready。

下一CPU证伪：把独立inactive native transport driver置于案例命令目录，在ephemeral loopback synthetic HTTP fixture验证真实aiohttp异步session、FreshAddedLog解析、pause/utility/resume、同32x6+6及故障latch/no duplicate sends；绝不连接18135或改实际服务、原registry、vLLM/Plugin/Gems/门槛/正式guard。保留原工具版本。准备完成后才形成需要用户审阅的确切正式协议/launch-gate方案，不提前问已有日志诊断授权。

执行前归档CPU checkpoint `/public-flash/jinghao/qwen3.6-35B/20261022-qwen36-35b-mx104-stack-regression/commands/checkpoint-native198-cli-cpu-001.py` SHA37cb1a95b33379ee520dad21b978fd8c9ac60d7b7bc1ef8776d3098f04cf5dd2，仅记录报告和下一CPU任务，无后台GPU作业。

CPU planning checkpoint已完成，continuation SHA460270b1120cc14bbe009ec9e743b6c4b20e5545bee97faa075925d8d17adbfe，phase accuracy_diagnosis_native198_cli_cpu_verified_readonly_planning，current_job=null。只更新optimize规划视图，没有新formal分数或门禁，baseline/acceptance正式事实未变。现有native CLI解析检查不等于完整native cli_evaluate或live driver已实现；下一CPU synthetic session/收发回执与失败sidecar验证仍需完成。状态不变安静，无新的用户操作请求。


### 实际异步session与回执解析的CPU loopback准备（执行前归档）

继续只读/CPU：native registry/CLI边界已明确，现准备独立inactive OrderedTransportChat（仅synthetic_loopback_only且端点必须127.0.0.1非18135），保持原native generate_until/payload/parse/cache/usage方法。合成HTTP fixture只bind127.0.0.1:0，socket连接白名单仅当前fixture端口，绝不真实服务。用真实aiohttp/session/urllib和冻结FreshAddedLog解析器验证198全部wire SHA、逐条发送回执+pause/is_paused/resume、32x6+6、尾6、乱序完成后原序/cache/usage；5种故障（missing ack、错PID、barrier500、resume500、HTTP500）检查latch、无重复wire、无后续wave、原生TIMEOUT映射与独立failed sidecar，cleanup异常只用合成emergency callback，不假装真实PID stop能力。此不是live adapter、实际native CLI/evaluator发布或新formal gate。
- `/public-flash/jinghao/qwen3.6-35B/20261022-qwen36-35b-mx104-stack-regression/commands/q35_ordered_transport_cpu_001.py` SHA99594849782fb69e3fffc5068a9a992883511bb7f1c206357ff9add36231026e。
- `/public-flash/jinghao/qwen3.6-35B/20261022-qwen36-35b-mx104-stack-regression/commands/native198-loopback-cpu-001.py` SHA81407e6c891a8c6bba65ed05622a4a1788a16b15558676546e5d0afd3d73a252。
预声明命令：`docker exec qwen36-35b-regression-eval-20261022 python3 -B /public-flash/jinghao/qwen3.6-35B/20261022-qwen36-35b-mx104-stack-regression/commands/native198-loopback-cpu-001.py --cpu-loopback-selftest`。全程0真实模型请求/0实际服务操作；失败产物保留，修复另新版本不覆盖。

CPU fixture首次执行前强化依赖SHA守护：旧001仅归档、尚未执行/0请求/无产物；改用独立002（不覆盖001），增加旧prototype报告及其全部native源码、重建payload与driver模块SHA强校验，测试逻辑与6案例不变。新 `/public-flash/jinghao/qwen3.6-35B/20261022-qwen36-35b-mx104-stack-regression/commands/native198-loopback-cpu-002.py` SHA359122db9fc2145aef82f5eea13719235a8c047ed39b4d1bc19762f4b6ef729b，命令 `docker exec qwen36-35b-regression-eval-20261022 python3 -B /public-flash/jinghao/qwen3.6-35B/20261022-qwen36-35b-mx104-stack-regression/commands/native198-loopback-cpu-002.py --cpu-loopback-selftest`。输出native198-loopback-cpu-002独立目录；旧001不运行。

CPU loopback002已退出0：report SHAcca19c4b2dae943ec82a188907039a0fc5bf4f2a21b42c185f62d8c983e729cb。6场景全通过：正常198真实aiohttp合成请求、32x6+6、原生wire SHA/parse/cache/usage/顺序通过；missing_ack与wrong_pid各10提交9ack，barrier500/resume500/http500各32，均无重复wire/无后续wave。所有失败仍被原生generate_until映射为198个TIMEOUT，但独立sidecar保持failed，不能被原生进程成功吞掉而签gate；resume500只触发合成emergency callback，不能冒充真实PIDstop能力。共314个合成请求、63个管理command URL逐项确认仅127.0.0.1非18135，0非fixture网络/0真实模型/0真实服务操作。注入取消时合成HTTP服务器输出两条ConnectionResetError，保留原始工具输出；属于模拟断连路径，不是真实服务错误或全案例失败。001脚本仅归档未执行，旧001产物目录不存在；driver001由002使用，所有原工具不改。

仍未就绪的边界：使用native模型方法的实例来自CPUfactory，真实constructor/完整native cli_evaluate/task与样本结果发布尚未运行；driver严格限制synthetic_scope、没有真实endpoint/精确PIDstop能力。不能把CPU通过外推到live模型或formal门禁。下一步集中完成实际native constructor/显式新alias CLI/evaluator全198合成闭环及失败sidecar与结果provenance的绑定，不再扩展任意小mock；然后形成确切正式协议/launch-gate方案并审阅是否需要新例外。

执行前归档状态checkpoint `/public-flash/jinghao/qwen3.6-35B/20261022-qwen36-35b-mx104-stack-regression/commands/checkpoint-native198-loopback-cpu-002.py` SHAfe14b21b623f279e54a7e266d4c3b59a1d9104f30cb335095a14fd6ed28e620b；只登记CPU结果和下一阶段，不产生真实模型流量。

CPU checkpoint已登记：continuation SHAb5dc90bd063c61b5a0ad0bda9b20e9fd7fd4253ee4edadd40c29c788c1b21fb1，phase accuracy_diagnosis_native198_loopback_cpu_verified_readonly_planning/current_job=null。此次只更新optimize规划视图；原baseline/acceptance完整147<160事实保持。下一集成限实际native constructor/CLI/task/样本结果198合成闭环及具体protocol/identity方案，防止无限增加CPU小探针；仍不运行实际模型或旧作业。


### native198 完整原生 CLI / 合成 HTTP 闭环（预归档，CPU-only）

2026-10-24：远端 continuation SHA b5dc90bd063c61b5a0ad0bda9b20e9fd7fd4253ee4edadd40c29c788c1b21fb1，current_job=null，仍为原配置 r21。仅执行实际 native constructor、原 GPQA198 task、cli_evaluate 和 results/samples 发布的合成闭环；显式 alias qwen35-ordered-synthetic-cli-001，不覆盖原 registry，不调用真实 18135 或操作服务。网络白名单只允许新建 127.0.0.1 随机 fixture 端口；原生参数、payload 和 strict 保持，合成输出不代表模型精度。正常198及 http500 失败路径检查 native 输出与失败 sidecar 绑定，无后续 wave/重复 wire。

执行前归档远端 commands/native198-fullcli-loopback-cpu-001.py SHA bd49bc04281f616bacad423a57978efd656e20fc3f60b4dda923d93912f8950a，以及 commands/q35_native_diagnostic_cli_cpu_001.py SHA 9cd800cdf03c922e751b48e48016750cb3862a77d59107d6275ce293d00e4cd8，均在当前 CASE 根路径。执行命令：docker exec qwen36-35b-regression-eval-20261022 python3 -B /public-flash/jinghao/qwen3.6-35B/20261022-qwen36-35b-mx104-stack-regression/commands/native198-fullcli-loopback-cpu-001.py。原工具和旧结果不覆盖；异常保留新 failure.json，不重放已完成模型流量。此闭环通过也不是 live-ready 或 formal gate。

CPU CLI 001 在 AST 复用前缀阶段因保留 parser.add_argument 而未保留 parser 定义，NameError 退出1；尚未创建新输出目录，0 合成/真实请求。原脚本保留。独立002仅修正排除旧 parser.add_argument 并增加 CLI 模块 SHA 检查，SHA 5131bbab27d81683259605b74ba4cc922e43f8dc467ddece64a23969310604f7；执行同上仅将文件后缀001改002。

CPU CLI 002 已完成正常198合成请求、真实 constructor/原 task/CLI/结果发布，7 waves32×6+6，transport completed；随后观察层按 str.splitlines 及每题一条记录假设解析 samples，遇文档 Unicode 分隔字符且实际每题 strict/flexible 两行而退出。原生结果不改。独立003 SHA d39a4b1c4ec77185f80941b58340dd4008e4634732d5bb7a89cf57aa487f86f5 按 LF 及每题两 filter 只读核验既有正常198，不重放正常流量；只执行原未提交 http500 失败路径32次合成 wire，验证失败 sidecar 和原生输出绑定。执行命令同前文件改003，旧错误保留。

CPU CLI 003 已完成原未提交 http500 路径，32 ACK/单 wave、failed sidecar，native 将198项转 TIMEOUT 并发布结果；独立按 LF/两filter 核验正常与失败产物已过，但外层聚合内存断言退出1，不能报全部通过。独立004 SHA fdfff60cb56451f45416e6ef57cd36098e472eae5cd88dd2a5e1b209f711b169 只读核验两份既有 CLI 输出，并对原正常响应数据库做只读 SQLite backup 后跑原生 cached_only CLI，硬拒全部HTTP，0新合成聊天请求，用于捕获辅助网络尝试与发布绑定。执行命令文件改 native198-fullcli-cache-audit-004.py，原失败不覆盖，不重放任何198生成。

CPU004原生 cached_only 成功且无driver/无HTTP，报告 SHA cbcf29828ad752a8c8879405df359814436bda9eddacdad7facdd66b710f13bd；捕获一个 huggingface.co:443 metadata DNS尝试被 socket 守护拒绝。此测试先导入 HF 再设置 offline，与真实 runner 在子进程启动前设 offline 的顺序不同；支持003聚合断言受 CPU harness 离线初始化影响，非真实模型问题。独立005 SHA 46336c8f52b792b59e8bc1e7f71bc0046aa66dc10fbb4418660c1fcf90f176f1 保持只读产物+私有cache快照，进程启动前显式 HF_HUB_OFFLINE=1/HF_DATASETS_OFFLINE=1/HF_DATASETS_CACHE=/root/.cache/huggingface/datasets；再次 cached_only，无新聊天生成，并要求零网络尝试。命令：docker exec -e HF_HUB_OFFLINE=1 -e HF_DATASETS_OFFLINE=1 -e HF_DATASETS_CACHE=/root/.cache/huggingface/datasets qwen36-35b-regression-eval-20261022 python3 -B CASE/commands/native198-fullcli-cache-audit-005.py。旧003结果与未知历史计数不改。


### 完整198题的具体双通道方案（审阅稿，不启动新GPU流量）

选择保留原正式协议，不把有序诊断悄悄升级成 formal gate。原 formal_accuracy→SHA绑定 llmrun→openai-chat-completions、rolling C32、原 task/strict/160/198 阈值、原无日志 launch 和原验收工具均保留。当前正式结论仍是 baseline160、candidate147失败。有序诊断使用独立且显式的 qwen35-ordered-diagnostic-v1 alias；原 registry key 不覆盖，现有 formal guard 应继续拒绝这个 alias。结果、缓存、日志与来源 sidecar 标注 diagnostic，不能拿诊断分数或恢复后的配置签发正式 gate。

具体诊断矩阵为 B/A/B，每臂两次完整198题，合计1188个诊断请求；各臂固定相同 native doc0..197、32×6+尾6，原 task/dataset/seed42/HTTPseed1234/temp1/p.95/k20/65536预算/stops、native payload/parse/cache/usage/filter/最终doc映射保持。每次使用全新响应缓存，禁止复用已有回答；六份全部保留，不挑高分或追加最好轮。每 wave 原生 keep pause/cachefalse，逐条发送并核验 fresh Added精确ID/API PID/offset，随后同引擎 utility FIFO 屏障，再 resume/unpaused；wave全部终态后才下一 wave。尾6原样处理，不能补齐假请求、改C1或改变fallback。请求ID在各臂同repeat/doc一致，内部随机后缀保持默认。此协议与原rolling32不同，属于诊断；不宣称直接读取scheduler队列/设备shape。

服务生命周期预案：仅现有专用A/B/eval容器与GPU0/1。以启动前最新 continuation/PID/starttime/SHA为准，原B-r21→临时日志B-r22→临时日志A-r7→临时日志B-r23→finally原无日志B-r24；这些ID尚未创建或保留，若当前身份已变则拒绝，不复用旧stopper。只加已获授权的日志flag；每次 graph capture/各rank至少两replay、C8与完整manifest比对，另32短资格请求不计入1188。原服务参数、优化源码、模型和vLLM不变，不开启profiler。精确PID/starttime白名单停止，不操作源容器/GPU2/3。恢复需原launch、stable manifest、无日志/profiler/hooks/proxy、unpaused、graph/C8和fresh两rank引用全部通过。

失败策略：native timeout7200/max_retries3配置保持，但有序transport一旦任何ACK/身份/屏障/HTTP/解析失败就锁定失败，拦截重复wire，取消尚未结束的本案例客户端，不提交后续wave/臂；保留全部部分结果、原生TIMEOUT和失败sidecar，finally恢复。启动前归档唯一命令/SHA与started状态；只有native结果、全部样本及transport均核验后才写completed绑定，进程崩溃留下started即incomplete，不凭CLI exit0判通过。外部真实PID失败恢复能力必须使用既有精确stop实现并经CPU故障生命周期演练；当前synthetic emergency callback不是该能力。实际ACK/admin截止时间与总预算须在可执行计划中预冻结，不能看结果延长或补跑。

判读与正式回归衔接：每题每臂两次相同且B重新启用相同、A/B不同，才触发用户已授权的单变量回退；需证明实际执行路径、回退控制差异、重新启用复现。若全198仍无稳定A/B差异，保留未复现结论，不能为了产生根因而盲改采样数值实现。若定位并修复，恢复原无日志参数后，仍须按原formal_accuracy/llmrun完整198重新签发同身份score>=160/198 gate；诊断日志launch的分数不得rebind至无日志服务。正式性能只使用原无日志契约和当前有效gate；所有A/B/revert重建同配置稳态准入，旧11轮incomplete保留且不计入验收。若将来要让有序协议直接成为正式验收，必须另外具体版本化wrapper/guard/protocol/provenance及日志launch全角色性能契约，并取得用户新授权；本方案不执行该变更。

目前只完成CPU核心集成；live端点/真实PID恢复的适配器未启用。下一步限定为独立inactive live adapter及有序198控制器的源码/SHA/CPU生命周期准备，沿用既有日志诊断授权，不自动运行本矩阵或改formal工具。技术准备就绪后按当时真实运行状态和授权范围决定执行；需要新增正式协议例外时再提出具体审批，不能用持续mock或无变化轮询替代推进。

CPU005原生cached_only成功，报告 d36254810f2b2a2c07520266de68b35fc111304aeaf7a68571fce62ba3ef25ad，启动前offline后0网络尝试、0driver/新增wire。下一步只读逐题比较两份原生发布与原198的doc/prompt/target/native arguments并保存checkpoint；commands/checkpoint-native198-fullcli-cpu-005.py SHA fec6b9e6ee9032ae7de3f11a8ab52aa2e0b646931829b982e1c993ae25e03b9e，执行 docker exec eval python3 -B CASE/commands/checkpoint-native198-fullcli-cpu-005.py。仅更新continuation和新独立证据，current_job仍null，旧测试退出状态不改。

CPU核心独立核验完成：005报告 SHA d36254810f2b2a2c07520266de68b35fc111304aeaf7a68571fce62ba3ef25ad；逐题来源报告 SHA 12dae1d99ff9ed67434f2acb87954a21c5053d3cfb0dcaedc8f101894aa789c9，正常/故障均198题、396 filter行，doc/prompt/target/native arguments与原正式样本逐项相等，旧candidate strict147再由原生行复现。当前 continuation SHA f3e08449fd97d32c5698a23622bb326dde252d02a14f3e4e333e07f9ee5996c9，phase=accuracy_diagnosis_native198_fullcli_cpu_core_verified_readonly_planning，job=null，r21配置未操作。本轮0真实模型请求/服务操作；001/002/003失败原样保留，不能宣称这些外层测试全部退出0。监控继续仅用于下一有限技术准备，CPU工作本身不通知。


### 有序198 inactive 实施准备与CPU生命周期审阅

2026-10-24 当前 continuation SHA f3e08449fd97d32c5698a23622bb326dde252d02a14f3e4e333e07f9ee5996c9，job=null、r21原配置保留。只归档未启用工具，不运行真实端点/服务/模型流量。独立计划 execution_enabled=false；每个服务/评测/stop入口均须在任何外部动作前拒绝该计划。原stop/launch内嵌执行代码保持逐字一致，只收窄到本次r21/r22/A-r7/r23/r24并加计划守护。新host lease以实际PID/start_ticks/完整argv后缀和不可变服务引用每2秒核验；eval只读10秒有效host attestation，不假称能读取另一个容器/proc；失效或Host撤销禁止后续wire，恢复失败仅提交精确binding的host emergency request。eval自身取消使用eval容器内PID/starttime和CLI+armplan参数白名单；未确认退出则禁止下一臂或恢复launch。

Live adapter继承原native构造/payload/parse/cache/generate方法，有序transport单独显式alias、不覆盖registry。每波保存raw response/finish/usage/全文SHA和前后两rank、实际running指标；不作收益/FGV覆盖证明。原vLLM/Plugin/Gems/模型和formal guard不改，日志例外范围保持。入口需显式新reviewed计划，当前false不会因调用命令自动打开。

远端执行前已归档CASE/commands独立文件及SHA：
- /public-flash/jinghao/qwen3.6-35B/20261022-qwen36-35b-mx104-stack-regression/commands/qualify-service-ordered198-restore-001.py SHA 1f177d4a7b6717bf23b312ab2dd37a0de8c384d0611554bc37849a6d8dc999a9
- /public-flash/jinghao/qwen3.6-35B/20261022-qwen36-35b-mx104-stack-regression/commands/launch-service-ordered198-restore-001.py SHA eff9e038e4c448cfcf837ee15dddaf7fcec63a79e929361ce30a69d7d1073a25
- /public-flash/jinghao/qwen3.6-35B/20261022-qwen36-35b-mx104-stack-regression/commands/stop-ordered198-eval-001.py SHA dfdb0a941471f109116544aebb3108a91c660d842c3b12c1833ce4095f808004
- /public-flash/jinghao/qwen3.6-35B/20261022-qwen36-35b-mx104-stack-regression/commands/run-ordered198-inactive-001.py SHA 26b5267d05d88e2b8f22cc4fc1067944aa962fbaf78588145f931dc2668b6d54
- /public-flash/jinghao/qwen3.6-35B/20261022-qwen36-35b-mx104-stack-regression/commands/ordered198-liveprep-cpu-001.py SHA b272d4f4b9c46356bea093fc2cfde79921d4a698c52ed21d6ccd8fdbedb1f3a2
- /public-flash/jinghao/qwen3.6-35B/20261022-qwen36-35b-mx104-stack-regression/commands/q35_ordered_transport_live_001.py SHA c0984bb1a4e356790f9737abca431c987da5acd4816a3c0b9531a189f41d17bb
- /public-flash/jinghao/qwen3.6-35B/20261022-qwen36-35b-mx104-stack-regression/commands/stop-service-ordered198-001.py SHA babac681b09693ac4fc9113ad052a2eb32d1e758e159c336b7c7dce2d3af9a9c
- /public-flash/jinghao/qwen3.6-35B/20261022-qwen36-35b-mx104-stack-regression/commands/launch-service-ordered198-001.py SHA 422493a8638a40f318cfc1a1753667399519eb51186df92bf7e3b4017172eb3a
- /public-flash/jinghao/qwen3.6-35B/20261022-qwen36-35b-mx104-stack-regression/commands/q35_native_diagnostic_cli_live_001.py SHA 89cee6032971c2420855a0d3c4258b8bec62517af523abbbbd36d42f3f19cfc4
- /public-flash/jinghao/qwen3.6-35B/20261022-qwen36-35b-mx104-stack-regression/commands/qualify-service-ordered198-001.py SHA aed2859591b570a83ffc90f80fd7f65821eac4a7ccef2ac5fa5218a31c6ac59a
- /public-flash/jinghao/qwen3.6-35B/20261022-qwen36-35b-mx104-stack-regression/commands/q35_ordered198_ownership_001.py SHA fba0d2b4351523386b6010eb7f159b15dc665a19d90f9bb18af6aaf5aee3e85d
- /public-flash/jinghao/qwen3.6-35B/20261022-qwen36-35b-mx104-stack-regression/commands/ordered198-001-execution-plan.json SHA b5b252665b10f9a7734d0771074934d31f32533bb2e58941f02b232904507ca3

CPU审阅命令：docker exec -e HF_HUB_OFFLINE=1 -e HF_DATASETS_OFFLINE=1 -e HF_DATASETS_CACHE=/root/.cache/huggingface/datasets qwen36-35b-regression-eval-20261022 python3 -B CASE/commands/ordered198-liveprep-cpu-001.py。审阅实际orchestrate函数成功及7类失败生命周期、8入口inactive拒绝、PID复用/argv/lease/emergency负向守护、原内嵌stop/launch源码一致性；强制网络/子进程/signal拒绝，0模型/服务操作。mock不是硬件通过。Host只读预检命令为 run-ordered198-inactive-001.py --execution-plan CASE/commands/ordered198-001-execution-plan.json --preflight-only。

本地记录预写首次因stdin解释器编码错误未落盘；远端唯一脚本和SHA归档已在CPU命令前完成，本条用项目.venv解释器补齐本地记录。

CPU001八类actual orchestrate生命周期、8入口inactive拒绝及PID/lease负向核验通过，报告 SHA edb00075db729962dfd77bea1e5a8a5e72ff118e600384763aa525d41379a369，0网络/进程/signal/GPU操作。随后只读复核发现Host cancel在stop_eval自身来源守护失败时可能未及时置eval_exit_unconfirmed；当前计划从未启用，未发生真实取消。独立002先置未确认标志并在finally检查child退出，补四种stop失败/退出组合的真实方法CPU演练，未确认退出则restore在任何动作前拒绝。原001不改、不执行硬件。预归档修正：
- /public-flash/jinghao/qwen3.6-35B/20261022-qwen36-35b-mx104-stack-regression/commands/run-ordered198-inactive-002.py SHA e48de61cf0d8bb553a429d235499a30e5118d79032d9df45e00db69b207f3ee0
- /public-flash/jinghao/qwen3.6-35B/20261022-qwen36-35b-mx104-stack-regression/commands/ordered198-liveprep-cpu-002.py SHA 9ff76b94b2c38ffc0e2e7e2e7008300a58e8f870283e47b19316468e44331eaa
- /public-flash/jinghao/qwen3.6-35B/20261022-qwen36-35b-mx104-stack-regression/commands/ordered198-002-execution-plan.json SHA 16448a9b54a0138589b460f29debf11e62a3a2471786d5798648ee8ec893bb6e
CPU执行命令同上仅入口改ordered198-liveprep-cpu-002.py，保持启动前offline、socket/子进程/signal硬拒绝。

CPU002八种实际生命周期及四种实际Host取消守护组合全部通过，8入口对inactive计划在外部动作前拒绝；报告 SHA b007bcfdfd78dfe3e1ac52b48721631d6cc6f4f5cad88f687cb596389beb21d2。Host只读preflight同样通过，execution_enabled=false，0模型/服务操作，未创建未来服务或1188矩阵输出目录。技术准备已完成，不继续mock循环。当前心跳明确限制“不要默认发1188 GPU流量/重启/新profile”，剩余仅是否扩大至完整198有序诊断的范围决定；日志许可沿用不重问。qwen35b已通过automation_update delete成功删除，等待决定时不空轮询。
预归档 checkpoint-ordered198-inactive-ready-001.py SHA a38613f2706ffc1bffcc082fdeabe46084034d0e721f90f7853f4c4e39e4d139；执行 python3 -B CASE/commands/checkpoint-ordered198-inactive-ready-001.py，只读重新确认完整source清单及native CPU报告，并在原continuation SHA匹配时备份/更新等待决定状态，不进行HTTP或服务操作。

准备完成checkpoint：continuation SHA e227e81168fbc15524f7ee92bcbcc5ac61a5d3f54aa2bd86a39ea1727a32b80d，phase accuracy_diagnosis_ordered198_inactive_ready_awaiting_scope_decision，job=null；Host preflight回执 SHA db093bf495249d192b2cd361e9422b62b5918f5e46bfcbfe05cfaf0844e3a953。baseline/acceptance原正式160/147和性能incomplete保持不变；监控已删除，等待扩围决定。


### 用户确认启动完整198有序诊断（新启用计划003）

用户直接回复“启动完整198题有序诊断”，批准B/A/B各两轮1188诊断+32资格请求；临时日志授权沿用，完整结束/失败后恢复原配置。禁止正式协议/160门槛变化、profiler、vLLM修改或挑最好轮次。当前job=null/r21空闲，GPU0/1两进程只属于本案例B容器，34冻结文件及3份真实native源码匹配，旧作业/新矩阵输出均不存在。
- /public-flash/jinghao/qwen3.6-35B/20261022-qwen36-35b-mx104-stack-regression/commands/ordered198-001-authorization.json SHA 182c794c996a2edfe60e81f1f7cc505726b737869eaf2590c663dc9acc2f5188
- /public-flash/jinghao/qwen3.6-35B/20261022-qwen36-35b-mx104-stack-regression/commands/ordered198-003-execution-plan.json SHA b70139696877b96e5fb1ea24e6ab283935db67582bf9a041b362cbdfc528fc57

原inactive计划001/002不改。执行前Host命令：python3 -B CASE/commands/run-ordered198-inactive-002.py --execution-plan CASE/commands/ordered198-003-execution-plan.json --preflight-only。随后通过SHA绑定原run-background-job-v2.py创建唯一job accuracy-ordered198-001，命令为 ["python3", "-B", "-u", "/public-flash/jinghao/qwen3.6-35B/20261022-qwen36-35b-mx104-stack-regression/commands/run-ordered198-inactive-002.py", "--execution-plan", "/public-flash/jinghao/qwen3.6-35B/20261022-qwen36-35b-mx104-stack-regression/commands/ordered198-003-execution-plan.json", "--execute-reviewed-plan"]。本次only启用新计划，不改已核验控制器。

启用003只读预检通过，来源服务PID171203/start_ticks1108427847、GPU0/1仅属本案例B、native三源码匹配。唯一启动器 commands/start-ordered198-approved-001.py SHA d497716fc1ae932c3afdd0958843745ba308fb0feb439c7f3963d78da73a6bd7；执行 python3 -B CASE/commands/start-ordered198-approved-001.py。启动前再次核对授权/计划/旧continuation SHA、CPU报告、原source精确身份和GPU独占，先保存唯一command/preflight再调用冻结background wrapper；不重复启动job或重放旧模型诊断。

启动成功：job accuracy-ordered198-001，外层PID2685136/start_ticks1111622804精确cmdline匹配，launch SHA1e52a8905a5907ffa297d79db66ea550f19809e3153083e1df854d876515a137、command SHA16063b225bbf07640d531feddc01d3b8d10ceb69497f077833fa2f56ff33ecae。当前phase accuracy_diagnosis_ordered198_loading_candidate-01-r22、native result尚无；服务日志已显示模型加载/graph capture。监控qwen35b重新create成功、ACTIVE/hourly。活动controller会CAS写continuation，因此不并发改它的旧automation/awaiting历史字段；以新授权/当前job/原生进程/本监控为准，待终态再整理。当前没有本轮精度结论，正式147<160不变。


### 首次完整有序启动的工具路径错误与接续

首臂r22 graph/C8/manifest通过，但native CLI在任何wave或诊断HTTP提交前调用check_lease失败：继承的CPU ref函数要求Path，实际绑定路径是str，AttributeError: str has no read_bytes。0 request/response/admission文件，native child退出1；原控制器在finally自动恢复r24，目前不并发干预。工具错误不属于模型精度退化，旧job/源/部分证据全部保留，禁止重放原控制器。

独立派生工具只将ref(r[path])改为ref(Path(r[path]))；其余只改唯一root/job/模块引用与服务白名单，接续使用source r24→日志B-r25→日志A-r8→日志B-r26→finally原B-r27，矩阵仍是全部尚未提交的1188，不重试已提交诊断。旧job的r22/r24资格请求作为额外历史16条单独保留，不混入1188或隐瞒为本轮32。用户刚确认的1188诊断授权继续有效，无需重问日志或扩围。

预归档路径修正与针对性CPU测试：
- /public-flash/jinghao/qwen3.6-35B/20261022-qwen36-35b-mx104-stack-regression/commands/q35_ordered198_ownership_002.py SHA e6df47aece7ad345ec269e099838dcbe179f89d092d2e4c37c8a35409c9d6533
- /public-flash/jinghao/qwen3.6-35B/20261022-qwen36-35b-mx104-stack-regression/commands/q35_ordered_transport_live_002.py SHA b0763d2564b6accf72d0320ffb9d56503480a714f439d2c9a53a64fac87c6dbd
- /public-flash/jinghao/qwen3.6-35B/20261022-qwen36-35b-mx104-stack-regression/commands/q35_native_diagnostic_cli_live_002.py SHA 0b2a0dea2d8fc2a6729a815acd29c4636d5798956ff40b223e119c5b7a2d1911
- /public-flash/jinghao/qwen3.6-35B/20261022-qwen36-35b-mx104-stack-regression/commands/launch-service-ordered198-002.py SHA 4c90e308aa77cbeab495f6087caeba49552a1f4cea78647355b1ec6eee59392b
- /public-flash/jinghao/qwen3.6-35B/20261022-qwen36-35b-mx104-stack-regression/commands/qualify-service-ordered198-002.py SHA 8d21fd432bb6edc4f2bff7534223b4f6dd361ba86db71ebcb35c7d281dae4468
- /public-flash/jinghao/qwen3.6-35B/20261022-qwen36-35b-mx104-stack-regression/commands/launch-service-ordered198-restore-002.py SHA d7b1b4d909a3fcc4fd5152bb01bd48a7779beaedf05e5f88b748fbb36a9a1195
- /public-flash/jinghao/qwen3.6-35B/20261022-qwen36-35b-mx104-stack-regression/commands/qualify-service-ordered198-restore-002.py SHA 6872499607c0ceddf3c57e8662dbb643ab6684faef2123348085ded129347154
- /public-flash/jinghao/qwen3.6-35B/20261022-qwen36-35b-mx104-stack-regression/commands/stop-service-ordered198-002.py SHA 5e5f0e93d561ea2d3c75e9cf8098fc052285756f9c3c2ea6c1b829ba56df02b8
- /public-flash/jinghao/qwen3.6-35B/20261022-qwen36-35b-mx104-stack-regression/commands/stop-ordered198-eval-002.py SHA dde08b9982115c7d535f0ce31280249a97f7da4060451ede38ba7986c9b96f05
- /public-flash/jinghao/qwen3.6-35B/20261022-qwen36-35b-mx104-stack-regression/commands/run-ordered198-followup-001.py SHA e77c0e64eab7c77b583a607d59df46b5f78fdc5f6f48260ed5fe541942a9840c
- /public-flash/jinghao/qwen3.6-35B/20261022-qwen36-35b-mx104-stack-regression/commands/ordered198-pathfix-source-delta-001.json SHA 3efb896028378e3683ef4bf7cf24cf9bea5b2fe82a6055dfb0f5465504f27872
- /public-flash/jinghao/qwen3.6-35B/20261022-qwen36-35b-mx104-stack-regression/commands/ordered198-pathfix-cpu-001.py SHA e5f20720996de311de5bb6adf656712a2b414464de574555f9de7355916405bc
CPU命令：docker exec -e HF_HUB_OFFLINE=1 -e HF_DATASETS_OFFLINE=1 -e HF_DATASETS_CACHE=/root/.cache/huggingface/datasets eval python3 -B CASE/commands/ordered198-pathfix-cpu-001.py。使用真实临时JSON文件与原ref函数，不再mock ref，精确复现str失败、修复后lease通过且篡改文件被拒；无任何网络/服务/模型/signal动作。核对每个派生文件的可逆源码delta，实际生命周期逻辑保持已过CPU002原样。

原job已native exit2、r24原launch graph/C8/manifest恢复passed，current_job=null，continuation SHA3598b841ebf487295720c8546b8baa61efc440e7a7f092c5930b01ce35d622f3。Path真实接口CPU回归通过，报告SHA512bb910cbb7e6a2802a7bac2a2b8e073996868d028fd4dde2dd132ed26482b6。预归档 prepare-ordered198-followup-001.py SHA 0525c11cbc8e359139e4d25ff8b178976d27e4ff160feca3ac87455f5e1023b7；执行 python3 -B CASE/commands/prepare-ordered198-followup-001.py，只读冻结old native2/child1/精确Path错误/0wave及0诊断ID，独立fresh只读RPC确认r24恢复身份，保存0题证明；生成唯一新004启用计划并做只读preflight。该脚本不启动模型作业，随后另按返回SHA执行启动。

接续准备只读预检通过：新004计划SHA71b282724c05fd7cf4f0cdb194a9ca6287f15ba43097fab1ba27bee333c261fb；原失败0题及恢复证明SHAef86c2a55d7ff9fc3d7c1268619cebf97a4863d2f8624d93a68cfd2eb990dd28；fresh原配置r24 RPC SHAbe3bf5a529d77ecf5297750264e48949100c63abf66ecaef5c4505d1db33be8e，unpaused/nohooks/profilerNone与stable manifest一致。
预归档一次性启动器 start-ordered198-followup-001.py SHA 17c7bc09c30fb31ef2af59241cc2bba046f05ae6883ebb95c3867f00ae764ed6；执行 python3 -B CASE/commands/start-ordered198-followup-001.py。仅在旧native2/0题证明及r24精确PID180792/start_ticks1111646398仍匹配、GPU0/1独占时，通过原background wrapper创建唯一job accuracy-ordered198-followup-001。后续仍1188未提交诊断+新32资格，旧16资格保留为历史额外开销。

接续已启动：accuracy-ordered198-followup-001，外层PID2712023/start_ticks1111690462真实cmdline核验通过；launch SHA65d49288cbd5252572bd6ba436221cb421ff08f396082677911cfb67d9693d44、command SHAc36b3de6e4e8a8a12f0fef1a2187b74c5c028e70710e1bba28219bb7ad536d8c，phase accuracy_diagnosis_ordered198_loading_candidate-01-r25，result未出。监控prompt已改为跟进此唯一job/004计划与r25/A8/r26/r27；旧001不可重放。当前尚无本轮精度结果，不将加载/CPU通过当作模型验收。

第二次job在原config读取又遇runner.load_config(str)接口错误（要求Path.is_file），仍0wave/0诊断，正在自动恢复r27；记录工具问题而非模型退化。新CLI003只增加load_config(Path(cfgref.path))，其余新命名空间source r27/B28/A9/B29/restore30；先审阅真实CLI AST配置→cache/命令构造段及内嵌ExplicitOrderedChat原构造器、全部198原payload/WireSHA，强制无HTTP/进程/signal。不能再次仅mock接口或GPU探错。
- /public-flash/jinghao/qwen3.6-35B/20261022-qwen36-35b-mx104-stack-regression/commands/q35_ordered198_ownership_003.py SHA 8e585710bd5750822fdc98c06b916f8b4af3a29cdac71cdd3742c5c2603cb514
- /public-flash/jinghao/qwen3.6-35B/20261022-qwen36-35b-mx104-stack-regression/commands/q35_ordered_transport_live_003.py SHA 38212d580b9f2c096dbe1d8ccda7dee1c28fc5eaa7047cff1e880883feb7ec6d
- /public-flash/jinghao/qwen3.6-35B/20261022-qwen36-35b-mx104-stack-regression/commands/q35_native_diagnostic_cli_live_003.py SHA bbede07e11a92bb1203dabe9066082ad62c28c9c1b85dffb4d0d662f8380dcec
- /public-flash/jinghao/qwen3.6-35B/20261022-qwen36-35b-mx104-stack-regression/commands/launch-service-ordered198-003.py SHA 8712e684f545b7aa0acd332fabd5a5f4a9cb2807eb28286fcf7399c1bae5c665
- /public-flash/jinghao/qwen3.6-35B/20261022-qwen36-35b-mx104-stack-regression/commands/qualify-service-ordered198-003.py SHA 7f1b5b2ca32fdedf1c7ceb8fb42f256cbe410285e016a8ce171ebb9d2735d147
- /public-flash/jinghao/qwen3.6-35B/20261022-qwen36-35b-mx104-stack-regression/commands/launch-service-ordered198-restore-003.py SHA bbb72ba8f27319b900a673d49335452db60946aa9fcf95e5f1f11717b8d53d86
- /public-flash/jinghao/qwen3.6-35B/20261022-qwen36-35b-mx104-stack-regression/commands/qualify-service-ordered198-restore-003.py SHA cb54058378821267ea9ee34fa78a0348a553d40767e3a7af9e9eca5b6993885b
- /public-flash/jinghao/qwen3.6-35B/20261022-qwen36-35b-mx104-stack-regression/commands/stop-service-ordered198-003.py SHA 78c0cf07a6dc29fde912951539cdf9d9e35670c9877f3cc678789e745d48ce63
- /public-flash/jinghao/qwen3.6-35B/20261022-qwen36-35b-mx104-stack-regression/commands/stop-ordered198-eval-003.py SHA cc02814a4ca2cf6fade856e53d07cb13565c48430385111603fdbdab9f17c9b7
- /public-flash/jinghao/qwen3.6-35B/20261022-qwen36-35b-mx104-stack-regression/commands/run-ordered198-followup-002.py SHA dea77a6248ee851e1607dc05c8d3b25f6e7de2014c6897dc85a45afa1ce6a08a
- /public-flash/jinghao/qwen3.6-35B/20261022-qwen36-35b-mx104-stack-regression/commands/ordered198-native-boundary-delta-001.json SHA c870b54544d8ba50a724aa45614c493163fb3bacf4e64163d07b5d92d920335c
- /public-flash/jinghao/qwen3.6-35B/20261022-qwen36-35b-mx104-stack-regression/commands/ordered198-native-boundary-cpu-001.py SHA 3966e3838b597808995414527e8264e4f9c80cf898492302978beb0102541bdd
CPU命令：docker exec -e HF_HUB_OFFLINE=1 -e HF_DATASETS_OFFLINE=1 -e HF_DATASETS_CACHE=/root/.cache/huggingface/datasets eval python3 -B CASE/commands/ordered198-native-boundary-cpu-001.py；仅真实路径/原生构造/198 payload CPU边界，不执行任务或网络。

实际native边界CPU验证通过：report SHA86d52d3fab0eb0855800c7165cb4ae01c82b74b17576e10cda771928b5a63555，真实AST配置读取→命令→原生嵌套构造器、198原payload与wire SHA全部匹配，0HTTP/生成。第二job已退出2、r27原配置恢复通过、current_job=null，continuation SHA6554ec12ee762daa673f08de4d59bf8a0a3500c701e9cee1a9905ac27b011372。预归档 prepare-ordered198-followup-002.py SHA d26d4062ddd3fcfec2fcfe4384e9a5257f39aab99c33faa4c862d82bb6480ea4；命令 python3 -B CASE/commands/prepare-ordered198-followup-002.py，只读冻结第二失败0题与fresh r27恢复，然后新建005计划（source27/B28/A9/B29/restore30），本次仍仅未提交1188；两次失败合计32历史资格另列。

第二失败0题及r27恢复独立核验通过，证明SHAefb23e82104975c4945838fc0224450c5dd9caa1b74aec0f043c2da6bff7a748，fresh RPC SHA3889972593cd46ea4124f95ce5d5d58212b1edca4a24ec0b83e999b72cbd0701；新005计划SHAebe04cf687c180226fe79c2557e3d48dc4975d808bf2597e3b9829b3be57739c，preflight通过。启动器 start-ordered198-followup-002.py SHA bc2a47b3e05b36e5bbd17a32e593e8920c7dee145f9393ac11a25a950891310d 先绑定真实native完整边界CPU报告86d52..、零题/恢复证据及r27精确PID190244/start_ticks1111714636，保存唯一command后创建唯一job accuracy-ordered198-followup-002。执行 python3 -B CASE/commands/start-ordered198-followup-002.py；不执行旧job，不重试已提交诊断（两旧均0）。

最终接续启动：accuracy-ordered198-followup-002，外层PID2739643/start_ticks1111757323精确匹配；launch SHA78431df13ba9b1145c48b2bc046534a941fc9a0c84d895be8a42ce102b9f6bdc、command SHA1122dd5da88c02c3fafacec2342e50544133aef0aeb3a11e6d8e46ed5aba2ff4。phase accuracy_diagnosis_ordered198_loading_candidate-01-r28，result未出。监控已更新为005/当前root与r28/A9/r29/r30；旧两job0题错误、原16+16资格/恢复全部保留。当前不报实际首波已提交或新模型得分，需看真实回执后再更新。

首波已真实开始：phase accuracy_diagnosis_ordered198_running_b1_r0、32request/32ACK且已有响应，尚未完整198分数。预归档只读首波核验 verify-ordered198-first-admission-001.py SHA a2ce96c52bccc1ad96174b95dd9e4914224fbaabf50084e3fb2dd851757bceb7；命令 python3 -B CASE/commands/verify-ordered198-first-admission-001.py，逐项匹配32原payload/wireSHA、native Added PID/精确ID/inode/logSHA与屏障、已完成rawresponse与usage/textSHA，不新发任何HTTP/生成；仅progress证据不是full gate。

首波独立只读核验通过：commands/ordered198-followup002-first-admission-001.json SHA572c1c89d03bb56c489b8b9473478ea5730ad973fcd5fb63b5efadea1cb4a385。32实际提交有native精确Added PID/ID/inode/日志SHA与屏障支持，32payload及默认wire SHA与原native198一致；观察时19份response raw/ID/usage/textSHA通过。B-r28 manifest SHA1384885d8413ab85c04b2812540eeb9e5651bdecbfee7ea06e1745666fc27371、qualification SHAedcb8850bde867ecc2ed8059e7c7a2ab6a1cdf643216c4c2c54e4e26d2fd1951；phase accuracy_diagnosis_ordered198_running_b1_r0，continuation SHA64ac38a6471c8e30601a6b520b5b5bed6f79873684882354f15bf6ceb319db2c。只有partial progress，六轮完整分数未知，不是formal gate；后续不得再整轮重试已提交1188。


### 2026-10-24 10:37 有序198诊断进度与独立产物核验准备

只读检查确认 `accuracy-ordered198-followup-002` 精确 PID/start_ticks/cmdline 仍匹配，当前 B-r28/repeat-0；首波32返回齐全，第二波32已准入、观察到31返回，原生作业尚未终态。没有重放请求或改动 controller/continuation。

执行前归档纯文件核验器 `/public-flash/jinghao/qwen3.6-35B/20261022-qwen36-35b-mx104-stack-regression/commands/verify-ordered198-artifacts-001.py`，SHA `df0c382281ff3ea45893f3df0005e5f9e71718f15d9a52fc1dcb5861bec19bdf`；唯一命令 `/public-flash/jinghao/qwen3.6-35B/20261022-qwen36-35b-mx104-stack-regression/commands/ordered198-artifact-checkpoint-001.command.json`，SHA `16129e3983a5c9a356b192b4562a7b4d4ed0f78e6ecd2dc1f8cb0dbb8c826b68`。核验完整 wave 的请求字节、Added 身份/日志/顺序、管理回执、raw 返回与 usage、实际并发、两 rank 源引用及 graph/C8 资格；不发 HTTP、无新生成、不评分、不签 gate。该核验器的全量模式仍仅覆盖归档产物，最终还必须原生 strict 独立重算和 fresh 恢复核验。当前命令只核验已经完成的 wave，结果待实际执行。

独立观察命令001在 Host 检查 eval 容器专有 `/app/lm_eval` 路径时退出1，0模型/管理请求、未生成验证报告。保留原失败；核验源码未改，仅将新唯一命令002置于专用 eval 容器执行，命令 SHA `383b26065ed6a858c129418500a75baacfd2679fca6164019e2db4e2f224144e`，输出另用 checkpoint-002，不覆盖001。

checkpoint-002 原生退出0：前两波64响应的原payload/wireSHA、逐条Added顺序/日志、管理回执、实际C32、两rank runtime/source与graph/C8已独立通过；报告 SHA `98d5273bbeb136b08e9d2aa991a092c985d1f0a10f6ba1cfeba7eb95ede8593b`。当时第三波32请求及32ACK、5返回，仅属于进度，不代表完整198或六轮得分。

另归档未执行的全198原生strict离线scorer `/public-flash/jinghao/qwen3.6-35B/20261022-qwen36-35b-mx104-stack-regression/commands/score-ordered198-native-001.py`（SHA `c4a890a9d5466c970d053035ab164047e8ad0fae25c5425b80dfacd52fd9a51e`）及核验准备清单 `/public-flash/jinghao/qwen3.6-35B/20261022-qwen36-35b-mx104-stack-regression/commands/ordered198-independent-verification-preparation-001.json`（SHA `fe5e8892bc2b1885cda5e36d5d28c1c11684442f6c9d81254f24fbe1cd0fd8b9`）。仅AST语法审阅，尚未完整矩阵实测，不宣称最终核验已通过。完整独立结论还须六份396行native样本、原160/147重算、全部42波及fresh恢复证据；任何partial不能执行全量入口或重跑1188。

02:39:17Z最后只读检查：精确wrapper身份仍匹配，原生result尚无，B-r28/repeat0；前两波已完成，第三波32已准入、10返回，累计96准入/74返回，完整轮次分数未知。Controller与continuation未修改，源服务及其他GPU未操作；本轮无须用户操作。


### 2026-10-24 11:40 有序完整198诊断例行检查

既有唯一作业wrapper的PID/start_ticks/cmdline匹配，B-r28/repeat0；首四波128返回完成，第五波32已准入、31返回，观察累计160准入/159返回，无原生终态或错误回执。未改continuation/controller或推理代码。执行前归档新的纯文件核验命令 `/public-flash/jinghao/qwen3.6-35B/20261022-qwen36-35b-mx104-stack-regression/commands/ordered198-artifact-checkpoint-003.command.json`，SHA `ae65b379d007f008e59f65b83280d63d614c27ef8bd79ba1f09decb5d70fe8c8`，沿用已通过的独立产物核验器；只核验完成wave，不重放任何模型或管理请求，输出唯一checkpoint-003。

新checkpoint-003原生退出0：首四波128份返回全部独立核验通过，报告 SHA `1b4efb92a05d9a6773ea0598503b335a016adea8aef6f9b0bfbeca23900f2f42`。03:41:10Z仍为B-r28/repeat0；累计160准入/159返回，最后原生metrics running1/waiting0，ownership lease内容时刻约0.6秒前，未见native terminal/error。不把部分返回或进度条当完整得分；无新模型/管理请求、无服务变更、正式160/147及性能阻塞保持。


### 2026-10-24 12:38 首个完整有序198轮次终态与独立核验准备

唯一控制器精确身份保持，phase已进入B-r28/repeat1；B1/repeat0原生终态completed/exit0，198返回齐全，第二轮已进入第二波。先不依据未核验分数作结论。新归档纯文件checkpoint004命令 SHA `9106c6825b9cb065c03266840c1935503aa65b10a378d54214c6661bdc46c8f2`。首轮原生发布样本实际filtered_resps为单字符串列表，而独立score函数prediction为字符串，故未执行的全量scorer001存在观察层表示比较错误；保留001，归档002仅改为 `[prediction] == filtered_resps`（SHA `ebb21c79e23b291910a2203a337fdd2081ce4040f2a36bfec5603b852b44b7f0`），不改strict函数/数值/模型。独立首轮scorer `/public-flash/jinghao/qwen3.6-35B/20261022-qwen36-35b-mx104-stack-regression/commands/score-ordered198-first-repeat-001.py`（SHA `5b553b627be67764ed2976f4bed4d8a7b66040f2f6f281b14f174df64648d9af`）派生自002，仅放行b1/repeat0 completed/exit0及已核验七波198，先重现旧160/147，再匹配396行原生发布。score函数AST与原scorer完全一致，仍无formal gate或AB结论。新评分命令待artifact报告SHA绑定后归档再执行。

checkpoint004退出0，首轮七波198与第二轮首波32共230返回已独立通过；报告SHA `d62029d8e2ca075e4414748c9db52d859ac928f0c1259fb491dc095e23132576`。现归档首轮离线原生评分命令 `/public-flash/jinghao/qwen3.6-35B/20261022-qwen36-35b-mx104-stack-regression/commands/ordered198-first-repeat-score-001.command.json`，SHA `c06331db7f43566e790c710a6444d0fac4257f9596e5e2e2c95225b6343ffea7`；前件和产物SHA均冻结，仅创建新独立核验目录后执行，不生成/重放模型输入。

首轮独立原生strict评分退出0：B1/repeat0为156/198（0.7878787878787878），原396行doc/prompt/target/arguments、raw文本和usage、过滤器及发布分数均匹配，旧正式160/147逐题重现。报告SHA `e0d8b779ac87b48194052f760f2f4856a593a29d0caecbbe7da913cd12d13430`。这是新有序协议的第1/6轮诊断分数，不能直接与旧滚动协议计算迁移收益，不能发gate；原正式147<160未改变。04:41:46Z仍B-r28/repeat1，累计262准入/261返回，A及重新启用B尚未开始，单变量回退仍未触发。归档更新后的全量核验准备002，SHA `de6b09528f6d606e13b1a63f3be08aa61814f6e8ce2b102c6c1019104eac1ebf`，未来仅使用scorer002；旧001保留不执行。


### 2026-10-24 13:39 有序198例行进度

05:38:47Z精确wrapper身份仍匹配，phase B1/repeat1、B-r28，作业无result或错误回执，lease内容年龄约1秒。首轮198已完成；第二轮四波128完成、第五波32准入/23返回，累计358准入/349返回。新唯一纯文件核验命令 `/public-flash/jinghao/qwen3.6-35B/20261022-qwen36-35b-mx104-stack-regression/commands/ordered198-artifact-checkpoint-005.command.json` 执行前归档，SHA `449d9c2a82c95c239d7408dee112abb0ac85d923ca0ccc36197ba555209d373d`，沿用已验证核验器，只读取已完成wave，不生成/重放模型请求或访问服务管理接口。

checkpoint005原生退出0，11完成波共326返回独立通过；报告SHA `c52fd33a693abc1cc2b9db7e5b0f8d40e0ef0ac9febc9cb057b6c196b1f8a19c`。05:39:38Z第二轮第五波返回24，累计350原始返回/358准入；没有新完整轮次分数或AB结论。首轮156/198诊断分数和原正式147<160保持，状态正常，无需用户操作，静默按小时跟进。


### 2026-10-24 14:44 B1两轮完整结束，Base臂已运行

06:43:53Z控制器精确身份匹配，B1两轮各198原生completed/exit0，自动切到A revert-01-r9并开始repeat0；A首波32完成、第二波32准入/25返回，源容器/其他GPU不操作。新归档纯文件核验命令006，SHA `ffab3108a86e84f24d1be8e7e36d2f575b45c9f0ece6a1cee404f7629127d3f0`；B1-pair原生离线scorer SHA `29eda65f3b08b932d39bf05e93d383a9e433b176d8997ea8cc8e4f64a3bced53`，仅验证已完成两轮396，不放行未完成的A/B2或formal gate。原生score函数AST与全量002一致，不预设两轮分数/文本相同；须与首轮既有156报告逐题绑定。评分命令待artifact006报告SHA冻结后归档执行，无新生成。

checkpoint006退出0，15波共428返回（B1两轮396+A首波32）原payload、Added日志、管理屏障、C32/尾6、两rank源码/graph资格独立通过，报告SHA `2bb6b55f57bea1d345c7d623985b84d86d9fc08d743dab703010604c62b0658b`。归档B1-pair离线评分命令 `/public-flash/jinghao/qwen3.6-35B/20261022-qwen36-35b-mx104-stack-regression/commands/ordered198-b1-pair-score-001.command.json`，SHA `f0a26a303e35e0b9bf043d17c34aee34621b9d4f86cf3c1b352edc3984037068`，只放行B1两轮原生终态0并独占新核验输出目录，不干预当前A臂。

B1-pair离线评分退出0，报告SHA `435466138814d13019d3c762254f760633f52f309faea2aa4b404ae11e4ff543`：两轮均156/198，逐题198篇全文完全一致、strict翻转0；792行原生filter样本均验证，旧正式160/147逐题重现。Base A臂正在运行，B2尚未开始；这只确立B1重复性，未确立A/B差异、原13题因果或正式精度恢复，不触发盲目数值回退。保留全部轮次并继续预声明矩阵。


### 2026-10-24 15:48 Base首轮例行检查

07:47:59Z唯一控制器身份仍匹配，phase A-r9/repeat0、无native result/error，租约年龄约1.85秒。Base首轮四波128完成，第五波32准入/22返回；累计556准入/546返回，尚无新完整分数或AB结论。执行前归档新的纯文件核验命令 `/public-flash/jinghao/qwen3.6-35B/20261022-qwen36-35b-mx104-stack-regression/commands/ordered198-artifact-checkpoint-007.command.json`，SHA `baf5f798fa409717431733c9a48ae99ea8be3ab4e6d20608742da23d36851010`，只读取完成波次并写新checkpoint007，不重放模型/admin请求。B1两轮156/198且全文相同的已核验结果不变。

checkpoint007原生退出0：18完成波524返回全部独立通过，报告SHA `b9b873acdcbbe4a0d0f50d3b1f5fc9b255e02f82f3f810a2dd59fed62a39f175`。07:48:54Z Base首轮第五波返回23、首轮151/198，累计547返回/556准入。没有新完整分数或AB结论，无需用户操作，静默继续既有作业；无模型/admin请求或服务配置变更。


### 2026-10-24 16:51 Base首轮完整结束

08:51:26Z唯一控制器精确身份匹配，phase已进入A-r9/repeat1；A/repeat0原生completed/exit0，198返回齐全，A第二轮首波32完成、第二波32准入/25返回。无controller错误，lease内容年龄约1秒。不预设Base首轮得分或与B1的差异。执行前归档纯文件checkpoint008命令SHA `fee20f0dad7c0cfa415f23befb07100766b84bfac7f8bea6c0811ebcc67d2c61`；另归档仅限已完成B1两轮+A首轮的离线原生scorer SHA `608804f697c4ecdcc387cde5c173126b8dc1b107874733b873a085e96ab1d8a1`，score函数AST与全量002完全一致，不放行未完成轮次、不签gate，评分命令须后续绑定artifact008 SHA再归档。

checkpoint008退出0，22完成波626返回独立通过，报告SHA `ff8a2587310c0408479b459a37d30435d770a046997f82574cd35637491b7078`。归档B1两轮+Base首轮的594回答离线原生评分命令 `/public-flash/jinghao/qwen3.6-35B/20261022-qwen36-35b-mx104-stack-regression/commands/ordered198-b1-a-first-score-001.command.json`，SHA `8ef6f68604cfe11faee60d84c2b7179da60c22bb92c4dd715c62fe8fe8b301f6`，仅在指定三份native终态完成/exit0且artifact绑定匹配时创建新目录执行；不发新请求，不根据分数选择轮次。

B1 pair+A first离线核验退出0，报告SHA `91551a4c8b98178f90e828d1c6d54fe09f15051a352098d0d3276b1edfd6203d`：三轮均156/198，198题三份全文全部相同、strict差异0，1188条原生filter行均核验、旧正式160/147再次逐题重现。该受控完整198范围尚未复现A/B差异，仍须A第二轮与B2重新启用完成后才给完整矩阵结论；未做数值回退或优化修改。原正式147<160不变，诊断结果不发gate。


### 2026-10-24 17:47 Base第二轮例行检查

09:47:00Z精确wrapper身份匹配，A-r9/repeat1正常生成，无native job result/error，lease年龄约0.33秒。Base第二轮前三波96完成，第四波32准入/31返回，第二轮127/198、累计722准入/721返回。已完成三轮156/198且全文相同的结论不变，没有新完整分数或稳定BAB结论。执行前归档纯文件核验命令009，SHA `888b63a1e6228ca83bb94ac5b4c94497368b1f2c7c265de5a71d2fe62873a962`，仅核验完成wave并写新产物，不生成/重放模型或admin请求。

checkpoint009原生退出0：24完成波690返回独立通过，报告SHA `74b4ac1ed1405efd425aed83212ea2549ab9efbc0cb0409617805733b5473d57`。09:48:16Z Base第二轮仍127/198、累计721原始返回/722准入，未新增完整分数/AB结论，无需用户操作；保持静默每小时跟进。未改continuation/controller/推理配置，未增加模型或admin请求。


### 2026-10-24 21:18 运行时核验已到第六轮

心跳携带时间为10:48Z，但此次实际远端只读时刻为13:18:30Z，采用运行时事实：精确wrapper仍匹配，当前B2 candidate-r29/repeat1，前五轮全部原生completed/exit0（包括Base第二轮与重新启用B首轮），第六轮两波64完成、第三波32准入/5返回，累计1086准入/1059返回。无native job result/error、lease年龄约1.22秒，尚未恢复原B-r30。不得按旧时间/旧phase重放任何作业。归档新纯文件checkpoint010命令SHA `e13ba11ac57a0750ecd6919497e61ac864d947bd399b5b179ee41885a6e2232b`；仅前五完成轮990回答的离线scorer SHA `4816079d61951fefb056fec5eee144ddcfe137cb0d2b37f4463aedbafd62e8e5`，score函数AST与全量002相同，不提前发最终六轮/恢复结论。评分命令后续绑定artifact010 SHA后再归档执行。

checkpoint010退出0，37完成波1054返回独立核验通过，报告SHA `dc983cb8bfcd8d154a7817f8e2cbde5e5d9cff647fad106bd40b357956235a40`；当前最后一轮第三波10返回，仅为观察计数。归档前五轮离线原生评分命令 `/public-flash/jinghao/qwen3.6-35B/20261022-qwen36-35b-mx104-stack-regression/commands/ordered198-first-five-score-001.command.json`，SHA `03f282af65ff54fc87c7246ef878c9c66a7b0a753d8cfc39fdb69f5dd227c914`，先检查指定五轮native completed/exit0和报告绑定后创建新目录执行；不发模型流量、不声称六轮已完整。

前五轮离线原生评分退出0，报告SHA `7a5950851bb163dc7cf1ca16601f55e2575502f844fdb84d6f209f7225801d37`：strict五轮均156/198，198题五份全文全部相同、strict翻转0；990回答/1980原生filter行均验证，旧正式160/147逐题重现。已覆盖Base两轮和重新启用B首轮，仍未复现A/B差异；等待第六轮及r30原参数恢复后给完整结论。单变量回退未触发，不改采样数值逻辑；正式gate仍失败，无性能晋级。


### 2026-10-24 21:27 例行检查与最终独立核验入口准备

13:26:34Z唯一controller精确身份仍匹配、native job无result，最后一轮B2/repeat1第三波22返回（第六轮86/198），累计1086准入/1076返回，lease内容年龄约1.30秒。前五轮156/198且198题全文一致的已通知结果不变，无需再次通知。

为完成后及时收尾，归档默认inactive的最终独立协调核验器 `/public-flash/jinghao/qwen3.6-35B/20261022-qwen36-35b-mx104-stack-regression/commands/verify-ordered198-final-001.py`（SHA `8780669d3f12401b0655b0cb536a03028ee3a8493b894d91b09bc1e88eb3d4bc`）和准备清单 `/public-flash/jinghao/qwen3.6-35B/20261022-qwen36-35b-mx104-stack-regression/commands/ordered198-final-verification-001-prepared-plan.json`（SHA `5fd4daab65e38da360ed8ed70f800b987578ae339e55624b2821ab5bd6ed75ce`）。仅AST语法/前件审阅，尚未执行：必须全部六轮和controller原生exit0、summary completed、current_job null、r30原启动恢复/graph两replay+C8/稳定manifest通过后，才能执行完整42波1188、2376 native样本、旧160/147重现、fresh RPC与精确PID/argv/nohooks/unpaused、恢复B全部源码字节核验和逐题六轮比较。无模型请求/服务重启/数值逻辑修改/正式gate；观察错误保留并用新文件修复，禁止重跑模型。当前不执行这个终态入口、不改活动continuation。


### 2026-10-24 22:21 最后一轮例行检查

14:21:43Z精确wrapper身份匹配，第六轮B2-r29/repeat1仍在生成：前四波128完成、第五波32准入/31返回，第六轮159/198，累计1150准入/1149返回。无native job result/error，lease年龄约0.55秒；未恢复r30，不运行终态核验器。前五轮全文一致/156的已通知结论未变。执行前归档纯文件checkpoint011命令SHA `8d2cc757ff1688222bbdf20e12b7a01d00e1f9bb971071045dd6de90250f6108`，只核验已完成波次，不发模型/admin请求。

checkpoint011原生退出0：39完成波1118返回独立通过，报告SHA `9c80e5ef534e084edcc525a2d0c25aef5ac2bed5d639d4b2949240edff139b6b`；14:22:59Z第六轮仍159/198、全矩阵1150准入/1149返回，无终态或原r30恢复。无需用户操作，保持静默跟进；前五轮完整156且全文一致的已通知结果不变。


### 2026-10-24 23:27 完整1188原生作业终态与最终独立核验

15:27:01Z只读确认唯一job原生exit0，六轮各198/所有42波均结束，summary completed/error null/restore_error null；wrapper已退出属于预期。Controller已自动恢复原无日志B candidate-r30，restore passed，continuation current_job=null/phase completed，SHA `643e21e88ea149882b762a6e45510d89e6536a3fbfe2ca48effce3f26a66b46d`；新manifest `42b31a0cfa987c5be990c22054e42709c4f74f61808a479f5cb426b3e4f180de`。先不把原生终态当独立通过。归档准备好的终态协调核验命令 `/public-flash/jinghao/qwen3.6-35B/20261022-qwen36-35b-mx104-stack-regression/commands/ordered198-final-verification-001.command.json`，SHA `85c64e1f1bb5b039a1ae8d017e4f43952d9642360deb70d6ca9d28fa6631acc7`，按已审阅全部前件执行；不新增模型请求、不重启、不改vLLM/优化或gate。完整独立结论待执行。

最终独立核验原生退出0，报告SHA `24f8f077ae4d88e920139278a3b7a016e2af4eb2e333d6b34fdfcd02e7a337f6`：全部1188回答/2376原生filter行、42波原payload/Added/FIFO/rank来源通过；strict六轮均156/198、198题六份全文全部相同、stableAB0/unstable0。原r30无日志/profiler/hooks且unpaused恢复、精确PID/argv、graph两replay+C8和r27/r21全部稳定manifest字段相同；fresh5755源码及运行引用文件字节检查0差异，两rank FGV仍未加载。1158stop/30length均原样进入strict；旧正式160/147逐题重现。原13题机制未确认，未做盲数值回退、未签gate/放行性能。

授权有序1188诊断与恢复均已完成，没有可继续的后台作业；结束本轮临时监控，后续新的模型诊断范围另行决定。终态checkpoint脚本执行前归档 `/public-flash/jinghao/qwen3.6-35B/20261022-qwen36-35b-mx104-stack-regression/commands/checkpoint-ordered198-verified-001.py`，SHA `e7614bc183e9c477e17df8dba0cb21628379f05a6d5867da6f03955614d70762`，仅在controller终态和continuation旧SHA完全匹配时CAS写入已核验结论，不动服务/模型/优化代码。


### 完整有序诊断结论与当前边界（regression-planning-001复盘）

| 臂 | 两轮原生strict | 各题全文 |
|---|---|---|
| 当前B1-r28 | 156/198、156/198 | 198题相同 |
| 原Base A-r9 | 156/198、156/198 | 与B1逐字相同 |
| 重新启用B2-r29 | 156/198、156/198 | 与A/B1逐字相同 |

完整1188诊断回答、2376原生filter行、42波、原payload/日志屏障/两rank/source/graph及恢复独立核验通过。稳定A/B差异0、不稳定题0；因此本轮结论是“相同有序条件下未复现稳定迁移差异”，条件性的单变量数值回退没有触发。没有修改模型、vLLM或优化数值逻辑。原始13题差距的机制仍未确认，不能把执行上下文敏感性直接当作全部因果，也不能把六轮156低于160的诊断分数签成正式gate。

原正式A160/B147证据保持，candidate gate失败，完整性能验收仍未完成；原baseline性能11轮incomplete原样保留。Prefill/Decode/Mixed没有新增无profiler性能数据，不计算累计收益。FGV仅安装/源码字节一致，两rank实际仍未加载；历史两个profile窗口的shortlist/GDN/graph命中不外推为1188的FGV内核覆盖。

源qwen3.6-35B-verify及GPU2/3/4/5其他任务保留。本轮B-r30恢复原无日志配置，fresh5755源码/运行引用文件0差异，无profiler/hooks且unpaused，原graph两replay/rank+C8通过。qwen35b临时监控已通过app工具删除；没有后台模型job或默认追加流量。回归整体仍incomplete，只有本轮授权有序诊断结束。

### 后续可审阅方向：原始滚动并发重复性取证（提案，未授权/未启动）

优先验证原始rolling32下的重复性，而非盲回退数值实现。若用户决定扩大取证范围，可另行预声明B→A→重新启用B，每臂两次完整198，共新增1188诊断请求，四服务C8另32资格；全部六次按固定顺序保留，不因分数或文本选择重跑/删题。原native runner/task/backend（openai-chat-completions）、lm-eval seeds42、HTTPseed1234/temp1/p.95/k20/65536预算/stops与strict保持；响应cache各次全新。继续已有临时日志授权，结束恢复原无日志launch；不使用有序pause/utility准入、不启用新profiler、不改registry/源码/模型/门槛。只读Added日志观察不能冒充精确device batch证明。

这会新增超出已完成1188的模型请求，当前仅为范围提案，不执行。实施前仍须归档独立controller/配置/命令、真实原生入口及失败/取消/恢复审阅；现有有序controller绝不重放。身份或原生证据/恢复失败停止后续并保留partial；输出length等健康观察仍按原strict计分。若原始协议也没有稳定source AB区别，则报告波动边界，不编造代码根因；若稳定区别复现，再按已授权条件做单变量回退/重新启用和机制证明。任何将有序协议升级正式验收或gate绑定规则变化均需另行明确契约，原冻结工具保持。最终正式性能仍须等原正式契约完整198>=160的新gate。


### 2026-10-25 用户指定单轮正式 C64 精度评测

用户先要求当前环境单轮正式198题C32，随后明确改为C64；尚未启动C32生成。执行formal-gate模式，原native formal_accuracy→llmrun→openai-chat-completions滚动并发；保持原task/strict/采样/原无日志r30及160/198绝对门槛。新独立C64契约显式声明并发32→64；不作为与旧C32同配置的迁移收益比较。不追加有序/六轮诊断，不择高分重跑。

执行前归档独立commands：
- `formal64-fresh-manifest-001.py` SHA `7779b64a6078b12bfc731cf748eb8ea580a3a58a7a5c7ac15ae775b0ed340425`。
- `prepare-formal64-r30-001.py` SHA `9b7884bc78e9a40b4d8081fcb69ab4f1527c756388c4362aa41c0a26363d1ffd`。

准备已通过，ready SHA `176a44362984d070df04ffc5d20d61e9325f7e36b93182fc4b173e01cd03df68`。新鲜源清单与精确r30进程/两rank核验通过，原graph两replay+C8属于同一未重启实例；两份原生provenance相等、与旧契约仅并发metadata不同。保持冻结formal/acceptance/llmrun不覆盖。新C64契约明确从原paired配置字段移除并发并声明用户授权差异，保留绝对160/198，未伪称旧C32配对配置相等。已建立每小时安静监控`qwen35b-c64`。
- 执行前归档 `run-formal64-r30-001.py` SHA `f86fab7ed873ea01a739a9891716535b15328e222be66ceb668ca43f001465fe`。
- 执行前归档 `start-formal64-r30-001.py` SHA `322f112dfd77ea8fb863a8738ccea43e2735e1fd98666e9443380d2b773655b1`。

启动001在background runner解析argv长度guard处退出1（未mkdir job、未进入controller/formal）。0模型请求；保留原启动错误。独立修正starter002仅给Python添加-u，argv由3项变4项满足原guard，原controller/正式配置完全不变。新脚本SHA `db7897e02e43910caeb8e484721787a32a80eba23c1721cb23374c2503aeb76e`，禁止重放001。

唯一作业已启动：`accuracy-formal-c64-r30-20261025-001`，PID814313/start_ticks1120464751，native launch SHA `ef572149a51414fb535415fb8e3a4f956d68042f6ad05af6b51b28bbbd1b2f66`，command SHA `d67cf1e348e17609749d8cc49262ac5d4edc1dc7b3661fdaec4f494a893171d6`。continuation launch SHA `92ff5f9cac7695817f41d77cc621e7c3451233c33c9b621aa306c1ce0da935e2`。不重放启动器001/002或controller；仅观察此作业，终态再消费原生结果。

原native已进入请求阶段：effective run_id `dcc01cae1d594dcb8836b5b5ce8cff17`，num_concurrent64、缓存命中0/待生成198。归档只读启动核验器 `observe-formal64-start-001.py` SHA `994cff0bc5d0ca892de423f7eb7d6bf76d58ab14387a1258720a5103c6837a9f`，核验精确wrapper与eval原生CLI身份/信号量C64，记录观测metrics；不将服务running数量当作直接device shape。

启动独立核验通过，report SHA `316aee0bc47b58575edef3d8e030a25f3adfef28bd1aeb6ae5bcbaec258a198e`：eval原生PID12331/start_ticks1120465505，CLI openai-chat-completions/num_concurrent64、native信号量64，响应cache复用0题。服务实测running64/waiting0（观测快照，不作为device shape证明）。尚无正式分数；唯一作业继续，监控qwen35b-c64已绑定实际PID与SHA并保留状态不变静默。


### 2026-10-25 C64正式单轮原生完成，独立核验前

controller/native job exit0，summary passed_pending_independent_review、error null，发布strict161/198，原160/198门槛未改；不是最终独立核验结论。准备0新模型请求的独立native strict逐题重算/396filter一致性、旧160/147重现、fresh当前r30身份/RPC/5755源码字节与原gate check。旧progress helper最终matched0是非gate阶段观察，不取代最终native161。保留完整日志。
- 执行前唯一归档 `score-formal64-native-independent-001.py` SHA `a6982a687020dbf8ca404be8ab279f9621ee7c2be4de6947166b1d70575922ee`。
- 执行前唯一归档 `verify-formal64-final-independent-001.py` SHA `437b08a7b55a0e72b2dc6f6fee01b492d315a8ce44e220ed727c9c2ca1aa6c59`。

Independent final verification passed: native strict161/198 >= unchanged160/198, all198 docs/396 filter rows, old160/147 independently reproduced. Verification SHA c57b1b2cc6a0b2058bb9f4f64ccee78fd93239eea1ac42454b8ce3cd8700ff0a; gate SHA c81410e38c95dda62f1ffa0e730dedee0745b4cc397579b6307bae4b8a6181c3. Fresh r30 unchanged,5755 source/reference files match, no hooks/profiler/prefixcache,unpaused. One native initialization/cache reuse0; timeout0/empty0; completion65536 docs90,120 retained in strict. No original wire finish_reason captured. Old C32 failure and original13 cause remain unresolved; no numerical rollback/source edits or performance launch. Monitor qwen35b-c64 deleted via app. Before CAS checkpoint, archive checkpoint-formal64-verified-001.py SHA b833f66b9626e6444eae91ac613e735313cdace1a419096d0f7c7449b7d30210. Initial local UTF8 upload generator failed before any remote write; confirmed old continuation unchanged, ASCII transfer only repairs record transport.


### 2026-10-25 单轮正式C64最终结论

当前r30完整198题strict **161/198 = 81.313131%**，达到未改动的160/198阈值；新原生gate已签发并独立check通过。独立verification SHA `c57b1b2cc6a0b2058bb9f4f64ccee78fd93239eea1ac42454b8ce3cd8700ff0a`，gate SHA `c81410e38c95dda62f1ffa0e730dedee0745b4cc397579b6307bae4b8a6181c3`。完整198唯一doc/396filter行的原prompt/target/生成参数、strict原函数逐题重算、前后manifest及fresh两rank/nohooks/unpaused、5755源码引用字节均核验通过。模型/源码/服务启动参数未改变；没有重新跑题或挑最好分数。

该结论绑定用户指定的滚动C64新契约与当前r30，旧C32 160/147仍有效，原13题机制未确定，不能解释为C32同配置迁移恢复。当前精度gate已满足，性能基线/稳态与最终四场景验收仍incomplete；没有自动启动性能。timeout0、empty0，doc90/120达到65536预算，原样纳入strict，未捕获原wire finish_reason，未把预算等同原生finish字段。

终态continuation SHA `bdb5041bae0c69380358089d22af0ea7a66662a67ed6b78b524dc830685c6506`，phase accuracy_formal_c64_verified_passed/current_job null；qwen35b-c64每小时监控已由app工具删除，单轮授权任务完成。


### 2026-10-26 PR638只读对照

PR head `3e04e696f5ab93d25ef90b1f0e1d0fb50cd9ab60`，base与容器HEAD均为`7cb559947cb61fd8b69fa5027d8ec113e528a644`，仅修改MetaX `impl/attention/flash_attn.py`。容器文件SHA `37062afce9b70f24ec64664a6b0995a3e82c8afd41b410fbb4ecb09e3d768a71`；PR文件SHA `f49f4a5b401a5ca66f04f10b27e7b6f186e3efe1c8d214556efb0b1edaf36514`，非逐字一致。gather/reshape/trim及共同attention参数AST相同；容器要求环境flag（当前API实测=1），PR去掉flag并新增DECODER限制，且将dense/paged双调用合为单调用。只对当前decoder+flag1范围可说静态核心路径对应，跨attention类型/flag0行为不等同。PR未包含FLA/GDN chunk_delta_h改动；现有161/198属于容器代码，不能直接归为PR head硬件通过。未改源码/重启/生成。比对证据`/public-flash/jinghao/qwen3.6-35B/20261022-qwen36-35b-mx104-stack-regression/commands/pr638-versus-current-B-20261026-001.json` SHA `6e09713ee0589a0d3838b2b9d6eb3558123cb9e8b4798613e59baf79ad603be5`。


### 2026-10-26 FLA术语澄清

用户追问上一答“没有覆盖FLA/Gated DeltaNet chunk_delta_h修改”。fresh只读B容器确认：`vllm_fl/dispatch/backends/vendor/metax/patches/chunk_delta_h.py` SHA `6ba59032211ff3370c2e63d07d401717f71959d62b065e1213ab8168625f611f`，相对当前Plugin HEAD7cb559947无本地diff。该文件是release/0.2已有MetaX适配，patches/__init__.py导入并在运行时替换vLLM同名H kernel；未修改vLLM落盘源码。对照当前vLLM原实现，kernel计算体AST完全相同，autotune原num_stages[2,3,4]改为[1]，num_warps[2,4]及BV[32,64]保持，候选12→4，源码说明用于避免MetaX共享内存限制。因此不能把此已有vendor补丁说成这轮新增的本地优化；PR638基于相同release/0.2已继承它，只是PR差分未改这个文件。它与PR638的FlashAttention连续KV Prefill优化不同，也不能混为FlagGems-vllm独立gdn_chunk调参。全程无源码修改/模型流量。


### 2026-10-26 当前Plugin相对最新上游完整只读清单

GitHub核验release/0.2最新仍为`7cb559947cb61fd8b69fa5027d8ec113e528a644`，与容器HEAD一致；最新main为`aae3c1c3c2e993f5ff0ffea03af3553da9df9cd3`，两分支已分叉（main独有67提交/release独有43提交）。对当前B容器所有512个HEAD blob逐个计算真实文件Git blob SHA，7处差异与git diff精确一致，无assume-unchanged/skip-worktree；4个新增文件。忽略源码仅构建生成_version.py，不当作手写推理优化。

| 文件 | 内容 |
|---|---|
| `impl/attention/flash_attn.py` | 单prefill且KV>=2048/非量化时按block table收集连续KV，保持分页fallback；带env开关，和PR638不是逐字相同 |
| `envs.py` | 注册连续KV开关，默认0，当前服务实测1 |
| `patches/topk_topp_sampler.py` | 受模型/shape/dtype守护的Qwen MoE shortlist和VL counting选择，复用上游RNG/logprobs；显式幂等apply_patch并刷新已导入别名 |
| 新`impl/qwen36_moe_shortlist.py` | top64 FP32候选、阈值/tie安全检查、融合准备/散射，不满足安全条件回原生filter |
| 新`impl/qwen3_vl_counting.py` | BF16网格近似counting筛选，保留幸存FP32值；仅Qwen3-VL专用shape，本Qwen3.6 MoE不启用 |
| `patches/__init__.py`+`worker/model_runner.py` | 将采样/GDN补丁从vendor包早期导入移到vLLM导入完成后、Sampler构造前，修复循环导入/旧类别别名 |
| `ops/fused_moe/fused_moe.py` | GEMM2独立调参覆盖，复制config，每chunk选择，并要求两次GEMM的BLOCK_SIZE_M相同 |
| `ops/fused_moe/fused_moe_utils.py` | staged MoE同样支持GEMM2覆盖；SILU改CachedOp(silu_and_mul)，其他activation保留原路 |
| 新`configs/moe/metax/E=256,N=256,device_name=metax.json` | 20个token数档位，部分GEMM2 SWAP_AB与大M pipeline/tile配置 |
| 新`tests/integration/test_metax_sampler_lifecycle.py` | 6种导入排列、重复注册/patch及reload的采样器别名生命周期测试；此次仅审计未重跑 |

FLA chunk_delta_h的num_stages=1是当前release已有内容，不列为本地新增。最新main完整769树条目未截断；对当前实际516个tracked+untracked文件直接比较，205个同名文件内容不同、74个容器独有、190个main独有，含分支适配/重命名/文档与测试差异，不能把469个路径全部说成我们本地修改。完整路径/补丁/文件SHA归档`/public-flash/jinghao/qwen3.6-35B/20261022-qwen36-35b-mx104-stack-regression/commands/plugin-current-latest-20261026-001-audit.json` SHA`61b06f3954416280918b96e572a9a4b7203748cc726cf7744923016d29b0a9e1`。全程无源码修改/模型流量/服务重启，当前C64 gate不变。

2026-10-26用户明确授权PR638+C64：按[pr638-001](pr638-001.md)应用唯一PR文件，新r31最小回归通过，现原native滚动C64/full198已开始、cache0/198、观察running64/waiting0。旧r30 C64161及原C32 160/147保留；旧gate不能用于新源码，当前新精度结果待核验。首controller的旧观察白名单错误保留，接续仅现有r31，无重复应用/重启/已发请求。

PR638单轮正式C64已独立完成且失败154/198<160/198，无当前gate。原C32160/147和前轮C64161均重算有效；一次22损失/15收益不确立PR因果，PR服务r31保留、无盲改/重跑、监控已删除。详见[pr638-001](pr638-001.md)，新issue accuracy-pr638-001，原少13题根因仍未定。

2026-10-26（北京时间）：用户明确指出NV原生GPQA参考77.53%，接受本轮154/198=77.7777778%，要求PR正式提交。按新PR验收依据高于参考0.2477778个百分点，PR638已由draft改为Ready for review；GitHub复读open/draft=false/merged=false，head仍3e04e696f5ab93d25ef90b1f0e1d0fb50cd9ab60。原冻结160/198拒绝及154原始结果完整保留，未改分数/旧contract/原生gate，也未重跑模型或自动性能。此为用户更新的PR接受依据，不是数值修复/稳定AB根因证明。PR正文只去掉原草稿说明；追加内部评测详情被自动审批拒绝（未明确授权向公开GitHub披露），因此内部结果仅本地保留。

2026-10-26当前候选状态更新：用户新要求的PR638+FGV MoE组合r39单轮原生滚动C64/full198独立strict160/198（80.81%），新gate验证通过（预声明NV77.53参考，亦满足旧160绝对门槛）；源与当前身份完整核验，监控已删除。原C32160/147及原13题机制未被重写或解释，没有新的配对C32复现结论或性能收益。详情见当前fgv-moe-001.md，不重复任何有序/正式评测。


## 当前组合 sampler-shortlist-C64 正式回归补充

保留本实验原有结果与范围。当前组合（FGV guarded shortlist49e9、既有MoE/GDN调优、FlagTree fe1d24f6、Gems a456）在新独立回答缓存的一次原生rolling C64/fullGPQA198中得分158/198=79.7979798%，通过流量前冻结的用户NV77.53%阈值；198唯一doc/396filter行、旧160/147/161/154离线复算、当前同c2/source/manifest已独立通过。新gate SHA13b72e7e2035e0fd28e44f2c1c809e7532c109759978a7a6f83e1e85fc450deb，独立report SHAab644f95c7160ad791e74d844b67aa6cad23aefbd7aef6d6360ef5eb337dc46d；远端operator/sampler-shortlist-001/formal-c64-002/independent-verification-001。该分数证明当前组合，不声称本实验孤立精度收益，也不改历史C32/旧160绝对参考；完整四场景正式性能未运行。完整记录见[sampler-shortlist-001.md](sampler-shortlist-001.md)。


## 2026-10-28 当前 opt3 组合精度复测

用户重启后的当前组合、实际prefix-on/GPU4/5/TP2，原生GPQA198/滚动C64独立通过**161/198=81.3131% >= 77.53%**。198唯一doc/396filter行/原prompt-target-args/无旧回答缓存/前后fresh源码一致，旧160/147/161/154逐题重现。验证：`/public-flash/jinghao/qwen3.6-35B/20261022-qwen36-35b-mx104-stack-regression/accuracy/user-gpqa-erqa-c64-20261028-001/gpqa-followup-001/independent-verification-001/verification.json` SHA c9437b838bd089152dc01a11c3f32076e89941334e545a89b8f175606366ebb9。此为保留组合精度，不证明本点独立贡献，不与旧prefix-off不同配置计算收益。随后官方ERQA多模态C64发生FGV MoE临时cache13申请256MiB OOM，服务退出；GPQA已测通过分数仍有效，旧实例gate不可直接用于新实例/新参数。ERQA部分证据保留、完整400分数缺失，不自动恢复/补跑/性能。详见[user-gpqa-erqa-c64-20261028-001.md](user-gpqa-erqa-c64-20261028-001.md)。
