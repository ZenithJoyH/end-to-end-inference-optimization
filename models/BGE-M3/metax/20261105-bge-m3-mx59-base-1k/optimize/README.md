# 20261105-bge-m3-mx59-base-1k / optimize

<!-- e2e:summary:start -->

- 案例：20261105-bge-m3-mx59-base-1k
- 当前状态：linear-test-ci-fix-pushed-external-network-blocker
- 当前候选：{"vllm-plugin-FL": "dafb78f8e8f3f5d4c0c2822a82aa370a8632f53b391d20e79716c64b394aae08", "FlagGems": "cb47fb279da85372c09298b49f66b8a77dc083456c07a1d660fdd062e0809f8c", "FlagGems-vllm": "34ebbd6c6b976f7ce2ce779b86c13f4c2e09752d670ca81158ef57dc648d4f2e"}
- 下一步：Maintainer restore CPU runner GitHub connectivity and rerun required rule CI; no further source changes justified; batch-budget-004 remains stopped.

| 实验 | 状态/决定 | 场景 | 文档 |
|---|---|---|---|
| image-001 | Do not switch to release as a performance improvement; observed slower but stable causal comparison not established | embedding-p1024-c64-n256 | [image-001.md](image-001.md) |
| plugin-slim-002 | retained source consolidation; fresh candidate processes validated; original live process preserved | embedding-p1024-c64-n256 | [plugin-slim-002.md](plugin-slim-002.md) |
| interface-fix-003 | applied to actual installed BGE-M3 source; all targeted tests and paired functional regression passed | embedding-p1024-c64-n256 | [interface-fix-003.md](interface-fix-003.md) |
| batch-budget-004 | Stopped at user request; preserve completed A/B diagnostic results; exclude cancelled revert group; retain default32768. | embedding-p1024-c64-n256 | [batch-budget-004.md](batch-budget-004.md) |
| fgv-review-fix-005 | applied to actual editable BGE-M3 installation after isolated regression; numerical kernels/configuration unchanged | embedding-p1024-c64-n256 | [fgv-review-fix-005.md](fgv-review-fix-005.md) |
| fg-review-fix-006 | validation gaps resolved; tests/benchmark applied to actual editable installation; no production changes | embedding-p1024-c64-n256 | [fg-review-fix-006.md](fg-review-fix-006.md) |
| operator-pr-007 | Two operator-scoped PRs open for review; no merge; installed sources unchanged | operator-delivery | [operator-pr-007.md](operator-pr-007.md) |
| linear-ci-008 | Keep test-only repair; upstream required CI remains blocked during network checkout; maintainer intervention required | operator-delivery | [linear-ci-008.md](linear-ci-008.md) |

| 场景 | 角色 | 指标 | 数值 | 单位 | 范围 |
|---|---|---|---|---|---|
| embedding-p1024-c64-n256 | A-current | input_token_throughput | 45228.87656959786 | token/s | diagnostic-incomplete-steady-state |
| embedding-p1024-c64-n256 | A-current | request_throughput | 44.16882477499791 | request/s | diagnostic-incomplete-steady-state |
| embedding-p1024-c64-n256 | A-current | mean_e2el | 1121.5401278677746 | ms | diagnostic-incomplete-steady-state |
| embedding-p1024-c64-n256 | A-current | round_mean_p99_e2el | 4238.286671857348 | ms | diagnostic-incomplete-steady-state |
| embedding-p1024-c64-n256 | B-release | input_token_throughput | 26678.938068130425 | token/s | diagnostic-incomplete-steady-state |
| embedding-p1024-c64-n256 | B-release | request_throughput | 26.053650457158618 | request/s | diagnostic-incomplete-steady-state |
| embedding-p1024-c64-n256 | B-release | mean_e2el | 1737.0677833405352 | ms | diagnostic-incomplete-steady-state |
| embedding-p1024-c64-n256 | B-release | round_mean_p99_e2el | 5719.100159360096 | ms | diagnostic-incomplete-steady-state |
| embedding-p1024-c64-n256 | A2-current | input_token_throughput | 76719.80976182171 | token/s | diagnostic-incomplete-steady-state |
| embedding-p1024-c64-n256 | A2-current | request_throughput | 74.92168922052902 | request/s | diagnostic-incomplete-steady-state |
| embedding-p1024-c64-n256 | A2-current | mean_e2el | 950.7143995215301 | ms | diagnostic-incomplete-steady-state |
| embedding-p1024-c64-n256 | A2-current | round_mean_p99_e2el | 2587.6251520356163 | ms | diagnostic-incomplete-steady-state |
| embedding-p1024-c64-n256 | batch-budget-004:A-32768 | total_token_throughput | 119242.2078124537 | token/s | diagnostic-only; numeric-gate-failed; revert-cancelled-by-user |
| embedding-p1024-c64-n256 | batch-budget-004:A-32768 | request_throughput | 116.44746856684931 | request/s | diagnostic-only; numeric-gate-failed; revert-cancelled-by-user |
| embedding-p1024-c64-n256 | batch-budget-004:A-32768 | mean_e2el | 509.79673744150205 | ms | diagnostic-only; numeric-gate-failed; revert-cancelled-by-user |
| embedding-p1024-c64-n256 | batch-budget-004:A-32768 | round_mean_p99_e2el | 818.1971219368279 | ms | diagnostic-only; numeric-gate-failed; revert-cancelled-by-user |
| embedding-p1024-c64-n256 | batch-budget-004:B-65536 | total_token_throughput | 119764.46639301354 | token/s | diagnostic-only; numeric-gate-failed; revert-cancelled-by-user |
| embedding-p1024-c64-n256 | batch-budget-004:B-65536 | request_throughput | 116.95748671192729 | request/s | diagnostic-only; numeric-gate-failed; revert-cancelled-by-user |
| embedding-p1024-c64-n256 | batch-budget-004:B-65536 | mean_e2el | 506.86474760223064 | ms | diagnostic-only; numeric-gate-failed; revert-cancelled-by-user |
| embedding-p1024-c64-n256 | batch-budget-004:B-65536 | round_mean_p99_e2el | 818.1240261159833 | ms | diagnostic-only; numeric-gate-failed; revert-cancelled-by-user |

<!-- e2e:summary:end -->
