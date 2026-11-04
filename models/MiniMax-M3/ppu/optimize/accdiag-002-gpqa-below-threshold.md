# accdiag-002：GPQA 正式门禁低于 0.88

## 事故与证据有效性

- 触发：`fw-006` 绑定的 GPQA Diamond 全量 198 题正式门禁得分 `172/198=0.8686868687`，低于用户冻结阈值 `0.88`。
- 评测证据有效：198 个唯一题目、396 条原生 sample/filter 记录齐全，0 timeout、0 request error，所有 prompt/doc/target 可与上游历史全量运行逐题对齐。
- 由于分数未达阈值，维护版 wrapper 正确地未生成可消费 gate/run-record；对应 heartbeat 已停用。
- 正式证据：`/mnt/nfs/users/jinghao/minimaxM3/20260921-minimax-m3-ppu-e2e/accuracy/fw006-formal-gpqa-c64-threshold88`。

## 样本级差异

当前 PPU-07 `172/198` 与上游 PPU-13 redesign/index-topk 历史 `177/198` 运行使用相同的 198 题、prompt、target 和核心生成参数。逐题比较结果：

- 两者都对 166 题，都错 15 题；当前相对历史退化 11 题、改善 6 题，净少 5 题。
- 提取答案相同 177/198；原始回复逐字节相同仅 1/198，表明不同服务/执行路径下长 CoT 存在显著轨迹漂移。
- 历史运行 26 题达到 30000 completion-token 上限，其中 13 题答对；当前运行 23 题达上限，仅 7 题答对。
- 非截断题的当前得分是 165，历史是 164；净少的 5 分全部来自 30K 输出上限样本的答案可提取性/正确性变差，不是普遍性短答题退化。

比较证据：

- `/mnt/nfs/users/jinghao/minimaxM3/20260921-minimax-m3-ppu-e2e/results/accdiag-002-gpqa-below-threshold/sample-comparison.json`（SHA-256 `7c63b84f...`）。
- `/mnt/nfs/users/jinghao/minimaxM3/20260921-minimax-m3-ppu-e2e/results/accdiag-002-gpqa-below-threshold/upstream-178-vs-177-comparison.json`（SHA-256 `0340b4ee...`）。上游自身两次同数据运行也出现 5 题退化、4 题改善和大量原始回复漂移。

## 当前归因边界

- 当前 formal 实际 API payload 为 `temperature=1, top_p=0.95, top_k=20, max_tokens=30000, seed=1234`。`lm-eval` 任务展示的 `do_sample=False` 不会将这个 OpenAI chat payload 变为 greedy；这是一个有 seed 的采样路径。
- 历史 `177/198` 来自 PPU-13 旧 redesign/index-topk patch 服务；当前 PPU-07 是 no-patch + AABS0 + `fw-006`。上游记录明确未在当前 no-patch+AABS0 路径重跑全量 GPQA，因而 `177/198` 不是当前执行路径的 last-known-good gate。
- `fw-006` 仅改变 FlagGems SQLite schema reflection 范围，现有/缺失 table 语义、选中 config、graph replay 和固定十题 greedy 回归已通过；但在 candidate/revert 相同 formal 对照完成前，不将其宣称为“已排除”。
- 当前最强证据指向：历史 gate 与当前服务身份不同，且采样型长 CoT 对并发调度/数值微扰高度敏感；30K 截断使轨迹分叉直接转化为不可提取答案和净失分。分类更新为 `formal_contract_sampling_nondeterminism_confirmed_with_truncation_amplification`。`fw-006` 仍没有 candidate/revert formal 级因果排除，但目前无证据表明它修改了数值或答案语义。

## 最小复现结果

- 在同一服务实例 `bd37abcbf719:8023:588850:273180627` 上，对 `69/121/131` 使用与 formal 一致的 `temperature=1/top_p=0.95/top_k=20/max_tokens=30000/seed=1234` payload，每题同时重复 2 次。
- 6/6 原始响应哈希全部不同。doc 69 两次分别为 `B/length/30000` 和 `D/stop/10339`；doc 121 为 `B/stop/19450` 和 `B/length/30000`；doc 131 两次都提取 `A`，但分别在 2250/2020 token 停止且响应哈希不同。
- 与当前 formal 对齐：doc 69 formal 答 `B`，重复中可翻转为正确 `D`；doc 121 formal 答 `C`，两次重复均翻转为正确 `B`；doc 131 formal 答 `D`，两次重复均翻转为正确 `A`。
- 这直接证明在目标 C64 并发形态中，固定 request seed 并不保证生成轨迹、停止长度或答案可复现。
- 结果路径：`/mnt/nfs/users/jinghao/minimaxM3/20260921-minimax-m3-ppu-e2e/results/accdiag-002-gpqa-below-threshold/repeated-current-service.json`，SHA-256 `daa4e1c5916b4b1104de74dde22e56ecf01cfd9f252e8ba5c52103c4624bfc88`。

## 决定与下一步

- 不用“重跑到过线”作为修复：在当前契约下，单次 198 题分数会混合模型能力、并发非确定性和截断运气。
- 优先修正 formal 契约：若要可复现回归，改为 greedy 生成；若必须保留 `temperature=1/top_p=0.95/top_k=20`，则用多次/多 seed 分布和置信区间判定，不用单次 0.88 硬门槛。同时应单列 30K 截断率与截断组得分。
- 如果用户仍要判定 `fw-006` 的独立因果，可在原始 SQL 与 `fw-006` 之间做同 prompt/同 payload 的 candidate/revert 对照；脚本已保存，但本轮未重启服务、未执行该二分，避免在契约本身已证实不稳定时扩大变更。
- 新的正式 `score >= 0.88` gate 生成前，暂停叠加新的性能优化，不关闭 P1K 场景。
