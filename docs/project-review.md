# 项目复审：问题、改进与未完成项

审查日期：2026-09-06；修复更新：2026-09-07。范围是当前工作区的控制工具、评测代码、SOP/实验契约、Plugin 工程规范、技能与已有案例。未连接目标机器，未新增模型性能测量。这里记录项目维护发现，不作为性能案例或可迁移加速证据；执行规则仍以 SOP 为主。

## 总体判断

项目已经具备目标隔离、基线/候选/回退、正确性门禁、失败记录和 Plugin 设计约束。当前最需要加强的是**让测量证据与结论范围一致，并把文档中的必要条件落实到工具**。继续增加优化技巧清单，收益低于补齐这两点。

多模型/多平台的工程原则较完整：已有规则要求复用扩展点、按能力和 shape 选择实现、检查非目标路径与可选依赖、区分实验结果和 PR 准备状态。这里的支持是设计目标；inventory 覆盖平台、mock 通过和一台 PPU 成功，均不代表已完成对应设备的数值/graph/性能验证。

## 已确认的问题与本轮处理

| 优先级 | 问题与影响 | 处理及剩余边界 |
|---|---|---|
| P1 | 精度契约的 dataset revision 原来只是非空字符串；原始 runner 的 dataset_path 只用于预检，实际数据由 lm-eval task 决定。同名自定义 task 可能使记录和实际任务不一致 | 正式 wrapper 增加实际任务/数据来源采集与绑定；原始 runner 保持不变。需在规定评测镜像验证实际 API/结果结构，不能用本地测试宣布正式精度已跑通 |
| P1 | results 只检查分数和 SHA；即使其中模型/endpoint 指向别处、有效样本数为 1，配上 198 行 samples 也可能签发 gate | 增加原生结果身份、任务、生成参数、seed、样本数和实际题目内容的交叉核验；不再仅依赖文件未变化 |
| P2 | 性能结果强制依赖 failed 字段，旧客户端缺字段时误拒绝；另一方面只有计数而无性能指标时又可能通过 | 公共工具显式识别结构并核对指标、计数与时长；XingChen wrapper 已复用公共执行/校验，仅保留历史矩阵转换 |
| P2 | 有限批次、持续并发和到达率容量没有明确区分，短测可能被解释为服务容量 | 已实现参数化有限批次及有限请求 open-loop 速率/burst 扫描、原生联合 SLO goodput 和比较判定；持续 closed-loop/业务trace/队列与长稳未实现，不扩大 passed 的结论范围 |
| P2 | 预热只写轮数，未明确缓存历史、稳定判据和进程间重复 | 已实现可配置预热窗口判据/预算、两级波动和回退漂移检查，比较器核对独立进程数量；缓存操作和服务重启仍按既定流程取证执行，不自动操作共享状态 |
| P2 | 长稳是笼统要求，缺少持续时长、负载循环、idle/resume 和异常判定 | 验收模板与契约补充可执行长稳计划；按改动风险选择范围，未执行保持未完成。历史闲置退出根因仍未知，不能归因于算子改动或用 C8 代替排查 |
| P3 | 实验契约把 cache/graph 等不同一概列为不可比较，与优化这些参数的流程冲突 | 改为禁止未控制差异；声明为主要变量时允许受控 A/B，资源/语义取舍单列 |
| P3 | 技能仍要求完整过程放案例目录；历史环境段落又把过期设备编号写成“当前” | 技能统一引用模型 baseline/optimize/acceptance 的事实主记录；历史环境明确标注，当前配置指向有日期的记录 |

原始缺陷通过本地负例复现；新门禁的工具验证与目标镜像集成验证分别报告。固定 GPQA、同服务实例 gate、同挂载及源适配容器保护均是既定约束，本轮保持。

2026-09-06 的审查验证为 38 项测试、11 份原始资产 SHA 和 95 个文件链接。

2026-09-07 修复后的完整 `scripts/validate-local` 检查通过：85 项测试全部通过，其中包含通过 `E2E_LM_EVAL_WHEEL` 指定固定官方 wheel 后启用的 3 项源码接口检查；Python 编译、CLI 帮助入口、inventory、Shell 和 Playbook 检查通过，11 份原始资产 SHA 不变。另检查本轮涉及的 12 份文档中 89 个本地文件链接，均可解析。执行器到比较器的本地联调使用合成数据和模拟子进程；这些检查不调用模型 API 或加速卡，不代表正式评测镜像兼容性与模型精度通过。

## 2026-09-07 修复落点

- [公共性能计划](../evaluation/performance/performance_plan.py)支持配置校验、无请求 dry-run、客户端能力预检、超时、预热稳定性和逐轮失败证据；每次运行冻结服务/配置/比较契约及原始产物 SHA。
- [性能比较器](../evaluation/performance/compare_performance.py)重验原生结果、控制台输出和命令；检查单一假设允许的字段变化、独立进程、缺轮、波动、回退漂移、主指标、守护指标及联合 SLO。禁止同一物理测量产物充当多个角色，返回 passed/failed/incomplete。
- [模型 wrapper](../models/XingChen4-29B-A4B/ppu/optimize/tools/standard_perf.py)先验原 runner SHA，再用 AST 读取矩阵，实际运行交给公共入口。历史默认轮数和 workload 不被静默替换。
- 精度采集已按真实 CLI 注入任务 metadata；正式 samples 按冻结 filter 集合检查 198 个唯一题目，兼容同题多 filter 多行并拒绝内容冲突。通过固定官方 wheel 的未修改源码方法检查发现并修复，不称为完整镜像集成。详见[精度接口说明](../evaluation/accuracy/README.md#真实接口与镜像集成边界)。
- [Plugin 工程文档](plugin-change-review.md)新增可填写的版本/模型/平台/shape/执行模式证据矩阵，区分 hardware、mock、static 和未测项，不新增审批或虚构跨平台通过。

## 2026-09-07 后续全项目修复

继续检查主入口之外的 profiling、参考 runner、控制脚本和模型工具，发现以下可复现问题并修复。此前 85 项测试没有覆盖这些失败路径，不能据此称整个项目已无缺陷。

| 问题 | 修复与验证边界 |
|---|---|
| 精度参数被原 runner 的 `int()` 静默转换，验证失败后仍可能留下 evaluated 记录，序列化失败留下半截文件 | 包装层严格检查整数参数，全部验证后才发布 run-record；JSON 使用无覆盖的原子发布。原始 runner 字节不变 |
| 性能结果中的模型/客户端/负载元数据与计划不一致仍可能通过，console script 未变化也不代表 benchmark 源码未变化 | 交叉核对原生身份、并发、到达率和逐请求输入长度；重验版本/help/runtime 探针，绑定 benchmark/CLI 源码与 Python 解释器。执行探针保留虚拟环境入口，源指纹不宣称覆盖全部第三方依赖 |
| profiling 忽略失败、预热失败仍汇总；SGLang 把并发数用作到达率，并依赖缺失的示例数据路径 | 共享诊断编排与原生结果校验，显式目标/case/超时；并发和到达率分开，SGLang 保存详细 JSONL，采集/非采集轮分组。新增有效 trace 未观察到时保持 incomplete |
| trace 工具把 CUDA runtime/stream 参数误算设备耗时，非法文件或目录失败可能返回成功 | 主机、设备、未知类别单列；校验结构与时长，传播失败并保护已有输出，明确累计活动时长不等于端到端耗时 |
| 控制目标存在 Host/group 同名歧义，堡垒机错误在 stderr 时漏判，挂载未知选项丢失 | 拒绝歧义目标，检查两路输出；保留未知挂载字段、拒绝重复目标，归一化有效读写模式 |
| 模型 sanity 的子串匹配可误通过，历史 collector 混合 workload/NaN 仍能汇总，launcher 只拿 PID 就报告启动成功 | 精确检查答案，collector 复用公共原生校验；launcher 检查参数、进程、端口和 health/models readiness，失败保留 PID/log 并非零退出 |
| 历史环境与负载标签易被误认为当前事实，已有补丁没有具体 PR 状态 | 标记历史测量/环境变化和有限批次语义；按保存的 patch/实验填写 needs_revision 与已测/未测矩阵，不重写或冒充运行代码已验证 |

本次最终 `scripts/validate-local` 验证为 **141 项测试全部通过**，包含固定官方 wheel 的 3 项源码接口检查及真实本地虚拟环境的客户端探针检查；Python/Shell/Playbook、CLI 帮助入口和 11 份原始资产 SHA 检查通过。另检查 22 份文档中的 141 个本地文件链接，均可解析。首次综合验证暴露 macOS `/var` 与 `/private/var` 入口别名差异，修复探针入口记录后重新执行完整检查通过；没有把失败的一轮计作成功。

代码入口与命令见[性能工具说明](../evaluation/performance/README.md)、[精度入口](../evaluation/accuracy/README.md)和[模型复现入口](../models/XingChen4-29B-A4B/ppu/optimize/reproduction.md)。本轮未连接远端；服务闲置退出根因、目标镜像集成、长稳和最终 PR 硬件证据继续保留为未完成项。

## 外部资料如何进入流程

下列资料于 2026-09-06 查阅。优先使用固定版本；公开机制用于设计实验，不直接提供当前平台的最优参数或性能保证。

2026-09-07 补核 [SGLang v0.5.11 原生 benchmark](https://github.com/sgl-project/sglang/blob/v0.5.11/python/sglang/bench_serving.py)的到达率/并发参数及详细结果结构，以及 [Kineto trace 输出实现](https://github.com/pytorch/kineto/blob/main/libkineto/src/output_json.cpp)的活动分类。它们用于修复参数和统计口径，未作为目标平台性能证据。

| 来源 | 采用的原则 | 落点 |
|---|---|---|
| [vLLM v0.24.0 benchmark](https://docs.vllm.ai/en/v0.24.0/cli/bench/serve/) | 到达率、并发上限和 goodput 分别定义；逐请求结果用于核验 | SOP B2、实验契约负载模式 |
| [MLCommons Endpoints](https://mlcommons.org/benchmarks/endpoints/) | 用速度/容量曲线解释工作点，避免只展示峰值 | 容量任务增加负载扫描；不照搬其固定时长和点数 |
| [NVIDIA 测量窗口](https://docs.nvidia.com/deeplearning/triton-inference-server/user-guide/docs/perf_analyzer/docs/measurements_metrics.html)、[GenAI-Perf 指标](https://docs.nvidia.com/deeplearning/triton-inference-server/user-guide/docs/perf_benchmark/genai-perf-README.html#metrics) | 明确窗口、计时边界及 token/chunk 统计对象 | SOP B1、实验契约指标口径；不要求其他平台安装 NVIDIA 客户端 |
| [vLLM 调优](https://docs.vllm.ai/en/v0.24.0/configuration/optimization/)、[graph 设计](https://docs.vllm.ai/en/v0.24.0/design/cuda_graphs/) | 将调度/KV/graph 的配置与实际执行分开取证 | SOP C3 的触发信号、首个实验与取舍 |
| [vLLM Plugin 设计](https://docs.vllm.ai/en/v0.24.0/design/plugin_system/) | 插件仍需核对所支持的引擎版本组合 | 沿用 Plugin PR 规范，按实际修改补具体正反例，避免新建旁路接口 |

## 剩余需要实际目标的工作

1. **在下一次明确目标的正式精度任务中验证包装器。** 在规定镜像核对 task 解析、离线数据路径、生成参数和原生结果 schema；字段不匹配时先适配并增加真实格式夹具。完成依据是同一目标的一次完整运行与可重验 gate，而非帮助入口或 mock 测试通过。
2. **以代表性业务 workload 验证新性能入口。** 当前本地验证覆盖参数、证据生成与比较联调；尚无新远端性能结果。需要持续容量结论时再补真实到达/队列观测、持续负载和长稳；有限扫描不会自动证明这些条件。
3. **为实际 Plugin PR 填充兼容证据矩阵。** 模板与判定边界已准备，运行证据要来自明确的最终补丁和可用目标 CI/硬件，不能由项目工具测试替代。

后续扩展以减少人工误差为目标，不再重复增加政策正文。SOP 管阶段，实验契约管字段和判定，评测文档管命令，模型配置管当前事实，案例与技能管可复用证据。
