# 20260921-p16k-scenario-entry-baseline-16 P16K 场景入口基线与分阶段定位

- 状态：`failed_incomplete_warmup_unstable`
- 分类：`framework`
- 正式目标场景：`P16384/D1024/C64/N128`
- 目标阶段：Prefill、Decode、Mixed
- 依赖：当前保留的 max-seqs64、MBT16384、M<=32/exact-M64 MoE 组合

## 优化方向与瓶颈依据

P16K 是第三个固定正式场景，尚没有当前保留组合的
scenario-entry baseline。P4K 的 admission 结构、large-M MoE、Sparse MLA、
KDA 和通信占比不能直接外推到 16K prompt。

本点先建立无 profiler 入口基线；如果低开销指标不足以定位，
再采集 16-rank trace，分开 Prefill、Decode 和 Mixed。未获得三阶段
证据前不选择代码或配置候选。

## 优化内容与适用边界

入口基线不修改源码。冻结 workload 为 16384 输入、1024 输出、
并发上限 64、128 请求、finite batch、temperature=0、ignore-eos。
服务保持 TP16/BF16、`max_num_seqs=64`、`max_num_batched_tokens=16384`、
`max_model_len=80000`、`FULL_DECODE_ONLY` 和 prefix cache disabled。

基线使用 3 轮 warmup + 3 轮 measured，主指标是 output throughput；
要求 128/128 成功、指标有限、warmup 末端三轮相对离散不超过 5%。
每轮超时 7200 秒，入口诊断总预算 4 小时；超预算或不稳定则保留
`incomplete/deferred-too-slow` 证据并进入独立 baseline-recovery。

## 正确性与路径命中

当前正式精度结论仍为 `172/198=86.87% >= 86%`。因为本点会创建新
服务实例，性能流量前重新执行固定 C1+C8 baseline-sanity，并核验
16 个 worker、graph capture、前缀缓存关闭及实际源码身份。该 sanity 不代替
198 题正式精度。

第一次启动预检在执行 `vllm serve --help` 的 CLI 能力检查时提前退出，
未创建模型进程、端口或日志。已改为对实际 vLLM 源码
`engine/arg_utils.py` 中 `--enable-prefix-caching` BooleanOptionalAction 定义做只读检查；
该修正只影响预检脚本，不改变服务命令或实验变量。

修正后服务就绪，C1 1/1、C8 8/8 全部命中预期答案，服务仍健康。
baseline-sanity 的 30 分钟 heartbeat 在评测前创建；短测在首次触发前
完成，终态后已暂停监控。运行身份清单 SHA-256 为
`e774d57ed27294314a7c37434614e1fe55a2cd1a9162f262df1d7b737dcb0580`；
C1/C8 结果 SHA-256 分别为
`b843f3d3dd09dd1601e4e3b3b09ffccb4ee9bce191655bd4a3f9ce2e799bb40d` 和
`898f335c9130d05df700998294f5389546072e253e191a72fc5b4db675ac331f`。

## 性能效果

三轮 warmup 均为 128/128 请求成功，输出吞吐为：

| 轮次 | output throughput | P99 TTFT | P99 TPOT |
|---:|---:|---:|---:|
| warmup-1 | 373.524 tok/s | 137.846 s | 167.431 ms |
| warmup-2 | 435.222 tok/s | 112.730 s | 143.489 ms |
| warmup-3 | 435.896 tok/s | 112.686 s | 143.039 ms |

三轮相对离散为 14.331%，超过 5% 门槛，runner 在 measured 前停止。
第二、三轮吞吐只相差约 0.155%，支持“首轮冷态、后续进入稳态”，
但不能据此丢弃首轮或补造正式 baseline。

## 决定、风险与回退

本尝试判定为 `failed/incomplete`，不产生 P16K baseline 数字。源码、YAML、
交付启动脚本和生产 DB 未变；服务健康且队列归零。下一步在同一
实例上执行独立 steady-state baseline recovery。

## 外部证据

`/mnt/nfs/users/jinghao/glm5.3-flash/optimize/e2e-opt-20260911/full-scenarios/p16384-d1024-c64-n128/baseline/scenario-entry-current-16/`

- run-record SHA-256：`59fb2b7ed341049ca785cdef37048a3c9b5d47b0cbc94191046bd35f26e96d00`
- 汇总 SHA-256：`c75a3bbb07e5b8e752a2400256247878114a6aa4670aed74bd4b286680a5a017`
