# 20261022-qwen36-35b-mx104-stack-regression / acceptance

Latest C32: GPQA158/198 (79.80%) passed pre-frozen75% and independent audit. ERQA incomplete with OOM:180success/32HTTP500/188unsubmitted, no full400score. Service exited; gate remains evidence for evaluated instance, not future restarts. Terminal partial evidence verified; monitor deleted. No final performance claim.


<!-- e2e:summary:start -->

- 案例：20261022-qwen36-35b-mx104-stack-regression
- 当前状态：GPQA158_C32_passed075_ERQA_C32_OOM_incomplete
- 当前候选：release02@1bc0c77 + FGV guardedshortlist49e9/tuned MoE/GDN + FlagTree fe1d24f6 + Gems a456722a
- 下一步：Preserve full GPQA158/198 gate and ERQA180success32HTTP500188unsent partial proof. API exited; no automatic restart/rerun/performance or gate rebind.

| 实验 | 状态/决定 | 场景 | 文档 |
|---|---|---|---|

| 场景 | 角色 | 指标 | 数值 | 单位 | 范围 |
|---|---|---|---|---|---|
| p1024-d1024-c64-n128 | baseline | output_throughput | 1500.2496605103297 | token/s | 单实例3轮中位数观测；波动超限且整套incomplete，不作为完整验收 |
| p1024-d1024-c64-n128 | baseline | mean_ttft_ms | 1941.0504114348441 | ms | 单实例3轮中位数观测；波动超限且整套incomplete，不作为完整验收 |
| p1024-d1024-c64-n128 | baseline | p99_ttft_ms | 3740.857904739678 | ms | 单实例3轮中位数观测；波动超限且整套incomplete，不作为完整验收 |
| p1024-d1024-c64-n128 | baseline | mean_tpot_ms | 40.68825538566619 | ms | 单实例3轮中位数观测；波动超限且整套incomplete，不作为完整验收 |
| p1024-d1024-c64-n128 | baseline | p99_tpot_ms | 42.11236411701972 | ms | 单实例3轮中位数观测；波动超限且整套incomplete，不作为完整验收 |
| p1024-d1024-c64-n128 | baseline | mean_itl_ms | 40.68825552905164 | ms | 单实例3轮中位数观测；波动超限且整套incomplete，不作为完整验收 |
| p1024-d1024-c64-n128 | baseline | p99_itl_ms | 40.25421550497413 | ms | 单实例3轮中位数观测；波动超限且整套incomplete，不作为完整验收 |
| p1024-d1024-c64-n128 | baseline | mean_e2el_ms | 43565.13567097136 | ms | 单实例3轮中位数观测；波动超限且整套incomplete，不作为完整验收 |
| p1024-d1024-c64-n128 | baseline | p99_e2el_ms | 45333.94738264382 | ms | 单实例3轮中位数观测；波动超限且整套incomplete，不作为完整验收 |

<!-- e2e:summary:end -->

完整精度结果：基线160/198（80.81%），候选147/198（74.24%），候选低13题/6.5657个百分点，未达到冻结门槛，未签发gate。按精度诊断Skill保留失败证据并进行同请求B/A/B对照，根因未定；正式性能保持阻塞。性能原基线11轮全部保留，P4K预热不稳、P1K部分延迟波动，整体incomplete。安装一致性与FGV实际内核覆盖分别记录，未宣布最终验收。详见[state.yml](state.yml)及[完整实验](../optimize/regression-001.md)。


2026-10-28 当前opt3/prefix-on原生GPQA C64/full198：**161/198=81.3131%**，396filter行/旧160147161154重现/当前前后fresh源码服务身份独立通过，冻结门槛77.53%。验证：`/public-flash/jinghao/qwen3.6-35B/20261022-qwen36-35b-mx104-stack-regression/accuracy/user-gpqa-erqa-c64-20261028-001/gpqa-followup-001/independent-verification-001/verification.json` SHA c9437b838bd089152dc01a11c3f32076e89941334e545a89b8f175606366ebb9。随后ERQA OOM退出，无完整400分数；此项只精度，不表示四场景性能验收。详见[本次实验](../optimize/user-gpqa-erqa-c64-20261028-001.md)。

ERQA partial210 success/64HTTP500/126unsubmitted independently verified; full400 score null. Frozen incident f0d8a15a6e9a2cdb29d0f9675592b24bc2824b24e75362037e19a4517b155239. Monitor deleted at terminal failure; awaiting user recovery approval.

User rejected lowering utilization. Latest read-only report: `/public-flash/jinghao/qwen3.6-35B/20261022-qwen36-35b-mx104-stack-regression/accuracy/user-gpqa-erqa-c64-20261028-001/erqa/oom-analysis-001/analysis.json`, SHA ef9f0fe401f33f4c4f29e080fcb2161c70c223a2cc067a0c5aea844be30b29c5. This supersedes the old inactive0.8 recovery proposal; no such change was executed.
