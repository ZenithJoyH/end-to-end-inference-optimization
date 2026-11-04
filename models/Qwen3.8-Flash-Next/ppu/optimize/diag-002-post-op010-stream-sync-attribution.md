# diag-002：post-op010 stream-sync 归因

## 结论

`prof-005` 的同步长尾不是 native TopK，而是两类 metadata 主机取值和一类
graph wrapper 直接同步。rank0/rank1 三阶段同步调用次数完全一致：
Prefill/Mixed/Decode = `109/6804/4843`，但 rank1 累计等待时间分别高
39.4%/39.1%/62.3%，说明 collective/straggler 放大了同步等待。

主要父路径：

- `_local_scalar_dense → item → repeat_interleave`：Prefill/Mixed/Decode
  `36/2268/4644` 次。
- `_local_scalar_dense → item → nonzero_numpy → index_put_`：
  `36/2268/36` 次。
- `copy_ → _to_copy → to → index_put_`：`36/2268/36` 次，Mixed
  仅约 14ms，不是首个优化目标。
- graph wrapper 无 ATen 父节点：Prefill/Mixed/Decode `1/0/127`次；
  `execute_new_0_cached_64` 的 62 次直接同步在 rank0/rank1 为
  1.857s/2.920s。

`repeat_interleave` 次数每步恰好是 36 层，与
`PleShortConvAttentionMetadataBuilder.build()` 中每层构造 token group 的实际调用点一致。
该处未传 `output_size`，而总 token 数已经由 CPU metadata 精确得到，因此选为
op-014 的最小因果实验。

## 边界

- profiler-on 时间只用于归因，不是收益。
- TopK 独立探针 12/12 组 control-adjusted stream sync 为 0，已排除。
- 任何同步消除候选都必须通过输出一致、graph capture/replay 和无 profiler P4K
  测量。

## 证据

- `/mnt/nfs/users/jinghao/qwen3.8-flash/20260919-qwen38-flash-next-ppu-e2e/profiling/prof-005-p4k-post-op010`
- v2 聚合 SHA-256：`ab22f50fe6d6d1e056310f550cf707297eb9a7b832de1f60c1b1d5e1ccc5a388`
