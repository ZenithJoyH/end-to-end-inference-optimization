# 20260920-p4k-sparse-mla-shape-analysis-05 P4K Sparse MLA prefill

- 状态：`complete/rejected`
- 分类：`operator/improve`
- 目标场景：P4096/D1024/C64/N128
- 目标阶段：Prefill、Mixed；Decode 作为守护

## 优化方向与瓶颈依据

P4K 16-rank trace 中，rank0 Sparse MLA prefill 在 Mixed/Pefill 的累计设备活动
分别为 24.694%/21.630%，是 Mixed 第一、Prefill 第二热点；per-rank 设备活动离散
低于 1%/10%，没有明显单 rank straggler。实际已知有效 shape 为 TP16、BF16、
per-rank H4、DQK512、DV512、topk2048，主 kernel 由 thead vendor/预编译路径提供。

已有本模型案例证明：只优化前置 sparse-index 转换，微基准虽有 3.55x–4.54x，
端到端却为 -0.041%/-0.005%，因此本轮不重复该方向。先确认 P4K trace 的真实
M/SQ bucket、vendor symbol、调用频次和现有可配置边界，再比较完整 Sparse MLA
调用；不会从历史模型直接复用 BH/BK 或 split 参数。

## 预冻结实验与停止条件

1. 解析 16-rank trace/运行源码，确认 Plugin→FlagGems-vllm/FlagGems/vendor 的
   实际调用链、shape、dtype、layout、graph 模式和 fallback。
2. 检查已有 backend 是否暴露 tile/split/backend 选择；若主 kernel 为不可配置的
   预编译实现，只比较真实存在且语义兼容的替代实现，不复制另一平台参数。
3. 首轮 microbenchmark 计入完整调用及必要 workspace/merge；候选必须在目标 P4K
   主 shape 上中位至少加速 5%，且边界 shape 无明显退化，才允许修改源码。
4. 源码候选还需 reference 数值、非对齐/边界 shape、fallback、graph capture 和
   两次 replay；最终必须回到无 profiler P4K A/B/R，输出吞吐至少 +3%。

停止条件：实际实现未命中、无可控变量、完整调用收益不足 5%、数值/graph 失败、
workspace/merge 或通信抵消收益。任何 microbenchmark 收益都不直接计入端到端。

## 性能效果

调用链确认生产服务命中：

```text
Plugin TheadMLASparseImpl
  -> /usr/local/lib/python3.12/site-packages/flash_mla/flash_mla_interface.py
  -> flash::flash_sparse_prefill_fwd_kernel
```

trace kernel 模板和 live wrapper 共同确认 `DQK=DV=512`、`BK=64`、H4；P4K
Mixed 主 bucket 为四个 4096-token prompt，即 `SQ=16384`。FlagGems-vllm 的
TLE Sparse MLA 在代码中对 thead 直接返回 false，通用 Triton fallback 的最小
head tile 为 BH16，仍需为 H4 做 4 倍 padding。

以 `SQ16384/SKV65536/HQ4/HKV1/DQK512/DV512/topk2048/BF16` 比较完整调用，
3 次预热、7 次交错计量结果如下：

| 实现 | 中位延迟 | 7 轮范围 | 相对 vendor |
|---|---:|---:|---:|
| thead vendor | 43.005 ms | 43.003–43.021 ms | 1.000x |
| FlagGems-vllm 通用 Triton | 51.943 ms | 51.927–52.121 ms | 0.828x |

通用实现慢约 20.8%，没有达到 1.05x 算子门槛。数值对照通过：output/LSE
在 `atol=rtol=0.02` 下 allclose，output 最大绝对误差 `6.1035e-5`、LSE 最大
绝对误差 `1.4305e-6`、output cosine `1.0`。由于性能已明确失败，不进入源码
接入、graph 或 P4K 服务 A/B/R。

## 决定、风险与回退

决定为 `rejected`。没有修改源码，生产继续使用 thead vendor Sparse MLA；当前
保留组合和启动脚本不变。知识差量为 `refined`：对于本模型 PPU H4/DQK512 的
P4K SQ16384，现有通用 Triton 并不是可行 replacement，未来应先检查 vendor
是否暴露小 tile/新版实现，而不是先切换到通用 fallback。下一步转向 P4K
large-M fused MoE 的现有 stage-config 命中与可调空间。

## 外部证据

- `/mnt/nfs/users/jinghao/glm5.3-flash/optimize/e2e-opt-20260911/full-scenarios/p4096-d1024-c64-n128/operators/sparse-mla-05`
- 结果 SHA-256：`ab6cd6c9b38937b87af7ed14c493b16de4ce9f4452e0c407cd5650f2eadddb09`
- 冻结计划 SHA-256：`94d6545d6b3b987f2a229ed4fc5d867acac2bd10203c8bb0ea2041ef73f45d29`
- benchmark SHA-256：`9fa1805012d02d468ba085d8fbcd2e77ce63f58574edbfa85cbfad85e56daeeb`
