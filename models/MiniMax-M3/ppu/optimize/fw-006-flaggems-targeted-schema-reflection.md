# fw-006：FlagGems 单表 schema reflection

## 契约

- 分类：`framework`
- 父目标：`p1024-d1024-c64-n128`
- 状态：`retained-accuracy-passed-formal-performance-pending`（早期 30K gate 未通过；后续 60K/131K gate 通过）
- 单变量：`SQLPersistantModel.build_sql_model_by_db()` 从无边界 `AutoBase.prepare(engine)` 改为先确认 table 存在，再只 reflection 请求的 table。
- 不改：数据库内容、config key/value、Triton kernel、vLLM 调度、graph 配置和 workload。

## 假设与门槛

- `fw-005` 的 4/4 rank Python 栈证明慢路径为对 605-table SQLite 配置库的并发全库 reflection。单表 reflection 应消除该 7 s 级设备空泡，且不改运行时选中的 config。
- 实施前保存 FlagGems revision、clean status、补丁和回退方法。
- 先做临时 SQLite 的 existing/missing table 单元验证，再重启 graph 服务做 capture 和两次 replay。
- milestone：同配置 `P1024/D256/C64/N128`，以 baseline/candidate/revert 的新服务首轮和稳定轮对照，重点守护 output throughput、TTFT、TPOT 和 max single ITL。
- 候选成功条件：同配置慢路径不再出现，同时稳定态 throughput/TPOT 不退化超过预置护栏；若仅首轮改善，结论限定为 tail/warmup 修复。
- 停止条件：单表 reflection 数值/缓存语义失败、graph 失败、文本 smoke 失败，或 baseline/candidate/revert 不能建立可比性。

## 回退

- 恢复 `/workspace/FlagGems/src/flag_gems/utils/models/sql.py` 的本实验补丁，重启同参数服务，重做 graph/health/文本 smoke。

## 实施

- FlagGems revision：`3c6f7537d2d5d3aa680c55bbee5c70f2100c5b85`；实施前 clean。
- 修改文件：`/workspace/FlagGems/src/flag_gems/utils/models/sql.py`。
- 补丁 SHA256：`c222f7ff28bf8ba5e66cc7f4e0fff58fbd548704201c5a06c9d9f0e6b5c21363`。
- 改动：`build_sql_model_by_db()` 先用 `inspect(engine).has_table(name)` 判断目标表，再以 `reflection_options={"only": [name]}` 只加载当前表；不改 table name、key、config 或 kernel。
- existing/missing table 单元语义测试通过；补丁 diff/checksum 保存在 `/mnt/nfs/users/jinghao/minimaxM3/20260921-minimax-m3-ppu-e2e/results/fw006-patch-and-unit-test.txt`。
- 候选、revert 与最终保留服务都完成 6/6 graph capture、health 和北京文本 smoke。最终服务实例：`bd37abcbf719:8023:588850:273180627`，prefix cache disabled。

## P1024/D256 milestone baseline/candidate/revert

| 角色 | r1 output tok/s | r1 max single ITL | 后续稳定态 |
|---|---:|---:|---:|
| baseline original | 318.93 | 7.086 s | r2 466.52 tok/s；r3 再次慢路径 340.85 tok/s / 9.500 s |
| candidate | 452.52 | 1.100 s | r2/r3 465.18/468.54 tok/s，max ITL 0.774/0.778 s |
| revert original | 322.90 | 7.112 s | r2/r3 466.59/466.05 tok/s，max ITL 约 0.78 s |

- baseline→candidate 首轮 output throughput `+41.89%`，max single ITL `-84.48%`；revert 重现 7.112 s 气泡，机制与时间漂移已区分。
- 候选稳定态与 revert 基本持平；收益来自消除 schema reflection 空泡，不是 kernel 吞吐提升。
- 证据：`performance/fw006-baseline-original`、`performance/fw006-candidate-targeted-reflection`、`performance/fw006-revert-original`。

## P1024/D1024 checkpoint

- 模式：`inference-performance-evaluation/checkpoint`，`performance_only`；因当前候选无精确绑定的正式 accuracy gate，未执行或声称 formal。
- workload：`P1024/D1024/C64/N128`，finite batch，3 预热 + 3 测量，temperature 0，ignore EOS，prefix cache disabled。
- run-record `complete`，6/6 轮各 `128/128` 成功；预热末两轮 output-throughput spread `0.65%`，通过 10% 预置门槛。
- 测量三轮 output throughput `533.89 / 532.80 / 532.50 tok/s`，P99 ITL `58.34 / 58.57 / 58.99 ms`，无多秒气泡。
- 测量中位数：output `532.80 tok/s`，total `1065.59 tok/s`，P99 TTFT `64552.63 ms`，P99 TPOT `60.001 ms`，P99 ITL `58.567 ms`。
- 与历史同配置 baseline 测量中位数的描述性对照：output `-0.59%`，P99 TTFT `-0.13%`，P99 TPOT `+0.73%`，P99 ITL `+0.29%`；均在预冻结守护范围内。历史 baseline 三轮 output spread `21.14%`（其中一轮 423.81 tok/s），候选三轮仅 `0.26%`。由于历史 baseline 没有绑定本次 comparison contract，该对照不冒充自动 formal comparison。
- 证据：`/mnt/nfs/users/jinghao/minimaxM3/20260921-minimax-m3-ppu-e2e/performance/fw006-p1k-candidate-01`。

## 正确性

- `minimal-regression`：固定前 10 题 GPQA greedy/C8，strict `10/10`，flexible `7/10`，0 timeout，0 空输出，0 乱码。
- 原生日志仍有与 baseline 相同的 2 个 `finish_reason=length` / 30000-token 截断观察，未新增异常。
- heartbeat `minimax-m3-fw006-minimal-regression` 以30 分钟频率创建，评测终态后已停用。
- 证据：`/mnt/nfs/users/jinghao/minimaxM3/20260921-minimax-m3-ppu-e2e/accuracy/fw006-minimal-regression`。
- 这是最小回归，不是 198 题正式 accuracy gate。

## 正式 GPQA gate（低于阈值）

- 用户冻结阈值：`exact_match,strict-match >= 0.88`；等于阈值通过。
- 正式范围：`gpqa_diamond_generative_cot` 全量 198 题，客户端并发 64，`temperature=1,top_p=0.95,top_k=20,max_gen_toks=30000`；wrapper seed 为 42，实际 OpenAI chat request seed 为 1234。
- 绑定服务：`bd37abcbf719:8023:588850:273180627`；graph、TP16、prefix cache disabled，`image_lineage=verified`、`mount_parity=passed`。
- provenance 与服务 preflight 通过；正式结果为 `172/198=0.8686868687`，低于 `0.88`，0 timeout、0 request error。
- 证据齐全且有效，但 wrapper 因低于阈值正确地未生成 gate/run-record。heartbeat `minimax-m3-fw006-formal-gpqa-c64` 已在终态后停用。
- 样本级定位见 [accdiag-002-gpqa-below-threshold](accdiag-002-gpqa-below-threshold.md)：相对上游 PPU-13 历史 177/198，净少 5 分全部来自 30K 截断组，非截断组反而多对 1 题。
- 证据：`/mnt/nfs/users/jinghao/minimaxM3/20260921-minimax-m3-ppu-e2e/accuracy/fw006-formal-gpqa-c64-threshold88`。

## 后续 60K/131K 正式 gate

- 用户要求把 `max_gen_toks` 提升至 60000、服务 `max_model_len` 提升至 131072，并在私有 Plugin `thead.yaml` 黑名单中加入 `conv3d,cudnn_convolution` 以通过启动 dummy profile；这与上面的 30K/65K gate 是不同契约，不能直接算作同配置精度提升。
- [accformal-004-gpqa-c64-60k-131k-threshold88](accformal-004-gpqa-c64-60k-131k-threshold88.md) 对 198 题、C64 签发了 `180/198=0.9090909091 >= 0.88` 的正式 gate。它绑定后续服务 `bd37abcbf719:8023:895010:279945667`，该服务在评测完成后退出。

## 决定与边界

- 保留候选。它修复了 P1K Mixed 中已多次复现的 FlagGems 全库 schema reflection 尾延迟，稳定态守护指标无实质回退；后续 60K/131K 精度契约已通过，但与早期 30K/65K 结果不可直接归因比较。
- 仍只能声称 D256 milestone 和 D1024 candidate checkpoint 的性能结果；尚无同契约、当前组合的 P1K 正式 baseline/candidate/revert，因此不宣称端到端累计收益，也不转入 P4K。新服务或源码改动必须按精度 Skill 重新绑定或重跑。
- `pr_readiness=needs_revision`：补丁为通用 SQLAlchemy 单表 reflection 修正，但尚未运行 FlagGems 上游完整单测/CI，PostgreSQL 路径未实测。

## prof-002：当前 131K/原 linear 图服务热点复核（预冻结诊断）

- 触发：`op-004` MoE paired 算法与 `op-005` 原生 mm 替换均失败；尤其 `op-005` 单卡两 shape +54–57%，但无 profiler 的 P1024/D256/C64/N128 A/B/A 输出吞吐 464.28→411.02→464.30 tok/s。历史 `prof-001` 为 65K 服务，不能直接证明当前 131K/黑名单/保留 fw-006 路径的热点。
- Profiling Skill 模式 `reprofile`，只做诊断，不把 profiler-on 时间作为正式性能收益。服务源为独立优化容器 `minimaxM3-opt-20260921`，私有 FlagGems `linear.py` 原版 SHA256 `4d46bae0804ac32b698582d010d5f0e02d3570c6703efff9d1d666e2bf43fd94`，保留 fw-006 SQL 补丁与 Plugin `thead.yaml` blacklist `[conv3d,cudnn_convolution]`。启动仍为 TP16/BF16、max_model_len 131072、max_num_seqs32、max_num_batched_tokens8192、无 prefix cache、FULL_DECODE_ONLY graph 1/2/4/8/16/32；仅增加 PyTorch profiler 配置与唯一 trace 目录。原回退服务 `bd37abcbf719:8023:1201737:286530453` 在停机前需再次验证并确认无 benchmark 客户端；不得触及源适配容器或 8013。
- 对齐历史 `prof-001` 的诊断 workload：P1024/D128/C64/N64，`/v1/completions`、随机固定长度、temperature 0、ignore EOS，1 轮预热+2 轮运行，仅最后一轮 profile，timeout 1800s。原生脚本 `commands/performance/vllm_profile.py`；新服务脚本 `commands/performance/prof002-current-131k-service.sh`，客户端脚本 `commands/performance/run-prof002-current-131k.sh`，都需先保存 SHA。唯一产物目录 `profiling/prof-002-current-131k-p1k-mixed/`，执行前目录不存在；trace 目录预期 16 个 rank 非空 gzip JSON。最近无 profiler 上下文是 `op005-d256-revert-01`，其 D256/N128 与该诊断 D128/N64 不同，不计算速度比。
- 诊断问题：当前 Prefill、Decode 和 Mixed 中哪些路径主导 device activity 与可见空隙？phase 边界优先用 rank0 `execute_new_<new>_cached_<cached>` 注释；new>0 的事件标为 Prefill/Mixed，new=0 标为 Decode-only，不把相邻 kernel 活动和重叠 device-sum 误认为端到端 critical path。检查 16 rank 覆盖、graph 实际命中、候选 kernel call/shape、collective spread，以及另一种解释（客户端/排队、调度间隙、通信或 graph break）。
- 停止条件：profiler 不能启动、客户端失败/超时、trace 未新生成/不可解析、rank 覆盖不足或 phase 边界不能确认时标为 `incomplete`，不按旧热点投入算子开发；无需强行重复。若有效，更新此实验和 `state.yml` 的三阶段热点与下一单变量候选，再用无 profiler 性能 Skill 验证任何后续收益。
- 远端控制副本已预存并通过 `bash -n`：`commands/performance/prof002-current-131k-service.sh` SHA256 `d9e03ff2bac7be932d3a98845506dcb5521067382f8d54241b78d165d5c46385`；`commands/performance/run-prof002-current-131k.sh` SHA256 `5edfec838680ee50326fd1001e9e72ead7422b9f209cb4c7656acafa89250408`。新 trace 根目录预检不存在，NFS 剩余约 8.6T；当前原版 `linear.py` SHA 与回退 service manifest 的 live PID/ticks/health 已核验。下一步仅精确停止这个回退实例并创建唯一 trace 根，再启动 profiler 服务。
- 回退服务 PID 1201737 已按绑定身份精确停机，8023 关闭，PPU 空闲，`profiling/prof-002-current-131k-p1k-mixed/traces/` 新建且采集前为空。profiler 服务 v1 在 `source /usr/local/PPU_SDK/envsetup.sh` 立即退出：其 shell `set -u` 与 SDK 脚本未绑定的 `$1` 不兼容；原始失败日志 `profiling/prof-002-current-131k-p1k-mixed/profiler-server.log` 保留，无模型进程、无 PPU compute、无 trace。修正版仅改为历史已验证的 `set -eo pipefail` 并使用唯一 `profiler-server-v2.log`，另存 `commands/performance/prof002-current-131k-service-v2.sh` SHA256 `1a4f21120c20f06fbbbe5c38b761e5e0b3c7afc81898fa584ec4b9d93b501b97`，`bash -n` 通过；不覆盖 v1 命令或日志。
- prof-002 v2 服务完成 6/6 graph 与 startup，health HTTP 200；`profiling/prof-002-current-131k-p1k-mixed/service-runtime.json` SHA256 `abce0ec3f76f7307241d1ba9ab90337703a942532f28339263eebc77c0fbf356`，manifest `service-manifest.json` SHA256 `e9b4d3e4b6613976429d8fc75fa32dcad060c9aeb93647914330c194457543ee`，live 验证绑定 `bd37abcbf719:8023:1217286:286682028`。启动参数包含精确 `torch_profiler_dir` 和 `record_shapes=true`。客户端 `dry-run.json` SHA256 `6b1dbdb601cc48df0a0fa7139af1b9a9d045280fe16ddc0eda2b05ff1e1f34b0` 已执行前审阅：P1024/D128/C64/N64、seed 42、温度0、固定随机长度、无限到达率，run1 未 profile/run2 含 `--profile`，路径/端口正确。执行脚本单独保存为 `commands/performance/run-prof002-current-131k-v2.sh` SHA256 `74fe54a3dc5f00b8c135f63040f5e57c9c51cb4ecc8d5abd483e0fcf828a42d1`，执行前再次确认 trace 空、client 目录不存在、PID/ticks 与 health 有效。
- `prof-002` 原生 `diagnostic.json` SHA256 `735f61b4f18b6fc7c384364e5e459bf1eec0bc86befd4c869bb580f8c8fbdcce`，状态 complete、预热 64/64 和唯一 profiled 轮 64/64 成功、0 error；trace 采集前为空，采集后 16 个 rank gzip JSON（每个约 20MB，回执逐文件记录 SHA）及独立 APIServer trace，rank 0–15 覆盖完整，服务随后 health 200。Profiler-on output throughput 389.93 tok/s 仅作诊断，不能与无 profiler D256/N128 求速度比。
- 复用旧 trace 解析脚本得到 `summaries/phase-rank-analysis.json` SHA256 `456e008bb6911443868992055e18178a2e08be9ed29fd397d1116ee9e373456f`：rank0 `execute_new_<new>_cached_<cached>` 注释有 Prefill/Mixed 与 Decode 分支；16 rank `fused_moe_kernel` 活动累计中位约 7.628s（spread 0.12%），`linear_kernel` 7.644s（spread 0.40%），稀疏 GQA prefill 1.019s、decode 0.501s。与早期 `prof-001` 的热点排序相近，但旧服务是 65K；这不是实测速度比较。
- 新 `commands/performance/analyze-prof002-phases.py` SHA256 `73ea998d689b8420016cadd88afde5cef656d91e2af282fab9fe73851b9d441e` 使用 GPU 侧 261 个非重叠 `execute_new` 注释归属设备事件、CPU 侧 265 个注释只看调度空隙；`summaries/rank0-phase-device-analysis.json` SHA256 `d0c84e1a3118420bb55ed0109cf208596eab28b7341e69e38ff6a6175a5a0527`。Decode-only 的 device activity sum 13.553s，其中 linear 5.756s/74256 calls、fused MoE 5.363s/28406 calls、sparse decode 0.481s/14204 calls；Mixed Prefill+Decode 为 6.243s，其中 MoE 2.089s、linear 1.757s、sparse forward 1.001s、ring all-reduce 0.711s。单独 Prefill-only 0.217s，样本仅 1 个 GPU 注释，不能据此推断正式长 prompt 的 Prefill 瓶颈。未落入 GPU 注释的活动累计 0.224s（约总活动 1.1%），未见相邻 GPU 注释重叠。CPU worker 正 gap 累计 11.408s 与 GPU 执行重叠，不能当作净空闲；最大单 gap 约 362ms，未出现此前多秒 reflection 气泡。
- 新 `commands/performance/analyze-prof002-moe-grids.py` SHA256 `e6f1511a33394bbb65d350f2d650115b88b4ddc0a2467bdfc357f6035bc0e00b`；`summaries/rank0-moe-grid-analysis.json` SHA256 `26b83d471f89cc9b2796a0ab06113e24f8f031dd2fd6988449f7a8b9d813001f`：Decode-only 的两组 `fused_moe_kernel` grid `[12288,1,1]` 与 `[768,1,1]` 各 13975 calls，活动累计 3.212s 和 2.112s、p50 约 230.7µs 与 156.8µs。当前源码 `invoke_fused_moe_triton_kernel` 按 `ceil(EM/BM)*ceil(actual_N/BN)` 生成 grid，GEMM1/2 共用 kernel 名；尚未用运行时实际 shape/config 证明两组 grid 各属于哪个 stage，不能直接据此改变 kernel。
- 结论边界：当前短 Mixed 诊断中 Decode 的 linear 与 MoE 仍是并列首热点，Prefill/Mixed 还包含稀疏注意力和通信，单卡局部 MoE/linear 方案已有反例。下一步先核对实际 MoE GEMM1/GEMM2 的 per-rank weight shape、config 和 grid 来源，做高成本方案的完整 transaction 上界；只在可兑现门槛时再开新算子实现实验。
