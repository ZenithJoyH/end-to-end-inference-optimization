# 当前用户服务验收

本轮 acc-011 全量精度已完成并通过原生及独立复核：**GPQA163/198（82.32%）** 达155/198阈值；**ERQA246/400（61.50%）**，全400计分、零拒答剔除，无指定ERQA阈值。目标为当前 `qwen36-27b-clean-20261028` 用户8010服务，两套均C64、模型默认t1/p.95/k20/无额外request seed、30k输出预算、prefix-on。原生队列完成于2026-10-28 18:19:56 CST，独立复核实际时间22:02:58 CST；触发时间18:31不冒充实际执行时刻。68条原生超时重试保留，最终400题均非空返回。用户服务未暂停/停止/重启或改配置/源码，性能暂停；半小时监控 `qwen27b-clean-c64` 已删除。

| 本轮数据集 | 正确 / 完整计分 | 得分 | 结论 |
|---|---:|---:|---|
| GPQA | 163/198 | 82.32% | 达155/198，原生及独立验收通过 |
| ERQA | 246/400 | 61.50% | 全400计分、零剔除；无指定阈值 |

[本轮完整记录](../optimize/acc-011-clean-c64-full-accuracy.md)。以下是此前过程及历史实例记录，不能替代以上新实例最终结果。

acc-011 新clean容器本轮GPQA **163/198（82.32%）** 已原生/独立验收通过；ERQA **131/400** 条响应、尚无完整分数。当前8010/C64默认采样服务保持，整体精度范围待ERQA完成，性能暂停（2026-10-28 16:29 CST）。

当前新服务 [acc-011](../optimize/acc-011-clean-c64-full-accuracy.md) 正在评测：`qwen36-27b-clean-20261028` / 8010，GPQA198→ERQA400均C64、默认采样；15:39 CST已开始GPQA，尚无本轮完整分数。以下acc-008等为历史实例结果，不能作为新实例gate。半小时监控ACTIVE，用户服务不动，性能暂停。

env-010 镜像维护完成（2026-10-28）：mx-104 本地镜像 `qwen36-27b-metax-optimized:20261028-clean-env`，ID `f001fd92fbc7`，已真正删除目标 Env 键。其余镜像配置、17 层文件系统、代码修改和 editable 安装核对一致；当前用户8010服务身份/环境与 health200 保持，未暂停或重启。临时快照/归档已清理；模型及脚本仍须原挂载。精度历史和性能暂停状态不变，未重测。详见 [env-010](../optimize/env-010-clean-image.md)。

acc-008 全量精度已完成并独立验收：当前8010用户服务、GPQA/ERQA均64并发、模型默认t1/p.95/k20、无额外request seed、输出预算30000、prefix-on。GPQA **162/198（81.82%）** 达155/198阈值；ERQA **244/400（61.00%）**，400完整计分、零拒答剔除，无指定ERQA阈值。原生队列于2026-10-27 19:59:53 CST完成，20:20独立复核通过；59次原生超时重试保留，最终400题全部返回。半小时监控qwen27b-8010-c64已删除；用户服务未停止/重启/修改，性能仍暂停。

acc-008最新：GPQA **162/198（81.82%）** 通过155/198阈值并独立复验；ERQA **144/400** 条唯一非空响应，尚无最终分数。用户8010/C64/默认采样及服务保持，半小时跟进继续；性能暂停。

acc-008: new user8010 service full accuracy RUNNING. GPQA198 entered native generate_until at2026-10-27 16:58:15 CST, C64/cache0/newrun86f261cd7fcd48f8a3bed83ca59e416c; native preflight exit0, durable controller5777/startticks1140221643. ERQA400/C64 queued serially afterGPQA. Actual model-defaultt1/p.95/k20/no request seed/outputbudget30000/prefix-on preserved; no current final score. Monitorqwen27b-8010-c64 ACTIVE30min. No service/source changes or performance run.

2026-10-27: Plugin maintenance [env-007](../optimize/env-007-plugin-update.md) complete: release/0.2 HEAD1bc0c77 (PR638 formally merged), editable0.2.2rc2.post1+g1bc0c775f.d20261027. Effective attention unchanged, metax.yaml local changes preserved;249 other package versions unchanged.8CPU/mock+28differential and actual login-shell fresh import passed. User9998 service exited with EngineDeadError before pip; no service actions/restart and no inference/performance tests.

项目总体仍为 **incomplete**：本轮用户要求的C64默认采样全量精度已完成，性能最终验收保持暂停。

| 数据集 | 正确/完整题数 | 得分 | 结论 |
|---|---:|---:|---|
| GPQA | 163/198 | 82.32% | 达冻结155/198，原生gate及独立复核通过 |
| ERQA | 239/400 | 59.75% | 全400计分、零剔除；无指定阈值，仅报告得分 |

两套均并发64，绑定用户B容器当前9998/qwen36-27b-black-list服务及黑名单9配置，默认temperature1/top_p0.95/top_k20、不额外请求seed、输出预算30000，prefix caching保持开启。56条原生超时重试保留，最终400题全部返回计分；400题/630图/评测源码/配置和同实例/四包源码内容后验一致。当前graph capture启动日志已核验，未冒充trace证明的新实例两次replay，不代表最终性能验收通过。

[完整记录](../optimize/acc-005-c64-model-default-accuracy.md)与[当前结构化状态](../optimize/state.yml)保存外部原生结果和独立回执路径/SHA。监控qwen27b-c64已删除，用户服务保留、原verify未动，性能仍暂停，未提交/推送。

历史[acc-004](../optimize/acc-004-pr638-full-accuracy.md)白名单配置的159/198与235/400单列；因并发、采样和缓存等配置不同，不作单变量收益或回退归因。

2026-10-27 12:18 CST：按用户最新明确要求，已删除 mx-104 其余17个 Qwen3.6-27B 相关容器（含原 verify、A clone、两个评测容器、13个已退出历史 dense 容器），仅保留 `qwen36-27b-regression-b-20261022`。保留B的API/Engine/两worker启动时间未变，9998 health200；271个无关容器身份/运行状态无变化。镜像、volume、挂载数据、模型、结果与备份均保留；性能仍暂停。
