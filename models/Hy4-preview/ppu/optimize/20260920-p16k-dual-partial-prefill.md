# 20260920-p16k-dual-partial-prefill

- experiment-id：`20260920-p16k-dual-partial-prefill`
- 分类：`framework`
- 状态：`unsupported_rejected`
- milestone：`P16384/D128/C16/N16`

## 方向与假设

P16K scenario-entry 预热中，KV 饱和后实际驻留为 23–25 个请求。纯 Decode
窗口 generation throughput 可达约 `300+ tok/s`，但每当 2048-token 长
Prefill chunk 进入 Mixed iteration，generation throughput 长时间降到约 `5–20 tok/s`。

当前 scheduler 每次最多只允许一个 partial prefill，因此候选将下列四个参数视为
一个原子机制变量：

| 配置 | max batched tokens | partial prefills | long partial prefills | long threshold |
|---|---:|---:|---:|---:|
| baseline/revert | 2048 | 1 | 1 | 0 |
| candidate | 4096 | 2 | 2 | 2048 |

候选允许每个 iteration 处理两个长 Prefill chunk，但显式把每个请求限制在
2048 token，避免单个 prompt 用尽 4096 token 预算。

## 冻结契约

- milestone：`P16384/D128/C16/N16`，父场景 `P16384/D1024/C64/N128`。
- 评测：同一 plan 的 baseline/candidate/revert，每个服务 1 轮预热 + 2 轮测量。
- 主指标：output throughput 提升至少 `2%`。
- 守护：P99 TTFT/TPOT/ITL 任一回退不超过 `5%`，total throughput 回退不超过 `2%`，失败请求为 0。
- 停止条件：未命中双 partial-prefill 路径、主指标改善不足 `2%`，或任一尾延迟守护越界。
- 晋级：先扩到 `P16384/D128/C32/N32`，然后才能进入父场景 Mixed checkpoint。

## 实施、正确性与结果

- baseline：已完成，两轮 output throughput 为 `12.9791/12.9701 tok/s`，相对 spread 约 `0.07%`，各 `16/16` 成功。
- candidate：在 engine config 创建阶段被当前 vLLM 拒绝，报错 `Concurrent Partial Prefill is not supported`；未启动 worker、未进入性能测量。
- 源码：无改动，仅候选服务启动参数。
- 正确性：baseline graph 完成 51 个 Decode graph capture 并完成预热+两轮 replay；candidate 因能力门禁未进入正确性验证。
- 性能：无 candidate 性能数据，不计算收益。
- 决定：`reject`；不绕过能力门禁，不修改 vLLM 源码。

## 外部证据

- 根目录：`.../results/performance/20260920-p16k-d128-c16-n16-dual-partial-prefill-01`
- baseline run record SHA256：`3722f01963d86d2714179ab28d6c354668a6cf4ccf638efaf50e456772e32e4d`
- candidate 失败日志 SHA256：`84a9959d26f4fdedc24798ac34b4fa6946f50ff6a76ddcbac1fa4f796083caa7`

## 回退

停止候选服务，用未修改的
`/mnt/nfs/users/jinghao/hy4-preview/start_hyv4-preview.sh` 或 baseline 四项 scheduler 配置重启。
