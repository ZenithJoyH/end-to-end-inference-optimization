# acc-021：当前多模态／16图实例C64完整GPQA

收尾：两项终态原件与CPU审计已完成归档，monitor `qwen3-8-ppu07-mm16-accuracy`已产品确认deleted；全suite598模型HTTP均200／0重试，当前BF16／image16服务保留，不再自动发起任务。以下继续／待结束monitor描述均保留为历史。

后继ERQA已完整结束且独立CPU审计通过：251/400＝62.75%（score-only、无阈值），G/SUITE_FINISHED齐全、原controller与两evaluator/helper均退出。同一8010源与身份仍完全一致，健康空闲、KV／抢占0，当前新gate保持有效；结束monitor并保持服务等待方向，详情见[acc022终态](acc-022-full-erqa-mm16.md)。本页下方“ERQA继续／无分数”为历史快照。

## 本轮GPQA终态：175/198通过，ERQA继续原队列

strict `175/198＝88.3838%≥88%`，当前同一BF16／image16多模态8010的GPQA新gate已原生签发，独立CPU审计通过。FINISHED epoch`1792831639.103561`；198唯一doc0..197／396双filter行、每(doc,filter)一次且同题raw／usage一致；198份完整API对象通过真实prompt逐题唯一映射，198次服务HTTP200、0真实客户端超时／重试。189份非空final含thinkend／正常EOS，另9题达到60000长度、没有thinkend／final=None，原runner转成`<TIMEOUT>`占位并计错，不能称为网络超时；doc为32/71/76/81/94/121/130/145/147。首份日志原时间2026-10-24 08:38:12 UTC（16:38:12+08），原始证据已由既有controller冻结于`G/diagnostics/terminal-evidence-001`，未补推理／修复／重测。没有提前EOS、NaN／非法访存新日志。

80个原manifest成员与49／652冻结输入全部SHA重验通过，source前后／当前、三repo HEAD-index／engine／bootstrap及8010进程精确绑定不变；GPQA evaluator／helper退出，原suite controller仍运行ERQA。原生acceptance `check`通过，gate SHA`14036dc9fc0b7ee386025dfc6778c87c18933a81c85d596980381995bbc0bcae`，summary SHA`52df26de44d2f5f0fcc7961f26727e405dcb110271609d64cfa38c15b11e45e2`，manifest SHA`d602ec1be035e88cb0ac77ac9f91fcf659003b8a88634af06a41de5b2a8f3636`。

原生结果及samples位于`G/results/Qwen3.8-Flash-Next-ppu07-acc021-c64-mm16/78da456a49034ee888bd4100c521e9a4/gpqa_diamond_generative_cot/Qwen3.8-Flash-Next/`，文件时间后缀`2026-10-24T08-47-11.335129`；results SHA`4bf628e33c6ae3d6843a299596dd4f65a8d83ed7342d6c751e6f1311034acca0`，samples SHA`e607ad3d03bd5e07ccfce976e593472db33449c6009f0732d9d4d0160d449b04`。gate为`G/evaluation/accuracy-gate.json`。完整解析API/token不是wire bytes；没有本轮逐层QK／logits／state或独立逐rank kernel现场，不以本轮与历史176/198差1题直接归因多模态／16图。

CPU审计脚本SHA`3638cfa6659abc90404c3e9f1d2f1310d13222e032420a32e6bc19946898a9ff`，报告SHA`0a664b17c25b00c76475033b74c56a34821c4d32c29b13302219d49b9f44aec3`，本地`/private/tmp/qwen38-acc021-suite.fFYQXM/gpqa-terminal-audit-001.json`。按执行前计划，仅CPU复制这两个既有文件到全新`G/diagnostics/terminal-audit-001/`，拒绝覆盖；远端白名单／SHA及落盘后逐项回读均通过，回执`archived-existing-CPU-audit-readback-verified`，没有模型／GPU调用。原80成员manifest保持原样，新增两文件单独以这两SHA绑定。

ERQA FORMAL_STARTED epoch`1792831640.620891`，由原suite自然串行开始400题C64，当前无终态分数。monitor保持ACTIVE只读跟进ERQA，两项全部终态后删除；0新模型启动／重启／smoke，不启用encoder graph／8035／提交推送，不自动开启性能任务。以下为执行前与运行中历史快照。

## 授权与范围

2026-10-24 用户明确要求用当前8010继续一轮全量GPQA及ERQA／C64，保留BF16和现有修复，不重启、不启用encoder graph、不访问8035、不提交推送，保存完整证据。GPQA与[acc022 ERQA](acc-022-full-erqa-mm16.md)串行，各自C64，合计并发不超过64；不是两套同时128并发。没有新smoke、模型／算子／性能请求或任何服务／容器重启；仅创建独立CPU评测容器。

使用本地accuracy `formal-gate`，bundle SHA`1ed06a57f1f6e1ef39fb7fd872f579122b098a18f0255ade0a1160d6432c2b66`。已完整读取Skill／项目映射／正式入口／accuracy契约／实验契约；inventory与PPU-07 connectivity-check完成ok3／changed0。无子代理。原eng072 monitor已结束删除，不能恢复旧controller。

## 当前服务与先决证据

PPU-07，模型容器`qwen3.8-flash-opt-ppu07-20261015`，8010／TP8物理8–15。API Host3459214／start553495020／argvSHA`646b86aec9182f0f5f53227e2880519d7d4dd7a5fbd7964b76d47417bf06fc2d`；只读新核health200空闲，prompt6908／generated3856，源与eng072终态完全相等。三库canonical `/opt` editable、FGVLLM开关1、BF16 model9e74fb34、MoE原布局cac5b989、PLE／QSA／index／index_put／randn／黑名单／pin047全部保留。image16／video1，encoder graph与compile false，语言FULL_AND_PIECEWISE与prefix cache禁用不变。

eng072当前同实例14请求minimal、capture两类7/7、C8前FULL1309／真实unpadded8 FULL184、各8rank异尺寸及16图实际SDPA→Torch→Gems函数来源及588项CPU审计已通过。只作为本轮运行身份／启动护栏引用，不用旧176/198代本轮分数，不把该Python来源称为本轮198题逐rank kernel或逐层QK／logits／state现场。权重身份为metadata／tokenizer hash＋全部权重stat，不是重读全量权重字节。

## 冻结正式契约

`gpqa_diamond_generative_cot`，198唯一doc0..197、limit0、C64，`exact_match,strict-match`阈值0.88；原温度1／top_p.95／top_k20／min_p0／presence0／repetition1／max60000，原API默认seed／stop及evaluator seed42不变，完整token IDs／prompt。API最多3总尝试、7200s／次，eval整体重试0、正式轮数1，独立UUID／SQLite响应缓存，不读旧答案。198逻辑题不等于HTTP尝试数，最大594API尝试。

新CPU eval=`qwen38-eval-ppu07-acc021-c64-mm16-20261024`，规定`harbor.baai.ac.cn/flageval/flageval-llmeval:v1`；无GPU映射。维护版formal_accuracy调用原始llmrun（SHA`82cf6e8304cb6f9eb8ca48fe4055f6bbb2054a7b6a90d56de3d6b7a08e90c61e`），两次新provenance一致后冻结schema3 contract，再原生preflight，之后单轮formal。dataset内容指纹预期`content-sha256:167548b01bcfd7d38d0eb80bb01bd1e6dded4d3aa14b41a4bdba0beb5423dadc`，不静默改任务／来源／阈值。

## 命令与产物（执行前）

G=`/mnt/nfs/users/jinghao/qwen3.8-flash/20261015-qwen38-flash-next-ppu07-container/accuracy/acc-021-full-gpqa-ppu07-c64-mm16-20261024`。ERQA另用同根acc022子目录。现有远程根真实uid0／0700、规范解析无symlink，剩余空间充足；只新建两目录，拒绝覆盖。唯一串行controller `G/commands/suite.py --mode run`，prepare／launch分别最多一次；不含model kill／stop／restart或新模型启动指令。

- suite SHA`3661026af482918fa4867c728e10bc6b46fc40bdf6597ae5c4ee0259663da744`；source probe SHA`e0768e31949a01d46859f7462f5befca99b32eec23a995aa67c06550e2309b37`。
- ERQA参数／wire桥接SHA`d6cba55d2a2ae32916ab8eade0307e57517c9c71c8714af6284bfb5250c7ab4b`，ERQA CPU audit SHA`51748db98ecf6d14f45573d1ebc60c7b8a6b8190f8e9375a65c1481b2d70da6a`。
- 17冻结输入STAGED SHA`d77ec070c89dab6d737a9c1c911f0c60c073662aae11c264755538b792ca2cdf`；最终传输包SHA`457ee928c159af3e3bde6a21eb769ec724e12d8dfeeadb09f989b00e001f6476`。
- 本地`/private/tmp/qwen38-acc021-suite.fFYQXM`，3项CPU控制／原始HTTP观察测试及脚本语法通过。v1只是本地构造候选，新增真实question_id↔wire index绑定后形成上述v2，尚未发正式请求。
- 部署先核tar SHA和17输入＋STAGED白名单，保存原始commands／bundle，再`--mode prepare`；核两项PREPARED／前后source／payload和数据proof通过后，创建30分钟只读monitor，再唯一`--mode launch`。

保存services/runtime、source-before/after、同实例minimal引用、evaluator inspect、两provenance、config/contract、preflight、FORMAL_STARTED、原生results/samples/run-record、完整解析API对象与token日志（非HTTP wire bytes）、原始退出码、gate（若可签发）、summary／FINISHED与终态manifest。服务错误仅按本轮byte/inode新窗口判断，不拿旧log当新事故。

## 停止／判断与后续

普通错答、空final、length由原评测自然收集，不自动重跑；区分contentNone→TIMEOUT占位、真实HTTP／7200超时、60K截断／EOS。只按每(doc,filter)及真实缓存映射核198唯一题，helper排除None的子集高分不当正式分。低分按diagnosis冻结，无新性能优化；若GPQA低分但服务／source精确健康空闲、证据完整，仍继续用户显式指定且已冻结的单轮ERQA，仅accuracy诊断，不签GPQA gate。执行／身份／源码故障或证据incomplete则不启动下一阶段；不自动修复／恢复。现有在途自然排空最多等10min，不强制停止模型请求。

终态须独立CPU核原生样本／分数／provenance／source／当前服务与进程退出；score≥0.88且证据有效才报告本轮原生gate。不与不同软件／配置历史直接归因多模态或16图。两项结束后写回同一acc021／acc022／state／README及eng072覆盖，终止monitor，保持当前BF16 image16的8010等待方向。

上述为执行前快照；当前运行状态见文末，不能把它当作新终态分数。

### CPU准备首错保留与仅编排修正

首次prepare在调用source CPU probe时因`docker exec`的容器名误放在env参数之后，错误为`No such container: env`；在创建评测容器／GPQA provenance／任何新模型请求前退出，当前8010不受影响。原`commands/suite.py`／PREPARE_STARTED／CLIENT_ERROR原样保留，SHA分别`3661026af482918fa4867c728e10bc6b46fc40bdf6597ae5c4ee0259663da744`／`a0f8ea29ad496d21de49811054f2b972d8a0bee2163f21956442d6fb4712ef44`／`a9d09cced0067d5cf617a1402ad8afdb49aed97f12645c31b6b272049b868d6b`。只读确认两个新evaluator都尚未存在，正式请求0。

仅把容器名移到`docker exec MODEL env ...`正确位置，另存`commands/suite_v2.py`（SHA`36893f3fb404504fc435212f5de0e8c07f13c13d551788e6553dcd8f2ebf8fcf`），不覆盖原脚本或重启服务；另外使用PREPARE_STARTED-002／CLIENT_ERROR-v2标记，旧首错不是后续formal的新错。STAGED-v2同时绑定旧首错及新脚本，4项CPU测试含命令顺序检查通过。新唯一正式控制器改用`suite_v2.py --mode run`；正式任务仍0次，不是重跑GPQA／ERQA。

## 预检通过及唯一正式队列已启动

两CPU evaluator已创建且无GPU映射；GPQA两次新provenance逐字一致SHA`c39228d57fd391a9f723496f54fa2fb3f0d7aeb17810a2edf63559152dc63523`，原生preflight通过。PREPARED SHA`b3831e12105ddd8ac9acca575ab776b2016937897a00460c6af63647df3dc62a`，49冻结输入SHA`0dd8609c60605c41fbab78f1b51382cc7c74a11e73557bf1e02978ee24ae642f`，config SHA`13cd7f82b60da2de55c47e672a38becf250bb0b60e56e42cb130f6b144ad3b4c`，contract SHA`89972e489148bf819984ffdfc250796b28f0cc08256f4d162108efd9dd6fa0f7`。ERQA400题／630图片及真实16图payload零请求预检通过。独立prelaunch审计核所有冻结项／当前source和API精确相等，模型计数仍prompt6908/generated3856。

按已记录命令仅一次执行`G/commands/suite_v2.py --mode launch`，返回controller Host2518158/start554233287/argvSHA`cd15d2325ba55535166029db968588509c85a3dcd421c1d1a60e456a250dd35e`，CLIENT_PID原件及当前proc一致。GPQA FORMAL_STARTED epoch`1792826507.881332`，原生runner日志明确attempt1/1、独立UUID/SQLite、num_concurrent64，ERQA尚无FORMAL_STARTED／wire请求。当前无新CLIENT_ERROR-v2；历史CPU prepare首错仍完整保留。仅启动客户端，不启动／重启模型或额外smoke。

30分钟只读heartbeat `qwen3-8-ppu07-mm16-accuracy`已产品确认ACTIVE，监控此唯一串行队列；普通推进静默、首新异常／实质结果／明显停滞／需用户处理才通知。终态独立CPU审计后写回并删除monitor，保持8010；当前分数／gate均尚未产生，不估ETA。

启动后只读复核epoch`1792826639.8729439`：同API健康200、running64/waiting0、KV11.49%／抢占0，prompt32314／generated36428，原生完整解析API对象及token已返回，日志持续增长；原controller仍相同身份。未把64在途或helper子集当作完成题数／正式分数；ERQA仍0请求。结构化记录schema4／唯一ID／新增文档链接及diff空白检查通过。
