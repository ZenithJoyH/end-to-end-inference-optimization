# accdiag-014：8010恢复及状态清零受控复现

状态：局部24/24请求已完成、原症状未复现，证据已冻结，heartbeat已暂停，等待用户方向；分类 accuracy-diagnosis/execution-mode；不进行性能优化或全量GPQA。

## 目标、范围与假设

用户于2026-10-15明确授权恢复PPU-07的8010、定位非法内存访问及reasoning-only问题，禁止全量GPQA。原acc-012失败证据与127/198观察分数保持冻结。仅作用于容器 `qwen3.8-flash-opt-ppu07-20261015`、卡8–15；卡0–7和8035其他任务不触碰。

先以冻结runtime-before中的argv/env恢复原候选，不顺带调整blacklist、Gems、compiler或KV-zero接线。新日志放入原case的 `diagnostics/accdiag-014-service-failure-20261015/recovery-001/`，不覆盖 `service.log`。恢复前核验源码指纹、8010无监听和卡8–15空闲；旧evaluator/helper/controller均已退出。恢复后捕获新身份/源码、health、graph，旧gate不继承。

首个算子实验拆分 `nonzero_numpy`、布尔index_put清零、前置gather与后置scatter，原生Torch/CPU为精确oracle；固定shape/dtype/stride、mask全false/全true/混合、空/边界/非对齐batch，逐阶段同步以区分异步上报点。测试进程仅使用物理卡8，内存限制为小张量，不修改运行中vLLM/Gems源码，不切服务开关。若需服务运行时插桩或patch，先保存隔离与回退依据，单独记录变量，不把微测当真实服务复现。

服务复现先冻结8条原始请求：null142/144/149/155、reasoning有答案对照151及按doc_id升序的3个字符串对照。核验prompt hash、原采样/seed1234/stop/max60000，C1→C8→C1各一次，共24条上限；新增响应证据字段单独列为响应取证差异。若出现非法访问或服务退出，停止后续请求并保存失败，不自动循环重启。小并发不复现不排除C64持续更替问题，不自动扩至完整198题。

## 门禁与回退

新增直接证据：旧 `service.log:3788–3833` 的驱动invalid-page明确记录 `Exception at function: _index_jit_function`。Python nonzero的count.item是同步上报点，不应当作首个fault kernel。GDN前一行确有 `ssm_state[prefill_state_indices]` advanced-index gather；但尚需张量/最小复现区分合法地址计算错误与无效metadata，不能单凭kernel名称确认源码根因或与乱码的关系。

微测脚本 `case/commands/accdiag014-state-zero-micro.py` SHA `c121dea5b53840410b5d1b9dbc90dec9b8d95561b8160003b9a5ad33cdcb623d`；物理卡8、单进程显存上限2%，按nonzero→zero→gather→chain四个独立进程串行执行，每步前后同步并与CPU逐位比较；输入包括FP32 `[B,6,128,128]`、int32/int64索引、stride `[102400,16384,128,1]` 的padding参考布局。该layout取设备寄存器/源码线索构造，未宣称为已捕获的完整故障张量。缓存使用独立SQLite文件，不与服务DB并发写；健康idle后才运行，不与API诊断负载重叠。

微测控制器 `case/commands/accdiag014-micro-controller.py` SHA `a3b1de68a88cc3aeb95317120a1251fd7e0bb1141df85c78d1403c8f611801e2`，命令 `python3 case/commands/accdiag014-micro-controller.py --case case --container qwen3.8-flash-opt-ppu07-20261015`，输出 `diagnostics/accdiag-014-service-failure-20261015/micro-001/`，任一阶段失败不继续后续阶段；CUDA_LAUNCH_BLOCKING=1仅作用于微测进程。

局部客户端 `case/commands/accdiag014-cohort.py` SHA `cd195cecc54ecca2624e28a346dfb0a87e16df02ddbe424b82aed77d87f46e92`，先 `--mode prepare --case case` 离线冻结8题及逐字prompt hash，再 `--mode run --case case` 一次。原stop为task的 `</s>` 加原API eos字符串 `<|endoftext|>`；仅增加 `return_token_ids=true/return_prompt_text=true` 两个响应取证字段，不改生成参数或服务源码。原来没有raw token，因此不宣称新增字段与旧原始响应字段完全相同。CPU宿主客户端不引入正式evaluator或评分逻辑；输出 `cohort-001/`，24条上限、零重试，身份改变/服务错误停止。

本次用户授权解除“不得恢复服务”的旧边界，但不伪造旧FINISHED/FINAL_SUMMARY。每个新阶段独立一次性目录/锁，已有客户端只监控不重发。无其他8010客户端、健康且idle、身份未漂移才发送诊断请求。服务失败/数值不一致即停当前臂，保留原实现及补丁；不降低阈值、不从reasoning补计正式答案、不签发精度gate。正式性能保持blocked。

## 执行及证据

远端根目录为 `/mnt/nfs/users/jinghao/qwen3.8-flash/20261015-qwen38-flash-next-ppu07-container/accuracy/acc-012-full-gpqa-ppu07-c64-master-20261015`（下称case）。恢复脚本 `case/commands/accdiag014-recover8010.py` SHA `7f00f691e3e2bc1cb4e15b2ebafe48ad4f29d40160421b4f99860767aadc9514`，执行 `python3 case/commands/accdiag014-recover8010.py --case case --container qwen3.8-flash-opt-ppu07-20261015`。运行前完整源码/import/artifact指纹必须与 `evidence/source-before.json` 一致，重复运行拒绝。新启动脚本及receipt在recovery-001；原始PYTHONPATH等环境也暂按冻结运行事实保留，避免把安装方式调整混进首次恢复对照。

## 性能效果与决定

### 终态取证命令（执行前记录）

2026-10-15 20:53只读确认客户端退出、FINISHED.json及24份结果齐全，服务健康且idle。后续仅追加终态证据快照，不发送推理请求、不改变服务或旧正式产物。CPU取证脚本将保存为 `case/commands/accdiag014-freeze-terminal.py`，SHA `ca47cb8a737030295e050e0d6fd690e5b02017b708441f7f4addbc7116a79290`；命令 `python3 case/commands/accdiag014-freeze-terminal.py --case case`。脚本核验24原始响应SHA、8唯一doc三臂、C1前后完整tokens/messages、prompt一致性、当前PID/start ticks/argv、idle指标及原源码/import/model/tokenizer指纹；只创建一次性 `diagnostics/accdiag-014-service-failure-20261015/terminal-freeze-001/`。恢复日志仍在写入，按固定字节前缀快照保存并标明范围，不把活动日志的整文件SHA当稳定身份。原127/198及无有效gate保持不变。heartbeat已通过产品接口确认为PAUSED，8010保持运行。

### 已执行（2026-10-15 17:46 +08:00）

17:37:07恢复启动，17:43:15 API ready；源码/import/engine/model/tokenizer与原候选逐字指纹一致。新API宿主PID1290447（容器1224087）、Engine宿主1295971，TP8在物理卡8–15。恢复日志保存在recovery-001/service-restored.log；FULL和PIECEWISE捕获完成，health200、idle0/0、模型endpoint身份正确。尚不宣称本次服务两次实际replay通过，后续由局部请求取证。

17:45:38–17:46:35微测4阶段均exit0：nonzero30个、bool清零30个、gather32个、chain中的gather/clear/scatter各32个，总188次数值检查均与CPU逐位一致；包括空mask、全mask、混合mask、小/非对齐batch、int32/int64和padded stride。全部在新独立进程同步执行，无非法访问，原服务仍health200。**仅排除这些小池/布局/输入下的独立算子错误；未覆盖真实大池高block ID、服务metadata复用和graph执行，不能据此排除index或宣布修复。** 微测进度和各stage日志在micro-001，async job `j286767504686.1579996`。

8题清单已离线冻结为cohort-001/requests.json，SHA `d205fea6e3b3def7678829b932099813c9ecfc86ee765ea56c4860559353747a`；顺序142/144/149/155/151/0/1/2，全部prompt hash与原生样本匹配。按计划一次性启动C1→C8→C1客户端，不调用formal runner，不重计正式分数。

局部客户端实际于17:48:15 +08:00启动，Host PID1634714、async job `j554771784166.1634641`，新服务身份 `ppu07-8010-1290447-477285377`。17:49快照处于c1-before、已派发1/24、完成0、错误0、health200、running1/waiting0；首个prefill伴随index_select冷shape编译提示，不按其warning认定错误/停滞。原heartbeat复用同ID `qwen3-8-ppu07-gpqa-c64`，已确认为ACTIVE/30分钟，仅只读监控该客户端，实质结果/阶段切换/异常才通知；不得重启/补发/扩C64/跑formal，局部终态暂停。当前尚无复现结果，不作根因或修复声明。

不测性能收益；正确性定位未完成，根因仍suspected-not-isolated，未修改生产源码，未保留任何新性能候选。

### heartbeat 2026-10-15 18:19 +08:00：前两条null目标在新实例C1产生最终答案

按 inference-accuracy-diagnosis 只读核验原客户端及服务身份，未发送任何额外请求。客户端仍为Host PID1634714，API PID1290447/start ticks477285377/argv与冻结服务身份匹配；Engine和8个worker存活，health200。requests.json SHA仍为d205fea6e…，未改采样、prompt、stop或源码。

已派发3/24请求、完成2/24请求，覆盖2个唯一doc（142、144）；当前c1-before的doc149在生成，C8及C1-after尚未执行。不能把8个唯一doc的3臂合计称24道题，更不能外推完整198题分数。

| doc | 完成时间 +08 | 最终答案文本 | completion tokens | 原始token证据（0-based） | finish/stop |
|---|---|---|---|---|---|
| 142 | 18:06:36 | The best answer is D. | 16338 | `</think>`248069位于16001；末token248046 | stop/null |
| 144 | 18:14:54 | The best answer is B. | 3734 | `</think>`248069位于3524；末token248046 | stop/null |

两个回复均有非空reasoning及非空最终content，raw token数量与completion_tokens一致，闭合思考后确实继续输出最终正文，再由主EOS `<|im_end|>`248046结束；不是60K截断或TIMEOUT占位。不能仅凭最终答案字母宣称两题评分正确，此处是输出健康复现，未重计原正式分数。原始文件为 `cohort-001/c1-before/doc142-result.json`、`doc142-response.raw.json`（response SHA e0cdc47e7128bc6464eaf97088208a06fa74d55b3b94372b7cb28a04c430021a），及doc144对应文件（SHA b1932ef347f87261bb3759fe3d010dad7f58a7270bf0e205bd4e5fa14827b2fe）。

当前服务running1/waiting0、KV0.2618%、preemptions0，累计生成24321 tokens、最近约15.1 tokens/s，持续生成而非停滞。progress.json最近18:14:54、service日志18:19:41更新，无新ERROR/illegal-page、客户端失败0，FINISHED未出现。已耗时约31分26秒，不估ETA。

阶段性结论仅为“原null目标142/144在新实例C1未复现空最终content”。它表明当前parser至少在这两条原请求上能正常处理think-end及最终正文，但重启初态和负载条件均与原C64不同，尚不能归因为并发、缓存清零、index或compiler，也不能排除间歇性解析/生成异常。继续监控原有客户端，不暂停heartbeat，不改服务、不加埋点、不自动扩C64或启动formal GPQA。

### heartbeat只读核查 2026-10-15 19:19 +08:00：已进入C8

本次heartbeat触发标记为18:48:56；实际远端观测时间为19:19:26，报告使用实际观测时间，不能把稍后产物说成18:48已完成。沿用同一精度定位流程，客户端PID1634714、服务1290447/start ticks477285377/argv均未变，requests.json SHA仍d205fea6e…，无额外模型请求或源码/配置操作。

首轮C1于19:00:36全部8条完成，随后同一客户端自动进入预冻结C8臂；目前派发16/24、完成14/24请求，覆盖8个唯一doc。C8已完成6/8，doc142、155仍生成，C1-after未开始。所有14个返回均HTTP200、非空reasoning及最终content、finish=stop/stop_reason=null，raw token数量与usage一致，均含think-end248069并以主EOS248046结束；completion_tokens 486–22621，无空最终content、真实HTTP失败、60K caps或length finish。不要把14次请求称为14道唯一题，或由此生成GPQA分数。

| doc | 首轮C1最终字母 / tokens | C8最终字母 / tokens |
|---|---|---|
| 142 | D / 16338 | 生成中 |
| 144 | B / 3734 | B / 4589 |
| 149 | B / 5349 | B / 6845 |
| 155 | C / 22621 | 生成中 |
| 151 | B / 781 | B / 2418 |
| 0 | D / 633 | D / 702 |
| 1 | B / 11311 | B / 11822 |
| 2 | B / 486 | B / 599 |

六条已形成C1/C8配对的最终字母相同，但完整文本和token数并非逐字一致；温度1且执行batch形状不同，不以固定seed推定所有中间数值/采样必然相同。不能用尚未完成的两条或未运行C1-after补齐A/B/A结论。原始结果、response raw及逐文件SHA仍在cohort-001各臂；12条新增结果的SHA/token/think-end位置写入state，原两条证据不覆盖。

health200，API/Engine/8 worker及原客户端存活，running2/waiting0、KV1.374%、preemptions0，累计generation tokens115140、最近约28.6 tokens/s；progress.json最近19:17:30、服务日志19:19:26更新。错误0、无invalid-page或worker退出，FINISHED未出现，未见停滞；已耗时1小时31分11秒，不估ETA。heartbeat保持ACTIVE，只监控现有任务。

当前能确认：原null目标在新实例首轮C1均有最终正文，C8已完成的6条也未复现；不能因此排除原C64持续进出、大block ID或长时间状态复用相关问题，更不能宣布index/KV-zero/compiler根因或修复。旧acc-012故障分数127/198与无有效gate状态不变，未启动全量GPQA、正式性能仍blocked。

### heartbeat 2026-10-15 19:23 +08:00：C8新增doc155正常最终答案

本次19:23:05只读核查为派发16/24、完成15/24请求（8个唯一doc）；首轮C1仍8/8完成，C8新增doc155后7/8完成，剩doc142生成，C1-after尚未开始。doc155于19:22:53返回HTTP200，completion_tokens=raw token数量=16438，think-end248069位于16193（0-based）、末token248046，finish=stop/stop_reason=null；最终正文明确 `The best answer is C.`，与首轮C1字母一致。原始 `cohort-001/c8/doc155-response.raw.json` SHA `92bebca347926fdffa1cd3dafd418d59817819f0f9d5691b454250f46aec0663`，对应result和events记录均保留。未从reasoning重计答案，未改原formal得分。

全部15个完成响应均有非空reasoning/最终content、正常think-end→正文→主EOS，无60K cap、length finish、HTTP错误或非法访问。七条C1/C8配对的最终字母相同，但仍无完整A/B/A结论。客户端PID、服务PID/start ticks/argv及requests SHA均匹配冻结身份，Engine与8 worker存活，health200；running1/waiting0、KV0.8242%、preemptions0，累计生成121293 tokens，服务最近19:23:05更新。最近25.2 tokens/s指标窗口跨过doc155完成，不当成单请求稳定速度或ETA依据。已耗时1小时34分50秒，无明显停滞，FINISHED仍无。

仅记录新增完成结果，不启动任何请求或改动。heartbeat继续ACTIVE；根因仍suspected-not-isolated，C64持续更替/大状态池/graph路径尚未排除，正式性能仍blocked。

### heartbeat 2026-10-15 19:53 +08:00：C8完成，进入最后一轮C1

19:53:13只读确认派发19/24、完成18/24请求、覆盖8个唯一doc；首轮C1为8/8、C8为8/8、C1-after为2/8，当前doc149生成。服务、客户端身份及请求清单SHA保持一致，未加请求或操作任何服务/源码。health200、Engine及8 worker存活，错误0、running1/waiting0、KV0.2892%、preemptions0，累计生成148312 tokens、最近14.9 tokens/s；最新progress19:47:59、服务日志19:53:13，无明显停滞。已耗时2小时4分58秒，不估ETA，FINISHED仍无。

C8最后的doc142在19:25:34结束，最终正文D、18886 tokens、think-end位置18658、末token248046，正常stop/null。全部8条C8与首轮C1最终字母一致，均有非空最终正文；这不是全量GPQA分数。随后同一客户端自动进入冻结的C1-after，doc142于19:43:46输出D/16338 tokens，doc144于19:47:59输出B/3734 tokens；这3个新增响应均正常think-end→正文→主EOS，无60K截断、HTTP错误或非法访问。全18个完成请求输出健康正常。

进一步仅离线读取已存响应，核验doc142/144的C1-before与C1-after**全部输出token IDs、parsed message完全相同**，三臂prompt_token_ids相同；并非只比较最终字母。token列表按紧凑JSON编码的SHA：doc142的C1 `9af89cf15d0951324e27c9a636714bfa11956b9d5380f665fb912bc99511d960`、C8 `c0e5996e233e0dc59b1f9dda0abd984c49398dad66dcde2f72eaba65f0e89431`；doc144的C1 `8f77fd9850a7f1403e425c04765abfe4a2d7f18a9b6f47f40b77c42b0c332dda`、C8 `39c1b8b5fc1ddd72a5bb352bed20bd13317408d871916f933e135f74d916b751`。C1与C8首个输出token差异分别在0-based16/39；这只定位为生成token轨迹已有差异，不代表已找到首个数值/算子分歧，也不能凭batch下不同轨迹认定bug。

新raw响应SHA：`c8/doc142-response.raw.json`为ba238d7773f3954b9b8ed812badfe2ad6c41984748c3fe0cf88a1310f8c3b5f7；`c1-after/doc142-response.raw.json`为8b2077efaa1a1c889d563974c12b6270a70567aa4c62869005b43b7e37dcfc0c；`c1-after/doc144-response.raw.json`为01ce32cfb58f17ed854ab2d60a5ad8980b5c6072cbd2b101101c8717e546377d。对应result/events保留，不修改原正式分数。

当前证据不支持“仅运行本次C8就会持续污染之后所有C1”的简单假设，但仍不排除原C64更大状态池、长时持续进出、metadata/graph复用或特定算子/编译问题。尚未完成全24条，也没有原异常的稳定复现；根因仍suspected-not-isolated，不作修复结论。heartbeat保持ACTIVE，继续只读监控，不自动扩C64、插桩、切Gems/compiler或重跑formal。

### heartbeat 2026-10-15 20:23 +08:00：最后一轮C1已6/8完成

20:23:46只读确认：派发23/24、完成22/24请求，覆盖8个唯一doc；C1-before8/8、C8为8/8、C1-after为6/8。当前最后一轮doc1生成，doc2尚未派发；服务端waiting0不能解释为客户端已派发完24条。新增C1-after结果如下，原始raw/result均保留在cohort-001/c1-after，对应SHA写入state：

| doc | 完成时间 +08 | 最终正文答案字母 | completion tokens | think-end位置（0-based） |
|---|---|---|---|---|
| 149 | 19:53:57 | B | 5349 | 4977 |
| 155 | 20:19:16 | C | 22621 | 22420 |
| 151 | 20:20:10 | B | 781 | 592 |
| 0 | 20:20:58 | D | 633 | 416 |

新增4条均有最终正文和非空reasoning、stop/null、末token248046，输出token数量与usage相等。仅离线读取已存响应，再次核验最后一轮已完成的6条（142/144/149/155/151/0）：各自与首轮C1的完整token IDs和parsed message完全相同，三臂prompt_token_ids相同。这里的相同不含response ID、时间戳等传输元数据，不把raw JSON SHA不同误称生成不一致，也不将最终字母视为正式评分。

全部22个返回无空最终content、HTTP错误、60K cap或length finish，均有think-end及主EOS。原客户端PID1634714、API PID1290447/start ticks/argv和请求SHA未变；Engine/8 worker存活，health200。running1/waiting0、KV0.1932%、preemptions0，累计生成175547 tokens、最近15.3 tokens/s，progress最近20:20:58、服务日志20:23:46，持续生成、无明显停滞；耗时2小时35分31秒，不估ETA。FINISHED未出现，原heartbeat保持ACTIVE。

没有发送额外请求、修改/重启服务或重跑GPQA。C64持续更替、大状态池和实际index异常仍未被该局部试验覆盖；原问题未复现、根因未隔离，正式gate及性能阻塞不变。

### 终态 2026-10-15 20:58 +08:00：24/24完成，未复现原症状

唯一客户端于20:33:53.493605结束，原生async回执exit0；从17:48:15.089817起耗时2小时45分38.404秒。3臂各8次请求、共8个唯一doc，24派发/24完成/0错误，所有请求均HTTP200、非空reasoning及最终content、finish=stop、包含think-end248069且以主EOS248046结束，raw token数量与usage全部一致；无真实HTTP超时、空最终content、length finish、60K cap或非法访问。总completion184805、prompt8541，与恢复服务的累计计数精确吻合；单次completion486–22621。

| doc | C1-before tokens | C8 tokens | C1-after tokens | 三臂最终字母 |
|---|---|---|---|---|
| 142 | 16338 | 18886 | 16338 | D |
| 144 | 3734 | 4589 | 3734 | B |
| 149 | 5349 | 6845 | 5349 | B |
| 155 | 22621 | 16438 | 22621 | C |
| 151 | 781 | 2418 | 781 | B |
| 0 | 633 | 702 | 633 | D |
| 1 | 11311 | 11822 | 11311 | B |
| 2 | 486 | 599 | 486 | B |

全部8条C1-before/C1-after的**完整输出token列表和parsed message逐字一致**，3臂prompt_token_ids一致；全部8条C8最终字母与C1相同。最终字母仅作响应比较，不是新评分。C8 token轨迹不同，温度1/batch形状不同下不能仅据此认定数值错误，更未定位首个算子/张量分歧。末两条C1-after为doc1于20:33:19.804532完成B/11311 tokens、doc2于20:33:53.462717完成B/486 tokens，原始响应SHA和完整token-list SHA已写入state。

20:53:40只读确认客户端退出，API1290447/start ticks477285377/argv未变、Engine/8 TP worker存活、health200、running0/waiting0、KV0、preemptions0，无新增服务错误。20:58:40的终态冻结再次核验相同运行身份、idle与完整源码/import/model/tokenizer指纹一致，不新增推理请求、不重启服务；8010保持运行。FULL/PIECEWISE capture已有记录，但本次未增加逐请求graph replay命中埋点，不以24次HTTP成功代替各graph路径的两次replay证明。

终态冻结成功：`case/diagnostics/accdiag-014-service-failure-20261015/terminal-freeze-001/report.json` SHA `5b99b0b16f003e7e4b006ed3e60d79b1e05733263b78a2b2c0592d57ff157aac`；`manifest.json` SHA `c1681790ea52ae1beaefbd7a16bd5cbf17b8c15197702626ac6ad45675dcd7a3`。冻结包括三臂raw/result、请求清单/事件/身份/终态、命令源码、恢复receipt、微测进度、源指纹及活动服务日志的固定字节前缀，旧证据不覆盖。原生 `cohort-001/FINISHED.json` SHA `f285c297db8ea35ba029445a8cab86afe628f7844efda06fa72e454c52ebf09e`。

结论遵循 inference-accuracy-diagnosis 的最小复现与根因证明要求：**not-reproduced-in-scoped-C1/C8，root cause not-isolated，无修复/回退补丁，无有效正式gate**。188个独立小池检查和本次24次API请求只削弱“小池独立算子必错”及“本次C8会持续污染后续C1”的假设；不覆盖原C64持续进出、高block ID、大状态池和实际metadata/graph复用。不能把恢复后正常认定为清零缺陷已修复，也不能认定nonzero为首个非法访问kernel。旧acc-012故障污染127/198与无有效gate保持原状，正式性能仍blocked。

已通过产品接口暂停原heartbeat `qwen3-8-ppu07-gpqa-c64`，不再自动发请求。下一步仅建议、未执行：经用户确认后另行冻结不超过128请求的C64持续更替局部范围，或针对大池高block-ID构建tensor复现；若需代码/运行时埋点、切Gems/compiler、重启或GPU单测，先明确单变量、隔离、回退及原始张量/索引/stride/bounds取证方案。未经新方向不扩展实验、不重跑全量GPQA。
