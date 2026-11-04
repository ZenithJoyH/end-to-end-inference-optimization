# op-004：MetaX 无 LoRA FlagOS 完整 MoE 接入

- 日期：2026-10-13；用户明确要求在独立容器验证正确性和 graph 后回写 qwen-vl。
- Host/model：mx-59 / Qwen3-VL-30B-A3B-Instruct / MetaX / TP2。
- 分类：operator/replace；使用已有 FlagGems-vllm 完整 MoE，不新增 kernel。
- 状态：completed / retained-code-only；性能和正式 GPQA：not_run。
- 独立容器：qwen-vl-sampling-opt-20261012；Remote case 沿用 `/public-flash/jinghao/qwen3-VL/20261012-qwen3vl-metax-sampling-migration`，本轮使用 commands/op004/、logs/op004-*、results/op004-*。

设计：在 TritonExpertsFL 的现有完整调用扩展点接入 MetaX，无 LoRA、原生浮点 SiLU、无量化/量化block并且 MoE 组件选择 FlagOS 时调用公共 `flaggems_vllm.fused_experts_impl`。库 MetaX 函数只接受 SiLU，量化分支另有契约，故其他能力范围保留原分步骤路径。NVIDIA 现有完整入口保持原条件；其他平台不改变。复用现有 manager/policy 解析，尊重 vendor/per-op override，不增加新环境开关、registry 框架或模型身份白名单。参数、输出 copy 与 router 权重语义沿用已有完整入口，LoRA 仍允许在两次 GEMM 间注入。

关键变化是 MetaX 将由库负责 align、GEMM、激活与 sum；库可能选择 GEMM1+SiLU 或 GEMM2 direct_sum。Plugin 原 VLLM_TUNED_CONFIG_FOLDER 不再决定完整库内部配置；需用真实 MetaX 整链输出和大 T graph 验证，不继承上轮分步骤的测试结论或性能数字。

先复核独立容器镜像/规范化挂载、源码与依赖一致性并保存原内容。按项目精度 Skill 的 minimal-regression 执行完整链数值对比、独立参考、支持边界/路由反例、graph capture+至少两次变化输入 replay；随后在独立容器启动 TP2 graph 模型服务做 smoke/C8 与命中证明。源码回写采用 SHA guard，仅回写本轮 Plugin 文件，保存补丁和回退；不重启源服务。未通过正确性/graph 时不部署。

首个证伪实验：实际 TritonExpertsFL.apply 的 MetaX/no-LoRA FlagOS 路由应进入库完整函数；改成 LoRA、vendor policy、不支持激活/量化则应保留旧分支。设备测试覆盖 BF16/FP16/FP32、小/非对齐/大T、router权重输入/输出、bias和expert-map，并对整链而非两个孤立 GEMM 判断。

模型 graph 服务与算子 graph 证据分开记录；没有正式 GPQA 阈值/gate 或无profiler性能测量时，不宣称正式精度和性能验收通过。回写授权来自本轮用户明确指令。

首轮验证（logs/op004-validation.log）在旧分步骤 baseline 的测试实例处失败：测试绕过 __init__ 后遗漏 quantization_emulation=False。依据项目精度定位 Skill 分类 measurement-invalid，不能归因于候选数值；v2 补全原父类字段并保留首轮原件，生产代码不因该测试问题改动。设备预检发现宿主机 MACA 从上次 3.7.0.38 变为 3.7.1.5，本轮重新验证，旧性能结果不用于本轮比较；GPU4/5 空闲，其他工作负载不动。

v2 在 BF16 T1/8/64/257/1024 的完整数值与两次变化输入 replay 通过；T4096 首次进入大T配置时库内 GEMM1 启动失败：shared memory required=98304、hardware limit=65536，定位至 MetaX get_default_config 沿用 200000-byte 限制且 stages 最少2。按精度定位 Skill 归类 execution/resource regression，冻结日志，不部署该版本。v3 只在 MetaX 库原 default-config 边界按实际 device properties 约束 stages（允许降到1），缓存每个 device 的共享内存元数据，不复制 kernel、不新增 torch compute/fallback；NVIDIA 通用实现与 autotune 均不改（MetaX-only 修复，NVIDIA tuning 不适用）。完整接口参数/语义不变，重跑同一矩阵后才考虑部署。此修复是接入当前完整库必须解决的正确性/可执行性依赖，与 Plugin 接入分仓库保存补丁。

v3 暴露估算还遗漏 paired gate/up 的第二份 B tile。独立容器配置检查确认：Torch 和 Triton 都报告65536；T4096 GEMM1 选 BM128/BN128/BK64/stages2、PAIR_GATE_UP_DOT=true，无 embedded 配置，实际两份 B tile 需要98304。v4 在该 paired 路径按 A+2B 估算，stages降到1；GEMM2保持A+B估算。只改host配置元数据计算，kernel不变。保留v2/v3失败原件，以v4重跑大T与原矩阵来证明修复，而非增加宽泛异常fallback。

v4 paired kernel 即使 stages1 仍需66560（含编译器布局/scratch），超过65536。最小单变量 probe 仅将 PAIR_GATE_UP_DOT 设为false，完整 SiLU 融合与大T direct_sum 保持启用；BF16 T4096/8192 数值及各两次变化输入 replay 通过（max_abs_diff_baseline=.00390625）。因此 v5 按64KiB硬件能力关闭该不支持的 paired 变体，使用已有普通 fused-SiLU kernel，不回到 Plugin 分步骤、更不走 Torch/reference fallback。probe 原件：commands/op004/probe.py、logs/op004-generic-fused-probe.log、results/op004-generic-fused-probe.json。待v5原矩阵和模型服务验证，不以probe替代整体结论。

v5 的 BF16/FP16 T1/8/64/257/1024/4096/8192 整链与变化输入 replay 全部通过；首个输入端加权测试差异较大。核对 vLLM modular prepare 文档：输入权重在 prepare 阶段已应用，且仅适用 top-k=1；原测试错误地传 raw input/top-k8，对原apply并非合法调用。还确认完整库API内部会应用输入权重，所以直接传已加权的 activations 会重复加权。v6 在 MetaX apply_router_weight_on_input=true 时保留原分步骤路径，并用真实 top-k1、预加权输入验证该边界；当前Qwen3-VL top-k8/default output-weight 路径仍直接调用完整库。NVIDIA 原有分支不变，未扩展到该边界的语义重设计。

v6 half 的完整矩阵及输入端加权/bias/expert-map 边界通过；FP32首次启动需81920而上限65536，定位general config仍按2-byte输入估算。v7仅将dtype="float32"的元素字节数改为4，沿用实际上限与stages保护；其他dtype不扩大改动。FP32矩阵保持原容差，不降低正确性标准。

v7 FP32候选可执行，比较时原分步骤 baseline 的vLLM默认配置触发81920资源错误，连vendor fallback也失败；trace明确发生于old=run_apply(base,...)，是原FP32执行限制，非本轮候选错误。v8 对BF16/FP16继续同时比较原路径和独立参考；FP32改为独立数学参考和变化输入graph验证，明确旧路径不可比较，不用吞掉异常或标记旧路径passed。此边界不涉及当前BF16模型的正式GPQA分数；不修改vLLM配置算法。

最终设备v8通过：21场景（2空输入、19非空）、11路由/接口检查；每个非空场景capture后改变输入/路由replay两次。BF16/FP16标准T=1/8/64/257/1024/4096/8192，额外预加权top-k1 fallback、bias、expert-map；FP32 T1/64只与独立参考比较。max_abs_diff_baseline：BF16 .00390625、FP16 .00048828125；原容差BF16 atol/rtol=.03/.03、FP16=.006/.01、FP32=.003/.01，未事后放宽。完整public API调用计数38（预加权fallback不算命中）。JSON/log：results/op004-validation-v8.json、logs/op004-validation-v8.log。

独立TP2模型服务第一轮证明两个worker实际进入库MetaX完整MoE，torch.compile/初始profiling通过；之后Plugin worker调用vLLM kernel_warmup，函数无条件导入MiniMax3 NVIDIA model，触发MetaX Triton不支持do_not_specialize_on_alignment。失败与MoE计算无关，发生在capture_model之前。无现有全局skip配置，v9在Plugin MetaX worker平台边界跳过该组NVIDIA专用warmup，保留模型_dummy_run、LoRA清理和原FULL_AND_PIECEWISE capture流程；其他平台行为不改，vLLM只读。当前Qwen不使用DSv4/DeepGEMM/FlashInfer/MiniMax warmup，模型实际预热由原profile/dummy/capture完成。其他MetaX模型的冷启动影响未测，需作为独立兼容依赖列入PR未测项，不宣称跨模型性能通过。保留logs/op004-model-service.log失败原件。

第二轮独立服务已完成同配置TP2/原FULL_AND_PIECEWISE graph启动、端口18404 readiness；两个worker 70297/70298 的库MetaX DEBUG记录实际完整MoE调用。启动证据为 logs/op004-model-service-v2.log / manifests/op004-service-launch-v2.json，source仍未回写。正在执行两个single与两轮C8共18请求，并用验证专用observer委托原CUDAGraph.replay计数（不进入生产源码，不把日志观测时间当性能结果）。

模型验证通过：2 single + 2×C8 =18请求全部成功且非空；两TP worker的原生graph replay均观测到1/2/16次。结果 results/op004-model-graph-validation.json，原始请求/响应 results/op004-service-responses.json，各rank replay JSON保存在results/op004-graph-replay-pid*.json。仍未执行完整GPQA或正式性能，不用服务日志中的吞吐估计宣称加速。

replay观察器覆盖startup/warmup阶段，计数不解释为请求逐条命中次数；两个worker实际模型完整MoE命中日志、capture完成与18成功请求共同构成集成证据。样例科学问答连贯，部分响应因max_tokens=96结束于length，属于输出观察，不冒充正式分数。

## 部署和边界

commands/op004/deploy_gate.py 检查设备矩阵/模型graph结果均passed、独立容器三文件SHA匹配验证候选，然后执行apply-v9.py deploy。规范化挂载passed、原snapshot identity保持、source原SHA匹配后回写三个文件：Plugin fused_moe_utils.py、Plugin worker.py、FlagGems-vllm MetaX fused_moe.py。备份 patches/op004-deploy-v9-before.json；产物 results/op004-deploy-gate.json、op004-deploy-v9-manifest.json、op004-deploy-v9-mounts.json。没有启动或重启qwen-vl源模型服务。

仅停止本轮独立验证服务的端口18404/API PID69810；源容器和独立容器保留，其他工作负载不动。stop证据 results/op004-service-stop.json。

默认当前Qwen3-VL BF16、SiLU、无LoRA、输出端router权重、FlagOS路径现在直接调用公共flaggems_vllm.fused_experts_impl，函数来自该库MetaX backend。LoRA、量化、非SiLU、预加权输入以及显式vendor/reference的相关组件继续原路径；NVIDIA原完整分支保持。vLLM源码、权重、tokenizer、MCTLLASS已有补丁与采样迁移保持不变。

回退命令：在mx-59运行 python3 <remote-case>/commands/op004/rollback-v9.py，默认dry-run；--execute才恢复三文件，检查候选SHA并拒绝active source service。不会自动重启。pr_readiness=needs_revision：其他MetaX模型的warmup/冷启动行为、非目标平台硬件、量化场景及正式模型精度/性能仍需验证；本轮完成的是用户指定的完整入口接入与作用范围内正确性/graph验证。

部署后source实际API来源/eligibility和三文件SHA验证通过，Plugin/FlagGems-vllm git diff --check通过，vLLM工作区干净：results/op004-source-postverify.json、logs/op004-source-postverify.log。回退dry-run验证3文件、mutated=false。没有提交、推送或创建PR。

外部产物总清单：manifests/op004-artifacts.json，记录145项脚本、补丁、验证/部署原件的SHA与大小。阶段复盘 planning-op004-20261013 写入state.yml/README：组合累计性能和Prefill/Decode/Mixed热点均未知，下一轮先冻结正式精度/同配置性能契约；不以本轮功能测试或旧采样microbenchmark签发端到端结论。
