# 分页KV gather：物理stride与地址宽度

KV gather的逻辑view大小不代表其物理地址跨度。多层交错的cache可有很大的页stride；地址上界应按实际物理block ID、stride、页内offset和指针元素单位计算。FP8值和FP32 scale用不同单位，后者int32的2^31元素边界对应约8GiB。应在乘法前提升索引，不能依靠有效token mask修复有效行的整数回绕。

gather也依赖cu_seqlens定位批次。upper_bound搜索区间包含B+1个前缀；测试应包含B+1为2幂的边界、非对齐序列、带padding stride、输出哨兵和graph replay。这里不宣称支持任意不符合API约定的内部stride。

实测限制及证据见[案例卡](case-index.md)，排查顺序见[优化地图](optimization-map.md)。当前仅MetaX C550/DeepSeek-V4 Flash FP8 indexer复现，不以算子数值通过替代新模型正式精度，亦不把无崩溃等同吞吐稳态通过。
