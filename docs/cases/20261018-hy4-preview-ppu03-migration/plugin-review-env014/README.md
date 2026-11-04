# env014：scaled_mm 按现有环境变量直接导入

已更新 PPU-03 / hy4-preview 中实际安装的 `/workspace/vllm-plugin-FL`。官方基线仍为 `8b2033e417a535a828a1d7594d36bd33e36e3b57`。

本轮只改三个路径：`linear.py` 撤回INT8 dispatch并按环境变量导入；`register_ops.py`完全恢复官方；新增的`impl/int8_scaled_mm.py`删除。最终相对官方为**11文件（6新增/5修改），+1145/-5**。没有任何测试文件差异。

选择规则沿用已有环境变量，两个调用入口都采用函数内惰性导入：

```python
if fl_envs.VLLM_FL_USE_FLAGGEMS_VLLM:
    from flaggems_vllm import triton_scaled_mm as scaled_mm
else:
    from flag_gems import scaled_mm
```

保留原`dynamic_per_token_quant_int8` CachedOp、PPU opaque custom op/fake，以及INT8权重/scale/bias/out_dtype处理。未新增dispatch key、环境变量或provider包装。显式启用FGV但缺包时报错，不静默换库；env0不导入FGV。is_supported恢复官方AST。

完整diff（本地文件 `docs/cases/20261018-hy4-preview-ppu03-migration/plugin-review-env014/full-diff.md`） · 完整Git补丁（历史路径当前不可用：`/tmp/hy4-scaled-mm-20261019-01/full.patch`；须从原 revision 或远端证据恢复） · 相对env013的三路径差异（历史路径当前不可用：`/tmp/hy4-scaled-mm-20261019-01/from-env013.patch`；须从原 revision 或远端证据恢复）

完整补丁SHA256 `6a74255c65d2553819dd8ea018b815c665260bb2e9127fc3aa7d20f7c549f0be`；三路径delta SHA `a32b271186788edee81f9b495d8d707164b33126a96897790c7b09fe232e2580`。部署后615个regular文件（含原样生成_version.py）逐项核对，补丁与本地候选相同。文件权限及symlink未漂移。

验证：全部Python语法、两基准严格git apply和内容校验、linear.py Ruff F类检查通过；隔离AST检查覆盖opaque runtime、PPU apply、非PPU apply的env0/1共6个路由组合和1个缺包反例，检查参数原样传递且原CachedOp/fake/权重处理保持。上述是stub导入/调用契约检查，没有真实算子、GPU数值、编译、capture或模型运行，不代表env0在当前固定Gems上支持INT8。

两个gems-opt HEAD/branch/clean和tracked源码SHA摘要前后不变：FGV46387d7f96050204c1b932f35680a3ea03896fa6，FG3ba1d1d99010de56d12088992f8b0da3444d90ca。服务身份前后相同，未重启、未请求模型、未开始评测，heartbeat保持暂停。当前新源码不能继承旧env011的启动/graph/分页或精度通过；PR readiness仍needs_revision，87%完整198题gate未签发。

本轮没有更改BF16 Indexer。此前澄清仍有效：其权重本来是BF16，但官方投影后走FP8索引；新增BF16执行路径是兼容方案选择，未证明是唯一或最小方案，不由W8A8权重强制要求。其他硬件未测，无性能提升声明。

| 保留文件 | diff | 职责 |
|---|---|---|
| `vllm_fl/dispatch/backends/flaggems/impl/bf16_indexer.py` | +126/-0 | BF16分页cache写入和decode的Gems ABI适配；非权重量化逻辑。 |
| `vllm_fl/dispatch/backends/flaggems/impl/bf16_mla.py` | +52/-0 | 公开sparse provider的head补齐/裁回与sink ABI。 |
| `vllm_fl/dispatch/backends/flaggems/impl/mla_ops.py` | +66/-1 | 将BF16/TopK/MLA提供者接入现有DEFAULT registry。 |
| `vllm_fl/dispatch/backends/flaggems/impl/top_k_per_row.py` | +86/-0 | 固定FlagGems TopK低层签名、有效区间及索引契约。 |
| `vllm_fl/models/hy4/attention.py` | +20/-3 | 在官方模型边界消费BF16 runtime plan钩子，其他结构保留。 |
| `vllm_fl/models/hy4/bf16_indexer.py` | +273/-0 | BF16 Indexer metadata、物理页、TopK索引及有状态graph边界。 |
| `vllm_fl/models/hy4/bf16_sparse.py` | +43/-0 | 复用官方HY4 sink/metadata并接入cache、concat与sparse provider。 |
| `vllm_fl/models/hy4/registration.py` | +5/-0 | 配套vLLM缺失的hy_v4 parser惰性注册。 |
| `vllm_fl/models/hy4/runtime.py` | +69/-0 | 当前PPU BF16 plan及dtype/shape支持条件。 |
| `vllm_fl/quantization/w8a8/linear.py` | +74/-1 | 原量化CachedOp、PPU opaque/fake边界，以及按已有环境变量直接导入scaled_mm。 |
| `vllm_fl/reasoning/hy_v4_reasoning.py` | +331/-0 | 用户要求按vLLM主线语义回移植、当前版本缺少的HYV4 parser。 |

外部证据根 `/workspace/.hy4-preview-migration-20261018-01/scaled-mm-20261019-01`。原始full.patch、from-env013.patch、commands/和deployment-result.json存于该根。修改前备份plugin-env013-before.tar.gz SHA256 `5290239f4194073a5b407766cb98dbffa0631903f01afdff845f3419a9e45f1f`；commands/rollback.py只恢复本轮三个路径且有后续修改保护，不重启服务。
