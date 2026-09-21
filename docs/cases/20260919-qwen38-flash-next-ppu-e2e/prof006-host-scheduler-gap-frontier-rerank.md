# prof-006：op-019 停止后的 P4K host scheduler gap 前沿重排

## 结论

`prof-006` 仍有执行价值，但它只是一个低开销的因果证明实验，不是已经
具备 `>=1%` P4K Mixed 收益机制的 scheduler 优化候选。当前没有新的
等价 scheduler 配置值得直接试验；唯一值得继续的问题是：在不开启
torch profiler 的条件下，相邻 graph replay 之间是否存在所有 TP rank
同时发生、且可归因到 scheduler/dispatch 交接的设备空转。

`prof-005` 的 P4096/D128/C64/N64 Mixed marker 墙钟中位数为
`40.143524s`，累计 device activity 中位数为 `30.600s`，两者差额
`9.543524s` 足够容纳 `1% = 0.401435s` 的收益；但 activity 可以重叠，
差额也包含 collective wait、runtime/sync、CPU 工作和 profiler observer effect，
不能把 `9.54s` 当作 host gap 或收益上界。因此当前判定为：

- **可执行的候选只有 `prof-006a` 证明实验；**
- **直接实施 host scheduler 优化仍为 no-go；**
- 只有 `prof-006a` 证明可消除的全-rank device-idle 下界超过 Mixed
  墙钟 `1%`，才解锁条件候选 `fw-012`。

## 不重复的已知边界

1. `fw-011` 已证明当前服务启用 async scheduling，vLLM V1 scheduler 已是
   running-first；`async_scheduling=True` 没有新变量。
2. `max_num_batched_tokens=6144/8192`、`long_prefill_token_threshold=2048`
   和 `max_num_seqs=48/64` 已分别形成拒绝或 Pareto 证据，不再扫描中间值。
3. concurrent partial-prefill 参数在当前 revision 中 unsupported/未被 scheduling
   loop 消费；DP1 下 `prefill_schedule_interval` inert。
4. `scheduler_reserve_full_isl`、`watermark`、`priority` 和
   `disable_hybrid_kv_cache_manager` 没有可信的等价 `>=1%` 机制；
   `stream_interval>1` 会直接改变 ITL 语义。
5. 已有 host/sync 控制不支持继续按调用次数放大：
   - `op-014 repeat_interleave(output_size)` 同卡组服务收益只有 `+0.1309%`；
   - `fw-008` common-slot graph host-sync 服务收益只有 `+0.4994%`；
   - `fw-009` GDN initial-state bool-index 的乐观 P4K/D128 上界约 `0.51%`。
6. `prof-005` 中 rank 间 sync 时长差与 collective wait 纠缠；`fw-010` 的
   PCCL Simple 控制在 rows64/4096 整链分别退化 `66.177%/25.156%`，
   不能把 rank spread 重新包装为 scheduler gain。

## 候选重排

### 1. `prof-006a-device-idle-host-handoff-proof`

- 类型：framework diagnostic；唯一立即候选。
- 机制：用预分配的 device event 环记录每个 graph window 的开始/结束，
  用预分配 host ring buffer 记录 `Scheduler.schedule`、metadata finalization、
  executor handoff 和 graph enqueue 的 `perf_counter_ns`。热路径不日志、不分配、
  不 `.item()`、不逐步 synchronize；请求结束后一次回收。
- 可信性现状：有足够大的未解释墙钟包络，但没有设备空转证据；
  因此只支持诊断，不支持代码优化。
- 成功门槛：三个有效 P4096/D128/C64/N64 测量轮的中位结果同时满足：
  1. 按 step 取 `min(TP0..7 inter-window idle)` 后累加，减去 event-only
     control 开销，下界严格大于当轮 Mixed marker wall 的 `1%`；
  2. 至少一个可修改的 host segment 能按 step 解释上述下界，不能只有相关性；
  3. 仪器化相对 marker-only control 的墙钟扰动不超过 `0.5%`，请求、
     graph marker 和 TP rank 覆盖完整。
- 停止条件：保守全-rank idle 下界 `<=1%`；scheduler/metadata 在前一个
  graph 结束前已 ready；gap 只发生在个别 rank；gap 落在 collective/
  runtime wait 内；或仪器化本身扰动超限。任一项成立就将 host scheduler
  方向结案为 no-go，不实现 `fw-012`。

### 2. `fw-012-async-schedule-result-handoff-overlap`（条件候选）

- 类型：framework；只在 `prof-006a` 通过后解锁。
- 机制：不改 token budget、request 顺序、priority、KV admission 或输出节奏，
  只将 `prof-006a` 证明位于 critical path 的 schedule-result/metadata/dispatch
  交接移入前一 graph 的异步重叠区间，并用固定地址双缓冲保护
  graph replay。
- 当前可信性：**尚不可信**。async scheduling 已开，所以在新证据出现前，
  “再做一层 overlap”更可能是 inert 或重复现有机制。
- 实施前门槛：在不运行端到端服务候选前，一个只改交接时机的因果控制
  必须消除至少 `50%` 的已定位 idle，且剩余空转、新增 host 工作和
  event 开销合并后仍预测 `>=1%` P4K Mixed 墙钟收益。
- 服务门槛：先在 P4096/D128/C64/N64 同卡组 A/B/R 达到输出吞吐
  `>=1%`、所有 P99 guard 回退 `<=5%`，再在精确
  P4096/D1024/C64/N128 重复同门槛；graph capture 和至少两次 replay、
  canonical/最小正确性不得改变。
- 停止条件：交接不在 critical path；优化只能通过改变 admission/ITL
  语义实现；需要修改 vLLM 源码而不能在已授权的 Plugin 边界内完成；
  graph 地址/生命周期不稳定；或 D128 首轮低于 `1%`。

## 首个证伪实验契约

1. **基线身份**：保留的 service50 配置，TP8/PP1/DP1，
   `max_num_seqs=64`、`max_num_batched_tokens=4096`、exact M64 BM16、
   op008 QSA cap8448、native `mm/mm_out`、默认 PCCL；不带 profiler hook。
2. **workload**：先用已有诊断契约 P4096/D128/C64/N64，seed 42，
   1 轮预热 + 3 轮测量；它只判定机制，不代替 P4096/D1024 端到端结果。
3. **A/B 开销控制**：A 仅记录预分配 graph-boundary device events；B 另外记录
   预分配 host ring timestamps。两臂都不做热路径回收，完成后一次同步并导出。
4. **分类**：对每个 `new/cached` step 输出 graph duration、相邻 graph device-idle、
   schedule CPU duration、schedule-ready→dispatch、dispatch→enqueue 和 rank spread；
   以 `sum(min_rank(idle_i))` 作为最保守的 TP8 公共空转下界。
5. **决策**：只有上述下界扣除 A 臂开销后超过 Mixed wall `1%`，且按 step
   命中一个可在 Plugin 内改变的 host segment，才创建 `fw-012` 实验。
   否则 `prof-006` 完成 no-go，非 QSA 方向不再扫 scheduler 配置。

## 证据边界

- 本重排只使用已归档的 `prof-005`、`fw-008/009/010/011`、
  `op-014` 和当前 `state.yml`/`README.md`；没有运行远端命令。
- 没有新的端到端 speedup，也没有改变已拒绝实验的结论。
- 即使 `prof-006a` 通过，D128 只是 milestone；保留候选仍必须回到精确
  P4096/D1024/C64/N128 同卡组 A/B/R。
- 正式精度仍被继承的 GPQA `170/198 = 85.86% < 88%` 阻塞；
  本文不签发性能或精度验收。
