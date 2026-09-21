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
- `performance-run`：`compare_performance.check_run` 核验 `contract` 下每个 `records` 的原始指标、输出 SHA、请求与绑定。仅证明单轮数据有效，不产生加速比或最终验收结论。
- `performance`：`compare_performance.compare` 对 `contract` 和 `records` 做完整比较；`failed/incomplete` 都不能关闭为通过。

`scope.model/host` 必须与原生 service 对应。正式 performance 必须前置 accuracy gate、使用
`scope=formal` 的原生 comparison contract，并由原生比较器核验 candidate 自带的 accuracy gate。
accuracy journal 当前只支持 `formal-gate/gate-check`；baseline-sanity/minimal-regression 继续原有流程，
不能用 service 格式检查替代回归完成证据。所有前后检查的 manifest/contract 必须列入 context_files。
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
