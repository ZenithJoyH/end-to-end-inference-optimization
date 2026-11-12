# acc-001: opt17 C64 GPQA / ERQA

> 最终：评测及独立审计完成。GPQA **126/198=63.64<64**，有效未达标、无gate；ERQA **175/400=43.75>=40**通过，0拒答、native/全400口径一致。原用户服务完整保留，控制器退出、自有adapter已停、监控已删除。

用户2026-11-05要求对已重新启动的当前模型运行完整GPQA和ERQA，C64，并每30分钟检查通知实际进展。已明确沿用模型默认采样、GPQA65536/ERQA18000输出上限及strict64/native40阈值；每数据集一次，合法GPQA低分仍完成ERQA。

当前mx-59/qwen3vl，qwen3vl-opt17/8030/GPU0,1/TP2/BF16，prefix cache开启。模型容器命名空间API346908/ticks681351047（Host183357），原argv/env/cwd/源码/缓存保持。只创建CPU评测器和loopback19964默认采样传输，不重启/停止用户模型，不改推理源码或评分，不清cache/不测性能。

本地inference-accuracy-evaluation/formal-gate模式；完整Skill bundle已冻结。官方v1原始GPQA runner经维护版formal_accuracy.py；ERQA沿用冻结flagevalmm400题630图及filter_rejected原评分。新CPU评测器只读复用同模型旧评测资产，模型权重/图/源码真实指纹重新取证。Graph仅当前startup capture+normal smoke/C8，不伪称直接replay计数。

远端目录由用户明确批准：`/public-flash/jinghao/qwen3-VL/20261105-qwen3vl-c64-accuracy-mx59-001`。正文198+400按序，各一次；smoke1+C8护栏9请求。模型默认T.7/P.8/K20/rep1，无requestseed；taskseed42。保留原生超时/重试，独立UUID响应缓存，已有KV不清。启动前CPU双provenance、198实际工厂payload（仅模型名变化）、400/630图和评分源码核验。

状态：CPU准备中，尚未发送模型请求。监控qwen3vl-opt17-c64已创建，每30min；两项终态及原服务保留独立核验后删除。采集器故障只能CPU复核已有结果，不得重发或改判分阈值。

## 执行前归档
- `/public-flash/jinghao/qwen3-VL/20261105-qwen3vl-c64-accuracy-mx59-001/commands/default_sampling_proxy.py` SHA256 `0767e576db32e00324d49e37cc62dd348ca2b3c7495920762149fb825229dc39`
- `/public-flash/jinghao/qwen3-VL/20261105-qwen3vl-c64-accuracy-mx59-001/commands/proxy_cpu_test.py` SHA256 `e8adcca445363879a939fffc7f0f14b27bc72fa3926461f2815f57aec889067e`
- `/public-flash/jinghao/qwen3-VL/20261105-qwen3vl-c64-accuracy-mx59-001/commands/collect_current.py` SHA256 `73b12bf4fb938fb2520851ddcd63c4b53f5a3c2ed90eb068cc954267b637e2c9`
- `/public-flash/jinghao/qwen3-VL/20261105-qwen3vl-c64-accuracy-mx59-001/commands/prepare_environment.py` SHA256 `855443279b2f5b2b8b969e0679af118701c550e04d4c8c2bceb18ac982538b59`
- `/public-flash/jinghao/qwen3-VL/20261105-qwen3vl-c64-accuracy-mx59-001/commands/accuracy_controller.py` SHA256 `ffc73aca841c4caaeae9cf4f85d9fc7eacade9078012b8b34ca056cf6ebcc244`
- `/public-flash/jinghao/qwen3-VL/20261105-qwen3vl-c64-accuracy-mx59-001/commands/payload_parity.py` SHA256 `7bb6548e461d76cb2454ad242fe3257c922d822f91ed530cc63c1023d63054a7`
- `/public-flash/jinghao/qwen3-VL/20261105-qwen3vl-c64-accuracy-mx59-001/commands/start_controller.py` SHA256 `d777a9d8bced00967b631fe238472993e04a2d2c27c49aa9551da83eb52e3442`
- `/public-flash/jinghao/qwen3-VL/20261105-qwen3vl-c64-accuracy-mx59-001/commands/prepare_cpu.py` SHA256 `0903331b8e2256a435dab75a303085ed4d6a6aa9eeb9a44ea97c75b54602698d`

- 本次CPU预检脚本 `commands/prepare_cpu.py` SHA256 `0903331b8e2256a435dab75a303085ed4d6a6aa9eeb9a44ea97c75b54602698d`，执行前与其余命令一并归档。

CPU准备出现历史引用位于新评测器唯一bind之外的路径错误，0模型请求；保留旧日志，使用历史原文件字节SHA一致的任务内副本修正路径，不改任务/判分/数据或模型。
- 修正执行前归档 commands/payload_parity_v2.py SHA256 `6f1e0a463126a79c00d847440070b90c0a3c71bac9b72c8ea6fe258863f43622`
- 修正执行前归档 commands/finish_prepare_v2.py SHA256 `140915b0329ced83e0a5d676b7ca09387642abb18a0e17292f7f851461a3e7f1`

修正准备脚本生成时匹配returncode子串导致的SyntaxError（执行前失败、0请求）；新不可变finish_prepare_v3.py已用compile验证所有可执行脚本，SHA256 `a9655d2b5d55064d5e7c96d41560b2565022f2fecf59b416850c2c19f99d7ad1`，保留前两份失败日志。

CPU数据/工厂已passed；发现原official镜像无扩展名GPQA模板的strict regex不同于历史冻结协议。发送任何正文前，仅私有CPU评测器模板一行恢复为旧provenance精确正则，保留新旧字节和SHA；不修改原镜像标签/旧评测器/推理服务，不放宽阈值。最终重新采集provenance3/4，两份必须一致、同198raw/evaldocs，taskconfig只允许模型名与并发变化。旧source全树SHA差异单独保留。
- 执行前归档commands/accuracy_controller_v2.py SHA256 `26c8243fb1b6cdacec9fb8a852778cb237e5f90a5c0f0b495218be129eb841e2`
- 执行前归档commands/start_controller_v2.py SHA256 `665116817ac8d0758f55cdd9d979ac4150094ab7e55e48ad2966f8e9e380e627`
- 执行前归档commands/finish_prepare_v4.py SHA256 `6438f38c022140dd9eeeefd4626e146ecc28320bdfce639733eba114a4536534`

## 已启动

2026-11-05 18:46:20Asia/Shanghai smoke1+C8/source全部通过；18:46:28开始完整GPQA198/C64（尚无最终分数），完成后同一控制器自动ERQA400/C64。唯一controller250626/ticks681512052，commands/accuracy_controller_v2.py SHA26c8243fb1b6cdacec9fb8a852778cb237e5f90a5c0f0b495218be129eb841e2。严禁重复start/prepare/并发interrupt。

prepared2dcc7912/contract9e74efad/payloadparityc082c6f6通过。全部CPU事件已resolved且正文0请求；最终provenance3/4精确一致，同198题、原strict正则、原gen_kwargs，taskconfig只允许模型名opt15->opt17和并发32->64变化。新私有评测器严格模板恢复回执b957796d、事件解决回执3c107491，保留之前全部字节和失败日志。

两CPU evaluator qwen3vl-opt17-gpqa-mx59-20261105（officialv1）与qwen3vl-opt17-erqa-mx59-20261105（原flagevalmm），直接bind新case，Host gpqa/erqa即原生输出。进度看logs/events.jsonl、full-gpqa.log/full-erqa.log及native IDs；request-audit uniqueSHA不是覆盖门槛，原生score logger matched0不是0分。GPQA验证使用configs/gpqa-provenance-3.json，不拿未恢复正则前provenance1/2作冻结依据。

用户源模型qwen3vl-opt17/8030、容器API346908/ticks681351047、Host183357、GPU0,1/TP2/prefixON全程保留；默认T.7/P.8/K20/rep1，无seed覆盖。finally只停自有adapter，必须核验source/PID/argv/env unchanged/models200。监控qwen3vl-opt17-c64每30min，全部终态及独立复核后删除。不追加GPU诊断/完整评测/性能/修复。

18:48Asia/Shanghai只读回执：控制器同PID/ticks活跃，GPQA原生53/198、代理118次已发/54返回，实际上游cap65536且无sampling/seed覆盖；ERQA尚未启动。源models200/opt17正常。阶段分数不是最终分数，不提前判定passed/failed。

19:01Asia/Shanghai定时只读检查：唯一controller250626/ticks681512052活跃；GPQA原生进度187/198（首个代理快照185返回/198已发，随后原生187）；ERQA尚未启动，暂无最终分数。原源容器API346908/ticks681351047、opt17/8030/prefixON一致，models200；未做新的GPU/模型请求、变更、重启或补跑。继续既有控制器和30min监控。

两数据集已原生终态：GPQA126/198=63.636363<64，无gate；ERQA175/400=43.75>=40。执行本地inference-accuracy-diagnosis冻结accdiag-opt17-c64-gpqa-001，根因未确认、不自动修复或重跑。执行前归档CPU独立核验 `commands/independent_final_audit.py` SHA256 `affda3f828c4977cb887f65b81834fdb9e654d68f8b2b02bb1942a978748221f`，只复核已有结果、源码、参数和当前服务，不新增模型请求。

独立CPU审计v1误用请求配置而非原生UUID effective_config，被维护版缓存命名空间校验拒绝。该审计工具问题不改变原生评测结果，保留原日志；v2改读唯一原生effective_config，沿用同一严格校验，无模型重跑。执行前归档commands/independent_final_audit_v2.py SHA256 `67c955ff25371f8ac909cb4bd029d3de0735b67af33f82e6a297c83bf876c300`。

## 最终独立核验与决定

GPQA于2026-11-05 19:36Asia/Shanghai、ERQA于20:14结束。完整198题及400唯一question_id、全部630图/原评分源码、strict原提取规则及分数交叉核验passed。GPQA126/198=63.6363636364<64，正式失败保留、未签gate。ERQA175/400=43.75，0拒答，native与全部400计错相同，通过40阈值。两数据集各一次完整评测，未拼接旧成绩或重跑挑分。

GPQA实际198次/198HTTP200、198unique消息，全部cap65536；ERQA原生重试流程460次/460HTTP200、399unique消息，cap18000，覆盖以400唯一原生question_id判定。60条BrokenPipeError均在同请求已记录upstream200后发生，保留作健康诊断，不额外否决原生有效精度。全部实际请求未带sampling/seed覆盖，模型默认T.7/P.8/K20/rep1/prefixON保持。

独立审计v1误用请求配置被严格UUID缓存身份检查拒绝；CPU-only v2使用唯一原生effective_config复核同一完整结果后通过，未改数据/评分/阈值/原结果、未重发请求。完整源码、模型配置/分片文件元数据、tokenizer、运行身份/argv/env/git/版本在before/afterGPQA/afterERQA/final及新只读current快照精确一致，原源容器API346908/ticks681351047、opt17/8030/models200保留。模型分片历史全字节SHA仍未提供，不将元数据一致伪称全字节验证。Graph范围仅当前startup capture+正常配置smoke/C8，未安装直接replay计数。

本地inference-accuracy-diagnosis冻结`accdiag-opt17-c64-gpqa-001`：正式分数有效低于预冻结阈值，gate-blocking；根因unconfirmed。历史opt15 C32的127/198仅作参考，不同Host/代码/实例/批轨迹/缓存且无requestseed，不是单变量对照；本轮不证明PR1069、MoE或native回归。未做新的GPU最小复现/二分/修复/性能。只有另行受控定位及修复后同契约正式通过才能解除精度阻塞，不自动追加完整轮次。

全部授权评测和审计终态；控制器退出、仅自有adapter停止，用户模型未stop/restart/改源码/清cache。两个CPU评测容器及原始产物保留。自动监控`qwen3vl-opt17-c64`已成功删除，无当前待跑任务。

### 最终证据（原始样本/日志均远端保留）
- gpqa-completed: `/public-flash/jinghao/qwen3-VL/20261105-qwen3vl-c64-accuracy-mx59-001/results/gpqa-completed.json` SHA256 `90a9c3a043d4460ef48a0afd96196aaf67d39e94c2e9228474ee6d664c6dbac2`
- erqa-completed: `/public-flash/jinghao/qwen3-VL/20261105-qwen3vl-c64-accuracy-mx59-001/results/erqa-completed.json` SHA256 `7d4ef2d340c32c18c04636e87f6158e261f16b966a3c28a2486461172fc6badf`
- completed: `/public-flash/jinghao/qwen3-VL/20261105-qwen3vl-c64-accuracy-mx59-001/results/completed.json` SHA256 `206d8ac8d68473b52a0df297f4521f4fa9238644181c576e642b84b31f151c95`
- user-service-final: `/public-flash/jinghao/qwen3-VL/20261105-qwen3vl-c64-accuracy-mx59-001/results/user-service-final.json` SHA256 `590b22f563020aec371d6abc9f6021f3e88b6f846c435976deb59eee2b2259e6`
- independent-final-audit: `/public-flash/jinghao/qwen3-VL/20261105-qwen3vl-c64-accuracy-mx59-001/results/independent-final-audit.json` SHA256 `1b246eb40d187862b081ab728dcfc04335899397d1f163f6deb62a6d1c192181`
- accuracy-diagnosis-frozen: `/public-flash/jinghao/qwen3-VL/20261105-qwen3vl-c64-accuracy-mx59-001/results/accuracy-diagnosis-frozen.json` SHA256 `0ec10385c13474e14826beb9d2e4a18bb80151095dd26219987ae3469858de97`
- gpqa-sampling-audit: `/public-flash/jinghao/qwen3-VL/20261105-qwen3vl-c64-accuracy-mx59-001/results/gpqa-sampling-audit.json` SHA256 `20b37d2ffdbdbc55db1e34960e2c36b85cb72ec47ef51c2a997e2d8cc7cf6b3d`
- erqa-sampling-audit: `/public-flash/jinghao/qwen3-VL/20261105-qwen3vl-c64-accuracy-mx59-001/results/erqa-sampling-audit.json` SHA256 `a6fbf30494360d3b100410794de18ba00f1a70deaa2612fb4b12fdb8c54068a3`
- GPQA native result SHA256 `0b97f4bfc45a683f3e92337a1f7e4206e7c9dd5dd0d24a2383afc68b8b963f60`；samples SHA256 `269b06dd2f99b2d39b0f8c247f9d8ba9f170af6c1c8374281ad5b08d1c0eaa80`。

后续[diag-002只读提取/截断审计](diag-002-extraction-truncation.md)完成：未确认正确最终答案漏提取；65明确选错+6触顶未答完+1未触顶重复无结论。共8个64K触顶，另2条早已strict判对。原成绩不改、原服务/配置精确一致，无模型重跑。
