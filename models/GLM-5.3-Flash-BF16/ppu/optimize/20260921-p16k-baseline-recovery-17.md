# 20260921-p16k-baseline-recovery-17 P16K 稳态入口基线恢复

- 状态：`complete`
- 分类：`framework`
- 正式目标场景：`P16384/D1024/C64/N128`
- 依赖：`20260921-p16k-scenario-entry-baseline-16` 的三轮完整 P16K 预调

## 优化方向与瓶颈依据

入口尝试的 warmup 吞吐为 373.524、435.222、435.896 tok/s，整体离散
14.331%，因首轮冷态超过 5% 门槛而在 measured 前停止。后两轮仅差
约 0.155%，请求均 128/128 成功，服务日志无运行错误，因此本点只恢复
稳态基线，不改代码或调度参数。

## 优化内容与适用边界

复用同一健康服务实例，在已完成三轮完整 P16K 预调的前提下，
使用相同 workload、seed 派生规则、TP16/BF16、max-seqs64、MBT16384、
prefix cache disabled 和 FULL_DECODE_ONLY，重新执行独立 3 warmup + 3 measured。

该数字属于稳态服务 scenario-entry baseline，不包含新 P16K shape 首轮
编译/缓存成本，不是未优化 anchor。后续候选如与它比较，必须使用
同样的 fresh-service 三轮完整预调条件。

## 正确性与路径命中

复用已绑定的服务 manifest，C1 1/1、C8 8/8 已通过。恢复运行前要求
running/waiting 为 0、健康接口 200、prefix cache query/hit 仍为 0。

## 性能效果

同一服务实例完成独立 3 warmup + 3 measured，6 轮共
768/768 请求成功，0 失败。warmup 输出吞吐为
435.133、435.051、434.860 tok/s，相对离散度 0.0627%，通过 5% 门禁。

measured 三轮输出吞吐为 434.186、434.205、434.863 tok/s，
中位数及汇总门禁如下：

- 输出吞吐：`434.205104 tok/s`
- 总 token 吞吐：`7381.486770 tok/s`
- 请求吞吐：`0.424028 req/s`
- P99 TTFT：`112655.729 ms`
- P99 TPOT：`143.780 ms`
- P99 ITL：`1776.229 ms`
- P99 E2E：`255324.723 ms`
- measured 输出吞吐相对离散度：`0.1557%`

`run_complete`、`all_requests_successful` 和
`measured_relative_spread_at_most_5_percent` 三项门禁全部通过。

## 决定、风险与回退

稳态基线成立，决定进入 P16K Prefill/Decode/Mixed 分阶段归因。
该数字不包含 fresh service 首轮 shape 冷启动成本，也不是未优化
anchor；后续候选必须使用同样的三轮完整 P16K 预调条件比较。
本点没有修改源码、YAML 或服务启动配置，无代码回退项。

## 外部证据

`/mnt/nfs/users/jinghao/glm5.3-flash/optimize/e2e-opt-20260911/full-scenarios/p16384-d1024-c64-n128/baseline/scenario-entry-steady-recovery-17/`

- `run-record.json` SHA-256：`06ea13ce5ac609a170d6115c0e15f4e8c43957f71ab059ce825dcaceb87132db`
- `summary.json` SHA-256：`afb77188614096a00dfd26d46d31df4a55c1c0b7001fbe14b7c70b3b302cd3db`
- 首次 prepare 仅因 validation 引用字段解析错误失败，局部输入保留在
  `scenario-entry-steady-recovery-17-prepare-failed-01/`；没有启动 benchmark，
  不计入性能结果。
