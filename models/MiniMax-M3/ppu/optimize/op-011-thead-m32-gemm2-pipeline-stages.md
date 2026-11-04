# op-011 T-Head M32 GEMM2 pipeline stages

- 状态：单卡筛选通过、服务集成待执行；分类：`operator/improve`；父场景：`p1024-d1024-c64-n128`，Decode/Mixed；依赖：op-010 的 BK64 stage 实验候选（未保留）。

## 优化方向与瓶颈依据

`prof-002` 的 Decode rank0 fused MoE 累计活动为 5.363 s/28406 calls，但活动时间可跨流重叠。`op-008` 证明 16/16 TP worker 实际调用顶层 `invoke_fused_moe_triton_kernel`；目标 GEMM2 为 A=(128,192)、B=(128,6144,192)、C=(32,4,6144)、BF16、M32、E128、top-k4、incoming BM16/BN64/BK128/warps4/stages4。`op-010` BK64 单 stage 测试提升 37.19%，两组端到端 A/B/A 的吞吐观察约 +8%，但 P99 ITL 波动使两组比较都为 `incomplete`，补丁已回退。其结果不能作为本轮通过证据。

本轮先固定 BK64、BM16、BN64、warps4、数据和执行模式，只比较 `num_stages=4` 与 2/3。假设减少 pipeline stage 能进一步降低这个小 K=192 的 stage 完整调用延迟；若并未改善或 graph/数值失败，则不接入服务。原 BK128/stages4 仅作为未优化锚点，不与 BK64/stages2 的差值单独归因。

## 优化内容与适用边界

第一步只在空闲的单张 PPU 上运行独立 MoE stage micro，不修改源码。每个候选使用同一固定输入，分别完成 BF16 对照、graph capture/两次 replay，并用三组不同 seed 做 BK64/stages4 → BK64/stages2 或 stages3 → BK64/stages4 配对测量。按原有 `triton.testing.do_bench` 同步事件计时，同时记录 graph replay 时间；不将 profiler 或单卡数字当成端到端收益。

搜索晋级：某一 stage count 在三组配对实验的中位完整 stage p50 均改善至少 5%，数值一致且 graph 正常。若晋级，才在独立优化容器的私有 FlagGems T-Head vendor 入口实现严格 shape/config guard；非目标 shape/config/dtype/设备全部走原路径。目标服务保持 TP16 BF16、131072 context、`max_num_seqs=32`、`max_num_batched_tokens=8192`、prefix cache off 和原 FULL_DECODE_ONLY graph 配置。不得修改适配容器、权重、tokenizer 或 vLLM。

## 正确性与路径命中

- micro：M32 目标 BF16 reference、finite/最大误差、graph capture 和至少两次 replay；M16 与其他阶段保持原路径。
- 服务候选（仅搜索晋级后）：16/16 worker 实际路径命中、graph capture、smoke/C8、固定 10 题 minimal-regression；如改变图/dispatch 语义则立即完整 GPQA formal-gate。正式阈值仍为 198 道题 strict-match ≥0.88，旧退出服务的 gate 不可沿用。
- 单卡结果：3 个 seed 的 BK64/stages2 对 BK64/stages4 配对完整 stage p50 分别改善 14.49%、14.07%、14.31%；所有目标输出与 stages4 逐位一致，与原 BK128/stages4 BF16 allclose，graph capture+2 replay 全部通过。服务验证仍 `not_run`。

## 性能效果

- micro 主指标：完整 stage p50 ms，三组独立 seed 均需相对 BK64/stages4 ≥5% 改善；这是筛选门槛，不是服务收益。
- 服务 targeted（仅晋级后）：P1024/D256/C64/N128 finite batch，原实现/组合候选/原实现，同参数和同预热准入；主指标 output tok/s，守护 TTFT、TPOT、ITL 与失败。父目标 P1024/D1024/C64/N128 尚需另测。
- 已知尾延迟波动必须保留所有正式轮；若比较器仍为 `incomplete`，不事后删轮或放宽阈值。
- 当前结果：micro 已过筛选门槛；服务端到端仍 `not_run`，未测 Prefill 和 Mixed 守护，不宣称端到端优化。

## 决定、风险与回退

微基准不达门槛即停止，本轮只读优化探查结束。若实施候选，任何数值、graph、live-hit、精度或端到端守护失败即精确回退本轮私有 FlagGems 补丁。回退仅作用于独立容器 8023 任务服务，不碰源适配容器。`pr_readiness=experimental`。

## 外部证据与预记录操作

远程 case：`/mnt/nfs/users/jinghao/minimaxM3/20260921-minimax-m3-ppu-e2e`。进入单卡 micro 前，只读核对当前优化容器、8023 PID/start time/launch、无评测和 benchmark 客户端及 PPU 进程；然后仅使用已存在的 `commands/performance/stop-minimax-service-for-microbenchmark.sh op011-before-stage-screen` 停止绑定服务。micro 脚本先保存至 `commands/performance/`，原始结果留 `results/`、日志留 `logs/`，使用不存在的新文件名。若 micro 未晋级，用已有 `launch-minimax-service-from-stopped.sh` 加原始源码启动命令恢复 8023，并检查 graph/health/smoke。所有实际路径、SHA 和结果在执行后补录。

本轮单卡脚本本地执行副本 `/private/tmp/op011-moe-stage-screen.py` SHA256 `63bb22c3eb66680cc1363342816bbe4f0d034fc1e0787894c5ea6bc555613d34`；runner `/private/tmp/op011-run-moe-stage-screen.sh` SHA256 `11ed56cc5c916218785fb492618c3b40d0f5e57db2bd06c837b5342b652b2f4d`。仅在远端同名目标不存在时上传到 `commands/performance/`，校验 SHA 后执行。预记录命令（case 目录为当前目录，任何检查失败即停）：

```bash
commands/performance/stop-minimax-service-for-microbenchmark.sh op011-before-stage-screen
commands/performance/op011-run-moe-stage-screen.sh
# 若筛选未晋级：原私有源码不变，恢复 8023；命令文件使用已有 op010-perf2-revert-service.sh 的原参数。
commands/performance/launch-minimax-service-from-stopped.sh \
  op011-post-screen-original-launch \
  commands/performance/op010-perf2-revert-service.sh \
  logs/op011-post-screen-original-131k-server.log
```

执行记录：已核验仅有任务独立容器 8023 实例 `bd37abcbf719:8023:1368844:288789027` 且无评测/benchmark 客户端，精确停止并释放 16 张 PPU；源适配容器未动。脚本经 Ansible `force=false` 上传并校验 SHA。原生结果 `results/op011-moe-stage-screen.json` SHA256 `c24e4842ac250847cb0ba50f3b8cff850026197123edc8fc7dcc566110e83147`；日志 `logs/op011-moe-stage-screen.log` SHA256 `22ae9480bd311415502e493ba082640fdf7aa3cc23385faa18dd163b1228ea1a`。三组 A/B/A p50（ms）：seed 20260924 的 BK64/stages4 0.19012/0.19008、stages2 0.16256；seed 20260925 原 0.19404/0.19408、候选 0.16676；seed 20260926 原 0.19044/0.19036、候选 0.16316。`num_stages=3` 三组也提升 11.93–12.23%，但均低于 stages2，故只晋级 stages2。此次微测的 `triton.testing.do_bench` 是单卡 stage、无完整模型，不能直接宣称端到端收益。

服务集成候选补丁本地执行副本 `/private/tmp/op011-thead-m32-gemm2-bk64-stages2.patch` SHA256 `b9669b0d0aa9d5a56f8bcdb1365af835f74d362993d6d4fff8d2dcf8e617b9af`，仅更改私有 FlagGems 的 `_thead/fused/__init__.py` 并新增 `_thead/fused/fused_moe.py`。它复用 op-010 已真实命中的精确 stage guard，同时将 BK128→64、`num_stages`4→2；两个变化是 op-010 实验依赖和本轮增量，不从原路径对组合的差值单独归因给 stages。临时一次性 `op011` 命中标记用于 16 worker 证明，后续 PR 整理时移除并重新测试。预记录远端变更命令：先对补丁 SHA、原 vendor init SHA `6a965e61477dde4bdc43e6c6587294a0e28debb9a91f4809eeb93e903c118994`、新文件不存在、无服务/设备占用做断言；`git -C /workspace/FlagGems apply --check <case>/patches/op011-thead-m32-gemm2-bk64-stages2.patch` 通过后才 `git apply`，随后核对 `git diff --check`、实际文件 SHA、顶层导入与特化配置。失败不得静默继续启动服务。回退只以该补丁 `git apply -R`，需先核对候选 SHA，不改 `sql.py` 和 Plugin blacklist。

远端可执行变更副本 `commands/performance/op011-apply-moe-candidate.sh`，本地原件 `/private/tmp/op011-apply-moe-candidate.sh` SHA256 `a8c31ce6d0d5347cd759dae5b2cc709c9400fd5140f7fe93f56554a8d798bce6`；执行前 `force=false` 上传并校验。唯一 transition `transitions/op011-apply-moe-candidate` 保存应用后 SHA 与状态。命令：`commands/performance/op011-apply-moe-candidate.sh`。

候选已在私有 FlagGems 副本应用，公共 MoE 文件不变；`_thead/fused/__init__.py` SHA256 `fae31da546fd72fb937a9a79033e3dae09ac730446d90eeeb08367da1ace9f9d`，新增 vendor wrapper SHA256 `dcbfa3fd2011711fcd05a1045a3d918907f87c6b11039ee69a537b53c2f9e9ed`。新进程顶层 API source 指向 `_thead/fused/fused_moe.py`。下一步在服务启动前使用目标/回退 stage 回归：本地 `/private/tmp/op011-vendor-stage-regression.py` SHA256 `98cb0605ddff67ba7317ec0960e6f8a6d11f42b832357389229b78cfb33bbacb`；runner `/private/tmp/op011-run-vendor-stage-regression.sh` SHA256 `0470c1e1041a1c4b93dcffbb867c1af0b06f194be84039c4f3ad940a89800945`。仅新路径上传至 `commands/performance/` 并核验 SHA；命令 `commands/performance/op011-run-vendor-stage-regression.sh`；结果/日志分别为 `results/op011-vendor-stage-regression.json`、`logs/op011-vendor-stage-regression.log`，不得覆盖。

vendor stage 回归已通过：M1/2/4/8/16 与原 generic 逐位相同且命中 0，M32 逐位相同且 vendor 命中 1；另一个 M32 incoming BK64 配置不被误命中。M32 graph capture 与两次 replay 后仍逐位相同。结果 `results/op011-vendor-stage-regression.json` SHA256 `cf54681a00f3dfd08c54af69478e54c6ee23d30de8a61eb6380e87c68dc69346`；日志 `logs/op011-vendor-stage-regression.log` SHA256 `41e59b2a1eeddfd3f3160d41cd69155321d95e0bfa69d70f99b6b15d5c9ccb9d`。

下一步目标 TP16 服务命令副本 `/private/tmp/op011-candidate-131k-service.sh` SHA256 `8e10cd93a51ea900e9ee45d3141409ae2c6ced3b4ac1c128fdeb17fea0a7ce01`，与上一轮原路径脚本相比仅改变专用日志名并移除 role 变量，vLLM 参数和 cache 路径完全相同。上传至 `commands/performance/op011-candidate-131k-service.sh` 且校验后，以已有精确 launcher 执行：

```bash
commands/performance/launch-minimax-service-from-stopped.sh \
  op011-candidate-131k-launch \
  commands/performance/op011-candidate-131k-service.sh \
  logs/op011-candidate-131k-server.log
```

必须核对 graph capture、health、北京 smoke、16/16 worker 标记与实际服务身份，未通过不得开始精度或性能评测。

TP16 候选已启动；`logs/op011-candidate-131k-server.log` 原生出现 16 个不同 `Worker_TP0..15` 的 `op011 THEAD_M32_STAGE2_BK64_STAGES2_HIT` 标记、FULL_DECODE_ONLY 6/6 capture、`enable_prefix_caching=False`、startup complete，launcher 的固定北京 smoke 和 health 通过。原服务启动期 FA2 不可用提示仍存在，不能据此判定是本轮 MoE 回归；测量期须继续观察致命错误。

评测前服务身份脚本：本地 `/private/tmp/op011-build-service-manifest.py` SHA256 `03eead3fba5051b9f0578eac82912dbe60be27377d227b9e11168f5088ae7b99`，本地 `/private/tmp/op011-collect-service-identity.sh` SHA256 `e8aee757f68cf6d1379475f87252da9636742edf2e6140aeb7c655cc2cadca95`；上传至 `commands/performance/` 的新文件并核验。采集脚本在独立容器内用已维护的 `capture-baseline-service.py` 生成 `results/op011-candidate-runtime.json`，校验源码、graph、16 worker 命中和 blacklist 后生成 `results/op011-candidate-performance-manifest.json`，再用维护版实时 identity verifier 核对 PID/start_ticks；失败即停止评测。命令 `commands/performance/op011-collect-service-identity.sh`。

候选服务身份 `bd37abcbf719:8023:1383226:292858289`，runtime `results/op011-candidate-runtime.json` SHA256 `1d5930f472088dd6ecbb073ccf8e856e5c90d17ba4f60c842fead3f3a1510a75`；manifest `results/op011-candidate-performance-manifest.json` SHA256 `e117b8633b05435f22c45c0fdfaeac808cec3b0c9c9ad0df3d380b49d688887c`；实时 verifier 通过。当前 FlagGems-vllm + FlagGems 联合内容 SHA256 `62504469e7be6276d554dc26a59d5589824f66cdf4b64543156eba3e0999f82c`，为此候选独有，正式精度旧 gate 不可沿用。

精度 Skill 显式使用 `minimal-regression`：固定 GPQA 前 10 题、C8、seed42、greedy、max_gen_toks60000，仅护栏，**不签发 198 题 gate**。新配置本地 `/private/tmp/op011-minimal-regression.json` SHA256 `75ee91a474a23dce30c19f439974c6889621a1a26e052a3f04c40dc5c1687825`，远端新路径 `commands/accuracy/op011-minimal-regression.json`；preflight 脚本 `/private/tmp/op011-preflight-minimal-regression.sh` SHA256 `03d5becfd3da221206f7a95bf96eb79992a3243f3cd64c899ee0cf491dc42bec`，launch 脚本 `/private/tmp/op011-launch-minimal-regression.sh` SHA256 `9ec3abc3f246f28206608eaf5dbca62673b190f40ba19b6f2df4b3717f998ef3`，远端对应 `commands/accuracy/` 新路径。上传校验后先运行 `commands/accuracy/op011-preflight-minimal-regression.sh`；只有 preflight 通过并在启动真正 evaluator 之前创建本任务 30 分钟只读 heartbeat，才运行 `commands/accuracy/op011-launch-minimal-regression.sh`。终态读取原生结果、样本与健康观察后停用 heartbeat。

原生 preflight 已通过，仅创建 `accuracy/op011-minimal-regression/` 的评测容器身份和 preflight 证据，尚未启动 lm-eval。按精度 Skill 在实际评测前创建本任务 heartbeat `minimax-m3-op011-minimal-gpqa-c8-60k`，每 30 分钟只读观察精确评测进程、服务与上述路径，每次通知，终态停用；不得修改或复制进程。

最小精度回归已原生退出码 0 完成，耗时 640.876 s：10 道唯一 `doc_id`、strict-match 10/10；20 行样本来自 strict/flexible 两种 filter，不能当成 20 题。无 timeout、空输出或 60000-token 截断，最大 completion 22449 tokens。结果 JSON SHA256 `2e81933f4fd9cc08657a7eb1adf59037a64586eb87fbdae229db6960f5c52763`，样本 JSONL SHA256 `bbb14475d6f996e9a5b1eb5358a2e8cef1f8f291dd2b23d43a84f9f628fa3ef6`；原始路径均在 `accuracy/op011-minimal-regression/`。评测后实时 verifier 仍确认候选实例 `bd37abcbf719:8023:1383226:292858289`，health=200。heartbeat `minimax-m3-op011-minimal-gpqa-c8-60k` 已于原生终态后暂停。此结果只证明本轮最小回归，不是完整 198 题 gate。

性能 Skill 拟显式使用 `targeted` 模式，milestone `p1024-d256-c64-n128` 映射父目标 `p1024-d1024-c64-n128`，只缩短输出 1024→256；不等于正式场景通过。精度最小回归通过之后，复用已冻结且仍与本轮目标完全相同的 `commands/performance/op010-p1k-d256-warmup5-plan.json` 实测 SHA256 `4ed3a76e6b2a8d20277cfece3641461bb5f5f5b502e2c7a14c29a1e0efaa8e2c`（P1024/D256/C64/N128，finite batch，5 预热+3 测量，每角色独立服务实例，末两预热吞吐 spread≤10%，首个测量轮不事后删除）。本轮新比较契约本地 `/private/tmp/op011-p1k-d256-comparison.json` SHA256 `e9f20ed7d53af81f31b890dca63c24ec17726835242dfb3903b21cbb342f4db4`，拟存 `commands/performance/op011-p1k-d256-comparison.json`；原路径/候选/原路径 A/B/A，同一个变量 `/flaggems_sha256`，主指标 output tok/s 至少 +3%，total throughput 退化≤3%、P99 TTFT≤5%、P99 TPOT≤3%、P99 ITL≤10%，每角色三轮 spread≤15%，A/revert 漂移≤10%。这是在看到本轮服务性能前冻结的门槛，不因 op010 的历史 `incomplete` 放宽稳定性约束。任何比较 `incomplete` 时仅报告数值信号而不晋级。

预备的性能变更和测量脚本均须先以 `force=false` 存入远端 `commands/performance/` 新路径，并逐个核验 SHA：

- `op011-switch-moe-candidate.sh`：`a18da8b9ca805eaba2fa188fbc5ad06699f555d554d3aa710c4ec54bff70662a`，精确候选/原 SHA、空闲服务与设备、补丁逆向检查；只改本轮 vendor 两文件。
- `op011-performance-service.sh`：`2c69a557b85a16008650a6653ef75f6c7ce8aa62f7965a949d97b6d4dedc4dd5`，baseline/candidate/revert wrappers SHA 分别 `6524bee2cca6ef5caa43b306c9234a26dd2e1820225aecd8bee6a4f1426100a0`、`133809ebd681dcabeba056e1bcb3ffa9a816a75a47da9fb239efde8b9361fcd8`、`e5c3be72d3ab0fa74fb193be6e296628e9ec7bf634be93c70f2ae48e6102a30f`。服务参数/cache 不变，仅使用唯一日志名。
- `op011-collect-performance-identity.sh`：`3705b68f7762cf7f64cd30b010d245a4a7cd9030a96c3d89199e0810ac814bdc`，每角色新 runtime/manifest，原路径使用已有原版 builder，候选使用本轮 builder。
- `op011-run-d256-role.sh` 原版：`b0bf5c43d3dbb9960c0f1be2f7cfd0b0205e57ccdb377443261582ba84636103`，预执行的 plan SHA 手工抄录错误，首次 baseline 在 dry-run 之前退出，0 请求、未创建 run 文件。修正后的远端新文件 `op011-run-d256-role-v2.sh` SHA256 `bbfe34244887d4047d7bd1bae39543e0ce50ab000e97ad101ea3e7056e703e66`，只修正断言中的 SHA 字符，不改变 plan、contract、命令或输出路径；先 dry-run 再测 5+3 轮，run ID 唯一并拒绝覆盖。

最小回归通过且无客户评测进程后，预记录 A/B/A 远端顺序（case 为 cwd；任一门禁失败即停；旧候选实例在第一步精确停止）：

```bash
commands/performance/stop-minimax-service-for-microbenchmark.sh op011-perf-before-baseline-stop
commands/performance/op011-switch-moe-candidate.sh revert op011-perf-baseline-source
commands/performance/launch-minimax-service-from-stopped.sh op011-perf-baseline-launch commands/performance/op011-perf-baseline-service.sh logs/op011-perf-baseline-131k-server.log
commands/performance/op011-collect-performance-identity.sh baseline
commands/performance/op011-run-d256-role-v2.sh baseline
commands/performance/stop-minimax-service-for-microbenchmark.sh op011-perf-before-candidate-stop
commands/performance/op011-switch-moe-candidate.sh apply op011-perf-candidate-source
commands/performance/launch-minimax-service-from-stopped.sh op011-perf-candidate-launch commands/performance/op011-perf-candidate-service.sh logs/op011-perf-candidate-131k-server.log
commands/performance/op011-collect-performance-identity.sh candidate
commands/performance/op011-run-d256-role-v2.sh candidate
commands/performance/stop-minimax-service-for-microbenchmark.sh op011-perf-before-revert-stop
commands/performance/op011-switch-moe-candidate.sh revert op011-perf-revert-source
commands/performance/launch-minimax-service-from-stopped.sh op011-perf-revert-launch commands/performance/op011-perf-revert-service.sh logs/op011-perf-revert-131k-server.log
commands/performance/op011-collect-performance-identity.sh revert
commands/performance/op011-run-d256-role-v2.sh revert
python3 commands/performance/compare_performance.py --contract commands/performance/op011-p1k-d256-comparison.json --run-record performance/op011-d256-warmup5-baseline-01/run-record.json --run-record performance/op011-d256-warmup5-candidate-01/run-record.json --run-record performance/op011-d256-warmup5-revert-01/run-record.json --output performance/op011-d256-warmup5-aba-comparison.json
```

执行进度：最小回归后旧候选服务已精确停止；`op011-perf-baseline-source` 把本轮 vendor 补丁逆向回退到原 SHA，而 `sql.py` 和 Plugin blacklist 均保持原状。原路径 baseline 服务 `bd37abcbf719:8023:1390556:293012555` 已 graph/health/smoke 通过，manifest `results/op011-perf-baseline-performance-manifest.json` SHA256 `b81489f5b01c6bd0e184ebd120a4787a7fd1900448261de1947e083fcfd61069`。实际 dry-run 预览确认为 P1024/D256/C64/N128、固定 seed 派生、5+3 轮、prefix cache off。首次 runner 因手工抄错 plan SHA 在 dry-run 前退出，0 请求、无 run 目录；v2 只修正断言。原路径 baseline `performance/op011-d256-warmup5-baseline-01/run-record.json` 已 complete：5 次预热末窗 spread 0.1607%，3 次正式轮次均 128/128 请求成功；output throughput 464.396/465.252/466.283 tok/s，median 465.252 tok/s。P99 ITL 277.54/283.81/304.69 ms，仍需依照冻结比较器检查稳定性，不能单看 throughput 宣称增益。之后服务被精确停止、补丁重新应用，候选 B 服务 `bd37abcbf719:8023:1404307:293134231` graph/health/smoke 通过且 16 worker 命中；manifest `results/op011-perf-candidate-performance-manifest.json` SHA256 `33038e1e62158b6b32bf70ff221cd20d49246418b25a8ca3f606893076ed869c`。候选 dry-run 契约同上，其正式轮次进行中。

首轮 A/B/A 全部 5+3 轮执行成功，候选 output throughput 中位数 512.358 tok/s，回退 A 中位数 466.222 tok/s；但冻结比较器 `performance/op011-d256-warmup5-aba-comparison.json` 状态为 `incomplete`，唯一 issue 是候选 manifest 的 `performance_context/cache_preparation` 描述比 A 两端少了 `; same case cache paths.`，属于元数据文字差异，并非测量轮失败。不能事后改签名或把这份回执称为通过。当前服务是原路径回退实例 `bd37abcbf719:8023:1421587:293226422`，原始 MoE SHA 已恢复。计划在不改变 plan/阈值/源码的前提下，以当前回退服务作为新一轮 A，使用统一描述的候选 manifest，重新做完整 A/B/A；所有新产物用 `wave2` 唯一命名。候选描述标准化仅允许上述已核验旧文案改为 A 两端的文案；两者启动命令、缓存路径、prefix cache off、graph capture 设置不变。新执行副本 `/private/tmp/op011-wave2-normalize-manifest.py` SHA256 `e0e9540743fe19b0f2286231ca0cd67001edb5c8bb05e81e4f5e3c45df261c1a`，`/private/tmp/op011-wave2-run-role.sh` SHA256 `25d69ea9fb1d9788d5005a48d1670bf4d64be97c66e0431771abb291403bc6cc`，将以 `force=false` 上传至 `commands/performance/`。预记录顺序：运行 wave2 baseline；精确停止当前 8023 服务；复用已校验 op011 补丁应用命令；以独立 wave2 日志启动候选；捕获 runtime、调用已校验的 op011 manifest builder 并产生唯一 raw manifest，再以标准化脚本产生正式 manifest，verify-live 后运行 wave2 candidate；精确停止、回退补丁、以独立 wave2 日志启动原路径；捕获 runtime、调用原路径 manifest builder 产生正式 manifest，verify-live 后运行 wave2 revert；最后用原冻结比较器输出独立 wave2 回执。中途任一失败保留原生证据并不升级候选。

wave2 baseline `performance/op011-d256-warmup5-wave2-baseline/run-record.json` 已 complete，8/8 轮、errors=[]，预热末窗 spread 0.1301%。首次 wave2 candidate 启动尝试意外沿用旧 wrapper；它检测到首轮旧日志已存在而退出，导致启动器仅等待 health、没有新服务、没有 benchmark 请求。确认当前容器无 8023 API 进程后，精确终止这次孤立启动器 PID 4013706；失败 transition 留存 `transitions/op011-wave2-candidate-launch`，不重用。修正为同一启动参数和同一 `cache/baseline-no-prefix` 缓存路径、独立 wave2 日志的脚本：`/private/tmp/op011-wave2-service.sh` SHA256 `3f236c8c964610058125a9ea012e6a05a3d479eb15c8ad18468ff80da22a133f`，candidate wrapper SHA256 `4c1a59e489adde24a62f3d73a421bb57eba1a9599d34c6e3cc8486658a1423e3`，revert wrapper SHA256 `1f60c62f5fff87c04c164439513928688478e7c997e25ac587a768fffde40f0c`。三者上传到 `commands/performance/` 并校验后，用唯一 transition `op011-wave2-candidate-launch-v2` 再启动；原路径 PPU 释放和候选源码 SHA 已通过先前检查。

wave2 B 启动 graph/health/smoke 通过、16/16 worker 命中。一次容器相对路径误用留下空 `results/op011-wave2-candidate-runtime.json`（未进入证据链），改用绝对路径生成 `results/op011-wave2-candidate-runtime-v2.json`，原始候选 manifest 与经文案标准化的正式 manifest 分别存 `results/op011-wave2-candidate-manifest-raw.json` 和 `results/op011-wave2-candidate-manifest.json`（后者 SHA256 `bc05bf0103cdad79091e6f35f29c2cc7e4bfe46b1e134112fac5a8a4fb3cc786`）。wave2 B `performance/op011-d256-warmup5-wave2-candidate/run-record.json` 8/8 轮 complete、errors=[]、预热末窗 spread 0.2753%。候选服务精确停止，补丁按 SHA 逆向撤销；wave2 最后 A 服务 `bd37abcbf719:8023:1456618:293547846` graph/health/smoke 通过，manifest `results/op011-wave2-revert-manifest.json` SHA256 `5608902528182fb3c1718b361f2bcb76daebe37810d31cdde908d05593939e59`，`performance/op011-d256-warmup5-wave2-revert/run-record.json` 8/8 轮 complete、errors=[]、预热末窗 spread 0.4558%。全部正式测量轮原样保留，没有事后剔除。

冻结比较器回执 `performance/op011-d256-warmup5-wave2-aba-comparison.json` SHA256 `b0d10ea2416c5a8abe029ef36ac378a3d72ecd60980e2a36e9709984ec577b6c`，`changed_paths` 仅 `/flaggems_sha256`，状态 **incomplete**。P1024/D256/C64/N128 output throughput 中位数 A/B/A 为 464.772/512.363/463.071 tok/s，候选相对首个 A 的诊断信号 +10.24%；total throughput 2323.861/2561.813/2315.356 tok/s，P99 TTFT 21047.87/19114.34/21198.20 ms，P99 TPOT 67.757/61.484/68.062 ms。但 P99 ITL 分轮 A 为 278.67/303.20/303.40 ms，B 为 549.13/285.36/284.63 ms，最后 A 为 480.36/370.04/373.12 ms；B、最后 A 的轮间 spread 和 A 两端 ITL 漂移违反预冻结稳定性上限。故不能以中位数吞吐信号晋级或宣称端到端收益。首轮比较回执 `performance/op011-d256-warmup5-aba-comparison.json` SHA256 `0c1ab366eae837ea41aa2a05daf742c346d71ce18b9d9ef8e2f0b325a96ce55e` 也保持 `incomplete`，原因是 manifest 描述差异，未被覆盖。

最终决定：op-011 仅保留单卡 stage 正向、BF16/graph、TP16 真实命中与 10/10 最小精度证据；本次候选**不晋级、不保留源码改动**，不做 P1024/D1024 正式性能或 198 题正式 GPQA gate。当前独立容器 8023 实例 `bd37abcbf719:8023:1456618:293547846` 保持健康 200，私有 FlagGems vendor init 已恢复原 SHA256 `6a965e61477dde4bdc43e6c6587294a0e28debb9a91f4809eeb93e903c118994`，本轮新增 vendor 文件不存在；先前已保留的 fw-006 SQL 反射优化和 Plugin `thead.yaml` 黑名单未回退。下一轮应先解释 P99 ITL 波动来源或预先制定可复现的尾延迟稳定性契约，再判断是否重试 MoE 候选；本轮不放宽门限，也不把 op-010/op-011 孤立增益相加。

## 2026-09-24 用户要求恢复候选（执行前记录）

用户明确要求将原 MoE 优化恢复到当前独立优化容器。本次按最近一轮 op-011 解释：严格 T-Head/M32/BF16/MoE GEMM2 guard，`BLOCK_SIZE_K` 128→64 且 `num_stages` 4→2；这只是恢复实验候选，不改变此前 `incomplete` 的性能结论，也不继承旧服务的精度 gate。

执行范围仅为 PPU-07 的 `minimaxM3-opt-20260921` 容器及其 8023 任务服务。执行前核对实例、无评测客户端、原私有源码 SHA、补丁 SHA 和 `git apply --check`。使用已有受校验的远端 `commands/performance/stop-minimax-service-for-microbenchmark.sh` 精确停止该服务；以 `commands/performance/op011-switch-moe-candidate.sh apply op011-restore-20260924-source` 应用已留存补丁 `patches/op011-thead-m32-gemm2-bk64-stages2.patch`（SHA256 `b9669b0d0aa9d5a56f8bcdb1365af835f74d362993d6d4fff8d2dcf8e617b9af`）；通过已有 launcher 启动新的、唯一日志的候选服务。新服务命令先保存为远端 `commands/performance/op011-restored-20260924-service.sh`，本地执行副本 `/private/tmp/op011-restored-20260924-service.sh` SHA256 `ddd7574a9c59edd29e599665a26494a875e76be1ac86cc6f788d17769e2d6361`，仅日志路径与前一轮 wave2 脚本不同。启动后验证 graph、health、smoke、16/16 worker 命中及进程参数；失败时不宣称恢复成功，按补丁的逆操作精确回退，并记录终态。

当前运行实例的命令行以及前一轮 `commands/performance/op011-wave2-service.sh` 都显式含 `--max-num-seqs 32`；用户提到的未设置该参数的脚本尚未定位为当前 8023 实例的启动依据。本次恢复保持运行实例参数不变，不同时改变服务并发上限，避免配置变量混入 MoE 对比。
