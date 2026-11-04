# FlagGems-vllm 安装版 MoE 回收与 vLLM 源码复核

后续用户已要求并完成 [editable 安装切换](editable-installation.md)。当前直接从源码仓库加载；本文“非editable”“安装副本”等描述保留为源码回收阶段的历史事实，回退应按后续安装记录执行。

2026-10-22；Host `mx-104`；容器 `qwen3.6-35B-verify`。本记录是初次代码审计之后、按用户明确要求执行的源码同步，不是新性能优化实验。

## 执行前冻结

用户授权：把安装目录独有的 MoE 改动整理回 FlagGems-vllm 源码仓库，保持现有优化逻辑不变，并核验源码与实际加载代码一致；检查 vLLM 源码修改并在存在时迁到 Plugin。

- 远程工作根目录：`/public-flash/jinghao/qwen3.6-35B`；沿用已有唯一案例目录 `20261022-qwen36-35b-mx104-code-audit`，本轮产物放在其 `reconcile-001/` 下。
- 源仓库：`/opt/FlagGems-vllm`，HEAD `e1a02b6b2e47abea9a6cfeaaf3431f50f7f476f8`。
- 唯一拟写源码：`src/flaggems_vllm/runtime/backend/_metax/fused/fused_moe.py`，原 SHA256 `16023d6d43c4068e611f175f51d2c57cf4a358b2c0a6db0a3d6de7c067855fb9`。
- 权威输入：`/opt/conda/lib/python3.12/site-packages/flaggems_vllm/runtime/backend/_metax/fused/fused_moe.py`，SHA256 `c575c8a798232cd86e18e1239d2a314cd0e3afe21faf5951c45798c84f706679`。
- 保留已有 GDN 修改；源码与安装版 `gdn_chunk.py` SHA256 均为 `109a6f92b0a7bb728acc6029d471bdb302d097c9ef04ded48bf8ccc7b6c0e04d`。
- `/opt` 与 `/workspace` 为该容器私有层；不在 `/public-flash`、`/data` 挂载内。当前未发现模型服务进程。

已读取目标仓库 `AGENTS.md`、`workflow.md` 和项目 Plugin 设计约束。本次是已存在实现的原字节回收，不新增算子或改变算法；按用户“逻辑不变”的要求不重排格式、不改 autotune、fallback 或 dispatch，不执行该仓库 workflow 中与当前任务无关的 conv1d 开发内容。

变更方案：执行前保存原文件与安装文件、源码差异和哈希清单；以 HEAD、两个 MoE SHA 和已有 GDN SHA 为硬性前置检查；原子替换源码单文件，保持 mode；不重装包。远端可执行副本为 `/Users/baai/Documents/ChatGPT/端到端推理优化/.cache/model-record-archives/20261102-record-reconciliation-01/files/docs/cases/20261022-qwen36-35b-mx104-code-audit/commands/reconcile-moe-001.py`，先保存再执行，SHA 由本轮回执记录。

验证方案：比较整棵包的 `.py/.json/.yaml/.yml` 文件清单和 SHA；确认 GDN 与安装文件未变；AST/compile 检查；使用 `/opt/conda/bin/python` 的登录 shell 重新导入包，核对实际模块/函数来源、文件 SHA，以及内存函数 code object 与源码编译结果。没有在运行的模型 worker，因此此处核验范围为新解释器导入，不能称为现存 worker 内存验证。

回退范围只包括本轮同步的源码文件：使用 `reconcile-001/backups/source-fused_moe.py` 恢复前先检查当前源码仍为本轮结果 SHA，避免覆盖后续修改。安装版、GDN、Plugin 和 vLLM 不属于该回退的写入范围。

## 结果

同步与核验已完成。只改了容器源码仓库的 MetaX `fused_moe.py`；复制的是安装版完整原始字节。TP2 专家形状支持、GEMM1/GEMM2 tile、pipeline 条件及 ablation 日志均按原样保留，没有重构或格式化。源仓库现有未提交修改为 `fused_moe.py` 和此前已有的 `gdn_chunk.py`；GDN 原始修改保持不变。

| 检查 | 结果 |
|---|---|
| MoE 源码与安装版 SHA256 | 均为 `c575c8a798232cd86e18e1239d2a314cd0e3afe21faf5951c45798c84f706679` |
| 整包源码/安装 `.py/.json/.yaml/.yml` | 各 276 文件，路径与内容差异均为 0 |
| 本轮源码变更范围 | 仅 `runtime/backend/_metax/fused/fused_moe.py`；mode 仍为 0644 |
| 安装包/GDN 内容 | 与同步前完全一致 |
| Python AST/compile | 通过 |
| 新解释器实际导入 | `/opt/conda/bin/python`，`flaggems_vllm` 仍从 site-packages 导入 |
| 公共 `fused_experts_impl` | 与安装版 MetaX 模块中的函数是同一对象 |
| 加载函数与源文件编译结果 | 31 个顶层函数全部相等，包括 Triton/pointwise 包装下的原始函数；递归比较 bytecode、常量、参数、符号、flags、异常表，排除文件名和调试行表 |

**没有改成 editable 安装。** 当前使用的安装副本与源码副本相等；后续若编辑源码，仍须按安装流程同步并再次核验，不能把本次一致视为两目录会自动联动。

这也不改变模型调用链：初次审计已确认 Plugin 的相关 MoE adapter 直接引用的是 `/workspace/FlagGems/src/flag_gems/fused/fused_moe.py`，而不是本次回收的 FlagGems-vllm 实现。本轮验证的是 FlagGems-vllm 自身公共入口与加载文件，没有切换 Plugin backend，不能据此宣称模型 MoE 已改走 FlagGems-vllm。

## vLLM 是否需要迁移

**未发现当前容器中需要迁移到 Plugin 的 vLLM 落盘源码修改。** `/workspace/vllm` HEAD 为 `bc150f50299199599673614f80d12a196f377655`；本地 `v0.20.2` tag 和 `origin/releases/v0.20.2` 指向同一提交。

- staged、tracked、untracked 修改均为 0；assume-unchanged/skip-worktree 标记为 0。
- 绕过 Git 文件状态缓存，独立读取全部 4,737 个 HEAD blob 对应文件，计算 Git blob SHA1，差异为 0。
- 唯一 ignored 文件 `vllm/_version.py` 是生成的版本元数据，不包含推理实现修改。
- 实际导入 `vllm.__file__=/workspace/vllm/vllm/__init__.py`，为 editable 安装；未发现 site-packages 中另一个 vLLM 代码树。

现存行为替换已放在 `/workspace/vllm-plugin-FL/vllm_fl/dispatch/backends/vendor/metax/`：

| Plugin 文件 | 已有扩展内容 |
|---|---|
| `patches/topk_topp_sampler.py` | 采样函数及采样器类替换 |
| `patches/gdn_linear_attn.py` | `GatedDeltaNetAttention.register_oot` 注册 |
| `patches/chunk_delta_h.py` | vLLM FLA H kernel 运行时替换 |
| `patches/pynccl_wrapper.py`、`patches/cuda_wrapper.py` | MCCL/CUDA wrapper 及通信适配 |
| `patches/utils_patch.py`、`patches/__init__.py` | 库发现及能力检测替换 |
| `impl/attention/flash_attn.py` | 连续 KV 单请求 Prefill 路径 |

`/opt/qwen36-final-moe/patches/vllm_metax_contiguous_single_prefill_ly.diff` 虽带 vllm 名称，其实际 diff 目标也是 `vllm_fl/.../flash_attn.py`。没有为“迁移”重复实现这些 Plugin 补丁，也没有修改 vLLM 或 Plugin。

上述结论基于当前容器和本地 HEAD；未联网拉取上游进行历史审计，不推断过去从未修改 vLLM。逐项哈希、入口和位置见本地 `/Users/baai/Documents/ChatGPT/端到端推理优化/.cache/model-record-archives/20261102-record-reconciliation-01/files/docs/cases/20261022-qwen36-35b-mx104-code-audit/vllm-source-audit.json` 及远端同名回执。

## 产物与回退

远端本轮目录：`/public-flash/jinghao/qwen3.6-35B/20261022-qwen36-35b-mx104-code-audit/reconcile-001/`。

| 路径（相对远端案例根目录） | 内容 |
|---|---|
| `reconcile-001/backups/source-fused_moe.py` | 修改前源码原字节备份 |
| `reconcile-001/backups/installed-fused_moe.py` | 权威安装版原字节备份 |
| `reconcile-001/before.json`、`result.json` | 前后源码/安装文件清单、SHA、状态和限定变更范围 |
| `reconcile-001/before.patch`、`after.patch` | 回收前后相对 FGV HEAD 的完整源码差异 |
| `reconcile-001/moe.patch` | 本轮回收的 MoE 修改，保留原字节差异 |
| `reconcile-001/import-verification.json` | 31 个函数的源码/加载 code object 指纹和实际导入来源 |
| `reconcile-001/vllm-source-audit.json` | vLLM 文件、安装、导入和已有 Plugin patch 的复核 |
| `reconcile-001/README.md` | 本记录的远端副本 |
| `/Users/baai/Documents/ChatGPT/端到端推理优化/.cache/model-record-archives/20261102-record-reconciliation-01/files/docs/cases/20261022-qwen36-35b-mx104-code-audit/commands/rollback-moe-001.py` | 已准备、未执行的带 SHA 防覆盖检查的单文件回退脚本 |

回退入口为在 `mx-104` 上运行 `python3 /public-flash/jinghao/qwen3.6-35B/20261022-qwen36-35b-mx104-code-audit/commands/rollback-moe-001.py`。它只在源文件仍等于本轮结果且备份校验通过时恢复源文件，不影响安装版与此前 GDN 修改；回退后会重新出现源码/安装不一致。

已执行命令的 SHA256：

| 脚本 | SHA256 |
|---|---|
| `/Users/baai/Documents/ChatGPT/端到端推理优化/.cache/model-record-archives/20261102-record-reconciliation-01/files/docs/cases/20261022-qwen36-35b-mx104-code-audit/commands/reconcile-moe-001.py` | `13a191ba46bc6eb66e568ac11a03d06d480d78b36f685f2d21bc04bc2c54f2aa` |
| `/Users/baai/Documents/ChatGPT/端到端推理优化/.cache/model-record-archives/20261102-record-reconciliation-01/files/docs/cases/20261022-qwen36-35b-mx104-code-audit/commands/verify-moe-import-001.py`（首次未完成） | `ad3826471f6910f8c64a8baaff2074b314a96cc5e3f477dcb09e03e06ee47ed1` |
| `/Users/baai/Documents/ChatGPT/端到端推理优化/.cache/model-record-archives/20261102-record-reconciliation-01/files/docs/cases/20261022-qwen36-35b-mx104-code-audit/commands/verify-moe-import-002.py`（通过） | `4ad7b6e6162bad2fe22badbfdbd80c554d2a38463aa779ed42a9b55f519f24d8` |

首次函数核验未识别 `PointwiseDynamicFunction._scalar_fn`，在读取 `_silu_and_mul_kernel` 时停止；补充包装层读取后重跑，31 个函数全部通过。这是核验脚本修正，执行源码未因此变化。发布脚本及备份/结果的独立 SHA 清单保存为 `reconcile-001/publication.json`。

本轮未启动模型、执行设备 kernel、graph capture、精度或性能测量；当前容器无运行中的服务/worker。本次结果是源码回收和实际包导入一致性证明，安装执行代码未变，不构成新的数值或性能验收。未 commit、push 或创建 PR。
