# env024：MLA BF16 路由收敛

已在离线候选删除 `_get_bf16_operator()`，必要适配映射合并回 `get_operator()`。相对 env023 仅修改 `dispatch/backends/flaggems/impl/mla_ops.py`，+38/−46，净减 8 行。没有部署、服务操作、模型请求或精度/性能评测；两个 gems-opt 不变。

本轮单文件完整 diff（本地文件 `docs/cases/20261018-hy4-preview-ppu03-migration/plugin-review-env024/from-env023-diff.md`） · 相对安装记录的完整 diff（本地文件 `docs/cases/20261018-hy4-preview-ppu03-migration/plugin-review-env024/from-env021-diff.md`） · 相对官方的完整累计 diff（本地文件 `docs/cases/20261018-hy4-preview-ppu03-migration/plugin-review-env024/full-diff.md`）

## 最终职责与必要范围

`get_operator()` 仅对三个 `bf16_indexer_*` 组合接口和 `flash_mla_sparse_fwd` 的 PPU 适配作条件映射。前者需要 Plugin 的 cache/prefill/decode 组合实现，后者需要已有 head-padding adapter。BF16 接口在其他平台仍不启用，其他平台 sparse MLA 使用原 provider。

普通 `top_k_per_row_prefill/decode`、`concat_and_cache_mla`、`concat_mla_q`、`flash_attn_varlen_func` 等直接进入原 `get_flaggems_vllm_operator()`，不再绕行 BF16 获取函数；普通名称查询不再导入 BF16 adapter 或检查 thead 平台。原 query-quant ABI 适配和 FP8 graph provider 优先选择也恢复原解析路径。

BF16 适配仍使用现有 `get_public_operator()` 检查 `VLLM_FL_USE_FLAGGEMS_VLLM` 和底层 FGV provider。decode 额外检查 FG 的 `bf16_paged_mqa_logits`；先检查 FGV 开关/provider，再查询 FG，可避免集成关闭时无用的 FG 导入。现有 operator allow/registry/strict 机制未修改，不捕获或吞掉执行错误。

模型层、BF16 算子计算、cache、TopK 完整行宽、pack/unpack 显式尺寸、opaque op/fake、量化编译边界与两个 Gems 源码全部不变。PPU HY4 runtime 仍在 `validate_hy4_runtime()` 明确选择 BF16；普通 FP8 名称解析恢复不表示已经验证 PPU 支持 FP8 计算。

## 检查与结论边界

| 范围 | 结果 |
|---|---|
| 路由与导入 | 22 项本地 static/mock 检查通过：普通算子在 PPU 与官方获取结果/查询一致，四个必要 adapter、FGV 开关、各依赖缺失、FG logits 缺失、operator 开关、非 PPU 原路径、非 CUDA PPU 排除。 |
| 原特殊路径 | 原 FP8 graph 优先/缺失时 fallback，以及 query-quant eager/compile 两条 ABI 路径通过 mock 检查；不代表设备运行。 |
| 源码范围 | 相对 env023 只有 mla_ops.py 一个文件变化；模型和数学实现逐文件相同。451 个 Python 文件语法通过，Plugin tests 与官方一致。 |
| 补丁 | env023、安装基线 env021、官方三套基线 strict apply/whitespace 检查通过，应用结果完整清单相同。 |
| Lint | 修改文件 Ruff 无诊断；没有格式化其他文件。 |
| 硬件与服务 | 未部署、未运行。env022 的服务验证仅覆盖安装 env021；env023 的 9 组 CPU/mock 计算对照保留其原范围，本轮未重复运行未变的计算代码。 |

最终累计仍为 11 个生产文件，相对官方 +1058/−20；包含 env023 的模型/后端职责整理。`pr_readiness=needs_revision`，新组合启动/graph/分页和完整精度仍待后续授权安排；198 题/87% 阈值与 heartbeat 暂停状态保持，不签发 gate，不提交/推送。

## 源码与证据

最新离线源码 `/tmp/hy4-mla-routing-20261020-01/candidate`；基线快照 `/tmp/hy4-indexer-boundary-20261020-01/candidate` 不覆盖。当前安装记录仍是 `/workspace/vllm-plugin-FL` 的 env021/r15；本轮仅在本地操作，没有重新连接目标环境，不把旧健康结果当作本轮新验证。

固定依赖沿用 FGV gems-opt `46387d7f96050204c1b932f35680a3ea03896fa6` 与 FG gems-opt `3ba1d1d99010de56d12088992f8b0da3444d90ca`，未对其源码或安装执行任何写操作。

本地原始产物 `/tmp/hy4-mla-routing-20261020-01` 保存 `check.py`、`validation.json`、三套 patch 和逐文件 SHA；本检查器位于 Plugin 仓库之外，不修改测试文件。完整 patch 已嵌入本目录 Markdown，后续可提取核验，不依赖临时目录长期存在。

相对 env023 delta SHA `969b9df404b5d5c495dcb34d856dbaa7917db9d18d07864eb8f159bebcb9e3dc`；相对 env021 SHA `c10919c228e20fd7499804bfd0690bee6916e1cc502bfe43db72a822d6067d8d`；相对官方完整 SHA `fc652cb227d43425d20296d1bb37712000bbd8b667f0b44bb65fd7a4e87ab4c7`。
