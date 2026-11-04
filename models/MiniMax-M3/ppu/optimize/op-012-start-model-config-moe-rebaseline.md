# op-012：按 start-model.sh 配置恢复 MoE 候选并重建基线

- 状态：planned；分类：`operator/improve` 候选复测，依赖 op-011；目标 P1024/D1024/C64/N128，首个 milestone P1024/D256/C64/N128。
- 用户指令：恢复先前 MoE 优化，并改以 `/mnt/nfs/users/jinghao/minimaxM3/start-model.sh` 的 8013 配置测试。该源脚本 SHA256 `ce6d0ec10b67a3c3fa9cb5d5969d50251fbc3327b562bbc129d73223eea3d3c7`，不会修改它，也不改源适配容器。
- 配置基线：PPU-07 独立容器 `minimaxM3-opt-20260921`，TP16/BF16，`vllm serve`，端口 8013，served name `MiniMax-M3-opt`，`max_model_len=100000`，`max_num_batched_tokens=8192`，`FLAGTREE_AABS=1`，`FULL_DECODE_ONLY`（不指定 capture sizes），prefix cache disabled；不显式设置 `max_num_seqs`，以启动日志中的有效值为准。与旧 8023/131072/AABS0/显式 32 的服务是不同配置，旧性能和精度 gate 不迁移。
- 唯一源码变量：旧 op-011 补丁 `patches/op011-thead-m32-gemm2-bk64-stages2.patch`，严格 T-Head/M32/BF16/GEMM2 shape guard，把 BK128/stages4 改为 BK64/stages2；其余 shape fallback。补丁 SHA256 `b9669b0d0aa9d5a56f8bcdb1365af835f74d362993d6d4fff8d2dcf8e617b9af`。恢复到此配置只建立候选，不把以前两轮 `incomplete` 的吞吐信号宣称为通过。
- 已有正确性：op-011 在旧 8023 配置下通过 BF16/graph/fallback、TP16 16/16 命中及固定 10 题；新 8013 配置必须重新核验 graph capture/replay、服务 smoke/C8 和最小回归。若进入正式性能，需按触发条件取得绑定当前新配置和服务的完整 GPQA gate。
- 性能计划：使用性能 Skill `targeted` 模式，先冻结新的同配置 P1024/D256/C64/N128 baseline/candidate/revert 计划和比较契约；不能将旧 8023 baseline 与本候选比较。守护 TTFT/TPOT/P99 ITL 和失败，保留所有正式测量轮；有波动则 `incomplete`，不事后剔除。

## 执行前控制与回退

已先在原 8023 配置恢复 op-011：独立容器 8023 新服务通过 graph/health/北京 smoke，16/16 worker 日志命中；此时补丁仍在私有 FlagGems 源码。下一步精确停止该任务 8023 服务并确认 16 张 PPU 释放、8013/8023 端口空闲、没有评测/benchmark 客户端。服务新脚本本地副本 `/private/tmp/op012-start-model-config-8013-service.sh` SHA256 `368b3e3c56da19cf0222e900defc5feb4cbd27f73f11e27fb8cf15b4917b06fb`；远端执行副本 `commands/performance/op012-start-model-config-8013-service.sh`。它保留源 `start-model.sh` 的环境变量及有效 `vllm serve` 参数，仅将 `nohup`/相对 `server.log` 替换为独立控制和唯一 case 日志 `logs/op012-start-model-config-8013-candidate-server.log`。

新 launcher 本地副本 `/private/tmp/op012-launch-8013-service.sh` SHA256 `9d9e0fccd78765524ec0938f1046da16eb4a7b66cad27ac0e8e58cd4d72afe66`，远端执行副本 `commands/performance/op012-launch-8013-service.sh`。执行前两份脚本均须以不存在的新文件名上传、核验 SHA 和 `bash -n`；执行时使用唯一 transition `transitions/op012-start-model-config-8013-launch`，检查 health、graph、prefix cache、北京 smoke、进程参数和 MoE 16/16 命中。服务失败或新配置不支持该 graph 时停止于事实检查，不动源适配容器；旧 8023 可按原参数和唯一新日志恢复。

8013 服务现已按此计划启动并通过 health、graph capture、北京 smoke；日志中 16/16 worker 命中 MoE 特化。实际进程 argv 没有 `--max-num-seqs`；运行时将未指定的 graph capture sizes 解析为 51 个尺寸。服务身份、源码与配置将在本次新产物中重新绑定。为避免复用硬编码 8023 的旧身份脚本，已准备仅把其服务端口匹配改为 8013 的 `/private/tmp/op012-capture-service.py`（SHA256 `5f1a2490426ff3bfd9157a5533454e2860f81ed6e874a2e7fdb188d25b01cb98`），以及验证 8013 位置参数、未显式设置 max-num-seqs、旧 MoE 补丁 16/16 命中和图捕获的 `/private/tmp/op012-build-service-manifest.py`（SHA256 `03203d051cbfcf451de414807c0bd3b9e77f2a4acaaed09bd33142835901c48c`）。远端副本分别存入 `commands/performance/` 同名文件；执行后将原生 runtime/manifest 保存在 `results/` 新路径，均不覆盖既有产物。

新候选实例已绑定为 `bd37abcbf719:8013:1479960:294574249`；runtime `results/op012-8013-candidate-runtime.json` SHA256 `9e51ae5f9a90e70c042e39c8a25955c1e9c541e2a2fad30e4b8c95e21afb571a`，manifest `results/op012-8013-candidate-manifest.json` SHA256 `ff863da43cd1a239e7fe10e282b997e86b763332039f5641292d817146ddb6b5`。当前进程环境核对 `FLAGTREE_AABS=1`；manifest 仅记录 `max_num_seqs` 为未显式指定，不把旧 32 当成新配置的有效值。

准确性 Skill 显式使用 `minimal-regression` 模式，在同一 8013 候选上运行固定 GPQA 前 10 题、并发 8、`max_gen_toks=60000`；仅是正确性护栏，不签发 198 题正式 gate。新配置本地 `/private/tmp/op012-minimal-regression.json` SHA256 `1b0f95e282363fda0915ecef7053368e113b4d33f9c9c3024074a6debab0e79a`，远端 `commands/accuracy/op012-minimal-regression.json`；preflight 脚本 `/private/tmp/op012-preflight-minimal-regression.sh` SHA256 `9bc6c2c3cfe4c1c4c4bf29a7263e2e1543fe01f3f86ea039e667a992152f5169`；launch 脚本 `/private/tmp/op012-launch-minimal-regression.sh` SHA256 `db6b2743edc6f4883b028ca29d2171409adf49c33915793ef95a1adba71ec5bc`。远端副本存 `commands/accuracy/` 新路径。执行前检查 evaluator 容器身份、8013 health、当前 manifest 及新输出目录不存在；先 `--preflight-only`，实际启动评测前建立当前任务的 30 分钟只读 heartbeat，结束后暂停。所有产物保留在 `accuracy/op012-8013-minimal-regression/`。

原生 preflight 退出码 0，通过 evaluator 身份、8013 health、当前 service manifest 验证；`accuracy/op012-8013-minimal-regression/preflight.log` 留证。实际运行前创建本任务 heartbeat `minimax-m3-op012-8013-minimal-gpqa-c8`，30 分钟，只读监控精确评测进程、当前服务及该输出目录，终态暂停。

## 新配置下的 targeted 性能契约（首轮测量前冻结）

性能 Skill 模式 `targeted`；父场景 `p1024-d1024-c64-n128`，首个 Mixed milestone `p1024-d256-c64-n128`，仅将 D1024 缩短到 D256。Prefill 由 TTFT/input-token 吞吐作客户端代理，Decode 由 TPOT/ITL/output-token 吞吐作代理，Mixed 看完整请求和波次尾延迟；这些不是纯设备阶段时长。基于当前已通过的 TP16/graph/service 命中事实，先对该 milestone 测原实现 A、候选 B、原实现 A，同一份 8013 配置，只有私有 FlagGems 补丁 SHA 可变。此次 `performance_only` 只给诊断性能结论，不是正式 P1K 或四场景验收。

冻结计划 `/private/tmp/op012-8013-p1k-d256-plan.json` SHA256 `df6922f615e16ee7bcd6e143b53f9093a818b700dd20bc99712e958dc898ee92`，远端 `commands/performance/op012-8013-p1k-d256-plan.json`：`/v1/completions`、受控随机 P1024/D256、C64/N128、有限批次、seed42、temperature0、ignore_eos、5 次预热+3 次全部保留的测量轮、末 2 次预热吞吐 spread≤10%，每轮 timeout 3600 秒。冻结比较契约 `/private/tmp/op012-8013-p1k-d256-comparison.json` SHA256 `8b8b00cbf727227d2686782b0f38fdfcfcf638c38f63d1d0159485b8b42dc179`，远端 `commands/performance/op012-8013-p1k-d256-comparison.json`：主指标 output tok/s 至少 +3%；total tok/s 回退≤3%、P99 TTFT≤5%、P99 TPOT≤3%、P99 ITL≤10%；每角色 3 正式轮 spread≤15%、A/revert 漂移≤10%。历史 op-010/011 P99 ITL 波动可能再次使本轮 `incomplete`；不删轮、不事后放宽门槛。

尚未启动任何性能客户端。先结束新配置最小精度回归；若失败或证据无效则暂停性能测试并定位。若通过，再准备同参数的 baseline/candidate/revert 独立服务、当前 manifest、dry-run 与唯一 run ID。

性能角色控制脚本已经在本地准备但尚未执行：`/private/tmp/op012-8013-role-service.sh` SHA256 `df48c32fb6cbf8327410ccc04f9ac297e01a5286bf90996952d0a06452de5b22` 用相同 `start-model.sh` 有效参数为 baseline/candidate/revert 生成各自唯一日志；`/private/tmp/op012-stop-8013-service.sh` SHA256 `23d75f8e333bdeaf99d49411eb4cd77dab79983602034ff7726dd75fd3797d52` 先验证当前 manifest、无评测/benchmark 客户端，再精确停止唯一 8013 PID 并等待设备释放；`/private/tmp/op012-launch-8013-role.sh` SHA256 `d563b13f8ac116eec87e35038e7df8d5a9130593db8f3cdc647c541ce756df51` 检查端口、设备、graph、health、北京 smoke 和 MoE 命中/非命中；`/private/tmp/op012-build-role-manifest.py` SHA256 `296f16eda21ca10bd0a775bb49b4917690ace91fe2014dce8d9c23a712535db8` 对每个新实例验证配置、源码及真实路径；`/private/tmp/op012-run-d256-role.sh` SHA256 `eb39ffaecb79735b79bbd24153bacf7ab5ef8b84727d2586f143788cd5464dc2` 先 dry-run 再执行维护版性能 runner。远端执行副本均放在现有 case 的 `commands/performance/` 中，上传前检查新路径不存在并校验 SHA。

预定独立服务顺序：当前候选通过最小回归后精确停止 → `op011-switch-moe-candidate.sh revert` 到原 MoE 源码 → 8013 baseline 启动/身份/5+3 轮 → 精确停止并 apply 同一补丁 → 8013 candidate 启动/身份/5+3 轮 → 精确停止并 revert → 8013 revert 启动/身份/5+3 轮 → 冻结比较器；最后如需按用户要求保留候选，在回退证据完成且无新错误后重新 apply 补丁并启动 8013 restored 实例，重新验证其身份/graph/smoke。任一阶段失败停止并报告，不能用不同配置的旧数据补洞。

最小回归原生完成：评测进程退出码 0，固定 10 道唯一 `doc_id`、20 个 strict/flexible filter 行，`exact_match,strict-match=1.0` 即 10/10。使用维护版 `sample_validation` 对原始样本核验，空输出 0、乱码 0、超时 0、显式截断 0。原始结果及样本分别位于 `accuracy/op012-8013-minimal-regression/minimax-m3-op012-8013-minimal-regression/op012-8013-minimal-greedy-c8-60k-20260924-01/gpqa_diamond_generative_cot/MiniMax-M3-opt/results_2026-09-24T06-25-41.401793.json` 和同目录 `samples_gpqa_diamond_generative_cot_2026-09-24T06-25-41.401793.jsonl`。此结果仅为最小回归，非 198 题正式 gate。heartbeat `minimax-m3-op012-8013-minimal-gpqa-c8` 已按原生终态暂停。

原实现 A 实例 `bd37abcbf719:8013:1489650:294723308` 在相同 8013 配置下完成 P1024/D256/C64/N128 的 5 次预热+3 次正式轮，128/128 每轮成功、0 error，末两预热 output tok/s 629.38/631.90，spread 0.40%，`run-record.json` 为 complete。正式轮 output tok/s 为 628.824/563.590/630.206；P99 TTFT 为 6456.611/8647.705/6550.136 ms，轮内系列 spread 约 33.5%，已超过预冻结 15% 稳定性门槛。原生路径 `performance/op012-8013-d256-warmup5-baseline/run-record.json`。因此这一 A 角色虽完整，但本次比较已注定 `incomplete`；不能用其对候选签发通过。按用户测试意图仍对恢复候选做同计划一次诊断性测量，但不再将本轮作为可晋级 A/B/A，跳过无效的第三角色并保留候选服务。

原实现 A 精确停止后，补丁已重新应用；新候选 8013 实例 `bd37abcbf719:8013:1534829:294820272` 的 graph/health/北京 smoke 和 16/16 worker 命中通过。原生身份文件 `results/op012-8013-candidate-perf-runtime.json`、`results/op012-8013-candidate-perf-manifest.json`。首次性能角色 runner 在执行前检查时发现 candidate manifest 文件名仍指向最小回归旧实例；尚未对新候选发送性能请求。修正版 `/private/tmp/op012-run-d256-role-v2.sh` SHA256 `00cf7f90ccf68732fc6c0f17acf7dbb347738b64c9a0c9a02382335b46d4b864` 只调整 candidate role 的 manifest 路径，计划、比较阈值、run ID 和 benchmark 命令不变；远端保存为 `commands/performance/op012-run-d256-role-v2.sh`，先单独 dry-run 审阅，再正式执行。

## 8013 配置下的诊断结果与留存状态

候选 B 的 dry-run 再次核对 `/v1/completions`、`MiniMax-M3-opt`、8013、P1024/D256/C64/N128 及 5+3 轮，随后 `performance/op012-8013-d256-warmup5-candidate/run-record.json` 完整退出，8/8 轮各 128/128 成功、0 error；末两预热 output tok/s 为 630.971/624.434，spread 1.04%，通过预热准入。原实现 A 与候选 B 正式轮原始值如下，单位为 tok/s 或 ms；中位数仅是描述，不是通过比较器的收益：

| 角色 | output tok/s r6/r7/r8（中位） | P99 TTFT ms r6/r7/r8（中位） | P99 TPOT ms 中位 | P99 ITL ms 中位 |
|---|---|---|---:|---:|
| 原实现 A | 628.824 / 563.590 / 630.206（628.824） | 6456.611 / 8647.705 / 6550.136（6550.136） | 98.610 | 774.291 |
| MoE 候选 B | 631.167 / 558.823 / 586.626（586.626） | 6459.310 / 8019.103 / 6448.802（6459.310） | 105.192 | 774.598 |

描述性 output 吞吐中位数差为 -6.71%，但 A/B 的 P99 TTFT 正式轮 spread 分别为 33.45%/24.31%，均超预冻结 15%；第三个原实现回退角色未运行（该比较已无法通过稳定性门槛）。状态为 `incomplete`，不能认定 MoE 算子在 8013 下退化 6.71%，更不能把旧 8023 的 +8%/+10% 信号迁移过来。若需严谨决定保留/回退，应先解释这一配置的波次/TTFT 波动，冻结新契约，再从头测同配置 A/B/A。

原生 run-record SHA256：A `ed66a71480e3d70951dc3e1db169e034a7f75c96e041c085dd25b81153865a1b`，B `6b5a7b793bd27cb7d8d62c7d55bdb78eef3ddfeac85583ab83d3f570625d3453`；B manifest `results/op012-8013-candidate-perf-manifest.json` SHA256 `ba37aef98f1faf2234ca3fbbbc3b4b639fe717e426f0d4979c64ff28031e8350`。当前独立优化容器保留实验性 op-011 MoE 补丁，8013 实例 `bd37abcbf719:8013:1534829:294820272` health 正常，进程命令行与 `start-model.sh` 一致且没有 `--max-num-seqs`，日志有 16/16 MoE 命中；8023 不再监听。此次未运行新的 198 题 GPQA，正式精度与性能验收仍未完成；`pr_readiness=experimental`。

补充 shape 边界：8013 候选服务每 10 秒的聚合日志中有 32 个窗口显示 `Running: 64 reqs`，而 op-011 只对 M32 GEMM2 特化。启动期的 16/16 命中来自 graph capture/smoke，不证明 C64 正式测量的主要 decode 批次实际落在 M32；在未取更细的运行时 shape/graph replay 证据前，“M64 占主导使 M32 特化覆盖低”仅是待验证假设。这是本次不能从旧 8023 性能信号推断 8013 收益的另一原因。
