# env018：完整 Plugin review 与 TopK 共享接口收敛

已逐文件审查 env017 相对官方的全部12个生产文件，核验615文件安装清单、实际import和两个Gems身份。发现一处明确应修的问题：PPU共享TopK被改为HY4专用4参数ABI，官方PortableSparseAttnIndexer等调用方仍按8参数调用。原函数绑定可稳定重现TypeError；这属于我新增适配层扩大了共享接口影响，并非数值误差。

已部署修复：删除整个86行TopK adapter文件，两个共享key恢复FGV原函数；HY4 prefill在原CachedOp调用处传rows/stride/K，HY4 BF16 decode组合直接调用FGV TopK，必要的单token/长度/类型/device保护留在组合边界。mla_ops适配映射5→3，146→144行。runtime仅纠正PPU无原生FP8的注释。

本轮4文件修改、1个新增文件撤回；相对官方由12文件+1085/-20收敛为**11文件（5新增/6修改）+1021/-20，净减少64行**。其余7个已修改文件逐字节不变。两个gems-opt保持FGV46387d7f / FG3ba1d1d9、clean及tracked摘要相同，Plugin tests仍官方字节，无vLLM/权重/挂载修改。

完整官方diff（本地文件 `docs/cases/20261018-hy4-preview-ppu03-migration/plugin-review-env018/full-diff.md`） · 本轮delta patch（历史路径当前不可用：`/tmp/hy4-review-20261019-01/from-env017.patch`；须从原 revision 或远端证据恢复） · 完整可应用patch（历史路径当前不可用：`/tmp/hy4-review-20261019-01/full.patch`；须从原 revision 或远端证据恢复）

| 文件（均位于 vllm_fl/） | 审查结论、保留理由与边界 |
|---|---|
| dispatch/backends/flaggems/impl/top_k_per_row.py | **整份删除**。FGV已提供原8参数接口，4参数包装改变共享key的ABI，会使原调用方在Python绑定时TypeError；HY4在调用处传齐参数即可。 |
| dispatch/backends/flaggems/impl/mla_ops.py | 收回两条TopK adapter映射，返回FGV原函数，仍受FGV环境门禁。只保留BF16 cache、BF16 decode组合和sparse头数适配。注册函数AST仍官方；PPU不可达FP8路线不启用，其他平台provider选择维持。 |
| dispatch/backends/flaggems/impl/bf16_indexer.py | 保留。BF16缓存键需适配concat_and_cache_mla的空RoPE/slot ABI，decode组合FG BF16 paged logits和FGV TopK，仍需布局/类型/单token保护。将原包装中的必要保护收回该组合边界并在kernel前检查；cache及logits数学函数AST不变。 |
| dispatch/backends/flaggems/impl/bf16_mla.py | 保留，字节不变。当前TP16每rank4个MLA query heads，而固定FGV sparse API要求64/128，补Q heads和sink后裁回输出，属于provider ABI适配；FGV环境门禁不变。不复制库kernel，不把它放入vendor。 |
| dispatch/backends/flaggems/impl/quantization.py | 保留，字节不变。env016已实际重现FGV量化libentry被Dynamo展开失败；仅量化custom-op/fake边界必要，不能因“减少包装”再删除。原quant CachedOp/环境选择/数值fallback不变，没有整层linear包装。其他平台硬件未测。 |
| models/hy4/attention.py | 保留，字节不变。factory/prepare/sparse backend三个可选hook让PPU换为BF16索引缓存和路径，避免进入原FP8量化/cache与缺失原生后端；非PPU继续原路径，sink规则保持。再删需用其他模型层路由补回，并无当前证据更简单。 |
| models/hy4/bf16_indexer.py | 保留metadata/分页/prefill/decode编排、短范围无排序分支和opaque graph边界；本轮仅TopK调用补rows/strides/K，纠正短范围注释。QK、BF16 ReLU/加权/求和顺序、offset、页读取及padding AST保持。暂不加batch融合/host缓存/新kernel，后续算法精简须正式精度支持。 |
| models/hy4/bf16_sparse.py | 保留，字节不变。复用原vLLM metadata/builder与HY4 sink语义，仅在当前缺原生实现的cache/concat/sparse入口调用DEFAULT provider；局部子类避免扩大进程级替换。尚未做删除该层的整模型消融，不称唯一最小方案。 |
| models/hy4/runtime.py | 保留选择和输入/能力保护。PPU无原生FP8，当前BF16兼容路径及H/D/block/dtype/非spec约束合理；其他平台仍官方。只纠正注释，整个AST与env017相同。没有转回FP8或新建INT8 Indexer。 |
| models/hy4/registration.py | 保留5行lazy reasoning parser注册，文件字节不变。实际vLLM0.24+empty缺该HY4 parser，而启动参数指定hy_v4；不是重做模型注册/loader。原官方注册结构保持。 |
| quantization/w8a8/linear.py | 保留FGV triton_scaled_mm直接调用和zero-token guard，字节不变。前者遵循用户明确指定；后者保护空输入。原动态quant CachedOp与官方weight/layout/scale/bias方法保持，不新增GEMM dispatch或整层custom-op。 |
| reasoning/hy_v4_reasoning.py | 保留331行主线backport，字节不变，SHA再次匹配已证明的vLLM@5d20979f源码等价回执。仅DeltaMessage import适配0.24；不能为缩短代码改写请求模式、token后缀与streaming边界。没有把它继续做成PPU特例。 |

目前不建议继续机械删除剩余模块：BF16模型编排、库ABI适配与模型sink语义有不同职责，合并到一个文件或vendor会重新混淆边界。没有证据支持删掉必要量化编译边界，也没有以FP8/INT8重写Indexer。当前保留路径仍不是经整模型消融证明的“绝对最小补丁”；尤其TP16新服务、长缓存、完整GPQA尚未执行。

验证与结论边界：

| 检查 | 当前结果 |
|---|---|
| 旧共享TopK接口 | static binding：两个原8参数调用均TypeError，回执冻结 |
| 新共享TopK | 真实函数identity等于FGV公共函数，签名8参数；FGV环境门禁与原policy保持 |
| 真实PPU共享prefill/decode | 各4行/宽4097/K2048，含0/1/65/4097长度与非零起点，CPU参考和各2次改变输入graph replay通过 |
| HY4实际prefill调用处 | 保持原BF16算术和offset，命中default.flagos，CPU参考及2次graph replay通过 |
| HY4 BF16 decode组合 | FG BF16分页logits→FGV TopK，H32/D128/block64，长度65/4097，改变物理页映射和峰值后的2次graph replay通过 |
| 输入保护 | 5项非法metadata在kernel launch前拒绝；无设备故障 |
| 非PPU/缺符号/policy | 8项mock/static路由检查通过，非PPU所有key与前版选择一致；不冒充其他平台硬件通过 |
| 工程和源码 | 全量语法、fatal lint、两基线strict Git apply、9项static review断言通过；W8A8/parser/sparse/cache关键源码字节或数值AST保持 |
| 安装复核 | 614文件与实测候选相同（含未变的ignored _version.py），fresh import/目标provider/TopK身份与8参签名通过；旧service07健康200、身份不变 |
| 整模型/正式精度 | 未重启服务、模型请求0、GPQA未开始，heartbeat暂停。新源码TP16启动/graph/C8/分页/198题均未验证，无87%gate，无性能提升结论 |

独立device0峰值allocator 28958720 bytes、reserved134217728 bytes。算子作用域minimal-regression passed；服务/模型整体incomplete_user_hold。issue review-topk-abi-001为confirmed Python ABI scope、修复已验证，未观测/未测试模型分数影响。PR readiness仍needs_revision_pending_model_validation。

源码：PPU-03 / hy4-preview / `/workspace/vllm-plugin-FL`，官方HEAD `8b2033e417a535a828a1d7594d36bd33e36e3b57`。完整patch SHA `90ec637b7ea554042a0e5ba87948a6377794a80677bf1edc90226ecfc240f0f9`；delta SHA `a6c522f90c32ad05e436ba0d7c4a1436e17105bc84530efc2c1e5147015b2000`。

外部证据根 `/workspace/.hy4-preview-migration-20261018-01/review-20261019-01`：baseline-abi-failure.json、results/candidate.json、probe-finished.json、routing-result.json、static-review-result.json、installed-import-result.json、deployment-result.json、current-source-manifest.json、logs/candidate.log，commands/保存命令。两个Gems和服务在probe/部署/安装复核前后均校验。

备份 plugin-env017-before.tar.gz SHA `8c3445b3c77a6a234de5457581cc38be5f58a8ad818a125e509bf491e132e80b`，包含5路径及撤回的TopK文件。回退 `docker exec hy4-preview python -B /workspace/.hy4-preview-migration-20261018-01/review-20261019-01/commands/rollback.py`，仅恢复本轮5路径并守卫当前SHA，不操作服务。

本轮delta：

```diff
diff --git a/vllm_fl/dispatch/backends/flaggems/impl/bf16_indexer.py b/vllm_fl/dispatch/backends/flaggems/impl/bf16_indexer.py
index dc0187b..d022e5e 100644
--- a/vllm_fl/dispatch/backends/flaggems/impl/bf16_indexer.py
+++ b/vllm_fl/dispatch/backends/flaggems/impl/bf16_indexer.py
@@ -5,8 +5,6 @@ from __future__ import annotations
 
 import torch
 
-from .top_k_per_row import top_k_per_row_decode
-
 
 def _validate_cache_write(keys, cache, slot_mapping):
     if keys.ndim != 2 or cache.ndim != 3 or slot_mapping.ndim != 1:
@@ -107,6 +105,20 @@ def bf16_indexer_decode_flaggems(
     range top-k are one implementation concern and must
     not leak into the model adapter.
     """
+    from flaggems_vllm import top_k_per_row_decode
+
+    if next_n != 1:
+        raise NotImplementedError("HY4 BF16 indexer supports single-token decode only")
+    if seq_lens.shape not in ((q.shape[0],), (q.shape[0], 1)):
+        raise ValueError("seq_lens must contain one length per decode row")
+    if seq_lens.dtype != torch.int32:
+        raise TypeError("seq_lens must be int32")
+    if indices.ndim != 2 or indices.dtype != torch.int32:
+        raise ValueError("Row-wise top-k expects INT32 indices [rows, top_k]")
+    if indices.shape[0] != q.shape[0]:
+        raise ValueError("query and indices must have the same number of rows")
+    if seq_lens.device != q.device or indices.device != q.device:
+        raise ValueError("query, seq_lens and indices must share a device")
     logits = _bf16_paged_mqa_logits_flaggems(
         q,
         cache,
@@ -117,7 +129,16 @@ def bf16_indexer_decode_flaggems(
         max_context_len=max_context_len,
         clean_logits=clean_logits,
     )
-    top_k_per_row_decode(logits, seq_lens, indices, next_n=next_n)
+    top_k_per_row_decode(
+        logits,
+        next_n,
+        seq_lens.reshape(-1).contiguous(),
+        indices,
+        logits.shape[0],
+        logits.stride(0),
+        logits.stride(1),
+        indices.shape[1],
+    )
 
 
 __all__ = [
diff --git a/vllm_fl/dispatch/backends/flaggems/impl/mla_ops.py b/vllm_fl/dispatch/backends/flaggems/impl/mla_ops.py
index 168c809..3eef6c0 100644
--- a/vllm_fl/dispatch/backends/flaggems/impl/mla_ops.py
+++ b/vllm_fl/dispatch/backends/flaggems/impl/mla_ops.py
@@ -38,7 +38,7 @@ def _flaggems_query_quantizer(implementation):
 
 
 def _get_bf16_operator(name):
-    from . import bf16_indexer, bf16_mla, top_k_per_row
+    from . import bf16_indexer, bf16_mla
 
     # The fixed FGV version lacks BF16 paged logits; only this op uses FG.
     if name == "bf16_indexer_decode":
@@ -55,14 +55,6 @@ def _get_bf16_operator(name):
             bf16_indexer.bf16_indexer_decode_flaggems,
             "top_k_per_row_decode",
         ),
-        "top_k_per_row_prefill": (
-            top_k_per_row.top_k_per_row_prefill,
-            "top_k_per_row_prefill",
-        ),
-        "top_k_per_row_decode": (
-            top_k_per_row.top_k_per_row_decode,
-            "top_k_per_row_decode",
-        ),
         "flash_mla_sparse_fwd": (bf16_mla.sparse_mla, "flash_mla_sparse_fwd"),
     }
     if name in adapters:
@@ -70,7 +62,13 @@ def _get_bf16_operator(name):
         return (
             implementation if callable(bf16_mla.get_public_operator(provider)) else None
         )
-    if name in ("concat_and_cache_mla", "concat_mla_q", "flash_attn_varlen_func"):
+    if name in (
+        "top_k_per_row_prefill",
+        "top_k_per_row_decode",
+        "concat_and_cache_mla",
+        "concat_mla_q",
+        "flash_attn_varlen_func",
+    ):
         return bf16_mla.get_public_operator(name)
     return None
 
diff --git a/vllm_fl/dispatch/backends/flaggems/impl/top_k_per_row.py b/vllm_fl/dispatch/backends/flaggems/impl/top_k_per_row.py
deleted file mode 100644
index 3debbab..0000000
--- a/vllm_fl/dispatch/backends/flaggems/impl/top_k_per_row.py
+++ /dev/null
@@ -1,86 +0,0 @@
-# SPDX-License-Identifier: Apache-2.0
-"""FlagGems adapters for row-wise top-k capabilities."""
-
-from __future__ import annotations
-
-import torch
-
-
-def _normalize_decode_lengths(seq_lens: torch.Tensor, num_rows: int, next_n: int):
-    if next_n != 1:
-        raise NotImplementedError("PPU HY4 BF16 supports single-token decode only")
-    if seq_lens.shape not in ((num_rows,), (num_rows, 1)):
-        raise ValueError("seq_lens must contain one length per decode row")
-    return seq_lens.reshape(-1).contiguous()
-
-
-def _validate_common(logits: torch.Tensor, indices: torch.Tensor) -> None:
-    if logits.ndim != 2 or logits.dtype != torch.float32:
-        raise ValueError("Row-wise top-k expects FP32 logits [rows, width]")
-    if indices.ndim != 2 or indices.dtype != torch.int32:
-        raise ValueError("Row-wise top-k expects INT32 indices [rows, top_k]")
-    if logits.shape[0] != indices.shape[0]:
-        raise ValueError("logits and indices must have the same number of rows")
-    if logits.device != indices.device:
-        raise ValueError("logits and indices must share a device")
-
-
-def top_k_per_row_prefill(
-    logits: torch.Tensor,
-    row_starts: torch.Tensor,
-    row_ends: torch.Tensor,
-    indices: torch.Tensor,
-) -> None:
-    """Select request-relative top-k indices for prefill rows."""
-    from flaggems_vllm import top_k_per_row_prefill as flaggems_topk
-
-    _validate_common(logits, indices)
-    if row_starts.ndim != 1 or row_ends.ndim != 1:
-        raise ValueError("row_starts and row_ends must be 1D")
-    if row_starts.shape[0] != logits.shape[0] or row_ends.shape != row_starts.shape:
-        raise ValueError("prefill ranges must contain one start/end per row")
-    if row_starts.dtype != torch.int32 or row_ends.dtype != torch.int32:
-        raise TypeError("prefill row ranges must be int32")
-    if logits.device != row_starts.device or logits.device != row_ends.device:
-        raise ValueError("logits, row ranges and indices must share a device")
-    flaggems_topk(
-        logits,
-        row_starts.contiguous(),
-        row_ends.contiguous(),
-        indices,
-        logits.shape[0],
-        logits.stride(0),
-        logits.stride(1),
-        indices.shape[1],
-    )
-
-
-def top_k_per_row_decode(
-    logits: torch.Tensor,
-    seq_lens: torch.Tensor,
-    indices: torch.Tensor,
-    *,
-    next_n: int,
-) -> None:
-    """Select top-k indices within each decode row's valid token range."""
-    from flaggems_vllm import top_k_per_row_decode as flaggems_topk
-
-    _validate_common(logits, indices)
-    if seq_lens.dtype != torch.int32:
-        raise TypeError("seq_lens must be int32")
-    if logits.device != seq_lens.device:
-        raise ValueError("logits, seq_lens and indices must share a device")
-    kernel_seq_lens = _normalize_decode_lengths(seq_lens, logits.shape[0], next_n)
-    flaggems_topk(
-        logits,
-        1,
-        kernel_seq_lens,
-        indices,
-        logits.shape[0],
-        logits.stride(0),
-        logits.stride(1),
-        indices.shape[1],
-    )
-
-
-__all__ = ["top_k_per_row_decode", "top_k_per_row_prefill"]
diff --git a/vllm_fl/models/hy4/bf16_indexer.py b/vllm_fl/models/hy4/bf16_indexer.py
index 02842b4..8f490fe 100644
--- a/vllm_fl/models/hy4/bf16_indexer.py
+++ b/vllm_fl/models/hy4/bf16_indexer.py
@@ -39,7 +39,7 @@ def _paged_sequence(kv_cache, block_table, seq_len):
 
 
 def _fill_hyv4_full_range_indices(row_starts, row_ends, request_start, output):
-    """Handle short rows which the radix TopK provider cannot accept."""
+    """Return the whole valid range when no ranking is needed."""
     if output.numel() == 0:
         return
     positions = torch.arange(
@@ -63,7 +63,10 @@ def _select_topk_row(q, weights, keys, offset: int, output):
     logits = _hyv4_weighted_relu_reduce(scores, weights)
     starts = torch.zeros((1,), dtype=torch.int32, device=logits.device)
     ends = torch.full_like(starts, keys.shape[0])
-    _top_k_per_row_prefill(logits, starts, ends, output)
+    _top_k_per_row_prefill(
+        logits, starts, ends, output,
+        logits.shape[0], logits.stride(0), logits.stride(1), output.shape[1],
+    )
     valid = output >= 0
     output.add_(offset)
     output.masked_fill_(~valid, -1)
diff --git a/vllm_fl/models/hy4/runtime.py b/vllm_fl/models/hy4/runtime.py
index 1d82bd1..74f8b97 100644
--- a/vllm_fl/models/hy4/runtime.py
+++ b/vllm_fl/models/hy4/runtime.py
@@ -221,8 +221,8 @@ def validate_hy4_runtime(vllm_config) -> HY4RuntimePlan:
 
     from vllm_fl.dispatch.types import BackendImplKind
 
-    # The fixed PPU Gems revision uses the BF16 indexer ABI. Do not change
-    # the official runtime selection for other platforms.
+    # PPU has no native FP8 support; retain the BF16 compatibility path.
+    # Other platforms keep the official runtime selection.
     if getattr(current_platform, "vendor_name", None) == "thead":
         return validate_bf16_hy4_runtime(vllm_config)
     if not current_platform.is_cuda():
```
