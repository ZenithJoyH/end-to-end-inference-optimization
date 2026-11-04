# 收敛后 Plugin 完整差异（测试变更已撤回）

目标：PPU-03 / hy4-preview，实际安装目录 /workspace/vllm-plugin-FL。官方基线为当前已安装HEAD `8b2033e417a535a828a1d7594d36bd33e36e3b57`，不是GitHub不断变化的最新main。本次只读导出，不升级基线。

当前完整差异 **15个生产文件，8新增、7修改，+1327/-14**；`tests/`无tracked/untracked差异。2个已有测试已恢复官方，5个新增测试已删除。生产包源码、Gems和服务实例前后未变；没有发送模型请求、启动评测或重启服务。

- [完整可应用Git补丁](/Users/baai/Documents/ChatGPT/端到端推理优化/.cache/model-record-archives/20261102-record-reconciliation-01/files/docs/cases/20261018-hy4-preview-ppu03-migration/plugin-review-env012/full.patch)
- 逐文件展开的完整diff（本地文件 `docs/cases/20261018-hy4-preview-ppu03-migration/plugin-review-env012/full-diff.md`）
- [机器可读清单、SHA和现场摘录](/Users/baai/Documents/ChatGPT/端到端推理优化/.cache/model-record-archives/20261102-record-reconciliation-01/files/docs/cases/20261018-hy4-preview-ppu03-migration/plugin-review-env012/changes.json)

完整补丁SHA256：`0038f4f205c7cfb1c7bc2cc8ccaf4ec4035245151be84f3690c61ae3c1674c6f`。已静态检查可严格应用到同一官方快照，15个结果文件SHA与现场相同；这不是重新执行模型测试。Git标准diff包括tracked修改与新增文件，已核对tracked文件权限及symlink没有额外变化。setuptools-scm自动生成且Git忽略的 `_version.py` 保持原样，不属于手工补丁。

两个Gems保持干净：FGV gems-opt@46387d7f96050204c1b932f35680a3ea03896fa6，FG gems-opt@3ba1d1d99010de56d12088992f8b0da3444d90ca。

需要明确：**组合已跑通，不等于每个保留文件或每一行都已证明不可删除。** `attention/mla_prefill.py`当前主要是公开能力判断一致性；`reasoning/__init__.py`只有包说明；decode候选排序是保守保留。128行分块的具体阈值、host metadata缓存和超出当前next_n=1的兼容分支也没有逐项不可删除证明。下面分别标明目的、删除影响和证据边界，不把它们统称为启动必需。本轮仅按用户要求撤回测试，未擅自继续改这些生产逻辑。

既有env011记录的182项CPU/mock/parser、设备回归、51组capture、16rank两次replay、C8和13249-token分页/13184-token缓存命中均是此前证据；本次没有重跑。正式198题GPQA继续暂停，没有当前组合87%精度gate。

| 文件（相对仓库根） | diff | 保留必要性判断 |
|---|---|---|
| [vllm_fl/attention/mla_prefill.py](/Users/baai/Documents/ChatGPT/端到端推理优化/.cache/model-record-archives/20261102-record-reconciliation-01/files/docs/cases/20261018-hy4-preview-ppu03-migration/plugin-review-env012/current/vllm_fl/attention/mla_prefill.py) | +2/-9 | 兼容性保留，尚未证明默认启动必需；[说明](#file-1) |
| [vllm_fl/dispatch/backends/flaggems/impl/bf16_indexer.py](/Users/baai/Documents/ChatGPT/端到端推理优化/.cache/model-record-archives/20261102-record-reconciliation-01/files/docs/cases/20261018-hy4-preview-ppu03-migration/plugin-review-env012/current/vllm_fl/dispatch/backends/flaggems/impl/bf16_indexer.py) | +156/-0 | 核心ABI必要，decode排序保守保留；[说明](#file-2) |
| [vllm_fl/dispatch/backends/flaggems/impl/bf16_mla.py](/Users/baai/Documents/ChatGPT/端到端推理优化/.cache/model-record-archives/20261102-record-reconciliation-01/files/docs/cases/20261018-hy4-preview-ppu03-migration/plugin-review-env012/current/vllm_fl/dispatch/backends/flaggems/impl/bf16_mla.py) | +47/-0 | 小head/sink ABI必要；[说明](#file-3) |
| [vllm_fl/dispatch/backends/flaggems/impl/int8_scaled_mm.py](/Users/baai/Documents/ChatGPT/端到端推理优化/.cache/model-record-archives/20261102-record-reconciliation-01/files/docs/cases/20261018-hy4-preview-ppu03-migration/plugin-review-env012/current/vllm_fl/dispatch/backends/flaggems/impl/int8_scaled_mm.py) | +15/-0 | 固定版本INT8提供者必要；[说明](#file-4) |
| [vllm_fl/dispatch/backends/flaggems/impl/mla_ops.py](/Users/baai/Documents/ChatGPT/端到端推理优化/.cache/model-record-archives/20261102-record-reconciliation-01/files/docs/cases/20261018-hy4-preview-ppu03-migration/plugin-review-env012/current/vllm_fl/dispatch/backends/flaggems/impl/mla_ops.py) | +66/-1 | registry/能力选择接入必要；[说明](#file-5) |
| [vllm_fl/dispatch/backends/flaggems/impl/top_k_per_row.py](/Users/baai/Documents/ChatGPT/端到端推理优化/.cache/model-record-archives/20261102-record-reconciliation-01/files/docs/cases/20261018-hy4-preview-ppu03-migration/plugin-review-env012/current/vllm_fl/dispatch/backends/flaggems/impl/top_k_per_row.py) | +100/-0 | 当前TopK接口/索引契约必要；[说明](#file-6) |
| [vllm_fl/dispatch/backends/flaggems/register_ops.py](/Users/baai/Documents/ChatGPT/端到端推理优化/.cache/model-record-archives/20261102-record-reconciliation-01/files/docs/cases/20261018-hy4-preview-ppu03-migration/plugin-review-env012/current/vllm_fl/dispatch/backends/flaggems/register_ops.py) | +12/-0 | 新CachedOp的注册必要；[说明](#file-7) |
| [vllm_fl/models/hy4/attention.py](/Users/baai/Documents/ChatGPT/端到端推理优化/.cache/model-record-archives/20261102-record-reconciliation-01/files/docs/cases/20261018-hy4-preview-ppu03-migration/plugin-review-env012/current/vllm_fl/models/hy4/attention.py) | +20/-3 | 模型接入点必要；[说明](#file-8) |
| [vllm_fl/models/hy4/bf16_indexer.py](/Users/baai/Documents/ChatGPT/端到端推理优化/.cache/model-record-archives/20261102-record-reconciliation-01/files/docs/cases/20261018-hy4-preview-ppu03-migration/plugin-review-env012/current/vllm_fl/models/hy4/bf16_indexer.py) | +379/-0 | BF16缓存/分页/索引编排必要，部分开销优化可再收敛；[说明](#file-9) |
| [vllm_fl/models/hy4/bf16_sparse.py](/Users/baai/Documents/ChatGPT/端到端推理优化/.cache/model-record-archives/20261102-record-reconciliation-01/files/docs/cases/20261018-hy4-preview-ppu03-migration/plugin-review-env012/current/vllm_fl/models/hy4/bf16_sparse.py) | +43/-0 | 缓存/concat/sparse与sink接入必要；[说明](#file-10) |
| [vllm_fl/models/hy4/registration.py](/Users/baai/Documents/ChatGPT/端到端推理优化/.cache/model-record-archives/20261102-record-reconciliation-01/files/docs/cases/20261018-hy4-preview-ppu03-migration/plugin-review-env012/current/vllm_fl/models/hy4/registration.py) | +5/-0 | 保持原reasoning-parser参数必要；[说明](#file-11) |
| [vllm_fl/models/hy4/runtime.py](/Users/baai/Documents/ChatGPT/端到端推理优化/.cache/model-record-archives/20261102-record-reconciliation-01/files/docs/cases/20261018-hy4-preview-ppu03-migration/plugin-review-env012/current/vllm_fl/models/hy4/runtime.py) | +76/-0 | 平台准入与BF16运行契约必要；[说明](#file-12) |
| [vllm_fl/quantization/w8a8/linear.py](/Users/baai/Documents/ChatGPT/端到端推理优化/.cache/model-record-archives/20261102-record-reconciliation-01/files/docs/cases/20261018-hy4-preview-ppu03-migration/plugin-review-env012/current/vllm_fl/quantization/w8a8/linear.py) | +74/-1 | 固定INT8依赖与编译边界必要；[说明](#file-13) |
| [vllm_fl/reasoning/__init__.py](/Users/baai/Documents/ChatGPT/端到端推理优化/.cache/model-record-archives/20261102-record-reconciliation-01/files/docs/cases/20261018-hy4-preview-ppu03-migration/plugin-review-env012/current/vllm_fl/reasoning/__init__.py) | +1/-0 | 工程包入口，未证明硬性必需；[说明](#file-14) |
| [vllm_fl/reasoning/hy_v4_reasoning.py](/Users/baai/Documents/ChatGPT/端到端推理优化/.cache/model-record-archives/20261102-record-reconciliation-01/files/docs/cases/20261018-hy4-preview-ppu03-migration/plugin-review-env012/current/vllm_fl/reasoning/hy_v4_reasoning.py) | +331/-0 | 当前vLLM缺失parser的兼容回移植必要；[说明](#file-15) |

<a id="file-1"></a>

**1. `vllm_fl/attention/mla_prefill.py`**

修改：availability 改为复用 MLA provider 的能力查询，替换原先仅接受 is_cuda() 的检查。

目的：让 prefill backend 的公开支持判断与实际可解析的 PPU/FlagGems provider 一致，兼容显式选择该 backend 的入口。

必要性边界：不能把这个改动称为当前默认启动的硬门槛。当前 BF16 runtime 已绑定 plan.prefill_backend；现场 vLLM 的 MLAAttention 在493行取得该类后直接构造，当前路径不依赖再次调用这个 is_available。它是接口一致性修改，属于可继续单独撤回评估的文件。

证据：当前文件diff；运行时构造调用点的只读摘录见 changes.json 的 native_prefill_constructor_evidence。没有做撤回本文件后的独立启动消融。

[当前完整源码](/Users/baai/Documents/ChatGPT/端到端推理优化/.cache/model-record-archives/20261102-record-reconciliation-01/files/docs/cases/20261018-hy4-preview-ppu03-migration/plugin-review-env012/current/vllm_fl/attention/mla_prefill.py) · [该文件完整diff](/Users/baai/Documents/ChatGPT/端到端推理优化/.cache/model-record-archives/20261102-record-reconciliation-01/files/docs/cases/20261018-hy4-preview-ppu03-migration/plugin-review-env012/per-file/vllm_fl/attention/mla_prefill.py.patch) · [官方基线源码](/Users/baai/Documents/ChatGPT/端到端推理优化/.cache/model-record-archives/20261102-record-reconciliation-01/files/docs/cases/20261018-hy4-preview-ppu03-migration/plugin-review-env012/official/vllm_fl/attention/mla_prefill.py)

<a id="file-2"></a>

**2. `vllm_fl/dispatch/backends/flaggems/impl/bf16_indexer.py`**

新增：BF16 indexer cache写入、公开bf16_paged_mqa_logits调用和decode TopK接口适配。

核心必要性：官方 indexer 路径使用FP8缓存和查询接口；本次保留的PPU路径使用BF16 cache，必须把keys/slot_mapping、paged cache、FP32权重及有效长度传给当前Gems公开接口。否则模型层没有对应的BF16写缓存和decode提供者。

保留边界：decode最后对候选再排序是保守逻辑，用于延续既有候选顺序、避免未经验证的累加顺序变化；尚无独立精度/启动消融证明该排序必须保留，不能把它归为已证实启动必需。显式shape/dtype检查属于支持边界保护。

证据：env011的真实设备分页/MLA回归、服务BF16 decode与DEFAULT provider路径、C8/长分页请求。排序本身没有单独A/B评测；本轮不评测。

[当前完整源码](/Users/baai/Documents/ChatGPT/端到端推理优化/.cache/model-record-archives/20261102-record-reconciliation-01/files/docs/cases/20261018-hy4-preview-ppu03-migration/plugin-review-env012/current/vllm_fl/dispatch/backends/flaggems/impl/bf16_indexer.py) · [该文件完整diff](/Users/baai/Documents/ChatGPT/端到端推理优化/.cache/model-record-archives/20261102-record-reconciliation-01/files/docs/cases/20261018-hy4-preview-ppu03-migration/plugin-review-env012/per-file/vllm_fl/dispatch/backends/flaggems/impl/bf16_indexer.py.patch)

<a id="file-3"></a>

**3. `vllm_fl/dispatch/backends/flaggems/impl/bf16_mla.py`**

新增：公开Gems provider查询与BF16 sparse MLA参数/返回值适配。

核心必要性：当前TP16下每rank只有4个attention heads，固定Gems sparse MLA接口要求64或128 heads。这里填充query和sink、调用公开kernel后裁回4heads，并保持sink语义和输出layout。删除padding会直接违反当前kernel的shape约束。

保留边界：provider查询包含FGV优先及FlagGems可用时回退；核心是配合两个固定仓库提供公开算子。没有逐条删减所有provider分支证明每个fallback都是当前启动必需，也不代表其他平台验证通过。

证据：此前两个公开sparse provider的数值/两次graph replay及实际TP16服务启动/请求。固定provider的head约束来自目标源码。

[当前完整源码](/Users/baai/Documents/ChatGPT/端到端推理优化/.cache/model-record-archives/20261102-record-reconciliation-01/files/docs/cases/20261018-hy4-preview-ppu03-migration/plugin-review-env012/current/vllm_fl/dispatch/backends/flaggems/impl/bf16_mla.py) · [该文件完整diff](/Users/baai/Documents/ChatGPT/端到端推理优化/.cache/model-record-archives/20261102-record-reconciliation-01/files/docs/cases/20261018-hy4-preview-ppu03-migration/plugin-review-env012/per-file/vllm_fl/dispatch/backends/flaggems/impl/bf16_mla.py.patch)

<a id="file-4"></a>

**4. `vllm_fl/dispatch/backends/flaggems/impl/int8_scaled_mm.py`**

新增：从公开FlagGems-vllm triton_scaled_mm取得INT8实现及可用性检查。

必要性：当前FlagGems的scaled_mm为FP8路径，不能承接本模型W8A8的INT8输入/权重；固定FlagGems-vllm提供所需INT8接口。此文件把依赖选择留在DEFAULT backend，而非放入vendor/thead或模型代码。

删除影响：linear.py中的int8_scaled_mm CachedOp无法解析该DEFAULT实现；在空CUDA扩展环境中不能假设存在可替代的native INT8线性实现。该独立小文件也可以合并进现有backend模块，但实现职责仍应留在backend。

证据：env011四组W8A8真实设备数值、空token、两次graph replay和fullgraph，以及服务中DEFAULT INT8提供者。

[当前完整源码](/Users/baai/Documents/ChatGPT/端到端推理优化/.cache/model-record-archives/20261102-record-reconciliation-01/files/docs/cases/20261018-hy4-preview-ppu03-migration/plugin-review-env012/current/vllm_fl/dispatch/backends/flaggems/impl/int8_scaled_mm.py) · [该文件完整diff](/Users/baai/Documents/ChatGPT/端到端推理优化/.cache/model-record-archives/20261102-record-reconciliation-01/files/docs/cases/20261018-hy4-preview-ppu03-migration/plugin-review-env012/per-file/vllm_fl/dispatch/backends/flaggems/impl/int8_scaled_mm.py.patch)

<a id="file-5"></a>

**5. `vllm_fl/dispatch/backends/flaggems/impl/mla_ops.py`**

修改：沿既有registry暴露BF16 cache/decode能力，并在当前PPU选择固定Gems的TopK、concat、varlen和sparse MLA适配。

必要性：模型通过CachedOp/registry请求能力，不能直接import vendor中的Gems实现。本文件负责名称到DEFAULT provider的映射、policy、依赖可用性和PPU的BF16 ABI选择；缺少它，上述适配无法被模型路径解析。

范围：新增选择限vendor_name=thead，其他平台保留原provider接口；实现代码仍在FlagGems backend。BF16新增key在非目标平台不宣称可用。它是当前支持边界，并不是已实现全平台通用支持。

证据：此前registry/policy反例及其他平台mock路由；当前实际服务的DEFAULT provider和源码身份。其他平台硬件未测。

[当前完整源码](/Users/baai/Documents/ChatGPT/端到端推理优化/.cache/model-record-archives/20261102-record-reconciliation-01/files/docs/cases/20261018-hy4-preview-ppu03-migration/plugin-review-env012/current/vllm_fl/dispatch/backends/flaggems/impl/mla_ops.py) · [该文件完整diff](/Users/baai/Documents/ChatGPT/端到端推理优化/.cache/model-record-archives/20261102-record-reconciliation-01/files/docs/cases/20261018-hy4-preview-ppu03-migration/plugin-review-env012/per-file/vllm_fl/dispatch/backends/flaggems/impl/mla_ops.py.patch) · [官方基线源码](/Users/baai/Documents/ChatGPT/端到端推理优化/.cache/model-record-archives/20261102-record-reconciliation-01/files/docs/cases/20261018-hy4-preview-ppu03-migration/plugin-review-env012/official/vllm_fl/dispatch/backends/flaggems/impl/mla_ops.py)

<a id="file-6"></a>

**6. `vllm_fl/dispatch/backends/flaggems/impl/top_k_per_row.py`**

新增：将模型层TopK调用适配为当前FlagGems公开低层接口，补充num_rows、stride、top_k及decode长度布局。

必要性：prefill输出要求有效区间内的row-local索引，模型再转换为request-local索引；decode支持显式每行长度。直接把现有高层调用透传给固定Gems的8参数入口会发生签名/布局不匹配。

保留边界：当前服务没有启用MTP，next_n>1等兼容分支不是当前配置启动的必要证据；保留是接口支持范围选择。范围检查用于避免把不支持输入传给kernel。

证据：此前cached-prefill分页重排、TopK=2/2048、int32/int64 block-table和graph replay，实际13K分页请求。

[当前完整源码](/Users/baai/Documents/ChatGPT/端到端推理优化/.cache/model-record-archives/20261102-record-reconciliation-01/files/docs/cases/20261018-hy4-preview-ppu03-migration/plugin-review-env012/current/vllm_fl/dispatch/backends/flaggems/impl/top_k_per_row.py) · [该文件完整diff](/Users/baai/Documents/ChatGPT/端到端推理优化/.cache/model-record-archives/20261102-record-reconciliation-01/files/docs/cases/20261018-hy4-preview-ppu03-migration/plugin-review-env012/per-file/vllm_fl/dispatch/backends/flaggems/impl/top_k_per_row.py.patch)

<a id="file-7"></a>

**7. `vllm_fl/dispatch/backends/flaggems/register_ops.py`**

修改：注册新的int8_scaled_mm key，impl_id为default.flagos，带真实公开provider可用性检查。

必要性：linear.py使用CachedOp("int8_scaled_mm")；仅定义Python包装而不注册，manager不能按policy解析它。这里沿用既有DEFAULT注册位置，没有把Gems算子伪装为vendor实现。

范围：新增能力key是通用backend能力；当前新增执行调用限PPU线性路径。注册本身不替换其他既有key或平台原有linear调用。

证据：此前policy/vendor-only反例、实际INT8解析和四组W8A8设备验证。

[当前完整源码](/Users/baai/Documents/ChatGPT/端到端推理优化/.cache/model-record-archives/20261102-record-reconciliation-01/files/docs/cases/20261018-hy4-preview-ppu03-migration/plugin-review-env012/current/vllm_fl/dispatch/backends/flaggems/register_ops.py) · [该文件完整diff](/Users/baai/Documents/ChatGPT/端到端推理优化/.cache/model-record-archives/20261102-record-reconciliation-01/files/docs/cases/20261018-hy4-preview-ppu03-migration/plugin-review-env012/per-file/vllm_fl/dispatch/backends/flaggems/register_ops.py.patch) · [官方基线源码](/Users/baai/Documents/ChatGPT/端到端推理优化/.cache/model-record-archives/20261102-record-reconciliation-01/files/docs/cases/20261018-hy4-preview-ppu03-migration/plugin-review-env012/official/vllm_fl/dispatch/backends/flaggems/register_ops.py)

<a id="file-8"></a>

**8. `vllm_fl/models/hy4/attention.py`**

修改：消费runtime plan的indexer工厂、query/weight准备钩子和sparse backend。

必要性：保留官方投影、RoPE、shared/full indexer及sink逻辑，只有cache/算子ABI不同的位置选择BF16路径。没有这些接入点，仍会创建官方FP8 Indexer并执行原生sparse backend预检，新增BF16提供者不会被模型真正使用。

范围：三个字段默认None，未选BF16 plan时沿用原有构造/执行。不是重写整个HY4模型，也没有按模型路径或机器名选择实现。

证据：当前模型构造、实际BF16 cache/indexer模块加载、16rank服务capture/replay及分页请求。

[当前完整源码](/Users/baai/Documents/ChatGPT/端到端推理优化/.cache/model-record-archives/20261102-record-reconciliation-01/files/docs/cases/20261018-hy4-preview-ppu03-migration/plugin-review-env012/current/vllm_fl/models/hy4/attention.py) · [该文件完整diff](/Users/baai/Documents/ChatGPT/端到端推理优化/.cache/model-record-archives/20261102-record-reconciliation-01/files/docs/cases/20261018-hy4-preview-ppu03-migration/plugin-review-env012/per-file/vllm_fl/models/hy4/attention.py.patch) · [官方基线源码](/Users/baai/Documents/ChatGPT/端到端推理优化/.cache/model-record-archives/20261102-record-reconciliation-01/files/docs/cases/20261018-hy4-preview-ppu03-migration/plugin-review-env012/official/vllm_fl/models/hy4/attention.py)

<a id="file-9"></a>

**9. `vllm_fl/models/hy4/bf16_indexer.py`**

新增：BF16 indexer的有状态模型编排，使用vLLM metadata和cache；完成物理页gather、query-key打分、有效区间TopK、索引转换及decode padding。

核心必要性：当前官方Indexer是FP8/native接口，不能仅更换一个函数名就使用BF16缓存。分页读取必须按block_table映射物理页，TopK必须是request-local位置；cache写入和输出buffer修改需在有状态custom op中声明，才能进入当前graph路径。

保留边界：128行分块用于限制长prefill工作区，具体数值128并非kernel ABI硬要求；host metadata缓存是降低重复CPU同步的开销措施，并非单独证明的启动必要条件。短区间直接填索引是为满足当前TopK kernel输入限制。

证据：此前真实物理页重排、缓存复用、短/长边界、两次graph replay及当前两次13249-token服务请求。没有完成正式GPQA。

[当前完整源码](/Users/baai/Documents/ChatGPT/端到端推理优化/.cache/model-record-archives/20261102-record-reconciliation-01/files/docs/cases/20261018-hy4-preview-ppu03-migration/plugin-review-env012/current/vllm_fl/models/hy4/bf16_indexer.py) · [该文件完整diff](/Users/baai/Documents/ChatGPT/端到端推理优化/.cache/model-record-archives/20261102-record-reconciliation-01/files/docs/cases/20261018-hy4-preview-ppu03-migration/plugin-review-env012/per-file/vllm_fl/models/hy4/bf16_indexer.py.patch)

<a id="file-10"></a>

**10. `vllm_fl/models/hy4/bf16_sparse.py`**

新增：在官方HYV4 sink实现上覆盖cache写入、query拼接和BF16 sparse MLA调用，通过CachedOp使用DEFAULT provider。

必要性：当前空CUDA扩展运行时不能依赖native cache/concat/sparse符号；模型还必须把learnable sink、topk_length和实际物理索引传给Gems。该类复用官方其余attention逻辑，避免修改vLLM全局实现。

范围：已删除无行为差异的metadata builder子类和get_builder_cls覆盖，直接继承原生UNIFORM_BATCH metadata。FP8方法显式拒绝是保护边界，当前配置只走BF16。

证据：当前继承原生metadata后的51组capture、16rank各两次replay、sink数值与分页请求。

[当前完整源码](/Users/baai/Documents/ChatGPT/端到端推理优化/.cache/model-record-archives/20261102-record-reconciliation-01/files/docs/cases/20261018-hy4-preview-ppu03-migration/plugin-review-env012/current/vllm_fl/models/hy4/bf16_sparse.py) · [该文件完整diff](/Users/baai/Documents/ChatGPT/端到端推理优化/.cache/model-record-archives/20261102-record-reconciliation-01/files/docs/cases/20261018-hy4-preview-ppu03-migration/plugin-review-env012/per-file/vllm_fl/models/hy4/bf16_sparse.py.patch)

<a id="file-11"></a>

**11. `vllm_fl/models/hy4/registration.py`**

修改：增加5行hy_v4 reasoning parser的惰性注册。官方已有HY4 config/model/loader注册未重写。

必要性：当前服务明确使用--reasoning-parser hy_v4；配对vLLM 0.24.0+empty不自带该parser，官方Plugin基线也没有注册该名字。不注册则不能按原参数解析/启动服务。

范围：仅登记类路径，具体parser保持独立；此前重复general plugin注册已验证。配对vLLM未来自带同等parser时应重新评估此shim。

证据：当前命令行与实际parser模块、此前重复注册和51个parser用例。

[当前完整源码](/Users/baai/Documents/ChatGPT/端到端推理优化/.cache/model-record-archives/20261102-record-reconciliation-01/files/docs/cases/20261018-hy4-preview-ppu03-migration/plugin-review-env012/current/vllm_fl/models/hy4/registration.py) · [该文件完整diff](/Users/baai/Documents/ChatGPT/端到端推理优化/.cache/model-record-archives/20261102-record-reconciliation-01/files/docs/cases/20261018-hy4-preview-ppu03-migration/plugin-review-env012/per-file/vllm_fl/models/hy4/registration.py.patch) · [官方基线源码](/Users/baai/Documents/ChatGPT/端到端推理优化/.cache/model-record-archives/20261102-record-reconciliation-01/files/docs/cases/20261018-hy4-preview-ppu03-migration/plugin-review-env012/official/vllm_fl/models/hy4/registration.py)

<a id="file-12"></a>

**12. `vllm_fl/models/hy4/runtime.py`**

修改：在既有runtime plan中增加三个默认None字段、BF16配置/算子检查和PPU分流，并保留官方其他runtime主体。

必要性：官方基线会因is_cuda()只接受NVIDIA而拒绝当前PPU；当前路径需要BF16 cache、H32/64 D128 indexer、latent512/RoPE64及block64。这里在分配大权重前确认这些契约，并绑定模型钩子和prefill backend。query权重先按BF16缩放再转FP32，不能随意改变运算顺序。

保留边界：_bf16_query的异常函数是防止误走FP8准备路径的保护；所有配置检查和显式backend错误提示不等于每行均是当前输入的启动必经逻辑。没有重新引入独立bf16_runtime.py或修改官方全局metadata。

证据：当前PPU实际构造/源码身份和此前支持范围反例、BF16权重舍入用例；非目标原流程保持的静态/mock核验。

[当前完整源码](/Users/baai/Documents/ChatGPT/端到端推理优化/.cache/model-record-archives/20261102-record-reconciliation-01/files/docs/cases/20261018-hy4-preview-ppu03-migration/plugin-review-env012/current/vllm_fl/models/hy4/runtime.py) · [该文件完整diff](/Users/baai/Documents/ChatGPT/端到端推理优化/.cache/model-record-archives/20261102-record-reconciliation-01/files/docs/cases/20261018-hy4-preview-ppu03-migration/plugin-review-env012/per-file/vllm_fl/models/hy4/runtime.py.patch) · [官方基线源码](/Users/baai/Documents/ChatGPT/端到端推理优化/.cache/model-record-archives/20261102-record-reconciliation-01/files/docs/cases/20261018-hy4-preview-ppu03-migration/plugin-review-env012/official/vllm_fl/models/hy4/runtime.py)

<a id="file-13"></a>

**13. `vllm_fl/quantization/w8a8/linear.py`**

修改：保留原dynamic_per_token_quant_int8 CachedOp，新增INT8 mm CachedOp；在同文件内加入runtime/fake/opaque注册和PPU调用分支。

核心必要性：固定Gems组合下要选择支持INT8的FGV实现；先前直接让Dynamo跟踪Gems包装时在jit_function.params等Python控制流中失败。opaque custom op把这些控制流留在运行时，fake提供输出shape/dtype，支持当前FULL_DECODE_ONLY编译/capture。

范围：没有graph.py；其他平台保留官方linear调用，PPU分支仍走原CachedOp/policy。is_supported提前检查两个提供者是可用性保护，不是额外量化算法；原权重变换和can_implement逻辑不改。

证据：此前Dynamo失败记录、四组真实设备W8A8数值/两次replay/fullgraph/空输入，当前模型capture/replay；去掉PPU分支后类AST与官方一致。

[当前完整源码](/Users/baai/Documents/ChatGPT/端到端推理优化/.cache/model-record-archives/20261102-record-reconciliation-01/files/docs/cases/20261018-hy4-preview-ppu03-migration/plugin-review-env012/current/vllm_fl/quantization/w8a8/linear.py) · [该文件完整diff](/Users/baai/Documents/ChatGPT/端到端推理优化/.cache/model-record-archives/20261102-record-reconciliation-01/files/docs/cases/20261018-hy4-preview-ppu03-migration/plugin-review-env012/per-file/vllm_fl/quantization/w8a8/linear.py.patch) · [官方基线源码](/Users/baai/Documents/ChatGPT/端到端推理优化/.cache/model-record-archives/20261102-record-reconciliation-01/files/docs/cases/20261018-hy4-preview-ppu03-migration/plugin-review-env012/official/vllm_fl/quantization/w8a8/linear.py)

<a id="file-14"></a>

**14. `vllm_fl/reasoning/__init__.py`**

新增：只有一行包说明docstring，没有注册、分支或初始化操作。

保留理由：与独立reasoning parser目录对应的常规显式包入口。

必要性边界：没有启动功能必要性证据，不能把这1行称为PPU/HY4的硬性适配。当前setuptools使用packages.find；namespace包等替代组织方式仍需按打包方式决定。它属于可以继续省略/合并的工程文件。

证据：完整文件只有docstring；此前成功导入不证明删除它就会失败。本轮按要求只撤回测试，没有改生产文件。

[当前完整源码](/Users/baai/Documents/ChatGPT/端到端推理优化/.cache/model-record-archives/20261102-record-reconciliation-01/files/docs/cases/20261018-hy4-preview-ppu03-migration/plugin-review-env012/current/vllm_fl/reasoning/__init__.py) · [该文件完整diff](/Users/baai/Documents/ChatGPT/端到端推理优化/.cache/model-record-archives/20261102-record-reconciliation-01/files/docs/cases/20261018-hy4-preview-ppu03-migration/plugin-review-env012/per-file/vllm_fl/reasoning/__init__.py.patch)

<a id="file-15"></a>

**15. `vllm_fl/reasoning/hy_v4_reasoning.py`**

新增：从vLLM主线固定commit 5d20979fc90a38f450e0fb89661b271926a3061a回移植HYV4 parser，适配当前DeltaMessage导入路径。

必要性：当前vLLM缺少HYV4 parser，而服务需要hy_v4；此前HYV3 shim不能正确覆盖HYV4 suffix、起始思考token和no_think等语义。用户已明确要求按当前主线语义调整，因此保留主线完整提取/请求模式逻辑。

范围：331行主要为上游parser代码，不是针对PPU重写的逻辑。当前DeltaMessage位于vllm.entrypoints.openai.engine.protocol；后续vLLM包含兼容实现时可移除回移植并使用原生注册。

证据：此前51个parser用例（包含流式、no_think、suffix等）和当前实际服务响应；完整高推理GPQA尚未运行。

[当前完整源码](/Users/baai/Documents/ChatGPT/端到端推理优化/.cache/model-record-archives/20261102-record-reconciliation-01/files/docs/cases/20261018-hy4-preview-ppu03-migration/plugin-review-env012/current/vllm_fl/reasoning/hy_v4_reasoning.py) · [该文件完整diff](/Users/baai/Documents/ChatGPT/端到端推理优化/.cache/model-record-archives/20261102-record-reconciliation-01/files/docs/cases/20261018-hy4-preview-ppu03-migration/plugin-review-env012/per-file/vllm_fl/reasoning/hy_v4_reasoning.py.patch)

测试清理原始回执：`/workspace/.hy4-preview-migration-20261018-01/review-test-cleanup-20261019-01/cleanup-result.json`；删除前备份：`tests-before.tar.gz`，SHA 1f768d3e2fd0d6cd9518e075199dbbda8c7a0b597a24ba043e7673e2b1a77505。历史回归脚本和原始结果保留在外部证据根，不加入当前Plugin补丁。
