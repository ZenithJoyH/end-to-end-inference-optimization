# 20260920-p4k-scenario-entry-baseline-01 P4K 场景入口与瓶颈定位

- 状态：`failed_incomplete_warmup_unstable`
- 分类：`framework`
- 目标场景：P4096/D1024/C64/N128
- 目标阶段：Prefill / Decode / Mixed
- 依赖：当前保留的 max64、16384 token budget、M<=32/exact-M64 MoE 组合

## 优化方向与瓶颈依据

P1K 低风险方向已收敛，但 P4K 正式目标尚无当前组合的 scenario-entry baseline。
长 prompt 会改变 Prefill、Mixed admission、large-M MoE、Sparse MLA、KDA 和
通信占比，不能把 P1K 热点直接外推。

本轮先建立无 profiler 基线，再以相同服务配置采集 16-rank trace，分别形成
Prefill、Decode、Mixed 视图。只有阶段证据收敛后才选择单变量代码或配置优化。

## 优化内容与适用边界

首轮不修改源码。冻结 workload 为 P4096/D1024/C64/N128、finite batch、
temperature=0、ignore_eos、前缀缓存关闭；服务保持 TP16/BF16、max64、
`max_num_batched_tokens=16384` 和 `FULL_DECODE_ONLY`。

baseline 使用 3 轮预热、3 轮 measured，主指标为 output throughput；要求请求全部
成功、指标有限、graph 服务健康且预热吞吐相对离散不超过 5%。诊断时间预算为
3600 秒，超预算则按 `deferred-too-slow/incomplete` 保存部分证据。

## 正确性与路径命中

当前正式精度 gate 为 `172/198=86.87% >= 86%`。开始测量前重新核验模型、容器、
源码、启动参数、prefix cache disabled 和 graph 路径；baseline 本身不引入新数值实现。

## 性能效果

三轮预热均为 128/128 请求成功，输出吞吐分别为 859.648、1020.995 和
1068.110 tok/s；相对离散为 20.418%，超过冻结的 5% 门槛，因此 runner 在
进入 measured 前按契约停止。P99 TTFT 从首轮 46.608s 降到后两轮约
24.4s，说明首轮是明显冷态；第二、三轮吞吐差异约 4.6%，但不能据此补造正式
baseline。

## 决定、风险与回退

当前决定为 `failed/incomplete`，不产生 P4K baseline 数值，也不声明收益。
源码与启动参数未变，服务保持健康且 running/waiting 均归零。下一步进入独立的
steady-state baseline recovery；后续候选必须采用相同的三轮完整 P4K 预调条件。

## 外部证据

- `/mnt/nfs/users/jinghao/glm5.3-flash/optimize/e2e-opt-20260911/full-scenarios/p4096-d1024-c64-n128`
- `baseline/scenario-entry-current-01/results/baseline-p4k-current-01a/run-record.json`
  （`failed`；输入在运行前后均完成 SHA 校验）
