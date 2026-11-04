# eng-066：PPU 完整 FlagGems-vllm MoE 入口

## 授权与预冻结范围（2026-10-22）

用户要求在 Plugin 平台判断中开放平头哥，直接调用 `fused_experts_impl`。本轮仅修改 PPU-07 的 `qwen3.8-flash-opt-ppu07-20261015` 中 `/opt/vllm-plugin-FL` 的 MoE 快路径及原有路由测试；不改全局 `PlatformFL.is_cuda()`，不修改两算子库、BF16 归约、i64/randn、PLE i64+CTA、QSA M16、黑名单和调优配置。不重启、不发推理/GPU测试、不访问8035、不提交或推送。

分类为 `operator/replace`：复用已有完整 thead MoE 实现，而非新增 kernel。旧路径的 NVIDIA-only `is_cuda()` 在 PPU 返回 false，故此前走分步 alignment/GEMM/activation/sum；历史 env065 回归并非本候选完整 API 的设备验证。

唯一生产变量：在原 NVIDIA 条件旁增加 `vendor_name == "thead" AND VLLM_FL_USE_FLAGGEMS_VLLM`。保留无 LoRA、SiLU、无 gemm1 clamp 三个限制；开关关闭时 PPU 仍走分步路径，NVIDIA 原两库选择不变，其余平台不扩大。完整 thead API 在非 naive alignment 时调用 `moe_align_block_size_no_tle`，但其融合、配置和临时内存策略可能与旧分步路径不同，不能由签名兼容推定数值/graph/性能等价。

## 实施与回退契约

- 原 Plugin HEAD：`a696859b9aa528dfd5b21f5da3403fdc16bac4cd`；现有 PR455 staged 改动和其他工作区差异全部保留，index 不变。
- 目标：`vllm_fl/ops/fused_moe/fused_moe_utils.py`；原 SHA `0e1dfd8482b0d38afae7d88c9fd6ac725a30078979d56a0a567e836cb7fcadb7`。
- 复用 `tests/unit_tests/ops/test_fused_moe_backend_routing.py`，不新增生产 helper 或独立测试文件。
- 外部证据根：`/mnt/nfs/users/jinghao/qwen3.8-flash/20261015-qwen38-flash-next-ppu07-container/engineering/eng-066-thead-full-moe-entry-20261022`。执行前保存带 SHA 的命令/候选，排他备份原文件，写入前重验原 SHA。
- 当前 API：Host1426766/start536664682/argvSHA c146e2da4762690185e9b3573c5f48796a5cb42aa2037de0d08d9ada40595010，仅核验8010，不操作进程。
- 回退仅指从本轮备份恢复这两个文件；不自动回退、不清 Git、不覆盖其他修改。

## 验证契约与停止条件

按本地 `inference-accuracy-evaluation / minimal-regression`，本轮仅 CPU 工程子集：实际 AST 入口 mock 调用、平台/开关/LoRA/activation/clamp 路由矩阵、实际 thead 签名绑定、语法与差异检查。禁止用 mock 声称目标硬件通过。检查失败停止部署并保留首错；目标源码、HEAD/index或服务身份漂移则停止，不静默覆盖。

设备及模型 `minimal-regression=incomplete`，graph capture、至少两次 replay、模型 smoke/C8、数值与性能均 `not_run`。候选仅可作为待验证磁盘源码保留；当前服务仍为旧加载实例，不签发/继承精度 gate，不声称已实际调用新完整 API。下一次获授权重载后需核对完整 API 的运行命中、graph和模型回归，再考虑性能。

## 执行结果

写入前 CPU：120 个路由/原有 guards 矩阵及原测试 AST 的6个入口用例通过（实际 apply AST＋mock，无生产库 import），实际 thead 签名接受调用参数。修复了测试新增 fallback 分支中二维权重夹具的 IndexError，首错 XML 保留；修正三维夹具后的两轮均126通过，原文件格式检查、5个脚本/源码 AST 语法检查通过。不把这些称为 GPU/真实 Torch/vLLM 集成通过。

待执行的唯一写入命令：在 PPU-07 Host 执行 `python3 <E>/commands/apply_source.py`。脚本 SHA `2f17cebd90f00f99cd38d77359c467656bd056ab54b8c7c8dc84ec61a6672249`；绑定候选 utils SHA `e787cdb8e5f09ef9d41d194bc2c9b563ad6445bd4323210225af1d5103f8fe6b`，原测试 SHA `dac76da92333676fe05820d0cfe5a30bb3d74ebc28327927a2188d92ae690b8f`→候选 `e6c0cb7f05b2cc33c71a8f2553464beb625a41f8cbf8bf1f836e4f344921ed72`。CPU source probe SHA `5510b55ecba68562a1cee10b6c7fe4786bf37c03176b0438093906ee92f66672`；脚本只备份/原子替换两文件、source/Git/模型元数据前后核验、8010只读health/metrics及CPU AST测试，无启动/停止/重启/推理。证据目录排他新建，owner0/755父目录、规范路径无symlink、约7.0TB可用已核。

首次执行在任何写入前触发 Git index 哈希保护，`FIRST_ERROR.json` 保留。只读核实是工具哈希口径不同：初检对 `ls-files --stage` 先 strip，得到2bf5d26c；source probe保留末尾换行，得到 `871bdbffa2c0b52bd93f482182837654b5f5bc8201d1cc456f5c35a4d664adf0`。同一份60974 bytes输出的strip/raw两种SHA同时重算均吻合，HEAD/状态和两目标原SHA不变，非真实暂存变化。只修正审计脚本预期为raw SHA，不改任何候选代码/marker；原尝试不覆盖。

更正工具后的唯一写入改在 `<E>/apply-002/commands/apply_source.py`，SHA `4a959b66659b8cd23513d8c642a656aa219826af1655d2d86fab3c930cba392b`。本次新证据/备份全部排他写入`apply-002`，原失败仍保留在父E。其余源码和CPU契约不变。

## 终态：磁盘候选已保留，设备回归待授权

`apply-002`完成，仅两目标文件变化。生产diff为一个注释替换＋平台条件6行净增加，不新增helper、不改全局platform判断。原路由测试扩展NVIDIA/昆仑/thead及开关两值共6例，关闭开关的thead断言进入原分步形状检查；外置CPU矩阵另外覆盖120组合，包含无vendor、MetaX、LoRA、非SiLU和clamp。容器回读SHA与被测AST payload相等，126/126通过；35条旧pytest的Python AST弃用告警，非算子故障。未执行完整依赖集成测试、GPU、graph或模型。

完整Plugin树差异恰为两文件；Gems/FGVLLM源码、关键修复、模型/tokenizer元数据、native graph源码、版本、三个仓库HEAD/index均未变。备份两原件SHA吻合，24份manifest成员大小/SHA全部核验；测试vendor快照精确绑定当前FGVLLM thead源SHA `807d12ce829343bcd4ef72e809d5c772dd9be4095db6e77adcaacd7810ca0f7e`。安装、环境、cache及PR959/982未改。

8010前后精确实例不变、health200、running/waiting/preemption均0，prompt3210/generated6158相等；0重启/推理/GPU/8035访问/提交推送。新磁盘入口尚未加载，运行服务仍旧分步MoE实例，不继承旧graph/GPQA gate。

关键外部证据（均在`<E>/apply-002/`）：

- `backup/utils.py`、`backup/test_routing.py`及各自`.diff`：完整回退原件/变更。
- `FINAL_SUMMARY.json` SHA `154a029bc306bb68cc940b5b84235ffe9fd6e824207031514f569f940c9444bc`。
- `manifest.json` SHA `9bd9f557b9bdfd588452affdd7cfd8a034e9551160641109c2dbd95d53b51ad6`，24文件已独立核验；不包含manifest自身或后写summary。
- `source-before.json` SHA `553def3d4c6281ce654efa52eb5c9106904cf3ec53b87472d6485b1244c8c2de`；`source-after.json` SHA `eb462f637777df7d683e66b4a671dbe85341c9428444c2ff77fe6097def049bc`。
- `cpu-tests-deployed.log/.xml`、`deployed-hashes.json`、`service-before/after.json`：实际回读绑定、126 CPU用例、同实例/请求计数不变。

决定：按用户要求保留磁盘候选；`engineering=passed-scoped-CPU`、`minimal-regression=incomplete`、`pr_readiness=experimental`，无新formal gate/性能结论。下一步须新授权后重载8010，核完整API命中、capture和至少两replay，再做小范围数值/模型回归；本轮不自动执行。

## 新授权：单次8010重启与10请求设备最小回归

用户2026-10-22明确授权仅一次重启8010，证明thead实际调用完整`fused_experts_impl`，检查capture及至少2次replay，随后2C1＋8C8；保留BF16/现有算子修复，不访问8035/全量GPQA/提交推送。该授权覆盖同一eng066磁盘候选，也加载env065后续Gems旧路径清退；不修改三库生产源码、不额外运行GPU微测或推理。

预冻结R=`<E>/model-regression-001`，private cache=`/opt/qwen38-eng066-thead-full-moe-20261022/cache`；沿用原10条短doc2/B请求，max2048、seed1234、温度1/top_p.95/top_k20/min_p0/presence0/repetition1/原stop、完整prompt/token，0重试/隐藏预热，先2C1完整token一致且FULL实际dispatch>=2才8C8。CLI与旧实例逐字相同，库从三规范/opt源码editable加载，开关1，PYTHONPATH仅本R bootstrap。新隔离编译cache保留旧cache不清理，不作为性能比较。

复用env065原控制器/eng053 HTTP与native graph helper，不执行旧mode。仅精确Host1426766/start536664682/argv c146e2da…接收一次SIGTERM，owned tree自然排空、8–15空闲后唯一新启动；180秒不排空或启动失败即停止，不追杀/重启或恢复第二次。readiness预算40min，首次输出异常停后续阶段、8C8在途自然保存原始HTTP bytes/headers/token/错误；不因诊断失败自动修改模型。

实际路径证明：保留8rank包/函数对象来源journal，新增完整fused_experts_impl对象来源；仅bootstrap注册目标thead模块已有`GEMS FUSED MOE`入口DEBUG日志的一次性handler，记录实际函数源码SHA及包含Plugin apply的栈，每rank首次命中后恢复原logger level并移除handler。不包裹/替换计算函数、不读Tensor值或额外执行模型。首次日志/编译证据只证明入口实际执行，不宣称逐kernel trace或完整数值中间态；它与native graph dispatch/capture证据分别核验。

结果范围为`minimal-regression`，bundle `804b60f96089a5f37ee76d40c1ba11405ed8e61b45940786b52e52ed7b91edfb`；10同短题护栏不是formal分数/困难题或性能验收，不继承旧gate。只在完成/失败/明显停滞/需处理时后台通知，正常编译不估ETA。当前：命令准备中，尚未停止旧8010或发请求。

执行前5命令已AST检查，日志handler CPU mock通过（实际命名的调用栈、首条唯一写入、原logger级别恢复、不修改数学返回值）。唯一新controller=`R/commands/model-control.py`，SHA `ff5ff1f047fdee59bd6193d937e518dc1a86686749cb04ce404b70f4c7a2e830`；origin_audit `541073164010790fd7180b984e23259e9e7d4922c9dbf4893466f867335c5bfa`；原eng053 helper `8c9c1e3485a12af2a5b1cc0a05cffc39bc77196411c8046ef9117d55767dd0f4`与source_probe `5510b55ecba68562a1cee10b6c7fe4786bf37c03176b0438093906ee92f66672`逐字复用。先只执行`--mode prepare`，核PREPARED/冻结源/launch/requests后仅一次`--mode launch`；此后只监控原`--mode run`，不重复调用。日志证明若capture期尚无记录可等2C1，但all8 actual-call缺失则不续C8、不追加请求。

prepare完成且二次核验：PREPARED SHA `7b22519d8b5d5cbf2e275503eb398823b913b9d2f0a3ef6e4f2f5c32bcf5841e`，source-before `097edbfba04717d004aeac74954ffb17e1bc640e7386cf1921d04fa37f16ccfc`（与apply002 source-after对象完全一致），requests `07e9533a4dfb3c139536fd138471749fa3e64ef3b20087db86d3704bb180c89e`，launch `b5524a882125e1634746dc61815d3b9833eab3e204d1d80d39691c46733a32d1`。pin047原字节SHA `61da24bb3e07a5fd19a43aee42843c63a1deaa404c74d62be70d7879f6ba8fa8`保留；唯一restart/launch marker此前不存在。沿用30分钟monitor `qwen3-8-ppu07-gpqa-c64`已从过期acc018提示更新为本R，只读/仅完成失败明显停滞需处理通知。下一步仅一次launch，后续不得重复。

唯一driver已launch：Host1692313/start537709226/argvSHA `a39c9dd1e1e0175918e88cd8129390e2f6971b53d0e217ec4bf5048e172cad1f`。旧API在epoch1792661266.768后仅一次SIGTERM，1792661268.807自然排空；1792661269.032唯一SERVICE_START_ATTEMPT，docker-exec1693667/start537709557。17:29+08八rank来源journal均生成，模型加载中；0新HTTP请求，READY/capture/replay/实际入口调用尚待既有driver，不能再次launch/restart。

17:33+08只读更新：8rank完整fused_experts_impl对象均为`flaggems_vllm.runtime.backend._thead.ops.fused_moe`，file及SHA807d12ce精确一致，三包根均canonical/opt，switch1/vendor=head；这只是实际对象加载，不冒充函数体执行。rank-call记录0、请求0、READY未生成、无source/call ERROR或DRIVER_ERROR；唯一driver仍S，原生编译进度已从Dynamo transform前进至range(1,8192) graph缓存。shm60秒提示伴随持续编译，不单凭提示判停滞。保持原driver自然等待capture→C1/replay/actual-call→C8，monitor ACTIVE；不再重启或改埋点。

18:03+08 heartbeat只读核验：新API Host1693692/start537709560/argvSHA `c146e2da4762690185e9b3573c5f48796a5cb42aa2037de0d08d9ada40595010`与READY和8010 listener一致，health200。READY SHA `d2d964f1e74a98cc90348adc09cf3f33d323f087c8098150db2cd77bcdf1fdb9`；PIECEWISE/FULL capture各7/7。8rank实际入口日志均存在：真实thead `fused_experts_impl` frame及Plugin `apply`栈、源SHA807d12ce一致，合并回执SHA `5388e26d93dac3a57f7dda672464261a9eaa4b51371f15bc376876058c561f7e`。首日志发生于启动期，仅证明8rank经Plugin进入完整Python实现，不独立证明每次kernel完成、各请求/各层命中或每rank replay trace。

两C1均HTTP200、最终B、580完整token且序列精确相等，prompt321、think-end位置270、末EOS248046；raw SHA/usage/非空final已独立CPU核验。C8前native FULL dispatch累计1145，回执SHA `2ef22239b44e72fdaf58f19a11e58bb27bb5f2808c1e5de278bd12b3f33e83af`；随后既有driver派发固定8C8，服务日志已有unpadded8/padded8/FULL count61。18:03:26快照为10派发/3完整HTTP返回/7在途（C8 seq5已正常B319），全部只有1唯一doc；该快照不是终态通过。18:02:28 metrics running8/waiting0/preemption0、KV约1.02%，后续输出继续推进，无首次异常或driver错误。BF16、i64/randn、PLE、QSA M16、alignment及新入口共9处关键源码SHA只读重验一致。FINAL_SUMMARY/FINISHED尚无，继续原monitor，仅完成/失败需处理通知；未追加请求/重启/源码变化/8035访问。

18:05只读发现原driver已自然退出，FINAL_SUMMARY/FINISHED齐全且健康范围passed；原summary SHA `4b5f0d498667224165699f126ca25db3f7b489e594020302fd1dabec94ca09e7`，原manifest SHA `5f43822bf8ef5c5e096f3aea3cf8d7866aa011d3d62121e0a4dda1f162fbd754`（106成员）。进入终态CPU独立审计：新保存命令`R/commands/cpu-terminal-audit-001.py`，预执行SHA `665655dbb6ac4290a3eb4799a90300668a9969d5aea62a2e7c04cc95b0f157b1`，只允许排他新建`R/cpu-terminal-audit-001`。该工具核原manifest/完整HTTP/token、8rank真实入口、capture/replay/C8、前后及当前源码Git、精确8010 health/metrics；补存日志尾部与调用栈所引用的8份新实例编译模块/相关源码，不读GPU、不发推理/修改服务。审计失败保留原错及中间结果，不更改模型或复跑模型。

## 终态：10请求最小回归与独立CPU审计通过

原driver在18:04:16+08完成并自然退出，18:11:47独立CPU审计通过。scope为同一短doc2的2C1＋8C8，共10请求/1唯一题；10份HTTP200、完整response bytes/headers/token/prompt已逐份核SHA、Content-Length、usage及原请求payload。全部最终B（诊断性gold匹配10/10），无真实HTTP失败/网络超时、None占位、空final、异常提前EOS或2048截断；没有FIRST_ANOMALY/DRIVER_ERROR/FREEZE_ERROR。各seq completion长度为`580,580,588,562,562,319,712,588,562,748`，两C1完整序列相等；总prompt3210/generated5801与服务计数及10次成功POST精确一致，无追加推理。

PIECEWISE/FULL capture各7/7，C8前native FULL dispatch1145，终态1878，其中实际unpadded8/padded8 FULL319；包含至少两次实际replay及真实C8。8rank首入口栈均含Plugin apply→FGVLLM thead fused_experts_impl，实际函数源SHA807d12ce一致。保存栈引用的8份本实例Inductor编译模块、入口/相关算子/native graph源码及映射SHA；此为实际入口与编译路径佐证，不是各层各步kernel trace或逐rank replay追踪。

原106个冻结manifest成员大小/SHA全部一致，所有原freeze日志均为本次补存终态日志的完整前缀；新增完整service/driver/docker-exec/events尾部另存审计目录，未改旧原件。source-before/source-after/独立当前source_probe对象完全相等，三库源码、HEAD/index、BF16模型、i64/randn、PLE i64+CTA、QSA M16、MoE修复与模型/tokenizer元数据均保持。新API1693692/start537709560/argvSHA c146e2da精确绑定，18:11 health200、running/waiting/preemption均0，保留当前8010运行。仅一次服务启动；0额外GPU测试/推理/8035访问/提交推送。

证据仍在`R=model-regression-001`：`FINAL_SUMMARY.json`、`FINISHED.json`、`manifest.json`与`terminal-evidence-001/`为控制器原件；独立审计在`R/cpu-terminal-audit-001/`，`report.json` SHA `34f27990fac62735f8c8fa02ae8ee40508711d189bb22c2b8da9c7d5b3284d51`，`manifest.json` SHA `1e2c12fad7722ca48f3196ddc29ccd9c5bb7180b8cebd90275f02438ef6cb28f`，附`responses-audit.json`、`source-current.json`、`compiled-and-source-index.json`与日志。审计命令SFTP复制首次因目标路径不可达未落盘，随后通过已验证SSH排他传输并核原SHA，仅执行一次审计成功；非模型/服务故障。

决定：`minimal-regression=passed-scoped`，保留BF16完整thead入口候选与既有修复。没有本轮formal gate、完整模型/困难题/60K正确性或性能结论；C8不同请求与C1 token不完全相同不违反本次冻结护栏。无完整逐层/状态/logits现场，不能宣称数值等价或全池因果。此轮monitor `qwen3-8-ppu07-gpqa-c64`已由产品工具确认删除，等待用户下一步，不自动重启/全量GPQA/性能测试。

## 后续明确授权的正式精度

2026-10-22用户另行要求复用当前8010做C64单轮全198题。已建立[acc019](acc-019-full-gpqa-thead-full-moe.md)，18:29原生评测启动，controller3724689/start538077673；API仍1693692/start537709560，0重启/0新增smoke。新provenance/preflight通过，分数待本轮结果；本段不改变上述eng066最小回归结论或提前签发gate。

2026-10-23 acc019已终态CPU审计：strict174/198＝87.8788%＜88%，结论failed-score、无gate。198唯一doc/396双filter行有效，187份完整正常响应（174正确/13错答）和11个异常任务TIMEOUT占位，累计50条真实API total timeout；未返回11题缺完整token/状态现场，尚不能归因完整MoE或BF16。原88manifest及新100文件/93source前缀回读SHA通过，source前后/当前、三repo HEAD/index及同一API保持，health200且空闲，原controller/eval/helper退出。完整证据与路径见同一acc019文档；本页短doc2最小回归仍为passed-scoped，不升级为正式精度通过。已删除本轮GPQA monitor，保留当前BF16 8010，等待方向，不自动复测/修复/切回FP32或推进性能。

后续用户仅授权分析原件：[11题超时定位](acc-019-full-gpqa-thead-full-moe.md#11题超时的已有证据定位2026-10-23只读分析)发现相邻第二C1及全量服务日志明显慢速，完整入口的MoE选参/转置缓存/小M分支与旧分步路径不同；结合8题旧60K及3题旧长响应，主要解释为性能回退放大原有长推理，撞上每次7200秒时限。该关联证据不等于具体kernel因果隔离、数值等价或正式性能结果；C8整批差距较小，不能泛称所有场景慢3倍。未执行新测试/重启/源码更改，当前入口保留不动，failed-score仍阻止晋级。

继续CPU分析将优先级收敛到4项模块级转置缓存对48层96权重的持续淘汰，原函数AST/mock三轮均100%miss；现有全部vendor MoE编译变体对应转置布局。若复制固定进graph，每步可有很大的额外全权重流量，但实际节点/时间比例仍缺证，不能称根因confirmed。G1宽N/shared是第二独立变量，G2并非所有参数更差。完整报告/限制与SHA见[同一acc019记录](acc-019-full-gpqa-thead-full-moe.md#阶段结果首要嫌疑收敛至4项全局转置缓存选参是第二独立变量)，仍无新GPU/推理/生产修改或服务操作。
