# Qwen3.6-27B / mx-104 verify 容器代码整理

2026-10-22（Asia/Shanghai）。用户指定 `mx-104 / qwen3.6-27B-verify` 为已优化环境，并选择“保留现有实现，整理代码、补丁包和说明”。最初按diagnostic范围完成代码保全与静态梳理；随后按用户明确要求，仅将该容器私有Plugin更新到最新release/0.2，保留现有优化。未启动模型服务，不继承本地旧历史的精度/性能结论。

## 报告与交付

- [env-003 Plugin迁移结果](../../../models/Qwen3.6-27B/metax/20261022-qwen36-27b-mx104-code-audit/optimize/env-003.md)：当前HEAD `7cb55994`，版本 `0.2.2rc2.post1+g7cb559947.d20261022`，原两文件优化保留；10项CPU测试和真实MetaX路由通过。增量包为远程case下 `env-003-release02-bundle.tar.gz`（约2.11MB），含完整Git基线bundle、补丁、说明、校验和回退入口。

- [完整代码与优化点报告](../../../models/Qwen3.6-27B/metax/20261022-qwen36-27b-mx104-code-audit/optimize/audit-001.md)
- [vLLM 源码迁移核验](../../../models/Qwen3.6-27B/metax/20261022-qwen36-27b-mx104-code-audit/optimize/audit-002.md)：4737个受跟踪文件与容器内v0.20.2基准逐文件一致；无隐藏修改、无新增源码。相关扩展已在Plugin，当前无需搬迁。
- [结构化状态与验证](../../../models/Qwen3.6-27B/metax/20261022-qwen36-27b-mx104-code-audit/optimize/state.yml)
- 远程包：`/public-flash/jinghao/qwen3.6-27B/20261022-qwen36-27b-mx104-code-audit/code-review-bundle.tar.gz`。
- 同目录 `delivery/` 保存展开后的说明、补丁、快照、逐文件清单、校验结果与专题审阅；`SHA256SUMS` 用于包内完整性校验。

## 已确认的主要内容

| 内容 | 容器事实 | 结论边界 |
|---|---|---|
| Plugin 连续 KV prefill | 原相对d1653d9的唯一语义优化，现已等价迁移到7cb55994，2文件；支持长单 prefill 的连续KV路径，默认关闭 | 原大diff主要是CRLF；已分别导出语义版和逐字节版 |
| 当前 GDN 调用链 | 模型主路径直接进入 vLLM 自带 FLA；没有连接 Plugin 遗留 FLA wrappers 或 FGV | 库内融合代码不能视作当前模型已命中 |
| FGV GDN 固定配置 | 源码和安装态一致；只针对H8/H16 | 27B常规TP2 value-head H24不匹配，未证明目标收益 |
| FGV 安装态 MoE | 276文件中唯一与源码不同的文件 | 导出独立overlay，dense27B不计其收益；直接重装源码会丢失它 |
| FlagGems | editable，无Git基线 | 保留源码与SHA；不伪造新增diff/作者或收益 |
| 旧脚本/patch | 旧开关与调用链不一致，模型路径也不同；full动态shape旧patch未体现在当前文件 | 原样保留并标注，不自动应用 |

## 环境与执行边界

- 模型路径：`/data/Qwen3.6-27B`，dense，64层，linear/full attention 48/16。
- 用户远程目录原始路径和规范路径均为 `/public-flash/jinghao/qwen3.6-27B`；非符号链接，owner/group UID/GID 0，0755，预检可用约3.24TB。
- 镜像：`harbor.baai.ac.cn/flagos-inner-models-release/metax-qwen36-27b-release-1021:latest`；ID `sha256:afcbdac2f632d7a37de05f318cfe804007cc0ce3a332be8ff36f0d1913c74a9e`。
- 挂载：`/data`→`/data` RW/rslave；`/public-flash`→`/public-flash` RW/rprivate；网络/IPC为host。未创建容器、改变挂载或设备状态。
- 已运行仓库 inventory 和仅限mx-104的connectivity-check；首次沙箱内Ansible RPC失败，沙箱外只读连接成功。
- audit阶段写入仅限新远程case目录、本地记录与临时审阅目录；env-003按用户要求更新容器私有 `/workspace/vllm-plugin-FL` 及该包editable安装metadata，其他仓库未改。采集/补充/验证命令先保存，再执行；交付包 `commands/` 保留代码。
- 采集与末次核验均未发现容器内推理进程；未使用其他容器/Host的服务补证。

## 验证与保留决定

4种补丁表示均通过应用检查与临时回放；语义版与容器实现AST一致，其他补丁逐字节一致。源码快照4116个清单条目校验通过；末次检查覆盖4113个不同源文件（4115次hash比较），无差异。FGV源/安装包逐文件比对完成。

远程交付包约7.45MB，SHA256 `c4261380a0a7f58b19baeb31711a55c6a112fc14955fc071999bf3db86e1fe36`；29个包内文件，28项清单校验通过。本案例schema/阶段身份/链接及 `git diff --check` 通过。全项目记录检查另有366条其他案例错误，本案例0条；未修改无关记录或宣称全项目检查通过。

原实现已完整备份，旧脚本和附带材料原样保留；当前Plugin安装已迁移。精度、性能、graph及正式验收均 `not_run`；没有新增加速比，`pr_readiness=needs_revision`。原审计证据为静态代码observation；新增CLI/dispatch验证不等同模型执行；不修改SOP或把一次审计升格为通用性能经验。

可复用经验：审计时同时核验Git工作树与普通安装包，检查真实模型调用链；剥离换行噪声；按真实value-head形状核验特化，而不是按注释中的模型名归因。

当前回退备份：容器 `/opt/plugin-release02-env003/activation-v4/backup`，Host case下 `snapshots/env-003-v4-original-plugin-and-metadata.tar.gz`。完整验证和回退命令见env-003。迁移期间发现/tmp下既有同名flash_attn.py会遮蔽安装包；最终验证使用python -P，旧文件未改。
