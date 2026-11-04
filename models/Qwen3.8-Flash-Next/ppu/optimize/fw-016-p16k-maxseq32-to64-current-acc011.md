# fw-016：当前 acc-011 P16K max-num-seqs 32→64

## 假设与边界

当前 P16384/D128/C64/N64 负载并发 64，而 live 配置最多同时容纳 32 条序列；`op-027` 的 maxseq32 基线 P99 TTFT 约为中位数的两倍。提高准入上限可能减少排队，但可能放大 Decode ITL、KV 占用或抢占。旧 P1K 的 maxseq64 曾提高吞吐 72.51%，同时 P99 ITL 恶化 561.37%，不能直接迁移到 P16K。

分类：`framework`。变量仅为同一优化容器 8010 服务的 `--max-num-seqs 32→64`；模型、权重、Plugin/FlagGems、native `mm` + FlagGems `mm_out`、QSA 无静态边界、batched-tokens4096、async、graph 和其他启动参数保持不变。使用 PPU0–7 同卡顺序 A/B/R，8000 保持健康、身份不变且不接收压测流量。所有性能角色显式 `--no-enable-prefix-caching`。每个服务核验 FULL graph capture、两次 changed-input replay、固定 C8、单条长上下文和 C64 边界非空/错误检查；B/R 的 C1/C8/长上下文原始回复哈希须与 A 对齐，C64 回复哈希留档检查后才发性能流量。改动不进入 8000 或正式双服务。

## 预冻结定向契约

- 父目标 `p16384-d1024-c64-n128`；首个 milestone `p16384-d128-c64-n64-fw016`，相对目标缩短输出与请求数，强调 C64 准入成本，但不能代表 D1024 长 Decode。
- 同卡 A(32)→B(64)→R(32)，每角色 3 预热 + 3 计量；温度 0、`ignore_eos=true`、随机 prompt seed 42、`/v1/completions`、finite batch、每轮 64 请求。前两次预热之后最后两次吞吐 spread ≤10%，保留所有计量轮。
- 主指标输出吞吐 B 相对 A 提高至少 1%；A/R 输出漂移 ≤1%。守护：总 token 吞吐不下降，P99 TTFT/TPOT/ITL/E2E 各不恶化超过 5%，零失败/超时/抢占，且无服务健康、graph replay 或显存异常。
- 任一门禁失败则回退到原 maxseq32，不尝试 D1024；若首个 milestone 通过，必须补当前 P16K Prefill/Decode/Mixed 与 D1024 Mixed，并完成最小回归、正式 GPQA 新 gate，才考虑保留配置。
- 性能结果仅 `targeted` / `performance_only`，不以旧 acc-011 175/198 作为新服务的精度证明。用户当前继续性能优化的授权只覆盖诊断性探索；没有 fresh gate 不做正式验收。

## 状态与证据

状态：`incomplete_rejected_no_gain_restored`。[perf-016](perf-016-current-acc011-p16k-three-phase-entry.md) 当前三阶段基线已完成且原服务恢复。远程唯一案例目录为 `/mnt/nfs/users/jinghao/qwen3.8-flash/20260919-qwen38-flash-next-ppu-e2e/fw016-p16k-maxseq32-to64-current-acc011-20260924`；事前冻结 8000 PID/start-ticks `1335499/294745394`、8010 `2641118/297617620`，双方健康、空闲。控制脚本和角色执行脚本位于该目录 `commands/`，SHA-256 分别为 `6e8aa91fed8aec14ef246c13f31ca1d831a7c7e92cfa4c69d83d0eb60d39aef7`、`c22d92dd80567e2e557b7f44ee7fda6b4f7a5d9e711630b1f68ea9a6a940d689`。冻结的计划和比较门禁为 `commands/fw016-plan.json` 与 `commands/fw016-comparison.json`，原服务快照为 `original.json`。A 服务 `2760314/297652905` 和 B 服务 `3281781/297804844` 均完成 3+3、graph 与最小回归后已精确停止。R 组服务 `3804606/297958718` 已启动但检查链中断，仅有 graph replay；没有 C8、长上下文或任何 R 性能轮次。2026-09-28 只读核对后精确停止 R，原 8010 argv/env 恢复为 `1310899/327519847`，FULL graph 和两次 replay 通过，8000 仍为 `1335499/294745394`，两个端口均健康。恢复回执 `services/original-restored/restore-receipt.json` SHA-256 `00b222c6d556eb8eb846bde6d859296721f780e1b838a8739dff57fa8104946e`。

A 组原生回执 `performance/fw016-baseline-01/run-record.json`，SHA-256 `906e1282bb258e632bf3b35da633b305c9182615d6c2bf3e916649281b91e204`。三轮预热与三轮正式测量均 64/64、零失败、零抢占；预热末两轮 spread 0.01966%。正式输出吞吐中位 40.890111 tok/s，总 token 吞吐中位 5274.824370 tok/s；P99 TTFT/TPOT/ITL/E2E 中位分别为 187518.986/720.181/757.833/200139.392 ms。以上仅是 A 基线，不能单独证明 B 的收益。

B 组原生回执 `performance/fw016-candidate-01/run-record.json`，SHA-256 `6df6a18cda97629aba55f28a5b0d9d4d77a7763118f78d50497e4e19acb82f79`。三轮预热与三轮正式测量均 64/64、零失败、零抢占；预热末两轮 spread 0.27362%。正式输出吞吐中位 41.035045 tok/s、总 token 吞吐中位 5293.520796 tok/s；P99 TTFT/TPOT/ITL/E2E 中位分别为 186925.439/734.601/756.657/199433.058 ms。相对 A，输出吞吐仅 +0.354446%，低于预冻结的 +1% 主门槛；P99 TPOT 上升 2.002247%。R 未完成，不能签发维护版 A/B/R `passed` 或 `failed` 回执；本点按证据不足且已知收益低于门槛拒绝保留，不把 A/B 数值宣传为已验证的端到端提升。跨四天后补做 R 不能有效证明原 A/B 的时间漂移，因此没有补跑。旧正式精度 gate 也不自动绑定恢复后的新服务实例。
