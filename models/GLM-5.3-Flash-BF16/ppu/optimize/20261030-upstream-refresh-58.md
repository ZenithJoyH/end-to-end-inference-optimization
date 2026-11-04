# 三库更新与当前生产脚本精度验证（点58）

用户于2026-10-30要求更新优化容器中的 Plugin、FlagGems 和 FlagGems-vllm，再使用自己的启动脚本启动模型并测试精度。本轮仅限 PPU-13 / `glm5.3-flash-opt-20260911` / 8011；不修改 vLLM、模型权重、tokenizer 或用户脚本，不执行性能测量、不提交推送。

## 更新计划与回退

官方远端默认分支冻结为 Plugin `main@7094141e28a2680644fc41073aa9dfdfbf1f0044`、FlagGems `master@fe919c559c2a701dbf715d8521ee4a6d57130d3c`、FlagGems-vllm `main@9f6a0ef7816883ee2ac84379b2b18abb070517d4`。三库现有工作区均无跟踪分支，含未提交改动，不能直接 pull/reset。先完整归档原目录及 Git/index，核验归档，再在容器私有新源码目录准备这三个固定官方版本；原源码保留用于回退，不把历史适配差异盲目覆盖到新版本。安装时核验仅一个有效安装与实际导入路径。

远端任务根：`/mnt/nfs/users/jinghao/glm5.3-flash/optimize/e2e-opt-20260911/resume-20261030-point58-upstream-refresh`。新变更命令保存到该根的 `commands/` 并记录 SHA 后执行。源容器不变。本轮当前预检：源/优化容器镜像均 `29a6712e24ca8e758ac8b33d3412892f0541bff108e2c057445fa671578237f6`；唯一目录映射均 `/mnt:/mnt:rw:rprivate`，挂载一致；16卡空闲，未发现当前目标服务。启动前仍复核端口及设备。

用户脚本 `/mnt/nfs/users/jinghao/glm5.3-flash/start-model-opt.sh` SHA `8fdae3f4f200be2e46d9c8a3120380181961844c5125b1e9bda771847fa22bdb`，served name 为 `glm5.3-flash-opt1`。脚本先设置 Sparse MLA vendor 环境变量后又 unset，最终路由按默认选择；不替用户修改。原 TP16/BF16/MBT32768/maxseq64/maxlen80000/FULL_DECODE_ONLY/关闭前缀缓存保留。脚本的相对 `service.log` 通过新任务工作目录隔离。

## 验证契约

使用本项目 inference-accuracy-evaluation 的 minimal-regression 与 formal-gate：先当前新身份的 C1/C8、16K边界、明确答案、C64、FULL capture 与至少两次运行回放；通过后正式198题 GPQA Diamond，C64、seed42、temperature1、top_p0.95、maxgen60000、strict >=0.86、独立UUID缓存、eval_max_retries0，无补充替换或 best-of。历史173/198不绑定新版本。正常调参 DB 写入保留开始/结束证据，不改旧 manifest 或清库。

当前状态：官方三库已更新为固定版本并完成必要兼容及CPU/设备验证，实际各1份editable安装。临时RPC1200的P4096/C1/C8/C64通过后已停止；恢复原300的完整回归在P1024/D64/C8于20:24:13再次RPC超时，已精确清理、正式GPQA零请求/无新分数。长请求栈观察到FG MM在线候选编译，未将含debugger暂停的快照当无干扰因果证明；问题接[点59](20261030-native-mm-registration-repair-59.md)，仅现有thead.yaml原生MM注册排除先作独立验证，再新身份整模/精度，不重跑临时1200或复用历史分数。以下保留完整失败与修复证据。

归档/拉取命令：`commands/prepare-v1.py`，SHA `052fbe50e81755fab3423c09e24f734a76f48d9bae97db4557d57cab5357866f`。先在已核验的父目录中新建唯一任务根和 commands，独占写入命令，再在目标优化容器中执行。命令仅归档三库及 Git/index、拉取冻结默认分支并读取上游差异，不修改源码/index、安装或启动服务；任一远端SHA与冻结值不符即停止。

v1在 Plugin 归档后 fetch 因 `pack has 2 unresolved deltas` / `invalid index-pack output` 失败，非源码或模型失败，零安装/请求。改用保存后的 `commands/prepare-v2.py`（SHA `a6c6ea52b5120f884c1c690877854adfafb21439e9b68a5899948eeefd33e407`）：校验并复用原 Plugin 归档，继续归档另外两库，在容器私有 `/workspace/e2e-opt/glm53-20260911/upstream-20261030-p58/` 用独立 shallow clone 拉取三个冻结官方版本，避开原仓库对象库问题，不修写原 Git 对象或覆盖工作区。

v2已通过，三库固定SHA及干净工作树已核验。原完整归档 SHA：Plugin `2356330906b3c6da990c0dc63a7be77f9b5915f6f003cc3a3945b68005e8ab51`，FG `ae6819e9306e0a223dfd5ddd23cee02c3d136311b3adac77a5a997bfc250c528`，FGV `5a93f2bdb6a888f4b0d98a18aca8ea461b888c5fff69afe634dae73e147e2ec4`。官方 Plugin 最新提交就是合入 PR454，公共GLM模块/测试已存在。

安装命令 `commands/install-v1.py`，SHA `0605ff7470c0b4abac40253befda4b59cf9b8fcff9e0c5e4d5fd09f6b49d6ca5`。三库均 editable/no-deps；FG使用其声明的隔离构建依赖（避免容器内 setuptools-scm10 与FG声明<10冲突），不升级 torch/vLLM/运行依赖。安装后检查唯一metadata/真实导入、新源码import与GLM CPU测试；失败停在模型启动前。

## 可选通信依赖兼容性诊断

三库已安装，唯一metadata/实际import与原torch/vLLM等依赖版本检查通过。首次GLM CPU套件397 passed/30 failed/4 skipped，失败栈指向 FGV `fused_allreduce_rms_norm.py` 包级导入 FlashInfer MNNVL，后者误选已加载的 TileLang CUDA stub，缺少 `cudaDeviceReset`。调用精度定位Skill，分类为可选依赖导入兼容性，尚无模型精度成绩/模型请求。直接先加载Torch、再加载stub、再公开import FGV可复现；先于Torch加载stub会被其自身终止，该次诊断不作为相同根因证据。

必要兼容修复命令 `commands/optional-fix-v1.py` SHA `024a44aff1d0d42c4ddaebad07743bf61012c005ace1d73915bef1afa571f262`：仅在FGV已有runtime选择NVIDIA时探测NVIDIA专属MNNVL，其他平台保持该能力不可用。不修改FlashInfer/TileLang第三方包，不改数值kernel、计算路由或推理参数。保存原文件与补丁SHA后写入，再跑同一导入复现、阻断FlashInfer通信的PPU公开import检查以及原完整GLM套件；不跳过失败测试。工程适用条款为算子规范B3/D1/D5/E5；非PPU硬件未验，暂不宣称PR就绪。

兼容验证完成：相同最小导入 before失败/after通过；禁止加载FlashInfer通信的PPU公开import通过；原完整GLM套件 **427 passed / 4 skipped**，原30失败消失，原失败保留。仅FGV上述一个源文件增加必要兼容边界，Plugin/FG保持官方版本。

## 模型启动与最小回归

命令 `commands/model-v1.py`，SHA `b646d597b4a6b704152e5d97ea4f92a61434c42f93aa0ca0b46de70741217444`。prepare重新冻结实际四库源码、脚本和空闲设备；dispatch唯一后台执行原用户脚本，工作目录为本任务 `production/`。顺序为P4096/D16的C1/C8，P1024/D64的C1/C8，P16383/16384/16385 D8边界、11明确答案、P4096/D16 C64/N64，检查FULL捕获及多token运行回放覆盖、当前16worker映射和服务身份。readiness3600秒，单请求900秒，无自动重试；失败只停本任务精确归属实例，不改用户脚本、不跑GPQA。全部通过后另行冻结正式评测。

已于13:15:14唯一派发模型控制器 PID3516430/start605312388，开始执行原用户脚本。正式工具包先行保存至 `commands/accuracy-tools-v1.tgz`，SHA `1fb34d0e166df106497ed6ad3ca790c713543223e288af5bc29b4e67a10fe202`；包含当前项目维护版包装器、原始runner和完整accuracy Skill bundle，传输/准备不发模型请求。

首次服务在13:16初始化失败，未发模型请求。首个worker栈为 `No valid MLA prefill backend ... FLASH_ATTN required dependencies not available`。公共GLM构造函数已有短作用域兼容patch，但守卫使用 `current_platform.is_cuda()`，PPU是vLLM OOT，守卫不成立；旧用户工作区同处使用 `device_type == "cuda"`。失败完整保留于 `production/service.log` / `model-failure.json`；观察到设备无运行进程，未重放旧控制器或开始GPQA。

新必要修复命令 `commands/OOT-fix-v1.py` SHA `c34fd33513a422d57c04e665473b86eb9853fe1290536fb11c25eadcd7a7878c`：只恢复公共构造函数这一行Torch设备契约，复用现有 FlagGemsMLAPrefillBackend 和 temporary_patches，不新增模型/平台分支、后端或数值kernel。补8个实际公共构造入口的路由/异常恢复单测，覆盖OOT CUDA、原生CUDA FlagGems、NVIDIA reference和CPU，要求未修版2失败/6通过，再修改并跑完整GLM套件。对应Plugin规范A1–A4/B1–B4/C2–C4/F1–F4；CPU桩只证明接线与回滚，后续TP16整模/FULL仍待验。

OOT修复已通过：新8项在原代码2失败/6通过，修复后完整GLM套件通过；当前真实平台观察为Torch device_type=cuda、native is_cuda=False，符合机制。新模型命令 `commands/model-v2.py` SHA `b534d15e1a2aa3fd482121a88d8d43a7a413b6a9169e3c574d5d935afb117385`，结果独立写入 `model02/`；仅在新CPU回归通过、设备和8011空闲时重新冻结并用相同用户脚本/最小模型契约验证，原失败不覆盖。

当前CPU为435 passed/4 skipped/0 failed（93.18秒）。model02于13:25:48唯一派发 PID3739226/start605375772，原脚本进程日志确认TP16、MBT32768、maxseq64、prefix=false和FULL_DECODE_ONLY。

正式命令预保存 `commands/formal-v1.py` SHA `c5bdb2ecc3fd9035f0d69d2a30948f88d61662df6abfa0480f3ddc83f332e644`，尚未派发。只有model02完整通过、当前源码/实例/空闲一致才允许dispatch。准备包括新工具包SHA、Skill bundle `1ed06a57f1f6e1ef39fb7fd872f579122b098a18f0255ade0a1160d6432c2b66`、两次provenance、原生preflight和新schema3契约；实际一次198/C64评测后按原生run-record签发，再按用户此前明确授权仅审计同实例正常DB写入、schema5绑定当前证据，不改原manifest/分数。API与eval重试均0，结果只有原生单轮，不补充/best-of。

为避免模型初始化较长造成接续遗漏，执行前另存 `commands/formal-v3.py` SHA `e58b59933229b4e6e2ce3ec36d9001d815add65b05d8cd2f537e64fa9a3df4f6`。v1未执行，v3仅增加独占dispatch标记和等待model02成功的编排，不改正式采样/门槛。该控制器可以先等待现有模型控制器；model02失败、退出无成功回执、当前源码/实例/空闲校验失败均停止，零正式请求，不重启或修代码。实际评测是否开始只以 `formal-gpqa-01/native-dispatched.json` 和原生生成进度为准，等待控制器的派发不能当作GPQA已开始。

条件式控制器于13:34:08唯一派发，PID4173496/start605425792，当前等待model02。尝试创建每30分钟只读heartbeat被自动审批拒绝（本次用户未明确授权持久监控）；没有创建定时任务或其他替代调度。当前会话只读跟进已授权控制器，实际模型/精度任务的授权和执行不受影响。

## FULL graph 阻塞与最小迁移评审

model02于13:43:48完成初始profile/KV分配，但16rank日志明确报告 `FlagGemsSparseMLABackend (support: NEVER)`，将用户FULL_DECODE_ONLY降为PIECEWISE。控制器13:43:50按冻结要求停止精确自有API及关联worker，停止回执 `model02/model-stop-result.json`；设备16卡均回到1MiB/空闲。正式接续13:43:53因模型失败终止，**GPQA零请求**。这不是新精度分数失败，也不能把降级服务作为原脚本FULL验证通过。

调用关键算子Skill，按当前源码重新核对旧公共路径差异。官方新主线增加了真正的BF16 indexer、DeepGEMM可选依赖保护等，不可整文件搬回旧FP8 indexer。后续仅评审迁移：Sparse MLA按实际operator能力声明单token Decode graph、UniformTypeKV组内准确识别MLA spec、KPool元数据稳定地址；H4普通kernel的mask/小head存储与物理索引融合转换，避免恢复旧padding/整数中间量OOM。当前仅完成只读比较，未简单把NEVER改为支持；候选必须通过当前设备独立oracle、两次更换输入的capture/replay、完整模型和新198题评测。此前CPU435通过仅属于graph迁移前源码，不能冒用为新候选结果。必要SQL缓存单表反射差异另核验，FG最新主线已具备该修复，不覆盖新FG实现。

保存迁移命令 `commands/graph-port-v1.py` SHA `60a6997be538dbecde0a127894931564b69970c52f7540f569f6ebef83edd6d9` 后执行。生产代码仅：Plugin `impl/mla.py`（按实际op能力预检、group spec、H4、融合整数转换）与 `glm5/kpool.py`（地址稳定）；FGV通用H4 masked kernel、新convert_sparse_indices及公共导出、SQL仅反射目标表。新版FGV公开Sparse MLA实际为 `_thead.fused.flashmla_sparse`，原64/128专用实现保留，新增H4预执行路由到普通masked kernel并声明待验证能力。没有恢复旧FP8 indexer、旧模型/runtime、旧vendor SDK入口、vision或mHC调参改动，没有删除新主线新增API/测试。

所有目标文件在 `graph-port-before/` 留前态，`graph-port-plan.json`记录逐文件前后SHA及补丁；不修改源容器或原工作区。新测试保留新主线原有内容，只合并与迁移相关的旧测试及补充真实公开PPU graph矩阵。先完整GLM套件，再公开Sparse H4 oracle/存储、H64/128守护、7组改变输入两次graph回放、整数转换/SQL测试；单PPU结果不当作TP16整模或新全量精度。失败保持OFF、保存证据，不进入模型或正式评测。

graph-unit-v1为471 passed/1 failed/4 skipped，唯一失败在新主线测试辅助函数 `_make_batch([])` 的空列表torch.cat，尚未进入待测builder。保存 `commands/graph-recover-v2.py` SHA `7ebad1ab9bd7df1bca1f406c36ed9103b6b00df30263d4f5aa8d9693777be8d7`，仅修该fixture返回空int64张量，保留零批次测试/断言和全部生产源码；再执行完整GLM与原计划设备矩阵。旧失败不覆盖，不启动模型或正式评测直至验证通过。

条件式后续命令预保存：`commands/model-v3.py` SHA `ffc62e4e860982702533821ea9f540527e220f35ef523e54084c9a327456b09c`，仅在上述CPU/单PPU通过且设备空闲后冻结 `model03/` 并执行原脚本/相同完整最小回归。正式接续 `commands/formal-v4.py` SHA `1fb4050c3310449d9a11604fc2133397ef201c43b183de5cab8ec5cf6904a7be`，唯一新跟进回执 `formal-model03-*`，不覆盖旧model02跟进失败。正式子目录仍为未曾生成的 `formal-gpqa-01`，只有model03通过和同身份空闲才发一次原生198题C64；当前这些命令均尚未派发。

14:17设备前置闭环：CPU完整472 passed/4原有skip/0 fail（91.22秒）；公开Sparse H4/大head守护、改变输入graph、整数转换/SQL组合171 passed/444 deselected（15.91秒），`graph-port-completion.json`通过。零模型请求，所有16卡均回空闲1MiB。允许接续model03原脚本TP16完整回归，单PPU结果不替代模型或正式精度。

14:18唯一派发model03 PID955990/start605689059；条件式正式接续PID956349/start605689154仅等待当前model03通过，不代表GPQA已开始。启动脚本/TP16/MBT/全部推理参数保持，实际评测仍以正式子目录native-dispatched为准。

最终只读核验预保存 `commands/final-audit-v1.py` SHA `d9fb836375e0a9b4692377aa0126960f507857dc29f3c65f5369fb477d62834b`。仅在model03通过且正式终态后执行，核验同一实例/四库源码/参数/模型/tokenizer、唯一editable安装、脚本、当前DB与health，零生成请求；精度仍由原生正式证据独立决定。

本地记录核验：YAML与diff空白检查通过；全项目 `validate-local --records` 有375项其他模型/既有过程产物错误，当前GLM案例筛选0项，不修改其他模型记录或清理其材料，不把全项目检查报告为通过。

首档FULL捕获实际679.56秒通过；第二档仍慢，16worker主线程CPU运行且无终止异常，瞬时GPU利用率0不能单独证明根因。保存 `commands/graph-stack-v1.py` SHA `ccd487d721968c0aaf8bd00b99c4a442682708cc98ae0cffd8b51da8c7b216f6`：仅核对自有API日志、父子链、PID命名空间、worker start_ticks/argv和未附加调试器后，对TP11主线程抓一次gdb Python/native栈，25秒上限，结束核对已detach且实例存活。不改源码/参数/DB、不发新模型请求；仅用于启动阻塞定位，不作为profiler或端到端收益。

14:44栈快照结束且worker已detach、相同ticks存活；native栈落在CPython `sre_ucs1_match/search`，但主机gdb没有py-bt辅助，未得到Python调用方，不据单栈断言根因。容器无匹配辅助文件。保存 `commands/get-gdb-helper-v1.py` SHA `ad188c4a2e018f2ba6c07b998d15d62945a88093e3dcba93320dd4bc0bcd1a59`，只下载CPython官方v3.12.3的Tools/gdb/libpython.py到本case并记录SHA、检查主机GDB Python版本，不安装依赖或执行模型代码；后续使用须单独核验该SHA。

远端下载因TLS连接reset失败，零进程附加；本机同一官方URL下载成功，helper SHA `8337d11b41f46a72d7070a94d76296d26db27e419ea66e878ceac7df14cfc16d`、70792字节。已核对其命令为调试器侧内存读取/栈展示，无inferior函数调用；只作为case工具，不安装到模型环境。保存 `commands/graph-stack-v2.py` SHA `759a135b2bb20ff80c80790bdef45f580a26b4e1dd9fc8be840715963922ea74`：先独立GDB无附加preflight helper，再按原精确归属抓同一TP11栈、detach核验；仅补Python栈观测，不改模型/源码/参数或发请求。

14:51完整Python栈已取得、同实例存活且detach；FGV MoE align `_run_tle_atomic_fused` →libentry default_policy/bench→SQL get_benchmark/get_sql_model→`AutoBase.prepare`→SQLAlchemy SQLite反射。3/11档已完成，但栈仍落缓存反射；不能据单worker栈量化全部启动耗时。当前代码确有only=lambda单表过滤，需确认目标不存在时空filter集合的行为。保存纯CPU `commands/sql-missing-probe-v1.py` SHA `edbd01eefabb396231d261529613d8cd3c30592f77f852b453adbad9db2f1363`，使用实际已安装FGV方法和独立内存1013表，记录missing lookup SQL/无关表内省数量，不访问生产DB或发模型请求。

实际方法CPU复现确认：missing返回None，但产生12158条SQL，其中12156条内省无关表（1013张简单内存表，0.552913秒）；only过滤为空时SQLAlchemy仍扫描全部schema。结合真实调用栈确认启动中反复进入此问题，不把单次简单DB耗时或单栈等同整模全部耗时。

保存 `commands/stop-model03-v1.py` SHA `9e698b2ff105dced51613663cc3bf0fcf93d984400f6a91486ba693288f10424`，核验model03控制器ticks/argv、API日志归属、无C1/正式请求后，记录诊断中止并仅停止自有控制器/API/关联worker；旧model03与正式接续失败完整保留。再执行 `commands/sql-missing-fix-v1.py` SHA `624e02ea2aac0a974e7e529bd1df47c3c81120f22f22760a9682c82e5cf8e0dd`：FGV SQL仅加has_table早退、保留既有单表/FK反射、不缓存negative结果；新增0/32/1013噪声表测试，要求旧实现3失败，再修复并完整SQL、相同复现无噪声内省、完整GLM测试。原文件/补丁/SHA保存，生产DB/数值kernel/原脚本和推理参数不动。失败保持OFF不进入模型或GPQA。

model03已于15:18:03按原readiness3600预算失败并由原控制器精确清理，15:18:07正式接续停止，零模型/GPQA请求。后续stop-v1的API断言因实例已消失而在任何停止/源码修改前阻止执行；旧失败未覆盖。保存 `commands/recover-sql-v2.py` SHA `cf4280f50e3b533a81e966f9119fd1c0fef5a948cc81db93dfc3aa67beb667c4`，仅重验源码、原失败和自有清理回执、端口及16卡空闲后执行已保存CPU SQL修复，不再停止任何进程。

后续命令预保存（尚未派发）：`commands/model-v4.py` SHA `b9809203469a6c7c7427a02d743567973e3f7ce3562a656d566c3208dd4d1e7a`，仅SQL修复及完整CPU通过后新建model04、按原脚本/同最小模型契约启动；`commands/formal-v5.py` SHA `1b24036d25bef51ecee08dff67b67cb50b00f85dce60c3418f9ab9cb2dc35966`仅条件接续model04，不重跑任何既有GPQA。新当前审计 `commands/final-audit-v2.py` SHA `27d7ee63aef1494689882a121c04514ccbddc34895a8c0af22cdc20963526514`，零生成、正式终态后执行，旧v1未执行且保留。

SQL修复闭环通过：新增3项原代码全部失败；完整SQL13 passed。相同1013表/相同missing返回None，SQL12158→2、无关内省12156→0（0.000253910秒，仅该CPU复现），全GLM回归通过，数值/graph文件未变，生产DB零操作。SQL文件SHA `62b1973407d315531e40a364557c172a7a397dddd166d2fff7918446360f3d3f`，回执 `sql-missing-fix-completion.json`。允许按已保存model04/正式v5接续原脚本验证，不以CPU查询结果代替整模或端到端性能。

17:11:23唯一派发model04 PID992872/start606729355；17:11:24条件式正式v5 PID993296/start606729450等待当前完整模型回归。原脚本/MBT/FULL与全部推理参数保持，旧model03终态及正式零请求保留；新正式实际开始仍以formal-gpqa-01/native-dispatched.json为准。

model04权重预取阶段数分钟无新日志，先核验FG当前实现：已含has_table早退与单Table metadata映射，本轮无需修改FG。保存 `commands/graph-stack-v3.py` SHA `f56a421dcba49c7a697fe3cf71e295f163f7e7b47bf544935e1118ee2a29e963`，复用已验证官方helper，按model04源码guard与自有日志解析TP11、核对祖先/命名空间/ticks后抓一次栈；模型请求/正式开始后不附加，零请求/源码变更。用来区分当前停顿是否仍属SQL，不推测前次原因仍适用于本次。

17:20该栈快照完成且worker同ticks存活/detach：Python位于profile_run→embed_multimodal视频dummy→公共vision linear→TP all_gather，native为libpccl的ncclTopoSearchTryGpu/RecGpu。表明该时刻执行通信初始化拓扑搜索，不能据此量化全部启动时间或认定死锁；保留现有通信库/环境/原脚本，没有叠加通信优化或源码补丁。

model04已完成11/11 FULL捕获，17:29:05就绪；首个P4096/D16 C1在17:29:06 HTTP500，当前实例由控制器精确清理，正式零请求。异常栈：输入embedding的mask函数触发Inductor→preserve_rng_state→torch.clone(CPU RNG)→FG GPU clone→CUDA device guard拒绝CPU。核对FG注册表与registrar：clone、max_pool3d的extra_dispatch_keys把 `(key, fallthrough_fn)` 写成平坦元组，registrar逐项解释为全局Autograd→GPU实现，再把function当key产生此前启动TypeError警告，导致部分错误注册已生效。

保存 `commands/autograd-fix-v1.py` SHA `8dd5584e7fcea66b8b550fee9c0c27701cc684ee6ff2f20b90b9179efeee2128` 与 `commands/autograd-tests-v1.py` SHA `47fb915a326e606c8c1ded093ae0c9f6adbb04f3d987b3affa6060447ed93511`。仅修FG上述两条注册为嵌套的(backend Autograd key, fallthrough)对，复用现有backend_info.dispatch_key，保留原CPU Autograd行为、GPU设备实现和数值kernel；不加平台/CPU计算分支、不改Torch/vLLM/脚本/参数。先独立无conftest注册测试证明原错误，再验证CPU RNG/clone布局和梯度、CPU/GPU池化及clone数值/梯度、Inductor编译与两次更换输入graph、完整GLM单测。执行前核验model04源码冻结、空端口和16卡空闲；任一失败保持OFF不晋级。

v1因文本选择器空白匹配计数不符在任何源码/测试写入前停止，原错误保留。新 `commands/autograd-fix-v2.py` SHA `f30cd9443d82a95028e0145f2402c65041e70899fad6de0478a37afa4cad93d4`仅改为AST选择clone/max_pool3d两条、逐项核验原结构并按源码跨度替换；原修复范围、所有before/after测试和阈值不变，不重复模型请求。

Autograd v2修复验证通过：原代码新CPU/配置测试失败，修复后11项全过（13.81秒），覆盖CPU RNG状态/布局/梯度、加速器clone与池化数值/梯度、Inductor及两次更换输入graph，完整GLM单测通过。数值kernel不变，回执autograd-fix-completion-v2.json。

预保存下一轮 `commands/model-v5.py` SHA `7f8f9f11930fe95dbf52979feb73349e5dcd4a948e3593aae4c81f077d70dbf5`，仅上述全部通过后启动model05，原脚本及完整模型回归不变。条件式正式 `commands/formal-v6.py` SHA `11314f757f187a662911c9dee7e13dc2d8b86df456bf612e77390ada76f4e9f2`，只绑定model05成功实例，198/C64/86%/60K参数与零重试、不补充契约不变。最终只读审计 `commands/final-audit-v3.py` SHA `f34482c4ea735cee34a854fa34f7650f4b66a705b9846cc75a9344bfaa93a3af`，正式终态后执行。model04与旧正式接续失败均保留；迄今没有发过正式GPQA请求。

17:51:16唯一派发model05 PID1890718/start606968601；17:51:17正式v6条件等待PID1891159/start606968696。原脚本、MBT、FULL与全部推理参数不变；仅模型回归成功后才允许一次正式198/C64原生生成。

model05于18:06:36完成11/11 FULL并启动服务，18:06:42开始首C1，18:11:41正确返回，真实请求未复现CPU RNG clone错误；随后C8于18:16:41因`sample_tokens` RPC超时失败，原控制器已精确清理，正式v6停止、零GPQA。日志未见对应OOM/非法访问/新的worker数值异常；超时本身不能区分冷调参、长算子执行或通信等待。只读核对vLLM envs/multiproc_executor：`VLLM_EXECUTE_MODEL_TIMEOUT_SECONDS`默认300秒，同时用于execute_model与sample_tokens；不修改vLLM源码。

准备可审查的 `commands/rpc-diagnostic-v1.py` SHA `720db29dabfdd14b486c98c46d0451a7fa2e79dcb5edcf5974bfa5d54b87a939`：唯一临时环境差异为`VLLM_EXECUTE_MODEL_TIMEOUT_SECONDS=1200`，客户端1800秒，原脚本、TP16/BF16/MBT32768/maxseq64/FULL/数值代码/生产DB策略不变。仅P4096/D16的C1、C8、C64各一次；成功或失败均停止精确临时实例，无重试、不发GPQA或签gate。若成功，另行恢复原默认300秒服务并完整模型回归通过后才做原正式198/C64。dispatch必须验证由直接用户批准且绑定本命令SHA的approval.json；当前只允许零生成prepare，不创建approval、不启动诊断。需要批准源于用户此前“保持MBT和启动参数不变”的明确限制，不是精度Skill新增审批门禁。

RPC方案已零生成prepare通过（rpc-diagnostic-01/model-prepared.json）；尚无approval或dispatch，已向用户提出临时1200后恢复300/保持300先离线定位的选择。等待期间保存只读 `commands/awaiting-approval-audit-v1.py` SHA `9df5b96f70cbaa07f80fa8045f7d26f162c06c6b128e58ab34d29a8fdc713db2`，核验源码冻结、三库唯一editable安装、脚本和当前空闲、方案未派发及零GPQA；不改库/服务/参数或发请求。

18:40只读审计完成：三库各1份editable/metadata且实际导入均指向本轮新目录，HEAD仍为7094141/fe919c5/9f6a0ef；源码符合model05冻结，脚本SHA未变。当前目标API0、16卡各1MiB空闲，RPC方案未批准/未派发，原生GPQA请求0、无当前正式gate。实际源差异计数为Plugin运行代码3+测试3，FG运行代码1+测试1，FGV运行代码6+测试3；其余原工作区及归档保留。FG注册源SHA `b19171acbd9b5cb20c56c348a23bf8189341e627390cfaad541580ff65d3f52a`，新增注册测试原版5失败/2通过/4未选，修复后11通过。审计回执awaiting-approval-audit-v1.json。当前等待用户对临时RPC启动环境变更的选择；不把C1/FULL通过或历史分数当作新版本全量精度通过。

用户已直接批准临时RPC1200诊断并随后恢复300（两个相同范围问题均收到明确同意）。仅C1/C8/C64各一次，MBT/数值源码/原脚本不变，诊断实例不跑正式GPQA；停止该实例后恢复原300并完整模型回归，通过后才进行全量精度。唯一派发包装器 `commands/approved-rpc-dispatch-v1.py` SHA `e20ea92ea0fcf646430e7a84be569d961830ce8173e3797cc0e660a40cbcfcb9` 已保存，执行前复核源冻结、精确服务OFF、16卡空闲、无既有派发与GPQA，并独占创建用户批准回执。

19:22:11临时诊断唯一派发，宿主控制器PID4148767/start607514122，回执 `rpc-diagnostic-01/model-dispatched.json`。派发前已确认源码冻结、原脚本SHA、无API、16卡空闲；直接用户批准回执已独占保存。该轮无GPQA或精度gate，结束精确停止临时实例。

API2886992/start607514233已确认RPC环境1200；EngineCore2887474的/proc启动环境缺该键（动态Python环境尚不能据此判断）。保存只读调试命令 `commands/rpc-engine-env-v1.py` SHA `8c25723de70aaf35ed556effef69424713bdc54f5dc6e83aecc5993c745ca2a4`，仅对本临时实例EngineCore按API父链、namespace/start/argv检查后短时attach/detach，读取Python os.environ中的单个RPC键和栈，不调用inferior函数、不打印其他环境值、不发额外请求或改库/参数。

EngineCore环境观测v1已正常detach且进程存活，但CPython3.12对象inline属性未读到，不能以gdb退出0当有效证据。保存v2工具修复，仅按官方helper的get_keys_values读取同一环境单键，无模型重跑。`commands/rpc-engine-env-v2.py` SHA `c3a531c5aa19900cc1105d7ac026773dab7a2f7ae291c0464510f5a8c1d45364`；helper SHA `09e8025c5e66868fbafbbeee04cedc1c9e754eaff1bda3370287b2ea6238a027`。原失败日志保留。

预存长C8定位工具 `commands/rpc-c8-worker-stack-v1.py` SHA `363420bd1cc9bb792fe064f75b9583f23469df5ae9c7e4155d8c62a77bc1e325`，仅当本轮已批准C8请求正在执行且明显长等时，对精确自有TP11取一次Python/native栈并detach；不追加请求/重试、不变MM策略或数值源码。

19:29环境v2已读到EngineCore Python os.environ中RPC键缺失；调试器25秒预算结束，确认TracerPid0且同进程存活。此证据仍不能排除vLLM启动后缓存环境值，需要继续核对env缓存或请求中的实际timeout，不能声称引擎1200已确认。没有追加模型请求。19:30权重加载427.90秒结束，服务继续初始化。

纠正环境v2观测：官方PyBytes.proxyval返回str，工具误用bytes比较，故原null不构成键缺失证据，原日志保留并标观测无效。v3仅修正键值类型、减少栈输出，仍同实例只读环境核验。`commands/rpc-engine-env-v3.py` SHA `329c2796178bf06cd9dace6d445f94896fc93f65ae4b15cc574a50e6b5e7562a`，helper SHA `718785b357a0541981cd7e09a8a353697c3d4aef8ebb0188ccbea79bf01bd897`。

Python环境观测v3仍因对象类型读取失败，未签发配置已生效结论。保存 `commands/rpc-engine-env-v4.py` SHA `47ce3ad1ee47969741d635041f72ebfd8dbfa40ccf5cdce1fd0764678e490f4d`，改为只读libc environ内存中的RPC单键（helper SHA `9cb55891fefa1995f4c505f782a18ae249fad311ca530e8a4b7d20ef9a958ea3`），无inferior调用或新模型请求；所有调试均确认detach同进程存活。

19:37动态libc环境只读核验成功：精确EngineCore的RPC键值1200，gdb正常退出/detach，同PID/start存活；日志SHA `3c52143979f388ddd071df0906cca079fce0652c1730bc7fd59367abccd4f7a9`。此前Python读取工具失败及proc快照缺键均不作为实际环境缺失证据。

保存后续原300恢复回归命令 `commands/restored-model-v1.py` SHA `79d87ccb09eefa857974466b861a3fbca27c544cd39d452595c7a1de4046672f`（仅临时诊断三阶段全部通过并停止后才prepare/dispatch；原脚本无环境覆盖、显式核对300、完整原最小回归）。正式条件命令 `commands/formal-v7.py` SHA `0e29edfd8ac28f00588546eb673bd57de0c137632294ac2031c2cb74c1d87a3e`，仅恢复后完整通过才允许一次原生198题C64；最终只读审计v4 SHA `0df2adf4fdfe338d121ebf1c70afe3e0ea3392427b7ea3f53810a88d7a785202`。三份目前仅保存，尚未派发。

19:36 FULL11/11与服务ready通过，C1于19:36:54通过、C8于19:37:50通过；C64同刻开始。缓存已自然积累，且仅功能诊断，不能用此把RPC根因签为已确认、不能算性能收益。已保存有限条件接续器 `commands/approved-rpc-follow-v1.py` SHA `619785ea1e942856b54d1638efdeed35fd0d21422ffacb021c7e9ef8200e8ac2`：只等待现有诊断成功+精确停止，才执行恢复300/完整模型/原生一次GPQA/最终只读审计；任何前置失败不重试、不改源或策略。不是周期monitor。

19:40:41有限条件接续器唯一派发，PID393990/start607625095，当前等待既有C64，不重启/重跑。C8已完成，预存C8栈工具未执行；改存相同归属核验的C64单次栈工具 `commands/rpc-c64-worker-stack-v1.py` SHA `9b529f8f451af5a138b1962cd83025afca473dd0ccc06836520c03833aa42fd1`，仅现有C64长等时执行，不添加模型请求或改变策略。

19:42 C64现有请求的TP11单次栈取证完成并detach同进程存活，日志SHA `2ae390a42dac11f40ac93c2542c64532ce8608f93a2394e2286e79d5a862d666`。实际执行落在公共BF16 indexer的logits第114行；源码是row32/col512两层Python循环，逐块调用router_gemm/ReLU/带权归约。该快照证明此路径命中，尚不能归因全部耗时或证明此前RPC根因，不是MM调参栈，也不据此叠加新优化。

19:52:47 C64原生64/64通过，19:52:50诊断completion与临时实例精确停止回执均落盘。C1约11.21s、C8约55.39s、C64约897.62s，仅诊断耗时（含原生编译/调参及调试观测影响），不作性能收益或根因单变量证明。没有补发或丢弃请求，没有正式GPQA/gate。19:52:59原300恢复完整回归唯一派发PID738868/start607698900，目录restored-rpc-01，原脚本无RPC环境覆盖，启动前独立进程确认默认300。

纠正19:52恢复启动状态：restore01在运行原启动脚本前的300核验发生JSON解析工具失败（vllm.envs导入INFO混入stdout）；production目录/启动命令均不存在、零模型请求、零GPQA。原失败和条件formal/follow失败全部保留，当前服务OFF、临时1200已停止。仅修复证据为单一标记JSON并在prepare前验证解析，不改模型/数值/门槛/900客户端预算，复用已通过诊断。新命令已保存：restored-model-v2.py SHA `303fb35bb27184e3732fc79c6d162364900ab5d46991f74a58de23bc21b57c21`，formal-v8.py SHA `fca07f4a5cee0c781f9bd1a13d071dc7eeb32ecd1ed376b8ae1de7a2d7d154b8`，final-audit-v5.py SHA `20e16b51666d0400f049fb0d6b1e6525fa40f5123d237590c08c1ec95ac1f69d`，有限接续approved-rpc-follow-v2.py SHA `527b123c6e4e2c442be666a7ab13032a7a71b2f5455d2830517b702717620293`。新唯一目录restored-rpc-02。

20:00:27工具恢复有限接续器v2唯一派发，PID889021/start607743749。先实际核验标记JSON默认300，再唯一启动原脚本；仅完整模型回归通过后接一次正式GPQA，原诊断不重复，旧restore01编排失败保留。

20:04只读确认restore02实际API3052606/start607746389已启动，日志属于唯一restore02目录，原脚本SHA未变，environment_overrides={}、API无RPC覆盖；默认300在prepare和run前均实际核验。模型控制器893804/start607745157于20:00:41唯一派发；正式条件控制器894264/start607745244仅等待完整回归，原生GPQA仍零请求。

20:13:35原生产300实例ready，身份PPU-13:glm5.3-flash-opt-20260911:3052606:607746389；FULL11/11捕获334秒通过。`restored-rpc-02/production/restored-RPC-timeout.json`核验容器默认300且API/EngineCore均无覆盖，不再继承临时1200。C1于20:13:36开始，后续按原完整最小回归顺序，GPQA尚未发送。

原300的P4096/C1于20:13:41通过、C8于20:14:27通过。P1024/D64/C1既有回归请求长等，保存单次精确自有TP11栈定位 `commands/original300-smoke-stack-v1.py` SHA `5fb55b726c31c15aeab9a49d21e463a853d5513ec083d402022ac99e0d9cc403`，不追加请求、改环境或MM策略，不在phase终态后attach。

P1024/D64/C1于20:19:11正常通过，计划栈工具因phase已完成在attach前守护退出，没有附加调试。现C8同类长等，预存 `commands/original300-smoke-c8-stack-v1.py` SHA `396ba4943d3b1ee77201a6688800c5b7997a35168c8a53a6761560ca18eaf45b`，仍仅现有请求单次精确TP11快照，不追加请求或改变策略。

20:23:07 P1024/D64/C8既有长请求TP11栈已捕获、正常detach同进程存活，日志SHA `b7503c2dcfbeabe0f9d143915dec6a5dad3d0e327897c6cf9c96a6bb88628c4a`。链路为Torch Inductor调用mm_out→FG general_mm→libentry default_policy/bench→Triton make_hgbin等待编译子进程；确认一个长等待点是当前在线MM调参编译，不是只凭源码推测或FP32异常。该快照仍不证明原model05全部RPC因果，且有短时调试暂停影响，不算稳态性能。20:24:12原生尚无新RPC错误，C8继续，后续边界/答案/C64/GPQA未开始。不变源码/策略、RPC300、原脚本与MBT。

2026-10-31收尾：点59仅既有thead.yaml的mm/mm_out注册排除后，原RPC300完整模型/FULL/C64回归通过；更新三库+必要兼容+该配置的同实例原生GPQA198题C64得163/198=82.3232%，低于86%。外层4小时超时后原生结果完整写出，零生成结果/provenance及当前身份核验通过，原失败保留；本轮无gate，不能用历史173等旧源码分数替代。当前冻结待精度诊断，不自动补跑或叠加性能实验。证据与事件统一见[点59](20261030-native-mm-registration-repair-59.md)。

2026-11-01最新精度评估：用户随后授权点59全部21道timeout题统一补跑一次。10-31 20:12结束，21题答对9题、其他177题原样保留，合并172/198=86.8687%≥86%，补充口径达标。11-01独立核验全部样本/生成与来源、同实例当前三库源码/原参数/RPC300通过。原生单次163/198及失败证据仍保留，未伪造成新单次全量gate；无新性能实验。详细SHA/产物和范围见[点59](20261030-native-mm-registration-repair-59.md)。
