# accformal-006 PPU-13 当前无黑名单服务全量 GPQA / C64 / 60K

状态：passed。2026-10-17 17:56:54 +08:00正式启动，19:27:08结束，耗时5413.94秒（90分14秒）。strict-match为179/198=90.4040%≥88%，198唯一题目校验通过，gate签发及独立check通过。用户明确要求当前服务、64并发、max new tokens60000、精度阈值88分。

## 冻结范围

formal-gate，覆盖fw-014路由dtype/边界与worker时机修正、fw-015移出新增测试/撤销thead.yaml差异、fw-016原参数重启后的当前组合。PPU-13容器`minimaxM3`，绑定实例 `fad201d7b6ec:8024:30544:494374945`，endpoint `http://127.0.0.1:8024/v1/chat/completions`。不修改源码、thead.yaml、采样语义或模型服务，不重启。TP16 BF16，100000上下文、max_num_seqs64、8192批token、prefix关闭，FULL_AND_PIECEWISE sizes1/2/4/8/16/32/64。当前已完成16rank双模式capture、FULL180次及C1/C8 10/10；正式评测仍另立新证据，不继承旧分数。

精确task `gpqa_diamond_generative_cot`，limit0、198个唯一doc_id，metric `exact_match,strict-match`、阈值0.88，判定仅score≥0.88；并发64、lm-eval seed42、temperature1/top_p0.95/top_k20/max_gen_toks60000。原始正式runner SHA256 `82cf6e8304cb6f9eb8ca48fe4055f6bbb2054a7b6a90d56de3d6b7a08e90c61e`，通过本项目formal_accuracy.py包装，不用替代runner或旧响应缓存。请求timeout14400秒，API重试3次，原runner任务重试1次；逐请求60K截断等单独观察，不另加精度门槛。

## 环境与证据准备

评测容器`flageval_llmeval-jinghao`（2454b5b6e523），规定`flageval-llmeval:v1` image ID `sha256:bcefa10b9be062ed449ac1e7b7925fa4f9a46e1361fbb25cc6e99616bc59a4f5`，host网络、原有/mnt挂载；只使用当前任务独立目录。任务/数据provenance重新采集两次，核对后冻结契约、做服务preflight，再创建后台launcher与heartbeat。评测文件与native结果保存：`/mnt/nfs/users/jinghao/minimaxM3/20261017-minimax-m3-ppu13-plugin-support/accuracy/accformal-006-gpqa-c64-60k-threshold88`。

用户明确指定已运行的当前服务做正式精度，不是新一轮性能优化；不创建新模型容器。该范围例外与之前原位Plugin替换一致。对目标容器身份、镜像与本案例baseline inspect做当前连续性复核，并对两时点规范化挂载做机器diff；manifest中的verified/passed仅指这个明确的same-container baseline→formal检查，不伪称新容器clone已验证。原baseline的not-applicable历史字段不改写。模型身份方法为非权重文件内容hash及权重路径/大小/mtime清单，不宣称完整权重逐字节hash。

## 跟进与终态

终态已完成，heartbeat已PAUSED；本节原先约定的执行边界与下方历史观测保留，不表示仍在评测。当前完整结果与输出健康差异见文末。

本轮按本地inference-accuracy-evaluation/formal-gate，bundle SHA256 `6e94a080dd3b64544c535e1fd4bda506f55516374d14d0f8ca6aa148bba2c7b2`。长评测采用当前任务heartbeat约30分钟检查，仅在有意义进展、异常、需处理或完成时通知；按native唯一题目证据报进度，不用filter行数或token吞吐推算完成数。监控不改、重启或重复评测/服务。

结束后检查native分数、198唯一题目、多filter一致性和服务/源码未漂移，符合契约时签发gate；阈值失败或证据无效时调用精度定位技能分类并保留现场，不自动改代码或再跑一轮。终态报告路径、更新当前实验和汇总，并暂停heartbeat。正式性能不在本轮范围。

## 启动回执

两次任务/数据provenance字节一致，dataset revision `content-sha256:167548b01bcfd7d38d0eb80bb01bd1e6dded4d3aa14b41a4bdba0beb5423dadc`，198题，filters为strict-match/flexible-extract（正式指标仍为strict-match）。预检通过。唯一后台launcher host PID3596311/start_ticks494682378，记录在`accuracy/launcher-process.json`；实际CLI确认`--seed 42`、num_concurrent64及max_gen_toks60000。原生日志`Cached requests: 0, Requests remaining: 198`，run UUID `6fb31ec6a1984d0eb23d672be5b44664`。初始观测health200、服务running64/waiting0，已收到首批响应；不把构造contexts的198/198当作完成题数。

Heartbeat：`minimax-m3-ppu13-accformal006-gpqa-c64-60k`，ACTIVE、30分钟，绑定当前任务，只通知有意义变化/异常/完成；旧accformal005 heartbeat保持PAUSED。终态文件为`accuracy/final-result.json`或`accuracy/finalizer-error.json`；成功gate为`accuracy/accuracy-gate.json`，native路径与score在终态回执中列出。

冻结SHA256：service manifest `c9503cb4bb1a76e7efacc79af18e5349bf65873e04e4a0deaf2e7534d2886759`；config `9f6d56e8d62c513a219cfc7daed7a83d68e7cacf924fcb4813f55c2c19ea834a`；contract `180a9449abe65d6fe2c00eb475e8e1634e0196c15f814c7b9706f14ef7672204`；provenance `dd9f6b65e3c92c1321de2aeaff82a3606d623e92e67d982529df3f7220a45b8f`；launcher脚本 `24d1edc168a09dac286a043cc22c97e6acf9c39f46c3cddc110f9dea27451871`。工具源与原runner均保存于本run的tools目录。

正式manifest使用全部Git列出文件内容hash，和minimal阶段“只选代码/配置文件”的hash算法不同；数值不同不能解释为代码变化。本次另做`runtime/source-continuity-check.json`与restart-001完整选中文件表逐项复核，三个源码树与实际vLLM全部相同，SHA256 `e7f7331504c7ace534c3eb8e9c2ece0a787acaac346f9d822ba3e02ed84d3bfb`；不改写旧回执或旧SHA。

## 2026-10-17 18:29 +08:00 监控

仍在生成阶段，启动后约32分09秒。18:29:03只读检查原生`Requesting API (concurrent)`为169/198请求返回（85%）；这不是已校验的唯一题目完成数，尚无native结果/样本、final-result、finalizer-error或accuracy-gate。评测日志最后更新18:28:17，较启动轮52/198有明确进展，不判定停滞，不给剩余时间估计。

18:27检查launcher PID3596311/start_ticks494682378仍匹配，评测进程存活；模型PID30544/start_ticks494374945匹配，health200，运行29/排队0。18:29扫描当前评测日志未发现ERROR/Traceback/超时/连接异常、finish_reason=length或completion_tokens=60000；服务日志末512KiB未见ERROR/Traceback/EngineDeadError/OOM。尚无最终分数及完整样本级输出健康结论。未改动、重启或重复启动评测/服务，heartbeat继续ACTIVE。

## 2026-10-17 18:57 +08:00 监控

18:57:13观察启动后3619秒，仍在生成；原生请求进度181/198（91%），比上轮169增加12个返回请求，不替代唯一题目校验。launcher PID及start_ticks匹配，评测进程存活；模型实例不变、health200，服务运行11/排队5。评测日志最后更新18:53:07，尚无native结果/样本与终态文件，不能报最终分数或签发gate。当前日志未见ERROR/Traceback/超时/连接异常、length结束或60000 completion tokens；服务日志末512KiB未见ERROR/Traceback/EngineDeadError/OOM。空输出等完整样本健康结论待原生样本落盘后核验。尾部请求仍有进展，无充分证据判定停滞或估算ETA；继续原heartbeat，不改动服务或评测。

## 终态：2026-10-17 19:27 +08:00

正式strict-match为0.9040404040404041（179/198），高于冻结阈值0.88。原生样本包含strict-match与flexible-extract各198行，唯一doc_id为198；不把396行当作396题。辅助flexible-extract为0.6363636363636364，不替换正式strict-match指标。evaluator退出0，finalizer确认服务与源码未变化，gate issue退出0；另行只读执行acceptance.py check退出0、`PASS: formal accuracy acceptance verified`。当前实例仍匹配，health200、running/waiting均0，评测进程已自然退出，无finalizer-error。日志最后更新19:27:08，终态回执19:27:09落盘。

输出健康：完整解析198条API响应、198个唯一response id、无解析失败或空content；184条stop、14条length，后14条达到60000 completion tokens。native样本摘要timeouts/empty/garbled均0，但其truncations=0不能解释为无截断：当前sample_validation.py只识别样本顶层finish_reason/truncated，不检查API usage；本轮截断事实以原生API日志14条为准。未改写原回执、未修改校验器、未自动补跑。该观察不改变冻结的score≥threshold判定。

远端根目录仍为上文run目录，关键终态路径：

- `accuracy/final-result.json`，SHA256 `5333da3c62d97a5ab6e11436f65081d02dacd7b7f4939da09242e58fbddb5cb6`。
- `accuracy/accuracy-gate.json`，SHA256 `7a59b0cb5a68f91ea88af39c6b699bbff262df8e5b013dd206b6d17465c16048`。
- `accuracy/sample-validation.json`，SHA256 `d926efedd21d1c2423f835b6cfe40755b26c6102100a6c2723b87538743d6b7c`。
- `runtime/service-posteval.json`，SHA256 `0f9650e5514ccd72501fa6f95bc554b84098c04a13fbf687aca171121159e6f0`。
- `accuracy/native/minimax-m3-ppu13-accformal006-gpqa-c64-60k-support-refine001/6fb31ec6a1984d0eb23d672be5b44664/run-record.json`，SHA256 `c7cd8497be7ace6b34eca3c0caa04be0a0e7a2d7ddd262b9b82aaa66da0bf8e1`。
- 同一native run下`gpqa_diamond_generative_cot/MiniMax-M3/results_2026-10-17T11-27-01.970876.json`及`samples_gpqa_diamond_generative_cot_2026-10-17T11-27-01.970876.jsonl`。

决定：当前fw014+fw015+fw016组合的文本GPQA精度通过，仅绑定本次相同服务/源码/配置；不证明各点独立贡献，不与旧不同容器的92.42%作因果比较。性能、真实多模态、PIECEWISE请求replay及100K边界仍未验收。按用户范围不自动发起性能实验或诊断修复。heartbeat `minimax-m3-ppu13-accformal006-gpqa-c64-60k`已通过产品工具暂停；模型服务保持运行，原回退方式不变。
