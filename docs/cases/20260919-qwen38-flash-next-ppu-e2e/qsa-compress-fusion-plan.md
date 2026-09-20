# Qwen3.8 QSA 压缩事务融合候选草案

状态：`draft / not applied / not benchmarked`

本文档仅整理候选接入与验证方法。本轮没有修改远端源码、容器或服务，也没有发送推理或性能请求。对应草案补丁为
[qsa-compress-fusion-draft.patch](qsa-compress-fusion-draft.patch)，focused
测试草案为
[qsa-compress-fusion-tests-draft.patch](qsa-compress-fusion-tests-draft.patch)。

## 1. 已核验环境

- Plugin 实际导入路径：`/workspace/vllm-plugin-FL-qwen38-adaptation`，commit
  `939600b323c02c21916f1f76bfb4cd8c2b02578d`，branch
  `support-qwen3.8-flash`。
- FlagGems-vllm 实际导入路径：`/workspace/FlagGems-vllm/src`，commit
  `5865ed53b183`。
- FlagGems 实际导入路径：`/workspace/FlagGems/src`，commit
  `2b1e5cfdbd22`。
- 候选 kernel 来自 FlagGems-vllm commit `3780fe7` 引入的
  `flaggems_vllm.ops.qwen4.qsa.qwen4_compress_norm_mrope_store_groups`。
- 当前 Plugin 有与本候选无关的未提交修改：PPU slot-mapping graph replay
  synchronize 和 blocking CUDA events。真正接入时必须保留，不得 reset
  或覆盖。

## 2. 当前调用链

`QSAIndexer._update_and_compress()` 当前依次执行：

1. `qsa_store_cache_rows(raw_key_cache, raw_slot_mapping, token_k)`；
2. MRoPE 时把三轴 position 写入 `rope_position_cache`；
3. `qsa_compress_groups_with_ratio(...)` 产生 BF16 `pooled` 和
   `first_positions`；
4. `GemmaRMSNorm` 处理 `pooled`；
5. `apply_qsa_rope()` 处理 normalized key；
6. `qsa_store_cache_rows(compressed_key_cache, compressed_slot_mapping,
   normalized)`。

候选只替换第 3–6 步。raw key 和可选 position cache 的写入仍保留原
路径，因此候选 kernel 看到的 paged raw cache 与原实现一致。

## 3. 候选精确签名

```python
def qwen4_compress_norm_mrope_store_groups(
    raw_cache: torch.Tensor,
    raw_block_table: torch.Tensor,
    token_to_req: torch.Tensor,
    logical_positions: torch.Tensor,
    compressed_slots: torch.Tensor,
    compressed_cache: torch.Tensor,
    norm_weight: torch.Tensor,
    cos_sin_cache: torch.Tensor,
    compress_ratio: int = 4,
    norm_eps: float = 1.0e-6,
    rotary_dim: int = 64,
    mrope_section: tuple[int, int, int] = (11, 11, 10),
    mrope_interleaved: bool = True,
    rope_cache: torch.Tensor | None = None,
) -> None:
    ...
```

实现在同一 Triton kernel 中完成 group pooling、Gemma RMSNorm、RoPE/MRoPE
和 compressed-cache store。内核显式把 pooling 结果先舍入 BF16，再进行
FP32 RMSNorm，以匹配当前非融合路径的 BF16 中间物化语义。

## 4. 最小接入设计

草案补丁遵循 Plugin dispatch 边界：

- 在 `FlagGemsBackend` 中添加 FlagGems-vllm Qwen4 符号可用性检查和转发
  wrapper；
- 注册 `default.flagos.qwen4` implementation；
- 模型侧仅在开关与符号 capability 同时成立时于启动期解析一次直接
  callable，并且只在精确 shape/dtype/layout 契约成立时调用；
- 实验期默认关闭，只有
  `VLLM_FL_QWEN4_FUSED_QSA_COMPRESS=1` 时启用；
- guard 不成立时保留原始 compress → norm → RoPE → store 路径。

不应在 stateful kernel 开始执行后通过 `try/except` 动态 fallback；部分写入后
重跑原路径无法证明事务等价。因此 fallback 必须发生在 launch 之前，
由静态 capability/shape guard 决定。草案故意不使用会在调用异常后重新
dispatch 的 `CachedOp`：若融合 kernel 已经 launch 后失败，应让当前请求失败并
回退候选版本，而不是在未知的部分写入状态上运行另一实现。

草案已对当前 Plugin working tree 执行远端只读
`git apply --check`，确认能干净套用；没有执行 `git apply`。

## 5. 精确 guard

只在以下条件全部成立时进入候选：

- 实验开关开启，且 FlagGems-vllm 导出目标 callable；
- `index_head_dim == 128`、`compress_ratio == 4`、`rotary_dim == 64`；
- raw/compressed cache 均为 BF16 `[blocks, page_size, 1, 128]`；
- norm weight 为 contiguous BF16 `[128]`；
- cos/sin cache 为 BF16 `[positions, 64]`；
- block table 为 rank-2 int32/int64；request、logical position 和 compressed slot
  为形状一致的 int32/int64 向量；
- 所有 tensor 在同一 accelerator device，不是 CPU/meta；
- 如有 rope-position cache，其 shape 为 `[raw_blocks, page_size, 1, 3]`、
  dtype 为 int64，与 raw cache 同 device；
- MRoPE section 必须为 `(11, 11, 10)` 且 interleaved 为 true。

`--language-model-only` 会移除 runtime MRoPE 字段，此时
`rope_position_cache is None`。三个逻辑轴使用同一个 1-D position，因此用
检查点 section 作为 lane selector 不改变语义；这一点仍必须由数值测试
和服务回归证明。

## 6. 数值测试矩阵

测试必须比较完整事务，而不是只比较候选 kernel 和某个 Torch 参考。

1. 从同一 raw cache、block table、metadata、norm weight 和 cos/sin cache
   制作两份 compressed-cache clone。
2. baseline 执行当前的
   `qsa_compress_groups_with_ratio -> GemmaRMSNorm -> apply_qsa_rope ->
   qsa_store_cache_rows`。
3. candidate 执行一次融合 op。
4. 比较：
   - 所有有效 compressed slot 的 `max_abs`、`max_rel` 和 `allclose`；
   - 无效 request、负 slot、越界 slot、未满 4-token group 对 sentinel
     cache 的保持；
   - page 边界、非连续 physical page 和 int32/int64 metadata；
   - 1-D RoPE 和三轴 interleaved MRoPE；
   - rows `0/1/8/32/64`，另覆盖 Prefill 中一次完成多个 group 的
     实际 metadata shape。

初始阈值使用 FlagGems-vllm 已有测试边界：BF16
`atol=0.03, rtol=0.02`，同时报告实际最大误差。如果结果能逐位一致，
将门禁收紧为逐位比较。尚需继续执行 QSA selection 和 sparse attention，
检查候选 compressed key 对 top-k index 与最终 attention output 的影响。

## 7. Graph capture/replay 计划

### 独立算子门禁

1. 在专用 stream 上 warm up baseline 和 candidate，排除首次 Triton 编译。
2. 预分配 raw/compressed cache、metadata、weight 和 cos/sin cache；捕获区间内不
   创建 tensor、不做 host sync。
3. capture 一次 candidate，记录 capture 后 cache snapshot。
4. 使用同一地址 replay 两次；两次 replay 后的有效 cache row 必须与
   eager candidate 和首次 capture 一致。
5. 用 sentinel 检查 invalid slot 在 capture/replay 中都未被修改。

### 模型集成门禁

- 使用 graph 服务完成 capture，并对相同 decode batch replay 至少两次；
- dispatch 日志或临时计数器必须证明
  `qwen4_compress_norm_mrope_store_groups -> default.flagos.qwen4`；
- 关闭实验开关后，同一服务必须命中原路径，不能仅从启动成功
  推断 fallback 生效。

## 8. 性能试验与停止条件

在正确性和 graph 门禁全部通过后，才进行性能测量。

- microbenchmark 比较完整 baseline transaction 和候选 transaction；两者
  使用同一 metadata 分布、warmup、重复次数和同步方式。
- 分别覆盖 Decode rows `1/8/32/64` 和 Prefill 的真实 group-completion shape。
- 算子级候选需在主要 shape 上使完整 transaction 提升至少 `5%`，
  才进入服务 A/B/R。
- 服务先在 P1K Mixed 做同配置 A/B/R，再按 P4K、P16K、P32K
  验证长序列可兑现性。

任一以下情况立即停止或回退：

- exact guard 未命中或实际 impl-id 不是 `default.flagos.qwen4`；
- 候选修改 invalid slot/cache row；
- 数值超过预冻结阈值，或 downstream top-k/attention 差异导致最小回归
  失败；
- graph capture 失败、两次 replay 不一致或捕获期出现分配/同步；
- 完整 transaction 微基准提升低于 `5%`；
- Mixed 端到端收益不可兑现，或 Prefill/Decode 任一守护指标超出案例
  预冻结回退边界。

## 9. 尚未解决的 PR 问题

- 草案用环境变量作为实验开关；如候选保留，需决定是否转为 Plugin
  capability/config 并补充用户可见文档。
- `default.flagos.qwen4` 是 FlagGems-vllm 的模型特化，不应放入 T-Head
  vendor backend，除非后续实现使用了 PPU 专有指令或配置。
- 需在 Plugin 单测中证明未安装 FlagGems-vllm、非 BF16、非 128-dim、
  非 ratio-4 和非标准 MRoPE 时全部保留原路径。
- 候选最终保留时，需将当前 Plugin/FlagGems-vllm 的具体 revision、命中证据、
  补丁和回退命令写入 `models/Qwen3.8-Flash-Next/ppu/optimize/`。
