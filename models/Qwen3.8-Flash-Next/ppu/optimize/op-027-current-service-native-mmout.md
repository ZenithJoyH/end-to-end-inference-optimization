# op-027：当前 acc-011 配置的 native `mm_out` 单变量验证

## 假设与身份边界

- 分类：`operator/replace`。当前 PPU-01 优化容器 `qwen3.8-flash-opt-candidate-20260919` 的 8010 服务使用私有 FlagGems SQLite 修复、`max-num-seqs=32`、`max-num-batched-tokens=4096`、无 QSA 静态边界，当前 dispatch 为 native `mm`、FlagGems `mm_out`。
- 历史 `op-023` 在不同的 maxseq64/QSA-bounded/MoE 配置上，P16K/D128 native `mm_out` A/B/R 提升输出吞吐 3.3513%。该收益不能直接迁移到 acc-011 环境；本轮重建同配置 A/B/R。
- 只切换已完成正式评测的 8010 所在 PPU0–7；8000/PPU8–15 保持原样且空闲，源适配容器不变。每个性能服务显式关闭 prefix cache；原 8010 服务身份和回退信息在变更前冻结。
- 当前 acc-011 精度 gate 为 175/198，绑定原双服务。8010 重启及 provider 变化会使该绑定失效；本轮性能结果仅是 `targeted`，不能声明正式验收。若候选保留，先做最小回归，再做同契约完整 GPQA。

## 冻结实验契约

- 父目标：`p16384-d1024-c64-n128`。首个证伪 milestone：`p16384-d128-c64-n64`，finite-batch，`/v1/completions`，temperature 0、ignore EOS；它缩短输出及请求数，不能冒充正式目标场景。
- A/B/R 顺序在同一 PPU0–7、同一端口及相同代码/环境运行。唯一主变量为 `VLLM_FL_FLAGOS_BLACKLIST_APPEND` 是否加入 `mm_out`；原有 `_conv_depthwise2d,index,normal_` 保持。
- 各角色 3 次 warmup + 3 次 measured，warmup 最后两轮输出吞吐相对 spread ≤10%，全部测量轮保留，零失败。
- 主指标：维护版比较器以 B 相比 A 的输出吞吐至少 +1% 判定，R 用于 A/R 漂移 ≤1% 的独立校验；另补充报告 B 相比 A/R 中点，避免混淆两种口径。总 token 吞吐不下降；中位/P99 TTFT、TPOT、ITL、E2E 回退均不得超过 5%。这是本实验筛选阈值，不是用户的最终 SLO。
- 服务启动、graph FULL capture 和至少两次 changed-input replay、实际 dispatch、源码/进程身份、prefix cache 关闭、8000 健康与空闲、同机无其他评测流量均是前置条件。
- 晋级：D128 通过后，在相同当前配置上做 D1024/C64/N128 Mixed 及 Prefill/Decode 守护，再按高风险 backend 变更执行精度最小回归和全量 GPQA；失败则恢复原 provider，不累加其他改动。

## 执行状态

2026-09-24：`complete_passed_milestone_accuracy_pending`。既有 8000/8010 进程、容器和 8010 running/waiting=0 已只读核验。预检冻结了原 8010 PID 1468973/start-ticks 294783869 和 8000 PID 1335499/start-ticks 294745394。脚本通过精确 SIGTERM 仅停止原 8010；8000 不变。A/B/R 顺序在同一卡组与端口执行，三个服务均通过 FULL graph capture、两次 changed-input replay、维护版 benchmark dry-run；每个角色 3 次预热与 3 次正式计量、所有轮次 64/64、零失败，预热稳定性通过。A→B 服务身份差异仅 `VLLM_FL_FLAGOS_BLACKLIST_APPEND` 加入 `mm_out`，A→R 服务身份无差异，运行时确认 B 走 native `mm_out`、A/R 走 FlagGems `mm_out`。

| 角色 | 输出 tok/s | 总 tok/s | 单轮耗时中位数 (s) |
|---|---:|---:|---:|
| A，FlagGems `mm_out` | 40.913191 | 5277.801579 | 200.228823 |
| B，native `mm_out` | 42.032787 | 5422.229469 | 194.895477 |
| R，FlagGems `mm_out` | 40.877267 | 5273.167455 | 200.404787 |

维护版比较器状态 `passed`、`issues=[]`：B 相对 A 输出与总吞吐 +2.7365%，耗时 -2.664%；TTFT/TPOT/ITL/E2E 的中位/P99 均改善 2.396%–2.659%；A/R 输出吞吐漂移仅 0.0878%。另以 A/R 中点计算，B 输出吞吐 +2.7816%。比较器自身使用 A 而非 A/R 中点作为收益分母，已按实际实现标明，未修改冻结比较契约或原始结果。该结果只属于 P16384/D128/C64/N64 targeted milestone；没有据此宣称 P16384/D1024/C64/N128 正式达标。

R 完成后由冻结 PID/start-ticks 精确停止；原 8010 argv 和关键环境变量被恢复，新 PID 3432267/start-ticks 296610886，FULL graph capture 和两次 changed-input replay 通过，8000/8010 健康均 HTTP 200，原 8000 PID/start-ticks 保持 1335499/294745394。由于原 8010 实例已重启，acc-011 的旧 175/198 gate 不再直接绑定现态。该 gate 的原始 service manifest 把每个 replica 的 PID/start-ticks 纳入 `launch_config`，而维护版 rebind 只容许 `service_instance_id`/`runtime_evidence_sha256` 改变，因此不能用修改/复用旧回执绕过重新评测。native provider 候选也未做最小回归和正式 GPQA，故仅保留为性能候选，不部署到服务、不签发精度或正式性能 gate。下一步若晋级，先做当前身份的最小正确性与同契约完整 GPQA，再运行 P16K/D1024 的 Prefill/Decode/Mixed 守护和正式比较。

远端实验目录：`/mnt/nfs/users/jinghao/qwen3.8-flash/20260919-qwen38-flash-next-ppu-e2e/op027-current-service-native-mmout-20260924`。`original.json`、`services/original-stop.json`、`services/<role>/{runtime.json,service-manifest.json,graph-replay.json,service.log,stop.json}` 是身份及回退证据。冻结命令与契约为 `commands/op027_control.py` (SHA-256 `a35c60bbfacf32bb73267bc6e88532749f13bbdecbea61cfdc5ec1f5f2055663`)、`commands/op027-plan.json` (`c37203d1395dbf8e0bb1bb1aa666ccbfc0077267f816a9fa79b21569331c23da`) 和 `commands/op027-comparison.json` (`cb6d6219b47f5c6f573d7cb8bee27ab9a5dc5bb1c98a3535585201c279463f76`)；执行脚本是 `commands/op027_run_role.sh`。A/B/R 结果分别位于 `performance/op027-{baseline,candidate,revert}-01/run-record.json`，比较结果为 `performance/op027-comparison-result.json`，SHA-256 `ed249f504e95077b74d27214bcda30869c74af5e1ccd8cfff6625bebd774a8df`。恢复脚本 `commands/op027_restore_original.py` SHA-256 `7f623ffbd568675fbde819aff83a980038d8721d44547721c654c6fc7e8ca77d`；回执 `services/original-restored/restore-receipt.json` SHA-256 `015a6eb737fe91b1485b52c9ad5e6d2355feb18f70fdd033738ac4495a46c4bf`。

## 2026-09-28 精度最小回归续验

`plan-034` 在 fw016 拒绝后将本点重新列为首要候选。先于全量 GPQA/长 Decode，开展 `minimal-regression`：在原 8010 上固定种子采集 C1、C8、16K 长上下文和 C64 原始回复；只将 8010 切到 native `mm_out`，用完全相同请求逐项比较文本、finish reason 和 completion tokens。检查 FULL graph、两次 changed-input replay、空输出/错误、服务健康；脚本在正常完成或普通异常后精确停止本次候选并恢复原 argv/env。此检查不是 GPQA 分数，也不授予 D1024 正式性能资格。

远端新目录为 `/mnt/nfs/users/jinghao/qwen3.8-flash/20260919-qwen38-flash-next-ppu-e2e/op027-native-mmout-accmin-20260928`；`commands/op027_accmin.py` SHA-256 `86fa277007b48011c9d47e37a209737fcb97ade62e956032c30c11b40f072ea3`。启动前脚本会核验 8000/8010 当前 PID/start-ticks、优化容器/镜像、Plugin diff SHA 和私有 FlagGems SQLite 文件 SHA；原始响应与最终回执分别写入 `results/`。状态：`prepared_not_run`，不改变现存性能结论。
