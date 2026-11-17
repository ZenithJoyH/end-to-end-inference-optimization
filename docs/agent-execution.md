# 可恢复的 Agent 执行记录

借鉴 FlagScale-Agent 的执行前后 Guard、会话锁和反复失败复盘，将这些机制放在项目调用层。
`agent_step.py` 是可选的控制记录工具：不执行 shell/SSH、不启动或停止评测、不自动选 Skill，
也不写模型业务状态。正式结论继续来自原生验收器，Agent 负责依据返回结果推进工作。

## 具体执行必须委派

本节落实 [AGENTS.md 第 5.5 节](../AGENTS.md#55-主-agent-协调与-dsh-headless-执行)。主 Agent 负责规划、
协调、观察、证据复核和验收；除该节列明的直接执行例外外，可独立交付的具体执行必须委派。
默认使用对应目标机器上的 `dsh headless`，按下文恢复流程回退到内置子 Agent。源码与执行路径分析、
日志/trace 分析、代码及实验脚本/配置编写、容器复刻与环境准备、服务启动/调整、算子实验、
正确性回归、profiling、性能测试和结果统计均属于执行工作，仍须满足原有授权、隔离及验收门禁。
纯本地任务保持本地执行，其中可独立交付的具体分析、实现和测试委派给本地子 Agent；不新增远端授权。

### 执行前分配与阶段核查

- 每个阶段开始时，在既有阶段或实验记录中列明工作单元、执行者、输入及已验证状态、预期产物、
  依赖与资源、时间预算、成功/停止条件和验收标准。远端任务同时绑定准确的 Host、容器、工作目录、
  实际导入路径与读写权限；子任务不得扩大范围、递归委派或提交/推送代码。
- 可委派的工作尚未分配时，先派发再执行；不得由主 Agent 先做完，再补一次名义上的委派。
  同一源码副本的写入、共享设备测量及同一服务启停按原规则串行，独立且资源不冲突的任务才可并行。
- 小型执行任务可合并派发。任务较小、命令只读、便于顺手完成或执行器发生故障，均不单独构成
  主 Agent 接管的理由；不得将连续执行工作拆成多个单步操作来规避委派。
- 阶段结束时，在同一记录中汇总子 Agent 已交付与未完成的工作单元、各自产物位置、主 Agent
  直接执行的例外及原因和验收结果。按独立产物核查分工，不以调用次数、命令数或 token 数代替工作量，
  不为提高委派比例重做已完成工作，也不把完整优化任务一次性交给无人复核的执行者。
- 分配和例外使用既有任务/阶段记录，控制输入与事件继续保存在批准的控制产物目录；不新增模型
  业务账本，不要求为采用本节而启用可选的 `agent_step.py`，也不声称工具已自动强制这些分工。

### 主 Agent 直接执行的限制

主 Agent 直接操作仅限 `AGENTS.md` 第 5.5 节列明的规则及上下文读取、最小只读预检、任务派发与观察、
产物回收、验收复核、纯本地规则/文档/记录维护、授权范围内的紧急控制及符合条件的单步辅助操作。
每次直接执行须简述例外类别、原因和范围，写入既有任务、阶段或实验记录；纯本地规则维护可在
当前任务说明中记录。记录例外无需新增审批，但不能放宽原有授权、命令审批或共享环境保护要求。

只读预检用于精确派发、恢复和资源协调，不包括大范围源码搜索、完整日志扫描、trace 解析或批量统计。
任务控制命令不得夹带由主 Agent 编写的业务实现或实验脚本来替代委派。验收允许查看实际 diff、
针对性核对执行路径和原始证据、核验绑定与回执，以及调用不启动新 workload 的现成原生校验器；
需要深入补充分析、修改实现或重跑测试/评测时，必须再次委派。纯本地规则、文档和记录维护例外
不包含业务代码、实验脚本或评测/控制工具的实现；主 Agent 不得以验收或维护名义重做具体执行。
子 Agent 的完成自述和退出码 0 仍不能替代精度、graph、端到端性能及原生验收结果；主 Agent
必须复核实际交付和证据，保留失败与未完成项，最终保留/回退和验收决定由主 Agent 负责。

## 先冻结接口，再执行

`interface.json` 声明能力 ID、接口版本、显式操作集合及结果契约。
`scripts/skill_bundle.py inspect --skill-dir /absolute/skill --capability-id ID --selection MODE`
验证身份和操作，并输出完整文件 SHA 集合；缺少模式、资源或身份不匹配返回 `incomplete`。
路径相同和 Git HEAD 相同都不能证明内容相同。缓存文件不参与指纹，bundle 内不允许符号链接。
项目入口不是可独立安装的公共 bundle：项目外部依赖由下面的 context/source 校验冻结。

`skill_bundle.py` 初始实现与本轮 Hub 的同名工具保持一致，现由本项目维护，不运行时 import Hub。
`agent_step.py` 在适配和优化项目初始同版，`project_gates.py` 各自拥有原生校验映射。
任何后续同步都须显式比较和运行回归，不能自动跟随另一个工作区。

## 一个操作对应一个唯一 run

调用方准备 JSON spec，下方给出本项目示例。所有路径必须换成已核实且批准的绝对路径；
不要把示例路径直接作为生产目标。`context_files` 只列本轮冻结输入，不列会持续增长的日志。
工具另外冻结自身、校验器源码及相关项目规则。Skill/配置/校验代码发生变化后返回复查要求，
不能通过改写旧哈希继续声称是同一轮。

```sh
python3 scripts/agent_step.py begin --spec /approved/case/step-spec.json --run-dir /approved/case/control-run-001
python3 scripts/agent_step.py observe --run-dir /approved/case/control-run-001 --evidence /approved/case/progress-snapshot.txt --completed 32
python3 scripts/agent_step.py check --run-dir /approved/case/control-run-001
python3 scripts/agent_step.py finish --run-dir /approved/case/control-run-001
```

`begin` 验证接口、冻结内容、登记资源占用并执行前置检查；通过后仅为 `ready/incomplete`。
调用方随后按原有项目流程启动所选工作。`observe` 记录真实进度快照及单调递增完成数；日志变长
不等于有效进度，不要用重复行数或重试数冒充已完成样本。
`finish` 重新核对身份并执行原生完成校验，只有通过才成为 `verified/passed`，同时冻结完成回执。
`check` 不发起新评测；即便已完成，也会重读回执和原生依赖，发现删除、替换或篡改返回 `incomplete`。
旧进度快照只是观察记录，不能作为正式通过证据。

CLI 的退出码 0 表示控制操作成功，**不等于验收通过**；必须读取 JSON `status`。
复查原因或校验错误返回 2。工具异常同样失败关闭，不通过模型自评或宽松兜底来通过 gate。
原生校验结果只证明读取到的证据绑定，不代替现场进程、容器和设备取证。

## 时间、错误与恢复

- `budget_seconds` 是本轮预算；`stall_seconds` 从最近一次完成数增长开始计时。0 表示不设置。
- 超预算、长期不增长、连续两次相同 `error_signature` 返回明确复查原因。长期运行但持续增长
  不会仅因总耗时被标成停滞；超预算仍单独提示。
- 这些值是调用方检查时计算的决策信号，**不是后台 watchdog**。调用方决定是否停止准确的
  客户端、缩小同配置实验、证伪一个假设或修改方法，不能无条件重试，也不能自动停止模型服务。
- 接手已有任务先 `check`，核验当前服务/进程/证据与记录对应，再观察或结束原 run；不要重放启动命令。
- 失败可执行 `fail --note '实际失败原因'`。此操作不会释放设备占用，避免误以为远端进程已经停止。

## 执行环境适配：Codex 与 dsh

本项目的规则、Skill、原生 gate 和 `state.yml` 记录与环境无关；Codex 与 dsh 只在执行器接口和进度
通知上不同。迁移或并行使用时按下表映射，不因更换环境降低门禁、改写证据或复制账本。

| 能力 | Codex | dsh | 共同要求 |
|---|---|---|---|
| 远端执行 | 原任务/子 Agent 机制 | `dsh headless`，可指定 `--permission-mode` | 派发到明确 Host，边界和产物精确；不猜接口 |
| 权限与沙箱 | approval/sandbox 配置 | permission mode 与命令审批 | 记录实际模式；只读任务不授予写权限 |
| 会话接续 | thread/session 恢复 | `--session-id` 或同 session 继续 | 先确认旧执行已停止、写入者唯一，再决定恢复 |
| 内置回退 | 原生子 Agent | `subagent`；`subagent_fork` 继承上下文 | 交接已核验状态和未完成工作，不重置预算 |
| 进度通知 | heartbeat/automation | 自动创建的进度定时任务或后台 job | 长评测自动启用、无需逐次审批；同一评测只保留一个监控，终态停用 |
| 执行控制记录 | 任务记录 | 后台 job / 共享任务板 | 只作控制，不替代 `state.yml` 业务账本 |
| 技能发现 | 读取仓库内 `SKILL.md` | 读取仓库内 `SKILL.md` | 不依赖全局同名 Skill，不安装副本 |

- 每次任务开始前核实当前执行环境的入口、版本与 help：父 Agent 与远端执行器可能是不同版本
  （例如本机与远端 rc 版本不同），参数以实际 help 为准；缺失或权限不足按恢复规则回退，不自动安装。
- 首次任务确认执行环境已加载项目 `AGENTS.md`；未自动加载时先完整读取，再冻结目标、契约和分工。
- 长评测需要后台跟进时自动启用进度监控，无需逐次审批；dsh 定时任务默认 30 分钟、目标为当前
  任务/session，并记录任务 ID 与终态清理证据。调度不可用不阻断评测，改为前台或后台 job 并保留
  原生进度产物。Codex 旧 automation ID 在 dsh 下不可操作，只作为历史证据记录，不假装已暂停或复用。
- 历史记录中的 `codex/*` 分支、Codex 作者身份和 `~/.codex` 产物路径保持原样；新工作使用当前环境
  可核验的身份与命名，不重写历史证据。

## dsh 恢复与回退

本节落实 `AGENTS.md` 第 5.5 节。主 Agent 根据现场证据编排恢复；`dsh_recovery.py` 只输出建议，
不检查远端、不发命令、不重试、不停止进程，也不替代原生验收器。未接入本节的旧控制器不会自动改变行为。

执行器故障不自动允许主 Agent 接管具体执行。不可恢复或恢复次数耗尽后，先核实旧执行及关联
写入者已停止、交接范围和剩余预算，再将未完成工作交给内置子 Agent；预算耗尽先重规划，副作用
未知先核验，不得借回退重置预算或绕过门禁。内置子 Agent 也无法承担时，在既有记录中说明能力
缺口并调整计划，主 Agent 只能执行第 5.5 节明确例外内的操作，不自动安装工具或扩大权限。

### 先区分失败发生在哪一层

| 已核验的状态 | 下一步 |
| --- | --- |
| SSH 断开、远端状态未知 | 重连并核实原任务；不要把 SSH 退出当成 dsh 退出，也不要直接派发第二份任务。 |
| 远端仍在执行 | 继续观察已有任务。超过软观察时限且有实质进展时，在总预算内继续；无进展先定位等待原因。 |
| 调用方总预算耗尽 | 按预冻结范围停止准确的任务执行及关联子进程，复查现场并重规划；不能通过恢复或 fallback 重置预算。 |
| 执行已结束，已有有效产物 | 先收集、核验并复用产物；缺少最终文字不要求重新计算。异常退出本身仍如实记录。 |
| 瞬时故障，尚未启动或已确认终止且无副作用 | 在冻结的总预算内有界重试；保留同一 task-id、独立 attempt-id，不能并发派发。 |
| 已结束，有有效 session 和检查点 | 核实该安装版本实际支持恢复，再以原上下文恢复；检查点仅是接续线索，不能视为验收通过。 |
| 未安装、配置/权限错误或无法恢复 | 报告根因，确认旧执行及写入者已停止后自动回退；不自动安装、不扩大权限。 |
| 测试失败、精度不达标或正式证据无效 | 返回任务失败/未完成，按原诊断及验收流程处理；换执行者不能抹掉失败或绕过 gate。 |

必须区分 dsh 自发退出和控制器主动终止。即使进程返回码为 0，若记录有 controller timeout 或 error 事件，
也不能判定调用成功。

### 派发、观察和交接

- 长分析使用已批准工作根内的独立远端控制进程及持久化输入/事件/产物，SSH 只负责启动和观察。
  启动确认丢失时，先按 task-id/attempt-id 查找已有任务，不能立即再启动一次。标准输入使用已保存的
  任务文件，标准输出/错误落到唯一文件，不依赖交互终端或可随连接关闭的管道；无需引入后台服务或修改系统配置。
- 任务拆成可交付的小单元，例如先验证 trace/rank 身份、再提取确定性统计、最后做归因与复核。
  大文件扫描和重复统计优先运行参数化解析器，不让模型在多个步骤里反复输出整段 trace 或源码。
  只读任务可以在授权的控制产物目录保存执行器日志/计算结果，不因此取得模型源码写权限；任务要求绝对禁止写入时由控制器回收 stdout。
- 派发前冻结软观察时限、无实质进展时限和整个子任务的总预算。启动、各次恢复和内置回退共用总预算；
  预算不足先缩小任务或重新规划并保留旧记录，不能偷偷重置计时。软观察时限仅触发检查，不直接触发 kill。
  日志增长、模型思考文字和 token 消耗不能单独算实质进展；应核对已完成的文件/阶段、命令结果或可验证的中间产物。
- 每次启动保存 task-id、attempt-id、Host/容器、工作目录、任务/规则/源码指纹、PID/PGID 与进程启动身份、
  dsh session-id、权限及产物路径。不能只按 PID 或名称判断原任务仍活着；恢复前核实 PID 复用、同一机器及同一上下文。
- 同一 session 不允许两个恢复者。只有原 dsh 和关联任务子进程均已停止、写入范围已核验，才考虑
  `--session-id` 接续或切换执行者；仍在运行的 pytest/benchmark 等子进程应继续观察或按授权准确停止，不能再跑第二份。
  已确认部分写入可交接，但不允许从头重放可能有副作用的步骤；无法确认时先 reconcile。
- 自动恢复最多 2 次，瞬时故障采用有界退避并占用同一总预算；同一错误连续 2 次停止机械重试。
  入口缺失、权限/配置问题和任务自身失败不走瞬时重试。恢复失败后按相同证据要求交接到内置子 Agent。
  每个 attempt 保留结果及失败原因；不删除失败、不刷新旧证据 SHA，不把回退后的成功改写成原 dsh 成功。

### 本地决策入口

当前故障分类与按能力恢复方法见 [dsh headless 按能力恢复](dsh-headless-recovery.md)。历史 fallback 不构成整机永久禁用；仅在原有授权、旧执行状态、能力和总预算均核实后，为新的安全工作单元恢复已验证可用的 dsh 能力。不得把受限 CPU 冒烟成功扩大为真实 Host / GPU 执行资格。

`scripts/dsh_recovery.py --snapshot /absolute/control/dsh-snapshot.json` 将调用方已核验的状态映射到
下一步动作；完整字段和 CLI 示例见工具帮助。状态未知、上下文漂移、旧写入者未停止或副作用不明时，
优先核验而不是启动新执行者。即使输出 `fallback`，主 Agent 仍须按原边界完成交接并独立验收；
输出 `resume_existing` 也不证明该版本恢复功能已实际验证。快照及决策回执放在批准的外部控制产物目录，
不创建新的模型业务账本，不改变 `agent_step.py` 的职责。

## 协作占用与产物位置

`resources` 和 `lease_registry` 是可选的合作式占用登记。多个任务或项目必须使用**同一个**可写
registry 和同一规范资源 ID（例如同一 Host/设备 UUID）；不同目录或不同别名无法互斥。
登记与 journal 更新用 `flock` 串行化；要求文件系统支持可靠文件锁。它不是 GPU 调度器，也不是
跨多机的分布式锁，不能发现未接入登记的任务。

只有终态才允许 `release --evidence /approved/case/resource-inspection.txt --note '核实精确进程退出及资源已空闲'`。
释放证据须由调用方现场检查得到；工具只记录其路径和哈希，不声称自己检查过远端设备。
无超时自动抢占。遗留 owner 先核实对应进程，不能因会话断开就删除占用文件。

spec、run.json、进度快照和 registry 放在批准的控制/外部 case 目录，不放入 `models/`。
既有业务记录只引用所选操作结果、证据路径和必要哈希；不创建第二套模型阶段或历史目录。
工具不改变项目既有远程操作、服务生命周期与审批边界。

## 本项目原生 gate 与示例

- `service`：`acceptance.validate_service(formal=False)` 核验 manifest 格式及身份，允许原生工具支持的非正式服务。
- `accuracy`：`acceptance.check_gate` 校验 gate 与当前 service manifest；对应 `manifest`、`gate`。
- `performance-run`：`compare_performance.check_run` 核验 `contract` 下每个 `records` 的原始指标、输出 SHA、请求与绑定。分别核验原始输入计划的 SHA 和规范化有效计划的一致性；默认值补全和序列化排版不会被误判为 workload 改变。无输入来源的旧回执仍要求精确快照 SHA。回执中的服务身份集合必须与冻结的 `services` 集合完全一致。仅证明单轮数据有效，不产生加速比或最终验收结论。
- `acceptance`：测量结束后只读调用 `final_acceptance.validate`，要求 scope 的 `case_id/baseline_id` 匹配预冻结项目范围。入口和清单见 [性能工具](../evaluation/performance/README.md#项目范围冻结与最终验收)。
- `performance`：`compare_performance.compare` 对 `contract` 和 `records` 做完整比较，并执行同样的 `plan`/`services` 精确绑定；`failed/incomplete` 都不能关闭为通过。

`scope.model/host` 必须与原生 service 对应。正式 performance 必须前置 accuracy gate、使用
`scope=formal` 的原生 comparison contract，并由原生比较器核验 candidate 自带的 accuracy gate。
accuracy journal 当前只支持 `formal-gate/gate-check`；baseline-sanity/minimal-regression 继续原有流程，
不能用 service 格式检查替代回归完成证据。所有前后检查的 manifest/contract/plan、预期服务
manifest 和前置 accuracy gate 必须列入 `context_files`。
完成后冻结 gate/run-record 本身；其依赖仍由原生验证器逐次核验。业务结论写回原有
`baseline/optimize/acceptance` 的 state、实验 Markdown 和摘要，不由 journal 自动推进。

以下是 targeted 单轮有效性检查；若要报告相对收益，应使用 `performance` 收齐可比角色的记录。

```json
{
  "schema_version": 1,
  "run_id": "targeted-001",
  "owner": "current-task",
  "capability_id": "e2e/performance",
  "selection": "targeted",
  "scope": {
    "model": "Example",
    "host": "HOST-01"
  },
  "skill_dir": "/absolute/project/skills/inference-performance-evaluation",
  "context_files": [
    "/approved/case/service.json",
    "/approved/case/plan.json",
    "/approved/case/comparison.json"
  ],
  "before": [
    {
      "kind": "service",
      "manifest": "/approved/case/service.json"
    }
  ],
  "after": [
    {
      "kind": "performance-run",
      "contract": "/approved/case/comparison.json",
      "plan": "/approved/case/plan.json",
      "services": [
        "/approved/case/service.json"
      ],
      "records": [
        "/approved/case/measurement/run-record.json"
      ]
    }
  ],
  "budget_seconds": 1800,
  "stall_seconds": 600,
  "resources": [
    "HOST-01/device-uuid"
  ],
  "lease_registry": "/approved/shared/agent-leases"
}
```


## 人工暂停、接管和恢复

用户可直接说“暂停，我来调整”“这一步我已手动完成”“按这个配置继续”，由 Agent 整理命令和证据；
不要求用户填写 JSON。人工指令优先于自动计划。存在 run 时，Agent 在下一次远端变更或发起请求前
执行 `check`，只有 `automation_allowed=true` 才可继续。`paused/manual` 是正常控制状态，数值验收仍为
`incomplete`，不计成失败。没有 journal 的旧任务先把暂停/接管意图写入当前案例，再补执行记录。

| 人工意图 | 操作 | 保留/核验 |
|---|---|---|
| 暂停，稍后继续 | `pause --note '用户要求等待'` | 保留证据与资源登记；暂停期间不累计 Agent 活动预算 |
| 接管部分步骤 | `takeover --actor 用户 --note '手动压测'` | 自动化停止发起变更；用户操作可产生原生回执 |
| 原配置继续 | `resume --note '用户要求继续' --evidence <新现场检查>` | 冻结输入不变、前置 gate 重验；保留已完成轮次，不重启工作负载 |
| 配置/源码/契约已改变 | `supersede --note '用户调整 TP/参数…'` | 原证据与原因保留，旧 run 不刷新 SHA、不标成性能失败 |
| 手工完成评测 | 恢复后 `finish` | 消费实际原生回执，执行相同验收器，不因手工完成而免检或重跑 |

例如：

```bash
python3 scripts/agent_step.py takeover --run-dir /approved/case/run-001 --note '用户接管服务参数调整'
python3 scripts/agent_step.py check --run-dir /approved/case/run-001
python3 scripts/agent_step.py resume --run-dir /approved/case/run-001 \
  --note '用户要求继续，已核验原服务和配置未变' --evidence /approved/case/fresh-inspection.json
```

这些命令仅更改控制记录，不向远端发信号。Agent 应报告仍在运行的精确服务/客户端，以及哪些动作已经暂停；
停止既有客户端或服务仍按用户意图和远端操作规则执行。监控在暂停/接管期间保持只读，不自动恢复评测。
`resume` 需要人的明确继续指令；等待时间、进度增长和新文件出现都不能替代该指令。

变更后恢复时，Agent 先整理新旧差异，并明确证据影响：

- 仅人工观察/执行，输入与服务未变：保留原 run，原生回执验证后接续。
- 仅服务重启：按精度 rebind 流程获取新绑定，新的性能实例使用新 run。
- 源码、参数、设备、workload 或门槛改变：新契约/新 run，按影响范围补最小回归、正式精度和性能。
- 仅控制工具或规则升级：新 run 重新消费并校验现有原生证据；通过时无需仅为 journal 重跑模型。

旧 run 可用 `supersede` 关闭；确认相关进程已停止或资源已空闲后 `release --evidence … --note …`。
随后使用 `begin --parent-run <旧run目录> --spec <新spec> --run-dir <新目录>` 建立有来源的新记录。
同一案例内 successor 必须保持 scope；换 Host、TP/设备拓扑或 baseline 身份时创建新案例。
资源登记不会因暂停、接管、超时或 supersede 自动释放，避免另一个任务误用仍被占用的设备。

人工可以改变目标、场景或阈值，但新规则只对新实验生效；历史结果保留当时契约。
人工允许继续诊断与正式验收通过是不同结论，最终分数/覆盖/证据检查不能靠手工修改 passed 绕过。
