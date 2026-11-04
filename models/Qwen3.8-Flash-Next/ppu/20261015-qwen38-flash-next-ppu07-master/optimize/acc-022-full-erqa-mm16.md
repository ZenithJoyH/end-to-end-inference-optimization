# acc-022：当前多模态／16图实例C64完整ERQA

## 终态：251/400＝62.75%，完整原生结果及独立CPU审计通过

收尾：计划中的5份CPU审计文件已复制到`E/diagnostics/terminal-audit-001/`，白名单、原SHA及落盘后逐项回读通过，未覆盖任何原件；notes SHA`9f65809e056db1fd348d94f4e8c435927d616547dda1e2a7a1b4e04b9522b5ee`。monitor `qwen3-8-ppu07-mm16-accuracy`已产品确认deleted，不再定时检查。全suite实际598次模型HTTP均200、0重试，两项各只执行一次；当前8010保留等待方向，未停止／重启。下述归档计划及monitor待结束描述是已完成动作的执行前记录。

ERQA完整400唯一question_id／400原生items／400 evaluated／400真实index-binding及完整wire一一核验通过；原生accuracy **251/400＝62.75%**，无预冻结ERQA阈值／同配置baseline，因此为有效实测score-only，不签ERQA gate，也不凭一次后测宣称多模态／16图前后精度等价。单图188/287＝65.5052%，多图63/113＝55.7522%，分组题目不同，不把组间差归因于图数配置。

原生分项：Spatial Reasoning 53/84＝63.10%；State Estimation 36/55＝65.45%；Action Reasoning 45/72＝62.50%；Pointing 29/34＝85.29%；Trajectory Reasoning 40/66＝60.61%；Task Reasoning 23/38＝60.53%；Other 6/14＝42.86%；Multi-view Reasoning 19/37＝51.35%。所有分项correct/total由原生evaluated与冻结data的sub_task重建，百分比与原生metrics逐项一致，未重评分或替换parser。

400请求／400次HTTP200／0重试／0真实HTTP超时，实际客户端峰值在途64；0空final／60K length／提前EOS，所有完整token长度／prompt／usage、thinkend及EOS均核验，native answer/reason与raw message按原生规则逐字相等。630张图引用及最大16图均保留，逐题图片顺序、文本片段、采样payload与真实ID绑定一致。完成生成2298955／prompt182339 token；加GPQA2374758／79715和原minimal3856／6908，精确等于当前服务generation4677569／prompt268962。不是用派发数、部分body或helper子集当完成。

原suite自然结束：E/FINISHED epoch`1792836245.683172`，G/SUITE_FINISHED epoch`1792836245.6849377`，原controller及两evaluator／helper均退出，无CLIENT_ERROR-v2／FREEZE_ERROR。3077个E原manifest成员、701个两阶段冻结输入、125个原生评测源码文件及630份native图像SHA重验通过；source前后／当前、三库HEAD-index／engine／bootstrap及API3459214/start553495020保持完全一致。当前health200，running/waiting/KV/preemptions均0，BF16／image16／所有修复保留，encoder graph关闭，0新模型启动／重启／smoke／GPU／8035／提交推送。

原生路径：`E/native-output/erqa/erqa_result.json`（SHA`f1363a6839532d529495834b63bba8a5c6919210f74f7feb2c32e5f5f839e4ea`）、`erqa_evaluated.json`（SHA`c962f8cfd22dc421f4a7b29f0bac3611d5a337191e7683458ed5e8bdad3b6831`）、`items/`，以及`E/wire/`和`E/index-binding/`。summary SHA`6684deaced5c0b4ea4dfabb539371dfdb3f4b32875f3b82dba354285c0dda4d4`，manifest SHA`c68b13f57c78a5bf27bd188a437bc312a9671f4544f7eba462557a5fc849a64b`，SUITE_FINISHED SHA`f895a46222a7b023b55ca1a35364fb69387f89813a0bec9dd9efaf94ba33c54a`。完整终态日志保存在`E/diagnostics/terminal-evidence-001/`。

CPU独立审计003 SHA`9f0eb477aad068d3fc111ed097341773b2fd1831d4499b830570c602626ea8e1`，报告SHA`fcd5c95e24dd57da87605b46b6aa239cfdc68318a2aa85cfe6f0dc363567fcd0`；前两版仅CPU断言误把图片占位符当作wire原文、漏掉native think分离附带换行，已只读核对原生组装源码后更正审计，两版脚本及说明保留，不修改native评分／原文或重跑推理。归档执行前计划：将001/002/003脚本、003报告与audit-notes共5份既有CPU文件复制到全新`E/diagnostics/terminal-audit-001/`，拒绝覆盖，逐项SHA核验后回读。原3077成员manifest不改，新增audit另行绑定。

GPQA当前同实例新gate175/198＝88.3838%≥88%已核验；GPQA9题60K空final保留计错，非网络超时，不影响既定阈值判定。本轮无逐层QK／logits／state／独立逐rank kernel现场；旧eng072来源仅同实例护栏。全suite已终态，结束monitor后保持当前健康8010等待用户方向，不自动开始性能。以下为历史准备和运行快照。

2026-10-24 当前状态：原串行suite在GPQA175/198新gate签发并冻结终态后，自然于epoch`1792831640.620891`开始ERQA400题C64；没有手动新launch／run、0模型重启／smoke。GPQA独立终态CPU审计通过；ERQA无分数／gate，继续原评测及只读monitor，普通在途／派发不当完成。以下“等待GPQA”为历史快照。

## 授权／依赖

2026-10-24用户明确请求当前8010各一轮完整GPQA和ERQA／C64，0模型重启、保留BF16及修复、encoder graph关闭、不访问8035、不提交推送。复用[acc021串行控制器](acc-021-full-gpqa-mm16.md)，GPQA后确认同一实例／source／健康空闲才运行ERQA，各自C64、总cap64。不额外smoke／性能或新GPU测试。此前因image1暂停的评测没有启动，本轮是新授权与独立输出。

## 原生数据和评分

ERQA是图文精度，不是纯文本；原生ERQA/test完整400唯一question_id、630图片引用，287单图／113多图，最大16。data.json SHA`c02963830b51a6103f07d4e2fa60c76ba566d7af88214bcb4545c7475658663c`，图片当前均存在并已CPU全字节SHA核验。保留所有图片／顺序／原生prompt-template及BaseEvaluator，不拼图、截断样本、改标准答案／parser或helper子集评分。

当前模型无同软件ERQA阈值／baseline，本轮只报告原生accuracy及正确数／400、分项和输出异常，threshold=null，不签GPQA式formal gate或凭一次后测宣称开启16图前后精度等价。原生任务`/app/tasks/erqa/erqa.py`，原API ModelAdapter／HttpClient流程保留。

## 执行契约

E=`/mnt/nfs/users/jinghao/qwen3.8-flash/20261015-qwen38-flash-next-ppu07-container/accuracy/acc-022-full-erqa-ppu07-c64-mm16-20261024`。

新独立CPU evaluator=`qwen38-mmeval-ppu07-acc022-c64-mm16-20261024`，镜像`flageval/mm-eval:v0.3.8_1`／imageID`sha256:946d2725872c7fd1a5ca643be16132bb1d22af709f52819bbe7b0f5da81900f9`。仅复制已有本地ERQA数据／图片，不复制旧answers／items，独立UUID chat名及空输出，use_cache=false、num_infers1、num_workers64，limit完整400、不加try-run／skip。模型仍同eng072 API3459214/start553495020，不重启或改服务；新native评测控制端口29622仅CPU调度用途，执行前检查空闲。

保留当前Qwen采样T1／top_p.95／top_k20／min_p0／presence0／repetition1／max60000，API原默认seed／stop不变；nonstream，return_token_ids／return_prompt_text。原生HttpClient每次timeout7200s，BaseApiModel既有Tenacity最多5总API尝试保留（400逻辑题最多2000HTTP尝试）；正式任务本身只启动一次，无自动整体重跑。此机制与GPQA最多3总尝试分开统计，合计最坏2594次模型HTTP，不冒称598次HTTP。

原生adapter的_build_model_config不传top_p／top_k，因此使用本轮G/commands/erqa_adapter.py桥接：仅model_init后更新保留的chat_args；调用原始process_single_item／原始评分。零请求payload预检验证真实16图组装及最终参数。请求时只在CPU客户端观察原requests.post，原调用一次、原response对象原样返回，不改变重试／None parser／reasoning或结果。按真实native item index／attempt保存request bytes、response bytes／headers、错误与已返回完整token；native返回后保存真实question_id→index绑定，不能凭输入顺序猜映射。Authorization头不记录。GPQA日志为原生完整解析API/token，不因此宣称GPQA也有wire捕获。

## 证据与判断

先CPU dataset-proof（400唯一ID／图片SHA／native所有源码）及16图payload-proof，核新容器native源码与本轮只读来源一致，再冻结config／contract。当前三库／engine源、镜像／挂载、READY＋8010 listener/start/argv、同实例capture/replay／来源及14请求minimal引用随acc021重新取证。

保存native-output的items/result/evaluated、wire及index-binding、完整runner log／退出码、source前后／metrics／服务新日志窗口、原生分数审计及summary／FINISHED／manifest。真实HTTP错误／超时与空final／60K length分开报告；原生content=None可能触发parser异常及原5次尝试，原行为保留并记录，不能补推理或改parser使本轮通过。普通错答／截断继续原定完整收集；服务或source故障不再启动新阶段，保留原错。终态仅CPU审计已有证据，模型服务保持不变。

控制器／桥接／包SHA及命令冻结详见acc021；最终4项CPU机制测试不代替本轮400题结果。

## 当前：预检通过，等待串行GPQA结束

PREPARED SHA`ecf9137cb546998f1979397d128bca51eb011f23f445b04526f5365fa2eaded4`，652冻结输入SHA`a76ad0a47e85274c3089f6e60ba3016f4480b4ebe33c43033532579954bdbae8`；config SHA`0b5d2c53daa250ade0d46eba239c182570eb98af3f6579b1106251e7e8ad2437`，contract SHA`01b01cdaca87b75b68c397badfed775a31252a348c6fedba44caea2a5aae1dba`。dataset-proof SHA`24bdd98f5a08fbfbfda215681baa8140c1fbffaa6602bb44358117378327a875`、payload-proof SHA`239de606a1365a96b01f9e926079c3597e1fcdc09d741a44f330aad441688187`，均是零推理请求CPU校验，不是精度结果。

原acc021 controller2518158/start554233287已单次launch，GPQA原生attempt1/1开始；ERQA FORMAL_STARTED尚未出现、wire/items/index-binding均0，只等原队列串行推进，不另行launch／run。30分钟只读monitor `qwen3-8-ppu07-mm16-accuracy`已ACTIVE。未产生ERQA分数或gate；8010未重启、encoder graph保持关闭。
