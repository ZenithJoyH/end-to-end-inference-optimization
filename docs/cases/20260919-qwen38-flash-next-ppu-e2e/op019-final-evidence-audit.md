# op-019 最终证据与停止决策独立审计

## 审计结论

`op-019` 应停止 performance timing 和 FlagGems/服务集成。最终 smoke
没有生成 `result.json`，并在进入 graph 验证和性能计时前退出；因此没有
可以晋级的 eager/graph 性能结论，也没有理由修改服务源码。

将真实 `qsa_select_paged_tokens` producer 放入同一 captured transaction 是
合理且优先级最高的重开方案，但它不是当前证据唯一能推导出的技术解。
任何替代方案都必须同样证明：同一 graph replay 中 producer 的 selected
值确实变化、generic 确实消费新值、candidate membership 被重建，且
A/B/A 结果分别回到对应 oracle。只把 producer 放进 graph，却不验证
producer 输出和 consumer 命中，仍不足以重开。

## 最终失败证据

- 最终目录：
  `/mnt/nfs/users/jinghao/qwen3.8-flash/20260919-qwen38-flash-next-ppu-e2e/microbench/op019-qsa-r4-direct-membership-smoke-20260920T165455Z-1947604`。
- `audit.txt` 明确记录 `exit_status=1` 和 `result_json=missing`。
- 最终脚本 SHA-256 为
  `d20e5c8df2f306043b2d7d13b0e1964b4e7ea61e8d058a3d73fadba553674fee`；
  与当前本地审计副本一致。
- `console.log` SHA-256 为
  `eea36e8260fe4325e75fdff40be9a9c85d9bedb23d7dcee10aebff963df073aa`。
  失败发生在 `run_case` 的 eager changed-input 预检：
  `selected_a_sha != selected_b_sha`，但
  `eager_a_sha == eager_b_sha == 1cc47b65...`。
- 代码顺序是先运行初始 generic/candidate、structure reference 和
  correctness，然后做 eager A/B 预检，之后才进入
  `_graph_dynamic_aba`。因此最终失败的精确边界是：**eager 动态输入
  control 已无法建立，最终尝试并未进入 graph 门禁**。

所以 `graph_dynamic_input_evidence_unresolved` 作为停止类别可以接受，
但若写成“graph replay 已运行但未证明 membership 重建”则过度声明。
更准确的表述是“standalone rows4096 changed-positive-index control 在 eager
阶段就不可信，因而 graph dynamic-input 门禁无法开始”。

## rows1/TOPK1 control 的结论边界

Control 结果位于：

`/mnt/nfs/users/jinghao/qwen3.8-flash/20260919-qwen38-flash-next-ppu-e2e/microbench/op019-qsa-positive-index-value-probe-001/result.json`

文件 SHA-256 为
`68430bd253bd91ee648de9ad6f36425d57eb3f2c5f45c6990b4105fdff69de61`。其内
五项布尔检查全部为真：

- token `0` 输出精确等于 `V[0,0]`；
- token `2049` 输出精确等于 `V[128,1]`；
- 两个正索引输出不同；
- `-1` 输出 exact zero；
- 两个期望 V 值本身不同。

这证明当前 generic QSA 在 `rows=1, TOPK=1` 的独立调用中使用了
正 selected-index 值，能排除“generic QSA 数学上完全忽略正索引”。
它不能证明 rows4096 形状的 eager 动态替换可靠，也不能证明
graph replay 会读取新 selected 值。

## 脚本本身的审计发现

1. 当前 `_graph_dynamic_aba` 不符合冻结设计的“同一 captured graph，
   更改同一静态 selected buffer，再 replay B/A”。它分别用
   `selected_a` 和 `selected_b` 捕获 `graph_a` 与 `graph_b`，然后按
   A/B/A replay 两个不同 graph。即使这段通过，也不能单独
   证明某一 graph replay 重读了动态 selected 并重建 membership。
2. 最终尝试在上述 graph 函数之前就失败，所以它未造成虚假的
   graph-pass 结论；但重开前必须修正这一验证方法。
3. 最终运行没有结构化 `result.json`。“rows4096 generic 对照、
   sampled FP32、structure/fallback 和 group-base 双射已通过”可由同一
   脚本的执行顺序和后续失败点接支，但没有持久化的数值摘要。
   它应被称为“未触发前置 assertion”，不应被扩展为已完成
   full correctness suite。
4. result payload 中 `fixture_origin` 键重复两次，Python 会静默覆盖前值。
   它不影响本次停止决策，但重开前应清理，避免 schema 审计歧义。
5. 历史日志确实保留了同指针复制、原地 Triton 变换和独立
   B pointer 等多次诊断失败；但最终可审计的硬回执是上述
   `165455Z-1947604` 目录。因而“多种 standalone 输入更新尝试都
   没有建立可信动态证据”是合理摘要，不应把它写成 PPU
   backend 已被证明存在特定 cache bug。

## 源码、服务与资源边界

- 2026-09-21 复核时，容器内
  `/workspace/FlagGems/src/flag_gems/fused/qsa.py` SHA-256 仍为
  `e18fbb229d9c4a5c2b06a6858ae4679596e1a6f971a4ff8878acbbc4f469db23`，
  与 op-019 之前记录的保留基线相同。
- 该 FlagGems 工作区**不是 clean**：`git status` 仍显示 `qsa.py` 已修改，
  diff 是先前保留的 `static_score_columns`/runtime-bound 改动。因此准确
  表述应是“op-019 没有引入持久化 FlagGems/service 改动”，而不是
  “FlagGems 仓库无任何未提交改动”。
- service50 的 `8030/health` 复核为 healthy；PPU0–7 均为
  `1 MiB / 98304 MiB, 0%`，PPU8–15 仍由保留服务使用。
- 本次哈希复核只对 op-019 直接涉及的 `qsa.py` 建立了
  “恢复到已知保留基线”证据；不应由这一个 SHA 扩展声称整个
  Plugin/FlagGems 工作区所有文件都未变。

## 重开所需的最小证据

1. 把真实 selected producer 和 generic/candidate consumer 纳入同一 graph，
   或提供等价的、PPU 上已验证的同 graph 动态输入机制。
2. 在 graph 外只改 producer 的合法上游输入，并持久化 A/B/A
   producer-selected SHA/摘要，generic output SHA，candidate membership 摘要
   和 candidate output SHA。
3. 只捕获一个 graph；replay B 和 A 都必须命中各自 oracle，且 B
   不能与 A 相同。
4. 先生成完整的结构化 correctness/graph 回执，再进入
   Prefill/Mixed rows4096 的完整事务计时。
5. 仍必须满足原冻结的两 phase × eager/graph 的最小 8% 门禁，
   未通过前不进入服务集成。
