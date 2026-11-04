# OP009：GDN prefill FP32修复性能代价

用户2026-10-14明确要求保持FlagGems全部开启，对比修复前后Prefill/Decode/Mixed并做回退。采用本地inference-performance-evaluation targeted模式、baseline-sanity/minimal-regression范围，诊断例外仅限本周期；历史native50000 GPQA158/198<80保留，无formal/gate/四场景完成。继续既有独立优化容器，本case镜像谱系/挂载门禁复核，不操作源8002/其他任务/vLLM/共享代码/权重/tokenizer。发布/更新PR不是本轮请求，不推送。

唯一变量为私有FG-vLLM MetaX GDN prefill两个文件：baseline/revert使用public612原gdn_chunk(f4a6bd6c)，保持正确Vmajor接入及完整21白名单；candidate使用PR925精确公开修复(5e25ad42/082a40de)，已通过11tests和原9矩阵/18changed-input graph。旧BF16已知超容差只用于用户要求的速度参照，不可因其较快重新保留。其他源码SHA/TP2BF16/8192/prefixoff/graph64/MTP-fwd与nonMTP-packed/FGattention1及无blacklist都冻结。阶段结束后回退原BF16做对照，再恢复进入本轮时的OP007精确FP32源码6ea79405，不自动部署公开scratch。

| phase | workload | 预热/测量 | 主指标/守护 |
|---|---|---|---|
| Prefill | P1024/D1/C64/N128 | 3/3，固定末2输出吞吐spread≤10% | total token throughput；mean/P99TTFT与P99E2EL |
| Decode | P1024/D512/C64/N64 | 3/3，固定末2≤10% | output throughput；meanTTFT/TPOT、P99ITL/E2EL |
| Mixed | P1024/D256/C64/N128 | 6/3，固定末3≤10% | output throughput；meanTTFT/TPOT、P99ITL/E2EL |

父场景P1024/D1024/C64/N128，专项缩短输出/Decode单波64请求；未覆盖P4K/P16K/P32K或正式D1024。TTFT/TPOT/ITL含调度/排队/网络及Decode初始Prefill，非纯GPU阶段耗时。random固定token、T0/ignoreEOS、seed42按原生runner轮次派生相同输入，/v1/completions，全部角色同client/plan/比较契约。单轮600s，未稳定/超时保留failed/incomplete，不删慢轮、不重试候选或放宽门槛。每角色1独立实例、3测量轮，比较全指标spread≤10%、baseline/revert漂移≤1%。native primary0%和latencyguards5%仅描述无性能退化契约，不作正式晋级；FP32数值正确性与其性能代价分开报告。

执行顺序：精确核验进入实例390234/create1791956405.71与idle、保存现存两文件和四repo指纹；停止本case模型；baseline旧BF16三阶段→candidate PR925 FP32三阶段→revert旧BF16三阶段→恢复进入源码FP32。每启动角色双rank实际GDN/FA/packed与graph至少两replay、两固定smoke和新C8十题；末次restore同源码同配置用既有C8等价证据，不发新完整GPQA。性能计时不带profiler；路径证明的短trace独立。

状态prepared/not_run。产物在批准远端case的commands/manifests/logs/results/op009-*，原始runrecords results/op009-E2E/op009-{baseline,candidate,revert}-{prefill,decode,mixed}/run-record.json。命令与配置执行前保存，校验和如下；完整Skill bundle亦冻结。未知显存/功耗等保持null，不能从局部kernel或历史fw001数字宣称本修复收益。

- `commands/op009-source-spec.json` SHA `3974dcccc09f92715765872bcd8664beb49cbdceaec807c4a60ebc515b4cafbd`
- `commands/op009-performance-skill-bundle.json` SHA `4e27796b3c628daa6266a4ecdd356c446e172fe0de25d3fced7ddc11abd145ae`
- `commands/op009-accuracy-skill-bundle.json` SHA `f0d42f77d615206c593d11458a5403e8296b9b0ccff1606b08b4e2df69f2a0d1`
- `commands/op009-prefill-plan.json` SHA `0ca9728ac5acb498c57a65add884343c72ef41297e3e5bcc733dd30c92e62904`
- `commands/op009-prefill-comparison.json` SHA `53afb0ce72ae1009d7d85911c62940c9d16b915bf736a27b2cdf6339b5646653`
- `commands/op009-decode-plan.json` SHA `711df9a662cda985c1d8f774f08bff97e937024ae84ba2610e9af40628c9df1b`
- `commands/op009-decode-comparison.json` SHA `dfb640c7683ca5cb954f826e1a6a2de93c9787ce7aa41a7d4e196d186c33789e`
- `commands/op009-mixed-plan.json` SHA `fd675399604bc6f8419b1015e6db4744e71ba375d356e3d19b649729b3cbe351`
- `commands/op009-mixed-comparison.json` SHA `dfb640c7683ca5cb954f826e1a6a2de93c9787ce7aa41a7d4e196d186c33789e`
- `commands/start-op009-baseline-01.sh` SHA `7adc3ebc4011839ec2ad4934d881567ea96d9b94f23caf942167017195444cc8`
- `commands/op009-bind-op009-baseline-01.py` SHA `3ea30f5f069250863fdc037a768d6abea154c50f7ad5417dde130c94f5553f1a`
- `commands/op009-op009-baseline-01-c8-config.json` SHA `a812b2c108c5aacc08ea3353cf5fe9b547eced454d7818815f13c506ae4c0836`
- `commands/start-op009-candidate-01.sh` SHA `4cca708ef8003f86869401d2afb5c2d32ec81380a8e98105c300f1c3d95264ad`
- `commands/op009-bind-op009-candidate-01.py` SHA `438c3b70d5f3a9d3263daa627e224241145d74e14db22832b4d077d90d3682fd`
- `commands/op009-op009-candidate-01-c8-config.json` SHA `04931ce3a9cbe934ea08373cb83d2524faf349a065bfcf0f1ba6bbf50df9916c`
- `commands/start-op009-revert-01.sh` SHA `0728e49c54d129ba1959eb1cc5637f099827a7087af1a59239b01d8ccc8bcc2c`
- `commands/op009-bind-op009-revert-01.py` SHA `b902b49f6bef724f2ae23644c13059b5b69d348bd16c3926aff8320e343e9697`
- `commands/op009-op009-revert-01-c8-config.json` SHA `729c459c9d6a9d31b34f6a87f861723e8e5434d4983b6146bb87bbf1343b935f`
- `commands/start-op009-restore-01.sh` SHA `207d2c13e4b31e57d2ddce2b8c85e4f4c4f0acb6c276d09a1bb85df370464d62`
- `commands/op009-bind-op009-restore-01.py` SHA `f555da7f18a685173923dd42776364b475365899d5e3ae499916f787bfb266ee`
- `commands/op009-op009-restore-01-c8-config.json` SHA `adf0ab41927fafdd5c2cb7b128f9301f8cf578201c19c958c869689ee9b32b8b`
- `commands/op009-switch-private.py` SHA `c3b17d70d84ea94e4736b6059f731b26ee5d42e2896aca12a7eb346d167a49b0`
- `commands/op009-controller.py` SHA `f08403e841a260fbb92b22ca84d9a78ebec1a14f925a4ba4614ac78220af47f8`
- `commands/op009-launch.py` SHA `49d534ac85b7807838a36f18be27d9d4cbbe81341980328ffbd24957271aff2e`

唯一控制器已启动：hostPID113296/create1791958300.57，manifests/op009-process.json绑定workerSHAf08403e841a260fbb92b22ca84d9a78ebec1a14f925a4ba4614ac78220af47f8；results/op009-progress.json与logs/op009-controller.log实时记录。无重复启动。

终态只读校验命令预先保存commands/op009-finalize-existing.py，SHA d3638b8a9321b2ed22aaf339ff1893fd36d920940765931b8f09528b2fe0b5ef；仅在控制器完成且当前FP32原源码/精确实例相等时，消费九份既有runrecords及冻结比较契约并保存results/op009-terminal-validation.json，不发模型请求、不改服务。若已有终态回执仅只读。

终态校验v1仅保存、未执行；客户端源产物路径位于优化容器内，最终使用commands/op009-finalize-existing-v2.py SHA f05f3b8773add7ddd04fcd6d47a7b3064784d45e6850b602b5eacf7d57f95d2e，在该容器中只读校验，避免Host路径误判。v2不调用嵌套docker、不发模型请求，其他验证不变。

记录校验发现此前OP008两个JSON发布回执位于本地case目录；本轮已逐字校验后迁至远端results，更新引用，仅本地Markdown/YAML保留。全项目校验仍有其他案例及历史索引/过程材料失败，未触碰无关案例；本轮源代码、计划与实验记录的限定检查另行通过。

基线Prefill checkpoint：原生check_run通过，3warm/3measured；各测量轮128成功、0失败、131072输入/128输出token。total throughput三轮6183.138860/6196.256291/6179.876292 tok/s，中位6183.138860；meanTTFT三轮8285.203922/8266.820117/8290.152510 ms，中位8285.203922。runrecord SHA5a52fb3bfa0c5e0cfa33dfef9549156e373337748c93bad4e9b3243c5f136ab7；当前旧BF16基线398081/create1791958358.04，manifestSHA259d520224e7e89958ec08346e23ae0d4ff62a682b1deca2c6d96258f5361c94，FGsourcef23993c24c7ba937e1d0b5cfd0fef13d9b24315032a3bea40e8d348379e338b3。各rank190graph/96legacyWY/96prefillH/2880packed/960FA splitmerge及新C8通过。不能在candidate/revert完成前计算修复代价。

循环监控恢复被自动审批拒绝，原因是当前用户未明确授权重新启用持续30分钟自动化；旧heartbeat保持PAUSED，无替代定时任务/规避。仅当前会话前台只读跟进已授权单轮控制器，性能计划/请求不受影响。

基线Mixed准入失败：6warm/0measured，末3输出713.504121/715.988611/636.765345tok/s，spread11.103407%>冻结10%；所有6轮128成功/32768输出tokens，失败是未稳态而非请求错误。原始failed record保留，不将warmup当measured，不放宽规则。候选441312/create1791959876.79正在按原计划启动；继续各阶段与回退，不计算Mixed可信代价。基线Decode已有3measured输出931.228494/930.070057/929.432431tok/s，中位930.070057；TPOT中位56.572527ms，待终态统一原生重验。

候选实际绑定qwen36-fa-opt:441312:1791959876.79，manifestSHA6c357f2b496fec3c3abd89e29ae3a5a9b8493b569de1b2aa0f7ab7d5f91d3b15，FGsource86cf0b94719a68c66ec9f0146f82449dcd69950f2e64f081004008568ec53b98；两rank各96preciseWY/0legacyWY、190graph、96prefillH、2880packed、960FA split/merge，完整21白名单不变。C8进行中，尚无candidate测量代价。

候选Prefill3measured原生check_run通过，吞吐5670.593227/5669.920162/5666.263414tok/s，中位5669.920162；meanTTFT9030.567136/9031.046784/9035.863766ms，中位9031.046784。每轮128成功/0失败/131072输入/128输出，runrecordSHA7678b82c6b11f38b8fd66d081ef7e067b3edf9123f9b667cc770b3daa1fcc023；回退未齐，最终归因待验证。代价属于PR925完整修复（FP32/IEEE及有界tile），不是孤立dtype消融。候选Decode3warm/0measured准入失败，末2输出892.193124/716.081056tok/s，spread21.900752%>10%；recordSHA81bbc0d21e746843e555b92371587c16602cf16593ea8e6d6e1c395ed2ed2307，不能用预热中位当Decode性能代价。C8候选已通过范围内sanity，Mixed继续，数值问题与性能波动不作因果混同。

候选Mixed完成6warm/3measured，原生check_run重验通过，recordSHAfbc149f8ae9bb329e80172b6e5855b4d90d79ebb9ec9bd3fe90fc3b9819bfe61；输出671.822879/670.433035/669.850612tok/s，中位670.433035；meanTTFT5891.308587ms、meanTPOT72.418267ms、三轮P99ITL中位1500.147918ms、P99E2EL中位30405.150898ms。末3warm散差.110665%通过；原始基线Mixed未稳态，因此不能与其warmup计算收益。当前回退旧BF16实例481486/create1791961414.67启动，继续冻结三阶段，最后恢复原FP32。

回退Prefill原生check_run通过，recordSHA8655c146c9891d72572771748a0f35781359d15255d28977f37711c68088bba0；总token吞吐中位6233.578941tok/s、meanTTFT8216.763846ms、P99TTFT/E2EL中位10725.498358/10725.498162ms，sourcef23993c2与基线相等。当前回退实例481486/create1791961414.67，manifestSHA22ad0df6dfe2d9f48b831f845f7a5835d9fe04fe81fe6f34281fd9b1e5671a13；完整21白名单、graph及C8均保持/通过。回退Decode继续，最终恢复进入的原FP32。

终态：`completed / incomplete / original-FP32-restored`，native controller耗时5114.823416s。57轮=36warm+21measured：九阶段记录7个native完整、2个稳态准入失败；source/计划/client/全部轮和三原生比较已只读重验。终态验真回执results/op009-terminal-validation.json SHA54db01e6ee3572f4f875edbdf9f6b142fb0f1d43cd7d66397a95e1592c07e14e，不发模型请求。

| 阶段 / 指标 | 修复前baseline | PR925 FP32 | 修复前revert | 结果 |
|---|---:|---:|---:|---|
| Prefill total token throughput tok/s | 6183.138860 | 5669.920162 | 6233.578941 | FP32−8.300294%；回退漂移+0.815768% |
| Prefill meanTTFT ms | 8285.203922 | 9031.046784 | 8216.763846 | FP32+9.002106%；回退漂移−0.826052% |
| Prefill P99TTFT ms（三轮描述值的中位） | 10819.595925 | 11784.257379 | 10725.498358 | FP32+8.915873%；漂移−0.869696% |
| Decode output tok/s | 930.070057 | — | 934.948005 | 候选3warm散差21.900752%、0measured，不比较代价 |
| Decode meanTPOT ms | 56.572527 | — | 56.312641 | 同上；原/回退数据完整不能填补候选 |
| Mixed output tok/s | — | 670.433035 | 712.452900* | baseline6warm散差11.103407%、0measured；revert测量散差50.727150% |
| Mixed meanTTFT ms | — | 5891.308587 | 5237.044394* | revert异常轮27439.921893ms，散差424.155157%，不可用中位掩盖 |
| Mixed meanTPOT ms | — | 72.418267 | 69.337709* | 三方比较incomplete，不计算收益/代价 |

*Mixed回退三测量轮输出712.452900/351.366645/712.773694tok/s，meanTTFT5237.044394/27439.921893/5226.728006ms；异常轮128请求全部完成、32768输出token，P99E2EL75921.634719ms。完整计数不等于稳态有效，全部保留，无删轮。日志相邻时间未发现明确编译/抢占/服务error，未定位根因；不能因旧BF16健康返回就排除host/device/shape/调度问题，也不能因候选Decode波动就认定FP32数值有错。

Prefill三角色全部指标测量波动≤10%、回退漂移≤1%、source唯一变化/flaggems_vllm_sha256，因此可归因这份完整精度修复/有限配置的性能成本。native comparison=failed，原因是吞吐未达到0%无退化和时延超过5%守护；这是性能退化结论，不使已有数值/graph回归变为失败。Decode/Mixed native comparison=incomplete；禁止用预热补测量或仅凭两侧漂亮中位数计算Mixed成本。

三角色KV规划均869418tokens；未采样绝对显存峰值、利用率/功耗，保持null。原生metric为client代理，非纯设备时间；固定P1K缩减场景、不代表四正式场景/长期容量。PR925候选86cf0b94与基线/回退f23993c2的源码SHA独立记录；最终原OP007FP32源码6ea79405恢复，不能把PR清理后的测量直接当恢复版本的精确性能。

当前恢复qwen36-fa-opt:526267:1791963121.41、manifests/op009-restore-01-service.json SHA213f007eb19feab52926948ea15ca877428aae74556b521fe8ecdb1b000dbf1c；runtimeSHAf9992b674e72502ffe1e7c04b7c6cdf73d97b2b68fe70d47b834fe90acda9c5e，双rank各190graph/96preciseWY、两新smoke通过，同进入源码/启动配置C8等价，不新增C8/完整GPQA。完整21白名单、FGattention1、无blacklist、MTPfwd/nonMTPpacked保持，源8002/其他GPU/共享代码/vLLM/权重/tokenizer未操作。PR保持Draft，未新增GitHub消息/提交推送。已有heartbeat仍PAUSED（恢复申请被自动审批拒绝），本轮以前台跟进完成，没有替代定时任务。

rev008复盘：精度修复已经过原容差验证，但完整FP32链有可复现Prefill成本；当前先保留正确源码。下一轮先定位测量长尾与shape/编译/主机调度覆盖，在新契约下统一三角色测量；再按代表性trace选择一个FP32数据流/tile改动，原失败输入+慢衰减9矩阵/18graph原容差优先。不能以旧BF16较快回撤正确性修复，也不能先叠加新kernel。正式GPQA158/198历史失败保留，无formal gate/验收。全部原始日志/轮/比较SHA在state及远端。
