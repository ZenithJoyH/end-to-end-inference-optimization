# Plugin release/0.2 迁移回归验证

acc-008 全量精度已完成并独立验收：当前8010用户服务、GPQA/ERQA均64并发、模型默认t1/p.95/k20、无额外request seed、输出预算30000、prefix-on。GPQA **162/198（81.82%）** 达155/198阈值；ERQA **244/400（61.00%）**，400完整计分、零拒答剔除，无指定ERQA阈值。原生队列于2026-10-27 19:59:53 CST完成，20:20独立复核通过；59次原生超时重试保留，最终400题全部返回。半小时监控qwen27b-8010-c64已删除；用户服务未停止/重启/修改，性能仍暂停。

acc-008: new user8010 service full accuracy RUNNING. GPQA198 entered native generate_until at2026-10-27 16:58:15 CST, C64/cache0/newrun86f261cd7fcd48f8a3bed83ca59e416c; native preflight exit0, durable controller5777/startticks1140221643. ERQA400/C64 queued serially afterGPQA. Actual model-defaultt1/p.95/k20/no request seed/outputbudget30000/prefix-on preserved; no current final score. Monitorqwen27b-8010-c64 ACTIVE30min. No service/source changes or performance run.

2026-10-27: Plugin maintenance [env-007](../../../models/Qwen3.6-27B/metax/20261022-qwen36-27b-mx104-plugin-regression/optimize/env-007-plugin-update.md) complete: release/0.2 HEAD1bc0c77 (PR638 formally merged), editable0.2.2rc2.post1+g1bc0c775f.d20261027. Effective attention unchanged, metax.yaml local changes preserved;249 other package versions unchanged.8CPU/mock+28differential and actual login-shell fresh import passed. User9998 service exited with EngineDeadError before pip; no service actions/restart and no inference/performance tests.

状态：用户当前9998黑名单9服务C64/默认采样全量精度已完成：GPQA163/198（82.32%）达155阈值；ERQA239/400（59.75%）全400计分、零剔除且无指定阈值。原生与独立后验通过，半小时监控已删除、用户服务保留，性能仍按用户要求暂停。旧白名单C32/C8的159/198与235/400留作异配置历史，不作单变量收益归因。

本案例验证用户指定的 mx-104 / qwen3.6-27B-verify 当前代码迁移。模型使用 /data/Qwen3.6-27B，保留已有实现，源容器不承载本次性能测试或源码变更。旧环境以容器内完整原 Plugin 及 editable metadata 备份恢复，候选以当前容器快照为准；不使用本地旧优化数字作为基线。

用户在测量前明确接受：完整198题 GPQA 候选分数不低于更新前实测；输出吞吐下降不超过5%，各延迟上升不超过5%，并以回退复测排除漂移。A1首先取得参考分数，再冻结候选数值阈值，不事后换参考分数。

远程任务目录：`/public-flash/jinghao/qwen3.6-27B/20261022-qwen36-27b-mx104-plugin-regression`。原始命令、日志、inspect、trace和评测结果均在该目录。当前源镜像为 `sha256:afcbdac2f632d7a37de05f318cfe804007cc0ce3a332be8ff36f0d1913c74a9e`；两个专用clone必须先通过writable-layer快照谱系与原始挂载一致性校验。两目录挂载为 `/data` rw rslave 和 `/public-flash` rw rprivate。源码和安装位于非挂载的 /workspace、/opt 中。

执行记录：[val-001](../../../models/Qwen3.6-27B/metax/20261022-qwen36-27b-mx104-plugin-regression/optimize/val-001.md)。[baseline](../../../models/Qwen3.6-27B/metax/20261022-qwen36-27b-mx104-plugin-regression/baseline/README.md) / [optimize](../../../models/Qwen3.6-27B/metax/20261022-qwen36-27b-mx104-plugin-regression/optimize/README.md) / [acceptance](../../../models/Qwen3.6-27B/metax/20261022-qwen36-27b-mx104-plugin-regression/acceptance/README.md)。本案例为已优化环境的迁移回归，不签发原始未优化anchor的项目累计优化结论。

2026-10-27 12:18 CST：按用户最新明确要求，已删除 mx-104 其余17个 Qwen3.6-27B 相关容器（含原 verify、A clone、两个评测容器、13个已退出历史 dense 容器），仅保留 `qwen36-27b-regression-b-20261022`。保留B的API/Engine/两worker启动时间未变，9998 health200；271个无关容器身份/运行状态无变化。镜像、volume、挂载数据、模型、结果与备份均保留；性能仍暂停。
