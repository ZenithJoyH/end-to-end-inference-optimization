# op-013：shape-selective mm provider 决策

## 结论

未进入实现。`prof-005` 中 `aten::mm` 的真实物理 M 主要是 Mixed `4096`
和 Decode `2017`，而先前证明三个 shape 中 FlagGems 快于 native 的微基准只覆盖
`M=64`。当前证据不支持把 M64 结论外推到生产 shape。

按 prof-005 rank0 计数，三个 M64 上 FlagGems 更快的 K→N shape 占全部 mm
调用约 34.4%（Prefill/Mixed/Decode 分别 146/9191/146 次）。即使乐观地把
M64 微基准收益外推，加权完整 GEMM 收益也只有约 6.3%，低于预先设置的
8% 实现门槛；对 Mixed 全阶段的乐观上界约 0.59%，不足以预测
`>=1%` 精确 P4K 收益。

## 生产 shape 计数（rank0）

| K→N | Prefill M4096 | Mixed M4096 | Decode M2017 |
|---|---:|---:|---:|
| 320→10240 | 97 | 6104 | 97 |
| 768→2560 | 48 | 3024 | 48 |
| 2560→12 | 36 | 2268 | 36 |
| 2560→2048 | 48 | 3024 | 48 |
| 2560→2560 | 1 | 63 | 1 |
| 2560→10240 | 1 | 63 | 1 |
| 10240→4 | 96 | 6042 | 96 |
| 10240→320 | 97 | 6105 | 97 |

`mm_kernel_general` 已退出 Prefill/Mixed/Decode top20，与 op010 native provider
已命中一致。只有当 M4096/M2017 真实 shape 的直接 provider 微基准改变这个
加权上界时，才重新打开 op-013。

## 证据

- `/mnt/nfs/users/jinghao/qwen3.8-flash/20260919-qwen38-flash-next-ppu-e2e/profiling/prof-005-p4k-post-op010/summaries-v2/hotspot-aggregate.json`
- 对应 trace 冻结清单：`prof-005-p4k-post-op010/summaries-v2/trace-SHA256SUMS`
