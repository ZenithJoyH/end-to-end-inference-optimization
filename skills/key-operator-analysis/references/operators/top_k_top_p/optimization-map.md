# Sampling 优化地图

| 信号与匹配键 | 首个实验、机制 | 晋级与停止 | 证据 |
|---|---|---|---|
| MetaX C550、FP32 contiguous M<=64/V151936，实际走8轮4bit radix，histogram占可见时间 | 对比逐桶比较与masked局部histogram，保持整数key、计数、grid、下游完全一致；先完整过滤逐位oracle | 非整批M、尾部V、仅一行非BF16、原始FP32位模式、tie/NaN/±0及变化输入graph均通过后，回父Mixed稳态B/C/R；任何掩码差异停止 | [C550案例](case-index.md)，reproduced，非跨平台 |
| 静态发现失败BF16 guard仍有无效计数 | 先量完整算子占比；跳过该局部工作，不同时改radix | 算子收益不足晋级门槛则不合入；不能以计数逻辑量推端到端 | 同案例约3%完整算子收益，未合入 |
| 想把radix桶分组8改16以少读输入 | 核验CTA并行度、循环长度和寄存器；单变量完整算子B/C/R | 小batch回归或M64无收益则停止；逻辑读取减少不代表硬件更快 | 同案例M1慢约24%，M64近无收益，反例 |
| 端到端收益与B/R漂移同量级 | 同时报告候选相对基线和回退、所有计时轮；核验实际采样默认值及seed含义 | 不以初始参考给较大的百分比冒充稳定孤立收益；正式精度另有gate | 同案例+3.76%vsB、+1.67%vsR，漂移2.06%；仅performance_only |

当前参数不外推至其他M/V、平台、FlagTree版本或compact-CDF算法。每次重新验证dispatch、稳态准入和模型目标workload。
