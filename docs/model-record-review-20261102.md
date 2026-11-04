# 模型记录整理报告（2026-11-02，第二轮更新）

已整理 **13 个模型、55 个独立/旧布局案例**。本轮保持 GLM 与 Qwen3.8 的文件不动，处理其余 52 个案例的基线入口、指标汇总和身份隔离。没有执行远端操作、模型精度/性能评测、提交或推送；`models/` 继续暂缓提交。

统一入口：[模型优化记录导航](../models/README.md)。本页描述记录维护结果，不代表任何模型通过了新的性能或精度验收。

## 本轮解决的问题

### MiniMax-M3.1 的 TP16 / TP8 身份隔离

原来一个平台目录同时保存 TP16 的 case_id 与 TP8 的 active_case_id，恢复时容易把原 anchor、后续场景入口和当前源码混用。现已拆成两个具有独立 identity、baseline、optimize、acceptance 的案例：

| 案例 | 基线边界 | 实验数 |
|---|---|---:|
| [20261008 TP16](../models/MiniMax-M3.1-Flash-W8A8/ppu/20261008-minimax-m31-w8a8-ppu-e2e/README.md) | 原适配配置的 anchor；组合正式比较未完成 | 8 |
| [20261010 TP8](../models/MiniMax-M3.1-Flash-W8A8/ppu/20261010-minimax-m31-w8a8-ppu-tp8-e2e/README.md) | 用户 TP8 配置加 correctness fix-001 的 scenario-entry baseline | 33 |

43 份优化点/PR 文档已移到所属案例，实验 ID、原数值及失败/回退结论保留，引用已修正。旧三阶段路径只作为迁移导航；无法唯一归属的共享字段放在旧 optimize/state.yml 的 `shared_or_unassigned_legacy_fields`，不再当成任何拓扑的当前状态。原始三份状态和文档共 49 个文件已逐字节归档并核对 SHA。不同 TP 不计算软件加速比。

### 基线缺口按真实用途分类

首轮“45 个 baseline 没有顶层 metrics”不是 45 个漏测或数据遗失。本轮检查非活跃案例，并对新增 TP16/TP8 案例分别汇总，得到：

| 分类 | 案例数 | 处理结果 |
|---|---:|---|
| 有结构化性能测量 | 18 | 明确展示指标、角色、单位、范围、字段来源；历史、缩减、回退和 incomplete 结果保持原边界 |
| 明确未执行 E2E 性能测试 | 32 | 根据原任务/状态注明 not_run 或原适用范围；不以精度、启动、组件检查代替基线 |
| 仅历史参考观测 | 2 | Qwen-VL opt10 结果导入、opt13 跨 Host 比较；明确没有同配置正式 anchor，原观测留在 optimize |

52 个基线入口均列出 P1K、P4K、P16K、P32K（D1K/C64/N128）的记录覆盖和缺失项。表中的记录审查状态不是新签发的测量回执；已测不等于稳态、身份、对比和最终验收条件全部通过。

从 9 份已有结构化状态中补齐 **212 条**指标，其中 208 条直接对应原字段，4 条按原有三轮 measured 数据计算中位数并保留全部来源指针。没有从 Markdown 猜测数值，也没有选取更快轮次或重算优化收益。主要修复包括：

- MiniMax-M3 的历史性能数据明确标注诊断/历史范围。
- MiniMax-M3.1 的 TP16 阶段代理、实验配置基线，以及 TP8 正式长度/缩减阶段的 scenario-entry 指标分别记录。
- Qwen3.6-27B 的缩减三阶段 baseline/revert 和四场景回归数据补入指标表；保留 Mixed 漂移及 P1K TTFT 波动超限，整套结果仍为 incomplete。
- Qwen3.6-35B 的 script19 场景入口补出吞吐及延迟，限定为该候选 baseline，不作为原 anchor 或最终累计收益。
- Qwen-VL 的 D256 sampling milestone 从 optimize 的结构化行补入 baseline 展示，未换成 D1024。
- xing4 的历史 revert 指标补入结构化视图；GPQA 暂缓与旧契约边界保持不变。

细目：[基线分类清单](/Users/baai/Documents/ChatGPT/端到端推理优化/.cache/model-record-archives/20261102-record-reconciliation-02/baseline-review-final.json)。指标逐条可由 source_pointer 定位；跨文件引用使用 source_record；计算值另带 derivation。

### 记录导航与引用

模型总览、各可维护模型/平台入口及 MiniMax 的跨案例链接已更新。正文中的历史外部证据路径保留，没有用本地路径可点击来冒充远端证据已验证。排除代码示例后，非活跃模型与案例文档无断链；没有改写 GLM、Qwen3.8 的正文或状态。

## 仍保留的边界

1. **GLM 与 Qwen3.8**：按本轮用户指令不修改，过程文件与原有记录问题继续暂缓。完整检查仍报告 84 个新增过程文件位置错误及 257 个既有材料待迁移告警；其中包含下述 xing4 保留文件。没有扩大白名单或屏蔽检查。
2. **已有 history**：沿用用户明确要求，逐字节保持原样。xing4 的 `optimize/performance-measurements.json` 被这些历史文档引用，暂留原路径；没有通过软链接或自动重写 history 来消除这一项。
3. **一项具体 workload 证据缺口**：Qwen3.6-27B 早期 `combo-001-fa-splits-warps` 的 Prefill、Decode、Mixed 三个缩减阶段汇总共 20 条 baseline/revert 指标，原本没有在本地结构化记录中保留完整 P/D/C/N。现以 `unresolved-workload-*` 明确隔离；保留每个原生 run-record 的远端绝对路径和 SHA，不拿这些数值计算正式场景收益。需要读取原 comparison contract/phase plans 才能关闭。详见[缺失证据清单](/Users/baai/Documents/ChatGPT/端到端推理优化/.cache/model-record-archives/20261102-record-reconciliation-02/unresolved-evidence.json)。同目录 op010r2 的 workload 已从其明确 unchanged 的结构化性能契约恢复。
4. **运行事实与正式验收**：本轮只维护本地记录；历史镜像、源码、挂载、服务、精度 gate 和远端产物留存均未重新验证。`completed` 仍须按任务范围解释，不能自动提升为最终四场景通过。

## 归档与恢复

用户指定归档根为 `.cache/model-record-archives`，已被 Git 忽略，只在本工作区可用，不能替代远端长期保存。

- 第一轮归档了 513 个过程文件（models 36、docs/cases 477）：[逐文件迁移清单](/Users/baai/Documents/ChatGPT/端到端推理优化/.cache/model-record-archives/20261102-record-reconciliation-01/migration-manifest.json)；[原始备份](/Users/baai/Documents/ChatGPT/端到端推理优化/.cache/model-record-archives/20261102-record-reconciliation-01/before.zip)及[整包 SHA](/Users/baai/Documents/ChatGPT/端到端推理优化/.cache/model-record-archives/20261102-record-reconciliation-01/before.zip.sha256)。这些迁移结果保持不变。
- 第二轮修改前模型备份：[before-models.zip](/Users/baai/Documents/ChatGPT/端到端推理优化/.cache/model-record-archives/20261102-record-reconciliation-02/before-models.zip)及[整包 SHA](/Users/baai/Documents/ChatGPT/端到端推理优化/.cache/model-record-archives/20261102-record-reconciliation-02/before-models.zip.sha256)。
- 第二轮逐文件修改记录：[changes.json](/Users/baai/Documents/ChatGPT/端到端推理优化/.cache/model-record-archives/20261102-record-reconciliation-02/changes.json)；其中 before/ 保存改写前副本。
- MiniMax 拆分：[迁移清单](/Users/baai/Documents/ChatGPT/端到端推理优化/.cache/model-record-archives/20261102-record-reconciliation-02/minimax-migration.json)及[原始账本与文档](/Users/baai/Documents/ChatGPT/端到端推理优化/.cache/model-record-archives/20261102-record-reconciliation-02/minimax-original)。

恢复时先校验 SHA，复制到新的检查目录，再核对原位置是否已有更新；不要直接覆盖活跃任务。归档中的维护脚本仅供审计，不应重复执行。

## 校验结果

- 模型 YAML/schema、三阶段身份、实验文档链接：**0 错误**，原 MiniMax 的两条混合身份告警已解除。
- 新汇总指标：**212/212** 与原结构化字段或明确的中位数计算一致。
- MiniMax 原始记录：**49/49** 文件 SHA 一致，41 个实验及43份单点/交付文档均有归属。
- 本轮受保护路径写入：**0**；已有 history 变化：**0**。
- 非活跃模型与案例文档断链：**0**（忽略代码示例中的伪链接）。
- `git diff --check`：通过。完整项目记录检查因上述暂缓过程材料仍未全绿。

[本轮校验回执](/Users/baai/Documents/ChatGPT/端到端推理优化/.cache/model-record-archives/20261102-record-reconciliation-02/verification.json)。未更改公共程序，本轮执行的是记录/引用/数值一致性校验，没有运行无关的设备或模型测试。
