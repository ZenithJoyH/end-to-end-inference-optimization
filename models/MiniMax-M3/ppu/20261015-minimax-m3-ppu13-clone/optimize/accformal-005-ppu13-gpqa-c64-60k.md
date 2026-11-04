# accformal-005 PPU-13 全量 GPQA C64 / 60K

- 最终状态：`passed`；strict-match **183/198=0.9242424242424242（92.42%）≥0.88**。2026-10-15 14:14（北京时间）完成，当前服务绑定gate已签发、复验通过，heartbeat已暂停。
- 用户要求：对已手动启动的当前服务执行并发 64 的全量 GPQA。Skill：`inference-accuracy-evaluation`，显式模式 `formal-gate`；bundle SHA256 `6e94a080dd3b64544c535e1fd4bda506f55516374d14d0f8ca6aa148bba2c7b2`。
- 预冻结：`gpqa_diamond_generative_cot`，198 个唯一 doc_id（0–197），`limit=0`，指标 `exact_match,strict-match`，阈值 0.88；生成 `temperature=1,top_p=0.95,top_k=20,max_gen_toks=60000`，并发 64，lm-eval seed 42，单请求 timeout 14400 秒，API retries 3 / eval retries 1，沿用此前正式契约。
- 目标服务当前位于 PPU-13 / `minimaxM3-latest-20260924` / port 8024 / model `MiniMax-M3`；TP16 BF16，100000 上下文，服务 max-num-seqs 64、batched tokens 8192、`FULL_AND_PIECEWISE` capture sizes 1/2/4/8/16/32/64。用户当前配置启用 prefix caching；本轮只评测这一配置的精度，不迁移旧 PPU-07 gate。
- 启动日志 `/mnt/nfs/users/jinghao/minimaxM3-new/service.log` 原生证明 prefix caching=True、PIECEWISE mixed / FULL decode 两组 graph capture 完成及 16/16 worker 的 op011 启动命中。进程内 PID701，Host PID2271009；实际 service_instance_id 将由本次运行取证生成。
- evaluator：PPU-13 的现有空闲容器 `flageval_llmeval-jinghao`，规定镜像 `harbor.baai.ac.cn/flageval/flageval-llmeval:v1`，image ID `sha256:bcefa10b9be062ed449ac1e7b7925fa4f9a46e1361fbb25cc6e99616bc59a4f5`、host network、同一 `/mnt` 映射。

## 产物与执行计划

沿用用户在本任务指定的共享工作根 `/mnt/nfs/users/jinghao/minimaxM3`，在 PPU-13 核验 realpath/owner/权限/7.5T 空间后，使用唯一新目录 `/mnt/nfs/users/jinghao/minimaxM3/20261015-minimax-m3-ppu13-gpqa-c64` 保存这次跨 Host 精度材料。该目录已检查不存在；不会覆盖 PPU-07 的旧评测目录。此次请求包含执行评测所需的工具、配置、日志、样本与结果写入。

先执行 `mkdir /mnt/nfs/users/jinghao/minimaxM3/20261015-minimax-m3-ppu13-gpqa-c64` 并建立 `commands/`、`tools/`；上传本地 `/private/tmp/minimax-m3-accformal005-20261015/capture-service.py`、`prepare.py` 和维护版 accuracy 工具归档，保留原始 `test/Accuracy_test/llmrun.py` 相对路径并验证其固定 SHA `82cf6e8304cb6f9eb8ca48fe4055f6bbb2054a7b6a90d56de3d6b7a08e90c61e`。随后执行 `python3 <case>/commands/prepare.py`：仅新增本次产物，冻结当前服务/代码/模型文件清单与 tokenizer 指纹、启动日志快照、sanitized evaluator inspect、配置；任何身份或配置漂移即停止。

在 evaluator 中连续两次 `formal_accuracy.py --capture-provenance`（不发模型请求），核对实际注册的精确任务、数据集 split 与 198 题内容相同，再冻结 schema3 contract。随后执行 `--preflight-only`。预检通过后，建立当前任务的 30 分钟 heartbeat，只在有意义的进展、失败、需用户处理或终态时通知，再分离启动唯一 evaluator。原生输出和 progress 保留在本次目录；终态执行样本/结果验证、达到阈值时 issue gate，并暂停 heartbeat。

## 当前结果

准备脚本已执行：当前实例 `97cffbb2cec0:8024:701:475142525`；service manifest SHA256 `63099018a177279799a65fca1d4918444361598fe2f8c9288e813667a8e7d784`，config SHA256 `1d407124bf19ccbe35fc6f3a1912f7337cacf48451a7486dfbf455209b166e68`。工具归档 SHA256 `d61086320d13a133b376f0b517bf0fb124e268ff7ea55e49656d105d80962c0b`；capture/prepare 脚本 SHA256 分别 `83bccf17c8e1071bc05df1f44049c5d9b4a279d03e49702c25982926d67018f3` / `ecd8091cc5088f4ff293afb0b992f3a71b32bdf16c9b045772fefdc8dac35b11`。

两次规定 evaluator 内的 provenance 采集均退出 0，内容完全相同：SHA256 `dd9f6b65e3c92c1321de2aeaff82a3606d623e92e67d982529df3f7220a45b8f`，原始数据集 revision `content-sha256:167548b01bcfd7d38d0eb80bb01bd1e6dded4d3aa14b41a4bdba0beb5423dadc`，198 题 raw/processed 集合均通过工具核验。下一步上传并运行 `commands/freeze-contract.py`（本地 SHA256 `f3aea0967fea58f9bb454b2447e4020bf0a1381de117d5002900a5c42862dd0b`），比较两次 provenance 后以新文件冻结 contract；再调用同一 `formal_accuracy.py` 和 config/contract/service/evaluator inspect 执行 `--preflight-only`。

预备 launcher/finalizer 为 `commands/run-evaluation.py`（本地 SHA256 `28e24640b6aa21ecfc838c0225a410e1b653bbfb6f47a13de453f4038bbee776`，语法检查通过）。执行 `python3 <case>/commands/run-evaluation.py --detach` 前将再次比对当前源代码和 PID/start_ticks，检查 evaluator 无其他评测，以新建 launch lock 拒绝重复；Host 后台进程执行唯一 docker exec 正式 runner，输出 `accuracy/evaluation.log`。结束后复核同一服务/源码、校验 198 个唯一样本/filters，达到 0.88 时调用原生 `acceptance.py issue`，保存 `accuracy/final-result.json`；失败保留原生输出及 finalizer-error，不重启或重复模型服务。

此次服务配置与旧 PPU-07 不同，旧分数/最小回归不能代替本次结果。正式性能仍未执行。

## 正式启动

2026-10-15 12:39:29（北京时间）启动唯一 Host launcher，原始 wrapper/preflight 均通过；12:39:44 原生 lm-eval 日志确认 `Requests remaining: 198`、独立 cache 命中 0、`concurrency: 64`、`max_gen_toks: 60000`。本次原生 UUID 为 `d5effb3c4aaa47e09ffa50d97c02310d`，输出目录 `accuracy/native/minimax-m3-ppu13-accformal005-gpqa-c64-60k/d5effb3c4aaa47e09ffa50d97c02310d/`。原生任务有效 generation kwargs 还包含 task 默认的 `do_sample: False` 和 `until: ['</s>']`，已进入 provenance，不另行改写任务。

launcher 身份保存在 `accuracy/launcher-process.json`，执行命令在 `accuracy/started.json`；评测日志 `accuracy/evaluation.log`，native `progress_score.log`、有效配置、frozen inputs 均位于上述 UUID 目录。后台脚本在终态将保存 `accuracy/final-result.json`，若合法分数达到阈值则生成 `accuracy/accuracy-gate.json`；finalizer 自身错误则保存 `accuracy/finalizer-error.json`。

监控 `minimax-m3-ppu13-accformal005-gpqa-c64` 已创建并 active，30 分钟 cadence，仅在有意义进展、失败、需操作或完成时通知；终态暂停。启动后的现场检查表明唯一 formal wrapper、lm-eval、阶段计分 helper 均正常运行，当前服务 health 200，未发现 finalizer 错误。完成题数以实际 API/cache/sample 证据为准，不能把 context building 的 198/198 当作答题完成；目前不提供 ETA。

12:41 启动检查：服务原生日志显示 `Running: 64 reqs, Waiting: 0 reqs` 且持续输出 generation tokens；launcher、EngineCore、worker 进程仍在，native 阶段计分当时为 `completed=0/198`、timeouts=0（首波请求尚未结束）。未发现请求失败或 finalizer 错误。这只证明本轮请求在执行，不作为性能比较结果。

## Heartbeat 观察：2026-10-15 13:15（北京时间）

本轮已运行约 36 分钟。对同一 SQLite 响应缓存运行原始 `score_progress.py --once` 的只读核验给出 `completed=167/198, matched=167, timeouts=0, strict=158/167 (94.61%)`；这是阶段值，非全量正式分数。读取原生 API 响应日志并按 response id 去重，167 个响应均 `finish_reason=stop`，空输出 0、60000-token 截断 0，最大已完成响应 25320 completion tokens，未发现 evaluator ERROR/Traceback/timeout 日志。

当前服务仍为 PID701/start_ticks475142525，配置未变；Host launcher、wrapper、lm-eval 和原有阶段计分 helper 均在，health 返回200。13:15:39 的服务日志显示 Running18/Waiting13、KV96.4%，持续生成342 token/s（仅运行健康观察，不是性能对比）；没有 stall 证据。答题日志最后更新13:14:05，服务日志13:15:41；尚无 final-result/finalizer-error/gate。尾部问题长度明显不均，不从前160题速率线性推算 ETA。Heartbeat 保持 active。

后续只读一次性阶段计分观察应显式传入 `docker exec -e HF_HUB_OFFLINE=1 -e HF_DATASETS_OFFLINE=1 ... score_progress.py ... --once`。本次新增观察进程首次未带 offline 环境，发生 HF HEAD 联网重试，已仅停止该 `--once` 观察进程并以 offline 方式完成核验；运行中的正式 evaluator 和原有 helper 未受影响，这些联网重试不属于评测请求错误。

## Heartbeat 观察：2026-10-15 13:40（北京时间）

运行约61分钟，原始阶段计分工具 offline 只读核验为 `completed=176/198, matched=176, timeouts=0, strict=167/176 (94.89%)`；比前次增加9题，非最终分数。原生 API 日志中176个不同响应均 `finish_reason=stop`，空输出/60000-token截断均0，最大已完成响应56644 tokens，ERROR/Traceback/timeout日志0。API答题日志最后更新13:39:21，服务日志13:40:24。

Host launcher、正式 wrapper、lm-eval 和原有阶段计分 helper 均在，health200、服务PID701/start_ticks475142525不变。服务日志13:40:19为Running9/Waiting13、KV98.8%，仍持续生成（约194 tokens/s，仅健康观察）；剩余22题存在长输出与排队，未见终态文件或停滞证据。尾部完成间隔差异较大，不给ETA。Heartbeat保持active。

## Heartbeat 观察：2026-10-15 14:10（北京时间）

运行约91分钟，原始阶段计分工具 offline 只读核验为 `completed=196/198, matched=196, timeouts=0, strict=183/196 (93.37%)`，比前次增加20题，尚无全量正式成绩。原生API响应日志中196个不同响应含187个`stop`、9个`length`，9个均达到60000 completion tokens；空输出0、ERROR/Traceback/timeout日志0。此前未出现的60K截断已记录为输出健康观察，不能单独否决未来合法`score>=0.88`的精度结论。

Host launcher、wrapper、lm-eval和原有阶段计分helper均存活；health200、服务PID701/start_ticks475142525不变。14:10:19服务状态Running2/Waiting0、KV22.0%，持续生成约65 tokens/s。答题日志最后更新14:01:06，服务日志14:10:20；末2题仍在生成，不能仅凭9分钟无完整响应判停滞。尚无final-result/finalizer-error/gate，不给ETA；heartbeat保持active。

## 最终结果与绑定复验

2026-10-15 14:14:02（北京时间）原生正式评测退出码0，strict-match **183/198=92.42%**，达到预冻结88%阈值。耗时5673.284068秒（约94分33秒）。样本检查证明198个唯一doc_id、396行（strict-match/flexible-extract各198），strict正确183；同一doc跨filter的原始内容一致。14:40现场重新采集的服务/PID/start_ticks/模型文件清单/tokenizer/engine/三个源码工作树与冻结runtime完全相同，原生`acceptance.py check`复验返回`PASS: formal accuracy acceptance verified`。

正式输出范围为当前PPU-13 `97cffbb2cec0:8024:701:475142525`、TP16/BF16、100K、max-num-seqs64、FULL_AND_PIECEWISE、prefix cache enabled的完整组合；该结果不提供各个优化点的独立贡献，也不代表四场景性能验收通过。若后续改变源码或启动配置（包括关闭prefix cache），不能直接复用此gate；同身份重启按rebind规则核验。

原生API日志198个不同响应为187个stop、11个length，11个达到60000 completion tokens；timeout0、empty0、evaluator ERROR/Traceback0。原生samples中doc_id147包含Unicode替换字符（1题），按两个filter去重后计一次。样本检查器的`truncations=0`来自其仅检查samples顶层字段，而samples没有保留API finish_reason；实际截断数采用API日志的11。输出健康观察不改变合法`score>=threshold`的gate结论。

结果文件（均位于 `/mnt/nfs/users/jinghao/minimaxM3/20261015-minimax-m3-ppu13-gpqa-c64/`）：

- `accuracy/final-result.json`：SHA256 `3a4a15987779e8853acc6d3bba67df0efe5f3089504897133a6518c3e8383377`。
- `accuracy/accuracy-gate.json`：SHA256 `1581ef7f6ea06e53141ef57d69f9d2ffe7b44dff83772626ac9539e3ac53b4f0`，schema3，passed=true，服务manifest SHA `63099018a177279799a65fca1d4918444361598fe2f8c9288e813667a8e7d784`。
- `accuracy/native/minimax-m3-ppu13-accformal005-gpqa-c64-60k/d5effb3c4aaa47e09ffa50d97c02310d/run-record.json`：SHA256 `8a53590173239e232c75d035eda5eeb5f2e3b5bafa0764e2186f2cf58ece424e`。
- 同UUID目录下 `gpqa_diamond_generative_cot/MiniMax-M3/results_2026-10-15T06-13-54.686841.json`：SHA256 `52d3a51adab56b3b22965e08ef028c3f5a7859791e0362ee47eca634c5e3149d`；对应 `samples_gpqa_diamond_generative_cot_2026-10-15T06-13-54.686841.jsonl`：SHA256 `7d490ea0e7da02b0db2bc3fd751393d6f9a4910a460cecd5a5c50aac042ff7de`。

final-result与gate最后更新14:14:03，评测launcher/wrapper/lm-eval/helper均已正常退出，当前模型服务health200、Running0/Waiting0。自动化 `minimax-m3-ppu13-accformal005-gpqa-c64` 已经`automation_update`返回`PAUSED`；无重跑、无服务重启、无源码修改。
