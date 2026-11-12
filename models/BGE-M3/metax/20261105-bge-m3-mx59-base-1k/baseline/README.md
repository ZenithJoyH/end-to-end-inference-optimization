# 20261105-bge-m3-mx59-base-1k / baseline

<!-- e2e:summary:start -->

- 案例：20261105-bge-m3-mx59-base-1k
- 当前状态：completed-diagnostic-steady-state-unproven
- 当前候选：—
- 下一步：Diagnose run-to-run variance before any stable image-speedup attribution

| 实验 | 状态/决定 | 场景 | 文档 |
|---|---|---|---|

| 场景 | 角色 | 指标 | 数值 | 单位 | 范围 |
|---|---|---|---|---|---|
| embedding-p1024-c64-n256 | historical-source-gpu2 | input_token_throughput | 40553.59 | token/s | historical-observation-not-paired |
| embedding-p1024-c64-n256 | historical-source-gpu2 | request_throughput | 39.6 | request/s | historical-observation-not-paired |
| embedding-p1024-c64-n256 | A-current | input_token_throughput | 45228.87656959786 | token/s | diagnostic-incomplete-steady-state |
| embedding-p1024-c64-n256 | A-current | request_throughput | 44.16882477499791 | request/s | diagnostic-incomplete-steady-state |
| embedding-p1024-c64-n256 | A-current | mean_e2el | 1121.5401278677746 | ms | diagnostic-incomplete-steady-state |
| embedding-p1024-c64-n256 | A-current | round_mean_p99_e2el | 4238.286671857348 | ms | diagnostic-incomplete-steady-state |
| embedding-p1024-c64-n256 | A2-current | input_token_throughput | 76719.80976182171 | token/s | diagnostic-incomplete-steady-state |
| embedding-p1024-c64-n256 | A2-current | request_throughput | 74.92168922052902 | request/s | diagnostic-incomplete-steady-state |
| embedding-p1024-c64-n256 | A2-current | mean_e2el | 950.7143995215301 | ms | diagnostic-incomplete-steady-state |
| embedding-p1024-c64-n256 | A2-current | round_mean_p99_e2el | 2587.6251520356163 | ms | diagnostic-incomplete-steady-state |

<!-- e2e:summary:end -->
