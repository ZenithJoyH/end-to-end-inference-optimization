# op-011 官方 MetaX 镜像 MoE 调用来源检查

用户指定 cr.metax-tech.com/public-ai-release/maca/vllm-metax:0.24.0-maca.ai3.8.2.5-torch2.10-py312-ubuntu22.04-amd64，在 mx-59 创建独立检查容器。目的为核对官方平台、selector、专家实现和底层算子来源，不更改现有 qwen-vl/Plugin，不作为新优化候选或跨环境性能对比。

远程独立产物目录 /public-flash/jinghao/qwen3-VL/20261013-metax-native-moe-image-inspection。远端执行前保存 commands 副本和 SHA。镜像本地已存在，身份 sha256:d080f0f3aa7108b7e9d9cc23eec704bdb7828ec6bb731dab6129a77200238d1e。检查容器 metax-native-moe-inspect-20261013，无目录挂载、无服务端口、无网络，环境限制设备0，先做来源检查。此为用户明确指定新官方镜像的对照诊断，不从已适配容器复刻，不使用其作为模型正确性/性能测试容器；因此无源容器挂载一致性或镜像谱系通过的声明。

状态：completed / diagnosis-only。检查内容为包版本、平台 entry point 与 monkeypatch、Qwen 非量化默认 MoE 选择、原生 Triton 和可能的 mctlass/custom ops 调用条件。若需要执行算子，只在确认空闲设备0后做小规模来源见证，不启动完整模型，不推断正式精度与端到端性能。

## 实际来源与选择

官方镜像安装 vLLM 0.24.0、vllm_metax 0.24.0+g436274.d20260813.maca3.8.2.5.torch2.10.0、torch 2.10.0+metax3.8.2.2、triton 3.6.0+metax3.8.2.2、mctlassEx 0.1.1+metax3.8.2.2torch2.10；没有 vllm_fl、flag_gems、flaggems_vllm。mcoplib 初始化日志版本0.4.9、commit8b5bd8b。vllm_metax 的 platform entry point 注册 MacaPlatform，实际对象 MxsmlMacaPlatform；enum OOT/device_type cuda/is_cuda False/is_cuda_alike True。

`vllm_metax/customized/layers/unquantized_fused_moe_method.py:65` 用 register_oot 替换 vLLM 的 UnquantizedFusedMoEMethod，构造时设置 moe_backend=triton，并调用自有 selector。标准 activation format 的候选固定 TRITON，batched format 选 BATCHED_TRITON。标准模式通过 `vllm_metax/utils/fused_moe.py:23` 的 get_triton_experts_cls 选择 MetaX 或镜像内 vLLM 的专家类，不依赖 NVIDIA 的平台优先级列表。Prepare/Finalize、modular kernel、activation 等框架继续复用 vLLM，专家 apply 与 GEMM dispatch 默认由 MetaX 副本提供。

真实 factory（完整 FusedMoEConfig + set_current_vllm_config 上下文）确认：默认 method 来自 vllm_metax.customized.layers.unquantized_fused_moe_method，experts 来自 vllm_metax.model_executor.layers.fused_moe.experts.triton_moe；进程内设置 USE_VLLM_TRITON_EXPERT=1 后 method 仍为 MetaX 的 OOT method，但 experts 改为 vllm.model_executor.layers.fused_moe.experts.triton_moe。同一开关也让旧 fused_experts 函数入口在两个模块之间选择。此开关属于 vllm_metax，不能推定仅设置它就会改变现有 qwen-vl 的 FlagOS Plugin 选择。

实际运行默认值（不是 TYPE_CHECKING 声明）：USE_VLLM_TRITON_EXPERT=False，MACA_VLLM_ENABLE_MCTLASS_PYTHON_API=True，MACA_VLLM_ENABLE_MCTLASS_FUSED_MOE=True，USE_PRECOMPILED_KERNEL=True。MetaX 的 invoke_fused_moe_triton_kernel 名称不代表一定启动 Triton：源码 BF16 无scale的分支直接调 cutlass_moe_mm_bf16 → mctlassEx_fused_moe_bf16_gemm → mctlassEx.FusedMoeGEMM → 编译扩展。其它条件走 mcoplib 的预编译 Triton kernel；关闭 USE_PRECOMPILED_KERNEL 时可走 MetaX 文件中的本地 Triton JIT。仅关闭 MCTLASS_FUSED_MOE 不会切回镜像内 vLLM 专家类。

平台 import_kernels 默认导入 mcoplib._C 与 mcoplib._moe_C，注册 SiLU、token排列和求和等扩展算子；即使专家 GEMM 切回 vLLM Triton，这些底层扩展仍是 MetaX 编译实现。镜像中 vllm._C/vllm._moe_C Python 模块不存在，不代表注册的 torch.ops 不可用。

## 设备调用见证与边界

卡0确认空闲后，BF16 T64/E128/H2048/I384/K8，无LoRA、无量化，真实构造 experts 并调用 apply。默认 MetaX 路径记录两次 invoke_fused_moe_triton_kernel、两次 cutlass_moe_mm_bf16、两次 mctlassEx_fused_moe_bf16_gemm 和两次 FusedMoeGEMM.__call__，返回有限值。USE_VLLM_TRITON_EXPERT=1 的同配置调用也成功，两次 invoke_fused_moe_triton_kernel 来自 vllm 模块，MCTLLASS GEMM调用为0，返回有限值。Python profile仅用于函数来源见证，没有采集设备性能数据；未做独立数学参考数值比较、graph或完整模型测试，不签发正确性/性能gate。

初始检查容器仅映射 /dev/dri，在 FusedMoeGEMM 初始化时段错误。保留失败栈后创建补齐 /dev/mxcd 的 metax-native-moe-inspect-20261013-io，插件初始化通过。首次真实method探针缺 vLLM CustomOp 配置上下文，补齐 set_current_vllm_config 后通过；未修改任何安装源码。最终保留正确映射容器，无目录挂载、无网络/端口；探针进程退出后不持有GPU权重或运行模型服务，qwen-vl及优化容器未变更。

原始源码文本+SHA：results/collect.json；默认和切换的实际factory：results/runtimefinal.json；设备调用来源：results/hardware.json、results/hardwarenative.json；失败证据：logs/runtimev2.log、logs/runtimeio.log。命令均在commands，镜像/容器规范记录results/container.json与container-io.json。以上路径相对于本记录远程独立产物目录。

最终汇总 results/summary.json SHA256 ab913e82bc97d323ff45e8d7c0d70e3fab3e9ea0b3f0ad341495db5d088d5ee3；35项产物的SHA见results/artifacts-sha256.json。初始失败容器已精确停止，正确映射检查容器保留运行，未删除任何容器。
