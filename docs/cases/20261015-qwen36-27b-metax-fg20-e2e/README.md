# Qwen3.6-27B / MetaX / 当前20FG端到端优化

mx-59/TP2/C550/GPU2,3，原启动脚本20FG、FP32 GDN、.002/.02不变。独立容器由有效快照a6d57a99复刻、mountparity通过；源18002仅按授权暂停恢复，源8002与其他任务不动。

OP002真实ABI packed W4虽完整调用快8.29%，三阶段Decode+1.39%/Mixed+1.33%<2%，已撤回。随后完整Mixed trace复现FG full新小整数尺寸在线调优引入约1.5s preprocess；OP003固定FG full路径通过194数值/16replay及微测，新baseline Mixed输出spread0.1794%通过10%。

共同OP003前提下metadata候选新B/C/R全部完成87轮/27measured/9408请求0失败：PF+0.5804% passed、Decode观察+0.2495%但baseline平均TTFTspread13.4452% incomplete、Mixed+0.2646%未达2% failed。最大B/R决策指标漂移0.998445%仍在1%内；全部慢轮保留，不能将微测或暖轮当端到端收益。

Decode历史慢轮在早期2.203s输出暂停内新编译GDN H kernel，source→binary约0.616s；9个不同cache目录具有完全一致lowered source与binary。FP32只剩固定tile但N_BUCKET/SKEW_BUCKET仍进入constexpr/autotune key，动态首批未覆盖key是重复JIT的强证据。历史精确bucket/rank停顿不可恢复，未追加模型请求或修改GDN。单一吞吐暖轮准入不能证明TTFT/key覆盖稳态。

原Plugin/full/四仓与source18002已精确恢复、full20不变，模型仍使用重新下载且原25SHA相等的新路径；候选只归档，监控暂停。当前20无正式198gate/四场景验收，无推送。下一方向是FP32无用JIT分桶键的限域验证，尚未执行。

[模型事实](../../../models/Qwen3.6-27B/metax/20261015-qwen36-27b-metax-fg20-e2e/README.md) · [FW002最终回退与TTFT诊断](../../../models/Qwen3.6-27B/metax/20261015-qwen36-27b-metax-fg20-e2e/optimize/framework-002-mixed-batch-overlap.md) · [OP003](../../../models/Qwen3.6-27B/metax/20261015-qwen36-27b-metax-fg20-e2e/optimize/op-003-metax-full-small-integer.md)
