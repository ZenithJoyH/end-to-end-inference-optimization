# 20260922-mhc-moe-align-critical-path-32 mHC / MoE align 临界路径归因

- 状态：`complete`
- 分类：`operator/attribution`
- 目标：解释为什么 mHC 与 MoE align 单算子大幅加速，端到端却无收益

## 已有因果证据

| 算子 | 算子层结果 | 同配置服务 A/B/R |
|---|---:|---:|
| mHC pre，P1K Decode | 5.528× | 输出吞吐 -0.587% |
| mHC pre，P4K 大 M | 3.3548×–3.8076× | 输出吞吐 +0.0938% |
| MoE align stage2，P1K small-M | 3.635× | 输出吞吐 -1.308% |

历史文档把 MoE align 的顶层 provider 命中误当成了特化 kernel 命中。
本次补充候选服务 trace 后已纠正：MoE 的 A/B/R 实际没有执行新 kernel。

## 归因方法

1. 优先复用已有 A/B/R、算子结果和 16-rank trace，量化实际调用次数、阶段占比、
   理论零成本上限与可见的 CPU/launch 边界。
2. 检查同 stream 串行、异 stream 重叠、collective/GEMM 相邻间隔、dispatch 和 graph
   replay 边界，判断 microbenchmark 节省是否落在请求临界路径。
3. 只在现有 trace 不能回答时，才分别对 mHC 与 MoE align 补一次单变量候选/
   回退 trace；不把 profiler-on 时间当成端到端收益。

## 成功标准

对两个算子分别产出定量上限和 trace 支持的因果解释，明确是占比过小、
非临界路径/重叠、接入成本、相邻 kernel 交互还是测量边界不等价。若证据
无法区分，结论必须保留为 `incomplete`，不以猜测代替。

## mHC 归因结果

Plugin 的 `reference.torch` 路由确实调用 vLLM `MHCPreOp.forward_native`，
其 Python 语义入口是 `mhc_pre_torch`。但 P4K baseline/revert 服务 trace 中实际
执行了 `mhc_pre_fused_kernel_hc_mult_4`：rank0 合计 10680 次、
1.436268 s，并覆盖 `M=1/64/4096/12769/16384`。该 kernel 名称和实现只
出现在 FlagGems/FlagGems-vllm，FlagGems PT2 模块又明确用
`torch.library.wrap_triton` 包装同一内核。

因此微基准中 3.35×–5.53× 的分母是单独 capture 的 eager/reference
公式，而不是 vLLM 服务编译图的真实分母。服务图已将 reference 语义降到
同类 FlagGems 融合内核；切换 dispatch provider 虽然改变了日志中的路由名，
却没有删掉微基准所计时的那段服务成本。P4K 同配置 A/B/R 只有
`+0.0938%`，与“有效服务实现基本等价”一致，属于测量漂移范围。

## MoE align 归因结果

重建原候选后，`M=32/E=288/topk=8/BM16` 完整 align 调用仍为
`0.06656 ms → 0.01834 ms`，即 `3.6292×`，数值和 graph 通过。但同一
候选的 C32 服务 trace 显示：

- `execute_new_0_cached_32` 出现 119 次，说明确实进入 small-M/C32 服务图；
- 新 `moe_align_block_size_stage2_padded_vec` 命中 `0` 次；
- 老 `moe_align_block_size_stage2` 仍执行 `2772` 次，中位 `51.68 us`，
  合计 `143.274 ms`。

当时的 FlagGems-vllm selector 还要求 `expert_map is None`，生产 EP 路径
不满足这个条件；但 2026-09-23 对运行容器的 Plugin 调用链复核发现更早的
接入障碍：Plugin 的 `moe_align_block_size` 实现直接调用
`flag_gems.moe_align_block_size_triton`，而新 kernel 只存在于
`FlagGems-vllm` 的 `moe_align_block_size_no_tle` 路径。旧 trace 证明
新 kernel 未执行，不能仅凭它把 `expert_map` 判为唯一根因。即使修复
selector，仍须让服务实际走到候选入口并取得 trace 命中证据。
所以历史 `-1.308%` 不能解读为“快 kernel 被邻接开销抵消”，因为快
kernel 根本没有执行；它只是同一有效服务路径上的 A/B 漂移。按历史
Decode activity 份额 7.68% 和 3.635× 估算，若真命中的设备 activity 理论上限约
5.57%，但仍需服务关键路径实测，不是可直接相加的端到端收益。

## 决定

mHC provider 切换不再作为当前优化方向。MoE align 的历史 A/B/R 更正为
`no-op specialization / inconclusive performance effect`；针对 `expert_map` 的真实
接入修复转入 `20260922-p32k-moe-align-ep-33`；该点的 EP selector 修复
已通过算子门禁，但 Plugin 接入仍未完成。

## 外部证据

- 命令：`/mnt/nfs/users/jinghao/glm5.3-flash/optimize/e2e-opt-20260911/commands/mhc-moe-align-critical-path-32-20260922`
- 证据：`/mnt/nfs/users/jinghao/glm5.3-flash/optimize/e2e-opt-20260911/analysis/mhc-moe-align-critical-path-32`
- trace 汇总 SHA-256：`8238cf356fd1ad7474c3ac237940febb5d9dab9994a695b7ff2242c0fa9637fe`
- MoE M32 重建结果 SHA-256：`6584fc9c65767796baa42f242e68273d353c41c29fb718c3c5ccbee0ce07d692`
- 16-rank trace manifest SHA-256：`c9b7a248bdca0a1d9b9578044386a3f9ac7294a57b5477d73aac60964ffedcca`
