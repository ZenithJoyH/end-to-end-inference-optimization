# 推理分析工具与现有优化流程的结合

本轮依据用户要求，将外部仓库中适用的分析能力逐项引入当前项目。设计参考固定于
BBuf/AI-Infra-Auto-Driven-SKILLS 的 `5df356636bf9da3a1446653043942ff3487c1430`；
采用本项目原创实现，不整包安装、不复制未明确许可的外部源码或长篇材料。
本页是工具集成设计与验证记录，不是模型实验账本。

## 范围与接口约束

- 只在当前项目实现本地离线分析、知识检索及其文档与测试；不连接远端、不启动服务或设备 workload。
- 使用标准库，保留现有工作树修改；不修改 `models/`、`docs/cases/`、inventory、原始 `test/` 导入资产或正式验收器。
- 新工具的 JSON 是诊断 sidecar，使用来源路径与 SHA256、假设、缺口和明确结论边界；不得签发 accuracy/performance gate。
- 缺少阶段/层/shape/设备归属时保留 unknown/incomplete，不以累计 kernel 时间、异流交叠或理论容量推导精确端到端收益。
- 只分析显式提供的文件；工具不抓取网络、不运行输入命令、不自动刷新知识或改变服务配置。
- 新增代码、实验脚本与测试由本地子 Agent 执行；主 Agent 负责规划、接口协调、针对性复核与文档整合。

## 接入点与结果去向

| 当前问题 | 使用入口 | 交回的原流程 |
|---|---|---|
| 同名 kernel 分不清阶段/层，或多 rank/多 stream 时间线难以导航 | [trace 分层、区间和候选表](../skills/inference-profiling/references/trace-analysis.md) | `inference-profiling/analyze`，以原事件和范围支持归因；仍按 SOP C2 确认关键路径/竞争 |
| 准备实现新快路，不清楚上游是否已做或有哪些回归 | [上游 PR 查询](../skills/key-operator-opt/references/upstream-pr-history.md) | `key-operator-opt` 的 provider 比较与首个证伪实验；发现卡不变成本平台案例 |
| graph/workspace 挤占 KV，长输入等待多或容量判断不清 | [显存/KV 分账](../skills/inference-roofline-analysis/references/offline-estimates.md#显存与-kv-分页账本) | 框架工作点判断与规划；实际 Running/Waiting、抢占和完整 Decode 证据仍需现场验证 |
| 缺少可复算的算子 shape/FLOPs 估计 | [shape/FLOPs 估算](../skills/inference-roofline-analysis/references/offline-estimates.md#shape-与算法-flops) | Roofline 的 `F_algo` 输入；`F_exec`、HBM 流量和硬件屋顶各自取证 |
| 换 revision 或启动候选参数后，不确定 CLI 是否认识 flag | [离线 CLI 参数检查](../evaluation/performance/README.md#离线-cli-参数兼容检查) | 启动配置预检；实际服务 runtime、参数值语义与 readiness 仍由原流程核实 |

只在这些问题可能改变下一步决策时运行相应工具。已有同输入有效报告直接复用；没有匹配记录时保留缺口或选择其他有依据的实验。工具不会递归调用 Skill、采集 trace、补跑 benchmark 或修改服务。

报告和导航 trace 放入当前批准的外部 case 产物目录，在现有优化点的证据/假设/下一步记录路径、输入与输出 SHA、当前 scenario/candidate/phase/rank/shape 的匹配依据和决策影响。本页及工具 JSON 不新增模型状态字段、阶段目录或正式通过条件。

## 与外部设计的取舍

| 参考来源（固定 revision） | 采用的机制 | 本项目实现边界 |
|---|---|---|
| [pipeline analysis](https://github.com/BBuf/AI-Infra-Auto-Driven-SKILLS/tree/5df356636bf9da3a1446653043942ff3487c1430/skills/llm-pipeline-analysis) | forward/layer/kernel 层级、可核验锚点与 Perfetto 范围 | 显式边界绑定 trace SHA；不凭 kernel 名猜层，跨流结束使用真实最大 end，缺失尾边界保持未知 |
| [profiler analysis](https://github.com/BBuf/AI-Infra-Auto-Driven-SKILLS/tree/5df356636bf9da3a1446653043942ff3487c1430/skills/llm-torch-profiler-analysis) | kernel/source、overlap、fusion 候选视图 | 异流时间交叠命名为交叠，不冒充 hidden/可移除时延；相邻关系不证明数据依赖 |
| [PR history](https://github.com/BBuf/AI-Infra-Auto-Driven-SKILLS/tree/5df356636bf9da3a1446653043942ff3487c1430/model-pr-optimization-history) | 有范围的检索和审阅等级 | 原创少量元数据卡；状态核验、diff 审阅、本平台复现分开，不复制大规模历史库 |
| [capacity planner](https://github.com/BBuf/AI-Infra-Auto-Driven-SKILLS/tree/5df356636bf9da3a1446653043942ff3487c1430/skills/llm-serving-capacity-planner) | 权重/KV/graph/其他显存分账与容量解释 | 平台中立输入；hybrid groups、块对齐和完整 Decode 范围显式提供，理论上界不等于 SLO 容量 |
| [compute simulation](https://github.com/BBuf/AI-Infra-Auto-Driven-SKILLS/tree/5df356636bf9da3a1446653043942ff3487c1430/skills/model-compute-simulation) | 可复算 shape 与算子计算量 | 优先实际 per-rank shape；保留估算/未知，不默认模拟全部模型或套用 NVIDIA 算力表 |
| [auto benchmark](https://github.com/BBuf/AI-Infra-Auto-Driven-SKILLS/tree/5df356636bf9da3a1446653043942ff3487c1430/skills/llm-serving-auto-benchmark) | 用实际 help 快照检查候选 flag | 离线检查显式 argv，不执行 shell，不替代现有 runner、四场景或 baseline/candidate/revert |

## 执行前分配

| 单元 | 执行者 | 输入与产物 | 依赖与预算 | 验收标准 |
|---|---|---|---|---|
| A：trace 分层与 overlap/fusion | 内置 external_review | 现有 trace 摘要与 Profiling 方法；新增独立诊断 CLI、结构化范围/锚点、原事件导航、区间并集及候选表、单元测试 | 本地文件；总预算 30 分钟，软观察 5 分钟；不改共享文档 | 多 rank 不混算、跨流长尾正确、未知边界显式保留、候选不冒充关键路径、合成测试通过 |
| B：上游 PR 查询 | 内置 internal_review | 当前 case-index 方法与固定外部来源；新增本地查询 CLI、少量有来源的原创元数据卡与单元测试 | 可只读联网核实 PR 元数据；总预算 25 分钟，软观察 5 分钟；不改共享文档 | 可按框架/模型/算子检索，来源/审阅/复现等级分开，历史记录不冒充当前 dispatch，离线查询可用 |
| C：显存/KV 分账 | 内置 capacity_tools | 现有容量案例与方法；新增平台中立账本/分页容量诊断 CLI 和单元测试 | 本地显式快照/日志；总预算 25 分钟，软观察 5 分钟；不改共享文档 | 不将 hybrid 等效 token 当池，按 rank/组/块检查、未知输入有界、不预测 SLO 吞吐 |
| D：shape/FLOPs 估算 | 内置 capacity_tools（C 交付后串行） | 现有 Roofline 口径；新增 `shape_flops.py` 与独立测试 | C 已交付，接口独立；总预算 20 分钟，软观察 5 分钟 | 算法量与执行量分开、不默认除 TP、特殊架构不回退成普通 Attention |
| E：CLI 参数兼容 | 内置 internal_review（B 交付后串行） | 现有启动配置约束；离线 argv/help 检查与 `validate-local` 帮助入口 | B 已交付；总预算 15 分钟，软观察 5 分钟 | 不执行命令、精确 flag 检查、未知/动态参数显式返回缺口 |
| F：集成与验证 | 主 Agent 整合文档，内置 integration_review 独立验证 | A–E 实际接口与测试回执；现有 Skill、SOP/映射/工具导航；适用本地检查与独立使用验证 | 先只读复核已交付单元，全部作者停止写入后串行全量测试；总预算 25 分钟，软观察 5 分钟 | 所有入口可发现、方法不重复、无第二套 gate、保留既有修改与失败项 |

主 Agent 直接执行例外为 AGENTS 5.5(1) 规则/上下文读取、(2) 最小入口预检、(3) 派发与控制记录、
(4) 实际 diff 和原始证据复核、(5) 纯本地规则/文档维护及其现成检查。业务实现、深入分析和代码测试不由主 Agent 接管。

## 实现与验证结果（2026-11-13）

| 单元 | 交付与验收 |
|---|---|
| A | `trace_analysis.py`、独立导航 JSON 与 24 项回归；原事件/SHA/边界、跨流 max-end、分组/裁剪/unknown 与候选表已复核。补充 5 分钟导航序列化核验，采用数值 pid/tid 和可读 metadata；未做真实 Perfetto UI/trace_processor 导入。 |
| B | `upstream_pr_query.py`、6 张原创发现卡及 18 项回归；PR 元数据只读核验，全部保持 discovery/current dispatch unknown；主 Agent 抽核已关闭未合并 PR 与 PR943 当前 head。 |
| C | `capacity_analysis.py` 与 12 项回归；显式分账、组/块对齐、full Decode、0 与 unknown 及不跨 rank 汇总已复核。 |
| D | `shape_flops.py` 与 11 项回归；GEMM、Attention QK/AV、非均衡 MoE 投影和显式同 scope 聚合已复核；F_algo 估算与 F_exec/HBM 未知分开。 |
| E | `validate_cli_flags.py` 与 17 项回归；精确声明/alias、参数值与 scope 的未验证范围已复核；五个新增工具加入 `validate-local` help 检查。 |
| F | 独立本地使用复核、5 个更新 Skill 的 quick_validate、全量代码检查和链接检查已执行；原生记录审计的既有债务保持可见。 |

本轮新增 82 项回归。`./scripts/validate-local --all` 运行 409 项测试，结果为 OK（3 项跳过）；
Python 编译、Inventory、Shell/Playbook 语法、帮助入口、11 份原始资产 SHA 和 diff 空白检查均通过。
完整原始输出位于 `/private/tmp/ai-infra-integration-validation-20261113.log`。
5 个更新 Skill 的 system `quick_validate.py` 均通过；独立使用 fixture 与链接检查产物位于
`/private/tmp/ai-infra-independent-20261113/`。
独立 13 条 CLI 使用检查通过，另核验最终导航序列化；16 份文档的 21 个新增本地链接/锚点通过。
具体观察与下一项证伪实验见该目录的 `SUMMARY.md`，70 份外部产物的 SHA 见 `artifact-manifest.json`。

保留的失败与处理：

- A/C 首次 py_compile 使用系统默认缓存路径时被沙箱拒绝；改用批准的临时缓存路径后通过，未放宽权限。
- B 首轮测试对宽关键词结果的期望过窄，修正为准确 AND 查询后通过，未改变检索语义。
- E 首次将三个工具放错 help 检查目录，主 Agent 复核实际 diff 后派回修正；五个实际路径 help 与最终全量检查通过。
- 独立使用复核发现容量文档把“布局名称未知”与“每组分配未知”混为一谈；已明确完整显式每组块需求仍可做有假设上界，未知布局不用于 token→block 推导，保留复现输入和输出。
- 首轮记录审计发现本轮两个公共脚本未登记，已只在 `public_script_files` 登记这两个已实现入口；未扩大历史 `files` 例外。
- 登记后 `--records` 仍因既有 `scripts/dsh_recovery.py` 未登记返回失败，原始输出为 `/private/tmp/ai-infra-integration-records-20261113.log`。该脚本在本轮前已存在于 HEAD 且本轮无 diff，保留债务，不把本轮代码通过写成全项目审计通过。

主 Agent 已按既定例外复核实际源码/diff、定向与统一检查原文、PR 元数据、记录失败及文档；
本轮没有未交付的实现单元。目标机器、真实 trace/计数器及模型精度/性能集成未执行，不产生端到端收益结论。

## 后续：公共恢复工具登记修复

用户要求继续处理上述记录审计问题。工作单元 G 分配给内置 `integration_review`：
输入为 `dsh_recovery.py`、现有测试、执行说明和公共脚本登记规则；先核实其为可复用的离线决策工具，
再限域维护 `docs/process-artifact-inventory.json` 的公共入口清单及 `scripts/validate-local` 的帮助入口。
不修改恢复决策逻辑、记录审计器、历史 `files` 例外或其他模型/案例。
总预算 10 分钟，软观察 3 分钟；产物为最小 diff、`validate-local --all` 的新原始日志和验收结论。
验收要求为该脚本确实符合公共工具边界、现有测试/帮助检查通过，记录审计不再报告此未登记错误。
主 Agent 只做规则/上下文读取、最小入口预检、分配留档、实际 diff/原始回执复核和本页结果维护。

G 已完成并经主 Agent 复核：该脚本是有 20 项既有行为测试覆盖的公共离线建议器，已登记到
`public_script_files` 并纳入帮助入口检查；恢复逻辑、审计器和历史例外未改。
`./scripts/validate-local --all` 退出 0，409 项测试运行结果 OK（3 项跳过），记录与产物审计通过。
新原始日志为 `/private/tmp/dsh-recovery-registration-validation-20261113.log`，SHA256 为
`7c023727efd31999756de801da7097dbcae3b996c21b0d35a83cd4c8abf75b7c`。
前文的未登记失败为修复前历史；当前仅保留 1 条既有产物待核验迁移 WARN，不删除或放宽例外。
本单元无未交付工作，未连接远端、启动服务或执行设备实验。

## 后续：触发与执行链验证

用户要求验证新增能力是否会被正常触发和执行。阶段 H 采用独立场景验证：由本地 fixture 执行者准备
隔离的合成原始材料，由未继承实现对话的新执行子 Agent 接收自然语言问题并从项目规则自行选择方法，
主 Agent 复核实际读取路径、调用命令、原始报告和结论去向；同时验证无需调用时的边界。
准备单元分配给 `integration_review`，只在 `/private/tmp/e2e-trigger-validation-20261113/` 生成材料，
预算 10 分钟；静态路由核查分配给 `internal_review`，只读现有入口，预算 8 分钟。
准备完成后分批派发独立执行单元，每个单元有独立输出目录、12 分钟总预算与 3 分钟软观察；
不提示预期工具名或指定技能，禁止递归委派、联网、远端、真实服务和设备 workload。
所有场景产物留在外部临时目录，既有实现/单位测试不能代替本阶段实际选择与命令执行证据。
发现触发缺口后仅修正对应规则/引用或已复现的实现问题，并用新的独立执行单元复核；
具体预冻结输入、分配、期待行为及原始回执在外部控制记录中维护，不向独立执行者提供期待答案。

### 触发验证结果（2026-11-13）

使用 9 个不继承实现对话的新执行子 Agent，仅提供自然语言目标、材料路径和操作边界，未提示预期脚本或 Skill。
本轮观察到 6 个适用场景均自主发现并实际运行维护入口，3 个边界场景也符合预冻结预期；未发现功能性漏触发或命令失败。

| 场景 | 观察到的发现与执行行为 | 结果边界 |
|---|---|---|
| T1：多 worker 时间线与相邻算子 | Profiling Skill → trace reference → `trace_analysis.py`，生成分层 JSON 与导航 | 两 rank 分组、跨窗裁剪、未知层和融合依赖保留；不将交叠当可省时间 |
| T2：实现快路前查询上游 | 关键算子 Skill → PR reference → `upstream_pr_query.py` | 区分 merged 与 closed-unmerged，所有匹配仍是 discovery，不升级为本平台复现 |
| T3：graph 显存与长输入准入 | 项目路由 → Roofline 离线分账 → `capacity_analysis.py` | 逐 rank/组上界为 3/2，均保留 2 GiB 残差；不计算服务吞吐 |
| T4：per-rank shape 分账 | Roofline Skill → 估算引用 → `shape_flops.py` | 原生 F_algo 与独立复算一致；F_exec/HBM/瓶颈保持未知 |
| T5：已有 argv/help 的版本兼容 | AGENTS → 集成路由 → 性能工具说明 → `validate_cli_flags.py` | 找出 1 个未知 flag，不执行 argv 或 shell 形状值，不当作 readiness |
| T6：失联后的恢复判断 | AGENTS → 执行说明 → `dsh_recovery.py` | 回执为 observe，未启动替代者或控制进程；此项是既有公共恢复工具登记的行为复核 |
| N1：只有 TTFT/TPOT 概念问题 | 读取口径文档，交付记录中未调用 helper 或采集 | 不为概念问题强启分析 |
| N2：同输入已有有效结果 | 仅核对 source SHA、scope 和逐项绑定，复用 sidecar | 未重跑 FLOPs 或补采；仅复用算法分账，不认证运行候选身份 |
| N3：没有可靠阶段/层边界 | 无 annotations 做一次有界分组分析 | phase/forward/layer 全部 unknown，未凭名称或次数均分 |

集中核验：23 份输入 SHA 未变，183 条已记录 SHA 引用匹配，shell 值执行哨兵不存在。
6 个入口的当前源码与前轮冻结版本一致；其中 5 个冷场景直接记录了工具源码 SHA。
T2 缺少执行时工具源码 SHA，保留命令、退出码、原始结果、索引 SHA 和前轮/当前源码一致的旁证，
不补造执行时绑定。N1 及部分前期文件读取没有完整独立原始流，不能据此声称完整系统命令审计。

保留执行例外：T3 首次分析成功后，为补原始流留档重复生成过一次同输入报告；首次产物未覆盖，
两份字节一致，该次不算独立复现或新增证据。随后场景明确复用有效结果，不为补日志重跑。
材料准备阶段最后的空输出目录断言与已并行启动的场景产物冲突；未清理输出或重放准备，已用 23/23 输入 SHA 核验完成冻结。

本轮未修改工具实现或将条件调用改成无条件门禁。入口由 Agent 按项目规则发现和委派调用，
不是 runner 后台自动 hook；每场景一次独立验证不代表未来所有提示词的确定性或生产可靠率。
全部材料为离线合成样例，未覆盖真实服务、硬件、正式模型 gate 或 Perfetto 导入。

原始场景与回执根：`/private/tmp/e2e-trigger-validation-20261113/`；最终机器汇总为
`control/scenario-results.json`，详细复核为 `control/H-VERIFICATION.md`，预冻结任务记录为
`/private/tmp/tool-trigger-validation-20261113-plan.md`。主 Agent 已针对实际命令、原生报告、绑定和边界复核；
记录中的历史失败与证据限制均保留，不以本轮触发通过覆盖模型验收状态。
