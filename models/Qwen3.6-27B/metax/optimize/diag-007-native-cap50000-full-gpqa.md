# diag-007-native-cap50000-full-gpqa

状态：completed-failed；模式：formal-gate。用户2026-10-13明确要求max gen token50000、完整精度一次，直接授权新正式输出预算契约；不改题、不改阈值。

## 配置与范围

当前原生MetaX attention_backend黑名单服务保持，实例qwen36-fa-opt:82515:1791815908.86，独立容器qwen36-27b-fa-opt-20261012/2、3卡18002。原修正版GPQA198/gold/strict80%、C32/temperature1/top_p.95/top_k20、harnessseed42/APIseed1234、Thinking/prefixoff/graph/TP2 BF16都不变。唯一生成变量max_gen_toks30000→50000；当前源码四仓库内容SHA及22个权重/tokenizer文件复验相等。

两次实际provenance相同，原始和处理后198题及helper来源与旧契约相等，仅generation配置差异，新config/provenance/contract独立保存。参考旧原生30000为160/198＝80.8081%；FlagGems30000为159/198＝80.3030%，两个旧分数/gate保持。本轮158/198＝79.79798%，低于80%，未签发新gate；历史gate不替代新预算失败结果。

## 精确进程与监控

评测容器qwen36-fa-gpqa-fixed-20261012，PID2184/create1791857595.66，启动2026-10-13 02:13:16 UTC（北京时间10:13:16）；run UUID4869e32f008c42d0b233214fa5a03ea9。原生日志确认max_gen_toks50000、cached0/remaining198、C32；preflight passed，启动前运行和排队请求均0。198请求耗时1:10:13，正式结果于2026-10-13 03:23:49 UTC生成（北京时间11:23:49）。

之前diag006的81920长预算诊断已精确SIGTERM客户端PID1556，服务未停未重启；两条已完成30000响应均length/invalid，长预算两条未完成，保留所有partial/取消回执，不宣称81920成功。监控qwen36-metax-flash-attention-op001重新绑定本完整正式进程，已于终态验真后PAUSED；服务保持，不重评。

## 终态核验与比较

保存的diag007-finalize-terminal.py仅核验已生成results/samples/run-record、198唯一题/双filter396行、task/data来源、same source/current exact实例，达score>=80才issue/check新gate，不产生模型请求。配对旧原生160/198，允许arguments中仅max_gen_toks改变，其他prompt/doc/gold相等；按HTTP内容SHA对齐usage/finish_reason，统计新length和原14触顶题现在正确/仍错。单轮temperature1/C32变化可能包含采样轨迹/批调度变化，不能将所有差异严格因果归给预算。

不修改模型/服务/源码/题目/指标，不重复评测或测试性能；源8002不操作。

## 证据

远端根目录：/public-flash/jinghao/qwen3.6-27B/optimize/flash_attention/20261012-qwen36-27b-metax-flash-attention

| 产物 | SHA256 |
|---|---|
| commands/gpqa-native-cap50000-config.json | d16b9ace21fe7f877ef00902fbab6d0708a384cf0ba48aa8cc19d87d564cad27 |
| commands/gpqa-native-cap50000-contract.json | f334e29202ae6546c00e6414448b96e6efecf58757ff3e7d56c9960358468d1e |
| manifests/gpqa-native-cap50000-provenance.json | d93ae2aa8437a7821073bea903319d81bb0d654e77ffc4ee949ea299bd75219f |
| manifests/native-cap50000-service.json | c3ca2147f40c34e50a4cc9932d130c5f04b8a85265860688ea07edc931c63696 |
| manifests/gpqa-native-cap50000-process.json | ff6b53157b4193c21bd5625a21f348d17f646967f3d58b43e55119a69a4a149a |
| commands/diag007-launch-formal.py | 94a234cc56027ad52a4ff0f14a423f3fbd83da1336aa2ae7781cec295276048e |
| commands/diag007-finalize-terminal.py | 3895b33ecdfbe19f959b94326d4b94bbcf285f94fb5ee044303dbcce3b612baa |

结果results/gpqa-native-cap50000；日志logs/gpqa-native-cap50000-formal.log；新终态验证results/gpqa-native-cap50000-terminal-validation.json、新gate results/gpqa-native-cap50000-accuracy-gate.json（终态回执已生成，new gate未签发）。其他命令/身份/校验SHA见state.yml。

## 终态结果及逐题对照

| 正式同原生backend评测 | correct/198 | strict | length |
|---|---:|---:|---:|
| 旧30000 | 160 | 80.8081% | 14 |
| 新50000 | 158 | 79.7980% | 5 |

新预算少2题、-1.0101个百分点，未达到冻结80%，不签发gate。198唯一题/两filter396行、来源及same prompt/doc/gold、仅generation max_gen_toks变化已验证；模型当前精确实例和四仓库源码重新核验相等，超时0、运行异常0。没有run-record是wrapper低于阈值不签发的预期行为，native结果/样本已独立验真。

149题双方正确、9新正确、11旧正确、29双方错误。新正确IDs：8/12/27/45/64/71/99/152/180；旧正确新错IDs：10/21/48/88/93/94/97/98/129/166/186。

length从14降到5，stop193。新触顶IDs32/36/69/90/145均错，输出50000；前4题原先也触顶，145为新触顶（旧轮正常结束但错）。原14触顶题10本轮正常结束，5答对（27/45/64/71/180），5正常结束仍错，4继续触顶。

| 原14触顶题中本轮答对 | 新输出token |
|---:|---:|
| 27 | 35410 |
| 45 | 34089 |
| 64 | 22760 |
| 71 | 44832 |
| 180 | 23008 |

只有3道新正确题实际使用超过30000输出，另2道不到30000。原14题新旧完整响应前缀均不一致，前68–3307字符内已经分叉；没有“原样旧30000思考后追加20000”的反事实证据。更长输出可以使部分回答完成，但本轮不能把全部9收益或11损失严格归因上限，C32采样/调度/数值路径变化仍待定位。

根因状态：确认截断减少、轨迹分叉；没有确认整体精度改善或新算子数值回归。冻结accdiag-007-outputcap50000-full-score事件，当前50000正式范围失败，暂停继续性能优化；未自动降回30000、改变gold/指标/阈值、重评或新增请求。旧30000通过的两个gate和全部产物保留。

终态results/gpqa-native-cap50000-terminal-validation.json SHA 0b103f1d528135999e3a0c55f34659cdd1b1a8c54e9b19dae6aa1e7de42ae7a2；health SHA aac4f38925dc943afdda3ab0e5cb964fbc05eae55abca80df2bb90a297538d21；postmortem SHA2b332aad8dc2a85dba155bce5eea674bd0be7087988490eccb1786f61aa4d6f3。native results SHAcea497092cfed3068a7b03c910c97e00ab6199ee6b6e15c874cdf106a41e1dce，samples SHA4d11164b66e4e6c51f78ea917405bb9c61a8a9dc2dce181a669ded5a1c4ef21f。完整路径/其他SHA在state.yml。

rev-002复盘：当前FGvllm私有候选字节仍在但被原生attention绕过，micro收益不能当当前组合E2E收益；四场景稳态仍未测。后续优先在用户新指令范围内分离同seed/C1复现与C32批轨迹差异，再对持续错误定位共享路径或独立reference，最后同50000完整契约重评。此监控仅归档规划，不执行这些新实验。
