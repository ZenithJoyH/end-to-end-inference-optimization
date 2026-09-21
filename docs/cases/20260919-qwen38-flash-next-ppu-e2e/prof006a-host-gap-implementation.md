# prof-006a：no-probe / event / event+host-ring 因果诊断

## 结论

已在 PPU-01 用固定 Plugin revision
`939600b323c02c21916f1f76bfb4cd8c2b02578d` 的私有 `/opt` 副本执行。最终结论为
`no_go_or_inconclusive`：不解锁 `fw-012`，不修改保留服务。

该草案只回答一个问题：P4096/D128/C64/N64 Mixed 的相邻 graph 之间，是否存在
所有 TP rank 共同发生、并且可由 Plugin 内 model preprocessing 因果解释的设备空转。
它不是 scheduler 优化，也不产生端到端 speedup。

## 固定源码接口

- Plugin general entry point 对固定 vLLM stock `Scheduler` 安装幂等 shim；只有
  真正构造 Scheduler 的 engine 进程才创建 ring 和 registration。
- vLLM 固定 revision `ee0da84ab9e04ac7610e28580af62c365e898389` 的
  `MultiprocExecutor.execute_model(scheduler_output, non_block=False)`：由 Plugin 在
  runtime wrapper 在 event 臂仅保留实例用于停采后 worker RPC flush，在
  `event_host` 臂另记录 dispatch 入口/返回；不修改 vLLM 源文件。
- `ModelRunnerFL.execute_model()`：worker 入口后记录 host 时间；在
  `_model_forward()` 前后记录预分配 device event 和 host enqueue/return 时间。
- 当前 `WorkerFL.init_device()` 构造 ModelRunner 后一次性预分配 1024 对 event 和定长
  `array` ring。三轮 P4K/D128 预计 579 个 graph step，1024 有余量；溢出直接无效。

首次运行正是因为错假设 `AsyncSchedulerFL` 而只有 8 个 worker registration，
已按门禁停止并修正到实际 stock Scheduler。该失败运行不进入最终分析。

## 三臂与热路径

- control `no-probe`：补丁已加载但 probe 禁用，用于约束 event 本身扰动。
- A `event`：只在 model-forward 前后 `Event.record()`，在下一个 worker entry 对前一 end event
  做非阻塞 `Event.query()`；不记录 host timestamp。
- B `event_host`：保留 A，并把 `perf_counter_ns()` 标量写入预分配 ring，覆盖 schedule、
  dispatch、worker entry、graph enqueue/return。
- 两臂热路径均不写文件、不日志、不创建 tensor、不 `.item()`、不 synchronize。Python
  `perf_counter_ns()` / `Event.query()` 会返回标量对象，这是 Python 插桩不可消除的最小
  runtime 成本；同时要求 `abs(A/control-1)` 和 `abs(B/A-1)` 均不超过 0.5%。
- 服务启动和 graph warmup 时只预分配，不采样。独立客户端 warmup 完成后，runner 仅向
  probe 自注册的 engine+TP0–7 精确 PID 发送 `SIGUSR1` 清零并激活；三轮完成后发送
  `SIGUSR2` 停采。停采后的非测量 trigger 由 engine 通过
  `MultiprocExecutor.collective_rpc("prof006a_flush")` 使 TP0–7 在各自正常 RPC
  执行线程中 synchronize/export。PID 和 `/proc/<pid>/stat`
  start-ticks 必须匹配，避免误发信号。

## 因果边界

device event 可给出每个 rank 的相邻 graph idle，但不能把 device clock 直接映射到
跨进程 host clock。因此分析器不会把 schedule/dispatch 的相关性计为可优化收益。

唯一计入 causal lower bound 的段是：

1. 下一个 step 的 worker entry 对前一 graph end event 执行 `Event.query()`；
2. TP0–7 全部返回 complete；
3. 取各 rank `worker_entry -> graph_enqueue` 的最小值；
4. 再以该 step 的 `min_rank(inter_graph_idle)` 封顶。

这证明被计入的 preprocessing 时间发生在所有 rank 的前一 graph 已完成后、下一 graph
入队前，且位于已授权 Plugin ModelRunner 边界。schedule/dispatch 时间只作为上下文输出，
不用于解锁 `fw-012`。

三轮中位必须同时满足：event-only 的公共 device idle 严格大于 wall 1%；A/control
和 B/A 绝对墙钟扰动均不超过 0.5%；上述 causal Plugin preprocessing lower bound 严格大于 wall 1%；
请求、63 个 Mixed step、三轮、TP0–7、engine/worker tag 全覆盖。否则结果为
`no_go_or_inconclusive`。

## 资产与使用顺序

- `prof006a_probe.py`：复制到 Plugin `vllm_fl/prof006a.py`。
- `prof006a-plugin.patch`：只修改 Plugin `__init__.py`、`worker.py`、`model_runner.py`。
- `run-prof006a-host-gap-diagnostic.sh`：`preflight/install/run/revert`；不负责擅自重启服务。
- `lifecycle-prof006a-host-gap.sh`：私有源码副本、PPU0–7/8031 fresh-service、精确停服和回退。
- `analyze-prof006a-host-gap.py`：验证三轮、rank/tag、ring、两级扰动和因果下界。

正式执行前仍须用既有 transition engine 从 service50 身份分别创建 A/B 服务，只允许新增：

```text
VLLM_FL_PROF006A_ARM=event|event_host
VLLM_FL_PROF006A_DIR=<该臂唯一绝对目录>
VLLM_FL_PROF006A_CAPACITY=1024
```

其余 launch argv、maxseq64/batched4096、M64 BM16、QSA cap8448、native `mm/mm_out`、
PCCL、容器、设备组和源码身份必须相同。A/B 各做独立 warmup + 三轮 measured；禁止在
同一服务内切 arm。

## 精确回退

`revert` 先要求 probe 文件 SHA 与冻结资产相同，再执行 `git apply -R --check`、
`git apply -R`，最后只删除本实验创建的 `vllm_fl/prof006a.py`，并要求三个被修改文件
恢复到冻结的初始 SHA，而不是错误要求全局 clean。它不 reset、不 checkout，
完整保留原 `model_runner.py` 的 blocking-Event dirty diff。

## Blocker / no-go

以下任一项成立就不运行或不解锁 `fw-012`：

- Plugin/vLLM revision、目标方法签名或三个目标文件内容不匹配；
- 实际 executor 不是被验证的 `MultiprocExecutor`；
- 注册不是恰好 engine + TP0–7，或任一进程未从私有 Plugin 副本导入；
- PPU Event 不支持 `enable_timing`、`elapsed_time` 或非阻塞 `query`；
- SIGUSR1/SIGUSR2 已被进程占用；
- ring 溢出、三轮/63 Mixed/tag/rank 覆盖不完整；
- A/control 或 B/A 的绝对墙钟扰动超过 0.5%；
- 公共 idle 或 causal Plugin preprocessing 下界不严格超过 1%。

即使通过，D128 也只是机制证明；`fw-012` 必须另立 experiment-id，并回到精确
P4096/D1024/C64/N128 同卡组 A/B/R。正式精度仍被继承的 GPQA
`170/198 = 85.86% < 88%` 阻塞。

## 最终结果

event-only 公共 device idle 为 `7.6339%`，但 `3x63` 个 Mixed step 中严格因果
step 为 `0`，Plugin preprocessing lower bound 为 `0`。A/control 为 `-1.0349%`，
B/A 为 `+1.2161%`，两个绝对扰动门禁均失败。三臂内部稳定，因此这是
可重复的 no-go，不是单轮异常。最终 `analysis-v2.json` SHA-256 为
`99f088f20693860a9175b19f65007902781b56dbb92c7844d2b1e7cbca563abf`。
