# Qwen3-VL / MetaX 采样算子归属迁移

2026-10-12；SOP0.40；acceptance_scope=diagnostic。模型为mx-59的qwen-vl容器内Qwen3-VL-30B-A3B-Instruct，源/独立验证容器及镜像/挂载/源码指纹门禁均有外部证据。任务是迁移既有采样实现并核对来源；没有正式模型精度或端到端验收。

原Plugin接入依赖vLLM中的未跟踪top_p_values_only_metax.py。先在独立qwen-vl-sampling-opt-20261012验证，再按用户源码调整指令回写qwen-vl：FlagGems-vllm提供apply_top_k_top_p API及MetaX backend，Plugin保留原开关/shape路由，vLLM tracked reference不变、工作区恢复干净。没有重启/停止源服务，用户既有MoE改动保留。

语义reference为vLLM ee0da84ab的apply_top_k_top_p_pytorch；计数排序与三个阈值kernel来自容器既有实验文件，原作者/生成过程没有Git证据。当前复用FlagGems排序kernel及基础操作，设备检查BF16无损性，任意FP32使用精确值排序，不允许Torch compute fallback。实现支持范围与依赖由实际MetaX测试限定，其他平台未实测。

49项算子测试（含目标M64/V151936和graph两次replay）及7项Plugin路由测试通过。旧算法尾部计数缺少valid mask在两个用例分别造成40/8192项差异；只补该mask后全部消失，迁移候选也与reference一致，属于已复现的算子正确性问题，不推断模型正式分数。

三轮同进程、无profiler、k20/p0.8、包含双方相同clone开销：目标BF16网格输入reference/candidate中位数28.6916/1.8757ms（逐轮加速比中位数15.296×）；任意FP32为28.7395/22.4789ms（1.278×）。这是对vLLM reference的算子级观察，不是对有边界错误旧实验的迁移收益，也不是端到端加速比。

模型服务C8、TP2两个worker、完整GPQA及P1K/P4K/P16K/P32K正式性能not_run/incomplete；pr_readiness=needs_revision。FlagGems内部sort JIT API依赖与非目标平台尚需进一步审阅。保留scope有限的代码迁移结果；没有提交、推送或创建PR。

[结构化记录](../../../models/Qwen3-VL-30B-A3B-Instruct/metax/20261012-qwen3vl-metax-sampling-migration/optimize/state.yml)、[单点迁移记录](../../../models/Qwen3-VL-30B-A3B-Instruct/metax/20261012-qwen3vl-metax-sampling-migration/optimize/op-001-sampling-library-migration.md)、[最初分析](../../qwen3vl-metax-topk-topp-analysis.md)。外部原件、最终两仓库补丁及回退入口均位于用户授权根目录下 /public-flash/jinghao/qwen3-VL/20261012-qwen3vl-metax-sampling-migration/，SHA见state。回退dry-run验证10个文件，拒绝覆盖后续修改，不自动重启服务。

后续只读 [MoE 补丁审查](../../../models/Qwen3-VL-30B-A3B-Instruct/metax/20261012-qwen3vl-metax-sampling-migration/optimize/op-002-moe-path-review.md) 确认：已有改动调用 MCTLLASS 替换 GEMM2，但当前默认 dispatch 解析选择 default.flagos，单独打开 vendor 模块开关不改变选择顺序。下一步优先验证显式 GEMM2 接入与命中，再分离 GEMM1 调参和融合候选。本轮未修改 MoE 源码或运行设备/模型性能实验。

按用户后续明确指令完成 [MoE 库来源切换](../../../models/Qwen3-VL-30B-A3B-Instruct/metax/20261012-qwen3vl-metax-sampling-migration/optimize/op-003-moe-library-switch.md)：Plugin 的 GEMM adapter 和 NVIDIA/no-LoRA 完整入口改为调用 FlagGems-vllm 公共 API。3 项接入检查、20 组 FP16/BF16 数值与每组两次 graph replay 通过，旧路径差异均为 0；部署后在 qwen-vl 验证实际来源和默认 dispatch 接入。仅修改两个 Plugin 文件，原 MCTLLASS/采样补丁、策略和 vLLM 保持不变，未重启服务，模型精度/性能未测。回退 dry-run 验证两个文件；没有启用 MetaX 完整融合或宣称新增性能收益。

2026-10-13 按用户进一步指令完成 [MetaX完整MoE接入](../../../models/Qwen3-VL-30B-A3B-Instruct/metax/20261012-qwen3vl-metax-sampling-migration/optimize/op-004-metax-full-moe.md)：当前无LoRA、原生浮点SiLU、默认输出端router权重、相关组件选择FlagOS时，直接调用FlagGems-vllm MetaX fused_experts_impl。21个设备场景、11路由检查通过；19非空场景各两次变化输入replay。原FULL_AND_PIECEWISE TP2模型服务完成capture、两个worker原生replay观测及18成功非空请求（2单请求+2轮C8）。必要修复包括库MetaX共享内存预算与paired变体能力保护、Plugin MetaX worker跳过不支持的NVIDIA warmup。三文件已回写qwen-vl，source来源/SHA与三文件回退dry-run通过，源服务未重启。量化/其他激活/LoRA/预加权输入/显式非FlagOS选择保留原路径。正式GPQA与端到端性能未测，不累计旧采样算子加速比。

2026-10-13 [旧开关移除与Worker必要性整理](../../../models/Qwen3-VL-30B-A3B-Instruct/metax/20261012-qwen3vl-metax-sampling-migration/optimize/op-005-remove-sampling-switch.md)：hook/测试/start-model.sh不再使用EXACT_TOPK_TOPP_M64开关；Worker保留已复现的预热兼容判断并删额外日志，完整MoE helper保留支持范围/既有策略约束。独立0/1卡49项算子、8项路由、实际hook graph及TP2/C8共18响应通过并回写qwen-vl，四文件回退dry-run通过。源4/5配置不变、源服务未重启；验证服务停止且0/1释放。正式GPQA/端到端性能未测。

2026-10-13后续整理：独立_can_use_metax_fused_experts已删除，原支持/策略条件内联到TritonExpertsFL.apply，净减15行；20项路由对照、2组MoE graph及独立TP2/C8 18请求通过并回写。Worker仅纠正注释：由NVIDIA模型入口导入、实际在common/ops/index_topk.py:82定义的_index_block_score_kernel，在81行jit装饰器解析时失败，尚未执行该kernel。当前回退入口为同案例commands/op005-inline/rollback.py；详细证据见op005 r2记录。

2026-10-13 [FlagTree升级可行性预检](../../../models/Qwen3-VL-30B-A3B-Instruct/metax/20261012-qwen3vl-metax-sampling-migration/optimize/op-006-flagtree-upgrade-review.md)：独立私有overlay的官方0.7.0.post2+metax3.6实际提供jit新参数，原MiniMax warmup导入passed；API错误可修复。未改变任一容器全局旧编译器/源Worker保护，未测新编译器算子或模型graph，正式升级另需回归。

- 2026-10-13：[op007 Worker/MoE 清理与默认 FlagTree 升级](../../../models/Qwen3-VL-30B-A3B-Instruct/metax/20261012-qwen3vl-metax-sampling-migration/optimize/op-007-worker-moe-cleanup.md)：独立graph/C8验证后回写；无正式精度/性能结论。

- 2026-10-13：[op008 上游未量化保证与重复判断清理](../../../models/Qwen3-VL-30B-A3B-Instruct/metax/20261012-qwen3vl-metax-sampling-migration/optimize/op-008-unquantized-entry-cleanup.md)：仅删除三行，独立数值/graph/真实worker配置/C8通过后回写。

- 2026-10-13：[op009 NVIDIA/MetaX 完整MoE统一审查](../../../models/Qwen3-VL-30B-A3B-Instruct/metax/20261012-qwen3vl-metax-sampling-migration/optimize/op-009-moe-unification-review.md)：共同契约可统一；四op检查有策略含义且不保护失败缓存，生产保持op008。

- 2026-10-13：[op010 MetaX按现有NVIDIA调用条件对齐](../../../models/Qwen3-VL-30B-A3B-Instruct/metax/20261012-qwen3vl-metax-sampling-migration/optimize/op-010-metax-nvidia-call-alignment.md)：独立graph/C8后回写；关闭MoE入口及native选择阻塞仅诊断，其他不改。

- 2026-10-13：[op011 官方MetaX镜像MoE来源检查](../../../models/Qwen3-VL-30B-A3B-Instruct/metax/20261012-qwen3vl-metax-sampling-migration/optimize/op-011-metax-official-image-moe-inspection.md)：新官方镜像无FlagOS依赖，默认OOT method选择MetaX专家，BF16两次GEMM实际进入MCTLLASS；USE_VLLM_TRITON_EXPERT=1选择镜像内vLLM专家，同shape设备调用通过。仅来源诊断，未测数学参考/graph/模型精度性能，未改qwen-vl。

- 2026-10-13：[op012 用户指定Plugin采样回退](../../../models/Qwen3-VL-30B-A3B-Instruct/metax/20261012-qwen3vl-metax-sampling-migration/optimize/op-012-revert-plugin-sampler.md)：source/clone均恢复原HEAD PyTorch fallback并移除新增Plugin测试，采样函数四组graph各两次变化输入replay通过；MoE/库/Worker未改，不重启服务。完整模型回归及正式精度性能未测。
