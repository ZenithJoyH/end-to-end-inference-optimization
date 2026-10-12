# 可恢复的 Agent 执行记录

借鉴 FlagScale-Agent 的执行前后 Guard、会话锁和反复失败复盘，将这些机制放在项目调用层。
`agent_step.py` 是可选的控制记录工具：不执行 shell/SSH、不启动或停止评测、不自动选 Skill，
也不写模型业务状态。正式结论继续来自原生验收器，Agent 负责依据返回结果推进工作。

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
