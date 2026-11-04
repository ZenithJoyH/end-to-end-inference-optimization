# env-065：旧兼容实现清理与FGVLLM专用算子默认接入

- 当前状态：completed-source/test/doc-cleanup；Gems旧common/MoE差异已清退，FGVLLM旧PLE测试合并、3说明链接恢复，CPU/静态及manifest审计passed。全部生产修复保持，不重载或新增设备/模型测试；此前Gems磁盘收敛仍无新模型绑定。前一阶段一次8010切换＋10短doc2回归是历史结果，不重签formal gate；无性能结论。
- 用户2026-10-22授权：清理FlagGems中不再使用的PLE/QSA/GDN及导出，启用`VLLM_FL_USE_FLAGGEMS_VLLM`，必要修复直接落FGVLLM。
- 目标：PPU-07 / `qwen3.8-flash-opt-ppu07-20261015`，三个规范源码目录。后续用户授权的唯一重启已使用，8010健康保留；禁止再次重启/追加请求、访问8035、全量GPQA、提交或推送。
- 本地`inference-accuracy-evaluation`显式模式`minimal-regression`：10条同一短doc2，不当作10唯一题或全量分数，候选不可继承acc018旧gate。下文源码阶段的“不重启/模型incomplete/原服务未变”均是当时历史，后续授权与终态见末节。

## 优化方向与设计归属

复用Plugin既有`VLLM_FL_USE_FLAGGEMS_VLLM`分支，不修改Plugin registry或默认源码、不另造dispatch。当前旧服务保持原私有副本/开关；本次修改规范editable源码、root新shell默认环境和后续明确启动的候选。原Docker Config.Env不支持原地删除/更新，不编辑Docker内部配置；现有用户shell需source更新或显式export。开关覆盖多类专用算子，不能称只迁移alignment。

FlagGems只移除`fused/ple_state.py`、`fused/qsa.py`、`fused/gdn_packed_decode.py`及`fused/__init__.py`中对应导出，先全树反向引用审计。`common_slot_mapping.py`不在本次删除范围。保留index/index_put/randn i64、现有MoE修复及全部旧私有树用于在线服务和回退。

FGVLLM generic alignment目前仍可能在PPU尝试TLE且4stage零extent为0；复用op061已确认的能力门禁和3处`max(1,...)`，只改host dispatch/launch geometry，不修改四阶段kernel、排序契约、tile/warp/调优或其他vendor路径。现有`tests/test_moe_align_block_size.py`补CPU路由/零extent及设备边界用例，禁止另造重复测试文件。

## 编码前项目真相表

| 字段 | 冻结范围 |
|---|---|
| Current op / API | `moe_align_block_size_triton`及共享4stage launcher；不是torch标准单算子，参考现有两库原四阶段源码/测试 |
| Editable | Gems旧3文件及fused导出；FGVLLM alignment host gate/3个extent、原测试文件；root bashrc/profile追加有界新shell默认开关 |
| Read-only | Plugin、vLLM、权重、tokenizer、原私有Gems/FGVLLM/BF16树、现有service/历史证据、benchmark和调优配置 |
| Build | 源码editable，无重新pip或依赖升级；Python AST/精确diff核验 |
| Validation | CPU提取真实host函数AST，mock kernel/alloc验证路由与非零extent、保持非目标路径；源码/导出反向引用、spec/direct_url与新shell变量 |
| Benchmark / active set | not_run；本次不比较性能。CPU覆盖thead/nvidia、TLE开关/失败、CUDA标志、E10/250/512/1025、M0/1/64/128/8065等geometry |
| Aggregation / timeout | 全部CPU用例逐项计数，失败停止、不筛选；CPU命令限120s，不新增模型请求 |
| Autotune / profiler | 不新建/改kernel或性能参数，沿用原libtuner，豁免新增NVIDIA配置；不运行profiler/设备枚举 |
| Fallback policy | 不新增torch计算fallback；PPU从不支持TLE分支直接进已有Triton四阶段，原NVIDIA路径保持 |

## 算子契约与路径表

| 项目 | 契约 |
|---|---|
| 输入 | 合法expert ID的整型topk_ids，目标常用int32；现有连续/shape/stride约束不扩大 |
| 输出 | 原地写int32 sorted/expert/count；有效前缀按expert分组，组内次序按原测试multiset契约，padding/count/alias不改 |
| 数值 | 整型索引，无新的promotion或浮点舍入；NaN/complex/autograd不适用；非法ID支持范围不改变 |
| 空输入 | 允许0路线及紧缩0长度输出，launch extent至少1，kernel原mask保护；不通过torch填充补洞 |
| fast/special | 原非thead且满足TLE条件仍沿原路径；small-group/singleton kernel不改 |
| general | PPU或原非TLE条件进已有4stage；共享launcher同时保护no_tle入口 |
| unsupported | TLE cooperative在thead不进入；其他原unsupported/error边界不变，不吞新错误 |
| reference-only torch | 原设备测试oracle允许；本次CPU不导入生产包或torch，不把mock当数值/graph通过 |

FGVLLM AGENTS/workflow完整读取；`optimization.md`、`deep_opt.md`在该revision不存在，记录缺失，不伪称已读。workflow中预填conv1d任务与本用户alignment迁移无关，以当前用户范围和上述窄契约为准。这里只做必要兼容修复，G5设备数值/G6性能及新模型门禁保持待验证，不进入深度性能优化。

## 正确性、停止条件与回退

先核Host/容器/挂载私有性、Git、exact8010、源SHA与无引用，再备份所有预定8文件及权限；三旧模块采用移动到可恢复备份，不直接丢弃。应用前每份核expected SHA，拒绝覆盖同期编辑。禁止改安装和在线私有源码；生产包不导入、设备不初始化。CPU/static失败冻结首错，工具错误和模型错误区分，不自动扩测或恢复服务。

root启动文件仅为未显式设置开关的新shell提供默认`1`，保留用户显式`0`和其他PYTHONPATH。不以shell环境声明冒充8010已切换。既有旧root启动备份和FP32源码回退备份均不改。

回退只针对本次精确文件/marker、在核当前SHA后从新备份恢复；不reset Git或清源码树、不自动回退服务。清理会删除3个规范目录旧模块，但备份/原私有目录均可恢复。

## 性能效果与晋级

本次无baseline/candidate/revert测量，吞吐/延迟均null，不声明收益。`pr_readiness=needs_revision`，等待新路径的设备数值、graph capture≥2replay、C1/C8及按风险触发的新formal验证；需要重启/设备测试时先告知用户取得方向，不自动执行。

## 外部证据

计划根：`/mnt/nfs/users/jinghao/qwen3.8-flash/20261015-qwen38-flash-next-ppu07-container/environment/env-065-flaggems-vllm-routing-20261022`。命令和关键配置先保存`commands/`并记录SHA后单次执行；备份受限0700/0600，不打印root启动文件原文。当前仍处于实施前，完成后在同一文档补结果。

## 执行前命令与CPU检查

候选和一次性命令位于本地临时目录`/private/tmp/qwen38-env065.qMZosh`，AST检查7文件通过。仅将3份命令和3份源码payload以排他USTAR传入上述新外部根，核SHA后仅一次运行其`commands/control.py`；不运行任何服务启动或评测脚本。

- control SHA `767b0265ee09f74f4eda2171a5dd68e51369b949f723e833fadcd2a0975a03bb`
- apply SHA `098ebe5e4ae839c86eb740305bcbbc92520207df00d91e0762c87d19d9e94230`
- CPU audit SHA `183c2ffc2a052efaf4a7535419e75a2b575a614649e44d3b28dbce17d2230fe7`
- stage SHA `5965c376a60b8d49901cdfb3d63a755efc062380a328bdd9dfcaa46f06ce9073`
- 新Gems fused导出SHA `f5ae8e0e2f3d25351758083a24049dd5c0e4e9036387d74af18c4a7d08805b0a`
- 新FGVLLM alignment SHA `39949f44cf8c232d6297d4366577b62da686d43a5622ea01e150e25fefab940d`
- 原测试文件补充后SHA `ef21e15710d2c1729a05ba7d897b1925c50041d31e5eb49c84ce2b7e081dc1cd`

本地CPU提取真实host函数，执行原测试文件新增7路由＋12extent用例及530geometry，全部通过；所有其余函数/kernel AST逐份同原FGVLLM基线，只改2个host函数。首次本地调用误传Gems源作为FGVLLM基线，被严格AST差异断言拒绝；读取真正未改FGVLLM文件并核原SHA后通过，不是模型失败，也未在失败后修改kernel绕过。系统Python未安装black，未安装新工具/依赖，格式验证不冒充已执行Black或全套CI。

生产路径Torch调用AST列表前后完全相同；原代码已有3处zeros初始化及多处empty分配，继承保留、不声称满足全库“无Torch compute”清理。本次没有新增compute/copy/fallback，没有把这些既有调用扩大成重构范围。

## 完成结果与证据边界

唯一control已正常退出，`SOURCE_FINISHED.json`、`FINAL_SUMMARY.json`、`FINISHED`齐全。实施前核源SHA、原8010身份及唯一`/mnt→/mnt`挂载，目标源码/root均为容器私有overlay；未改容器镜像/ENV/挂载、没有pip安装或依赖更新。

1. 旧`ple_state.py`、`qsa.py`、`gdn_packed_decode.py`已从规范Gems源码移到`<外部根>/removed-legacy/`，三文件逐SHA一致；`fused/__init__.py`去除三组import和9个导出。`common_slot_mapping.py`保留。旧模块源文件和同目录sourceless pyc均不存在；没有清理缓存。3859份含Gems引用的源码/测试AST未发现阻塞显式引用，Gems根包无悬空旧名称；动态用户代码和未扫描外部依赖不作完备保证。
2. FGVLLM只新增runtime device导入、generic TLE分支的thead门禁、共享4stage三处max1；kernel/其余函数AST均与该FGVLLM原文件相同，不能拿两库不同版本作此结论。已有测试文件新增7路由＋12extent用例，原设备矩阵补M0/M1，未创建新的仓内测试文件。目标容器同样19用例＋530geometry全部CPU通过；不把它们称实际排序数值或GPU graph通过。
3. Plugin本轮0源码改动。静态检查Plugin当前从FGVLLM公开导入的26个符号，均存在于该revision的声明导出；不等同运行时vendor分支/签名/数值全覆盖。Plugin BF16、Gems index/index_put/randn/i64及旧MoE、FGVLLM PLE i64+CTA和QSA M16共7项关键SHA全部保持；各库editable路径与版本不变。
4. `/root/.bashrc`、`/root/.profile`仅追加env065默认开关。三种新`bash -ic/-lic/-lc`在原Docker旧PYTHONPATH输入下均清除旧覆盖、取得开关1并解析三个规范源码目录；显式0测试保持0。已有用户终端需`export VLLM_FL_USE_FLAGGEMS_VLLM=1`或source启动文件；直接非shell Docker exec仍须显式设置此开关并清除旧PYTHONPATH。没有把不可变Docker Config.Env宣称为已更新。
5. 原8010 Host1924405/start531054985、argv SHA `c146e2da…`、原私有PYTHONPATH和未设置的专用算子开关前后相同，health200；三个实际在线私有源码树全部前后同SHA。即**当前在线服务仍原Gems MoE路径，尚未加载本次规范目录或FGVLLM开关**。不重启、不停止、不发任何推理/GPU请求、不访问8035、不提交/推送；monitor保持PAUSED。

备份8个精确原文件在`<外部根>/backup/`，目录0700、复制备份0600、原SHA逐份校验；root文件原文不打印或写入项目。备份manifest SHA `21abb49c3f42d97129cd6bb180329f6cdb7c0437a567acc5355148a703ffc6db`。源码变化只限Gems src四路径（3移出＋导出）和FGVLLM src一个host文件，外加既有测试文件和两个shell文件；原Git HEAD/index暂存内容不改，VS Code可见差异，未reset/commit/push。

summary SHA `90a24b4f0d14790ed83d9b0e73154de3b3d5c5ed0be61f2d33a8ee5f5e296710`；33文件manifest SHA `1add8ca876113434b59d2a52b6ffa863d71984073352a48b26c8a5161be1335c`，终态独立逐文件hash/大小核验全部一致。最终bashrc SHA `90b6e1523c069ecba336309dfface588de5ce6c5bae9d240afd0c9b8eeb4fdea`、profile SHA `06be61ef6e65dce1809f6932795db5713c2d2d51a822cbf73b36c9d8139c442e`。

决定：保留规范源码及新shell默认候选，但不晋级为模型通过或正式性能候选。需要用户另行授权服务切换后，才能验证真实导入/dispatch、设备边界、capture与至少两次replay、C1/C8，并按广泛专用算子切换风险补新formal契约；不自动执行这些步骤，不改写acc018旧结果/gate。`pr_readiness=needs_revision`、性能not_run、formal gate null。

## 新授权：仅一次8010重启与10请求模型最小回归

用户2026-10-22已明确授权：仅重启8010一次，加载三个规范/opt源码目录、开关1，验证graph capture/≥2replay及2C1＋8C8并确认来源；保留BF16/所有修复，保存完整证据，不访问8035/全量GPQA/提交推送。本段替代前文“不重启”的当前操作限制，但只允许本次一次启动，无自动恢复或第二次启动授权。

本轮R为上述env065外部根`model-regression-001`，唯一`R/commands/model-control.py`。覆盖env062/063/065，使用本地`e2e/accuracy minimal-regression`，bundle SHA `804b60f96089a5f37ee76d40c1ba11405ed8e61b45940786b52e52ed7b91edfb`。沿用acc018 baseline已冻结的10条短doc2请求，2C1再8C8，max2048/0重试/无HTTP隐藏预热，原温度1/top_p.95/top_k20/min_p0/presence0/repetition1/seed1234/stop/完整prompt和token。这是短题护栏，不扩大到困难题或全量。

先完成原生PIECEWISE/FULL各7/7 capture，再用前2条C1产生的原生FULL已完成执行统计证明至少2次replay（结合冻结native wrapper源码），完整token两次相等才进入C8；不为先凑replay另发推理请求。原生统计不冒充独立逐rank GPU replay trace。

唯一允许对旧Host1924405/start531054985/argv c146e2da…发送一次SIGTERM，空闲确认及冻结owned tree后自然排空；不追杀子进程/停容器。只查物理8–15空闲，绝不查0–7或8035。新CLI与原实例逐字相同；仅切canonical源码editable、专用算子开关1、独立新cache/log根。保留normal_/index_select黑名单、QSA M16、PLE i64+CTA和固定pin047调优。PYTHONPATH不再含三个库源码覆盖，只含本轮启动bootstrap：保留逐字pin047并记录8rank加载函数对象/来源，不改数学函数、不采集逐层/状态/张量、不添加额外模型执行。源库解析必须全部落/opt标准目录。

prepare阶段只冻结现有源/Git/模型metadata/tokenizer/weights stat及精确实例，复制既有HTTP/graph helper而不执行其旧run；新命令与SHA先保存。run排他一次自然排空→启动→readiness最多40min；异常停止新阶段、在途自然收集，保存首错、原始HTTP bytes/token、日志/8rank来源/编译佐证和manifest。startup失败不重启、不补发/改源。终态保留新8010不停止，回写本记录/state/README；新formal gate仍null、性能not_run。

模型执行命令已在`/private/tmp/qwen38-env065-model.WAyP8l`保存并5文件AST通过，排他staging至新R/commands：model-control SHA `89241b98f448833b2bb53ba2b23ef8abb1ac3ad69be56341d7f2b3ae2b1f5c50`，source_probe SHA `5510b55ecba68562a1cee10b6c7fe4786bf37c03176b0438093906ee92f66672`，origin_audit SHA `32625a356d9af06e66e2fafb234adff944b21f935f91d5a095f0627d84d63c4c`，冻结旧HTTP/graph helper SHA `8c9c1e3485a12af2a5b1cc0a05cffc39bc77196411c8046ef9117d55767dd0f4`，stage SHA `c2e3830b24e51bd0e2c7ab95308d03b58922c892a11b6b4b830acdf47c019d10`。先只执行`--mode prepare`，核PREPARED/launch/requests/source后仅一次`--mode launch`；后续只读监控原run。未执行旧helper的prepare/restart/run。独立cache根`/opt/qwen38-env065-fgvllm-minimal-20261022/cache`，Gems与FGVLLM均实际读取`FLAGGEMS_CACHE_DIR`和`FLAGGEMS_DB_URL`，不清旧缓存、不增加新性能变量或预热流量。

prepare已成功，未停止/启动/发请求。PREPARED SHA `38899924bbc6d0d9a113b05d20c78f868eb1468e152373cfa7d95a571cc0c16d`，source-before `2b5cbe056bc5c8a7c4807293baa069688d113d5c6d4d2d4c3c2568c3c168259d`，requests `e4a18024f742dc3ab9a36e9103a06b176c867e6bf0ab466263fe35aafead244c`，launch `4dc8964606a5124441269eb28be47cff3dac2a0d1f579eaa7b31309d4c96647d`，pin047字节仍`61da24bb…`。新进程spec全部canonical，原CLI、黑名单、10 seq/max2048/0重试已二次核验。下一步仅一次launch，禁止重放prepare/launch/run。

唯一driver Host1425501/start536664349/argvSHA `b36722f792c4e2bfc68b2dbd64a94925b9707af5e848ea746776646ac0aa3619`已启动。旧8010仅一次SIGTERM后自然排空（epoch1792650820.0319605），物理8–15逐卡空闲后唯一新启动attempt在1792650820.2545366；不得再次launch/restart。初期新服务加载权重，8rank source journal均已生成，未发HTTP；READY及capture/replay仍待既有controller自然完成。API日志NS PID不能直接当Host实例绑定。

14:52+08只读复核：主torch.compile完成，PIECEWISE capture已4/7，独立新缓存持续产生FGVLLM MoE/PLE产物、8worker CPU推进；尚无READY/HTTP/error，不能将shm60s等待提示单独当停滞。all8 journal的Plugin/Gems/FGVLLM包根均为规范/opt目录，6个专用函数实际对象指向FGVLLM（含thead MoE sum/QSA），GDN packed beta仍为Plugin补丁；这是加载对象与新编译来源证据，不是逐kernel调用trace。

终态另备一次CPU-only审计命令`R/commands/terminal-audit.py`，本地AST通过，SHA `fbe3cf43f169aa068fa3be67d6a59bbf810d60945d0e8e59379598ea6b0d2f87`。仅在原driver已退出/僵尸且FINISHED/summary通过时排他执行：独立核原manifest、10raw/prompt/token/usage/thinkend/EOS/两C1相等、graph/8rank来源、source前后一致、精确8010健康，以及现有编译源和产物哈希，补冻完整日志尾部至新`cpu-terminal-audit-001`。不发模型或GPU请求、不改服务/旧原件；审计失败保留首错，不自动重复或修模型。

14:58:08+08 READY绑定新Host API1426766/start536664682/原argv SHA `c146e2da…`，health200，PIECEWISE/FULL capture各7/7、all8规范来源/开关1。15:04+08两C1都B517，完整token相等、thinkend位置266/EOS248046、非空final/finishstop；进入C8前原生FULL计数929。其后8条C8已全部由原controller派发，15:05尚在途，errors0；完成数不能用10派发代替，终态审计仍待补。

## 模型终态与独立证据审计（2026-10-22 15:07–15:11+08）

原controller已自然退出，`FINAL_SUMMARY.json`、`FINISHED.json`及`terminal-evidence-001`冻结完成，唯一启动1次、HTTP请求10次、重试0、隐藏请求0。随后仅一次执行上述CPU审计，排他生成`R/cpu-terminal-audit-001`，没有再次启动或模型/GPU测试。

| 核验项 | 结果 |
|---|---|
| 源码加载 | all8 package根均为`/opt/vllm-plugin-FL`、`/opt/FlagGems`、`/opt/FlagGems-vllm`，editable加载；开关1，PYTHONPATH仅pin047/启动来源journal bootstrap，无库源码覆盖 |
| graph | PIECEWISE/FULL各7/7；C8前native FULL929，终态summary下界1718；其中真实unpadded8/padded8 FULL至少438次，另有自然排空的7/6/5/4/3/2/1行。结合冻结native wrapper说明replay，不称独立逐rank每次GPU trace |
| 两C1 | 均B517，完整token序列逐项相等，thinkend位置266，末EOS248046 |
| 八C8 | seq2..9均正常最终B；completion tokens依次558/624/815/675/603/658/753/438，不要求不同batch下推理token逐项相同 |
| 输出/HTTP | 10份完整HTTP200、prompt各321，总prompt3210/generated6158；完整API token长度与usage逐份一致，均thinkend248069、末EOS248046、finishstop/非空final；无None占位、真实HTTP失败/超时、2048截断或异常marker |
| 范围 | 诊断gold匹配10/10但仅1唯一doc；不是正式strict分数，不签新gate，不外推困难题、C64/60K或性能 |
| 源/配置 | source-before/after逐字相等，BF16 model/i64 index/index_put/randn、PLE i64+CTA、QSA M16及FGVLLM host门禁/空extent关键SHA全保持，normal_/index_select黑名单及pin047保留 |
| 终态服务 | API1426766/start536664682/argvSHA `c146e2da4762690185e9b3573c5f48796a5cb42aa2037de0d08d9ada40595010`，health200，running0/waiting0/KV0/preemptions0，保留不停止 |

实际来源：all8已加载函数对象的MoE alignment/fused-MoE/topk/PLE在FGVLLM ops，MoE sum及QSA公开选择在FGVLLM thead backend；GDN packed beta修复仍从`/opt/vllm-plugin-FL/vllm_fl/patches/gdn_packed_decode.py`提供，不虚称所有GDN已迁入FGVLLM。独立复核56个journal函数链源码SHA无不一致。新隔离cache编译源也命中FGVLLM HC、topk、MoE alignment/fused/sum、PLE fusion/conv和QSA核心；QSA公开thead wrapper与下层通用核心文件不能混为不同路径故障。完整已存编译source及同目录IR/binary哈希列表2500模块，见CPU审计`compiled-origin-and-artifact-hashes.json`；这是编译与加载证明，不是全部层/状态/logits/每kernel实测因果现场。

完整request/HTTP headers/原始body/token与result均保存在R的`reqNNN-doc002-*`；服务/driver日志、8rank journal、原source前后快照和固定调优日志已冻结94份文件，独立逐SHA/大小全部一致。CPU审计另补冻完整日志尾部，原controller manifest不改。首次graph/请求JIT有长等待但持续编译推进，已保存原始日志，不能据启动开销推断稳态回退。

- summary SHA `20a790a4907e8243ea710a0fbdc074f58d7303dc24e991594d0bfc67a9f595bb`
- 原manifest SHA `3dfc27d1c626379fe84859281bd546e58911f0555903c22886fa35aa7befe59d`（94份全核）
- CPU报告SHA `a9c7b7a15391b2a8795c3cc74abc7d8daf2bb19ac2a33cd45eac26a72fbc17d9`
- CPU manifest SHA `f68fd4823507d00f2bedc7169b09d91fc1a5d796db21c38321fcbaa0c8f15979`（再次逐份核验通过）

决定：保留本轮canonical BF16＋FGVLLM开关1的健康8010及现有修复/回退备份，minimal-regression passed（上述范围）。本Skill促使先核capture/replay/C1一致再C8、终态绑定和完整证据审计，未以短题代formal。`pr_readiness=needs_revision`仍待跨平台/更广范围证明；不提交/推送、不访问8035、不重跑全量、不自动执行后续验证，等待用户方向。已有heartbeat保持PAUSED。

## 后续授权：清退未使用Gems common slot及自有MoE差异

用户2026-10-22明确要求：清理Gems不再使用的`common_slot_mapping`及导出，撤回自有MoE修改和对应测试，保留回退备份、FGVLLM修复及Gems index/index_put/randn；不重启、不访问8035、不提交推送。延续同一env065优化点，外部新排他根为`E/legacy-retirement-001`，无新模型或性能实验。

方向为源码收敛/旧路径清理，非性能提升。当前规范Plugin开关1分支直接从FGVLLM导入MoE；精确API1426766/start536664682/argvSHA c146e2da…仍健康空闲，prompt3210/generated6158，无新流量。三库及安装vLLM源码反向引用仅发现Gems common函数定义与两处导出，没有调用点；动态外部使用不作全覆盖保证。Gems既有MoE差异恰为op061的thead TLE门禁、3处max1及对应新增测试，本轮按用户要求撤回，不改FGVLLM等效修复。

仅4个精确文件可变：`src/flag_gems/fused/common_slot_mapping.py`移入可恢复备份；`fused/__init__.py`删除该import/export且要求等于当前HEAD；`fused/moe_align_block_size.py`及`tests/test_moe_align_block_size.py`恢复已核当前HEAD f0aa7f12180cea4776a2aba3f3889b8fb82a28b1的原始blob。保留原Git HEAD/index/其余文件，不reset/checkout、不改其他仓库、不pip、不改环境/cache/服务。原4份文件及完整diff先排他备份并核SHA；每次写前再次expected-SHA确认，源冲突即停止，不自动覆盖或扩清理。

本地accuracy `minimal-regression`（bundle804b60f…）只执行CPU工程子集：HEAD精确字节、AST/无悬空符号/反向引用、三库源码前后allowlist、关键修复SHA、Git HEAD/index不变、editable解析及8010实例/health/counters不变。用户禁止重启/推理，因此本次新磁盘候选模型graph/C1/C8为incomplete，不拿此前10请求套新源码绑定，不签gate或性能结论。先保存命令/SHA后一次执行；失败保留既有证据和部分变更，不自动重试、恢复服务或修改当前FGVLLM路径。

命令位于本地`/private/tmp/qwen38-env065-retirement.Ly4vx9`，4份AST检查通过。control SHA `a6ca7e42927c177731205b177b0a1bb4be73d67be13776c1dc7576d748998042`；apply SHA `5a0bf5075c07de194fb6a65fc4cacc9d1271a59e724d80b98f3a8df88f421a73`；只读source_probe沿用已核字节`5510b55ecba68562a1cee10b6c7fe4786bf37c03176b0438093906ee92f66672`；stage SHA `25f32177cb40be52a066260d95401305d4419b01ce30a7ddbd5f59a512e67647`，先排他复制至`E/commands/env065-retirement-stage.py`。仅USTAR排他staging至新`R/commands/`，核命令SHA后一次执行control（无mode/服务方法）。control先核容器/同实例空闲/source-before与上次model-after完全一致，apply备份后仅动4路径；source-after要求Gems src恰3差异（另tests恢复独立核），Plugin/FGVLLM/其余关键内容均不变。CPU验证失败保留首错，不自动重复。

首份默认tar混入macOS附加元数据，被stage精确3成员断言拒绝，发生在R.mkdir之前；只读确认R仍不存在，controller/apply均未执行、生产源码未变。未放宽断言或改stage；本地重新用`COPYFILE_DISABLE=1 tar --format=ustar`生成并列出恰3成员后再传输。这是前置传输工具错误，不是模型/CPU候选失败，也不计重复执行清理。

### 清退完成与CPU独立审计

唯一control正常退出，`FINAL_SUMMARY.json`和`FINISHED.json`齐全，执行清理仅1次。外部R完整路径：`/mnt/nfs/users/jinghao/qwen3.8-flash/20261015-qwen38-flash-next-ppu07-container/environment/env-065-flaggems-vllm-routing-20261022/legacy-retirement-001`。

- `common_slot_mapping.py`原件移到`R/removed-legacy/common_slot_mapping.py`，另有独立复制备份；对应import/export移除。三库＋已安装vLLM的精确符号反向引用由7297份文件中的2份定义/导出，变为7296份中的0份；不宣称覆盖未知外部动态调用。
- Gems fused导出文件、MoE alignment和原测试文件均与HEAD f0aa7f12180cea4776a2aba3f3889b8fb82a28b1对应blob逐字相同，SHA依次`7eaada325e249261f44629ed364ff89076672f209235d6aeef37f14a94f275af`、`a2308bb7aaba53427ae7dcadf9002c1976fe160b33a1c00d0f3540f51f51386d`、`d47ff1c5a520107f4317e2d032ba4c3e924e8048a0e18059618304d077b5951c`。独立读取再次核验通过，未用git reset/checkout或修改index。
- Gems Git工作区只剩`src/flag_gems/ops/index.py`、`index_put.py`、`randn.py`三项自有差异，其关键SHA完全保留。Plugin完整树和FGVLLM完整src前后相等，BF16、PLE i64+CTA、QSA M16、FGVLLM alignment TLE门禁/3处max1保持，FGVLLM MoE测试独立核SHA仍`ef21e15710d2c1729a05ba7d897b1925c50041d31e5eb49c84ce2b7e081dc1cd`。三库HEAD/index、editable路径和版本均未变。
- 4份原文件完整复制备份在`R/backup/`，SHA逐份核验，备份文件0600/证据根0700。`R/Gems-before.diff`保留原全部修改，`R/baseline/`保留此次恢复的3份上游blob；原有env062 FP32/旧私有树/env065前期备份完全不动。删除为可恢复移出，不丢弃唯一证据。
- 前后同一8010 API1426766/start536664682/argvSHA `c146e2da4762690185e9b3573c5f48796a5cb42aa2037de0d08d9ada40595010`，health200，running0/waiting0，prompt3210/generated6158均不变，开关1/启动bootstrap不变。没有服务操作、推理、GPU测试、生产包导入、pip、缓存或采样变更；未访问8035/其进程/0–7，不提交推送。

summary SHA `d85c7e540d4f528133f3753eccb90f81c78b93574922e51f188c580ca93f3c4e`；manifest SHA `2ffa38cefecbae2dbbe60155cbab7c9dcf56c93ca26600a8a78fdd2a83bf0f34`，独立核26份文件大小/SHA全部一致；backup manifest SHA `97590a51eeb26d355deb67d2b222b1d6fa9e5e9c01aee3cfa2e0be84007f2bbe`。`CPU_AUDIT.json`保留精确恢复/反向引用/剩余修改检查，source-before/after保存三库与模型/原生graph工具指纹。

决定：保留当前磁盘收敛版本，CPU工程passed；本地minimal-regression的模型graph/C1/C8为**incomplete（用户明确暂不重启/推理）**，未把之前10请求结果套给清退后的源码。运行中Gems旧导出/函数对象未强制卸载，现有FGVLLM活动路径未改；不以磁盘清理冒充运行中代码重载。无新gate/性能结论，monitor继续PAUSED。以后若显式将开关改0，Gems MoE现为上游原实现，PPU原TLE/空extent修复已按本次授权撤回，须另行验证或有授权地从备份恢复，不能宣称该旧路径仍已修复。

回退须先核目标4文件当前SHA/缺失状态及本备份manifest，再精确恢复`R/backup`对应文件；不要reset整个仓库，不覆盖index/index_put/randn、FGVLLM或用户后续编辑，不自动重启服务。本次Skill将源码检查和模型验证分开记录，未因清理成功虚报新模型通过；后续等待用户方向。

## 后续授权：FGVLLM测试合并与说明链接恢复（实施前）

用户要求将容器旧`tests/test_ple_conv_large_state.py`合入原`tests/test_ple_conv.py`，保留边界/graph覆盖，恢复`.github/copilot-instructions.md`、`CLAUDE.md`、`GEMINI.md`三个符号链接；现有算子修复与全部回退备份不变，不重启、不访问8035、不提交推送。本轮仍为env065源码收敛，外部新排他根`E/tests-docs-cleanup-001`。目标AGENTS及workflow完整读取，optional optimization/deep_opt不存在；workflow预填conv1d开发任务不扩大本次纯测试/文档范围。

| 编码前项目字段 | 本轮冻结 |
|---|---|
| Current op | 已有PLE短卷积state测试组织，不新增/改造torch或生产算子 |
| Editable | 原PLE测试、旧独立测试移出、三个说明链接；共5路径 |
| Read-only | 所有src/调优/导出/注册/benchmark、MoE测试、AGENTS、Gems/Plugin、安装/服务/cache及旧备份 |
| Build/validation | Python AST/compile、测试函数/装饰器/参数case Counter逐份等价，31case不得少/重复；graph循环、索引/canary/state断言保持；链接按HEAD且可解析；CPU源码指纹/精确8010绑定不变 |
| Benchmark/active set | 不执行性能或设备测试；原20＋旧11=31参数case静态覆盖，非已有PR扩展211项的新运行 |
| Autotune/profiler | 本次无kernel/perf参数/dispatch变化，显式不适用，不动NVIDIA配置 |
| Fallback/Torch | 仅测试oracle使用已有torch计算；不新增任何生产compute/fallback |

| 算子/测试对齐契约 | 保持内容 |
|---|---|
| dtype/layout | 原BF16/FP16/FP32，strided cache与实际rowstride204800、大row10485/10486/11242/12000、NULL/负数/越界、空输入int32/int64 |
| 输出/语义 | 原独立CPU oracle、输出容差、state exact、alias/inplace、guard/canary断言逐份保持；不借测试合并调整舍入 |
| 路径 | 原public PLE绑定不变；旧独立测试原直连implementation导入使用私有alias避免重绑定原public入口，仅归一化两处调用名称，不改变被测函数 |
| graph | 原3个mode的单次replay及旧9case每次3个动态indices replay全部保持；只静态核等价，本轮不执行GPU |
| unsupported/autograd | 既有CPU拒绝/资源skip和空输入语义保持；不扩大训练或其他平台承诺 |

三链接HEAD分别指向`../AGENTS.md`、`AGENTS.md`、`AGENTS.md`；当前AGENTS存在且与3个展开文件逐SHA相同。先备份5份原文件，再原子替换原测试、把旧独立测试移到可恢复目录、原子恢复相对symlink；不创建损坏链接、不改AGENTS或其他文件。合并后的新增case继承原module的ple_fusion marker，参数与函数体保持；不跑pytest导入生产包以免初始化设备，不用旧211或上轮10题代本次验证。CPU工程passed与device/model未运行分开记录，不签新formal gate或声称性能收益。发生SHA冲突/AST差异即停止，无自动重启/扩测/提交。

本地候选在`/private/tmp/qwen38-env065-tests.BHwDFQ`，原8个函数完整AST相同，旧3函数（含嵌套graph/reset/verify）仅对2处私有导入alias调用名称归一化后AST完全相同；31参数case Counter无丢失/重复。保留12个静态graph参数case及30次静态replay契约（原3次＋旧9×3），未实际执行。原module已有torch/算子依赖；旧单独文件头部importorskip不另带入，未扩大无依赖环境支持。所有原oracle/断言/参数/资源skip不改。候选语法/空白/88列检查通过；本地未安装pytest/Black/isort/flake8，未安装依赖或声称全套pre-commit通过。

执行前命令SHA：control `f678f2aac36aab47181892a3621084f78c11182c9e15e40312e3c3239e82c3c2`，apply `61ec92192af53b57add668c4f34f8a81d87c4a6210abc5922f8300d16fdc7fea`，CPU契约 `7a45b1a6c6b2bf4e1d2da25641cb48cd9864312152fab199e0290ab747571d96`，source_probe `5510b55ecba68562a1cee10b6c7fe4786bf37c03176b0438093906ee92f66672`，stage `5ae8118962046af478c88a6b5700d66a0455a88c02f586d645f4e0f620ae7c7a`。合并后test SHA `44198f22d018bc58299ff5caa925166c0c3555cdf0891d00258ff5b03a2ad6a2`；case Counter SHA `4b485d5781e82f36b5ca7b32ddf2ab6954488ed1076f4bd18afd815df7186cc8`。stage先排他保存`E/commands/env065-tests-docs-stage.py`，用关闭macOS附加元数据的USTAR将5个命令/候选排他传入新R/commands；核SHA后仅一次执行R/commands/control.py。先核当前source等于上一轮legacy-retirement/source-after及同实例空闲，再备份/应用/CPU审计；前后全部生产src/模型/安装原生graph指纹须完全一致，完整FGVLLM树仅5路径变化、各库HEAD/index不变、服务计数不变。不修改其他路径以解决格式或审计问题。

### 测试/说明整理完成

唯一control正常退出，`FINAL_SUMMARY.json`与`FINISHED.json`齐全，应用1次，0设备/模型请求/服务操作。外部R为`/mnt/nfs/users/jinghao/qwen3.8-flash/20261015-qwen38-flash-next-ppu07-container/environment/env-065-flaggems-vllm-routing-20261022/tests-docs-cleanup-001`。

1. 旧独立PLE测试的独立oracle及2个测试函数合入原`tests/test_ple_conv.py`，原8函数AST精确不变，迁入3函数仅两处调用别名归一化后AST相同，参数case Counter精确等于20＋11＝31，无丢失或重复。大row/实际stride204800、三dtype、NULL/负数/越界/空输入、canary、原output容差/state exact及所有graph循环保持。12 graph参数case/30 replay只是本轮静态保留契约，不是新执行次数。独立文件从活动仓库移至`R/removed-legacy/test_ple_conv_large_state.py`，保留原字节及另份备份，不删除原数值证据。
2. 三说明文件恢复真实相对链接：`.github/copilot-instructions.md → ../AGENTS.md`，`CLAUDE.md → AGENTS.md`，`GEMINI.md → AGENTS.md`。独立readlink/resolve/existence和Git HEAD blob核验均通过，AGENTS内容不改；对应Git类型差异消失，不生成复制文件或失效链接。
3. FGVLLM完整有效树恰5个批准路径变化，其余所有有效条目相等；三库全部生产源码、模型/权重metadata/tokenizer、版本/editable解析与原生graph工具指纹前后相等。PLE i64＋CTA、MoE TLE/空extent、QSA M16、Plugin BF16/GDN及Gems index/index_put/randn均未变；三库HEAD/index不改，Gems清退结果和既有所有备份不动。
4. FGVLLM当前Git仅4处修改：两个生产文件`ops/moe_align_block_size.py`、`ops/qwen4/ple_conv.py`及两个原测试`test_moe_align_block_size.py`、`test_ple_conv.py`；没有旧独立测试或3个说明类型差异。语法、空白、88列、diff-check和容器内静态等价通过；未运行全套pre-commit或真实pytest/GPU，不以静态覆盖宣称数值/跨平台通过。
5. 5份原文件已复制备份于`R/backup/`，目录受0700根保护、文件0600，逐SHA回读；backup manifest SHA `6747ac2638bd3acaa6d730d713d76f2d266e8c43a41a2a9e1f91669496c36627`。旧独立文件另移出保留，kernel/先前回退备份不动。summary SHA `aa7c1f104fb0ceab3e83ee3d50ff5dff455b1df3f5f04cd2ddf2a46f62c0f5ac`，manifest SHA `1877ddbac47bd5f1cf4a3a14d2ce4427572105eab643f20bc44b22115de2e678`，独立核27份文件SHA/大小全部一致。
6. 同一8010 API1426766/start536664682/argvSHA c146e2da…前后不变，health200、running0/waiting0、prompt3210/generated6158，环境/请求计数完全一致。没有导入生产算子或初始化设备、不GPU、不重启/推理/GPQA、不访问8035及0–7、不pip/改cache、不提交或推送，monitor保持PAUSED。

决定保留测试/说明整理，`minimal-regression`的本次CPU工程子集passed，device/model未运行，无新gate/性能结论，也不改写原211矩阵或10短题结果。该Skill促使区分静态契约保留与新硬件验证。回退须核当前5路径类型/SHA、备份manifest和无同期编辑，精确恢复相应原文件；不reset仓库或覆盖算子修复，不自动重启。准备上游提交前仍需按用户授权补实际设备测试和完整仓库风格检查。

## 非MoE三个修复点的上游去重核验（2026-10-22）

用户要求提交除MoE外的三个修复点，并明确确认范围为PLE i64、PLE CTA同步、QSA M16，已有PR或已合入者不得重复提交。本次只读GitHub API及指定blob哈希，不连接目标机器、不改容器或服务。

- PLE两个修复已经完整包含在[PR #959](https://github.com/flagos-ai/FlagGems-vllm/pull/959)，关联[Issue #958](https://github.com/flagos-ai/FlagGems-vllm/issues/958)。当前状态open/draft、未合入，head `22194f0b2ee0cebb51f945a20a157b82c4e19c65`；diff仅`ops/qwen4/ple_conv.py`及原`tests/test_ple_conv.py`，没有MoE。源码回读SHA `2f273afafdfd1a991dd0138b0d330d001cf0cd17bdcb96b83a22a5f3929140c0`，等于已验证候选；现有PR保留211项扩展边界/graph测试，不用容器最近31项组织版本替换或缩减它。
- QSA M16已经通过[PR #940](https://github.com/flagos-ai/FlagGems-vllm/pull/940)于2026-10-19T02:46:41Z合入main，merge commit `b4d3382bb04da4e0ab444849697865b4d5fcd86e`。当前main的thead wrapper仍调用共享实现并传`min_block_m=16`，回读SHA `3bb3d08342ac47415c62c5c11b2d88b85aa8fe9701d48890b5a8751b88db895a`，等于当前保留版本。

决定：三项均已有上游提交覆盖，按用户去重要求不新建Issue/PR、不追加commit或push、不修改现有PR正文/草稿状态，也不把MoE、说明链接整理或其他仓库改动混入。此次不是新CI/数值验证或新精度gate；仅核实公开状态和源码覆盖，后续若要推进审阅可继续原PR959。

### 后续授权：检查CI/review并转正式PR

用户明确授权若无问题将PR959转Ready for review，不修改容器或重启服务。2026-10-22只读核head仍`22194f0b2ee0cebb51f945a20a157b82c4e19c65`：code style、rule-check、select ci targets、multi-backend summary与license/cla全部success，0失败/待完成；NVIDIA及matrix backend测试/benchmark两作业skipped，不能当硬件测试通过。reviews为空、requested reviewers为空、review threads为空；三条历史会话均为作者进展说明，无change-request或未解决阻塞。GitHub当次MERGEABLE/CLEAN不等于已审批。

已于2026-10-22T08:06:41Z（北京时间16:06:41）将原PR转为Ready for review，随后回读open、isDraft=false、head未变，仍无审批或合并；原PR附加本任务。不新增commit/push、不重跑CI/硬件测试、不发审阅邀请、不操作任何容器/服务或访问8035。

尝试同步正文旧draft状态说明时，工具安全自动审查拒绝了正文外发更新（认为完整替换payload涉及未经本轮明确授权的验证/环境细节）；回读正文未变，未通过CLI或其他方式绕过。故当时界面状态已正式送审，但正文仍有旧draft文字。本次CI/review检查不产生新数值结论、精度gate或硬件覆盖。

用户随后明确允许仅更新draft状态说明及已核CI，不新增环境或验证细节。重新读取PR与CI后，仅3处精确替换：`Limits / draft status`标题改为review status；`PR remains draft`改为ready for review（后续原有限制逐字保留）；旧“新提交CI需独立检查”句改为head22194f0b已核5项通过、两硬件作业跳过、无失败/待完成检查。其余正文逐字保留，无新增模型/硬件/验证事实。工具更新成功，独立回读完整body精确等于预期，isDraft=false、head未变；不改代码、标题/base、关联Issue或审批状态，无容器/服务/8035访问或操作。

## 独立MoE PR授权与冻结范围（2026-10-22）

用户明确要求单独提交MoE修复PR，保留算子内thead拦截和空输入修复，复用原有测试文件；不得混入PR959，不修改容器或重启服务。本地独立克隆`/private/tmp/moe-fgv-pr-20261022.lgc4aR/repo`，上游main `7417158440a80753fb21dab3a124c1be388ab7eb`，干净树。当前MoE源码与env065原始baseline逐字相同；生产候选复用此前已保存源码，不接触/opt或SSH。AGENTS/workflow完整读取，optimization/deep_opt缺失，不虚称读取；预填conv1d任务不扩大本次已有算子修复范围。

| 项目真相 | 本轮约束 |
|---|---|
| Current op / editable | FGVLLM MoE alignment host dispatch；仅`ops/moe_align_block_size.py`及原`tests/test_moe_align_block_size.py` |
| Read-only | 所有kernel、调优/注册/导出/benchmark、其他算子/PR959/容器/运行服务 |
| Build / validation | 临时venv安装CPU测试/风格工具；真实host函数AST路由、零extent/正geometry等价、所有kernel/其他函数AST不变、仓库pre-commit；不导入生产包或初始化设备 |
| Active set / timeout | 原7路由＋12extent mock、530 geometry；扩展原设备矩阵M0/M1，并在同文件覆盖compact空buffer及graph契约（新增设备测试本轮不执行）；CPU检查每项60s、工程检查10min |
| Benchmark / aggregation / profiler | 不执行，无新吞吐/延迟收益结论；仅兼容与边界修复送审 |
| Autotune / integration | 不改kernel/warp/tile/autotune；所有正extent保持；已有导出/注册/benchmark不需要新增；仅零extent clamp为1并保留原mask |
| Fallback | 不新增torch compute/拷贝；thead直接进原四阶段，其他平台TLE及异常fallback原样。原有torch.zeros初始化继承不扩展，不称全模块零torch调用 |

| 对齐契约 | 本轮保持 |
|---|---|
| API/reference | 已有MoE API，不是torch公开原生算子；复用原文件torch oracle、专家内token multiset及exact expert/count契约 |
| Input/output | 原合法num_experts>0/block_size>0、整型topk route IDs、shape/layout/alias/workspace契约；空topk/零长度输出有界mask；不新增浮点/promotion/autograd承诺 |
| Semantics | expert内顺序不保证稳定；不修改路由数学、排序容差、dtype或非法输入处理；非目标平台行为保持 |

| 路径 | 处理 |
|---|---|
| TLE fast | 非thead且原HAS_TLE/CUDA/expert条件满足时完全沿原路径 |
| thead / general | 算子内已知不支持cooperative barrier的thead跳过TLE，进入原四阶段；不全局禁用TLE |
| empty | 三处launch extent用max1，仍执行原masked四阶段并写回count0，不新增生产torch fallback |
| 其他fast/unsupported | singleton/small-group/所有kernel不变；未知异常仍遵循原策略，不新增宽泛捕获或永久失败缓存 |

精度方法选择minimal-regression，bundle804b60f…，本轮只完成CPU工程子集；新隔离PR候选device/graph/model为not_run/incomplete，不拿Gems旧83项或此前FGVLLM模型10条冒充本次PR完整硬件测试。提交描述只公开通用源码机制/合成测试/实际CPU检查，排除内部模型数据、完整日志、路径和环境细节。计划单独新分支，diff须恰两文件，核上游仍缺修复后才发布，CI结果另核。

### 独立PR候选发布前验证

候选生产源码SHA `39949f44cf8c232d6297d4366577b62da686d43a5622ea01e150e25fefab940d`与env065保留源码逐字相同，只改两个host函数及runtime device导入，其他所有函数/kernel AST不变、原torch调用列表不增。测试SHA `a85bce9ac43fb7b6b2b65eefeec648256c7e6f5a5e9178a3872b09dba8f8aef2`，仅扩展原测试文件：原7路由＋12extent测试、原设备matrix补M0/M1，另4个compact空buffer参数case（int32/int64、E10/B16与E512/B64），各保存3次graph replay断言及count预先改为-1后写0校验。该4项是新增未执行的硬件测试，不报实测通过。

真实host函数/测试AST在隔离mock中19项全部通过，另530组geometry通过；不导入生产包、不初始化GPU。原测试函数体/oracle不变，仅扩展参数和新增测试。首轮pre-commit由Black规范化新测试一处skipif换行，exit1保留；第二轮仓库root完整7项hooks全部passed、exit0，未修改其他文件。原CI工具54项unittest通过，check_ci_pins及两文件语法/AST/diff-check通过。环境为本地独立Python3.12 venv，非目标设备或上游CI实测；无新数值/graph/model/perf结论。

发布计划：fork `ZenithJoyH/FlagGems-vllm`独立分支`fix/moe-thead-tle-empty-launch-20261022`，parent为上游main74171584，只有上述两个文件；提交公开正文不含内部环境/日志/题目，明确CPU/mock检查与硬件未运行。PR959源码head22194f0b和正文作为只读前后基准，禁止改动。无需新Issue或跨仓库依赖；新PR的维护者/CI后续结论不提前假定。

### MoE独立PR已提交

已创建正式[PR #982](https://github.com/flagos-ai/FlagGems-vllm/pull/982)，open/Ready for review，2026-10-22T08:26:03Z（北京时间16:26:03），head `d614a6ae44d8ec3a297136062b4848a4016dd5f5`，parent main74171584，tree `1b3824de447e77482e4b1c332db02b63bb1a0f16`。独立分支只有1commit/2file/163add/4delete；生产修复17行diff，其余为原测试文件扩展，不包含PLE/QSA/Plugin或其他仓库变更。

两个远端blob逐字回读等于本地最终检查文件（source blob b49b6bac、test blob559ce7fa），SHA256仍为上节39949f44与a85bce9a。PR959的head、完整body和draft=false前后完全相同，未追加评论或提交；当前PR已附加本任务。全程未连接目标Host/容器、不重启服务、不访问8035、不发模型/GPU/GPQA/性能请求。

创建时额外maintainer_can_modify=true权限被安全审查拒绝，未创建PR；先精确查重确认无PR，再按安全替代方案置false后唯一创建982，回读maintainer_can_modify=false。未授予维护者向用户fork分支直接推送的额外权限，无重复PR。

初始CI：rule-check与CLA已success；code style运行中（[basic ci run39747699008](https://github.com/flagos-ai/FlagGems-vllm/actions/runs/39747699008)）。当次GitHub MERGEABLE、UNSTABLE对应CI尚未结束，不是冲突或已验收；未声称上游CI/设备测试全通过，不擅自触发硬件CI或重试。正文明确仅19mock＋530geometry/本地7hooks＋54CI工具测试已执行，新compact graph/设备matrix未执行，无新formal gate或性能结论。`pr_readiness=ready_for_review`表示可交维护者评审，不是硬件/模型验收passed。

## MoE PR必要性与当前Plugin调用链只读复核

用户随后要求先验证PR修复必要性，并确认平头哥是否实际调用完整`flaggems_vllm.fused_experts_impl`。使用关键算子分析的source-to-kernel/命中证据分层与只读CPU条件对照，不修改或发布任何源码/PR、不重启/推理/GPU测试、不访问8035。连接预检首次在本机Ansible RPC启动失败，未到远端；按PPU-07限定提权重试后连接passed/changed0，未改变目标环境。

### 当前事实和对上一条回复的纠正

当前8010仍API1426766/start536664682/argv c146e2da…，进程白名单环境开关1、PYTHONPATH仅env065 bootstrap；Plugin HEAD a696859b加既有PR455及保留改动，FGVLLM HEAD b4d3382b加现有修复。只读核下列磁盘文件SHA均等于该实例启动时`source-before.json`冻结值，也与本地CPU分析快照逐字相等：

| 文件（Plugin根/opt/vllm-plugin-FL） | 关键位置 | SHA256 |
|---|---|---|
| vllm_fl/platform.py | 154–156：is_cuda仅vendor=nvidia且device_type=cuda为真 | dd7c89f16f38aba558a9e3db9eb29efe89f6ab06a1877f17759b6574797346a3 |
| vllm_fl/ops/fused_moe/fused_moe_utils.py | 398–410：完整fused_experts快路径要求current_platform.is_cuda；284/324/498为分步alignment | 0e1dfd8482b0d38afae7d88c9fd6ac725a30078979d56a0a567e836cb7fcadb7 |
| vllm_fl/dispatch/backends/flaggems/impl/fused_moe.py | 23–24/46：开关1导入并调用FGVLLM通用moe_align_block_size_triton | dde648e75e18183bf8995882a3c6c2bc53d6298a53ad0d813d8619b87fb950e7 |

**上一条将库内thead完整入口关系直接套到当前Plugin主路径，不充分，应纠正。** 库内`_thead/ops/fused_moe.py:1927`确实调用no_tle；但当前Plugin的完整API快路径是NVIDIA-only，PPU的is_cuda=false（is_cuda_alike=true不等价），即使无LoRA/SILU/无clamp全部满足也不会进入。当前走`TritonExpertsFL.apply → _prepare_expert_assignment → CachedOp alignment → moe_align_block_size_flaggems → flaggems_vllm.moe_align_block_size_triton → 4stage`，GEMM1/2分别调用库内invoke kernel，不是直接使用完整thead fused_experts_impl。小M naive assignment可跳过alignment，不能称每步都会执行四阶段。

既有8rank journal核vendor=thead/switch1、通用alignment和invoke函数对象来源FGVLLM ops、sum来源thead；该journal原本没有采集fused_experts_impl，不能伪称它直接提供了完整API对象证据。独立检查同实例冻结的`cpu-terminal-audit-001/compiled-origin-and-artifact-hashes.json`（SHA `267320374e7df5229f6f2938e6f3cd072fbd18e67f55b961d73c7c93ae897bcd`）：19份alignment stage1/2_vec/3/4模块全部有成功binary，14份generic ops/fused_moe.py的fused_moe_kernel、34份thead sum模块；未在该索引发现thead完整fused_moe.py来源。源条件、对象和成功编译产物相互支持，但不是新逐调用GPU trace或性能计时。已有service.log表明modular NoDPEP准备/thead flagos策略，未新增埋点读取在线对象。

### CPU必要性对照与结论边界

只在本地`/private/tmp/qwen38-moe-necessity-20261022.uQp0FG/cpu-path-check.py`提取已核SHA的真实host函数AST执行，脚本SHA `3178abbb1c1ac61415c651e67614b9bb9a648cbd8828b74ca11b0403fc52d3d5`；结果`cpu-result.json`保留。无生产包导入/设备初始化或远端写入。

- PlatformFL真实is_cuda函数以thead/cuda元数据求值false；完整fused_experts快路径在其余条件全真时仍为false。
- 当前assignment真实helper在E512/topk10、expert_map=None、普通BF16配置下，M0/1/12走naive绕过alignment，M13/64/128进入通用alignment；这只是所列参数下CPU路由复现，不外推EP/量化条件。
- 对原FGVLLM host与PR相同SHA39949f44候选，在thead/HAS_TLE=True/正常M64输入下CPU mock对照：原版先尝试TLE，模拟已知后端拒绝后才四阶段；修复版直接四阶段。此前op061对真实PPU编译器/旧IR已证实distributed_barrier拒绝，本次不重新GPU编译或声称测得重复开销。**平台门禁确实保护当前Plugin可能进入的通用入口，不因库内另有no_tle就多余。** 若将来单独授权切完整thead API，适用性须重新审计，不能现在改Plugin条件。
- 对直接空alignment/compact空buffer调用，原三extent=[0,0,0]，候选=[1,1,1]；M1/64/128/8065的正extent完全一致。共享launcher的零边界缺陷及已有原始arange失败机制支持保留max1。**当前普通配置M0会走naive，现有请求未证实触发空alignment，因此空输入部分应定位公共API边界健壮性，不能称它修复了本轮模型错答/停滞。**

决定：保留PR982两项的技术依据，但分别记录“当前分步路径的已知不支持TLE尝试防护”和“公共alignment零边界修复”。此次只读验证不改PR/容器/服务或精度/性能gate；没有新硬件A/B、完整调用trace或性能收益，GPU实际取消保护后的复现若需要须另行说明资源/风险并获授权。knowledge_delta=refined/contradicted：不能从库内vendor fused_experts实现或包级符号存在，推断Plugin在PPU命中完整API；必须先检查PlatformFL.is_cuda外层条件，再查CachedOp的实际库函数。
