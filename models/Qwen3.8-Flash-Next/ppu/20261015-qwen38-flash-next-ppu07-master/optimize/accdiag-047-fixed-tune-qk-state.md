# accdiag-047 — 固定调优配置、doc71 Q/K RMSNorm 与初始化边界

2026-10-20后续正式组合验收：[acc-017](acc-017-full-gpqa-ple-fixed.md#终态177198通过正式阈值7条60k问题仍存在)保留当前047固定调优/观察器并加载051 PLE修复，177/198（89.39%）通过0.88阈值，原生gate绑定核验通过。仍7条60K reasoning-only；本记录的旧043差异/原因置信度不因此改写，不把组合通过当047独立数值或性能证明。

## 范围与门禁（2026-10-20）

用户授权仅8010增加窄埋点、固定调优并重启一次；不访问8035，不重跑GPQA。
按 `inference-accuracy-diagnosis` 与 `e2e/accuracy minimal-regression` 执行，accuracy bundle
`6e94a080dd3b64544c535e1fd4bda506f55516374d14d0f8ca6aa148bba2c7b2`。

- 固定两条相同doc71前缀343 token、串行C1、max_tokens=1、零重试、无额外推理预热。
- 只对已核验API3385225/start513345302执行一次SIGTERM，自然退出后启动一次；失败不自动恢复。
- 私有副本保留attention/MoE FP32、Gems index/index_put/randn i64、QSA M16；不改安装或共享源码。
- 固定Inductor候选选择，不按计时择优：合法候选最小warps、优先R32、再小X；关闭动态R-block及coordinate-descent。
  Gems/vendor配置保持当前快照。记录选择和实际首launch，不能以配置文件代替命中。
- 仅两条请求捕获Q/K norm完整输入、weight、epsilon及输出；选中GDN conv/SSM状态、实际索引/flag、清零后chunk输入及写回；PLE选中conv状态；最后token逐层边界、完整logits/prob/noise/RNG/API tokens。
- 预清零未初始化字节非有限不当故障；有效清零后state/output非有限、真实索引越界及输入不符为异常，保留首次marker与已产生原件，不扩请求。
- 每rank窄张量预算512MiB，旧sampler预算128MiB。不转储全状态池。

## 比较与限制

043与045 input/position/seed/noise一致、raw logits最大差1.1875；Q/K RMSNorm R32/R64为可疑归约边界，尚无因果结论。
本轮两个请求固定同一调优配置，记录第一/第二次状态与中间值，并CPU离线对比旧043/045 logits。
观察边界会改变fusion/编译分段及执行时序；不能把新旧差异自动归为原kernel bug。
两条fresh C1/max1不能保证两次graph replay、C8或60K收敛覆盖；缺项记incomplete，不追加请求。
旧acc015 164/198 failed-score/no gate保持，不能恢复性能优化或签发新formal gate。

## 执行状态

CPU准备通过，PREPARED SHA `282aabc6d37b18d961c594a7afc4ea8e03ae10e07002cb210e5bf64fa443417a`。
源/镜像/挂载一致，QK AST剥离观察语句等价；CPU18项正反例通过，CUDA_initialized=false。
CPU导入编译器查询设备数时在空CUDA_VISIBLE_DEVICES下产生unknown-error警告，未初始化CUDA、未进行GPU测试或模型推理；不作为模型故障。
probe SHA `3c44d919a980d56ea2e0c63b271eeed2f905c08faecb3a303cabc87c98ae9c01`；
pin SHA `61da24bb3e07a5fd19a43aee42843c63a1deaa404c74d62be70d7879f6ba8fa8`；
controller SHA `0874ad12617e33ca7c7e58612a506f9964201eb91c6ecb92a116bca3b6b0be1e`。
已进入唯一授权重启步骤，随后只监控同一driver。旧heartbeat保持PAUSED，使用前台进度。
远端命令先保存至当前CASE/commands，随后CPU AST/源文件/候选选择/假输入契约检查，全部通过才使用唯一重启机会。

产物根：`/mnt/nfs/users/jinghao/qwen3.8-flash/20261015-qwen38-flash-next-ppu07-container/accuracy/acc-015-full-gpqa-ppu07-c64-current-i64-qsa-20261018/diagnostics/accdiag-047-fixed-tune-qk-state-20261020/runtime-001`。

## 终态：新增观察路径触发OOM，原数值问题未覆盖

09:28:16+08 READY，两类graph各7/7，all8来源/48MoE FP32实例绑定、12QSA/36GDN/1PLE观察器检查通过。
新8010 API1302306/start517498709，argv SHA与旧实例一致。原API一次SIGTERM自然退出，无其他信号；唯一driver1310020/start517500718。
第一条343前缀请求09:28:16.924派发，09:28:23.700 HTTP500；第二条未派发、零重试/零补发。

首次排他marker：09:28:23.677431+08、TP3、step1、`narrow047-forward-error`。
栈已明确：新增 `probe047.py:selected()` → `pool.index_select(0, idx)` →
FlagGems `index_select.py:67 dim_compress` → `shape_utils.py:223 inp.permute(order).contiguous()`，
尝试分配 **24.22GiB**，当时只剩 **12.98GiB**。本意只选一条SSM状态，但实际算子先把整个池连续化。
这是本轮新增取证路径引起的资源故障，不是原Q/K归约、NaN、非法访存或状态初始化错误的证据；本次故障机制由栈和源码确认。

已保留原始HTTP500、请求与完整prompt、8rank实际输入和embedding末行共16PT、首次marker、全服务/各rank/调优/客户端日志、源码及编译缓存。
**未取得**GDN选中状态/实际索引、清零与写回、Q/K输入输出/归约中间值、logits、概率或生成token；失败时根本未返回token，不能补造或声称完整数值现场。
客户端和服务自然退出，09:29:00 FINISHED/FINAL_EVIDENCE已生成；当前8010无listener。没有第二次重启、恢复、额外请求或8035访问。

下一方案：先以已读CPU索引对pool做单行`narrow`视图，再直接拷CPU并在CPU拼接，不再调用GPU `index_select`、全池contiguous或GPU索引运算。
这只作为CPU检查的修正方案，尚未部署；重新恢复8010需要用户新的明确授权。原精度原因仍not-isolated，本轮minimal为incomplete，无formal gate，旧164/198 failed不改。

终态审计 `failure-audit-001/report.json` SHA
`55bbaa3b0e0f2b835b30ee258c672f186b3c4c39e23e937b162e526466e2e96a`：
16PT实际输入无问题且embedding末行有限，124冻结项与10471缓存成员SHA通过；client退出、8010无listener、源码前后一致。
CPU切单行再拷贝的3项检查通过（非连续layout/精确选行、仅选中行存储量、源变NaN后快照不变）；仅CPU proposal，未部署、无新增GPU或推理。
全8rank冻结FX各96条FP32 attention/MoE归约与2条原有BF16 embedding归约，未回退FP32实现；i64和QSA M16源SHA仍一致。
审计manifest SHA `2fd1b4b05dd3b9ed61bbbcf00b2a6d33cffc7533a40b4921412445b01a46f42d`。

## runtime-002：用户授权黑名单回退后继续（2026-10-20）

用户明确“把index_select加入黑名单然后继续验证”。本轮仅追加
`VLLM_FL_FLAGOS_BLACKLIST_APPEND=normal_,index_select`，保留平台/模型默认黑名单；不改观察器、不部署单行narrow方案。
复用同一私有047源码与固定调优缓存，旧runtime-001冻结原件不覆盖，新HTTP/日志/PT写runtime-002。
先核验8010仍无listener、原driver已退出和物理8–15可用，再仅启动8010一次；不访问8035或卡0–7。
两条完整相同343前缀/C1/max1、原采样/seed不变、零重试/隐藏预热；首次异常即停止补位，不重跑GPQA。
准确区分黑名单配置、实际生效与新数值结果；单纯启动成功不当恢复完整精度。
原失败原因和未覆盖项保留；这轮不签formal gate，不扩大请求预算，heartbeat仍PAUSED，前台监控。

runtime-002在启动前CPU AST测试缺lineno而停止，0模型请求/0服务启动，原文件保留；仅修检查脚本为`ast.fix_missing_locations`，实际续跑改为独立`runtime-003`，仍归本实验。
新controller `commands/accdiag047-blacklist-control-v2.py` SHA
`30b6428a76d94768ca38e2901a0fdf0c0185750a32561aec5425c075039d4cdd`；
PREPARED SHA `116fe60c457362077f72146728c1916624ea6fb20e3781a62a5b72f1242275dd`。
CPU真实黑名单解析检查通过，既有默认sentinel保留并追加normal_/index_select；镜像/挂载/所有源SHA与001一致。
确认8010无listener且原driver退出、仅8–15资源门禁通过后，按新授权启动一次；无SIGTERM/kill或其他服务探测。

### runtime-003终态：黑名单越过旧OOM，但埋点参数读取失败

09:44:29+08 READY：API1960305/start517634753，完整argv不变，API进程实际环境`BLACKLIST_APPEND=normal_,index_select`，无whitelist覆盖；all8来源/12QSA/36GDN/48MoE与两类graph7/7通过。
复用同一私有源码/缓存，未部署单行narrow方案。自动KV容量由旧1656999变为2106958 token，CLI不变但运行内存布局并非严格相同，后续不能隐去该差异。

首条doc71约0.769秒HTTP500；首次排他marker为09:44:30.265967+08、TP0、step1。
这次栈不再是`index_select/dim_compress` OOM，而是在`probe047.py:core`字典构造中读取`a[1]`时报`IndexError: tuple index out of range`。
两个`selected(...)`条目在Python求值顺序中均先于该错误，支持本次已越过此前选行OOM边界；但不是任意shape或精度通过证据。
实际`_forward_core`调用把`b/a/core_attn_out`作为关键字传入，新观察器错误地假定全部是位置参数。该异常属于新增取证脚本，不是模型的数值或状态故障。

第二条未派发，无重试/额外恢复；服务与客户端退出，8010无listener。保留首次marker、原始请求/HTTP500、16份all8输入/embedding末行、完整服务/客户端/rank/调优日志及编译缓存。
GDN状态字典在`retain`之前构造失败，所以选中状态与实际索引未提交PT；Q/K、logits、概率、noise和生成token也未产生，不宣称完整数值现场。
下一步只做CPU检查`inspect.signature(original).bind(*args, **kwargs)`统一取命名参数；未改在线源码，重新加载仍需用户方向。
本轮结论为incomplete；旧164/198 failed/no gate保持，不访问8035、不重跑GPQA，monitor仍PAUSED。

终态`failure-audit-002/report.json` SHA
`395ebc8ccebc2a3265f793dd1363a1d2195340d99a56822965484336c7bc7615`：
源前后一致、driver退出/8010无listener、16PT实际input和embedding有限值、120冻结项/13031缓存成员SHA通过。
缓存同时保存旧`fa4b6a6f11`与新`a09bc59113`两代，每代各8rank均96FP32归约和2原BF16 embedding归约；首次CPU审计错误假设只有8份FX而停，保留failure-audit-001部分材料，修为明确核验两代16份，未变更服务或重发模型请求。
这说明复用缓存目录并非全量缓存命中；黑名单配置后出现新compile key，不能把两次视为严格cache/key/内存布局相同。
实际方法签名`(mixed_qkv, b, a, core_attn_out)`的CPU绑定8项正反例通过，修正建议为命名绑定，不增加埋点范围。
CPU方案尚未部署，服务仍停，等待用户决定是否允许再次仅恢复8010；不自行重跑。

## runtime-004：授权修正参数绑定后仅恢复一次

用户明确允许修正埋点参数绑定，仅恢复8010一次、继续原两条同前缀，并保留index_select黑名单/FP32/i64/QSA M16，不访问8035、不跑全量GPQA。
本轮修复仅把GDN `_forward_core` 取证从`args[0..3]`改为真实签名`bind(*args, **kwargs)`后的命名读取；原调用与返回保持，不改变模型数学或扩大捕获范围。
CPU验证真实wrapper的全位置、全关键字、混合和关闭观察调用，以及缺参/重复参拒绝；先通过再用一次恢复机会。
新私有bootstrap存修正版probe，其他bootstrap文件逐字一致；继续使用同一047 Plugin源码和固定调优缓存，旧001/003证据及源码原件不覆盖。
新运行目录runtime-004，原2条doc71/343前缀/C1/max1、采样/seed与stop不变、零重试/无额外预热。
新实例的自动KV容量、graph及source实际核验，缺失两次replay/C8/60K覆盖仍记incomplete；不签新formal gate、不解除旧164/198精度阻塞。前台跟进，旧heartbeat继续PAUSED。

runtime004准备完成：真实wrapper共11项CPU检查通过，CUDA未初始化；唯一差异为GDN观察器按签名绑定参数，probe SHA `fce05253b5e472aa5c91a7ceaf9f5a6bb8242333b0634e92e5b75927598e272a`。
新bootstrap `/opt/qwen38-accdiag047-bindfix-20261020`，其余三个bootstrap文件逐字一致；Plugin和缓存仍为原047私有目录。
controller `commands/accdiag047-bindfix-control-v3.py` SHA `bdc313d3a992f8b4def3bb0f5829b4ef4a098f5618dcc7f885713d9e380888fb`；PREPARED SHA `0e7cab2e2fbb206c02450feed299c0d0a2392835740a44fa3791a581ef54a25c`；请求清单 SHA `bdfba7024ef805e543f6aa638eda1aa9d064f200d0ff8c13de2cea5d05fd966c`。
准备期间两次CPU脚本错误（fake Chunk调用语义、复制变量遮蔽）均保留原件，发生于0服务启动/0请求；修正后核验已有部分文件SHA，不覆盖旧证据。
执行前记录命令：同一controller依次 `--mode recover`（仅一次）和 `--mode launch`（仅一次）；只检查8010及物理8–15。无listener故不发送停止信号；失败不再恢复。当前尚无新精度结论。

### runtime-004异常终态：首条成功，第二条取证预算耗尽

获准的唯一一次恢复已执行；all8新probe/i64/FP32/QSA M16与两类graph7/7就绪，自动KV容量2106958 tokens（与003一致）。原两条doc71/343/C1/max1均已派发，无额外请求/重试。
首条约28.598秒HTTP200，完整prompt校验一致，输出token1596/`We`，finish_reason=length是预设max1而非60K推理截断。参数绑定和旧index_select全池OOM本轮均未复现。
第二条约2.244秒HTTP500；原排他FIRST_ANOMALY为2026-10-20 10:03:36.234400+08、rank5、step4，`kernel_capture→retain`抛出`047 narrow evidence budget exhausted`。`NARROW_BYTES`是跨两条累计计数，512MiB/rank保护上限触发，属于观察器取证预算故障；不据此认定原模型数值错误或NaN。
8010随后自然退出，无再次恢复/停止信号，不访问8035或GPQA。CLIENT_FINISHED、FINAL_EVIDENCE和FINISHED齐全（10:04:39+08），已保存4120份PT、首条原始HTTP/完整单token和sampler、第二条部分QK/状态以及HTTP500、全rank/服务/调优日志与编译缓存。
第二条未产生最终logits/概率/token，不能完成两条完整输出对照；状态/层覆盖和文件有效性待CPU审计，不能把4120文件数当完整因果现场。旧164/198 failed/no gate保持，本轮incomplete、无formal gate/性能结论。
终态只读CPU脚本：`commands/accdiag047-bindfix-partial-audit.py` SHA `8e65b7a823ab0a4bcf8f0bba9ba6e7c49d82a38838f13e91165475a84e259eb7`，`commands/accdiag047-bindfix-terminal-audit.py` SHA `7dd417602c08f4c33c483e2dbfd2dcb3228f6fab39b08e287b111edab820d8bb`；仅读/校验旧证据，无推理或GPU调用。

CPU部分数值审计 `runtime-004/cpu-partial-audit-001/report.json` SHA `b57fd76d969b7055debf51fb624d8dce0dcb6207f2afdb0f64e1a02d3f710b1e`：4120PT大小/SHA通过，各rank首条389份narrow+完整sampler、第二条123份narrow无sampler。240个已保存Q/K输入输出均有限，与FP64公式再转BF16最大差0.03125（并非独立设备reference，不直接判实现错误）；384个GDN初始状态检查均有限且全零、写回与已保存chunk final_state逐字相同，覆盖首条36层×8rank和第二条12层×8rank。可配对的576项前沿/状态一致，没有检测到已覆盖前缀的重复请求差异；不能外推第二条未到达层或Mixed C8/长输出。
首条all8 raw logits相对旧043最大差1.5、旧045最大差1.28125，采样后概率逐字相同；仍不能用单token/onehot概率一致推定forward一致或原精度修复。新增tap/固定调优/编译路径与旧参考不同，未完成跨环境因果二分。
终态 `runtime-004/post-controller-audit-001/report.json` SHA `43922cbea14aabf2de648eb24d12876bffec0297c19a8113fdfcc1dc7a649f39`：driver已退出、8010无listener，当前源码前后一致、actual READY环境保留normal_/index_select；4232冻结项与16042缓存成员SHA通过，原fa4b6a6f11和当前a09bc59113两代各8rank FX均96FP32归约+2原BF16 embedding归约。
原始目录为本CASE `diagnostics/accdiag-047-fixed-tune-qk-state-20261020/runtime-004/`，`runtime/FIRST_ANOMALY.json`保留排他原时间，原始HTTP、sampler、PT、全日志与缓存归档不覆盖。此轮不再修改/恢复；后续若缩减重复取证、重新验证完整两条，必须先获得新8010恢复授权。旧heartbeat继续PAUSED。

## runtime-005：用户授权去重取证并仅恢复一次

用户明确允许缩减重复张量保存，保留index_select黑名单/FP32/i64/QSA M16，仅恢复8010一次补做原两条同前缀；不访问8035、不跑GPQA。继续同一accdiag-047/minimal-regression，原2条doc71/343/C1/max1/采样seed/stop不变、零重试/隐藏预热。
本轮拟仅改观察器序列化：张量按dtype/shape/原始内容SHA寻址，重复快照只写引用，各取证点/descriptor/阶段/请求标签保留，不删除数值样本或改变模型运算。先CPU逐字往返、重复/NaN位模式/非连续与空张量检查，并用旧004实际张量核算去重预算；保留512MiB/rank上限，不通过无界提高预算规避。
新bootstrap独立，原Plugin/固定cache/旧004现场不改；准备与CPU证据通过后才消耗一次8010恢复，已有服务则不动并报告。首次异常停止新派发，冻结已有全部证据，未产生的数据不补造；第二次恢复需要新授权。当前未启动服务或发新请求。

CPU9项检查通过，报告 `dedup-005-preflight/report.json` SHA `40ae441e14021e021dcada6f51257459c03c88a82f9fd6da9cc132e26236d364`；旧rank0的389完整首条+123部分第二条均逐位还原。原逻辑张量535479050 bytes变为去重序列化232784875 bytes，完整首条225785080 bytes；假设第二条内容全异但shape/取证点数不变，保守两条451570160 bytes，低于536870912。不把该估计当运行事实，实际逐rank核验。
新bootstrap `/opt/qwen38-accdiag047-dedup-20261020`，只新增evidence047.py和改retain序列化；QK/GDN/PLE/sampler计算与绑定不变。Store SHA `0a3fa0d6c92c3b73ad065d4a117e03ecfcae554692cb56655128ea5d66dced20`，probe SHA `0e699da48166dd54aeaffdaf211147811f68c80b4defa517382dd4f73f9287a8`；descriptor保留原shape/stride/storage，NaN载荷与正负零不合并。
controller `commands/accdiag047-dedup-control-v2.py` SHA `84c57e33894f698eafdc67fdb81cc6b9ebf2ed85dd4e2647d102bc311676e448`；PREPARED SHA `fce025d68c159204ec2a6d953f11e72fc4ac57f5b19c61d17ea96076c8229877`。首次CPU准备因未复制receipt就比较private047字段而拒绝，0启动/0请求，原脚本及错误摘要保留；v2分两阶段精确比较后通过。
执行前冻结：同一controller依次 `--mode recover`和`--mode launch`各一次；仅8010及8–15门禁，无停止信号，不访问8035，不允许自动再次恢复。终态只读CPU审计脚本 `commands/accdiag047-dedup-audit.py` 与 `commands/accdiag047-dedup-host-audit.py`负责解引用/数值/全文件SHA/源码绑定，不发送推理。

预算估算限定：451570160是两份旧首条唯一快照完全不共享时、沿用旧单请求内部重复关系的投影，不是任意数值/任意shape的硬上界；在线仍有同一512MiB保护，逐rank实际字节及快照完整性另核。不通过修改停止marker、跳过异常点或提高上限规避失败。

### runtime-005终态：两条正常，完整sampler数值一致

唯一恢复已执行，10:16:13+08 READY，实际8010 API2642517/start517826106，完整argvSHA5744d999不变。all8新probe/FP32/i64/QSA M16与两类graph7/7核验，API实际append `normal_,index_select`，autoKV2106958 tokens；从未访问8035。唯一driver退出，服务保持原实例health200、running0/waiting0/preemption0、prompt686/generated2。没有新增/重试/预热请求、再次恢复或全量GPQA。

原两条doc71/343/C1/max1于10:16:23和10:16:27正常HTTP200，均token1596/`We`；finish_reason=length仅因冻结max1，不是60K问题复现。FIRST_ANOMALY、HTTP错误、NaN/非法访问和预算耗尽均未检出。
每rank保存两条各389个narrow快照（778）+4个input/sampler记录；全8rank共6256个观察记录及7924个内容寻址张量blob，全部引用可核验还原。每rank原逻辑张量808237442 bytes，实际去重序列化248241237–248950777 bytes（约236.7–237.4MiB），原512MiB上限未变。rank4唯一blob987、其他991，完整389标签仍两条配对，不因去重数量不同就认定模型差异。

`runtime-005/cpu-audit-001/report.json` SHA `393468973ac1bcff4c4948b4a65b9625f92352b47cc087561a0389bbe44eb95b`：

- all8两条完整raw logits、actual_probs、noise逐字相同，seed/RNG相同，API token1596和原始prompt343一致。
- 1856项已配对前沿/QK输入输出/初始状态/完整sampler检查无差异；这是明确比较子集，不称所有kernel未初始化缓冲逐字相同。
- 576处GDN（36层×2条×8rank）初始状态有限且全零，已保存写回与chunk final_state完全一致；本轮新鲜C1未支持清零/写回故障假设，但不能排除原C64或旧环境状态问题。
- 384个Q/K输入输出均有限，与FP64公式再转BF16最大差0.03125；这不是独立设备reference，不据此判RMSNorm实现错误。
- 相对旧043 raw max仍1.5、旧045 max1.28125（all8一致），采样后概率相同；原跨环境forward差异尚未隔离，不称原精度修复。去重只解决我方观察器重复保存预算，不改变模型数学。

`runtime-005/post-controller-audit-001/report.json` SHA `e9e68d1a99380f8d463d033b5acdbe868a317cc0c10518150d08e49795b519a7`：14280冻结文件/18602编译缓存成员SHA通过，完整服务/driver/rank/调优日志尾部补冻，源前后一致、driver退出与8010同实例健康空闲。两代cache各8rank FX均96FP32归约+2原BF16 embedding归约，完整bootstrap五文件归档。

本轮两个C1请求与窄数值重复性目标已完成；实际graph replay事件0，未做C8/60K，因此广义minimal-regression覆盖仍incomplete，不签formal gate或性能结论，不解除旧164/198 failed/no gate阻塞。记录已按精度定位/最小回归方法写回；下一步限于已保存证据的CPU分析，若需更改埋点或再次重载先询问用户，旧heartbeat保持PAUSED。

## runtime005后离线来源分析：固定调优与初始化（用户授权继续）

只读旧043/045/047 HTTP、PT、CAS、编译归档和明确关联源码，CPU离线新增分析报告排他保存到本实验`offline-origin-001`，不修改服务/配置/埋点或旧产物；0新推理/0GPU测试/0重启/0服务信号/0端点请求，不访问8035，保留全部现有修复。
先核对证据可比性：043逐层frontier只为doc81，doc71仅input/sampler，所以不能把doc81逐层张量拿来找doc71跨043→047首差。当前047的doc71 Q/K/state充分，但旧043对应state/QK缺失必须保留unknown。
按精度定位技能分别核验：(1)当前取证实际kernel和固定配置命中范围、AOT恢复与fusion变化；(2)当前GDN/PLE已保存状态/有效初始化与跨请求复用；(3)旧043/045与047编译产物的具体计算路径/归约顺序差异。静态候选不冒充实际launch，CPU反事实不冒充设备reference。若缺单变量因果证据，报告suspected和下一最小受控设计，新增埋点/重载必须另告用户。

### 离线终态：编译路径为优先嫌疑；当前初始化未支持故障，旧043未排除

本轮0新推理、0GPU测试、0端点请求、0重启/信号/源码与埋点变更，不访问8035。仅读既有张量/归档及目标容器相关源码，用CUDA_VISIBLE_DEVICES空、PYTHONPATH空、OMP/MKL1做CPU分析；另仅读权重检查点24个小Q/K norm张量，不加载模型执行。既有8010服务未操作；不以历史healthy回执冒充本轮在线健康检查。

1. **1.5是前向真实差异，不是输入或随机性漂移。** all8的16组043/045→047实际input_ids/positions/query_start_loc/logits_indices对照一致，seed/RNG/noise一致。043→047有245254/248320项raw不同，max1.5、mean_abs0.2233851042、RMSE0.2829501531，去均值后max仍1.4990659396。最大token18746，-2.6875→-4.1875。top1仍1596，过滤概率只有一个非零项，故token/概率相同不能证明forward一致。think-end raw13.375→13.5、EOS248046 raw6.5625→6.28125；不能外推原60K因果。

2. **固定配置实际命中，但不等于Q/K均按R32归约。** 当前768个Q/K前后调用快照（两个kernel各384条记录）均有source SHA/config。归约实际源码SHA `0ecb5cceef7da2fc50a3374645d8543215ed71163b986c99c46f53c08c3a76ca`，all8配置R0_BLOCK32/XBLOCK16/4warps；另materialization pointwise1024/4warps。源码同一combo kernel的Q分支硬编码`R0_BLOCK_0=256`，不使用外层32，K分支才循环R32。576组实际kernel参数→Q/K快照input/weight/output绑定逐位一致。终态configuration-pinned事件为0、fresh pinned-kernel-launched仅16，并非Q/K未固定：已有AOT对象保留诊断属性，Torch `__getstate__`保存self.__dict__、`__setstate__`恢复，实际调用快照比初始化日志更有力；不把“pin-installed”本身当全模型每个算子命中证明。

3. **新增tap改变fusion，是配置A/B的混杂因素。** 精确源码SHA链接到96份当前静态生成代码；当前Q是persistent256平方和/rsqrt/乘weight融合，K是loop32平方和/rsqrt/乘weight融合，前有materialization。旧043/045已保存独立或joint Q/K平方和kernel，FP32 sum写回后另算normalization；旧AOT bundle存在R32/R64、X16/X64、4/16warps差异。二者不只是同一个kernel改一个R参数。旧bundle不是当时doc71逐请求launch trace，不能宣称原043每一层都用了R64。首轮静态解析器只搜rsqrt+sum的async_compile字符串，漏掉旧sum-only standalone函数；补审保留原报告并追回48个旧源文件（包括含Q/K联合分支的sum kernel），不是旧路径不存在或模型故障。

4. **CPU反事实支持舍入机制，不证明最终1.5因果。** 在192组真实Q/K输入上仅改变FP32累加分组，R32/R64有14组、18元素BF16输出不同，max0.015625；R32/R256有16组、22元素不同，max0.015625。CPU不是PPU warp/FMA/libdevice.rsqrt精确模拟；当前数据也不是旧043 Q/K输入，不能由局部1ULP直接推算或宣称解释深层1.5。

5. **当前状态/权重初始化故障未获支持，范围明确。** GDN576处初始状态均全零/有限，288组第二条post SSM与首条完全相同，写回与chunk final_state一致。两条GDN实际索引不同（例如第0层1→73），故pre池值不同是不同槽内容，不能冒充同槽复用或错误；不能拿second-pre与first-post不等判故障。PLE all8使用同一索引37复用，has_initial_states_p=false、两次输出/状态一致。保存的192份Q/K norm权重等于检查点对应24个张量转换为相同dtype，未见该权重未初始化/加载错；不外推所有参数已验证。旧043没保存doc71逐层、Q/K或GDN/PLE设备状态，所以历史初始化假设仍unknown，跨轮首差层无法离线定位。

综合分类：`cross-run-forward-numeric-drift-with-compiler-fusion-and-reduction-confound`；编译/归约路径为**优先suspected**，不是confirmed根因。当前两条fresh C1的GDN未清零、PLE残留或Q/K权重加载错误不获支持，但不能据此排除旧043初始化或C64复用问题。保留原164/198 failed/no gate；无新精度/性能通过结论。

下一最小证伪（**未执行**）：先在获准的隔离GPU资源上，用保存的同一Q/K输入运行旧/新冻结kernel及配置，核设备reference、有效R分支和BF16舍入；若要模型因果A/B，必须保持同一埋点、初始化与cache策略，只替换目标归约实现，不能把“关闭全部tap+恢复自动调优”当单变量。需要GPU测试、新埋点或8010重载时先报告用户获授权，不自动执行，不全量GPQA。

### 离线证据索引

产物D为本CASE `diagnostics/accdiag-047-fixed-tune-qk-state-20261020/offline-origin-001`，原043/045/047运行原件不覆盖。`FINAL_REPORT.json` SHA `0be4a0ce960c85fe229346f07e2e0bdddf95d18bf6060341dee25959924df47e`。

| 报告 | SHA256 |
|---|---|
| `tensor-report.json` | 25cba09998826461f58500b76886f31b33a9b197615c7f3158ba5463300085f6 |
| `compiler/report.json` | 91dba70edfab9cff17f08f1712529f4c95e0a2b01110213971f9e1a30deb89ce |
| `counterfactual/report.json` | 8b999a274dd1a94a06af2d3d7922d25a86c14e007441d185c2b2ac82b05fbbfa |
| `standalone-supplement/report.json` | a052a75f83eea61239ea2e127fdecad0045d765227199e09203c44976761150b |
| `checkpoint-weight-001/report.json` | 8e071297cd7fa173e32152cc54a1d24c504ef1e037ed4169235616c6e52e3eac |

全部命令先排他保存于CASE/commands：`accdiag047-origin-tensors.py`(927e3bef)、`origin-artifacts.py`(91eefb04)、`origin-counterfactual.py`(21d949dc)、`origin-standalone.py`(93eca475)、`origin-checkpoint.py`(6605107d)、`origin-finalize.py`(7f0fab42)，以上缩写文件均有相同accdiag047-前缀。原首个manifest生成时包含自身空文件条目，保留原件，另由`origin-manifest.py`在打开新文件前完整计算清单；此为CPU归档工具问题，不改模型或原证据。

完整清单`FINAL_MANIFEST_COMPLETE.json` SHA `e2de3256d09ccac0d7865e447f93dee943f01bbaa3134cd77944d0afbbcf209d`，88个既有离线文件大小/SHA复核通过，旧自引用manifest作为历史工具产物也按实际字节纳入新清单，不覆盖。所有分析进程已完成；本轮仅离线定位，等待用户下一方向，不自动重载或增加测试。

## 保存输入GPU算子A/B：资源隔离门禁（新用户授权）

用户允许以保存的Q/K输入小范围GPU对比旧043与当前归约/fusion，明确不重启8010、不影响服务、不访问8035、不全量GPQA，资源不足先停止。沿用同一accdiag-047/diagnosis与minimal-regression局部范围，无性能目标/新gate。
执行前计划：仅在物理8–15发现独立空闲卡且至少8GiB可用时进入GPU阶段；其他卡组不查询。不把在线TP8卡的剩余显存视作已获准同卡争用。独立进程、独立缓存、保存原始输入/输出/FP32中间和IR/二进制；先冻结最多4组QK输入，旧sum路径R32/R64与当前融合路径各2次数值重复，不运行模型/采样或扩大GPQA。
本轮初步只读：8010 API2642517监听、health200、running0/waiting0/preemption0，prompt686/generated2；8–15每卡均有计算进程，free12621–12701MiB，总98304MiB。显存数值足够小测试，但没有独立空闲GPU可满足“不影响服务”的隔离门禁；不自行共享TP8卡、不初始化CUDA或启动算子客户端、不探测0–7/8035。下面将用`commands/accdiag047-gpu-ab-preflight.py`仅重核/冻结身份、资源与未执行计划，保存到`gpu-ab-001`。

资源门禁终态：`gpu-ab-001/RESOURCE_GATE.json` SHA `5e2bd15782ae6f935f0df3ed7246cb8aa4b2a0351d2ce522a2361acb022a4477`，8010原实例仍健康/空闲且计数686/2不变，8–15全部有计算进程，独占空闲候选0。**不是显存不足，而是无法在当前范围获得独占隔离资源**；为遵守不影响服务，采用保守独占门禁，不推定用户已允许增加同卡GPU上下文。GPU A/B未执行，尚无任何新设备数值证据。
`PLAN.json` SHA `4c2732fa4bdd7d460aee0d39ef6c6c8fb88da9f502c8ce32422a453b010bc01e`，冻结最多4组既有输入/3路径/各2重复，独立缓存和完整输入/输出/中间量/编译证据，当前为not-executed；`MANIFEST.json` SHA `429a8a6059b4bccc2bb28d9833119ef71aea85d0b9ca18244245a203705a4f1b`。preflight脚本 SHA `b3608dddb5a4aae4fe2257a8ac5851d63bcd82e03d8a6410350716947cffb3cd`。
0新推理/0GPU进程/0GPU launch/0重启与信号/0源码埋点变更/0其他卡组查询/0访问8035；没有full GPQA或新gate。结果incomplete-resource-isolation，不把计划当运行、没有因显存余量自动共享。知识差量为本轮未执行，无新算子数值结论。等待用户指定独立空闲卡，或明确接受8010空闲窗口内限资源同卡微测后再另行冻结资源与停止条件；不自动重试。

## gpu-ab-002：用户授权停止8010后进行保存输入验证

最新用户明确“可以直接把8010服务停掉然后进行验证”，覆盖上一轮禁止停止该服务的资源限制。不扩大到8035/物理0–7，不停止容器、不修改模型/source/埋点/缓存或现有FP32/i64/QSA M16/index_select黑名单，不发新模型请求/GPQA。
执行前保存`commands/accdiag047-gpu-ab-stop.py`：重新核API PID/start/argv与8010 listener和running/waiting均0，只向该API发送一次SIGTERM，观察关联worker自然退出和8–15资源释放。若身份漂移/仍有负载/退出不完整则停止，不自动升级信号或追杀其他进程。
新原始目录`gpu-ab-002`，保留001未执行资源门禁。继承001冻结的4组Q/K输入、旧平方和R32/R64和当前融合Q256/K32三路径、各两次；独立GPU进程/缓存、最多使用8–15中的一张已释放独占卡。保存输入/权重/FP32中间/输出/数值差异及编译IR；旧完整norm无法忠实恢复时明确区分旧原生sum kernel和语义后处理，不冒充完整043模型重放。首次真实错误保全证据，不自动重试。验证后保持8010停止，不自行恢复；无正式gate或性能结论。

### gpu-ab-002终态：设备复现归约舍入，模型差异因果仍未证明

精确核验8010原API2642517/start517826106/argv5744d999、listener、running/waiting0及8卡worker祖先链，**仅向该API发送一次SIGTERM**，worker自然退出；未停止容器或发其他信号。STOP_RECEIPT SHA `3ec695150dae63a56a4834b66ec472c12e8564b799601a0a913c602ae80f4ad5`。结束再核8010无listener、8–15均无计算进程/free98202MiB，**服务保持停止，没有自行重启**；源码与runtime005的PREPARED完整sources前后一致，FP32/i64/QSA M16/黑名单未变，不访问8035。

资源释放后只在物理15启动一个独立GPU进程，固定rank0第3/7/23/27层的旧存Q/K各一组，343tokens、BF16，Q[343,3,256]/K[343,1,256]。源码逐字匹配后仅提取原jit函数，去掉外层autotune与固定设备benchmark入口：旧043联合sum源码05b04919，当前实际函数0ecb5cce。每路径两次、共24个variant runs；独立新cache、无随机输入/模型请求/采样/GPQA。峰值Torch allocated10724864bytes；5份实际编译kernel/44新cache文件、完整输入/输出/中间量与服务关停完整日志保存。

为了隔离R参数，旧sum的R32/R64均固定X16/4warps/stages1/fp_fusion=true；这是旧原生函数的同配置反事实，不冒充旧043 X64/16warps完整bundle或doc71实际launch。旧归一化后处理使用明确标记的GPU语义重建（FP32 sum→rsqrt→乘输入/weight→BF16），不是已恢复完整旧融合下游。当前保持Q有效R256/K32。两种局部变化及限制在执行前GPU_EXECUTION_PLAN冻结，SHA `47fe5ef783df5872f63fd0bd0b86379137f96e74a8d3615fc02c6c145f8cb6e1`。

| rank0层（0-based） | 旧R32/R64的Q差异元素/max | 旧R32/当前Q差异元素/max | 旧R64/当前Q差异元素/max |
|---|---|---|---|
| 3 | 2 / 0.0078125 | 3 / 0.00390625 | 3 / 0.0078125 |
| 7 | 2 / 0.015625 | 1 / 0.0078125 | 1 / 0.015625 |
| 23 | 0 / 0 | 0 / 0 | 0 / 0 |
| 27 | 2 / 0.00390625 | 1 / 0.00390625 | 1 / 0.000244140625 |

全部K输出在三路径上相同；current的4组Q/K共8项均与实际模型runtime005保存输出逐位一致。三路径的所有重复输出/中间量逐位一致，有限值检查、输入未修改及输出guard通过，没有kernel错误/NaN/非法访问。旧R32/R64的FP32平方和仍存在小差异，最大0.0000457763671875；BF16差异仅Q共6个元素，每个encoding差1ULP。这是**目标PPU上归约顺序引发舍入差异的reproduced证据**，比CPU反事实更强，但不能直接宣称算子实现错误。

首个具体例：层3 Q[row174,head1,ch31]，R32/R64 FP32 sum分别76.6633071899414/76.66331481933594，FP64 sum76.66331117320806；precast分别-0.0528564490377903/-0.0528564453125，位于BF16舍入分界两侧，输出-0.052978515625/-0.052734375（1ULP）。当前输出等于后者，FP64公式再舍入等于前者；单点oracle优劣不等于整模型优劣。全部6个差异的输入、weight、sum、inv、precast、输出/FP64对照见`DIFFERING_ELEMENTS.json`，SHA `968d46c8a02192e3adeb5d7a7ccce2990e1d970f4701bf9589a6dbe690322f5b`。首次数值差异marker与全部原始PT保留，不把有限舍入差异当模型事故。

CPU独立审计SHA `139ee1edbc72b845470b271a7bdf1be25d8be9a67f5a034306dc84a654c495bc`；GPU RESULT SHA `17218bd20d812206a1414018231ab4f82bb6c2641599dd079c274ffecfa80001`。FINAL_REPORT SHA `a2b095dc90961337fc893a7ed6fc402ae6951a490a049f5bd4b0de0c54fe4d49`，FINAL_MANIFEST SHA `0bfa435d4427962845c0f442922b206c8eb11b559e2257f4d10ea3f599401ec6`，142冻结文件大小/SHA复核通过。GPU进程退出、原8010未恢复、所有受检卡无残留负载。

CPU准备时有两次我方校验错误：函数SHA漏尾换行、观察点[343,768]/[343,256]误当kernel的三维view；均发生在0GPU launch之前。原脚本保留，v3明确按运行时含换行SHA及reshape后byte-exact绑定通过，未修改原tensor或放宽数值校验，未当作模型故障。

命令均先保存CASE/commands并校验：`accdiag047-gpu-ab-stop.py`(5b96fcb2)、`prepare-v3.py`(364a09b2)、`postprocess.py`(8cf430d0)、`run.py`(147145f3)、`launch.py`(cb107e3a)、`audit.py`(0b499abe)、`freeze.py`(7ca9dccc)；后六缩写均有相同accdiag047-gpu-ab-前缀。旧prepare/prepare-v2原件及工具失败说明保留，不覆盖001与runtime005。

知识差量：从“CPU分组舍入可疑”提升为“同一保存输入、同一PPU、相同X/warps仅改R即可复现Q的一ULP舍入”。当前kernel忠实重放排除了本小实验输入重建错误；没有模型状态参与，不能拿本结果证明历史state初始化正确。旧043 doc71中间值仍缺、当前Q256与fusion仍耦合，**最终logits max1.5、C64/60K不收敛的因果尚未确认**。下一模型因果实验若开展，应保持输入/初始化/埋点/cache策略不变仅替换Q/K归约，需先获得8010恢复与明确请求范围；本轮不自动执行。无新精度gate/性能结论，旧164/198 failed/no gate、性能阻塞与heartbeatPAUSED保持。

## runtime-006：用户授权仅恢复8010并复核问题

用户要求“重启下服务验证下问题是否修复”。8010当前无listener；本轮只恢复它一次，不停止容器、不访问8035，不改源码/埋点/固定配置/缓存策略。保留FP32/i64/QSA M16及normal_/index_select黑名单。上一轮GPU A/B没有实施新数值修复，故不能把重启叫作修复；先原样重做两条doc71/343相同前缀/C1/max1/原seed采样/零重试/无隐藏预热，比较输入、完整logits、概率、token与runtime005和旧043，判断差异是否仍在。
采用inference-accuracy-diagnosis与inference-accuracy-evaluation minimal-regression的明确局部范围；观察器不新增hook，仅配置输出目录和opaque请求ID换为006，保留同一无损去重代码与512MiB/rank预算。新产物`runtime-006`，旧日志/PT/缓存归档不覆盖，执行脚本先保存在CASE/commands。两条max1若正常，只能说明此局部运行与重复性；实际两次graph replay、C8、完整输出/60K均不由此推断，不签gate/解除旧164/198阻塞。若异常，保存首次现场、停止补位，无自动第二次恢复；heartbeat仍PAUSED，前台跟进。

006准备已通过：源码/模型指纹与005相同，容器镜像/挂载门禁通过；新controller `commands/accdiag047-restart-recheck-control.py` SHA `088cb7e18c6e236827445192d22a711bc1b7050cad7afd0e1ac2ecd137489176`，PREPARED SHA `ae758b96dfcb5a9c8861e88acf49118599dcefdb4b160f87f3f9ff05bca6dda8`。执行前冻结：对该controller依次`--mode recover`与`--mode launch`各一次，前者只恢复已停的8010、后者唯一driver等待READY后自动发送原两条，失败不重启/重发；不运行旧005启动命令或覆盖旧路径。

### runtime-006终态：服务恢复正常，旧043前向差异仍为1.5

本轮仅恢复8010一次、0停止信号/0源码与埋点变更；11:05:37+08 READY，API3644676/start518122313/argv SHA5744d999。保留同一私有Plugin/无损去重bootstrap/固定调优cache，all8实际probe、FP32/helper/i64/QSA M16及API黑名单`normal_,index_select`核验，两类graph capture各7/7，autoKV2106958tokens。容器和其他服务不操作，不访问8035。

原两条doc71/343/C1/max1在11:05:47和11:05:51均HTTP200，token1596/`We`、输入prompt逐位匹配，零重试/额外预热/请求；finish_reason=length仅因冻结max1，不能冒充60K截断复现。FIRST_ANOMALY、NaN、HTTP失败/非法访问/证据预算耗尽均未检出。唯一controller于11:06:56自然完成与退出，FINAL_EVIDENCE/FINISHED齐全；服务保持新实例health200、running0/waiting0/preemption0，prompt686/generated2。

CPU全量窄取证审计`runtime-006/cpu-audit-001/report.json` SHA `1e673c90ea402d6fdb427335cea56e5e3f7c4f37fd21f0ba52436952a97b57e5`：6256观察PT/完整CAS还原；all8两条完整logits/prob/noise/seed/RNG均相同，576处GDN有效initial_state有限全零、写回与chunk final_state相同，384个Q/K输入输出有限。每rank778narrow+4input/sampler，预算约237MiB，旧512MiB上限不变。

新增`cpu-audit-001/restart-comparison.json` SHA `1e8cfa2b648b6ec24fccf3e80f03b3436fe74575c6c2271699d0bc6351c01837`：以005首条为reference，all8×2条共16组input_ids/positions/query_start/logits_indices一致，logits最大差0，prob/noise/RNG/token相同；**重启并未改变当前前向结果**。与旧043仍有245254/248320个raw项不同、max1.5（all8），与旧045仍max1.28125；过滤后概率相同不代表forward相同。GPU A/B之前没有部署新数值修复，不能把这次恢复说成已加载修复或将正常HTTP当原精度问题解决。

Host终态`post-controller-audit-001/report.json` SHA `5cb42239eab82f8e02bd4a7ad57d85f1d775fdc3e6e2a35c682b37d79cc265db`：14280冻结文件、21162编译缓存成员大小/SHA通过，完整服务/rank/tuning日志尾部补冻、源码前后一致、driver退出/服务绑定与黑名单一致。复用同一cache目录并不等于全量缓存命中；当前归档成员比005的18602更多，不以路径相同宣称无编译增量。原缓存与前轮归档均保留，未清缓存来制造结果。

审计工具与SHA：`commands/accdiag047-restart-recheck-audit.py` cd7a7c0ce7f70815eae0401b40e4e5d5592324c85483fc682dbb3ba816d14669，复用冻结005数值检查仅改当前R路径；Host首版因新controller的helper未在顶层导出而`KeyError: listener`，发生在CPU审计、无新推理/服务变更。保留首版脚本及HOST_AUDIT_TOOLING_ERROR，v2仅把原有继承的listener/metrics/stable/guard/cpu别名补到审计namespace，所有绑定/源码/编译校验不放宽；v2 SHA ffd84b82dc424978bc737aff83704fe4cf0454c574cb58cea58d015481f3a7a8。未修改运行controller或重启来绕过审计。

Skill完整bundle SHA `6e94a080dd3b64544c535e1fd4bda506f55516374d14d0f8ca6aa148bba2c7b2`、接口e2e/accuracy与minimal-regression已冻结在`SKILL_BUNDLE.json`（文件SHA f0d42f77）。按该方法严格区分局部健康/重复性和formal精度；本轮只有两条max1，不覆盖C8、长输出、实际两次graph replay或大索引边界，广义minimal状态仍incomplete，无formal gate/性能结论，旧164/198 failed/no gate及性能阻塞保持。结论为**服务恢复、首条NaN未复现、既有前向差异未消除，原精度问题不能判定已修复**。原问题因果仍suspected编译/归约，下一步应保持其他条件不变做模型内单变量Q/K归约对照；新增修改/埋点/重载前先获用户方向，不继续重复重启或自动全量GPQA。服务保持运行，heartbeat继续PAUSED。
