# 组合001：B64 的 splits 与 warps

当前状态：incomplete/reverted；回退对照和终态验真已完成，原OP001 FG保留运行。候选Mixed零测量、比较指标声明缺口均保留，详见文末终态。以下原型数据及过程记录仅为历史。

固定M16/N16，仅B64比较s16W1/s8W1/s16W2/s8W2，另加s16W1回退；B1/B16全部使用原路径。Q12/KV2/D256 BF16页784，KV1K/4K/16K/32K，maxK262144。CPU FP32 oracle atol0.002/rtol0.02，完整API graph2replay/5组×40次计时。

结果前冻结晋级：B64/K1K延迟下降至少15%，B64的4K/16K/32K退化不超过5%，全部数值通过，B1/B16原路径一致。失败即恢复OP001 FG服务并停止本轮离线调参。成功才准备窄guard私有补丁、C8/graph与同契约P1K阶段及Mixed baseline/candidate/revert。正式精度失败与formal门禁不变；micro不是E2E收益。

原始命令、结果与SHA外部保存，见state.yml。

组合实测（B64完整API graph，各5组中位数）：

| KV长度 | OP001 ms | s8/W2 ms | 延迟下降 |
|---|---:|---:|---:|
| 1K | 0.308486 | 0.254349 | 17.55% |
| 4K | 0.931206 | 0.813747 | 12.61% |
| 16K | 3.416576 | 3.058778 | 10.47% |
| 32K | 6.669696 | 6.048128 | 9.32% |

12矩阵×5配置=60项FP32检查通过。两处私有源码改动是支持形状的自动split上限8，以及同形状split8时warps2；其他batch保持原路径，explicit split数量保持原请求（此形状explicit8现在使用W2）。N32不接入。补丁SHA `f302d6b56b44d33c16b5aef9f9564763bcda104cbb2861b89600842731f97a21`，候选FGvllm私有py-tree `f4694df706fa4fde22de111a6b1dfe80c85ef4f06206ce2b1550f01f9d1e39d9`，其余三个仓库SHA不变。原件、回退和安装回执在远程patches/results。

真实源码16矩阵×baseline/candidate/revert=48项FP32/graph检查通过，覆盖KV0/1/783/784/785、1K/4K/16K/32K、变长KV（含空序列）和非连续Q/out head布局；33项fallback与精确原源码相等。结果SHA `797ddbce4f51ee79fbe70724fd1322e43e634d54fec8b53c53791718338509f6`。这些检查不是正式GPQA80% gate。

端到端Skill模式targeted/diagnostic。旧入口基线未绑定新比较契约，不事后补写；新baseline/candidate/revert三实例均按同一冻结契约测量。Prefill P1K/D1/C64/N128、Decode P1K/D512/C64/N64各3warm+3measured；Mixed P1K/D256/C64/N128为6warm+3measured、固定末3窗口<=10%。客户端、采样和计划与diag009相同，保留全部轮。候选使用专属VLLM compile cache防止源码变更复用旧框架图，原FG Triton cache保留；完成graph/预热准入后才计稳态。

比较契约SHA `9ff52da91a1083856309081c53589cc5ca6721d8393ce2c1f196f043d692a16a`，结果前冻结Mixed输出吞吐至少+1%，meanTTFT/meanTPOT/P99ITL退化<=5%，比较指标baseline/revert漂移<=1%，每角色3测量轮、单独进程（诊断级）。Prefill/Decode另作守护。控制器mx-59 PID3424337/create1791881763.23，回执SHA `4273f4ffc3614ecef6032bb4ca7bc705120a01b7ac412483f26e5d3409f08c8e`。基线fg-combo-baseline-01已通过graph/C8，Prefill测量中。控制器最后先保留原FG回退实例，再按证据决定是否临时保留候选。

当前17.55%不是服务提升。新源码完整50000 GPQA待评；正式门禁和四原始场景验收仍未解除。PR准备度experimental，其他平台/模型/硬件未测，不提交或推送。

真实路径修正：fg-combo-01绑定失败，双rank执行的仍是`grid=[16,64,2]`/64threads，未执行候选。管理器日志“block size784”是逻辑页；实际KV tensor为`[2,54880,16,2,256]`，vLLM以16为kernel block并将每个784逻辑块拆为49物理块。原guard784未命中。该原型没有candidate性能轮，不能报模型收益。原controller失败、trace和三项合法baseline保留；原件已精确恢复后按页16重测。

真实页16、49物理页组成一个逻辑块的重测（BF16/GQA6/D256/B64，完整API graph）：

| KV长度 | 原路径 ms | s8/W2 ms | 延迟下降 |
|---|---:|---:|---:|
| 1K | 0.305875 | 0.250304 | 18.17% |
| 4K | 0.928915 | 0.803622 | 13.49% |
| 16K | 3.406592 | 3.006842 | 11.73% |
| 32K | 6.651091 | 5.947104 | 10.58% |

12矩阵×5配置=60项FP32通过，结果SHA `d4f32e560f34ee213930cabc339f51c7164b9c370f24b363393b93ef2b90e338`。修正后支持条件为physical16、B64、packedGQA6、BF16、D256且无CuQ；不扩大到物理页784。真实源码19矩阵×3=57项GPU/graph通过，含物理15/16/17、逻辑783/784/785边界、空/变长/非连续布局；34项fallback通过（含CuQ路径）。夹具首次逻辑页变量漏定义在0GPU测量退出，失败保留，v2仅修正夹具。通过结果SHA `2ef36d44c6b6981bd5fe4eea1b30bc40f83506986b5befbb73895f6c03daed52`。

新FGvllm py-tree `4c3877f2f1bbb91304d5c9ea5f09a943931eed1dc2b1c582f183e36262333627`；其余三仓库不变。修正版patch SHA `ac95bb315d2dcda2d8906231aafccad4cae36512f5a70874ede9930bde9a4c3d`，安装回执SHA `6482330e1c68413c748441611e627aa96514f3942e62b6badd386469b19a8416`；旧原型不覆盖。未改vLLM源码/权重/tokenizer。

续跑controller mx-59 PID3511278/create1791885418.56，回执SHA `eb9619f15f02fb38334f214ca551874e5b97073d97495e0d5742c4673bdeb5ea`，worker SHA `96a689b23e01d0c675fd81131840b05d74ae67e2e5cc1dcd757c98fd160db908`。精确复用已绑定9ff52契约且完整的三项baseline原始记录，不重复测量、不事后补绑，也不改门槛。候选fg-combo-02使用新框架compile cache；必须在双rank观察8splits/128threads再跑C8与三阶段，最后精确回退原OP001。当前仍只有算子收益，正式精度待评。

真实服务fg-combo-02实例`qwen36-fa-opt:145075:1791885420.1`，manifest SHA `01ebe4233bcb9285736676e1edac049521a1b30428f0520bdc95094d84d4e79f`。双rank各48次实际8split/2warp，grid `[8,64,2]`/block `[128,1,1]`、244regs/shared24576，各315 graph launches；C8 10doc/20filter健康回归通过。该门禁不替代正式198题80%分数。

Mixed失败：候选末三预热输出吞吐`712.965/713.023/584.452 token/s`，relative spread18.033%超冻结10%，6warmup全部保留，0measured。Native run-record failed按稳态准入不足解释为incomplete；不得据此报候选Mixed增量或重试删轮。Prefill/Decode各3measured有效，Decode warmup约945对baseline930 token/s，测量增量待逐轮与回退校验，不用warmup充正式结果。controller3511278失败在candidateMixed，源8002未操作。

精确回退与既定对照controller PID3589593/create1791898592.35，回执SHA `310e9df5605ecb96ca60a85eafe31a133aa654ef7a145bf6beffacb1e0940938`，worker SHA `79d231814ec9dc10283e41c45099e65bcaa901cc8c75a897a8a4992337f9dab2`。只停止核验的候选、恢复原两文件、启动原OP001 FG回退并完成同计划三phase；不重复候选，不更改warmup/阈值，最终保留原路径。对照用于判断漂移及定位下一轮Mixed波动，不挽救本次无测量的候选Mixed。新代码完整50000精度/四正式目标仍未验收。

已校验SHA的3轮真实测量中位数（非warmup，回退漂移仍待核验）：Prefill输出5.972304→5.973693tok/s，meanTTFT8367.330→8364.205ms；Decode输出929.525941→945.428376tok/s（+1.7108%），meanTPOT56.220208→55.059597ms（-2.0644%）。该Decode有限单波次仍含初始Prefill/排队残余，不是纯设备阶段。Mixed无测量，不能据此声明整个场景收益或保留候选。原FG回退服务已启动并在C8/对照收尾。

终态收尾（2026-10-13）

本轮为 `incomplete/reverted`，精确回退与既定三阶段对照已完成，保留原 OP001 FlagGems 服务。九份原生记录共36预热轮、24测量轮，全部已完成轮请求/token计数、错误、原始JSON/验证/输入/客户端SHA、种子与命令重验通过。候选 Mixed 六轮预热全部保留、零测量，不能补用预热数字；未重跑候选或放宽门槛。

| 三轮测量中位数 | baseline | candidate | revert | 候选变化 | 回退漂移 |
|---|---:|---:|---:|---:|---:|
| Prefill 输出 tok/s（D1代理） | 5.972304 | 5.973693 | 5.979916 | +0.023% | +0.127% |
| Prefill mean TTFT ms | 8367.330 | 8364.205 | 8355.716 | −0.037% | −0.139% |
| Decode 输出 tok/s | 929.525941 | 945.428376 | 931.594180 | +1.711% | +0.223% |
| Decode mean TPOT ms | 56.220208 | 55.059597 | 56.091589 | −2.064% | −0.229% |
| Decode P99 ITL ms | 50.588242 | 49.179986 | 50.381909 | −2.784% | −0.408% |
| Mixed 输出 tok/s | 706.646134 | incomplete | 705.876865 | 未比较 | −0.109% |

Mixed原路径回退固定末三预热为705.365/706.199/707.641tok/s，散差0.322%，准入通过；三测量轮吞吐散差0.0588%。baseline/revert各比较指标漂移均≤1%；候选Mixed18.033%慢轮未在本次原路径回退复现，仍不能仅据此归因候选数值。候选/回退Decode阶段仍包含初始Prefill、调度和网络残余。完整指标及全部轮次以远端回执为准。

另一独立证据缺口：原生比较器报告 `decision metrics were not frozen as required metrics in the benchmark plan`。比较契约的meanTTFT/meanTPOT未在阶段计划必需指标中声明；上述原JSON经原冻结计划重验后的描述性中位数不等于原生comparison通过。保留原契约/SHA和incomplete回执，不事后补绑或改计划。

终态验证 `results/combo001-terminal-validation.json` SHA `e0dcdfc4341703a614ba1f4e9e0a4f8afcf4c88470e9ae2beec53ad47ea12b48`；原生Mixed比较 SHA `2f9036935be931c44de9150406fb08b74b42ca924091f1f7973341e260deadd9`，均位于既定远端案例目录。当前实例 `qwen36-fa-opt:162168:1791898639.1` /18002/2、3卡，四仓库SHA与原OP001一致，FGvllm `e63fa0c72c65e0064c73265f5e53ca449f9cf55530881b371f82b9f5a740c44b`；FG白名单仍含attention_backend、无黑名单、prefix off、TP2 BF16 graph。graph/C8通过，controller已结束。候选两文件patch和两原件全部保留，不自动重新安装。

源8002/共享源码/vLLM/权重/tokenizer未变更；当前50000正式精度158/198失败及旧30000记录保留，不签gate、不关闭四正式场景，PR experimental。rev005结束有界周期；下一轮需新冻结的完整比较指标及Mixed归因证据，当前不追加模型请求或性能。知识差量：逻辑784≠物理16，真实命中是门禁，N32 spill负优化、N16W2去spill，组合微测收益不能代替Mixed。
