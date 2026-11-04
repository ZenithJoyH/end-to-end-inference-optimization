# op012: sampler call rollback and opt5 performance recovery

User requested rollback of the new library sampling call after opt5 regression. Continue in existing isolated qwen3vl-p64k-opt-20261015, own8111/GPU0,1; source container remains protected. Restore only Plugin MetaX sampler file to024plugin-opt HEAD. Keep FlagOS and original ATen registrations, all existing blacklist items, MoE JSON, gems-opt and sort. Do not remove library operators or user files.

Freeze current service identity before changes: user opt5/TP2/memory0.91/maxseq64/graph64/no-prefix-cache; Plugin08da21cb, FG-vllm f6fdb9b, gems-opt c3c5f5ab2, vLLM ee0da84ab. Recheck image/mount gates and source fingerprints. Shared public-flash library copy intentionally removed by user.

Performance: targeted/performance_only, P4096/D1024/C64/N128 finite batch. Initial contract: two warmup and two measured rounds per B/C/R service (superseded by uniform warmup recovery below), warm window2 TPS spread<=8%, measured spread and B/R drift<=8%. Improvement threshold2%, p99TTFT/TPOT/ITL guards<=10% regression, per-round900s and startup900s. Keep every measured round; transient first measurement means incomplete, never remove it. Freeze sampling seed/temperature/top-k/top-p after checking original benchmark and generation_config. Historical CSVs are observations, not equivalent native contracts.

Prefill: client TTFT; Decode: client TPOT/ITL and output throughput; Mixed: duration and completed throughput. These proxies include queue/scheduler/network costs, not pure device time. P16K/P64K and other final scenarios not run here; do not extrapolate. B current library, C original Plugin reference, R library restored. Initial tentative leave-reference policy is superseded by measured candidate regression; see delivery-policy revision below.

Correctness minimal-regression: reference path numerical/metadata and graph checks external to repositories, smoke/C8 and two-worker capture/replays for new services. No formal GPQA per prior user instruction. New commands, patches, plans, manifests and logs saved under remote op012 paths before execution. Exact PID/startticks/argv and idle guards before stopping own service only.

Preflight completed with before.json SHA b89a0c31ad9272b747848fc673047e0d68cba98c4cc4959997b8df8ab81d9d6e. Source/target mount differences were only redundant Mode spellings rw,rslave / rw,rprivate versus empty, with identical RW and Propagation. prepare_v3 normalizes only those duplicate tokens and compares every other field exactly; raw inspect remains. No mount changes. Prior syntax/raw-string comparison failures stopped before any source mutation.

Original benchmark does not supply temperature; this vLLM revision defaults to server generation configuration, not greedy. Current model generation_config is temperature0.7/top_k20/top_p0.8. New native plan explicitly sets temperature0.7; k/p retain the same model defaults, seed42 and fixed range_ratio0. Historical opt4/opt5 CSV source retains SKIP_FIRST1; all original rows preserved as observations, not reclassified as admitted steady-state data. Current measured roles keep all two measured rounds.

## Warmup recovery contract v2

Original baseline01 failed client PATH before sending requests. Baseline02 sent two complete warmup batches with128/128 success each: TPS325.801428 and966.341813, duration402.306s/135.636s. Native warmup spread99.14% exceeds8%, so the tool correctly stopped before any measured round. All evidence retained; no measurement deleted or relabeled.

Use plan-recovery.json SHA2bd366c7bb35ae13c5e0f0582314521f7ba16372506345a3eac09040c52b4d27 for B/C/R uniformly:3warmups, stability from last2 at8%, then2 measured. Baseline03 reuses the same unchanged service after the failed warmup; C/R are new service instances with the same admission rule. Remaining thresholds and workload unchanged. Native commands and dataset seeds freeze with the new plan. First anomalous warmup remains cold/transient diagnostic, not the optimization target.

Sequential controller consumes only passed native records, checks pause marker before each action, and stops on failure. The initial controller planned to leave reference after B/C/R. This tentative retention action is superseded below after two measured candidate rounds showed a slowdown; the exact controller was stopped before that final action, without stopping the independent reverse benchmark. No automatic changes outside one Plugin file and own8111 lifecycle.

Baseline03 complete: warmups972.259/967.751/968.580 TPS, measured956.276/963.126 TPS (rounded progress); all128/128 successful per round, native record complete/errors[]. Last warmup-window spread0.0856%, within8%. Approximate measured median959.701 TPS; final comparison recomputes exact unrounded values from raw artifacts. Candidate reference sampler file restored exactly branch HEAD; own service restart started, other three repos/config remain untouched.

## Candidate result and delivery-policy revision

Reference candidate completed: admitted measurement897.552/905.534 TPS, median901.543 (rounded), about6.06% below baseline959.701. All128/128 success; warmup-window905.631/903.099 spread0.280% passed. The slowdown is in admitted measurements, not merely first warmup. Both worker source proofs were actual native reference calls, MoE JSON and other three repo fingerprints unchanged.

Initial leave-reference plan is superseded by the performance objective: do not retain a known negative candidate if reverse closure confirms. User was told the two measured results and change of plan. Original sequence controller is precisely stopped only after C completes and R starts; R lifecycle/benchmark runs in its independent session and continues. No measurement interrupted or removed. If B/C/R confirms regression, retain unchanged R library service and archive the exact tested rollback patch. P16K/P64K remain unmeasured; do not generalize this P4 result to all user scenarios.


## Final result / 2026-10-17

**已按用户要求保留回退，性能恢复未确认。** 最终只将独立容器 Plugin MetaX 采样文件恢复到024plugin-opt HEAD：无过滤直接返回，有过滤调用 vLLM 原参考实现。FlagOS 保持启用，库内算子仍保留；MoE JSON、gems-opt/sort 和其他路径未改。

| metric | B library | C reference rollback | R library restored |
|---|---:|---:|---:|
| output_throughput | 959.701 | 901.543 | 735.034 |
| p99_ttft_ms | 18390.858 | 18562.713 | 18418.084 |
| p99_tpot_ms | 65.841 | 69.600 | 116.064 |
| p99_itl_ms | 579.628 | 583.657 | 580.498 |

以上均为两个准入后测量轮的中位数，仅为观察值。B逐轮956.276/963.126、C897.552/905.534；C中位数901.543，数值上比B低6.06%，没有回到历史opt4约985.46。R逐轮508.761/961.307，TPS跨度约61.57%，其TPOT亦大幅波动。原生工具因R轮间波动及B/R漂移判为incomplete，不能用这一组比较签发恢复、回退负收益或库调用稳定更快的因果结论。没有丢弃慢轮次或改为挑选快轮次。

三组统一3预热/2测量，末两轮预热跨度<=8%；R预热971.400/968.182通过，但准入后仍出现尾部拖慢。单轮900s预算、2%主收益门槛、10%延迟守护及8%测量/B-R稳定门槛均未更改。服务记录显示尾部剩余少量请求缓慢结束，128/128成功；GPU0/1只见当前worker。缓存审计在默认/root/.triton/cache未发现所查采样kernel近期元数据，不能据此证明或排除其他编译/运行原因。波动根因未定位，不把静态BF16分支推断当作实测归因。

最初计划最终保留原参考；C两轮均较低后，曾提出仅在R稳定回到B时保留库调用，并精确停止旧序列防止未经比较再次部署。R条件未满足，因此恢复最初用户要求的参考调用。原finish_baseline控制器因comparison=incomplete在任何最终部署前停止，错误回执保留；后续finish_reference_incomplete只在完整R结束、队列空闲和精确PID/argv/startticks守护下重启自己的8111。未修改其他服务或源8000。

最终服务：`/public-flash/jinghao/qwen3-VL/20261015-qwen3vl-metax-p64k-opt3/manifests/op012-retained-service.json`，API8111/served qwen3vl-opt5/TP2 GPU0,1，memory0.91/maxseq64/graph64及其他启动参数保持。新服务是与C源码相同的回退路线，完成健康和graph验证，**未将此前C数值伪装成该新进程的重新测量结果**。

最小回归：9 parameter/mask cases completed; optional direct-sampler graph incomplete after 600s; production model graph passed。实际最终参考调用的9个参数/identity、已知mask及禁止库调用案例完成；独立直接采样graph在600s超时，精确清理本次测试及其子进程后，补做2个生成请求通过。未将此独立graph记为通过。四次服务B/C/R/final均有真实双worker路径证明、capture、各16replay和17个smoke/C8请求。最终源码保护核验通过：只改采样这一个Plugin文件；FlagGems-vllm、FlagGems、vLLM及用户MoE JSON完全保持，源容器四仓库指纹一致。所有测试在外部案例目录，没有向仓库重新添加用户已删除的测试/perf。

回退补丁：`/public-flash/jinghao/qwen3-VL/20261015-qwen3vl-metax-p64k-opt3/commands/op012-sampling-rollback-20261017/final-plugin-rollback.patch`。原始原生比较、完整轮次及哈希引用见`/public-flash/jinghao/qwen3-VL/20261015-qwen3vl-metax-p64k-opt3/results/op012-comparison.json`；命令/配置/检查/日志索引`/public-flash/jinghao/qwen3-VL/20261015-qwen3vl-metax-p64k-opt3/commands/op012-sampling-rollback-20261017/evidence-index-v2.json`。系统Python元数据检查曾无效，已用Conda Python核实实际依赖；无真实依赖变更。

P16K/P64K未重测；历史opt4→opt5跨过多次代码/配置调整，其下降原因尚未分离。本轮为targeted/performance_only和minimal-regression，正式GPQA按用户要求暂缓，pr_readiness=experimental，不作正式/四场景最终验收。
