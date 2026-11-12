# BGE-M3 Plugin 完整 diff 审查

> 本文保留修复前的只读审查快照。R1/R2/R3 已按后续授权整改并完成本地验证，当前结果见 [整改与验证记录](plugin-review-fix.md)；下文的35文件统计与 `needs_revision` 均属于修复前状态。跨仓库公开交付/版本固定仍是 PR 前置项。

日期：2026-11-05，Asia/Shanghai。范围：mx-59 / BGE-M3 容器内实际 editable 安装的 `/workspace/bge-m3/tune-src/vllm-plugin-FL`；分支 `bge-m3-review`，比较基线 `5463eae824b1fbaa3d331564ab2fb4c51f1b6e09`。本轮只读审查，没有修改目标源码、索引、分支、安装或服务。

完整补丁为 35 files / +2311 / -3，SHA256 `453043aea590d95f73e4bc2bbc22f9a75b2b208568b3adec2fe3ce8ee25bd897`。结论：`pr_readiness=needs_revision`。主要问题是新增 Linear 调优实现越过 Plugin/算子库边界，以及默认路径中无收益的包装；并非所有 35 个文件都应删除或缩减。

## 需要整改的发现

### R1 / P1：Plugin 解包 FG 私有 kernel 并重建 tuner、launcher，且注册为 vendor 实现

位置均相对于容器内 Plugin 根目录：

- `vllm_fl/dispatch/backends/vendor/metax/impl/bge_m3.py:55–73`：从 `flag_gems.linear.__module__` 导入实现模块，访问 `linear_kernel`、沿 `.fn` 解包到 `triton.runtime.JITFunction`，创建独立的 `libtuner/libentry`，使用私有 `_disable_aabs_for_small_dims`。
- 同文件 `110–135`：Plugin 分配结果、构造 grid/stride 参数并直接 launch kernel。
- 同文件 `146–152`：将这条 FG 计算路径注册为 `BackendImplKind.VENDOR`、`vendor.metax.bge_m3`。
- `vllm_fl/configs/bge_m3_metax.py:5–22`：配套的 tile/warp/stage 配置。

已核对实际安装的 FG `runtime/backend/_metax/ops/linear.py`：这些是算子实现与内部 launcher 的细节，Plugin 此处实际重做了公开 `linear` wrapper 的主要执行组织，而不是只传递模型配置。未新增 `@triton.jit` 本身不等于符合仓库职责边界。内部装饰器链或私有 guard 变化会使 Plugin 失效；FG 实现也不应以厂商原生算子的身份注册。

依据：Plugin A1、A4、B1、B2；算子规范第 0 节及 A1–A3；Plugin 变更评审第 2 节。ATen Linear 实现/调优归 FlagGems，不因模型专用 shape 而变成框架逻辑；若只缺公开配置能力，应在 FG 暴露受控公开入口，再由 Plugin 经既有 dispatch 调用。

建议：将这些调优候选和 launcher 移回 FG 的 MetaX 实现/配置；Plugin 留下能力/shape guard、公开 API 调用及正确 fallback，并固定公开依赖版本。若当前仅保留 FP16 dense profile，FP32 专属调优可拆成独立后续改动；不能直接删除整个 FP32 joint 功能来回避问题。用户文档 `docs/models/bge_m3.md:112–130` 中宣称“Linear 调优应位于 Plugin、无需算子侧变更”的表述也应随实现一起调整。

### R2 / P2：默认 FP16 路径无条件改写 Linear，仅增加纯转发

位置：`vllm_fl/models/bge_m3/model.py:45–49`，`vllm_fl/models/bge_m3/linear.py:22–33`，`vllm_fl/dispatch/backends/flaggems/impl/bge_m3.py:22–24`。

模型初始化始终调用 `bind_linear_policy`，替换所有未量化层的 `quant_method.apply` 及普通 `torch.nn.Linear.forward`。当前 FP16 YAML 选择 `bge_m3_linear: flagos`，解析到的默认 provider 仅调用 `native_apply`。因此 FP16 dense 服务也承担每次 Linear 前向的额外 Python 转发与实例方法替换，却没有使用任何新算子或参数；这部分对当前默认路径是可删除的改动。这里没有据此推断端到端减速幅度，也没有把它当作精度错误。

依据：Plugin F5 的主题聚焦/清理要求，以及变更评审对保持原默认路径、使用最窄扩展点的要求。

建议：仅在选中具有实际适配作用的 provider、且目标 dtype/能力满足时绑定；默认 provider 直接保留层原方法。补充“默认策略不改变 apply/forward 身份”的契约断言；现有测试证明返回值/梯度等兼容，但没有要求默认路径零包装。

### R3 / P2：Attention 单测替换了真实 provider，缺少完整生产链路的验证

位置：`tests/unit_tests/models/bge_m3/test_attention.py:40`；关联 `tests/unit_tests/dispatch/test_bge_m3_policy.py` 与 `tests/unit_tests/models/bge_m3/test_linear.py:126–127`。

Attention 测试把模型模块的 `CachedOp` 替换为 PyTorch reference，因此可以验证 packed metadata/参数转发，却不经过真实 OpManager/FGV 实现。策略测试主要检查注册与 resolve，Linear 的硬件数值测试则直接调用 vendor 函数。这些单测有价值，但不能组合解释为“从真实模型入口到实际后端命中及独立数值比较已通过”。

依据：Plugin F1、F2、F4。并非指测试 expected 直接复用了被测函数；其主要缺口是真实生产链路和当前硬件证据。

建议：保留现有单测，再补一个实际 BGE 模型入口经 dispatch 到真实 FGV 的集成验证，明确断言 impl_id、packed 多文档隔离、独立参考数值、不支持能力和执行中错误不重试。Linear 完成 R1 的公开 API 整理后，也按实际模型绑定入口验证。当前审查不启动模型服务或执行 GPU 测试，故此项没有新硬件通过结论。

## 已检查且建议保留的改动

| 内容 | 判断与理由 |
|---|---|
| `worker/worker.py` 两行与对应新契约测试 | 必要共享修复：透传 `AsyncModelRunnerOutput`，避免异步 pooling 输出落入 `IntermediateTensors` 断言。类型标注同步合理；测试覆盖 async/sync/None/pipeline 四种返回。不能因它位于通用 Worker 就判为无关。 |
| BGE 架构注册、IO entry point、主入口中的懒注册 | 有明确调用用途；自定义架构名，不覆盖原生 `BgeM3EmbeddingModel`，注册有幂等 guard。 |
| `models/bge_m3/model.py` 的 packed PAD 位置映射 | 属于输入/token metadata；按 A3 可在框架侧实现。不是因为含 Torch 张量运算就必须迁至算子库。测试参考来自 HF，未发现 reference 与生产共用同错 helper。 |
| joint pooler / IO processor | 复用 vLLM 现有 heads、按请求选择输出和打包 tensor transport，属于模型语义/框架编排；ContextVar 不依赖全局 FIFO。已核对当前 vLLM 0.24 的 pre_process/merge_pooling_params 为同一次同步预处理调用，暂未发现跨线程错配。 |
| `pooling` 可选 extra / orjson | 使用 vLLM 已有 JSON response 选择，不修改 vLLM；可选依赖不强制安装到全部用户环境。 |
| 两组 examples、配置与 README 模型入口 | 对应 FP16 dense 与 FP32 joint 两种明确用法；不是无目的增加多套入口。 |
| 已移除的三份历史性能 JSON | 在本次原始父节点基线下无净改动；无需为使 diff 好看而恢复。当前源码中没有加入单次性能结果大表。 |
| 版权头与局部格式 | 主要为新增文件内容，未发现这次完整 diff 对大量无关旧文件做版权/格式清洗；不可将镜像头增量中的版权变更数量直接当作此补丁的无关改动。 |

## 工程规范复核状态

| 条款/范围 | 状态 | 证据或边界 |
|---|---|---|
| A1/A4，算子规范 0/A1–A3 | needs_revision | R1，FG 私有实现/调优及 launcher 留在 Plugin。 |
| A2/A3，模型、metadata 与分发落点 | static_checked | 主要目录合理；PAD 位置和 tensor transport 不是新增数值 kernel。 |
| B1/B2 | needs_revision | 有 dispatch 接入，但 FG 计算注册为 VENDOR、绕过公开 FG wrapper。 |
| B3/B4/C1 | partial_static | 存在 dtype/shape/梯度/布局 guard，执行异常未发现跨后端重试；缺少新增实际运行证据，不声称完整契约通过。 |
| C2/C3、请求与模型实例隔离 | partial_static | 懒注册幂等，参数对象保留、请求 ContextVar/transport header；无新全路径运行验证。 |
| D3/D4/D5 | partial_static | 文档有公开固定 FG/FGV SHA、blacklist 增量语义与退出说明；R1 的私有 API 接入仍须纠正。未把公开 fork 的固定 SHA 本身判为违规。 |
| F1/F2/F4 | incomplete / needs_revision | R3；18 项 CPU shell/HTTP 通过；其余 CPU 收集受现有依赖导入阻塞；当前 GPU、完整模型与 formatter/linter/pre-commit 未通过验证。 |
| F3、graph | not_verified / explicit_scope | 当前 examples 明确 eager，FP32 attention builder 标记 NEVER，不把此审查当作 graph 支持证明；本轮没有 graph 改动或验证。 |
| F5 | needs_revision | R2，可去除默认策略无收益的 Linear 包装；其余 shared Worker 与 IO 改动具备主题关联。 |
| F7/G1/G2 | partial_static | 源码注释/异常英文、示例 logger、支持入口已更新；没有执行完整 lint。文档可维护信息大体合理，但须修正 R1 的职责说明。 |
| H 量化条款 | not_applicable | 本次无新增量化格式或行为。 |

## 实际执行与限制

- 精确审查了完整 patch、35 个改动文件及需要的原始基线/相邻 dispatch/Worker/测试基础设施；只读取了目标容器当前安装的相关 vLLM/FG/FGV 接口，没有访问其他模型适配工作区。
- 25 个改动 Python 文件 `ast.parse` 通过；新增 `examples/bge_m3_dense/serve.sh` 的 `sh -n` 通过；完整 patch 的 `git diff --check` 通过。
- 在 BGE-M3 容器以 `CUDA_VISIBLE_DEVICES=-1 MACA_VISIBLE_DEVICES=-1 USE_FLAGGEMS=0 VLLM_PLUGINS=fl PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1` 执行 `pytest -q -p no:cacheprovider -m 'not gpu'`，范围为 BGE 模型测试、BGE dispatch policy 及 Worker 新返回契约测试。收集到 22 项并发生 5 个收集错误，退出码 2；原因是**原有** `vllm_fl.utils -> flag_gems -> FlagTree` 导入链要求 active driver，屏蔽 GPU 后报 `0 active drivers`。不是五项断言失败，也不是本 diff 新增的导入回归。
- 随后单独运行可收集的 `test_launch.py` 与 `test_http_client.py`：18 passed，2.67s。没有给其余测试签发通过结果。
- 两次 pytest 临时目录分别为容器内 `/tmp/bgem3-diff-audit-20261105.pcyuMv`、`/tmp/bgem3-diff-audit-smoke-20261105.PyszlJ`；pytest 缓存和源码字节码写入被禁用。没有补写或伪造原生测试报告，结果来自本次 CLI stdout。
- 本地与目标容器都未发现可用 ruff/shellcheck 可执行程序；未安装新依赖，formatter/linter/pre-commit 为 `not_run`，不能用语法检查代替。
- 未执行模型精度、GPU 数值、graph 或端到端性能；未修改 Plugin/FG/FGV 源码、安装或服务。发布前需在最终修订代码上补齐对应检查。

最小整改顺序：先解决 R1 的公开 API 与归属，再解决 R2 的默认路径包装，最后针对最终代码补齐 R3 的链路/设备验证。当前不得标记 `ready_for_review` 或全规范通过。
