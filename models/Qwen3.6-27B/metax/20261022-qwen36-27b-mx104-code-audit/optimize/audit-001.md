# audit-001：Qwen3.6-27B verify 容器代码与优化点

日期：2026-10-22（Asia/Shanghai）。范围为 `mx-104 / qwen3.6-27B-verify`。用户明确选择保留现有实现，整理代码、补丁包和说明。本次完成代码保全和静态审计；未启动服务、修改源码、安装依赖或执行性能/精度测试。

## 核心结论

当前容器包含不同来源的实现和参考材料，不能直接用本地历史或目录名称判断哪些优化已对 27B 生效：

1. Plugin 的未提交语义改动只有一项：可选的连续 KV 单 prefill FlashAttention，涉及两个文件。
2. 补全模型调用链后，当前27B的 GDN 主路径直接进入 vLLM 自带 FLA；Plugin 中选择 `flag_gems.fused.FLA` 的遗留 wrappers 没有连到该主路径。FlagGems/FlagGems-vllm 中的融合代码应保留，但不能因已安装或有白名单字符串就认定接入了该模型。
3. FlagGems-vllm 的 GDN 固定配置确实已安装，但其 H8/H16 条件不匹配本模型常规 TP2 的 value-head H24，也没有当前服务命中证据。
4. FlagGems-vllm 安装包额外存在一项 MoE 改动，源码仓库没有它。它应保留在还原包中，不能计作 dense 27B 的收益。
5. 远程工作目录中的旧启动脚本与当前 Plugin 存在开关名、GDN 白名单名和模型路径差异。脚本原样归档，不能直接当作此次容器的已验证启动入口。

采集时容器处于 running 状态，但 `/proc` 检查未发现 vLLM/EngineCore/Worker 推理进程。因此本文区分“磁盘实现存在”“包解析路径已核验”“静态可达条件”和“运行时命中”；最后一项本次没有证据。

## 环境与源码身份

用户模型目录：`/data/Qwen3.6-27B`。配置为 `Qwen3_5ForConditionalGeneration / qwen3_5_text`，64 层，48 层 linear attention、16 层 full attention；BF16，dense MLP。全模型 Q/KV heads 为 24/4，full-attention head dim256；linear key/value heads 为 16/48，K=V=128。旧脚本写 TP2，但没有当前运行拓扑证明；本文 H24 仅为常规 TP2 分片推导。

| 组件 | 版本 / revision | Python 包解析路径 | 本次观察 |
|---|---|---|---|
| vLLM | `0.20.2+empty`，`bc150f50299199599673614f80d12a196f377655` | `/workspace/vllm/vllm`，editable | detached HEAD；Git 工作区干净；抽查 attention/FLA chunk 与 HEAD 字节一致 |
| Plugin | `0.2.0+gd1653d9ff`，`d1653d9ff0450ce0366686bfcde5d8aecab44755` | `/workspace/vllm-plugin-FL/vllm_fl`，editable | main；2 个已跟踪修改，无 untracked |
| FlagGems | 安装元数据 `5.0.2`；revision 未知 | `/workspace/FlagGems/src/flag_gems`，editable | 无 `.git`，无可追溯 `_version.py`；保留当前源文件和 SHA，不编造基线 diff |
| FlagGems-vllm | `0.1.0`；源码 `e1a02b6b2e47abea9a6cfeaaf3431f50f7f476f8` | `/opt/conda/lib/python3.12/site-packages/flaggems_vllm`，普通安装 | 源码在 `/opt/FlagGems-vllm`；1 个未提交源码文件；安装包另外有 1 个差异 |
| Torch | `2.8.0+metax3.7.0.7` | 安装包元数据 | 未运行设备计算 |
| FlagTree / Triton | FlagTree `0.6.1+metax3.6` | `/opt/conda/lib/python3.12/site-packages/triton` | Triton 由 FlagTree 提供，不能把无 triton distribution 误判为未安装 |
| FlashAttention | `2.6.3+metax3.7.0.7torch2.8` | 安装包元数据 | MetaX vendor 依赖 |

镜像 ID 为 `sha256:afcbdac2f632d7a37de05f318cfe804007cc0ce3a332be8ff36f0d1913c74a9e`，引用 `harbor.baai.ac.cn/flagos-inner-models-release/metax-qwen36-27b-release-1021:latest`。`/data`、`/public-flash` 为共享 bind mount；`/workspace`、`/opt` 没有对应目录挂载。本次只在用户远程目录的新案例子目录写审计产物。

## 优化点与适用边界

以下分类描述代码的主要机制，不代表本次测得性能收益。

### A. 连续 KV prefill FlashAttention：Plugin 本地改动

- 分类：`operator/replace`，以 KV 布局转换选择 vendor FlashAttention 的连续 KV 路径。
- 文件：`vllm_fl/envs.py:16`；`vllm_fl/dispatch/backends/vendor/metax/impl/attention/flash_attn.py:661,804`。
- 方法：从分页 KV cache 的 block table 收集 key/value，构造连续 KV，再调用不带 block table 的 `flash_attn_varlen_func`。意图是用额外 gather/临时张量成本换取长 prefill 的执行效率。
- 当前开关：`VLLM_FL_METAX_CONTIGUOUS_SINGLE_PREFILL=1`，默认关闭；在 impl 初始化时读取。
- 条件：最终后端为 MetaX `MacaFlashAttention`、非 cascade、DCP=1，当前批次恰有一个 prefill、该请求累计 KV 长度至少 2048、KV 非量化。批次可以同时包含 decode 请求；阈值不是本次新增 query token 数。
- 不满足条件时保持原分页 prefill；decode 分支不改。
- 当前默认 MetaX dispatch 指向 vendor 后端。仍须以实际 dispatch policy/运行命中为准；旧 `VLLM_FL_USE_FLAGGEMS_ATTN` 在本 revision 没有读取点。
- 原始 Git diff 显示 1278 增、1234 删，主要因为两个文件 LF→CRLF。语义补丁保留相同 Python AST，原样补丁保留逐字节结果；没有改写容器换行符。
- 尚未验证的边界：短/长 chunk、mixed、sliding window、量化 fallback、graph capture/replay、gather 临时内存及实际端到端净收益。

### B. GDN 模型主路径与 FlagGems 融合实现

补充采集 `vllm/model_executor/layers/mamba/gdn_linear_attn.py` 后，当前代码链如下。MetaX OOT 类继承 `_forward_core`，它自己的 `forward` 经 `torch.ops.vllm.gdn_attention_core` 回到该方法。

| 阶段 | 当前静态调用链 | 配置及范围 |
|---|---|---|
| Prefill | GDN 本地 `ChunkGatedDeltaRule` → 本地 `forward_native` → vLLM `fla.ops.chunk_gated_delta_rule` | MetaX `PlatformFL.is_cuda()` 为 False，默认 auto 不满足 FlashInfer 条件，走 vLLM Triton/FLA |
| 常规 decode | `_forward_core` → vLLM `fused_sigmoid_gating_delta_rule_update` | 未走 packed 分支的 recurrent decode；不是 Plugin 遗留 `fused_recurrent_gated_delta_rule_fwd` wrapper |
| Packed decode | `_forward_core_decode_non_spec` → vLLM `fused_recurrent_gated_delta_rule_packed_decode` | `VLLM_ENABLE_FLA_PACKED_RECURRENT_DECODE` 启用、无 speculative mask、无 prefill、有 decode；旧脚本设置了该开关，实际服务未运行 |

精确位置：GDN `383,384,772,956,975,1051`；vLLM `fla/ops/__init__.py:9–15`。这些主路径没有导入 FGV 或调用 Plugin 遗留 wrappers。vLLM 自带代码及 Plugin HEAD 中的 MetaX H-kernel 平台兼容 patch 属当前环境已有能力，不包装成本次新优化。

以下是 **FlagGems 库内存在、尚未证明接入本模型** 的融合实现：

- 分类：`operator/improve`。
- 遗留 wrapper：Plugin `vllm_fl/ops/fla/chunk.py:12–15` 按精确键 `chunk_gated_delta_rule_fwd` 选择 `flag_gems.fused.FLA` 或 vLLM 原生实现；不能把这个 wrapper 当成上表实际模型入口。
- FlagGems `fused/FLA/chunk.py:92` 将 gate cumsum、KKT 和三角求逆合并到 `fused_cumsum_kkt_solve_tril.py`，随后调用 `recompute_w_u_fwd`、H-state 和 output kernel。融合可减少 kernel launch 和中间读写，但本次没有测量收益。
- varlen 使用 BT64；当前实现支持 K128、value/key head 比3的形状。库函数支持该形状不等于当前模型接入它；仅修改白名单名称不能补足调用链。
- `chunk_fused_tail_vblock.py` 虽已接入，但 guard 要求 K=V=64，当前27B K=V=128不符合；不把它列为27B收益。
- `chunk_gated_delta_direct.py` 通过 FlagGems 公共 wrapper 接入，Plugin 直接调用 FLA `_fwd`，绕开该 wrapper；也没有当前服务命中证据。
- FlagGems MetaX MM 另有 occupancy/L2 预算、Split-K、小 N/GEMV 等选择能力。由于缺少来源基线，且旧脚本白名单没有 mm/mm_out，本次保留源码，不认定为该容器新增或已生效优化。

### C. FlagGems-vllm GDN：已有融合实现与本地固定配置

- 分类：`operator/improve`；文件 `src/flaggems_vllm/runtime/backend/_metax/fused/gdn_chunk.py`。
- e1a02b6 已包含融合 cumsum/KKT/求逆、V-major 状态布局、H kernel 配置搜索、N/skew 分桶和特定 kernel 的 LICM 编译绕行。这些属于当前 HEAD 已有实现，不混入本地未提交补丁。
- 本地 diff 仅新增 `_prune_qwen_h_configs` 和一次性配置日志（421–454、494、979–995），保留单个 H kernel 配置，意图减少新分桶在线 autotune 的停顿；这不自动等于预热充分后的稳态收益。
- 条件：H8/H16、K=V=128、BT64、varlen、有 final state。H8且有 initial state选 BK64/BV32/W2/S3，否则选 BK64/BV64/W4/S3；条件外保留原候选。
- `H=u.shape[-2]`（956），是 value heads。27B 常规 TP2 推导为 H24，不能拿 key-head H8替代。TP4 的 value-head H12也不满足。
- 源/安装文件逐字节一致；但当前模型静态入口直接走 vLLM FLA，不是 FGV。只能归为“已安装、当前目标启用未证明且常规形状不匹配”。
- 维护注意：进程级 compiler wrapper、skew 分桶读取引起的同步和打印日志需在未来 PR 整理中评估；本次原样保留。

### D. 安装包独有 MoE：环境附带内容

- 分类：`operator/improve`，附带诊断日志。
- 源码与安装包共276个文件，只有 `_metax/fused/fused_moe.py` 不同；没有两侧独有文件。
- 安装包增加 E256/topk8 的小专家形状，对大 M GEMM1 使用 BK32，并扩展 GEMM2 basic pipeline 和一次性配置日志。
- 27B 是 dense MLP，不能将此项计为27B性能贡献。原样导出为独立 overlay 补丁；从源码直接重新安装会丢失这处安装包改动。

## 旧脚本和参考材料

| 材料 | 与当前代码的关系 | 本次处理 |
|---|---|---|
| `start-model-base.sh` / `start-model-flagos.sh` | 模型路径分别为 `/public-flash/models/Qwen3.6-27B`、工作目录下 `Qwen3.6-27B`，不是用户本次指定 `/data/Qwen3.6-27B`；是否别名未验证 | 原样保留，不执行 |
| `VLLM020_CONTIGUOUS_SINGLE_PREFILL=1` | 当前 Plugin 不读取；当前读取新名字 `VLLM_FL_METAX_CONTIGUOUS_SINGLE_PREFILL` | 记录启用差异，不替用户修改参数 |
| `VLLM_FL_USE_FLAGGEMS_ATTN=1` | 当前 Plugin 无读取点，不能凭它宣称选择了 FlagGems attention | 记录为旧配置 |
| `gdn_prefill,gdn_decode,gdn_packed_decode` 白名单 | 当前没有 alias 映射；遗留 wrappers 的精确键为 `chunk_gated_delta_rule_fwd`、`fused_recurrent_gated_delta_rule_fwd`，但当前模型也未连接这些 wrappers | 不能据旧脚本或简单改名宣称 GDN 命中 |
| `/opt/dense27b_contiguous_prefill_patch_ly` 与 `/opt/qwen36-final-moe/patches` | 两份旧 patch 语义相同，都修改 Plugin；名字虽写 vllm，但没有对应当前 vLLM dirty 改动；旧 patch 的开关与门槛和当前不同 | 放入 reference-only，不作为当前重放补丁 |
| `/opt/qwen36-moe-v725/patches/full_dynamic_shape_fix.diff` | 当前 FlagGems MetaX `full.py` 仍保留按 N autotune 和 scale 路径，未体现该旧 patch | 标为未在当前文件体现，不计收益 |
| `short_1k.json`、`long_context.json` | MoE 配置参考；不能以存在证明被27B使用 | 原样包含在快照 |

没有复制或引用旧 README 中的加速比，也没有从用户本地历史继承精度 gate。

## 代码包结构与恢复边界

远程根目录：`/public-flash/jinghao/qwen3.6-27B/20261022-qwen36-27b-mx104-code-audit`。

交付包 `code-review-bundle.tar.gz` 解开为 `delivery/`：

```text
README.md
optimization-map.md
patches/
  01-plugin-contiguous-prefill.semantic.patch
  01-plugin-working-tree.exact.patch
  02-fgv-gdn-fixed-config.patch
  03-fgv-installed-only-moe.patch
  series.json
snapshots/code-snapshot.tar.gz
snapshots/supplement.tar.gz
manifests/
reference-only/
review/
commands/
SHA256SUMS
```

两个 `01-*` 是同一改动的替代表示，不能叠加应用。语义版基于 Plugin d1653d9，换行归一为 LF；exact版基于同一 HEAD，重放出容器原始 CRLF 文件。`02-*` 基于 FGV e1a02b6；`03-*` 以该仓库源码为前像、安装包为后像，路径映射成源码 `src/flaggems_vllm/...` 以便评审，还原安装态时须显式处理安装映射。补丁已在临时前像目录验证，没有应用到目标容器。

FlagGems 没有 Git 基线，交付当前源码快照及逐文件 SHA。vLLM 交付 revision、干净状态和相关调用链文件。包不含权重、数据集、缓存、日志、native 二进制或完整 Git 对象库，不能冒充完整镜像备份；恢复原环境还需要已记录的镜像和依赖。

## 本次验证、保留决定与限制

- 代码快照4116个清单条目已逐一核验 SHA；补充调用链另有独立清单与 SHA。
- 4个补丁表示均通过 `git apply --check` 和实际临时应用回放；exact/FGV 对比逐字节相等，semantic 对比归一化字节及 AST 相等。
- 两个 FGV 树共276文件逐字节比较；关键 Python 文件完成 AST 语法检查。
- 包解析位置来自新建轻量 Python 进程的 `find_spec`/安装元数据，不是运行中模型函数对象证明。
- 当前实现全部保留；没有删除文件、源码重构、升级依赖、运行服务、提交或推送。
- 精度、性能、graph capture/replay、新正式验收均 `not_run`；主指标变化和单项收益均未知。`pr_readiness=needs_revision`，表示代码与证据已整理，但启用条件、适用范围及硬件回归尚不足以作为最终性能 PR。
- 本次只形成容器实况记录，不修订性能 SOP，不把一次静态观察升级为通用性能结论。

## 外部证据

路径均位于上述远程根目录：

- `snapshots/code-snapshot.tar.gz`：SHA256 `cbfde87955eefde60a67b755938a498b4718df675b1497ae6b9feaec3e2369f8`。
- `snapshots/supplement.tar.gz`：SHA256 `40fca2f2142d280c391714bec27c84e197e85316c538607863bac241864d1378`。
- `manifests/inspect-sanitized.json`：筛选环境变量后的容器信息；非完整环境变量转储。
- `delivery/manifests/patch-validation.json`、`fgv-source-vs-installed.json`、`source-files.json`：回放和逐文件校验依据。
- `delivery/review/`：Plugin、FGV、FlagGems/运行时的专题代码审阅。
- 包总 SHA、最终源码一致性核验见同目录 `state.yml`，不在正文重复维护。
