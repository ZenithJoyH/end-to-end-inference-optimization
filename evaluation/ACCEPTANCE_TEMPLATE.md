# <实验 ID> 精度与性能验收

## 1. 验收契约（测试前填写）

- 执行规则版本、日期及验收范围（formal/performance_only/diagnostic）：
- 用户提供的远程工作根目录、本案例子目录及路径/权限/空间检查：
- 预冻结 contract/config/service manifest 路径与 SHA：
- 模型、权重 revision、tokenizer 和 chat template：
- 服务代码、Plugin、算子库和 revision：
- 硬件、并行策略、dtype/量化、graph 配置：
- vLLM 完整启动命令及 runtime 证据：
- [ ] baseline/candidate/revert 均显式包含 `--no-enable-prefix-caching`
- [ ] service manifest 记录 `enable_prefix_caching=false` 且 `prefix_cache_state=disabled`
- 质量任务、数据集 revision、样本数和生成参数：
- 绝对精度门槛或可信 baseline：
- 允许的最大回退：
- 输出健康门槛：超时、空输出、截断、异常重复：
- 性能 workload、轮数、warmup 和主/守护指标：
- 性能评测 Skill 模式、场景 ID、结论范围和下一触发条件：
- 场景目录、稳定 scenario ID 与预冻结 full 验收集合：
- targeted/checkpoint 计划、被省略场景及最终补齐记录：
- 负载模式（finite_batch/closed_loop/open_loop）、时长、到达序列和客户端排队口径：
- 预热完成判据/预算、缓存冷热及正式精度后的状态恢复方案：
- 独立进程重复、配置顺序、统计单位、不确定性和停止规则：

## 2. 执行模式与小样本

- [ ] eager 服务可运行
- [ ] graph capture/replay 服务可运行
- [ ] graph 下 8 并发固定请求全部满足期望
- [ ] 无错误、超时、空输出、异常截断或重复
- 延迟、吞吐、显存和设备利用率 sanity：
- 请求集、命令、配置、日志和结果位置：

## 3. 正确性回归

- 精度评测 Skill 模式与覆盖 experiment ID：
- 算子/组件数值对照、shape/dtype/layout 覆盖：
- graph/eager 一致性：
- baseline/candidate 输出差异：
- 已知非确定性及控制方式：

## 4. 全量精度

- 目标机器：
- 评测容器名称：
- 评测镜像引用与 image ID/digest：
- 正式 runner 路径与 SHA-256：`test/Accuracy_test/llmrun.py`
- 任务配置：`gpqa_diamond_generative_cot` / `limit=0` / `expected_samples=198`
- 实际解析的 task、数据来源/指纹、评测器版本与预冻结证据：
- 优化容器中的服务模型名、endpoint 与网络路径：
- 评测进度 heartbeat automation ID、默认/实际频率、监控路径与终态清理证据：
- [ ] `--preflight-only` 通过
- [ ] 评测容器基于 `harbor.baai.ac.cn/flageval/flageval-llmeval:v1`
- [ ] 使用单服务 `llmrun.py`（若例外使用分片，已记录用户指示和合并验证）
- [ ] 正式进程正常结束
- [ ] 198 个唯一完整样本与预期一致
- [ ] 冻结 filter 集合完整，同题多 filter 行的原始内容一致；行数与题数已区分
- [ ] `results_*.json` 和 `samples_*.jsonl` 完整
- [ ] 原生结果中的服务、任务、生成参数、seed 和实际样本数与契约一致
- [ ] 超时、空输出、截断和异常重复已检查
- [ ] 绝对或相对精度门禁通过
- [ ] run-record 与同一 samples SHA 的完整输出健康审查通过
- [ ] acceptance.py issue 生成的绑定 gate 及证据可重新核验
- 正式指标、baseline、candidate、差值和门槛：
- 命令、effective config、缓存和结果位置：

## 5. 正式性能

> 仅在第 4 节通过后，使用同一 graph 服务配置执行。

- 性能评测 Skill：`inference-performance-evaluation` / `formal`
- [ ] 当前候选服务身份重新取证且 acceptance.py check 通过
- [ ] baseline/candidate/revert 条件一致，各身份及比较范围独立记录
- [ ] 冷启动、warmup、稳态和 profile 分账
- [ ] 所有正式轮请求与 token 数完整
- [ ] TTFT、TPOT/ITL、E2E、吞吐、显存和错误率已记录
- [ ] 多轮中位数/均值和波动范围已记录
- [ ] 必需指标完整，百分位统计单位与有效样本量清楚
- [ ] 声称持续容量时已验证负载曲线、队列趋势和 SLO goodput；否则标不适用
- [ ] 需要时完成通信验证
- 自动比较计划/契约与各角色独立 run-record：
- compare_performance.py 判定、退出码与结果路径（未覆盖的任务条件另行核验）：
- 命令、配置、逐轮结果、汇总和原始产物位置：
- 远程产物清单、校验和、留存状态及回收/清理责任：

### 长稳计划与结果

根据改动的生命周期风险预先选择时长和压力条件，不统一规定小时数；未执行保持 `not_run/incomplete`。

- 状态（not_run/passed/failed/incomplete/not_applicable）及理由：
- 持续时长、负载循环、active/idle 恢复与退出条件：
- 周期 sanity、错误/重启、资源增长和队列趋势：
- cache/graph/调度等状态变化的覆盖、异常处理与原始证据：

## 6. 结论

- 精度门禁：`passed|failed|incomplete`
- 性能门禁：`passed|failed|incomplete`
- Plugin 工程复核（如适用）：设计记录、非目标回归、最终补丁复测与未测项：
- PR 准备状态（与精度/性能状态分别记录）：
- 是否接受候选：
- 限制、异常和下一步：
