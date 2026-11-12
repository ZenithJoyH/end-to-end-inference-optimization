# 20261104-qwen36-mx59-main-config-001 / optimize

<!-- e2e:summary:start -->

- 案例：20261104-qwen36-mx59-main-config-001
- 当前状态：PR1069 head039f03ed的采样实现及Plugin公开接口适配已应用到mx-59/qwen36-35b磁盘，CPU真实导入/分发与fallback检查通过。当前用户服务及64K压测未重启；新代码GPU/graph/模型精度未测，待用户重启后生效。旧GPQA176当前strict/165历史strict及ERQA245/400仅保留原实例结论。
- 当前候选：main-profile016dac84-on-image-c467
- 下一步：用户结束当前压测并重启服务后可使用新算子；本次未发模型请求或GPU测试，不自动复用旧gate。

| 实验 | 状态/决定 | 场景 | 文档 |
|---|---|---|---|
| clone-image-issues-20261111-001 | 指定镜像8个独立进程确认CPU clone guard故障；topk性能Issue #8959及clone #8566补充证据均已发布，Excel链接已回填 | clone/topk问题反馈 | [clone-image-issues-20261111-001.md](clone-image-issues-20261111-001.md) |
| topk-softmax-image-20261111-001 | 指定202611091810镜像独立组件：22数值+2 graph replay通过；M8192较原生慢29.4%，M64快21.1%。未改源/服务，非E2E或历史黑名单因果 | MoE路由 | [topk-softmax-image-20261111-001.md](topk-softmax-image-20261111-001.md) |
| sampler-pr1069-align-20261106-001 | PR1069原始实现+最小接线已部署；CPU import通过，GPU/graph/E2E未运行，待重启 | 采样API | [sampler-pr1069-align-20261106-001.md](sampler-pr1069-align-20261106-001.md) |
| fgv-moe-main-config-001 | Keep pre-experiment new profile and exact launch; no >=3% regression reproduced, operator micro trigger not met; large cold-shape JIT contamination confirmed. No additional code optimization. | — | [fgv-moe-main-config-001.md](fgv-moe-main-config-001.md) |
| fgv-gdn-cleanup-001 | Reverted only unused FGV GDN local fixed-config/prune/logging to tracked HEAD; preserve Plugin GDN/MoE/sampler; no benchmark or model gate | — | [fgv-gdn-cleanup-001.md](fgv-gdn-cleanup-001.md) |

| 场景 | 角色 | 指标 | 数值 | 单位 | 范围 |
|---|---|---|---|---|---|
| p1024-d1024-c64-n128 | historical_mx104_retest | total_token_throughput_all3_arithmetic_mean | 2777.65 | tok/s | cross_host_user_observation_no_causal_gain; unstable_short_context |
| p1024-d1024-c64-n128 | user_mx59_opt5 | total_token_throughput_all3_arithmetic_mean | 2156.9267 | tok/s | cross_host_user_observation_no_causal_gain; unstable_short_context |
| p4096-d1024-c64-n128 | historical_mx104_retest | total_token_throughput_all3_arithmetic_mean | 4358.46 | tok/s | cross_host_user_observation_no_causal_gain; unstable_short_context |
| p4096-d1024-c64-n128 | user_mx59_opt5 | total_token_throughput_all3_arithmetic_mean | 5211.5033 | tok/s | cross_host_user_observation_no_causal_gain; unstable_short_context |
| p32768-d1024-c64-n128 | historical_mx104_retest | total_token_throughput_all3_arithmetic_mean | 10920.0133 | tok/s | cross_host_user_observation_no_causal_gain; stable_long_context |
| p32768-d1024-c64-n128 | user_mx59_opt5 | total_token_throughput_all3_arithmetic_mean | 10901.2 | tok/s | cross_host_user_observation_no_causal_gain; stable_long_context |
| p65536-d1024-c64-n128 | historical_mx104_retest | total_token_throughput_all3_arithmetic_mean | 9463.4433 | tok/s | cross_host_user_observation_no_causal_gain; stable_long_context |
| p65536-d1024-c64-n128 | user_mx59_opt5 | total_token_throughput_all3_arithmetic_mean | 9383.4733 | tok/s | cross_host_user_observation_no_causal_gain; stable_long_context |
| p1024-d1024-c64-n128 | controlled_mx59_old1 | total_token_throughput_measured3_median | 2907.060559418215 | tok/s | same_host_targeted_performance_only; 1 service per role, 3 measured rounds; not formal acceptance |
| p1024-d1024-c64-n128 | controlled_mx59_new | total_token_throughput_measured3_median | 2982.5798748912484 | tok/s | same_host_targeted_performance_only; 1 service per role, 3 measured rounds; not formal acceptance |
| p1024-d1024-c64-n128 | controlled_mx59_old2 | total_token_throughput_measured3_median | 2892.5560312383573 | tok/s | same_host_targeted_performance_only; 1 service per role, 3 measured rounds; not formal acceptance |

<!-- e2e:summary:end -->

- [plugin-gdn-lazy-pr-001](plugin-gdn-lazy-pr-001.md)：GDN 延迟注册的 [PR #699](https://github.com/flagos-ai/vllm-plugin-FL/pull/699) 已按用户要求于2026-11-06关闭、未合并。正常 CLI/当前服务不依赖此补丁；保留特定导入顺序问题的证据、分支与讨论，未改服务或 #702。

- PR #699 已按用户纠正改为 `release/0.2`（vLLM 0.20.2），真实依赖已复现原 GDN 循环并验证延迟后该路径恢复；独立采样循环不在该 PR 范围。

- [用户新容器成功路径核对](gdn-user-container-audit-20261106-001.md)：mx-59/vllm0202-fl-release02-20261106 的干净 release 基线正常 CLI 初始化且 GDN 注册成功；同容器新解释器先导入 layernorm/sampler 则出现循环警告、入口结束时 GDN 未注册。#699 是导入顺序相关修复，不是正常 CLI 必现启动故障；源码和服务保持不变。

- [plugin-kv-budget-pr-001](plugin-kv-budget-pr-001.md)：[PR #702](https://github.com/flagos-ai/vllm-plugin-FL/pull/702) 已于2026-11-06按用户要求关闭、未合并。回退后ERQA C64完成245/400、无请求失败/超时且未观察到OOM，修复必要性与纯KV因果尚未建立；保留分支、补丁、15项CPU测试及全部验证记录。

- PR #702 follow-up42b27b3: post-warmup requested-limit hint now includes initial occupancy; initial-free-memory hint and increment bookkeeping preserved. 15 CPU tests passed; no deployment/GPU-model changes.

- [cross-platform-pr-audit-001](cross-platform-pr-audit-001.md)：对 #699/#702 的 release/0.2 基线完成其他平台源码审计。22个 Worker 分支调用、18个 warmup 提示夹具、3个导入失败注入通过；多个通用平台及 Sunrise 的 KV 公式仍遗漏初始占用，MUSA/GCU/Sunrise 存在局部导入失败后不再重试的控制流。Ascend/TXDA 分支单列；未实测其他设备 OOM 或真实循环导入，未修改 PR/服务。

- PR702@42b27b3 applied to mx-59/qwen36-35b private Plugin: exactly3 files,15 CPU tests passed, other6514 source records unchanged. Running service preserved without restart/reload; new startup hint applies next launch. See [deployment record](plugin-kv-budget-pr-001.md).



- [user-gpqa-erqa-c64-20261105-001](user-gpqa-erqa-c64-20261105-001.md)：沐曦59 opt6、原GPU4/5/0.9/prefix-on，各C64串行的一次评测尝试已结束。GPQA全198/396独立核验：本次预冻结原生168/198（84.8485%），同批回答按历史strict离线复算160/198（80.8081%）；8题来自提取规则差异，gate仅绑定本次冻结规则。ERQA仅364成功、29原生超时、7未提交；已完成部分201/364（55.2198%）不等于全400精度，全量分数不可用。32条输出用满65536token且无最终答案，按原规则计错。真实partial、所有旧错误完整保留，0新生成独立审计通过；原客户端退出，服务队列观察0/0，源码和启动配置保持。停滞机制未确认，不能据此断言OOM或64并发绝对容量。未补跑、未签ERQA gate、无四场景E2E验收；终态审计后删除本轮监控。详见ROOT/terminal-review-001.json（SHA eb23ddad39d8602ebe13519800dcd3365d3176b64cd5c9dd0525ee3ddb0a230d）。

- [erqa-unsubmitted7-20261105-001](erqa-unsubmitted7-20261105-001.md): user requested only previously unsubmitted393..399;7HTTP200/no newfailure,4correct. Combined205correct/371successful responses=55.2561%; original29timeouts countedzero gives diagnostic205/400=51.25%. Two-phase supplement, not native single-run full400; old29 never retried, originalpartial/source/config untouched. Independent06edccb622734781e44392103150ed36f1a7dd56edab8f76492bb1c6a5d36873, summary3c3f8d304f707d894bb54d66fe06f39358fd849330a3770713a018ce3c07f3de. Supplement monitor deleted after completion.

- [erqa-timeout29-20261105-001](erqa-timeout29-20261105-001.md)：用户授权的原29道超时题已各重跑一次，29题全部返回、5题正确、0请求失败；其中18题输出达到65536 token仍无最终答案，按原规则计错。与已有371题/205正确合并，400题合计210正确（52.50%）。这是三阶段汇总；原371题未重跑，原超时记录保留，服务参数和源码未改。独立报告112c2e43dca4508953641d899910449cf510ea06da2ad83241a1b6ed90428a84、终态复核dcb8dc4eb1d5ef49291fc84e840e6696ae2d410717ac5816882d2fc7c7a7f753均通过。监控已删除；无单轮全新C64评测或新gate声明。

ERQA timeout29 retry heartbeat (2026-11-05T14:51Z): 11/29 completed,0failed; remaining18 scheduler-running,0waiting; exact service/client/source guard passed. No final29/400 score yet; existing monitor retained. Evidence and immutable scope: [erqa-timeout29-20261105-001](erqa-timeout29-20261105-001.md).

- [erqa-quality-20261105-001](erqa-quality-20261105-001.md)：零生成离线核验400题：210正确、140正常单字母选错、50条65536 token思考截断无final；当前无额外格式误判，解析器未漏掉已生成的final。49/50截断有长句反复出现，触发机制待隔离。历史思考59/72（81.94%）只是失败轮成功子集；当前同72题58/72（80.56%），不能把它与全400分数直接当作精度大幅回退。已知旧完整非思考190/400（47.50%），当前三阶段210/400（52.50%）。temperature0+思考循环为首要协议假设，MoE/GDN/视觉数值回退未确认；未改分、未重跑或重启，GPQA gate保持。最终离线报告SHA d5be21a43d9f9133cbf7a8b62c69fbb3c99f58b4c2a6fb20385bf19458be319e。

- [erqa-default-sampling-c64-20261106-001](erqa-default-sampling-c64-20261106-001.md)：按用户新指令，以模型generation_config默认temperature1/top_p.95/top_k20、thinkingTrue/max65536/C64重新完整评测官方400题；不添加presence_penalty1.5推荐预设。当前opt6同API661469和完整源码/参数未改，400份图文/请求已冻结e2a72f9f，已实际发送模型流量。startobserver5c05d8a3确认新wire参数及66send/2completed/0failed仅为启动快照。控制器516508、Eworker6987及独立核验入口唯一；禁止重放已启动工具或旧模型请求，旧210/400保持独立。半小时监控qwen35-mx59-erqa-default-c64 ACTIVE，尚无本轮最终分数。

Final defaultsampling ERQA400 single-run:236/400=59.00%,400uniqueHTTP200,0requestfailures/timeouts,64clientpeak,397stop+3length65536/no-final countedwrong. Same currentservice/source/launch unchanged through terminalfresh. Versus oldgreedy three-phase210/40052.5%, observed+26correct/+6.5pp and length50->3; not a replicated causal or performance claim. Independent f54bdd59d7d9d54fd75ffe21459a4dc7fb9a2820df0fad86338cad24253a7335; terminalreview f6ef5f89dd04e584a038f33d7ecbed2a0034594664ff3d08e9760615d2ba3692; summary17cce7f189723c888960d4ecfe8aa7d92e40215e2fc98b0abfa48c618071666b. Monitor qwen35-mx59-erqa-default-c64 deleted after terminal audit; no further automatic traffic. See [current experiment](../optimize/erqa-default-sampling-c64-20261106-001.md).
- [PR702 用户容器只读核验](kv-budget-user-container-audit-20261106-001.md)：干净release/0.2未打补丁仍正常完成启动，health200；因此不是当前启动的必要补丁。源码初始non-Torch预算漏项存在，但原始快照未记录，本次未量化漏算量或复现OOM。每卡终态约94.07%占用不能独立证明漏项因果。无重启/改源/模型流量，PR保持原状。
- [GDN延迟注册回退](gdn-lazy-revert-20261106-001.md)：用户确认的mx-59/qwen36-35b已恢复原patches导入，移除ModelRunnerFL延迟导入；仅两文件修改，保留采样/MoE/KV及GDN实现。原生exit0、AST/逐字比较/diff检查通过，其他扫描4165个Python文件不变。未重启或热加载，下一次启动生效；不宣称新硬件/精度验证。
- [KV预算修正回退](kv-budget-revert-20261106-001.md)：用户要求在mx-59/qwen36-35b回退#702后自行ERQA复现。worker已恢复HEAD原计算，配套helper/test备份后移除；保留此前GDN注册回退及采样/MoE改动。原生exit0、AST/逐字/diff检查通过，其他扫描4164个Python源码不变。未重启或发评测，需下一次启动生效，未宣称OOM复现或排除。
- [KV预算回退后ERQA400](erqa-kv-revert-default-c64-20261106-001.md)：用户重启mx-59/qwen36-35b并开启prefix cache后，以默认temperature1/top_p.95/top_k20、thinkingTrue/max65536/C64启动一次官方400题。保留当前0.9/GPU4/5/TP2及全部服务参数；实际流量已发出，启动观察18完成/0失败、64running仅为当时快照，尚无最终分数或OOM结论。新进程/source绑定、每30s日志/指标及完整guard、半小时监控已就绪，不重放或补分。历史236/400与210/400独立保留。

最新终态：[KV预算回退后ERQA400](erqa-kv-revert-default-c64-20261106-001.md) 为245/400（61.25%），两题输出截断按错计入。99段连续日志与fresh身份核验通过，未观察到OOM；不构成纯KV单变量因果或普遍无OOM保证。半小时监控已删除，未自动继续评测或性能测试。

- [回退后GPQA C64新一轮](gpqa-kv-revert-c64-20261106-001.md)：已完成198题/C64：当前预冻结strict176/198（88.89%），同批历史strict165/198（83.33%），均超过75%；独立与终态复核通过，未观察到OOM，监控已删除。
