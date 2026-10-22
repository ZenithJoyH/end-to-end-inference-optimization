# Qwen3-VL / MetaX opt10 全量端到端记录

2026-10-22：归档用户在 mx-59/MetaX C550/TP2/GPU6,7 上的 opt10 完整人工结果，生产容器 `qwen3vl-p64k-opt-20261015`、9999。当前源码和服务保持不变。

最新CSV SUMMARY（1K为10月22日复测，其余为10月21日）：P1K/P4K/P16K/P32K/P64K的输出吞吐分别1511.12/1082.16/374.66/175.74/76.44 token/s，总吞吐3022.26/5410.82/6369.18/5799.26/4968.68 token/s；均D1024/C64/N128。1K新组及其余场景均取各自第3–4轮SUMMARY，全部原始轮次仍保留。

当前1K复测全4轮总吞吐差幅1.45%，用户已确认稳态；旧1K8轮63.49%波动及JIT诊断仍保留。4K历史差幅32.78%，16K/32K/64K均低于1%。本轮完整精度已通过：GPQA **130/198=65.66分**（阈值64），ERQA **162/400=40.50分**（阈值40），两项均通过。1K稳态确认；最终性能验收incomplete，不把完整场景覆盖等同于正式通过。

[模型最新记录](../../../models/Qwen3-VL-30B-A3B-Instruct/metax/20261022-qwen3vl-metax-opt10-results/README.md)；[全部指标、逐轮结果与SHA](../../../models/Qwen3-VL-30B-A3B-Instruct/metax/20261022-qwen3vl-metax-opt10-results/optimize/records-008-opt10-full-results.md)；[平台导航](../../../models/Qwen3-VL-30B-A3B-Instruct/metax/README.md)。

外部快照：`/public-flash/jinghao/qwen3-VL/20261022-qwen3vl-metax-opt10-results/results/opt10-full-import.json`，SHA `ef8e4e33bcfe3bf2bcb16377fb6e1cc38fb509e0178d9fc009ddb484e7574b50`。

新1K完整回执：`/public-flash/jinghao/qwen3-VL/20261022-qwen3vl-metax-opt10-results/results/opt10-p1k-confirmed.json`，SHA `b995ae48fa803b2236fe87ac3cbe839ea6d62f1873e7eb38f92d04dfa38c693e`。

[本轮GPQA与ERQA精度证据](../../../models/Qwen3-VL-30B-A3B-Instruct/metax/20261022-qwen3vl-metax-opt10-results/optimize/acc-009-gpqa-erqa.md)。
