# Plugin 迁移至最新 release/0.2 基线

2026-10-22；Host `mx-104`；容器 `qwen3.6-35B-verify`。用户要求将该容器 Plugin 修改调整到最新 `https://github.com/flagos-ai/vllm-plugin-FL/tree/release/0.2` 上。当前工作范围为基线迁移与现有优化移植，不开展新的性能优化。

## 执行前冻结

- GitHub branches API 本轮返回 `release/0.2` 最新 SHA `7cb559947cb61fd8b69fa5027d8ec113e528a644`；实际抓取后再次核对。
- 原仓库 `/workspace/vllm-plugin-FL`，HEAD `d1653d9ff0450ce0366686bfcde5d8aecab44755`，main，5 个 tracked 修改和 3 个 untracked 文件；全部保留。
- 原 Plugin 为 editable 安装，版本 `0.2.0+gd1653d9ff`；vLLM `0.20.2`、FlagGems 与刚完成 editable 切换的 FlagGems-vllm 均保持当前版本和代码。
- 仅 `/public-flash` 与 `/data` 为容器目录挂载；Plugin 源码位于容器私有层。当前无模型服务/worker。
- 远端产物沿用 `/public-flash/jinghao/qwen3.6-35B/20261022-qwen36-35b-mx104-code-audit`，本轮新增 `plugin-release02-001/`。

实施方式：先备份原 Git 差异、未跟踪文件、运行源码清单及安装入口；在容器私有新目录准备独立 checkout，抓取并锁定目标 SHA，三方合并原优化，处理接口变化。完整原仓库备份到 `/workspace/vllm-plugin-FL.before-release02-20261022`，新仓库占用原 `/workspace/vllm-plugin-FL` 路径，并离线 `--no-index --no-deps --no-build-isolation` editable 重装刷新元数据。无 commit/push，不升级其他组件。

上游 MoE 改用 CachedOp，保留新结构；本地 SiLU 接入沿用相同 key 并按新结构调整。GEMM2 配置、连续 KV Prefill、采样分支及其边界保持现有语义。独立审查已在原环境确认 PlatformFL 的 `device_name=metax`、`is_cuda=False`，旧 `is_cuda()` 和新 `device_name=='nvidia'` 完整 MoE 快路径均不命中，不为迁移额外扩大适用范围。

本轮一次性命令先保存在远端 `commands/` 再执行。本地仅保留摘要、远端路径与必要 SHA。回退由完整原仓库及安装入口备份恢复，操作前检查当前候选和源码状态，避免覆盖后续工作。

## 当前交付

- 容器源码 `/workspace/vllm-plugin-FL`，分支 `release/0.2`，HEAD `7cb559947cb61fd8b69fa5027d8ec113e528a644`。这是本轮 GitHub API 与实际 fetch 双重核验的分支最新提交：[上游提交](https://github.com/flagos-ai/vllm-plugin-FL/commit/7cb559947cb61fd8b69fa5027d8ec113e528a644)。相对旧基线增加 46 个提交、上游改动涉及 367 个文件。
- editable 版本 `0.2.0+g7cb559947.d20261022`；实际加载 `/workspace/vllm-plugin-FL/vllm_fl/__init__.py`，`direct_url.json` 为 `editable=true`、`file:///workspace/vllm-plugin-FL`。
- 原 5 个 tracked 修改及 3 个 untracked 文件完整移植，仍作为工作区未提交修改保留；未创建 commit、PR 或 push。
- 原完整仓库及安装入口备份保留。首次直接重命名因 OverlayFS 返回 EXDEV，发生在源码/安装变更之前；改为完整复制并比对所有文件内容、链接、模式（含 Git 元数据）后替换该容器私有目录。相关失败和成功回执均保留。
- vLLM、FlagGems、FlagGems-vllm 的 Git 身份/差异及 Gems 源码清单均与操作前一致；其他 Python distribution 的版本和依赖声明未变。FlagGems-vllm 继续从 `/opt/FlagGems-vllm/src/flaggems_vllm` editable 加载。

## 原优化的移植边界

| 修改 | 新基线下的处理与证据 |
|---|---|
| `flash_attn.py` / `envs.py` 连续 KV Prefill | 保持原开关、支持条件和实现；与原修改后文件 AST 相同 |
| `topk_topp_sampler.py` | 保持 Qwen MoE shortlist 和 Qwen3-VL counting 选择及 fallback；仅继承上游文件头，AST 相同 |
| `fused_moe.py` | 保持 GEMM2 独立配置、BLOCK_SIZE_M 检查等；按上游结构将原 6 处 `call_op` 对应到相同 key 的 CachedOp，归一化后核心函数 AST 相同 |
| `fused_moe_utils.py` | 保持目标 BF16、非量化 MetaX staged 路径；3 处调用按相同 key 调整为 CachedOp，包括新增 `_silu_and_mul` 实例。保留上游新增 W8A8 guard 及 Kunlunxin/NVIDIA 分支；目标路径后缀 AST 相同、上游前缀与 HEAD 相同 |
| `E=256,N=256,device_name=metax.json` | 原字节保留，原 `VLLM_TUNED_CONFIG_FOLDER` 路径继续有效 |
| `qwen36_moe_shortlist.py` / `qwen3_vl_counting.py` | 两个原 untracked 实现均按原字节保留，未丢失共享采样入口的依赖 |

实际平台为 `PlatformFL`、`device_name=metax`、`device_type=cuda`、`is_cuda=False`。旧版 `is_cuda()` 与新版 `device_name=='nvidia'` 完整 MoE 快路径在本平台均不命中；不能只根据兼容 CUDA 的 device_type 断言走该快路径。模型实际配置为 BF16、无 quantization_config。

“优化逻辑保持”指上述原有局部修改及目标路径。升级同时包含上游 46 个提交，不以局部 AST 相同推断整个新基线的模型行为、graph 或性能均与旧版相同。

## 已执行验证

| 核验 | 结果及范围 |
|---|---|
| 三方合并与语法 | 5 个 tracked 文件合并无文本冲突；302 个 Python 文件语法通过；`git diff --check` 通过 |
| 原优化语义与文件一致性 | 8 个修改文件通过 AST/精确字节验证；上游新增分支单独保留并核验 |
| 上游 CPU/mock 单测 | 101 passed，8.08 秒；dispatch call_op / policy / manager、activation、FlagGems whitelist。测试期间 463 个源码/配置文件不变；未使用设备模型或 GPU graph |
| 原版与新版实际 dispatch 选择 | 5 个 key 的 impl_id 完全相同，见下表；验证的是进程内解析/缓存预热，没有调用 GPU kernel |
| 实际模块与函数 | 安装后 89 个已加载 Plugin 模块（含生成的 `_version.py`）全部来自当前 `/workspace/vllm-plugin-FL`；7 个修改的 Python 模块中 50 个实际函数代码对象与对应源码重新编译结果一致 |
| 采样器构造符号 | 按 active 探针的完整顺序（平台、general plugin、attention 与 sampling 模块）初始化时，vLLM sampler 构造点、ops 模块与 Plugin 的 `MetaXTopKTopPSampler` 为同一个对象；重复 `register_model()` 不报错。未执行 `importlib.reload` |
| 安装与其他组件 | Plugin 元数据及 `_version.py` 一致，提交标识为 `7cb559947`；其他 distribution 未变，vLLM/Gems 代码未变 |
| 隔离解析与补丁复现 | 从 `/tmp` 使用 `python -I -B` 忽略 cwd/PYTHONPATH 后仍指向新源码；仅有一个 Plugin distribution，旧安装入口无残留；完整补丁独立 check/apply 后 8 文件与实际源码逐字节相同 |

候选阶段尚未执行 editable 构建，生成的 `_version.py` 曾由旧 editable finder 提供，CPU 测试包装器因此记录一次来源断言失败（pytest 本身为 101 passed）。正式安装生成新版本文件后，上述 89 模块的严格路径核验已通过。最初的全方法 AST 比对也正确识别了上游 W8A8/平台分支变化；最终采用“上游前缀相同 + 目标 staged 后缀相同”核验，没有删除上游逻辑来满足旧版断言。

| key | 原版 / 新版 impl_id | callee 归属 |
|---|---|---|
| `moe_align_block_size` | `default.flagos` | `flag_gems.moe_align_block_size_triton` |
| `invoke_fused_moe_triton_kernel` | `default.flagos` | `flag_gems.invoke_fused_moe_triton_kernel` |
| `moe_sum` | `default.flagos` | `flag_gems.moe_sum` |
| `silu_and_mul` | `default.flagos` | `flag_gems.modules.activation.gems_silu_and_mul` |
| `topk_softmax` | `vendor.metax` | `vllm._custom_ops.topk_softmax` → `torch.ops._moe_C.topk_softmax` |

独立复核确认上述 backend 方法和实际 wrapper 的旧/新 AST 相同，未把 MoE callee 改到 FlagGems-vllm。正常重复初始化会出现上游 DeepSeek 注册同一实现的 warning；原版 reference 注册缺少属性的 warning 在新版导入中已消失。日志按原样保留。

**继承的采样导入顺序问题**：额外直接导入 `vllm.v1.sample.ops.topk_topp_sampler` 的探针触发循环导入；仅先取 `current_platform` 仍不足以避免。随后显式加载补丁时，ops 符号会更新，但已被 `vllm.v1.sample.sampler` 导入的类别名可能保持原类。使用原完整备份与新版本运行相同 sampler-first 顺序，均观察到 `constructor_identity=false`、`filter_identity=true` 和相同循环导入 warning；证据为 `sampler-first-import-comparison.json`，该问题非本次迁移新增。本轮保留原实现，不以通过的 active 顺序掩盖此限制；实际服务启动顺序及采样优化是否命中仍待服务验证。

## 外部产物与回退

以下相对路径以 `CASE=/public-flash/jinghao/qwen3.6-35B/20261022-qwen36-35b-mx104-code-audit` 为根，主要结果位于 `CASE/plugin-release02-001/`。

| 产物 | 内容 |
|---|---|
| `before.json`、`original.patch`、`original-changes/` | 原 Git/安装身份、源码清单、5 tracked 差异及全部 8 个原文件 |
| `installation-before.tar.gz`、`original-full-backup.json` | 原 editable 安装入口备份及完整原仓库备份清单 |
| `preparation.json`、`merge-result.json` | 上游差异和合并结果 |
| `semantic-verification-v2.json` | 最终语义核验；初版失败结果另保留，不覆盖 |
| `tests-cpu-mock-001/{receipt.json,junit.xml,pytest.log}` | 101 个 CPU/mock 测试及候选版本来源问题原始证据 |
| `{original,candidate,active}-import.json` | 三阶段模块、函数、平台和实际 impl_id；对应日志在同目录 |
| `activation.json`、`editable-install.log` | 成功安装、版本、源码及其他依赖不变的回执 |
| `rebased-plugin-release02.patch` | 基于新 HEAD 的完整局部补丁，包含 3 个未跟踪文件 |
| `final-validation.json`、`isolated-import-v3.log` | 完整补丁独立应用、隔离 Python 解析、旧入口清理等最终核验 |
| `sampler-first-import-comparison.json`、`*-sampler-first-import.log` | 原版/新版相同导入顺序问题的对照；最终核验中保留这一限制 |
| `commands-sha256.json` | `CASE/commands/` 本轮全部保存脚本的 SHA256 |

安装执行命令：`/opt/conda/bin/python -m pip install --no-index --no-deps --no-build-isolation --disable-pip-version-check --no-cache-dir -e /workspace/vllm-plugin-FL`。没有改变运行时环境变量或升级其余依赖。

完整补丁 SHA256：`87c1da39ecd5ae1f072df4d0173a826c9b9c90f05105448b2adf280f9cdb8e58`。原未跟踪 JSON 保留 CRLF 字节；独立应用时按 `core.whitespace=cr-at-eol` 识别换行，未执行 whitespace 自动修复。最终核验完成于 2026-10-22 20:04（Asia/Shanghai）。

回退脚本为 `CASE/commands/rollback-plugin-release02.py`，本轮仅保存并语法校验，未执行。可在 Host 运行 `python3 <该绝对路径>`；它首先要求无模型/worker、当前源码和安装文件仍与交付清单一致、原备份未变，然后保留新仓库到 `/workspace/vllm-plugin-FL.release02-rolled-back-20261022`，恢复旧仓库及原 editable 元数据。后续有源码修改时会停止，需重新审阅，避免覆盖新工作。恢复后应重新做 import/代码核验。

关键命令 SHA256：

- 成功激活 `activate-plugin-release02-v2.py`：`d6635eec2cabd68f57a6f6f8a0908517e297b5c001e9b9a8896e12a13eb44036`。
- 安装后探针 `probe-plugin-release02-v3.py`：`2d1e6c4179339fbd279a18abf8ad549bd3628b7745eb2bc825500faddaeee5f8`。
- 回退 `rollback-plugin-release02.py`：`8ff21c8f2b158bfcd2dff44841183af48d5c5119114888cd47ab94eb6145808c`。
- 最终归档核验 `finalize-plugin-release02-v3.py`：`1d84f5d69d7ef12a718267e617ae33b903f0a05a80d0aa91bdf57a8470b6cd63`。

## 结论边界

`migration=completed`；源码/安装/导入/目标 dispatch 解析一致。`pr_readiness=needs_revision`：原优化范围和实现均予保留，尚需采样边界及非目标路径的数值验证、目标 graph 启动/capture/两次 replay、模型精度和同配置性能回归，才可评价升级后的端到端行为与 PR 验证充分性。

本轮没有启动模型服务，没有硬件数值、graph、正式精度或性能结果；其他平台/其他模型的硬件验证为 `not_run`。上游 CPU/mock 测试不代表这些项目通过。
