# 模型优化产物契约

本契约规定 `models/<model>/<platform>/` 的长期记录方式。目标是让 Agent 能从一个稳定入口恢复当前状态，同时让人无需阅读运行脚本、原始回执或 trace 就能理解进展和结论。

## 结构化记录与人类文档

每个 `baseline/`、`optimize/`、`acceptance/` 都以 `state.yml` 和 `README.md` 为入口：

- `state.yml`：结构化事实主记录，供 Agent 优先读取和更新。使用稳定 ID、明确状态、数值与单位、证据路径和 SHA；未知值为 `null`，不得从 Markdown 猜回结构化事实。
- `README.md`：面向人的阶段总览。用简短文字和表格说明当前状态、关键性能/精度数据、结论边界、风险与下一步；数据必须来自同目录的 `state.yml`，不能维护另一套冲突事实。

此外，`optimize/` 中每个优化点必须有一个 `optimize/<experiment-id>.md`。它是该优化点的人类可读说明，
与 `state.yml` 中同 ID 的结构化条目对应；`optimize/README.md` 只做多轮总览和索引，不替代单点文档。

新增条目同时填写 `document: <experiment-id>.md`。既有短文件名允许通过 `document` 显式映射，
保留原始实验 ID 和外部证据；同一优化点的历史子实验可指向同一文档，不复制正文。README 必须有可点击链接。
`scripts/check-project-records.py` 检查 YAML 重复键、实验 ID、文档存在性、README 索引、Skill 入口引用及新增过程材料；
已接入 `scripts/validate-local`。此检查不假装验证远端证据或 Markdown 中所有数值的真实性。

更新时先写 `state.yml`，再更新当前优化点 Markdown，最后同步 `README.md` 总览。Agent 进入模型任务时
先读平台导航、三个 `state.yml` 和 `optimize/README.md`，只在需要了解具体改动时读取相应
`<experiment-id>.md`。后续模型优化不创建 `history/` 或其他逐轮子目录。

## 三个目录

### `baseline/`

`state.yml` 至少记录环境和服务身份、镜像/挂载门禁、正式目标目录、当前场景 workload、正确性状态、Prefill/Decode/Mixed 基线指标、重复与波动、原始证据位置和基线状态。`README.md` 必须展示已执行性能测试的结果表，包括场景、范围、状态、吞吐、TTFT、TPOT/ITL、E2E 和必要说明；不可用项写 `—`。

如果正式目标 baseline 尚未完成，README 仍要明确列出目标场景并标记 `not_run`、`incomplete` 或 `deferred-too-slow`，同时区分已经取得数值的缩减/历史诊断 baseline。不能用“环境已准备”代替性能结果状态。

### `optimize/`

`state.yml` 是当前优化状态：当前目标场景与阶段、当前组合候选、保留/回退/失败/未完成实验索引、Prefill/Decode/Mixed 瓶颈、累计与单点性能证据、精度 gate、回退入口、下一轮候选和外部产物索引。`README.md` 是多轮优化总览，保留当前进展、累计结果、实验索引、关键对比、已保留改动、失败经验和下一步。

每个优化点对应一个稳定 `experiment-id` 和一个同名 `<experiment-id>.md`。文档在实施改动前创建，
实验推进时持续更新，最终至少包含：

1. 优化方向、分类、目标场景与 `prefill|decode|mixed` 阶段；
2. 瓶颈证据、假设、主要变量、预期收益、守护指标和停止条件；
3. 实际优化内容、涉及组件/源码文件/配置、命中条件、fallback、graph 与兼容边界；
4. 最小正确性、完整精度触发/结果以及实际路径命中证据；
5. 同 workload 的 baseline/candidate/revert 性能数据、变化比例、波动和结论边界；
6. `retained|reverted|failed|incomplete|superseded` 决定、原因、风险、回退方式与下一步；
7. 外部原始产物的绝对路径和必要 revision/SHA。

一个优化点只使用一份 Markdown；不同运行轮、命令、trace 和补丁版本在该文档内按阶段更新，不拆成
多个过程文件。`README.md` 用紧凑表格链接每个优化点并汇总累计效果。旧决策不能覆盖当前状态，
但也不得为它们创建 `history/`、`experiments/`、`planning/` 或其他逐轮目录。需要跨任务复用的机制
结论进入 `docs/cases/`、SOP 或对应知识库；完整过程材料留在远程 case 目录。

单点 Markdown 至少采用以下结构：

```markdown
# <experiment-id> <优化点名称>

- 状态、分类、目标场景、目标阶段、依赖：

## 优化方向与瓶颈依据
## 优化内容与适用边界
## 正确性与路径命中
## 性能效果
<!-- 同 workload 的 baseline/candidate/revert、单位、变化比例、波动和守护指标 -->
## 决定、风险与回退
## 外部证据
```

`optimize/README.md` 的实验总览表至少列出 ID/链接、优化方向、场景/阶段、主要变量、性能效果、
正确性状态和最终决定。总览中的数字来自 `state.yml`，详细机制与边界链接到对应单点 Markdown。

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

1. 已完成性能测试必须同时写入结构化指标、对应 `<experiment-id>.md` 的性能效果和 README 总览表。
2. `state.yml` 中的 `current` 只描述当前生效状态；旧实验和旧决策进入同文件的稳定 ID 账本，
   不创建模型内历史目录。
3. 每个数值带 workload、单位、测量角色和结论边界；不同 workload 不计算直接加速比。
4. README 和优化点 Markdown 中的表格可以舍入，`state.yml` 保留原始精度；三者必须可追溯到同一证据。
5. 大型或过程产物缺少稳定外部位置时，先补外部归档再从模型目录移除；不得为精简目录而丢掉唯一证据。
6. 本规则面向后续新增和更新；已有 `history/` 目录不由 Agent 自动迁移、删除或改写，除非用户明确要求。

## 活跃任务过程材料的迁移

`docs/process-artifact-inventory.json` 是 2026-09-21 审查时的既有路径清单，不是新增文件的白名单生成器。
这些文件仅获准暂留以保护活跃任务和唯一证据，每次验证均报告待迁移数量；不得自动追加清单掩盖新材料。
新任务的命令、脚本、配置和原始结果直接进入用户指定的远端 case 目录。

迁移既有材料前，先确认使用该路径的任务已空闲，逐项核对本地当前 SHA、外部副本 SHA、
原始运行路径与仍有效引用。更新本地导航到可访问的外部位置后再移除源文件，保留恢复路径与清单；
不得因为远程记录提到同名文件就假定已有相同副本。未完成这些核验时保持 `pending-active-task-review`，
不宣称目录清理完成。此过程不触及用户保留的已有 `history/`。
