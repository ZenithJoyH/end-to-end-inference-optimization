# PPU HY4 最小执行链审阅候选（env013）

已部署到 PPU-03 / hy4-preview 的实际安装源码 `/workspace/vllm-plugin-FL`，官方基线固定为 `8b2033e417a535a828a1d7594d36bd33e36e3b57`。本轮没有升级官方基线。

相对官方：**13 个文件（7 新增、6 修改），+1172/-5**；上轮15文件、+1327/-14。测试tracked/untracked diff仍为空。两个gems-opt的HEAD、branch、干净状态及全部tracked文件SHA摘要前后均未变：FGV `46387d7f96050204c1b932f35680a3ea03896fa6`，FG `3ba1d1d99010de56d12088992f8b0da3444d90ca`。

- 完整可应用 Git 补丁（历史路径当前不可用：`/tmp/hy4-essential-20261019-01/full.patch`；须从原 revision 或远端证据恢复）
- 逐文件展开的完整 diff（本地文件 `docs/cases/20261018-hy4-preview-ppu03-migration/plugin-review-env013/full-diff.md`）
- 本轮相对 env012 的删改（历史路径当前不可用：`/tmp/hy4-essential-20261019-01/from-env012.patch`；须从原 revision 或远端证据恢复）
- 逐文件SHA和部署回执：外部证据根的 `review/changes.json`

完整补丁 SHA256 `7ac885d463c832f5815098d8745ec5ed0214765f5cc46fbd64810149c50de039`。已从部署后的安装目录重新导出，核对616个regular文件（含原样Git忽略的生成_version.py），与离线候选逐项一致；tracked权限与symlink未漂移。补丁严格应用到官方及上轮两个基准、Python语法、局部F类lint、受保护函数AST一致性、namespace parser路径静态解析均通过。

**当前仅为源码已部署、静态检查通过的审阅候选。没有重启、发送模型请求或开始评测；service07仍为此前env011已加载的进程，不能据此认定env013启动、分页、graph或精度通过。** 旧env011验证仅留作历史，当前87%完整198题GPQA gate未签发。其他平台硬件未测，PR准备状态needs_revision。后续需重新验证当前版本，逐行prefill也可能降低吞吐。

本轮撤回/收窄：

| 位置 | 调整 |
|---|---|
| attention/mla_prefill.py | 完全恢复官方，移出最终diff；HY4计划仍直接绑定所需prefill class |
| reasoning/__init__.py | 删除只有docstring的新增文件；parser保留并按namespace解析 |
| backend bf16_indexer.py | 删除decode候选二次排序、gather和ATen redispatch |
| model bf16_indexer.py | 删除128行特化、跨层host metadata缓存、多请求key合并；逐行执行并保持物理页映射、索引转换及BF16运算顺序 |
| backend bf16_mla.py | 删除FGV之外的FlagGems后备查找；固定FGV公开导出足够 |
| TopK / runtime | 删除next_n>1及显式prefill选择兼容；只允许当前单token、无speculation、自动prefill配置 |

保留的13文件及必要性如下。这里依据当前缺失符号、dtype/shape/ABI和实际调用链判断，不声称已逐个删除并重新做整模型验证。

| 文件 | diff | 必要职责 |
|---|---|---|
| vllm_fl/dispatch/backends/flaggems/impl/bf16_indexer.py（本地文件 `docs/cases/20261018-hy4-preview-ppu03-migration/plugin-review-env013/full-diff.md`） | +126/-0 | BF16 cache与decode算子ABI |
| vllm_fl/dispatch/backends/flaggems/impl/bf16_mla.py（本地文件 `docs/cases/20261018-hy4-preview-ppu03-migration/plugin-review-env013/full-diff.md`） | +52/-0 | 稀疏MLA的小head与sink ABI |
| vllm_fl/dispatch/backends/flaggems/impl/int8_scaled_mm.py（本地文件 `docs/cases/20261018-hy4-preview-ppu03-migration/plugin-review-env013/full-diff.md`） | +15/-0 | 固定Gems组合的INT8矩阵乘入口 |
| vllm_fl/dispatch/backends/flaggems/impl/mla_ops.py（本地文件 `docs/cases/20261018-hy4-preview-ppu03-migration/plugin-review-env013/full-diff.md`） | +66/-1 | 通过现有DEFAULT registry接入提供者 |
| vllm_fl/dispatch/backends/flaggems/impl/top_k_per_row.py（本地文件 `docs/cases/20261018-hy4-preview-ppu03-migration/plugin-review-env013/full-diff.md`） | +86/-0 | TopK公开低层签名与索引契约 |
| vllm_fl/dispatch/backends/flaggems/register_ops.py（本地文件 `docs/cases/20261018-hy4-preview-ppu03-migration/plugin-review-env013/full-diff.md`） | +12/-0 | 注册INT8 CachedOp实现 |
| vllm_fl/models/hy4/attention.py（本地文件 `docs/cases/20261018-hy4-preview-ppu03-migration/plugin-review-env013/full-diff.md`） | +20/-3 | 将官方HY4接到BF16 runtime plan |
| vllm_fl/models/hy4/bf16_indexer.py（本地文件 `docs/cases/20261018-hy4-preview-ppu03-migration/plugin-review-env013/full-diff.md`） | +273/-0 | 有状态BF16分页Indexer编排 |
| vllm_fl/models/hy4/bf16_sparse.py（本地文件 `docs/cases/20261018-hy4-preview-ppu03-migration/plugin-review-env013/full-diff.md`） | +43/-0 | 复用官方sink模型语义的BF16 sparse接入 |
| vllm_fl/models/hy4/registration.py（本地文件 `docs/cases/20261018-hy4-preview-ppu03-migration/plugin-review-env013/full-diff.md`） | +5/-0 | 当前vLLM缺失hy_v4 parser的惰性注册 |
| vllm_fl/models/hy4/runtime.py（本地文件 `docs/cases/20261018-hy4-preview-ppu03-migration/plugin-review-env013/full-diff.md`） | +69/-0 | PPU选择与BF16支持契约 |
| vllm_fl/quantization/w8a8/linear.py（本地文件 `docs/cases/20261018-hy4-preview-ppu03-migration/plugin-review-env013/full-diff.md`） | +74/-1 | W8A8选择和必要的编译边界 |
| vllm_fl/reasoning/hy_v4_reasoning.py（本地文件 `docs/cases/20261018-hy4-preview-ppu03-migration/plugin-review-env013/full-diff.md`） | +331/-0 | 原启动参数要求的HYV4 parser回移植 |

## vllm_fl/dispatch/backends/flaggems/impl/bf16_indexer.py

按当前FlagGems接口写BF16分页cache、计算paged-MQA logits并调用TopK；官方FP8 Indexer接口不能直接替用。已撤回额外候选再排序和native ATen redispatch，仅接受provider选出的候选。

完整文件内容及diff（本地文件 `docs/cases/20261018-hy4-preview-ppu03-migration/plugin-review-env013/full-diff.md`）

## vllm_fl/dispatch/backends/flaggems/impl/bf16_mla.py

TP16后当前模型每rank只有4个query heads，而固定Gems sparse provider只支持64/128；补齐后裁回，并传递FP32 sink、topk_length。已删除FlagGems后备查找，直接使用固定FGV公开导出。

完整文件内容及diff（本地文件 `docs/cases/20261018-hy4-preview-ppu03-migration/plugin-review-env013/full-diff.md`）

## vllm_fl/dispatch/backends/flaggems/impl/int8_scaled_mm.py

当前FlagGems同名scaled_mm是FP8接口，W8A8需要FGV公开triton_scaled_mm。包装器适配现有registry的调用契约，不复制kernel。

完整文件内容及diff（本地文件 `docs/cases/20261018-hy4-preview-ppu03-migration/plugin-review-env013/full-diff.md`）

## vllm_fl/dispatch/backends/flaggems/impl/mla_ops.py

将上述BF16 cache/TopK/MLA包装接到CachedOp，基于既有能力与policy选择；当前新增BF16选择限PPU，非目标平台保留官方选择主体。未将任何Gems数值实现放到vendor/thead。

完整文件内容及diff（本地文件 `docs/cases/20261018-hy4-preview-ppu03-migration/plugin-review-env013/full-diff.md`）

## vllm_fl/dispatch/backends/flaggems/impl/top_k_per_row.py

固定FlagGems是8参数低层接口，需要行数、stride、K及长度布局；模型需要可解释的row-local位置。已去掉next_n>1支持，只保留当前单token decode，并在不支持输入处报错。

完整文件内容及diff（本地文件 `docs/cases/20261018-hy4-preview-ppu03-migration/plugin-review-env013/full-diff.md`）

## vllm_fl/dispatch/backends/flaggems/register_ops.py

新增int8_scaled_mm的default.flagos注册及真实公开提供者检查；linear.py使用该CachedOp，缺少注册则无法按policy解析。原有注册保持。

完整文件内容及diff（本地文件 `docs/cases/20261018-hy4-preview-ppu03-migration/plugin-review-env013/full-diff.md`）

## vllm_fl/models/hy4/attention.py

保留官方投影、RoPE、full/shared Indexer与sink，只在cache/算子ABI边界消费indexer工厂、prepare和sparse backend。没有这些钩子仍会构造当前PPU不可用的原生FP8路径；plan字段默认None时保留官方路径。

完整文件内容及diff（本地文件 `docs/cases/20261018-hy4-preview-ppu03-migration/plugin-review-env013/full-diff.md`）

## vllm_fl/models/hy4/bf16_indexer.py

按原生metadata/block_table访问物理页、准备QK/加权ReLU/TopK并转换request-local索引；custom op声明cache和输出buffer修改，隔离graph控制流。短区间直接填索引满足当前TopK的限制。已删除128行特化、跨层host metadata缓存和多请求key拼接，改为逐query行计算；保留BF16运算顺序。pack/unpack保留，因为原生requires_padding由decode长度差异触发，单token graph的0/1补齐也需要它。逐行可能变慢，未做性能声明。

完整文件内容及diff（本地文件 `docs/cases/20261018-hy4-preview-ppu03-migration/plugin-review-env013/full-diff.md`）

## vllm_fl/models/hy4/bf16_sparse.py

继承官方HYV4实现及原生UNIFORM_BATCH metadata，只覆盖当前缺少native CUDA符号的cache写入、query拼接与BF16 sparse调用，传递learnable sink及topk_length；没有重复metadata builder或vLLM源码patch。

完整文件内容及diff（本地文件 `docs/cases/20261018-hy4-preview-ppu03-migration/plugin-review-env013/full-diff.md`）

## vllm_fl/models/hy4/registration.py

当前服务使用--reasoning-parser hy_v4，而配对vLLM 0.24.0+empty及官方Plugin基线没有该parser。仅增加类路径注册，原有模型/config/loader注册不重写。

完整文件内容及diff（本地文件 `docs/cases/20261018-hy4-preview-ppu03-migration/plugin-review-env013/full-diff.md`）

## vllm_fl/models/hy4/runtime.py

官方原生CUDA/FP8前提不适用于当前PPU；沿用既有runtime plan接入BF16 cache、Indexer工厂和MLA prefill。检查D128/block64等实际kernel契约，保持权重先BF16缩放后转FP32。已删除显式CUSTOM选择兼容分支；当前新增路径只允许自动prefill选择且无speculation，避免声称支持未验证配置。其他平台官方验证主体保留。

完整文件内容及diff（本地文件 `docs/cases/20261018-hy4-preview-ppu03-migration/plugin-review-env013/full-diff.md`）

## vllm_fl/quantization/w8a8/linear.py

保留原dynamic_per_token_quant_int8 CachedOp，新增INT8 mm CachedOp；PPU路径用同文件opaque custom op隔离Gems Python包装，fake给出输出契约。此前直接跟踪包装发生Dynamo jit_function.params错误。没有graph.py，非PPU类调用主体保持官方逻辑。

完整文件内容及diff（本地文件 `docs/cases/20261018-hy4-preview-ppu03-migration/plugin-review-env013/full-diff.md`）

## vllm_fl/reasoning/hy_v4_reasoning.py

保持用户要求的vLLM主线固定commit 5d20979fc90a38f450e0fb89661b271926a3061a的完整parser语义，仅适配当前DeltaMessage导入路径。当前vLLM缺少原生实现，不能删为HYV3 shim。331行主要是上游实现；新增目录按namespace导入，不保留仅有docstring的__init__.py。

完整文件内容及diff（本地文件 `docs/cases/20261018-hy4-preview-ppu03-migration/plugin-review-env013/full-diff.md`）

外部证据根 `/workspace/.hy4-preview-migration-20261018-01/essential-20261019-01`；部署回执deployment-result.json。修改前备份plugin-env012-before.tar.gz，SHA256 `ef5327ad3dc0d7d74022f70e8d077f18bafe108af2e9d5c17b9c5b31ee0f2684`。回退脚本commands/rollback.py只恢复本轮7路径，并校验未被后续修改，不触碰Gems或服务。

本地长期保留本说明与完整diff Markdown。原始Git补丁、逐文件before/after快照、SHA清单和控制脚本已归档到上述容器私有证据根，40文件逐项校验；归档SHA256 `ce0a52e5d2cd6efdfea48b61fe461f8507bc6611ff098f40646a5430dd427da5`。可直接打开的本机补丁在 `/tmp/hy4-essential-20261019-01/full.patch`，其SHA与容器内 `review/full.patch`一致。

权重量化范围澄清（用户追问后的只读核验）：config为compressed-tensors/int-quantized，W8A8权重按channel、动态激活按token；默认dtype=bfloat16。实际safetensors文件头抽查layer0的q_a/q_b/kv_a/kv_b/o_proj均I8；indexer.wq_b/wk/weights_proj及k_norm均BF16，且在量化ignore中；embed_tokens/lm_head/norm也是BF16。没有读取权重数据区、加载模型或发起评测。

普通BF16激活输出/attention/cache与新增BF16 Indexer应分别判断：linear.py保持INT8权重×动态INT8激活并输出原activation dtype；原生/官方Indexer在BF16投影后另做FP8 query/key量化，而当前新增Indexer保留BF16 Q/K和cache、改调固定Gems公开BF16分页算子。这是旧PPU适配迁移的兼容执行方案选择，不由INT8 checkpoint强制要求，也没有证明它是官方结构下唯一或最小可行方案。BF16与FP8的舍入、TopK边界、cache大小/带宽均可能不同，当前没有完整198题gate证明等效。此前将整个BF16链路笼统标为“必要”过强，应以具体provider/ABI缺口判断。
