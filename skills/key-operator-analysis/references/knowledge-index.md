# 关键算子知识索引

只读取当前问题需要的材料。所有代码文件都是历史源码快照，使用前必须与目标环境的实际 revision 对照。

## 通用方法

- [operator-analysis-method.md](operator-analysis-method.md)：定义、理论性能建模、源码到 Kernel 的调用链、benchmark、profiling、优化验证与报告规范。新算子或完整分析任务优先阅读。
- [case-to-knowledge.md](case-to-knowledge.md)：实际端到端案例结束后，将完整案例提炼为算子证据卡、优化地图和稳定理解的规则。关闭算子优化案例时必须阅读。

## mHC

TP通信首差异定位另见[TP allreduce限域证据卡](operators/tp_allreduce/case-index.md)：Qwen3.8-Flash-Next/PPU TP8 BF16完整目标行在归约前相同、归约后不同；不与下列Sinkhorn mHC性能案例混用，不把FP64单次舍入reference差异直接称通信bug。

- [operators/mhc/README.md](operators/mhc/README.md)：mHC 数学语义、Prefill/Decode 特征、带宽与 launch 瓶颈、post+pre fusion、graph-friendly 调度和验证矩阵。
- [operators/mhc/optimization-map.md](operators/mhc/optimization-map.md)：mHC Decode backend 替换的首个实验、端到端晋级证据和停止条件。
- [operators/mhc/case-index.md](operators/mhc/case-index.md)：GLM-5.3-Flash/PPU 上单算子 5.528× 但 P1K 吞吐下降的反例证据卡。

当前实测知识只覆盖 GLM-5.3-Flash、PPU、TP16、`hc_mult=4`、`hidden=4096`
和 P1K/D1K graph workload。不要把该负优化外推到其他平台、shape 或 post+pre fusion。

适用关键词：`mHC`、`MHCPreOp`、`MHCPostOp`、`MHCFusedPostPreOp`、`HCHeadOp`、`Sinkhorn-Knopp`、multi-stream residual。

## MLA Attention

- [operators/mla_attention/README.md](operators/mla_attention/README.md)：稳定 MLA 理解，涵盖 latent KV、decoupled RoPE、Prefill/Decode 分流、dense/sparse MLA、backend 与理论优化方向。
- [operators/mla_attention/optimization-map.md](operators/mla_attention/optimization-map.md)：由真实案例提炼的症状、匹配条件、首个实验、停止条件和待验证前沿。开始 MLA 优化时在 README 后读取。
- [operators/mla_attention/case-index.md](operators/mla_attention/case-index.md)：MLA 实际案例证据卡。只读取与当前 stage、有效 per-rank shape、dtype、backend、硬件和执行模式匹配的卡片。
- [operators/mla_attention/FEISHU_SUMMARY.md](operators/mla_attention/FEISHU_SUMMARY.md)：适合快速了解结论和对外沟通的精简版，不代替完整分析。
- [operators/mla_attention/research/deepseek_v2.pdf](operators/mla_attention/research/deepseek_v2.pdf)：DeepSeek-V2 论文原文；需要核对公式、实验设置或原始表述时读取。
- [operators/mla_attention/research/deepseek_v2_summary.md](operators/mla_attention/research/deepseek_v2_summary.md)：DeepSeek-V2 论文方法、公开结果和不能直接外推到单 Kernel 的限制。

固定 vLLM 源码快照：

- [MLA 公共层](operators/mla_attention/research/vllm_vllm__model_executor__layers__attention__mla_attention.py)
- [DeepSeek-V2/V3 模型实现](operators/mla_attention/research/vllm_vllm__model_executor__models__deepseek_v2.py)
- [FlashInfer MLA backend](operators/mla_attention/research/vllm_vllm__v1__attention__backends__mla__flashinfer_mla.py)
- [FlashMLA backend](operators/mla_attention/research/vllm_vllm__v1__attention__backends__mla__flashmla.py)
- [Triton MLA backend](operators/mla_attention/research/vllm_vllm__v1__attention__backends__mla__triton_mla.py)
- [FlashMLA ops wrapper](operators/mla_attention/research/vllm_vllm__v1__attention__ops__flashmla.py)

适用关键词：`MLA`、latent KV cache、decoupled RoPE、weight absorption、FlashMLA、FlashInfer MLA、Triton MLA、DSA、sparse attention。

一般分析先读论文摘要；只有摘要不足以支持结论时再读取 PDF 原文。

## Flash Attention / packed GQA

- [optimization-map](operators/flash_attention/optimization-map.md)：逻辑/物理 KV 页、真实 dispatch 命中、splits/warps 与 spill、Mixed 稳态停止条件。
- [case-index](operators/flash_attention/case-index.md)：Qwen3.6-27B/MetaX C550 的限域算子收益和候选 Mixed 未完成反例；不外推其他硬件、模型或页映射。

## Top-k / top-p sampling

- [README](operators/top_k_top_p/README.md)、[优化地图](operators/top_k_top_p/optimization-map.md)、[证据卡](operators/top_k_top_p/case-index.md)：MetaX values-only sampling中实际BF16/radix分支、局部整数histogram、桶分组反例与小收益的回退漂移判读。仅C550/FlagTree3.6.0/Qwen3-VL TP2限域证据，正式GPQA未做。

## Sparse indexer prefill top-k

- [证据卡](operators/indexer_topk/case-index.md)、[排查地图](operators/indexer_topk/optimization-map.md)：MetaX C550上多轮Mixed中的精确stride copy JIT变体、保留合法行pitch的wrapper修复，以及三轮P32稳定性验证。该路径选择attention索引，与词表sampling分开。未新增完整GPQA或跨平台验证。

## Fused MoE

- [operators/fused_moe/optimization-map.md](operators/fused_moe/optimization-map.md)：按
  stage、有效 M、expert 数、dtype 和 graph 模式匹配的候选与停止条件。
- [operators/fused_moe/case-index.md](operators/fused_moe/case-index.md)：Fused MoE 端到端
  实测证据卡；当前包含 GLM-5.3-Flash/PPU 的小 M Decode 特化边界。

当前限域证据覆盖 GLM-5.3-Flash/PPU/TP16/BF16 的 cached32 与 cached64
Decode。M<=32 和 exact-M64 GEMM2 已分别获得同 workload 服务收益；exact-M64
GEMM1 的最佳中位加速仅 1.0485×，未过 1.05× 算子门槛。不得把这些配置外推到
其他模型、平台、dtype、专家数、量化路径或 Prefill shape。

适用关键词：`fused MoE`、`invoke_fused_moe_triton_kernel`、GEMM1/GEMM2、
small-M Decode、stage config、expert routing。

## FP8/FP4 MQA logits

- [operators/fp8_fp4_mqa_logits/optimization-map.md](operators/fp8_fp4_mqa_logits/optimization-map.md)：
  跨仓库迁移后的 runtime/tune-config 来源核验、冷 shape、graph 与数据库判读规则。
- [operators/fp8_fp4_mqa_logits/case-index.md](operators/fp8_fp4_mqa_logits/case-index.md)：
  GLM-5.3-Flash/PPU 上 144 候选在线调优导致 RPC timeout，以及切换到
  FlagGems-vllm 单配置后的修复证据。

适用关键词：`fp8_fp4_mqa_logits`、sparse-indexer MQA、`libtuner`、
online autotune、tune-config runtime、cold shape、worker RPC timeout。

## MM 派发、布局与请求内调参

MM请求内调参、Config bucket与raw BenchmarkCache的区别另见[MM诊断地图](operators/mm/optimization-map.md)及[证据卡](operators/mm/case-index.md)：GLM-5.3-Flash/PPU的M20481/8198冷bucket触发104候选搜索、缓存正常写回；仅机制诊断，不是数值kernel或性能修复通过。

DeepSeek-V4-Flash/MetaX的BF16→FP32投影另验证了高层router primitive绕过vendor、转置权重实体化及native NT接入：同一地图/证据卡给出实际派发、输出dtype、stride与graph的首个检查。op004阶段的新GPQA与三轮P32通过当轮契约，彼时第三轮仍有非copy/GEMM的raw-M特化编译；不外推PPU调参机制或其他平台速度。

后续[op005 MM证据卡](operators/mm/case-index.md#deepseek-v4-flash--metax去除量化等边界特化后残余nt编译仍在)补充：量化/padding等原7项已消除，第三轮BF16 NT新编译与慢段仍在；运行时bounds、tile/EVEN cache键、选参benchmark须分开核验，不能把标量5%通过当完全预编译覆盖。

## QSA sparse GQA

- [operators/qsa_sparse_gqa/optimization-map.md](operators/qsa_sparse_gqa/optimization-map.md)：
  小 query-head tile 特化的生产 rows 门槛、首个实验和停止条件。
- [operators/qsa_sparse_gqa/case-index.md](operators/qsa_sparse_gqa/case-index.md)：
  Qwen3.8-Flash-Next/PPU 上 literal-four-lane 候选在 rows64 加速、但在
  生产 rows4096 退化的反例证据。

当前限域证据覆盖 PPU/TP8/BF16、query heads 3、head dim 256、
TOPK 2051 和现有 online-softmax/dot 组织。rows64 的 21.659% graph 收益
不能外推到 rows4096；生产 rows4096 graph 实测退化 4.563%。

另有 MiniMax-M3.1/PPU/BF16/GQA8 的正确性机制卡：当前 Triton 3.6.0 的 M8 A ldmatrix K位遗漏，经原始→A-only IR修正→原始证明。该卡不增加性能结论，也不将编译问题外推到其他shape/dtype/revision。

适用关键词：`QSA`、`sparse GQA`、`GROUP_SIZE=3`、`BLOCK_M`、
paged KV、logical TOPK、query-head padding。

## PLE short-conv 状态地址

[证据卡](operators/ple_short_conv/case-index.md)及[排查图](operators/ple_short_conv/optimization-map.md)：独立state kernel遗漏乘前i64，不能以输出或通用index已修复代替逐kernel审计；本例stride204800边界10486，离线驱动匹配、未GPU修复验证。

## Conv3d 启动预热

- [case-index](operators/conv3d/case-index.md)：MiniMax-M3/PPU-13的399360 patch大规模视觉预热，冷autotune约16分钟后自然完成；区分慢候选扫描与永久死锁。仅诊断观察，不是请求Prefill/Decode或已验证优化配置。

## randn / 大N输出地址

- [case-index](operators/randn/case-index.md)：Qwen3.8-Flash-Next/PPU startup合成BF16 N6400030720，输出偏移先i32溢出后扩位的缺陷；固定版数值/边界/graph及startup通过，不是模型精度gate。
- [optimization-map](operators/randn/optimization-map.md)：分别检查RNG计数与store地址，危险原实现用有界地址探针，固定版再做完整覆盖/canary/参考/graph；不按同步上报栈直接认定首错kernel。

## 快速使用顺序

KPool尾页graph输入生命周期另见[证据卡](operators/kpool_cache/case-index.md)和[排查图](operators/kpool_cache/optimization-map.md)：GLM-5.3-Flash/PPU公共路径开放FULL后，capture外临时槽位映射未原地址刷新、释放可复用；合法地址下复现旧尾块写入。仅诊断机制，未生产修复/新模型gate，不否定PR默认eager边界。

1. 用 profiler 和运行时 dispatch 证据确定具体算子与实现。
2. 读算子 `README.md` 建立语义、数据流和性能模型。
3. 读 `optimization-map.md`，按当前有效 shape 和环境选首个可证伪实验。
4. 只打开 map 所链接的匹配案例卡；需要进一步证据时，从 `docs/cases/` 的摘要链接到对应模型/平台的 `baseline/`、`optimize/` 或 `acceptance/` 主记录，原始大产物按其中的外部路径查阅。
5. 案例完成后按 `case-to-knowledge.md` 回写知识差量。

## GDN / Gated Delta Rule

- [README](operators/gdn/README.md)：实际export的state ABI、量化后输入参考和state精度边界。
- [optimization-map](operators/gdn/optimization-map.md)：舍入消融、慢衰减多chunk回归及正确FP32链的性能证伪。
- [case-index](operators/gdn/case-index.md)：Qwen3.6-27B/MetaX的布局纠错、精度不足修复与失败项；模型GPQA/E2E收益未测。

## Fused MoE 配置语义

- [README](operators/fused_moe/README.md)：配置格式、阶段覆盖与执行路径的边界。
- [optimization-map](operators/fused_moe/optimization-map.md)：更换配置后性能持续下降时的首个检查和单变量证伪。
- [case-index](operators/fused_moe/case-index.md)：Qwen3-VL/MetaX旧stage覆盖与新完整表的差异；性能贡献未独立量化。


## 分页KV cache gather

- [稳定理解](operators/kv_cache_gather/README.md)、[排查地图](operators/kv_cache_gather/optimization-map.md)、[证据卡](operators/kv_cache_gather/case-index.md)：大物理页stride下FP32 scale地址32位溢出、B+1搜索边界、同名跨库dispatch核验，以及无内存错误但吞吐测量仍不稳的限域证据。

当前仅MetaX C550/DeepSeek-V4 Flash FP8 indexer复现；不外推其他平台的性能或模型正式精度。

DeepSeek-V4-Flash/MetaX 后续 NT 调查已在同一 [MM地图](operators/mm/optimization-map.md) / [证据卡](operators/mm/case-index.md#deepseek-v4-flash--metaxnt候选试跑与configcache分桶)验证真实请求的 Default 精确M配置miss与6候选试跑；有界log-M与形状域准备消除三轮NT JIT/cache写入。保持原始BenchmarkCache和实际EVEN条件；当前三轮通过5%稳定性，但仍有index/mHC2编译，不能升级为全链路零JIT或其他模型/平台结论。
