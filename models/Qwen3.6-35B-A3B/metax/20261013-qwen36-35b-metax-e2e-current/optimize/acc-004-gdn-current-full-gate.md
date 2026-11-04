# acc-004 GDN 当前版本正式精度

用户2026-10-14明确恢复基于gdnopt版本的端到端优化。当前手工启动的8010 API PID952702/birth491055395，完整原白名单加gdn_decode/gdn_packed_decode，TP2 GPU6/7、prefixoff、FULL_AND_PIECEWISE graph；两个rank的packed MetaX kernel命中与capture完成日志已核验。直接graph replay次数尚未观察，不编造计数。

调用本地精度Skill `formal-gate`（e2e/accuracy）：沿用198题、strict-match>=.8、65536 cap、temperature1/top_p.95/top_k20/seed42/C32；只更新served-model绑定、唯一eval_model/run输出和当前provenance。原82.8283%回执属于旧源码+白名单实例，不rebind。两次provenance相同、真实dataset revision保持；预检中，未开始生成。

源码和模型清单、镜像/挂载已核；四repo12252文件只含已记录GDN改动，当前Plugin/Gems-vllm新快照与SHA保留。同一案例继续，原anchor baseline身份不改；GDN为当前组合候选。精度期间不并发GPUbench/profile/probe，不部署源变更。低于80或证据无效冻结失败并调用diagnosis，不自行改契约。

正式复测已启动，不重启服务。UUID `f8675c1380524ff396d0b07bac65fd26`，hostcontroller PID488476/birth492530345；命令/日志/只读monitor与SHA已写state。观察2026-10-14T13:57:57.027230+00:00已完成37/198、0timeout、32active；中途计分不当作正式分数。

精度进行中只做CPU工程准备：当前hostAPI434959/ns952702、EngineCore435364/ns952973、TP435799/800对应ns953241/2、birth491061978；新P1K milestone plan与comparison已冻结、nativeCLI dryrun返回0，未发任何性能请求。observer/clientidentity/controller待精度gate后补齐。

2026-10-14T14:37:35Z只读监控：同UUID/controller仍运行，已135/198、0timeout、32active/0waiting，无原生results或run-record。此为中途进度，不签gate或开始性能流量。

纯CPU客户端身份wrapper已保存，SHA318c175d3c0cb5df9226698fdca7de887af5738251e4ca4b0471cb696c82e9d5；6项协议检查通过（exec保持PID/birth/timeNS、重复身份与四类drift拒绝）。验证使用占位脚本，未导入vLLM、0模型请求/0GPUquery，不能当作真实performance通过。真实contract/observerconfig/controller待新gate后fresh绑定。

2026-10-14T15:05:28Z同UUID已197/198、0timeout、1active/0waiting，controller仍运行，无正式results/run-record。已保存新终态校验脚本commands/validate-gdn-g64k-terminal-20261014.py SHA77495c139c8b1eb59b12ade3233813f702c736dab8aa427e440adbbd4d1ae472，未执行。它先核精确controller退出/APIidle、当前实例/源码/权重/镜像挂载与frozen-config，只有真实完整native run-record才运行原生acceptance issue/check；不重放创建脚本、不发送生成请求。graph直接replay计数仍unknown。

2026-10-14正式终态：本次新UUID f8675c1380524ff396d0b07bac65fd26全部198唯一题/全部冻结filter与来源配置由原生wrapper/acceptance验证，strict-match164/198=82.8283%>=80，0timeout。当前GDN服务源码四repo12252、权重、launch args/selectedenv、精确PID/birth/boot、镜像和规范化挂载连续性通过。新schema3 gate accuracy/gdn-current-g64k-accuracy-gate-20261014.json SHA6852c4ed948413acbfe8d1594a8fce04959114aff5cfa17c028f19be50b6dac0原生issue/check均通过，非旧分数rebind。与历史anchor恰好同分不说明逐题结果相同或证明性能收益。直接graph replay count仍unknown。

终态v1在raw mount数组比较处AssertionError，未写continuity/gate；保留失败日志。聚焦inspect两容器镜像与挂载属性相同，v2采用项目verify-container-mounts原生normalize完整属性比较，通过后签gate；没有修改旧manifest/hash或弱化source/sample门禁。v2 SHA64a45079bef0e4d03bdd9b0419f4c3bbb41ce3aaa1d389bfad0f8fd0afd36842、normalizer SHA32adacf39859e88ad6e2dad04ada248a00b636c795fed67d34328f5264bec3e3。
