# Baseline

状态：`baseline_measurement_in_progress`。源容器的两个 TP8 服务已按用户授权优雅停止，源容器仍保留；当前两套隔离 graph 服务分别使用 PPU 0–7/端口 8020 与 PPU 8–15/端口 8030。两者都显式关闭 prefix cache，镜像谱系与挂载门禁已通过。

| 场景 | 范围 | 状态 | 输出吞吐 | TTFT | TPOT/ITL | E2E | 说明 |
|---|---|---|---:|---:|---:|---:|---|
| P1024/D1024/C64/N128 | full target | complete baseline | 330.73 tok/s | P99 104.90s | P99 TPOT 96.47ms / ITL 94.96ms | P99 202.07s | 三轮中位数；C64 在 max-num-seqs=32 下存在 admission 波次 |
| P4096/D1024/C64/N128 | full target | not_run | — | — | — | — | 待 P1K 闭环后进入 |
| P16384/D1024/C64/N128 | full target | not_run | — | — | — | — | 待测 |
| P32768/D1024/C64/N128 | full target | not_run | — | — | — | — | 待测 |

Prefill milestone `P1024/D1/C32/N64` 的无干扰三次实测总 token 吞吐为 `5433.49 / 5415.82 / 5424.73 tok/s`，P99 TTFT 为 `6315.30 / 6344.22 / 6347.56 ms`。该结果来自 PPU 8–15 的未修改路径，用于同组 `max-num-seqs` 候选筛选；不能与 PPU 0–7 直接计算加速比。

Decode milestone `P32/D1024/C32/N64` 的无干扰三次实测输出吞吐为 `355.12 / 355.86 / 355.98 tok/s`，P99 TPOT 为 `90.15 / 90.54 / 90.00 ms`，P99 ITL 为 `92.04 / 92.28 / 92.43 ms`。预热输出吞吐相对波动约 `0.56%`，通过稳定性门禁。

正确性 `baseline-sanity`：2048/8192/30000 输出上限下分别有 3/1/1 个截断。最后一轮 10 个请求全部返回，strict-match `0.9`，但一个样本生成到 30000 token、`finish_reason=length`，评测器记为 `timeouts=1`，因此输出健康状态为 failed，不签发正式精度 gate。环境证据：快照镜像 `sha256:d87b7b26…cb9bbe6`；源/优化容器代码指纹匹配；`/mnt` 挂载源、目标、RW 与 `rprivate` 传播一致。
