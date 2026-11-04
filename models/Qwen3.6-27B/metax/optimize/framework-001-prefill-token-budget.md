# Framework001：Prefill token 预算

当前状态 incomplete/reverted，既定对照已结束；当前目标 P1K；继承原OP001 FG源码，继续既有独立优化容器/案例。用户要求当前模型端到端优化，本轮沿用诊断性授权，仅一个配置变量8192→4096，不修改源码或正式精度契约。

三阶段trace说明Prefill/Mixed主要成本在GEMM、通信与Prefill阻塞；每批8条新prompt的GPU范围约1.34s。假设较小预算降低长Prefill干扰，但更多迭代/较小GEMM可能降低吞吐。Decode/GDN/FA仍需守护，收益待测。

同配置baseline/candidate/revert：Prefill P1K/D1/C64/N128、Decode P1K/D512/C64/N64，3warm+3measured、末2输出吞吐散差≤10%；Mixed P1K/D256/C64/N128，6warm+3measured、固定末3≤10%。每轮600s，所有测量轮保留，比较指标测量散差≤10%、baseline/revert漂移≤1%。相对正式P1K/D1K缩短输出，Decode仅一波64请求，含初始Prefill/调度残余；不能替代正式场景。

测量前逐项冻结phase计划required_metrics与各phase比较契约，修复上轮配置缺口，旧结果不补绑。主晋级条件为Mixed输出吞吐≥3%改善，Prefill/Decode吞吐及各延迟守护退化≤5%；sentinel主指标不独立要求改善，但其原生验证/漂移/波动及守护必须有效。候选失败即精确回退8192，不删除慢轮、增加预热或重评候选。所有角色prefixoff、TP2 BF16、graph64、FG attention开启，采样/客户端/设备与当前源相等。

候选及回退需实际graph两rank命中/两次replay和固定10题C8健康回归。当前50000正式GPQA158/198<80仍阻塞正式性能；本轮无gate签发、四场景完成或PR结论。最终先留原8192，之后按证据判断配置是否可晋级，不能自动部署源8002。

原始计划、命令、结果、进程回执与SHA均在既定远端case/commands、manifests、results/fw001-E2E和logs/fw001-*。state.yml索引为主记录。

控制器v1初始化失败：嵌套代码的NUL转义进入subprocess argv，0请求/0服务或源码变更。失败回执及日志保留；v2仅改源码校验序列化为bytes([0])并使用新进程/日志/进度路径，计划/门槛/角色未改。AST字符串与源码编译预检已补充。

实时基线checkpoint：原生check_run重验Prefill通过，三测量轮中位输出5.981416tok/s（D1代理）、meanTTFT8353.339ms。原始记录/SHA已写state.yml，当前Decode运行；候选/回退未完成，没有新的增量或保留结论。

用户追加硬约束：本轮端到端优化不得通过关闭FlagGems算子取得收益，可优化FlagGems实现。当前基线和候选/回退脚本均保持16项ATen及attention_backend注册集合、FGattention=1、无blacklist；8192→4096只改变批处理预算。后续候选需保留相同已开启集合并证明目标FG路径命中，历史attention黑名单实验不用于本轮优化晋级。

2026-10-13 22:56北京时间checkpoint：候选4096实例190468/create1791902509.78已通过双rankgraph（至少190replay）和C8，17项白名单完整、FGattention1、无blacklist、四仓库SHA与基线相同。原生check_run重验五项完成阶段记录通过。Prefill三测量轮输出5.981416→5.722659tok/s（−4.326%），meanTTFT8353.339→8558.106ms（+2.451%）；Decode输出931.768815→909.231550tok/s（−2.419%），meanTPOT56.069247→57.324706ms（+2.239%），P99ITL50.415352→743.560366ms（+1374.869%），超冻结5%守护。Mixed尚无完成轮、回退漂移待核验，继续唯一控制器既定对照，不追加请求/调门槛/提前宣称保留。时延退化不等于数值根因。

终态（2026-10-13 23:34 北京时间）：`incomplete/reverted`。九份原生记录已重验；当前原8192服务及四仓库SHA相等，完整16项ATen及attention_backend保持开启，FGattention=1、无blacklist。无模型请求/服务修改的终态校验回执已保存。

| 阶段 / 指标 | baseline | candidate4096 | revert8192 | 候选变化 | 回退漂移 |
|---|---:|---:|---:|---:|---:|
| prefill / output_throughput tok/s | 5.981416 | 5.722659 | 5.971807 | -4.326% | -0.161% |
| prefill / mean_ttft_ms ms | 8353.338965 | 8558.106087 | 8367.444870 | +2.451% | +0.169% |
| decode / output_throughput tok/s | 931.768815 | 909.231550 | 933.245831 | -2.419% | +0.159% |
| decode / mean_ttft_ms ms | 6386.535265 | 6477.109067 | 6383.696202 | +1.418% | -0.044% |
| decode / mean_tpot_ms ms | 56.069247 | 57.324706 | 55.975217 | +2.239% | -0.168% |
| decode / p99_itl_ms ms | 50.415352 | 743.560366 | 50.576085 | +1374.869% | +0.319% |
| mixed / output_throughput tok/s | 708.317032 | 675.800543 | 710.938702 | -4.591% | +0.370% |
| mixed / mean_ttft_ms ms | 5352.699465 | 4431.693368 | 5419.304623 | -17.206% | +1.244% |
| mixed / mean_tpot_ms ms | 69.307164 | 77.151470 | 68.865832 | +11.318% | -0.637% |
| mixed / p99_itl_ms ms | 1384.395263 | 787.956470 | 1384.793538 | -43.083% | +0.029% |

Mixed比较为incomplete：meanTTFT baseline/revert漂移1.244%超过预冻结1%。回退Mixed末三预热输出707.627/643.066/709.245tok/s，散差9.352%低于10%准入门槛，全部慢轮保留；三测量轮TTFT散差1.520%，未超10%，但不能解除跨实例漂移限制。九记录共36warmup/27measured，原生check_run重验全部通过。以下百分比仅描述已有轮中位数，Mixed不能作通过的性能结论。

各阶段 native comparison 状态：prefill=failed, decode=failed, mixed=incomplete。详细 issues、每角色warmup窗口、全部测量轮散差及原始SHA保存在state.yml和远端回执。sentinel主指标不要求独立改善的原规则不变，所有守护/波动/漂移仍按冻结契约判定；没有删轮或调门槛。

4096候选在Mixed缩短TTFT，输出吞吐与TPOT仍退化；Decode P99ITL超5%守护，候选不晋级。客户端指标包含排队/调度/网络与初始Prefill残余。不能将时延变化归因数值问题，数值根因unknown；这一批有限请求不能外推长期容量或四场景结论。

终态回执 `/public-flash/jinghao/qwen3.6-27B/optimize/flash_attention/20261012-qwen36-27b-metax-flash-attention/results/fw001-terminal-validation.json`，SHA `58fc818fc1c5f2c057561b5dfff521c7287a09b3abffa3eed96ca92ca9b8ecea`。原8192精确实例 `qwen36-fa-opt:212498:1791904066.54` 保留运行，18002/2、3卡，FGvllm e63fa0c。源8002/共享代码/vLLM/权重/tokenizer未修改。v1控制初始化失败证据保留；v2与全部角色结果保留，未重复候选或追加GPQA/性能。

正式50000 GPQA158/198<80及旧30000记录不改，不签gate、不关闭正式场景。rev007归档负结果，下一次先基于实际命中的FlagGems热点选择单个实现优化；本周期到此结束，监控PAUSED。
