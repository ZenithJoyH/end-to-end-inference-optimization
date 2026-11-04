# diag-005：INT8 MoE FP32 分块累加的抵消精度诊断

op-003候选尚未部署。源码确认generic MoE在W8A8 per-channel情况下仍以FP32 accumulator逐Ktile累加整数dot。CPU合成强抵消输入显示数学整数sum=0，BK64/128/256可能分别-11/-5/+7；这只是CPU模拟，必须目标PPU核验。正式模型分数未失败，当前普通Worker基线保持，不能把该边界问题推定为当前模型下降。

最小复现仅合成INT8形状[E128,N768,K6144]、M64/8192、对称正负半向量，FP32 powers-of-two scales，CPU整数reference=0。固定absolute tolerance.001，在独立空闲PPU8比较当前generic/BK256，graph2及compiledIR；任何不符均冻结候选晋级，保存证据，先诊断/修复或回退。无用户数据/权重值读取，不影响0–7模型或外部客户端。

硬件确认：M64/seed0/BK128=-.00244140625、BK256=.00341796875；M8192/seed0/BK64=-.00537109375、BK256=.00341796875，CPU整数oracle均0；三个seed、eager三次和graph2完全匹配CPU逐tileFP32预测。Scope/source/model/root均保留。结果SHA3d9e3ba443683a908a19bdff56a005c1fbf1176b77bccecf50a52e8d1f5c3d74，scopeSHA1198831ee815ea0ebbb71db96d10df872a2710325f54d266f7ef44554f46fdca。原模型正式分数未失败，不能推定GPQA下降；本点候选严格operator回归失败，冻结并转fix-002。
