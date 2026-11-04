# env-001：将当前独立验证环境迁移到 mx-104

当前终态（2026-10-23 22:02UTC）：迁移与ERQA通过；同设备六实例180轮targeted对照证实split1吞吐回退P1K11.37%、缩减长KV38.30%，全轮与源码证据有效。已恢复原split1/helper，prefixON、graph16/C8及health通过；本轮监控停用。完整长KV扩大尚未执行、无mx104 GPQA gate或正式验收。下文保留各阶段原始决策历史，最终表格和复盘见文末。

用户2026-10-23要求暂停mx-59测试，把当前容器和相关服务迁至104，另明确指定远程工作目录`/public-flash/jinghao/qwen3-VL`。当前范围为模型容器`qwen3vl-pr977-20261022`的有效writable-layer快照，以及原GPQA/ERQA评测环境；源生产9999和其他Host模型不在变更范围。

迁移使用新案例`20261023-qwen3vl-metax-mx104-migration`；相同共享NFS路径可直接读取已有模型/证据，镜像通过私有docker save/load文件迁移，不推送外部仓库。不覆盖源容器，不将旧Host分数或部分ERQA结果拼接到新Host。当前源模型容器已于03:12:13 UTC停止（只读发现），没有重启它；暂停回执记录的两个控制器及原生ERQA客户端均已停止。

新目标：mx-104，C550 GPU0/1，TP2，18977，`qwen3vl-pr943-split1-mx104-20261023`。驱动3.8.1、MACA3.7.1.5一致；其他服务使用GPU2/3，不变。保留采样、gems-opt、MoE、Plugin单行num_splits1、prefix cache ON及完整服务argv。模型目录bind保持`/public-flash`和`/data`同Source/Destination/模式/传播；新主机的/data是本地主机对应路径，私有代码与导入路径由镜像保留且必须重新校验。CPU评测器使用新案例目录作为其产物bind；它不改变模型容器mount-parity门禁。

实施门禁：快照镜像层/配置谱系、迁移包SHA、目标模型挂载diff、四仓库及权重/tokenizer指纹、实际导入、两rank native split1/FlagOS MoE命中、capture/至少两次replay、smoke/C8。未通过前不启动完整ERQA和性能流量。迁移本身不构成性能提升，不与mx-59计算速度差。精度/性能结果目前均not_run于mx104。

远端脚本、镜像包、inspect、原始证据：`/public-flash/jinghao/qwen3-VL/20261023-qwen3vl-metax-mx104-migration`。回退为停止目标案例创建的精确服务，保留新旧容器和快照；不自动恢复mx-59评测。

快照进展：模型镜像7aed06b4、ERQA997570d1、GPQA6342cb93均生成；源save包进行中，目标导入控制器等待完整包SHA。首次门禁因Docker User空串/null表示差异停止；已实测等价默认root，只对该字段做规范化后继续，失败回执保留，未改模型源码或启动语义。完整脚本SHA见state.migration.artifacts。

迁移包15818401792bytes，SHA bd960bae54b6ce3d7298018c66d8a12d8cacce936cbb041d1bb94a4b90cac3dc，两端校验相同，三个镜像已导入。首次目标资源门禁在创建容器前因显存条件停止，保留migration-failure.json；随后原生mx-smi复查0/1均859MiB且无进程，2/3无关模型仍运行。v3复用已验证镜像，继续相同GPU0/1资源检查；不放宽空闲门槛，不停止其他服务。

设备计划修订：03:36:44UTC持久化原生回执明确显示GPU0/1各62091MiB，关联其他VLLM workers33906/33907。没有停止它们，且本案例尚未创建目标容器或运行测量。改用空闲GPU4/5，CUDA/MACA_VISIBLE_DEVICES调整为4,5，TP2/完整argv/所有模型源码及语义配置不变。后续全部baseline/candidate/revert固定在同一4/5设备集合，不能与旧Host或0/1数据混比；旧两次资源门禁回执保留。

迁移门禁全部通过：新服务`qwen3vl-pr943-split1-mx104-20261023:32:1103764578`，GPU4/5、TP2、端口18977、served alias qwen3vl-pr977。源与目标镜像层/配置、目录挂载、四代码树、模型与tokenizer指纹验证一致；仅物理可见设备映射改变。两rank实际FlagOS MoE bbc2edded、native kvcache split1，capture/至少16replay与单请求/C8通过。完整原生回执`results/migration-completed.json`、`manifests/environment-gates.json`、`manifests/mount-comparison.json`、`service/results/minimal.json`；源mx59两个旧控制器已复查不运行，原模型容器仍exited。

迁移后的新一轮ERQA400（40分阈值）已经按原数据630图/原native400题契约从头启动，8并发、18000输出预算、temperature0.7、响应缓存关闭；不接续或拼接旧Host110条已派发的部分结果。性能控制器仅等待ERQA通过，再按同一GPU4/5做独立重启0/1/0两组、P1K完整与缩减P64K哨兵、5预热+3测量；主输出吞吐、副总吞吐，延迟守护。全部原始数据保留，波动/漂移不挑轮，有效回退后扩大。无当前新精度分数或性能数字，不跨Host复用GPQA gate，不声明全项目验收。

2026-10-23 07:48 UTC跟进：原生ERQA已完整保存400条，182答对、398条参与原生计分、2条SDK超时被原生拒答过滤，native accuracy45.73；按全部400条将拒答计错为45.50，均高于阈值40。原采集器在读取两条缺少correct的拒答记录时KeyError，性能控制器随之退出且尚未切换源码/服务。按inference-accuracy-diagnosis分类为采集schema不兼容；准备只核验已有原生400条、原生过滤方法、数据/源码及原服务身份，保留全部失败和结果，不重跑或修改native评分。修复命令与SHA已记入state，核验成功后按同一冻结计划恢复性能控制器；不会重放迁移或ERQA。

修复与验证结果（07:56 UTC）：完整raw/evaluated各400唯一ID与冻结题集完全相符。调用原生BaseEvaluator.filter_rejected核验ERQA_115、ERQA_213为SDK APITimeoutError拒答；native accuracy182/398=45.73，全部400计错45.50，均过40。原始runner退出0，模型/配置/四仓库/模型/tokenizer与原评测实例全程一致，630图和原生源码SHA后验通过。results/erqa-completed.json SHA74da2885f794baa5b2476f9d1c9456a87eb0085469e82641947a7f842b3d80c1。原采集器KeyError与性能停止回执保留，未重跑模型请求或改分母/阈值契约；原契约metric即native accuracy，45.50仅作完整400条保守补充。该分数绑定原mx104实例32:1103764578，不能视作后续重启实例的新评测或GPQA gate。

性能恢复使用commands/perf_controller_gpu45_resume1.py（SHAbcbfba8a），仅增加空目录/无旧控制器/原服务一致性守护、复用既有空目录并把新失败写到独立文件，benchmark/预热/阈值/矩阵和最终恢复逻辑不变。新控制器326708/startticks1105292086，07:56:14UTC启动；B1 split0服务30634:1105295016正在启动，尚无正式测量。保留其他服务，监控已更新至新控制器且仍ACTIVE。

08:18 UTC跟进：首组split0基线B1在5轮预热后未达到稳态（全5轮输出949.90/1018.09/1380.47/1144.75/1590.63token/s；最后3轮spread32.30%>5%）。全部128请求成功、每轮输入/输出均131072tokens，源码和输入前后SHA通过；尚无measured轮，不能用这些数值判断split1收益/回退。各轮中位ITL约36–37ms，>1秒token间隔376/306/148/193/0；同时间窗口Triton mcfatbin写入260/207/52/136/2，前四轮主要_guarded_sweep/sort及采样相关kernel，表明运行期编译仍活跃。CPU/内存/IO压力只读快照未显示明显饱和，不能以快照排除历史竞争。控制器已在08:20:33UTC恢复原split1源码/helper并通过两rank capture+16replay及C8，实例92578:1105417090。

根据预热失败证据冻结独立v2测量计划：所有baseline/candidate/revert统一12轮固定预热，再验证最后3轮output spread<=5%，通过才保留全部3轮测量；全部6个服务独立重启同GPU4/5，新ID W12-B1/C1/R1/B2/C2/R2，原5轮结果/失败回执保留且不混合。仅变更测量预热预算，采样/gems-opt/MoE/prefixON/模型启动参数和性能门槛不变；新计划/比较元数据/缓存策略及控制脚本路径SHA在state记录。若新固定预算仍失败则停止恢复并继续定位，不放宽标准或选择幸运窗口。

08:27:41UTC新计划已启动：控制器475511/startticks1105480822，scriptSHA898a3185；planSHA3b921051，comparisonSHA348113e2，cache-policySHAce7c679e，全部在发送新性能请求前归档。W12-B1/C1/R1/B2/C2/R2统一12预热+3测量，旧B1五轮不参与新比较。诊断回执results/perf-warmup-diagnosis.json SHAce21a3e3；原split1恢复回执passed。当前新基线服务启动中，尚无可比性能结论；监控仍ACTIVE并已切换至新控制器/新终态文件。

最新进度检查：W12固定12轮后仍incomplete，全部12×128请求成功但最后3轮spread17.45%，0测量轮；09:07:58UTC已恢复split1与原helper，两rank graph16/C8passed，实例174823:1105700599。当前准备确定性形状预热，不再增加完整压测轮数。

09:18UTC跟进：W12-B1固定12轮后仍未通过末3轮5%稳态门槛（17.45%，0测量轮），控制器已于09:07:58UTC恢复split1及原helper，两rank graph16/C8通过。继续限域只读诊断：commands/probe_sampling_cache_keys.py（SHA faf1f0d8a7e98aa84d095b21fd6e70e4864652926abd2d307aa1cb1584c77f02）在两个独立解释器中只导入和读取采样JIT依赖/缓存键，无kernel launch或模型请求，判断跨进程缓存失效来源；不修改模型源码或扩大预热预算。

补充只读证据归档命令：commands/analyze_warmup12_existing.py，SHA 2aad8bd60cf7615b6762d02e75b52514961ec6213c7db1588e0f2251e99ef9bc，核验12轮原生SHA/请求数/门槛、编译产物时间与M/PASS对应关系，保存独立results/perf-warmup12-diagnosis.json；原始性能结果不重写。

按关键算子分析与规划复盘（env-001-recovery-review-02）确认：第12轮新M4/12/20/61各需8pass×2rank，产生64个_guarded_sweep产物；总74个编译产物，与88个>1秒ITL间隔同轮。两独立导入的sort/FV源码SHA相同，get_int_t和one_zeros的@tl.constexpr函数repr携带不同进程地址，进入FlagTree JIT.cache_key，导致跨重启/TP进程缓存键不一致。证据results/sampling-cache-key-probe.json（SHA5c35aa17）及perf-warmup12-diagnosis.json（SHA1c2a7da0）。不修改该算子或编译器；其修复另案延后，避免污染attention0/1对照。

下一测量契约SC64：targeted/performance_only，仍P1024/D1024/C64/N128及P65536/D128/C8/N16缩减哨兵，GPU4/5、prefixON、12预热/3测量、末3<=5%及比较门槛不变。每个独立worker在原graph capture和KV分配结束后，临时helper执行原生_dummy_sampler_run的M1..64两遍，验证真实优化采样覆盖、第二遍0编译miss、RNG/KV不变，随后移除helper hook。六角色同法、独立实例、新输出路径；先graph/C8和coverage通过再正式请求，失败恢复原split1/helper，旧5与12轮保留不混用。所有脚本/config路径SHA已在state的sampling64_preparation中冻结，未修改vLLM/FV/FG/Plugin的采样/MoE源码。当前累计收益未知，不签发mx104 GPQA gate或全项目验收。

SC64已于09:38:33UTC启动：controller914705/startticks1105905979，commands/perf_controller_gpu45_sampling64.py SHAc35fe20d；helperSHA c0ec2433、planSHA3b921051（与W12数值计划完全相同）、comparisonSHA391eee0d、cache-policySHAd99adbfa。已核验并停止本案例空闲的W12-RESTORED实例，SC64-B1为183235:1105908823，正在启动；尚无coverage或测量结果。心跳已更新至SC64控制器/终态文件，旧W12失败不再作为当前状态。

SC64首组门禁核验（09:50:36UTC）：两rank实际优化采样均覆盖M1–64；首次准备各417.53秒、编译miss676/679，第二遍各约0.45秒且0编译miss，RNG保留、临时hook全部移除，KV预算前后均27672947507.2bytes/rank。worker.cache_config.num_gpu_blocks不可用，未以None==None证明block数；原生启动日志SC64-B1/W12-B1/W12-RESTORED均562992tokens，容量一致，预热在KV分配后且不执行KV attention。graph capture/至少16replay每rank及C8全部passed；coverage回执SHA96358ce5/551fcfe6，minimalSHA43479e04，完整路径在state。09:49:41UTC原生性能客户端流程已启动，09:51检查仍在client preflight，尚无完成预热/测量轮。控制器914705身份一致，无新终态失败；完整准备耗时不计入性能收益。

10:18UTC跟进：SC64-B1在client capability preflight阶段停止，rounds为空，原生回执明确未发送benchmark请求；sampling shape/graph/C8门禁通过仍有效。09:56:11UTC自动恢复原split1/helper并再次graph16/C8passed。只读定位客户端-c探针cwd=/public-flash/jinghao，被该目录同名vllm源码目录当作namespace package遮蔽editable安装；真实/workspace/vllm/vllm/benchmarks/serve.py完整。归档commands/verify_client_cwd.py SHA9e8f54ae73b8b45b13b716d49787921186603f6ec60cea9852eb3a404bde42a2，只对照旧cwd与当前case目录，运行完全相同runtime probe并要求解释器/benchmark全部SHA与W12成功回执严格相同；不触碰共享目录或模型源码。

冻结CWD64恢复方案：沿用已通过的observer.sampling64.py与相同12预热/5%/3测量计划，六独立角色改为CWD64-B1/C1/R1/B2/C2/R2。只将benchmark客户端subprocess cwd固定到本case，避免ambient namespace；源模型服务cwd/env/argv不改。commands/perf_controller_gpu45_cwd64.py及start_perf_cwd64.py、新比较/缓存元数据SHA见state.client_cwd_recovery；原SC64失败与恢复回执完整保留。先完成runtime probe严格源码绑定复核才启动。

CWD64恢复已启动（10:24:39UTC）：固定本case客户端cwd后，完全相同原生探针通过，解释器/版本/全部benchmark及CLI源码指纹与W12成功回执严格一致；旧cwd复现失败，共享同名目录未改。results/client-cwd-diagnosis.json SHA38681d6a48ce2322e845dbcb28b270fb4e6e2b8c4a5564755999c3d445a351b9。唯一控制器1244310/startticks1106182655，manifest perf-controller-cwd64.json；首组CWD64-B1实例284405:1106185450于10:25:07UTC启动。新实例的形状准备、graph/C8须重新通过后才发送性能流量；当前0完成预热/测量，无吞吐结论。心跳已更新为cwd64终态文件，SC64零请求失败与09:56恢复均为历史。

11:38UTC跟进：CWD64-B1已通过12轮预热的末3轮稳态门槛（2.4996%<=5%），首个测量轮13却产生131073输入tokens，其中索引64为1025而非1024。全部128请求与131072输出成功，原生日志在发请求前已报告decode/re-encode多1token；不是attention性能回退。原生RandomDataset的10次长度修正耗尽仍返回不匹配结果。控制器已11:07:12UTC恢复split1原helper，graph16/C8passed，实例366271:1106416538。保留无效测量，不放宽长度门禁。准备CPU-only原生生成复现与全部30轮长度预检，固定候选base seeds1042/2042/3042/4042按长度有效性选择，完全不看吞吐；任何新计划六角色统一重跑，模型配置不变。归档命令commands/audit_random_input_lengths.py SHA678cb19647bb337af2a7c46edcb415ddcbf7b4503d27580ff0d6c37079d54902，执行前已记录。

失败归档命令commands/summarize_cwd64_existing.py SHA4bfd337a0542bce2b61553a9f273b960e928684abcfa9340973d48eb69e00ad7：仅重验13轮raw/validation/output SHA、稳态门槛与恢复回执，写独立results/perf-cwd64-diagnosis.json，不覆盖原数据或发送请求。

CPU预检通过：原seed74295精确复现索引64=1025；按预定候选顺序首个base seed1042的两场景共30轮、2160条输入均独立重编码为目标长度。证据random-input-length-audit.json SHAa540328db52fdee5167636fd6d0e0c32f7a42575c5d58b280bfb576761f600a0。规划复盘env-001-recovery-review-03保留采样形状准备（CWD64轮2–13无>1秒ITL间隔），不改vLLM生成器/模型源码、不放宽token校验。新IV64测量计划只将base seed42→1042，六角色全部统一、全部重跑，原始13轮不混用；保持12预热/末3<=5%/3测量及全部性能门槛。脚本与新configs的执行前SHA见state.input_validated_recovery；每角色dry-run必须匹配CPU审计的30个case/round/seed。

IV64于11:46:45UTC启动，唯一controller1434728/startticks1106675186；scriptSHA007d3e64、planSHA7f7f7e3b、comparisonSHA025c85d4、cache-policySHA3822c2a5，均执行前保存且启动时复核。已确认控制器身份一致，无iv64新失败；当前IV64-B1准备新实例，0完成轮次。监控已切至iv64终态文件，旧CWD64恢复回执不再代表当前进程。

11:49:33UTC只读复核：IV64-B1服务375049:1106677999已于11:47:13启动；唯一控制器1434728/startticks1106675186仍运行，无iv64失败回执。两TP worker正在加载权重；新实例的采样覆盖/graph/C8和性能轮次尚待完成。未重复启动或调整配置。

12:20UTC跟进：IV64-B1两rank实际M1–64采样准备通过，首次各504编译miss、第二遍均0miss，RNG保留且临时hook移除；graph capture/16replay每rank及C8passed。11:54:47UTC进入native benchmark流程，当前完成P1K预热10/12轮，每轮128成功、0失败、输入/输出各131072tokens，原生validation及输出SHA均通过。输出吞吐1544.12–1620.26token/s仅为预热观察，尚未执行12轮末3稳态准入，无完成测量轮。当前控制器1434728身份未变且无新失败；继续原计划，不新增实例或改配置。完整coverage/minimal/runtime/dry-run路径与SHA记于state.input_validated_recovery.first_trial_proof。

12:49UTC里程碑：IV64-B1（split0首个baseline实例）的P1K已完整通过12轮预热及3轮测量，稳态准入末3spread2.8882%。测量轮13/14/15输出吞吐分别1600.606/1577.969/1601.509token/s，总吞吐3201.212/3155.938/3203.017token/s；全部保留，输出中位1600.606、总中位3201.212，测量spread1.4707%。全部15轮128请求成功，输入/输出逐条1024且各131072总tokens，原生命令与CPU审计seed一致，outputSHA和必需指标均验证通过；三测量轮无>1秒ITL。TTFT/TPOT为含调度的客户端代理，不能充当纯设备阶段时间。正在进行缩减P64K预热，已5/12轮验证通过，每轮16成功、输入1048576/输出2048。唯一控制器仍运行，无新失败。这里只是首个baseline进程P1K的部分结果，完整进程后验源码审计、P64K与candidate/revert尚未完成，不能判断split1性能回退。完整三轮SHA及延迟在state.input_validated_recovery.p1k_first_process_partial_result。

13:56UTC检查：首个基线IV64-B1已于13:20:54完整结束两场景30轮（24预热+6测量），所有raw/validation/output SHA重验通过，service/model/tokenizer/四仓库前后完全一致，run-record SHAe7b08b0e6741a9cbd158d42db9e64029a6960c46579deb131f4e5478c21d6dcc。缩减P64K的末3预热spread0.11484%，测量输出13.972822/13.985251/13.982846token/s，总吞吐7168.0576/7174.4337/7173.2001token/s；全部保留，输出中位13.982846、总中位7173.2001，测量spread0.088889%。prefix cache全程ON，计数增量queries17694720/hits2016，观察到微量命中，不用预期reuse0替代实测。

同一控制器已自动进入IV64-C1（split1）实例463238:1107242784，13:21:21启动、13:28:25开始benchmark；两rank全部M1–64准备、第二遍0miss、RNG保留、hook移除、graph16/C8全部passed。13:59:37UTC复核P1K已完成12/12轮有效预热，每轮128成功、输入/输出均131072，末3波动重算2.0656%<=5%，无新失败；尚无完成candidate测量，不能拿这些预热吞吐和baseline测量作性能回退结论。继续原六角色计划，独立重复/revert未齐，不扩大或改配置。

14:29UTC首对测量信号：IV64-C1的P1K全部12预热+3测量原生输入/输出、命令、CPU预检seed及outputSHA验证通过，末3预热spread2.0656%，三测量spread1.3618%，各轮128请求成功、输入/输出均131072；三轮无>1秒ITL。测量输出1418.8986/1399.6175/1415.9052token/s，总吞吐2837.7973/2799.2351/2831.8104token/s，全部保留。与IV64-B1首个实例比较，中位输出1600.6062→1415.9052、中位总吞吐3201.2123→2831.8104（均-11.5394%）；mean TPOT中位38.3435→43.5334ms（+13.5353%），mean TTFT中位1663.5352→1642.6785ms（-1.2538%），P99 TPOT+13.6329%。两实例开始时model/tokenizer/engine/FG/FV/argv/safe_env相同，Plugin仅attention scalar文件不同。

该信号已通知，但当前只有每角色一个实例，C1后验源码、revert漂移和第二独立组尚未齐，不能视为完整有效回退或提前扩大。当前C1缩减P64K预热4/12通过，每轮16成功、输入1048576/输出2048；控制器1434728仍正常，继续原计划。阶段表现主要是客户端逐token时延上升，不冒充纯设备Decode归因。后续仅重大变化或完整结果再通知，避免重复播报首对差异。

15:02UTC只读跟进：唯一IV64控制器1434728/startticks1106675186仍运行，无当前终态失败。C1缩减P64K已完成11/12轮预热，逐轮原生validation、输出SHA及16条65536/128token长度复核通过，0失败；当前C1共23预热+3测量，仍只有P1K测量完成。未到长KV固定12轮准入或测量阶段，不据预热数据作回退判断。首对P1K信号上轮已通知，本轮保持安静；继续原六角色矩阵，未重启、改配置或扩大范围。

15:29UTC里程碑：IV64-C1于15:19:39完成两场景30轮，原生run-record SHA297f4cce33581c1b23d06bb396bbe6304ea997061e50f43d3e9947a9c2aa8493；全30轮raw/validation/output SHA、逐条长度、成功数及前后输入核验通过，service/model/tokenizer/四仓库前后完全一致，source-after SHA40089ebfba2fe1e1a848cdbabc1d2b43bc8ecc11ab7c59b63f92fa2a3d003d1f。缩减P65536/D128/C8/N16末3预热spread0.07316%，三测量spread0.05599%；输出8.611457/8.612865/8.608044token/s，总吞吐4417.6773/4418.3999/4415.9264token/s，全部保留。与B1首组中位比较，输出13.982846→8.611457、总吞吐7173.2001→4417.6773，均-38.4141%；mean TTFT28038.133→31473.412ms（+12.2522%），mean TPOT353.251→654.419ms（+85.2558%）。长KV的>1秒ITL在B1也有308/308/315次，C1为491/491/491次，不能直接套用先前P1K编译归因。TTFT/TPOT仅为客户端代理，本次未做设备阶段归因。

控制器自动进入IV64-R1(split0)，实例551211:1107955264于15:20:06启动，15:27:09开始原生benchmark；两rank实际M1–64准备各504miss、第二遍0miss，RNG/KV预算保留且hook移除，graph capture/16replay每rank与C8passed。该实例KV预算27672943411.2bytes/rank为其前后核验值，不以不可用block数作证明。当前未完成R1测量或第二独立组，首对P1K/P64K仅为回退信号，暂不扩大，也不外推缩减长KV结果至完整P64K/D1K/C64/N128。全部模型配置/prefixON/采样/gems-opt/MoE保持，继续原冻结矩阵。

15:59UTC只读跟进：唯一控制器1434728/startticks1106675186正常，无新终态失败。IV64-R1(split0) P1K已完成12轮预热，末3输出1590.1815/1581.4913/1602.9143token/s，spread1.3472%通过；当前完成2/3测量，输出1615.2876/1607.7886token/s，总吞吐3230.5752/3215.5771token/s，均保留。全部14条原生轮次128成功、0失败、逐条1024/1024、输入/输出均131072tokens，validation和输出SHA通过，两测量轮无>1秒ITL。第三轮、长KV、进程后验源码和第二独立组未齐，不从两轮窗口签发恢复/回退结论。原配置及矩阵继续，正常进度不重复通知。

16:29UTC跟进：IV64-R1(split0) P1K的三测量轮均完成并保留，输出1615.2876/1607.7886/1607.7220token/s，总吞吐3230.5752/3215.5771/3215.4441token/s，中位输出1607.7886、总3215.5771，测量spread0.47056%；相比B1输出中位暂为+0.4487%。全部15轮128成功、逐条1024/1024、输入/输出各131072、validation/output SHA通过，三测量轮无>1秒ITL。进程后验源码审计仍待整个R1结束，不能据此提前签发最终因果/验收结论。当前缩减P64K8/12轮预热有效，每轮16成功、逐条65536/128，0失败；长KV尚无测量，第二独立组尚未开始。控制器1434728身份一致、无新终态失败，继续原矩阵，配置不变；正常进度保持安静。

16:59UTC第一组闭环：IV64-R1于16:52:17完成30轮，run-record SHAb9a705332a921b820478d9e732065d3dbc67ddab4a1b6a8b8a77a1ab8a63564f；全30轮原生raw/validation/output SHA、逐条token长度与成功数、前后输入及service/model/tokenizer/四仓库一致性核验通过，source-after SHA06a15db228b04b3b21959eb57e8444ae6a6e623c64e08a5542d89694a7289a6d。缩减P64K末3预热spread0.75614%，测量spread0.16069%；三轮输出13.906772/13.923409/13.929145，总吞吐7134.1738/7142.7086/7145.6513token/s，中位输出13.923409、总7142.7086，mean TPOT中位353.4929ms。split0回切后，P1K输出中位相对B1+0.4487%，缩减P64K相对B1-0.4251%，均在冻结5%漂移范围内。该闭环支持先前split1性能回退信号，但只有一组独立0/1/0，不替代两组完整比较，不提前扩大。

控制器已进入IV64-B2，实例640539:1108511025于16:52:43启动、16:59:57开始benchmark；双rank真实M1–64准备各504miss、第二遍0miss，RNG/KV预算保留、hook移除，graph capture/16replay与C8passed，minimal SHAce042df61cba1c0891485a731866cb39fc53086bc37c2e0af798fd729a2a23de。冻结controller/plan/comparison/cache-policy SHA再次一致，原配置和其他服务不变。

17:29UTC只读跟进：IV64-B2完成P1K固定12轮预热，末3输出1597.8665/1595.9164/1612.7548token/s，重算spread1.0538%<=5%，准入通过。12轮逐条1024/1024、128请求成功、0失败、总输入/输出各131072，原生validation及output SHA复核通过；当前尚无完成测量轮。唯一控制器1434728/startticks1106675186正常，无新增终态失败。原冻结矩阵与全部模型配置保持，第一组闭环不重复通知，等待第二组完整测量与后验审计。

17:59UTC只读跟进：IV64-B2的P1K全部12预热+3测量完成并通过原生validation/output SHA与逐条1024/1024核验，每轮128成功、0失败、总输入/输出各131072tokens。三测量输出1590.8617/1598.0981/1599.9505token/s，总吞吐3181.7235/3196.1961/3199.9010token/s，全部保留；中位输出1598.0981、总3196.1961，测量spread0.56872%，三轮无>1秒ITL。当前缩减P64K7/12有效预热，每轮16成功、逐条65536/128、validation/output SHA通过，0测量。唯一控制器1434728身份正常，无新终态失败；整进程后验源码及C2/R2仍待完成，继续原计划和配置，正常进度不通知。

18:29UTC只读跟进：IV64-B2于18:25:14完成两场景30轮，run-record SHAebbf342b680e821e4a12fcd599467495099896d62aa0717107ed6a8d0c2351a8。全30轮raw/validation/output SHA、逐条长度/请求数和前后输入校验通过，service/model/tokenizer/四仓库前后完全一致，source-after SHAa03c76fd8e94b2f29882cba3b06d6dc25eb191ce6031f617d9b6150c09730233。缩减P64K末3预热spread0.07093%，三测量spread0.16398%；输出13.920424/13.943285/13.941115，总吞吐7141.1776/7152.9051/7151.7922token/s，全部保留，中位输出13.941115、总7151.7922。第二基线完成不替代C2/R2或完整比较。

控制器已自动进入IV64-C2(split1)，实例727635:1109068799于18:25:41启动；18:29检查尚无benchmark-started事件和完成性能轮，新实例采样覆盖/graph16/C8证据待后续核验，不沿用C1门禁。唯一控制器身份一致，无新终态失败，所有配置不变，正常进度仅写记录。

18:59UTC只读跟进：IV64-C2新实例两rank真实M1–64准备通过，首次各504miss、第二遍0miss，RNG/KV预算保留、hook移除；graph capture/至少16replay每rank及C8passed，minimal SHAddeedb3c63c15aafca4ebe398701e674f1f4f67183e805af9ed5cc2a9fd50601。18:32:49开始benchmark，当前P1K10/12预热完成，每轮128成功、0失败、逐条1024/1024、总输入/输出各131072，原生validation及output SHA通过。未完成固定12轮准入，0测量，不能用预热作第二组性能结论。唯一控制器1434728身份未变，无新终态失败，原模型配置/prefixON不变，正常进度保持安静。

19:29UTC只读跟进：IV64-C2的P1K完成固定12预热及全3测量，末3预热spread2.20418%通过、测量spread1.80823%。三轮输出1426.5089/1419.2640/1400.8454token/s，总吞吐2853.0179/2838.5280/2801.6909token/s，全部保留；中位输出1419.2640、总2838.5280。15轮原生validation/output SHA、逐条1024/1024及128成功/0失败核验通过，三测量轮无>1秒ITL。当前缩减P64K3/12有效预热，每轮16成功、逐条65536/128，0测量；C2全进程后验源码和R2尚待完成，不提前签发完整回退或扩大范围。控制器1434728身份一致，无新终态失败，配置不变，正常进度保持安静。

19:59UTC只读跟进：IV64-C2缩减P64K已完成10/12轮有效预热，每轮16请求成功、0失败、逐条65536/128、输入1048576/输出2048，全部原生validation/output SHA通过。尚未完成固定12轮稳态准入、长KV0测量；P1K三测量原始SHA再次复核一致。唯一控制器1434728/startticks1106675186正常，无新终态失败，C2全进程后验源码及R2仍待完成；继续冻结计划，配置不变，正常进度不重复通知。

20:29UTC只读跟进：IV64-C2于20:23:43完整结束30轮，run-record SHA7b5dcdf25c65e9e5ec794076056b0d88cfcd57c6f2b6fd8d06d70e60747ec53c。全30轮raw/validation/output SHA、逐条token长度和成功数、前后输入及service/model/tokenizer/四仓库一致性核验通过，source-after SHAb62f13b3754fc743ac24e507c276718ec6aeafc8ba6849a2e4e311d7c7f5ecfe。缩减P64K末3预热spread0.012886%，三测量spread0.053698%；三轮输出8.619452/8.614824/8.617093，总吞吐4421.7787/4419.4049/4420.5685token/s，全部保留，中位输出8.617093、总4420.5685，mean TPOT中位653.8810ms。第二候选完成但R2未齐，不替代最终独立回退和漂移门禁，不提前扩大。

控制器已启动最终回退组IV64-R2(split0)，实例814640:1109779601于20:24:09启动；20:29暂无该实例coverage/graph/C8完整回执或benchmark-started事件，不复用旧实例门禁。唯一controller1434728身份一致，无新终态失败，所有配置不变，正常进度仅记录。

20:59UTC只读跟进：IV64-R2两rank真实M1–64准备、首次各504miss/第二遍0miss、RNG/KV预算保留、hook移除全部通过，graph capture/16replay每rank和C8passed，minimal SHA7890216daaf7482010da24c4fef4b62a2ed0e65a92995f104120d8d4bc6ea27c。20:31:13开始原生benchmark，P1K固定12预热完成且末3spread2.25770%<=5%通过；全部12轮128成功、0失败、逐条1024/1024、总输入/输出各131072，validation/output SHA通过。尚无完成测量轮，不以预热签发最终回退。唯一controller1434728身份一致、无当前终态失败；继续原矩阵，全部结束后恢复原split1/helper并重新graph16/C8，正常进度保持安静。

21:29UTC只读跟进：最终回退IV64-R2的P1K三测量全部完成并保留，输出1620.2143/1587.0441/1592.4051token/s，总吞吐3240.4286/3174.0882/3184.8102token/s，中位输出1592.4051、总3184.8102，测量spread2.08302%。15轮128成功、0失败、逐条1024/1024、输入/输出各131072，原生validation/output SHA复核通过，三测量轮无>1秒ITL。当前缩减P64K7/12有效预热，每轮16成功、逐条65536/128、输入1048576/输出2048，0测量。最终R2全进程后验源码/长KV、冻结聚合比较及split1原helper恢复验证尚未齐，保持最终判断待定。控制器1434728身份一致，无当前终态失败，全部配置不变，正常进度不通知。

22:02UTC终态：六个独立实例均完整结束，两场景每实例12预热+3测量，共180轮（144预热+36测量）全部保留。独立重验所有raw/validation/output SHA、逐条token长度、成功数及六实例前后service/model/tokenizer/四仓库一致性通过；冻结比较器结果failed/退出1仅源于性能门槛，不是证据不完整。comparison SHA c2e362f2101cfa8945bb74c14c8fc1171926ab6b00f2a12b9104465c34807d94，completion SHA dc4d1184d603376b4659bc4898f42138d4722ae35cd8c325f1f04e02af95985e。聚合按每进程三轮中位数、再取两个独立进程中位数，不声称总体请求P99或统计置信区间。

| 场景与指标 | split0 baseline | split1 candidate | split0 revert | candidate变化 |
|---|---:|---:|---:|---:|
| P1K/D1K/C64/N128 输出token/s |1599.35|1417.58|1600.10|-11.37%|
| 同场景 总token/s |3198.70|2835.17|3200.19|-11.37%|
| 同场景 mean TTFT ms |1661.48|1646.01|1670.06|-0.93%|
| 同场景 mean TPOT ms |38.379|43.494|38.351|+13.33%|
| P64K/D128/C8/N16 输出token/s |13.96198|8.61427|13.95042|-38.30%|
| 同场景 总token/s |7162.50|4419.12|7156.57|-38.30%|
| 同场景 mean TTFT ms |28216.51|31463.17|28348.41|+11.51%|
| 同场景 mean TPOT ms |353.085|654.150|352.520|+85.27%|

主输出吞吐与副总吞吐均越过3%回退限，TPOT等守护超过10%。baseline→revert输出聚合漂移P1K+0.04656%、缩减P64K-0.08280%，稳定性与重复门禁均合格；两组证明回退可复现。TTFT/TPOT包含排队、调度与通信，不能将这些比例直接当作纯设备prefill/decode耗时；具体kernel瓶颈尚无trace。完整P64K/D1K/C64/N128未执行，本轮不属于全项目正式验收，没有跨Host复用GPQA gate。

21:56:56恢复原Plugin split1与原observer，22:00:25恢复回执passed；22:02独立运行时复核当前实例902026:1110336333、prefix cache ON、health200，attention SHA2eaec0be、原helper SHAcfa7553e、MoE SHAbbc2edded完全一致，graph capture/16replay每rank及C8passed。restore SHA34327048e1548e91b9c8436d30148614f2dcc2f96f75b3b8ce07b4617f78cb07，minimal SHA1d37d63dac408507a493363b736a03e70f7041f84d3da55274fd8096dc43f683；控制器已退出，其他服务未动。ERQA45.73仍绑定其原始mx104测量实例，不伪造重启实例新分数或GPQA gate。

规划复盘env-001-split-comparison-review-04：当前是split1正确性措施的性能代价，不是相对未优化anchor的累计收益。下一步优先为原始长KV工作负载冻结新的同设备targeted扩展计划、native输入预检与资源/时限；扩大尚未启动，不能复用缩减基线数字。随后用独立profiling区分attention设备开销与mixed干扰，任何多split数值修复另立实验并要求固定前缀回放、graph/C8及当前Host GPQA>=64。初始targeted全部终态，按指令停用本轮监控，保留恢复后的split1服务。
