# 20260921-p4k-mqa-logits-exact-shape-review-08 P4K MQA logits 精确 shape 复核

- 状态：`rejected/no-new-run`
- 分类：`operator/improve`
- 目标场景：P4096/D1024/C64/N128
- 目标阶段：Mixed/Prefill；Decode 不是本算子的主路径

## 优化方向与瓶颈依据

rank0 P4K trace 中 `_fp8_fp4_mqa_logits_kernel` 在 Mixed 设备活动汇总中约占
9.313%，每个 Mixed admission wave 调用 11 次。目标是确认当前生产
`BM4/BN64/HEAD_BLOCK16/warps4/stages2` 是否已覆盖当前 P4K 精确 shape，
以及历史搜索是否已证伪主要替代配置。

## 实验边界

1. 从已验证 trace 提取每个 Mixed marker 的 kernel grid、调用数和耗时，
   并用 CPU `Input Dims`/scheduler token budget 反推 M/H/D 边界。
2. 核对运行中 `flaggems_vllm.runtime` 与 kernel tuner 的实际配置集合，
   不根据 YAML 文件位置推断。
3. 将当前 shape 与已有大 Prefill 微基准对齐。若已覆盖同一 shape 带，
   且最佳替代配置仍低于 `1.05x` 算子门槛，则停止，不重复启动服务。

## 正确性与风险

本轮默认只读复核。如果出现新候选，才要求完整调用的 FP32 logits
与当前配置比较，同时覆盖非对齐 M/N、graph capture 和至少两次 replay。
不允许把 NVIDIA/Hopper TLE 配置套用到 PPU。

## 性能效果

实际导入源为 FlagGems-vllm 可编辑安装目录。
`runtime.get_tuned_config("fp8_fp4_mqa_logits")` 和
`_fp8_fp4_mqa_logits_kernel.fn.configs` 的完整集合一致，且都只包含：

`BM4/BN64/HEAD_BLOCK16/warps4/ctas1/stages2`。

PPU device capability 为 `(8, 0)`，`HAS_TLE=False`，未进入仅为 Hopper/WGMMA
设计的 TLE 快路。

rank0 trace 有 16 个 Mixed admission wave，每个 wave 均调用该 kernel 11 次。
`BM4/BN64` 解释下，grid 覆盖：

- M 维 grid 从 `3178` 到 `4096`，对应约 `12.7K–16.4K` rows；
- N 维 grid 为 `64/79/80`，对应上界 `4096/5056/5120`；
- 每次 kernel 中位数约 `8.415–13.581 ms`；
- 前 15 个有可靠 parent shape 的 wave 中，14 个可由 scheduler token 量与
  cached 数直接解释 grid；最后 `new3/cached61` 不简化推断精确 M，
  因此仅保留观测 grid，不伪造精确 shape。

这一 shape 带已由历史微基准直接覆盖：

| shape | current | 最佳替代 | speedup |
|---|---:|---:|---:|
| M16384/N4096/H32/D128 | 10.90827 ms | BM4/BN128/w4/s2 10.72484 ms | 1.01710x |
| M16364/N5120/H32/D128 | 13.57567 ms | BM4/BN128/w4/s2 13.32079 ms | 1.01913x |

其他已测 `BM8/BN64`、`BM2/BN128`、8 warps 和 stage 1/3 均无收益或明显变慢。
最佳候选低于本轮 `1.05x` 算子晋级门槛；即使按 Mixed 9.312% 份额
乐观估算，端到端上限也不足 0.2%。

结论：无新候选，不重复微基准、不修改源码、不启动服务。下一优先级
转到 Prefill 11.603% / Mixed 6.003% 的 PCCL all-reduce 关键路径与算法选择复核。

## 外部证据

- trace：`/mnt/nfs/users/jinghao/glm5.3-flash/optimize/e2e-opt-20260911/full-scenarios/p4096-d1024-c64-n128/profiling/p4k-d1k-maxseq64-retained-01`
- 历史同 shape 带微基准：`/mnt/nfs/users/jinghao/glm5.3-flash/optimize/e2e-opt-20260911/mqa-large-prefill-config/microbench-01`
- grid 证据：上述 trace 目录 `analysis/mqa-grid-evidence-v2.json`，SHA256
  `bceb293a3bf1b72f09245ad7520538f81cc6893a99427a58a2c41797cbb0abbf`。
- live config 证据：`analysis/mqa-live-config.txt`，SHA256
  `8f76c5c4eda8790be5d1dc3fe99edc687e56e60cd465444cf3cf425fc280d986`。
- 历史 result SHA256：
  `d74ab9b2b95ab93a8772716253aec2a8910d9deaab7f7b8e843cb97135a920c4`。
