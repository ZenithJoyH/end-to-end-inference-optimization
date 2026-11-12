# 20261105-qwen3vl-opt16-hot1k-mx59-001 / baseline

<!-- e2e:summary:start -->

- 案例：20261105-qwen3vl-opt16-hot1k-mx59-001
- 当前状态：completed
- 当前候选：old filter on current stack
- 下一步：BoundedP1K baseline and revert verified; no further run

| 实验 | 状态/决定 | 场景 | 文档 |
|---|---|---|---|

| 场景 | 角色 | 指标 | 数值 | 单位 | 范围 |
|---|---|---|---|---|---|
| p1024-d1024-c64-n128 | old1 | total_token_throughput | 3045.655713892056 | token/s | targeted/performance_only; median of all3 admitted measured rounds |
| p1024-d1024-c64-n128 | old1 | output_throughput | 1522.827856946028 | token/s | targeted/performance_only; median of all3 admitted measured rounds |
| p1024-d1024-c64-n128 | old1 | mean_ttft_ms | 1711.7291839749669 | ms | targeted/performance_only; median of all3 admitted measured rounds |
| p1024-d1024-c64-n128 | old1 | mean_tpot_ms | 40.33835395749961 | ms | targeted/performance_only; median of all3 admitted measured rounds |
| p1024-d1024-c64-n128 | old1 | median_itl_ms | 38.72897243127227 | ms | targeted/performance_only; median of all3 admitted measured rounds |
| p1024-d1024-c64-n128 | old1 | duration_s | 86.0714488523081 | s | targeted/performance_only; median of all3 admitted measured rounds |
| p1024-d1024-c64-n128 | old1 | measured_relative_spread | 0.01246441234407402 | fraction | all3 admitted measured rounds |
| p1024-d1024-c64-n128 | old2 | total_token_throughput | 3071.2508575976603 | token/s | targeted/performance_only; median of all3 admitted measured rounds |
| p1024-d1024-c64-n128 | old2 | output_throughput | 1535.6254287988302 | token/s | targeted/performance_only; median of all3 admitted measured rounds |
| p1024-d1024-c64-n128 | old2 | mean_ttft_ms | 1717.201819876209 | ms | targeted/performance_only; median of all3 admitted measured rounds |
| p1024-d1024-c64-n128 | old2 | mean_tpot_ms | 39.98198072114471 | ms | targeted/performance_only; median of all3 admitted measured rounds |
| p1024-d1024-c64-n128 | old2 | median_itl_ms | 38.4520054794848 | ms | targeted/performance_only; median of all3 admitted measured rounds |
| p1024-d1024-c64-n128 | old2 | duration_s | 85.354147920385 | s | targeted/performance_only; median of all3 admitted measured rounds |
| p1024-d1024-c64-n128 | old2 | measured_relative_spread | 0.011205468247665796 | fraction | all3 admitted measured rounds |

<!-- e2e:summary:end -->

| 角色 | 全部3轮总TPS token/s | 中位数 | 组内差幅 | meanTTFT代理 ms | meanTPOT代理 ms | medianITL代理 ms |
|---|---|---:|---:|---:|---:|---:|
| 旧过滤路径 old1 | 3037.84, 3075.80, 3045.66 | 3045.66 | 1.246% | 1711.729 | 40.338 | 38.729 |
| 当前 PR1069 | 3046.84, 3086.50, 3030.17 | 3046.84 | 1.849% | 1723.277 | 40.277 | 38.700 |
| 回切旧过滤 old2 | 3071.25, 3082.82, 3048.41 | 3071.25 | 1.121% | 1717.202 | 39.982 | 38.452 |

当前对首旧+0.04%，回切漂移+0.84%；9计时轮128/128成功、缓存增量0。仅当前公共栈切采样路径的P1K诊断，不是全opt15镜像对照或正式验收。
