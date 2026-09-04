# <实验 ID> 精度与性能验收

## 1. 验收契约（测试前填写）

- 模型、权重 revision、tokenizer 和 chat template：
- 服务代码、Plugin、算子库和 revision：
- 硬件、并行策略、dtype/量化、graph 配置：
- 质量任务、数据集 revision、样本数和生成参数：
- 绝对精度门槛或可信 baseline：
- 允许的最大回退：
- 输出健康门槛：超时、空输出、截断、异常重复：
- 性能 workload、轮数、warmup 和主/守护指标：

## 2. 执行模式与小样本

- [ ] eager 服务可运行
- [ ] graph capture/replay 服务可运行
- [ ] graph 下 8 并发固定请求全部满足期望
- [ ] 无错误、超时、空输出、异常截断或重复
- 延迟、吞吐、显存和设备利用率 sanity：
- 请求集、命令、配置、日志和结果位置：

## 3. 正确性回归

- 算子/组件数值对照、shape/dtype/layout 覆盖：
- graph/eager 一致性：
- baseline/candidate 输出差异：
- 已知非确定性及控制方式：

## 4. 全量精度

- [ ] `--preflight-only` 通过
- [ ] 正式进程正常结束
- [ ] 唯一样本数与预期一致
- [ ] `results_*.json` 和 `samples_*.jsonl` 完整
- [ ] 超时、空输出、截断和异常重复已检查
- [ ] 绝对或相对精度门禁通过
- 正式指标、baseline、candidate、差值和门槛：
- 命令、effective config、缓存和结果位置：

## 5. 正式性能

> 仅在第 4 节通过后，使用同一 graph 服务配置执行。

- [ ] baseline/candidate/revert 条件一致
- [ ] 冷启动、warmup、稳态和 profile 分账
- [ ] 所有正式轮请求与 token 数完整
- [ ] TTFT、TPOT/ITL、E2E、吞吐、显存和错误率已记录
- [ ] 多轮中位数/均值和波动范围已记录
- [ ] 需要时完成通信验证
- 命令、配置、逐轮结果、汇总和原始产物位置：

## 6. 结论

- 精度门禁：`passed|failed|incomplete`
- 性能门禁：`passed|failed|incomplete`
- 是否接受候选：
- 限制、异常和下一步：
