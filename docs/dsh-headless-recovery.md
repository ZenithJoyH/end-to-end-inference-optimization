# dsh headless 按能力恢复

本页记录 2026-11-16 的诊断与恢复范围。历史 fallback 只适用于对应任务、失败原因和能力，不是整台机器或后续所有工作单元的永久禁用。恢复不重放已完成工作，不重置原任务预算，也不停止正在运行的合法任务。

## 已核实的故障

| 范围 | 证据与原因 | 当前处理 |
| --- | --- | --- |
| mx-104 | 当前有可用 dsh；默认 bwrap 隔离 PID namespace、重建 `/proc` 和最小 `/dev`，沙箱内进程与设备视图不能当作真实 Host 全貌 | 新固定只读任务 13.93 秒完成；代码编辑/CPU测试仅使用下述已验收收紧 runner。真实 Host PID、设备占用及生命周期核验保留真实 Host 执行层 |
| mx-57 MiniMax | 本地摘要记录两次 `UND_ERR_SOCKET` 后回退；本轮未取得原始 CAP session，也未连接当前项目 inventory 中不存在的 mx-57 | 原会话可在其原有授权/控制入口下为下一新工作单元做受限健康检查；本轮不把其他 Host 的结果当成该 Host 已修复 |

当前已检查入口版本为 `0.2.2-rc.1`。时点版本、CPU成功和历史错误都不能替代后续目标任务的现场核验。

### 继续排查：代码执行准入

2026-11-16 续阶段原生检查发现：mx-104 默认 bwrap 在 root 下继承了 payload 的 capability（含 `CAP_SYS_ADMIN`），虽然 probe 标记 full、mount namespace 独立且 `NoNewPrivs=1`。旧固定 CPU 读取成功不能批准任意代码执行；原方案在 capability guard 停止，失败原件保留。

随后使用任务私有、真实 bwrap + setpriv 的收紧 runner：严格保留唯一 workspace，代码执行时 capabilities 清零、`NoNewPrivs=1`，独立 network namespace，并在根挂载之后将 `/run` 隐藏为只读空目录。104 已通过原生正负例，且实际 dsh 完成一次合成代码修复、目录外 fs-edit 拒绝和一次冻结 CPU 单测通过；测试、canary、runner 和控制文件 SHA 不变。详见 [代码与 CPU 测试恢复配方](dsh-headless-codework.md)。这没有启用 `danger-full-access` 或改变共享安装。

部分目标 Host 没有安装 bwrap，选链回退到 Landlock ABI1；现场自建 canary 证明普通写入虽被拒绝，`os.truncate` 仍能截断目录外文件，不能靠缩小 workspace 补齐。两机已经在任务私有目录部署同一已核静态 bwrap（非 setuid、无 file capability），不改全局 PATH、profile 或系统安装；原生 capabilities/读写/网络/socket 正负例通过。随后两机都实际完成唯一代码编辑、目录外 fs-edit 拒绝和一次冻结 CPU 单测，真实工具输出 `DSH_TEST_EXIT_CODE=0`；仅源文件一行改变，冻结测试、canary 和控制文件保持。不能把新私有 runner 的资格转写为旧默认 Landlock 已修复。

### API 断流的进一步诊断

已加入 [任务级诊断 hook](../scripts/dsh/README.md)，只记录固定白名单的请求阶段、相对耗时、HTTP 状态、进程内 socket 序号及错误码；不改 endpoint、协议、dispatcher、重试或权限，不记录请求内容与凭据。5项 mock 与原生 loopback 对照均通过；一次真实 synthetic 任务正常完成，3个请求 HTTP200、http/1.1、0重试，未复现历史断流。

现场 Node24/SDK 对照中，响应头前断开得到 `fetch failed` 变体，HTTP200后响应体中断精确复现历史 `terminated: other side closed (UND_ERR_SOCKET)`。这支持“响应体传输中断”的推断，不能唯一定位网关、上游或中间网络。合法 SSE `[DONE]` 后 SDK 主动取消 body 也会产生底层 `request:error`，所以必须结合最终任务/重试/工具证据，不能把所有此事件当作断流。网络根治仍未证实。

## 已落地的静态审查配置

使用 [任务级 overlay](../scripts/templates/dsh-static-review.patch.yml) 与 [调用说明](../scripts/templates/dsh-static-review.README.md)，不改共享 profile。内容 SHA256：`f538c9dd3222071ce93451906b35d31265799178e1dab3547a227000c654c80a`。目标环境已核原生工具 schema 恰为 `glob`、`grep`、`read`，不是仅在提示词中禁止 shell；各有一次真实 read 成功回执。grep/glob 的实际任务行为未在本次动态冒烟中逐项测试。

stdin 可传 overlay（`--patch /dev/stdin`），任务作为明确的位置参数；因此无需为了采用配置在远端新建配置文件。模板只适用于已核对插件 ID/名称的版本；后续新增工具也须复核真实工具表。它不提供任意代码执行或写入能力，也不把 partial Landlock 变成 full enforcement。

进一步将内部文件内容通过 dsh 发送给外部 provider 的一项测试被自动审批拒绝，未启动；不能将此前 hash 读取授权当作内容外发授权。该动作未重试。部分目标 Host 最终改用本次生成的两行纯测试文字，审批允许后完成动态验证。后续使用仍限本次生成的测试文字或任务原本明确允许交给该 provider 的输入。

## 下一工作单元的派发规则

1. 先核验旧任务和关联写入者已停止，或确认新工作单元资源与写入范围独立。已有有效结果直接复用，不为“改用 dsh”重跑。
2. 对已核实为可用的能力使用全新短 session，明确输入文件、独立产物、工具范围、软观察/总预算/准确清理。只读任务选择 `--permission-mode read-only --approval-policy never`；编辑/测试按[收紧 codework 配方](dsh-headless-codework.md)仅授予确切私有工作根，不能只把模式改为 workspace-write 而沿用未验收 backend。实际参数以目标版本 `--help` 为准。
3. 从小的可验收工作单元恢复，优先文件读取、静态分析和独立补丁生成。全新短任务成功只说明该能力当前健康；不要追认旧业务任务成功或声称网络根治。
4. 默认 API step 内部重试与外层 session 恢复分别计数，共用总预算。失败后检查持久 session 的 `assistant/attempt`、`llm/retry`、`llm/retry-started` 和最终结果；headless CLI JSON 不投影内部 retry，不能用“没有 retry 行”断言未重试。
5. 短任务也发生相同断流时，保留错误与部分产物，按原有有界恢复规则处理。不要无限重试、提高重试上限、自动重放整个业务任务，或把失败计数改写为成功。
6. `read-only` 限制文件写入，不能禁止 Python 导入、设备初始化或通过可见 Docker socket 操作服务。禁止执行的静态审查必须禁用执行工具或使用已审固定读取工具；单靠 prompt 禁令不足以提供技术隔离。
7. 沙箱缺少真实 Host PID/设备视图时，仅该能力回退，其他可独立交付的 CPU 工作继续 dsh。不要依据沙箱 `/proc` 声称 Host 空闲、清理进程或启动设备争用任务。

## 本次明确拒绝的修复

- 没有证据支持增加传输重试次数；现有重试机制已生效。
- 不用 `danger-full-access` 或关闭沙箱恢复 Host 视图。
- mx-104 已安装 Landlock 探测结果是 `partially enforced (older ABI)`，不能充当 full enforcement 的等价替代；部分目标 Host 实际工具输出同样存在 partial 警告。外层 stderr 为空不代表工具内部没有警告或非零退出。
- `sandbox-local.runnerCommand` 是自定义 runner 接口，不是 backend selector；填 `/usr/bin/false` 或直接填 Landlock 程序不会形成安全的自动回退。
- 不为原子替换方便而放开整个 `/public-flash`。授权额外父目录前须考虑目录内其他文件的技术可写范围；优先生成补丁后受控应用。

## 证据与边界

控制文件、原生检查、smoke 事件、持久 session 与脱敏回执保存在各任务批准的外部产物目录；当前项目只保留方法和能力边界。

本次未修改远端共享安装、profile、模型源码或服务，未启动模型/GPU工作。短 smoke 不能证明长期稳定性；后续真实工作单元应继续记录成功、断流、恢复和失败。

官方同版本参考：[重试契约](https://github.com/deepseek-ai/deepseek-harness/blob/dsh-v0.2.2-rc.1/packages/llm/llm-retry/README.md)、[headless JSON 投影](https://github.com/deepseek-ai/deepseek-harness/blob/dsh-v0.2.2-rc.1/packages/bundle/headless/src/json-stream.ts)、[任务级 CLI overlay](https://github.com/deepseek-ai/deepseek-harness/blob/dsh-v0.2.2-rc.1/apps/cli/README.md)。现场安装与原始回执优先于文档。
