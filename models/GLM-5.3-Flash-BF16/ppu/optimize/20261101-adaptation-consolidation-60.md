# 20261101-adaptation-consolidation-60 当前适配补丁梳理与收敛

状态：已完成并保留。下文包含冻结设计、执行进度与失败恢复原记录；最终验证、当前身份及结论见“最终结果与交付”。

## 方向与范围

用户要求梳理并收敛当前适配代码。仅操作PPU-13 / glm5.3-flash-opt-20260911 / 8011实际安装的三库，沿用现有专用优化容器及私有未挂载源码；不更新上游、修改vLLM/权重/tokenizer、增加新平台模型路径或提交推送。原MBT32768、TP16/BF16、maxseq64/maxlen80000/FULL_DECODE_ONLY/关闭prefix、RPC300与启动脚本不变。先实际差异审查，再收敛职责一致的重复部分，不为文件数删掉必要适配。

## 初始事实

Plugin main7094141、FG masterfe919c5、FGV main9f6a0ef；各1份editable，实际根为`/workspace/e2e-opt/glm53-20260911/upstream-20261030-p58/{plugin,flaggems,flaggems-vllm}`。当前差异18文件：11生产+7测试，Plugin4+3、FG1+1、FGV6+3。没有旧整套PPU模型分支。主要补丁包括公共Sparse MLA的H4/graph与缓存地址、物理索引转换、可选NVIDIA依赖隔离、ATen Autograd注册和SQL缓存缺表探测。已有临时MM排除不应在没有原300回归证据时删除。

当前实例3267540/start608188946健康且空闲；源适配容器不动。原单次163/198及用户授权补充172/198=86.8687%均保留，只证明点59之前源码，不伪造新源码精度gate或性能收益。

## 执行与回退准备

远端唯一目录`/mnt/nfs/users/jinghao/glm5.3-flash/optimize/e2e-opt-20260911/resume-20261101-point60-adaptation-consolidation`。变更前保存三库完整源码/Git/index、精确diff与小型审查材料，以及当前实例/源码/argv/env/权重/tokenizer/DB/thead/镜像挂载。命令`commands/prepare-v1.py` SHA `eac3e18a4ea07ed0d332f8aa54e830b06f10248c00c501bca8bf09370d964337`先暂存点59 commands/point60-prepare-v1.py，再执行创建新点60并校验复制；此步零生成、不改源码或服务。后续候选必须按文件SHA保护应用与反向回退，不动无关dirty/index。

## 设计约束与验证

遵循Plugin A1–A4/B1–B4/C1–C4/D2–D5/E1–E4/F1–F5/F7；算子A1–A4/B1–B3/C1–C7/D1–D2/E1–E4/F3–F4。优先复用公开接口，平台能力与模型语义边界保留；请求/slot/block纯metadata留框架，数值KV/Attention实现留算子库。没有新开关或诊断hook；可选依赖按当前vendor机制隔离，fallback只能在执行前选择。

先检查上游与现有改动、明确独立主题和可删除/保留清单，再选择最小候选。按影响面执行当前仓库CPU契约、导入/路由/失败路径与格式检查；需要时暂停精确优化服务，安装到当前实际源码，原脚本重启验证真实PPU、FULL capture与至少两次变化输入回放、C1/C8/三16K/11答案/C64。整理前结果不自动证明整理后代码，未执行项明确记录。设计阶段尚未实施候选；本轮不声明完整PR就绪。

11:51:28只读准备完成，三库完整源码/Git/index归档，当前镜像与挂载一致、源码私有未挂载再次核验通过。Plugin/FG/FGV archive SHA分别91b56ddf…/7482a6f8…/1d2acf45…；小型源码审查材料205099字节，SHA `f9943bf5f3b35458bcacf4e3cc6e48b94476f1763405b95e38a9bfa85f045ccd`。没有源码/服务变更或生成请求，全部暂存区diff为空、原工作区改动完整保留。

## 审查结论与候选

保留必要边界：公共Sparse MLA的H4 mask/thead64/128优化、FULL能力声明与UniformTypeKVCacheSpecs处理、KPool稳定地址、OOT构造一行修复、SQL缺表/单表反射、Autograd注册tuple修复及原MM排除均有独立既有故障证据，不为减少diff撤掉。

共审查三项候选（第三项后续决定不实施）：①现有FGV convert_sparse_indices不读写KV数值，只做request/page/slot纯metadata，按当前Plugin A3移入通用`vllm_fl/attention/sparse_mla_metadata.py`，删除FGV新API/导出与原测试文件；不能把它塞入职责不同的多模态patch utils来少一个文件。Triton kernel AST保持完全一致，设备guard改用已核验的torch.get_device_module统一入口；全套独立数值/边界/变化输入graph测试迁入Plugin现有test_mla，增加回放前输出哨兵。②删除MLA里忽略module参数的_flag_op薄转发，直接复用现有public capability getter，真实binding/vendor选择/执行失败不重试测试保留。③可选NVIDIA MNNVL导入改为原子返回tuple，一次发布五个符号，保留其他vendor不探测SDK与ImportError/OSError后的全空清理，减少重复初始化。

预计总差异18→16文件（11→10生产、7→6测试），无新增thead开头文件、平台模型分支或新环境开关。主要收益为正确的职责边界、减少跨库公开API耦合及重复导入状态，不作为性能优化收益。FG不再扩大改动。当前FGV workflow.md已读取，引用的optimization.md在审查材料未出现，需按实际仓库检查存在性；本轮不新写数值kernel/调参算法，不宣称其性能G6或PR就绪。

## 最终候选与执行前检查

MNNVL原子helper方案已在本地基线/候选18个vendor/导入成功/ImportError/OSError契约组合验证行为一致，但审查发现并未减少有效职责，增加helper也没有实质收益，因此**不实施该项**，保留现有NVIDIA限定与部分导入失败清理。不是为少几行取消必要的cleanup。

本轮实际只改6条文件路径：Plugin MLA删除无用_flag_op并直接公开capability lookup；纯整数映射迁入通用attention/sparse_mla_metadata.py；全部metadata独立数值/边界/graph测试迁入既有test_mla，回放前填充哨兵；FGV恢复原ops导出并删除本轮曾新增的metadata实现和测试文件。原kernel AST完全一致，H4、KPool、SQL、Autograd和临时MM排除不改。预期最终16文件=10生产+6测试。

本地固定Ruff0.14.0的3文件check/format通过，语法与kernel AST相等检查通过。格式工具仅安装本机/tmp，模型依赖未改；FGV的optimization/deep_opt在实际固定revision中均不存在，本轮不新写数值算法、不作其性能G6验收或PR就绪声明。

可重复候选包candidate-v1.tgz SHA `60fc0202ec422e9d27bed1625e7169838c0b3dbbd259dba9a6e7061d05ac1597`，六路径manifest SHA `d59ae5a78d46c3e039914688006cc3ee82aaf42efdcae032ea69d0773a5c8851`，patch SHA `0cb1dc1305a882138a54bd1d8f0e5a77a12ae6bd6ed8cbe75f4831eae15ff9c3`。含精确before/after原文，不依赖git reset。

执行前保存controller `commands/control-v1.py` SHA `eebb6d21106e7c30d918d511ced51a8b311ccbe74db5658c7fcda42865e85dae`；候选原脚本完整模型回归 `commands/model-v1.py` SHA `056cce96ea08d4cf54a2961a90200412e2f8b3e7cf4afcf29d057e3cdd0ce01d`；失败时精确原源码/原参数恢复回归 `commands/recovery-model-v1.py` SHA `66a62bc5cc5d9df9c8589f35d70d009194228fff4e702874b6a567993088772a`。

先zero-change prepare确认用户未接管、原实例空闲、输入SHA/归档/现有dirty/index均一致，再唯一dispatch。控制器只停止当前模型API及所属子进程，原子应用六路径，运行CPU GLM/dispatch/whitelist与单PPU完整145项metadata矩阵（独立oracle、strided/mixed dtype/空/无效页面/两次变化输入sentinel graph），通过后原脚本启动完整模型/FULL/C1/C8/三16K/11答案/C64。原启动参数/MBT/RPC300/生产DB URL策略不变，不跑新GPQA/性能。不将整理前172补充分数改绑新源码。任何失败保留证据，仅在源SHA与归属符合时反向恢复六路径，并重新启动原服务做完整回归；用户状态冲突则停止覆盖。

12:12:04控制器零变更prepare通过，SHA `63e3fcbb7843e4b3f1520db4d9e05a6994974ac9e9d95110053fee59d0e1da3e`。核验原实例/argv/log归属、原工作区与暂存内容、6路径before/after及回退包均一致，当前空闲且无用户接管；即将唯一dispatch，后续停止/源码修改/回归只由该精确控制器执行。


## 首次编排失败与传输修复

12:13:44已唯一派发v1（PID4119626/start622223390）。精确停止原API后，六路径大包作为`docker exec python -c`单参数超过OS ARG_MAX，于12:13:49在子进程创建前失败，**源码写入0、候选CPU/设备/模型请求0**；失败原文保留`failure.json`。12:13:51原源码与index逐项确认一致，控制器正在按预案原脚本恢复服务并做完整模型/FULL/C64回归，不重复启动或覆盖该恢复。

准备同候选的独立接续目录`transport-recovery-02`，仅修复编排：大包经`docker exec -i ... python -`标准输入传输，API导入证明使用显式JSON marker避免库INFO日志混入。数值kernel、六路径候选包、测试矩阵/阈值、启动参数均未改。控制器只有在原恢复完整通过、旧PID已退出、当前API身份匹配且空闲时才允许prepare/dispatch；不会重试已完成的候选模型请求，本轮此前尚未执行任何候选测试。

新命令提前保存：control-v2.py SHA `cac37e25bdd3aaaafd468a2287406254c539714f7590ee25fa330f2d6866f6b9`；model-v2.py SHA `4abf3edaaf6895c88e360da5077f18c68213d9009c8291483e86a41b3bd1e191`；recovery-model-v2.py SHA `9018dc58335a0de61213ec827e5c73e6d89f5839346d53923e3a917a6700920f`。本机隔离临时目录执行超131072字节真实六路径正向/反向应用，两向文件SHA全部通过，未接触模型环境；测试回执SHA `23a19d6b50c31da82bc6e5c0245b8f1f2954e75b8254734bd7dd02b4f14a70cc`。原失败保留，不能把工具测试说成模型通过。

新目录保存工具`commands/prepare-transport-v2.py` SHA `d21e949a09f062021ade712eb915ed56d5676c4eabbc6ee5955f93da5706337d`，输入包SHA `241814cb72df810f395a71c6ec2d15fdc244ab6c5542926cb81cb13f797b793a`；仅排他创建接续目录及命令/原冻结事实副本，不修改运行源码或服务。

候选完整通过后才运行的最终只读命令`transport-recovery-02/commands/final-review-v1.py` SHA `7c913d5283d14a3b7c61d908cf9813fe20e980226e8686d2cde8cfb16f1d76d8`：零生成复查安装路径/唯一editable、精确source/index/实例/原参数/health、镜像挂载、原生各阶段计数/FULL与16worker运行库，以及移动kernel实际AST相等；不改绑旧精度或宣称性能收益。


## 收敛后的职责清单（待原生验证）

| 组件 | 必要生产差异 | 保留理由 |
|---|---|---|
| Plugin：Sparse MLA适配器 | 公开capability/binding、H4形状与FULL能力、统一cache spec处理；纯整数索引映射归通用attention metadata | 调用与请求/页表组织由框架负责，不新增平台模型分叉；算子选择在执行前完成 |
| Plugin：GLM5 KPool/model | 稳定metadata buffer与OOT设备构造最小修复 | 变化输入graph必须读取当前值，避免旧地址与PPU构造错误 |
| Plugin：现有thead.yaml | 原mm/mm_out注册排除 | 解决已定位的请求内冷调参RPC问题，本轮不重新放开 |
| FG：注册入口 | Autograd fallthrough tuple处理 | 修复当前公共注册数据结构兼容，不引入模型/平台特化 |
| FGV：Sparse MLA公共/既有thead backend | H4合法mask与原64/128优化实现 | 数值Attention属于算子库，平台数值实现留既有backend |
| FGV：fused_allreduce_rms_norm | NVIDIA可选依赖隔离与部分导入失败清理 | PPU不能强制要求NVIDIA SDK，必要初始化/cleanup不能仅为少几行而删除 |
| FGV：SQL | 缺表与单表反射修复 | 防止缓存miss反射全库，保留原调参URL、策略与数据 |

预计Plugin5生产+3测试、FG1+1、FGV4+2，共10生产+6测试。所有跨平台契约仍受当前上游设计约束；真实硬件仅验证PPU，不宣称非PPU或多模态整模通过。没有把本轮纯职责整理解释为端到端性能收益。

当前安装三库全量Python调用点只读扫描确认：convert_sparse_indices只出现在现有Plugin MLA适配器/测试和本次新增FGV导出/实现/测试，没有遗漏其他库内调用方。公共get_flaggems_vllm_operator本就只负责可选库公开属性查找，无需新增注册层；本轮去除转发不改变能力或执行失败语义。

12:39:49原源码精确恢复回归完整通过：C1/C8、三16K、11/11答案、C64 64/64及FULL11/11与多token回放，原控制器已退出。12:40:57接续v2零变更prepare通过；当前恢复实例3887635/start622226686健康空闲，源码/index仍为原版、补丁包/原参数/RPC300不变。即将唯一派发v2，只运行此前尚未执行的候选CPU/设备/模型验证。

12:41:26接续v2已唯一派发，PID506497/start622389619，回执`transport-recovery-02/control-dispatched.json`。禁止重复启动原控制器或v2；后续源码应用、CPU/设备/模型测试及失败时的精确回退只由此控制器负责。

12:41:32实际六路径应用成功，差异已核验Plugin8/FG2/FGV6共16。12:42:46 CPU原生exit0，644 collected /179 deselected /465 selected且**465全部通过、0失败**，用时70.19秒，日志SHA `8c5235b25e0826ab4977d6b42c53d2cc886bda24792cd08855e2cb9f8432ce18`。控制器误把预估472当作通过数量下限而触发回退；不是CPU/源码正确性失败。原始通过日志、source-applied、failure与六路径精确反向回退均保留，GPU及候选模型尚未运行。

为仅恢复证据/编排并复用已完成原生CPU结果，保存`commands/pause-evidence-v1.py` SHA `b410b6782e9f07172ec01bd6b0e29c75fdf325b6a5e6a0f7227cbc8099e7c6ec`：仅在已确认原生全部通过、失败正是数量预估断言、恢复operations只有user_script_started且零请求时，按精确PID/start/argv/scriptSHA停止v2两个Host编排进程，再按精确日志/API归属停止其尚在启动的冗余原版恢复服务。源/index必须保持原版，PPU释放后才能重新应用同一补丁，接续**未运行的**设备及候选整模；如已发恢复模型请求或出现用户接管则拒绝中断。原恢复过程明确标为编排中断，不伪造恢复通过。不会更改任何测试、数值/精度阈值或丢弃慢轮。

暂停工具v1在发出任何信号前因expected argv遗漏末尾run而拒绝操作；已只读核验两PID/start/argv/SHA和零请求状态一致，保存v2 `commands/pause-evidence-v2.py` SHA `9931ec9fbc87bd0ccd245a5d6c6b71c64c2d19c2aa852c347ab465f3a9cbe0b3`，只修正argv完整匹配，不放宽进程归属条件。

证据接续唯一目录`evidence-recovery-03`：复用同源码/测试清单的原生465/465 CPU结果，SHA及644−179=465闭合核验；只运行此前未执行的145 GPU用例与候选模型完整回归。仍为原六路径补丁，未更改任何源/测试或数值/精度/性能门槛。执行前命令SHA：

- `control-v3.py`：`e5a359135312f9e692f1afa1b02a5ae6c27ed5608ef2d3d1a222b80e790fac8e`
- `model-v3.py`：`8263d306467ce8270eef5797b5ef9ce7348b5b24eb8e08ad37a14d34e7266adb`
- `recovery-model-v3.py`：`64f2a6681b681cf5764ed4c9794b2e0cdf75cbe8507127a2e4aceac3c8b32839`
- `final-review-v3.py`：`28005b2858c3b279eb57ac38df5da23ed6349499533c493271ce7455dc550b62`

保存工具`commands/prepare-evidence-v3.py` SHA `d950dfc3157f50e655a574ebb60b3671e855df9e743fa10bd5b8365de7ce831e`，输入包SHA `361bd719b0023ddc0d799786126d0bf2ab09cfcc626878039ff0553c765c3f42`。先校验pause已完成/前PID退出/目标无API/设备空闲/源码index为精确原版，zero-change prepare后才允许唯一dispatch。

12:47:40冗余恢复已按精确PID/argv/SHA与API日志归属停止，实际模型请求0，原源码/index完整、16卡空闲；回执`transport-recovery-02/evidence-recovery-pause-01/completion.json`。12:48:24 evidence03零变更prepare通过。即将唯一dispatch复用465 CPU通过结果并执行第一次设备/候选模型验证；旧两次编排失败原文及旧完整恢复通过证据分别保留。

12:49:07 evidence03已唯一派发PID670281/start622435684，`evidence-recovery-03/control-dispatched.json`。只此控制器继续源应用和未完成验证；禁止再运行旧v1/v2控制器或旧恢复模型任务。

12:49:50设备原生exit0，246 collected /101 deselected /145 selected且**145全部通过**，38.09秒，日志SHA `b7c933027845bf7d03154c35630308a2b7248e188cc1319cbd686f1ec854676c`。145=108基础row/width/dtype/stride组合+32混合dtype/page size+空页面1+3种width graph+不支持契约1；3种width各两次变化输入且输出先填充sentinel，共6次回放，独立CPU整数oracle逐位比较、输入不被修改。

12:50:02 validation-completion确认CPU465（原生结果同源码复用）与PPU145通过；真实新进程导入为Plugin通用metadata，FGV旧导出与旧实现模块不存在。源码SHA：Plugin `478ec9fa45c35b21d078cdfdc5aae90953f6543c8135188e9ba699021ba7bbf9`、FG仍`121f177f076e7b8d531cd1c2ec6269bbcdb196d386dc8c46191efadc3073ccfc`、FGV `d6cbf04fa6c4b1f4871c0641d61f7926d0c7d907542f0549eb363a42cd170bb9`。差异16（10生产+6测试）已经实际核验，暂存区语义不变。

12:50:27原start-model-opt.sh已首次启动此候选整模回归；无启动环境override，MBT32768/RPC300/FULL_DECODE_ONLY与原参数不变。此时整模/FULL/C64尚未完成，不将局部CPU/设备通过冒充模型精度或性能通过。

最终只读审计命令细化为`evidence-recovery-03/commands/final-review-v4.py` SHA `d0122a3356dbf46adab1e39ba915cadc0f52a2d31c0421d8db7e2d211c51e2a4`，在原生整模通过后执行。除前述文件/index/安装和kernel AST外，再把当前manifest中的权重/tokenizer/引擎/三库/原启动配置与本次原生after逐项比较；当前manifest与原生manifest均保留，runtime证据SHA和正常DB写入不伪造一致，不签发新精度gate。v1/v3最终审计尚未执行，使用此最终版本一次。

13:13:20候选C64 64/64通过，13:13:45整模完整回归通过，13:13:46控制器completion通过；实例3917036/start622443729，全部原参数/RPC300，未见OOM/非法访问/RPC错误。

最终v4零生成审计已通过源/index/实例/权重/tokenizer/启动配置/唯一editable/镜像挂载、kernel AST及各阶段计数检查，但额外新增的“任何worker maps不得出现tilelang路径”断言失败。只读对照证实**原版完整恢复与候选各16worker加载的库集合完全相同**，都包括PPU SDK libcudart、TileLang的CUDA stub/libtilelang/libtvm/cython wrapper；不能把库加载直接等同执行TileLang kernel，也不能宣称运行库未加载。本轮没有增加TileLang代码或更改依赖，当前MLA路由日志为glm5.flaggems；现有H4/thead数值代码为Triton/Triton TLE（TLE并非TileLang），本轮不作全推理栈“没有执行任何TileLang kernel”的新认证。原生完整模型passed不改写，v4该观察失败保留。

仅修正这条不属于原生最小回归通过条件的过严观测解释，保存最终只读v5 `commands/final-review-v5.py` SHA `24dca0d0039bce3f3cceee814e85a0683c35d79344dd015479c390d853d6a9bd`。继续复用本次模型/设备原生证据，按前后各16worker库集合相等、16rank真实选中FGV MLA以及当前身份复验写观察，不重跑模型、不改源/参数/阈值、不隐藏已加载库或伪造no-TileLang声明。


## 最终结果与交付

2026-11-01T13:18:17.884001+08:00当前只读审计完成，回执`evidence-recovery-03/final-review-v5.json` SHA `1537aced93f9d3b7c3ef29863451e6312260c5b00af6e9cef77d1d84e5698979`。当前实例`PPU-13:glm5.3-flash-opt-20260911:3917036:622443729` health200/运行0/等待0；源/index/安装/启动配置/权重/tokenizer/镜像挂载再次核验通过，实际改动已保留在唯一安装的私有三库中。没有Git提交或推送。

| 范围 | 最终结果 |
|---|---|
| 实际差异 | 18→16文件，11→10生产、7→6测试；Plugin8（5+3）、FG2（1+1）、FGV6（4+2） |
| CPU契约 | 原生465/465全部通过；纠正包装器数量预估后按同源码/SHA复用原结果，无重跑 |
| PPU metadata | 原生145/145，独立整数oracle、strided/mixed dtype/page边界、输入不变；3种width各2次sentinel回放 |
| 完整模型最小回归 | P4096/D16 C1/C8、P1024/D64 C1/C8、P16383/16384/16385 D8、11/11明确答案、P4096/D16 C64 64/64全过 |
| Graph | FULL11/11 capture及完成多token请求的重复decode覆盖；不是新的逐rank device profile |
| 参数与服务 | 原start-model-opt.sh SHA `8fdae3f4f200be2e46d9c8a3120380181961844c5125b1e9bda771847fa22bdb`，TP16/BF16/MBT32768/maxseq64/maxlen80000/FULL_DECODE_ONLY/prefix disabled/RPC300均不变 |
| 必要边界 | H4/原thead64/128数值实现、KPool稳定地址、FULL/cache spec、OOT一行构造、SQL、Autograd和原MM排除保留；无旧PPU模型路径或新平台开关 |
| 证据边界 | 没有新198题GPQA、性能/ABR/正式四场景或非PPU/多模态硬件验收；原172补充分数不改绑新源码 |

生产DB仍为`sqlite:////opt/glm53-flash/flaggems/TunedConfig_thead_triton_3_6.db?timeout=1800`，当前主文件SHA `1cb5d4bb34b6a48b958e7c5f67b43fb8b08736cd9f2a078ce0974f254f769fc2`（与本轮开始相同），未清/复制/回退或改调参策略。实际库导入路径为既有`/workspace/e2e-opt/glm53-20260911/upstream-20261030-p58/{plugin,flaggems,flaggems-vllm}`，每库1个editable。

主要原生证据（均位于本点`evidence-recovery-03`）：

- `completion.json`：SHA `ebda5d90bc4f1dbdcd40f90b4672adf549ba6d6fea051960db5b26ec2222f0aa`
- `validation-completion.json`：SHA `dc3a39e5bbf8fa3a59ef88a00ccca9dbc89e33a1a8077aed48d308edaedb7178`
- `model01/model-completion.json`：SHA `bef5bc5b278b704a953c8e8be40f92d6441a08a4a8619971ddc00c430e45b8e4`
- `model01/production/graph-regression.json`：SHA `585979d9fc748f932394124294174e6c00a831e983be0c8e6d550fcbd7d071fb`
- `model01/production/worker-runtime-maps.json`：SHA `466d8d5955d70cc9f84e042764648b0a505f64847701a400c50a31b5277dfee9`
- `model01/service-consolidation-final-readonly-v5.json`：SHA `59cb7346c53a3967d1ca9b07865f6b088f558ebeddc8a93e66dd28dd4b373bf7`
- `model01/runtime-consolidation-final-readonly-v5.json`：SHA `bee87968a6b1aa558e78b2abe218ad1ad98bd73bcd8d126f175158f7f40440a7`

TileLang加载观察按前节如实保留：原版/候选16worker库集合相同，16rank选中FGV MLA；不能以此签发全推理栈无TileLang执行证明。v4额外库缺席断言失败没有改成通过，也没有修改任何原生测试或数值阈值；v5仅修正审计语义并复用已有模型证据。

同步修正state.yml中早期遗留的当前service/accuracy/current_target/active_experiment/next_candidate视图，旧段原文保存为*_historical_pre_point60，不把历史gate留作当前有效。原始失败、完整原版恢复、请求前编排中断、CPU证据接续和最终通过均在同点外部目录保留；没有新增history目录。

本地写回验证：state.yml重复键/当前身份与精度作用域检查、点60索引链接及diff whitespace检查通过，GLM案例记录错误0。全仓另有375个既有记录问题未在本任务修改，不能据此宣称全仓records通过。


## 用户追加：收敛后单次全量198题/C64精度

2026-11-01用户明确授权保持原启动脚本/MBT/启动参数，运行一次64并发全量GPQA，以strict>=0.86判定。当前同实例3917036/start622443729、三库内容SHA与收敛结果一致，health200空闲；复用已通过的此实例完整模型/FULL/C64最小回归，不重启服务或重复smoke。正式范围198唯一doc0..197、C64、seed42、temperature1/top_p0.95/maxgen60000、独立UUID缓存、API及评测重试0，无补充/择优/跑到过线。输出健康单独记录，不另设零超时门槛。

唯一正式子目录`formal-gpqa-01`。命令提前保存`commands/formal-gpqa-v1.py` SHA `322f2f37b78441b1c5a6b927a0935c83dec0d39c5af00c4be66c9eb9e421f15a`、`commands/prepare-formal-v1.py` SHA `f7782bcbd8ae2be219c113dd264e0b82ceb0e3cd2fa143e56fa8dd6ae3086689`；维护版工具包`commands/accuracy-tools-formal-v1.tgz` SHA `9428e7de76f2cab857000e7918fb4d97ec4398015e308bdc163f5a5dc1ac4945`。原始runner SHA82cf6e83、Skill bundle1ed06a57（formal-gate）已核验。先原规定flageval镜像内采集两次task/data provenance并冻结契约，再GET模型预检，以上零生成；核对prepared后唯一派发原生评测。

客户端每请求timeout14400秒，整轮控制器等待原生进程结束，不沿用曾使包装器提前退出的4小时整轮timeout；规划预算86400秒，非擅自修改服务器RPC300。源/参数/服务身份漂移即保留证据停止晋级；低分不自动补跑。正常DB写入只在已有明确授权下按原生schema3→显式同实例schema5审计绑定，原manifest和精确DB指纹均保留，不改变分数/阈值。正式结果原生198题/各filter与task/data provenance全部核验后再报告。

本轮后台跟进已创建：automation `glm-gpqa-c64`，每30分钟检查，状态未变安静，仅实质进度/终态/需用户操作通知，正式终态及最后只读审计完成后删除。监控明确不得派发或重发请求，即使尚无dispatched也不能自行启动；准备/唯一派发由主聊天负责。

14:27:49零生成准备通过：两次provenance完全一致（SHA `6e601ca05f6c88ace46aa405800660465873082b49a6ceed240b85323c862dde`），dataset revision `content-sha256:167548b01bcfd7d38d0eb80bb01bd1e6dded4d3aa14b41a4bdba0beb5423dadc`，198题/strict0.86契约冻结；GET服务预检通过。freeze SHA `fe570c46bc45f2b632557fd6698c216d7acd82e68e7758354d9b93601390e144`。模型实例/源码/原参数不变，即将唯一dispatch；之后只由此控制器执行一次原生评测。

14:30:03正式控制器已唯一派发，PID2724242/start623041337（`formal-gpqa-01/dispatched.json`），同一模型实例3917036/start622443729；命令SHA322f2f37。此后禁止再次dispatch或运行prepare/run，监控只读检查原生进度与证据。

14:30:28原生wrapper已唯一派发，14:30:43出现Requesting API(concurrent)0/198；14:32:07只读确认服务health200，**64个请求实际运行/等待0**，无Traceback。effective_config真实run_id `7fd4c42b937546059b14657b6e0e309a`，C64/limit0/expected198/seed42/temp1/top_p0.95/60000/API0与eval0重试均与冻结一致。模型服务未重启、未改源/启动脚本/MBT/参数。此时尚无完整分数或gate，不能以旧172补充分数或0/198进度判定本轮。`glm-gpqa-c64`监控持续只读，终态后按当前源与198题原生证据报告达标或失败。


## 正式终态与精度事件（2026-11-01）

20:02:07原控制器终态：原生单次198题/C64 strict **164/198=0.8282828282828283（82.83%）<0.86**，formal.exit=1；396行/198唯一题/两个filter及task/data provenance已由原生独立汇总核验，未产生run-record或精度gate。输出健康20个timeout标记、空输出0/乱码0/截断0，仅作健康观察；失败依据为分数低于冻结门槛，不另设零超时条件。原始结果与失败原样保留，不自动补跑/择优或开启性能实验。

按`skills/inference-accuracy-diagnosis/SKILL.md`冻结事件`point60-formal198-C64-below086`：可信原生分数未达门槛，根因尚未确认；尚无同输入/同条件的旧新版语义差异或数值分歧证据，不能归因metadata迁移。点59原生163/198同样低于门槛，其172补充口径不可充当本源单轮gate。下一步只读完成身份/证据核验并保留所需复现方向；本轮不发新模型请求。

最终零生成审计命令先保存`commands/formal-final-audit-v1.py`，SHA `235c0a26285dbc21c5fbb689b3700a8f1e9a5512a32d943325e8e9029f06e6cb`：复核当前三库/index/唯一安装/引擎/原argv和环境/权重/tokenizer/thead/DB/镜像挂载与正式开始/结束身份；复用原生198题数据验证全部filter和provenance，仅写新审计回执，不改原采样/配置/阈值/manifest，不重跑模型或改库。执行后再补最终SHA并删除本轮heartbeat。


20:04:51最终只读审计通过，`formal-gpqa-01/final-readonly-audit-v1.json` SHA `3eca89327eabc95faf586ef57690f9122f2a5888e41605ebdfb50dcc17d7bab1`。再次独立复算原生strict164/198、核验396行/198唯一题、全部filter/原prompt-target-arguments与冻结task/data provenance、冻结文件SHA；没有发出任何生成请求。当前同实例3917036/start622443729仍health200且空闲，源码/index/唯一editable/原脚本与argv/env/权重/tokenizer/thead/镜像挂载/DB均与正式开始和结束身份相同。FULL原生capture与重复多token覆盖证据复验，无新profiler或新graph模型请求。

- 原生完整结果：`formal-gpqa-01/results/GLM-5.3-Flash-point60-consolidated-C64/7fd4c42b937546059b14657b6e0e309a/gpqa_diamond_generative_cot/glm5.3-flash-opt1/results_2026-11-01T12-01-58.144505.json`，SHA `614a2f989082ff7847d84b52ee44478f2a7f69762fbd07b9fc759a78d01db1e3`。
- 原生samples同目录`samples_gpqa_diamond_generative_cot_2026-11-01T12-01-58.144505.jsonl`，SHA `fc896c5ff6576bf978552b3540ea3cc5d9b2393fbbc155bf94ebf68a4452f902`，未修改题目/答案/采样。
- `formal-gpqa-01/native-score-summary.json` SHA `70e49ed44126840cbaff0d1807a3fa5f4f5457467e4cbd42660d470f0ed2d4a4`，`completion.json` SHA `d96500d08d79bfcfa4ed9b8bbb6fda59fb283173a3c59e60cd29d47832125d21`；没有签发gate。
- 当前manifest `evidence-recovery-03/model01/service-formal-final-readonly-v1.json` SHA `ccdbe7751be0fb24231219a54b6c77cc6d30fb25fdf4fe8c99818f71a8dde9ca`，runtime SHA `486423eee99c7d8d30605953c38526acdffcce2ff69d991594d9c7c4b8354845`。
- DB开始/结束/最终审计主文件均`1cb5d4bb34b6a48b958e7c5f67b43fb8b08736cd9f2a078ce0974f254f769fc2`，本次不存在缓存SHA绑定漂移，也未触发schema5补绑定。

结论：本轮用户要求的单次全量C64已经完整执行，**精度未达86%**（至少需171/198，当前差7题）。不把20个timeout标记另作门槛，也不据此确认根因；目前尚无同条件旧新版数值或语义二分证据。只保留已冻结失败和当前原参数健康服务，不自动回退用户源码、不补跑、不叠加性能优化。可供下一次诊断的首个步骤为只读划分错误与timeout的交集并检查原始请求终态；若需最小复现/修复则沿同一事件继续记录。后台`glm-gpqa-c64`已在正式终态及最终审计后删除，无重复评测或自动后续实验。


## 用户授权：20题超时标记诊断与必要补跑

用户原话：“你看看这20道题目是什么情况吧，如果有必要的话可以单独重跑下”。按精度定位Skill以及精度评测`minimal-regression`执行，不修改模型源码/启动脚本/MBT/任何推理参数或RPC300。只读核验发现20题并非全部60K截断：

- 19题没有usage/正文，原生`lm_eval.log`恰好有19次async API timeout异常；客户端每请求14400秒，在获得并发信号量后才开始计时，非排队等待超时。async异常经None转为`<TIMEOUT>`，后续统一写timeout=true。未保留这些请求的输出，不能判断其是否也生成到了60K。
- doc_id=190有正常API响应，usage prompt376/completion60000，finish_reason=length；message.content=None，reasoning长度228302字符。`LocalChatCompletion.parse_generations`仅提取content，调用端将None映射为同一`<TIMEOUT>`。这是达到长度上限且无最终正文，被工具标记为timeout；不是该题HTTP超时。原始评分不改写，不将reasoning当最终答案重新评分。
- 原模型服务日志无Traceback/OOM/非法访问/sample_tokens/RPC/ERROR。原生19次错误发生于18:30:44至19:39:32（日志原UTC10:30:44至11:39:32），全轮结果20:01:58写出。失败机制已证实，模型为何长时间无最终返回、是否存在数值退化仍未确认。

冻结全部20题doc_id=[8,12,15,32,47,48,64,69,71,75,76,79,81,88,90,93,94,127,130,190]。这20题原strict全部0，其余178题有164正确；排除异常后的164/178=92.13%仅作诊断子集数字，不能替代全量准确率。

有必要统一补跑一次观察减小在途请求数后是否完成及长度结束是否复现。唯一新子目录`rerun20-01`，命令提前保存`commands/rerun20-v1.py` SHA `92ae339424c0941916d979b73a2bce51fd5aafd34a70d8b19a6874e845fdd570`，使用原生lm_eval --doc_ids及SHA核验原始runner/冻结Skill bundle。保持C64上限（只有20题，实际最多20并发）、seed42/temp1/top_p.95/maxgen60000/API timeout14400/API与eval重试0/独立UUID缓存，整轮无4小时强制外层终止，不重跑到过线。先零生成prepare核验当前身份/空闲/评测容器无其他lm_eval/同task-data provenance及原prompt-target-arguments；再由主聊天唯一派发。原服务、生产DB及评测器不改。

原生结果完成后统一替换全部20题，其他178题保持原样，补充口径为(164+补跑正确数)/198；无best-of，不混作新的单次全量C64 gate。原始164/198与20题补跑及补充结果各自保留，监控仅只读跟进，禁止重复派发。背景监控在prepare通过后创建、派发前保存，终态当前审计后删除。

20题零生成prepare已通过：全源/实例/原参数/DB和178题保留范围核验，task-data provenance与原全量相同，独立run_id `e3a73d62fb074e0586f8378499699f7b`；没有发送模型请求。后台监控`glm-20`已创建，每30分钟只读跟进、未变安静、终态审计后删除。即将由主聊天唯一dispatch，监控禁止派发。

20:26:28补跑控制器已唯一派发PID1463708/start625179793（`rerun20-01/dispatched.json` SHA `d687e1ddc2d9a5d4a69261fcd4fa9cedf6999db4c58832223cca96468303e270`）；20:26:54 host-start确认精确原身份和无模型/源码/参数变更。prepared SHA `9ab8fc922a3c10cdd554faba034a890b8f0792a86364d866a78552f1cdd492b2`，request-contract SHA `96ab3a4e3e65f2fb794ef3b98af12223b7b6e0f774ca2f086e19fc73287f728d`，诊断回执`diagnosis-before.json` SHA `8ed2d214a5c478fb5075994ed8e49aecf808ae17b70163e5674ddad84758975a`。后续只读观察，禁止重复dispatch/run/inside。

20:27:02原生lm_eval已实际启动（评测容器PID64215/start625183219，20:27时间按UTC原回执+8小时展示），日志Requesting API0/20；只读确认**20请求实际运行/等待0**，无Traceback，模型实例及源/原参数未变。后台`glm-20`继续跟进。此时无补跑分数，不提前判断达标。


23:34:18（2026-11-01）全部20题原生生成结束，exit0；23:34:24控制器completion有效。补跑strict10/20，统一替换后174/198=0.8787878787878788>=0.86，原164/198完整保留。没有生成新完整gate。新轮没有HTTP客户端超时；7个标记doc_id=[8,15,71,79,81,88,130]的原始HTTP响应均finish_reason=length、completion60000、content=None且有reasoning，被同一评测器映射TIMEOUT。其余13题有最终正文（10对3错），doc190本次6,888 token正常给出正文并答对。未将reasoning提取当最终答案。

本轮DB主文件从`1cb5d4bb34b6a48b958e7c5f67b43fb8b08736cd9f2a078ce0974f254f769fc2`变化到`eda5cc0b64ac0201733c1a11f82b87f4b2898852a9fd8098c9b73a321b5de4f7`，控制器确认同实例/源/argv/env/DB URL和策略不变。精确指纹与前后manifest原样保存，没有归一化、清库或改旧manifest；本轮未签发gate，不为此制造绑定回执。

最终只读核验命令执行前保存`commands/rerun20-final-audit-v1.py` SHA `8dc2da901fe75d2320fdb7121f26a0ec41879db509d22a47f359e7375a1b08a0`。仅复核当前身份/源/index/唯一安装/镜像挂载/原argv环境/权重/tokenizer/thead/DB/已有FULL证据和原始20题各filter/provenance、178题逐行未变及统一合并，不调用模型、不开新试验；按原方法在评测容器复验task-data provenance。7个长度结束的原始HTTP元数据与HTTP timeout0单独保存，最终审核完成后清理监控。


## 20题补跑最终核验与结论（2026-11-02 00:03）

最终零生成审计已通过：`rerun20-01/final-readonly-audit-v1.json` SHA `10e31b11066e6bdfdb5630627ca3ee60be3fdaccf950fe4b299b8f684a044473`。独立核验20唯一题/两个filter共40行、原doc/prompt/target/arguments与冻结task-data provenance；在规定评测容器再次只读计算provenance与原冻结完全一致。合并396行/198唯一题，所有20题统一替换、其余178题逐行保持原样，无best-of或自动重试。当前实例3917036/start622443729仍health200空闲，源/index/唯一editable/原argv环境/权重/tokenizer/thead/镜像挂载及已有FULL capture/重复多token覆盖证据均通过，原脚本/MBT32768/RPC300未变。审核未调用模型，未重做最小回归或capture。

| 口径 | 正确数 | strict分数 | 86%判定 |
|---|---:|---:|---|
| 原始单次全量C64 | 164/198 | 0.8282828282828283 | 未达标，原始结果保留 |
| 本次20题一次补跑（C64上限、实际最多20在途） | 10/20 | 0.5 | 诊断子集，不单独作全量gate |
| 全部20题统一替换，其余178题不变 | 174/198 | **0.8787878787878788（87.88%）** | **用户授权补充口径达标** |

本轮20个HTTP请求均正常结束，**没有客户端HTTP超时**。13题得到最终正文，其中10题正确、3题错误；另外7题为HTTP成功但生成到60K时无最终正文，仍被原评测器标为TIMEOUT。JSONL没有传播原始finish_reason，样本检查的truncations字段仍为0；原始HTTP元数据的7次length结束另行保留，不把0解释为没有长度结束。

| 结果分类 | doc_id |
|---|---|
| 正确10题 | 12、32、47、48、64、90、93、94、127、190 |
| 有最终正文但错误3题 | 69、75、76 |
| 60K结束且无最终正文7题 | 8、15、71、79、81、88、130 |

doc190原轮正常HTTP/60K无正文，本轮6,888 token正常正文并答对。7题原始响应均finish_reason=length、content=None、reasoning存在，记录了request_id/usage/推理字符长度，没有输出题面或答案。说明TIMEOUT标签混合“请求超时”和“无可提取最终正文”两种路径；该映射机制已确认。原19题在本轮不再HTTP超时，是实际20在途子集的观察，不能证明C64原长请求稳定性或数值根因已经修复。采样和批次组织可能影响生成，未进行单变量二分，不给代码回归或修复有效性下结论。

原生与合并证据均位于`rerun20-01`：

- 原生results：`results/GLM-5.3-Flash-point60-consolidated-C64-rerun20-01/e3a73d62fb074e0586f8378499699f7b/gpqa_diamond_generative_cot/glm5.3-flash-opt1/results_2026-11-01T15-34-18.419065.json`，SHA `a8503fcbb13064f3406e2b717bc78f89247dac030070c8f7e03f2eadc3fb6bb3`。
- 原生samples同目录`samples_gpqa_diamond_generative_cot_2026-11-01T15-34-18.419065.jsonl`，SHA `542dbdab4be3c252e62facba8299a064c12bebd414899a0d5087b3d4d83d814b`。
- `merged-samples.jsonl` SHA `b4dc2f0b7abd95dbb0e5358e8360e8f71ad110bd000e810742c8a1af3a9b732d`。
- `score-summary.json` SHA `08efaa4a7bb360ab9275342c7dce1981939455381fe0ac9c4830c9104ef0a58d`，`completion.json` SHA `d5d08f4e2419f4d49cc44b405a1766878a5b4744f73682a3d3e7ee6bad5d4389`。
- 当前manifest为点60`evidence-recovery-03/model01/service-rerun20-final-readonly-v1.json`，SHA `6fb7e4884f7e1955e6fe6c2af02f601e0e0b479ab4569cd7a976a74d366a5d3e`；runtime SHA `1363a008072dde2c94eb725964e5519f3b6de9523fab53e33a04845c775e37b7`。

当前DB SHA仍等于补跑结束的`eda5cc0b64ac0201733c1a11f82b87f4b2898852a9fd8098c9b73a321b5de4f7`；同实例和所有稳定身份/URL/策略未变，准确保留开始与结束DB字节指纹。没有完整旧DB逐行差分证书，不据此制造新gate或声称性能可比；本轮无需改变计分或服务启动方式。

结论：按本次用户授权的统一补充口径，当前精度**174/198，87.88%≥86%**；原单次C64 164/198保留、没有伪造新完整C64 gate或改原分数。7题输出健康问题不另加精度门槛。请求占位符机制已定位，C64长请求性能/数值根因仍未闭环。本轮诊断与一次补跑完成，保持原服务，不自动追加请求/性能实验或源码修改；监控`glm-20`已在最终审计后删除。记录写回state、总览、平台和案例，未建立history目录。
