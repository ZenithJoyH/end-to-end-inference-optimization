# 20260924-p32k-align-direct-38 MoE align 直接接入 FlagGems-vllm

- 状态：Plugin 路由已接入、正式精度通过、性能未重新晋级；分类：`operator/replace`；父场景：`p32768-d1024-c64-n128`；阶段：Decode、Mixed。
- 用户指令：把 Plugin 中的 MoE align 调用接到 FlagGems-vllm 算子，修改后执行全量大 GPQA 精度测试。

## 优化方向与瓶颈依据

改动前 Plugin `default.flagos` 的 align adapter 调用 `flag_gems.moe_align_block_size_triton`，绕开 FlagGems-vllm 中已保留的 padded stage2。点36的窄路由候选已在真实无 EP Decode 形状通过数值、graph replay 和 16/16 rank 命中验证；但同配置 P32K/D128 Mixed 吞吐仅提升 0.0822%，未过原性能 +3% 门槛。本次按用户要求重新接入并做高风险 MoE backend 的正式精度验证，不把旧单算子数据作为新的端到端收益。

## 优化内容与适用边界

仅修改优化容器私有 Plugin 副本的 FlagGems backend adapter，目标文件原 SHA-256 `a923d10ac1899ea76ee9ff7871383d05e71e758cd076aadc421e75ef17f483ba`。已复用点36经验证的候选，现行 SHA-256 `2cc46caf18d9a8e549fba48a167a2e33764d184d7e17c2d7483a5bf89c4afeec`：PPU、int32 contiguous、topk8、E288、已测 EP 或无 EP 小 M/BM 形状调用 `flaggems_vllm.ops.moe_align_block_size_no_tle(..., use_padded_stage2_vec=True)`；其他形状、平台与 `pad_sorted_ids` 保持 FlagGems fallback。可选依赖延迟导入；已选择候选后的错误不静默回退。

## 正确性与路径命中

后续当前身份更新（2026-10-18）：用户重启服务后要求64并发全量GPQA，新结果为169/198（0.853535），低于0.86；详情见[本次评测及诊断](acc-20261018-gpqa-c64.md)。该轮原生样本/分数与服务身份有效，10题记录60K长度结束；尚未证明与本点MoE align有关。下面的173/198仍只代表2026-09-24的32并发历史实例，不能作为当前服务gate。

同日补充：按用户授权统一重跑上述10题后，4题新增正确，合并分数为173/198（87.37%），达到86%门槛；当前补充汇总与2026-09-24历史173/198是两个独立来源。补跑仅10个请求、实际最大并发10，保持原生成参数；原始64并发全量结果保留，未签发新的一次全量gate。

已核对目标仓库状态和私有导入路径，完成数值/边界/fallback、graph capture 与两次 replay、C1/C8，并在当前服务身份下完成 `formal-gate`。正式 task `gpqa_diamond_generative_cot`，198 题，`strict_accuracy >= 0.86`；超时/截断只作诊断记录。正式结果与新服务、源码内容、权重/tokenizer、graph 与启动参数绑定，未复用历史 gate。

开始实际回归前已创建每 30 分钟一次的当前任务 heartbeat `glm-align38-accuracy-progress`；终态后停用。最小算子/adapter 回归命令已保存至远程本次目录 `run-minimal.sh`，SHA-256 `0ac0c15f8dcee1428a62101c59f5e4741d6291f5f6c0e3f19c8f1978bb4d455e`。

离线 adapter 最小回归通过：目标候选 73 次、fallback 9 次，包含 16 种 EP map、7 个真实无 EP Decode 形状、边界和 padded fallback；目标路径 graph capture 与至少两次 replay 均通过。原生结果 SHA-256 `72eeca02fb9f2d5b2cbd635f48ed0d3429f4f477ec9aa438c136875a99f68087`，路径为本次远程目录 `adapter-minimal.json`。

当前 TP16 服务已启动，graph capture 完成且 `/v1/models` 正常；C1 为 1/1、C8 为 8/8。两份响应原件 SHA-256 分别为 `bdd50a123dabc9b182c29f8fe035442c1ffd15557a795c3644ee765068c9b1ac` 和 `81d80b6f80a3ad9fddd2c75661f7a52e06abb0dae31e9e22cf1eb2950cd3ac6f`，位于本次远程目录 `sanity/`。原生服务指标中 prefix cache query/hit 均为 0。

首次正式预检未发送评测请求，因旧 manifest 生成器虽写入 FlagGems-vllm 内容 SHA，却缺少新版工具要求的 `flaggems_vllm_installed` 实测布尔字段而失败；原生错误保存在 `preflight.log`。优化容器当前可导入路径已核验为 `/workspace/e2e-opt/glm53-20260911/FlagGems-vllm/src/flaggems_vllm/__init__.py`。新 `build-manifest-v2.py`（SHA-256 `3d78d5d7eceb99fe2b86912ef24144e420967058250f990f9ab532b7b8ab5f30`）将该字段标记为 `true`；`capture-service-v2.sh`（SHA-256 `a099fc5ff7c04386082996970d7cdba1d69229b8ae7d624e8c4960d569d3a1e4`）使用新文件名重采，保留首次失败记录。

v2 manifest SHA-256 `3cd23e1ff239e5f4a2b5302091edf74f8120c0e6f98d27f74ff54c47b282b825`、runtime 证据 SHA-256 `a94d72822e6a10288fbc378b669899d07b6981288cbf04cc9136f0d0704e2452`。新预检/全量命令 `run-formal-v2.sh` SHA-256 `d45a190dfa7490f7a4f38c8a7405ce43ee1f45af0016bd2739434fde68ecbf38`，容器内 `formal-inside-v2.sh` SHA-256 `caa93a024c831fc1c403791b43a921fb4f9ac420d8a06fa343ae8f80d4411b90`；旧失败产物不覆盖。

`run-formal-v2.sh preflight` 已通过，原生 `preflight-v2.log` 明确写入 `Preflight passed; no evaluation was started`。之后才启动正式全量答题，阈值与配置保持冻结。

正式全量评测于 2026-09-24 17:27:48 +08:00 启动，运行日志为本次远程目录 `formal-v2.log`，终态退出码写入 `formal-v2.exit`。运行中分数未用于结论。

198/198 请求完成，正式进程退出码 0；原生 `run-record.json` 位于本次远程目录 `results/GLM-5.3-Flash-BF16-align38-c32-60k/68c6cef5b39f46ebba0bcf0f96b1e31e/`，SHA-256 `8a22a342c7a14a9a06213affce531e3f230a20fc0e510136c0fd6d5d0ae93c20`。它绑定结果文件 SHA-256 `eb367704f79cc66ac1e07ccc8276aad2361a477929da1aa955eff083da072771` 与 samples SHA-256 `3ccbed65b889a12e53692e430dc4a34d34738607587abd80e097e9b8dbe9ff0e`。签发命令 `issue-gate.sh` SHA-256 `a52359e6d25ad8360c9b30961fe3aaefa42022186975736b89d8b52b74fa3737` 已存本次远程目录。

正式 gate 已签发 `passed=true`，strict 分数 **0.8737373737373737（173/198）**，高于预冻结门槛 **0.86**。gate SHA-256 `649549d443f70240ab19a900d5531c8a853423952649a3f48e9f4f76db1a2e49`，路径为本次远程目录 `accuracy-gate.json`；服务 SHA 绑定 v2 manifest `3cd23e1ff239e5f4a2b5302091edf74f8120c0e6f98d27f74ff54c47b282b825`。评测后复核 API PID 仍为 `1946308`、Plugin 文件 SHA 仍为 `2cc46caf18d9a8e549fba48a167a2e33764d184d7e17c2d7483a5bf89c4afeec`。历史 172/198 与本次相差 1 题，但生成采样存在随机性，不能把差额归因于 MoE align 改动。

正式 gate 另经 `acceptance.py check` 只读复核，结果 `PASS: formal accuracy acceptance verified`。

全量评测进度 heartbeat `glm-align38-accuracy-progress` 每 30 分钟检查一次；正式 gate 完成后已暂停，未留下活跃监控。

## 性能效果

本次请求尚不包含新的端到端性能测量。历史点36同一候选在 P32K/D128 的 A/B/R 为 36.177648→36.207369→36.199152 tok/s，候选仅 +0.0822%，未达到 +3%；该数字不是新代码/新服务的性能结论。

## 决定、风险与回退

按用户要求保留当前优化容器中的 Plugin 路由，正式精度已通过；这仅证明正确性门槛，不代表该优化点已达到端到端性能门槛。点36同一候选在 D128 的 +0.0822% 仍低于 +3%，本轮没有新性能 A/B/R，更未覆盖正式 D1024。`pr_readiness=experimental`；本次未提交/推送代码。回退只在停服后对优化容器内 Plugin 文件执行精确 SHA 切换，不触碰源适配容器、权重或其他服务。

## 外部证据

- 远程任务目录：`/mnt/nfs/users/jinghao/glm5.3-flash/optimize/e2e-opt-20260911/align-direct-gpqa-38-20260924/`。
- 已保存的切换/回退命令：该目录 `switch-source.sh`，SHA-256 `1847a2eace71c77cdb64e003f65d621436112b335d3f2b5aff44c62e344037de`；仅在目标优化容器停服且原件 SHA 匹配时可执行。容器当前只有 `/mnt` bind mount，目标 `/workspace/e2e-opt/...` 是私有副本。
- 服务启动命令已保存为该目录 `launch.sh`（SHA-256 `3afa1bf09d29a717dead02cfcb9356e833cfa39ffb23793b09c3aa3cf6136a2e`）和 `launch-inside.sh`（SHA-256 `8858c1cdfb4ef2bd6c75886247383dd29f02eb9534917e16cf0cea3defedd60d`）；沿用 TP16、BF16、MBT32768、maxseq64、FULL_DECODE_ONLY、前缀缓存关闭。
- C1/C8 命令为该目录 `run-sanity.sh`，SHA-256 `17cd1554db726f3df0a7d6e33696f667889685f60e65fa9738dd630560e2c435`。正式配置 `accuracy-config.json` SHA-256 `66661f7efb97aacb21665b42bba90165c450662c52a143c403722b1dd3fc97d6`，冻结 198 题、并发 32、最大输出 60K、seed 42、阈值 0.86。评测工具复制在该目录 `workspace/`，原始 runner SHA-256 `82cf6e8304cb6f9eb8ca48fe4055f6bbb2054a7b6a90d56de3d6b7a08e90c61e`。
- 服务身份采集命令 `capture-service.sh` SHA-256 `65ea219c6da26e14c2872821fcad6d28aa5e618fa55c0082bb95c59ef0d96bc9`；manifest 构建器 SHA-256 `92cba2eac8f343a70f0bae5828cae1cb28d0a28f20d75af0ff780544e1021b71`。前者仅采当前优化容器与实例，后者将 endpoint 绑定到正式 GPQA 的 `/v1/chat/completions`。
- 新服务实例 `PPU-13:glm5.3-flash-opt-20260911:1946308:295638122`；manifest SHA-256 `c23b4ecc68934e36f67eadc1177ee9b92d67013d59667282d10c828de12b9c71`，runtime 证据 SHA-256 `72db31de18b3293bc8f43682cc82570a0d403a37eab0a9ebfae0c22c8df15a26`，两者位于本次远程目录 `service/`。评测准备命令 `prepare-formal.sh` SHA-256 `869e93a9fea1cce48ef919fab0161432fed23cf5389ea3727873a0c64cdfb934`，会采当前 evaluator inspect 和数据/任务 provenance。
- 正式评测数据内容版本 `content-sha256:167548b01bcfd7d38d0eb80bb01bd1e6dded4d3aa14b41a4bdba0beb5423dadc`；本次 provenance SHA-256 `8c7ec0f28b497e53a394800328a7805ac32a440d257bef1a55fb488383626e78`，evaluator inspect SHA-256 `4350deebd940374836a18150a3bed89377fddb617e4f831a419db8f48c4f99e3`。schema3 契约 `accuracy-contract.json` SHA-256 `a80dfd4a0df88fc43b2038ddf815c22005b3763e238aa4e6012e0e51a034e392`。执行命令 `run-formal.sh` SHA-256 `bc4de2d3436287150d3347e19568429ee90b9f1c734e98e2e2bd1689cc2383e7`，容器内命令 `formal-inside.sh` SHA-256 `92adadfc5f1b384d5b8d9601b3419e7560b791528404db8f1818a4119aaf34ff`。
- 点36源码候选及回归原件：`/mnt/nfs/users/jinghao/glm5.3-flash/optimize/e2e-opt-20260911/commands/p32k-align-dispatch-36-20260923/`。
