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

- 数据集或生成方式：
- endpoint、EOS 和采样策略：
- 输入/输出长度及分布：
- 并发、请求数和到达模式：
- warmup 与正式轮数：
- 客户端环境：

## 4. 正确性护栏

- smoke/sanity 请求与预期：
- baseline 结果：
- candidate 结果：
- 每个优化点的最小正确性回归：
- 尚未经过完整精度的已保留 experiment ID（最多累计 3 个低风险点）：
- 完整精度触发原因：`2-3-point-batch|high-risk-change|final-candidate|manual`
- 最近一次完整精度绑定的源码、配置和服务身份：
- 正式精度工具、样本数、阈值和结果：
- 超时、空回复、截断、重复或格式异常：

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

## 6. 瓶颈证据

- 首次判断：
- 请求/阶段/框架/通信/算子分解：
- profiler 配置与扰动说明：
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

| ID | 分类 | 风险 | 假设 | 主要变量 | 最小正确性 | 完整精度批次 | 性能结果 | 波动 | 决定 |
|---|---|---|---|---|---|---|---|---|---|

每个实验在正文中补充命令、配置、改动、日志位置和回退方法。组合诊断实验需说明为什么不能直接作为最终结论。

多轮实验、profiling、补丁和逐轮性能摘要归档到模型/平台的 `optimize/`；本节链接相应文件。正式验收前不得把中间最好结果移动到 `acceptance/` 冒充最终结论。

## 8. 最终候选与回归

- 最终改动：
- Plugin 设计复核结论、PR 准备状态及未测模型/平台（如适用）：
- baseline/candidate/revert 多轮对比：
- workload 矩阵：
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
