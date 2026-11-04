# 20261022-thinking-gpqa-metax103

<!-- fw005-current -->
2026-10-26 当前保留：[fw-005](optimize/fw-005.md) 以一个现有Plugin文件的原生TP P2P compute-stream生命周期修复headpack跨层临时缓冲压力。保持原 **0.85/KV567220/prefixOFF**、所有数学/kernel和用户启动脚本；不增加env/启动参数。八卡43层探针pending2752→0MiB、精确数值通过（仅此传输微测）。

新完整thinking GPQA **172/198=86.87%**通过80%阈值，新schema3 gate已绑定当前source与实例。原用户run_once/no-profiler，D1024/C64/N128，P1K3/P4K3/P16预热+3/P32预热+3，**14轮1792/1792成功，零OOM/非法访存/新增KV抢占**：

|输入|测量轮|输出吞吐(tok/s)|mean TTFT(s)|mean TPOT(ms)|
|---|---:|---:|---:|---:|
|16K|1|357.4344|36.4288|141.4292|
|16K|2|356.9035|36.4478|141.6487|
|16K|3|357.7659|36.3298|141.3659|
|32K|1|207.9711|72.5251|232.4410|
|32K|2|208.2478|72.4975|232.0488|
|32K|3|208.1731|72.2650|232.4472|


P16吞吐/TPOT spread0.241%/0.200%；P32为0.133%/0.171%。fw005验收时服务健康空闲。后续[僵尸维护](../../../../docs/cases/20261022-thinking-gpqa-metax103/zombie-cleanup-20261026.md)清理254→0，容器未重启；维护开始前18001已未监听，当前模型未运行，start-model.sh未变。属于同预算checkpoint稳定性，未补当前独立B/C/R或最终四场景正式验收；旧原镜像208.91仍仅未准入预热参考，不作加速比。新summary SHA `3bd44085286ff264b51d62b828c75b33f1ad1dc7deb3c29e14da3f18d803f54b`，完整路径/回退/未测项见fw005；下方op006等分数与测量是对应历史源码证据。
<!-- /fw005-current -->

<!-- op006-current -->
[op-006](optimize/op-006.md) 已复现并修复请求期 BF16 NT 选参：仅增加1个FG生产文件改动，Default log-M分桶并在请求前准备完整已验证形状范围，保留实际M/EVEN掩码与精确BenchmarkCache。新thinking GPQA **169/198=85.35%**通过80%阈值（op005为170/198，少1题）。

同一新实例、原始用户run_once、无profiler、prefix cache关闭，W3后保留全部三轮P32768/D1024/C64/N128：

| 轮次 | 输出吞吐(tok/s) | mean TTFT(s) | mean TPOT(ms) | 新编译（总/NT） |
|---|---:|---:|---:|---:|
| 1 | 203.3665 | 75.0368 | 237.2020 | 0/0 |
| 2 | 203.5084 | 74.9309 | 237.0885 | 0/0 |
| 3 | 201.2218 | 75.5128 | 239.9502 | 2/0 |

384/384成功，0 OOM/非法访存/抢占。吞吐spread **1.1244%**、TPOTspread **1.2064%**，均通过冻结5%阈值；三轮NT ConfigCache与BenchmarkCache均未变化。第三轮仍有index/mHC两项非NT编译，**不宣称全链路零JIT或旧31秒下降全部归因已闭合**。

中位吞吐203.3665tok/s；原镜像208.91仍仅预热参考，尚无正式稳定对照或新独立B/C/R；本组合四场景最终验收未完成。op006记录时服务健康空闲、prefixOFF；当前服务状态见上方fw005记录。
<!-- /op006-current -->


- [baseline](baseline/README.md)
- [optimize](optimize/README.md)
- [acceptance](acceptance/README.md)

## op005 历史参考

[op-005](optimize/op-005.md) 已修复量化/padding等原7项的token边界特化与launch key，共6个FG/FGV生产文件。新完整thinking GPQA **170/198＝85.86%**通过80%阈值。同一服务、无profiler、prefix cache关闭，使用用户原始run_once完成三轮P32768/D1024/C64/N128。

| 轮次 | 输出吞吐(tok/s) | mean TTFT(s) | mean TPOT(ms) | 新增编译（总/原7项） |
|---|---:|---:|---:|---:|
| 1 | 201.3868 | 75.0588 | 240.1629 | 3/0 |
| 2 | 203.7935 | 74.4507 | 237.1143 | 0/0 |
| 3 | 194.3892 | 77.8273 | 249.0065 | 3/0 |

384/384成功，无OOM、非法访存或抢占。吞吐spread **4.6697%**、TPOTspread **4.9518%**勉强满足冻结5%阈值；**第三轮下降仍在，不能宣称根因完全解决或全链路零JIT**。第一轮另3项来自BF16 NT GEMM/index/mHC heads，第三轮3项均为NT GEMM；原目标7项均未复发。全部轮次保留，没有挑选或重跑替换慢轮。

中位吞吐201.3868tok/s为本组合P32 targeted观察。原镜像208.91仍仅预热参考，没有正式稳定对照或新独立B/C/R；本组合四场景最终验收未完成。下一步首查NT实际输入布局、选参和请求期benchmark/cache miss，不能盲目去掉有效EVEN/tile条件。

历史native FP32 GEMM结果和172/198分数保留在[op-004](optimize/op-004.md)，早期原生编译恢复结果保留在[fw-003](optimize/fw-003.md)。

2026-10-27 用户当前服务C64默认采样全量评测完成：GPQA165/198=83.33%，MATH500479/500=95.80%，thinking/prefix cache均开启；[本次评测记录](/Users/baai/Documents/ChatGPT/端到端推理优化/docs/cases/20261022-thinking-gpqa-metax103/accuracy-c64-default-20261027.md)。历史fw005分数不代替本次结果。

2026-10-27 Plugin auxiliary cleanup completed: old examples 11 files removed; tests 2 files/652 lines -> 1 file/136 lines, 5 regressions passed; all changed paths 48 -> 36 (including untracked resources). Runtime package and current service unchanged. [Cleanup record](/Users/baai/Documents/ChatGPT/端到端推理优化/models/DeepSeek-V4-Flash-W8A8/metax/20261022-thinking-gpqa-metax103/optimize/cleanup-001.md).

2026-10-27 production cleanup retained: 36 -> 33 changed paths, 776 lines removed; obsolete model/compilation JSON removed, two real MoE tuning tables retained; native weight loader inherited. Final graph service20/20 minimal requests and repeated FULL replay passed, source/instance changed so historical formal scores are not current gates. [Cleanup details](/Users/baai/Documents/ChatGPT/端到端推理优化/models/DeepSeek-V4-Flash-W8A8/metax/20261022-thinking-gpqa-metax103/optimize/cleanup-002.md).

2026-10-27 cleanup-003: narrowed DeepSeek MetaX patch222->127 lines, moved model activation to existing config module, removed duplicate eager prewarm in favor of existing ModelRunner hook. Net10 lines removed;33 changed files remain.35 dispatch bindings and20-request graph regression passed; current API961222/ticks1151586767. Current log /public-flash/jinghao/deepseekV4/20261022-thinking-gpqa-metax103/plugin-cleanup-20261027-04/server.log. No formal score/performance measured for this source; see model optimize/cleanup-003.md.
