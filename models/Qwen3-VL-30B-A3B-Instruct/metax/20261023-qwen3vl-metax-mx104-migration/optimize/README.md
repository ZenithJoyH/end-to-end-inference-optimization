# 20261023-qwen3vl-metax-mx104-migration / optimize

<!-- e2e:summary:start -->

- 案例：20261023-qwen3vl-metax-mx104-migration
- 当前状态：pr638-only-attention-on-disk-model-service-currently-not-running
- 当前候选：Current container retained; MetaX Attention exact PR638, no explicit split1; sampling/MoE preserved
- 下一步：No automatic service start/restart. Container cleanup complete; final models9999 refused and no model process; prior split1 accuracy remains historical only.

| 实验 | 状态/决定 | 场景 | 文档 |
|---|---|---|---|
| maint-005-remove-other-qwen-vl-containers | Cleanup complete; keep qwen3vl-pr943-split1-mx104-20261023 running as container; images/volumes/host data retained; current model service absent, cause unestablished | no-model-workload | [maint-005-remove-other-qwen-vl-containers.md](maint-005-remove-other-qwen-vl-containers.md) |
| op-004-metax-fla-pr638-only | Remove explicit split1; retain exact PR638 Attention source, all other optimizations and current user service; restart needed for effective behavior | source-alignment-no-model-workload | [op-004-metax-fla-pr638-only.md](op-004-metax-fla-pr638-only.md) |
| op-003-metax-fla-pr638 | Apply PR638 head3e04e696 prefill only,preserve decode split1;running service not restarted | user-requested-code-application-no-performance-measurement | [op-003-metax-fla-pr638.md](op-003-metax-fla-pr638.md) |
| env-001-migrate-mx104 | Migration retained; exact split1/helper restored and graph16/C8 passed for correctness-preserving state. Performance tradeoff confirmed; no formal acceptance/fullP64K conclusion. Expanded diagnostic not_run. | p1024-d1024-c64-n128 | [env-001-migrate-mx104.md](env-001-migrate-mx104.md) |
| env-002-consolidate-flaggems-vllm | Canonical install retained;verified archives preserve old copies;4 retired repo dirs and old canonical temporary copy removed;service remains running split1/prefixON/4,5/18977 | same-TP2-service-minimal-regression | [env-002-consolidate-flaggems-vllm.md](env-002-consolidate-flaggems-vllm.md) |
| maint-003-current-container-zombies | Cleanup completed,no container/model restart,no live process killed,no source/environment change | no-model-workload | [maint-003-current-container-zombies.md](maint-003-current-container-zombies.md) |

| 场景 | 角色 | 指标 | 数值 | 单位 | 范围 |
|---|---|---|---|---|---|
| p1024-d1024-c64-n128 | baseline | output_throughput | 1599.3521083554203 | token/s | targeted/performance_only;median of process medians,all rounds retained |
| p1024-d1024-c64-n128 | candidate | output_throughput | 1417.5846062619453 | token/s | targeted/performance_only;median of process medians,all rounds retained |
| p1024-d1024-c64-n128 | revert | output_throughput | 1600.0968179888873 | token/s | targeted/performance_only;median of process medians,all rounds retained |
| p1024-d1024-c64-n128 | baseline | total_token_throughput | 3198.7042167108407 | token/s | targeted/performance_only;median of process medians,all rounds retained |
| p1024-d1024-c64-n128 | candidate | total_token_throughput | 2835.1692125238906 | token/s | targeted/performance_only;median of process medians,all rounds retained |
| p1024-d1024-c64-n128 | revert | total_token_throughput | 3200.1936359777746 | token/s | targeted/performance_only;median of process medians,all rounds retained |
| p1024-d1024-c64-n128 | baseline | mean_ttft_ms | 1661.4832275736262 | ms | targeted/performance_only;median of process medians,all rounds retained |
| p1024-d1024-c64-n128 | candidate | mean_ttft_ms | 1646.0114047877141 | ms | targeted/performance_only;median of process medians,all rounds retained |
| p1024-d1024-c64-n128 | revert | mean_ttft_ms | 1670.057269569952 | ms | targeted/performance_only;median of process medians,all rounds retained |
| p1024-d1024-c64-n128 | baseline | mean_tpot_ms | 38.379025382303794 | ms | targeted/performance_only;median of process medians,all rounds retained |
| p1024-d1024-c64-n128 | candidate | mean_tpot_ms | 43.49431146535767 | ms | targeted/performance_only;median of process medians,all rounds retained |
| p1024-d1024-c64-n128 | revert | mean_tpot_ms | 38.351063667619314 | ms | targeted/performance_only;median of process medians,all rounds retained |
| p65536-d128-c8-n16-kv-sentinel | baseline | output_throughput | 13.961980791378382 | token/s | targeted/performance_only;median of process medians,all rounds retained |
| p65536-d128-c8-n16-kv-sentinel | candidate | output_throughput | 8.614274666021132 | token/s | targeted/performance_only;median of process medians,all rounds retained |
| p65536-d128-c8-n16-kv-sentinel | revert | output_throughput | 13.950420416136602 | token/s | targeted/performance_only;median of process medians,all rounds retained |
| p65536-d128-c8-n16-kv-sentinel | baseline | total_token_throughput | 7162.49614597711 | token/s | targeted/performance_only;median of process medians,all rounds retained |
| p65536-d128-c8-n16-kv-sentinel | candidate | total_token_throughput | 4419.12290366884 | token/s | targeted/performance_only;median of process medians,all rounds retained |
| p65536-d128-c8-n16-kv-sentinel | revert | total_token_throughput | 7156.565673478077 | token/s | targeted/performance_only;median of process medians,all rounds retained |
| p65536-d128-c8-n16-kv-sentinel | baseline | mean_ttft_ms | 28216.505092161242 | ms | targeted/performance_only;median of process medians,all rounds retained |
| p65536-d128-c8-n16-kv-sentinel | candidate | mean_ttft_ms | 31463.16921385005 | ms | targeted/performance_only;median of process medians,all rounds retained |
| p65536-d128-c8-n16-kv-sentinel | revert | mean_ttft_ms | 28348.414716194384 | ms | targeted/performance_only;median of process medians,all rounds retained |
| p65536-d128-c8-n16-kv-sentinel | baseline | mean_tpot_ms | 353.0850218353229 | ms | targeted/performance_only;median of process medians,all rounds retained |
| p65536-d128-c8-n16-kv-sentinel | candidate | mean_tpot_ms | 654.1497922822371 | ms | targeted/performance_only;median of process medians,all rounds retained |
| p65536-d128-c8-n16-kv-sentinel | revert | mean_tpot_ms | 352.5200940386253 | ms | targeted/performance_only;median of process medians,all rounds retained |

<!-- e2e:summary:end -->
