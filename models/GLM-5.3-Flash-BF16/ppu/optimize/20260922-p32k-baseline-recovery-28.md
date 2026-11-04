# 20260922-p32k-baseline-recovery-28：P32K长 prompt 容差恢复

## 方向与冻结范围

- 状态：完成；`framework`，服务已停止。
- 父场景：`P32768/D1024/C64/N128`；恢复里程碑：
  `P32768/D128/C64/N128`。
- 当前组合不变：TP16/BF16/max-seqs64/MBT32768/max-model-len80000/
  FULL_DECODE_ONLY/前缀缓存关闭。
- point26和point27的失败证据保持原样，不复用其轮次作为本点结果。

## 恢复契约

fresh服务先C1/C8，再运行6 warmup+3 measured。warmup 4–6和
measured 1–3的输出吞吐相对极差均须不超过5%，全部请求成功。
这是新实验的事前冻结契约，不是对point27的3%门禁做事后修改。
5%用于判定长prompt多seed测量是否可用；后续候选相对baseline的
晋级收益门槛仍为3%。

控制脚本必须保留EXIT cleanup trap、外层`pipefail`与停服前空闲检查。
失败则停止并保留`incomplete`；成功后才进入P32K分阶段profiling。

## 产物边界

- 命令根：`commands/p32k-baseline-recovery-28-20260922/`。
- 结果根：`full-scenarios/p32768-d1024-c64-n128/baseline/recovery-28/`。
- 不修改源码、DB或交付脚本，不提交或推送。

## 当前结果

fresh graph服务启动成功，C1/C8分别`1/1`、`8/8`通过。
6 warmup+3 measured全部完成，共9轮`1152/1152`请求成功，无失败。

| 稳态窗口 | output tok/s | 相对极差 |
|---|---|---:|
| warmup 4–6 | 36.182660 / 36.167403 / 36.175000 | 0.042175% |
| measured 1–3 | 36.170666 / 36.174157 / 36.185298 | 0.040447% |

measured中位数：

| 指标 | 中位数 |
|---|---:|
| request throughput | 0.282611 req/s |
| output throughput | 36.174157 tok/s |
| total-token throughput | 9296.758291 tok/s |
| P99 TTFT | 221607.966 ms |
| P99 TPOT | 1730.091 ms |
| P99 ITL | 3503.669 ms |
| P99 E2E | 432788.350 ms |

`run-record.json`状态为`complete`，SHA-256为
`6af40af9b4f0844192e9d8157aca98e5e9789dde2ae7bfe266ef0b4d41cc9c74`。
point27的低值未在相同seed上复现；本点的偶发低值出现在前置
第3轮，不进入冻结稳态窗口。这进一步否定“固定seed必然低吞吐”，
但不对偶发扰动的物理原因做超出证据的归因。

EXIT cleanup成功，无`cleanup-failed`标记，目标vLLM进程不存在，
8011关闭。本点建立的是当前保留组合的P32K/D128 scenario-entry
baseline，不是未优化anchor，也不是P32K/D1024正式结果。
