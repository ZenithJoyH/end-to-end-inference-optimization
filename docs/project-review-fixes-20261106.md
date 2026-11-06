# 项目复审修复（2026-11-06）

范围：公共评测/控制工具、审查发现的记录错误、88 个过程文件及 Hy4 大型状态账本。
没有连接目标机器、发送模型请求或修改原始 `test/` 资产；修复完成后按用户要求分批提交，未推送。
工作区已有修改保持原状；活跃 DeepSeek 任务自行补齐了缺失链接，本次未覆盖该记录。

## 提交边界

本轮提交公共工具、对应测试与文档、54 个已跟踪过程文件的归档删除及两个 Qwen38 案例的归档说明。
另外 34 个归档文件原本未跟踪；归档副本和校验回执继续保存在本地 `.cache`，不进入 Git。
Hy4-testing、Qwen3VL topk PR、Qwen3.6 main-config 和 Tele 只读案例原本均未纳入 Git，
本轮对这些记录的字段、路径、链接和账本精简修复保留在本地。单独加入修改文件会缺少配套记录，
整案导入又会包含大量本轮之前的实验成果，因此本次不将这些案例首次纳入版本控制。
其他任务已有或新增的修改不在本轮提交范围内。

## 修复内容

| 问题 | 修复及验证边界 |
|---|---|
| 实际 D16 可以通过标为 D1024 的最终验收 | 固定四场景保留 ID 在计划执行和比较时统一校验 P/D/C/N、Mixed、finite-batch、`ignore_eos=true`；原生输出仍须逐请求满足 D1024。自定义业务场景保留自然 EOS 支持 |
| 镜像/挂载失败仍可发起性能请求 | 所有性能计划角色在请求前复用完整服务身份与隔离门禁，已绑定运行证据在请求前、逐轮及结束时核验 SHA。文件校验不代替远端现场取证 |
| Ctrl+C 被当作可重试错误 | 维护包装层传播取消并清理评测进程组/计分进程，并行入口取消全部当前分片。普通非零退出仍按原策略重试；原始 runner 字节不变 |
| Shell 语法检查只覆盖第一个文件 | 逐文件调用 `bash -n`；回归向每个入口注入语法错误，验证检查非零退出 |
| 实验字段、路径和索引不一致 | 修正 Hy4 12 处文档路径、Qwen3VL 3 个实验 ID 字段。DeepSeek 的 refactor-009 链接由并行原任务补齐。旧 schema 未被追认为新的运行/验收事实 |
| 过程文件混入长期记录 | 88 个文件逐字节备份、归档并核对 SHA 后移出记录目录；更新 4 处文件链接和各案例归档导航。既有 257 项待迁移材料与已有 history 保留，未扩大白名单 |
| 状态与恢复摘要膨胀 | Hy4 仅外置 90 个大型准备/运行回执字段；22 个实验、83 次规划及身份、current、指标、决定保留。账本由 5,565,570 降至 1,744,145 字节，默认摘要由 24,692 降至 1,773 字符 |

`case_records.py summary` 默认输出核心状态和详细字段的定位信息，`summary --full` 保留完整当前视图。
`detail --pointer` 按 SHA 核验后解引用外置字段；同级导航摘要必须与归档一致，发生漂移时拒绝静默选择旧值。
文件精简通过完整重建比较，未用删减失败实验或旧决定换取文件变小。

## 归档与恢复

- [过程材料迁移清单](../.cache/model-record-archives/20261106-project-review-fixes-artifacts-001/migration-manifest.json)：88 个原文件的路径、SHA、大小、归档副本及导航改动。
- [过程材料完整备份](../.cache/model-record-archives/20261106-project-review-fixes-artifacts-001/before.zip)及[整包 SHA](../.cache/model-record-archives/20261106-project-review-fixes-artifacts-001/before.zip.sha256)。
- [记录精简清单](../.cache/model-record-archives/20261106-project-review-fixes-records-001/manifest.json)：修改前完整记录、Hy4 外置快照、90 个字段指针、校验脚本与 SHA。
- [无损重建回执](../.cache/model-record-archives/20261106-project-review-fixes-records-001/roundtrip-result.json)。

归档使用此前已有的 `.cache/model-record-archives` 本地归档区，未纳入 Git，仅在当前工作区可用。
这些是必要恢复证据，不是可删除的普通缓存；迁移工作区时应连同引用一起转移。
恢复前核验整包与逐文件 SHA，先解压到新目录并比较当前内容，不能覆盖后续修改或直接重跑历史脚本。
本次未验证远端同名副本，也未清理远端材料。

## 验证

最终 `./scripts/validate-local` 全部通过：307 项测试中 304 项通过、3 项可选接口测试跳过；
Python 编译、Shell/Playbook、CLI 帮助、11 份原始资产 SHA、diff whitespace 和记录审计通过。
记录审计仅保留原有 257 项待迁移告警，不存在本次发现的 88 个违规过程文件。
另核验 11 份涉及文档中的 168 个本地文件链接，均可解析；88 份归档副本与原文件备份逐字节一致。

首次完整运行发现进程组存在性探针返回 EPERM，失败日志保留。修复后将该状态视为尚未证明退出，
继续有界等待；仅 ESRCH 确认消失，持续无法确认或实际发信号权限不足仍报错。新增边界回归及真实
孙进程取消测试后完成上述最终检查。记录解引用另增加不可变导航摘要漂移的拒绝测试。

[完整验证回执](../.cache/model-record-archives/20261106-project-review-fixes-artifacts-001/validation/result.json)
记录两次日志路径及 SHA；[最终检查日志](../.cache/model-record-archives/20261106-project-review-fixes-artifacts-001/validation/final.log)
保存全部检查结果。

所有性能证据为合成夹具；取消回归仅启动本地 Python 进程。项目工具检查不能替代真实模型精度、
graph 或设备性能验收，也不追认历史性能记录满足新增门禁。
