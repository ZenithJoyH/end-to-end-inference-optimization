# op-003：Plugin MoE 调用切换至 FlagGems-vllm

- 用户明确要求：将当前 mx-59/qwen-vl 中 Plugin 的 FlagGems fused MoE 调用切换到 FlagGems-vllm。
- 日期：2026-10-12；分类：operator/replace；范围：源码接入调整。
- 状态：completed / retained-code-only；性能与正式精度：not_run。
- Remote：`/public-flash/jinghao/qwen3-VL/20261012-qwen3vl-metax-sampling-migration`；使用 `commands/op003/`、`logs/op003-*` 和 `results/op003-*`，不覆盖已有材料。
- 验证环境：复用当前案例独立 `qwen-vl-sampling-opt-20261012`，变更前重新核验镜像/挂载和相关源码一致性。

设计：复用现有 FlagOS backend adapter 和 TritonExpertsFL 接口，只调整分步骤 `invoke_fused_moe_triton_kernel` 与完整 `fused_experts_impl` 的库来源。使用 FlagGems-vllm 公共 API，不硬编码 backend 私有路径，不更改 registry、策略、参数、LoRA 分支或模型配置。MetaX 当前使用分步骤路径；完整调用仍受原 NVIDIA/no-LoRA 条件约束。router、align、activation、sum 等邻接调用本轮不扩大修改。

FlagGems-vllm 已安装且暴露两个公共函数；旧参数是新签名的子集。分步骤公共入口当前指向 FlagGems-vllm 通用实现，完整入口在 MetaX 有 vendor override。本轮不新增融合开关、不更改导出策略、不宣称已启用 MetaX 完整融合。保持可选依赖在原调用位置加载；依赖错误沿用原 strict/fallback 语义，不静默重导入 FlagGems。

授权仅针对当前容器 Plugin 源码副本；先在私有验证容器修改、测试，再以 source SHA guard 回写用户指定的 qwen-vl。源服务若在运行则停止部署并保留验证候选，不自行重启服务。保存两文件原内容及仅本轮 diff，回退检查候选 SHA。

首个证伪实验：注入 FlagGems-vllm spy 验证参数和输出契约，并使旧 FlagGems MoE 调用报错以发现漏改。其次检查 dispatch wrapper 的实际公共函数路径；设备验证比较原 FlagGems GEMM1/GEMM2 和新调用，覆盖 BF16/FP16、naive/对齐路径、bias/router-weight 与目标 TP2 本地 shape，进行 capture 及两次 replay。数值失败先修复或回退，不部署失败候选。

技能：项目 `inference-accuracy-evaluation` 的 minimal-regression；算子与接入验证先执行。完整 graph 模型服务/C8 和正式 GPQA 没有本轮有效 gate，明确记为 incomplete/not_run，不签发模型精度结论。本轮不做性能比较。

## 验证结果

候选已仅修改两个 Plugin 文件，source/clone 相关输入 SHA 一致；复核原案例 snapshot image 和完全相同的 Mounts/Binds，通过后应用。公共 invoke 仍由 default.flagos adapter 选择，底层调用换至 FlagGems-vllm；完整入口参数与输出 copy 已做 mock 契约验证。

第一轮设备验证在旧 FlagGems 调用处编译失败：测试错误地将 naive 路径的 num_tokens_post_padded 设为 None，旧 kernel 的 tl.load 无法编译；真实 `_prepare_expert_assignment` 为该路径创建 topk_ids.numel()*BM 的 int32 单元素张量。按 `inference-accuracy-diagnosis` 分类为 measurement-invalid，尚未调用候选 kernel，不能归因于迁移。保留 logs/op003-validation.log 和 commands/op003/validate.py。v2 改为使用真实 assignment helper，并采用 Decode BM16 / Prefill BM128 配置；生产代码没有因此修改。

v2 通过 3 项参数/输出/dispatch 接入检查及 20 组设备用例：BF16/FP16 × T=1/8/64/257/1024 × GEMM1/GEMM2，包含 naive assignment、对齐 padding、bias、routed weights 和 BM16/BM128；每组 capture 后 replay 两次。与原 FlagGems 的 max_abs_diff 全部为 0；同时通过按 expert 分组的独立 FP32 矩阵乘参考（BF16 rtol/atol=.02，FP16=.005，测量前定义）。设备为隔离容器中的 physical GPU4；这不是完整 TP2 模型 graph 服务验收。日志与 JSON：`logs/op003-validation-v2.log`、`results/op003-validation-v2.json`。

部署前 source/clone 的相关 FlagGems-vllm/FlagGems MoE、库导出、既有 MCTLLASS/采样补丁和四仓库 revision 一致，证据 `results/op003-dependency-parity.json`。首次部署的 Mounts 列表原序比较拒绝，尚未写源文件；fresh inspect 未见映射差异。v2 采用项目 `verify-container-mounts.py` 的规范化全字段比较，保留严格边界，`results/op003-deploy-mounts.json` passed。使用已验证 snapshot，镜像谱系沿用原案例，不以挂载通过代替谱系证明。

`commands/op003/apply-v2.py deploy` 以原文件 SHA guard 回写 qwen-vl 的两个文件；没有 active vLLM model 进程，没有重启服务。原始两文件在 `patches/op003-deploy-before.json`；本轮 diff 为 `commands/op003/plugin.patch`（SHA256 `775d455a65fa6dd79726d724880f761162fdc11e1dba98c6a871627ff9a849af`）。保持 FlagGems、FlagGems-vllm、vLLM 源码及已有 Plugin vendor/sampler 改动不变。

回退：在 mx-59 运行 `python3 <remote-case>/commands/op003/rollback.py` 默认仅 dry-run；加 `--execute` 才恢复两个文件，执行前检查候选 SHA 和 active service。dry-run 验证两个文件、mutated=false；不自动重启。后续启动 worker 会加载新调用，已有进程不作热更新承诺。

部署后在 qwen-vl 新进程只读核验两个生产文件的候选 SHA，检查真实公共 API 文件位置，并用 spy 证明默认 dispatch 的 GEMM 调用进入新库而没有调用旧 FlagGems MoE。证据 `results/op003-source-postverify.json`、`logs/op003-source-postverify.log`；source `git diff --check` 通过，vLLM 工作区保持干净。源容器未运行设备计算或模型评测。

## 结论边界

当前 MetaX 分步骤路径调用 FlagGems-vllm 公共 `invoke_fused_moe_triton_kernel`（通用 `ops/fused_moe.py`）；完整 `fused_experts_impl` 的公共 API 在 MetaX 指向该库 MetaX backend，但原 NVIDIA/no-LoRA 条件未改，因此本轮没有启用 MetaX 的完整融合。router、align、activation、sum 原来源保留。现有 `default.flagos` impl_id 表达 backend 类别，不再意味着这个 MoE GEMM 来自 FlagGems 仓库。

模型服务/C8、两个 TP worker、正式 GPQA、量化路径数值及非 MetaX 硬件均未测；NVIDIA 完整入口只做 mock 参数契约。minimal-regression 的算子/接入部分通过，服务部分 incomplete，不签发模型精度 gate，不晋级正式性能。源码接入任务已完成；`pr_readiness=needs_revision`，尚需完整模型与非目标平台/依赖组合验证。没有新增 kernel、导出或调优，未做性能比较。
