# op009：MoE公共调用去掉workspace复用

用户明确要求：workspace复用逻辑去掉，fused_experts_impl调用与NV对齐，其余复用当前容器Plugin。本轮只采用当前020plugin-opt/8b059加原dirty源码，不切020plugin-opt-metax/f99分支。源环境mx59/qwen3.6-35B/8010/TP2GPU6/7，原地例外有效。只改Plugin的fused_moe_utils.py及其已有CPU契约测试，FlagGems/Gems-vllm/vLLM/模型/脚本不动；不重启服务。

归属operator/improve contract simplification：保留MetaX现有dtype/activation/quant/expert_map条件与库namespace，统一NV和MetaX调用output.copy_(gems.fused_experts_impl(...))。删除supports_fused_experts_workspace探测、out/workspace13/workspace2传参、旧getattr/callable接口兼容和result-is-output分支。vLLM apply的workspace形参/原有分步边界仍需保留，不能删除框架签名。公共库内部自行分配缓冲，现有Gems平台分发不改。

首个验证mode=minimal-regression/scope=CPU caller contract。从真实apply AST执行CPU张量与mock库，覆盖NV/MetaX调用、无workspace探测/传参、输出复制、异常单次上抛、缺公共API直报、量化/LoRA/其他平台边界、empty与strided输出。此检查不是设备数值/graph/模型精度，整体minimal在真实新源graph/capture>=2replay前incomplete。用户仅要求改代码，当前不重启/发模型请求；后续正式性能需新source精度gate，原170/198不迁移至新磁盘源码。

预检回执 `/public-flash/jinghao/qwen3.6-35B/20261013-qwen36-35b-metax-e2e-current/manifests/op009-before-20261015.json` SHA8ad44ee9f501c289422ed9da436e92fd20055e430ec30f920b34d4ebf49e3d6f；备份 `/public-flash/jinghao/qwen3.6-35B/20261013-qwen36-35b-metax-e2e-current/patches/op009-before-moe-call-20261015.tar.gz` SHA4db1864e70efbd8822597690374ec950b4357300fcc4a929be21d0a575b22e13。原517文件/index/dirty已冻结，外部全部source/GPU服务旧实例保持。候选本地暂存准备，执行前冻结SHA；真实应用前必须先CPU回归全通过，失败不部署/不删case。部署只替换两文件并核其余515文件及其他3repo全保持，原服务PID/birth/args/env不变；回退只能针对这两文件的精确SHA。

无预设性能收益：减少代码复杂度由用户明确要求，即使output copy/库分配可能有开销，不能用私有/旧微测假称E2E收益。当前P1K006稳定性失败/旧GPQA/其他私有实验全部保留。PR experimental，跨硬件/新源graph/GPQA/P1K not_run。

## 执行完成（2026-10-15 18:00 CST）

已将验证后的代码写入当前容器 `/workspace/vllm-plugin-FL/vllm_fl/ops/fused_moe/fused_moe_utils.py`，SHA297da4992197f496d6143832e36cdcc8eac021a471fd7a337e09941fc5ab8764。NV和MetaX统一为直接公共调用再output.copy_，不查询supports_fused_experts_workspace，不传out/workspace13/workspace2，不再有callable/getattr兼容或输出identity分支。原MetaX适用guards、namespace选择、LoRA/量化/其他平台分步路径及apply工作区形参都保持。Gems库支持workspace的公共API本身未删除，也未改库实现。

原生pytest暂存真实apply AST/mocks：**28passed/0failed/0skip，1.60s**。覆盖两平台参数/无探测、capability无关、单次异常传播、缺API直接上抛、8类语义边界、W8A8专用专家、NV量化参数、空/单token和strided caller-output/canary/workspace未写。只证接口行为，未执行设备算子/新模型graph/GPQA/E2E，不冒充全平台硬件通过。stage和最终写入字节SHA完全相同，无需重复同一CPU测试。

最终回执 `/public-flash/jinghao/qwen3.6-35B/20261013-qwen36-35b-metax-e2e-current/manifests/op009-applied-20261015.json` SHA3de3cb29324d8dbb0d6e42a9c89f011b8f3a071929bdc3435d2158df65c8e9b0；生产文件及对应tests/unit_tests/dispatch/test_metax_moe_public_api.py两处改变，其余515Plugin文件/index/branch020plugin-opt保持；全12252文件核验仅这两处允许差异，其他三repo、模型/tokenizer/fullenv与精确API实例982315/497862111保持。新Plugin文件manifest `/public-flash/jinghao/qwen3.6-35B/20261013-qwen36-35b-metax-e2e-current/manifests/op009-plugin-files-20261015.json` SHAbd239cf37e27e49a6599710763101d512c153105651c420a8e9bc5ed3fcda6a6。

CPU回执 `/public-flash/jinghao/qwen3.6-35B/20261013-qwen36-35b-metax-e2e-current/results/op009-CPU-contract-20261015.json` SHAdccb87d26168b63ed7f9536ed753c85e2697c8e7ba234ab6101ddabd9213f382，XML403040b44c2fef478d86f518749a74c1a37abb2db8c6cf33e6125185b437f745；testcommand39320cf6...。applycommand5d6ad619...已执行不可重放。增量patch ROOT/patches/op009-no-workspace-incremental-20261015.patch及原备份4db1864e...保留，rollback-op009-moe-call-20261015.py SHA753bd1187d5c83254641da2e47cb2edf5c50414996c3c6c089856796c9a24b47仅保存未执行。

服务未重启/未hotreload，磁盘候选gdn-current-plus-op005-moe-no-workspace-297da499与旧加载源区分。原170/198 gate只属历史/旧加载source，不能用于op009正式性能或重绑定新源码；后续实际启动应补graph/至少两replay、最小数值及新198/65536/temp1/top_p.95/top_k20/seed42/C32/80正式GPQA。当前整体minimal=incomplete、PR experimental、无新E2E收益。本轮只完成用户要求的代码变更，不能自动以此申请/实施服务中断或恢复旧性能自动化。
