# perfdiag-001：P1K Mixed 首 token 波次与 P99 ITL 波动

- 分类：`framework` 只读诊断；父场景 `p1024-d1024-c64-n128`，缩减 milestone `p1024-d256-c64-n128`，无源码或服务配置变量。
- 状态：complete/read-only，根因 `partially-attributed`，不改变 op010 `incomplete_reverted_no_promotion`。
- 边界：只读使用 PPU-07 case `/mnt/nfs/users/jinghao/minimaxM3/20260921-minimax-m3-ppu-e2e` 中 op010 两轮 A/B/A 共 18 个正式测量轮的原生 detailed JSON、validation、run-record、服务日志；不停止、重启、改变当前 8023 服务，不重复客户端。

## 触发与问题

op010 的目标 MoE stage M32 BK64 在 16/16 worker 真实命中，10 题 GPQA strict 10/10；P1K/D256 两轮 A/B/A 输出吞吐分别观察 +7.98% 和 +7.79%、回退复现。然而维护版比较器两次都给 `incomplete`：第一次 B 的三轮 P99 ITL spread 超过冻结 15% 上限，第二次增加统一预热 3→5 后 A 基线超限。不能以吞吐观察值宣称端到端通过，也不能事后删异常轮或提高阈值。

只读初查第二轮 A 基线 r7 相比 r6/r8 多出 56 次 300–500ms ITL，集中在请求索引 32–95 的前 4 个输出 token；所有 9 个第二轮测量轮又都有恰好 268 次 >500ms ITL。`max_num_seqs=32`、C64/N128 有多个请求波次。这支持“波次 Prefill/Decode 干扰或队列时序”的假设，但客户端明细尚不能排除 host/network 因素或证明服务端唯一根因。

## 诊断契约

1. 从两轮所有 18 个 measured JSON 与 validation/run-record 读取每轮 `completed/failed`、start_times、ttfts、itls、output throughput、P99 ITL；不混入 warmup，不合并不同契约计算速度比。
2. 对每轮分别统计 `>300ms`、`300–500ms`、`>500ms` ITL 的数量、影响请求及 token 位置，按 32 请求索引分组；核对异常组 start time 与 TTFT。
3. 用对应服务日志的 Engine `Running/Waiting`、Avg prompt/generation throughput 窗口定位这些时间是否与新波次 prompt 接入相符。只把时间关系标为相关，不把相关当唯一因果。
4. 同时检查原路径和候选是否都可出现长尾、是否存在模型服务错误/超时/失败请求。若日志分辨率不够，结论为 unresolved，不推定候选造成或消除了长尾。
5. 不改 op010 的 `incomplete_reverted_no_promotion` 结论。若将来要修改 Mixed 稳态或 ITL 守护契约，必须先冻结新契约，再从新服务实例做同配置 A/B/A；此诊断不能替代正式性能 Skill 或新 198 题精度 gate。

停止条件：现有 timestamp/日志不能证明具体服务端时序时，以“波次相关但根因未证实”结束只读诊断；不得继续无界追加重复试验。

## 结果与证据边界

两套 A/B/A 的 18 个 measured round 原生 run-record 均 complete，逐轮 128/128、0 failed。第一套 output tok/s 中位数 A/B/A=463.327/500.298/463.110，比较 `incomplete` 因 B P99 ITL spread；第二套 5 预热计划 A/B/A=465.361/501.598/465.732，比较 `incomplete` 因 A 基线 P99 ITL spread。两个结果既不能相加，也不能拿第一套 A 对第二套 B 计算新收益。

每轮按完整 `itls` 明细统计：第二套所有 9 轮均有 268 次 `>500ms` 间隔与约 775–777ms 单次最大 ITL；其中 8 轮恰有 29 次 `300–500ms`，第二套 A 基线 r7 有 85 次，多出的 56 次分别落在请求索引 32–63 和 64–95 各 28 次，主要是每请求前 4 个输出 token。该异常轮 P99 ITL 为 382.321ms，而同基线 r6/r8 为 277.983/281.913ms；output tok/s 463.740 仍处正常 463–466 区间。第一套异常 B r4 P99 ITL 476.220ms 的 `300–500ms` 事件 91 次，分布在索引 0–31 共 48、32–63 共 21、64–95 共 21、96–127 共 1；前几个及最后几个输出 token 均有，说明不能把所有长尾简化为“只发生在后续波次的首 token”。第一套原路径 A/revert 也有多轮 58 次这一区间事件（常态 29 次），候选不是唯一发生方。

原生 `start_times`/`ttfts` 证明这 128 请求并非同时执行：第二套 A r7 请求组 0–31 从初始时刻开始，中位 TTFT 2.50s；组 32–63 同期提交但中位 TTFT 20.07s；组 64–95 和 96–127 的开始时刻分别比首组迟约 17.6–20.1s 和 35.1–37.5s，中位 TTFT 分别 18.84/19.05s。服务配置 `max_num_seqs=32`；这与多波次队列/Prefill–Decode 交错一致。对应服务日志每 10 秒的 `Running/Waiting` 多次为 32/32，prompt throughput 在 0 与约 3276 tok/s 间切换，generation throughput 同时变化。日志粒度不足以把某一个 300–500ms 客户端间隔精确归到某一个服务端算子、网络跳或调度决策。

结论：Mixed P99 ITL 的离散跳变真实存在于原路径和候选，而非 op010 单独引入；现有证据支持与请求波次及 Prefill/Decode 干扰相关，但具体根因未证明。统一把预热 3→5 没有消除它。该诊断不提供新的 pass gate，也不支持改变冻结阈值。下一步若重测 op010，须先定义并冻结更能表达 Mixed 尾延迟的比较方法，再在新实例上完整 A/B/A；若要证明服务器关键路径，需选择性时序 trace，Profiler-on 仅用于归因，不能算正式速度。
