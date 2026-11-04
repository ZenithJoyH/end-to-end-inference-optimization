# op-010：T-Head 实际 MoE stage 入口 M32 GEMM2 BK64

- 分类：`operator/improve`；父场景 `p1024-d1024-c64-n128` Decode/Mixed。
- 状态：设计冻结，候选未进入目标模型评测。
- 目标：PPU-07 独立优化容器 `minimaxM3-opt-20260921` 私有 FlagGems；适配容器、模型权重/tokenizer、vLLM 不改。

## 前置证据与 op-009 纠错

op-008 真实 TP16 131K graph 服务 stdout 探针在 16/16 worker 均证明 `flag_gems.invoke_fused_moe_triton_kernel` 执行；M32 GEMM2 `A=(128,192), B=(128,6144,192), C=(32,4,6144)`，BF16、top_k=1、config BM16/BN64/BK128/warp4/stage4。`prof-002` Decode rank0 MoE 累计活动 5.363s，但可重叠，不能当端到端收益。op-009 以 T-Head 顶层 `fused_experts_impl` wrapper 作候选，单卡线上 stage4 对齐 full-call A/B/A 提升 20.15%，然而真实 TP16 graph/smoke 命中 0；该服务已停止，补丁已精确回退为原始 SHA，未运行无效的 GPQA/E2E。结论只是否定 full-call wrapper 这个接入点，不是否定 stage BK64 假设。

## 待执行的同配置性能 A/B/A 控制命令（2026-09-23 20:32 CST 预冻结）

最小精度回归已于 2026-09-23 20:34:50 CST 原生退出码 0 完成，耗时约 10 分 53 秒。`accuracy/op010-minimal-regression/` 下结果 JSON SHA256 `3692b4e0e945898dc7ad4a7f287a301a847889c68ab3e1626a10cc3ee9eba07e`，样本 JSONL SHA256 `bbb14475d6f996e9a5b1eb5358a2e8cef1f8f291dd2b23d43a84f9f628fa3ef6`，runner log SHA256 `2abc6572efc8bd5816f14ac956a6dfc0323ee374f07bd29af9053d1d7bb16380`。原生样本为 10 道唯一 `doc_id`，各有 strict/flexible 两种 filter 共 20 行；strict-match 10/10，flexible-extract 6/10；timeout 0、空输出 0、completion 最大 22449＜60000。该结果只为最小正确性护栏，不能签发 198 题正式精度 gate。完成后已通过维护的 service identity verifier 核对仍为候选实例 `bd37abcbf719:8023:1297632:288148032`，且无评测/benchmark 客户端；心跳 `minimax-m3-op010-minimal-gpqa-c8-60k` 已暂停。

仅在最小回归产生原生终态且无阻塞后，才停止绑定的候选服务。切换仅涉及独立优化容器和当前 case；每次重启重新 capture 服务身份，不复用旧 gate。基线与回退须精确核对 vendor 原 SHA 和新文件缺席；候选须核对双文件 SHA 和 16/16 worker 实际命中。三实例同启动参数/缓存目录，唯一变量为 FlagGems vendor stage wrapper。

本地脚本 SHA256：`op010-switch-stage-vendor.transfer.sh`=`3c19f8df93b0377919a6d636e892f64c2a247c4ecae560b9660ed226bd00d2fd`；`op010-performance-service.transfer.sh`=`0826067497df2ac711dbae8f64869e1978dc83ffee9adcabcadfb6ff646aedd8`；baseline/candidate/revert 服务 wrapper 分别为 `cfaec066437736869dcbbe2b64d279b0d0631e13f083bda4920528437f992805`、`b05a2b0e73e1d860aca74f27d9cc6f88f01075c63b41eabde7e35fd0808fb0f9`、`8adb65a2d38adebc47d4e005e7c3f4fca5b61531addecad31a33736f3e8c6b07`；`op010-collect-performance-identity.transfer.sh`=`a852fb077d168c435aae7afd3d0eff5e43a244919295b8433e21e94205d9c068`；`op010-run-d256-role.transfer.sh`=`3edd4ef67ea6aedf4cbe59c173c63fdd19f11522aaa0b9742e47c002e805ce4f`。上传到远端 `commands/performance/`，逐个 `force=false` 并校验 SHA；日志、transition、runtime/manifest、dry-run、run-record 均用唯一名且拒绝覆盖。

远端执行顺序（失败即暂停，不跳过门禁；以下以 case 根目录为 cwd）：

```bash
# A：停当前最小精度候选服务，回退 op010 补丁，启动原路径实例。
commands/performance/stop-minimax-service-for-microbenchmark.sh op010-perf-before-baseline-stop
commands/performance/op010-switch-stage-vendor.sh revert op010-perf-baseline-source
commands/performance/launch-minimax-service-from-stopped.sh op010-perf-baseline-launch commands/performance/op010-perf-baseline-service.sh logs/op010-perf-baseline-131k-server.log
commands/performance/op010-collect-performance-identity.sh baseline
commands/performance/op010-run-d256-role.sh baseline
# B：停止 A，应用精确补丁，启动新候选实例。
commands/performance/stop-minimax-service-for-microbenchmark.sh op010-perf-before-candidate-stop
commands/performance/op010-switch-stage-vendor.sh apply op010-perf-candidate-source
commands/performance/launch-minimax-service-from-stopped.sh op010-perf-candidate-launch commands/performance/op010-perf-candidate-service.sh logs/op010-perf-candidate-131k-server.log
commands/performance/op010-collect-performance-identity.sh candidate
commands/performance/op010-run-d256-role.sh candidate
# A：停止 B，精确回退并复测原路径。
commands/performance/stop-minimax-service-for-microbenchmark.sh op010-perf-before-revert-stop
commands/performance/op010-switch-stage-vendor.sh revert op010-perf-revert-source
commands/performance/launch-minimax-service-from-stopped.sh op010-perf-revert-launch commands/performance/op010-perf-revert-service.sh logs/op010-perf-revert-131k-server.log
commands/performance/op010-collect-performance-identity.sh revert
commands/performance/op010-run-d256-role.sh revert
```

`op010-run-d256-role.sh` 每角色先通过维护的 `vllm_perf.py --dry-run`，再运行 warmup3+measured3；比较只读取三个新绑定的 `run-record.json`，不得用 op007 数据替代。性能结果未产出前不宣称端到端收益。决定保留后还须移除实验 stdout 标记，重新验证 graph、性能和精度并签发新正式 gate。

三角色均成功后只读比较命令（`compare_performance.py` 为维护版，目标输出不得已存在）：

```bash
python3 commands/performance/compare_performance.py \
  --contract commands/performance/op010-p1k-d256-comparison.json \
  --run-record performance/op010-d256-baseline-01/run-record.json \
  --run-record performance/op010-d256-candidate-01/run-record.json \
  --run-record performance/op010-d256-revert-01/run-record.json \
  --output performance/op010-d256-aba-comparison.json
```

2026-09-23 baseline A 已执行：最小回归候选实例经 verifier 确认后停止，`transitions/op010-perf-before-baseline-stop/`；`op010-perf-baseline-source` 精确恢复 T-Head fused init 原 SHA 且删除本轮 vendor 文件；原路径 graph/health/北京 smoke 通过。A 服务实例 `bd37abcbf719:8023:1304782:288300092`，manifest `results/op010-perf-baseline-performance-manifest.json` SHA256 `dca0e87299f87a6c09747bd59d68ef1bfcb9f569541201d3df1c0414df6a5cac`，runtime SHA256 `5261f2870b88d53b4b3306922e8df63ddaee1cefea99ed3db2c565642ac62155`。`performance/op010-d256-baseline-01/run-record.json` 原生 `status=complete`、errors 空、3 warmup+3 measured 全部 returncode0；末两预热 output throughput 465.70865/464.17012 tok/s、spread 0.00331≤0.10。此时仅有 A，不计算候选收益。A 实例已在无客户端时精确停止，`op010-perf-candidate-source` 复原本轮两个 vendor 文件的候选 SHA，正在启动 B。

候选 B 实例 `bd37abcbf719:8023:1316931:288383620`，manifest SHA256 `ed2bb5b5051c21b53ed042450263de574830c2d0740c99bc4195873da903b4b3`，runtime SHA256 `737698e8dcb364facdcd459452bbb6e0b66fdd1177ebfa6f51f570d15fc72c0a`；新实例 16/16 worker 真实命中，graph/health/smoke 通过。`performance/op010-d256-candidate-01/run-record.json` 原生 complete、errors 空、3+3 全轮 returncode0，末两预热 output tok/s 498.71098/503.59960，spread 0.00975≤0.10。已观察 A/B 测量输出吞吐中位数 463.327/500.298 tok/s，差约 +7.98%；B P99 ITL 三轮 476.22/281.68/281.32ms，波动明显，正式判定必须等待回退 A 和冻结比较器。B 已无客户端时停止，`op010-perf-revert-source` 精确回退 vendor 补丁，正在启动最终 A 实例。

回退 A 实例 `bd37abcbf719:8023:1329041:288467840`，源码内容 SHA 与首组 A 完全相同；`performance/op010-d256-revert-01/run-record.json` 原生 complete、errors 空、预热准入 passed、3+3 全轮 returncode0。冻结比较器回执 `performance/op010-d256-aba-comparison.json` SHA256 `33f37966e6261ffa9640155332d48d2950b2a905a61a3b959034e5f48feea8c1`，状态 **incomplete**，唯一 issue 为 `p1024-d256-c64-n128/candidate/p99_itl_ms: excessive within-process spread`；B ITL 三测量轮 476.22/281.68/281.32ms，不能事后剔除第一轮。A/B/A output tok/s 中位数 463.327/500.298/463.110，观察改善 +7.98%，回退漂移 0.05%；P99 TTFT 21124/19638/20928ms，P99 TPOT 67.68/62.69/67.87ms，但上述 ITL 波动使该轮不得晋级为通过的端到端性能结论。比较器确认唯一变化路径 `/flaggems_sha256`。B 服务日志未见测量期致命错误；启动期 FA2 不可用提示与候选异常轮的因果关系未证实。当前原路径回退服务仍在 8023。

### incomplete 后的同契约稳态重测（2026-09-23 21:22 CST 冻结）

只针对测量准入不足调整预热轮数 3→5，仍用同一 P1024/D256/C64/N128 finite-batch、3 measured、C64/N128、seed/参数、比较阈值和 ITL ≤15% spread 守护；A/B/A 三个角色必须全部按新计划从独立新进程测量，不继承上一轮任何结果或服务身份。新计划 `commands/performance/op010-p1k-d256-warmup5-plan.json` 本地 SHA256 `4ed3a76e6b2a8d20277cfece3641461bb5f5b502e2c7a14c29a1e0efaa8e2c`；比较契约仍为原 SHA `a6b411a6e905566a4077e456cee3ba0778b656a09f5120e6705e28a7e0ced554`。若仍有 ITL spread 超限，则维持 `incomplete`，停止 op010 晋级，转入尾延迟根因分析或回退，不继续通过改变阈值追分。

第二轮脚本本地 SHA256：`op010-performance2-service.transfer.sh`=`fe9de1c40091830e37a752ac94087dcf81232788425089e196a312e89cf8e884`；baseline/candidate/revert wrapper 分别 `5deb60a71a0b0b53bf433c646bcd5ef317b572cfd104675433cd64d2ef4893dc`、`38122deb4ba0c1a3d7b584bccd2f7923214f8e82b4811910a47f448b76b05f53`、`84877917c336fa5a9ef3ee2e5392f7c60ae81fac27968111b85be71892c61083`；`op010-collect-performance2-identity.transfer.sh`=`ac77d23c80d975059bc475f6d49a9fa8f420e52a3757841f0d8c1877ae7041e5`；`op010-run-d256-role2.transfer.sh`=`6c1d732be6262c3733073ea09973b4263c0e7f0df1f2cfbaff3bb593f5b45597`。均上传至远端 `commands/performance/`，`force=false` 且 SHA 核验，运行产物全部使用 `op010-perf2-<role>`/`op010-d256-warmup5-<role>-01` 唯一名。

预记录远端命令（以 case 根目录为 cwd，任何门禁失败即停）：

```bash
commands/performance/stop-minimax-service-for-microbenchmark.sh op010-perf2-before-baseline-stop
commands/performance/launch-minimax-service-from-stopped.sh op010-perf2-baseline-launch commands/performance/op010-perf2-baseline-service.sh logs/op010-perf2-baseline-131k-server.log
commands/performance/op010-collect-performance2-identity.sh baseline
commands/performance/op010-run-d256-role2.sh baseline
commands/performance/stop-minimax-service-for-microbenchmark.sh op010-perf2-before-candidate-stop
commands/performance/op010-switch-stage-vendor.sh apply op010-perf2-candidate-source
commands/performance/launch-minimax-service-from-stopped.sh op010-perf2-candidate-launch commands/performance/op010-perf2-candidate-service.sh logs/op010-perf2-candidate-131k-server.log
commands/performance/op010-collect-performance2-identity.sh candidate
commands/performance/op010-run-d256-role2.sh candidate
commands/performance/stop-minimax-service-for-microbenchmark.sh op010-perf2-before-revert-stop
commands/performance/op010-switch-stage-vendor.sh revert op010-perf2-revert-source
commands/performance/launch-minimax-service-from-stopped.sh op010-perf2-revert-launch commands/performance/op010-perf2-revert-service.sh logs/op010-perf2-revert-131k-server.log
commands/performance/op010-collect-performance2-identity.sh revert
commands/performance/op010-run-d256-role2.sh revert
python3 commands/performance/compare_performance.py \
  --contract commands/performance/op010-p1k-d256-comparison.json \
  --run-record performance/op010-d256-warmup5-baseline-01/run-record.json \
  --run-record performance/op010-d256-warmup5-candidate-01/run-record.json \
  --run-record performance/op010-d256-warmup5-revert-01/run-record.json \
  --output performance/op010-d256-warmup5-aba-comparison.json
```

第二轮 5+3 A/B/A 全部执行完成，各 run-record 原生 `complete`、errors 空、预热准入 passed。独立服务身份：baseline `bd37abcbf719:8023:1341158:288593584`、candidate `bd37abcbf719:8023:1355142:288691648`、revert `bd37abcbf719:8023:1368844:288789027`。三个 manifest 分别在 `results/op010-perf2-{baseline,candidate,revert}-performance-manifest.json`，SHA256 分别 `271473e2603ab82f6ac00c412e51cf9a2033a7950913e5310b1f37e8d8f7315e`、`8c861d7addd684bc126f6c53e0b06f4523ea70846f08218cc0a4cd3617e6d86d`、`5fb489149d42d347b7ae072a08043211800d9e5a20a46ba47f34c16ccb8e268e`；A/revert FlagGems 联合内容 SHA 相同、B 为唯一变化。

维护版比较器回执 `performance/op010-d256-warmup5-aba-comparison.json` SHA256 `5c222a4bd6ada7c2f242239248fab39d1a69893c65fc2bde0df39d86fb7b0fd4`：**incomplete**，唯一 issue `p1024-d256-c64-n128/baseline/p99_itl_ms: excessive within-process spread`，确认变化路径仅 `/flaggems_sha256`。output tok/s 中位数 A/B/A=465.361/501.598/465.732，候选观察改善 +7.787%，回退漂移 +0.080%；P99 TTFT=20833.749/19488.149/20650.281ms，P99 TPOT=67.747/62.771/67.658ms。B P99 ITL 三轮 281.252/277.247/281.567ms，已稳定；但 A 的三轮 277.983/382.321/281.913ms 出现 37.5% spread，仍超过冻结的 15% 门禁。不能事后删掉 A 异常轮，也不把两个 incomplete 比较改称 passed；op010 按预写停止条件**不晋级**，不启动新 198 题 formal gate，不形成 PR 候选。优化容器现处原 vendor 源码回退状态，最后 A 服务保持健康。

只读长尾分解：第二轮所有 9 个测量轮的单次最大 ITL 均约 775–777ms、且 `>500ms` 事件均恰为 268 次，说明原 workload 本来就包含系统性的 Prefill/Decode 干扰。A 异常 r7 额外 `300–500ms` 事件 85 次，而 A r6/r8 各 29 次，正好多出 56 次；额外事件主要分布在请求索引 32–95 的前 4 个输出 token，A r7 对应的组 1/2 各 28 次，而正常轮这两组为 0。该事件使 P99 ITL 从约 278–282ms 跳至 382ms，但同轮 output throughput 仍落在 A 的正常 463–466 tok/s 带内。结合 `max_num_seqs=32`、C64/N128 finite-batch 和四个 32 请求波次的 TTFT/开始时间，推断这类 P99 抖动与新波次 Prefill/Decode 交错或排队时序有关；仅凭现有客户端明细不能证明唯一服务端根因，不能归咎于 op010 算子。后续应单列 Mixed 尾延迟诊断契约，而非对 op010 事后放宽阈值。

## 候选设计

直接在当前 `SpecOpRegistrar` 已支持的 `_thead/fused` vendor 模块导出同名 `invoke_fused_moe_triton_kernel`。其默认直接转发公共 FlagGems 入口；仅 PPU-ZW810E、BF16、无量化/scale/bias、A/B/C 精确 M32 GEMM2 形状、top_k=1、排序缓冲与 incoming BM16/BN64/BK128/warp4/stage4 匹配时复制 config 并设 BK64。GEMM1、Prefill、其他 Decode M、其他配置、其他平台保持原路径，不改变输出形状/别名/计算次序。此层之所以合适，是 Plugin 当前 `default.flagos` wrapper 在调用时从顶层 `flag_gems` 动态导入该 symbol，而 op-009 修改的 full-call wrapper 根本不执行。实验版一次性 stdout 标记只用于 16 worker 实际命中证明，PR 整理时移除。

先在独立单卡用真实 stage4 config 对公共 invoke 与 T-Head wrapper 做数值和 graph 对照，再启动目标 TP16 131K graph 服务，要求 16/16 worker M32 实际命中、6/6 capture、health、两次 smoke。使用本地精度 Skill 的 `minimal-regression` 模式固定 10 题/C8 护栏；随后本地性能 Skill `targeted` 模式做 P1K/D256/C64/N128 同配置 A/B/A，若无可兑现端到端收益则回退。通过后才进入 D1024 与新 198 题/64 并发/60K/阈值0.88 的正式 gate。旧 gate 绑定退出的 8023 服务，不可继承。

修改前私有 FlagGems revision `3c6f7537d2d5d3aa680c55bbee5c70f2100c5b85`；公共 `fused_moe.py` SHA256 `a780da6348ba611640b546b47c60b79baa1312094386ce8f49d99d0d8e4750af`，`_thead/fused/__init__.py` SHA256 `6a965e61477dde4bdc43e6c6587294a0e28debb9a91f4809eeb93e903c118994`；op-009 新 vendor 文件已删除。保留的 `src/flag_gems/utils/models/sql.py` 修改与 Plugin `thead.yaml` 黑名单不触碰。回退只针对本轮新 vendor 文件及原 `__init__.py`，精确 SHA 检查；`pr_readiness=experimental`。

## 验证矩阵

| 范围 | 预期 | 当前结果 |
|---|---|---|
| PPU-ZW810E M32 GEMM2 精确 stage | 顶层 vendor symbol 命中，BK64，数值/graph 通过 | not_run |
| M1/2/4/8/16、GEMM1、Prefill | 原 config/逐位数值 | not_run |
| 目标 TP16 131K graph | 16 worker 命中、capture、smoke、最小 GPQA | not_run |
| P1K/D256 Mixed A/B/A | 稳态输出吞吐提升且 TTFT/ITL 守护 | not_run |
| 其他平台及其他模型 shape | 原公共入口 | 静态路由待核验；硬件 not_run |

实验补丁 `patches/op010-thead-invoke-m32-bk64.patch` SHA256 `e23d9c38db0d73a10898d28e75ecc92011a1f9ad68b589e7c134fed913752a62`，仅改 T-Head fused 导出并新增 vendor stage wrapper，不改公共 MoE 与 Plugin。应用脚本 `commands/performance/op010-apply-stage-vendor.sh` SHA256 `94101693796813d87612ffc281aa20f3d4d2c8dba79fa87aa3f51a3efb496e5b`；执行前检查原始 SHA、空闲设备/端口、补丁 SHA、备份和 `git apply --check`，执行后 AST/diff 检查。命令：

```bash
/mnt/nfs/users/jinghao/minimaxM3/20260921-minimax-m3-ppu-e2e/commands/performance/op010-apply-stage-vendor.sh
```

补丁应用成功，vendor 导出 SHA256 `fae31da546fd72fb937a9a79033e3dae09ac730446d90eeeb08367da1ace9f9d`，新 wrapper SHA256 `0791a4715ec671e7eb6b55d747e4a5e0ce97e46b83380aea6023cb0333c2fc2d`；新进程顶层 `flag_gems.invoke_fused_moe_triton_kernel` sourcefile 指向 `_thead/fused/fused_moe.py`。下一步直接构造 TP16 实测 M32 GEMM2 stage4 输入，与公共 invoke 对照；M16 fallback 必须逐位一致，M32 必须命中、BF16 allclose/finite、stage 调用 A/B/A ≥5% 且 graph capture+2 replay 通过。此小测不代表完整模型或端到端收益。

`commands/performance/op010-direct-stage-micro.py` SHA256 `27b5539c073901b23ced240e3d1775f36f3a42810247e715d26c8a536e2ab1d1`；执行器 `commands/performance/run-op010-direct-stage-micro.sh` SHA256 `6a044c6a266f79f65bc1cccbd1c610c720cd04aa51a03120a042c877f6ed3b99`。唯一结果 `results/op010-direct-stage-micro.json`、日志 `logs/op010-direct-stage-micro.log`。命令：

```bash
/mnt/nfs/users/jinghao/minimaxM3/20260921-minimax-m3-ppu-e2e/commands/performance/run-op010-direct-stage-micro.sh
```

直接 stage 小测 `results/op010-direct-stage-micro.json` SHA256 `99f04967198987570bb7f08f172737a8bd30e970ccb6ca50c532fb48ddd38ef0`：M16 fallback 逐位一致、无命中；M32 sorted/expert 长度 2048/128，vendor 首次命中 1 次、输出逐位一致；A/B/A stage p50=0.33080/0.20784/0.33098ms，基线-回退中位 0.33089ms，BK64 改善 37.19%；graph capture+2 replay allclose。日志 SHA256 `6e4b62a69086bdd1ccab7160b27f2347d507acaa2ddc02b79a439b56e580fb72`。此为单 stage 且假权重，不等于服务收益。

TP16 候选服务使用 `commands/performance/op010-candidate-131k-service.sh` SHA256 `576adc13c641a63b2f00d3aa0c224305e836912145b7a81baa45beeaa055d106`，其余配置与 op-008 原 131K 诊断服务相同，唯一日志 `logs/op010-candidate-131k-server.log`，transition `op010-candidate-131k`。命令：

```bash
/mnt/nfs/users/jinghao/minimaxM3/20260921-minimax-m3-ppu-e2e/commands/performance/launch-minimax-service-from-stopped.sh \
  op010-candidate-131k \
  /mnt/nfs/users/jinghao/minimaxM3/20260921-minimax-m3-ppu-e2e/commands/performance/op010-candidate-131k-service.sh \
  /mnt/nfs/users/jinghao/minimaxM3/20260921-minimax-m3-ppu-e2e/logs/op010-candidate-131k-server.log
```

目标服务实际 16/16 worker 各出现一次 `op010 THEAD_M32_STAGE2_BK64_HIT`，graph 6/6、health=200、smoke 200；启动日志 `logs/op010-candidate-131k-server.log` SHA256 `5df89864e66626310c895532eebdff80562078945bf899399ad7423a737e4e16`。为把后续精度/性能绑定到具体实例，`commands/performance/build-op010-service-manifest.py` SHA256 `cb3b97a9fc2284eb062c927e28b629923256c780b433699f89a20c32acea3228`，`commands/performance/op010-collect-service-identity.sh` SHA256 `aec386bc22e6c732f25180b45d150bb11ce6c4e023c87838e135e5ff73786fc7`；取当前 PID/start_ticks、model/tokenizer/engine/Plugin/FlagGems 全内容 SHA、launch/graph/blacklist/16-rank hit，并用维护的实时校验器核验。当前候选执行：

```bash
/mnt/nfs/users/jinghao/minimaxM3/20260921-minimax-m3-ppu-e2e/commands/performance/op010-collect-service-identity.sh candidate
```

当前候选 service instance `bd37abcbf719:8023:1297632:288148032`，runtime `results/op010-candidate-runtime.json` SHA256 `1e4b05ca12b41cf23f21dc12ebc4a7e717c4299403bacf73f13bb8c922eae6a5`，manifest `results/op010-candidate-performance-manifest.json` SHA256 `66163556399661bf79f13a0ecc7fca3da11e6e936be76c74842ea130e098f16c`，维护的实时校验器通过。下一步精度 Skill 显式选择 `minimal-regression`，实验仅 op-010、固定 GPQA 10 题、C8、seed42、greedy/max_gen_toks60000、131K 服务；这是最小回归，不签发 0.88 formal gate。配置 `commands/accuracy/minimax-m3-op010-minimal-regression.json` SHA256 `0e05c02407cde2e97b724aaa4cc328769cb61b38a8b60fe1bfa71e9cb4ddadec`；preflight 脚本 SHA256 `a0323ea53ee0092f3d57801e5065d28b493b9e26d7e0150ccf18e7d82122bbfe`，启动脚本 SHA256 `1226b9f3cc1026138ab2f9cd310b7c1b1aeb160e877debc6a9cf272b8127d735`。原始产物仅远端 `accuracy/op010-minimal-regression/`。preflight 不发真实评测，实际启动前须创建本任务 30 分钟只读 heartbeat，终态停用。命令：

```bash
/mnt/nfs/users/jinghao/minimaxM3/20260921-minimax-m3-ppu-e2e/commands/accuracy/op010-preflight-minimal-regression.sh
/mnt/nfs/users/jinghao/minimaxM3/20260921-minimax-m3-ppu-e2e/commands/accuracy/op010-launch-minimal-regression.sh
```

预检通过，`accuracy/op010-minimal-regression/preflight.log` 已写入且未启动 lm-eval。实际评测进程启动前创建了当前任务 heartbeat `minimax-m3-op010-minimal-gpqa-c8-60k`，2026-09-23 20:23 CST 起每 30 分钟只读观察 PPU-07 的精确 evaluator/service 与本目录产物，每次通知，终态停用；心跳不能修改或复制进程。

若最小回归通过，性能 Skill 显式选择 `targeted`，milestone `p1024-d256-c64-n128` 映射正式父目标 `p1024-d1024-c64-n128`，仅输出长度 1024→256；这是 Decode/Mixed 快速证伪，不替代父目标正式场景。计划 `commands/performance/op010-p1k-d256-plan.json` SHA256 `9c5f04cf0b8822d99250192f4f72a1ef9b28ce658168e86a77f655cce60bdd6b`，comparison `commands/performance/op010-p1k-d256-comparison.json` SHA256 `a6b411a6e905566a4077e456cee3ba0778b656a09f5120e6705e28a7e0ced554`，均在看到性能数据前冻结。每个 baseline/candidate/revert 独立实例各 warmup3+measured3，末两预热 output throughput spread≤10% 才准入；正式轮全部保留。主指标 output tok/s 至少 +3%，守护 total throughput 退化≤3%、P99 TTFT≤5%、P99 TPOT≤3%、P99 ITL≤10%；每角色 measured spread≤15%，baseline/revert drift≤10%。同服务配置、同缓存、同客户端，`variable_paths=/flaggems_sha256`，prefix cache off、无 profiler。Prefill 以 TTFT/input-token 代理，Decode 以 TPOT/ITL/output-token 代理，Mixed 以整组有限批次端到端吞吐/尾延迟；代理含调度/网络，不冒充纯设备时间。当前 `prof-002` 只用于阶段归因，不进入收益计算。
