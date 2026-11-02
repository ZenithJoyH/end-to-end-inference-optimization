# DeepSeek V4 Flash W8A8：mx-103精度与端到端优化

<!-- fw005-current -->
2026-10-26 当前保留：[fw-005](../../../models/DeepSeek-V4-Flash-W8A8/metax/20261022-thinking-gpqa-metax103/optimize/fw-005.md) 以一个现有Plugin文件的原生TP P2P compute-stream生命周期修复headpack跨层临时缓冲压力。保持原 **0.85/KV567220/prefixOFF**、所有数学/kernel和用户启动脚本；不增加env/启动参数。八卡43层探针pending2752→0MiB、精确数值通过（仅此传输微测）。

新完整thinking GPQA **172/198=86.87%**通过80%阈值，新schema3 gate已绑定当前source与实例。原用户run_once/no-profiler，D1024/C64/N128，P1K3/P4K3/P16预热+3/P32预热+3，**14轮1792/1792成功，零OOM/非法访存/新增KV抢占**：

|输入|测量轮|输出吞吐(tok/s)|mean TTFT(s)|mean TPOT(ms)|
|---|---:|---:|---:|---:|
|16K|1|357.4344|36.4288|141.4292|
|16K|2|356.9035|36.4478|141.6487|
|16K|3|357.7659|36.3298|141.3659|
|32K|1|207.9711|72.5251|232.4410|
|32K|2|208.2478|72.4975|232.0488|
|32K|3|208.1731|72.2650|232.4472|


P16吞吐/TPOT spread0.241%/0.200%；P32为0.133%/0.171%。fw005验收时服务健康空闲。后续[僵尸维护](zombie-cleanup-20261026.md)清理254→0，容器未重启；维护开始前18001已未监听，当前模型未运行，start-model.sh未变。属于同预算checkpoint稳定性，未补当前独立B/C/R或最终四场景正式验收；旧原镜像208.91仍仅未准入预热参考，不作加速比。新summary SHA `3bd44085286ff264b51d62b828c75b33f1ad1dc7deb3c29e14da3f18d803f54b`，完整路径/回退/未测项见fw005；下方op006等分数与测量是对应历史源码证据。
<!-- /fw005-current -->

<!-- op006-current -->
[op-006](../../../models/DeepSeek-V4-Flash-W8A8/metax/20261022-thinking-gpqa-metax103/optimize/op-006.md) 已复现并修复请求期 BF16 NT 选参：仅增加1个FG生产文件改动，Default log-M分桶并在请求前准备完整已验证形状范围，保留实际M/EVEN掩码与精确BenchmarkCache。新thinking GPQA **169/198=85.35%**通过80%阈值（op005为170/198，少1题）。

同一新实例、原始用户run_once、无profiler、prefix cache关闭，W3后保留全部三轮P32768/D1024/C64/N128：

| 轮次 | 输出吞吐(tok/s) | mean TTFT(s) | mean TPOT(ms) | 新编译（总/NT） |
|---|---:|---:|---:|---:|
| 1 | 203.3665 | 75.0368 | 237.2020 | 0/0 |
| 2 | 203.5084 | 74.9309 | 237.0885 | 0/0 |
| 3 | 201.2218 | 75.5128 | 239.9502 | 2/0 |

384/384成功，0 OOM/非法访存/抢占。吞吐spread **1.1244%**、TPOTspread **1.2064%**，均通过冻结5%阈值；三轮NT ConfigCache与BenchmarkCache均未变化。第三轮仍有index/mHC两项非NT编译，**不宣称全链路零JIT或旧31秒下降全部归因已闭合**。

中位吞吐203.3665tok/s；原镜像208.91仍仅预热参考，尚无正式稳定对照或新独立B/C/R；本组合四场景最终验收未完成。op006记录时服务健康空闲、prefixOFF；当前服务状态见上方fw005记录。
<!-- /op006-current -->


## op005 阶段结果（历史）

[op-005](../../../models/DeepSeek-V4-Flash-W8A8/metax/20261022-thinking-gpqa-metax103/optimize/op-005.md) 已修复量化/padding等原7项的token边界特化与launch key，共6个FG/FGV生产文件。新完整thinking GPQA **170/198＝85.86%**通过80%阈值。同一服务、无profiler、prefix cache关闭，使用用户原始run_once完成三轮P32768/D1024/C64/N128。

| 轮次 | 输出吞吐(tok/s) | mean TTFT(s) | mean TPOT(ms) | 新增编译（总/原7项） |
|---|---:|---:|---:|---:|
| 1 | 201.3868 | 75.0588 | 240.1629 | 3/0 |
| 2 | 203.7935 | 74.4507 | 237.1143 | 0/0 |
| 3 | 194.3892 | 77.8273 | 249.0065 | 3/0 |

384/384成功，无OOM、非法访存或抢占。吞吐spread **4.6697%**、TPOTspread **4.9518%**勉强满足冻结5%阈值；**第三轮下降仍在，不能宣称根因完全解决或全链路零JIT**。第一轮另3项来自BF16 NT GEMM/index/mHC heads，第三轮3项均为NT GEMM；原目标7项均未复发。全部轮次保留，没有挑选或重跑替换慢轮。

中位吞吐201.3868tok/s为本组合P32 targeted观察。原镜像208.91仍仅预热参考，没有正式稳定对照或新独立B/C/R；本组合四场景最终验收未完成。下一步首查NT实际输入布局、选参和请求期benchmark/cache miss，不能盲目去掉有效EVEN/tile条件。

## 以下为阶段历史记录

迁移和完整198题评测均已完成。2026-10-22用户明确认可去加粗提取的170/198＝85.86%，历史精度验收为通过，原strict分数及原始证据保留。后续已保留 MCCL 预热、gather 地址和 prefill top-k 布局修复。当前32K三轮输出吞吐111.63/110.48/110.51 token/s，spread1.04%，无非法访存或OOM；原始镜像六轮完整预热均成功，但三组均未过5%稳态准入，对照为incomplete，不能认定性能一致。prefix cache持续关闭，未做新完整GPQA或最终四场景组合验收。

用户报告 NV GPQA 约86分、开启thinking，暂时没有原始结果/配置。103的原生服务已开启thinking，并有真实tokenize前缀及同实例单题False→True→False错→对→错的证据。旧59默认关闭thinking，不能直接与NV比较。单题证据不外推全量收益，完整前后结果还包含Host迁移。

| 同一批198题输出的计分 | 正确数 | 分数 | 结论边界 |
|---|---:|---:|---|
| 原冻结strict正式指标 | 153 | 77.27% | 低于80%，没有gate |
| 仅移除Markdown加粗后离线提取 | 170 | 85.86% | 17项恢复正确均来自完整最终答案；用户明确采纳该口径并确认精度通过 |
| 新版官方regex离线提取 | 161 | 81.31% | 仍有EOF问题，漏掉9项原本正确 |
| 新版regex离线追加结尾换行 | 170 | 85.86% | 用于证明EOF机制；未改真实输出或任务 |

188题stop，10题length到达30000 token，均未结束thinking。完整作答中去加粗后169正确、19错；10题截断中1题因中间推理出现正确选项而被计中。因此85.86%接近用户NV参考，但不能说198题均有完整最终答案，更不能证明所有跨平台条件一致。基础samples健康检查未识别length，API日志与全部198个原始回答内容哈希精确对应，以API事实为准。

镜像、挂载与源码门禁通过：目标精确使用不可变快照 `sha256:80d8351984a4e03799af003cd70d80300b62f92206be9ad48e3683717f965c30`；`/public-flash`、`/data`、`/var/lib/dsv4`映射逐项一致，volume146项单独复制校验。Plugin330、FlagGems3686、FGV403、vLLM2449个文件与源一致；实际私有安装保持`/opt`。模型62分片306,197,836,792字节及tokenizer全量SHA通过。7次FULL capture、C1/C8共16次replay、10请求最小回归通过。运行后实例、参数、源码、权重配置/index、tokenizer及health再次通过。

评测镜像同名标签发生8处源码漂移，已在本任务独立CPU评测容器恢复原59冻结版本，备份新版，未放宽正式strict或80%阈值。首次误引用准备contract被生成前校验拒绝，零请求；失败证据保留，修正引用后独立完整运行。没有证据支持继续修改attention/indexer/MoE；既有限幅修复与权重参考实现一致。缺少配对NV张量，不能宣称所有数值路径均被排除。

用户指定远程根 `/public-flash/jinghao/deepseekV4`，案例子目录 `20261022-thinking-gpqa-metax103` 权限0700。所有原始请求、响应、配置、脚本和结果已归档到该案例；112个文件/链接逐项校验相同，tree SHA `4add3c52561e93e5afb9c9ab9c4fe7f102b4a0e14431e07b7a6b51bdc2187fb6`。具体身份、SHA及诊断明细见[模型案例](../../../models/DeepSeek-V4-Flash-W8A8/metax/20261022-thinking-gpqa-metax103/optimize/README.md)和[acc-001](../../../models/DeepSeek-V4-Flash-W8A8/metax/20261022-thinking-gpqa-metax103/optimize/acc-001.md)。不保存本地完整数据或镜像，未提交、推送或创建PR。

后续性能修复前的审计快照覆盖Plugin23、FG5、FGV11个生产文件，FlagTree无本地补丁。已核对实际config与8worker一致的35项dispatch绑定；性能机制、原生复用、必要正确性修复、未启用路径和全部文件映射见[audit-001](../../../models/DeepSeek-V4-Flash-W8A8/metax/20261022-thinking-gpqa-metax103/optimize/audit-001.md)。没有同workload性能消融数据；不将历史注释数字用于本机收益结论。

<!-- perf-001:final:start -->

## perf-001 当前代码诊断性性能基线

perf-001历史快照时间：2026-10-23 00:23:00（Asia/Shanghai）。该阶段诊断性基线：P1K 642.29 token/s、P4K 437.87 token/s；P16K首次预热MCCL OOM，P32K未执行，四场景整体incomplete。

| 场景（D1024/C64/N128） | 状态 | 输出吞吐(token/s) | 总token吞吐(token/s) | mean TTFT(ms) | mean TPOT(ms) | mean ITL(ms) | mean E2EL(ms) | 批次耗时(s) |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| P1K | completed | 642.29 | 1,284.58 | 6,682.63 | 92.98 | 92.98 | 101,747.69 | 204.07 |
| P4K | completed | 437.87 | 2,189.36 | 19,049.12 | 126.37 | 126.37 | 148,586.35 | 299.34 |
| P16K | failed_oom_incomplete | — | — | — | — | — | — | — |
| P32K | not_run_incomplete | — | — | — | — | — | — | — |

使用用户指定vllm_perf.py的原run_once，源文件未改；COMMON_ARGS按冻结契约设置。D1024/C64/N128、finite batch、temperature0、ignore_eos、固定输入输出长度，prefix cache关闭。P1K/P4K恢复补测各固定4轮完整预热，末3轮输出吞吐spread≤5%后采集3个全新measured轮；全部保留，逐指标取三轮中位数，测量spread≤10%才称稳定。不重标旧warmup、不混合两实例、不丢弃较慢测量轮。

初始实例P1K/P4K的3轮完整预热因首轮过渡未达≤5%准入，均零measured轮，所有旧轮次保留。P16K warmup1先出现MCCL内部44MiB/512MiB分配失败，随后indexer query-sharding all_gather报DistBackendError；日志不证明精确触发shape或allocator根因。按停止规则终止精确客户端；旧模型进程随后自行退出。同容器恢复同配置服务后仅补测P1K/P4K。P32K因前序服务故障未执行，不能宣称已证明unsupported。

历史170/198＝85.86%由用户确认精度通过，仍属于原attempt01与同一批198份输出；原strict153/198＝77.27%及其证据完整保留。恢复实例仅有新10/10最小回归和graph验证，没有新的完整GPQA分数或正式精度gate。

这是已保留组合代码的scenario-entry诊断性当前基线。没有未优化anchor、candidate/revert A/B或单优化消融，没有设定性能SLO/通过阈值，不声称加速倍数或完整正式性能验收通过。生产源码、权重、tokenizer均未新增修改。

逐轮值、范围、证据SHA见[baseline](../../../models/DeepSeek-V4-Flash-W8A8/metax/20261022-thinking-gpqa-metax103/baseline/README.md)；故障与恢复过程见[perf-001](../../../models/DeepSeek-V4-Flash-W8A8/metax/20261022-thinking-gpqa-metax103/optimize/perf-001.md)。

远端根 `/public-flash/jinghao/deepseekV4/20261022-thinking-gpqa-metax103/performance-001`；最终summary SHA `94a776834acea80de320369c18e1bdd46edba8715e785447053cc1a689a9953a`。恢复plan/contract/preflight及每轮原生JSON、stdout日志的绝对路径和SHA保存在state.yml；原始输出、完整日志和脚本保留远端，不复制到模型目录。

<!-- perf-001:final:end -->

<!-- long-context-repair:start -->

## fw001/op001 阶段历史结果

| 输入 | 源码 | 输出吞吐(token/s) | mean TTFT(s) | mean TPOT(ms) | mean E2EL(s) | 整批耗时(s) |
|---|---|---:|---:|---:|---:|---:|
| p16384 | fw001_only_baseline | 191.64 | 70.752 | 260.926 | 337.508 | 683.963 |
| p32768 | fw001_op001_baseline | 109.52 | 140.343 | 439.042 | 589.336 | 1196.822 |

D1024/C64/N128、finite-batch、固定random长度、temperature0、ignore_eos；使用用户指定vllm_perf.py原run_once，prefix cache关闭。P16固定4预热+3测量；P32原4轮预热未稳态（零测量）全部保留，冻结恢复契约后再运行全新3轮预热（全部3轮spread≤5%）+3轮测量（要求spread≤10%，实际12.913%，未通过）。全部测量逐指标取描述性中位数，不丢第三轮；32K稳态性能结论为incomplete。TTFT/TPOT/ITL是含排队与调度的客户端代理。16K属于fw001-only，32K属于fw001+op001；没有同源码四目标正式验收或A/B加速结论。

MCCL子组初始化已前移到显存profile，P16七轮通过；P32暴露的FlagGems scale地址32位溢出及独立搜索边界问题以3行修复，算子参考/graph、13仓库测试、10模型请求与P32新恢复六轮请求完整性均通过，三轮测量吞吐稳定性未通过。完整证据与回退见[fw-001](../../../models/DeepSeek-V4-Flash-W8A8/metax/20261022-thinking-gpqa-metax103/optimize/fw-001.md)和[op-001](../../../models/DeepSeek-V4-Flash-W8A8/metax/20261022-thinking-gpqa-metax103/optimize/op-001.md)。原perf-001段保留为历史失败记录，该段为fw001/op001历史状态，最新op002稳定性结果见页首。

<!-- long-context-repair:end -->


原始镜像反复出现top-k mask/copy编译：六轮吞吐57.11/166.19/166.99/208.91/208.92/168.77tok/s，全部仍属预热，未改标测量。无新增编译的两个快轮也不能替代三轮稳态对照。完整条件与失败证据见[fw-002](../../../models/DeepSeek-V4-Flash-W8A8/metax/20261022-thinking-gpqa-metax103/optimize/fw-002.md)；修复与限域知识见[op-002](../../../models/DeepSeek-V4-Flash-W8A8/metax/20261022-thinking-gpqa-metax103/optimize/op-002.md)。


当前修复服务已恢复至 `mx-103/deepseekV4-flash:18001`，prefix cache关闭。2026-10-23 19:12 UTC恢复核验18/18请求通过，7/7 graph capture完成、C1/C8多次replay及8个worker审计通过，源码与三轮测量时一致；回执与边界见[op-002](../../../models/DeepSeek-V4-Flash-W8A8/metax/20261022-thinking-gpqa-metax103/optimize/op-002.md)。

2026-10-27 用户当前服务C64默认采样全量评测完成：GPQA165/198=83.33%，MATH500479/500=95.80%，thinking/prefix cache均开启；[本次评测记录](/Users/baai/Documents/ChatGPT/端到端推理优化/docs/cases/20261022-thinking-gpqa-metax103/accuracy-c64-default-20261027.md)。历史fw005分数不代替本次结果。

2026-10-27 Plugin auxiliary cleanup completed: old examples 11 files removed; tests 2 files/652 lines -> 1 file/136 lines, 5 regressions passed; all changed paths 48 -> 36 (including untracked resources). Runtime package and current service unchanged. [Cleanup record](/Users/baai/Documents/ChatGPT/端到端推理优化/models/DeepSeek-V4-Flash-W8A8/metax/20261022-thinking-gpqa-metax103/optimize/cleanup-001.md).

2026-10-27 production cleanup retained: 36 -> 33 changed paths, 776 lines removed; obsolete model/compilation JSON removed, two real MoE tuning tables retained; native weight loader inherited. Final graph service20/20 minimal requests and repeated FULL replay passed, source/instance changed so historical formal scores are not current gates. [Cleanup details](/Users/baai/Documents/ChatGPT/端到端推理优化/models/DeepSeek-V4-Flash-W8A8/metax/20261022-thinking-gpqa-metax103/optimize/cleanup-002.md).

2026-10-27 cleanup-003: narrowed DeepSeek MetaX patch222->127 lines, moved model activation to existing config module, removed duplicate eager prewarm in favor of existing ModelRunner hook. Net10 lines removed;33 changed files remain.35 dispatch bindings and20-request graph regression passed; current API961222/ticks1151586767. Current log /public-flash/jinghao/deepseekV4/20261022-thinking-gpqa-metax103/plugin-cleanup-20261027-04/server.log. No formal score/performance measured for this source; see model optimize/cleanup-003.md.
