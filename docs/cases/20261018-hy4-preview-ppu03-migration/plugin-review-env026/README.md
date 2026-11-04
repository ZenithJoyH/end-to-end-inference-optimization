# env026：当前实际安装 Plugin 的整体 review

结论：存在3项局部收敛候选，没有找到可直接删除整个适配文件的充分证据。此次只读检查，**没有修改任何 Plugin/Gems 源码**，没有重启、模型请求或精度/性能评测。

当前现场为 PPU-03 / hy4-preview `/workspace/vllm-plugin-FL`，官方 main HEAD `8b2033e417a535a828a1d7594d36bd33e36e3b57` 加 env025 已安装的 env024 组合。614文件清单与部署回执一致，累计11生产文件 +1058/−20，完整 patch SHA `fc652cb227d43425d20296d1bb37712000bbd8b667f0b44bb65fd7a4e87ab4c7`。两个 gems-opt HEAD/clean/tracked摘要与安装时相同，health200；服务没有重启，不能把旧 env022 的模型验证绑定到当前磁盘源码。

下列文件链接指向从容器读取的**只读现场快照**，不作为后续修改目标；后续修改仍必须直接落到容器实际安装目录。

## 1. runtime 的两项 TopK 检查与实际执行入口不一致

位置：runtime.py:188（历史路径当前不可用：`/tmp/hy4-full-review-20261020-02/installed/vllm_fl/models/hy4/runtime.py:188`；须从原 revision 或远端证据恢复）。

PPU 模型当前实际通过 CachedOp 使用 `bf16_indexer_cache_write/prefill/decode`；后端 prefill/decode 内部直接导入固定 FGV TopK。runtime 仍额外 `_resolve_registered_operator("top_k_per_row_prefill/decode")`，但不会使用其返回的实现。这是能力/策略检查与实际执行入口之间的重复，不能将检查所选的 raw TopK 实现当成实际执行证据。

建议将启动检查对齐真实组合入口，删除这两项孤立解析；底层 provider 可用性保留在组合入口的 backend 检查。若产品期望独立 raw TopK 的 dispatch 策略也控制组合算子内部，必须先明确该契约再接入选中的函数；本轮不能同时声称当前独立 raw policy 已生效。

分类：设计/配置一致性改进，未证明当前默认PPU配置发生错误。可以作为优先收敛点，不能仅凭这个 review 宣称任何白名单/策略语义变化已经验证。`concat_and_cache_mla/concat_mla_q/flash_mla_sparse_fwd` 仍被 sparse backend 通过 CachedOp 实际使用，相关检查应保留。

## 2. non-padding decode 的 copy_ 是同一 buffer 区间自拷贝

位置：backend bf16_indexer.py:246（历史路径当前不可用：`/tmp/hy4-full-review-20261020-02/installed/vllm_fl/dispatch/backends/flaggems/impl/bf16_indexer.py:246`；须从原 revision 或远端证据恢复） 与 末尾copy:286（历史路径当前不可用：`/tmp/hy4-full-review-20261020-02/installed/vllm_fl/dispatch/backends/flaggems/impl/bf16_indexer.py:286`；须从原 revision 或远端证据恢复）。

无 padding 时 `topk_indices` 已是 `topk_indices_buffer[:num_padded_tokens, :count]`，TopK 直接写目标 buffer。最后再次向同一范围 `copy_` 无需执行。建议只在 padding 分支中 unpack 后复制回原 buffer；non-padding 保持原地写入即可。完整 `count=topk_tokens` 行宽必须保留。

分类：局部冗余，可用一行缩进调整收敛，不改变数值或 ABI。这里没有测量该自拷贝是否实际产生 GPU kernel，不据此宣称性能收益；后续实施后仍需验证输出别名及 padding 两侧行为。

## 3. BF16 Indexer 分支重复保存了未读取的三个属性

位置：attention.py:203（历史路径当前不可用：`/tmp/hy4-full-review-20261020-02/installed/vllm_fl/models/hy4/attention.py:203`；须从原 revision 或远端证据恢复）。

factory 创建的 `indexer_op` 已持有自身 `k_cache/max_model_len`。随后外层 BF16 分支又设置 `self.k_cache`、`self.max_model_len`、`self.prefix` 并 return；Indexer 的 forward/prepare_inputs 不读取这三个外层属性。其他仓库内直接属性引用检索也未找到该 BF16 外层别名的消费者。

当前实际 vLLM `DeepseekV32IndexerCache.__init__` 以 prefix 在 `compilation_config.static_forward_context` 注册自身，注册不依赖外层模块另存 alias。因此可考虑删去三行，保留 `indexer_op` 管理 cache；官方 FP8 分支自身的字段不能一并删除。

分类：低优先级的重复状态清理。它不代表生成了第二份 KV cache；当前两个属性引用指向同一 cache 对象。删除外层 `self.k_cache` 会改变模块别名/外部属性可见性，实施时应核验 static context、named_modules 与 cache 发现方式，不能只按行数机械删除。

## 4. 应单列验证的 prefill 实现问题

位置：backend bf16_indexer.py:79（历史路径当前不可用：`/tmp/hy4-full-review-20261020-02/installed/vllm_fl/dispatch/backends/flaggems/impl/bf16_indexer.py:79`；须从原 revision 或远端证据恢复）。每个 chunk 对三个 metadata tensor 调用 `.tolist()`，随后 Python 逐 row 做 matmul/归约/TopK。实际 vLLM metadata builder 在 block_table 的 device 上分配这三者，并注释避免CPU同步；当前调用会将这些设备数据读回 CPU。

这是可定位的组织开销，适合作为后续优化方向；不能仅凭源码给出耗时占比或将首次339秒归因于此。减少同步、利用 chunk 批处理或替换库算子都需同条件验证，保持 request-local 索引、prefix cache、窗口范围和内存上界。

同时保留 env019 的 R2 观察：prefill 经 BF16 matmul/加权/归约舍入，FG paged decode 在 FP32 中累加，边界 TopK 可不同。它是已确认的数值差异，**尚未证明造成87%精度失败**；不能在“收敛代码”时顺手将 prefill 全改FP32或更换算法。应先明确数值参考，再用原198题/87%契约验证。此次没有改变精度口径、参数或阈值。

## 11文件逐项结论

| 文件（相对 vllm_fl/） | 结论 |
|---|---|
| dispatch/backends/flaggems/impl/bf16_indexer.py | 保留 cache、prefill/decode 与库 ABI 适配；可收敛non-padding自拷贝，prefill同步/算法问题单独验证。 |
| dispatch/backends/flaggems/impl/bf16_mla.py | head padding、sink padding、输出裁回对应固定FGV仅支持64/128头的接口。当前TP16每rank4头，暂无删除适配证据。 |
| dispatch/backends/flaggems/impl/mla_ops.py | 独立_get_bf16_operator已删，普通算子已恢复统一获取；当前必要映射与开关保留。不再为缩短函数新造获取框架或放宽未测平台。 |
| dispatch/backends/flaggems/impl/quantization.py | 局部custom-op/fake有env016量化fullgraph失败与窄边界成功证据，保留；不恢复整层W8A8包装。 |
| models/hy4/attention.py | factory/prepare/backend三个窄hook保留，非PPU原路径不变；外层BF16分支三行别名可低优先级清理。 |
| models/hy4/bf16_indexer.py | 模型只承担cache/metadata/chunk编排和opaque图节点；保留该编译/状态边界，不合并回backend或恢复模型侧数学。 |
| models/hy4/bf16_sparse.py | 复用官方metadata/sink实现，替换PPU的cache/concat/sparse入口，保留。未扩大dense+sinks等非目标配置的支持结论。 |
| models/hy4/registration.py | 当前vLLM无hy_v4 parser映射，lazy注册仍必要；不重复回迁官方已有模型/loader逻辑。 |
| models/hy4/runtime.py | 保留BF16支持条件、PPU无FP8的选择与原native路径；TopK检查应与真实组合入口对齐。原文件大量runtime事务/原生选择逻辑属于官方基线，不当作本轮新增代码删除。 |
| quantization/w8a8/linear.py | 原量化CachedOp、用户指定FGV triton_scaled_mm及zero-token guard保留，不增加int8 GEMM dispatch或整层包装。 |
| reasoning/hy_v4_reasoning.py | 实际0.24运行时缺少原生HY4文件；全部函数/类AST与已缓存vLLM main@5d20979一致，仅接口import适配。保留backport，不为减少行数重写主线解析语义。 |

必须保留的已证实修复：FGV量化局部编译边界、decode TopK完整行宽、pack `max_length=1` / unpack `total_tokens`、BF16 sparse头数与sink处理、主线parser backport。保护dtype/shape/stride的校验不能因“行数多”无依据删除。

## 检查范围与证据

现场614文件与env025清单一致，11文件逐项读审；Python语法检查通过，Plugin tests官方字节未改。静态AST核对组合入口、三个tolist、non-padding alias、外层属性读写及实际cache注册。parser函数/类与缓存主线版本AST一致；没有新跑设备测试/CPU数学回归或正式评测。

Ruff覆盖全部11文件，3个已有I001：bf16_mla.py、模型bf16_indexer.py、bf16_sparse.py。没有将其伪装为本轮新增缺陷；可在最终提交整理时只修import排序，不值得扩大当前运行变更。

本地证据根 `/tmp/hy4-full-review-20261020-02`：snapshot.json（当前完整manifest、11实际文件、必要vLLM源码）、extra-source.json（实际cache注册及reasoning registry）、audit.py、audit.json。原始证据按当前任务目录归档，不提交模型、数据集或日志。此次patch未变化，当前实际安装完整diff仍见 env025（本地文件 `docs/cases/20261018-hy4-preview-ppu03-migration/plugin-installed-env025/full-diff.md`）。

下一轮最小候选应只处理上述局部重复，逐项保存必要验证；不同时变更prefill算法、Gems版本、模型精度或服务启动配置。新安装源的启动/graph/分页/正式精度缺口继续保持，`pr_readiness=needs_revision`。

后续：上述3项局部候选已在 [env027](../plugin-cleanup-env027/README.md) 直接应用到容器安装路径并通过CPU契约核验；本review正文保留审查当时事实，prefill/R2问题未改。
