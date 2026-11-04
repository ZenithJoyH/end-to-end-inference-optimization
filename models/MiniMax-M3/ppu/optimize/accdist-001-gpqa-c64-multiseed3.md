# accdist-001：GPQA C64 多 request-seed 分布评测

## 目的与范围

- 用户选择保留 sampling 语义，以多次/多 seed 分布而非单次分数复核 GPQA 精度。
- 评测组件模式：`inference-accuracy-evaluation/formal-gate`，每个 seed 使用维护版 formal wrapper 运行全量 198 题；聚合层是 `diagnostic_distribution`，不签发新的 schema-3 formal gate。
- 覆盖候选：`fw-006-flaggems-targeted-schema-reflection`。
- 服务：PPU-07 / `minimaxM3-opt-20260921` / port 8023 / `bd37abcbf719:8023:588850:273180627`；不重启服务。

## 预冻结契约

- 数据/任务：`gpqa_diamond_generative_cot`，198 个唯一问题，`exact_match,strict-match`。
- 请求：C64，`temperature=1,top_p=0.95,top_k=20,max_gen_toks=30000`。
- lm-eval seed 固定为 42，保持题目/选项构造不变；只显式改变 API request seed：`1234, 2026, 3407`。
- 已在规定评测容器中无模型请求验证：`gen_kwargs seed=2026` 生成的 OpenAI payload 确实为 `seed: 2026`，而非 adapter 默认 1234。
- 每个 seed 独立缓存命名空间、provenance、contract、native results/samples 和进程日志，三轮串行，不叠加为 C192。

## 聚合与判读

- 点估计：三个 per-seed 分数的算术平均；同时报告 min/max。
- 不确定性：以 doc_id 为 cluster，每个 cluster 保留三个 seed 结果，对 198 个 cluster 做 10000 次 bootstrap，报告双侧 95% 区间。
- 参考阈值仍为 0.88，分别报告 `mean >= 0.88` 和更保守的 `bootstrap lower 95% >= 0.88`。
- 输出健康：每个 seed 报告 30000-token 截断数/比例；聚合报告三次全对、全错和 seed 间混合的题数。
- 这轮只用于观察分布。看到结果后不回填或更改聚合方法；若需取代正式门禁，另行冻结项目支持的 gate 规则。

## 证据路径

- 远程根：`/mnt/nfs/users/jinghao/minimaxM3/20260921-minimax-m3-ppu-e2e/accuracy/accdist-001-gpqa-c64-multiseed3`。
- 聚合契约：`aggregate-contract.json`。
- 预期聚合结果：`aggregate-result.json`。
- heartbeat：`minimax-m3-accdist001-gpqa-multi-seed-c64`，每 30 分钟检查精确进程和产物，已在启动前创建为 active。

## 结果

- 三轮均完成 198/198 个唯一 strict-match 问题，0 timeout、0 empty；进程和原生证据完整。
- seed 1234：175/198 = 0.883838，30K 截断 20。
- seed 2026：173/198 = 0.873737，30K 截断 20。
- seed 3407：173/198 = 0.873737，30K 截断 24。
- 聚合 mean/min/max：0.877104 / 0.873737 / 0.883838；question-cluster bootstrap 95% CI `[0.835017, 0.915825]`。
- 163 题三轮全对、14 题三轮全错、21 题 seed 间混合；点估计和置信区间下界均未达到 0.88。本实验是诊断分布，不签发 formal gate。
- 聚合结果：`aggregate-result.json`，SHA-256 `17cebad3b27ace64d6029e190fcbfc828651e93dc4fc08e6f7969a8b1369f9a9`。
- heartbeat `minimax-m3-accdist001-gpqa-multi-seed-c64` 已在终态后暂停。
