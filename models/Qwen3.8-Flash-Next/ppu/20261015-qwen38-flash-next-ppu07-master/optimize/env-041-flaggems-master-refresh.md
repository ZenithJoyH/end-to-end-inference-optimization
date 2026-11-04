# env-041：优化容器FlagGems master更新并保留i64修复

2026-10-20后续正式组合验收：[acc-017](acc-017-full-gpqa-ple-fixed.md#终态177198通过正式阈值7条60k问题仍存在)实际env041 Gems i64/randn与当前FP32/QSA M16/051 PLE组合177/198（89.39%）通过0.88阈值，源前后相同、原生gate核验通过。7条60K输出问题仍存在，不推定本版本独立解决旧症状；无环境变更或自动重测。

2026-10-19用户授权更新容器中的FlagGems。沿用PPU-07的`qwen3.8-flash-opt-ppu07-20261015`，按此前master+必要适配约定更新。本次仅包安装与CPU静态/导入核验，不重启/热切换8010、不访问8035、不发模型/GPU请求或全量GPQA；不改Plugin、FGVLLM、vLLM、Torch/FlagTree、权重、黑名单、共享启动脚本。

## 已核事实与实施范围

连接inventory限定PPU-07；首次沙箱内连接工具本地RPC未启动，沙箱外同一项目connectivity-check实际通过。容器镜像67309a95、唯一/mnt绑定保持现有隔离设计；安装与新源码目标都在未挂载/opt及私有site-packages，不改变挂载。

上游master冻结`f0aa7f12180cea4776a2aba3f3889b8fb82a28b1`（2026-10-19 08:25:01Z）；新真实副本拟`/opt/qwen38-flaggems-master-20261019-f0aa7f12`。先stage固定ref、读取新版本AGENTS/构建约束、与实际旧必要改动对比，再仅迁移未上游包含的index/index_put/randn早期i64提升；原副本不编辑、旧生成缓存不清理。不盲拷旧整文件覆盖master，存在冲突或必要模型API缺失先停止报告。

默认docker exec环境仍有`PYTHONPATH=/opt/qwen38-acc011-cachefix-20260924/FlagGems/src`，FlagGems版本5.5.0.dev0+g85cc5efb1.d20261015；当前8010的显式PYTHONPATH则加载私有038 Gems（index15ddfe41/index_putd8422ca2/randn48d700e3）。两者必须分开记录，安装成功不代表PYTHONPATH覆盖或运行worker已切换。默认路径覆盖不通过编辑旧live源码、强制sitecustomize或容器重建解决；新进程需去掉旧PYTHONPATH后验证安装绑定，服务切换/重启另等用户授权。

Plugin a696859b+PR4553cb373b1及本地FP32 helper SHAedab4737、FGVLLMb4d3382/QSA M16 SHA3bb3d083保持；旧038三个修复文件SHA与记录一致。完整revision/worktree/导入/source manifest、镜像/挂载、8010精确身份/计数、包安装元数据备份在执行前保存。新的editable安装只用no-deps/no-build-isolation，不自动升级依赖。回退为按已备份精确旧安装来源重绑，不自动回退/重载。

远端证据目录`BASE/environment/env-041-flaggems-master-20261019`，BASE=`/mnt/nfs/users/jinghao/qwen3.8-flash/20261015-qwen38-flash-next-ppu07-container`；执行脚本先本地apply_patch保存，再排他传至BASE/commands并核SHA，才执行。目录root规范路径、owner/权限/可用空间已只读检查；不覆盖现有数据。

当前状态completed-installed-CPU-import-passed-not-loaded-into-running-service。以下planned/执行前段落按时间保留；以末尾终态为准。无新的精度gate/性能结论，旧164/198 failed-score及性能阻塞保持；此次授权只覆盖安装更新，不能恢复heartbeat或启动任何评测。

准备入口`BASE/commands/env041-prepare.py` SHA cb753bb92bbfb19d160a6b288e7f258be11db414ea81db77773645bd1c0c472f：先固定8010身份/健康/零请求计数、镜像挂载和旧四树Python SHA与包metadata，再新建E并仅fetch固定master，不安装/修改旧源码。若非空闲零计数、身份漂移或目录已存在则拒绝。脚本本地AST核验；首次py_compile仅因macOS默认缓存路径权限失败，后续改独立PYTHONPYCACHEPREFIX，不修改脚本或掩盖失败。

## stage/安装前冻结

固定master已获取（FETCHED SHA68144f9c）；无AGENTS.md，已完整读取pyproject/setup。Host缺rg只使一次只读定位命令失败，改用Python文本过滤，不是模型故障。旧defaultGems git85cc5efb有4个untracked fused模块及init导出改动；为保留用户现有适配，四模块common_slot_mapping/gdn_packed_decode/ple_state/qsa原样保留并在新版init保留10个导出。新Plugin/FGVLLM的QSA M16来源不更改；不以保留接口声称新版kernel命中。

必要i64改动仅加在master现有文件对应表达式；没有用旧整文件覆盖新版本。准备后index SHA76006a1c、index_put75be5c88（新版基线变化导致不同于旧017 SHA，语义同为加载即i64）、randn48d700e3（逐字等于038已验证补丁）、fused init6acf205a。共8文件本地差异（4修改+4原样legacy文件），不含诊断hook。

执行入口`BASE/commands/env041-control.py` SHA3fa0389784b05ac4439fee61a7aa2bb6dae313571a94ad511ce33069379fbb7e；CPU-only `env041-cpu-check.py` SHAc048343fd542c2d915ceabf82297dccb552927306377d90056b50283c90402cd。先`--mode stage`复制新私有树/保存diff/核旧四树未变和CPU生成器，再`--mode install`单次备份旧精确metadata/finder/专属CLI后安装。现有setuptools80.10.2/scm10.0.5/wheel0.45.1不满足新构建pin，所以修订原no-build-isolation计划：使用pip隔离构建，仍`--no-deps`，仅临时下载构建工具，不修改运行时依赖。若构建失败，保留日志/不自动改pin重试。

浅固定checkout无tag距离，安装版本显式标记为本地构建`5.5.0.dev0+gf0aa7f121.env041`，不冒充上游release；实际身份以固定master和8文件patch/manifest为准。安装后清除PYTHONPATH的新进程核实际导入、唯一distribution及其他5包版本/来源不变；继承旧PYTHONPATH和运行8010单独说明，不删除旧源码或注入全局覆盖hook。

首次stage在CPU检查处停止：原脚本错误地把含tl.load的整个f-string当单个Constant，实际AST是JoinedStr多个Constant，误报changes0；尚未pip安装、未改变服务。保留`cpu-source-generator-check.log`及原脚本，源码补丁不改。CPU v2改为检查末段other=0与cast，SHA3179c6a0d88094e4bb2f40ef189cbf754f7b0e3c82f3cc178f6259b8b8c1e43a；仅续CPU审计入口`BASE/commands/env041-finish-stage.py` SHA30070d15a5d91557288987950867ffff1b9a12ac1dfb3b0bf9f21a74ecabfad9，复核既有新目录8文件scope/原四树/生成器与fused导出，写新v2日志，不重新stage复制或覆盖失败marker。

用户追问主线是否已有索引修复，立即只读重核：master仍f0aa7f12；index blob2243d5a4/index_put7a6b052f仍原加载无cast。PR5882/6413/6892均open/merged=false，最新mergeable=true（与前次GitHub计算中的false快照不同，不能继续宣称当前冲突），不影响“尚未合入主线”事实。故本轮新版必须保留本地i64补丁；尚未安装时已明确向用户说明阶段，未冒充升级已完成。

stage终态通过，STAGED SHA c7c7b5113b3b129403dab91995aae26abeedf90a3b0409e0b6b6f70ce44f2cd0；CPU v2核8种生成签名、16标量边界、3算子归一化AST与上游同值（randn RNG未改），所有src Python AST通过。fused init除4import/10export外与master AST完全相同，4legacy文件逐字等于旧私有038；git变化严格8文件，旧4树Python SHA、8010身份/零计数/health不变。接下来只执行已冻结control.py `--mode install`一次；保存精确安装元数据tar后用隔离构建/no-deps安装，不热切换8010。

单次安装成功，INSTALL_FINISHED SHA5184fd9a8d39e558417e4f7b11fdf7e8f71929c964f2809498ccaab3fa13e67b；隔离构建成功生成editable wheel（SHAce77e995fa1dae2210062165083033e29ac3f3aaeb0adbded7b1c2d3e8ddfcbc），仅卸载旧FlagGems安装元数据并重绑新副本，旧源码保持。clean-env find_spec和唯一distribution/其他5包origin+version一致检查通过；继承PYTHONPATH仍旧、当前8010仍私有038明确单列。无第二次pip或回退。

终态入口`BASE/commands/env041-terminal-audit.py` SHA2886db2a73eb272dd7b0becb9bd274d18446bcead22aadb9a919c5360b60be7f：CPU隐藏设备且不分配tensor，核包级导入/10兼容导出/FGVLLM QSA M16函数来源与FP32 helper源码SHA；未执行模型模块导入或算子。若隐藏设备导入失败如实留日志，不尝试GPU fallback。再核旧四树完整Python SHA、新关键文件SHA、镜像挂载与8010原身份/零计数，保存终态回执；不发推理、不重启、不访问8035。

## 终态

- 新FlagGems安装完成，源为`/opt/qwen38-flaggems-master-20261019-f0aa7f12`，master f0aa7f12180cea4776a2aba3f3889b8fb82a28b1+8文件本地兼容差异，版本为显式本地构建标记5.5.0.dev0+gf0aa7f121.env041，不是上游release。新版主线本身无index/index_put/randn修复，本次都以最窄补丁保留；randn源码逐字等于038已验证版本。
- 去掉旧PYTHONPATH的新进程实际包级导入与10兼容导出检查passed，vendor=thead、CUDA_initialized=false、0 GPU kernel。FGVLLM实际函数源码仍_the​ad/qsa_attention.py且M16，FP32 helper仅源码SHA核验；并非执行模型、QSA kernel或FP32 collective命中证明。8生成签名/16标量/全src AST及归一化范围检查通过，未执行新版本模型或设备数值回归。
- clean-env唯一FlagGems distribution/direct_url指向新目录；Plugin/FGVLLM/vLLM/Torch/FlagTree版本与来源保持，旧4树Python源文件全量SHA不变。安装元数据/finder/专属CLI精确备份留在E/install-before.tar；回退可在清除PYTHONPATH后对旧`/opt/qwen38-acc011-cachefix-20260924/FlagGems`重新editable绑定（保留原依赖，另获方向后执行），不覆盖整个site-packages。
- **继承容器原ENV的docker exec仍被旧PYTHONPATH覆盖**；验证新版新进程使用`env -u PYTHONPATH python3 ...`。容器ENV不可通过本次pip更改，未加入sitecustomize/优先级hook、未编辑旧源或共享start-model.sh来掩盖覆盖。当前8010仍加载旧private038，原身份/argv/health200及零请求counter不变；没有“线上已用新版”或“重启过”的结论。
- 镜像/挂载前后一致；TERMINAL_AUDIT.json SHA **29ebc5315832ee13176dfe1959076a3085a901c66dad094fe49ee54ac0f3c630**，SOURCE_AFTER与完整源码/patch/CPU检查/安装及导入日志集中E。无服务重启、模型/算子请求、8035访问或全量GPQA，monitor仍暂停；旧164/198 failed/no gate及性能阻塞保持。新模型回归/graph/rebind仍not_run，切换8010需用户明确授权。
