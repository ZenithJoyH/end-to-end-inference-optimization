# BGE-M3 收敛空间与 NVIDIA 接口复核

> 本文为修改前审查快照；用户随后授权的修复已应用到实际安装源码，结果见[interface-fix-003](../../../models/BGE-M3/metax/20261105-bge-m3-mx59-base-1k/optimize/interface-fix-003.md)。下文未对齐/未修改描述保留为历史审查证据。

2026-11-06（Asia/Shanghai）。用户要求再次检查适配代码是否还能收敛、是否新增算子，以及算子接口是否与 NVIDIA 对齐。本轮为只读审查：重新验证 mx-59 连接、BGE-M3 私有安装目录及三库完整补丁身份；未修改三库源码、安装、服务或 GPU 分配，未运行新的模型精度、性能或 NVIDIA 硬件测试。

结论：仍可删除一层约 6 行的 Plugin 转发函数，但没有保留 FP16/FP32/joint 全部功能同时大幅删除运行时代码的充分依据。没有新增公开算子 API 或独立数值 kernel；FG/FGV 修改的是既有算子的调优与能力。当前 BGE 使用的 attention 参数子集兼容，FGV 的完整接口尚未与当前 vLLM NVIDIA 接口对齐。

## 当前审查基线

三库根均位于 BGE-M3 容器 `/workspace/bge-m3/tune-src/`，远端读取的完整 patch SHA 与上一轮交付一致。

| 仓库 | Git HEAD | 完整 diff | Patch SHA256 |
|---|---|---|---|
| vllm-plugin-FL | `5463eae824b1fbaa3d331564ab2fb4c51f1b6e09` | 30 files / +1539 / -3 | `1f68a24bff51c88028f5b2764cca0b60a3e560089cd6f4eae63229b5826412bf` |
| FlagGems | `4897cc306cd83390c95b83b50df28f7edb1684c5` | 3 files / +191 / -1 | `d5aa1dbee7bce2b6c9862638d11b853636fae8665f4a4ef22f873c8231bbb7e8` |
| FlagGems-vllm | `7417158440a80753fb21dab3a124c1be388ab7eb` | 7 files / +617 / -12 | `e2afb78b80c84978e231fd2667cd71f896ccab52f7c9d6830b23a1eecc3ee731` |

Plugin 新增行包含运行时代码 431、测试 904、文档/示例/构建 204。不能把完整 diff 的 1539 行都视为运行时适配负担。上一轮 363 项与模型回归仍是上一轮证据，本轮不重新计为测试通过。

## 算子清单与职责

| 名称 | 实际变化 | 归属及结论 |
|---|---|---|
| `bge_m3_encoder_attention` | Plugin 新增内部 dispatch key，provider 转发到 FGV 公开入口 | 不是新增数值 kernel，也不是另一套公开 attention 算子 |
| `flag_gems.linear(input, weight, bias=None)` | 原 MetaX Linear 增加限定 FP32 shape 的独立 tuner 和两个配置候选，复用原 `linear_kernel` | 既有 ATen 算子优化；公开签名未改，NVIDIA 文件未改 |
| `flaggems_vllm.flash_attn_varlen_func` | 原 MetaX direct attention 扩展 FP32、IEEE QK/PV 计算、资源限制和配置选择 | 既有算子能力扩展；修改原 kernel，未新增独立 kernel 或公共 API |

Plugin 中 PAD 位置修正属于 token/position metadata；joint Pooler 复用 vLLM 既有 heads 并组织输出；IOProcessor 承担请求和响应处理。不能仅因这些代码使用 Tensor 操作，就把它们统称为新增底层算子。

## NVIDIA 接口：存在继承的完整签名差异

以实际安装的 vLLM 0.24.0 所调用的 `vllm.vllm_flash_attn.flash_attn_varlen_func` 为对齐目标，而不是另一个同名 FlashAttention 包。已通过 GitHub connector 读取[官方 v0.24.0 源码](https://github.com/vllm-project/vllm/blob/v0.24.0/vllm/vllm_flash_attn/flash_attn_interface.py#L176)，与容器内该文件逐字节相同，SHA256 均为 `690ddd0bcb3576d7d74693a766ffc51b0522ce00d5424570d7f77c2eb49c5f2d`。

| 对照项 | FGV 当前接口 | vLLM 0.24.0 NVIDIA 接口 |
|---|---|---|
| 参数个数 | 30 | 34 |
| 前 24 项，`q` 至 `v_descale` | 名称、顺序及实际默认值相同 | 相同 |
| 缺少的参数 | 未接收 | `output_scale`、`mask_mod`、`aux_tensors`、`dynamic_causal` |
| 第 25 项起的位置顺序 | `s_aux, num_splits, cp_world_size, cp_rank, cp_tot_seqused_k, fa_version` | `num_splits, output_scale, fa_version, s_aux, cp_world_size, cp_rank, cp_tot_seqused_k, mask_mod, aux_tensors, dynamic_causal` |
| `fa_version` 默认 | 2 | 常量 `DEFAULT_FA_VERSION` 的值为 2 |
| 返回结构 | 默认 `out`，请求 LSE 时 `(out, lse)` | 同左 |

已执行 AST 签名提取和 Python 参数绑定检查，不导入 GPU 依赖、不调用数值实现：

- 当前 BGE 的 Q/K/V 三个位置参数及 `out/cu_seqlens_q/cu_seqlens_k/max_seqlen_q/max_seqlen_k/causal/softmax_scale` 关键字，在两侧均可正确绑定。
- 显式传入上述四个新增参数，即使值为 `None`，FGV 仍会产生 `TypeError: unexpected keyword argument`；vLLM 签名可接受。
- 第 25 个位置实参在 vLLM 绑定到 `num_splits`，在 FGV 绑定到 `s_aux`。因此两者不能作为任意调用的无差别替换。
- FGV 完整 BGE 补丁没有修改第 1197 行的函数签名，首个相关 hunk 在第 1376 行。这是原版本接口差异，不是本次 FP32 扩展造成。当前 BGE 调用未触发，不把它误报为当前服务故障。

如果后续补齐完整接口，应作为独立兼容性修复：明确目标 vLLM 版本，核查现有位置调用、其他平台及 C-extension 转发，支持参数真实透传，不支持的非默认选项在执行前明确拒绝。不能用 `**kwargs` 静默吞参数，也不能直接重排参数后假定旧调用无影响。

此外，MetaX 的 FP32 能力不等于 NVIDIA 同 dtype 已验证。当前 FGV NVIDIA Hopper launcher 仍限 FP16/BF16；MetaX FP32 只承诺 forward、非 paged、非 causal 的完整双向 attention，其他不支持组合有显式拒绝。本轮未连接 NVIDIA 主机。

## Linear 与 Plugin 包装的补充发现

1. **Linear 签名相同，但不能声称全部异常语义对齐。** FG 通用/NVIDIA 路径 `src/flag_gems/ops/linear.py:399` 对输入 K 与 weight K 不匹配提前抛出 `RuntimeError`；MetaX 路径 `src/flag_gems/runtime/backend/_metax/ops/linear.py:215` 附近缺少对应检查。该差异已存在于原基线，本次补丁未引入，当前 BGE 合法 shape 不触发。最小修复应是执行前维度检查和零 launch 负例，不需要修改 kernel。
2. **Plugin 的同名包装不是完整 FlashAttention API。** `vllm_fl/models/bge_m3/attention.py:18` 和 provider `vllm_fl/dispatch/backends/flaggems/impl/bge_m3.py:16` 使用 `(query, key, value, **kwargs)`，无法直接接收 `q=, k=, v=`。当前调用以位置方式传 Q/K/V，未触发问题。它们是内部适配边界，不应描述为与 NVIDIA 完全同签名的公共接口。

## 可以继续收敛的范围

- 推荐删除 `models/bge_m3/attention.py:18–22` 的单调用点同名转发函数，在 `_forward_encoder_attention` 内直接调用 `get_default_manager().call_once(...)`。运行时代码约减少 6 行，也避免与真正的 FlashAttention API 混淆。相应测试应从真实模型入口发起，继续证明 dispatch、I/O hook、output identity 和部分写入报错不重试。
- provider 如统一采用 `q/k/v` 命名，应一起补关键字转发测试；它仍是受限的内部 provider，不能据此宣称完整上游 API 对齐。
- 不建议仅为减少一个文件移动模型注册入口：会牵涉 pyproject entry point 与安装元数据，收益只有少量行数。
- 保留 `call_once`、FP32 能力/shape guard、graph `NEVER` 声明、私有 tokenizer/Lock/ContextVar、joint 输出头和尺寸校验、PAD 修正、Worker 异步输出支持。这些代码对应已保留功能或明确支持边界。
- FG 独立 tuner 与 FGV FP32 metadata 校验、IEEE 计算和资源限制不属于冗余。删除测试或合并到更宽的全局策略不构成安全收敛。

本轮只完成审查与可复现的静态接口核验，没有发布上述建议。当前三库源码和服务保持原状；配套公开依赖仍待固定，原 `experimental` 状态未升级。

## 证据位置

- 只读取证工具：`/tmp/bgem3-nv-interface-read-20261106.py`；远端当前 HEAD、完整 patch SHA 和安装接口：`/tmp/bgem3-nv-interface-20261106.json`。
- 签名检查工具：`/tmp/bgem3-interface-check-20261106.py`；结果：`/tmp/bgem3-interface-audit-20261106/interface-check.json`。
- 官方源码逐字比较结果：`/tmp/bgem3-interface-audit-20261106/upstream-check.json`。
- 当前三库完整 diff 与 30/3/7 个变更文件均和前次本地审阅副本逐字一致，staged 为空；生产代码 AST 检查发现新增 Triton kernel 为 0，仅 FGV 原 `flash_varlen_fwd_kernel` 有修改。FGV 当前/基线签名 AST 相同。回执：`/tmp/bgem3-interface-audit-20261106/source-audit.json`。
- Plugin 与算子修改内容分别匹配此前交付 `1f68…`、`d5aa…`、`e2af…`；完整受控功能/硬件回归见[上一轮收敛](plugin-converge.md)及[算子库整改](operator-repositories.md)。
