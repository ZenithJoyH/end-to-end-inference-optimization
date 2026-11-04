# accdiag-027：doc71/81同前缀logits及think-end概率对照准备

用户2026-10-18明确要求继续同前缀对照，不跑全量GPQA、不影响8035；新增埋点/重启8010必须先告知。采用inference-accuracy-diagnosis，本轮先做只读能力核查和CPU前缀冻结，**尚无新增埋点/服务变更/推理请求**。原正式164/198 failed-score/no gate不变。

## 当前能力与授权边界

按inventory限定PPU-07并验证连接。只读核验8010 Host3094123/start502592140/argv5744d999及8035 Host4161238/start487889425/argv91849d0b精确未变、双health200。现有025 probe-config在进程导入时加载，full_capture_target_prefixes仅原doc178 seq73/119，ARMED025只在真实63Decode+455首次Prefill时激活；不能改旧config或借旧header把doc71/81伪装成已授权目标。该配置无已证明安全的热更新入口。

当前vLLM默认logprobs_mode=raw_logprobs、max_logprobs20；普通completion/chat接口支持logprobs/prompt_logprobs，但无逐请求切换raw_logits参数。原始logits与温度/penalty/top-k/top-p后的真实actual_probs是不同边界，不能将top20 logprobs缺少think-end当其概率为0，也不能以API诊断logprob冒充真实采样概率。现有021基础hook确有raw_logits/topkp_entry_logits/actual_probs/noise/RNG保存能力，但当前focus不覆盖71/81，完整采集需新增窄范围observer并仅重载8010；**没有执行此动作，须待用户确认**。

CASE=/mnt/nfs/users/jinghao/qwen3.8-flash/20261015-qwen38-flash-next-ppu07-container/accuracy/acc-015-full-gpqa-ppu07-c64-current-i64-qsa-20261018。拟CPU新建CASE/diagnostics/accdiag-027-same-prefix-logits-20261018，仅冻结旧raw token前缀、SHA和比较契约，不生成模型结果，不覆盖026/025原件。

## 先冻结的对照与证据要求

取doc71历史acc014正常A54281与025的60K；doc81取022局部正常D47578与025的60K。按原prompt IDs逐个相等核验，计算输出最长公共前缀。冻结prompt-only、首次差异前共同前缀和正常轨迹think-end前位置；末者同时保存正常/不收敛两支的同长度前缀，明确两支上下文不同，不能当同输入A/B。

真正同前缀比较要求**每个完全相同的token ID输入**分别在C1与实际Mixed中重算（并有重复控制），不让自由生成在首个分歧后自行漂移；可以原始token ID completion输入避免再次chat-template渲染。评分max_new_tokens=1是诊断差异，不改模型常规采样/stop；fresh-prefill评分不等同旧完整Decode历史或旧RNG offset。初始短前缀对照不能单独证明54K附近收敛行为或原C64根因。

若获授权，建议先仅8010一次重载加载**采样边界窄埋点**，不抓全部背景/逐层巨量张量；保留017 i64/QSA M16和模型数学。短前缀4点（2题×prompt-only/共同差异前）C1各2次共8评分请求；再7背景Decode加4目标依次准入Mixed C8共11请求，合计19、硬上限32/C<=8/0重试，不自动补发以凑覆盖或扩大长上下文/C64。每点保存完整raw logits、温度/penalty后topkp入口、实际过滤后prob、248069及EOS的raw rank/logit/logprob/是否被过滤、实际noise/RNG、真实输入/位置/slot/graph绑定及原始HTTP/token。首真实异常停补位、在途自然取证；8035精确保护漂移时不操作其他服务。长前缀/C64另按结果冻结差异与预算，不自动展开。此为待批准方案，非已执行测试。

CPU前缀准备脚本和SHA在执行前补记。现有heartbeat保持PAUSED；本阶段无后台推理任务，不创建新监控。

已保存CPU脚本`CASE/commands/accdiag027-prefix-prepare.py` SHA `342b48eaa9e826d625f8166a6ee7b09815841de9d672b76c1710bf27ce886adf`。本地py_compile通过后排他传输、核SHA，执行`python3 CASE/commands/accdiag027-prefix-prepare.py`一次；只读025的71/81 raw与历史正常回复/原始native日志，排他生成prefixes.json/manifest，不发送HTTP推理或修改probe-config。此步骤不消耗模型请求预算。

## 已冻结前缀；尚无新logits结果

prefixes.json SHA `91ce05aeb534073d0e970a34c7ec7599dac9de9d3b829cbe40edbd50130a43b8`、manifest SHA `df807be94c9d791897d57ea45f6240a36094d454a80927045be8cd8e6a67d805`；manifest独立大小/SHA核验通过，保存8个精确token-ID输入（4短点、4长分支预留）。历史正常不是同环境数值reference，当前没有新评分/概率测量。

| doc | 原prompt tokens | 正常/60K输出最长公共前缀 | 首个差异token（1基） | 正常轨迹think-end位置（0基） | 长前缀总输入tokens |
|---|---|---|---|---|---|
|71|343|10|11：4543 vs14235|53996|54339|
|81|778|30|31：494 vs13|47308|48086|

doc71正常源为acc014 native日志第623行，完整日志SHA `b1e2a46ce6a42a689cd66baf01a18db5bda97d4d4c16f24237d85d4d2ad4b81c`；doc81正常022 raw SHA `962e7059bdff59690e28a1f8a79ea602fe0445052a4f92c5a147e1b4f6a54ab8`。两题坏响应SHA9417307f/2d0efc42与025绑定相同，prompt IDs逐个一致。短点精确总输入为doc71的343/353、doc81的778/808，不通过自由生成制造“同前缀”假象。长正常和长失败分支长度相同但内容不同，不作同输入A/B。

现有服务未显式设置--logprobs-mode/--max-logprobs，采用当前代码默认raw_logprobs/20，不能无重载切换到完整两级采样边界。0新模型请求/0服务信号/0probe或源码修改；已向用户说明需要仅8010新增窄埋点并重载，等待明确确认。提议首阶段19请求、上限32/C8、0重试，不自动扩大长前缀/C64或全量GPQA。旧监控保持PAUSED，8035仍精确原绑定健康。

## 用户新授权执行契约

用户随后明确允许**仅8010窄采样埋点并重启一次，19请求、并发<=8**。该指令替代上文待批准/32预留预算，硬上限收紧为19，不自动扩大。使用当前027目录新增runtime-001；旧CPU前缀原件不覆盖。新私有目录/opt/qwen38-accdiag027-sampler-20261018，复制025 Plugin完整字节，保留i64/QSA M16、权重/engine/采样数学及原8010 argv。旧源码与launch保留为回退材料，但本轮不自动第二次重启。

固定8评分C1（4短前缀各2次）→7背景原始token-ID prompt、输出上限512用于维持Decode→4评分按真实7Decode逐条准入Mixed C8，总19。评分max_tokens1/原temp/topk/topp/seed/penalty，completion token-ID输入不再渲染模板。背景512的length是预冻结负载结束，不冒充GPQA故障或正式评分。背景正常提前结束导致后续Mixed不覆盖时停新增派发、自然取证，不补位/延长/追加。graph两类capture7/7与至少两次实际FULL回放由已有19请求核验，不发隐藏smoke/warmup。

窄observer沿用025注册tap/legacy索引与bounded graph证据，但背景ACTIVE恒空、不装021逐层GDN/QSA转储。只对12评分opaque请求保存每rank实际device input/positions/logits_indices与真实req/row/computed/scheduled/graph，rank0完整raw logits/topkp_entry/actual_probs/noise/RNG/真实sampled/discard；不改变任何输入或返回值。rank0预算128MiB，其他rank仅小输入PT；全层tap保持原字节但无ACTIVE时no-op。首输入绑定/非有限/概率支持/实际noise采样不符/HTTP/服务异常，排他marker停止补位，在途自然收集。C1和Mixed有限logits差异只记录、离线量化，不将普通batch差异未经阈值证明认定算子事故。

部署、CPU正反例、完整source/image/mount/current idle和8035精确保护门禁均须先通过，脚本/launch SHA保存后才停止旧8010。仅向精确核验的8010 API发SIGTERM等待原树退出；若不退出则报告、不自动追加kill或再次reload。重载后新namespace日志PID不当Host身份，READY绑定listener/8worker实际probe来源。没有新正式gate，旧164/198失败分数保持。必要时复用原heartbeat仅监控本轮唯一driver，终态暂停。

### 冻结执行副本（执行前）

| CASE/commands脚本 | SHA256 |
|---|---|
|accdiag027-probe.py|3324ec99bfb4263fab7dfd407f3a2c1572ac744cfab375998f8fa7d44dbc46f4|
|accdiag027-deploy.py|693872f9cd3ebc7abde4a8a151ac5a984dbdd290775454c83146549e3d30cb73|
|accdiag027-control.py|6d655909d6e706da967169dd8dd8ea7fcde06f1e3b1892d8557512660a5f6b08|
|accdiag027-cpu-test.py|3f6834c307d5b19a4ad487d4d639e1b34631cbe26292ffc52fc7f838770080de|

本地py_compile指定/tmp cache通过。排他上传核SHA后，先既有eval容器CPU（CUDA_VISIBLE_DEVICES空、OMP/MKL1）执行`python3 CASE/commands/accdiag027-cpu-test.py CASE/commands/accdiag027-probe.py`；CPU测试只AST提取纯检查函数、不加载probe/vLLM/模型。通过后Host `python3 CASE/commands/accdiag027-control.py --case CASE --mode prepare`一次（0重启/0请求），核PREPARED/source/launch后才`--mode restart`一次、`--mode launch`一次。唯一driver自动wait→8 C1评分→7背景+4 Mixed评分→自然drain/freeze，无隐藏预热请求。发生门禁或诊断客户端错误时保存并报告，不自动第二次重启/重发。

17项CPU正反例已通过（非设备证明）。首次prepare在旧017背景请求清单缺少target_prompt_token_ids时KeyError，停于新runtime-001/before.json，尚未写requests/config/deploy/launch，0私有部署/0重启/0模型请求；原件保留。修正版仅修准备控制面字段读取，改从旧017原始回复核对prompt_text后取prompt_token_ids；不重新分词或改题。新`CASE/commands/accdiag027-control-v2.py` SHA `d9a7d0b9718912d3d1fe46051762b6e5baba5fc4d55cca5beaec4b32261d1696`，当前运行目录切至同027的runtime-002，旧准备目录不覆盖。依次各一次`python3 <v2> --case CASE --mode prepare`→核SHA/source→`--mode restart`→`--mode launch`，原19/C8/单次重载/零重试不变；这不是模型事故或模型请求重试。

runtime-002 prepare通过（尚0重启/0请求），image67309a95/mount-parity逐项passed、完整旧source trees不变，新Plugin字节同025；probe3324ec99/model eb9f096d/runner c3537353、017i64双SHA与QSA M16 3bb3d083匹配。PREPARED `8b67f8abe2c8a01aa3128c5f65cdfbe2f0e15695a9b666301deff4e8ea835973`；requests `d007a7a3ea524dadc9ac2fac63560d432e65ea7eab61fe3b3efffc37cc609f3a`；config `02beb77e6f15a8c55327f4349b9f599a9a7bd617807de966ef638e466123af4f`；launch `fbbd0cecceb0b010b87528465a9e9740f79576fbc556c4d8a0823030bd91fb69`；DEPLOYED `3d80b739df9aa1550c152ef6d1a2cc13e99f1acb86c91eb2f410235574226426`。19=8 C1评分+7背景512上限+4 Mixed评分，所有原始tokenIDs/长度已核。8010/8035旧绑定和8010 idle已再次核验，接下来只执行已冻结v2的单次restart，再唯一launch，不重复prepare/部署。

## 保护基准变化，0/19请求停止（未重跑）

19:28:50.873216+08 RESTART_STARTED仅含旧8010树，保护8035 PID4161238不在树中；仅向旧8010 API3094123发一个SIGTERM，19:28:52.914584旧树自然退出、无其他信号。19:28:54.593856物理8–15每卡1MiB资源门禁通过，8035精确保护门禁再次通过后19:28:54.623091新8010启动。只重载一次、未重启容器。

唯一driver3221996/start503882387于19:29:57启动即发现8035无监听，19:29:57.421480在ready入口按保护门禁退出；19:30:44及19:32:47复查旧8035 PID不存在、端口无监听，原因尚未建立，不能自行认定为本任务造成或用户预期操作。**RUN_STARTED/READY/任何req raw均未生成、0/19派发、无新logits/概率结果**。不放宽门禁、不续发/重试/再次重启8010、不操作8035。已立即通知用户，请确认8035变化是否预期后才能考虑更新保护基准。

FIRST_ANOMALY SHA `d124dc2f757bbdb9be22609212044d3f95761f3add2265e1438a56c8db84586b`为controller-error（8035保护漂移），非模型数值事故；CLIENT_ERROR `1bdabc1705ccefdf06727925f8596efb3236b0cb557c4202fbe0c920673125bc`、FINISHED `535d13c83929d93b4c132f585881cb249b7082978ac5bb3aeb01bee32b67b48b`原件不改。第一次自动freeze发生于worker日志尚未创建时，FREEZE_ERROR `c07dbafd5db6672d43833094f0518cb203a727d0297306063322565a42bbebdf`明确保留，无FINAL_EVIDENCE，不伪造CLIENT_FINISHED或完成19题。

后续19:32:47只读可见8rank新probe3324ec99来自私有027 Plugin，均step0、权重加载完成、graph capture进行中，未见非法访问/RPC/Worker异常。8010尚未监听是启动阶段，不直接判服务故障。driver已退出，不能再调用launch/run/restart。源i64/QSA字节仍需在单独补冻中核验；未实际采样，不能声称窄采样设备验证通过或根因已定位。

仅CPU补冻脚本`CASE/commands/accdiag027-guard-freeze.py` SHA `eb84e7cf3be4937e3828a95e719f54db7261a4adaf28b2a5273853104e8c04b1`，执行`python3 CASE/commands/accdiag027-guard-freeze.py`一次；排他创建runtime-002/post-driver-guard-freeze-001，只复制已有第一marker/原请求清单/启动与错误日志/8rank已有事件字节前缀，核当前服务身份/health/源码SHA。无推理、无GPU测试、无guard重绑/源码修改/重启，不补造未执行的logits/HTTP/token。旧监控保持PAUSED，等待用户方向。

### 补冻完成，等待8035基准确认

补冻report SHA `f0adee789869a8a8a2c0abca2630d3761ef422213fecc2aa10b26fd95b106b2c`、manifest `7a82452e0e15300dbbbba871bf608d40d4047d922320cd887637b0b8c45bdb54`，28个已存在文件前缀独立复制SHA均匹配，不改旧FREEZE_ERROR/FINISHED。新8010 Host3199246/start503876115/原argvSHA5744d999，health200、PIECEWISE与FULL capture均7/7；8rank probe3324ec99来源已核，但executed_steps均0、无sampler PT，**不能宣称两次实际replay或窄采样设备验证通过**。017 index15ddfe41/index_putd8422ca2与QSA M16 3bb3d083当前文件SHA匹配。8035仍无监听，未擅自更新保护基准或操作该服务。

额外只读dmesg当前可读环：未见OOM匹配，存在旧PID4161238的PPU上下文释放记录（工具显示19:28:27.772+08）。该显示时间与稍后保护检查存在时序解释差异，且上下文释放不独立证明用户操作/进程退出原因；不据此给8035停服定因，也不隐瞒该记录。确定的本任务信号范围只有旧8010 API3094123单次SIGTERM，8035不在旧8010后代树。重启次数1已消耗，控制器已退出且未派发，当前19请求预算仍全未用；后续须用户确认8035状态变化是否预期，再决定保护基准和同实例续跑，不重复launch/run或重启。原正式164/198 failed-score/no gate及根因not-isolated不改。

## 用户确认8035预期停服，同实例续跑（执行前契约）

用户明确确认旧8035停服预期，授权更新保护基准、**不再次重启8010**、只续原19/C<=8/0重试，保留i64/QSA M16、首次异常完整采样与HTTP/token证据、不跑全量GPQA。本次inventory限定PPU-07；connectivity首次因本地sandbox RPC无法启动失败，按原脚本提升权限重跑后连接门禁通过，非目标机器故障。只读发现8035已由新PID3460404重新监听，不把它设为“可操作停服”；准备时冻结当前精确start/argv为保护基准，后续漂移停新增请求，不向该服务发信号。

续跑控制面脚本`CASE/commands/accdiag027-continue-v3.py` SHA `24ac6e67413638c1cb82fc2596758e9b68cab3921a1ea61dc098975342cb60ce`，本地py_compile通过；排他上传核SHA后依次仅各一次`python3 <script> prepare`（0请求）→核PREPARED/保护身份/原requests SHA→`python3 <script> launch`。新客户端与结果目录为同027下`continuation-003`，不再调用原v2的prepare/restart/launch/run，不部署/修改任何模型源码、埋点或配置，实际observer与服务日志仍来自runtime-002，非新服务实例。

准备门禁要求8010仍3199246/start503876115/argv5744d999，idle且prompt/generation计数0；原19清单、probe-config及probe/i64/QSA/全source不变、旧driver已退出且无旧raw请求/新采样PT。复制旧请求及部署回执到独立续跑目录，原件与旧FINISHED/FIRST/STOP不改。原observer STOP是旧控制面8035门禁，不当新模型事故；它可能使selected shared last-writer state在首真实请求时提前冻结，因此不能宣称后续首次数值异常拥有独立全池首现场。每个新评分请求的实际输入、完整raw logits/topkp入口/actual_probs/noise/RNG照常独立保存，原始HTTP/完整token全留存；缺失即报告，不能补造或热清marker。续跑首异常停止新增、在途自然drain，终态额外复制与SHA核验真实sampler PT和manifest。没有正式gate或性能结论。

continuation-003 PREPARED SHA `982598fc64c7fddc595137f85954767ab8cd4ad1fb89489ad357afe83b7953ad`；8035新保护3460404/start503952504/argv91849d0b。唯一客户端3593385/start503991384于19:48:08开始，19:50:10已19/19完成、0错误、0在途；19:50:17自然FINISHED且进程退出。四点评分C1两重复及Mixed的下一token分别1596/14235/1596/494，均一致；背景6条512预设cap、一条doc2自然336结束，不把该有限背景cap冒充60K症状。192份sampler/actual-input PT已复制并SHA核验，尚需CPU数值对照及实际Mixed/graph/服务前后身份审计。

终态CPU脚本`CASE/commands/accdiag027-offline-audit.py` SHA `dbd1b2483bf3ce8bf9219b7dc6ba77891cf79e241b3bfe0449fc58580f76dc76`，本地py_compile通过。确认原客户端已退出且CLIENT_FINISHED/FINISHED/CONTINUATION_FINAL_EVIDENCE齐全后，在现有CPU评测容器qwen38-eval-ppu07-acc015-c64-20261018，以CUDA_VISIBLE_DEVICES空、OMP/MKL=1执行该脚本一次；只读原HTTP/token、192份PT和已冻结日志，排他写新cpu-same-prefix-audit-001，不发推理/GPU请求、不改运行服务。CPU完整向量审计包含raw logits/实际过滤后prob/noise采样核对、thinkend/EOS raw rank/概率/过滤状态、C1重复与Mixed同输入L1/RMSE/支持集合差；短前缀/C8覆盖不能代替长Decode/C64或正式198题。

CPU审计已完成，report `cf8f5181610b7f05a6e118daaa1b69925ce78a5711cdad04a2d1055c7f4f1153` /manifest `fd5e3353969b9ea00d30dcbeed054190e0fa8286328cb371a710ee9afe5c6499`；19原始HTTP/token/192PT解包及SHA、96份实际输入与96份实际采样保存均通过，12评分每rank均一份input+一份sampler。四组C1重复raw/实际prob/noise逐元素完全相同；四组C1→Mixed的noise/RNG before相同，下一token相同。8rank各507条实际FULL回放记录，目标实际首次Prefill均graphNONE；Mixed四点每rankslot7/target computed0、实际7peer各computed>=原prompt且scheduled1、完整输入343/353/778/808，非仅准入时的client并发。

后续仅执行CPU/Host终态尾部审计`CASE/commands/accdiag027-terminal-audit.py` SHA `94abc1d86cd10c55879d6ee95ba97c5e3db90c3e45c5857d55ac62de309d7797`（本地py_compile通过）一次，排他写continuation-003/post-controller-audit-001；只复制旧8rank日志/服务尾部、核原prefix SHA、19 API完整tokens与rank0真实采样前缀、usage/counter、当前8010及8035精确身份/health和原source前后指纹，不发任何推理/微测、不重启/改源。既有监控仍PAUSED；本次前台小范围已终态，不创建后台客户端或重复监控。

## 终态结果：doc81采样前batch敏感，未隔离长推理根因

本轮**19/19 HTTP200、0错误/重试/追加请求、客户端已退出**；只沿用8010原实例，无第二次重启。19原始HTTP完整token均匹配rank0 non-discard实际采样前缀，counter匹配9356prompt/3420completion。8035新保护实例及8010精确身份前后相同、双health200，完整source前后相同。8rank尾部追加0字节，日志已齐；post-controller report `504ec4e77fd201c83bc8b9182972ebf5d653eb7d22b636bbbbe3b8dac2f06c95` /manifest `87aad4da41d8fcc34a4c35328b92bbca9aeb901eaaeea09b32813442358be737`。无新observer FIRST、HTTP故障、非法访存或已记录state mismatch/nonfinite；背景generic state-byte checks未逐层执行，不能把未报错当全状态数值通过。generic gather/scatter每rankmax632、rowstride102400，地址64716800elements/byte[258874880,259268096)在storage27751628800内、实际i64已核；20972边界未覆盖，不据此扩大范围。

| 精确同输入评分点 | C1两次重复 | C1→实际MixedC8 raw logits | 实际过滤后概率 | 下一token |
|---|---|---|---|---|
|doc71 prompt343|逐元素相同|逐元素相同|逐元素相同|均1596|
|doc71 prompt+10共同token=353|逐元素相同|逐元素相同|逐元素相同|均14235|
|doc81 prompt778|逐元素相同|max abs1.67578125；RMSE0.303474；中心化RMSE0.286991|同为单token支持，逐元素相同|均1596|
|doc81 prompt+30共同token=808|逐元素相同|max abs0.9140625；RMSE0.172994；中心化RMSE0.171045|L1=0.11866993；max abs0.05782603；5项支持集合相同|均494|

四个Mixed目标实际首次Prefill均graphNONE/slot7，7peer均真正Decode。四组RNG before SHA相同（8af47981…）、actual noise逐元素相同、96份采样记录均满足实际probs/noise argmax与sampled token一致。故**doc81差异已经在raw logits边界出现，不是本次随机噪声变化/采样token错误**；中心化差异也非纯全vocab公共平移。该batch依赖是观测事实，尚无已知正确同输入reference/逐层输出，不能宣称超出允许数值容差、归咎QSA/GDN/graph复用或确认60K根因。只有本轮C1重复两次；Mixed各一次，不夸称Mixed可重复稳定故障。

think-end248069在所有测量点实际prob均0，**有完整向量证明被本轮top-k/top-p过滤**，非“API top20没显示所以猜0”。原始softmax概率：doc71 prompt约1.37e-6、共同前缀约1.61e-8；doc81 prompt C1/Mixed约5.71e-7/6.48e-7，共同前缀约4.48e-11/7.07e-11。两EOS同样过滤。测量点仍是起始/短推理前缀，低结束概率本身合理，不能外推到48K–60K仍被压制或据此调采样强行结束。

doc71首次历史分叉的4543/14235在当前相同前缀仍都保留，prob约0.37754068/0.62245935；正常与cap轨迹不同token本身并不证明计算坏。doc81共同前缀494/13：C1概率约0.36811489/0.47266889，Mixed变为0.34569067/0.44387561，但同seed/noise仍采494（历史正常支）。历史完整Decode RNGoffset、执行history与本轮fresh-prefill不同，不把此比较解释成旧失败流程已重现。

首次数值差异完整raw logits/topkp入口/实际probs/noise/RNG、实际输入/映射、原始HTTP bytes/headers/完整token及8rank日志已保存在`continuation-003/terminal-evidence`和两个CPU审计目录；192PT全部torch CPU解包与SHA核验。未出现已配置异常，不伪造新的FIRST_ANOMALY marker；离线发现的batch差异如实列入对照结果。继承旧控制面STOP导致selected state可在第一条真实评分提前冻结，不能称doc81首次差异的完整逐层/全池现场。下一步若要定位第一分歧层，需用户另行确认窄逐层对照/必要8010重载和新的请求范围；本轮不自动执行。正式acc015164/198 failed-score/no gate原样保留，无新正式精度/性能结论，performance stacking仍blocked。当前根因置信度：**采样前batch差异已观察；60K不收敛根因not-isolated**。
