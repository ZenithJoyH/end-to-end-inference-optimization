# 20261013-qwen3vl-metax-flaggems-e2e-opt1 / optimize

<!-- e2e:summary:start -->

- 案例：20261013-qwen3vl-metax-flaggems-e2e-opt1
- 当前状态：resumed-new-linked-p64k-case
- 当前候选：op002 current MoE JSON + op005 sort int32 in qwen3vl-flaggems-e2e-20261013
- 下一步：Explicit user resume prioritizes P64K; linked new case 20261015-qwen3vl-metax-p64k-opt3; user source protected.

| 实验 | 状态/决定 | 场景 | 文档 |
|---|---|---|---|
| op-001-flaggems-baseline-profile | diagnosis-complete | p1024-d1024-c64-n128 | [op-001-flaggems-baseline-profile.md](op-001-flaggems-baseline-profile.md) |
| op-002-metax-moe-decode-stages | retained-private-json-user-restarted | p1024-d1024-c64-n128 | [op-002-metax-moe-decode-stages.md](op-002-metax-moe-decode-stages.md) |
| diag-001-p1k-stability-recovery | diagnosis-complete-routed-to-aten-isolation | p1024-d1024-c64-n128 | [diag-001-p1k-stability-recovery.md](diag-001-p1k-stability-recovery.md) |
| diag-002-aten-copy-cumsum-isolation | completed-negative-blacklist-reverted | p1024-d1024-c64-n128 | [diag-002-aten-copy-cumsum-isolation.md](diag-002-aten-copy-cumsum-isolation.md) |
| op-003-metax-moe-decode-tiling | not-retained | p1024-d1024-c64-n128 | [op-003-metax-moe-decode-tiling.md](op-003-metax-moe-decode-tiling.md) |
| op-004-metax-moe-prefill-tiling | not-retained | p1024-d1024-c64-n128 | [op-004-metax-moe-prefill-tiling.md](op-004-metax-moe-prefill-tiling.md) |
| op-005-flaggems-sort-sampling | retained | p1024-d1024-c64-n128 | [op-005-flaggems-sort-sampling.md](op-005-flaggems-sort-sampling.md) |

| 场景 | 角色 | 指标 | 数值 | 单位 | 范围 |
|---|---|---|---|---|---|
| p1024-d256-c64-n128-sampling | baseline | output_throughput | 977.8944082636442 | token/s | D256 milestone performance_only; not original D1024/four-scene acceptance |
| p1024-d256-c64-n128-sampling | candidate | output_throughput | 1127.8540341408989 | token/s | D256 milestone performance_only; not original D1024/four-scene acceptance |
| p1024-d256-c64-n128-sampling | revert | output_throughput | 976.9091213143791 | token/s | D256 milestone performance_only; not original D1024/four-scene acceptance |
| p1024-d256-c64-n128-sampling | baseline | p99_ttft_ms | 3750.2232788782567 | ms | D256 milestone performance_only; not original D1024/four-scene acceptance |
| p1024-d256-c64-n128-sampling | candidate | p99_ttft_ms | 3663.7600694969296 | ms | D256 milestone performance_only; not original D1024/four-scene acceptance |
| p1024-d256-c64-n128-sampling | revert | p99_ttft_ms | 3710.069257952273 | ms | D256 milestone performance_only; not original D1024/four-scene acceptance |
| p1024-d256-c64-n128-sampling | baseline | p99_tpot_ms | 63.411635457958084 | ms | D256 milestone performance_only; not original D1024/four-scene acceptance |
| p1024-d256-c64-n128-sampling | candidate | p99_tpot_ms | 54.84846783082421 | ms | D256 milestone performance_only; not original D1024/four-scene acceptance |
| p1024-d256-c64-n128-sampling | revert | p99_tpot_ms | 63.459185571793256 | ms | D256 milestone performance_only; not original D1024/four-scene acceptance |
| p1024-d256-c64-n128-sampling | baseline | p99_itl_ms | 443.4572266507894 | ms | D256 milestone performance_only; not original D1024/four-scene acceptance |
| p1024-d256-c64-n128-sampling | candidate | p99_itl_ms | 433.17675712518405 | ms | D256 milestone performance_only; not original D1024/four-scene acceptance |
| p1024-d256-c64-n128-sampling | revert | p99_itl_ms | 440.8864412643016 | ms | D256 milestone performance_only; not original D1024/four-scene acceptance |
| p1024-d1024-c64-n128 | baseline | output_throughput | 1133.5905555746235 | token/s | original P1K sampled performance_only; no four-scene/model-accuracy acceptance |
| p1024-d1024-c64-n128 | candidate | output_throughput | 1357.264823678639 | token/s | original P1K sampled performance_only; no four-scene/model-accuracy acceptance |
| p1024-d1024-c64-n128 | revert | output_throughput | 1130.6226228489777 | token/s | original P1K sampled performance_only; no four-scene/model-accuracy acceptance |
| p1024-d1024-c64-n128 | baseline | p99_ttft_ms | 3705.6466626096517 | ms | original P1K sampled performance_only; no four-scene/model-accuracy acceptance |
| p1024-d1024-c64-n128 | candidate | p99_ttft_ms | 3660.705538596958 | ms | original P1K sampled performance_only; no four-scene/model-accuracy acceptance |
| p1024-d1024-c64-n128 | revert | p99_ttft_ms | 3716.9909833092242 | ms | original P1K sampled performance_only; no four-scene/model-accuracy acceptance |
| p1024-d1024-c64-n128 | baseline | p99_tpot_ms | 56.08798338772177 | ms | original P1K sampled performance_only; no four-scene/model-accuracy acceptance |
| p1024-d1024-c64-n128 | candidate | p99_tpot_ms | 46.819179621402206 | ms | original P1K sampled performance_only; no four-scene/model-accuracy acceptance |
| p1024-d1024-c64-n128 | revert | p99_tpot_ms | 56.59023725873775 | ms | original P1K sampled performance_only; no four-scene/model-accuracy acceptance |
| p1024-d1024-c64-n128 | baseline | p99_itl_ms | 56.57907929271458 | ms | original P1K sampled performance_only; no four-scene/model-accuracy acceptance |
| p1024-d1024-c64-n128 | candidate | p99_itl_ms | 47.40343833342194 | ms | original P1K sampled performance_only; no four-scene/model-accuracy acceptance |
| p1024-d1024-c64-n128 | revert | p99_itl_ms | 56.95300864055751 | ms | original P1K sampled performance_only; no four-scene/model-accuracy acceptance |

<!-- e2e:summary:end -->
