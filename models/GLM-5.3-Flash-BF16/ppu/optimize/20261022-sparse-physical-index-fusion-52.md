# 点52：Sparse MLA物理索引转换OOM修复

最新14:28接续：[点53](20261022-steady-p1k-phase-baseline-53.md)已按用户授权修复正常调参写入的绑定分类问题。原生173/198、86%阈值及旧manifest/DB前后SHA保留，新增显式同实例缓存更新schema5 gate并经原生check通过，没有重跑或补充精度。当前源码/URL/策略/argv/实例均未改，三阶段P1K稳态基线已唯一派发；下面14:07“当前绑定未生成”只描述修复前历史，不再阻塞继续性能分析。

状态（14:07终态）：去掉全部临时MM/观测hook后，实际默认flagos生产路径C64与完整最小模型回归通过；同一实例原生单次198题/C64全量GPQA **173/198＝87.373737% ≥ 86%，分数达标**，无补充/择优替换。正式期间原调参DB SHA改变，严格前后绑定未通过，当前gate未生成；不能改写manifest掩盖差异或将其称为模型精度失败。服务健康且保持运行，无新稳态性能。11:40前OFF/临时策略为历史。

## 全量GPQA终态与DB绑定诊断（2026-10-22 14:07）

本轮独立UUID `9ed1dbe6679840c4ab49454698241f04`，原生结果时间为UTC 05:38:54，评测4830.078870秒；`formal.exit=0`。冻结C64、seed42、temperature1/top_p.95/maxgen60000、strict≥.86未变。`eval_max_retries=0`；API层沿用原配置`api_max_retries=3`，与无整轮/题目补跑的约束区分，不宣称API也零重试。

原生`acceptance.verify_run`复验全部引用SHA、task/data provenance、metadata、原doc/prompt/target/arguments、198唯一题与两个filter各198行（总396行）通过。strict答对173题，score `0.8737373737373737`，不是任何历史173题补充结果，也未用旧169/171/175分数改绑。doc_id **[8,15,71,75,79]** 的输出60000 token且原生timeout标记为true，只作输出健康观察，不增加精度门槛，未补跑。

原生控制器`completion.json`明确为`process_exit_code=0, identity_unchanged=false`，`accuracy-gate.json`不存在。对比原开始、结束和新增当前manifest：除运行快照SHA外，仅`launch_config.flaggems_db_sha256`从`96ce45e20e0a8a412170a3c1c1d160026463c78f513635169aed4db642c4e6aa`变为`605719d97abd8fbec95690cd7c5eacbe63b866ee18ed0793753f68b8f927ea84`。URL、三库/vLLM完整源码及git状态、argv/环境、权重/tokenizer/thead/脚本、镜像/挂载、实例均相同。与原Default调参写入一致，但未逐条归因DB写入者，不能夸大为完整写入因果证明。

按`inference-accuracy-diagnosis`冻结issue `point52-production-formal-DB-identity-drift`：已确认是严格身份绑定中的DB字段差异，不是模型数值回归证据；**本轮原生分数达标保留，当前服务绑定仍incomplete**。没有改旧manifest、清空/复制/回退DB、强签gate或重跑来凑一致。未自动继续性能；后续如何冻结可变调参缓存并取得有效当前绑定，须另行决定，不能用改旧记录代替。

终态只读审计复用既有FULL capture及多token请求证据，未新增推理。实例仍`PPU-13:glm5.3-flash-opt-20260911:2151833:535760459`、health200；16worker无临时hook环境/trace FD/TileLang映射，Plugin与FGV各一份editable安装，未见OOM、非法访问或sample_tokens RPC timeout。无模型或启动参数变更、提交推送、新性能或非PPU结论。

审计v1已通过当前完整身份与原生verify_run，但补充脚本的`str.splitlines()`把JSON响应内Unicode分隔符误当记录分隔，辅助解析失败；原始样本与native验证未失败。保存新`commands/terminal-audit-v2.py`（SHA`247958526f783b9c61293dd6615d590728c720b6c1a7c4d74df7f1bb2a490c2c`）后，仅改用原生`acceptance.iter_sample_records`、复用v1新快照，零模型请求恢复审计。旧v1/快照保留，未改采样/分数/阈值。最终`terminal-audit-v2.json` SHA`23b1079e709d538800684f5a7b068832d79f1be6b3fc742ab43145e32d7ee5ad`；run-record SHA`71e58dee74f42fd640680121cc94e6e60bf489f1c6d689055e9b1cfa4c4415b4`、results SHA`97edcd042d6e97371a76fce5709c4964a6f6c8d1b121e32d6ed236bb69548d61`、samples SHA`e3f13b47a8ac856081e2607afbf9ea0270714c5dd54a9885f64e5cdda7bc1ec2`。

以上证据均在远端`index-conversion-repair-08/production-no-mm-02/formal-gpqa-01`；完整绝对根见文末与state。终态与最终当前审计后，`glm-c64-gpqa`已删除（工具回执`deleteStatus=deleted`）。以下进行中均为保留的历史时点，不再描述当前状态。

## 实际生产路径接续09（生产回归通过，GPQA分数达标；当前gate因DB漂移未生成）

用户要求去掉临时MM策略，保持MBT/启动参数，重做实际生产C64与完整模型回归，全部通过后再64并发全量GPQA。沿用本点同一文档/源码，不叠加优化；新远端子目录`production-no-mm-02`不覆盖上一轮。

预检及原始无hook探针通过后，freeze`933f343c…`，12:03:14唯一派发控制器PID2866049/start535760382，命令`commands/index08-production-control-v1.py` SHA`6ff5a5b9…`。它以原脚本逐字启动，仅cwd改为本轮日志目录；未添加env覆盖、未改库。`glm-c64-gpqa` ACTIVE每30min只读/不变安静，回归失败审计或正式终态审计后删除。当前为服务启动中，不以准备或dispatch回执填回归/正式通过。

12:05:43原脚本服务就绪，实例`2151833:535760459`，16worker无PYTHONPATH/算子覆盖及旧trace FD探针通过，实际Sparse MLA日志为`glm5.flaggems`。C1通过；C8出现60s广播等待警告后于12:08:48自然完成8/8，没有延长超时、插入hook或重试。12:10:27原smoke/C8、三16K边界和11/11明确答案均通过，C64正在执行；无OOM/非法访问/RPC错误，尚不宣称64/64或正式通过。

12:15:49生产回归完整通过，原C64的64个请求/响应ID唯一、每项4096输入/16输出且非空；C1/C8、三16K边界、11/11答案、FULL 11/11捕获与多token回放通过。16worker前后均无临时PYTHONPATH/算子覆盖/旧trace FD，原生maps未映射TileLang，实际Sparse MLA为`glm5.flaggems`。原source/argv/环境、权重/tokenizer/thead及脚本未变，没有OOM、非法访问或RPC timeout。C8与C64长等待后自然完成，不因此宣称稳态性能提升或已无冷路径开销。

源码仍Plugin529cd814…/FGVba76c1df…/FG1a6197b7…，唯一安装与原index语义保留。原生产DB由239ed14b…变为96ce45e2…，是预声明允许的原Default调参合法写入，配置URL未变，不复制、清理、恢复或回退DB。当前生产回归`completion.json` SHAf69f1dba…、`production/c64.json` SHA030eccc6…、`production/final-audit.json` SHA5c7a17f9…，完整SHA见state。

正式命令`commands/index08-production-formal-v1.py` SHA2d0aafb3…先保存校验；复用原生正式工具归档d94c622d…及固定helper4aae6323…。两次真实provenance相同（c3c31ea3…）、198题数据内容指纹167548b0…，原生preflight通过，零答案请求。服务manifest3d459ebf…绑定生产回归同一实例，正式期间不重启/热改。

12:18:10唯一派发正式控制器PID3212528/start535850018，子目录`formal-gpqa-01`。冻结原198唯一题/C64/seed42/temp1/top_p.95/maxgen60000/strict≥.86、eval_max_retries0、独立UUID缓存、无补充/best-of。当前无最终分数/gate；native工具保留严格前后身份比较（含DB SHA），不能重写manifest掩盖漂移。既有`glm-c64-gpqa`继续只读跟进，终态审计后删除。没有自动性能实验、提交推送或源容器操作。

11:54只读确认当前源码精确为点52、目标无API、16卡各1MiB空闲，原launcher SHA5b1d0a52…未变，FlagGems MM/libentry原SHA不变。原脚本清除VLLM_FL_PER_OP、使用原生产DB；因此按原脚本启动默认flagos，不保留临时vendor覆盖、PYTHONPATH/sitecustomize观测或MM限4hook。不拷贝/清空/回退调参DB，正常调参写入只记录前后实际身份。

先`minimal-regression`原P4096/D16 C1/C8、smoke/C8、三16K边界、11明确答案、P4096/D16/C64/N64及FULL捕获/多token回放，证实实际默认实现。任何失败保留并只停止本轮自有服务，不自动重试或晋级；源码未变不回退既有修复。全部通过后保留同一实例，单独冻结`formal-gate`：198唯一题/C64/seed42/temp1/top_p.95/60K/strict≥.86、独立UUID缓存、零自动重试/无补充或best-of，原生runner、provenance与绑定gate不变。无性能、提交推送或其他平台扩展。

## 问题与单变量

沿点51 MM07必要C64失败：`forward_mqa → _convert_request_to_physical_indices → torch.remainder → empty_like`申请544MiB时OOM，全部16rank报错；当时每worker22次MM限4策略实际命中，不能把本次OOM继续称为RPC超时或候选未命中。原生证据在点51远端`mm-fixed-shape-07/model-regression-02/candidate/vendor/service.log`。完整峰值/碎片归因仍未知。

原转换物化多份全尺寸int64输入、块号、物理地址、前缀和、sink/scatter中间张量。已用FGV通用融合kernel逐行完成映射、无效项过滤和稳定压缩，仅分配最终int32索引与长度；不改变top-k顺序、重复项、物理槽位、有效计数或cache ABI。相对MM07模型候选，仅改变转换实现，H4及同一MM外部诊断策略为冻结前置，不宣称生产调参策略已验收。

## FGV编码前项目真相

| 字段 | 冻结内容 |
| --- | --- |
| 任务/API | 专用`convert_sparse_indices`，参考当前Plugin原PyTorch组合实现；非ATen算子，不注册虚构ATen schema |
| 可改 | FGV通用ops/导出/功能测试/benchmark，Plugin既有MLA辅助函数/单测；不新增thead模型路径 |
| 只读 | vLLM、FG、权重/tokenizer/生产DB/启动脚本；原MM07全部证据 |
| build | 既有唯一editable安装，纯Python/Triton无需重装；核验实际import |
| validation | 原实现独立reference逐位相等；空/非连续/页边界/无效空洞/重复/大地址；PPU graph两次动态回放；模型原C1/C8/16K/11答案/C64 |
| benchmark | 同shape原实现/融合实现，记录峰值allocated及中位调用耗时；只用于内存机制，不替代稳态E2E |
| active set | int32/int64索引/请求/页表，TOPK非二幂及KPool扩展宽度，rows1/8/64及大Prefill；真实16worker记录最大M32768、K2176，不把微基准K8320当作真实模型宽度 |
| timeout | CPU/设备验证900s；模型readiness3600s、客户端900s；首个错误停止，不盲重试 |
| profiler | 本轮原生OOM栈+精确分配/设备峰值与实际调用事件；不要求NVIDIA profiler，不伪造trace |
| autotune豁免 | 正确性/有界内存修复：固定1024元素scan tile、4warps，宽度循环覆盖；不扩大请求期搜索/graph内调参，无NVIDIA性能验收声明 |
| fallback | 生产仅Triton，无torch compute/copy/cast；仅允许metadata、empty与no-copy view；不支持输入显式报错 |

## 对齐契约与路径

| 字段 | 语义 |
| --- | --- |
| 输入 | request_ids[M]、block_table[R,B]、token_indices[M,K]，同设备、整数int32/int64，任意非重叠strides，正block_size；合法request IDs |
| 映射 | logical token>=0且logical_block<B、对应physical_block>=0；physical=block*block_size+token%block_size，计算地址先int64，最终int32与原实现一致 |
| 输出 | 新分配int32[M,K]和int32[M]；有效槽位按原列顺序稳定压至前缀，保留重复，尾部-1，无输入mutation |
| dtype/异常 | bool/float/complex、跨设备、rank/shape不符、非正block_size不支持；NaN/Inf不适用，推理forward-only |
| reference | torch组合仅测试/benchmark使用，不由生产导入 |

| 路径 | 实现/测试边界 |
| --- | --- |
| empty | M=0或K=0返回正确shape；K=0须填零长度，不能返回未初始化计数 |
| regular/wide | 每row按1024列循环：masked页表load、int64地址计算、block内cumsum+跨块计数，直接scatter最终前缀并填尾部；无O(MK)中间workspace |
| layout | 从真实stride寻址，不用contiguous/to生成大副本 |
| unsupported | 规范化metadata后显式报错，无torch fallback |
| external | 无TileLang，无新vendor依赖；非PPU硬件未测 |

## 模型验证与回退

Host PPU-13、优化容器`glm5.3-flash-opt-20260911`/8011；源容器不动。TP16/BF16/MBT32768/maxseq64/maxlen80000/FULL_DECODE_ONLY/关闭前缀缓存、launcher SHA5b1d0a52…保持。先完成算子/Plugin CPU与PPU数值、地址/内存、动态graph护栏，再以新身份启动原模型，复测P4096/D16 C1/C8、原smoke/C8、16383/16384/16385、11答案、原C64/N64。不得以子图/CPU通过代替整模。此轮显式`e2e/accuracy: minimal-regression`；正式GPQA/gate触发在原范围全部成功后单独冻结，不自动开展性能。

操作前完整核验SQL-only/OFF与三库状态/index、唯一安装/镜像挂载、DB和设备空闲；精确保存原文件，失败仅恢复本轮SHA匹配的变更与H4前置，保持原dirty/index和master DB不变。仅停止自有进程，不争抢用户任务。无提交/推送。

成功策略：保留H4前置与本次融合修复源码，精确停止仅用于诊断的模型实例；外部MM策略hook不写入安装库、不保留为生产开关。新正式精度/gate仍需单独冻结/评测，不自动启动性能。失败则全部回到本轮前SQL-only/OFF。FGV根包既有`ops import *`和`_FULL_CONFIG`消费ops导出，因此本次只增ops导出，不添加虚构ATen schema或重复注册框架。

10:59预检完整通过，16卡各1MiB、原SQL-only/OFF与DB身份不变；限定源码快照SHAac89f35c…。原始G1协议中的optimization.md/deep_opt.md在目标仓库缺失，已明确记录；本轮使用协议允许的固定调参豁免，只修内存正确性，不宣称NVIDIA或其他平台性能验收。现有`compute_global_topk_indices_and_lens`不做稳定压缩/缺页过滤，无法保持本函数契约，故未直接替换。

执行前冻结overlay六文件：Plugin辅助函数/单测两既有文件，FGV ops导出一既有文件和通用op/测试/benchmark三新文件，无thead文件。payload SHA5e43c448…、manifest f1492a4c…、相对MM07差异daadd1df…；source guard4f7e74f4…、controller d993df65…、metadata-only hook7048136f…。原MM政策、keys、20/100协议与数学kernel不改；精度bundle6e94a080…经原生verify绑定`minimal-regression`。freeze SHAe0f10a41…于11:12:45唯一派发控制器PID1663931/start535457493，`dispatched.json`绑定；新`glm-oom`监控30min只读跟进，不变安静、终态审计后删除，不重复旧点51。CPU/设备/模型结果尚待原生回执，不能填写通过。

## 外部产物与当前结果

### v1 CPU护栏与测试边界恢复

11:14 v1在CPU阶段失败：416通过/6失败/17 deselected，76.31s，`CPU.xml`/failure保留。两处cache测试直接用CPU张量验证转换数值，四处provider路由单测隐式执行了转换；新FGV算子为Triton设备专用，拒绝CPU计算，故触发NotImplementedError。尚无设备测试或模型请求，控制器已精确恢复SQL-only/OFF与DB不变并通过完整终态审计。不能填设备/数值/模型通过，也不新增生产Torch回退来迎合CPU fixture。

新`validation-recovery-01`只修测试分层：两处原cache数值案例标gpu并将输入放真实设备，原预期/断言逐字保留，新增必须执行的PPU cache阶段；四处CPU provider选择/错误传播测试隔离转换依赖，新设备测试仍真实对拍转换。两生产文件（Plugin转换wrapper、FGV kernel）SHA与v1一致，误差/内存/graph/MBT门槛未动，pytest首错即停。新payload28ba31ec…/manifest c4befe46…/diff e20b110e…，controller41190abf…/guard7fc35ecc…执行前保存；原v1全部材料、冻约与回退结果不覆盖、不混入新轮。新模型仍须前置真实数值/graph/峰值检查全过才启动。

新轮在SQL-only/OFF/16卡空闲预检后冻结SHAffe2521a…，11:22:45唯一派发PID1869851/start535517550，原monitor已更新相同新子目录。旧v1不是模型/数值失败，不通过放宽生产CPU支持“修好测试”；两处原断言转真实设备能实际约束新kernel。11:24 CPU原生collect为420项/19 deselected（新增两处gpu），仍在执行，无设备/模型结论。

11:25:24只读原生结果：CPU420通过/19 deselected，76.39s；FGV算子145通过，28.37s，包含int32/int64混合、非连续、页边界、无效空洞/重复/大地址/空输入及3宽度各2次更新输入的动态graph回放。两处原Plugin cache数值测试设备阶段已执行两个通过点，等待最终XML/控制器状态复核。峰值比较与整模尚未完成，不把此结果当C64或OOM充分修复证据。

## 正确性前置与内存机制效果（11:26）

原生XML和控制器复核：CPU420、FGV设备145、原Plugin cache设备2、benchmark4全部通过，两个迁移案例原断言由真实kernel完成；`validation-v1.json`允许进入模型。FGV设备测试包含3种宽度各2次更新输入的动态graph回放。

| M×K | 原组合中位ms | 融合中位ms | 原额外峰值bytes | 融合额外峰值bytes |
| --- | ---: | ---: | ---: | ---: |
| 8×2048 | 0.202320 | 0.040220 | 1000960 | 66048 |
| 64×8320 | 0.208280 | 0.045000 | 32482816 | 2130432 |
| 8198×8320 | 11.593660 | 0.558900 | 4161812992 | 272862720 |
| 16384×2048 | 5.533020 | 0.275220 | 2047148032 | 134283264 |

每项20次预热/30次CUDA-event测量，输出逐位一致；峰值是同输入下`max_memory_allocated-base_allocated`，不是reserved、进程总显存或模型峰值。原组合reference为同语义Torch组合，未声明与Plugin开启FlagGems的正式服务计时等价。8198×8320从约3.88GiB降到260.22MiB，验证该路径的全尺寸int64中间量是可消除内存来源；4.63–20.74×仅是单设备完整转换微基准，不是稳态端到端收益。

模型当前进入原参数启动/回归，尚无C64终态或正式精度gate，不能提前宣布完整OOM修复。

11:33:31原生回执核验：P4096/D16的C1与8/8请求通过；原smoke/C8、16383/16384/16385精确原文长度和11/11明确答案通过，FULL 11/11捕获后已完成多次多token请求。C64已进入此前失败的大批次路径，快照26running/38waiting，无OOM/RPC报错；这不是64/64完成或稳态性能结果，须等待控制器终态与身份审计。

## C64与完整最小模型回归终态（11:40）

11:38:58 `model-result.json`通过原冻结全部范围；11:39:03控制器结束并停止仅本轮自有诊断服务，保留H4及融合源码。11:40:18独立当前只读审计再次通过，未发任何模型请求。结果如下：

| 验证 | 原生结果 |
| --- | --- |
| P4096/D16 C1、C8 | 1/1、8/8通过 |
| 原smoke与C8 | 通过 |
| 原文输入长度边界 | 16383/16384/16385逐项通过 |
| 明确答案 | 11/11通过 |
| P4096/D16/C64/N64 | 64/64唯一请求与唯一响应、每题4096输入/16输出、非空，finish_reason均length；实际观察到64驻留 |
| Graph | FULL_DECODE_ONLY 11/11捕获，已完成多个多token请求；不是逐rank replay trace |
| 转换命中 | 16/16 worker，包含实际`32768×2176`，int32输出285212672 B（272MiB）+长度131072 B（128KiB），无额外tensor同步 |
| 故障 | 本轮未见OOM、illegal memory access或sample_tokens RPC timeout |

实际shape的一个旧int64全尺寸张量即`32768×2176×8=544MiB`，与原失败申请吻合；融合后直接输出272MiB并消除原链条的多份全尺寸中间量。独立同语义内存对照、实际命中与原C64重现范围成功共同支持**该转换路径OOM在本契约内已修复**。没有分配历史全量snapshot，仍不把所有峰值/allocator碎片归为唯一根因，也不把原冷MM RPC解释为同一个问题。

验证实例`PPU-13:glm5.3-flash-opt-20260911:1976007:535535035`，Plugin源`529cd814ae0ab3aae55304bc01a6ef43c82722d64ff6dfcf1c01a5419a104b64`、FGV源`ba76c1df80c4bf4316216bde10ac7a727601f810c58fe1cb1d670d51f6ff5085`，FG与vLLM未改。最终完整文件/index语义、唯一editable各1份、权重/tokenizer/thead、镜像谱系/挂载、启动脚本及生产DB均通过；生产DB仍`239ed14b…`。原TP16/BF16/MBT32768/maxseq64/maxlen80000/FULL/关闭前缀缓存argv不变，源适配容器未动。

**执行边界**：整模沿用MM07的`flash_mla_sparse_fwd=vendor`显式选择、独立同源起始DB和临时MM冷搜索限4诊断hook；此轮只隔离转换变量，没有宣称默认flagos整模、去掉临时MM策略后的生产路径或60K/198题均通过。MM hook随诊断进程退出，不写入安装库；当前8011 OFF是预定结束策略，不是运行失败，也未自动启动用户服务。高风险融合仍无当前正式精度gate，历史175/198、171/198等不复用；不能开始正式性能晋级。

关键原生证据：`candidate/vendor/c64.json` SHA`de4f0e14…`、`model-result.json` SHA`ab042637…`、`completion.json` SHA`498616ae…`、`final-audit.json` SHA`beda2e07…`，当前`terminal-current-audit-v1.json` SHA`2f75a766…`。独立审计命令`commands/index08-terminal-audit-v1.py` SHA`a6041efb…`先保存校验后执行，零模型请求，未并发或重复控制器；`glm-oom`已在终态审计后删除。完整SHA见state。无提交/推送。

## 规划复盘planning52

本次按`inference-optimization-planning`把MM06的异shape诊断、MM07的固定冷搜索机制/C64失败、点52首次CPU fixture失败回退和本轮通过分别列账。当前组合是公共模型+SQL修复+H4+融合转换；冷MM策略只是诊断进程hook，不是已部署的生产优化。新身份四场景均无稳态baseline→组合候选测量，累计收益未知，不能叠加旧MM冷调用和转换微基准加速。

Prefill已消除转换中间量，完整模型峰值/碎片仍未知；Decode只验证FULL和多token正确性，延迟/波动未测；Mixed仅有C64短正确性，不能替代D1024/N128三臂。下一轮顺序：先冻结实际生产provider/MM策略并做原最小回归，任何失败立即停止；再对最终新身份做198题/C64原生formal-gate，strict≥0.86；有有效gate后才建立当前场景同配置Prefill/Decode/Mixed稳态checkpoint、必要时reprofile。旧调度方案、MBT和新kernel调参均不在此轮自动扩展。当前交接本次已完成修复，不自动派发新实验。

本地GLM状态schema、链接及diff whitespace检查通过；全项目`validate-local --records`仍被其他模型既有schema/链接与过程文件问题阻塞，没有修改那些文件或宣称全项目验收通过。PR仍experimental：默认provider/生产策略、新正式gate、非PPU硬件和最终style审查未完成。

沿用用户授权远端根，唯一子目录：`/mnt/nfs/users/jinghao/glm5.3-flash/optimize/e2e-opt-20260911/resume-20261021-point51-sparse-mla-small-head/index-conversion-repair-08`，本轮在其`validation-recovery-01`。命令/SHA/源码/原生结果留远端；本地只保存MD、state与总览，不建history。上文进行中是各时点历史，终态以本节为准。
