# Plugin release/0.2 迁移回归验证

env-009 在线维护完成：新root登录/交互Bash已取消旧VLLM_FL_METAX_CONTIGUOUS_SINGLE_PREFILL，其他已核验环境变量及原bashrc内容保持；Docker固化Env与当前模型进程已继承值未改，完全移除仍需以后重建容器。可写层6.18→4.43GiB，实际减少1.75GiB；清理pip下载缓存和两份已归档历史验证缓存。当前API/Engine/两worker PID/startticks/完整环境SHA、源码/全部包版本与health200均未变；当前vLLM/Triton/Inductor缓存及模型、源码、回退备份均保留，无信号/重启/推理或性能测试。 Record: [env-009](optimize/env-009-online-maintenance.md).

acc-008 全量精度已完成并独立验收：当前8010用户服务、GPQA/ERQA均64并发、模型默认t1/p.95/k20、无额外request seed、输出预算30000、prefix-on。GPQA **162/198（81.82%）** 达155/198阈值；ERQA **244/400（61.00%）**，400完整计分、零拒答剔除，无指定ERQA阈值。原生队列于2026-10-27 19:59:53 CST完成，20:20独立复核通过；59次原生超时重试保留，最终400题全部返回。半小时监控qwen27b-8010-c64已删除；用户服务未停止/重启/修改，性能仍暂停。

acc-008最新：GPQA **162/198（81.82%）** 通过155/198阈值并独立复验；ERQA **144/400** 条唯一非空响应，尚无最终分数。用户8010/C64/默认采样及服务保持，半小时跟进继续；性能暂停。

acc-008: new user8010 service full accuracy RUNNING. GPQA198 entered native generate_until at2026-10-27 16:58:15 CST, C64/cache0/newrun86f261cd7fcd48f8a3bed83ca59e416c; native preflight exit0, durable controller5777/startticks1140221643. ERQA400/C64 queued serially afterGPQA. Actual model-defaultt1/p.95/k20/no request seed/outputbudget30000/prefix-on preserved; no current final score. Monitorqwen27b-8010-c64 ACTIVE30min. No service/source changes or performance run. Record: [acc-008](optimize/acc-008-c64-8010-full-accuracy.md).

2026-10-27: Plugin maintenance [env-007](optimize/env-007-plugin-update.md) complete: release/0.2 HEAD1bc0c77 (PR638 formally merged), editable0.2.2rc2.post1+g1bc0c775f.d20261027. Effective attention unchanged, metax.yaml local changes preserved;249 other package versions unchanged.8CPU/mock+28differential and actual login-shell fresh import passed. User9998 service exited with EngineDeadError before pip; no service actions/restart and no inference/performance tests.

当前容器清理状态：2026-10-27 12:18 CST：按用户最新明确要求，已删除 mx-104 其余17个 Qwen3.6-27B 相关容器（含原 verify、A clone、两个评测容器、13个已退出历史 dense 容器），仅保留 `qwen36-27b-regression-b-20261022`。保留B的API/Engine/两worker启动时间未变，9998 health200；271个无关容器身份/运行状态无变化。镜像、volume、挂载数据、模型、结果与备份均保留；性能仍暂停。 记录见 [env-006](optimize/env-006-container-cleanup.md)。

状态：用户新9998黑名单9服务的acc-005全量精度已完成并独立验收：GPQA163/198（82.32%）达到冻结155/198；ERQA239/400（59.75%），全400计分、零剔除，无指定ERQA阈值。两套均64并发、模型默认t1/p.95/k20、不额外请求seed、输出预算30k，保留用户prefix-on/服务配置。半小时监控已删除，服务未停止或重启，性能继续暂停。旧acc-004白名单/贪心C32与ERQAC8结果159/198和235/400单列，不能作单变量收益归因。

本案例验证用户指定的 mx-104 / qwen3.6-27B-verify 当前代码迁移。模型使用 /data/Qwen3.6-27B，保留已有实现，源容器不承载本次性能测试或源码变更。旧环境以容器内完整原 Plugin 及 editable metadata 备份恢复，候选以当前容器快照为准；不使用本地旧优化数字作为基线。

用户在测量前明确接受：完整198题 GPQA 候选分数不低于更新前实测；输出吞吐下降不超过5%，各延迟上升不超过5%，并以回退复测排除漂移。A1首先取得参考分数，再冻结候选数值阈值，不事后换参考分数。

远程任务目录：`/public-flash/jinghao/qwen3.6-27B/20261022-qwen36-27b-mx104-plugin-regression`。原始命令、日志、inspect、trace和评测结果均在该目录。当前源镜像为 `sha256:afcbdac2f632d7a37de05f318cfe804007cc0ce3a332be8ff36f0d1913c74a9e`；两个专用clone已通过writable-layer快照谱系与原始挂载一致性校验。两目录挂载为 `/data` rw rslave 和 `/public-flash` rw rprivate。源码和安装位于非挂载的 /workspace、/opt 中。

执行记录：[val-001](optimize/val-001.md)。[baseline](baseline/README.md) / [optimize](optimize/README.md) / [acceptance](acceptance/README.md)。本案例为已优化环境的迁移回归，不签发原始未优化anchor的项目累计优化结论。

独立旧版baseline-03已完成P1K噪声定位并退出：组件指纹与冻结A一致，graph重新验证通过，固定最小回归a2-sanity已核验9/10、算术2、12请求完整，无健康告警；同配置P1K/C64有界原生诊断已完成并审阅四trace，续发mixed阶段与旧请求停顿/Prefill交错相关，客户端迟发解释已收窄；具体异步调度原因未完全证明，性能仍incomplete。历史新版candidate02曾就绪，双rank graph重新核验通过，固定12请求最小回归b2-sanity已通过9/10和算术2；当前实例原生精度rebind/check通过，b2-performance-warmup5已在P1K五轮预热后停止：末三轮吞吐spread5.0496%超过冻结5%，正式测量0轮，不能做迁移回退判定。以上为env002之前的验证记录；本次Gems源码升级后原gate不适用，需新验证。

用户已明确批准精确清理并继续验证：仅残留baseline03两worker经全部身份/证据门禁后各发送一次pidfd SIGKILL；随后stop-v2核验全部进程退出并释放lease，GPU2/3空闲。candidate02组件指纹与已评测候选一致，新graph已通过；minimal及原生精度重新绑定均已通过，新版性能未通过稳态准入，正在核对波动，全部轮次保留。每小时跟进已删除，等待用户明确恢复；原candidate02已在环境维护前退出，旧lease核验后释放；维护没有重启模型服务，容器保留。

补充逐题比较：A1/B1完整198题的原生samples字节相同，两filter合计396条记录一致；strict同155题答对/同43题答错，无题目得失交换。B02最小回归doc8触及30k输出上限，单列健康观察；正式198分数不变。

升级前 B 容器源码安装整理记录：[env-001](optimize/env-001.md)。FlagGems `/workspace/FlagGems` 和 FGV `/opt/FlagGems-vllm` 都是 editable；两包有效源码与原安装态逐字节一致、250 包版本不变、3187 个 Python 文件语法及全新进程导入通过。FGV 原 GDN 修改及安装包独有 MoE 修改均保留。FlagGems 以官方 v5.0.2@30bfcc0 重建比较基线，原始历史 commit 仍未知，未用上游代码替换现有实现；未提交推送。原 verify 的四套代码指纹和原安装布局未变化。没有启动模型服务或恢复性能回归；后续评测须重新核验安装路径/服务身份。

当前 B 安装已按用户要求更新到官方最新主线：[env-002](optimize/env-002.md)。FlagGems master@b3a676f（5.5.0.dev0+gb3a676f6a），FlagGems-vllm main@d3214ce（0.3.0.dev1），两者 editable；4083文件语法和fresh import通过，其余248包版本不变。旧完整源码与修改保存在retained-source-v2和压缩备份中，未套用到当前主线。原verify未动，未启动模型服务或恢复性能；旧精度/graph仅为升级前历史，不签本次新版本模型验收。

2026-10-24用户已完成手工E2E对齐，只读复核见[env-002](optimize/env-002.md)：五场景吞吐变化+5.15%/+0.19%/+0.60%/-1.51%/+2.19%，同CSV长度/请求/token完整；P32K/P64K平均TPOT分别+5.69%/+6.36%，保留长序列延迟差异。按原脚本Run2/3均值口径，不能替代旧正式契约/当前源码精度gate，自动评测继续暂停。

2026-10-24 [fw-001](optimize/fw-001.md): automatic MetaX contiguous single-decoder-prefill selection replaces the experimental env gate. CPU8 routing tests, syntax/lint/diff checks passed. Current user port9998 service kept; next restart requires no export. Hardware/graph/model accuracy/throughput after this change remain not_run. Current comparison focus is total-token throughput, with TPOT deferred per user.

User-requested test cleanup: fw001 reuses its prior case validation script; the added Plugin test file was removed with backup. All8 CPU checks passed again; current Plugin diff contains only the MetaX attention source change. No production/service/performance changes in this cleanup.

2026-10-25 [diag-003](optimize/diag-003.md): user whitelist/blacklist manual comparison shows P1K/P4K total throughput -32.56%/-37.44%, but9998 is served by an earlier API without the intended blacklist. The API carrying BLACKLIST is a separate launch and does not listen; active workers still log Gems mm/index_select. Preserve ongoing user tests, resolve service identity before operator attribution. Read-only, no automatic changes.

2026-10-25 最新手工 P1K 已核实命中携带黑名单的9998服务，1185.80 vs历史白名单1760.54 total tok/s（-32.65%）。此前端口错配仅适用于旧轮次。源码按函数名精确排除，mm不覆盖mm_out；新worker graph capture仍出现Gems MM。具体耗时贡献待单变量验证；仅只读诊断，未恢复自动测试或改动服务。详见 optimize/diag-003.md。

2026-10-25 后续黑名单6手工结果：P1K1368.89/P4K2439.36 total tok/s，分别比有效黑名单4高15.44%/32.74%，仍比历史白名单低22.25%/15.75%。已核实当前六项黑名单与监听身份；剩余优先候选为独立 linear 词表投影路径，尚未实测归因。自动性能回归继续暂停，服务未改动。

2026-10-26：追加 linear 的用户手工五场景结果基本不变（均<0.3%），linear 不是当前证据支持的主要原因。P1K仍比历史白名单低22.11%。已记录当前编译缓存内 linear 降为 mm-out 的证据；需同当前环境白名单对照及代表性双rank profiling 才能进一步归因，尚未执行，服务未改。

2026-10-26 白名单P1K复验1766.99 tok/s恢复，确认黑名单7剩余22.40%差距。发现并更正此前漏看的MetaX强制PyTorch采样补丁：完整C64也走全词表sort，黑白名单在FlagGems radix sort/native选择上不同。已有明确调用链，具体收益待sort/sort_stable单组实验或trace，未执行新测试。

2026-10-26 用户指定 PR #638 最新3e04e696已应用到 B 的 flash_attn.py（SHAf49f4a5b...），原有配置及其他文件保留并备份。8CPU/mock和28差分用例通过；原verify不动，无服务重启，性能回归保持暂停。详见 optimize/fw-001.md 与 state.pr638_application。

PR638后完整精度acc-004已运行：candidate03两rank graph通过，原生sanity→GPQA198→ERQA400持久队列pr638-full-accuracy-v2已启动；此刻未出新分数。小时监控qwen27b-pr638启用，性能暂停，verify不动。

2026-10-26 17:15 CST：[acc-004](optimize/acc-004-pr638-full-accuracy.md)全量GPQA **159/198（80.30%）**，冻结阈值155/198，原生issue/check及396行/198唯一题SHA复验通过。ERQA400已串行运行，当前29条原生响应落盘，尚无最终分数；性能保持暂停。最小8/10的历史参考差异保留，不作PR单点归因。

2026-10-26 19:08 CST：ERQA **260/400**条非空原生响应已落盘，ID唯一且属于冻结题集；最终分数尚未生成。三条超时提示已核实来自原生重试，不能当作三题最终失败。既有控制进程与B服务实例健康，未重复启动；GPQA159/198通过、性能暂停。
