# diag-001：opt12通过版与opt14低分版受控对照

授权：用户要求继续定位当前GPQA59.60分，保持其他配置不变，先和此前通过版受控对照；用户另明确允许临停本任务opt14（8030、GPU0/1），结束恢复。仅本服务及其专用对照容器，其他服务不动。

关联问题：accdiag-opt14-c64-gpqa-001。使用本地inference-accuracy-diagnosis，完整GPQA使用inference-accuracy-evaluation formal-gate，不改原runner/评分/采样。不是性能优化，不测ERQA或吞吐。

## 已确认差异与控制范围

历史opt12 C64/defaults为129/198=65.1515，当前opt14为118/198=59.596。两次source-before中，engine/FlagGems/FGV完整源树、model/tokenizer manifest、generation_config、imports、versions全部exact；Plugin只有MetaX Attention文件不同。旧文件SHA4e12e6ba6b739560cfee8cae47324c859aae1058257b67b89ec2f9357569a174=PR638 Prefill+decode split1，当前SHAf81fa552667b3ed98d1cf141d2dee33ba10476cda9a997744495bdbc36289ef2=原paged Prefill+默认split0。两个子变化共同构成版本变量，第一组不能区分其各自贡献。

启动参数除历史name/port外相同；本次所有角色统一当前opt14的完整argv/env，8030、served qwen3vl-opt14、GPU0,1、TP2/BF16、batch8192/seq64/mem.91、FULL_AND_PIECEWISE64、prefixON；模型/data/models/Qwen3-VL-30B-A3B-Instruct。默认T.7/P.8/K20/repetition1、C64、taskseed42、上游不传request seed、stop和18000cap保留。禁止为得到好分改变随机性。历史样本可作描述统计，不能转旧gate。

## 预冻结有限对照

同一对GPU，串行三fresh模型角色：B1旧通过Attention→C1当前Attention→R1回切旧Attention，各完整198题一次。保持所有其他推理源树、解释器/依赖、设备、argv/env、客户端和任务/评分一致。每角色独立进程/KV/评测UUID响应缓存，相同普通smoke/C8后开始GPQA，prefix开关始终ON；不清用户旧cache、不复制回答缓存。三轮全部保留，不因分数追加第三组/新split或挑轮。

这组优先回答同机同配置下版本差距及回切是否复现；若B1/R1不能稳定恢复，报告采样/调度轨迹或历史状态未复现，不能盲指算子。若稳定差异成立，下一阶段先拆Prefill与split两个因素，须另冻结有限契约，不直接宣称rootcause confirmed。全模型C1/C8位级一致不是正式阈值，GPQA唯一分数条件>=64；保留诊断差异不改passed。

## 隔离、恢复与安全

远端新唯一case：/public-flash/jinghao/qwen3-VL/20261028-qwen3vl-gpqa-controlled-opt12-opt14（授权根同/public-flash/jinghao/qwen3-VL）。在临停前完成命令/源码与配置归档、当前source/env/argv/身份取证、真实源码快照及挂载相等验证、恢复脚本冻结；独立模型容器从当前有效源码状态不可变本地镜像复刻，保持/public-flash和/data映射模式/传播完全一致。/workspace源码是各容器私有；只改角色容器Attention文件，原source文件不动。

源临停绑定当前PID1597993/ticks1146418910，先校验idle/API身份。仅给目标API及其已记录后代发停止信号，不能用泛kill。单控制器finally无论成功/失败均停止自己的角色服务，再恢复原容器当前Attention SHAf81、完整原argv/env/cwd/8030/prefixON；核验新source实例健康、普通smoke/C8、source/配置一致。重启使原KV内容和旧实例gate不保留，明确新实例，不伪造旧PID。无并发interrupt或恢复controller。

模型角色日志、GPU/graph配置/启动capture证据、普通smoke/C8、真实import和四仓源码前后/当前模型身份归档。没有直接replay计数时如实记录，不能从smoke推定数值次数。不得用额外自加bitwise门槛拒绝有效分数。>=64才按原acceptance issue/check签该测量实例gate，不转恢复源实例。三角色完成逐题配对及responseSHA比较，保留全部原生证据。

状态：preparing，尚未临停或启动GPU对照。工程规范v1已读综述，涉及既有厂商API薄适配回切与配置/Graph生命周期；不新增kernel/模型特化/私有数值加载，不修改上游vLLM。依据A1–A4、B1–B4/C1、E3及F1/F2/F3保持旧公开native API与既有dispatch；本次不是新可提交PR代码，pr_readiness=not_applicable-diagnostic-rollback。

执行前冻结控制脚本commands/control.py，SHA `fad876ca4e357fe2eff292fa958700e19e0dc6908814d83df5ba84b3d4d3fa0a`，子命令prepare只归档/创建不运行模型，start排他启动唯一run控制器，run才临停和执行B/C/R、finally恢复。挂载比较原工具commands/verify_mounts.py SHA `32adacf39859e88ad6e2dad04ada248a00b636c795fed67d34328f5264bec3e3`。不可变快照docker commit --pause=false，保存当前有效私有依赖和未提交源码，不暂停现服务；三角色均从相同快照创建，挂载逐项相等和未修改源树先核验，再只替换对应Attention文件。快照阶段不发生成请求。

启动观察沿用此前多次通过的normal observer，仅原调用前后记录源码/参数及capture/replay完成次数，无新增数值计算或RNG调用；本轮改为同时验证显式split1与缺省split0，原native只调用一次且返回同对象，图replay16后移除图/import观察器，首次native命中后移除该探针。先fake CPU契约测试，再要求两rank真实命中/capture/16replay/移除证据及smoke/C8，才跑正式流量；不把CPU测试当硬件证明，也不把计数当独立数值reference。所有角色采用相同观察流程，仅期望split值随版本变化。原source容器不安装/开启观察器，恢复用原env和原代码。

只读实际API usage显示两历史GPQA均198响应、prompt范围172..2899，只有1题prompt>=2048；旧版GPQA后日志确有PR638命中，不能因为大多数prompt短就排除该分支。两版本都出现18000输出上限，仅作为诊断观察，不提高/降低正式score门槛。后续控制三轮不得以这种输出健康情况否决有效score>=64。

准备v1仅在复制tools时因共享盘copystat元数据EIO退出，未进入source采集/镜像/模型停启，0对照请求。原control.py保留。修正为新commands/control_v2.py（SHA `bb2743baa329f7cdb5ab49bb30e0a0aa286701618864fabf3163a0dd9ed6d9be`），只在source-before/snapshot均不存在时恢复该准备阶段，以原字节复制+存在文件SHA/bytes相等核验替代copystat，忽略macOS `._`资源分支，不改变原runner字节、实验协议或门槛。后续唯一start/run将用v2，不重跑旧v1。

v2已完成有效镜像快照sha256:1c00be94c2fdad21519b8174589d53aa47f562077016eb52897a60acffb98e97及observer CPU契约测试；source writable layer约5.19GB。Docker新版CLI把--pause弃用提示混入stdout，v2将提示和imageID一起作为镜像参数，首个clone在创建前被invalid reference拒绝，0模型临停/0对照请求。原始snapshot.json和旧脚本保留。v3只解析该已存在快照的唯一sha256行，现场image inspect核验后复用，不重新commit，不改变模型/协议；克隆前要求Docker系统盘剩余>12GB，当前约18GB。记录仅证明requested --pause=false，不以CLI提示推定实际快照时的暂停状态；源API当前仍保持同PID，正式临停尚未发生。

修复准备命令commands/control_v3.py SHA `b36114aa7096c87824bb5a9bcbf556a5af7b623bc9273b9326d23655999b74b9`。v3取代此前待启动v2；只有v3 prepare通过、plan与单finally恢复协议指纹冻结后，才用v3 start/run启动GPU对照。旧v1/v2不再执行，未有任何GPQA对照轮。

v3已创建B1睡眠容器并通过挂载校验，随后准备尾部引用缺失局部raw变量退出；模型仍未临停、0生成请求。使用独立CPU-only commands/finish_prepare.py SHA `a7a6c856ff5aa546116dea0a0107c019b41b1b6ac87428a7dbc1c1d7f4b39991` 补完该尾部：复用并验证已存在B1无模型进程/image/mount/source完全相同，不覆盖已有证据；创建剩余角色与CPU evaluator、冻结每角色两份provenance和plan。control_v3.py的run/finally本身未改变，完成后唯一v3 start/run；不再执行任何旧prepare。以上均准备工具incident，不计GPQA轮次或精度失败。

准备已全部通过：prepared.json SHA `160f5b207ea7233316a4af6259533c340ea53d1fdd480da4ec7eb0eee819f99f`；plan.json SHA `95e3cc49dd5a62ca10c1794f42da906a2f076bb9a094945c3891bde3a922afd5`。三角色B1/C1/R1 source hash/import/versions/model/tokenizer与source exact、source快照谱系verified、挂载三项passed；每角色两份原生GPQA provenance一致且198题相同。observer CPU original-once/default0/explicit1/same-return/capture+16replay/移除测试passed，硬件证明仍须各角色实测。补查CUBLAS/CUDNN/HIP/NVIDIA/OPENBLAS/OMPI/UCX/MPI/LD_PRELOAD额外计算env均未设置，原safe env恢复清单无此遗漏。源服务仍原PID/源码，0准备生成请求。

最终唯一待启动命令：commands/control_v3.py start/run（SHA b36114aa…），锁manifests/controller.json；所有固定artifact将在run前再校验。当前显式授权覆盖本次源服务临停及单finally恢复，源文件本身不改。监控qwen3-vl-gpqa（30分钟）已建立，待写入唯一controller身份。

2026-10-28 11:57:49（Asia/Shanghai）唯一controller1313960/ticks1147059617已正常临停已授权source API1597993及其关联进程，未改source文件/容器。B1私有模型126/ticks1147061633同一时刻开始加载，后续native/graph/smoke/正式流量证据待本实例产生，不复用旧证据。监控已更新唯一controller和单finally恢复约束。

12:01:52（Asia/Shanghai）B1正式GPQA198/C64开始；此前本实例两rank native split1（显式参数、原native已返回、Plugin SHA4e12）和FGV真实命中、capture及16次原委托replay、观察器移除、普通smoke/C8、source/config前后核验通过。对应roles/B1/graph和results/startup-observation.json保留原始证据。正式流量无额外采样/seed覆盖，尚无最终分数；源服务目前仍临停，finally待本组终态恢复。

2026-10-28 12:16（Asia/Shanghai）周期跟进：唯一controller1313960/ticks1147059617仍活跃，无根failure/终态；B1全部198已发，177个unique HTTP200完成，原生进度176/198，尚无正式结果/分数。C1/R1未开始。没有重跑、改配置或中断恢复流程；源仍处本次明确授权的临停阶段。


2026-10-28 12:46（Asia/Shanghai）关键结果：B1旧Attention于12:36:11完整129/198=65.151515分>=64，通过。原生198响应/唯一题目/逐题分数、source前后及实际无sampling/seed覆盖由控制器核验；独立原acceptance.check_gate复核passed。B1已经按顺序停止，其gate只绑定测量B1实例，不转给C1/R1或恢复source。

B1结果SHA4b96150a4d5347decdba5110519ea6a470bc33063f634b3acb7cab7fe41d7f86，native3a7d5e805c6122de9ab49564c062946736facdd7fb0162d475633e907e837224，samples35ae9ab4e7445387f3f7765531cab5f9e3a751b2b0bfb211c19d4d53c3e6904c，gate13d6dbf59f9adbb5de939c5092a4398d106ead60bd8145314b1986de3191f37a；startup-observation9ca29963de52befc7db7ff682122a26bdc0312a27482eb5a19744ac5a54ce766，sampling-audit4125e6c8c1c2a75a57e86328a3e2a91491ecb4e2924fdd10a3bc8290120fed17。

与历史opt12对同198题逐题复核：doc/arguments全部相同，总分也相同129，但只有164/198逐题判分相同、完整回答0/198相同。因此这是此次新测量通过，不能说逐题/完整响应忠实复现历史，更不能单凭同分排除采样/批轨迹差异。

C1当前版模型82/ticks1147294077于12:36:34启动，12:40:26当前实例native/graph/smoke检查通过后开始198/C64；12:46 proxy198已发、158unique200完成，原生157/198，无最终分数。R1尚未开始。唯一controller1313960/ticks1147059617持续活跃，无failure/恢复终态；source仍按授权临停，后续保持原冻结顺序和单finally恢复，不提前确认因果或追加轮次。


2026-10-28 13:16（Asia/Shanghai）跟进：C1当前Attention于12:57:39完整119/198=60.101010分<64，正式有效失败，无gate；相较最初118/198只多1题，不据此认同一回答轨迹或代码因果。独立CPU检查198unique、strict perdocsum119、task/data/config原生provenance、source前后及两ranknative0/graph观察证据有效。

C1回执5890f308d6d7c646ef23dc11b4f6f8025e9a0257c75633ecb4a97d3fdd585ad8；native2fca412732a97e2ace4c8eaa3d156a386d9f55bb14705557f0dd7b381f571ccb；samples ef9d4b7ec48ee6903ca2505a11cdcd904524121ab98483435970fc05b39c698f；sampling8d8553910229cfb88e12ef2bbf9774f8e5303b11b4d9c23d14926913a4867bfe；startup6094d48d3af32e81562e5d40a83fe46d14a3cef715aac101413fc7ac69c90e70。

同题/arguments exact的配对统计：B1/C1两者对104、两者错54、B1单对25、C1单对15，全文相同0；最初118分组/C1两者对100、两者错61、最初单对18、C1单对19，全文相同0。保留采样和批轨迹不确定性；当前只支持版本相关信号，不把其中一个Attention子改动称根因。

R1回切旧Attention模型83/ticks1147422812于12:58:01启动，13:02:00通过本实例前置取证后开始GPQA。当前198发/176unique HTTP200完成、native175/198，暂无最终分数。唯一controller1313960/ticks1147059617正常，没有额外请求或改配置；本组完毕仍由同一finally恢复source f81/原配置/prefixON，不启动并发恢复。

## 三角色终态与恢复

B1=129/198(65.1515)、C1=119/198(60.1010)、R1=129/198(65.1515)，全部198题来源/样本/逐题和、源码前后、默认采样审计有效；B1/R1 gate仅绑定已停测量实例。completed SHA89d83b0a2800a3bebc0a25c1602ce7fc4a892398bee716f228b673fe665a2d2c；paired SHA0852439b8722fe4f5b5b66869cab60cfc5b02f2e0be6986270036df765c10f52。B/R各129但17/17题相互翻转，全文0相同；仅支持版本相关回切信号，不是确定性回答复现或Prefill/split任一根因。

13:40:15单finally恢复原source1697323/ticks1147653843，f81/原argv/env/cwd/prefixON，当前graph配置/smokeC8/models200及独立CPU只读审计通过。restore SHA52e14bf2a65a366b861651cc873adabd7751bb83d0aacc6e5672bc7adeffbf33；旧controller1313960已退出。下一项[diag-002](diag-002-factorial-bridges.md)补齐两个因素组合，不重放此组。
