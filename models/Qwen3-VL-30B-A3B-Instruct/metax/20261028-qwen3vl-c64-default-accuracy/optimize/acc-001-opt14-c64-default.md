# acc-001：用户当前opt14服务的C64完整GPQA/ERQA

状态：preparing。用户要求对当前已经启动的Qwen3-VL服务，以64并发跑GPQA和ERQA。沿用此前模型默认采样、GPQA64/ERQA40阈值；分别完整198/400题，各一次，顺序执行，有效GPQA低分仍完成ERQA。mode=formal-gate。适用Skill为本地inference-accuracy-evaluation，方法映射/工具/实验契约已读；本轮不是性能测量。

## 当前服务与范围

mx-104，容器qwen3vl-pr943-split1-mx104-20261023，用户实例qwen3vl-opt14/8030，PID1597993/startticks1146418910，GPU0,1/TP2/BF16，模型/data/models/Qwen3-VL-30B-A3B-Instruct。maxbatched8192/maxseq64/gpumem.91，FULL_AND_PIECEWISE/maxcapture64，prefixON。预检models200，running/waiting均0。保留服务、源码、采样和缓存，不重启，不恢复历史服务。回退PR638后的实际源码及四仓/import/model/tokenizer指纹必须重新取证，不复用旧精度gate。

## 评测配置与执行

当前默认采样预期T.7/P.8/K20/repetition1，须配置/启动日志现场复核。原GPQA officialv1 runner和原ERQA flagevalmm完整任务/评分实现不改；仅沿用已经验证的loopback默认采样传输去掉客户端采样/seed覆盖，原messages/images/stop与18000输出cap保留。C64为客户端并发上限，不声称每步GPUbatch均64。

远端唯一任务根/public-flash/jinghao/qwen3-VL/20261028-qwen3vl-c64-default-accuracy（用户原授权根/public-flash/jinghao/qwen3-VL；路径/owner/权限/15TB空间/新目录不存在已核验）。GPQA新CPU容器qwen3vl-opt14-gpqa-mx104-20261028使用official v1 image1396e5d6；ERQA新CPU容器qwen3vl-opt14-erqa-mx104-20261028使用原冻结image997570d1。只绑定本次任务根，host网络、无GPU；不接触其他任务的评测器。新可执行脚本/配置先归档命令及SHA再执行。

复用旧20261026-qwen3vl-opt12-c64-default-accuracy中的已验证采样传输、原生任务来源与编排方法，但使用新文件和身份。修复已知采集生命周期问题：原生结果先回收/验证，不以代理drain或400个唯一消息体作为额外精度门槛；题目覆盖以400唯一question_id核验，保留全部原生拒答和重试，不发补跑请求。任务停用前核验用户服务原PID/source与models200保留。

正式前CPU默认请求factory测试、两次独立provenance、198题/ERQA400题630图来源校验、service manifest/preflight及普通smoke/C8；只记录现服务启动capture和正常graph配置，不安装侵入计数器、不编造直接replay次数。两项原生输出/逐题分数/源前后核验，GPQA达64才由原acceptance issue/check签本实例gate。ERQA同时报告native filter_rejected及全部400计错口径。低分保存并调用accuracy-diagnosis，不自动重跑、叠新优化、改阈值。

长任务继续沿用每30分钟进度通知偏好，创建本chat heartbeat；只管理自己的评测端/传输，结束后停用。原始数据留远端，本地同步state/README，未完成不填pass。

执行前归档bootstrap：commands/bootstrap.py，SHA `ce90caf7b36d8d4d540f1dac2bb34c961d6cae922abd1ffdbe1ac7798b4c98dc`。它只创建本次两CPU evaluator、解包冻结维护版工具并生成新配置/控制脚本，不触碰模型源码或进程；随后prepare与controller各自需在执行前记录生成SHA。工具包commands/evaluation-tools.tgz SHA `e65804f2332c9051f5e7559f9ff329d3d9cfef766992b1b6191e1462598f960c`。Skill bundle SHA `1ed06a57f1f6e1ef39fb7fd872f579122b098a18f0255ade0a1160d6432c2b66`，explicit selection formal-gate已通过。监控ID qwen3-vl-opt14-c64，thread heartbeat每30分钟，已active。

MetaX accelerator-check现场核验：C550，GPU0/1 PCI0000:2b:00.0/0000:3a:00.0，driver3.8.1，MACA3.7.1.5。两卡当前利用率0%，占用约62GB属于已加载目标服务；不释放显存。

bootstrap已完成，两CPU evaluator创建成功，0模型请求。生成脚本执行前SHA：prepare_accuracy.py `a3ed0bd4bd8d8cdc1cda5b4044f3c24ab56496d3eb254d05d6be41195df55db7`；accuracy_controller.py `0613f98ec249501a6ce0c96053f95a7f2663859fda70e74b153d46756df8405a`；start_controller.py `830b90d05b7d56a8041ee9fd29a3bb4485bf7c8cca76e316d5d42bc4d65652b4`；collect_current.py `345ef57a704e20c88fd3e5b6ccc16e096681431a09835d79a4b45299a7453a18`；default_sampling_proxy.py `29f4db3349277bd7be9026c430c2397125a1d2d21ab1dbe0798786cdde8e802a`。路径均为新case commands/，唯一控制器尚未启动；旧控制器/旧准备脚本不执行。

CPU准备已通过：两次GPQA provenance一致/同198题；真实GPQA与ERQA客户端factory的inert CPU请求经过传输后无采样/seed字段，messages/images/stops/cap保留；ERQA400题/630图/评分源码逐SHA通过。实测默认T.7/P.8/K20/repetition1，当前Attention SHA f81fa552…等于回退后分支原文件，PR638未加载到磁盘源码。prepared.json SHA `baf204475a2ea8c7c93db882ea2a7a689f166496d9c60235da9df857776380be`，execution-contract.json SHA `886b4e5076cb50f6712953e42ba0eb506b704e5b2f663590fb62275a77eca6ad`。准备0生成请求。正式控制器的排他启动锁为manifests/controller.json；只启动一次，运行前再次重验source及所有冻结artifact SHA。

2026-10-28 10:23:21（Asia/Shanghai）adapter-ready，10:23:35普通smoke/C8/source passed。唯一controller1150442/ticks1146494144已启动，GPQA正式preflight进行中；未重复启动，模型保持PID1597993/ticks1146418910。GPQA/ERQA完整结果尚未产生。

10:23:43 GPQA正式完整198题已开始，初始65个转发attempt/1个完成响应（不是最终分数）。ERQA尚未开始，当前唯一controller随后按原计划顺序执行。两评测容器本次直接bind新case，Host输出就是原生输出，不再使用旧private目录复制/harvest分支。监控已更新唯一controller身份，禁止重复启动。


## 2026-10-28 10:47（Asia/Shanghai）跟进

唯一controller1150442/ticks1146494144仍活跃，未重启/重跑。GPQA于10:41:07完整完成：**118/198=59.59595959595959分<64，有效失败，无gate**。独立CPU复核原生198unique、strict-match逐题sum118、结果/样本SHA、task/data/config/provenance、source前后精确一致；198次上游请求/198响应均无显式sampling或seed。原runner末尾SCORE logger matched0不是0分，正式分数来自原生结果及逐题样本。

GPQA回执results/gpqa-completed.json SHA8d79586704e7d2401b12c4caa59cfa279455ca6b85cb3286a9b0ec2e9f00a89e；native result SHA8837883b8dd708d236f674bc6095411fc88f9bc13f0371dcc3cfe36c0553f7ae；samples SHA5a438de884095a595e3e11209c75b7ae3e8ae3895f065a2d7de042f82222ee75；sampling-audit SHAf2b91da07f8cc925a70ff3ea945165d6a25bac152b842f6086334d15364e2b83。全部原始证据保留在本远端case，不用重复评测覆盖低分。

ERQA已10:41:08启动C64完整400。当前原生items338/400，proxy400attempt/338HTTP完成、399唯一消息体；消息体去重不是question_id完整性或附加精度门槛。暂无ERQA最终分数。modelsHTTP200仍opt14，继续原生任务，不改并发/采样/超时/重试。

调用本地inference-accuracy-diagnosis并冻结issue **accdiag-opt14-c64-gpqa-001**，入口SHAdae96b45…；完整方法已读，无machine interface，不假称机器模式选择。分类为来源有效的正式分数未达标，root cause unconfirmed。此前opt12 C64/defaults129/198通过，但source/实例不同且未冻结request seed，不能由一次分数差直接归因于PR638回退或某库更新；没有新增最小复现/GPU诊断/修复。正式性能晋级阻塞，先完成用户要求的ERQA，失败不触发完整GPQA自动重跑。


## 最终结果：2026-10-28 11:17（Asia/Shanghai）

ERQA于11:16:30完整结束，原生400 unique question_id、400条evaluated均有bool correct，181正确，0原生拒答。**原生45.25分>=40，通过；全部400计错口径同为45.25分**。data.json/630图/原评分源码SHA复核通过，原filter_rejected零拒答缺reject_info分支已核验，未变更分母或丢弃结果。

| 数据集 | 正确/总数 | 分数 | 阈值 | 结论 |
|---|---:|---:|---:|---|
| GPQA strict-match | 118/198 | 59.59595959595959 | 64 | failed，无gate |
| ERQA native | 181/400 | 45.25 | 40 | passed |
| ERQA全部400计错 | 181/400 | 45.25 | 40 | passed，0拒答 |

两项原生任务均仅完整执行一次；无补跑/调阈值/更改过滤或采样。ERQA实际449次原生转发attempt/449个upstream完成响应、49次下游回写关联error、399个唯一消息体，原客户端重试保留。这些是HTTP诊断计数，不能冒充题目数或额外否决400原生题目有效分数。全部上游attempt无sampling/seed字段覆盖，继承模型默认T.7/P.8/K20/repetition1。

独立只读终态审核再次调用原生来源/样本校验及原ERQA filter_rejected：GPQA198unique/perdocsum118/原结果SHA一致，ERQA400unique/181correct/原数据图评分源码一致；before/final/current的四仓源码/版本/import/model/tokenizer/默认配置/argv/env精确一致。用户模型原PID1597993/startticks1146418910、8030modelsHTTP200仍opt14，prefixON；评测controller1150442与自有adapter均退出。finally于11:16:32只停自己的adapter，未停止/重启模型、恢复旧服务或删除评测容器。终态审计0新生成请求。

| 远端结果（相对本case根） | SHA256 |
|---|---|
| results/erqa-completed.json | f65ffdf10006f651b84e57ff5fcd744f2f4964e5f8fd173c84da0615ba51b1af |
| results/erqa-sampling-audit.json | 2bf92c5083fbcd2706fa26776fed2499e04d8f3c5f7ee620ee22399c85ae93a9 |
| results/completed.json | 4716b66595148dce51ecc86a6d941cd62883e0a20353ba818b962b7b9324e577 |
| results/user-service-final.json | c91c399e23c543bef30447307a664ac6607749eed17309442d984f191139296e |
| results/adapter-stopped.json | 4d029a681e0881d30a397fbae3d81670391556dc830328710cb7bad1c5c3cf15 |

用户要求的本轮精度评测已完成，整体accuracy_status=failed（GPQA未达64），ERQA通过不豁免GPQA；未签formal gate、未测性能。accdiag-opt14-c64-gpqa-001的根因仍unconfirmed；不自动追加GPU复现/修改/重跑。与历史opt12的分数不同不证明PR638或其回退导致差异；seed/source/实例和轨迹须未来单独控制。graph证据范围仍仅本实例startup capture+正常配置smoke/C8，无直接replay计数，不追认硬件gate。

两数据集终态和当前用户服务保留均验证后，监控qwen3-vl-opt14-c64已由automation_update delete确认deleteStatus=deleted。原始全部样本、响应、日志、配置和证据仍在远端本case；本地optimize/acceptance双视图同步，无提交/推送。
