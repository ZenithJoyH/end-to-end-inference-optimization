# mx-59 qwen-vl：top-k/top-p 优化分析

2026-10-12，只读源码与历史证据分析。用户要求先分析已有优化；本轮未修改远端源码、启动/停止服务、运行性能或精度实验。结论为 observation，不签发验收或精度 gate。

## 核验对象与来源

- Host：inventory 中的 mx-59，项目 connectivity-check 已通过。
- 容器：qwen-vl；镜像引用 harbor.baai.ac.cn/flagos-inner-models-release/qwen-vl-metax:latest。
- 启动脚本：容器内 /public-flash/jinghao/qwen3-VL/start-model.sh；指定 Qwen3-VL-30B-A3B-Instruct、TP2、BF16、max-num-seqs=64、FULL_AND_PIECEWISE graph，并开启 VLLM_FL_METAX_QWEN3VL_EXACT_TOPK_TOPP_M64。
- vLLM：/workspace/vllm，HEAD ee0da84ab9e04ac7610e28580af62c365e898389；新增未跟踪文件 vllm/v1/sample/ops/top_p_values_only_metax.py，tracked diff 为空。
- Plugin：/workspace/vllm-plugin-FL，HEAD 4d4645b33627f0859e4b2d0be319bedc4562932d；采样 patch 与 fused_moe.py 有已有改动。
- FlagGems：/workspace/FlagGems，HEAD 2a52f9535ddf6e49d6df641f26eafec3f0d1ef23；大量已有工作区差异，未覆盖或整理。
- 历史命中证据：/public-flash/jinghao/qwen3-VL/service.log，第 280–281 行，2026-10-12 14:44:29，两个 TP worker 均输出 “Using exact Qwen3-VL M64 counting top-k/top-p dispatch”。这是历史命中，不能替代当前进程证明。本轮进程检查未发现运行中的 vLLM 服务；日志后段有 EngineDeadError，其原因未在本分析中定位，不归因于采样优化。

## 原路径与优化机制

实际接入点已在 Plugin 的 vllm_fl/dispatch/backends/vendor/metax/patches/topk_topp_sampler.py 中：替换 vLLM 模块的 apply_top_k_top_p 函数。原 Plugin patch 的注释记录 vLLM Triton 采样 kernel 在 MetaX 编译失败，因此强制使用 apply_top_k_top_p_pytorch。本轮未复现该历史编译错误。

vLLM 原路径位于 vllm/v1/sample/ops/topk_topp_sampler.py:363–404：升序排序 logits，同时生成 token 索引；按第 V-k 个值做 top-k 严格小于阈值的屏蔽；计算 softmax 和累积概率，移除累积概率 <= 1-p 的低概率前缀，至少保留一个 token；最后按索引 scatter 回原词表顺序。

新增实现位于 top_p_values_only_metax.py:171–305，实际命中的是 apply_exact_top_k_top_p_values_only，机制如下：

1. 假设输入 FP32 logits 的每个值都可无损表示为 BF16。将其编码为保持大小关系的 16 位整数 key。
2. 按每行 65536 个桶进行 scatter_add 计数，再对桶计数做 cumsum，通过 searchsorted 展开完整升序值数组。依然生成完整排序值数组，但不再生成和搬运排序 token 索引。
3. 从排序值中取 top-k 阈值并屏蔽，再执行 softmax/cumsum。top-k/top-p 复用同一排序结果；原路径本来也只排序一次，不能将收益描述成“合并两次排序”。
4. Triton 二分查找 top-p 的第一个保留位置，以阈值回到原 logits 直接做 mask。通过统计小于阈值和等于阈值的数量，并为等值项按原 token 顺序计数，尝试复现稳定排序在 top-p 边界的 tie 行为。

主要收益机制是更换排序算法、减少排序索引与 associated value 的搬运、移除最终索引 scatter。启用 FlagGems sort 时，原实现为 FP32 的 4-bit radix sort，共 8 pass，每轮同时搬运值与 int64 索引，并有 status/lookback 同步；候选计数路径避免这些多轮重排。候选仍有多个 PyTorch 操作、临时张量与 Triton launch，不是单 kernel 融合，也没有替换后续随机采样/RNG。

文件中的 _radix_sort_values 是未被当前两个 apply 函数调用的备用实现，不能按它解释实际候选收益。注释提到的“four passes”也不能代替上述 FP32 原路径的 8-pass 代码事实。

## 当前支持条件与正确性缺口

Plugin 仅在实验开关为 1、k/p 都存在、logits.dtype 为 FP32、shape 为 (64,151936)、k/p.shape 为 (64,) 时调用候选，否则回到原 PyTorch fallback。它没有验证 BF16 无损前提、连续 layout、k/p 的 dtype/device/有效值等完整契约。实际 batch 变为 63 等形状后会回退；并发上限 64 不等于所有采样步都是 M64。

最重要的缺口是无损 BF16 前提：vllm/v1/sample/sampler.py 先把 logits 转成 FP32，随后执行 logits processor、penalty、temperature 等操作，才进入 top-k/top-p。模型 BF16 并不能证明这个调用点的 FP32 值仍落在 BF16 网格上。任意 FP32 值被候选转换为 BF16 会舍入，可能改变排序、概率累积与筛选边界；“exact”是有前提的性质。

另一个静态可见的风险是 _threshold_counts:55–59：masked load 后，小于阈值的计数没有与 valid 相与；当前词表 151936 除以 block_n=256 有 128 个尾部无效 lane。须用边界测试证明这些 lane 不会污染 total_less/tie_remove_count，或显式屏蔽。此项尚未执行数值复现，不能报告为已确认的输出错误。

稳定 tie 的目标也须与实际 reference 绑定：vLLM 调用 sort 时没有显式 stable=True；当前 FlagGems sort 实现注释与代码采用稳定 radix，但不能将这种等值顺序承诺直接推广到所有 backend。

## 性能阶段与工程归属

采样发生在模型 logits 产生之后。机制上，Decode 每生成一个 token 都可能执行该路径，因此预期首先减少每步采样开销并改善 TPOT/输出吞吐。Prefill 完成后的首 token 采样也可能受益，但不直接加速 attention/GEMM；Mixed 的净收益取决于真实 M64 命中率、GPU 资源占用、调度与回退成本。没有本轮阶段计时，不能量化这些收益。

按项目分类属于 operator/improve：对采样过滤算子做算法特化。Plugin 接入是该算子优化的必要组成，不额外计为 framework 收益。

当前问题是 Plugin 已负责入口，却从 vLLM 命名空间导入平台专用实验实现，导致 Plugin 隐式依赖一份修改后的 vLLM 源码。合理边界是：Plugin 管理入口、支持条件、实现选择与 fallback；实现可放在 Plugin 的 MetaX backend，或在完善契约后沉淀为 FlagGems/FlagGems-vllm 中的采样算子。vLLM 保留原调用与 reference。当前普通函数入口并未在已读代码中体现 OOT 注册点，迁移不能假设直接套用 CustomOp.register_oot；必要时沿用范围受控、幂等的现有 Plugin patch。

仅移动文件不能消除 BF16 前提和边界风险。形成候选前应先明确支持语义，覆盖温度/penalty、等值边界、mask/-inf、非连续 layout、batch 与词表尾部；再验证 graph 和同 workload 的 baseline/candidate/revert。pr_readiness=needs_revision。

## 后续只读复核：两个算子仓库是否已有实现

用户追问后重新检查了当前 qwen-vl 容器。环境已有变化：FlagGems 当前 HEAD 为 9beec73856969aec8268a7a22788a17a119211fb，安装版本 5.5.0.dev0+g9beec7385；FlagGems-vllm 当前已存在于 /workspace/FlagGems-vllm，HEAD 为 f6fdb9b120787e12892ac67e54979cbf829c7d64，安装版本 0.3.0.dev1。两者 editable 安装指向对应源码目录，git 工作区均干净。前面的旧 revision 保留为首次检查事实，不与本次快照混用。

搜索两个仓库的 Python 实现与导出，未找到完整 top-p/top-k 采样过滤或本次 apply_exact_top_k_top_p_values_only、_counting_sorted_values 实现。FlagGems 已有 topk、sort、softmax、cumsum、searchsorted、multinomial 等基础算子；FlagGems-vllm 已有 topk_softmax、grouped_topk、persistent_topk、top_k_per_row_decode/prefill 等算子，但它们不实现本次基于概率累计阈值的 top-p 过滤，不能直接等同。

当前 Plugin 仍从 vLLM 的 top_p_values_only_metax.py 导入候选。因此可以称为新写的复合采样过滤算子实现：复用基础操作，并新增 first-keep 查找、阈值计数、稳定 mask 三个 Triton kernel；它不等于新写了所有基础 kernel，也不是完整的随机采样算子。

## 已有性能材料的结论边界

查看了 /public-flash/jinghao/qwen3-VL/test/perf_test 下的日志。perf.log 为 qwen3vl-final，使用当前组合优化；perf-base.log 与 perf-begin.log 的 model/tokenizer 则是 Qwen3.6-27B，不能与 Qwen3-VL 计算同模型加速比。当前启动脚本还同时开启 MoE GEMM2 特化与调优配置，因此组合结果也不能单独归因于 top-k/top-p。本轮没有获得该优化点同条件 A/B/revert 或正式精度证据。

## 本轮迁移结果

用户随后授权调整源码。已在独立容器验证并回写qwen-vl，vLLM仅移出原未跟踪实验文件，参考实现保持原样。新实现进入FlagGems-vllm MetaX backend；BF16前提通过设备校验保护，任意FP32走精确值排序。尾部mask风险已用原代码单变量复现并确认，修正后对拍一致。49项算子与7项Plugin测试通过，模型正式精度/端到端性能未测。详见 [迁移案例](cases/20261012-qwen3vl-metax-sampling-migration/README.md) 与其结构化证据。

## 2026-10-13 整理更新

最初分析的实验开关已从生产采样hook、测试和start-model.sh移除，按既有shape/dtype/layout自动选择库API，其他输入仍走reference。49项算子/8项路由、实际hook graph及独立TP2/C8通过并回写；验证使用用户释放的0/1，源4/5不变。Worker兼容判断已精简、完整MoE helper保留。详见[op005记录](../models/Qwen3-VL-30B-A3B-Instruct/metax/20261012-qwen3vl-metax-sampling-migration/optimize/op-005-remove-sampling-switch.md)。前文为此前事实；历史补丁/回退备份中的旧字符串不参与当前执行。

2026-10-13后续整理：独立_can_use_metax_fused_experts已删除，原支持/策略条件内联到TritonExpertsFL.apply，净减15行；20项路由对照、2组MoE graph及独立TP2/C8 18请求通过并回写。Worker仅纠正注释：由NVIDIA模型入口导入、实际在common/ops/index_topk.py:82定义的_index_block_score_kernel，在81行jit装饰器解析时失败，尚未执行该kernel。当前回退入口为同案例commands/op005-inline/rollback.py；详细证据见op005 r2记录。
