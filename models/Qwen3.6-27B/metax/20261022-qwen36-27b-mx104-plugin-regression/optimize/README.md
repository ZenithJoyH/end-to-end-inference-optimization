# 迁移验证总览

本轮 acc-011 全量精度已完成并通过原生及独立复核：**GPQA163/198（82.32%）** 达155/198阈值；**ERQA246/400（61.50%）**，全400计分、零拒答剔除，无指定ERQA阈值。目标为当前 `qwen36-27b-clean-20261028` 用户8010服务，两套均C64、模型默认t1/p.95/k20/无额外request seed、30k输出预算、prefix-on。原生队列完成于2026-10-28 18:19:56 CST，独立复核实际时间22:02:58 CST；触发时间18:31不冒充实际执行时刻。68条原生超时重试保留，最终400题均非空返回。用户服务未暂停/停止/重启或改配置/源码，性能暂停；半小时监控 `qwen27b-clean-c64` 已删除。 详见 [acc-011](acc-011-clean-c64-full-accuracy.md)。

以下进度段落按历史检查保留，以上为最终状态。

acc-011 最新（2026-10-28 17:59 CST）：ERQA **395/400（98.75%）** 唯一非空响应，剩5题，完整评分尚未生成；67条原生超时重试提示保留，继续原生任务。服务/source/默认配置与11冻结SHA通过；GPQA **163/198（82.32%）** 已验收，半小时通知继续，性能暂停。

acc-011 最新（2026-10-28 17:29 CST）：ERQA **371/400（92.75%）** 唯一非空响应，尚无最终分数；59条原生超时重试提示保留，任务持续增长、服务/源码/默认配置及11冻结SHA通过。GPQA **163/198（82.32%）** 已验收，继续既有ERQA与半小时通知，性能暂停。

acc-011 半小时进度（2026-10-28 16:59 CST）：ERQA **257/400** 唯一非空响应，尚无完整分数；相邻日志检查累计28条原生超时重试提示，任务持续返回，不能当作28题失败。当前服务/源码/参数和11冻结SHA核验通过，继续既有任务；GPQA **163/198（82.32%）** 已验收，性能暂停。

acc-011 当前（2026-10-28 16:29 CST）：本轮 **GPQA163/198（82.32%）** 达155阈值，原生与独立复验通过；**ERQA131/400** 唯一非空响应已落盘，完整评分待完成。用户clean容器8010/C64/默认采样及服务保持，半小时跟进继续，性能暂停。详见 [acc-011](acc-011-clean-c64-full-accuracy.md)。

acc-011 半小时进度（2026-10-28 15:59 CST）：GPQA **请求完成进度162/198（约82%，非得分）**；完整结果尚无，ERQA400/C64随后串行。相同服务/source/参数健康，11冻结SHA通过，继续既有作业及半小时通知，性能暂停。

[acc-011](acc-011-clean-c64-full-accuracy.md)：新 `qwen36-27b-clean-20261028` 用户8010实例，GPQA198已于2026-10-28 15:39 CST进入原生请求，缓存命中0/C64/默认t1/p.95/k20/无额外seed/30k预算；ERQA400/C64随后串行，尚无本轮最终分数。新结果目录与实例已核验，每30分钟跟进，用户服务不动，性能保持暂停。

env-010 镜像维护完成（2026-10-28）：mx-104 本地镜像 `qwen36-27b-metax-optimized:20261028-clean-env`，ID `f001fd92fbc7`，已真正删除目标 Env 键。其余镜像配置、17 层文件系统、代码修改和 editable 安装核对一致；当前用户8010服务身份/环境与 health200 保持，未暂停或重启。临时快照/归档已清理；模型及脚本仍须原挂载。精度历史和性能暂停状态不变，未重测。详见 [env-010](env-010-clean-image.md)。

env-009 在线维护完成：新root登录/交互Bash已取消旧VLLM_FL_METAX_CONTIGUOUS_SINGLE_PREFILL，其他已核验环境变量及原bashrc内容保持；Docker固化Env与当前模型进程已继承值未改，完全移除仍需以后重建容器。可写层6.18→4.43GiB，实际减少1.75GiB；清理pip下载缓存和两份已归档历史验证缓存。当前API/Engine/两worker PID/startticks/完整环境SHA、源码/全部包版本与health200均未变；当前vLLM/Triton/Inductor缓存及模型、源码、回退备份均保留，无信号/重启/推理或性能测试。 Record: [env-009](env-009-online-maintenance.md).

acc-008 全量精度已完成并独立验收：当前8010用户服务、GPQA/ERQA均64并发、模型默认t1/p.95/k20、无额外request seed、输出预算30000、prefix-on。GPQA **162/198（81.82%）** 达155/198阈值；ERQA **244/400（61.00%）**，400完整计分、零拒答剔除，无指定ERQA阈值。原生队列于2026-10-27 19:59:53 CST完成，20:20独立复核通过；59次原生超时重试保留，最终400题全部返回。半小时监控qwen27b-8010-c64已删除；用户服务未停止/重启/修改，性能仍暂停。

acc-008最新：GPQA **162/198（81.82%）** 通过155/198阈值并独立复验；ERQA **144/400** 条唯一非空响应，尚无最终分数。用户8010/C64/默认采样及服务保持，半小时跟进继续；性能暂停。

acc-008: new user8010 service full accuracy RUNNING. GPQA198 entered native generate_until at2026-10-27 16:58:15 CST, C64/cache0/newrun86f261cd7fcd48f8a3bed83ca59e416c; native preflight exit0, durable controller5777/startticks1140221643. ERQA400/C64 queued serially afterGPQA. Actual model-defaultt1/p.95/k20/no request seed/outputbudget30000/prefix-on preserved; no current final score. Monitorqwen27b-8010-c64 ACTIVE30min. No service/source changes or performance run. Record: [acc-008](acc-008-c64-8010-full-accuracy.md).

2026-10-27: Plugin maintenance [env-007](env-007-plugin-update.md) complete: release/0.2 HEAD1bc0c77 (PR638 formally merged), editable0.2.2rc2.post1+g1bc0c775f.d20261027. Effective attention unchanged, metax.yaml local changes preserved;249 other package versions unchanged.8CPU/mock+28differential and actual login-shell fresh import passed. User9998 service exited with EngineDeadError before pip; no service actions/restart and no inference/performance tests.

当前容器清理状态：2026-10-27 12:18 CST：按用户最新明确要求，已删除 mx-104 其余17个 Qwen3.6-27B 相关容器（含原 verify、A clone、两个评测容器、13个已退出历史 dense 容器），仅保留 `qwen36-27b-regression-b-20261022`。保留B的API/Engine/两worker启动时间未变，9998 health200；271个无关容器身份/运行状态无变化。镜像、volume、挂载数据、模型、结果与备份均保留；性能仍暂停。 记录见 [env-006](env-006-container-cleanup.md)。

- [val-001](val-001.md)：graph、198 GPQA和四场景A/B/A；执行中，尚未通过。


旧版首个实例四场景32/32轮完成，原生check_run复验通过；输出吞吐中位数1162.73/692.10/230.01/113.68 token/s。独立重复和新版/回退比较待完成。停止脚本解释器兼容已解决，baseline-02已精确TERM退出，容器保留；新版candidate-01指纹已核验仅Plugin不同，graph已通过capture/两次实际replay，最小精度10/10与算术2已通过；b1-formal-198完整精度已验收155/198，与旧版相等，原生issue/check回执通过；已切回未改动旧版baseline03，graph重验通过，a2-sanity已核验9/10/算术2/12请求完整，31SHA通过；a2-p1k-noise四trace已完成审阅，定位到refill mixed干扰，具体调度原因仍未完全证明；保持原噪声incomplete，推进candidate02测量。

<!-- e2e:summary:start -->

- 案例：20261022-qwen36-27b-mx104-plugin-regression
- 当前状态：acc011_full_accuracy_completed_performance_paused
- 当前候选：user-c64-03-clean-port8010
- 下一步：User clean-container C64 full GPQA and ERQA complete and independently verified; monitor deleted. Preserve user8010 service; no additional inference or performance, await user direction.

| 实验 | 状态/决定 | 场景 | 文档 |
|---|---|---|---|
| acc-011 | full native and independent verification complete; GPQA163/198 passed155 threshold, ERQA246/400=61.5percent zero exclusions; monitor deleted, user service preserved, performance paused | GPQA198-ERQA400-C64-model-default-sampling | [acc-011-clean-c64-full-accuracy.md](acc-011-clean-c64-full-accuracy.md) |
| env-010 | retained local clean image; effective Env removed; source service and all other config/source preserved | environment-maintenance | [env-010-clean-image.md](env-010-clean-image.md) |
| env-009 | online scope complete; new Bash legacy var unset,1.75GiB writable layer freed; service/source/settings intact; immutable Docker/live env removal deferred | environment-maintenance | [env-009-online-maintenance.md](env-009-online-maintenance.md) |
| acc-008 | full native and independent verification complete; GPQA162/198 passed155 threshold, ERQA244/400=61percent zero exclusions; monitor deleted, service unchanged, performance paused | GPQA198-ERQA400-C64-model-default-sampling | [acc-008-c64-8010-full-accuracy.md](acc-008-c64-8010-full-accuracy.md) |
| env-007 | release/0.2 updated to1bc0c77; local config preserved; editable refreshed;249 other versions unchanged;8CPU and28differential passed; service exited before pip, not restarted | environment-maintenance | [env-007-plugin-update.md](env-007-plugin-update.md) |
| env-006 | completed; B service unchanged and health200; unrelated containers unchanged; performance paused | environment-maintenance | [env-006-container-cleanup.md](env-006-container-cleanup.md) |
| val-001 | running | migration-four-scenarios | [val-001.md](val-001.md) |
| env-001 | retained_source_editable_maintenance_only | environment-maintenance | [env-001.md](env-001.md) |
| env-002 | latest_upstream_installed; prior modifications retained as whole backups, not active | environment-maintenance | [env-002.md](env-002.md) |
| fw-001 | PR638 applied in B and current combined precision verified; original verify untouched, performance paused, no individual PR benefit attribution | contiguous-prefill-auto-selection | [fw-001.md](fw-001.md) |
| diag-003 | Corrected missed MetaX sampler patch; prioritize controlled sort/sort_stable family exclusion at P1K, no new tests | manual-whitelist-blacklist-gap | [diag-003.md](diag-003.md) |
| acc-004 | Full user-requested precision complete; hourly monitor deleted; preserve minimal8/10 observation, performance remains paused | full-gpqa198-erqa400 | [acc-004-pr638-full-accuracy.md](acc-004-pr638-full-accuracy.md) |
| acc-005 | User full precision scope complete;30min monitor deleted;existing user9998 service preserved,performance remains paused | GPQA198-ERQA400-C64-model-default-sampling | [acc-005-c64-model-default-accuracy.md](acc-005-c64-model-default-accuracy.md) |

| 场景 | 角色 | 指标 | 数值 | 单位 | 范围 |
|---|---|---|---|---|---|

<!-- e2e:summary:end -->

性能比较准入补查：P1K三正式轮TTFT中位数波动 **10.015% > 5%**，因此当前性能结论为 **incomplete**。32轮完整性原生复验通过不能替代比较准入；所有轮次保留，需定位波动后复测。其余主/守护指标轮内波动未超5%；候选尚无性能结果，不能归因迁移回退。

用户明确批准后已精确清理两残留worker；原stop-v2确认全部退出、lease释放，GPU2/3空闲。继续candidate02新实例验证，定时跟进保持ACTIVE。

最新手工黑名单6（追加 mm_out/max_dim）结果：P1K **1368.89**、P4K **2439.36 total tok/s**，较有效黑名单4改善15.44%/32.74%，仍比历史白名单低22.25%/15.75%。下一优先排查仍放行的 `linear` 词表投影，小 batch sort 为次级候选；没有恢复自动评测或变更服务。见 [diag-003.md](diag-003.md)。

2026-10-26：追加 `linear` 后五场景总吞吐变化均低于0.3%，P1K1371.26/P4K2439.48 tok/s；此前 linear 首要假设未获实测支持，已降级。下一步需要当前白名单对照及有代表性的双rank P1K trace，不再盲目追加黑名单。仍暂停自动测试，未改动服务。

2026-10-26 白名单复验P1K恢复 **1766.99 total tok/s**，黑名单7低22.40%。已更正此前遗漏：MetaX补丁强制全batch走PyTorch采样，C64也会全词表排序；黑名单进入FlagGems8轮radix sort，白名单保留native。下一单变量应是sort/sort_stable这一组别名，精确贡献仍待验证；本轮仅只读分析。

2026-10-26：已将 [PR #638](https://github.com/flagos-ai/vllm-plugin-FL/pull/638) 最新3e04e696源码应用到 B；保留 metax.yaml/其他源码，8CPU/mock与28差分用例通过。下次启动加载；未做硬件测试或恢复性能回归。备份/回退见 [fw-001.md](fw-001.md)。

2026-10-26 用户授权PR638后的全量精度：[acc-004](acc-004-pr638-full-accuracy.md)新candidate03已完成graph两rank真实replay，固定最小→GPQA198→ERQA400单次原生串行队列已启动，尚无新分数；监控qwen27b-pr638每小时跟进。仅精度恢复，性能仍暂停。

当前精度队列为 **pr638-full-accuracy-diagnostic**：固定最小12请求正常完成但GPQA10=8/10低于旧参考9/10，保留失败并调用精度定位Skill。用户要求的全量GPQA198已于16:18:52 CST启动，后续ERQA400；仅精度诊断，不视作最小通过，不改155/198阈值，尚无新全量分数。

2026-10-26 17:15 CST：[acc-004](acc-004-pr638-full-accuracy.md)全量GPQA **159/198（80.30%）**，冻结阈值155/198，原生issue/check及396行/198唯一题SHA复验通过。ERQA400已串行运行，当前29条原生响应落盘，尚无最终分数；性能保持暂停。最小8/10的历史参考差异保留，不作PR单点归因。

2026-10-26 19:08 CST：ERQA **260/400**条非空原生响应已落盘，ID唯一且属于冻结题集；最终分数尚未生成。三条超时提示已核实来自原生重试，不能当作三题最终失败。既有控制进程与B服务实例健康，未重复启动；GPQA159/198通过、性能暂停。

最新小时检查（2026-10-26 19:31 CST）：ERQA原生响应 **300/400**，完整评分待生成；GPQA **159/198（80.30%）**已验收通过。原生重试警告仍3条，继续既有任务，性能暂停。

最新小时检查（2026-10-26 20:30 CST）：ERQA **398/400**条原生响应已落盘，剩389/393待返回、尚无最终评分；同实例health200、controller启动时间一致。原生超时重试warning累计4条，继续保留，不报告部分分数。GPQA159/198通过、性能暂停。

[acc-004](acc-004-pr638-full-accuracy.md) 全量精度最终验收：**GPQA159/198（80.30%）** 达155/198阈值；**ERQA235/400（58.75%）**，400全部评分、零剔除，无指定阈值。630图/数据/源码/配置及同实例身份后验通过，零额外推理。小时监控已删除，性能暂停；原最小8/10差异保留、不作PR单点归因。

启动配置范围澄清：当前用户`start-model-flagos.sh`为黑名单9项；已测candidate03为白名单27项并清空黑名单。因此GPQA159/198及ERQA235/400不覆盖当前黑名单脚本。只读核验实际仍监听18027评测服务，9998未监听；没有重启、改配置或重测。详情见acc-004记录。

[acc-005](acc-005-c64-model-default-accuracy.md)：用户新9998黑名单9服务，全量GPQA/ERQA均C64、模型默认t1/p0.95/k20准备中；保持用户当前prefix-on服务，旧白名单结果单列，性能继续暂停。

[acc-005](acc-005-c64-model-default-accuracy.md) 用户新9998黑名单服务精度已开始：GPQA198与后续ERQA400均C64，模型默认t1/p.95/k20、不额外设置请求seed，输出预算30k。22:20:29原生198题请求/响应cache0；尚无本轮分数。用户prefix-on保持，monitor qwen27b-c64每30分钟；性能暂停。

acc-005 半小时进度（2026-10-26 22:40 CST）：当前用户9998服务GPQA **149/198**请求完成，尚无最终分数，ERQA400/C64随后。11项冻结引用未变、同服务健康；原生客户端逐请求deepcopy保证采样参数隔离。性能保持暂停，不重复启动。

acc-005 当前（2026-10-26 23:04 CST）：**GPQA163/198（82.32%）** 达155阈值并通过原生及主Agent证据复核；**ERQA70/400**条非空原生响应已落盘、最终评分待完成。C64/模型默认采样及用户prefix-on保持，性能暂停。

acc-005（2026-10-26 23:35 CST）：ERQA **246/400**条原生非空响应落盘，16条原生超时重试提示保留，尚无最终分数；同服务正常、冻结参数未变。GPQA **163/198（82.32%）**通过，性能仍暂停。

acc-005（2026-10-27 00:05 CST）：ERQA **364/400（91%）**条非空原生响应，38次原生超时重试提示保留，尚无最终分数；同服务/配置正常。离线确认provider HTTP read600s与CLI7200s属不同配置路径，未调整运行中配置。GPQA163/198（82.32%）通过，性能暂停。

acc-005（2026-10-27 00:35 CST）：ERQA **393/400**条非空原生响应，7未落盘、最终分数尚无；同服务聚合7running/0waiting、health200，53条原生重试提示保留。GPQA163/198（82.32%）通过；性能继续暂停。

[acc-005](acc-005-c64-model-default-accuracy.md) 最终结果：**GPQA163/198（82.32%）** 达155/198；**ERQA239/400（59.75%）**，400完整计分、零剔除、未设ERQA阈值。当前用户9998服务/C64/默认t1/p.95/k20/无额外request seed/30k预算/prefix-on，独立原生与630图/数据/源码/配置/同实例后验通过，56次原生重试保留。qwen27b-c64已删除，用户服务未动、性能暂停；不与旧异配置结果作单变量归因。

acc-008（2026-10-27 17:24 CST）：GPQA原生进度170/198，尚无最终分数；ERQA随后。同实例健康、11冻结引用不变，继续既有队列和半小时通知，性能暂停。

acc-008（2026-10-27 19:46 CST）：ERQA398/400条唯一非空响应，2题待返回，尚无最终分数；59次原生超时重试提示保留，服务健康。GPQA162/198（81.82%）已验收通过，半小时跟进继续，性能暂停。
