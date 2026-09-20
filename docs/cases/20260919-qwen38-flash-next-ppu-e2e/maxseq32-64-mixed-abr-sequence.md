# max-num-seqs 32→64：P1K Mixed 最小严谨 A/B/R 序列

## 目标与结论边界

本序列只用于 `p1024-d1024-c64-n128` Mixed workload 的
`max-num-seqs=32 → 64` 单变量比较。它使用同一容器、同一 PPU 8–15、同一
8030 端口、同一 graph/prefix-cache 配置，并满足比较契约对
baseline/candidate/revert 每个 role 至少两个独立 `service_instance_id`
的要求。

顺序采用两个交错区块：

```text
B32-01 → C64-01 → R32-01 → B32-02 → C64-02 → R32-02
```

这个顺序在每个 candidate 后立即回退，可同时观察短时间漂移和回退可复现性。

## 执行前硬门禁

1. 冻结并记录以下文件的 SHA-256：
   - `commands/performance/perf-mixed-p1k-plan-v2.json`
   - `commands/performance/perf-maxseq-mixed-comparison.json`
   - `commands/performance/vllm_perf.py`
   - `commands/performance/performance_plan.py`
   - `commands/performance/compare_performance.py`
   - `commands/performance/normalize-maxseq-service-manifest.py`
2. Mixed plan 必须仍为 `P1024/D1024/C64/N128`、3 轮 warmup、3 轮
   measured，并包含 contract 的所有 decision metrics。
3. exact contract 只允许：
   - `/launch_config/max_num_seqs`
   - canonical `launch_args` 中 `--max-num-seqs` 对应的数值元素。

   按当前启动参数顺序，该元素预计为
   `/launch_config/launch_args/18`。正式执行前必须由 canonical
   列表再确认索引。不应允许整个 `/launch_config/launch_args` 子树任意变化。
4. 容器必须为 `qwen3.8-flash-opt-candidate-20260919`，容器 ID、镜像 ID、
   挂载、Plugin/FlagGems-vllm/FlagGems 内容哈希与冻结值一致。
5. PPU 8–15 上不得有其他服务；同一 Host 上不得同时运行其他精度、性能、
   profiling 或重负载客户端。
6. 每次启动都必须显式带
   `--no-enable-prefix-caching`、`--max-num-batched-tokens 4096`、
   `--max-model-len 80000`、`FULL_AND_PIECEWISE` graph 以及相同的环境变量。
7. 当前 `restart-candidate-maxseq64.sh` 的产物名是固定的，只能用一次。
   在真正执行本序列前，需将其启动、取证和停止逻辑参数化为
   `role/ordinal/max_num_seqs`，不得覆盖任何已有产物。

## 单个服务实例的标准流程

以下步骤对六个实例每次都重复执行：

1. 确认上一个 API、EngineCore 和 TP worker 进程树已完全退出，8030 未监听。
2. 以目标 `max_num_seqs` 启动新服务，获得新 PID 和 `/proc/<pid>/stat`
   start ticks。每个实例必须生成新 `service_instance_id`。
3. 等待 `/v1/models` readiness，核对 prefix cache 关闭、graph capture 成功，并完成
   至少两次 replay smoke。
4. 在发送性能流量前生成本实例的 raw manifest。raw manifest 必须来自
   当前进程的实际 cmdline、PID/start ticks、代码哈希、容器/镜像和设备取证。
5. 立即从该 raw manifest 生成唯一 normalized manifest：
   - `device_ids` 必须为字符串 `"8"`…`"15"`；
   - `launch_args` 必须符合 canonical 顺序；
   - `--enable-prefix-caching` 必须不存在；
   - raw cmdline 和结构化 `max_num_seqs` 必须一致。
6. 使用 `compare_performance.service_identity` 的同等规则做发流前身份 diff：
   - B32/R32 与冻结 baseline identity 一致；
   - C64 与冻结 candidate identity 一致；
   - 首个 B32 与首个 C64 只能出现两个预期 changed paths。
7. 运行 Mixed plan，角色、run-id、normalized manifest 和 exact contract 必须互相对应。
8. 运行结束后检查 `run-record.json` 为 `complete`、输入前后 SHA 验证均通过，
   然后再停止服务。无论测量成功或失败，都不复用该服务实例做第二个
   process repeat。

## 六个实例与固定命名

| 序号 | role | `max_num_seqs` | 需要的操作 | raw manifest | normalized manifest | run-id |
|---:|---|---:|---|---|---|---|
| 1 | baseline | 32 | 先强制回到干净 32 服务，不复用任务开始前的旧进程 | `maxseq32-mixed-baseline-01.raw-service.json` | `maxseq32-mixed-baseline-01.service.json` | `maxseq32-mixed-baseline-01` |
| 2 | candidate | 64 | 停 B32-01，启动新 64 服务 | `maxseq64-mixed-candidate-01.raw-service.json` | `maxseq64-mixed-candidate-01.service.json` | `maxseq64-mixed-candidate-01` |
| 3 | revert | 32 | 停 C64-01，立即启动新 32 服务 | `maxseq32-mixed-revert-01.raw-service.json` | `maxseq32-mixed-revert-01.service.json` | `maxseq32-mixed-revert-01` |
| 4 | baseline | 32 | 停 R32-01，再启动一个独立 32 服务 | `maxseq32-mixed-baseline-02.raw-service.json` | `maxseq32-mixed-baseline-02.service.json` | `maxseq32-mixed-baseline-02` |
| 5 | candidate | 64 | 停 B32-02，启动新 64 服务 | `maxseq64-mixed-candidate-02.raw-service.json` | `maxseq64-mixed-candidate-02.service.json` | `maxseq64-mixed-candidate-02` |
| 6 | revert | 32 | 停 C64-02，立即启动新 32 服务 | `maxseq32-mixed-revert-02.raw-service.json` | `maxseq32-mixed-revert-02.service.json` | `maxseq32-mixed-revert-02` |

建议的外部目录结构：

```text
manifests/maxseq-abr/<run-id>.raw-service.json
manifests/maxseq-abr/<run-id>.service.json
logs/maxseq-abr/<run-id>.service.log
performance/<run-id>/run-record.json
performance/<run-id>.console.log
```

不得将 `candidate-maxseq32-service-comparison.json` 或
`candidate-maxseq64-service-comparison.json` 复用为两个 process repeat 的 manifest；
否则两次会共享同一 `service_instance_id`。

## 身份 diff 的预期结果

`service_identity` 会去掉 `service_instance_id`、`runtime_evidence_sha256` 和
`base_url`，但这些原始字段仍必须存在并对应当前实例。对去掉 volatile
字段后的 identity，发流前必须得到：

```text
diff(B32-01, B32-02) = []
diff(B32-01, R32-01) = []
diff(B32-01, R32-02) = []
diff(C64-01, C64-02) = []
diff(B32-01, C64-01) = [
  "/launch_config/launch_args/18",
  "/launch_config/max_num_seqs"
]
```

任何其他差异，包括代码哈希、设备列表/类型、镜像、环境、graph 模式、
`max_num_batched_tokens`、prefix-cache 状态或非目标 launch arg，都必须在发流前停止。

## 最终比较输入

六个 run 全部 complete 后，按 role 提供下列 run-record：

```bash
python3 commands/performance/compare_performance.py \
  --contract commands/performance/perf-maxseq-mixed-comparison.json \
  --run-record performance/maxseq32-mixed-baseline-01/run-record.json \
  --run-record performance/maxseq32-mixed-baseline-02/run-record.json \
  --run-record performance/maxseq64-mixed-candidate-01/run-record.json \
  --run-record performance/maxseq64-mixed-candidate-02/run-record.json \
  --run-record performance/maxseq32-mixed-revert-01/run-record.json \
  --run-record performance/maxseq32-mixed-revert-02/run-record.json \
  --output performance/maxseq32-64-mixed-abr-comparison.json
```

这是产物消费命令；它不启停服务，也不发送模型请求。

## 失败停点与回退

| 失败点 | 处理 | 能否继续下一 role |
|---|---|---|
| 旧进程未完全退出、端口仍被占用 | 保留证据，不发强制信号；定位并清理当前任务进程树 | 否 |
| 服务未 readiness、graph capture/replay 失败 | 保留日志并停止该实例；修复后用新实例和新 ordinal 重试同一 role | 否 |
| raw/normalized manifest 不合法 | 在发性能流量前停止；不手工改已生成 manifest | 否 |
| identity diff 出现非声明变量 | 停止当前实例，检查启动参数、代码/镜像和 normalization；旧 run 不进入比较 | 否 |
| warmup 不稳、超时、原生结果不完整 | 将该 run 保留为 incomplete，停服务并用全新实例/新 run-id 重试同一 role | 否 |
| C64 出现正确性、OOM、进程或 graph 错误 | 立即停 C64，启动新 R32 做 smoke 恢复；不将失败 candidate 纳入性能比较 | 仅可进入恢复，不继续测量序列 |
| 一个 B/C/R 区块期间发生共享 Host 流量或资源干扰 | 作废整个区块，静默环境下用三个新实例重跑 | 否 |
| 最终 baseline/revert drift 超契约 | 结论为 incomplete；检查热状态、Host 干扰、驱动/频率和启动漂移后重跑完整六实例序列 | 否 |

所有重试都使用新文件名和新 run-id，不覆盖失败证据。如果失败可能影响同一
B/C/R 区块的可比性，应重跑整个区块，不只补一个看起来有利的 role。
