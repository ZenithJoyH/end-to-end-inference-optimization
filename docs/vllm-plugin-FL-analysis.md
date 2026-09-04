# vllm-plugin-FL 项目分析与新模型适配代码修改指南

## 1. 报告信息

- 上游仓库：<https://github.com/flagos-ai/vllm-plugin-FL>
- 分析分支：`main`
- 分析 revision：`ba52028ae1627f2d277138fc283ebc23b8087e12`
- revision 日期：2026-09-02
- 对应提交：`fix(gdn): keep packed decode beta in fp32 (#385)`
- 上游声明的 vLLM 对应版本：`main` 对应 vLLM `v0.24.0`，`release/0.2`
  对应 vLLM `v0.20.2`
- 分析方式：基于上述 revision 的静态源码、配置、测试及 CI 结构分析；未在目标加速卡上
  执行运行时验证。

后续实际适配前必须重新同步上游代码并记录新的 plugin、vLLM 和 FlagGems revision。
本报告中的文件位置和结论不得代替目标适配镜像中的实际检查结果。

## 2. 核心结论

`vllm-plugin-FL` 的定位不是单一算子库，而是 vLLM 与 FlagOS 多芯片能力之间的完整适配层。
它通过 vLLM 的 platform/general plugin entry points 完成启动注入，并同时覆盖：

1. 多芯片平台识别和 vLLM 配置改写；
2. 自定义 Worker、ModelRunner、Scheduler 和 graph wrapper；
3. FlagGems、芯片 vendor 实现和 PyTorch reference 实现之间的统一算子 dispatch；
4. attention、MoE、W8A8、通信和 KV transfer 等专用路径；
5. 模型注册、权重映射及版本兼容补丁；
6. 单元、功能、端到端、服务和 benchmark 测试。

后续适配新模型时，应优先复用已有扩展点，不应直接修改 vLLM 源码，也不应把所有问题都
塞进模型实现或 vendor patch。建议按以下优先级选择修改位置：

1. 配置或运行参数可以解决：只改平台/模型配置和启动脚本；
2. vLLM 已有模型实现但注册、权重映射或少量行为不兼容：增加 plugin 内的模型 shim 和
   capability-guarded runtime patch；
3. 缺少高层算子入口：通过 vLLM OOT operator 或工厂/注册接口把调用导入 plugin；
4. plugin 已有入口但缺少实现：通过 `CachedOp → OpManager → OpRegistry` 接入 FlagGems、
   reference 和必要的 vendor backend；
5. FlagGems 没有兼容实现：在 plugin 内实现兼容 eager 与 graph capture/replay 的 Triton
   算子，再通过同一 dispatch 框架注册；
6. 只有确实无法通过现有扩展点解决时，才增加最小、幂等、可检测、可回退的 runtime
   patch；仍然禁止改写 vLLM 源文件。

## 3. 整体架构与启动链路

### 3.1 启动链路

```text
安装 vllm-plugin-FL
    │
    ├─ vllm.platform_plugins: fl = vllm_fl:register
    │    ├─ 注册/补齐 custom-op schema
    │    ├─ 安装通用兼容 hook
    │    ├─ 设置 spawn 多进程方式
    │    └─ 返回 PlatformFL
    │
    └─ vllm.general_plugins: fl = vllm_fl:register_model
         ├─ 模型 config/registry/权重映射兼容
         ├─ 注册 FlagCX KV connector
         ├─ 注册量化 kernel 和 MoE router
         ├─ 安装模型/算子 runtime patch
         └─ 各 worker 进程中重复加载，所有 hook 必须幂等

PlatformFL.check_and_update_config
    └─ worker_cls = WorkerFL
          └─ ModelRunnerFL
                ├─ register_oot_ops()
                ├─ flag_gems.enable()/only_enable()
                ├─ attention backend dispatch
                ├─ graph capture/replay
                └─ 模型执行、采样与分布式通信
```

两个 entry point 位于
[`pyproject.toml`](https://github.com/flagos-ai/vllm-plugin-FL/blob/ba52028ae1627f2d277138fc283ebc23b8087e12/pyproject.toml#L36-L40)，
具体启动 hook 位于
[`vllm_fl/__init__.py`](https://github.com/flagos-ai/vllm-plugin-FL/blob/ba52028ae1627f2d277138fc283ebc23b8087e12/vllm_fl/__init__.py#L98-L185)。

### 3.2 关键目录职责

| 路径 | 主要职责 | 新模型适配时的典型用途 |
|---|---|---|
| `vllm_fl/__init__.py` | platform/general plugin 注册总入口 | 注册模型 shim、量化路径或幂等兼容 hook |
| `vllm_fl/platform.py` | 平台能力、worker、attention、graph、通信选择 | 平台级配置和能力声明，不放模型专属算子 |
| `vllm_fl/models/` | plugin 侧模型 shim | 复用上游模型类并补充协议、权重映射或加载逻辑 |
| `vllm_fl/configs/` | transformers/model config 兼容 | 上游尚无模型 config 时提供 plugin-owned config |
| `vllm_fl/patches/` | 模型或版本兼容 hook | 最小化、幂等、具备能力检测的临时兼容层 |
| `vllm_fl/ops/` | vLLM OOT 层和 MoE 等高层适配 | 把 vLLM 调用导向统一 dispatch |
| `vllm_fl/dispatch/` | 实现注册、策略、选择、fallback、诊断 | 新增逻辑算子和多 backend 实现的首选框架 |
| `vllm_fl/dispatch/backends/flaggems/` | FlagGems adapter | 对齐 vLLM 调用契约，调用同步后的 FlagGems 实现 |
| `vllm_fl/dispatch/backends/reference/` | PyTorch 参考实现 | 数值基线、fallback 和单算子对照 |
| `vllm_fl/dispatch/backends/vendor/` | 芯片专用实现和必要平台 hook | 仅保存确实与 vendor 相关的实现 |
| `vllm_fl/quantization/` | 量化 scheme、linear/MoE kernel 注册 | W8A8、FP8 或权重布局/scale 契约适配 |
| `vllm_fl/attention/` | attention 公共适配辅助 | 多模态或 attention backend 选择修正 |
| `vllm_fl/compilation/` | graph wrapper、breakable graph | graph capture/replay 与跨设备图对象适配 |
| `vllm_fl/worker/` | Worker、ModelRunner、Scheduler | 仅处理必须进入执行引擎主链路的能力 |
| `vllm_fl/distributed/` | FlagCX、collective、KV transfer | TP/DP/EP 通信和分离式服务 |
| `tests/` | unit、functional、e2e、serving、benchmark | 新模型和新算子的分层验证 |

## 4. 平台与执行引擎适配

### 4.1 PlatformFL

`PlatformFL` 是整个 plugin 的平台总入口。它从 FlagGems `DeviceDetector` 获取 vendor、
device type、dispatch key 和 `torch.<device>` API，再把 vLLM 的 worker 指向 `WorkerFL`。
它还负责：

- 按 NPU/MUSA/CUDA 设置 KV-cache block size；
- MLA block size 对齐；
- MUSA full graph 降级为 piecewise graph；
- 在特定 all-to-all backend 不兼容时关闭 graph；
- 通过统一 dispatch 选择 attention backend；
- 在 FlagCX 启用时切换 communicator；
- 返回 plugin 自己的静态 graph wrapper。

这些逻辑可见
[`platform.py`](https://github.com/flagos-ai/vllm-plugin-FL/blob/ba52028ae1627f2d277138fc283ebc23b8087e12/vllm_fl/platform.py#L176-L350)。

当前 `VENDOR_DEVICE_MAP` 覆盖 NVIDIA、Ascend、Iluvatar、MetaX、摩尔线程、Sunrise、海光和
平头哥。新平台适配至少要同时核对：vendor 规范名、device type、device name、可见设备环境
变量、vendor backend 目录、平台 dispatch YAML、测试平台 YAML 和 CI runner 配置，不能只加
一个映射。

### 4.2 Worker 与 ModelRunner

`WorkerFL` 和 `ModelRunnerFL` 深度参与设备初始化、模型加载、KV cache、graph、采样、
多模态、speculative decoding 和执行结果回传。当前 revision 中：

- `worker.py` 约 1,293 行；
- `model_runner.py` 约 7,673 行；
- `model_runner.py` 注明改编自 vLLM `v0.19.0`，但当前 plugin `main` 声明面向 vLLM
  `v0.24.0`。

因此这里是版本升级和新模型适配中风险最高的区域。新增模型时应先证明问题必须修改执行
引擎主链路，再修改这些文件。若只是模型注册、权重名称、单算子、attention backend 或
量化 scheme 问题，应优先使用对应的窄扩展点。修改 Worker/ModelRunner 时必须与目标 vLLM
revision 做逐段对照，并覆盖调度、KV-cache、prefill/decode、空 batch、TP/DP 和 graph 回归。

## 5. 算子 dispatch 设计

### 5.1 两层接入结构

算子适配包含两个不同层次：

1. **vLLM 调用入口层**：`CustomOp.register_oot`、`PluggableLayer.register_oot`、attention
   backend 注册、quant kernel registry，或在缺少正式扩展点时使用 runtime patch；
2. **实现选择层**：`CachedOp → OpManager → OpRegistry → FlagGems/vendor/reference`。

只在 backend 中写一个函数并不会自动覆盖 vLLM 调用；只注册 OOT 类但不接入 `CachedOp`
也无法获得统一 backend 策略。新增算子必须同时核对“调用如何进入 plugin”和“plugin 如何
选择实现”。

### 5.2 当前逻辑算子

当前 FlagGems backend 注册了 11 个逻辑算子：

- `dynamic_per_token_quant_int8`
- `silu_and_mul`
- `gelu_and_mul`
- `rms_norm`
- `rotary_embedding`
- `attention_backend`
- `moe_align_block_size`
- `moe_sum`
- `topk_softmax`
- `invoke_fused_moe_triton_kernel`
- `grouped_topk`

注册表见
[`flaggems/register_ops.py`](https://github.com/flagos-ai/vllm-plugin-FL/blob/ba52028ae1627f2d277138fc283ebc23b8087e12/vllm_fl/dispatch/backends/flaggems/register_ops.py#L29-L157)。
其中 `dynamic_per_token_quant_int8` 同时注册了普通 FlagGems 和 plugin 内 Triton adapter 两个
候选实现。

### 5.3 选择与 fallback

默认优先级为 FlagOS/FlagGems 150、vendor 100、reference 50；`op_backends`、环境变量和
allow/deny list 可以改变每个算子的顺序。`OpManager` 按当前进程惰性初始化，使用 policy
epoch 清理缓存，并在进程 fork 后重置状态。

`VLLM_FL_STRICT=0` 时，候选实现抛异常后会被标记失败并尝试下一个 backend；
`VLLM_FL_STRICT=1` 时首个异常直接暴露。热路径上的 `CachedOp` 会缓存已选实现，失败后再
切回 manager fallback。实现见
[`manager.py`](https://github.com/flagos-ai/vllm-plugin-FL/blob/ba52028ae1627f2d277138fc283ebc23b8087e12/vllm_fl/dispatch/manager.py#L508-L585)
和
[`dispatch/__init__.py`](https://github.com/flagos-ai/vllm-plugin-FL/blob/ba52028ae1627f2d277138fc283ebc23b8087e12/vllm_fl/dispatch/__init__.py#L151-L229)。

适配诊断阶段建议启用 strict 或强制单一 backend，原因是：

- fallback 可能让服务跑通，但实际没有使用预期的 FlagGems 实现；
- 数值精度错误通常不会抛异常，不会自动触发 fallback；
- 性能验收必须记录最终命中的实现，不能只记录配置中的首选项。

### 5.4 新增算子的标准改动面

如果 FlagGems 已有兼容实现，通常需要：

1. 在 `dispatch/backends/flaggems/impl/` 增加调用契约 adapter；
2. 在 `FlagGemsBackend` 增加 backend method；
3. 在 `flaggems/register_ops.py` 注册 `OpImpl`；
4. 在 `reference/` 增加可信参考实现和注册；
5. 必要时在 `vendor/<platform>/` 增加芯片专用实现；
6. 在 `ops/` 增加 OOT layer 或在现有高层路径使用 `CachedOp`；
7. 在平台 YAML 中设置明确的 `op_backends`、blacklist/whitelist；
8. 增加 unit、functional、eager 和 graph capture/replay 测试。

如果 FlagGems 缺失该算子，应把 Triton 实现放在 plugin 拥有的路径下并通过相同的
`OpManager` 接入，不得从模型代码临时直接调用。还应在适配容器 `/bug` 中保留 FlagGems
缺失或异常的最小复现证据。

## 6. 模型适配的三种主要路径

### 6.1 上游 vLLM 已完整支持模型

首选不增加模型源码，只增加测试配置、平台 operator policy 和必要的 adapter。检查重点：

- `architectures` 能否被 vLLM registry 正确解析；
- config 是否包含正确的 attention、MoE、hybrid/Mamba、RoPE 和量化字段；
- 权重名称、packed module、scale 和 ignored layer 是否一致；
- 模型使用的关键算子是否都能进入 plugin dispatch；
- eager 与 graph 的 prefill/decode 是否一致。

### 6.2 上游模型存在，但注册或契约不完整

Qwen3.5 是当前最清晰的参考模式：

- `patches/qwen3_5_text.py` 补充 config/model registry；
- `models/qwen3_5.py` 仍复用 vLLM 原始类，只补充 hybrid cache helper、权重前缀映射和
  `hf_to_vllm_mapper`；
- general plugin 使用 lazy class path 注册，避免在模型检查进程中过早初始化设备。

参见
[`qwen3_5_text.py`](https://github.com/flagos-ai/vllm-plugin-FL/blob/ba52028ae1627f2d277138fc283ebc23b8087e12/vllm_fl/patches/qwen3_5_text.py#L23-L59)
和
[`models/qwen3_5.py`](https://github.com/flagos-ai/vllm-plugin-FL/blob/ba52028ae1627f2d277138fc283ebc23b8087e12/vllm_fl/models/qwen3_5.py#L69-L105)。

后续新模型应沿用“复用上游类 + 最小 shim”的思路，避免复制整份模型实现。所有 hook 要
具备重复调用安全性，并使用 `hasattr`、symbol、signature、version 或 capability 检测，防止
在上游修复后继续重复 patch。

### 6.3 上游没有模型 config 或模型实现

GLM-5 展示了在 plugin 中注册自有 transformers config 的方式，但当前 `register_model()`
只注册了 `GlmMoeDsaConfig`，部分 model patch 仍处于注释或兼容代码状态。因此新增完整模型
不能只添加 config；至少需要确认：

1. transformers config 注册；
2. vLLM `ModelRegistry` 的 lazy model class；
3. 模型接口协议，如 generation、pooling、multimodal、hybrid cache；
4. 权重加载和量化映射；
5. attention、MoE/Mamba/DSA 等执行链路；
6. TP/PP/DP/EP 支持和通信；
7. eager/graph 端到端测试。

在不修改 vLLM 源码的边界下，新实现应位于 `vllm_fl/models/`，再通过 general plugin 注册。
如果模型实现大部分可复用上游相近架构，优先组合或薄继承，不要直接复制整份上游文件。

## 7. Attention、MoE 与量化改动思路

### 7.1 Attention

`PlatformFL.get_attn_backend_cls()` 本身只执行初始化期选择，返回 backend class path；真正的
prefill/decode 在对应 attention backend 中执行。FlagGems backend 当前默认返回 vLLM
`TRITON_ATTN`，只有设置 `VLLM_FL_USE_FLAGGEMS_ATTN=1` 才返回 plugin 的
`AttentionFLBackend`，且当前 FlagGems 路径明确不支持 MLA。

因此适配新 attention 结构时，应分别处理：

- backend 选择是否正确；
- metadata builder 是否覆盖 prefill、decode、prefix、chunked prefill；
- KV-cache layout、block size、cache dtype 和 scale；
- GQA/MQA/MLA/DSA/hybrid layer 的实际分支；
- TP/DP padding 和 graph capture shape；
- backend 是否在 graph 中执行，还是通过 breakable graph 在 eager segment 中执行。

不要把 `attention_backend` 选择器的测试误当成 attention kernel 的数值测试。

### 7.2 MoE

MoE 不只是一颗 fused kernel，至少包含 router、top-k/grouped-top-k、token-expert 对齐、两次
GEMM、激活、权重/scale 格式、expert combine/sum 和 EP/all-to-all。当前 plugin 对
`FusedMoE` 使用 factory monkey patch，并把 router、`moe_sum` 和多个内部步骤导入 dispatch。

适配新 MoE 模型时应先制作完整契约表，列明：expert 数量、top-k、group 数、renormalize、
scoring function、correction bias、shared expert、fused shared expert、quant mode、block shape、
TP/EP/DP 和 token padding。单独跑通 `fused_moe` 不代表完整 MoE 推理链路正确。

### 7.3 W8A8/FP8

当前 W8A8 路径通过 vLLM quant kernel registry、compressed-tensors scheme 和 MoE oracle
接入。`FLW8A8DynamicLinearKernel` 在加载后转置并固定 INT8 权重布局，动态量化 activation，
再调用 FlagGems `scaled_mm`。该处存在直接调用 FlagGems 的路径，没有完全经过通用
`OpManager`。后续若修改这条链路，应优先把需要策略控制、诊断或多 backend fallback 的
计算节点纳入统一 dispatch，而不是继续增加直接调用。

量化适配必须同时验证：checkpoint scheme、weight dtype/layout、scale 维度与 dtype、bias、
activation 动态/静态方式、ignored layers、MoE 两层权重、空 token、边界 shape、误差累积、
eager/graph 和最终生成精度。

## 8. Graph 兼容分析

plugin 的 `GraphWrapper` 根据 `device_type` 选择 `torch.cuda.CUDAGraph`、`torch.npu.NPUGraph`、
`torch.musa.MUSAGraph` 或 `torch.ptpu.PTPUGraph`，并按 `BatchDescriptor` 缓存 graph 和输出。
debug 模式会校验 replay 时输入地址是否与 capture 一致。代码位于
[`compilation/graph.py`](https://github.com/flagos-ai/vllm-plugin-FL/blob/ba52028ae1627f2d277138fc283ebc23b8087e12/vllm_fl/compilation/graph.py#L42-L251)。

新增或修改算子时至少检查：

- capture 阶段无 `.item()`、CPU 同步或依赖 tensor 数据的 Python 分支；
- 不在 capture 内创建不稳定的动态 shape、临时地址或不支持的动态内存；
- 输出、workspace 和中间 buffer 的地址在 replay 中稳定；
- in-place、view、stride、alias 和 zero-token 行为符合 vLLM 契约；
- 首次 warmup、capture、同 shape 新数据 replay、不同 capture size 都有测试；
- collective、KV-cache 更新和 attention metadata 使用 graph 支持的路径；
- piecewise、full 和 breakable graph 的实际模式被记录，不只写“graph 已开启”。

`breakable_cudagraph` 在当前版本直接复用 vLLM `0.24.0` 的实现，attention 和 KV-cache 边界
可能落在 eager segment。验收时应从日志和实际 capture/replay 证据确认执行模式，不能仅凭
`enforce_eager=False` 判定 graph 已生效。

## 9. 测试体系与本项目验收的对应关系

上游测试分为：

1. `tests/unit_tests/`：注册、policy、patch、量化契约和纯逻辑；
2. `tests/functional_tests/`：真实设备上的算子、graph 和 collective；
3. `tests/e2e_tests/inference/`：模型加载与离线生成；
4. `tests/e2e_tests/serving/`：服务 API；
5. `tests/benchmarks/`：throughput、latency 和 serving smoke；
6. `tests/platforms/*.yaml`：设备、容差、环境、用例和跳过项；
7. `tests/models/<family>/*.yaml`：模型路径、并行参数、eager/graph 和生成预期。

后续新模型建议按以下顺序提交验证：

1. import/registration/config/weight mapping 单元测试；
2. 新增算子的 reference 对照、dtype、shape、layout、边界和异常测试；
3. 单算子 eager 与 graph capture/replay；
4. attention、MoE、量化或 hybrid block 的组件测试；
5. 最小模型 eager 与 graph 跑通；
6. 使用模型真实最大上下文规则生成服务配置：模型支持长度大于 50000 时先用 50000，
   否则使用模型最大支持长度；
7. graph 模式 8 并发小批量精度与性能预检；
8. graph 模式正式精度评测；
9. 精度通过后进行 graph 模式正式性能验收。

上游现有 smoke YAML 中部分 `max_model_len` 只有 1024、2048 或 8192，这些值只适合其 CI
smoke 目的，不得直接复制为本项目正式服务配置。

## 10. 推荐的新模型代码修改流程

### 阶段 A：建立事实基线

1. 同步并记录 plugin、vLLM、FlagGems 的 branch、revision 和 clean worktree；
2. 核对 plugin/vLLM 版本矩阵，不混用不同 release 的内部 API；
3. 从模型 config 和实现生成结构、推理链路与关键算子清单；
4. 建立 native/reference 或已验证平台输出基线；
5. 在目标平台记录设备、driver/runtime、torch、triton、通信库和容器镜像。

### 阶段 B：定位最小缺口

1. 先关闭 FlagGems 或固定 reference/vendor，确认是模型层还是 operator 层问题；
2. 再使用 strict policy、per-op policy、FlagGems whitelist 和 dispatch debug 缩小到具体算子；
3. 对精度问题启用 I/O dump，比较第一处产生数值分歧的 layer/operator；
4. 对异常 fallback，核对日志中最终命中的 `impl_id`；
5. 对 graph-only 问题，分别比较 warmup、capture 和 replay，不混为一次服务失败。

### 阶段 C：选择正确扩展点

| 缺口 | 首选改动位置 | 同步修改 |
|---|---|---|
| architecture/config 未注册 | `patches/`、`configs/`、`models/`、`register_model()` | model config/registry 单测 |
| 权重名或量化元数据不一致 | model shim 的 loader/mapper | 权重映射与 ignored-layer 测试 |
| vLLM 高层层类需替换 | `ops/` 的 OOT class 或正式 registry | OOT whitelist/blacklist 与集成测试 |
| FlagGems 已有算子但 plugin 未接入 | flaggems adapter + backend + register_ops | reference、policy、数值、graph 测试 |
| FlagGems 算子报错或精度异常 | 容器 `/bug/<issue>/` 最小复现 | plugin 临时 policy、问题记录 |
| FlagGems 缺少算子 | plugin-owned Triton + dispatch | eager/graph、dtype/shape/layout 测试 |
| attention 类型或 metadata 不兼容 | attention backend/impl | prefill/decode/KV-cache/graph 测试 |
| MoE routing 或 experts 不兼容 | `ops/fused_moe/`、quantization、dispatch | router/expert/combine/EP 测试 |
| 平台实现差异 | `vendor/<platform>/` 和平台 YAML | 平台 CI、容差和 fallback 测试 |
| 引擎级 graph/worker 问题 | `compilation/` 或 `worker/` | 与目标 vLLM 对照及完整回归 |

### 阶段 D：逐层验证并保留回退

每次只引入一个实质变化，依次运行 unit、functional、最小模型和完整服务。新增 FlagGems
实现时保留 reference/vendor 对照，但适配验证阶段应使用 strict 或单 backend policy 证明
目标实现本身正确；完成后再验证生产 fallback policy。

## 11. 已识别的风险与不应直接照搬的做法

### 11.1 vLLM 内部 API 高耦合

项目大量导入 vLLM 私有模块、registry 和内部 class，并维护大体量 Worker/ModelRunner 副本。
任何 vLLM revision 变化都可能造成“能 import 但语义已变”的问题。不能只以安装成功作为
版本兼容证据。

### 11.2 默认 fallback 会掩盖接入失败

默认 `strict: false` 能提高可用性，但可能把 FlagGems 异常静默转为 vendor/reference 路径。
验收必须保存实际 op/impl 命中记录，并对目标实现做 strict 验证。

### 11.3 精度错误不会自动 fallback

dispatch 只在 Python 异常时切换候选实现；产生错误数值但正常返回的 kernel 不会被识别。
必须使用 reference、固定随机种子、明确容差和逐层 I/O 对照。

### 11.4 文档、能力声明和测试矩阵并非完全一致

上游 README 写明 Ascend 需要 eager，但 `PlatformFL` 声明 Ascend 支持 static graph，graph
wrapper 也包含 NPU 路径，测试矩阵还混合了 eager/graph 用例。这说明“代码存在 graph
分支”不等于“目标镜像已经验证通过”。本项目仍必须按实际平台完成 eager/graph 跑通，并
在 graph 模式完成后续验收。

### 11.5 存在违反本项目边界的上游做法

Iluvatar 的 `patch_triton_chained_or_for_iluvatar()` 会定位并原地改写 vLLM 安装目录中的
Triton 源文件，还会删除相应 `__pycache__`。参见
[`iluvatar.py`](https://github.com/flagos-ai/vllm-plugin-FL/blob/ba52028ae1627f2d277138fc283ebc23b8087e12/vllm_fl/dispatch/backends/vendor/iluvatar/iluvatar.py#L67-L148)。
这与本项目“不得修改 vLLM 源码”的规则冲突，后续适配不得复制该方式。应改为 plugin-owned
kernel、import-time symbol wrapper、正式 dispatch/OOT 扩展，或升级不需要该改写的 Triton。

### 11.6 部分路径绕过统一 dispatch

例如 W8A8 linear adapter 直接调用 `flag_gems.scaled_mm`，Ascend 部分 patch 的注释也明确
说明会绕过 CustomOp/dispatch。新增代码不应继续扩大这种例外；如必须保留，应记录原因、
支持约束、诊断方式和退出计划。

### 11.7 Graph 实现仍需目标平台验证

`GraphWrapper` 的 NPU replay 前包含显式 synchronize；graph class 支持集合与
`support_static_graph_mode()` 的 vendor 集合也不完全相同。此类代码应视为待平台验证能力，
不能从静态分支推断性能或完整兼容性。

### 11.8 原生扩展构建目前只声明 CUDA vendor

`setup.py` 的 `SUPPORTED_VENDORS` 当前只有 `cuda`。其他平台默认是 Python-only plugin；如果
新增能力依赖 `vllm_fl._C`，必须先确认目标平台是否具备等价 schema/实现，不能假定 CUDA
扩展能够跨平台加载。

## 12. 后续适配代码评审清单

### 模型与注册

- [ ] 模型 architecture、config type 和 lazy registry 已覆盖；
- [ ] 没有复制可以直接复用的 vLLM 模型实现；
- [ ] 权重 mapper 同时覆盖权重名和量化 ignored-layer 等元数据；
- [ ] hook 重复执行安全，并有明确 capability/version guard；
- [ ] 未改写 vLLM 源文件或其安装目录。

### 算子与 backend

- [ ] vLLM 调用确实进入 plugin，而不只是存在一个未使用的实现；
- [ ] FlagGems revision 与符号已核实；
- [ ] FlagGems adapter、backend method、`OpImpl` 注册和 OOT 入口完整；
- [ ] reference 实现可信，容差按 dtype 和累积误差设定；
- [ ] strict 模式证明目标实现可独立运行；
- [ ] 实际命中的 `impl_id` 已记录；
- [ ] FlagGems 异常或精度问题已在适配容器 `/bug` 中形成最小复现。

### Graph 与执行链路

- [ ] eager 和 graph 均可启动并完成最小推理；
- [ ] graph capture 和至少两次 replay 已验证；
- [ ] 不存在 capture-time host sync、动态分配或数据依赖主机控制流；
- [ ] shape、stride、地址、workspace、zero-token 和边界 batch 已覆盖；
- [ ] TP/PP/DP/EP、KV-cache 和 collective 的 graph 行为已验证；
- [ ] 后续 8 并发、正式精度和性能验收均使用 graph 服务。

### 记录与可复现性

- [ ] plugin、vLLM、FlagGems、模型和镜像 revision 已记录；
- [ ] 修改前后 vLLM worktree 均保持不变；
- [ ] 启动参数使用正确的 `--max-model-len` 规则；
- [ ] 代码 diff、配置、命令、测试输入、结果和限制均已归档；
- [ ] 性能优化一次只改变一个主要变量并保留基线；
- [ ] 适配总结和适配复盘已完成。

## 13. 建议优先阅读的上游文件

1. [README.md](https://github.com/flagos-ai/vllm-plugin-FL/blob/ba52028ae1627f2d277138fc283ebc23b8087e12/README.md)
2. [pyproject.toml](https://github.com/flagos-ai/vllm-plugin-FL/blob/ba52028ae1627f2d277138fc283ebc23b8087e12/pyproject.toml)
3. [vllm_fl/__init__.py](https://github.com/flagos-ai/vllm-plugin-FL/blob/ba52028ae1627f2d277138fc283ebc23b8087e12/vllm_fl/__init__.py)
4. [vllm_fl/platform.py](https://github.com/flagos-ai/vllm-plugin-FL/blob/ba52028ae1627f2d277138fc283ebc23b8087e12/vllm_fl/platform.py)
5. [dispatch/README.md](https://github.com/flagos-ai/vllm-plugin-FL/blob/ba52028ae1627f2d277138fc283ebc23b8087e12/vllm_fl/dispatch/README.md)
6. [dispatch/manager.py](https://github.com/flagos-ai/vllm-plugin-FL/blob/ba52028ae1627f2d277138fc283ebc23b8087e12/vllm_fl/dispatch/manager.py)
7. [ops/custom_ops.py](https://github.com/flagos-ai/vllm-plugin-FL/blob/ba52028ae1627f2d277138fc283ebc23b8087e12/vllm_fl/ops/custom_ops.py)
8. [compilation/graph.py](https://github.com/flagos-ai/vllm-plugin-FL/blob/ba52028ae1627f2d277138fc283ebc23b8087e12/vllm_fl/compilation/graph.py)
9. [tests/README.md](https://github.com/flagos-ai/vllm-plugin-FL/blob/ba52028ae1627f2d277138fc283ebc23b8087e12/tests/README.md)
10. [tests/run.py](https://github.com/flagos-ai/vllm-plugin-FL/blob/ba52028ae1627f2d277138fc283ebc23b8087e12/tests/run.py)

## 14. 总结

后续模型适配的正确思路是先定位缺口属于模型注册、权重契约、高层 OOT 入口、逻辑算子、
平台 backend、量化、attention/MoE，还是执行引擎本身，然后选择最窄的 plugin 扩展点。
`vllm-plugin-FL` 已提供较完整的 dispatch 和测试框架，应以它们作为新增代码的主干；runtime
patch 和 Worker/ModelRunner 修改只能作为经过证明的最后手段。所有新实现都应同时具备
明确的 reference、实际 backend 命中证据、eager/graph 覆盖以及目标平台端到端验证。
