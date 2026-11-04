# acc-014：QSA PPU M16 + i64 当前服务全量 GPQA

## 授权与冻结契约

2026-10-17用户要求“跑下全量的GPQA的精度测试看看吧”，明确授权一次新的198题正式精度运行，取代旧局部实验的禁止全量范围。模式 `inference-accuracy-evaluation/formal-gate`，Skill bundle SHA `6e94a080dd3b64544c535e1fd4bda506f55516374d14d0f8ca6aa148bba2c7b2`。不改源码、不重启8010、不操作8035、不自动修复或重试整轮，不做性能测试。

沿用原生任务 `gpqa_diamond_generative_cot`、198唯一doc、limit0、C64，指标 `exact_match,strict-match`、阈值0.88。temperature1/top_p0.95/top_k20/min_p0/presence_penalty0/repetition_penalty1/max_gen_toks60000，evaluator seed42、API默认seed1234及原stop不变，API retries3/eval retries0/timeout7200。仅增加返回token IDs/prompt响应证据字段，不改采样或答案取值。

当前绑定PPU-07、`qwen3.8-flash-opt-ppu07-20261015`、8010/物理8–15 TP8，API4022615/start487850554；保留private017索引先转i64再乘stride修复和诊断埋点，只启private019 QSA PPU BLOCK_M16。8035保护基准4161238/start487889425，不操作。正式结果只代表实际带埋点环境，不能冒充无埋点候选。

已知[op019](op-019-fgvllm-integration.md)局部11请求/9唯一题中doc32最终A、goldB，53126token、正常stop/非reasoning-only；失败原证据保留不改写。用户本次要求收集完整分数，不意味着局部回归已通过或QSA因果已证明。旧acc012故障污染127/198和acc013原生0分不代替本轮。正式阈值未变，不使用排除None的辅助子集分数。

## 执行前记录

远端唯一case：`/mnt/nfs/users/jinghao/qwen3.8-flash/20261015-qwen38-flash-next-ppu07-container/accuracy/acc-014-full-gpqa-ppu07-c64-qsa-m16-i64-20261017`。

已验证inventory/connectivity，工作根owner0/mode700、可用7.4T，新case不存在；8010 health200、running0/waiting0/KV0，旧acc013评测容器仅tail进程，scoped客户端已终态。当前源容器ID、镜像和/mnt挂载须再由准备控制器逐项核验。新建CPU评测容器 `qwen38-eval-ppu07-acc014-c64-20261017`，规定镜像 `harbor.baai.ac.cn/flageval/flageval-llmeval:v1`，只复制数据缓存，不复用响应缓存。

执行副本与SHA：

| 文件（相对case） | SHA256 |
|---|---|
| commands/acc014.py | cc3f8fbec0d395f3681a66ee160fa7d24e9c4bd35a45ef056bf9740ce21f70bf |
| commands/source_probe.py | b31aa2f84b2d8bb67287fd1a1975a8ba2554a9160472a7551fcc9f50c98f93bc |
| commands/accuracy-bundle.tar | a10b0e94ecab12773e1785b71db7cbcbac07d1904ad92601ad94bd091cf185b7 |

控制器基于只读审查过的acc013实现修改实际服务/路径；AST检查通过。操作顺序：排他mkdir新case/commands，scp -O传输上述文件，在新bundle目录解包维护版评测入口和原始runner；`python3 <case>/commands/acc014.py --mode prepare > <case>/prepare.log 2>&1`只做CPU来源/两次task-data provenance/preflight和新评测容器准备，不发模型请求。PREPARED后一次性后台 `python3 <case>/commands/acc014.py --mode run`，CLIENT_LAUNCH独占、保存PID/start ticks与日志；控制器FORMAL_STARTED独占、先重验当前source/实例/idle。失败不自动再起。

原服务日志及观察器位于op019/service-qsa-001，新case保存字节边界并终态复制delta/state；旧003的scoped FIRST_ANOMALY不得当本轮模型异常。原生输出保留raw响应/token/finish，区分content None→TIMEOUT占位和真正网络超时。观察generic/packed索引分开，旧最大740不代表20972覆盖。任何实际服务异常只取证，不自动重启。

## 状态

14:12:50+08 PREPARED，两个provenance逐字一致且与历史正式数据revision一致，preflight明确no evaluation was started。service-manifest SHA `5935e6bca1f514ffe4fe639fbd2869b0e2a2e2d4ae7f308281a1c65a684239ba`，contract SHA `4baba76baa719d9559e31139160ab46c6fb12eb306cebf9229c0fb815ebb3134`，source-before SHA `3d867b04575dc9a941660b8d36b205c753cddb84305d4c7308e7a434e3501fe8`；实际Plugin/private017 Gems/FGVLLM导入解析和i64文件SHA均符合当前候选。

新增唯一启动副本 `commands/launch-once.py` SHA `c6e88ac05e0284a25ee83e49dd895d1223d5facd422d953357206e557afbbeb3`，执行命令 `python3 <case>/commands/launch-once.py`；只创建CLIENT_LAUNCH独占marker并启动已有准备通过的控制器，不向服务发额外测试流量。服务身份和source由控制器再次重验。

score/gate未知。复用 `qwen3-8-ppu07-gpqa-c64`，30分钟仅实质进展/失败/停滞/完成通知，终态暂停。终态检查198唯一doc、完整服务及源码绑定、原生results/samples；仅有效完整证据且分数>=0.88签发gate，低分记failed，不完整记incomplete。

### 唯一正式启动

14:13:52+08唯一启动控制器Host1300183/start493345890，14:13:54写成FORMAL_STARTED；前置实例、source与idle检查通过。没有重启/修改模型、没有操作8035。`qwen3-8-ppu07-gpqa-c64`产品工具已确认ACTIVE/30分钟，新prompt仅只读监控acc014，不延续旧scoped请求或性能任务。

14:14:09原生runner已建立198请求，独立UUID `cc5ca1bee0f843b7a53fdf021cdcaf6e`，缓存命中0、remaining198，日志明确concurrency64及原采样/gen_kwargs；context构建198/198不是完成198题。结果尚未生成，不估ETA；运行期间不重复启动。

14:14:49 health200，running47/waiting17、KV5.46%、preemption0；控制器/8010/8035三个当前PID均在，已确认真实模型流量进入当前服务。该在途数不当已完成唯一题数。当前无最终分数。

### 14:44–14:48只读监控：首次真实generic大索引跨界

运行约31分钟，控制器/原生evaluator/helper均在、8010 health200、running64/waiting0、KV32.01%、preemption0，当前实例及8035未变。只读SQLite键→doc映射确认88唯一doc、未知key0、非字符串0、TIMEOUT占位0，阶段strict86/88（97.73%，非最终分数），已完成错误doc17/106。随后原始返回日志独立核验90个唯一response：90均最终content非空/stop、think-end与EOS完整、返回token长度与usage相等、无60K cap/reasoning-only/已见HTTP错误；与缓存快照时刻不同，不混用分母。最近原生日志持续更新，未终态，不估ETA。

8rank实际generic gather/scatter已超过20972，第一份保全的索引为21508、step64410、layer0；后续最大21688，row stride102400。21688的i64行偏移2220851200，反事实i32为−2074116096，正确字节区间[8883412480,8883805696)在storage27372339200内。实际实现64位，i32_overflow仅反事实，不当新故障。8rank均已自动保存first-i64-boundary的gather/scatter before/after JSON及PT，共64文件，after selected-row mismatch=false；目前无FIRST_ANOMALY/STOP_DISPATCH或服务illegal-access。packed实际设备索引另按device-replay-observation.layers[].actual_indices统计，不以generic值或scheduler ID代替。

追加仅复制既有证据的CPU脚本 `commands/freeze-boundary.py` SHA `2e067e8f40fa457f41dd3d2afa0f46b5cb80530835a81cf3b11f05b345d912e4`；执行 `python3 <case>/commands/freeze-boundary.py`。排他新建 `diagnostics/first-i64-boundary-freeze-001`，校验8rank边界64文件及64位/合法storage/after数值结果，复制已有8rank+rank-1日志固定字节前缀、当前服务/评测日志前缀和冻结配置/来源，保存manifest及SHA。无框架导入、无GPU/推理请求、无信号、无服务或客户端变更；在途最终回复未返回不补造。原生日志包含完整返回dict/token，不等同HTTP原始wire bytes；selected rows不是完整pool或36层独立现场。

复制及独立校验完成：84个文件、1495771871 bytes，SHA/大小失败0；report SHA `5454f89279bddb7062a519fddb52afbb5b430f496d5d9c66a75938850b53bd05`，manifest SHA `23ed14718076b79fb4b837a42de661d54286924485ba976af00a0c68a90a291b`。冻结日志含94份已返回dict（最终content均非空，最大10416token），不是94份HTTP原始wire文件。最早保存before为rank3/14:44:04.242378，索引21508，i64 offset2202419200 vs反事实i32 −2092548096，正确byte区间[8809684480,8810077696)合法。rank0 step/batch-binding可将其join到slot63/request `chatcmpl-ba2be3aa9c26c833-950b5367`，该请求371 Prefill tokens、全batch434tokens、graph NONE；与此前实际FULL replay记录分别归档，不称此大索引gather本身在FULL graph里执行。首次正常跨界已通知，不当异常、不停止正式评测。

14:48:06–07最新只读缓存映射**97/198唯一题，strict95/97（97.94%，阶段分数）**，错误doc仍17/106，未知key/非字符串/TIMEOUT均0；当前running64/waiting0、KV33.73%、preemption0。8rank packed实际device indices最大20148（未跨20972，不能用generic21688冒充packed覆盖），记录的invalid/nonfinite均0。服务、8rank日志和评测继续推进，无终态，无最终score/gate；保留带同步/埋点及selected-row的结论边界。监控保持ACTIVE，不追加/重试请求，不修改或重启服务。

### 15:14只读监控：首次reasoning-only/EOS证据

`inference-accuracy-diagnosis`仅做既有证据冻结，issue `acc014-output178-EOS-before-think-end`、分类request/output-health，根因尚未隔离，不因单条输出健康观察中断正式评测或签发失败gate。全量运行约60分46秒，15:14:40 SQLite键→doc映射确认148/198唯一题、未知key0；含1非字符串doc178（goldA），其余147字符串中143匹配，完整已完成分母的阶段值应记**143/148=96.62%**，不是helper排除None后的143/147；TIMEOUT字符串占位当前0，原生结算可能随后把None转为TIMEOUT。错误字符串题17/106/167/157，另加doc178空输出未答对。尚无正式results/samples/终态/gate。

首次排他marker原件时间14:59:49.4026656、rank2、step71363，kind `EOS-without-final-token-prefix`；STOP_DISPATCH独占由rank3写于.4026697，不是第二次异常。API response `chatcmpl-a0badf277fe2dcc8`，engine request加后缀`-b5d2b08d`。HTTP正常返回、finish stop、stop_reason null、455 prompt tokens/24 completion tokens，content None；完整reasoning为“| \nThe lines in the reference lines indicate that the reference lines represent lines, and the reference lines represent lines.”。完整API输出token为`[91,695,760,4965,303,279,5604,4965,12832,421,279,5604,4965,3875,4965,11,321,279,5604,4965,3875,4965,13,248046]`，无think-end248069，直接EOS248046。**不是60K截断、不是网络超时、不是仅评分器漏取一个已经存在的最终答案。**

故障请求step71340 Prefill455tokens，slot63；异常EOS时step71363、FULL graph/64tokens/64requests。8rank已各写first-state manifest+36个PT，共296文件，仍是有界selected rows及共享pool last-writer，不是36层独立因果历史。8rank最新generic gather/scatter最大36088，stride102400、i64偏移3695411200/反事实i32 −599556096，合法byte区间[14781652480,14782045696)，storage27372339200；packed实际设备索引最大36081。已记录invalid/mismatch/nonfinite均0，未见illegal access或服务错误；大索引覆盖与本次EOS异常并存不能直接证明两者因果。

15:14:24服务health200、running50/waiting0、KV56.01%、preemption0，控制器/eval/helper和8010/8035实例未变；最新原生日志15:14:11。148个已返回dict中147 content非空、148stop/终止EOS、147有think-end、完整token长度均匹配usage，最高22437、60Kcap0、真实HTTP错误0。观察器STOP_DISPATCH仅保留原marker；本轮正式runner继续完成原198题，不人为停止或重跑。

追加CPU仅复制脚本 `commands/freeze-output.py` SHA `d74f9176cc309a30704c0715a5f9be9e223777591664bb8d2611c163f64ce6e1`，执行 `python3 <case>/commands/freeze-output.py`，排他创建 `diagnostics/first-output-anomaly-freeze-001`。核验8rank已保存manifest对应文件大小/capture_error，复制原marker、全部已有state及日志/配置固定前缀，保存原response日志行/返回dict/完整token/prompt、rank0实际非discard采样前缀并比对API；保存manifest/SHA。无额外推理、无框架/GPU导入、无服务或客户端操作，不改源码/采样/旧证据。原始HTTP wire bytes没有采集，返回dict不可冒称原wire；未返回在途回复不补造。现阶段仅支持症状与生成边界已确认，不支持QSA/i64/graph/cache根因已确认。

冻结完成并独立重算318份副本SHA/大小全部通过，3102191129 bytes；8rank manifest对应288个state文件齐全、capture_error0。report SHA `4f365c1b23175be7139b47c27080d90f98b92dbfd305c8188e7faa6aea9c1690`，manifest SHA `f13e71c399961719d1cb792278e5e825359577a9041ed3c61490c748f716bdd6`，返回dict SHA `655bb31536989da8cb3aeb35f1adb551f185762c17a4be9ddb48175a6f40166f`，原始response日志行SHA `c0e96ce4e93d345eabef69960ddefb8aa62886a272e91089c22ad2e0a0096d9a`。rank0非discard采样前25token中的前24与API完整输出逐项相同；多出尾token198是post-sampler/pre-bookkeeping记录、不一定发出，不能当解析损坏。**异常输出在实际采样前缀已存在，非评测器凭空造成；首次数值分歧层和触发因素仍未知。** 当前服务可读完整日志固定前缀已保全，没有另采全机driver/dmesg，不冒充完整底层driver现场。

15:17:15再核验health200，无FINISHED/CLIENT_ERROR；i64 index/index_put、观察器、QSA adapter和PPU QSA实现5个当前文件SHA均与已冻结版本一致。监控继续ACTIVE，保持原正式运行至终态，未发送额外推理/重启/停止或修复操作；本条reasoning-only不单独决定正式gate，最终仍按完整198题strict-match与0.88判定。

### 15:44–15:45只读监控：175唯一题、无新增输出健康异常

本轮已运行约90分43秒。15:44:37只读SQLite键映射确认175/198唯一doc、未知key0、非字符串仍仅doc178、TIMEOUT字符串占位0；正确字符串163，错误字符串11题（17/106/167/157/171/89/113/69/160/59/14）。计入空输出的全部已完成分母，阶段strict为**163/175=93.14%**，不得用163/174的排空None子集代替；尚非最终分数/gate。

175个完整返回dict核验：175均stop/EOS，174最终content非空且含think-end，175完整token数与usage相等，最大39209token、60Kcap0；仅有此前doc178的24token异常，未见新增reasoning-only、真实HTTP失败/超时或服务illegal-access。旧FIRST_ANOMALY/STOP_DISPATCH原件未变，318份冻结证据不重复执行或覆盖。

15:44:24 health200，running23/waiting0、KV50.06%、preemption0，控制器1300183/start493345890、API4022615/start487850554及保护8035 PID/start均未变，评测wrapper/evaluator/helper正常。最新原生日志15:42:57（11942221bytes）；helper最近写15:35:21，因为按10题间隔输出而非服务停滞。剩余23题为30/32/48/55/71/76/79/81/88/90/93/94/121/126/127/130/138/145/147/164/168/185/186，不能因doc32较长就提前判60K截断，也不估ETA。

基于首次输出freeze manifest中每rank原inode及字节边界，只读解析之后的新日志：8rank均持续推进，step约95344–95386；没有新增generic prefill gather/scatter事件，累计最大仍36088，已记录i64合法byte区间和反事实i32偏移保留。此增量窗口packed实际device indices最大27539，累计历史最大36081，两者不是矛盾；增量invalid/nonfinite/mismatch均0。没有新的异常需要再冻结，不新增脚本/推理或服务操作；正式未终态，监控保持ACTIVE。

### 16:14–16:15只读监控：190唯一题、剩余8题

已运行约2小时49秒。16:14:43只读SQLite键→doc映射确认190/198唯一doc，未知key0、非字符串仍仅doc178、TIMEOUT字符串占位0；正确175、错误字符串14题（新增76/185/32），完整已完成分母阶段strict **175/190=92.11%**。helper的175/189=92.59%排除了None，不作本轮分数；尚无正式results/samples/FINISHED/gate，不提前宣布通过。

16:14:26 health200、running8/waiting0、KV25.40%、preemption0，控制器/原生evaluator/helper正常，8010及8035原PID/start未变。剩余doc79/88/90/127/145/147/164/186。190份原始返回dict均stop/EOS/token数匹配usage；189有最终content与think-end，仍只有已冻结的doc178异常。当前已完成最大57598token但没有60K截断、真实HTTP超时/失败、服务illegal-access或新增输出健康异常；不能将长生成预判为截断。最新原生日志16:12:34（17965862bytes），helper16:12:29。

16:15:04各rank最近4MiB日志只读抽查均在推进，step114180–114184；没有新的generic事件，累计已核验generic36088及对应i64地址合法性保留。rank1–7近期实际device indices最大27239，rank0近期actual_indices未重复打印，记未观测而非0；累计历史packed36081不因此降低。近期尾部invalid/nonfinite记录均0；这是尾部窗口核查，不冒充整个30分钟逐条重验。无新异常需重复冻结，保持原正式运行与heartbeat ACTIVE，不追加请求/重启/修复，不估ETA。

### 终态核验（2026-10-17 16:44起）

原生结果16:32:29.775写成，控制器16:32:53.422自然FINISHED，exit0、same_service/source均true。198唯一doc、每个filter198行/共396行；独立解析strict198条求和**176/198=0.8888888888888888（88.89%）>=0.88，正式精度passed**。这不是helper的子集得分。模型API4022615/start487850554及8035原实例保持，控制器/evaluator/helper均已退出，8010 health200、running/waiting/KV0、preemption0。CPU只读重新调用已冻结控制器的runtime/source检查当前实例与源码内容，均与before一致；维护版`acceptance.py check --gate <case>/evaluation/accuracy-gate.json --service-manifest <case>/services/service-manifest.json`退出0并报告PASS。

相对case的原始结果目录：`results/Qwen3.8-Flash-Next-ppu07-acc014-c64-qsa-m16-i64/cc5ca1bee0f843b7a53fdf021cdcaf6e/gpqa_diamond_generative_cot/Qwen3.8-Flash-Next/`，文件`results_2026-10-17T08-32-29.775464.json`及`samples_gpqa_diamond_generative_cot_2026-10-17T08-32-29.775464.jsonl`。run-record在该UUID根目录；gate为`evaluation/accuracy-gate.json`。

| 证据 | SHA256 |
|---|---|
| results | 5c2ce1dac0401fa84e129595682370730c1119a594cd468bccd9515fe26d2d88 |
| samples | 0dae6ab02aa800c59cc63c2c80f16638fed57620414f140b750adeec1af0ced8 |
| run-record | 12359ec190a8b652e6741cffad399910e3d47cbb0a0d785e081221d6addd2030 |
| accuracy-gate | 0bd69d0561a8fd3906095ea41bab47e8e8063214f07efe60c0a68f8053abe133 |
| FINAL_SUMMARY | d124ef375b6b7b371fcb74db30a3e4719af9f09529648acfa7fe04dca7f37785 |
| observer-manifest | 683906c3b2ccda5462fe5a23cf1306848a79d0b23b309a56e40effad13e7ecbc |

输出健康仍有问题：198份完整返回中192stop、6length60000；191最终content非空且有think-end，7题content None。6个截断doc79/88/90/127/145/164均只有reasoning、无think-end/最终答案；另doc178为此前24token提前EOS。原生samples的7个`<TIMEOUT>`对应这些API空content，**真实HTTP/网络超时0，不能报告成7次网络超时**。原生日志未见illegal access。严格错误22题为14/17/32/59/69/76/79/88/89/90/106/113/127/145/147/157/160/164/167/171/178/185，包含7个空输出，不删掉这些题再报分。最终helper出现198/198 matched0，是结算后的缓存值结构已非其safe-string解析形式，不是模型0分；以原生results/samples和有效gate为准。

追加仅CPU证据审计副本`commands/terminal-audit.py` SHA `85ef5f09b68948076a49a60547faac7375a9b747521ef19f8ce2fefcf59351c4`，命令 `python3 <case>/commands/terminal-audit.py`，排他新建 `diagnostics/terminal-audit-001`。逐一将198原始返回prompt/token与native doc对齐、单独保全7异常的原始日志行/返回dict和完整token，验证控制器380份observer拷贝SHA及8rank已有state文件大小/capture_error，记录终态manifest/report。只读原始证据、不改gate/原分数/原marker，零推理/服务操作；没有HTTP wire bytes，不冒称有。保留原有首次异常与大索引freeze不覆盖。

本轮gate只绑定当前QSA M16+i64、诊断同步/埋点、TP8物理8–15的8010实例；精度阈值通过不等于reasoning-only已修复，不证明任一改动独立收益，也不是无埋点环境或性能验收。终态归档后暂停原heartbeat，等待用户方向，不自动修复/重启/重跑或继续性能测试。

终态审计完成：198个原始返回prompt一一join到198个native唯一doc，完整token/usage一致；本轮2383588生成tokens、79715 prompt tokens恰等于服务累计计数扣除之前11条scoped流量（2479000−95412、83656−3941），没有监控额外推理。380份observer副本共3851620045bytes独立重算SHA全部通过；8rank manifest对应288状态文件无missing/size/capture_error。terminal report SHA `f9da89cb7b882e870dce879685986807da63484ef2e25a88a7cbc5a7ed47aa5a`、manifest SHA `4a2032cf92068cef74948f186908f9de6100c990ee93f064dbd3d3e25eba5fe4`；22份终态引用（含7异常原始日志行/返回dict、完整token）再次独立校验0失败。总耗时8339.364秒，即2小时18分59秒。

`qwen3-8-ppu07-gpqa-c64`已由产品工具确认**PAUSED**，保留原名称/频率/prompt，不再自动跟进。当前精度gate有效，但输出症状未解决；下一步等待用户选择，不在本次只读监控中继续复现、修复、重载、重跑或性能测试。原acc012/013及局部017/op019结果仍按原事实保留，不被本轮passed覆盖。

用户后续授权的7题离线定位见[accdiag-020](accdiag-020-output7-offline.md)：6个60K截断与doc178短退化/EOS区分；doc178首轮异常输出来自graph NONE的混合Prefill采样，864次GDN搬运/清零/写回检查、288状态PT和last-writer实际索引对应通过，但没有首token逐层数值/logits/概率证据，根因仍未隔离。本轮新增推理/埋点/重启均0；原分数/gate不变，需要加埋点或重载先告知用户。
