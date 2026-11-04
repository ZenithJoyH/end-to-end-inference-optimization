# 20261021-topk-sigmoid-tp8-accuracy / optimize


用户重启的MiniMax-M3.1-new2/8035本轮acc-007三项全量精度已完成：GPQA167/198=84.34%（81%门槛及原生gate复验通过），Math500464/500=92.80%，ERQA259/400=64.75%（后两项无指定阈值）。保留用户开启的prefix cache；该次监控已删除；用户随后切换原容器完成C64重测，原new2评测实例已退出；如今用户已在最新容器重启MiniMax-M3.1-new-new，当前单题核验见diag-010。详见[acc-007](acc-007.md)。下表以acc-007标明新结果；acc-001分数与perf-002 micro均保留为独立历史，未启动新性能测试。

精度对照[diag-008](diag-008.md)：已核验旧档86.36%/92.20%与new2逐题对照完成；用户补充的最高GPQA89.90%/Math93.80%/ERQA66.25%、32768上下文属于另一待定位轮次。用户已要求直接在原容器按根脚本启动、64并发重测；新案例20261022-old-container-c64-accuracy正推进服务切换，历史分数保留。

最新性能归档对照见[perf-009](perf-009.md)：new2相对旧Flash `MiniMax-M3.1-new` 的4K/16K/32K总吞吐分别+0.91%/+0.82%/+0.86%，仅小幅观察。历史汇总为第2/3轮均值，缺逐轮服务身份、缓存命中/稳态及独立重复，不能确认稳定代码收益；未启动新压测。

当前用户已在最新容器重启 `MiniMax-M3.1-new-new/8035`。用户旧GPQA文件只有一题；[diag-010](diag-010.md)按可见旧配置95109/T1/.95复现，输入395、生成1335 tokens，原生strict-match1.0，与旧文件同题一致。此前完整评测上限18000，预算不一致；本轮不产生全量分数或新gate。首个封装错误探针保留并排除，修正后结果独立归档。

用户又将同一路径更新为完整198题文件，[diag-011](diag-011.md)已原生离线复核strict-match180/198=90.91%。其生成上限95109，近期new2和旧C64全量均18000且167/198；new2少掉13题中11题触顶、10题在旧记录生成超过18k。题目/实际prompt/target全部198一致；预算是优先差异，但根因尚未单变量确认。零新增模型请求，没有把历史180绑定为当前服务新成绩。原始完整文件未上传远端，仅归档安全汇总。

已按用户授权提交当前Plugin适配：[官方PR #634](https://github.com/flagos-ai/vllm-plugin-FL/pull/634)，23文件，合并官方main新增Ascend注册后119项CPU合同与10项隔离元数据测试通过；初始CI测试前提问题已修复，提交92682e3已推送同一PR，新CI正在复验；仅改5测试文件，23项隔离逻辑与样式检查通过。完整状态见[pr-012](pr-012.md)。截至20:19五平台functional及静态/安全检查通过，其余functional/E2E仍运行或排队，尚未全绿。运行容器源码/服务未改，无新模型评测或性能收益声明。

<!-- e2e:summary:start -->

- 案例：20261021-topk-sigmoid-tp8-accuracy
- 当前状态：latest-user-restarted-service-single-sample-diagnosed
- 当前候选：user-MiniMax-M3.1-new-new-restarted
- 下一步：User historical complete file is180/198 at95109; recent new2/oldC64 are167/198 at18000. Budget is leading confirmed config difference; no new full inference or gate. Same-config95109 C64 GPQA would be next controlled measurement if requested.

| 实验 | 状态/决定 | 场景 | 文档 |
|---|---|---|---|
| acc-001 | all_three_complete_verified | — | [acc-001.md](acc-001.md) |
| perf-002 | retain installed split bridge; full API not selected; no model E2E A/B or new model gate claimed | moe-full-vs-split-micro | [perf-002.md](perf-002.md) |
| op-003 | revert op003 at user request; retain pre-experiment topk-sigmoid container version | — | [op-003.md](op-003.md) |
| review-004 | completed_installed_and_verified | — | [review-004.md](review-004.md) |
| review-005 | retain scoped Plugin refactor; keep current model process running | — | [review-005.md](review-005.md) |
| diag-006 | root-cause-confirmed-config-recovery-not-started | — | [diag-006.md](diag-006.md) |
| acc-007 | all_three_complete_verified | — | [acc-007.md](acc-007.md) |
| diag-008 | existing_comparison_complete_user_requests_old_container_c64_rerun | — | [diag-008.md](diag-008.md) |
| perf-009 | historical_archive_comparison_complete_formal_evidence_incomplete | — | [perf-009.md](perf-009.md) |
| diag-010 | single_sample_native_comparison_complete_no_regression_demonstrated | — | [diag-010.md](diag-010.md) |
| diag-011 | full_comparison_complete_budget_difference_confirmed_causality_unconfirmed | — | [diag-011.md](diag-011.md) |
| pr-012 | upstream_pr_main_merged_conflicts_resolved_ci_pending | — | [pr-012.md](pr-012.md) |

| 场景 | 角色 | 指标 | 数值 | 单位 | 范围 |
|---|---|---|---|---|---|
| gpqa | candidate | exact_match,strict-match | 84.34343434343434 | % | acc-007 new2 full 167/198 actual unique questions; native score |
| math500 | candidate | exact_match,none | 92.80000000000001 | % | acc-007 new2 full 464/500 actual unique questions; native score |
| erqa | candidate | accuracy | 64.75 | % | acc-007 new2 full 259/400 actual unique questions; native score |
| gpqa | candidate | exact_match,strict-match | 84.34343434343434 | % | acc-001 historical; full 167/198 actual unique questions; native score |
| math500 | candidate | exact_match,none | 93.4 | % | acc-001 historical; full 467/500 actual unique questions; native score |
| erqa | candidate | accuracy | 66.75 | % | acc-001 historical; full 267/400 actual unique questions; native score |
| moe-m1-balanced | split | full_call_graph_latency | 39.35420036315918 | us | perf-002 as-installed operator micro;2 independent processes, per-process median then median;not model throughput |
| moe-m1-balanced | full | full_call_graph_latency | 56.05219841003418 | us | perf-002 as-installed operator micro;2 independent processes, per-process median then median;not model throughput |
| moe-m1-balanced | split_revert | full_call_graph_latency | 39.38700079917908 | us | perf-002 as-installed operator micro;2 independent processes, per-process median then median;not model throughput |
| moe-m1-concentrated16 | split | full_call_graph_latency | 39.380000829696655 | us | perf-002 as-installed operator micro;2 independent processes, per-process median then median;not model throughput |
| moe-m1-concentrated16 | full | full_call_graph_latency | 56.157801151275635 | us | perf-002 as-installed operator micro;2 independent processes, per-process median then median;not model throughput |
| moe-m1-concentrated16 | split_revert | full_call_graph_latency | 39.36079978942871 | us | perf-002 as-installed operator micro;2 independent processes, per-process median then median;not model throughput |
| moe-m8-balanced | split | full_call_graph_latency | 202.27459907531738 | us | perf-002 as-installed operator micro;2 independent processes, per-process median then median;not model throughput |
| moe-m8-balanced | full | full_call_graph_latency | 214.5777988433838 | us | perf-002 as-installed operator micro;2 independent processes, per-process median then median;not model throughput |
| moe-m8-balanced | split_revert | full_call_graph_latency | 202.1988010406494 | us | perf-002 as-installed operator micro;2 independent processes, per-process median then median;not model throughput |
| moe-m8-concentrated16 | split | full_call_graph_latency | 132.4590015411377 | us | perf-002 as-installed operator micro;2 independent processes, per-process median then median;not model throughput |
| moe-m8-concentrated16 | full | full_call_graph_latency | 132.92960166931152 | us | perf-002 as-installed operator micro;2 independent processes, per-process median then median;not model throughput |
| moe-m8-concentrated16 | split_revert | full_call_graph_latency | 132.4597978591919 | us | perf-002 as-installed operator micro;2 independent processes, per-process median then median;not model throughput |
| moe-m16-balanced | split | full_call_graph_latency | 350.9554100036621 | us | perf-002 as-installed operator micro;2 independent processes, per-process median then median;not model throughput |
| moe-m16-balanced | full | full_call_graph_latency | 390.0152015686035 | us | perf-002 as-installed operator micro;2 independent processes, per-process median then median;not model throughput |
| moe-m16-balanced | split_revert | full_call_graph_latency | 350.7232093811035 | us | perf-002 as-installed operator micro;2 independent processes, per-process median then median;not model throughput |
| moe-m16-concentrated16 | split | full_call_graph_latency | 142.08940029144287 | us | perf-002 as-installed operator micro;2 independent processes, per-process median then median;not model throughput |
| moe-m16-concentrated16 | full | full_call_graph_latency | 134.8203992843628 | us | perf-002 as-installed operator micro;2 independent processes, per-process median then median;not model throughput |
| moe-m16-concentrated16 | split_revert | full_call_graph_latency | 142.08380222320557 | us | perf-002 as-installed operator micro;2 independent processes, per-process median then median;not model throughput |
| moe-m32-balanced | split | full_call_graph_latency | 676.3166046142578 | us | perf-002 as-installed operator micro;2 independent processes, per-process median then median;not model throughput |
| moe-m32-balanced | full | full_call_graph_latency | 742.8544235229492 | us | perf-002 as-installed operator micro;2 independent processes, per-process median then median;not model throughput |
| moe-m32-balanced | split_revert | full_call_graph_latency | 674.8538208007812 | us | perf-002 as-installed operator micro;2 independent processes, per-process median then median;not model throughput |
| moe-m32-concentrated16 | split | full_call_graph_latency | 161.32320404052734 | us | perf-002 as-installed operator micro;2 independent processes, per-process median then median;not model throughput |
| moe-m32-concentrated16 | full | full_call_graph_latency | 143.36259841918945 | us | perf-002 as-installed operator micro;2 independent processes, per-process median then median;not model throughput |
| moe-m32-concentrated16 | split_revert | full_call_graph_latency | 161.37160301208496 | us | perf-002 as-installed operator micro;2 independent processes, per-process median then median;not model throughput |
| moe-m64-balanced | split | full_call_graph_latency | 664.9108123779297 | us | perf-002 as-installed operator micro;2 independent processes, per-process median then median;not model throughput |
| moe-m64-balanced | full | full_call_graph_latency | 666.7319869995117 | us | perf-002 as-installed operator micro;2 independent processes, per-process median then median;not model throughput |
| moe-m64-balanced | split_revert | full_call_graph_latency | 664.82421875 | us | perf-002 as-installed operator micro;2 independent processes, per-process median then median;not model throughput |
| moe-m64-concentrated16 | split | full_call_graph_latency | 144.81120109558105 | us | perf-002 as-installed operator micro;2 independent processes, per-process median then median;not model throughput |
| moe-m64-concentrated16 | full | full_call_graph_latency | 146.53319835662842 | us | perf-002 as-installed operator micro;2 independent processes, per-process median then median;not model throughput |
| moe-m64-concentrated16 | split_revert | full_call_graph_latency | 144.77959632873535 | us | perf-002 as-installed operator micro;2 independent processes, per-process median then median;not model throughput |
| moe-m1024-balanced | split | full_call_graph_latency | 1725.6322479248047 | us | perf-002 as-installed operator micro;2 independent processes, per-process median then median;not model throughput |
| moe-m1024-balanced | full | full_call_graph_latency | 1726.8775939941406 | us | perf-002 as-installed operator micro;2 independent processes, per-process median then median;not model throughput |
| moe-m1024-balanced | split_revert | full_call_graph_latency | 1725.7429504394531 | us | perf-002 as-installed operator micro;2 independent processes, per-process median then median;not model throughput |
| moe-m1024-concentrated16 | split | full_call_graph_latency | 547.8420066833496 | us | perf-002 as-installed operator micro;2 independent processes, per-process median then median;not model throughput |
| moe-m1024-concentrated16 | full | full_call_graph_latency | 551.0029983520508 | us | perf-002 as-installed operator micro;2 independent processes, per-process median then median;not model throughput |
| moe-m1024-concentrated16 | split_revert | full_call_graph_latency | 548.0560111999512 | us | perf-002 as-installed operator micro;2 independent processes, per-process median then median;not model throughput |
| moe-m8192-balanced | split | full_call_graph_latency | 3881.9566345214844 | us | perf-002 as-installed operator micro;2 independent processes, per-process median then median;not model throughput |
| moe-m8192-balanced | full | full_call_graph_latency | 3884.222412109375 | us | perf-002 as-installed operator micro;2 independent processes, per-process median then median;not model throughput |
| moe-m8192-balanced | split_revert | full_call_graph_latency | 3883.358612060547 | us | perf-002 as-installed operator micro;2 independent processes, per-process median then median;not model throughput |
| moe-m8192-concentrated16 | split | full_call_graph_latency | 3885.6101989746094 | us | perf-002 as-installed operator micro;2 independent processes, per-process median then median;not model throughput |
| moe-m8192-concentrated16 | full | full_call_graph_latency | 3886.016082763672 | us | perf-002 as-installed operator micro;2 independent processes, per-process median then median;not model throughput |
| moe-m8192-concentrated16 | split_revert | full_call_graph_latency | 3885.1443481445312 | us | perf-002 as-installed operator micro;2 independent processes, per-process median then median;not model throughput |

<!-- e2e:summary:end -->

PR #634 terminal CI review: 42 success / 6 skipped / 5 failure including gate. Three dependency-fetch network failures and T-Head KV admission with external device occupation remain. PR description updated. CLI and GitHub integration lack official Actions rerun permission; administrator retry required. CI is not green. No running container accessed or modified. See pr-012.

PR #634 merged latest main aae3c1c and resolved both MoE conflicts in1172e4b. Title now states T-Head MiniMax-M3.1 W8A8 inference.67 dependency-isolated checks and static checks passed; new CI pending. Running container untouched. See pr-012.
