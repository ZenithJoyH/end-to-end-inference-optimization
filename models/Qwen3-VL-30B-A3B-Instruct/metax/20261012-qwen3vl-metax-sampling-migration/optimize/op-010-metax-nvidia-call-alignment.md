# op010 MetaX按现有NVIDIA调用逻辑对齐

用户明确要求Plugin调用层与NV一致，其他暂不调整，并询问如何关闭FlagOS MoE。仅将TritonExpertsFL.apply条件改为no-LoRA且(is_cuda或vendor_name metax)，完整调用内容不变；删除MetaX专有支持/输入权重/per-op条件及闲置get_default_manager导入。不新增helper、registry key、开关或fallback，NVIDIA原行为不变，其他平台仍staged。

用户指令明确接受完整MoE不再受四个内部op覆盖控制。当前Qwen3-VL支持配置为SiLU、BF16、输入侧路由权重False；本轮在FP16/BF16/FP32的该共同路径验证。对其他激活、FP8、输入已预乘权重等配置不扩大支持承诺；新入口按原NV逻辑把参数交给库，库拒绝的不再用旧MetaX特例转staged。已知输入权重prepare语义与完整库可能二次加权，本轮用户要求不做其他调整，不宣称True配置正确。NVIDIA专有SwiGLU差异不改。

关闭配置审查：selector调用use_flaggems全局而不是use_flaggems_op(fused_moe)；OOT factory黑名单与oracle hook同时核对。当前四内部op blacklists/policy不控制新的直接完整调用。对USE_FLAGGEMS/VLLM_FL_PREFER_ENABLED/PREFER和OOT/FlagOS blacklist以真实配置函数及selector做独立进程范围探针，若关闭后当前MetaX native选择错误，记录为现存阻塞不顺手修复。不会执行关闭后的正式模型验收或修改源启动开关。

冻结最小回归：新NV/MetaX平台条件等价路由（mock隔离，unsupported参数只验证与旧NV一致，不作数值支持承诺）；当前共同dtype数值/graph BF16 T64/FP16 T1/FP32小shape各2次变输入replay；真实TP2 FULL_AND_PIECEWISE capture、每rank2replay、2单+2波C8共18请求；source idle/SHA guard/mount parity过门后回写一文件，不重启源服务。命令commands/op010，结果日志留既有remote case。一文件回退备份与dry-run。正式GPQA/性能/其他平台硬件未测。

## 结果与回写

18个新路由用例通过，另以旧NVIDIA actual apply条件对照新MetaX actual apply，18个mock调用选择逐例一致。当前共同SiLU配置的BF16 T64/FP16 T1 E128 H2048 I384 K8与旧MetaX路径数值一致，FP32 T3 E4 H64 I32 K2与独立CPU float64数学参考通过；三dtype各两次变输入graph replay通过。GELU/FP8现在同NV逻辑直接交库，MetaX库明确前置拒绝，属于边界行为，不是兼容支持。输入加权True仅验证参数传递，未声称数学正确；既有prepare问题不在本轮修复范围。

TP2 BF16 FULL_AND_PIECEWISE：19项mixed/11项decode capture完成，两worker完整MetaX库命中/当前源码见证/至少2次native replay；2单+2波C8共18非空，0客户端错误，15输出达到96token限制，不作正式精度判断。独立通过后回写仅fused_moe_utils.py，当前source/clone SHA eee200132b6713b69d72180860806ccbc0ea0bc7f14d59fe079d252a1c3195fa，完整调用和staged尾部AST未变，vLLM工作区clean、FlagTree和启动脚本未改。源码仅净删15行条件及去掉闲置import，无新增helper/注册key/开关。

源服务不重启，验证服务18410精确停止、0/1卡释放。一文件回退dry-run passed/未修改，先恢复本轮再用更早SHA保护回退。最终53项产物SHA见manifests/op010-artifacts.json；commands/op010/nv_alignment.patch为本轮差异，patches/op010-final-qwen-vl-plugin.patch为累积补丁。无正式GPQA/性能/NVIDIA硬件验证、无提交/推送/PR。

## 当前关闭入口的实证

真实配置helper/selector的7个环境组合探针（不是关闭后完整模型启动）：默认、FlagOS blacklist=fused_moe/unquantized_fused_moe_method、OOT blacklist=fused_moe、OOT_ENABLED=0均仍选择TritonExpertsFL。原因是patched unquantized oracle只检查use_flaggems全局，完整call绕过内部dispatch；单独禁factory/这些key并不停止此选择。

USE_FLAGGEMS=0、VLLM_FL_PREFER_ENABLED=0、PREFER=vendor均使use_flaggems=False，但当前MetaX is_cuda=False/is_out_of_tree=True，原_get_priority_backends无MetaX分支，_AVAILABLE_BACKENDS未赋值，真实selector探针报UnboundLocalError。这是既有选择代码，旧/new该部分AST未改。本轮未修，不将全局开关误报成可正常启动的替代MoE方案，也不建议用上述blacklist伪装关闭成功。当前没有可在保留其他FlagOS算子的同时可靠单独关闭完整MoE的现成开关；全局关闭全部FlagOS选择可由USE_FLAGGEMS控制，但native路径需另行解决才能作为正常运行方案。

按用户“其他暂不做调整”只给出诊断，不新增env或改oracle/native backend。production仍默认FlagOS，所有不支持属性边界只按原NV调用契约处理，不宣称两平台所有算子行为相同。

## 2026-10-13 native 回退根因复核（只读）

重新从 mx-59 的 qwen-vl 读取当前源码。Plugin `fused_moe_utils.py:92` 在 OOT 且 use_flaggems 时返回 TritonExpertsFL；关闭后，无 LoRA 配置进入第101行 `_get_priority_backends`。该函数第51–75行仅覆盖 ROCm/NVIDIA CUDA/XPU/CPU，未覆盖 MetaX，也没有兜底赋值。PlatformFL 的 `_enum=OOT`；`is_cuda()` 第79–81行要求 vendor=nvidia，而 `is_cuda_alike()` 第69–77行允许当前 MetaX 的 cuda device_type。故异常发生在选择阶段，尚未调用专家计算，不能解释为原生 Triton kernel 不兼容。显式 moe_backend=triton 也在第146行之后处理，无法绕过第101行异常。

当前 vLLM `oracle/unquantized.py:113–118` 将 TRITON 映射到原生 `TritonExperts`；`experts/triton_moe.py:91–92` 的设备支持判断使用 is_cuda_alike，非量化 `(None,None)` 与 SiLU 也在支持表。其 apply 两次调用 `invoke_fused_moe_triton_kernel`，后者在 `fused_moe.py:772` 启动第292–293行的 Triton JIT `fused_moe_kernel`。整条专家链并非全由 Triton 实现：当前 SiLU 调用 `torch.ops._C.silu_and_mul`，token 排列和求和经 `_custom_ops.py:2158–2171` 调用 `_moe_C` 扩展算子。

上游原始 selector 在 `oracle/unquantized.py:167–168` 对 OOT 返回 `(OOT,None)`，不会自动当 NVIDIA 选择 TRITON；Plugin 接管选择后需要补全自己的原生回退。最窄修复位置是 Plugin backend 候选选择，为 MetaX 配置原生 TRITON（按 activation format 处理 batched），保留 is_supported_config 检查；不应修改全局 is_cuda 语义或在 apply 增加条件。此次仅分析，未实施修复，也未验证关闭 FlagOS 后原生 MoE 的设备数值/graph/模型启动；已验证的是异常根因与原生路径的源码支持条件。
