# 关键算子知识索引

只读取当前问题需要的材料。所有代码文件都是历史源码快照，使用前必须与目标环境的实际 revision 对照。

## 通用方法

- [operator-analysis-method.md](operator-analysis-method.md)：定义、理论性能建模、源码到 Kernel 的调用链、benchmark、profiling、优化验证与报告规范。新算子或完整分析任务优先阅读。
- [case-to-knowledge.md](case-to-knowledge.md)：实际端到端案例结束后，将完整案例提炼为算子证据卡、优化地图和稳定理解的规则。关闭算子优化案例时必须阅读。

## mHC

- [operators/mhc/README.md](operators/mhc/README.md)：mHC 数学语义、Prefill/Decode 特征、带宽与 launch 瓶颈、post+pre fusion、graph-friendly 调度和验证矩阵。

当前没有完成的 mHC 实测案例卡。不要把理论候选当作目标平台已验证知识；首个实际案例完成后再创建 case index 和 optimization map。

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

## 快速使用顺序

1. 用 profiler 和运行时 dispatch 证据确定具体算子与实现。
2. 读算子 `README.md` 建立语义、数据流和性能模型。
3. 读 `optimization-map.md`，按当前有效 shape 和环境选首个可证伪实验。
4. 只打开 map 所链接的匹配案例卡；需要命令、patch 或完整结果时再进入 `docs/cases/`。
5. 案例完成后按 `case-to-knowledge.md` 回写知识差量。
