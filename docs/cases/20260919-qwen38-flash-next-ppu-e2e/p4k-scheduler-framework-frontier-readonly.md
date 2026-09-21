# P4K scheduler/framework 新前沿只读审计

## 结论

**No-go：当前 revision 没有一个尚未测试、现成、单变量且对精确
P4096/D1024/C64/N128 Mixed 有可信 `>=1%` 吞吐收益、同时 P99 ITL
回退不超过 5% 的 scheduler 配置或 Plugin 调度开关。**

本结论排除了已经拒绝的 `max_num_batched_tokens=6144/8192`、
`long_prefill_token_threshold=2048` 和 `max_num_seqs=48/64` Pareto 重测；
也没有修改或运行远端服务。

## 运行事实与源码边界

- 当前 vLLM revision：`ee0da84ab9e04ac7610e28580af62c365e898389`
  （运行记录对应 vLLM 0.24.0）。
- 当前 Plugin revision：`939600b323c02c21916f1f76bfb4cd8c2b02578d`。
- 当前服务为 TP8/PP1/DP1、`max_num_seqs=64`、
  `max_num_batched_tokens=4096`、chunked prefill、FULL_AND_PIECEWISE graph。
- 启动门禁明确要求日志包含 `Asynchronous scheduling is enabled.`；因此
  `--async-scheduling` 不是新候选。当前 vLLM revision 在 executor 支持时也会把
  未显式设置的 `async_scheduling=None` 自动解析为 `True`。
- vLLM Scheduler 先调度 `running` 请求，再用剩余 token budget 接纳 waiting
  prefill。现有 profile 的 `execute_new_1_cached_1..63` 正好证明 Decode token
  已经优先占用预算；不存在一个遗漏的“先保 Decode 再做 Prefill”开关。

精确源码：

- [`SchedulerConfig`](https://github.com/vllm-project/vllm/blob/ee0da84ab9e04ac7610e28580af62c365e898389/vllm/config/scheduler.py)
- [`EngineArgs`](https://github.com/vllm-project/vllm/blob/ee0da84ab9e04ac7610e28580af62c365e898389/vllm/engine/arg_utils.py)
- [`VllmConfig` async resolution](https://github.com/vllm-project/vllm/blob/ee0da84ab9e04ac7610e28580af62c365e898389/vllm/config/vllm.py)
- [`Scheduler.schedule`](https://github.com/vllm-project/vllm/blob/ee0da84ab9e04ac7610e28580af62c365e898389/vllm/v1/core/sched/scheduler.py)

## 候选逐项审计

| 机制 | 当前 revision 中的真实行为 | P4K 判断 | graph/正确性风险 |
|---|---|---|---|
| `async_scheduling` | 已自动启用并由启动日志门禁验证；重设 `True` 无变量 | inert | 无；关闭反而去掉 CPU/GPU overlap |
| `max_num_partial_prefills` / `max_long_partial_prefills` | 参数存在，但 `EngineArgs._check_feature_supported()` 明确拒绝 Concurrent Partial Prefill；当前 V1 scheduler 也不读取这两个字段控制 waiting loop | unsupported/no-op，不可作为候选 | 启动失败或产生“参数有记录但执行路径未变化”的伪实验 |
| `prefill_schedule_interval` | 注释和执行路径仅用于 data-parallel rank 对齐；当前 DP1 | inert | 无收益，不能形成单变量因果证据 |
| `scheduler_reserve_full_isl=False` | 只放宽 waiting request 的 full-sequence KV admission gate；P4K prompt 恰为 4096，等于本轮可分配的完整 prefill，关闭 gate 并不会减少实际需要的 block | 无可信 `>=1%`；若在 cache 压力下产生差异，只会转化为后续 preemption/recompute | KV thrash、重算、ITL 长尾；混合 GDN/attention cache 风险高 |
| `watermark>0` | 只让 waiting/preempted admission 更保守 | 方向与吞吐目标相反 | 容量下降、TTFT 增加 |
| `scheduling_policy=priority` | 当前 benchmark 未提交不同 priority，所有请求仍按到达顺序 | inert | 无 |
| `stream_interval>1` | 合并多个 token 的流式回传，减少 host/API 输出频率 | 可能降低少量 host 开销，但会直接改变 ITL 观测粒度；`2` 起就有超过 5% ITL 回退的结构性风险 | 输出节奏/ITL 语义改变，不是等价调度优化 |
| `disable_hybrid_kv_cache_manager=True` | 强制不同 attention/GDN cache 使用统一大小；不是 scheduling overlap 开关 | 可能降低容量；已有 common-slot host-sync 服务收益仅 `+0.4994%`，没有证据支撑统一 KV 管理可跨过 1% | KV layout/capacity、graph metadata 和长上下文回归风险 |
| 其他 `long_prefill_token_threshold` | 2048 已证明切块没有恢复 ITL且吞吐约 `-0.69%`；3072/3584 只是同一机制的弱化插值 | 不再扫参；没有反转到 `>=1%` 的机制证据 | graph shape 增多、warmup 不稳定 |
| Plugin 自定义 Scheduler | Plugin 有 worker/scheduler 扩展边界，但没有一个现成开关可用；交替纯 Prefill/Decode 或人为留空预算会增加 step/launch，且重复实现 vLLM 私有调度语义 | 不是“现成低风险单变量”；当前证据不足以立项 | vLLM 私有 API、async placeholder、KV/GDN state、graph bucket 和取消/结束语义均需完整回归 |

## 为什么不把“Decode 预留预算”列为新候选

当前 Scheduler 的顺序已经是 running-first。Mixed 中 63 个 cached request 先各占
1 token，再由新请求使用剩余预算；profile 的 63 个
`execute_new_1_cached_1..63` window 是直接命中证据。因而在 Plugin 再加一个
“为 Decode 预留 64 token”的 shim，大部分 step 只会复现当前行为；若进一步强制留下
未使用预算，则总工作量不变但 step 数增加，没有可信的吞吐正收益机制。

## 后续边界

P4K framework 方向只有在新的低开销证据显示每步存在可消除的 host scheduler gap，
且其 critical-path 上界超过 Mixed wall 的 1% 后，才值得重新打开。当前应继续已排序的
collective/operator 路线；不要用新的 scheduler 参数扫描替代因果归因。
