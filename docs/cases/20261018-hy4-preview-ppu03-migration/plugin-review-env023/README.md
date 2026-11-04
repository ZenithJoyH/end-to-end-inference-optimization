# env023：BF16 Indexer 模型与后端职责整理

已完成离线候选，**尚未部署**。当前 PPU-03 / hy4-preview 仍运行已验证的 env021/r15 service08，服务健康。两个 gems-opt HEAD、clean 状态与 tracked-file 摘要前后相同；不重启、不请求模型、不启动 GPQA/性能评测，也不恢复 heartbeat。

本轮相对当前安装版本的完整增量 diff（本地文件 `docs/cases/20261018-hy4-preview-ppu03-migration/plugin-review-env023/from-env021-diff.md`） · 相对官方 Plugin 的完整累计 diff（本地文件 `docs/cases/20261018-hy4-preview-ppu03-migration/plugin-review-env023/full-diff.md`）

## 四个文件的必要改动

| 文件 | 调整后职责与改动必要性 |
|---|---|
| `models/hy4/bf16_indexer.py` | 保留 HY4 Module/cache 创建、forward_context 与 metadata 类型解析、prefill chunk/token 切片、decode metadata 传递、opaque custom op/fake 注册及输出初始化；模型侧不再实现 QK/ReLU/归约、分页 gather、TopK 区间算法或直接导入 Gems。 |
| `dispatch/backends/flaggems/impl/bf16_indexer.py` | 承接原有分页 key gather、短行全范围输出、prefill 逐行打分/加权/TopK 与 offset；已有 decode 入口承接 packing、布局转换、结果 unpack/copy。算子库导入集中到该后端。仅迁移原算法，不新写 kernel。 |
| `dispatch/backends/flaggems/impl/mla_ops.py` | +5 行：在现有注册列表和映射中增加 `bf16_indexer_prefill`，模型通过 CachedOp 进入后端；以 FGV `top_k_per_row_prefill` 的可用性及现有集成开关检查依赖。未改共享 TopK ABI 或非 PPU 路由。 |
| `models/hy4/runtime.py` | +1 行：在原启动能力检查中增加 `bf16_indexer_prefill`，缺少新入口时启动前明确失败。其他配置和选择逻辑不变。 |

后端 prefill 只接受张量、区间和 TopK 数，不导入 HY4/vLLM metadata 类型；模型负责将具体 chunk 转成该接口需要的切片。新入口复用 CachedOp、MLA 注册和 DEFAULT FlagGems backend，没有增加 dispatch 框架或直接跨层导入后端函数。

```text
HYV4BF16SparseAttnIndexer
  → 模型 metadata / chunk 切片 / cache 生命周期
  → CachedOp(cache_write / prefill / decode)
  → FlagGems backend（计算、布局适配、库接入）
  → FGV concat_and_cache_mla / TopK / pack / unpack
    FG bf16_paged_mqa_logits（固定 FGV 缺少该接口）
```

## 修改范围与行为保持

本轮四文件 +193/−153，主要是移动现有代码，净增 40 行；模型文件从 281 行降到 169 行。未新增/删除生产文件；Plugin tests 仍与官方完全一致。相对官方累计仍为 11 个生产文件 +1066/−20。

| 文件 | 本轮 diff |
|---|---|
| `vllm_fl/dispatch/backends/flaggems/impl/bf16_indexer.py` | +164/−18 |
| `vllm_fl/dispatch/backends/flaggems/impl/mla_ops.py` | +5/−0 |
| `vllm_fl/models/hy4/bf16_indexer.py` | +23/−135 |
| `vllm_fl/models/hy4/runtime.py` | +1/−0 |

prefill 继续使用原 BF16 matmul、BF16 ReLU/乘法/归约后转 FP32，不在职责整理时改变精度口径或批量算法；decode 继续调用 FG 的 paged logits 和 FGV 的 TopK。`count=topk_tokens` 完整行宽、padding 的 `max_length=1` 与 `total_tokens=num_decode_tokens` 全部保留，opaque 图边界及 buffer 原地更新语义不变。R2 数值观察未修订，其正式精度影响仍未知。

新 FGV 导入保持函数内 lazy loading；共享 `top_k_per_row_prefill/decode` 保持 8 参数 ABI。现有 `VLLM_FL_USE_FLAGGEMS_VLLM` 与 operator enable/registry 机制继续控制新入口的可用性，没有增加环境变量。非 PPU 路由保持原实现；已有 BF16 单 token 支持范围不扩展。

两个固定仓库没有写入：FGV gems-opt `46387d7f96050204c1b932f35680a3ea03896fa6`，FG gems-opt `3ba1d1d99010de56d12088992f8b0da3444d90ca`。Plugin 安装目录也没有写入。

## 检查结果与边界

| 检查 | 结果与证明范围 |
|---|---|
| Python 语法 | 451 个 Python 文件 compile 通过。 |
| 移动代码核验 | 四个 prefill helper 经符号名和 provider import 归一化后 AST 完全相同；cache writer、paged logits adapter、模型类及 fake 实现 AST 不变。 |
| CPU 对照 | 9 组通过：多请求/多 chunk/跨页 prefill、短上下文全选、TopK=0、无 padding decode、零行在首/中/尾、mixed 和空输入。使用真实 CPU PyTorch 计算，GPU provider 以进程内 mock 替代；最终 indices/cache 逐元素一致、底层 provider 输入值/shape/stride/调用顺序一致、返回 buffer 别名及未触及行保持。只证明重构契约，不证明 GPU kernel 或 graph。 |
| 路由隔离 | 新 PPU prefill 映射、依赖缺失、operator 关闭、非 PPU 无 FG 依赖及共享 TopK 原路由的静态/mock 检查通过。 |
| 补丁与范围 | 从当前 env021 和官方基线均 strict apply、whitespace 校验通过，应用后完整源码逐文件相同；仅四文件变化，无测试文件改动。 |
| Ruff | 对四文件与基线对照无新增诊断；模型文件保留原有 I001 导入排序告警，其他三文件无诊断。未为排序扩大改动。 |
| 现场保护 | 前后当前 Plugin/模型/tokenizer/Gems/服务实例一致，health200；CPU 检查未初始化 GPU。 |
| 硬件与整模型 | 本候选未部署；启动、capture/replay、分页与正式精度均未运行。env022 仅证明已部署 env021。其他平台硬件未实测。 |

首次 CPU 对照脚本曾比较 `torch.empty` 输出写入前的未定义内存，修正为仅比较该输出的 shape/stride/dtype，并保留最终完整输出比对；候选代码未因该检查器问题改变。

`pr_readiness=needs_revision`：职责整理完成，硬件/整模型与正式精度仍是缺口。198 题、87% 阈值及原参数保持，不签发新 gate、不提交或推送。性能未测量，无收益主张。

## 候选、证据与撤销

候选源码 `/tmp/hy4-indexer-boundary-20261020-01/candidate`；安装基线快照仍在 `/tmp/hy4-padding-fix-20261020-01/candidate`。当前实际安装 `/workspace/vllm-plugin-FL` 保持 env021，尚无需执行服务或安装回退。

外部本地产物根 `/tmp/hy4-indexer-boundary-20261020-01`：`refactor.py`、`static_check.py`、`cpu_check.py`、`run_cpu_check.py`、`final_readonly.py`、`static-check.json`、`cpu-check.json`、`lint-comparison.json`、前后安装身份 JSON、`from-env021.patch` 与 `full.patch`。原始结果及脚本未写入 Plugin tests 或当前项目的单测目录。

增量 patch SHA `7d4be3f60a8e8319f99af1cbc1955b4446f9024e2b29ff41fb8352f481e4e614`；累计 patch SHA `dceef28c9e54cc4f26f9f5a3b193aae0f1f90b771c927793a98328681b4e78d3`。两份完整 patch 已分别嵌入本目录 Markdown，可独立提取核验并应用，不依赖临时目录长期存在。精度/性能与服务生命周期仍等待后续明确工作安排。
