# Restore guarded shortlist inside FlagGems-vllm sampling interface

用户明确要求保留flaggems-vllm采样接口、补回shortlist、保留MoE/GDN。同一mx-104专用B/GPU4/5；当前服务370006/start1140894280/8020/opt2（执行前fresh核验），无活动job，原始代码栈由blacklist-gap-001独立9667文件及env/argv/cwd证明。只改私有FGV MetaX top_k_top_p.py及对应测试/benchmark，不改Plugin接口、RNG/vLLM/模型/FGV MoE c467/GDN/当前环境/阈值。初始候选先写远端artifact模块做真GPU验证，不在当前服务进程内试错。所有新命令先commands/SHA，保留失败不覆盖。没有新完整精度gate，GPU微测/短程仅diagnostic；采样高风险，最终新候选需要原生C64/full198正式精度。

应用本地key-operator-analysis及inference-accuracy-evaluation minimal-regression；服务/性能阶段按targeted与必要formal-gate执行。此前诊断证据：M64/V248320/k20/p.95/temp.6当前全量radix API约10.58ms、旧shortlist约2.30ms，bothranktrace8sweep/step约7.84ms；白/黑名单仅1.91%。目标保留公共API、稳定阈值语义，避免原shortlist的torch.topk受到globalGems注册影响、避免CPU bool(valid.all())同步。

## 项目真相表（编码前）

| 字段 | 冻结内容 |
|---|---|
| Current op | flaggems_vllm.apply_top_k_top_p(logits,k,p)，原生vLLM bc150f5过滤语义/已验证stable tie契约；远端workflow末尾conv1d任务为旧模板，本次以用户采样任务为准 |
| Editable | /opt/FlagGems-vllm/src/flaggems_vllm/runtime/backend/_metax/fused/top_k_top_p.py、tests/test_top_k_top_p.py、benchmark/test_top_k_top_p_perf.py；proto先独立artifact |
| Read-only | 旧source dcfa764e、原44test/baseline oracle/blacklist-gap输入与trace、Plugin/Gems/vLLM/MoE/GDN/权重/其他平台 |
| Build | editable纯Python+Triton，语法/导入；不重装依赖、不修改build配置 |
| Validation | 现有44精确过滤/alias/unsupported tests + fast/fallback混合k/tie/NaN/Inf/zero、非对齐N、变化输入graph；必须rtol0/atol0/equal_nan与旧完整FGV及独立oracle，无放宽 |
| Benchmark | 同当前栈完整APIold-full/new-shortlist/old-full，固定输入/seed；事件span+wall median，reset copy排除；目标M64/V248320完整API至少30%降低，原general sentinel无明显回归 |
| Active set | FP32 contiguous M1/7/8/32/64,V4097/151936/248320，来自BF16/temp.6及generalFP32；k1/20/63/64/128/V，p0/.5/.95/1；N1/257原general边界，M0/unsupported保留 |
| Aggregation | 所有预声明样本保留；3warm/10measure，new/old/new或old/new/old，报告median、min/max和漂移，不择优 |
| Timeout | CPU180s、GPU正确性900s/有限微测600s、服务600s；失败停止不自动重跑提交 |
| Profiler | 已有双方rank64步证据可用；若新路径需确认，沿用已授权有限trace，profiler时间不计性能 |
| Autotune | 新kernel仅MetaX固定层次算法：chunk1024/keep64/warps4；固定小候选首版无搜索。NVIDIA路径不改/不适用其tune config；参数豁免在此声明，收益不足再有界改一个参数或读deep指南（目标repo optimization.md/deep_opt.md均缺失，本地算子方法补充，不虚报已读取） |
| Fallback | NO_TORCH_COMPUTE_FALLBACK；metadata不支持仍NotImplementedError/原Plugin显式兼容路径；设备安全检查不通过时库内原完整counting/radix，纯GPUguard，无host读值 |

## 对齐契约（编码前）

| 字段 | 内容 |
|---|---|
| Device/backend | MetaX C550/CUDA兼容，FlagTree0.7 fe1d24f6/Triton3.6、Gems5.5dev a456722a；其他平台入口不变 |
| Input | 现有FP32 rank2 contiguous、M<=64、1<=V<=262144，kint32/int64[M]有效1..V，pFP32[M]有效0..1，同设备连续；只在p和k均存在/N>=4096时尝试shortlist |
| Output | 同logits对象/指针/shape/FP32，原地-inf掩码，保留值逐位不变；无RNG、无logprobs/class修改 |
| Dtype/promotion | 只现有FP32支持；不引入BF16/FP16新输入支持。排序用FP32 ordered key+tokenID uint64精确排列；softmax/CDF保持原全V形状与Gems函数，避免compact reduction改数值 |
| Semantics | 全batch设备guard：NaN、非有限最大值、k不在1..63或64th值不严格小于kth，转原完整算法；ties/±0/-inf按原路径或精确键处理。特殊值保留原实现行为，不扩大NaN正确性承诺 |
| Autograd | 原forward-only过滤，训练/backward不新增承诺 |
| Unsupported | 原metadata/dtype/layout/超batch/超V/p-only契约保留，拒绝前不写入 |
| Reference-only torch | oracle/validation/benchmark用Torch；production仅empty/empty_like与元数据+Triton/已有Gemskernel，不使用Torch topk/sort/compute、item/bool同步 |

## 路径表（编码前）

| 路径 | 触发/实现 | 验证/风险 |
|---|---|---|
| early/unsupported | 原空M/无过滤返回、原不支持拒绝 | 原44 tests及alias |
| fast | bothfilter,N>=4096；Triton分块1024精确选64候选，层次合并至64，设备validityguard；安全则结果fullV前缀-inf/尾64稳定排序；沿用原fullV softmax/CDF/threshold mask | M/V/形状/ties/k边界，GPU无hostsync；新层次select成本需实测 |
| runtime fallback | 任一row NaN/非有限最大/k>=64/边界ties导致shortlist不完整 -> 全batch原_sorted_values | 同graph安全->fallback->安全，原8pass/counting只在fallback执行，无值读回CPU |
| general | k-only、小N等保持原counting/radix | 与旧模块精确比对，除新增guard参数无数值修改 |
| external-library | 现有Gems softmax/cumsum/Triton helpers复用 | 不调用Torch计算fallback/不改库 |

下一步先归档完整原source/hash/revisions/保护清单，再执行独立proto编译、数值/graph/有限API微测。通过前不写production。接口已导出/注册，新增helper不需要改通用export或非目标backend。

## 实际执行与初步算子结果

- 准备命令commands/sampler-shortlist-prepare-001.py SHA3161a137f77eb0b7de246f62d6dc09c6203914932655b1513da8d3cade4a0c9b已执行；operator/sampler-shortlist-001/preparation.json SHA2fea4dd22be38dc42d54f8dfe9c0087b9883451b679e8d2a487e4245b09fcb95，9667保护文件与当前API370006/start1140894280/idle通过，0生产写入。
- 独立原型commands/sampler-shortlist-proto-001.py SHAe7a82110c2178186cc99922a3c03eb835037bf95ab111f56fa61f9df4fa2e2a0；只artifact加载，无生产registry/source修改。分块1024/64候选/层次uint64精确key；全batchdeviceflag确保原sort在不安全数据上运行。
- commands/sampler-shortlist-gpu-001.py SHA2e3240f983aacf9e3cedd090bb46b49a7adf3417bac51d3794e053626513913e，command SHA722b9ab5b058c1dc5c86e126643fe16c15655d25bf3cd50aa759cddc9340b723，native exit0。GPU4内存限制.025，服务idle、0模型请求；M8/V4097和M64/V248320、BF16→FP32/0.6/k20/p.95均与原完整FGV逐位一致。
- 同完整API old/new/old每组3预热10测量（copy排除），事件中位10.4739/3.5329/10.4696ms，wall10.5328/3.6037/10.5369ms。降低66.26%，只算子级diagnostic，不是端到端收益或精度gate。初步超过预声明30%门槛，仍需完整边界/graph/真实注册验证。
- 扩展测试commands/test_sampler_shortlist_candidate_001.py SHA2421f01a6a83f828b473dc900dd86853d8697dee6852745ab85474f78eb5e34c；validation001 SHA9477d99c3bf9f12f99c2bb2f7851a665c1e6377b26c70c05d604edec995f36a9已启动一次。保留原测试断言，新增真实大V graph同图safe→ties→k64→safe与RNG不变；终态待观察。当前生产源仍dcfa764e，服务未重启，MoE/GDN/Plugin不变。

## Graph测试初始化取证与后续冻结（执行前）

首validation001通过42项后停在原有test_changed_input_graph_replays的torch.cuda.graph.__init__→torch.cuda.Stream.__new__，尚未开始捕获/新kernel；GPUutil0。不是数值失败或已证明新kernel不支持graph。SSH观察断开但容器测试继续，未重放。精确测试PID382945/start1141615186，520s无进展后用独立归档sampler-shortlist-stalled-test-snapshot-001.py SHAc6f0e53bc8f9408ed13eb6c91fc63254285e4b578b9bc2c3a825d992a32eaea1禁用该测试core并SIGABRT取Python栈，原日志保留；模型服务未信号/源码未动。原测试不宣称86通过。另只读核对发现真实Gems注册参数为unused而非exclude；原001末尾未执行到的exclude保留错误，不覆盖原脚本。已归档blacklist-audit002需原001完整junit因而不执行。

后续validation003将在本案例精确停止当前模型后独占GPU4，前置创建capture stream再导入vLLM/Inductor，增加测试内存上限至.08（空卡>=10GiB）；真实断言/算法/原86集合不放宽，60s定期Python栈和逐项日志，900s父超时且精确取消该测试进程；这验证初始化/资源边界，不能预先归因根因。最终候选final002仅格式整理，Python完整AST与proto001相同，SHA387629b1c60baa927ca14cb0fd4abce90fba20e25674221b34e35df9a0499808。

服务与端到端验证选择accuracy minimal-regression和performance targeted，沿用明确授权的有限诊断，不签正式性能。冻结同当前无profiler/黑名单/原env/argv/cwd、GPU4/5、服务8020/opt2：原完整排序B0→shortlist C1→原完整排序R→shortlist C2最终保留。每臂P1024/D128/C64/N64/temp0.6/topk20/topp.95/seed42，3预热+2测量全部保存；稳态末两预热/两测量spread<=8%，原B0/R漂移<=8%，目标TPOT下降>=10%且输出吞吐>=10%提升，TTFT/p99TPOT守护上升<=10%。当前主场景P1024/D1024/C64/N128仅milestone映射，无四场景正式结论。初始B0已有graph服务capture；每新服务capture日志并两轮C8固定短题、健康及实际路径检查，MoE/GDN/Plugin源码保护，异常恢复原源码/原env服务。GPU单测必须全通过后才写生产源码；所有新程序先commands唯一文件/SHA，控制器必须detach保证SSH断线不重试。服务阶段结束后新高风险采样候选按原C64/full198/threshold.7753正式契约评估，不复用旧gate、不自动正式性能。

唯一服务控制器commands/sampler-shortlist-service-001.py SHAe832a95c7f639dd7228411efb5d91f33121c567ea0513a51faefbad7874eed1c；计划sampler-shortlist-service-001-plan.json SHA6adec5153c779b6c77d57d8df14303b87dde2002c0b9c3886eb628e6d18d6665；一次性starter SHA f7995dfd7c1e81809ef6786406d39f92f74928a9e29da35a09fd02ce915b8d0a。validation003 SHA bc9ab6533d5b01e2afb0e9b21bfba0ac413af8ede91119e59ebe92922888cf2d，blacklist-audit003 SHA34678092cd470111b338e479b2a7c0f21195906a739d4d3f085636565d5098f6。启动前已本地审阅AST、嵌套/proc NUL分隔、精确信号/恢复和GPU测试取消确认；Host detach运行，只允许370006/start1140894280及本控制器记录的新实例，不能因SSH断开重放。全环境只在控制器内存传递，保存筛选字段和内容SHA；所有角色env/argv/cwd完全保持，不带profiler。原case的native benchmark与服务执行helper只按冻结SHA复用，不重放旧控制器。

## 必需最小回归失败：signed zero边界（sampler-zero-tie-001）

service-001已完成原B0五轮无profiler基线后精确停服，validation003在空卡且预创建stream下45.24s跑完，**85 passed/1 failed**；包括原两种小N graph及M64/V248320同图safe→ties→k64→safe/RNG检查均通过。失败是新增test_shortlist_guard[zeros]：M7/V4097某行交替-0/+0，k20/p.95，204个mask与原生stable oracle不同。GPUguard已转原完整排序，因此先分类为疑似原完整路径的signed-zero稳定tie语义问题，不把候选“回退成功”当正确性通过。未生产应用、无候选/回退模型流量，controller自动恢复原source/参数服务；旧B0原生结果保留，不择优重跑。

按inference-accuracy-diagnosis冻结validation003日志/junit及原候选source，新增commands/sampler-shortlist-zero-diagnosis-001.py SHA10b74f800183b624c1940b39356e090cf5462f8751b5524b10f2c61f559c1143，仅复现M1/V4097交替signedzero，原full/proto/native三方，预期原full与proto同、对native差204；执行前不声称confirmed。

若复现确认，只在FGV的_threshold_counts/_stable_threshold_mask引入位级_numeric_order_key把±0当同值并按tokenID稳定处理；radix/counting内部原key/数值不改，不改Gems/vLLM/Plugin/RNG/MoE/GDN。用bit magnitude==0判断避免误把subnormal当0。该修正为满足既定原生stable语义，无放宽原失败断言。新final004 SHA49e9c663a72a151b5d6f30561ccd1a9702f87d527d68acf1f0e238d8a79817f2；88项（保留86+signedzero/subnormal2）tests SHA1a2d22e4de17e7490fe53021affc045a4c1e28d3d65289a0f01d578ba11cd542，validation004 SHA799d6dfa3ef31c18c6a9f6f46977a703858b7e6de5b3fcde032b2743935d3c81，blacklist-audit004 SHA0c007a5cddfba8211b57eacf64e78831d2313b841ec8de06351bfec8d56dfa6a，均先归档，未通过前不生产写入/晋级。首service001/所有旧输出禁止重放或覆盖；接续可引用已完整B0同配置基线，重新冻结当前恢复服务PID/start和新controller，不再次提交B0流量。

zero-diagnosis001实际native exit0：原full与proto结果相同、对native掩码均差204，device failed=1明确原full路径，根因stable threshold按IEEE total-order区分±0而原生stable按同值/ID处理；机制confirmed，修正后的原范围尚待验证。原service001已终态failed_partial/error operator-validation003/restore_error null，0生产应用/0候选请求，恢复API416731/start1141772989/原env/argv/源通过；原Host413138已消失且旧starter没有wait监督，未保存OS原生exit回执，不臆造exit2。业务summary与GPU测试exit1分别保留。

新唯一接续job sampler-shortlist-service-followup-001；controller SHAa94f84d2a4d98a48d5989f69eff81d4f4cb225c88c2086275f50f805e927d528，planSHA0a64c322d8fde874aabd463aee4bea8d92838ae079b44b7050b8e227a5fb3e8a，supervisorSHAf24376d32e4cc3eb4b179529e36c23d91add7230f58b66470c440eb9e5060254，starterSHA3c1c8e87dcedccf8b9c243b42dfdd6b063eed219d6b1e6f6d16907d4aab3e63b。复用首B0完整报告SHA b6d8bf3c8dcd3b0f77bc5f68c1d05cf1fa49f5e4efeed6b2553986d83d6c68d8（全部5轮原生64/64），新正式模型题0；只执行剩余C1/R/C2诊断，冻结契约不改。精确416731/start1141772989停止→空卡88测试+实际黑名单API微测全通过才生产49e9...，失败仍恢复原source服务。新增supervisor child.wait真实OS退出码/精确child binding，避免旧launcher丢失native exit证据；旧文件不修写。监控仍同qwen35-shortlist，每小时/重要变化通知。

final004原生验证**88 passed**（71.92s），native exit0，包含原断言/zero+subnormal、同graph四次切换及RNG；result SHA21b7f955b9660b2ddb393f0cc4eeeafb9d8d9ea559276a4cb7fe0ec72a4a4e4d。实际黑名单API审计exit0，report SHA2ae50386b0493a29d0b1c0f2a31d44bbf852a233d910f296726e6eb296558159：M64/V248320/0.6/k20/p.95完整API event old10.4494→new3.53434→old10.4564ms，降低66.188%；小generalM8/V257为.79258/.78976/.78298ms无明显回归；M7/V4097/k64安全回退为.80294/.92480/.78387ms，额外约.13ms（约17%）选择检查开销明确保留，不宣称所有形状加速。新source49e9已保持稳定，无放宽过滤精度。

followup001已实际候选C1启动/capture11/11、两轮C8全部16/16正确stop，MoE native日志两rank可见。controller对graph日志字面值写成`full decode`，实际`decode, FULL`，导致观察层误拒绝；因此0候选performance/0正式GPQA，自动回原source/API460533/start1141871593，native supervisor child.wait exit2、restore_error null。保留全部C1已提交请求/原日志/失败，不覆盖；不是模型错误/graph失败。新observer-audit001先0请求按实际schema复核并绑定旧证据，生成器SHAac1dde5f25c4a64d0cd2919ca120d2ba185649150ab2b511bcd3e5ba9497e7a7。

后续唯一job sampler-shortlist-service-followup-002/ROOT同D下service-followup-002，控制器SHAa40b6372bbf1156c246a0126430ec2f3adbdd14fec678780058416ea899827db、planSHAa7980d46a59b99ade0e3f67a144fe77443cb22a1d31edd5cdd93ab320c03d925、supervisorSHAca5edbc228e5369a05f3ad9403ec9ff283dcde4692b30ea63621bfa2a92dc610、starterSHA39c80c7e0d0cf36b90525384cc390d81aa8b1cc1e0eb55a96b406b66eb5220d3。只修观察判据/唯一root/精确460533身份，算法49e9不变；**复用已完成88/实际黑名单API/完整B0，不重跑这些GPU测试**。新实例自己C8+nativecapture核验；C1/R/C2的端到端性能尚未提交，沿用原冻结契约。禁止重放全部旧controller/starter/CPU/GPU脚本。最终native/model评估仍待，不签gate。

observer-audit001实际0请求核验通过，report SHA01d53a042e791105a374a6763e227c8a03ec75296f5de112d756e8f31124d984。followup002已实际启动一次：supervisorPID513108/start1141943542，launchSHA1d9cda7460bb01f1b7e82625ae9393a79aa5d720425ae6c46525164cd1166359；controller精确身份以后按D/service-followup-002.controller-launch.json读取。旧followup001 native exit2/历史C1两轮16请求/恢复均保留，不重新执行旧入口。

新增最终服务独立reader commands/sampler-shortlist-independent-service-001.py SHA69a1efb2700d3074ad218e97360260a9b9ecc04179ac885e7c6bfe680cb86835（默认inactive，尚未执行）。只有followup002 supervisor原生exit0、summary完成/error/restore_error null、current_job null/当前c2时才能审阅实际schema并唯一归档命令--execute-reviewed-verification。纯文件+health/models读数：88完整junit、原生20轮×64请求/65536输入8192输出、原始JSON/stdout/commands经冻结维护版validate_native_result独立重验、全部3warm+2meas/角色source/env/argv/cwd一致、原B0/R漂移及候选收益/TTFT/p99TPOTguard、当前PID/start/9667保护+仅3允许文件、无Torchcompute/hostreadback。输出D/independent-service-verification-001以前必须不存在，失败留痕新文件修复，不重跑模型补分。该reader不替代C64/full198正式精度，也不做正式性能签发。

followup002模型资格通过（新C1两轮16/16+capture11/11），但首warm轮native CLI进程外层120s预算耗尽，native return124；**实际原生JSON已64/64完成、failed0、输入65536/输出8192、每条输出128**，benchmark本体82.02195s，加CLI初始化/退出超过120s。只有这两个validation errors（process timeout与exit124）；不是数值/HTTP失败，也没有测量轮。原始warm/JSON/stdout/失败全保留，native controllerexit2/restore_errornull恢复原source/API505650/start1141982297。该冷轮属于预声明warm，不把它当稳态回归或测量后剔除。进一步原生纯文件audit生成器sampler-shortlist-budget-audit-001.py SHA33423901db3aac37431bb7d4846888c11f7460e8fceb31d4b77e5db12bdb77ee；不重放任何旧模型请求。

新execution-envelope方案（与workload/请求超时/预热准入分开）：只把维护客户端的整个CLI进程wall上限120→600秒；原生HTTP命令/body/timeout不加任何字段，3warm+2measure及8%准入完全不变。原B0全部5轮elapsed<120且完整成功，上限从未触发，因此在600下同样有效；继续引用全部原B0，明确这是diagnostic操作预算例外，不宣称正式对比契约。后续独立核验仍逐轮原生commands除了唯一结果路径必须全相同。

唯一新job sampler-shortlist-service-followup-003/ROOT D/service-followup-003：controllerSHA9ed0479e0375fc01b41e47fa4ce484abb7849ccb1724ccf1f2d04af173406479、planSHA40e3fd1e12661cbfaa2a01487dbefe2f2afae866faab95125f192943cdab0f2c、supervisorSHA1f9a56ee84cdccaf8aa5840fe77531a24a19d755e0b7268421b9c5ac85de8e01、starterSHA657df632322ffb495349468322cde7e2b09075ef48bc1d368ba81a9040596681。精确505650/start1141982297→C1/R/C2；算法49e9/全部受保护源不变，复用88+黑名单微测，不再做GPU算子测试。旧预算失败warm仅作历史开销，不并入新稳态矩阵，不回填成功。新的最终独立入口sampler-shortlist-independent-service-002.py SHA3bf81e1dba2051bb61e9372977650d68cfd3be981e29267421eb994cfd17a4ea，绑定003/native终态/currentc2，默认inactive输出D/independent-service-verification-002；旧reader001绑定002不可执行。正式GPQA仍未提交，须后续新精确服务方案，不能复用gate。

最终生产后另做一次真实public FGV入口的小范围集成核验（非模型生成）：验证实际导入/MetaX函数source49e9及私有MoE/GDN、实际黑名单，M64/V248320 scaled/k20/p.95与native原生oracle掩码相同，retained FP32 bit patterns（包括signedzero/subnormal）保持；只这一部署边界，不重跑88矩阵。仍需全量原生C64/full198精度，暂不声称模型精度通过。

followup003已原生exit0，summary completed_candidate_retained_pending_independent_review/errornull/restorationnull；C1/R/C2所有15轮完成，当前c2 API569935/start1142194043，launch9d2159/controller9ed047/plan40e3fd与监督receipt04c0be67d78dee84e0325146ac16e7bfff4fe41695214ca496f0bef36bedce65。独立002将按已冻结入口3bf81e执行，唯一commands/sampler-shortlist-independent-service-002.execute.command.json先x创建/SHA，再0生成审阅；不重放任何旧模型。正式准备时read-only实际find_spec确认triton位于/opt/conda/lib/python3.12/site-packages/triton，distribution为flagtree0.7.0+metax.gitfe1d24f6；来源是源码构建wheel，不能误写editable/source目录生效。

独立002实际通过report d1988e3c43120d824fc7890a1e7e23044517a3d4a0c10da05772258c65c46d6f，命令7f56bd64e140740542b817308fa9be86ad54770843bc2f3ea95b76ebe2877882。全部20轮保留且稳态/回退漂移1.020%通过；输出吞吐+11.1897%，meanTPOT-13.0037%，medianITL-16.1772%，meanTTFT-0.6975%/p99TPOT-10.5806%。只P1K/D128/C64/N64诊断，不是D1024/N128或正式验收。当前c2保留49e9，保护9667无意外差异。

下一步归档installed publicAPI独立bit级检查ffe7cdc19ccd6d4731a5f69ef751ea66a8ca215158916c67e48f3c8562f28914（仅独立GPU4进程，0模型请求）；正式manifest helper d3f45ccf1bde067099644812b13ecd38d052d28e08fc74824f0b79ae8d04c09e准确绑定已核对的site-packages Triton wheel版本；0生成formal准备器1bc5fc8188659033d0907fb523fd8f86670a88e6930849e97e31e999d3c56ce7。三个文件先commands唯一归档，不重装/不改当前源码/服务环境。完整正式流量将在preflight完成、同c2精确身份/保护源码确认后启动一次，保留原生rollingC64协议，不复用旧gate或回答缓存。

public-integration001在任何算子/生成前因独立进程free-memory准入失败：实际2341556224bytes（约2233MiB），低于2300MiB；nativeexit1，0kernel/0模型，原日志/报告目录完整保留。仅独立验证预算调整：002预声明min2000MiB、显存fraction.02（约1.27GiB），不抢占服务/不改数值断言/shape；源码49e9及所有88/GPU证据不变。新public002 SHA62871e40e0534535ee99ac2a3384334e2d229d486d723cb0f46152e4c672f5ef，manifest002 SHAb075d2ae4caedd7b1dac2547e526f3e195f18728247aa838c19c0c9e8e19d2ad，formalprepare002 SHA5d266808833419cdc5dd2f2c2ecb8ddc4397baa255977f0e79bed92af4ba5067只改引用，不覆盖001；001 formalprepare/manifest未执行，不执行旧入口。

public002实际nativeexit0，M64/V248320 BF16 scaled与±0/subnormal独立native oracle逐FP32位差0，保留值原位/RNG不变；实际公开函数和_shortlist_values各调用一次，测试进程profile finally恢复，没有服务hooks/模型请求。原Gems注册warning原样保留，不代表所验证API未命中。下一步唯一formalprepare002 execute.command先归档+SHA，0生成捕获谱系/源码/权重stats/tokenizer/当前c2/原生provenance两次与preflight，不运行旧r39辅助入口。

formalprepare002在manifest观察层exit1，0provenance/0正式生成：准确当前两rank PID/start均通过，但rank1原生stdout有缓冲、当前日志没有MoE行，observer错误把每rank已刷盘日志设成前件。不得把不存在日志伪称实测或为取日志重启改变当前身份；rank0原生日志有实际FGV MoE source，两个worker的源码字节/graph资格/保护清单继续绑定。新manifest003明确分别记录native_MoE_log_observed及证据边界，同时修观察log按LF拆分，绝不改kernel/模型/服务。SHA b5d35c64f581d02c26f2ec9f9b8054052f6625b9a6182edba13de29ee63b9bca；prepare003 SHA3aa1cad2e42d13ae9b798a8fee51abb513d87971311be5f0acb04e27adf22a0e，使用全新formal-c64-002输出，保留formal-c64-001全部0题错误，不重放002。

formalprepare003实际exit0，正式输出F=D/formal-c64-002，ready SHAb37619a72e078ea8f2548140b0e179ddc77ea6791f944528247793d3606add76。完整两次真实task/dataset provenance相等、旧原题/评分/生成源码和参数逐字段一致，model/endpoint metadata仅绑定当前opt2/8020，preflight通过；当前service manifest cd5e6aa4e39a1177b0d35aaf8732097acf232054d336999e5fb2941d1da81af4；config0eb4a03a1935167815922a1b9ee978dfb39a5b8ab3d0cd720f63f7865a42baf1，contract5060b691548f09bc4b2b017cca67a48b09b45667f684c4ad3de3ab7292745f3d，threshold.7753冻结、全198/C64/seed42/temp1/p.95/k20/max65536/HTTPseed1234、无回答缓存。0模型生成。

新单次正式执行计划：job sampler-shortlist-formal-c64-002，在当前精确c2 API569935/start1142194043/GPU4/5，原frozen wrapper→llmrun→openai-chat-completions，一次滚动C64/full198；controller f5e4d43aece9ac6d271497da4ddd55b12c941c46920b951a12c35e7b79dd00e9、supervisor ad3a02b45c60cdf634ff889aa95b45d44b02aaa6a2c85ae50f1009b816c1c476、starter5f03c7f38885aad7611fc49745af5099adc7f4fbae8bf458269767fbe6f33601、plan-freezer87860aecadfa26d7b5fe4efad32e7aca2a41330abf22effb756c1dfb813ef14d。先归档/SHA、冻结ready/工具/continuation并审阅，再显式启动唯一launcher。controller不改源/不重启服务；每30s精确API/env/cwd/9667源守护，身份漂移仅取消专用eval wrapper精确PID/start/argv及其已识别后代，不触碰模型/其他任务。8h整体操作预算、原生单请求7200与重试不改；所有partial保留，不整轮补跑。监督者child.wait留真实OS返回码。原生有效通过才acceptance issue/check新gate；未完整则不签发。正式后重新fresh manifest/源码/编译器与前件一致。

终态独立入口commands/sampler-shortlist-formal-independent-001.py SHA c27fa693efecdba787e385843461ea98800ad41e335bad67789585748048c99b 默认inactive，绑定新F/当前c2，只有完整native0或阈值失败native2/summary分数/errornull/currentjobnull才唯一命令--execute-reviewed-verification。scorer6953fb4a0aca4bdd47f92ee938e7de657804986b15afaf0e0937129ac8f60071的原native score函数AST保持旧003完全相同，离线重现历史160/147/161/154再核验198/396与新分数/新gate。输出F/independent-verification-001此前不存在，失败新文件修复/旧输出保留，绝不补跑模型。两rank当前原生MoE日志缓冲边界明确，graph replay为两独立C8、token>=2和FULL_DECODE_ONLY调度源码推导lowerbound2，不虚构直接counter/RPC。终态再准确记录，不提前说正式精度通过。

正式plan-freezer已exit0，execution-plan SHAa0525e034ad49c54514bff4bfff89dc5e84579e903d137695db5260a3861df8d；全部真实ready/config/service/contract/tool/新controller与scorer哈希审阅完毕。下一步仅执行commands/sampler-shortlist-formal-starter-001.execute.command.json归档后显式启动一次；controller/launch/native身份以后以实际回执为准。不得因为观察失败重复正式198。

唯一正式job已实际启动：starter命令5dd6cdc4d75b37f99d30e06c3e15fdedd07f55503b824dc70e1343c0977b4c19，supervisor693779/start1142406740、controller693780/start1142406743、job-launch SHA1e8eee4dbaed117dba85b45a228cc169489d19bf2225585715334a2d12543b6f。当前phase sampler_shortlist_running_formal_C64；evalwrapper15891/start1142406779，原生lm_eval命令已建立，runid2b3fe8a10ca941d0bb3df58de6c84aa4。正式流量启动后任何错误/观察不能使用0题逻辑整轮补跑。后续只观察此job，controller活动CAS勿并发修改。新start-observation001 df53e52aa4c4c780befa445b3db0d7fe4c934f6adbde947416140f1a1e561cc2唯一归档后只读currentnative日志/精确controller/supervisor与guard-latest及GETmetrics，不发模型或admin请求。

正式启动只读观察已exit0，start-observation-001.json SHAbc36e0d6f23548115d7684fb7d0e973847b46a79c784872614fbbff7fef2b02f；command5af1a83a302c2f93a60f78b549e6b6e22fcf7370b9b945ba234afde6364d0eaa。当前native初始化1/cache0/198待生成+已有原生响应，实际scheduler running64/waiting0，guard源码9667与精确API/env/argv仍通过；不是直接device shape观测。没有最终分数/gate，当前只观察唯一正式job。qwen35-shortlist hourly monitor已更新为F002/当前精确IDs与终态独立入口，状态不变静默、重要完成/失败通知、独立终态删除；所有旧观察/失败保持不重放。Accuracy Skill实际bundle再次inspect为1ed06a57f1f6e1ef39fb7fd872f579122b098a18f0255ade0a1160d6432c2b66，与本案例既有精度bundle一致。本次没有新profiler或正式性能。

2026-10-28本地凌晨heartbeat重新只读确认：正式F002 controller/supervisor均已退出，真实native-result exit0/formal.result exit0，summary passed_pending_independent_review/errornull，198完整唯一doc/396 strict+flexible行均已发布；原生strict=158/198=0.797979797979798，预冻结threshold.7753，当前仅待独立复核。原生gate13b72e7e2035e0fd28e44f2c1c809e7532c109759978a7a6f83e1e85fc450deb，runrecordccec6bb5cf3965e36d04ddf603f61d0f762574f8a70af9d730649d7e478329c3；这不替代独立结果。continuation current_jobnull/last_completed_job sampler-shortlist-formal-c64-002/phase passed_pending，SHAf5c68c92a13390f492de32d75dcc79739a2c4a16b42b7fb5f448261abb72ea1d。全量产物和plan文件SHA已先读核验，无新生成/补跑。

下一步只执行已冻结终态独立入口c27fa693efecdba787e385843461ea98800ad41e335bad67789585748048c99b，commands/sampler-shortlist-formal-independent-001.execute.command.json独立x归档并校验入口SHA后--execute-reviewed-verification。输出F/independent-verification-001尚不存在，任何失败保留全目录/日志，新文件修观察层，不重发模型。独立入口会离线旧160/147/161/154重现及当前逐题strict复算、fresh精确c2/完整源码/编译器/权重stats/tokenizer/同配置与newgate复核。

终态独立001实际exit0，command SHAea10e290cac03a7ab3cd2ade0f19ac6e8f790dd60a1ccadfc4eb832587d9882c；report ab644f95c7160ad791e74d844b67aa6cad23aefbd7aef6d6360ef5eb337dc46d、native-strict-scores baa6e40e1a639f1c63fd201e198cf00d95368922a2bda1bee3dfb2adfaea0fe6。**158/198=79.7979798% >= 用户NV77.53%预冻结阈值**，198唯一doc/396filter行/旧160、147、161、154逐题原native重算通过；初始化1/回答缓存0，0timeout/0empty；5题[32,93,115,178,185]达到65536预算，原样strict计分不修改。该分数属于当前shortlist+既有MoE/GDN+当前FlagTree/Gems组合，不是shortlist孤立精度收益；也不满足旧160绝对参考，不将历史C32迁移差异解释为已解决。

前/后/fresh完整源码与当前精确c2/API/env/argv/编译器一致，9667保护文件/MoE/GDN保留；fresh service23c53fcfeb0d1dbe69e070cabe051cab441ee7a649593cc860de0f93b4b1e609，runtime c5d1d4d3f1e462a8e8352d72458ac22eaffa63206a1f3966daaa305325d5604a。新gate13b72e7e2035e0fd28e44f2c1c809e7532c109759978a7a6f83e1e85fc450deb已原生issue/check并独立复验。原生controller receipt880241a9281b0f11a7e9968081145328cb313091e485bb1c3b36b3b04ef30c42/formalreceipt107fd67252483682635a4172cb6bfd1df79520df624d1db21e0c4f422d991eb9/summarye3092b8e05222348d8e811ab877973c02952aaf63bc107d0deade16343d37aa2。正式性能未启动；短程收益仍仅P1K/D128/C64/N64范围。

收尾前先归档commands/sampler-shortlist-final-checkpoint-001.py SHA179e257c0af6bf194f823e9b5b9ffb0294216369a298772d536ab271ae004e71；0生成调用只读guard再核验同API与9667源、确认current_jobnull/原continuationSHA后备份并CAS写入verified_passed和新gate/结论。保留所有历史分数、失败与恢复，不重复模型或观察入口；随后删除qwen35-shortlist监控，任务完成，不自动性能。

收尾checkpoint实际exit0，command9872649b9f2bba470a37320748e291803c843172716baeacc805c57c6d26e155，checkpoint4a7e9398ef793b48a4f47b22fff3b767c9dc9973c88914766547c0006f8033a5，continuation CAS后SHAbcb1919ed13a4b319b5a46ccaa0a29a2d09f07dfbf66cf2d86ca6e4d58a4d453/phase sampler_shortlist_verified_passed/current_jobnull。再次精确current API/source guard通过；没有新模型/管理请求、源码/服务变更。qwen35-shortlist监控已在app确认Deleted（deleteStatus deleted），不再空轮询。当前optimize/acceptance和baseline可读当前摘要已同步，所有旧分数/gate/失败与不完整性能保留；对应组合覆盖的实验只追加当前组合正式结果引用，不改其历史结论。用户任务完成：FGV采样接口+安全shortlist已保留，既有MoE/GDN不变；独立C64/full198达标。正式性能未运行、不自动后续优化/模型重试。


## 2026-10-28 当前 opt3 组合精度复测

用户重启后的当前组合、实际prefix-on/GPU4/5/TP2，原生GPQA198/滚动C64独立通过**161/198=81.3131% >= 77.53%**。198唯一doc/396filter行/原prompt-target-args/无旧回答缓存/前后fresh源码一致，旧160/147/161/154逐题重现。验证：`/public-flash/jinghao/qwen3.6-35B/20261022-qwen36-35b-mx104-stack-regression/accuracy/user-gpqa-erqa-c64-20261028-001/gpqa-followup-001/independent-verification-001/verification.json` SHA c9437b838bd089152dc01a11c3f32076e89941334e545a89b8f175606366ebb9。此为保留组合精度，不证明本点独立贡献，不与旧prefix-off不同配置计算收益。随后官方ERQA多模态C64发生FGV MoE临时cache13申请256MiB OOM，服务退出；GPQA已测通过分数仍有效，旧实例gate不可直接用于新实例/新参数。ERQA部分证据保留、完整400分数缺失，不自动恢复/补跑/性能。详见[user-gpqa-erqa-c64-20261028-001.md](user-gpqa-erqa-c64-20261028-001.md)。
