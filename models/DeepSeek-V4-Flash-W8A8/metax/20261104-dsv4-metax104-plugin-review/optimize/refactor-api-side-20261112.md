# 2026-11-12：FGV PR 接口兼容修复（侧聊隔离候选）

用户在本侧聊要求修复 #1136–#1147 接口审查中发现的问题。本轮只修改新建的本地隔离候选，不接管主聊天实验、不运行 GPU/模型请求、不访问或修改容器安装源码、不停止服务、不提交或推送。已有 PR 分支、暂存区、源工作区及共享 state.yml/README 未写入；提供独立结果供后续串行合并。

状态：`local_api_candidate_cpu_validated_gpu_pending`。这是代码候选与 CPU 契约验证完成，**不是设备数值/真实 dispatch/graph 或性能验收通过**，GitHub PR 尚未更新。

## 输入与隔离

- 独立根目录：`/private/tmp/dsv4-api-fix-side-20261112`，完整候选在各 `prNNNN/`；保留现有 PR 工作目录，只读取其已归档源码。#1145 用本次读取的最新 head 文件覆盖独立快照，没有覆盖旧分支。
- 冻结输入：`plan.json`、`before-NNNN.json`、`pr1145-current-head.json`；原生对照源码在 `upstream-sources.json`。
- vLLM 主线对照：`2011b8f0fd783dadc2d71359487b2b5d67a82744`；其构建所固定的 FlashMLA：`847ef308bb7a6828c8117301f5a5a84a095a90e8`。FGV 审查主线：`8dc679c9e1f662b962f5a384a14092527fb89bda`。

| PR | 候选基于的 PR head | 本轮处理 |
|---|---|---|
| #1136 | `4a505b46301ef61e1cbc6a18dcc4e5ee9c6276c7` | gather 接受 vLLM 原关键字；保留旧 FGV 名称，重复/未知/缺参提前报错 |
| #1141 | `6c3284cbbe9ee25bb2b17f39742b53263d43ff87` | Prefill TopK 通用/MetaX 的关键字契约同步，保留旧调用与 None 返回 |
| #1142 | `32426add4b1c6d1bc45a4e3571aefcc001f91b7c` | 仅明确 allocating/in-place 是不同接口；不猜测整数参数顺序或伪造等价实现 |
| #1144 | `59db18ed0d520e301aa1ae7947ec22ccb49e9537` | MQA 整数宽度/输出布局修复；paged 参数兼容及不支持能力前置拒绝 |
| #1145 | `9dd07431b4811409608436dec6fdde3bbdb0d574` | Decode TopK 的 vLLM 关键字兼容，保留所有 selector/tree/fallback 数值定义 |
| #1146 | `f7777fbd717162b40759dcea1e38fac41f01e8cf` | Sparse MLA 标准参数前缀、out 与 strided-view 处理、状态/扩展边界、配套 factory |

#1137/#1138/#1139/#1140/#1143/#1147 没有本轮待修的公共签名变更，不为追求字面一致扩大改动。

## 修复内容及能力边界

1. Sparse MLA Prefill 的 `out` 可作为第八个位置参数或关键字传入。通用实现消费传入 buffer；strided 输出不走假定连续的 descriptor 路径。MetaX serial 路径通过单次临时连续输出后复制，保留调用方 out 身份与未选中 head 的保护区域。
2. Sparse MLA Decode 接受当前 NV 的 `enable_batch_invariant=False` 参数。True 尚不支持，明确在分配/状态写入/launch 前抛出 NotImplementedError；没有通过忽略参数冒充 batch invariant。
3. MetaX headpack、辅助输出与 split-workspace 参数移入私有实现，公共入口仅保留受限旧关键字兼容桥。未知选项提前拒绝；dense/非 MODEL1 委派不再静默忽略这些扩展。
4. FGV 显式导出配套 `get_mla_metadata()` 工厂。scheduler 是后端私有状态；NV 与 FGV 的同名类不强制转换或混用，替换框架调用时必须同时选配对应工厂。没有新增 vLLM 生产依赖或隐藏全局状态缓存。
5. `fp8_fp4_mqa_logits` 的第六个整数参数真实表示 `max_seqlen_k`，返回每行从 start 开始的压缩 `[M,max_seqlen_k]` 布局；不再将整数误当 clean 布尔值。旧第六位置 bool 和 `clean_logits=` 仍走原完整 `[M,N]` 契约，并拒绝含糊组合。
6. MQA 点积 kernel 不变；新增一个 64 位地址计算的重排/转换 kernel，可写 FP32/BF16。固定 256 元素内存复制 tile 作为本次正确性适配的显式非 autotune 例外，没有性能通过结论。当前保留完整 `[M,N]` 临时矩阵和额外 launch，这是明确的显存/性能限制，不是原生 compressed kernel 的融合优化替代。新调用使用实际输入设备 guard。
7. paged MQA 可按当前 NV 顺序接收输出 dtype/indices，旧第八位置 bool 不误绑定。当前只支持 FP32/uniform rows；varlen indices、paged BF16 output 明确在 launch 前拒绝。MetaX BF16-query/shared/gathered 接口仍是平台扩展，不宣称其全部格式已与 NV 一致。
8. 原 MQA 数值测试和 benchmark 的完整范围输入保持不变；静态探测原生 runner 参数版本，使用旧 clean_logits 或当前 width 形式。探测不放入 benchmark 热路径，不用新源码重绑定旧性能数字。

## 本地验证

- 新旧 API/control-plane CPU 测试共 **71 项通过**；新压缩输出的实际 host wrapper 和数据搬移索引 AST 通过 CPU launch double 验证，不能代替设备数值或 BF16 硬件舍入验证。
- 五个改源候选分别运行原生 `test_ci_*.py`：各 **66 项通过**。原生 exports、registry、selector、no-torch-compute-fallback 检查通过；AST、Black24.8/isort5.12/flake8 7.1 通过。
- 使用已安装的原生 trailing-whitespace/end-of-file/large-files hooks 逐一检查所有本轮 delta。large-files 使用 `--enforce-all`；仅只读 Git attributes，候选 worktree 与不存在的私有 index 明确隔离；未建立/写入原分支 index。没有 YAML 改动。
- 六份 patch 对精确冻结的原文件进行 `git apply --check` 均通过，没有实际 apply 到原仓库。
- 改动文件中的 **43 个既有 JIT 定义 AST 完全保持**，仅新增 MQA copy/reindex/cast kernel。没有复制点积、attention、TopK 或路由数值 kernel。
- 补了待执行的 MQA 新压缩布局/FP32/BF16/新输入 graph 用例，以及 Sparse MLA 三维 indices/位置 out/跨步 head view/保护区/新输入 graph 用例。**本轮 0 GPU 测试、0 模型请求、0 性能测量。**
- 编写过程中有一次 CPU fixture 缺少新增 runtime 依赖，以及一次版本探测的 import-order lint 失败，均已修正；环境 hook 的非 Git 目录错误也已定位并按只读 metadata 运行。摘要在 `development-check-history.json`；最终检查全通过，不是模型故障。

适用算子规范 A1–A4/B1–B3/C1–C7/D1–D2/E1–E6/F3–F4：CPU/source 部分通过，设备相关必须项仍为 `needs_revision_device_gates_pending`。未测跨平台能力和原有性能缺口均保留；不能把本轮 CPU 检查当成新的 NVIDIA/MetaX CI 或端到端通过。

## 产物与后续

- 总结果及逐文件 SHA：`/private/tmp/dsv4-api-fix-side-20261112/result.json`。
- 独立补丁：该根目录 `patches/PR{1136,1141,1142,1144,1145,1146}.patch`；#1142 为文档边界说明。
- 补丁包：`api-fix-candidate-patches.tar.gz`，SHA256 `a958d8b2ccc843b9f030d05fdfea81a566f852c589f0cdb0ec6725b9a44acc49`。
- 后续先在协调后的独立 GPU 窗口验证新布局数值、真实分发、changed-input capture/replay，以及新增搬移的完整开销，再按各 PR 原性能/工程门禁决定保留或修改。此前不安装、不更新运行服务，不将有限支持称为与全部当前 NV 能力等价。
