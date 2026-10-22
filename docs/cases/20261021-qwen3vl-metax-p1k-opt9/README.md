# Qwen3-VL MetaX opt9 P1K 稳态

2026-10-22：[opt10全量端到端结果已归档](../20261022-qwen3vl-metax-opt10-results/README.md)，本页保留GPU0/1受控优化及历史诊断证据。

算子对比已完成：[op-007 main.py vs原生](../../../models/Qwen3-VL-30B-A3B-Instruct/metax/20261021-qwen3vl-metax-p1k-opt9/optimize/op-007-fa-main-native-micro.md)。18/18数值与graph通过，当前候选在全部已测shape上慢于原生；B64/KV1K为133.75 vs66.20μs。仅单卡每rank形状的graph设备计时，候选未部署，GPU2已释放。

补充：[main.py Flash Attention 源码对比](../../../models/Qwen3-VL-30B-A3B-Instruct/metax/20261021-qwen3vl-metax-p1k-opt9/optimize/analysis-006-main-flash-attention.md)。复核既有 trace 为原生 mcFlashAttn；候选尚未接入或测量。

2026-10-21 用户授权释放GPU并恢复验证。独立TP2/GPU0/1容器通过镜像谱系、挂载、graph与最小回归；Prefill/Decode/Mixed 双rank trace已完成。

跳过无效BF16计数仅约3%完整算子收益，sweep分组16无收益且小batch变慢，均未合入。局部整数histogram在M64完整采样约7.53→6.47ms，位级与graph通过，已保留回写。P1K/D1K/C64/N128两轮计时中位：基线1455.10、候选1509.86、回退1485.06tok/s，较基线+3.76%、较回退+1.67%，有2.06%时间漂移，不将3.8%当稳定孤立收益。其余源码/配置不变，正式GPQA依用户要求暂缓。

回写后四仓审计仅一个采样文件变化。回写当时9999未重启；后续用户重启为opt10，验证18144仍停止。opt10只读诊断将大波动收敛到未覆盖batch M的采样JIT，生产启动脚本未包含受控验证的M1…64采样预热；当前不宣称八轮均为稳态。见模型案例中diag-006。47组输入/129次过滤对拍、5次算子capture/20次变化输入replay及三个TP2服务回归通过。未提交/推送。

[模型案例与实验总览](../../../models/Qwen3-VL-30B-A3B-Instruct/metax/20261021-qwen3vl-metax-p1k-opt9/README.md)。远端原始产物：/public-flash/jinghao/qwen3-VL/20261021-qwen3vl-metax-p1k-opt9。
