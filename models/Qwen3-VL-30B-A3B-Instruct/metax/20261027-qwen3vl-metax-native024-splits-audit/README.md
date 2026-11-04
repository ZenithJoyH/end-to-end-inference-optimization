# 官方 vllm_metax 0.24 镜像 Attention splits 核验

核验本机官方tag对应的原始镜像manifest d080f0f3aa71…；registry独立重验鉴权失败，因此结论绑定该本机不可变摘要。

**仍复现auto0跨batch数值差异。** 六组同首序列B1/B8对照在split0下都有差，split1下均exact；真实rank0最大差2.44140625e-4。24项原FP64容差与16capture/48replay通过，不据此认定kernel语义错误或模型分数失败。没有完整模型/精度/性能评测。

原生调用链：platform entrypoint → MxsmlMacaPlatform → MacaFlashAttentionBackend → FlashAttentionImpl.forward → fa_utils → flash_attn → flash_attn_2_cuda.fwd_kvcache。默认Prefill/Decode分路开启，Prefill为paged varlen，Decode为kvcache且省略num_splits→默认0；querylength分桶路径也省略。实际fa_utils函数对象与被测native API一致。

[详细源码行号、验证结果与外部证据](optimize/op-001-vendor-attention-splits.md)。两临时容器已删除，GPU7释放，其他容器/原镜像未改。
