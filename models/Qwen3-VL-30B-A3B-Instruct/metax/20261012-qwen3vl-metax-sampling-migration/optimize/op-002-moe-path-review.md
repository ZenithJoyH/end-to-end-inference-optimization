# op-002：现有 MoE vendor 补丁审查

- 日期：2026-10-12；Host：mx-59；源容器：qwen-vl。
- 用户范围：检查当前 Plugin 的 MoE 优化如何进一步改进。
- 状态：read-only-diagnosis；本轮未修改推理源码、服务配置或启动服务。
- 分类：已有补丁属于 `operator/replace`；后续融合另列 `operator/improve`。
- 环境版本及独立容器门禁沿用 op-001；本轮只在源容器读取源码，在已通过门禁的 `qwen-vl-sampling-opt-20261012` 解析 dispatch。未运行设备计算或模型性能测试。

## 当前补丁与调用链

Plugin 修改位于 `/workspace/vllm-plugin-FL/vllm_fl/dispatch/backends/vendor/metax/impl/fused_moe.py`。它调用已安装的 `mctlassEx.FusedMoeGEMM`，替换第二次 GEMM；没有新增 Triton/C++ kernel。vendor 适配放在 Plugin 的 MetaX backend 边界是合理的，无需因采样算子的迁移而将其整体搬走。

当前模型 text config 为 hidden=2048、intermediate=768、experts=128、top-k=8、TP=2。每 rank 的数据流是：

`align → GEMM1 [T,2048]×[128,768,2048] → SiLU/mul → GEMM2 [8T,384]×[128,2048,384] → moe_sum`。

MetaX 的 `PlatformFL.is_cuda()` 返回 false；`TritonExpertsFL.apply` 使用分步骤的 CachedOp 路径。FlagGems backend 实际包装的是 `flag_gems.invoke_fused_moe_triton_kernel`，不是 FlagGems-vllm 的同名实现。

## 首要发现：开关不等于命中

启动脚本 `/public-flash/jinghao/qwen3-VL/start-model.sh` 设置 `VLLM_FL_METAX_QWEN3VL_MCTLLASS_GEMM2=1`，但没有为 `invoke_fused_moe_triton_kernel` 设置 vendor 优先策略；FlagGems blacklist 中也没有此 op。

在独立优化容器中，使用相同的影响 dispatch 的环境变量解析得到：

```json
{"prefer":"flagos","per_op":null,"candidates":["default.flagos","vendor.metax"],"selected":"default.flagos"}
```

解析时未设置 MCTLLASS 开关，以避免构造 vendor handle；源码检查表明该开关只控制 vendor 模块内的对象构造和 shape 分支，不改变 registry/policy。因此该结果证明正常默认选择是 FlagGems，不能证明运行模型的实际 kernel 命中。当前没有取得运行中模型 worker 的命中证据。

`CachedOp` 首次缓存所选实现；非 strict 模式下失败才标记实现失败并转 manager fallback。不能依靠 FlagGems 报错来启动性能候选，也不能将 fallback 的启动失败开销混入收益。

## Shape 与调参问题

- 白名单 M 为 GEMM2 展开后的行数：64/256/512/8192/16384/59144/65536，对应真实 T=8/32/64/1024/2048/7393/8192。Decode T=64 对应 M=512；59144 是工作负载特定值，不是通用支持边界。
- 小 M 要求 `BLOCK_SIZE_M=16`，大 M 要求 128。该 BM 同时决定前面的 expert 对齐，不能只更改 GEMM2 BM 而继续使用原 sorted metadata。
- 配置文件 `E=128,N=384,device_name=metax.json` 中的 N=384 是本地 intermediate 维度，不是 GEMM2 输出的 2048；JSON 的 key 是 T。
- tuning_short/long 在 T=64 的 BN/BK/GROUP_M/warp/stage 不同；vendor GEMM2 调用没有传入这些参数。vendor 命中后，这些调参不能用于解释其 kernel 收益，应分别测 GEMM1 与 GEMM2。未命中时两次 GEMM 仍会受共用配置影响。

## 建议按顺序推进

1. **显式、有限地接入 GEMM2 候选。** 复用现有 registry/per-op policy；若让 vendor 优先，需验证 GEMM1 随之进入 mcoplib 的影响。更可控的设计是在同一 MoE backend adapter 内按调用能力选择 GEMM1/GEMM2：支持的 GEMM2 走 MCTLLASS，其他输入保留原 FlagGems 路径。不要全局将所有算子切成 vendor。先证明 impl_id 和 vendor 分支命中，再测收益。
2. **收紧支持契约。** 把已有 shape 判断提取为可测 helper，补全 expert_ids、num_tokens_post_padded、route weights 的 dtype/device/layout/大小约束，保护 naive assignment（sorted ids 为 None）、量化、bias、非目标结构。只做 metadata 检查，不在 graph 热路径取 `.item()` 或引入同步。性能白名单与正确性支持边界分别维护；扩展白名单需要实际 shape 分布和测试。
3. **整理可选依赖与生命周期。** 当前模块导入即构造单例；MCTLLASS 的 `check_shape` 实际仅返回 True。应依据 worker/device 生命周期创建 handle，并在 capture 前完成预热，保持依赖缺失时可诊断。不要在每次调用做能力查询或以宽泛异常捕获吞掉 vendor 执行错误。此项必须复测 graph，不把静态检查当作 graph 通过。
4. **独立调 GEMM1。** 保留对齐 BM 的契约，分别比较 T=64 Decode 与大 T Prefill；小范围搜索 BN/BK/warp/stage。计时覆盖 align、activation、两次 GEMM 和 sum，不仅测 GEMM2。
5. **评估已有融合。** FlagGems-vllm 的 MetaX MoE 实现已有 GEMM1+SiLU 和 GEMM2 direct_sum 能力，但当前 Plugin 没有自动使用它。先针对当前 E128/TP2 做单独候选和数值/graph 测试，再考虑接入；不能将其其他 E256/E512 的 Qwen 特化直接视作本模型支持。direct_sum 可省去 `[T,8,2048]` 的中间输出及后续读取，T=8192 时该 BF16 张量为每 rank 256 MiB；这是流量机会估算，需计入清零/原子归约并验证舍入差异，不是性能结论。

## 验证与停止条件

首个证伪实验是独立容器内支持与非支持 shape 的真实 dispatch/分支计数，分别覆盖 GEMM1 和 GEMM2；若未命中，停止性能比较并修正接入。随后以同配置原路径为 baseline，对 T=1/8/32/64、白名单边界及实际 Prefill buckets 做正确性、capture 和至少两次 replay，再对完整 MoE 链做同进程无 profiler 比较。未通过时不扩展白名单或替换默认策略。

阶段收益最终需回到 P1024/D1024/C64/N128 的 Prefill/Decode/Mixed 视图和有效精度 gate，再推进其他正式场景。本轮没有冻结新性能契约，没有设备/模型数值结果、profile 或端到端性能证据，不能宣称已有补丁有效或优化达标。

| 验证范围 | 类型 | 结果 |
|---|---|---|
| 当前 shape、版本、配置和调用链 | static/read-only | executed_passed |
| 默认 impl 解析与 CachedOp 行为检查 | runtime metadata/static | executed_passed；不等于 kernel 命中 |
| 当前/候选 MoE 数值、graph、模型精度 | hardware | not_run |
| MoE 完整链与端到端收益 | hardware | not_run |
| 源码与服务变更 | 不适用 | 本轮无变更，无需回退 |

参考案例：[Qwen3.6 MoE 历史分析](/Users/baai/Documents/ChatGPT/端到端推理优化/docs/cases/20260903-imported-qwen3-6-moe/README.md)。只复用“分阶段配置与完整链计时”的方法，不继承 Hygon 的 shape、性能或判断。

`pr_readiness=needs_revision`：已有实验开关、硬编码行数、可选依赖生命周期、真实命中和模型验证仍需整理。未创建 PR 或提交代码。
