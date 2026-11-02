# PR924 统一接口与测试整理（侧对话，2026-10-15）

本侧对话用户要求调整 PR924：复用现有测试/benchmark shape 路径、共享 alignment，实现以 `fused_experts_impl` 为入口，移除新增底层 backend 导出。本次只修改隔离的本地 PR 副本及该 PR 分支；不接续主线程的 split-K 实验、不连接远端、不修改模型容器、运行源码、启动脚本、评测或主实验账本。

## 项目真相与验证范围

| 字段 | 内容 |
|---|---|
| API | 现有 `flaggems_vllm.fused_experts_impl`；不是新算子开发，不采用 workflow 中无关 conv1d 示例 |
| 输入 revision | PR924 `fb70fd23462d411e3131c011ac8434073237e927`，公开 base `6123527f05497e08bc677cb40e8364502c4f5a32` |
| 隔离副本 | `/private/tmp/flaggems-vllm-pr924-api-cleanup-20261015`；以 base 建立新副本，叠加经 GitHub 读取的精确 PR 文件；未复用旧 dirty 副本执行修改 |
| Editable | T-Head fused_moe 模块、恢复原样的 backend init、现有 `tests/test_fused_moe.py` 和 `benchmark/test_fused_moe_int8.py` |
| Read-only | 共享 fused_moe/alignment、其他平台、Plugin、模型和运行服务；旧副本的 dirty 状态保留 |
| Build/validation | Python AST、受影响文件 pre-commit、89 项实际 host 定义的隔离 mock/AST 检查；本机无 Torch/Triton/GPU，未执行 package/device pytest |
| Benchmark | 既有 FusedMoEINT8Benchmark，全 MoE 接口与同一 shared shape list；本轮不测量新性能，不沿用历史 micro 数字作为新 head 收益 |
| Autotune | 不新增 kernel 或调参；保留既有整数累加、选择条件、配置与调优边界，免新增 autotune 配置 |
| Profiler/timeout | 本轮不采集 profiler、不开展设备实验；无新的设备时限或模型请求 |

## 语义与路径契约

| 契约 | 内容 |
|---|---|
| 输入/输出 | 现有 per-channel W8A8 full API：BF16 hidden/输出，I8 专家权重，F32 token/channel scales，F32/BF16 router；不改变 inplace、dtype、shape 或数值算法 |
| 累加/适用域 | 保留 fb70fd2 的 810E 有界 INT32 GEMM1 与既有 generic INT32_DOWN GEMM2 选择范围；不扩展能力和 shape 白名单 |
| 其他语义 | NaN/Inf、signed zero、异常、layout、fallback 和 forward-only 边界沿用原 full API；本轮不增加训练承诺 |
| Torch 使用 | 新增 Torch 参考运算只在测试内；生产移除 adapter、scratch kernel，未新增 Torch compute/copy fallback |

| 路径 | 处理 |
|---|---|
| fast/special | 通过既有 `fused_experts_impl -> dispatch -> invoke`，保留原选择器与 kernel；内部 launcher 恢复其原模块名称，不作为新 backend 导出 |
| alignment | 继续调用共享 `moe_align_block_size_no_tle`；删除未被 full API 使用的 vendor preallocated wrapper 及其 zero kernel，未修改共享 alignment |
| general/unsupported | 既有 vendor 路径及显式报错保持原样；共享 generic 源码逐字节保持 base |
| 测试 | 硬件绑定数值测试改为统一 full-API 参数化测试；仅实现选择/能力/配置/转发/overflow/fallback 保留 vendor policy 单测 |

## 已发布改动

- PR：[FlagGems-vllm #924](https://github.com/flagos-ai/FlagGems-vllm/pull/924)。
- 新增提交：[e23198e68796373354ac0e7d7324145c8db468aa](https://github.com/ZenithJoyH/FlagGems-vllm/commit/e23198e68796373354ac0e7d7324145c8db468aa)，父提交 fb70fd2，fast-forward + expected-SHA lease 更新既有分支；没有重写历史。
- PR 累计仅三个修改文件：benchmark、T-Head fused_moe、tests。`_thead/ops/__init__.py` 已恢复 base，新增两个底层导出消失；无新 test/benchmark 文件。
- 既有 benchmark 添加 M32/64/65/1024/8192、E128/H6144/I384/top4 的共享 shape，统一通过 `flaggems_vllm.fused_experts_impl`；移除专门的 T-Head benchmark 函数。
- 数值用例在同一 tests 文件中按 shape、scale rank、router dtype 运行，不检查 vendor 或硬件名称；复用 literal_quant，CPU 稀疏整数参考支持大 shape，capture + 两次 replay 与 eager 要求逐元素相等。独立 CPU 全流程对拍沿用旧 full-pipeline 3%/1e-7 容差，不把它表述为旧低层 exact-integer kernel 测试的等价替代。

## 证据与限制

- `executed_passed/static+mock`：89 项隔离检查，命令 `/private/tmp/flaggems-vllm-pr-tools-20261014/bin/python -m pytest -q /private/tmp/pr924-cleanup-host-checks-20261015.py`。包括实际 full-API 主机路由、GEMM1/GEMM2 选择与 fallback、共享源码及导出恢复、benchmark 转发。
- `executed_passed/static`：受影响三个文件全部适用 pre-commit hooks；`git diff --check`；AST parse。
- `executed_passed/static`：完整 API、kernel、GEMM1/GEMM2 selector 与 fb70fd2 AST 相同；仅内部 launcher 名称恢复。
- `not_run/hardware`：新数值测试的设备收集/执行、现有 benchmark、其他平台、模型 GPQA 和 E2E；本地缺 Torch/Triton/GPU，未占用主线程设备或启动远端验证。旧 153/128 测试计数及 micro 时间不属于新提交。
- GitHub 发布后重新读取 head、PR 描述和四个涉及文件，确认 head=e23198e、三个累计改动文件、内容与本地最终文件精确相同。PR 描述已同步，并清楚标注设备验证待运行。
- 本地累计补丁 `/private/tmp/pr924-api-cleanup-20261015.patch`，SHA256 `74374f4d62ca1a0df912914488e100973d7072a7fc2215ddbf6b75edb66b9357`。原始临时验证脚本不提交公开仓库。

`pr_readiness=needs_revision`：代码整理及主机检查完成，仍需新公共数值测试和 benchmark 的实际设备验证；不宣布设备验收或性能完成。既有运行容器仍是原固定版本，本次没有自动部署新 PR head。应用新 head 前应核对调用方是否仍直接依赖两个旧底层 package-level 替换入口。

回退使用对 e23198e 的单独 revert 提交恢复 fb70fd2 行为，不 force-push；本次没有执行回退。

## 必要性复核后的最终版本

用户指出 `requires_cuda` 仍属额外测试结构改动。复核确认：它只是为了把新增 metadata policy 测试留在无 GPU 环境执行，才将原全文件 skip 拆到原有函数上，并非算子优化的必要依赖。前一节 e23198e 的代码整理状态不是最终最小 diff。

已追加提交 [a3c39928deca82e7a39cb5417f3d4288de5983e2](https://github.com/ZenithJoyH/FlagGems-vllm/commit/a3c39928deca82e7a39cb5417f3d4288de5983e2)，fast-forward/expected-SHA 更新 PR：

- 恢复原全文件 `pytestmark`/CUDA availability skip，移除 `requires_cuda` 和所有原函数新增装饰器。
- 删除 `_TensorMetadata`、两个 policy fixture 及新增 vendor policy 单测；主机边界检查保留在 PR 之外的临时验证脚本，不能计为公开设备 pytest 通过。
- benchmark 原 wrapper 本来就经 `ops_experts_impl` alias 指向 backend-selected `fused_experts_impl`，恢复 wrapper，去掉不必要的同义接口改名。
- 最终累计三个文件：生产 T-Head fused_moe +331/-1（与前一提交内容完全相同）；tests +101/-0（统一 full-API 数值/graph 测试与必要包 import）；benchmark +6/-0（五项共享 shape 和注释）。累计 +438/-1。
- 原有七个 helper/test 定义与 base AST 完全相同，原 benchmark wrapper 与 base AST 相同；共享 alignment/generic、backend init 均保持 base。
- 最终全部适用 pre-commit hooks、diff check 及 97 项隔离 host/mock/AST 检查通过。97 是临时隔离检查数，不是新设备 pytest 计数。新数值/graph 用例和 benchmark 仍未在设备执行，`pr_readiness=needs_revision` 保留。
- 新累计补丁 `/private/tmp/pr924-api-cleanup-minimal-20261015.patch`，SHA256 `142c33ea97752afd2bd60b1a167469523b5c85bd00ef23574e8b65ebed5d5c61`。

PR 描述同步为最终范围；发布后重新读取 head、描述和两个新改文件并逐字节核对。未连接或修改运行容器、模型服务、主线程源码及 split-K 实验。

## 整体 review 计划（a3c3992 为输入，实施前记录）

用户进一步要求按整个库的逻辑 review 并继续收敛。范围仍限 PR；不开展主线程的模型/性能工作。

| 项目真相 | 冻结范围 |
|---|---|
| Editable | 同三个公开文件；必要性审查覆盖 package backend replacement/alias、现有 config、dispatch、kernel、test/benchmark/CI selection |
| Read-only | 其他平台、共享 generic/alignment、backend exports、原测试及 wrapper、远端容器与模型 |
| Build/validation | pre-commit、AST、基于实际 host 定义的 mock 调用；设备 suite/benchmark 没有本地运行环境，不能宣称通过 |
| Benchmark/autotune | 不新增调参；删除不可能从当前 full API 命中的旧 K256 精确匹配表。实际 config 与 GEMM2 复用保持；benchmark 仅保留当前生效策略代表 shape |
| Profiler/timeout | 无设备 profiler 或额外性能试验；不采集模型数据 |

| 语义契约 | 本轮要求 |
|---|---|
| API/输入/输出 | 同前述 full API；无新公开符号、环境变量、dtype/layout/alias/异常承诺 |
| 累加 | 原 INT32 kernel 数值主体不改；G1 保留 K6144 受限支持范围，G2 复用 upstream 内部 schedule |
| 配置 | 保持当前 `get_moe_configs -> get_default_config` 优先级、原默认 tiles；不把历史底层 micro 配置当成当前完整接口配置 |
| 参考/Torch | 原生产路径不增加 Torch compute；测试只复用原 literal_quant 与独立 CPU 稀疏参考，不放宽容差 |

| review 发现 / 路径 | 必要动作及验证 |
|---|---|
| K256 死分支 | `_EXPECTED_CONFIGS` 是 GM1/stages3，现有 `get_moe_configs` 恒为 None，默认 GM8/stages4；完整 API 永远无法匹配。删表及匹配器，验证实际 full API 的 G1/G2 路由与配置不变 |
| 普通与不支持路径 | 保留 dtype/shape/layout/scales/capability/融合/路由/overflow guard；检查源码、fallback、shared bytes、未增加 exports 或 Torch fallback |
| 测试与框架不一致 | 新用例忽略 QUICK_MODE，导致 quick 运行所有大 shape。按现有 `conftest.QUICK_MODE` 缩小 quick 参数，full 不缩水；现有函数及 skip 保持原样 |
| benchmark 冗余 shape | M32/65 是旧 K256 调参边界探针；保留实际 full-API 代表点 M64/1024/8192，沿用原 wrapper/输入生成/统计 |

### 整体 review 结果

已更新 PR，追加提交 [0672be024bb607222c73bf70406a70ca5d23ba71](https://github.com/ZenithJoyH/FlagGems-vllm/commit/0672be024bb607222c73bf70406a70ca5d23ba71)，父 a3c3992；expected-SHA + fast-forward，没有重写历史。

1. 删除 `_EXPECTED_CONFIGS`、`_matches_gemm1_tile` 和修改 K256 的分支：这套配置只有直接手工调用底层接口才可能匹配，从当前公开 full API 的固定 GM8/stages4 配置入口无法到达。不是将历史 K256 吞吐带入当前 API。配置仍完全使用原有 `get_default_config`，不新增调优表或开关。
2. 能力函数改名为 `_supports_int8_moe`，反映它共同保护 GEMM1/GEMM2，不再误称仅供 tile 调优。按 device index 缓存的实际能力检查保持原样。
3. 既有 INT32 kernel 算术、完整 API orchestration、GEMM2 forwarding 与 selector、所有未选中路径保持原样；保留 shape/dtype/layout/scales/capability/模式及 overflow guard。未新增 generic、alignment、exports、Plugin 或其他平台改动。
4. 新数值用例遵守现有 QUICK_MODE：quick 为 4 项组合，覆盖空输入、普通 fallback、M64 和 M1024 两种实际选中情况；full 仍为 36 项并保留 M8192、2D/3D scale、F32/BF16 routing。原函数/marker/容差没有修改。
5. benchmark 新增 shape 只保留 M64/1024/8192，完整沿用原框架。CI 选择器实际输出 tests/test_fused_experts_impl.py、tests/test_fused_moe.py 以及 benchmark/test_fused_moe.py、benchmark/test_fused_moe_int8.py；不修改 CI 映射或测试基础设施。

最终累计 3 文件、+404/-1：T-Head +286/-1，tests +114/-0，benchmark +4/-0。所有新增生产 Torch 调用审计只发现一次 `torch.cuda.get_device_properties` 元数据调用，无新增 compute/copy fallback；唯一新增 import 是选中 GEMM2 后延迟导入既有 generic launcher，避免导入时替换或循环依赖。

验证：全部适用 pre-commit hooks、Python 语法编译、diff check 通过；`/private/tmp/pr924-overall-review-checks-20261015.py` 91 项隔离 host/mock/AST 检查通过。测试包括实际 launcher/dispatch、full-API 小 M 路由、GEMM2 实际 generic launcher metadata、边界/fallback/overflow/自定义配置转发、原测试/marker/framework 保持，以及 quick/full 参数数目。旧的 97 项检查属于上一个版本，不当作本轮计数。

已逐字节核对 GitHub 最终三个文件、head 和 PR 描述。标题/描述改为当前实际生效的整数累加修正与 GEMM2 复用，不再宣称 K256 或历史 micro 时间属于本 head。

本地补丁 `/private/tmp/pr924-overall-review-20261015.patch`，SHA256 `3331f2f2331568f8530abbdfe440010b42fcfe50b5f59aa22ffca3ee867688ff`。本轮没有连接远端或改变模型运行环境。

剩余限制：设备上的新 suite/graph/benchmark、强数值极值/抵消回归、其他平台和模型 GPQA/E2E 均 not_run。稀疏参考用例验证完整 API 和 graph，不等同于原低层极值/抵消整数累加测试；静态等价和历史 kernel 证据不能冒充本 head 新设备验收。`pr_readiness=needs_revision`，仍需硬件验证。

### 移除额外 QUICK_MODE 使用

用户继续质疑 QUICK_MODE。它原本是库已有开关，但新增导入和参数裁剪分支仍是本 PR 引入的测试策略，不能以“复用已有机制”为理由认定必要。本轮已移除该导入和所有条件分支，不修改库的开关定义、conftest 或既有策略。

新增提交 [ffe053ab9d81defd8cf8946278e315c3699d02a7](https://github.com/ZenithJoyH/FlagGems-vllm/commit/ffe053ab9d81defd8cf8946278e315c3699d02a7)，父 0672be0，expected-SHA/fast-forward。只调整 tests/test_fused_moe.py，恢复到 a3c3992 的精确内容（SHA256 `614871b94bbe78c2dbffad553674919647f1e74c3de7638212cc84f475d08986`）；保留上轮对生产代码死分支和 benchmark 冗余 shape 的收敛。

最终 tests 文件不包含 QUICK_MODE 或 requires_cuda，新增参数固定 36 组合，继承原全文件 skip。91 项隔离检查和全部适用格式检查通过；GitHub 重新读取核对 test 内容。PR 描述同步去掉 quick 裁剪的表述。设备未验证的限制保持，运行容器不变。累计三个文件 +391/-1；不再为本轮算子修复新增测试策略。

### 改为复用已有 W8A8 测试（实施前范围）

用户明确要求不改 `tests/test_fused_moe.py`，复用 `tests/test_fused_experts_impl.py`。已检查后者的 `test_fused_moe_int8`：它通过已有 alias 调用完整接口，启用 W8A8/per_channel，已有输入生成、量化、路由、反量化参考及容差，足以作为复用入口。

本轮只恢复前一文件至 base，并在既有 INT8 测试的 config decorator 中补 M64/1024/8192、E128/H6144/I384/top4 三项。目标权重及原参考会使用较多显存和逐 token 计算，因此沿用该文件**已经存在**的 RUN_LARGE_MOE_TESTS 控制，保持默认六个量化小 shape；不创建开关、不改现有开关/QUICK_MODE/skip，也不把新增 shape 加入 FP8/W8A16 等共享配置。算子和 benchmark 内容不变；不增加测试函数、参考或 graph wrapper。

### 复用结果

已追加并发布 [975c4cacb558cc7a75b3e13123d8ba5a04dbdca0](https://github.com/ZenithJoyH/FlagGems-vllm/commit/975c4cacb558cc7a75b3e13123d8ba5a04dbdca0)，父 ffe053a；expected-SHA/fast-forward。发布后读取确认累计只改三个文件：既有 T-Head fused_moe、既有 INT8 benchmark、`tests/test_fused_experts_impl.py`。

- `tests/test_fused_moe.py` 恢复 base 的精确 bytes，SHA256 `fb27592da2f93d8ceaa84ed6518abcf73400d86bcb1843404baf595367561259`，不再出现在 PR diff。
- `tests/test_fused_experts_impl.py` 仅 INT8 用例的 config decorator 改变，+13/-1；AST 核对确认恢复该装饰器后整文件与 base 相同。函数主体、参数/权重量化、routing、完整 API alias、dequant reference、容差、所有全局定义/控制及其他用例保持原样。SHA256 `3b958cd8d910f7cebabed2c577303c54642b2511323e4294b5bf00990e510191`。
- 现有大 shape 选项关闭时仍为 6 项，开启后为 12 项（9 项原用例 +3目标）；不扩展 FP8、W8A16、INT4 的共享参数矩阵。没有新增 QUICK_MODE 使用、requires_cuda、测试函数、参考实现或 graph wrapper。
- 算子 SHA807d12...a0f7e、benchmark SHA5e48c5...3f346 与本轮前完全相同；累计 +303/-2。
- 95 项隔离 host/mock/AST 检查、全部适用 pre-commit hooks、语法编译、diff check 通过。CI 实际选择现有 test_fused_experts_impl.py，以及两个 MoE benchmarks；无需改 CI 映射。
- 本地补丁 `/private/tmp/pr924-reuse-experts-20261015.patch`，SHA256 `b941e474e4aa1295fd2e4d9fabe21a40e6ac664ce238ca5a9d767a61b4319c92`。PR 描述同步删除上一套 36 参数/稀疏 CPU oracle/graph 测试的陈述，改为真实复用入口及现有 large-case 命令。

新设备数值/graph/benchmark、高幅值抵消、模型 GPQA/E2E 仍未执行；不以静态复用检查替代设备通过。`pr_readiness=needs_revision` 保留。未连接远端，不改变运行模型容器、主线程源码或流程。

用户要求明确 benchmark shape 来源，已追加 [e1fc3e3be1e0746054b642bfbec9c98d29b2b5d5](https://github.com/ZenithJoyH/FlagGems-vllm/commit/e1fc3e3be1e0746054b642bfbec9c98d29b2b5d5)，仅将注释改为 `# MiniMax-M3.1 per-channel W8A8 shapes (TP=8 shard).`。形状、实现及测试不变；验证唯一一行替换、Black check、diff check，发布后重新读取确认。未重复设备或主机测试；PR 描述明确此前验证属于代码不变的父提交。

用户随后要求注释仅保留 MiniMax、不体现 M3.1；已通过 [79d2369b591859928e11635430a9faa7e73c012c](https://github.com/ZenithJoyH/FlagGems-vllm/commit/79d2369b591859928e11635430a9faa7e73c012c) 将同一行改为 `# MiniMax per-channel W8A8 shapes (TP=8 shard).`，仅模型名称文字变更，GitHub 内容已核对。
