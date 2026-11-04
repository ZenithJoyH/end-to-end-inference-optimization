# 20260920-p4k-baseline-recovery-02 P4K 稳态入口基线恢复

- 状态：`complete`
- 分类：`framework`
- 目标场景：P4096/D1024/C64/N128
- 依赖：`20260920-p4k-scenario-entry-baseline-01` 的三轮完整预调

## 优化方向与瓶颈依据

首次 P4K 入口尝试的三轮均正确完成，但首轮吞吐仅 859.648 tok/s，后两轮为
1020.995/1068.110 tok/s，固定窗口离散 20.418%。服务日志未见运行错误，且后
两轮差异已缩小到约 4.6%，因此本实验只恢复稳态基线，不修改代码或调度参数。

## 优化内容与适用边界

复用同一健康服务实例，在已完成三轮完整 P4K 预调的前提下重新冻结一份独立的
3 warmup + 3 measured 计划。workload、seed 规则、TP16/BF16、max64、token
budget 16384、prefix cache disabled 和 `FULL_DECODE_ONLY` 全部保持不变。

这一定义属于稳态服务性能；后续候选若需与其比较，必须从 fresh service 开始先
完成三个不计入比较的完整 P4K 预调轮次，再执行同一 3+3 计划。冷启动或首次
shape 编译性能不在本基线结论内。

## 正确性与路径命中

复用 service instance 前检查 PID/start ticks 与 manifest 一致，running/waiting
为 0，prefix cache query/hit 仍为 0。三轮预调均为 128/128 成功；本实验仍要求
每轮全成功、指标有限、graph 服务健康。

## 性能效果

三轮新 warmup 为 1036.311、1072.323、1067.843 tok/s，相对离散
3.372%，通过 5% 门槛。三轮 measured 全部 128/128 成功，中位结果如下：

- output throughput：1071.417 tok/s；
- total token throughput：5357.084 tok/s；
- request throughput：1.0463 req/s；
- P99 TTFT：24.407s；P99 TPOT：58.560ms；
- P99 ITL：780.403ms；P99 E2EL：80.030s；
- measured output-throughput 相对离散：0.584%。

## 决定、风险与回退

当前决定为 `complete`，将 1071.417 tok/s 作为当前保留组合的 P4K 稳态
scenario-entry baseline。普通服务已在请求归零后优雅停止；下一步启动独立
profiler 服务，采集 Prefill/Decode/Mixed 证据。profiler-on 时间不用于收益判断。

## 外部证据

- `/mnt/nfs/users/jinghao/glm5.3-flash/optimize/e2e-opt-20260911/full-scenarios/p4096-d1024-c64-n128/baseline/scenario-entry-steady-recovery-02`
- `summary.json` SHA-256：
  `d254f692503e7bceee325cfec5001597ff16a317b05f45a4b26d5d301c5a0155`
- `run-record.json` SHA-256：
  `5ee1d1b79e8cb53bf515a668354c2ac83426f68fe5e3b7621043b7a9e94770cd`
