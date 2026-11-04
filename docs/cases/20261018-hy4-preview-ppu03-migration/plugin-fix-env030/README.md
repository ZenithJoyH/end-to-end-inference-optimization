# env030：BF16 indexer 分段边界修复

已直接修改 PPU-03/hy4-preview 安装目录 `/workspace/vllm-plugin-FL/vllm_fl/models/hy4/bf16_indexer.py`。两个gems-opt固定，未改vLLM、测试、权重或tokenizer，未开始评测。

新增10行：导入当前配置，在BF16 indexer构造处依照原attention分段编译条件，幂等加入 `vllm::hyv4_bf16_sparse_attn_indexer`。该op读取批次metadata、写indexer KV和TopK；如同原生sparse indexer，必须在PIECEWISE图段外执行。否则dummy捕获时metadata=None，图回放只填-1并跳过真实索引。算子计算和dispatch未改变，未增加通用GraphWrapper/平台特例。

原生FX分段和真实注册CUDA custom-op capture/replay复现已通过；后者stub cache writer，仅证明动态host路径机制。五项构造契约覆盖幂等、原列表保留、未编译和显式无分段反例。当前真实模型启动/9 smoke-C8/同题2次/三阶段16rank各2step replay和两次13249token分页通过，实际prefix hit 13184.0 tokens；前后身份一致。非PPU硬件未测试，无性能/完整精度结论。

本轮相对env027的完整一文件差异：

```diff
--- a/vllm_fl/models/hy4/bf16_indexer.py
+++ b/vllm_fl/models/hy4/bf16_indexer.py
@@ -4,6 +4,7 @@
 from __future__ import annotations
 import torch
 from torch import nn
+from vllm.config import get_current_vllm_config
 from vllm.forward_context import get_forward_context
 from vllm.platforms import current_platform
 from vllm.model_executor.models.deepseek_v2 import DeepseekV32IndexerCache
@@ -141,6 +142,15 @@
             raise ValueError("HYV4 BF16 paged indexer requires head_dim=128")
         if cache_config.block_size != 64:
             raise ValueError("HYV4 BF16 paged indexer requires block_size=64")
+        # This op reads per-batch metadata, just like the native sparse indexer.
+        # PIECEWISE capture uses metadata=None; keep the op outside graph segments.
+        compilation_config = get_current_vllm_config().compilation_config
+        op_name = "vllm::hyv4_bf16_sparse_attn_indexer"
+        if (
+            compilation_config.is_attention_compiled_piecewise()
+            and op_name not in compilation_config.splitting_ops
+        ):
+            compilation_config.splitting_ops.append(op_name)
         self.k_cache = DeepseekV32IndexerCache(
             head_dim=head_dim,
             dtype=torch.bfloat16,
```

[完整实验、原始证据路径和验收状态](../../../../models/Hy4-preview/ppu/20261018-hy4-preview-ppu03-migration/optimize/env-030.md)。
