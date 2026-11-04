# env017：统一 FGV 专用算子来源并简化 MLA provider

已更新 PPU-03 / hy4-preview 的实际安装 `/workspace/vllm-plugin-FL`，只改三个既有文件。两个 gems-opt 均保持原 HEAD 和全部源码不变；无 Plugin tests 修改、服务重启或模型请求，未开始 GPQA。

| 文件（vllm_fl/ 下） | 本轮修改与必要性 |
|---|---|
| dispatch/backends/flaggems/impl/top_k_per_row.py | 两个 TopK 改从 FGV 公开导入；保留 Plugin 四参数到固定 FGV 八参数的签名/长度布局适配。数值代码 AST 不变。 |
| dispatch/backends/flaggems/impl/bf16_indexer.py | cache writer 改从 FGV 导入 concat_and_cache_mla。固定 FGV 确实没有 BF16 paged logits，按用户补充指令，仅该算子继续从 flag_gems.fused 导入。其余数值与校验逻辑不变。 |
| dispatch/backends/flaggems/impl/mla_ops.py | 删除重复 PPU 白名单、反复逐算子探测和重复 prefill 选择；一张 adapter→provider 表表达五个必需适配，三种原样转发保留。检查与调用来源一致，FGV 依赖遵循原环境门禁；FG 只检查缺失的 BF16 logits。原注册函数和非 PPU provider 选择保持。164→146 行。 |

当前目标路径来源：TopK prefill/decode、concat_and_cache_mla、concat_mla_q、flash_mla_sparse_fwd、flash_attn_varlen_func 均 FGV；bf16_paged_mqa_logits 为 FG。没有全局自动 fallback，没有把算子挪进 vendor，没有改两个 Gems 或 W8A8 编译边界。原非 PPU FP8/general-quantizer 路径维持官方逻辑，本轮不扩大迁移范围。

完整官方 diff（本地文件 `docs/cases/20261018-hy4-preview-ppu03-migration/plugin-review-env017/full-diff.md`） · 本轮三文件 patch（历史路径当前不可用：`/tmp/hy4-fgv-mla-20261019-01/from-env016.patch`；须从原 revision 或远端证据恢复） · 完整可应用 patch（历史路径当前不可用：`/tmp/hy4-fgv-mla-20261019-01/full.patch`；须从原 revision 或远端证据恢复）

官方基线 8b2033e4；累计12文件（6新增/6修改）+1085/-20。本轮只改三文件，Plugin tests 逐字节等于官方；两基线 strict Git apply/语法通过。完整 patch SHA `f709fe70cbbfe6548a246a0ee1e2124656d34bc2428cb9e0e12a1a478fbb7654`；delta SHA `a951c37ff6500d38bc32675b7b8be25c3d989ed7167001cb42d62c0d352ec4fa`。

独立 PPU device0：TopK prefill/decode 各4行/宽4097/K2048，覆盖0/1/65/4097有效长度与非零起点；cache writer 覆盖 int32/int64 slots、非连续 keys、边界和无效 slots。4个数值用例全部通过 CPU 参考和各2次改变输入的 graph replay。峰值 allocator 234496 bytes、reserved 33554432 bytes。真实函数对象来源、FGV 环境门禁通过；8项静态/mock路由检查包含非 PPU 所有 key 选择与原版一致，但不代表其他平台硬件实测。

安装后 fresh import/所有目标 provider availability 复核通过，615文件清单与实测候选相同，实际 import `/workspace/vllm-plugin-FL/vllm_fl/__init__.py`；旧服务身份不变、health200。服务仍是 env011 内存代码，当前源码的 TP16 启动/graph/C8/分页和完整198题未执行，整体 minimal-regression=incomplete_user_hold，无当前87% gate，无性能结论，PR readiness 待模型验证。

外部证据根 `/workspace/.hy4-preview-migration-20261018-01/fgv-mla-20261019-01`：results/candidate.json、probe-finished.json、installed-import-result.json、routing-result.json、current-source-manifest.json、deployment-result.json、logs/candidate.log；commands/ 保存命令。FGV gems-opt46387d7f / FG gems-opt3ba1d1d9 前后均 clean 且 tracked 摘要相同。

备份 plugin-env016-before.tar.gz SHA `9193da267e2e74d1d7ba1e0612abe926c6953c894cf1befbaa0d38eeb7016348`。回退 `docker exec hy4-preview python -B /workspace/.hy4-preview-migration-20261018-01/fgv-mla-20261019-01/commands/rollback.py`；守卫当前三文件 SHA 后恢复 env016，不操作服务。服务与正式评测保持待用户审阅。

本轮相对 env016 的三文件 diff：

```diff
diff --git a/vllm_fl/dispatch/backends/flaggems/impl/bf16_indexer.py b/vllm_fl/dispatch/backends/flaggems/impl/bf16_indexer.py
index 6ee8c04..dc0187b 100644
--- a/vllm_fl/dispatch/backends/flaggems/impl/bf16_indexer.py
+++ b/vllm_fl/dispatch/backends/flaggems/impl/bf16_indexer.py
@@ -28,7 +28,7 @@ def _validate_cache_write(keys, cache, slot_mapping):
 
 
 def bf16_indexer_cache_write_flaggems(keys, cache, slot_mapping) -> None:
-    from flag_gems import concat_and_cache_mla
+    from flaggems_vllm import concat_and_cache_mla
 
     _validate_cache_write(keys, cache, slot_mapping)
     if slot_mapping.numel() == 0:
diff --git a/vllm_fl/dispatch/backends/flaggems/impl/mla_ops.py b/vllm_fl/dispatch/backends/flaggems/impl/mla_ops.py
index 443589a..168c809 100644
--- a/vllm_fl/dispatch/backends/flaggems/impl/mla_ops.py
+++ b/vllm_fl/dispatch/backends/flaggems/impl/mla_ops.py
@@ -38,63 +38,51 @@ def _flaggems_query_quantizer(implementation):
 
 
 def _get_bf16_operator(name):
-    from .bf16_mla import get_public_operator, sparse_mla
+    from . import bf16_indexer, bf16_mla, top_k_per_row
 
-    if name == "bf16_indexer_cache_write":
-        from .bf16_indexer import bf16_indexer_cache_write_flaggems
-        import flag_gems
-
-        return (
-            bf16_indexer_cache_write_flaggems
-            if callable(getattr(flag_gems, "concat_and_cache_mla", None))
-            else None
-        )
+    # The fixed FGV version lacks BF16 paged logits; only this op uses FG.
     if name == "bf16_indexer_decode":
         import flag_gems.fused as fused
 
-        if not all(
-            callable(getattr(fused, op, None))
-            for op in ("bf16_paged_mqa_logits", "top_k_per_row_decode")
-        ):
+        if not callable(getattr(fused, "bf16_paged_mqa_logits", None)):
             return None
-        from .bf16_indexer import bf16_indexer_decode_flaggems
-
-        return bf16_indexer_decode_flaggems
-    if name in ("top_k_per_row_prefill", "top_k_per_row_decode"):
-        import flag_gems.fused as fused
-        from . import top_k_per_row
-
+    adapters = {
+        "bf16_indexer_cache_write": (
+            bf16_indexer.bf16_indexer_cache_write_flaggems,
+            "concat_and_cache_mla",
+        ),
+        "bf16_indexer_decode": (
+            bf16_indexer.bf16_indexer_decode_flaggems,
+            "top_k_per_row_decode",
+        ),
+        "top_k_per_row_prefill": (
+            top_k_per_row.top_k_per_row_prefill,
+            "top_k_per_row_prefill",
+        ),
+        "top_k_per_row_decode": (
+            top_k_per_row.top_k_per_row_decode,
+            "top_k_per_row_decode",
+        ),
+        "flash_mla_sparse_fwd": (bf16_mla.sparse_mla, "flash_mla_sparse_fwd"),
+    }
+    if name in adapters:
+        implementation, provider = adapters[name]
         return (
-            getattr(top_k_per_row, name)
-            if callable(getattr(fused, name, None))
-            else None
+            implementation if callable(bf16_mla.get_public_operator(provider)) else None
         )
-    if name == "flash_mla_sparse_fwd":
-        return sparse_mla if callable(get_public_operator(name)) else None
-    if name == "mla_prefill_backend":
-        from vllm_fl.attention.mla_prefill import FlagGemsMLAPrefillBackend
-
-        return lambda config: FlagGemsMLAPrefillBackend
-    return get_public_operator(name)
+    if name in ("concat_and_cache_mla", "concat_mla_q", "flash_attn_varlen_func"):
+        return bf16_mla.get_public_operator(name)
+    return None
 
 
 def get_operator(name):
     from vllm.platforms import current_platform
 
-    # Only the current PPU path needs adapters for the fixed BF16 Gems ABI.
+    if name == "mla_prefill_backend":
+        from vllm_fl.attention.mla_prefill import FlagGemsMLAPrefillBackend
+
+        return lambda config: FlagGemsMLAPrefillBackend
     if getattr(current_platform, "vendor_name", None) == "thead":
-        if name not in {
-            "bf16_indexer_cache_write",
-            "bf16_indexer_decode",
-            "top_k_per_row_prefill",
-            "top_k_per_row_decode",
-            "flash_mla_sparse_fwd",
-            "concat_and_cache_mla",
-            "concat_mla_q",
-            "flash_attn_varlen_func",
-            "mla_prefill_backend",
-        }:
-            return None
         return _get_bf16_operator(name)
     if name.startswith("bf16_indexer_"):
         return None
@@ -103,10 +91,6 @@ def get_operator(name):
 
         fn = getattr(flag_gems, name, None)
         return _flaggems_query_quantizer(fn) if callable(fn) else None
-    if name == "mla_prefill_backend":
-        from vllm_fl.attention.mla_prefill import FlagGemsMLAPrefillBackend
-
-        return lambda config: FlagGemsMLAPrefillBackend
     if name == "fp8_fp4_paged_mqa_logits":
         graph_fn = get_flaggems_vllm_operator("fp8_fp4_paged_mqa_logits_graph")
         if callable(graph_fn):
diff --git a/vllm_fl/dispatch/backends/flaggems/impl/top_k_per_row.py b/vllm_fl/dispatch/backends/flaggems/impl/top_k_per_row.py
index e6b6e57..3debbab 100644
--- a/vllm_fl/dispatch/backends/flaggems/impl/top_k_per_row.py
+++ b/vllm_fl/dispatch/backends/flaggems/impl/top_k_per_row.py
@@ -32,7 +32,7 @@ def top_k_per_row_prefill(
     indices: torch.Tensor,
 ) -> None:
     """Select request-relative top-k indices for prefill rows."""
-    from flag_gems.fused import top_k_per_row_prefill as flaggems_topk
+    from flaggems_vllm import top_k_per_row_prefill as flaggems_topk
 
     _validate_common(logits, indices)
     if row_starts.ndim != 1 or row_ends.ndim != 1:
@@ -63,7 +63,7 @@ def top_k_per_row_decode(
     next_n: int,
 ) -> None:
     """Select top-k indices within each decode row's valid token range."""
-    from flag_gems.fused import top_k_per_row_decode as flaggems_topk
+    from flaggems_vllm import top_k_per_row_decode as flaggems_topk
 
     _validate_common(logits, indices)
     if seq_lens.dtype != torch.int32:
```
