# fw-019：新版 OAI experts 链路接入

## 冻结范围与设计

同用户请求和环境见fw-018；独立算子接入变量，不与router收益相加，不切换安装、不触碰8011。
复用 TritonExpertsFL.apply 现有整体FGV experts路径，仅扩展 SWIGLUOAI_UNINTERLEAVE 未量化/no-LoRA/CUDA接口分支。
保留原SiLU/NVIDIA选择及其调用参数；不开放W8A8/FP8/INT4、其他activation、其他设备或LoRA。
新版FGV能力由公开函数签名是否显式接受gemm1_alpha/beta/clamp_limit判断；缺少新API走原逐步Triton路径，不靠捕获kernel异常回退。
保留模型的gemm1_alpha/gemm1_beta/gemm1_clamp_limit，不写死1.702/1/7，也不丢弃bias、expert_map、router-weight位置或quant元数据。
实际激活参数需有限标量且clamp≥0；不支持参数留在原路径。选择后的执行错误传播，不掩盖。
大batch的router回退属于fw-018；FGV完整experts有自己的chunk逻辑，本项不人为将服务C64降到32。

## 首个证伪与验证范围

CPU加载实际TritonExpertsFL源码，用mock kernels验证原参数逐项透传、输出copy所有权、非默认alpha/beta/clamp、router-weight前后位置、local expert映射及bias。
覆盖旧FGV API/缺少FGV/开关关闭、SiLU、quant/LoRA/其他设备及异常传播，证明未支持时进入原pipeline。
外置CPU MoE oracle与mock FGV只验证集成契约，不证明实际Triton kernel正确或PPU速度。
不新增Plugin测试文件、不改thead.yaml、vLLM、权重、FGV内核。后续需PPU独立数值、graph capture+双replay、模型C1/C8和完整GPQA。

## 性能/回退与状态

Prefill/Decode/Mixed的净收益均未测；可能减少调用组织开销，但完整FGV调用/临时内存/输出copy成本必须实测。
旧逐步pipeline仍为fallback；原Plugin editable与fw-017副本保留，候选不安装即可回退。pr_readiness=experimental。
原始产物计划与fw-018共用router-oai-001-20261018，逐项测试可独立归属，不声称单变量端到端通过。
结果：CPU契约通过，最小精度回归整体incomplete，PPU/graph/模型/正式精度/性能not_run。

## 最终实现和证据

TritonExpertsFL构造时探测新版FGV公开函数的三个显式keyword参数并保存函数对象，避免在逐token apply/编译区域重复inspect.signature。
仅CUDA接口、FGV启用且fused_moe未禁用、无LoRA、未量化且输入/权重dtype匹配时开放OAI；不伪造硬件型号支持。旧API、无依赖、无symbol及不支持的分支保留原pipeline。
参数来源仍是原self.gemm1_alpha/beta/clamp_limit，保持上游构造时已有的默认解释，不写死模型默认值；bias、expert_map、global_num_experts、a1/a2 scales、block_shape、router-weight位置等均照原调用透传。
原SiLU分支不会收到额外OAI参数；FGV新API存在但执行出错时错误继续传播，不静默降级。

115项专项CPU/mock通过，覆盖M0/1/32/33/64、FP32/BF16/FP16、alpha/beta/clamp=(1.702,1,7)/(0.5,-2,0.25)/(1,0,0)、expert映射/bias、router-weight输入/输出位置、原始buffer不变、输出copy所有权。
另覆盖旧API/缺失依赖/非CUDA/禁用/LoRA、FP8/INT8/INT4/量化dtype、权重dtype不符、非有限或无效参数、SiLU原调用及异常传播。
执行的是实际Plugin apply/探测函数与明确mock的FGV实现，CPU小shape独立oracle核验集成；没有执行FGV Triton GEMM/activation，不是生产H6144/TP16数值通过。
组合最终600项通过及完整hash/日志/XML见[fw-018](fw-018-fp32-router-gemm-dispatch.md)，包含原topk415项回归。每项前后无GPU初始化断言通过，8011原服务health200且原进程保留。

候选未激活，原Plugin安装、fw-017候选和FGV源码均未改动；已有两级回退脚本保留。未提交/推送，未签发或复用旧精度gate，未宣称端到端收益。
下一步仅在设备条件明确后，用真实FGV核对完整MoE、激活边界、graph capture与双replay，再做TP16模型回归及正式GPQA≥88%。当前停止在用户指定的代码/CPU范围，不自动等待或重启。
