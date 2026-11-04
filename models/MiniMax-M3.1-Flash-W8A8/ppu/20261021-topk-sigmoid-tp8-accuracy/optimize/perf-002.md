# perf-002 完整 MoE 入口与分步桥接性能对比

状态：安装原样及统一选参归因对照均完成；保留已安装分步桥接，没有切换模型完整入口。用户要求比较两种调用方式。inference-performance-evaluation / targeted，并按key-operator-analysis先做完整MoE调用micro；不替代模型请求或四场景验收。

对照保留安装原代码：Plugin split桥接 vs FlagGems-vllm Thead完整fused_experts_impl。实际shape E128/H6144/I384/topk4，BF16激活、INT8权重、FP32逐输出通道scale，alpha1.702/beta1/clamp7；M1/8/16/32/64/1024/8192，均匀和集中16专家两种合成路由。输入分布不能冒充真实路由频率。Decode/Prefill按M区分，Mixed模型指标尚未测。

同进程配对split/full/split_revert，另以第二seed独立进程复测；graph预热6块×50，正式5块×100，CUDA event完整调用耗时，另记含host的graph replay时间。末3warm、全部measure spread和baseline/revert drift均要求<=5%，保留所有轮，超限标incomplete而非挑轮。数值比较rtol.02/atol.002、两次变输入graph回放，记录max abs及逐位相等比例。先验证再计时；失败保留证据不改源码。

独立benchmark只使用物理0，要求8045原服务空闲且初始空闲显存>6GiB；检查每个case/role无模型请求。原服务及0–7所属模型保留，8–15无关工作负载不触碰。临时过程脚本及原始结果只放远端当前case，实际SHA见state.yml；不修改Plugin/FV/FG或全局启动脚本。

按冻结M顺序从M1开始，覆盖M64等常用配对完整调用。只有数值/graph、当前源码身份、实际dispatch命中均成立且微基准没有明显回退，才考虑后续模型接入和必要正式精度；完整入口改选是高风险路径变化，旧split模型gate不能冒充其新gate。本实验不预先保留候选。

## 安装原样结果

两个独立进程/seed105、106，第二进程反向full/split顺序。各角色5测量块×100次graph replay，统计先取进程内中位数，再取进程间中位数；2×14个case全部数值/变输入graph输出逐位一致。所有预热/测量/回退漂移均满足冻结5%范围，未删轮。

| M | 均匀路由 split μs | 完整入口 μs | 完整入口耗时变化 | 集中16专家 split μs | 完整入口 μs | 耗时变化 |
|---:|---:|---:|---:|---:|---:|---:|
| 1 | 39.354 | 56.052 | +42.430% | 39.380 | 56.158 | +42.605% |
| 8 | 202.275 | 214.578 | +6.082% | 132.459 | 132.930 | +0.355% |
| 16 | 350.955 | 390.015 | +11.130% | 142.089 | 134.820 | -5.116% |
| 32 | 676.317 | 742.854 | +9.838% | 161.323 | 143.363 | -11.133% |
| 64 | 664.911 | 666.732 | +0.274% | 144.811 | 146.533 | +1.189% |
| 1024 | 1725.632 | 1726.878 | +0.072% | 547.842 | 551.003 | +0.577% |
| 8192 | 3881.957 | 3884.222 | +0.058% | 3885.610 | 3886.016 | +0.010% |

正数为完整入口更慢。上述是合成固定路由、单卡TP后完整MoE计算链成本，不含TP通信、外层shared专家、调度或网络；不外推真实生产路由分布、不同量化或模型吞吐。小M原样base config不同（split BN64/BK128/group1 vs full BN256/BK64/group8），不能归因于Python单入口本身；M64/1024/8192经受限策略复用后基本持平。额外统一选参仅修改独立benchmark进程中的selector，原库与模型未改，作为机制归因，不能替换原样性能结果。

首个尝试严格策略接口误用在任何GPU用例前终止，零测量，原目录-01保留；修正测试脚本接口后用新-02目录按相同契约实测。不把测试编排错误归为模型/算子失败。

## 统一选参归因对照与结论

仅独立benchmark进程把Thead完整入口的base GEMM选择器替换为已安装Plugin的真实选择器；未修改任何安装文件或服务。M1/8/16/32、两路由、两独立seed/进程共16case，仍按同一6warm/5measure/回退/5%规则，全部数值及两次变输入graph逐位一致，实际base config相等。

| M | 均匀路由 split μs | 统一选参完整入口 μs | 耗时变化 | 集中16专家耗时变化 |
|---:|---:|---:|---:|---:|
| 1 | 39.338 | 41.089 | +4.450% | +4.351% |
| 8 | 201.204 | 202.900 | +0.843% | +1.232% |
| 16 | 349.085 | 350.793 | +0.489% | +1.166% |
| 32 | 675.570 | 677.937 | +0.350% | +1.143% |

原样与控制组合，最大正式块spread为1.037%，最大baseline/revert漂移0.431%，最大跨进程spread0.791%；均小于冻结5%。全部原始块保留，不把小于波动门槛的差异称为显著收益。

M1原样完整入口+42.43%，统一配置后+4.45%；其余小M统一配置后剩约1.6–2.4μs差异。控制实验支持“主要差距来自base GEMM策略”，但剩余量化/alignment等差异未逐kernel消融，不把剩余全部归因于Python调度。完整fused_experts_impl是量化、alignment、GEMM1、激活/量化、GEMM2和归约的完整编排API，不是自动合成一个GPU kernel；graph replay也不会因Python入口减少就自动减少设备工作。

决定：原样M64/1024/8192基本持平，小M依赖路由且存在回退，当前不把完整API切换为默认，不用额外全量GPQA或模型压测掩盖这个负/中性结果。保持用户已经过三项全量验证的split服务和原源码。模型端到端A/B为not_run，本表不含TP通信/调度/shared expert/网络，不声明模型吞吐变化。若后续以统一API为工程目标，应先在库的现有策略边界统一选参，再单独验证接入后的模型graph/精度与Prefill/Decode/Mixed。

## 证据与收尾

原样结果：`/mnt/nfs/users/jinghao/minimaxM3.1/optimize/20261021-minimax-m31-topk-sigmoid-tp8-accuracy/performance/perf002-full-vs-split-20261022-02`；统一配置归因：`/mnt/nfs/users/jinghao/minimaxM3.1/optimize/20261021-minimax-m31-topk-sigmoid-tp8-accuracy/performance/perf002-matched-selector-20261022-01`。各目录controller/result.json、seed105/result.json、seed106/result.json及逐块日志均保留。脚本、controller、主结果和seed结果SHA见[state.yml](state.yml)。前后source/compiler/package/cache核验通过；结束时同一原服务实例健康，running/waiting均0。所有micro进程已终态，没有新后台评测、性能队列或源码改动；此前精度监控继续PAUSED。

knowledge_delta=refined：完整入口与分步调用首先按真实GEMM策略和路由比较；API数量不是GPU融合或加速证据。只将此次限域micro写为reproduced，不扩展为模型收益或其他平台结论。

## 对“完整入口融合后为什么更慢”的源码复核

2026-10-22只读复核当前容器，无新GPU测量/trace、无源码变化。Plugin文件SHA61023d7a…c99c93c，FV文件SHA05000e71…2c4472a，完整SHA见state。

1. “分步”是Plugin的调用组织方式，并不意味着其内部都未融合。Plugin fused_moe.py240–248和FV Thead fused_moe.py2096–2126都调用同一try_swigluoai_uninterleave_quant_int8。当前测试BF16/width384、M×topk<=32768符合2669–2706的guard。因此两条测试路径都已有激活+quant2融合，这不是完整入口独有的新增收益。
2. 完整入口1929–1933的GEMM1+激活融合只允许SILU/SWIGLUOAI；当前是不同的SWIGLUOAI_UNINTERLEAVE，因此do_fuse_silu=False。不可把generic SiLU或其他布局的融合能力算到当前packed-OAI路径上。此结论为实际源码分支，不是profile证明的kernel计数。
3. 两者对当前shape的主要设备流程均为quant1→alignment→GEMM1→激活+quant2融合→GEMM2→sum。完整API是完整编排入口，仍启动多个GPU kernel；本轮整链graph replay计时不会因Python入口由多个变为一个自动省下设备工作。没有逐kernel trace，未宣称精确launch数。
4. 已证实的主因是base配置选择差异：小M split为BN64/BK128/group1，full默认BN256/BK64/group8。它改变N方向并行块和K方向分块循环，可能令小batch更差，也可能在集中路由时更快；具体occupancy/寄存器瓶颈尚无硬件profile，保持机制解释而非已证硬件计数。selector-only实际对照使M1差距从42.43%收窄至4.45%，数值保持逐位相同。M64/1024/8192命中既有受限配置后基本持平，与该解释一致。
5. 剩余1.6–2.4μs尚未逐kernel定因。full首次量化用新增_split_quant_int8（2542–2569），split沿用原moe_kernel_quantize_input；两者数值约定兼容不代表kernel调度/耗时相同。它是下一单变量证伪候选，不能未经测试把全部剩余归到量化、Python或融合寄存器压力。

当前证据支持“配置策略使现有完整入口在部分shape变慢”，不支持“融合本身无效/导致回退”。若统一API，首改应是兼容既有选参策略并保持融合与量化语义，再验证剩余量化实现；本次问题分析不自动修改产品或启动模型评测。
