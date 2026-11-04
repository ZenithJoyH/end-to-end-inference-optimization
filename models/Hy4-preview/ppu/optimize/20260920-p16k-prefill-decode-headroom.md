# 20260920-p16k-prefill-decode-headroom

- experiment-id：`20260920-p16k-prefill-decode-headroom`
- 分类：`framework`
- 状态：`rejected_and_reverted`
- milestone：`P16384/D128/C16/N16`

## 方向与假设

双 concurrent partial-prefill 配置被当前 vLLM 的能力门禁拒绝，不修改 vLLM。
新候选保持单 partial-prefill 及 2048-token Prefill chunk，只将 scheduler
总预算从 2048 扩到 4096，使同一 iteration 仍可容纳 Decode token。

| 配置 | max batched tokens | partial prefills | long partial prefills | long threshold |
|---|---:|---:|---:|---:|
| baseline/revert | 2048 | 1 | 1 | 0 |
| candidate | 4096 | 1 | 1 | 2048 |

## 冻结契约

- milestone：`P16384/D128/C16/N16`，父场景 `P16384/D1024/C64/N128`。
- 复用紧邻、同代码、同 workload 的 dual-partial 实验 baseline；其两轮 output throughput 为 `12.9791/12.9701 tok/s`，spread 约 `0.07%`。
- candidate 与 revert 各自独立重启 graph 服务，1 轮预热 + 2 轮测量。
- 主指标：output throughput 提升至少 `2%`。
- 守护：P99 TTFT/TPOT/ITL 回退不超过 `5%`，total throughput 回退不超过 `2%`，失败请求为 0。
- 停止条件：主指标改善不足 `2%`、任一守护越界，或无法启动/capture/replay。

## 实施、正确性与结果

- 实施：candidate/revert 均以独立服务完成 51 个 Decode graph capture、1 轮预热和 2 轮 measured，每轮 `16/16` 成功。
- 源码：无改动，仅服务启动参数。
- output throughput：baseline `12.9791/12.9701`，candidate `13.0827/13.0785`，revert `12.9850/12.9726 tok/s`。candidate 中位数相对 baseline 仅约 `+0.82%`，baseline↔revert 漂移约 `+0.03%`。
- P99 ITL：baseline 约 `1444 ms`，candidate 约 `2761 ms`，回退约 `91%`，远超 `5%` 守护。
- KV 容量：candidate `419897` token，baseline/revert `424824` token，候选减少约 `1.16%`。
- 标准比较回执为 `incomplete`，因复用的 baseline 在测量前冻结了上一实验的 comparison contract。不事后改写 run-record；上述结果仅作诊断性同 workload 直接比较。
- 决定：`reject`，未达主指标且 P99 ITL 守护严重失败；不进入 C32/C64。

## 外部证据

- 根目录：`.../results/performance/20260920-p16k-d128-c16-n16-prefill-decode-headroom-01`
- candidate run record SHA256：`55e8311f2ce50e79fc00c9656c3ea4241446c5b6ae48bf01507caccf07695d3f`
- revert run record SHA256：`b04b369583bb010d303f91cc7e6bcf65d5bcb7243a4df36c67dd0157e3bde745`
- comparison SHA256：`e320b975a9bfdc7024f1f777cf281de34f5cc7727e8476d05ce9bbe06f1e7488`

## 回退

停止 candidate，以 `2048/1/1/0` 重启并执行 revert 轮。
