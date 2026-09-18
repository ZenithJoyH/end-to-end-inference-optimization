# 模型优化产物契约

本契约规定 `models/<model>/<platform>/` 的长期记录方式。目标是让 Agent 能从一个稳定入口恢复当前状态，同时让人无需阅读运行脚本、原始回执或 trace 就能理解进展和结论。

## 双视图

每个 `baseline/`、`optimize/`、`acceptance/` 都以两份入口文档为主：

- `state.yml`：结构化事实主记录，供 Agent 优先读取和更新。使用稳定 ID、明确状态、数值与单位、证据路径和 SHA；未知值为 `null`，不得从 Markdown 猜回结构化事实。
- `README.md`：面向人的摘要。用简短文字和表格说明当前状态、关键性能/精度数据、结论边界、风险与下一步；数据必须来自同目录的 `state.yml`，不能维护另一套冲突事实。

更新时先写 `state.yml`，再同步 `README.md`。Agent 进入模型任务时先读平台导航和三个 `state.yml`，
再按需阅读三个 `README.md`。后续模型优化不创建 `history/` 或其他逐轮子目录。

## 三个目录

### `baseline/`

`state.yml` 至少记录环境和服务身份、镜像/挂载门禁、正式目标目录、当前场景 workload、正确性状态、Prefill/Decode/Mixed 基线指标、重复与波动、原始证据位置和基线状态。`README.md` 必须展示已执行性能测试的结果表，包括场景、范围、状态、吞吐、TTFT、TPOT/ITL、E2E 和必要说明；不可用项写 `—`。

如果正式目标 baseline 尚未完成，README 仍要明确列出目标场景并标记 `not_run`、`incomplete` 或 `deferred-too-slow`，同时区分已经取得数值的缩减/历史诊断 baseline。不能用“环境已准备”代替性能结果状态。

### `optimize/`

`state.yml` 是当前优化状态：当前目标场景与阶段、当前组合候选、保留/回退/失败/未完成实验索引、Prefill/Decode/Mixed 瓶颈、累计与单点性能证据、精度 gate、回退入口、下一轮候选和外部产物索引。`README.md` 只保留人需要的当前进展、关键对比、已保留改动、失败经验和下一步。

每轮实验在 `state.yml` 的实验账本中保留稳定 ID、变量、状态、关键指标、决策、回退和外部证据引用；
`README.md` 用紧凑表格保留人需要的阶段演进和失败经验。旧决策不能覆盖当前状态，但也不得为它们
创建 `history/`、`experiments/`、`planning/` 或其他逐轮目录。需要跨任务复用的机制结论进入
`docs/cases/`、SOP 或对应知识库；完整过程材料留在远程 case 目录。

### `acceptance/`

`state.yml` 保存最终候选的源码/配置/服务身份、正式精度分数与阈值、最终性能四场景结果、守护指标、适用范围、未完成项、PR/交付状态和回退入口。`README.md` 是最终验收报告。如果尚未完成，只记录 `incomplete`、已有证据和缺失项，不放入中间最好结果冒充最终结果。

## 不进入模型目录的内容

以下内容默认保存在用户指定的远程 `<remote-workdir>/<case-id>/` 或其他外部证据位置：

- 启动、停止、传输、采集、修复和临时 benchmark 脚本；
- 模型专用 `.py`、Ansible 执行文件、源码快照和实验 patch；
- 原始 JSON/JSONL/CSV、完整请求响应、日志、trace、profile 和大数据集；
- PID、容器 ID、进程列表、health 输出等瞬时快照。

`state.yml` 只记录外部绝对路径、产物类别、revision/SHA、生成实验和留存状态。可跨模型复用的实现经过参数化和测试后提升到公共 `scripts/`、`evaluation/`、`test/`、`benchmarks/` 或 `unit_tests/`；最终代码改动以目标源码仓库 revision/commit 和 diff 校验为准，不在模型目录堆叠 patch 版本。

## 一致性要求

1. 已完成性能测试必须同时写入结构化指标和 README 结果表。
2. `state.yml` 中的 `current` 只描述当前生效状态；旧实验和旧决策进入同文件的稳定 ID 账本，
   不创建模型内历史目录。
3. 每个数值带 workload、单位、测量角色和结论边界；不同 workload 不计算直接加速比。
4. README 中的表格可以舍入，`state.yml` 保留原始精度；两者必须可追溯到同一证据。
5. 大型或过程产物缺少稳定外部位置时，先补外部归档再从模型目录移除；不得为精简目录而丢掉唯一证据。
6. 本规则面向后续新增和更新；已有 `history/` 目录不由 Agent 自动迁移、删除或改写，除非用户明确要求。
