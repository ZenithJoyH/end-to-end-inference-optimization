# accdiag-029：TP归约与HC combine首差异边界

用户2026-10-18授权：仅8010补TP allreduce后、HC combine前后窄埋点并重启一次，19请求/C<=8/零重试，保留i64及QSA M16，不影响8035、不全量GPQA。执行inference-accuracy-diagnosis、accuracy minimal-regression；已收敛至具体通信/HC边界，按key-operator-analysis方法核验实际源码，不进行性能优化。

028独立CPU已证明两个doc81前缀778/808在all8rank layer0的GDN本地branch完全相同、post-attn首次不同，但中间尚有TP allreduce/HC combine。029只观察第0层attention：此前控制frontier、归约后、combine完整三输入、注入logits/weight和输出；六个doc81 freshPrefill各2C1+1Mixed，全部目标token行，不转储其他47层或背景。doc71保留阴性采样控制。若tap未实际命中或Mixed不覆盖，不扩预算伪通过。数值有限差异不等于bug，不自动停；输入错位/nonfinite/HTTP/observer故障停止新增、在途自然取证。

当前只读：PPU-07连接门禁通过，8010 API1419056/start504556673/argv5744d999健康idle，累计prompt9356/gen3420；8035无listener（用户已确认预期停服），作为本轮保护null基准，后续漂移需停止新增并询问，不操作其他服务。约6.5TiB空间，旧028原件和全部PT不改。只在新私有未挂载目录复制Plugin，新增诊断tap，不改原数学/engine/Gems/FGVLLM/权重/tokenizer，不提交代码。

CASE=/mnt/nfs/users/jinghao/qwen3.8-flash/20261015-qwen38-flash-next-ppu07-container/accuracy/acc-015-full-gpqa-ppu07-c64-current-i64-qsa-20261018；新root=CASE/diagnostics/accdiag-029-tp-hc-boundary-20261018/runtime-001，private=/opt/qwen38-accdiag029-tp-hc-20261018。逐条复用02819个payload，只换opaque header，8C1→7背景512cap→4实际Mixed C8，评分max1为同前缀测点，不是60K完整作答评测。无隐藏warmup/请求重试。graph两类7/7及>=2真实replay纳入证据；CPU同步/新缓存/短Prefill/C8与原正式长Decode/C64不同，不做性能结论或60K根因确认。旧acc015164/198 failed-score/no gate和性能阻塞保持。

当前：设计冻结，尚未部署/重启/发送本轮请求。执行前保存脚本SHA、image/mount/source和保护基准；只有门禁通过后一次精确8010 API SIGTERM，旧树自然退出，不追加kill，不重启容器。8035 null基准需在控制器ready、watch和freeze全链正确支持，禁止旧无条件listener造成假失败；新observer SHA就绪校验必须绑定029，不复用旧027常量。首次差异两侧完整PT、raw logits/prob/noise/RNG/HTTP bytes/token及全部8rank事件/服务可读driver日志保留。完整性缺失如实记录。

## 执行前冻结

CASE/commands/accdiag029-probe.py SHA742d3fba2160add886c3e05f0920368a465b4d76fb45a31dffe80635ebe16e3f；deploy.py SHAf55bafc80dbcd1adc10e67ff58decf065983c7302a69d0926969c223f79925b1；control.py SHAe24c9427dcb707ab9415e10c30b782475d1149e31b27273e0680c25ed17fe46f。新probe继承冻结027采样观察器，仅layer0六doc81完整目标行13frontier；每rank4GiB预算。私有模型仅加7个现有customop tap，部署AST去除诊断if后与028数学完全一致；没有替换原运算。HC-only本来禁用，仍走原F.linear注入logits→sigmoid→weight→residual相加，新增各边界观察，不更改数学。

本地编译因系统默认pycache目录写权限失败一次（未执行远程/模型），显式PYTHONPYCACHEPREFIX=/tmp/qwen029-pycache后通过。排他上传以上脚本及cpu-test后，在原CPU评测容器CUDA空/OMP和MKL1，执行`python3 CASE/commands/accdiag029-cpu-test.py CASE/commands/accdiag029-probe.py CASE/commands/accdiag029-deploy.py /opt/qwen38-accdiag028-layers-20261018/plugin/vllm_fl/models/qwen3_8_flash_next.py`不可用（该私有源码不在CPU容器）；改为同一模型容器CUDA空/OMP和MKL1执行AST-only测试，不导入模型/不初始化CUDA。测试报告写新029cpu-tests-001，文件不会覆盖旧028。

通过后Host一次`python3 CASE/commands/accdiag029-control.py --case CASE --mode prepare`，核PREPARED/DEPLOYED/requests/config/source/image/mount/保护null门禁，再一次`--mode restart`和一次`--mode launch`。继承已冻结027的原始19请求/收集/单SIGTERM方法，控制面新ready明确核029 SHA，freeze显式支持8035=null。launch后只监控原客户端，不重发或再次重启。CPU-only后处理另存后执行，无额外推理。

## 保护漂移门禁停止：0部署/0重启/0请求

四脚本排他上传SHA通过，cpu-test SHA98acae7d61c618686782026109e3b0da22e1b2027c41c71a1f5247670d9651b9；19项CPU AST正反例全部passed、单线程/CUDA未初始化，含新增7tap、其他层不写、数学AST一致、首差异原件不变。仅AST测试，不是在线tap/算子数值通过。

prepare第一次在首行8035保护null谓词失败，尚未创建runtime-001、未部署私有源码、未发8010信号、未启动模型客户端，19预算全未使用。随后的只读核验：8010仍1419056/start504556673/argv5744d999/health200；8035已由其他任务新启动2452583/start504867239/argv SHA242fb3ad271106fe03d4e00b7d179a0a4bf773b26ddb5ac9b14cb03d48a60fc0，health200。本任务对两服务均0操作；新实例变化不是模型/埋点错误，不归因本任务。按冻结保护契约停止新增，等待用户确认以该新实例更新保护基准后再准备；不擅自重试prepare/重启、无全量GPQA。

## 用户确认续跑并明确不访问8035

用户确认8035重启预期，授权以新实例为保护记录继续19/C8/仅8010一次重载；随后明确“不需要访问8035服务”。据此仅记录上述用户确认身份，后续不读取8035 listener/proc/health、不发任何8035请求/信号，不能声称其当前健康/实例稳定已核。以操作隔离保护它：只向已核8010 API一次SIGTERM、精确旧树退出、物理8–15门禁；8035用户确认PID不在该树是静态排除，不读取其proc。新controller-v2保留原029脚本，唯一控制面差异是移除8035探测，基准在before/READY/terminal标记user_confirmed/runtime_checked=false；8010绑定和source/image/mount仍实核，不降级其门禁。

执行命令改为Host `python3 CASE/commands/accdiag029-control-v2.py --case CASE --mode prepare`，核验后仅一次restart与launch；新脚本排他上传并记录SHA，不覆盖第一次失败前的原件。probe/deploy/CPU报告与19payload不变，无新增推理或重复CPU。当前8010只读仍1419056/start504556673/原argv，health200；PPU-07连接门禁再次通过。

controller-v2 SHA2ab40b3d47ea282e7b5a2919a21697cae1e6b5c950cc65299c2ac89152b2bb8e，本地编译通过。此后所有新before/prepare/run回执绑定v2实际SHA；原失败prepare未创建runtime，因此新root仍001、19预算全未用。

v2 prepare通过，尚无请求/重启：PREPARED b7652e7ae1066a2a7f29eb8ab8c566f6a001b50d430b2bc35c7cde683cc6c17f，DEPLOYED891a8502c943fd58bfe9fc455e3e6b5fdbbd9ac5d1e25411660e1728ea0a4810，requests570951ceb0f5296aed86afe55c94f06ca9e73e9c5c3c467e04269183c5e9e690，config07ad5dcbe17197947f623ecb7aca8043b6f7fe5ac023fc0b81744cf213952638，launch0d9fac0ba1117a807175449d14dc07f482e9d4cf4db87de80241d2b02fb4c0da。新模型0eea7922734f4db4b8e9cb2c6ab3c93907475b2a7efc7b593e35bc8360fa3921仅7tap，去除diagnostic if后AST同028；runner c3537353与probe742d3fba已绑定，真实HCrole=attn核验。image/mount/source门禁通过，8035回执明确user-confirmed/not-accessed/runtime-checked=false。接下来按已冻结命令仅一次restart再一次launch，不访问8035。

22:27:40.014697+08仅向精确8010旧API1419056单SIGTERM，22:27:41.060036旧11进程树自然退出，其他信号0；22:27:43.004223仅启动新8010一次。8035未查询/未操作。唯一客户端2739268/start504951961/argv f78e3a42于22:28:13启动，controller-v2 SHA2ab40b3d，等待READY；不再执行restart/launch/run或增加客户端。启动/权重编译阶段非精度结果，重启授权已使用。

已预存终态CPU-only审计脚本CASE/commands/accdiag029-offline-audit.py SHA66851e0fe9705ccfc02f259782cac0fbafd309ea78eb470713fa4fa3db0ffbef，本地编译通过。原客户端退出且CLIENT_FINISHED/FINISHED/FINAL_EVIDENCE齐全、19raw完整时，仅在原CPU评测容器CUDA空/OMP/MKL1执行一次；只读旧PT、逐份SHA与完整解包624层PT+192输入/采样PT，核全部13边界的C1重复及Mixed、实际target参数链接、raw/API/rank0token与counter、source和8rank图回放。另以保存的8rank preTP分支算FP64和/一次BF16舍入作为CPU诊断参考，以保存HC三输入算FP64/CPU BF16公式；这些不是GPU路径重放、不能将不等于CPU舍入顺序直接当bug。CPU报告排他写cpu-boundary-audit-001及4个CPU参考PT，失败不自动重试或推理。8035只保留用户确认记录，不新增查询。

22:32:20 READY与RUN_STARTED，新8010实际Host2727961/start504948954/原argv5744d999；all8新probe742d3fba/两类graph7/7已核。8rank C1六doc81测点各13frontier完整，实际Index/IndexPut均verified_i64_load_before_multiply=true；FULL回放已>=2，所有C1重复无差异。

首次排他finite marker epoch1792333987.7376401（22:33:07.737640+08），rank6/step39/q017，layer0 post-tp：1991680元素607805不同，首flat20480，-0.015869140625→-0.0159912109375，max0.0078125、RMSE0.00033903655618421557；两侧PT/SHA已保存。all8/两个778和808point在线首差异均post-tp，之前5控制边界逐元素同；hc-input/hc-normed/hc-logits/hc-weight仍同，仅hc-block及后合并output/post-attn传播差异。目标实际slot7/computed0、7peer全Decode、778/808完整prompt绑定已在线核验。finite差异不是故障，不新停/改采样/补发。独立CPU待核。

22:34:00.914506 CLIENT_FINISHED，19全部结束/0错误/0在途，22:34:11.758040 FINISHED（SHA c5c947043c792ad849c5734c29725eab257d539b9be4785b775b00f28ccbad50），原client2739268已退出。FINAL_EVIDENCE46b202918b6c27962c591fe51f28a1fc9361c184d3c0aff69bd967287c8f982a、FIRST_DIFFERENCE_EVIDENCE184a16476d07656595ed36dbbaaf0aed290b0136a62c7c3a6fe4305dad40599d；source前后及8010健康idle已核，无CLIENT/FREEZE错误。counter为9356prompt/3523generation，不能拿旧0283420替代，本轮以19raw实际usage再核。原生终态8035字段明示未访问、非当前健康宣称。

CPU审计执行前静态复核发现counter映射应将API completion_tokens对应服务generation_tokens_total；尚未执行任何CPU审计时修正为v2新文件，SHA697320ade55358b15ca97553e45429667d97beec280b5c98b9fc9f15601854a2（原66851文件保留不执行）。仅在CPU容器一次`python3 CASE/commands/accdiag029-offline-audit-v2.py`，原始服务/probe/请求/产物不变，无重启/额外请求/8035访问。

## 最终结果：首差异已拆至TP归约，HC不是首发边界

独立CPU一次审计完成，CUDA未初始化/单线程，**624份第0层完整目标行PT和192份输入/采样PT全部解包/SHA/数值核验**，19完整API token全部匹配rank0 non-discard前缀；9356prompt/3523completion与服务counter一致，source前后完全一致，8010原新实例2727961/start504948954健康idle、客户端2739268已退出。all8rank两类graph capture7/7、实际FULL回放508条/rank；Index/IndexPut实际运行实现均为017 i64，QSA M16文件SHA不变。只执行一次8010重启，用户“不访问8035”之后无其listener/proc/HTTP访问或操作；不能声称其终态健康已核。19请求/并发<=8/零重试/无正式GPQA。

CPU报告`runtime-001/cpu-boundary-audit-001/report.json` SHA **c904d2e4544fa003ceaad87a4c75f451739750df169db2c78a4ae4e92f3ce968**，manifest **3a08e5b268e93503b0d24131d1407bd1193b2258fcf223ef9d1e7458b7ed84f5**；其中report及4份CPU参考PT的5项哈希独立再次通过。原生FINAL绑定1002文件逐份复核通过；仅活跃service-diag.log已增加随后health读取，原冻结前缀仍精确、其运行期完整副本不变，未把日志追加写成hash失败或改写原回执。原始目标层PT共6,238,529,776字节，首差异全局及8rank marker与两侧PT副本齐全，HTTP bytes/全部已返回token/logits/prob/noise/RNG、8rank完整运行日志、可读driver ring均保存。无FIRST_ANOMALY/HTTP错误/nonfinite/已记录非法访问；有限差异未触发全池state freeze，无全池历史，不能将完整目标边界张量称为全模型因果现场。

### 复核结论

- C1重复：两个点、all8rank的全部13边界精确一致；doc71阴性控制最终raw logits/prob/noise在C1和Mixed完全一致。
- doc81 778和808：all8rank逐元素证明前5边界（含GDN本地branch）精确相同，**第6个`post-tp`首次不同**。两点maxabs均0.0078125，RMSE分别0.00033903655618421557/0.0003406577205681602，607805/1991680及633283/2068480元素不同。首flat20480，即目标第8行/feature0，-0.015869140625→-0.0159912109375。
- HC三输入实际链接均核验：block=postTP，residual=postPLE，normed=attn-hc-residual；后两者与注入logits、weight在C1/Mixed仍精确相同，HC仅承接变化的TP结果。
- 对4个测点×8rank共32份HC输出，使用实际保存block/residual/weight的FP64公式、最后一次BF16舍入，**全部逐元素等于在线HC输出**；纯CPU BF16逐操作公式因额外舍入并不相同（最大0.0009765625），不能把CPU eager作为无条件逐位oracle。该证据支持“本轮HC输出是已有TP差异的传播”，并非HC首发差异。
- 每个测点8rank的归约结果彼此精确相同；8份本地输入FP64相加在C1/Mixed完全相同。但在线两种归约结果均不同于“一次FP64求和再BF16舍入”的参考（两点max0.0078125，RMSE约3.71e-4/3.72e-4）。这与低精度多步归约/顺序差异相容，**不单凭与FP64不相等证明通信bug**。
- 最终raw logits仍有变化：778 max1.1875/RMSE0.2367291，808 max0.9375/RMSE0.1454066；808实际prob L1=0.09232220/max差0.03044386。同noise、实际下一token仍1596/494。本轮最终漂移数值不等于028的1.67578/0.91406，新增tap/编译分割/缓存/时序可能改变后续路径，不能伪称与旧全48层测量逐位复现；**首层TP前同/TP后不同的边界则已再次直接证明**。

因此，本轮回答“TP allreduce还是HC combine先产生差异”：**TP归约输出先不同，HC combine不是首发**。精确实现机制仍suspected（批总行数778→785、808→815及目标起点0→7可能改变分块/归约顺序），当前无独立GPU归约reference/通信运行时分支埋点，不把它认定NCCL内部某个算法。只读源码追踪为`tensor_model_parallel_all_reduce→TP group.all_reduce→device communicator`；launch显式disable-custom-all-reduce，communicator源码仍有多条分支，源码/启动开关不能替代函数对象/分支真实命中。一次源码读取因重复vllm路径缺文件失败后已修正，仅工具路径错误，非模型错误。

### 限制、结论与下一步门禁

状态为局部受控边界定位完成，而非正式精度修复。首次full Prefill/778和808短前缀/C8/单token评分、有CPU同步和新编译cache，不等同原54K–60K Decode/C64负载；缺“控制归约变量→原症状消失/恢复”的单变量证据，故**原60K不收敛及低分根因not-isolated，acc015164/198 failed-score/no gate保持、禁止叠加性能优化**。

若继续，应先对已保存8rank分支输入做独立受控归约，分别固定总shape、目标行起点、累加dtype和运行时后端，区分BF16合法舍入次序与实现缺陷；GPU微测、改通信路径/加新运行时埋点或再次重启都不在本轮19请求授权内，须先告知用户并等待方向。本轮不再执行推理/重载/正式GPQA；原heartbeat继续PAUSED、前台终态收尾。

知识差量refined：028只能定位TP+HC区间，029全目标行证据拆出TP输出首差异及HC高精度公式一致；后续优先验证归约形状/偏移/累加，而非先改HC或QSA。证据卡仅记该模型/平台/形状，不外推其他模型或声称性能收益。方法bundle（执行前）：accuracy6e94a080dd3b64544c535e1fd4bda506f55516374d14d0f8ca6aa148bba2c7b2、diagnosis796f57d730fa08a05afa0417af3107087e8513d3de2c989d6a14b80ee8aece2e、key-operator002185ceaea65d585c476f04f4c325a5dc57b289a9f4ef37132c853231dc0e23。
