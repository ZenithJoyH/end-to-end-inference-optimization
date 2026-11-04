# fw-008：common-slot graph host sync 因果实验

## 状态

`rejected_and_reverted` — 真实 common-slot kernel 的 graph→consumer 因果探针、
服务 graph/canonical 和 P4K/D128 3+3 筛选均完成；候选输出吞吐只提升
0.4994%，低于预冻结的 1% 门槛，源码补丁已回退。

## 调用点与假设

Plugin `vllm_fl/worker/common_slot_mapping.py::_replay_common_slot_graph()` 在
T-Head 上执行：

```python
graph.replay()
current_stream().synchronize()
```

prof-005 中 graph-wrapper 无 ATen 父节点的 Prefill/Mixed/Decode 计数为
`1/0/127`；cached64 的 62 次直接同步在 rank0/rank1 profiler 中累计
1.857s/2.920s。该时间会吸收前序 collective/backlog，不能直接当成
common-slot kernel 时间，但可能阻止 CPU metadata 构建与已排队设备工作的重叠。

## 真实算子因果探针

使用 FlagGems `compute_common_slot_mapping`、P4K cached64 shape
（64 requests、4096 max tokens、block size 128），在两个不同 metadata 输出间
交替，consumer 在 GPU 上立即核对 slot mapping 和 computed-token 状态。
每臂 `2000 × 3`：

| Arm | mismatch | 中位 host wall / pair |
|---|---:|---:|
| 现有 host sync | 0 | 57.593µs |
| 同流 no fence | 0 | 51.255µs |
| 跨流 event wait | 0 | 61.663µs |
| eager producer 同流 | 0 | 74.929µs |

两个 producer graph 均通过 capture 和两次 replay。探针证明 no-fence 在该真实
shape 下没有复现陈旧读，event 不是低成本替代；它仍不是端到端正确性或性能证据。

证据：
`/mnt/nfs/users/jinghao/qwen3.8-flash/20260919-qwen38-flash-next-ppu-e2e/diagnostics/fw008-common-slot-graph-fence-01/result.json`，
SHA-256 `ad6b8b5d032454a708af42015cfb9d54a7a7636f06dd91573578d2dad090ab31`。

## 服务筛选

实验补丁仅增加默认关闭的 `VLLM_FL_SKIP_COMMON_SLOT_HOST_SYNC` 开关；候选服务57
在 PPU0–7 设置为 `1`，其余配置与保留服务一致。候选 common-slot 文件 SHA-256
为 `0b7f07ab3068197a2cb6219cdd2c0fd151dc0b39c408c71468315104a1fad85b`。

- FULL/PIECEWISE graph capture 正常。
- 24/24 canonical replay 一致，SHA-256 与 service50 同为
  `54f05e02051a882c0b45503581c97389e987c8e8b7be6bd7a227e544b7d9cbf7`。
- P4096/D128/C64/N64，2 warmup + 3 measured，零失败且 warmup spread 通过。

与此前同卡组、同配置 service54 基线中位数比较：

| 指标 | baseline | candidate | 变化 |
|---|---:|---:|---:|
| output throughput | 176.739 | 177.622 tok/s | +0.4994% |
| total throughput | 5832.387 | 5861.514 tok/s | +0.4994% |
| P99 TTFT | 34766.49 | 34724.01 ms | -0.1222% |
| P99 TPOT | 311.02 | 309.92 ms | -0.3545% |
| P99 ITL | 549.90 | 549.29 ms | -0.1108% |
| P99 E2E | 46295.61 | 46070.87 ms | -0.4854% |

全部守护方向良性，但主指标不足 +1%，因此不投入 fresh A/B/R。候选服务已按
精确 PID/start-tick 停止，补丁反向应用，common-slot 文件恢复 SHA-256
`811289ae9cbcf2869e506eeae7028818a07b65daf54b10d425c1c2baf60a64d6`；
PPU0–7 已释放，service50 保持健康。

性能证据：
`/mnt/nfs/users/jinghao/qwen3.8-flash/20260919-qwen38-flash-next-ppu-e2e/performance/fw008-d128-candidate-service57-01/run-record.json`，
SHA-256 `40b3d4dcbd7ee792bbf9f06e137b9a10c8ba30030d8aa3d93665eeca5e13fc8f`。

## 结论边界

该结果拒绝的是在当前 P4K/cached64/PPU/graph 服务中去掉 T-Head common-slot
host sync 的性能候选；不证明同步在其他 shape 或 runtime 上永远无价值。现有
同步是适配层已有正确性保护，默认行为保持不变。
