# acc-017：PLE i64＋CTA同步修复后单服务C64全量GPQA

## 授权与预冻结契约

用户2026-10-20要求使用64并发跑全量GPQA；此为新一轮明确授权，不受旧052局部10请求限制。不授权重启/恢复模型服务、改源码/采样/埋点、自动重跑整轮或访问8035。本轮使用本地inference-accuracy-evaluation `formal-gate`，覆盖accdiag051/052的PLE修复和当前FP32/i64/QSA M16组合。

PPU-07，优化容器qwen3.8-flash-opt-ppu07-20261015，8010/TP8物理8–15。初始只读API593716/start519643298/argvSHA5744d99971adc1f0e9c1885acb61cd9910ccc7fd7adb84f33a11d009702c007e未变，health200、running/waiting0、prompt3607/generated56310；052 driver已退出，10请求回归/CPU审计通过。故复用当前已预热健康实例，不重启。首次普通Ansible连接检查因本地RPC沙箱启动失败，限定PPU-07的授权外部只读检查随后通过；这不是远端故障。

正式任务gpqa_diamond_generative_cot、limit0、198唯一doc、C64、metric exact_match,strict-match、threshold0.88。temperature1/top_p0.95/top_k20/min_p0/presence0/repetition1/max_gen_toks60000，evaluator seed42、API默认seed1234与原stop；API retries3/eval retries0/timeout7200，返回完整tokenIDs/prompt。配置同旧正式契约，独立评测容器/UUID/本地响应缓存，不复用旧答案。诊断性输出健康不另设分数门槛。

## 执行与证据计划

新CASE=/mnt/nfs/users/jinghao/qwen3.8-flash/20261015-qwen38-flash-next-ppu07-container/accuracy/acc-017-full-gpqa-ppu07-c64-ple-fixed-20261020；新eval=qwen38-eval-ppu07-acc017-c64-20261020，规定flageval-llmeval:v1镜像。任务根已只读核实际规范路径、权限和约6.98TB可用空间，新CASE不存在。命令先保存CASE/commands并核SHA，禁止覆盖旧结果。

只复用维护版formal_accuracy.py包装原始test/Accuracy_test/llmrun.py和既有正式执行/单次launch/冻结函数，不新增评分实现。准备时重新核当前镜像挂载、全8worker来源/实际graph、私有051 PLE、047 Plugin FP32、env041 Gems i64/randn、QSA M16/normal_及index_select黑名单、模型/tokenizer指纹。新服务manifest不得拿旧manifest换PID。两次无推理provenance一致后冻结schema3契约，运行--preflight-only；其后创建/更新同一30分钟heartbeat，再唯一launch。

实际observer和服务日志在旧acc016/diagnostics/accdiag-052-ple-fixed-model-20261020/runtime-001。新byte/inode窗口与非journal文件边界独立保存；旧052 frozen目录不修改、不把旧token或旧marker作为本轮198题现场。score_requests为空，本轮不加重型逐层/QK/logits/state取证；native INFO含完整解析后API响应/token而不是HTTP wire bytes，边界/状态字段按实际已有记录报告，不虚称完整GPU首次因果现场。FlagTune启动期default fallback告警及旧043 logits差异保留，不为消除告警修改服务。

运行中只读监控原进程/8010 health/running/waiting/KV/preemption、最近产物和新错误；唯一完成题数只据samples去重或可核验缓存映射，不用多filter行数/在途/排除None的helper分数替代。无依据不估ETA。普通错答/空final/60K截断保留且继续收集，不自动重跑；服务故障只保全已有证据，不恢复。新异常及时通知，任何进一步埋点或重启先等方向。

终态核198唯一题、每filter完整且内容一致、原生results/samples/来源、服务/source前后一致及原控制器/evaluator/helper退出；有效score>=.88才报告维护acceptance签发gate。低分failed-score，故障污染/缺证incomplete；旧acc016故障污染38/198、acc015164/198 failed/no gate不改。更新本记录/state/README后暂停heartbeat，不自动修复或重测。

当前状态：本轮正式198题已于2026-10-20 18:40:45终态，strict177/198（89.39%）>=0.88，原生gate签发且只读复验通过；7条60K reasoning-only仍保留为诊断观察。8010原实例健康空闲，heartbeat已PAUSED，等待用户方向，不自动重跑或改服务。

## 已保存执行副本，尚未正式启动

控制器保存为CASE/commands/acc017.py，SHA e78cddf7c056b7573cdf804684423846be7e9945227012e0fbc30a0200601b12；CPU source_probe.py SHA11dc8c482389c83d5e97bfa48816a12e4892490509fead9181b0068009589504。以SHA核验后的旧正式编排函数为基础，仅替换本轮CASE/eval/实际052身份/051 FGVLLM导入和回归证据；runtime仅查精确API与8010 listener，不使用docker top或访问8035。Skill完整bundle SHA6e94a080dd3b64544c535e1fd4bda506f55516374d14d0f8ca6aa148bba2c7b2，显式formal-gate。

本地临时控制副本AST通过；传输仅排他创建新CASE及commands/evidence，并校验逐文件SHA。两次普通SFTP读取因堡垒机文件路径解析失败，没有执行旧脚本/产生新评测；改用已验证SSH只读提取后apply_patch生成新副本，不改变SSH配置或关闭host key检查。准备命令为`python3 CASE/commands/acc017.py --mode prepare`，无模型请求；成功后唯一`--mode launch`派生原`--mode run`。每阶段排他marker拒绝重复；若失败先核证据，不自动重新prepare/launch或重跑模型。

## 准备通过与单次启动

prepare成功：当前原API/私有源/镜像挂载/空闲检查通过，新eval已创建；两次无推理provenance逐字相同，SHA c39228d57fd391a9f723496f54fa2fb3f0d7aeb17810a2edf63559152dc63523，与旧正式198题来源相同。wrapper --preflight-only明确通过、尚未评测。Skill inspect只输出JSON不落receipt的本地工具用法差异已在任何SSH之前修正，随后排他部署成功；没有远端prepare重试或模型流量。

PREPARED SHA3dcf2ee657ea69632f8dbd1591149343e3e962be789834777b90ca449b9f04dd；config ce88080896f2fc67dd06bc5be2b7a6c19402c3fbd5d34313e1ee0b07503779d6；contract 9e303ff126a6fe18e3b3f2a47ae5dd2b5d0e32a9d083dedb38a302ae3ef16415；新service manifest 6c5e06559f0d7c2e8ded1cbfd3b54a56d7fdbdc51ce40d2c1feb19c8580bbb62；实际source-before 8dc7f0265b20e068c1c193a91ff4b54dd94173e8cb6e0c250fad2812ff99c8b4；observer boundary 477391d4fd567b739aa0e0af828ed447c59c416097322e03faacbb75158e7961；Skill receipt 4dbe821d2165f2314d0e9f5ad5eff70d9c249dad5210869a3119023c5b01e31a。

CPU显式实际路径核为Plugin047、051私有FGVLLM、env041 Gems（5.5.0.dev0+gf0aa7f121.env041）、vLLM0.24.0+empty、torch2.10.0/FlagTree0.7.0+ppu3.6；不是Docker继承旧PYTHONPATH解析。完整源码树指纹写入新manifest。两类capture7/7及每rank实际replay下界16000来自同一052现实例，不跨实例借用，不宣称精确总次数。

同一heartbeat qwen3-8-ppu07-gpqa-c64已由产品确认ACTIVE，名称Qwen3.8 PPU07 acc017 GPQA C64，原30分钟频率/当前会话保留；通知仅实质进展/首次异常/完成/需处理。prompt只读核本轮CASE/原进程，不执行prepare/launch/run、不访问8035/追加/重启；终态冻结/更新记录后暂停。上述门禁通过且监控已绑定后，仅执行一次`python3 CASE/commands/acc017.py --mode launch`，不自动重复。

## 已实际启动，进入原生C64生成

唯一launch成功，控制器Host2010231/start520050786。FORMAL_STARTED北京时间2026-10-20 16:24:42，原生请求从16:24:58开始；新UUID `2746611dabfd487698b60bd1e4ea60e2`，本地SQLite缓存明确Cached requests0/remaining198，配置C64、198全部题目、max60000和原采样均已从实际启动日志核验。上下文构建100%不是答案完成数，helper初始0/198也不是正式分数。16:25:19只读8010 health200、running64/waiting0/preemption0、prompt20056/generated56375持续推进，CLIENT_ERROR/FINAL_SUMMARY/FINISHED均未出现；在途不当完成，暂无可靠ETA。

结果根为CASE/results/Qwen3.8-Flash-Next-ppu07-acc017-c64-ple-fixed/2746611dabfd487698b60bd1e4ea60e2/。服务不重启、当前源/采样/缓存配置不变，不访问8035；原生wrapper/evaluator/helper属于同一eval链，不是多次正式尝试。任务元数据仍有do_sample=False兼容字段/未分词长度提示，实际chat API生成参数明确temperature1/max60000，沿用已核定的原生接口，不为去掉提示修改采样或重跑。

此后只读监控既有客户端直到终态；正式198题结果未知，不用旧38/198、164/198或052的10/10给当前分数。保留全部原生解析响应/token与新日志窗口；无本轮完整逐层/GPU state现场时如实报告缺失。

16:26:38交接只读：同API/控制器身份不变，native wrapper2010746、evaluator2013531、helper2013532健康，日志50831bytes推进；running63/waiting0/KV7.22%/preemption0，prompt29317/generated92207。没有执行ERROR/Traceback/database-locked/非法访存行或CLIENT_ERROR/FINISHED；未核验完成唯一题数，不由running63、日志字节或INFO行数推算完成。新分数仍pending，继续原30分钟有界只读监控，不重复launch。当前案例YAML/实验ID/文档链接和git diff --check均通过；未修改公共runner或模型源码。

## 终态：177/198通过正式阈值，7条60K问题仍存在

2026-10-20 19:18–19:22（北京时间）只读终态审计：FINISHED实际时间18:40:45，wrapper退出码0，控制器/wrapper/evaluator/helper原进程均已退出；正式启动到终态约2小时16分03秒，原生评价计时8135.638秒。8010仍为API593716/start519643298/原argvSHA，health200、running/waiting/KV/preemption均0。没有新增推理/重启/修改，没有访问8035。

原生strict-match为**177/198 = 0.8939393939393939（89.39%）**，达到预冻结0.88阈值。samples共396原始filter行，但只有198唯一题；strict-match与flexible-extract各198，每个(doc,filter)恰一次，跨filter的doc/resps/target/arguments无冲突。strict错题doc17/32/69/71/76/81/88/89/90/102/106/113/127/129/130/145/147/160/164/167/171；其中7条空final和14条有final错答，均保留在198分母内，没有排除None后计算子集高分。

198个不同原生API响应全部完整保存，token长度和usage完全一致、prompt长度也与API prompt IDs一致；API返回的prompt逐题唯一绑定原生samples，原始content与samples一致（None在评测层变为TIMEOUT占位）。191条正常stop/非空final/think-end/EOS，7条为**doc71/81/88/127/145/147/164**：均生成60000 token、finish=length、content=None、非空reasoning，全部未产生think-end248069、也无最终EOS。没有提前EOS、真实HTTP失败或网络超时；原生n-samples.timeout=7反映上述占位，不等于7次HTTP超时。

首次60K是doc71，18:22:56，API `chatcmpl-8331bfc336fd32d3`，formal-run.log物理第629行；其后doc81第633行18:23:25、doc88第636行18:24:01、doc127第642行18:30:57、doc145第645行18:35:51、doc147第648行18:36:56、doc164第654行18:40:29。完整解析API对象和60000原始token仍在本轮日志，固定文件21545316bytes，SHAeae006a81312a356752339251902f381366537b370e83739795d139160f63c92，最后更新18:40:38；不是wire bytes。对已冻结rank0采样记录逐token核验，全部198份API完整序列均匹配non-discard前缀，差异0；少数API末尾之后0–1个额外内部token不冒充已发API。故这些7条确实在到达生成上限前没有think-end，不是最终答案被展示层隐藏的证据；不据此宣称具体算子根因已定位。

完整source-before/source-after逐字相同（SHA8dc7f026…），19:20 CPU重新核当前完整source仍一致，原服务身份/私有051 PLE＋FP32/i64/QSA M16/黑名单/固定调优未漂移。维护acceptance原生gate只读`check`返回0/verified，未另签发或覆盖gate；正式通过条件仅为有效score>=threshold，7条输出健康观察不另否决通过。

控制器已复制本轮服务日志和8rank新窗口至`CASE/diagnostics/observer-delta/`，observer-manifest SHA2deff6ca6f7ed1db66334ae2bc394bf9f13adbd58600555aa730955b6657be7a。9份实际文件大小/窗口长度/SHA全部独立通过；8rank各581条显式replay、末服务累计count90368/step90632，解析/异常事件0。完整可读新服务窗口与后续只读检查无非法页/非法访问/NaN/执行错误。该轻量观察器没有完整逐层/QK/logits/state张量，也没有实际generic/packed索引事件；不能宣称覆盖PLE10486/generic20972，不能宣称7条不收敛或历史跨负载logits差异已修复。

原始产物（以下CASE即本记录的唯一远端case）：

- `CASE/results/Qwen3.8-Flash-Next-ppu07-acc017-c64-ple-fixed/2746611dabfd487698b60bd1e4ea60e2/gpqa_diamond_generative_cot/Qwen3.8-Flash-Next/results_2026-10-20T10-40-31.592103.json`，SHA6a5649dc386df1ebf383399b231e5ce8aa834d174273d13c783c3da95bceb199。
- 同目录`samples_gpqa_diamond_generative_cot_2026-10-20T10-40-31.592103.jsonl`，SHAc330c17d7f56337ccfff67f17545def66d1f4704bbc5c1c3a34bd4affcc319bb。
- 该UUID根`run-record.json`，SHAee1f3634b697439bc8bba0436b49dbe70cc5b2ae16ec2d34736909a3a12bb183。
- `CASE/evaluation/accuracy-gate.json`，SHA1605b3513cb2ea7a2f6e47c438c64fc19621664c6e9151d6ac4ad1c5fded0b31。
- `CASE/FINAL_SUMMARY.json`，SHA6acef289b2d9abca9285e0fe4d403b5e907881dd24f305026e3acbab12125797；`CASE/FINISHED`及`CASE/evaluation/formal-run.log`保留原件。

两项只读辅助审计限制如实记录：终态SQLite值不再能由旧阶段safe_pickle_string解码，得到的“0/198”不是模型分数，已弃用并改以原生results/samples计数；最初按Unicode splitlines拆JSONL误将字符串中的Unicode分隔字符当换行，引发审计JSONDecodeError，改用物理行读取后396行全部合法。两者均未改原件/模型/runner、未重试评测或推理，不影响原生gate。

产品已确认heartbeat `qwen3-8-ppu07-gpqa-c64` 为PAUSED，保留原8010运行，等待用户方向。当前绑定解除正式分数阻塞，但没有执行性能测试/新定位或全量重测；旧acc016故障污染38/198、acc015164/198 failed/no gate不改，组合通过也不独立证明每项改动的数值收益。

## 第三次heartbeat：180唯一题已完成，仍在运行

2026-10-20 17:55:34（北京时间，启动约90分52秒）只读SQLite/冻结prompt映射核验180唯一题完成、无未知key/重复doc/None/TIMEOUT。已完成子集strict168/180（93.33%），错题doc17/32/69/76/89/102/106/113/129/160/167/171；剩余doc15/48/64/71/81/88/90/93/94/115/121/127/130/145/147/164/168/185在途，不把它们归为reasoning-only或超时，不估ETA。正式198题分数/gate仍pending。

原生API日志180个不同response ID均finish=stop、非空final、含think-end且末EOS，完整token长度匹配usage；completion范围172–41635，无提前EOS/60K截断/真实HTTP失败或解析错误。固定日志前缀13055264bytes，SHAe3f8735587110ea31784dc5618e1068e703d138828cd326bc46bed133cd5a462，最近更新17:53:23；日志是解析后API对象，不是wire bytes。新服务日志窗口149749bytes无错误。

17:55:27原API/控制器/wrapper/evaluator/helper精确身份均未变，8010health200、running18/waiting0/KV32.98%/preemption0，服务累计prompt83322/generated2107763（包含旧052）。FINISHED/FINAL_SUMMARY/CLIENT_ERROR/exit.code均未出现；保留原评测自然排空，不访问8035、不重启/追加/重跑。当前仍无正式完整逐层/QK/logits/state证据，不能由输出健康证明实际PLE10486/generic20972边界已覆盖。

17:56:08补核完整source与before一致、控制器SHA不变；8rank本轮新窗口均有337条以上显式FULL replay记录，当前服务累计count59136–59264，非本轮独立总次数。顺序读取各rank最后step59347–59418持续推进，不是数值分歧证据；无JSON解析/异常事件、无FIRST_ANOMALY/STOP_DISPATCH，仍没有实际索引事件可证大边界覆盖。继续原30分钟只读ACTIVE监控，待终态后冻结并暂停。

## 第二次heartbeat：159唯一题已完成，仍在运行

2026-10-20 17:28:32（北京时间，启动约63分50秒）只读核验原生SQLite：159条key均映射到本轮冻结198题，159唯一doc、无重复或未知key，None和TIMEOUT均0。已完成子集strict为150/159（94.34%），错题doc17/69/76/89/106/113/129/167/171；仍有39题未完成，不能作为最终198题分数或gate。阶段分母未排除任何完成响应，正式score/gate仍null。

17:28:59原生API日志159个不同response ID全部finish=stop、非空最终content、含think-end且末EOS，token长度与usage一致；范围172–23288，无提前EOS/60K截断。固定日志前缀8360612bytes，SHA1e35327f8110f43ca24b87c43372be27dd1c23457242526428f0450c54623c15，最近更新17:27:42。这是解析API对象和完整token，不是wire bytes。未返回的39题不能归为reasoning-only。

17:27:04原API593716/start519643298、控制器2010231/start520050786及原wrapper/evaluator/helper身份均未变，health200、running41/waiting0、KV41.00%/preemption0；服务累计prompt83322/generated1683228包含旧052，不冒充本轮独立token量。原生执行错误0、服务新窗口106261bytes错误0。17:28:15完整source CPU指纹与before完全一致，控制器SHA未变；8rank新窗口各215条显式replay记录，末count43520为服务累计。17:28:59各rank尾部step44161，日志继续推进，无新异常或FIRST_ANOMALY/STOP_DISPATCH；无FINISHED/FINAL_SUMMARY/CLIENT_ERROR，不判停滞、不估ETA。

仍未取得generic/packed实际索引事件，不能证明PLE10486或generic20972边界被覆盖，亦无本轮完整逐层logits/state现场。只读监控未新增推理、修改或重启，0次8035访问；保持原heartbeat ACTIVE，终态再核198题、服务/source绑定与原生gate证据。

## 首次heartbeat：97唯一题已完成，仍在运行

2026-10-20 16:57:41（北京时间，启动约32分58秒）只读CPU核验：原生SQLite97条key全部映射到冻结198题prompt，无未知key、无重复doc，确认97唯一题完成；97条均为字符串，没有None或TIMEOUT占位。按原helper strict抽取计93/97（95.88%），错题doc17/106/113/129。这个分母包含所有当前完成题，未排除None；它仍只是已完成子集的阶段值，不是最终198题strict-match或通过结论，正式score/gate保持null。

同窗口原生INFO解析出97个不同API response ID，无解析失败；完整token长度均等于usage，全部finish=stop、非空final、含think-end、末EOS，无提前EOS/空final/60K截断，completion范围237–13473。解析日志固定前缀2945441bytes，SHA05d86a50e126c4ba30ceb8536a36b6edd9d7cbb14fc9d96db3ec15ec9e9fba1a；这是已有解析API对象，不是HTTP wire bytes。本次只用现有Arrow数据文件CPU只读映射和SQLite mode=ro/query_only，不加载模型、不改响应缓存；一次辅助命令在本地shell引号解析阶段失败后改用安全stdin读取，未发送推理或执行评测重试。

16:55:29健康快照：API593716/start519643298、控制器2010231/start520050786、wrapper2010746/start520050938、evaluator2013531及helper2013532/start520051753均为原进程；health200/running64/waiting0/KV32.21%/preemption0，service prompt66218/generated867201。原生日志16:55:27继续推进；新服务日志窗口53804bytes无ERROR/Traceback/非法页/非法访存行，native无数据库锁/HTTP异常/执行ERROR。CLIENT_ERROR/FINAL_SUMMARY/FINISHED均未产生，尚未终态、不估无依据ETA。

16:58:36补核8rank本轮新窗口：各有109条actual-cudagraph-replay-complete显式记录，最后count29952为当前服务累计计数，不冒充acc017独立总次数。日志逐步推进、无解析错误/异常事件；顺序读取时last step30081–30112不是rank数值分歧证据。FIRST_ANOMALY/STOP_DISPATCH不存在；当前完整source指纹重新CPU核验仍与本轮before完全相同，控制器SHA未变。本窗口无generic operator-pre或packed实际设备索引记录，PLE10486/generic20972覆盖仍无法证明，不能用scheduler block ID或“没有错误”代替地址边界验证；也没有新的逐层logits/state比较。

继续原30分钟ACTIVE只读监控，只在实质进展/首次异常/终态或需用户处理通知；本次0新增推理/重启/源码配置更改、0次8035访问，旧正式分数不改。
