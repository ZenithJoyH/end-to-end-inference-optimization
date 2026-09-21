# prof005：post-op010 P4K reprofile 草案审计

配套脚本：`prof005-p4k-post-op010-draft.sh`。本文和脚本均为本地草案，未在 PPU-01
执行，也未向当前 A/B/R 服务发送流量。

## Profiling Skill 选择

- mode：`reprofile`，因为 op010 已替换 `mm/mm_out` provider，可能改变 prof004 后的
  Prefill/Decode 热点排序。
- diagnostic scenario：`p4096-d128-c64-n64-post-op010-profile`，实际 workload 固定
  P4096/D128/C64/N64。它是低成本归因场景，不代替 P4096/D1024 正式性能结论。
- question：op010 后 `mm_kernel_general`、Fused MoE、QSA、通信和 graph gap 在 Prefill、
  Decode、Mixed 中的相对热点是否迁移；native `mm/mm_out` 是否只缩短部分 Decode shape，
  还是暴露相邻调度/通信瓶颈。
- 最近 no-profiler 证据：
  `performance/p4k-d128-mm-native-contract-comparison-01.json` 提供同 workload 的 op010
  上下文；新 D1024 comparator 只决定是否允许开始 prof005。不得把 profiler-on duration 与
  该 no-profiler 结果计算 speedup。

## prof004 审计和 prof005 修正

现有 `start-prof004-p4k-post-op008.sh` / `run-prof004-p4k-post-op008.sh` 的有效设计：

- 独立 profiler service、`torch_profiler_with_stack=false`、record-shapes 开启；
- P4096/D128/C64/N64，1 个无 profiler warmup + 1 个 profiled measured round；
- `profile-runs last`、1800 秒 bounded timeout；
- 采集后恢复普通 graph 服务；分析要求 1 async + 8 TP trace、gzip 完整和 rank0 phase split。

prof005 增加的硬门禁：

1. **仅 comparator passed 才能运行。** 每个 mode 都重新读取
   `performance/op010-p4k-d1024-sequential-abr-service46-47.json`，要求 status=`passed`、
   issues 为空、覆盖 `p4096-d1024-c64-n128`，且 changed path 只有 provider blacklist。
   因此当前 A/B/R 尚未完成时，`start`、`dry-run`、`capture` 都在发流前失败。
2. **执行时绑定 service48。** 不预写未来 PID；读取 service48 normalized manifest 与
   `after-process.json`，现场重验 container ID、PID、start ticks、完整 argv、native blacklist、
   QSA=8448、MoE tuned config、profiler 为空后才 transition。
3. **唯一目录。** profile、service49 transition、service50 restore、manifest、smoke 目录均
   `test ! -e`，不覆盖 prof004 或 A/B/R 证据。
4. **异步导出完整后才恢复。** capture 已开始时，restore 要求 maintained runner 的
   diagnostic=`complete`、无 errors、新 trace attestation 存在、容器内无 prof005 client/
   orchestrator，并且恰好存在可解压的 1 async + TP rank0–7 共 9 个 trace。超时、nonzero、
   `Stopping profiler` 卡住或异步导出未完成时不自动重启服务，先按精确 PID 检查 profiler 和
   client 状态。
5. **恢复门禁。** 成功 capture 后从 service49 profiler 服务恢复无 profiler native
   service50，normalize/verify manifest，并用 service48 canonical 做 1 次 capture + 2 次 replay
   对照。analysis 只有在 service50 live identity 已验证、恢复 canonical 存在且与
   service48 逐字节相同后才开始。

## 冻结 diagnostic contract

- model/tokenizer：Qwen3.8-Flash-Next / `/mnt/cpfs/models/Qwen3.8-Flash-Next`
- Host/container/port：PPU-01 / candidate optimization container / 8030
- topology：PPU 8–15，TP8，PP1
- graph：`FULL_AND_PIECEWISE`
- profiler：torch，no-stack，record-shapes；trace path 为当前容器和客户端共同可见的 NFS
  case 子目录，不推断 mount 映射
- workload：input 4096、output 128、concurrency 64、requests 64、random exact length、
  temperature 0、ignore EOS、request-rate inf、seed 42
- rounds：2 total；round1 warmup/no-profile，round2 measured/profiled
- timeout：每轮 1800 秒
- expected coverage：1 async_llm + 8 TP worker/rank traces
- phase boundary：`execute_new_*/cached_*` service markers与 timeline windows；必须同时有
  `prefill_graph` (`execute_new_1`)、`decode_graph` (`execute_new_0`)、
  `mixed_graph` (`execute_new_4`) 以及 outside-window accounting
- stop rules：comparison 非 passed、身份/环境漂移、dry-run 不符、请求失败、runner 非 complete、
  trace 非新文件/为空/不可解析、rank 缺失、phase marker 缺失或恢复 graph 不一致，均停止并保留
  `incomplete/failed` 证据

## 完整性和分析边界

- `vllm_profile.py` 负责 trace before/after、mtime/size、SHA 与 parseability 证明；脚本另外要求
  文件名覆盖 async + rank0–7、每个非空且 gzip 可解压。
- 为 8 个 TP rank 和 async trace 分别生成 category summary，并对 rank0–7 逐一生成
  Prefill/Decode/Mixed phase JSON 和完整性检查；不能只看 rank0 就宣称无 rank imbalance。
- phase completeness JSON 只证明可分段，不自动给出热点结论。后续人工分析必须分别报告
  Prefill、Decode、Mixed/interference 的累计时间、调用数、shape、rank 差异、graph gap、通信、
  host/runtime 和 unresolved alternatives。
- `trace_to_summary.py` 的活动时长允许重叠，不是 critical path、device utilization 或 CPU self
  time。profiler-on 时间不进入 comparator 或端到端收益结论。
- 若热点收敛到具体算子，再调用 key-operator-analysis；任何候选收益回到无 profiler
  performance evaluation 的 targeted/checkpoint 测量。

## 执行后语义修正（2026-09-20）

首次离线分析按草案把 `execute_new_1` 固定解释为 Prefill、`execute_new_4` 固定解释为
Mixed，8 rank 均因没有 `execute_new_4` 而判 `incomplete`。该结果原样保留在
`summaries/`，但只证明草案的 marker 假设错误，不使原始 trace 失效。

运行中 Plugin 源码证明 marker 的两个数字分别为
`len(scheduled_new_reqs)` 和 `len(scheduled_cached_reqs.req_ids)`。因此 v2 按以下通用
规则重算到独立的 `summaries-v2/`：

- `new>0,cached=0`：Prefill；
- `new=0,cached>0`：Decode；
- `new>0,cached>0`：Mixed。

P4K 每步最多接纳一个 4096-token prompt，所以 63 个真实 Mixed window 是
`execute_new_1_cached_1..63`。v2 的 Prefill、Decode、Mixed 和 outside accounting 在
TP0–7 全部通过，旧 `summaries/` 不覆盖、不删除。完整结果与证据边界见
`models/Qwen3.8-Flash-Next/ppu/optimize/prof-005-p4k-post-op010.md`。

## 执行与恢复顺序

推荐只在 A/B/R comparator `passed` 且 service48 graph 恢复完成后执行：

```text
prof005 ... start
prof005 ... dry-run
prof005 ... capture
prof005 ... restore
prof005 ... analyze
```

`lifecycle` mode 顺序执行以上步骤，但捕获失败时故意不自动 restore：这是为了避免在异步 trace
仍导出或 profiler/client 卡住时破坏证据。现场核验 export/client 状态后，再单独运行 `restore`。

执行前需将脚本置于远端 control directory，并确认下列已归档维护版依赖仍位于现有
`commands/` / `commands/performance/` 固定路径：

- `commands/performance/transition-prof005-preserve-op010.sh`（由本案例中已审阅的通用
  transition engine 生成的专用冻结副本；在停服务前同时验证源 manifest/live process 的
  native blacklist 与 QSA bound）
- `commands/performance/verify-live-service-manifest.py`
- `commands/performance/vllm_profile.py`
- `commands/performance/trace_to_summary.py`
- `commands/analyze-prof001-phases.py`
- `commands/analyze-prof005-phases.py`（本轮新增的三段分类包装器）
- `commands/performance/normalize-mm-provider-service-manifest.py`
- `commands/performance/run-graph-replay-smoke.sh`

`start` 会冻结 comparator、service48 身份、canonical graph 和上述执行器的 SHA；后续
`dry-run/capture/restore/analyze` 每次先 `sha256sum -c`，任一输入发生变化即停止。

transition helper 已在本轮审计中增加 pre-signal 环境门禁：源 manifest 与 live process 的
`VLLM_FL_FLAGOS_BLACKLIST_APPEND` 必须都等于 op010 native blacklist，QSA bound 必须都为
8448；随后仍在同一 Python 进程中复验 exact PID/start-ticks/argv 再发送唯一 SIGTERM。启动后
继续要求 selected environment 与源服务逐项相同。
