# op010 P4K/D1024 同容器顺序 A/B/R 审计与执行边界

本文配套脚本：`run-op010-p4k-d1024-sequential-abr-draft.sh`。它是本地草案，未在
PPU-01 上执行，也未复制到远端。

## 已核验的起点

- 容器：`qwen3.8-flash-opt-candidate-20260919`，完整 container ID
  `9b65cc77d73c5ecb9b22f580235b0475e253f18ccca5c2106cb01aba0acfb5e4`。
- service46 manifest 身份：
  `9b65cc77d73c-8030-2636577-259878814`；2026-09-20 只读复核时 live PID 为
  `2636577`、`/proc/2636577/stat` start ticks 为 `259878814`，完整 argv 与 manifest
  一致。
- service46 provider 变量：
  `VLLM_FL_FLAGOS_BLACKLIST_APPEND=_conv_depthwise2d,index,normal_,mm,mm_out`。
  其余关键环境保持 `VLLM_TUNED_CONFIG_FOLDER=.../moe-bm16-decode-only-01`、
  `VLLM_FL_QSA_STATIC_SCORE_COLUMNS=8448`、PPU 8–15。
- 已有 candidate run：
  `performance/p4k-d1024-mm-native-contract-candidate-01/run-record.json`，状态
  `complete`，role 为 `candidate`，scope 为 `performance_only`，轮次严格为
  3 warmup + 3 measured，warmup stability 通过。
- service46 已有 `graph-replay-smoke.json`，记录两次 replay，归一化文本相同。
  启动日志另有完整 graph capture 完成证据。

## 冻结序列

1. **B / service46 / native**：不重复发送性能流量。重新核对 container、PID、start
   ticks、完整 argv、live env、normalized manifest、candidate run 和两次 replay。
2. **A+R / service47 / normal**：只删除 blacklist 末尾的 `mm,mm_out`，保留 MoE
   tuned config、QSA bound、TP8、max-num-seqs=64、max-num-batched-tokens=4096 及其余
   argv/env。创建唯一 transition 目录、raw manifest、normalized manifest 和 graph
   replay 目录。随后在同一 fresh service47 上依次运行两个不可复用的 3+3 run：
   role `baseline` 与 role `revert`。
3. **恢复 / service48 / native**：从 service47 精确 PID/start-ticks 身份恢复
   `mm,mm_out` native provider，创建新的 raw/normalized manifest，重新完成 full graph
   capture 与 replay。service48 不作为 comparator 的第二个 candidate；它是任务结束时的
   operational retained state。
4. service48 已恢复后，维护版 comparator 消费 service47 baseline、已有 service46
   candidate、service47 revert。只有结果为 `passed` 才保留 D1024 性能结论；无论比较
   `passed/failed/incomplete`，最终服务都应维持 service48 native。

时序在墙钟上是 `B(service46) -> A/R(service47) -> native restore(service48)`，不是经典
`A -> B -> R`。比较器不依赖输入记录的时间顺序，但这意味着 baseline 是 candidate 之后
新建的正常路径实例，应在报告中保留该边界，不能描述成 candidate 之前的前置基线。

## 唯一产物

| 用途 | 唯一路径/ID |
|---|---|
| service47 transition | `transitions/mm-native-d1024-normal-service-47/` |
| service47 normalized manifest | `manifests/mm-native-d1024-baseline-revert-service47.json` |
| service47 graph | `smoke/op010-p4k-d1024-normal-service47-graph-01/` |
| baseline run | `p4k-d1024-mm-normal-baseline-service47-01` |
| revert run | `p4k-d1024-mm-normal-revert-service47-01` |
| service48 transition | `transitions/mm-native-d1024-native-restore-service-48/` |
| service48 normalized manifest | `manifests/mm-native-d1024-native-restore-service48.json` |
| service48 graph | `smoke/op010-p4k-d1024-native-service48-graph-01/` |
| comparator result | `performance/op010-p4k-d1024-sequential-abr-service46-47.json` |
| control hashes | `transitions/op010-p4k-d1024-sequential-abr-control-01/` |

脚本对以上所有路径执行 `test ! -e`，任何残留都停止，不覆盖、不追加到旧证据。

## PID 和失败回退门禁

- 每次 TERM 前，`transition-moe-drain-bm16-service.sh` 在容器内同一 Python 进程中重读
  `/proc/<pid>/stat` field 22 与完整 cmdline，并与 frozen `after-process.json` 比较；同时
  重验 manifest 的 `service_instance_id` 和 provider 环境，之后才只向 root PID 发 TERM。
- 等待范围仅是冻结的 PID/start-ticks 子树；不以宽泛 `pgrep` 作为成功条件。新服务必须是
  唯一匹配完整 argv 的 8030 root，新的 instance ID 由 container-ID/port/PID/start-ticks
  生成。
- service47 建立后设置 EXIT restore trap。baseline、revert、graph 或 comparator 前置步骤
  失败时，脚本仍尝试从精确 service47 身份恢复 service48。若 transition 本身在新 raw/process
  evidence 形成前失败，或 service48 restore 失败，自动流程停止；此时必须人工读取最后一个
  `before-process.json`/`after-process.json`，重新核验 live PID，禁止猜 PID 或宽泛 kill。
- comparator 在 service48 恢复和 graph replay 完成后才运行，因此比较结果非零不会把机器留在
  normal provider。

## 维护版 comparator 的角色与合同约束

- 三种 role 缺一不可：service47 `baseline`、service46 `candidate`、service47 `revert`。
  三个 run ID 与所有 raw result/validation path 必须唯一；不能复制 candidate record 改 role，
  不能跨 role 复用物理测量文件。
- 当前合同 `min_processes=1`，所以同一个 service47 process 可以分别承担 baseline/revert；
  两者仍是两个独立 3+3 测量 run。若合同提高为 `min_processes=2`，本方案不再满足，必须为
  **每个 role** 再建立不同 service instance，不能把 service47 的两个 run 冒充两个 process。
- baseline/revert 的 normalized service identity 必须完全相同；candidate 与其相比只能在
  `/launch_config/selected_environment/VLLM_FL_FLAGOS_BLACKLIST_APPEND` 下变化。
  `service_instance_id`、`runtime_evidence_sha256`、`base_url` 是 comparator 明确忽略的定位/易变
  字段，其他未声明字段变化会得到 `incomplete`。
- 三个 role 必须绑定同一个已冻结 contract、同一个计划和同一 benchmark client。计划固定
  `P4096/D1024/C64/N128` finite-batch Mixed、temperature 0、ignore-eos、3 warmup +
  3 measured、每轮 3600 秒。
- `required_metrics` 必须覆盖 primary `output_throughput` 及所有 guardrails：
  `total_token_throughput`、P99 TTFT、P99 TPOT、P99 ITL、P99 E2E；现有计划还要求
  `request_throughput`。
- 合同门槛：输出吞吐至少 +1%；total-token throughput 回退不超过 2%；四项 P99 回退均不超过
  3%；各 role 进程内相对 spread 不超过 8%；baseline/revert 每个决策指标漂移不超过 5%。
- scope 为 `performance_only`，即使 comparator `passed`，也不解除正式精度 gate，不扩展为
  正式验收或长期稳定性结论。

## 执行前部署要求

脚本以其所在远端目录作为 `control_dir`。审阅后须把脚本和以下冻结依赖放入同一个新的
`commands/performance` 控制目录或当前已审核目录；脚本会校验关键文件 SHA：

- `perf-p4k-mixed-entry-plan.json`：
  `da18d8b1eb558d098bcf2855b73a3102b28aecdacc4ad5bf6589170f664cb3ec`
- `perf-p4k-d1024-mm-native-comparison.json`：
  `207089003f68945b03d0261e5064d440bddc0f30e75b033bb352c7a12ecb2ee3`
- `normalize-mm-provider-service-manifest.py`：
  `c9507cca4d37793fcf872cad70b738241549c0bd3211bde3275cac9e5ba4c2aa`
- `transition-moe-drain-bm16-service.sh`：
  `09f75105bc6b4134cb14f85f95510b62f4e8b486648f50088cc2fd967b71fffd`
- `run-graph-replay-smoke.sh`：
  `61671cb1f72838a90334923a8f8aa1a33aee86d5d77e6bbe8ec206745eef75a7`

还需同目录存在 `vllm_perf.py`、`compare_performance.py` 和
`verify-live-service-manifest.py`。不能绕过 dry-run、manifest verification、graph replay 或
比较器重新校验证据。

## 已知风险

1. service47 同时承担 baseline/revert，满足当前 `min_processes=1`，但不能估计独立进程启动
   方差；它主要检查同一 normal 实例随时间的漂移。需要更强证据时升级合同并新增实例。
2. service46 candidate 早于 fresh baseline；温度、后台负载或 autotune 随时间漂移可能进入
   A/B 差异。baseline/revert 5% 门槛只约束 normal 路径两次测量，不能完全消除这一风险。
3. 完整 D1024 每个 role 都是 3+3 长测。service47 连续跑 baseline/revert 会延长墙钟时间，
   更容易受到共享机器干扰；任一 required metric spread 超限都应保留为 `incomplete`，不能手工
   挑轮。
4. EXIT trap 只有在 service47 raw/process evidence 已建立后才能安全自动恢复。启动中途、端口
   占用、worker 异常或 PID 身份漂移必须进入人工恢复，不得降级为宽泛 kill/restart。
5. service48 是恢复状态，不进入本次 comparator；其 graph replay 证明 graph 路径可用与归一化
   输出稳定，不等于重新测得 candidate 性能。
