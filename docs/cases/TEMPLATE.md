# <案例 ID>：<模型>/<平台> <优化目标>

## 1. 摘要

- 执行规则：`policy_version` / `policy_date`（历史未知保持 null）
- 验收范围：`formal|performance_only|diagnostic`
- 精度/性能状态：`passed|failed|incomplete`
- 状态：`planned|running|kept|reverted|not-proven|blocked`
- 结论：
- 主指标变化：
- 守护指标变化：
- 证据等级：`observation|reproduced|transferred|invariant`
- 适用边界：
- 模型/平台产物：`models/<model>/<platform>/{baseline,optimize,acceptance}/`

## 2. 任务与验收契约

- 模型、权重和 tokenizer：
- 平台、Host、设备与拓扑：
- 用户提供的远程工作目录、规范化路径与本案例子目录：
- 远程目录 owner/权限、可用空间、符号链接和既有内容检查：
- 源适配容器、镜像引用与 image ID/digest：
- 新优化容器、镜像引用与 image ID/digest：
- 镜像谱系状态与证据（`unverified|verified|failed`）：
- 源/优化容器规范化挂载清单路径：
- 挂载 diff 与 `mount_parity`（`unverified|passed|failed`）：
- 容器运行配置差异、资源隔离与共享挂载影响：
- 引擎、Plugin、FlagGems 和 runtime revision：
- 主指标：
- 守护指标：
- 通过门槛：
- 允许修改和禁止修改的范围：

## 3. Workload

- 场景目录：`scenario_id`、Prefill/Decode/Mixed、长度、并发/到达模式、用途：
- 预冻结的最终验收场景集合：
- 本轮 `test_scope`：`targeted|checkpoint|full`
- 性能评测 Skill 模式、场景 ID、结果、结论边界及证据：
- 本轮目标、哨兵、省略场景及选择理由：
- 数据集或生成方式：
- endpoint、EOS 和采样策略：
- 输入/输出长度及分布：
- 并发、请求数和到达模式：
- warmup 与正式轮数：
- 客户端环境：

## 4. 正确性护栏

- 精度评测 Skill 模式、覆盖 experiment ID、结果及证据：
- 精度进度 heartbeat 的 automation ID、频率、状态、监控目标和清理证据：
- smoke/sanity 请求与预期：
- baseline 结果：
- candidate 结果：
- 每个优化点的最小正确性回归：
- 尚未经过完整精度的已保留 experiment ID（最多累计 3 个低风险点）：
- 完整精度触发原因：`2-3-point-batch|high-risk-change|final-candidate|manual`
- 最近一次完整精度绑定的源码、配置和服务身份：
- 正式精度工具、样本数、阈值和结果：
- 超时、空回复、截断、重复或格式异常：

### 精度问题定位（触发时填写）

- issue ID、触发模式、失败类型和冻结证据：
- 最后可信正确状态与失败 candidate 身份：
- `measurement-invalid|identity/config|output-health|numerical|execution-mode|nondeterminism` 分类：
- 最小复现、重复性与 baseline/candidate 差异：
- 改动二分、执行路径/命中证据和竞争解释：
- 根因：`suspected|confirmed|not-reproduced|measurement-invalid`
- 修复或回退、最小回归、原失败范围复测及新 gate：
- 定位记录：`models/<model>/<platform>/optimize/accuracy-diagnosis/<issue-id>.md`
- 是否允许恢复性能优化及剩余风险：

## 5. Baseline

- 启动命令或配置：
- vLLM 性能服务参数：`--no-enable-prefix-caching`
- prefix cache 的 runtime 状态证据与 service manifest：
- 冷启动、预热和稳态边界：
- TTFT/TPOT/ITL/E2E：
- 请求与 token 吞吐：
- 显存、利用率、功耗和通信：
- 失败、超时和服务日志：
- 原始产物路径与校验：
- 远程 commands/manifests/logs/profiles/results/patches 清单与留存状态：

## 6. 瓶颈证据

- 首次判断：
- Profiling Skill 模式、scenario ID、trace 有效性、rank/worker 覆盖及产物路径：
- 请求/阶段/框架/通信/算子分解：
- profiler 配置与扰动说明：
- 热点结论、竞争解释、置信度和下一可证伪实验：
- 最终根因：
- 被排除的替代解释：

## 7. 实验记录

### 候选优先级（测量后持续更新）

分类使用 `framework`、`operator/replace`、`operator/improve`。跨层方案拆成关联实验，标明依赖，组合收益单独测量。

| 排名 | 分类 | 候选 | 瓶颈与命中证据 | 主指标净收益估计 | 成本/风险 | 依赖 | 首个验证实验 | 暂缓理由 |
|---|---|---|---|---|---|---|---|---|

### Plugin 设计复核（涉及 Plugin 时填写）

规范见 [Plugin 优化设计与 PR 准备](../plugin-change-review.md)，内容或链接保存在模型/平台的 `optimize/`。

- 目标 revision 的设计/贡献规范、相邻实现和复用扩展点：
- 改动归属及未选择更窄扩展点的理由：
- 真实支持/调优条件、默认选择、fallback、可选依赖和缓存状态：
- 共享调用方与非目标模型/平台影响：
- 代表性正例、反例、边界、graph/worker 测试及未测项：
- 实验补丁到最终代码的整理与重新验证：
- Plugin/FlagGems 的独立补丁、依赖及目标 CI：
- `pr_readiness`：`experimental|needs_revision|ready_for_review`；设计问题与下一步：

### 已执行实验

| ID | 分类 | 风险 | test scope / scenario ID | 假设 | 主要变量 | 最小正确性 | 完整精度批次 | 性能结果 | 波动 | 决定 |
|---|---|---|---|---|---|---|---|---|---|---|

每个实验在正文中补充命令、配置、改动、日志位置和回退方法。组合诊断实验需说明为什么不能直接作为最终结论。

多轮实验、profiling、补丁和逐轮性能摘要归档到模型/平台的 `optimize/`；本节链接相应文件。正式验收前不得把中间最好结果移动到 `acceptance/` 冒充最终结论。

### 阶段性优化规划复盘

- 规划 Skill、review ID、覆盖 experiment ID 和证据截止点：
- 当前组合候选及同配置 baseline→current 累计结果：
- 保留、回退、失败、未完成和相互依赖的实验：
- 已消除、减弱、迁移、暴露及仍不明确的瓶颈：
- 下一轮 1–3 个候选的排名、支持/反对证据与暂缓理由：
- 立即执行的首个证伪实验、scenario ID、所需 Skill、门槛和停止条件：
- 规划记录：`models/<model>/<platform>/optimize/planning/<review-id>.md`
- 下次规划触发条件：

## 8. 最终候选与回归

- 最终改动：
- Plugin 设计复核结论、PR 准备状态及未测模型/平台（如适用）：
- baseline/candidate/revert 多轮对比：
- 性能评测 Skill `formal` 模式、plan/contract SHA、比较判定与证据：
- 完整验收 workload 矩阵及各场景结论：
- targeted/checkpoint 未覆盖项已在 full 中补齐：
- graph、cache、混合 batch 和长稳结果：
- 多卡通信和负载均衡：
- 回退验证：
- `acceptance/` 中的最终性能和精度达标记录：

## 9. 结论与限制

- 已验证事实：
- 推断：
- 未解决问题：
- 不适用场景：
- 是否建议部署或继续实验：

## 10. 复盘与知识沉淀

- 最有价值的诊断信号：
- 无效或负优化及原因：
- 可更早执行的检查：
- 可复用脚本、配置或测试：
- 涉及的关键算子与知识目录：
- 案例开始前的既有判断：
- 知识差量：`confirmed|refined|contradicted|none`
- 新的稳定理解、适用边界或反例：
- 下次可提前执行的检查、可跳过方向或更深入实验：
- 算子 `case-index.md` 证据卡链接：
- `optimization-map.md` 更新及理由；无更新时说明：
- 稳定算子 `README.md` 更新及理由；单个新数字不作为理由：
- 对 SOP 的建议变更及证据等级：
