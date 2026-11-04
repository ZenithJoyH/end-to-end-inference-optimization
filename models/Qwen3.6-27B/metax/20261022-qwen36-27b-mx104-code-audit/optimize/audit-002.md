# audit-002：vLLM 源码修改与迁入 Plugin 核验

2026-10-22，Asia/Shanghai。用户询问当前容器是否存在 vLLM 源码修改，并要求将这部分修改迁入 Plugin。本次重新只读检查 `mx-104 / qwen3.6-27B-verify`；若没有待迁移内容，不制造重构或修改运行行为。

## 结论

**未发现需要从 vLLM 源码迁入 Plugin 的改动。** 当前 `/workspace/vllm` 与固定 HEAD `bc150f50299199599673614f80d12a196f377655` 一致；容器保留的 `v0.20.2` tag 和 `origin/releases/v0.20.2` 引用也指向此 HEAD。这是对容器内 Git 基准的核验，没有联网重新认证官方仓库。

检查不是只看 `git status`：逐个读取4737个受跟踪文件、约77.69MB内容，计算 Git blob SHA 并与 HEAD tree 比较，同时检查可执行位和符号链接。内容与模式差异0；assume-unchanged/skip-worktree等隐藏索引标记0；未跟踪文件0。唯一 ignored 文件为构建生成的 `vllm/_version.py`，单独核对其版本元数据。

新Python进程的 `find_spec` 和 editable 安装元数据均指向 `/workspace/vllm/vllm`；site-packages未发现另一份vLLM Python实现目录。没有将安装元数据 `0.20.2+empty` 与源码生成版本 `0.20.2` 的差异当作性能修改。

## 已在 Plugin 中的扩展

以下路径相对 `/workspace/vllm-plugin-FL`：

| 内容 | 当前位置 | 实现方式 |
|---|---|---|
| 连续 KV prefill | `vllm_fl/dispatch/backends/vendor/metax/impl/attention/flash_attn.py:810`、`vllm_fl/envs.py:16` | Plugin 自有 attention backend 与开关；两个未提交文件本来就位于Plugin |
| GDN H kernel | `vllm_fl/dispatch/backends/vendor/metax/patches/chunk_delta_h.py:306` | 运行时替换已加载 vLLM 模块的函数属性，不写vLLM文件 |
| GDN OOT | `vllm_fl/dispatch/backends/vendor/metax/patches/gdn_linear_attn.py:27` | `register_oot` 注册平台子类 |
| MetaX attention 注册 | `vllm_fl/dispatch/backends/vendor/metax/metax.py:21` | 注册Plugin内Maca FlashAttention/FlashMLA后端 |
| MCCL、CUDA wrapper等 | `vllm_fl/dispatch/backends/vendor/metax/patches/` | 平台运行时替换，已归属Plugin |

因此“Plugin改变vLLM运行行为”与“直接改写vLLM源文件”应分开表述。这些已有runtime patch将来是否收敛为更窄扩展点属于维护性设计，本次没有需要搬迁的vLLM源补丁。

两份旧contiguous patch虽然名字包含 `vllm_metax` / `VLLM020`，其diff header和installer实际目标都是 `vllm_fl/.../flash_attn.py`。它们也不是遗漏在vLLM仓库的修改。

## 执行与证据

先运行仓库inventory和仅限mx-104的connectivity-check，连接通过。只读检查没有修改源码、索引、依赖、容器或服务；未执行模型测试。由于待迁移文件数为0，本次不实施迁移，也不重新生成已有代码包。

新增证据保存到同一远程案例目录，文件名独立，不覆盖原始归档：

- `commands/verify-vllm-tree-audit-002.py`：逐文件核验代码。
- `manifests/vllm-tree-audit-002.json`：4737文件的比较结论、Git标记、安装与解析路径。
- `manifests/vllm-extra-audit-002.json`：生成版本文件及相关Plugin文件指纹。
- `review/vllm-source-audit-002.md`：本报告。

远程案例根：`/public-flash/jinghao/qwen3.6-27B/20261022-qwen36-27b-mx104-code-audit`。原始文件SHA写入同目录 `state.yml` 的外部证据索引。
