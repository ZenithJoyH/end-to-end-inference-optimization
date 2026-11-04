# acc-023 当前重启主线实例 C32 全量 GPQA

本次8题对照16/16完整、独立CPU审计及300成员回读通过，原driver和CPUwatch2均退出。xhigh5/8截断，medium0/8，8题medium输出均更少；仅限该选定单次C1范围，不是完整GPQA精度通过。原GPQA174/198仍未达88%，ERQA252/400终态保留；同BF168010健康空闲，未重启、全量复测或改默认策略。小时监控转终态后只读整体跟踪，不再派发测试。

当前终态：ERQA400题已完成，原生252/400＝63.00%（无阈值score-only），完整证据及独立CPU审计通过；GPQA重审有效174/198未达88%，原incomplete保留。8010同实例健康空闲。GPQA低分/底层原因未闭环，按用户要求保留小时只读跟踪，不自动复测。下方早期“运行中/未启动”均为历史，详细收尾见文末。

当前（2026-10-31）：JSON聊天审计映射已修复，已有GPQA重审有效但174/198未达88%；原incomplete保留。沿用同一8010的ERQA400/C32已于08:07:56启动，完整wire/真实ID进展与终态审计持续保存；不重启、不重跑GPQA。下方含旧快照，最新分析和接续见文末。

## clone 注册修复与独立验证

修复封存完成：implementation-manifest.json共89成员，逐项回读通过，SHAa498e24f73c0d57167a4f8c80c729aaf3961355af454f603abb9a49bba288f2a。完整CPU source probe前后仅Gems注册文件及两测试对应Git状态变化；Plugin/Mamba修复、FGVLLM、vLLM、BF16/model metadata/tokenizer及权重stat一致，用户启动脚本SHA不变。当前8010无监听，无第二次启动或新模型请求。下一步需用户允许再次通过同一脚本单次启动，完成新候选10请求最小回归后才续原C32全量GPQA/ERQA。

两处同根注册已应用：FlagGems `__init__.py` SHA2bdd23be167ade05d528cec2121bc903c6d96bf7f53d91b8e1d958a5aa2be35f，额外分发为nested pair且只作用于Autograd+当前backend key；thead实际为AutogradCUDA。clone/max_pool3d数值实现及registrar未改，原index/randn等修复保留。回归追加到已有tests/test_clone.py与test_max_pool3d.py；三文件Ruff format/check及git diff --check通过。

CPU-registration-002使用真实GeneralOpRegistrar、only_enable函数体与torch.library，metadata设备桩固定CUDA、独立子进程CUDA_VISIBLE_DEVICES空且确认未初始化CUDA；9项通过。旧clone配置重现“CUDA和全局Autograd先注册成功→函数误作key失败→CPU RNG clone进入错误后端”。旧max_pool3d重现注册错误，但本Torch仍使用CPU原生值/梯度路径；首轮要求它也CPU误路由的错误测试预期已修正，首轮失败报告保留。nested-global和device-scoped均在当前Torch2.10保持CPU梯度正常，不能声称全局fallthrough已实证断链；限定设备是收窄影响范围。

物理8实际验证已通过：8个float32/BF16 clone（连续/转置/空输入）与max_pool3d小形状用例，值及梯度与启用注册前的原生同设备独立参考精确一致；实际公开torch调用各命中原始FlagGems wrapper，函数对象/源SHA/Tensor元数据旁录，无数学替换。clone两种dtype各capture一次、两次replay前更换输入并污染固定输出，均返回新正确值且地址不变；CPU RNG未进入Gems，退出context后dispatch恢复。证据device-registration-001/REPORT.json SHAbc968f51f2f8b95ff02c5f19591bb4faae824e8dddbfa25bc12c29515da4967a；18成员manifest独立回读通过。只用了物理8，没有模型请求、服务动作或性能测量。新增的两个CPU注册测试随后通过原仓库pytest入口（2 passed），不是只检查测试语法。仍不能替代模型最小回归或正式精度。

独立失败终态审计terminal-audit.json SHA73b431740f16664de27ae4010762c23bea7ed3a9f74e184fdc47fb4bc400ec80：R2原23成员清单全部匹配、1HTTP500/0成功/9未发、总1次用户原脚本启动、父0请求、历史source-before/after-error逐字一致，原3进程全部退出、8010无监听。原driver.log在freeze时为空，退出后1752-byte尾部另存审计补充，不改原清单。没有成功FINAL_SUMMARY/FINISHED，不伪造。

客户端次生event(kind, **fields)参数冲突已仅在未来副本修正；使用真实冻结common源码AST函数的CPU验证确认STOP、事件schema及首错不覆盖，原common SHA50ea8f24保持不变。新副本client-future-001/common.py SHA94c4464ce489c269d6eaf1f5f775acdf2ac54dbc9801df3c872ee5e22ea66e76，仅改两个标识符，未加载执行推理或部署新的队列。

以下保留各阶段当时的状态；当前结论以上述修复封存为准。

## 本次用户脚本验证失败：CPU RNG clone 被错误分发到 PPU

2026-10-29 22:52:23（epoch1793285543.2135785），同实例续验的第0条真实请求返回完整HTTP500（153 bytes），8010随后自然退出。总计仅原脚本启动1次、实际请求1条/成功0条、剩余9条未派发；GPQA/ERQA续验未启动。原Mamba规格断言未在本次出现，但不能因此宣称模型回归已通过。

本次真实栈为文本embedding触发 `get_masked_input_and_mask` 首次Dynamo/AOT编译，`torch._dynamo.utils.preserve_rng_state` 复制CPU RNG ByteTensor，误入 `/opt/FlagGems/src/flag_gems/ops/clone.py:_launch_copy`，将cpu传入CUDA device guard后抛 `Expected a cuda device, but got: cpu`。不是模型输入放错设备，也不是新的Mamba张量错误。注册源码核验发现 `_FULL_CONFIG` 的clone额外dispatch配置缺少外层tuple，registrar将字符串Autograd解释成复用Gems clone；第二项函数又作为dispatch key传入。实际CPU误路由有完整栈证明，注册部分成功后失败的具体过程待CPU复现，不声称日志已保存该注册异常。

证据在 `G/repair-validation-001/validation-continued-001`：FIRST_ANOMALY、完整request/response/header、DRIVER_ERROR、service.log、source-after-error、terminal-evidence-001与manifest原件保留；没有伪造FINISHED。验证客户端另有event参数名重复的次生TypeError，首个HTTP500在此前已保存；仅修订未来客户端草案，不覆盖冻结common。修复计划：只改FlagGems _FULL_CONFIG中clone与max_pool3d两个同根的flat pair为nested pair，并使用现有后端键拼接惯例限定AutogradCUDA（thead）；保留real合法multi-pair和其他配置，不改数值kernel、黑名单或启动参数。两处原生Skipped registering operator warning也在冻结日志中找到。执行前命令G/commands/apply_clone_registration.py冻结，源码与测试备份存G/diagnostics/clone-registration-fix-001/backup；先核8010空闲、原脚本SHA及source-after-error完全一致，再应用。适用算子规范A1/A2/B1/B2/B3/B5/C2/D1/E1/E3/E6/F3/F4；此为ATen注册修复，CPU注册/梯度与目标设备实际路径分别验证，不把CPU结果当模型通过。下一步仅修复注册和CPU分发回归；本次单次启动授权已消耗，不再次启动服务，不发送额外推理。

## 启动已完成；验证客户端日志门禁修正后续验

2026-10-29 22:41:18（epoch1793284878.7806406）原验证driver在发送任何请求前因 `missing group initialization: []` 退出。首错、source-after-error及manifest已冻结，原目录不改；当前API Host991767/start600047166/argvSHAc1b658b05137910a59f347c6fbb9048146d22f1274886b324b761803a9f30fbc健康，来自唯一用户脚本启动。两类capture各7/7，源码前后完全相等。

只读核验确认这是验证门禁不适用：Plugin model_runner.py:305 使用 `init_logger(__name__)` 的 `vllm_fl.worker.model_runner` logger；native logger.py:63–68默认仅配置`vllm` INFO，209–214不为调用者配置handler/level，兄弟命名空间继承root WARNING。精确API的logging环境无覆盖，其他Plugin worker INFO同样缺失。worker.py:772无参数调用 initialize_kv_cache，mode=align且is_profiling=False，model_runner.py:7812–7822预分组/校验为强制代码路径。缺INFO不能证明未初始化，也不能伪造独立8rank日志。

沿用同一实例与尚未消耗的原10请求预算，在R/validation-continued-001另存验证结果。唯一验证控制器 `commands/validate_existing.py` SHA08d5a8c40bcdab36fa80c5a875c3707393534bfe7938b157ef94e75d07a58d8b，不包含服务启动/停止代码；stage脚本 `G/commands/stage-validation-continuation.py` 执行前保存。严格要求原driver已退出、原0请求、原manifest全部匹配、当前精确API/源/原脚本SHA绑定。门禁改为可核验的强制源码路径、成功TP8启动、真实prefix行为和10响应/capture/replay/C8；独立8rank初始化trace记null，未新增模型埋点。通过后才续原C32正式范围。

## 新授权：使用用户原启动脚本验证

2026-10-29用户明确“可以启动，但是需要使用我的模型启动服务脚本”。本次授权覆盖单次启动空闲8010及冻结10请求minimal-regression，通过后续原C32 GPQA/ERQA。唯一启动命令将为 `docker exec qwen3.8-flash-opt-ppu07-20261015 bash /mnt/nfs/users/jinghao/qwen3.8-flash/start-model.sh`；原脚本内容、nohup方式和全部环境/参数不变。它固定写 `/mnt/nfs/users/jinghao/qwen3.8-flash/service.log`，执行前复制旧日志留证；minimal和后续formal绑定新日志inode/byte边界。旧R/launch-service.sh不再执行，准备阶段controller/common/PREPARED/frozen保留pre-user-script副本后改为直接调用原脚本。不运行旧prepare，不重启/停止任何服务，不访问8035，保留BF16/现有修复与prefix cache。

本地inventory定位PPU-07；首次沙箱内Ansible RPC启动失败，沙箱外限定同Host的connectivity-check通过。当前8010无监听、R无DRIVER启动标记。执行前修改脚本 `G/commands/user-script-launch-adaptation.py` 仅调整验证编排及冻结证据，controller预定SHA 72644a8a4a7e2f4b476a2c3ac7d24afeb72f64c4c1e755e5decf2c3947fe8fdc；仍为10请求、0重试、2C1→8C8，未执行前不记通过。

原脚本已唯一执行：epoch1793284645.082113（2026-10-29 22:37:25北京时间），返回码0，原脚本SHA fc456e30929dc4cb7942405a59d083910e13acffa856c465964245c0aea61890；旧日志备份R/service-log-before-user-launch.log。唯一driver Host991068/start600047005/argvSHA6db0dc21be76605fc15bfc81c8094a07aa98790c5d239dfc1cbc0a7cfe833923。新日志device41/inode27006868286；当前仅加载，READY/请求/正式分数未产生。源预检查、设备8–15空闲检查与冻结SHA均由唯一controller通过，未停止/重启任何现存服务。后续只监控该进程，不重复launch。

## 修复实施（用户授权完整修复）

当前交付：代码、23项CPU与物理8设备复制/两次graph replay均通过；模型级验证仍待授权。自动审批拒绝了单次启动空闲8010并执行10请求的命令，理由为“当前可信用户指令仅授权修复本身，未明确授权此次启动与推理验证”。该命令未执行；只读复核R/DRIVER_LAUNCH不存在且8010无监听，没有绕过重试。待用户明确允许启动/最小验证后再继续，不能宣称正式故障已完全闭环。最终source-prelaunch-final与source-before相等，和事故源相比仅helper/runner/test三文件变化，vLLM、Gems、FGVLLM全树不变。implementation-summary/manifest已封存，manifest SHAa2d8971fc59aa8a035718aa4a232b9a38483a8583bf48b5f75281c69c58615bc。R最终controller SHA68e06a78c30d8e403b8aaabaf565275b739dbc9ee27570d3c9073b9c34a7421f，审查补上probe冻结、设备来源绑定、实际unpadded8 FULL门禁和失败source冻结；启动前准备原件保留。

2026-10-29继续同一issue。当前8010已无监听。修复归属Plugin worker兼容层，vLLM安装源码保持只读：按真实MambaSpec划分同构组，为每组绑定模型公开get_mamba_state_copy_funcs(type)及独立请求状态，复用原生preprocess/复制kernel；同构路径保持原生，异构spec-decode在任何分配/执行前明确拒绝（当前模型本已禁止spec-decode）。缓存重建时重建所有组，正式KV初始化时预分配。不能删除原生规格断言或退回关闭prefix来宣称修复。

工程条款A1/A3/A4、B4、C1/C4、E1–E4、F1–F3/F5/F7；无全局monkey patch、无新开关或数值kernel。验证顺序为CPU真实元数据与复制规划/独立参考、目标设备复制及graph边界、模型capture/replay和prefix命中单请求/C8，再新目录绑定原C32正式范围。原失败产物全部保留。脚本先存G/commands，新增证据G/diagnostics/mamba-fix-001；生产变更前备份原runner和完整diff，源码漂移则停止。保持BF16及现有修复，不访问8035、不提交推送。

已部署worker/mamba_buffers.py与runner两处接线，真实KV初始化提前分配并在重建时失效。helper SHAd9a05fef68331f425bf60f3683c7b9da7956d2f3f55fe621a69bdf096a07816c，runner SHAc9fe7494aad2ae7d07d12e79be6812a5c68bf1be4d847d1299ef82f386f4bb75。23项CPU单测通过；首次直接导入因加速器版vLLM自动查设备失败，原件cpu-tests.log/002保留，003使用CPU tensor及仅导入期capability stub，原生copy规划不替换，仅memcpy由CPU memmove代替，不能冒充设备。新helper/test Ruff通过；runner基线已有两组I001保持相同，排除I001的完整检查与git diff --check通过，未做无关全文件格式化。

物理8的device-copy-001通过：真实GDN/PLE BF16/FP32、400-token逻辑块、页内padding、完整storage字节参考均一致；原生copy kernel真实capture+2次replay，分别更新源并重置目标哨兵，地址稳定。它仅证明单卡状态复制，不代表模型TP8图或正式精度。

下一步使用G/commands/repair_control.py（执行前落盘）准备G/repair-validation-001。仅单次启动当前空闲8010；从当前start-model.sh冻结相同环境/argv，前台exec与独立日志是唯一启动封装差异，不改用户脚本。保持prefix enabled/BF16/image16/encoder graph=false。固定10请求、0重试：2C1为中性长prefix+原doc2（超过400-token边界、需真实prefix命中及完整token重复一致），随后8C8长短交替doc2；max2048、seed1234及原采样不变。两类capture各7/7、至少2native FULL dispatch、8rank分组初始化与源前后绑定。首错冻结，不自动恢复服务。最小通过后才续原C32正式范围，当前无新gate。

## 查因结果：prefix cache的align路径未兼容GDN与PLE异构状态

现场调用栈、当前源码及CPU元数据验证相互印证：startup原件18:10:28明确记录prefix cache开启后默认none→align；18:55:12真实execute_model调用Plugin `_get_mamba_bufs()`，进入vLLM0.24 `MambaBuffers.create → MambaCopyBuffers.create → get_mamba_groups`。后者要求所有MambaSpec对象与第一个完全相等，模型合法存在的GDN与PLE规格不满足此假设。

| 状态 | shape（TP8、非spec-decode、默认SD布局，CPU元数据重建） | dtype | 类型 |
|---|---|---|---|
| GDN | conv(3,1280) + recurrent(6,128,128) | BF16 + FP32 | GDN_ATTN |
| PLE | conv(9,10240) | BF16 | SHORT_CONV |

不是故障worker内存张量转储；卷积维顺序随布局变化，不影响两类规格不相等。CPU抽取当前真实shape/dtype计算、MambaSpec字段/dataclass比较及get_mamba_groups：GDN单组、PLE单组、相同GDN两组通过，GDN+PLE失败，统一page padding仍失败。配置选择函数也验证prefix=false→none、prefix=true→align。未导入Torch/Triton或执行设备。

模型已有按type的`get_mamba_state_copy_funcs(mamba_types)`，GDN两份copy函数、SHORT_CONV一份；当前runner仍调用旧单一`get_mamba_state_copy_func()`及统一MambaBuffers。仅删断言不能视作修复，还须核对各group的copy函数、状态索引和preprocess，涉及spec-decode时还须postprocess；本轮spec-decode关闭。修复应在框架compat/runner层接通异构group/type处理，不修改FlagGems数值kernel或伪造相同spec。

历史比对：当前_get_mamba_bufs、模型copy funcs及PLE/GDN shape方法与eng074升级前完整备份AST相等；vLLM mamba_utils SHA934e9d2a919d71badc3beb7e474b1508483f6298a171e67ed153b3bb3c0e4a49与旧acc021有效实例一致。以前prefix cache disabled绕过align路径，未覆盖已有兼容缺口；不能将它归因本次主线更新改坏这些函数，也不是BF16／MoE计算精度证据。C32不参与此规格断言。

短期规避方向为恢复`--no-enable-prefix-caching`，避开align；本轮只分析，没有更改启动文件或服务，也未验证新三库组合在关闭prefix后的推理。长期保留prefix须实现上述框架兼容，补小范围数值、capture/replay、单请求/C8及全量精度。状态mechanism-reproduced/fix-not-implemented，尚未完成修复后的设备与正式精度闭环。

证据G/diagnostics/mamba-static-analysis-001/report.json SHA759a37bd09ed024f4f476eb77f346d6bcdcbb08855f0af6b5c5bdb4364a298de；historical-source-comparison.json、8份源码快照均仅存目标机器；manifest-002 SHA5496f0ce39c47823e976e0fbf206cbfcfe0800ec88d77d2d77796d1e81ba0890，首版清单逐项回读通过。0模型请求／GPU／重启／生产源码修改／8035／提交推送。以下保留原故障及执行前记录。

## 故障终态：incomplete，无有效精度分数

## 后续只读定位计划（用户授权查因）

继续同一issue，不创建复测或新实验。已完整读取本地accuracy-diagnosis，连接限定PPU-07通过。现场日志确认prefix cache开启后MambaModelConfig默认选择align；Plugin worker在实际execute_model首批调用_get_mamba_bufs，旧vLLM get_mamba_groups要求所有MambaSpec对象完整相等。模型同时包含GDN双状态与PLE单短卷积状态，已有按type提供copy funcs的新模型接口，当前worker仍调单一旧get_mamba_state_copy_func。

只在CPU隔离命名空间抽取当前实际配置选择、shape/dtype计算及get_mamba_groups函数，验证同类组与异类组、统一page padding是否影响断言；dtype与enum用元数据stub，明确不冒充运行中KVCacheConfig对象或GPU测试。脚本本地/private/tmp/acc023_mamba_static_diagnosis.py SHAa930e0a69cb4ab212baaa3f4eaa388eb183f312cc1baad7ebaf295b9709a46cf，先保存G/commands/mamba_static_diagnosis.py并核SHA，在目标容器env-u PYTHONPATH/CUDA_VISIBLE_DEVICES空的python-B执行；证据仅写G/diagnostics/mamba-static-analysis-001。生产三库、服务、采样和cache保持只读，不重启／新模型请求／8035／提交推送。

追加只读闭合核验：故障后CPU source probe与source-before完全一致，source-after-failure SHA7b247de88554d90e4721a9534cb04883e0c3a10d83b4432f633fa93abec84043；API3528090/controller756726/native客户端757109均已退出，ERQA未开始。新增post-freeze-verification与manifest-002 SHA465d43557df0d977f27e2b7ddcb2260cfb28220cc43142081c106d085ead769c保留首版incident及manifest原件，未改原故障记录。仍缺逐层现场与单变量根因证明。

首批GPQA请求触发服务退出。北京时间2026-10-29 18:55:12，Worker TP0（随后其他rank相同）在Plugin model_runner.execute_model→_get_mamba_bufs→vLLM MambaBuffers.create→MambaCopyBuffers.create→get_mamba_groups的line233断言`all(mamba_specs[0] == spec for spec in mamba_specs)`失败；API3528090自然退出，8010无监听，非Agent停止。当前只能确认异常落在Mamba/KV规格兼容路径，不能直接归因FlagGems数值／BF16／MoE，prefix cache开启是待查边界而非已证根因。

原生评测退出code1，原始results为0.0，但198唯一doc对应396 filter行全部为TIMEOUT占位；日志真实出现API连接拒绝，不能把0/198解释成模型答错或正常精度下降，也不能称198真实HTTP成功。controller756726已退出，原FINAL_SUMMARY/FINISHED未生成，不伪造成功终态；CLIENT_ERROR-v2、原79成员manifest及terminal-evidence原件齐全并独立核SHA。ERQA未FORMAL_STARTED。原生runner的既有错误处理自然收集结束，没有Agent重试或新请求。

应用本地inference-accuracy-diagnosis，仅现有证据冻结，issue acc023-execution-mamba-spec-assert。G/diagnostics/incident-001含完整service原件、新byte/inode窗口、incident.json（SHA048805f0a937a06ca2d79b977f98e26d66d3328ed90bc7a3ae88dc9cc60da3ec）及独立清单。样本SHA272e992b3165f7e40380053a7e6968a6015eecb9381ae5452c7f54eea486cc36。无逐层张量／独立worker函数对象trace或可重复单变量验证，根因尚未确认。监控qwen-ppu07-c32-gpqa-erqa已产品确认deleted；没有重启、恢复、改源码、重跑或8035／提交推送。当前任务因服务故障未完成两项精度，等待用户后续方向。下文启动快照为历史。

2026-10-29用户授权使用已经手工重启的8010，GPQA198与ERQA400各一轮C32串行，总cap32。使用本地accuracy formal-gate，bundle SHA1ed06a57f1f6e1ef39fb7fd872f579122b098a18f0255ade0a1160d6432c2b66，覆盖eng073环境收敛、eng074/075三库更新。不重启服务／访问8035／提交推送／改源码或额外smoke，不启用encoder graph。

当前API Host3528090/start598444161/argvSHAc1b658b05137910a59f347c6fbb9048146d22f1274886b324b761803a9f30fbc；health200、running/waiting/KV/preemptions均0。BF16/TP8物理8–15、image16/video1、FULL_AND_PIECEWISE；用户本轮开启prefix cache，无PYTHONPATH及pin047注入。按实际配置运行，精度结论不兼作性能准入。三库HEAD40f992dc/04dafa8b/31a2705d，不能复用eng072旧实例minimal或旧gate。保存当前startup原生日志，不虚称当前worker函数对象trace／逐层现场或已观察两次replay。

固定task gpqa_diamond_generative_cot/limit0/198doc0..197/C32/strict exact_match阈值.88。原采样T1/top_p.95/top_k20/min_p0/presence0/repetition1/max60000、evaluatorseed42、原API默认seed/stop，完整token/prompt。API最多3总尝试/7200s，整项不重跑。规定flageval-llmeval:v1新CPU evaluator、新UUID响应cache；两次provenance一致、维护formal wrapper及原始llmrun SHA核验后preflight/一轮formal。普通错答/空final/length保留自然收集，真实HTTP超时与None占位分开。低分保留诊断，若同源健康空闲仍继续用户指定ERQA；源／实例／执行缺证则不启动下一项。

G=/mnt/nfs/users/jinghao/qwen3.8-flash/20261015-qwen38-flash-next-ppu07-container/accuracy/acc-023-full-gpqa-ppu07-c32-main-20261029；唯一commands/suite.py，复用旧串行编排仅重绑定新实例、当前源码、并发与产物路径，移除所有旧minimal继承断言。执行前保存脚本与SHA、完整bundle及STAGED；prepare与launch各一次。完整原生样本/results/run-record/gate/source前后/终态manifest保存在G，后台监控只读跟进。状态preparing，尚无新分数。

## 预检完成／启动前冻结

controller SHA1d98ff72c6e6360c1fbf712b7acd4de26ff388275201197ea4ec713bb641d2e4，传输包SHA44d9fccecfaa42a257e8f0e58d2f194675dbe128159d6911ca5378faa1ed147d，源码／runner全部在G/bundle及commands保留。准备零模型请求，两套CPU evaluator与原生数据／16图payload预检通过。GPQA两次provenance逐字相等SHA2f0731329362d0404aeb611ee49f23348792fc0a32fb33bd031a8f5e2c7abd3c；本轮工具版本不同于旧记录，使用本轮新来源，不改旧SHA。dataset仍167548b0完整198。

GPQA PREPARED SHA f62ef53bb49f76d5b04dfbf3203dfa157b2ba252a2e94c388e3a635778a972a2，55冻结文件清单SHA9c5e924b6bb52caa4b6e7bd61e63cb7a0fd4d03f26124bda3bca93883614d058；contract SHAbcafbd7c2e11852306fcf25703aee12d18356b6287eff8ef65f7ae0ec7c506ef；config SHA68808b9787a1bea2f312c0caa88008237f8174ff61b99a5a363b401c31af0705。prepare.log闭合后更新启动前冻结SHA，原准备阶段frozen-inputs-prepare-phase.json保留；无采样／模型配置／数据修改或推理重跑。

监控qwen-ppu07-c32-gpqa-erqa已产品确认ACTIVE，每30分钟只读检查，正常推进静默；终态独立审计后删除。只按以下唯一命令launch一次：`python3 -B G/commands/suite.py --mode launch`，controller自然GPQA→ERQA，禁止手动再run。未运行额外smoke；当前startup两类capture各7/7原件已保存，replay不虚报。无性能授权。

## 唯一队列已启动

单次launch返回Host756726/start598711999/argvSHA0f0bc4ca963d8fe71934a4b2116edbf478e981bbbd002f581449396cf8f7ccc3；独立/proc核同一身份。FORMAL_STARTED epoch1793271294.9491274，GPQA原生attempt1/1，run UUID fe84ef04093b46d18f1fa40ac594e071，实际命令num_concurrent32/全198/seed42/独立SQLite。原生离线Hub提示后使用已核验本地缓存属于预期，不视为HTTP模型故障。当前分数尚未产生，ERQA等待原队列串行推进，无手动二次launch。

### 新一轮原脚本验证授权

用户在明确“再用同一脚本启动8010一次，先完成10条最小回归，通过后继续C32 GPQA/ERQA”的问题后回复“允许”。新验证目录为 `acc-023.../repair-validation-002`，旧 `repair-validation-001` 与 continuation 首错完整保留。唯一新启动必须直接调用 `/mnt/nfs/users/jinghao/qwen3.8-flash/start-model.sh`（SHA `fc456e30929dc4cb7942405a59d083910e13acffa856c465964245c0aea61890`）；不修改脚本、不额外重启、不访问8035及物理0–7、不启用encoder graph、不提交推送。先2C1→8C8，独立CPU审计通过后串行GPQA198/ERQA400各C32；使用全新结果目录与响应cache。当前仅准备，尚未新启动或发模型请求。

新远端命令将先保存于 G0/commands/{stage_validation_v3.py,repair_control_v3.py,minimal_audit_v3.py}，再执行仅文件准备。新 R3 使用原脚本期望完整 argv SHA `c1b658b05137910a59f347c6fbb9048146d22f1274886b324b761803a9f30fbc`；运行前核8010空闲及物理8–15无计算进程。控制器只单次启动，不带stop或恢复；所有请求、捕获和源证据冻结后才允许原正式续跑。

R3已完成零推理准备：controller SHA `6556bff44cb3a6ed90ac39d6e9cf85b21c12340580dc4536eb83f872fa97d0b6`；CPU audit SHA `b8906092925a5658840c009e6e98dcecfe00d9a479f3cbf04febf3348a214855`；PREPARED SHA `6c6994cca7fa82c615054a5a6580d2e5048c145e397aced1791fb4f06eed47ab`；source-before与已验证clone修复source-after逐字相同，SHA `668a4bcffc0b63ffc4bc34fb47009d772a0b096604be288abb148f2f9312064b`。新请求ID与旧case分离，payload不变。监控 `qwen-ppu07-c32` 已创建，每30分钟只读，正常推进静默。唯一launch命令已下发，后续只跟踪原进程，不重复执行。

单次启动已执行：2026-10-29 23:37:18（Asia/Shanghai，epoch1793288238.2139933），原脚本返回0。唯一controller Host2287303/start600406320/argvSHA359584b119dddb28d5254d2a369140d8abfc02b49237b0456f16ac792db3ca9d；当前等待加载/capture/READY，未到新正式阶段。原service.log已在新R下备份后由用户脚本按原行为写入。

23:39:46本轮READY：新API Host2288060/start600406479/argvSHA c1b658b05137910a59f347c6fbb9048146d22f1274886b324b761803a9f30fbc，PIECEWISE与FULL各7/7。实际初始化独立逐rank trace仍为null，必经源码绑定和后续prefix请求证据另核；固定第1条已派发，尚不能计完成。


### 23:43 prefix命中护栏失败与CPU续验准备

R3原controller在2026-10-29 23:43:17因真实prefix hit为0退出；两条C1完整HTTP200，prompt1620/output546、goldB，完整输入和输出token分别一致，0C8/0formal。终态CPU审计30项判incomplete，report SHA43bfda47d37caa91e866f217aef9347810596417c4860ece525c472c6149c496；保留DRIVER_ERROR和原manifest，无FINISHED。当前同API仍健康空闲，未再次启动。

源码定位QSA compressed页统一可能使实际逻辑cache块从400扩到6400，原1620输入未覆盖；先用实际源码AST复算并核日志，不改运行中源码。CPU-only准备命令G0/commands/prepare-prefix-boundary.py（SHA f54b5c971593e08f80715b5a41217ca510109c9499cf24db6b4b598403235dbf），只读本轮两响应与原tokenizer，不调用API/设备，另存R3/diagnostics/prefix-hit-001/tokenizer-plan-001。准备6500-token相同C1两条+8C8、0新启动方案；总预算将从10变12，尚未授权/执行，不能静默扩负载。

用户最新要求每小时汇报；monitor qwen-ppu07-c32 已更新ACTIVE每小时，正常无变化也汇报，诊断尚未结束不因本次guard失败自动停报。

CPU实际AST重建通过：script SHA511a810070eaf45a9e87d1e25ec8ed279c3fa7cf79df6c78c3e97a5ea24801b6；report SHAc41995aaca953cda51835ac81009b179ffd17fb3a273009ba77eb50636015bdc。主/Mamba页409600，raw QSA页112000 padding至409600/logical400，compressed QSA页25600×16→logical6400；schedulerLCM6400/hash400，2166以下无cache发布。6500输入拆6400+100可覆盖边界。未读live KVCacheConfig，不冒充运行命中；engine仅同步最小block和容量，metrics400/16/None不代表worker spec。补充报告SHA6cd5e7ad2fdd945005ad68ad5c95cb7948c7270436fa5034e765805d61899979。

归档命令G0/commands/freeze-prefix-diagnosis.py SHA7a754517bd734d88022c2b6bb334849215fa2c86594a4fe9b4d46b18c26fda5e，仅CPU核当前源码SHA及精确API、读取8010health/metrics、将已有本地源码快照/CPU报告复制到R3/diagnostics/prefix-hit-001/cpu-source-001并生成manifest；不执行GPU、模型请求或服务操作。

归档已完成：R3/diagnostics/prefix-hit-001/cpu-source-001，10成员manifest SHA967bf211f40d3409f7fab1b63215815679e8092e6c1897b600a3e4bab404fbd5；全部快照与当前生产源码SHA逐项一致，精确API仍原实例、health200/running0/waiting0/preempt0。6500-token待批requests SHAfe2e5d740548e9fb75c8f761f5033a80df1844531be68e582709cec0e25773ce；tokenizer SHA0997f410c57a1f4e53b09e4be8f4a172d90edd9564368fb0847030937229b9f3，完整旧1620 API token可由该tokenizer逐字重建。没有新增推理或重启。


2026-10-30 00:53（Asia/Shanghai）每小时只读核验：PPU-07连接通过；当前API2288060/start600406479/argv SHA仍与R3 READY一致，health200，running/waiting/KV/preemptions全0，prefix queries3240/hits0无增加。原driver已退出，R3仍只有2条完整响应；validation-continued-001及两项repair-formal-001目录均不存在。用户脚本及Gems注册/Mamba helper/runner/native Mamba SHA与冻结值一致，磁盘余1939.9GiB。6500-token续验输入已备，新增2条预算批准仍pending，未派发请求或服务动作；每小时monitor继续ACTIVE。


<!-- hourly-monitor-current -->
2026-10-30 18:31:48+08:00 hourly read-only check: PPU-07 connectivity passed. Exact API1580148/start605206296/argv/listener unchanged, health200/running0/waiting0/KV0/preemptions0, RPC1800. Original validation driver/coordinator absent. Still2 original HTTP200 responses (757/553 tokens), prefix queries13000/hits6400,0C8 and no formal repair-formal-002 GPQA/ERQA directories. Script/critical SHA and25 original diagnosis members verified. Latest sampling-chain source/analysis manifests (21 and3 members) fully verified; all20 current source SHAs match, same API and request budget. Service-log inode stable, idle appends only, no new failure markers; disk free1930.92GiB. No new localization or validation this hour. Main supported cause remains RNG discarded-prefill rollback incompatibility: Gems advances31040 while Plugin rewinds4; CPU source replay supports mechanism but live request RNG/logits/state causality remains unobserved. Saved entry-offset restoration is the repair direction, not yet applied. C1 still failed; C8/formal pending a scoped repair and valid minimal regression. Monitor remains read-only/hourly active; no inference/GPU/compilation/source/cache/service action/8035/physical0-7 access.
<!-- /hourly-monitor-current -->


### 新增预算已批准，同实例续验

用户已直接批准“允许新增2条预算并继续”，覆盖同8010执行2条6500-token C1+8C8，新10+父2=12，0新启动/重启；通过独立CPU审计后续C32 GPQA/ERQA。未来命令将保存G0/commands/prefix-continuation-approved-v2，不改R3冻结文件和生产源码。controller SHA20f7a5ca0c431be4358868c0eb7a36826701c32f01190f986af0a1710ba02b6b；stager SHA07f2589678bc115e19ba0837cccc38b6057165f0a9f433ee9e8e7e37842fa08d；audit SHA54323648c6529c21da9ed08ebafc4bb450897fa0b2434729c0298ad9106dabb1。本地AST、重复/异PID、延迟stats与外部计数拒绝CPU检查通过。


续验已唯一launch：Host3491843/start603288178/argvSHA400cff7d5329a964503a110e34b94353120a212824c4d1150722d7576b14fbac；PREPAREDSHAa517568cf5f47cf276a541625a40045dea46be13abbf5aeb29066be4b89f3e70。当前第0条6500输入已派发，尚无完整响应，不计完成；同8010未重启。小时monitor已更新到新controller和已批准预算，不再索要同一许可。

正式续验已在本地重绑定新continuation，尚未stage/prepare/launch；原生契约和runner不改。未来命令资产G0/commands/formal-approved-v3，suite SHAd7e420fc229134a3d46a915810da4bcdc086d72331cf486afd715ee1ee645abf，stager SHAee27654cd6253e0b3a9d583e55c64db9ed011d9fd04387271112c375e5959fe9。所有准入仍要求新continuation终态及独立审计passed，同时核父R3首错/原单次启动，不改旧失败为passed。仅先保存审核后脚本资产，不能因此启动正式。

已授权原最小→独立CPU审计→正式队列的唯一CPU接续器将存G0/commands/continue-after-minimal.py，SHA97518c0c4cc43935bb3a77ba32f349d629a18fa92f18dd6923d50615581700d9。只等精确driver3491843退出，核无新首错及FINISHED passed；audit一次passed后才stage/prepare/launch正式一次。任何失败写ERROR并退出，不追加推理、重跑、恢复或服务操作。W=续验/formal-continuation-001，独占mkdir拒绝重复，不与手动执行抢跑。

续验首错：2026-10-30 07:42:36第一条6500-token请求HTTP500/153bytes，0成功、余9未发，C8/正式未开始。native EngineCore sample_tokens RPC TimeoutError，约300s与原生VLLM_EXECUTE_MODEL_TIMEOUT_SECONDS默认300一致；客户端600s并未耗尽。此前07:41在精确API子树观察到ppu-llc编译，不能据此确认具体kernel根因；原生dump num_computed6400/下一块100是调度元数据，不冒充设备完成。API与两个controller均已退出，8010无监听；source-before/after-error完全相等。原manifest SHA523a2abae710e99fedf9c7b38f9f125f20c3eda081100508314fed9a20c0b7d8，CPU audit SHA0cc216c6206979035d5450a5982afcf5ae206e5655970c9c6b966db878b14f3c=incomplete。
仅CPU终态归档脚本将存G0/commands/finalize-prefix-failure.py SHA564be41cdc25f41c448c88786a8473efc4b871718a3e2de3d7eeace059de27cd，另存V/diagnostics/failure-evidence-001的完整最后日志尾部/原错/source/nativeRPC源码与进程退出核验；不重跑、不改源码或用户脚本、不恢复服务。


### sample_tokens RPC 超时只读编译诊断

用户仅授权分析已有日志、源码和编译产物，不重启、不重跑、不访问8035。CPU只读探针将保存G0/commands/rpc_compile_probe.py，SHA bb8530f2c49b79346baa3cb67d3028130f5e8893ba1e8057ab8fef1a7e85cd95；限定本次AOT缓存root和07:37:30–07:45:00窗口，只读取已存在文件，不导入推理库/执行编译或GPU。新增证据独立保存V/diagnostics/rpc-compile-analysis-001，原冻结/首错/审计不覆盖。

CPU补充冻结命令G0/commands/rpc_compile_freeze.py SHAaf77ab3d991b2c3971a64ad473874d2f8208d7a67ebbaa0f9166ccc347196148；仅复制索引选中的截止时内核/最后内核、生产源码和现有FlagGems tuning DB/WAL到新诊断目录；SQLite只打开副本读取MM表，不改生产cache、不运行算子。

冻结索引3571组/8逻辑rank，归纳命令G0/commands/rpc_compile_report.py SHA1fc30653ba38b7f17dbc6599145c392da2733a8ea4f60d520f27549827371994；仅CPU聚合已有快照，另存REPORT/manifest，不覆盖原终态审计。不把编译组数/DB候选数当请求数或逐rank设备trace。

报告草案行号复核：narrow_n真实定义为mm.py:1117，原report脚本尚未执行；修正文本后的实际执行命令rpc_compile_report_v2.py SHAdd1b14743d099d6bf3f5a72609fb4e49177e7a96c064bb1d2b44e2a9d68845b5，原草案资产保留。

### 2026-10-30 08:03 RPC只读定位结论

本次主要阻塞强证据指向长输入首次MM编译与在线选参累计超过RPC预算，尚无单一设备算子卡死的直接证据；修复/模型回归仍未闭环。仅使用既有日志、源码和编译产物，0新推理/编译/GPU/重启/服务恢复，未改生产源码、用户脚本或生产cache，未访问8035。

- 第一条6500-token请求07:37:36派发，07:42:36 HTTP500，elapsed300.0675s。原生RPC默认300s，客户端600s尚未耗尽；这是内部RPC超时引发的HTTP500，不是HTTP网络读取超时。
- 对本次AOT缓存root的8个逻辑TP rank完整按时间窗取证：3571组新编译产物，3569组已有hgbin；各rank连续完成412–478组，主要为FlagGems `_thead/ops/mm.py:1004` 的`mm_kernel_ppu`和`:1117`的`mm_narrow_n_kernel_ppu`。0–7这里是TP缓存namespace，未访问物理0–7设备。
- 派发后270–300s窗口仍有464组MM家族二进制完成；逻辑rank4–7在错误返回后继续提交64组/rank，最后为派发+333.204～333.368s，说明不是编译停在单一内核。rank1/2最后两组未写hgbin，与其他rank已成功完成的同一cache key相同，符合退出中断；不能把缺文件反推编译器报错。
- 代表rank0/7单组source→hgbin最大约1.19/1.18s，中位约0.38s；时间跨度包含编译阶段与文件操作，不当纯CPU/device计时，不跨rank累加为端到端耗时。
- 既有FlagGems调优DB副本保留实际原始M=6400和M=100形状：主MM的6400×{N324,K10240;N2048,K2560;N2560,K768;N10240,K2560;N2560,K2560}各104候选均有有限p50；M100前三组各103候选，narrow-N的6400/100各45候选。DB没有逐条时间戳/独立rank身份，不能当本轮逐rank设备trace或完成题数。其形状与本次6400+100分块吻合，结合新编译时间窗和真实ppu-llc进程观察支持首次选参链路。
- 当前LibTuner在新M/N/K/layout键miss后逐候选同步bench，返回有限结果才写benchmark行，全部选完才发布best config。原生EngineCore的batch queue先异步enqueue execute_model，再enqueue sample_tokens；worker RPC按序调用，deadline在enqueue时即建立。因此sample_tokens的300s包括前面model执行/编译及队列等待，不能按方法名认定采样kernel卡死。不是先等model完全执行完再给sample_tokens新的300s。

证据路径：`/mnt/nfs/users/jinghao/qwen3.8-flash/20261015-qwen38-flash-next-ppu07-container/accuracy/acc-023-full-gpqa-ppu07-c32-main-20261029/repair-validation-002/validation-continued-001/diagnostics/rpc-compile-analysis-001`；REPORT SHA059eb0aa59ae1b381087bdc04966c5d315fa209fabb98e224dbb33fb7bbc63e7，manifest SHA7f944899afe2bd16f28348bd7db6d8aeb2c610d385b5981168efd67eef6c4483，119成员，包括14组截止时/最后编译内核、源码快照、调优DB/WAL副本及索引。索引SHA b4143061d87b94e070104f8ce6b111a11a98372e7210c4aff74e509ca1e510ac。

边界：未保存超时瞬间的逐rank Python栈、设备kernel事件和完整编译进程持续时间，不能绝对排除短暂通信/设备等待，也不能声称所有300s都是编译或某一层是根因。可确认在线编译/调优持续越过预算，主要热点已定位到通用MM而非sample_tokens；整体根因置信度strongly-supported，修复与原最小/C8/正式精度仍incomplete。API先前自然退出状态不变；仅发1条失败、余9未发，GPQA/ERQA均未开始。后续若获授权，优先处理长shape在线选参/编译与RPC队列预算的兼容，不能仅靠延长timeout宣称算子性能或精度问题已解决。

独立CPU回读已通过：新诊断manifest全部119成员大小/SHA一致，REPORT/manifest SHA一致；state.yml语法解析通过。小时monitor qwen-ppu07-c32 已产品确认ACTIVE并写入本次定位，仍只读、每小时汇报、不执行修复或服务动作。


### 2026-10-30 RPC budget repair: new explicit user authorization

User authorized repairing first-long-input compilation/tuning RPC timeouts, retaining BF16 and existing fixes, starting 8010 ONCE through the user start-model.sh, then 10 minimal requests and native C32 GPQA198 -> ERQA400. No8035, no commits/pushes, no automatic retries/recovery. This replaces the preceding read-only restriction for this repair only.

Configuration-only repair: replace unset VLLM_EXECUTE_MODEL_TIMEOUT_SECONDS with export VLLM_EXECUTE_MODEL_TIMEOUT_SECONDS=1800. Preserve all model argv, three source trees, MM tuning policy, BF16, prefix caching, image16/video1 and disabled encoder graph/compile. Native RPC deadline starts at enqueue; this finite budget accommodates the evidenced cumulative first-use compilation/tuning. It does not accelerate kernels or compilation.

New minimal: G0/repair-validation-003, 2 identical6500-token C1 then8C8 (4long6500+4short321), max2048/seed1234, zero retries/hidden requests. Client2400s, formal API7200s. Require exact frozen prompt/token hashes, complete outputs/goldB, C1 identical tokens, actual second-C1 prefix reuse >=6400, captures7/7 each, C1 native FULL delta>=2, true unpadded8 FULL increase, unchanged source and independent CPU audit passed. Actual API/EngineCore descendant environment must show RPC1800. Keep existing default caches; no reset, no full-cold-cache claim.

New formal dirs: GPQA/ERQA repair-formal-002; new evaluator names rpc1800-20261030, fresh response UUID/cache. Same maintained formal_accuracy+original llmrun and GPQA strict threshold .88; native ERQA score-only. Same sampling/max60000/7200s/retry limits, sequential total cap32. Never inherit old scores. Full raw/token/source/log/manifest evidence stays remote. Hourly monitor continues read-only.

Assets: G0/commands/rpc-repair-20261030; SHA256.json SHA 29ef7e39d6aa50874d8f19aa7ce5440bee9a68c6fe1b92ad2a53a2ba1063c781. Python AST/static unresolved-global checks passed. Before any mutation save exact user script backup start-model.sh.bak-acc023-rpc1800-20261030 and diagnostics/rpc-budget-fix-001. Old script SHA fc456e30929dc4cb7942405a59d083910e13acffa856c465964245c0aea61890 -> new875788ff3053946c6f25232f8699a24027184d80c4375af1fe0bde75fa7a3f4b. Native env lambda CPU default300/config1800 and host/container bash -n are required before launch.
- apply_rpc_timeout.py SHA256 0f0531e2473570c789f556e904e0eb9136c5d397c44dce2634d8125f25286464
- stage_validation.py SHA256 df5fbf0f26f49ce33cc3e63f8e6299b383066318e61a5d88024de38366769c4c
- repair_control.py SHA256 ffe6c449516de2a7f4a78d51158b1227d45332640a9d85b3549121b84ac3f0fd
- minimal_audit.py SHA256 9efac3c6eab015aca7a17dd932ea010bd3bb0a756078a4572b7467036dac5379
- coordinator.py SHA256 b15e490015ee4410b673df712ab1831fe703420629c62d6b1761398ba59176ab
- suite_repair.py SHA256 2e4d1242550df36a1823013065ad821488376da8f055f863a60831815ad538a5
- stage_formal_repair.py SHA256 ed3f0548563515cf73f252a1693c5e77be9b676e1749f61960c5f38ebd017198

Single coordinator launches minimal driver once, waits original exit and passed terminal receipts, runs independent CPU audit once, then stages/prepares/launches native formal suite once. Any minimal/execution/source failure freezes evidence and stops promotion without service actions.

RPC configuration applied and CPU verified: user start-model.sh SHA875788ff, exact old backup SHAfc456e30 retained. Installed native env resolver default300/config1800 and host/container bash -n passed; source-before/after unchanged. diagnostics/rpc-budget-fix-001 REPORT SHA822fb7346eb555c188911fec79a19150e00b0672ccdc1b74c207bc98f54ccdd8, manifest SHA221b90dc5ec0975ef664ba47a169a5f9445a71351118ac824ea5741c4aba747d. Zero starts/requests so far. Hourly monitor updated to new authorized R3/formal002 queue and remains read-only.

R3 prestart guard failed at2026-10-30T12:47:29+08:00 before SERVICE_START_ATTEMPT; starts0/requests0, coordinator exited and original failure retained. Physical12..15 are occupied by original dead8010 TP4..7: host2300869..2300872/start600409999, container1787496..1787499. Same containerId378fb2429d4cb36221ab5156d7417e18747c25544954c097c65195aafac21ddc/init2203648; parent is container init, original API2288060 absent. New read-only observation corrects any assumption that API exit meant all workers exited.
As necessary cleanup of this task target before the newly authorized single start, save commands/cleanup_r3_orphans.py SHAe232a5907cb1edccee7da8267dfaeef6b788018163e34df954b279865235ba16; validate exact start/argv/cgroup/containerNSpid and frozen log, save identities/old log, SIGTERM exactly4 old workers with45s grace, SIGKILL only same unresponsive old PID via pidfd if required. No other PIDs/ports/devices or container stop. Evidence R3/diagnostics/orphan-cleanup-001. User single model start remains unused; next independent verification will be repair-validation-004, preserving R3 guard failure and all old incidents.

R4 continuation assets are rebound only from repair-validation-003 to independent repair-validation-004 and commands/rpc-repair-20261030-v2, same10 inputs and runtime budgets/no math changes; formal dirs remain repair-formal-002 (never staged). Original guard error preserved, old startup budget unused. New asset manifest SHA2d17ddebfda8d71485f783665c05e14d9f2f1015994dfd238275b717154b65da; coordinator SHA5cb9ec7aad09fb92573c177cdc22c120cbbb2fb53eb0719e3890fecfa198b688; controller SHA3eda2ed871b7833e9d1619b06494abd89c0465ba4a755fd1fc186d1acbb37e5b; audit SHA6feb0c06670992e73c193175ea606a526c3efdb19e4c7b9c677ed2ab900f9bee. Only after precise old-worker cleanup and target free check may this new controller launch the user script ONCE.

Exact cleanup: TERM1793335976.587, all4 unresponsive after45s, pidfd SIGKILL1793336021.730. Original cleanup command then exited1 on immediate device-list assertion while driver released contexts asynchronously; no original REPORT fabricated. At1793336063.476 all4 proc entries absent, physical8..15 empty and8010 absent. CPU closure command commands/finalize_orphan_cleanup.py SHA102def10c2ae2c0bc6f41aca3235ae22821bfce8d81ad435537a2a8c55b54d3a will preserve this timing/initial failure and freeze post-cleanup-report/manifest, no further signals/start/requests.

Old orphan cleanup closed by separate CPU post-cleanup-report SHA667ef807e10efee2c6304df0a8c9edd0ef1bf973b1ca083a7150ab7ac872f7b8; manifest SHAef8f44337dfc55b4e205ef80823a95176c1da0061bcf1fe0a76def30e581acd0. Exact4 old workers absent, physical8..15 empty,8010 absent;0model starts/requests. R3 remains failed-prestart; R4 is separately prepared under the same unused one-start authorization.

R4 unique queue launched: coordinator Host1579334/start605206084/argvSHA29c3c2932a6ed7971cc172ca7bf4e7bab85737185fc770bac7a9374aa46118d1; driver1579336/start605206097/argvSHA948dc6a324074248999d216551630ef6f02864a9a0e5b46f090f718f89b2c669. PREPARED SHA074e8828f4449dcbbdc9feb539290645c29161fa1949e030599b0a90c66b81b3; source SHA668a4bcffc0b63ffc4bc34fb47009d772a0b096604be288abb148f2f9312064b;10 frozen requests SHAd9abbc6cdeff3f9633c38fee41960d4f4ee8fcd7a585d14a69942d21fb888e25. User start-model.sh executed ONCE at2026-10-30T12:57:16+08:00/epoch1793336236.386, exit0, new scriptSHA875788ff. Log inode27006868286/device41. Loading/capture underway; no READY/requests or formal yet at initial check. All subsequent monitoring must follow these exact original processes, no new launch or recovery.

R4 startup succeeded and API1580148/start605206296 is healthy. Before any inference, our overly strict /proc-environ-all-children guard failed at1793336382.092; original driver/coordinator error retained,0requests. Isolated installed setproctitle CPU check reproduced os.getenv=1800 both before/after while /proc/self/environ goes1800->absent; native EngineCore calls set_process_title before init. Absence in relocated exec-environ is not proof of missing runtime value. Save commands/freeze_rpc_env_proof.py SHA7be952c7ec0225775f93c3e3e6718023073936fb35920aae4952c9477fb6bb8e to freeze CPU native-env getter/source proof and exact live API binding under R4/diagnostics/rpc-proc-env-001. No restart or mathematical/source change; reuse same new instance and original10-request budget in new validation-continued-001 after correcting this evidence guard. No independent live child Python getenv trace claimed.

CPU proof escaping validated before upload/execution; actual freeze_rpc_env_proof.py SHA7be952c7ec0225775f93c3e3e6718023073936fb35920aae4952c9477fb6bb8e. Installed native-env lambda and process-title transformation are tested in isolated CPU process, not target process injection.


### R4 same-instance continuation after CPU-proven evidence-guard correction

The current API1580148/start605206296/argvSHA c1b658b05137910a59f347c6fbb9048146d22f1274886b324b761803a9f30fbc is healthy; original R4 driver/coordinator exited before any inference because our all-child-proc-environ guard was invalid. R4 retains DRIVER_ERROR/manifest, no READY or FINISHED fabricated. Source/title CPU proof is frozen at R4/diagnostics/rpc-proc-env-001, REPORT SHA2b84b4516f396cdb3ff4af7637a03349673b22a027b1b74f07b90ac6666af9ec, manifest-proof SHA627b13a2f475bd66555d26fbf1809caf2c16b09bfdf48468b4dfa7ced7ba22fe. Installed native getter remains1800 after setproctitle while /proc/self/environ becomes absent. Actual API export1800 is directly observed; child Python getenv is source-level inheritance inference, not independent live observation.

Continue the same still-unused10 requests under R4/validation-continued-001 with fresh header IDs and same payloads;0new starts,0added requests, no retry of a failed model response. Bind actual parent LAUNCHED/capture and preserve its guard failure. Correct evidence checks require exact current API env1800, SHA-bound installed title/RPC source and CPU proof, retaining missing child /proc values as observations. Original sampling, max2048, long/short token fingerprints, C1 repeats/prefix6400 and actual FULL/C8 criteria stay unchanged. Independent CPU auditor distinguishes parent startup from new validation-only receipt and includes full parent failure references.

Assets G0/commands/rpc-repair-20261030-v3; SHA256.json SHAaaec545f0c8e263ff8b980f28e6f05c744517a5551d66ed682a080367e7e3d52. stage_continuation.py SHA4a106bad22651a5cd7ef1fee2bf31d1ad97180fc494dd8c7d3d1b84ad5262d0c; repair_control.py SHA53b3d13719664a1895c379b847a77e04c460e42dbeb0f102fa5247d840445cfd; minimal_audit.py SHA5231e9343a1d1e80295932fe8866c99548db11e59abc5cd03b04fc75c1135d43; coordinator.py SHA35c15a45b4c94faa92590929e461d8e7e078b7037d6bac260d4a4011a70e634b. Python AST/static unresolved-global checks passed. New coordinator sends no service command; it waits corrected minimal/audit passed then same native formal repair-formal-002 GPQA/ERQA C32 once, with no additional smoke/stop/restart/recovery. Old R3/R4 errors and prior queue assets remain immutable.

Corrected same-instance validation dispatched once: R4/validation-continued-001 PREPARED SHA8841110db82f830a78a4fee1cf9aa6d425c95dfdd8025548c84d39535e760021, READY SHAda9f971baabcb595b686a6b1f4c95fa1ee03699fea1ff464ae1dd25fad0f85ed. Coordinator Host1940166/start605310201/argvSHAfcb848449d60f44366be769d7498542abba494fbfd0fbba1eafb44f0c07e24fe; driver1940690/start605310355/argvSHA39f037712fed5bc50854738c2e2742718576e74acd1268f93923bfb0224d78ee. RUN_STARTED1793337278.490; initial observation1dispatched/0completed,0newstarts. Same API1580148; no new model/math/source/cache-policy change. Original parent errors remain frozen; monitor tracks these exact new processes only.

CPU terminal audit of current R4/validation-continued-001 executed once using its frozen minimal_audit.py SHA5231e9343a1d1e80295932fe8866c99548db11e59abc5cd03b04fc75c1135d43 and explicit --case-dir/--output-dir; incomplete,2 valid complete responses/30 checks, no FINISHED synthesized. Before supplementary freeze, save G0/commands/freeze_c1_sampling_diagnosis.py SHAe73d46c22f10d2ecda18b0b97c8d7bfcbc41432abe068d21fb900137b3c547bb; CPU-only existing bytes/source inspection, no inference/repair/service operation. Output R/diagnostics/c1-token-difference-001; preserve all original failure receipts.

### 最新：RPC预算修复已应用，C1一致性阻塞全量（2026-10-30）

本轮已于12:57:16通过用户start-model.sh实际启动8010一次，原生RPC预算300→1800秒，最小HTTP2400秒；BF16/三库现有修复/MM选参/采样/cache策略均保留。不能将延长RPC预算表述为编译或算子加速；已有cache保留，也未完成全冷cache验证。

R=G0/repair-validation-004/validation-continued-001于13:14:38开始：仅派发seq0/1两条相同6500-token C1，分别105.47s和34.25s完整HTTP200/goldB/finishstop/EOS248046，均无RPC超时、空final或length。第二条真实prefix命中6400，query累计13000。输出分别757/553token，第3索引处分歧；13:16:58原driver在完整token重复护栏停止，coordinator随之退出，余8条C8未发。GPQA/ERQA repair-formal-002目录均未创建。两正确答案不能代替缓存数值正确性或正式精度；不放宽冻结护栏、不伪造FINISHED。

原生两类capture各7/7；已有native FULL表证明实际replay，但完整C8/10请求合同未通过，不能晋级。source-before与source-after-error逐字一致。精确API1580148/start605206296/argvSHA c1b658b05137910a59f347c6fbb9048146d22f1274886b324b761803a9f30fbc仍health200/running0/waiting0/KV0/preemptions0，保持运行；没有二次启动或源/采样修改。

CPU独立terminal-audit-001/report.json=incomplete，30检查/2条有效完整响应，SHA9132370488a5d8f0daf07d54c41d640684f2af9f98fa76385145d9c0042359d5，manifestSHA36327321ece55c743cfc3ce6bb2ef0549f4a3a63722b842363cce523fffbdef6。保留原driver错误和完整日志尾部。

新增CPU诊断R/diagnostics/c1-token-difference-001共25成员逐项大小/SHA回读：REPORT SHA4fd0b1e8807d7321552510e8cba06b3f63ca06757bed5ffe614dd261068613e8，manifestSHA438bbd4b62fcc5665c79fb2a5c634dac8d0f59331958a6cd4aae22c1c2298ca7。源码链：Plugin runner使用native Sampler，Gems注册exponential_；词表248320的FP32指数采样推进ceil(N/8)向4对齐=31040，而Plugin对discarded partial-prefill固定回退4。未缓存6400+100与缓存后100路径可能消耗不同dummy采样，这是随机数状态兼容疑点（suspected），尚无本轮live RNG offset/首差logits或状态张量，不能确认它就是本次根因，也不能排除prefix数值差异。未应用额外采样修复或新推理/设备测试。下一步先完成该差异定位；C8和正式评测等待有效最小回归。小时汇报继续ACTIVE。

### 2026-10-30 C1 sampling-offset CPU mechanism investigation

User asked whether localization was progressing; previous hourly checks were monitoring only. Resume existing-evidence/CPU diagnosis, no model traffic or service/source change. Before remote execution save G0/commands/rng_offset_cpu_replay.py SHA59e9351b7403ae62a257aaf64199a4ee6cc560733e064b0e15707cd3cb1f6b8b. Read only frozen diagnostics/c1-token-difference-001 source snapshots, extract original exponential_/philox state functions and Plugin discarded-prefill loop AST; use CPU metadata generator/state fixtures and kernel-call recorder, no Torch/Triton/vLLM imports or real tensors/device execution. Output R/diagnostics/rng-offset-cpu-001. Local4-case replay plus exact-offset-restore/native-assumed4 controls passed; this proves a source accounting incompatibility only, not live model root cause.

CPU mechanism replay now reproduced using the frozen original Python function bodies with CPU metadata generator/state fixtures and kernel-launch recorders: FP32 N248320 advances31040, original Plugin rewind4 leaves31036; FP64 N248320 leaves124156; BF16 N1024 leaves252. FP32 N32 advances4 and correctly restores0. Exact saved-entry-offset restore control returns0 across the isolated demonstration. This is a confirmed source accounting incompatibility conditional on this source path executing; actual failing-request branch/live RNG offsets/logits/Mamba state were not captured, so model incident root cause remains suspected. No production code, API sampling, startup script, service, cache or model request changes. Repair direction is to snapshot and restore the original per-request generator offset around discarded sampling, rather than hardcode a new decrement; not applied or device-verified.

Remote CPU replay completed: R/diagnostics/rng-offset-cpu-001 REPORT SHAe3c11bf2268d489ab318c19a10fb363af635eb68c5850fbd5eae2c99e7825950, manifestSHA6eedf4fc60cdec4d679532c9f6e149d1e388e207f5a859c89c49342d3fc9b003. Both frozen members verified; three actual current source SHAs match the frozen replay bodies. No live process injection/device execution or source changes.

### User requested continued localization: bind sampling and prefix paths

Save G0/commands/sampling_chain_probe.py SHA19352bd0b465e248aaac08dff74ce4474859ed5fd96af145bfa9ba1c853bc966 before CPU-only execution. Read current source, existing native service log and two original wire responses into R/diagnostics/sampling-chain-001; no imports of model/device libraries, no inference, no source/service/cache change. Trace seeded sampler activation, align split/discard flow, and grouped Mamba copy paths using existing evidence; do not promote CPU/mock into live path proof.

Before CPU execution save G0/commands/sampling_chain_analysis.py SHAed29126953c406173c1afceacc7b0ab4bbed67c4356e0359aef4ed8d56b58c09. Read-only current-source/native-log bridge with exact scheduler and native/compat Mamba preprocessing bodies using request/copy metadata fixtures. Existing LogOncePerLocation exponential hit is preserved as backend evidence, not per-request RNG trace. No new model request or source modification. Output R/diagnostics/sampling-chain-analysis-001; sources/input001 original manifests immutable.

### 本次C1不一致定位结论：采样随机数回退与FlagGems不兼容（代码机制已复现，本轮因果strongly-supported）

用户要求继续定位，现有证据已将主要问题收敛到随机数状态：相同seed1234/T1/相同6500-token请求，在align+prefix miss时由当前原生调度器强制切为6400+100，首块仍采样后丢弃；第二次实际命中6400后只处理100。当前实例native日志明确8192预算、第一/第二请求窗口各有100-token NONE dispatch，排除“6500仅因8192批次预算不足被拆分”的解释。完整调用链源码绑定Plugin新请求manual_seed→native Sampler→FP32 softmax→generator-aware exponential_→bookkeeping discarded-step rewind4。本实例原有/tmp/flaggems_enable_oplist.txt第70行实际记录GEMS EXPONENTIAL_，SHA69ca484d5063324a05202a97f8257e8de111ad0292d38e8dc459727adf1db5a1；logger once只证明本实例该backend调用过，可能来自startup warmup，不能当本次请求逐次trace。

CPU重放原始_mamba_block_aligned_split函数（block400与6400两种边界）均得6500 miss=6400(discard)+100(valid)、hit=100(valid)。结合已复现的Gems每draw推进31040/Plugin仅回退4，第一条首个有效token的源模型偏移为31036，第二条为0；即使logits完全一致，随机流也不再相同。因此C1全序列不一致不能直接归因为缓存数值错误，也不能因答案B相同宣布缓存正确。1620两次miss的源控制路径仍相同，可与历史两次输出相同并存。

另外用当前native preprocess_mamba和Plugin grouped wrapper原函数体做CPU元数据fixture对照：两种block下miss末块与hit末块的逻辑源/目标块及GDN/PLE复制函数规划一致。只替换底层指针收集/实际memcpy为记录器，未验证设备状态值或真实逐rank block表，不能据此完全排除prefix数值问题。没有本轮live RNG offset/首差logits/Mamba张量现场，最终模型因果仍为strongly-supported而非confirmed。

修复方向明确：Plugin对需要丢弃的行保存采样前per-request generator offset，完成该次采样后恢复原offset；不能依赖某个backend固定消耗4，也不应把Gems全局推进量硬改成4。该修复尚未应用，0新模型/GPU请求、0重启、源/脚本/采样/cache策略未改，C1仍失败，C8及正式继续保持未启动。已有单次启动预算已使用，不自动启动第二实例或补跑。

证据R/diagnostics/sampling-chain-001（20当前源码+完整既有service prefix/原响应/原错，manifestSHA67e2c370c20a1a2034917c33fbaf792b4858bc16fe377631bedf26a23c72063c）；新CPU分析R/diagnostics/sampling-chain-analysis-001（REPORT SHAa805f246b1263e5158d8bf21a958d4c7ddb3703d14d102acd36fcd7b9244000c、manifestSHAfe8df498799daf483b7aaf24655abd29be82fa682d5211e04d5b30b651a71ff8）。独立完整成员大小/SHA回读及20实际源码SHA一致性已核验；同API1580148/start605206296保持、2原始请求未增加。新报告只细化本次故障，不能作为正式gate或性能结论。

### New explicit authorization: repair RNG rollback and one8010 restart

User20261030 explicitly authorizes Plugin sampling RNG rollback fix, retain BF16/existing fixes, user start-model.sh ONE restart,2 long C1 actual prefix/token repeat then8C8, then native C32 GPQA198/ERQA400, full evidence/no8035/commit/push. New repair U=G0/diagnostics/rng-rollback-fix-001; new minimal R=G0/repair-validation-005; formal G/E repair-formal-003; assets A=G0/commands/rng-repair-20261030. Old failures/dirs immutable. Modes minimal-regression then formal-gate, ERQA native score-only. Implement request-local context manager around real sampler and remove old bookkeeping minus4; save original generator objects/offsets only for discarded seeded rows, finally restore on success/error, valid/global RNG untouched; no math kernel/seed/blacklist/flag/cache-policy change or global patch. Applicable Plugin clauses A1/A3/A4/B4/C1/E1-E4/F1-F4/F7; F3 model capture/two replays/C8 pending. Preserve current source before patch, all existing Git changes and exact rollback backup. CPU stage apply_rng_fix.py SHAde87b78eff3741ca25a71846759d04302f4031bf812b4cc5371a70b66dc4a120 saved before execution; payload SHA manifest 1ad166877d9042c2230e38a4b597965dcff46fa59f7230b255b1f5248a9013ce. Native user script remainsSHA875788ff; sampling fix alone is experiment variable. Source-only CPU checks before any service action; exact current oldAPI1580148/start605206296/argvSHA c1b658b05137910a59f347c6fbb9048146d22f1274886b324b761803a9f30fbc is the only restart target.

CPU tooling adjustment before any deployment: ruff is not on container PATH; reuse existing isolated /tmp/acc023-ruff/bin/ruff from prior checks. Initial A assets never executed apply or service operations. New reviewed A=commands/rng-repair-20261030-v2; candidate texts formatted/checked via stdin only. apply_rng_fix.py SHAac55a454ee8f2b99edcc589bdc895a19f25c344fe91f4e59e1c251b0fd2eed88, payload manifest SHA651cc7b418b012d8c206569bb9ca551b5d43436f111e4e5791a400ce8e0d7e73. Old A assets retained; U/R5/formal003 unchanged.

Final reviewed source payload A=commands/rng-repair-20261030-v3; two new candidate files passed target Ruff stdin check/fix+format after resolving test-only SIM117 style findings. Previous A/A-v2 never ran apply or a service command and stay preserved. Final apply_rng_fix.py SHA3620ea47096a634c25e0cbb022b4fced346efad53d6027aa097a94c2b48e53a9; payload manifestSHAf43f377491540e972fb8c2c248f7f26fe4d5e7b4aa1c675325fd933c9a830d84. Now run CPU fixture tests, then exact3-file deployment/backups and repository CPU tests/source delta verification; no stop/start in this command.

Repair deployed and source/CPU verification complete: U REPORT SHA5302d3c37f96a746fc3f5a919b0deef514fbd4f01f1e447ed3387ba5766f3715, manifestSHA6bc573494886515155440849c6986ee6e694dd0fc360ff302a21204bed82cfa2. Both isolated candidate and actual repository CPU14 passed; target Ruff/style and whole-worktree diff-check passed. Exact source delta3 files only: runnerSHA5c78833043957e14032fc065b0c1545c50e1fd46f5e174854b09083075c223dd/helperSHAd0ea4e18f0e56618ac216efbcea463bf09b1a51d35f44a43b32173109f4547da/testSHA bb0ddd03356d90701218223993e0a4ef957ff799b4e9db3f7ac788d019c834fe. Existing source trees/BF16/model/weights/tokenizer/HEAD-index and user script unchanged. Old API has old loaded objects; new one-restart authorization still unused. No new model traffic, no formal score or hardware pass claimed.


### RNG repair queue frozen before the authorized restart

A=G0/commands/rng-repair-20261030-v3 is frozen: SHA256.json=6d38913c0290be9fdeb4a2b9a2b4e8c17588cebaa1235bed8f9a8716b5e7ffc4. ControllerSHA7b494718eb63b63429e541221d810d0df50842c2e31f8c1ec6d7155084fd1a6c, independent auditorSHA02ad6f385d7d21b3c6f3c33bd922c229bf14c62abcf3bc6ec702db14c1371edb, coordinatorSHAdbf57f3617023cc8734a0f5fa27d1a41b32801f0bd7e0b9ed1c43587ae13a5bd. R5=G0/repair-validation-005 CPU stage completed with PREPARED SHAcd02e25408352ffa313ba597b1d9652282583ff750ec45f674c3674866676b54, requestsSHA6d3d7dcfb40fcb94b51d30b86cec141f3ca978ec40c5c3518592d84feadcfcd6, sourceSHA0a672c8fb3d7c253e04aaaae03739396cbdc87497ab8cf4758c3cda153b9a9b9. New request IDs only; original 2x6500 C1 +4long/4short C8 payloads unchanged. Native scriptSHA875788ff unchanged; RPC1800/HTTP2400; no cache clearing. Exact oldAPI1580148/start605206296 is sole SIGTERM target, wait all owned critical workers drain and physical8–15 free, invoke user start-model.sh once. No force kills or recovery. Prepared0 starts/requests; new restart budget stillunused before coordinator launch.

Execution command saved: python3 -B A/coordinator.py --mode launch. The unique coordinator launches R5 once, waits original driver exit, requires complete10 responses/second-prefix>=6400/C1 full-token equality/capture7/7 each/2 native FULL replays/actual unpadded8 FULL/source unchanged, then runs independent CPU audit once. Only allpassed stages new repair-formal-003 and one native C32 GPQA198→ERQA400 queue. Serialcap32, GPQA strict .88 formal-gate and ERQA native score-only, fresh UUID/cache and native retries preserved. Any failure freezes existing evidence and stops progression; no fake FINISHED, no automatic re-run/restart, no8035/commits/push. Existing hourly monitor follows this queue only.


2026-10-30 19:40:38–19:40:40+08 single restart executed: exactly one pidfd SIGTERM to oldAPI1580148; API/EngineCore/8workers naturally drained and physical8–15 free. User original script launched once at1793360440.7354064 withSHA875788ff unchanged, return0. New API READY pending; no inference sent yet. Unique coordinator1335508/start607626350/argvSHA4d65d25c584752e73e8cea459e4ad00d6ed84f5c473f32159eaa2ff98148eec9 and minimal driver1335510/start607626361/argvSHAd3100cf04476e5280b290cc3130b6beed57f5cf4dfbba6fd939565256d63bc34 bound to nativePID receipts. Restart budget1/1 used; no further recovery/restart. Existing hourly qwen-ppu07-c32 ACTIVE now follows R5/formal003 only; oldR4 history preserved. No8035/commit/push.


2026-10-30 19:43:09 read-only: newAPI1336953/start607626732/argvSHAc1b658b05137910a59f347c6fbb9048146d22f1274886b324b761803a9f30fbc READY at1793360586.326011, both graph captures7/7; first6500-token seq0 dispatched19:43:06. Old API no longer current. Single restart1/1, no furtherstarts; current health200. Native minimal is running, no complete response yet/noC8/formal.


2026-10-30 19:44:53 read-only: R5 two6500token C1 complete HTTP200/goldB/stop, output553/553 and native C1_REPEAT_CHECK tokens_equal=true; second prefix actual hit6400 (0→6400), FULL_delta1013 beforeC8. Seq0 elapsed40.37s/seq1 34.01s from native dispatch/completion events; not a controlled performance result. EightC8 seq2..9 dispatched19:44:20.916–.920, currently in-flight; no extra requests or retries. No formal/evaluator yet. New currentAPI health200, zero preemptions. This resolves the observed repeat-token guard in this bounded C1 case; formal precision and wholeC8 stillpending, no gate claim.


2026-10-30 19:48:32 R5 native terminal passed:10/10 complete HTTP200/goldB/nonemptyfinal/stop/EOS, no retries/length/RPC failure; C1 553/553 exacttoken repeat and secondprefix6400; C8 actualunpadded8 FULL_delta244, totalFULL1619; sourcebefore/after equal, API1336953 healthyidle/preempt0. FINISHED summarySHAe8a983cf2b6998c86cfc20e2bf28ec4e1071875e34785a727b1927f51909ebb7, manifestSHA07b335ee00201b76304703fc2096086d236cdb91a652e51d93dc0e1ac6929b50. Unique originaldriver/coordinator exited.

Original terminal-audit-001 failed only on overly narrow log regex `mamba_cache_mode...align`; dependent graph-path check then failed. All10 responses and other29 checks valid. Actual frozen service.log lines26/27 explicitly say native "Mamba cache mode is set to 'align'" and "Prefix caching in Mamba cache 'align' mode is currently enabled"; current SHA-bound native model_executor/models/config.py emits that exact wording. This is an auditor formatting defect, not a runtime/model failure; original audit/ERROR retained, no gate claimed yet.

Before CPU correction execution, save A2=G0/commands/rng-formal-20261030-v1: SHA256.json8bd53ca05996f4f0324ce84ff9fe464666d73fe654ad4e450ca3f10c38c96b4b, revised auditorae0f1f8db5c566e2eae0007724cb8ab05b1bb509d0dfd3aec0bd57b50fd986f9, coordinatorc0252affcf45227b276a7a80e5c4f1b49601ad08abe1daef91bd3c96a2989658. Only accepts exact native align log variants and binds original/future auditor separately;3 positive/4 negative CPU regex cases pass, all31 original checks retained plus explicit correction provenance. New CPU report terminal-audit-002, originalfrozeninputs/PREPARED/firstaudit unchanged. W2=R5/coordination-002 invokes onlynewCPUaudit, then original authorized formal003 stage/prepare/launch once ifpassed; neverlaunchesmodel/minimal/service. Command saved python3 -B A2/coordinator.py --mode launch. No extra model requests or restart, GPQA/ERQA still0formal untilnative markers.


2026-10-30 revised CPU terminal-audit-002 passed32/32 checks,10 valid complete responses, no new requests/devicework/serviceactions. Original terminal-audit-001/coordination-001 failure preserved. Unique CPU/formal-only continuation coordinator1653848/start607700868/argvSHA4abe3f7facd6c732ff351ee614c02483325fbbd7fc5bc19fb9cd3ba57ddf93e8 started once, W2=R5/coordination-002. Formal repair-formal-003 preparation is in progress; await CLIENT_PID/FORMAL_STARTED, no formal score yet. SameAPI1336953 retained; no secondrestart or minimal rerun.


### Sampling fix model minimal accepted; fresh native C32 formal started

2026-10-30 19:53:38+08 FORMAL_STARTED epoch1793361218.159551, GPQA198/C32,0new modelrestart/smoke. Native log19:53:52 confirms concurrent32/timeout7200 and Cached requests0/remaining198; no old answers reused. Fresh config/cacheUUID3153eafb4cc341e8a6230b6a2e653648; native strict threshold.88, original sampling/stop/max60000/eval_seed42 retained. Unique formalcontroller1666133/start607704298/argvSHA15cb2a3da1541b04377163791247809dc13cdc109f309f17304f4f434670e2f0, controllerSHAf253035e14b7c8cebcd0f0deb63751910dbd7113d8bbbd3689ef6e3886a4eb5c. BothGPQA/ERQA preflight/preparation passed, ERQA native400/workers32 is serial pending. No formal score/gate yet; score-only forERQA.

R5 independentCPU audit002 REPORTSHA c1a555aaec65dbf7d4c8d29b2038db6d3f9db339af3c5302d3d8a58ac75a4798, manifestSHA833dac3fbf9dcdbfaa2bebf3d32deee1daa4fe14b58c2f9061298896b5450ed7,32/32passed; originalaudit001fail kept. Current model sampling fix passes requested bounded2longC1→C8 and native graph guards, not equivalent to full formal accuracy or independent per-rank/kernel/RNGoffset trace. One8010 restart used exactly; same newAPI1336953/start607626732 retainsBF16/image16/encodergraphoff/allpreviousfixes and unmodifiedstart-model.sh875788ff. Wholequeue no commit/push/8035. Hourly qwen-ppu07-c32 remainsACTIVE onW2/formal003; terminal results/source/samples/native score/manifests and finalaudit must be complete before final gate report. Current GPQA underway, ERQA notstarted, no inference outsidefixedminimal and authorizedformalqueue.


19:55:54 final read-only check in this turn: same formal-boundAPI1336953/start607626732/argv unchanged, health200, actualrunning32/waiting0/KV0.0346896568/preemptions0. Currentformal newbyte/inode log window has noTraceback/EngineCorefatal/WorkerProc exception/illegalmemory/TimeoutError; no CLIENT_ERROR-v2/FREEZE_ERROR/SUITE_FINISHED. GPQA continues; no score yet.


2026-10-30 19:58+08 read-only monitor: originalformal1666133 and W2coordinator1653848 retain boundstart/argv and areactive; sameAPI1336953/start607626732/listener/argv, health200, running32/waiting0/KV0.0397878941/preemptions0. GPQA native progress has reached1/198; no samples/doc-cache mapping audited yet, so this is nativeprogress only, not an independently verified unique completion count or score. progress_score helper still0 and not used as score. ERQA400 remains serial queued. Newformal logwindow has nofatal/RPC TimeoutError, noCLIENT_ERROR/FREEZE/SUITE_FINISHED; diskfree1854.46GiB. User script875788ff, RNG3files/Mamba/Gems registration SHA, all3 repoHEAD/staged-content and audit002 report/manifest match frozenbindings. No newmodel/device/service/source/cache actions or8035. Recentmain update19:55 already reported current phase; no duplicate notification withinminutes, hourlymonitor remainsACTIVE. Nextstep observe originalGPQA thenERQA/terminalaudit; no manuallaunch/retry.


2026-10-30 21:01+08 hourly read-only monitor: current GPQA formal003 remains active C32; same boundAPI1336953/start607626732/listener/argv health200/running32/waiting0/KV0.4651420051/preemptions0. Original formalcontroller1666133 and W2coordinator1653848 active. CPU native-cache-key/full-prompt-doc audit independently confirms124/198 unique docs in the fresh SQLite cache and124 complete native parsed API objects mapped to exactly the same124 doc IDs. All124 stop, valid fulltoken/prompt usage, thinkend and EOS;0emptyfinal/60Klength/placeholders/transport error lines in this prefix. Raw198 and processed198 doc hashes exactly match frozen provenance; no partial/helper score treated as final. No GPQA results/samples/FINISHED/gate yet; ERQA400 remains serial queued. Currentformal newbyte/inode service window has nofatal/RPC TimeoutError; no newCLIENT_ERROR/FREEZE/W2ERROR. Diskfree1404.33GiB. Script/RNG3files/Mamba/Gems registration SHA and all3HEAD/staged-content unchanged. Nextstep continue original GPQA thenERQA and finalCPU audits, no manualrequests or service actions. Hourly notification due and sent with124/198 only, not accuracy/pass claim.

CPU progress evidence is G/diagnostics/hourly-progress-20261030T2058-v2: REPORT SHA0f2aaa22d21e9875224d12f802766eb1259c25c5bfe9e404366da3b083fe3699; post-process terminal-manifest SHAd3ec843eee79703cc21be6371861d2aa8e23b7a6a2b8908a018ad633560ed051,7 members independently hash-readback verified. Read-only original SQLite snapshot, original native hash_args, frozen task preprocessing/Template, complete native-log prefix, no evaluator/LM/device execution or score. Initial2058 CPU audit failed because it compared native source_tree canonical-entry digest against raw bytes; original exit/error retained, v2 uses exact original source_tree digest and validates raw/processed198 doc identities. Original v2 manifest records an in-process log snapshot; definitive terminal-manifest binds final audit.log/exit/report/originalmanifest after exit. This is CPU audit bookkeeping only, no production/source/runtime issue or extra inference.


2026-10-30 21:57:49+08 hourly read-only: GPQA formal003 remains active, CPU nativecache/fullprompt audit verifies195/198 unique doc IDs and195 complete parsedAPI objects with same docset;3in-flight.190normal completions,5doc32/71/79/88/127 reached60000tokens/finishlength/contentNone/no thinkend, no token/usage evidence mismatch. These are length-capped model outputs, not RPC/network timeouts; native helper excludesNone and is not formal score. First native UTC timestamps13:15:42,13:25:10,13:28:55,13:32:13,13:55:47 (local21:15:42 through21:55:47), retained full nativeprefix lines512/581/590/596/620. Original workflow continues natural collection with0manualretry. No finalresults/samples/gate/SUITE_FINISHED yet; ERQA400 stillqueued. SameAPI1336953/start607626732/listener/argv health200/running3/waiting0/KV0.1091191112/preempt0, originalformal1666133/W2coordinator1653848active; currentformal window nofatal/RPC TimeoutError and no newCLIENT_ERROR/FREEZE/W2ERROR. Script/source5critical/threeHEAD/staged-content unchanged; diskfree1403.95GiB. Nextstep await last3 then originalnative scoring/CPUaudit and serialERQA; no model/service/source/cache/GPU/8035/commit/push actions.

Current CPU snapshot G/diagnostics/hourly-progress-20261030T2155 uses new output directory and preserved currentcase only: REPORT058af997801588c4f9fda8ae6e295c950a932052817f133e7ed1d4cfa11dcbc7; manifest58ae95e6701254926673c8c5413121a79eecc0e37a1a88042f97198634135674 (in-flight stdout excluded); postexit terminal-manifestff26f46491b7705710883f445ecc8fe5f91e59e3c712fb065df4161557ec7723 independently verified. Native hash_args plus actualtask preprocessing/template and raw/eval198 doc SHA validation;195cachekeys and195 completeAPI objects map uniquely tosame195docs, fivecachevaluesNone/notstrings are output-parse values, not transporterrors. No newnative score calculated or fullgpqa_audit run bymonitor. All prior snapshots/firsterrors retained.


2026-10-30 22:59:47+08 hourly terminal review: native GPQA completed198 unique docs/396 strict+flexible rows; strict174/198=0.8787878787878788 < frozen.88 (24wrong:8length60000/contentNone→TIMEOUT placeholders plus16ordinary wrong). Eight lengthdocs32/71/79/88/127/145/147/185;190stop,0token/usage evidence issues or native transporterror lines. No RPC/device fatal in model service window. Native results22:20:41/43 saved, originalFINAL_SUMMARY/FINISHED verdict remainsincomplete: postrun native-audit at22:24:03 failed prompt_doc_binding, controller/W2 exited and didnotstartERQA400. No formalpass gate or SUITE_FINISHED, no optimization continuation. Same currentAPI1336953/start607626732/listener/argv health200/running0/waiting0/KV0/preempt0; script/5criticalsource/3HEAD/staged-content unchanged, free1403.75GiB. Originalformal/native-audit processes gone; evaluatorcontainer retained only tail -f /dev/null, no helper running. No restart/retry/source/evaluatorrepair/ERQAlaunch/GPU/8035/commit/push inmonitor.

Issue acc023-formal003-terminal-JSON-chat-binding-and-low-score (gate-blocking): original response_observations picks longest nativearguments string, which is serialized JSON chat in arguments.gen_args_0.arg_0[0]; searching it verbatim inside rendered prompt_text produces0/198 matches. PureCPU decoding that exact existing JSON yields198 unique nativeuser prompts, all198 API objects map uniquely and actualsample.resps agrees190content/eightTIMEOUT. This confirms auditor format/accounting defect, not model RPC failure. Native174/198 rawscore is independently verified but remainsbelowthreshold even aftermapping accounted for; original terminalincomplete is immutable and no gate is issued. Model low-score causal attribution/RNG/logits/Mamba-state trace absent; do not blameBF16/samplingfix or borrowoldscore. Futuremain work may repairCPUauditor binding and diagnose24wrong cases under separately scoped actions; monitor neverappliesfix or resumes stoppedqueue. Existing hourlyreport remainsACTIVE because user requested progress until entirefix/GPQA/ERQA task complete or userstop.

CPU-only terminalfreeze G/diagnostics/terminal-freeze-20261030T2253: REPORT3b78f72bd28dcb4865d1e50d79296db035d5b73905a9cbb29f38b5c6d2d91330/postexit terminal-manifest0280794368c207880f3148b9606650040e9e6ef61b20fde22b8df6676d1b6721. TerminalSQLite safe-string decoder returnsNone for198nonstring-decodable values; this is not198 networkfailures, finalAPI/samples establish8lengthonly. IndependentpureCPU terminal-evidence-review-001 script9e7c29bd709704115237dd5ba5883b9d648f2a89f41b89d49de837bdbcc20362, REPORTbe2bda34bdab6f6f8270c400b75ac186da718978e72e53048b568fc96b1ca661, terminal-manifestc43f6ed5cff56a5d6ce1073a60c46192d38de177fdd0b616e1af4e19e0dd8792 (13members readbackpass). Fivechecks passed:113originalmanifest members,56frozeninputs/provenancepair/sourcebeforeafter,198unique/396rows/samecontentperdocfilters,decodednativeJSON API/samplemapping198 and190content/eightplaceholderagreement, originalfailedterminal+ERQAunstarted/controllersexited. Originalmanifestc46561d7fffe2adbde034a2841f48596b4e811be99088b00218c2a1d5310b67f/summaryc85551cf524abc62cedcfa824bb140c110df8853c24ad336b1753b0b2cfaddce remainunchanged. Native resultSHA68a327b8030e2796219a522d49f08ce1ade823e2337930790358f884217f5c73; sampleSHA2a108a5cae861dc1741527ff29c7aa71e6ed1e4ad6462c7fffc6112a37add350. Existingcomplete rawAPIjsonlSHA8a0a214e606bdb9113ccd0d0900be852314151cd79123389c01fd0cb2d5e8f4c. Originalsuite-terminal-audit-001 report509cfef483c1c1975741de3204179705340c7c57b3caf23a3c2509976a9cc5a5=incomplete, retains staleR metadata repair-validation-005/validation-continued-001; newCPUreview usescorrectR5, nooriginalreceipt rewritten. Allfirsterrors/outputs retained; CPUreview isnot a newformalrun or originalgate repair.


2026-10-30 23:53:25+08 hourly read-only follow-up: no new execution, validation or diagnosis result this hour. GPQA native174/198=87.8788% remainsbelow88%; originalformal terminalincomplete and JSON-chat audit binding issue remainfrozen. ERQA FORMAL_STARTED absent, no newformal directory or SUITE_FINISHED; originalformal1666133/W2coordinator1653848 remainexited. ExactsameAPI1336953/start607626732/listener/argv health200/running0/waiting0/KV0/preempt0, no newmodel fatal/RPC TimeoutError in currentformal window. Key5source/threeHEAD/staged-content/userstartscript unchanged; originalsummary/manifest and13member terminalreview hash-readback unchanged; diskfree1403.68GiB. No newinference/GPU/CPUauditexecution/source/cache/service/8035/commit/push actions. Currentblocker remainsauditorJSONbinding plusnative low-score/8length; next main-task work must address those and ERQAcontinuation under its authorized scope, monitor doesnotresume/retry. User-requested hourlyupdates remainACTIVE; task incomplete, no formalpassgate.


2026-10-31 00:59:33+08 hourly read-only follow-up: no new repair/validation/diagnosis result. Originalformal/W2 remainexited, ERQAunstarted/noSUITE_FINISHED/no newformal directory. NativeGPQA174/198below88% and originalauditJSONbinding/incomplete remainfrozen. ExactsameAPI1336953/start607626732/listener/argv health200/running0/waiting0/KV0/preempt0, no newservicefatal/RPCTimeoutError;5criticalsource/threeHEAD-stagedcontent/userstartscript/originalsummarymanifest and13member CPUreview SHA unchanged, free1403.67GiB. No inference/GPU/CPUaudit rerun/source/cache/service/8035/commit/push actions. Blocker remainsCPUauditorbinding and low-score/8length; main-task followup needed, monitor doesnotrepair/resume/askduplicateapproval. UserhourlyupdatesACTIVE, no validformalpassgate.


2026-10-31 01:59:42+08 小时只读核验：无新增修复、诊断或验证结果。原GPQA174/198（87.8788%）及审计incomplete继续冻结；原formal/W2均退出，ERQA未启动，无新formal目录或SUITE_FINISHED。精确同一8010实例健康200，running/waiting/KV/preemption均0，无新RPC/设备fatal；关键源码、三库HEAD及暂存内容、用户脚本、原summary/manifest和13成员CPU证据SHA不变，磁盘余1403.41GiB。未执行推理、审计重跑、源码/cache变更或服务操作，未访问8035。阻塞仍为审计JSON映射及低分原因，待主任务继续处理；monitor不恢复队列，保留用户要求的小时汇报。


2026-10-31 03:02:05+08 小时只读核验：本小时无新增诊断、修复或验证结果。GPQA174/198（87.8788%）及原审计incomplete保持冻结，formal/W2均已退出，当前没有评测运行；ERQA仍未启动，无新formal目录或SUITE_FINISHED。精确同一8010健康200，running/waiting/KV/preemption均0，无新服务fatal/RPC错误；关键源码、三库HEAD/暂存内容、用户脚本及原冻结证据SHA不变，磁盘余1403.29GiB。仅执行不写远端文件的只读检查，未重跑CPU审计/推理/GPU、未修改源码/cache或操作服务，未访问8035。阻塞仍为审计JSON映射及低分原因，后续待主任务处理；监控保持小时汇报，不恢复队列。


2026-10-31 04:01:49+08 小时只读核验：暂无新增诊断、修复或验证。原GPQA174/198（87.8788%）及审计incomplete继续冻结，formal/W2保持退出，ERQA未启动，无新formal目录或SUITE_FINISHED。同一精确8010健康200，running/waiting/KV/preemption均0，无新服务fatal/RPC错误；源码、三库HEAD/暂存内容、原启动脚本及冻结证据SHA不变，磁盘余1403.24GiB。未重跑CPU审计、推理或GPU，未改源码/cache或操作服务，未访问8035。阻塞仍是审计映射和低分原因；后续待主任务处理，监控不恢复队列，保留小时汇报。


2026-10-31 05:06:22+08 小时只读核验：暂无新增诊断、修复或验证，GPQA174/198（87.8788%）及原审计incomplete保持冻结；formal/W2仍退出，ERQA未启动，无新formal目录/SUITE_FINISHED。同一精确8010健康200，running/waiting/KV/preemption均0，无新服务fatal/RPC错误；关键源码、三库HEAD/暂存内容、原脚本及冻结证据SHA不变，磁盘余1402.91GiB。未重跑审计/推理/GPU、未改源码/cache或操作服务，未访问8035。阻塞仍是审计JSON映射和低分原因，待主任务处理；监控不恢复队列，小时汇报继续。


2026-10-31 06:02:21+08 小时只读核验：无新增诊断、修复或验证结果。GPQA174/198（87.8788%）及原审计incomplete继续冻结，formal/W2均已退出，ERQA未启动，无新formal目录或SUITE_FINISHED。同一精确8010健康200，running/waiting/KV/preemption均0，无新服务fatal/RPC错误；关键源码、三库HEAD/暂存内容、原脚本及冻结证据SHA不变，磁盘余1402.89GiB。未执行推理、审计重跑、GPU、源码/cache变更或服务操作，未访问8035。阻塞仍为审计JSON映射及低分原因；待主任务处理，监控不恢复队列，保留用户小时汇报。


2026-10-31 07:07:47+08 小时只读核验：无新增诊断、修复或验证。GPQA174/198（87.8788%）及原审计incomplete继续冻结；formal/W2均退出，ERQA未启动，无新formal目录或SUITE_FINISHED。同一精确8010健康200，running/waiting/KV/preemption均0，无新服务fatal/RPC错误；源码、三库HEAD/暂存内容、原脚本及冻结证据SHA不变，磁盘余1402.81GiB。仅只读检查，未执行推理/GPU、审计重跑、源码/cache变更或服务操作，未访问8035。阻塞仍为审计JSON映射与低分原因，待主任务继续处理；监控不恢复队列，小时汇报保留。


### 2026-10-31 用户新授权：修复审计映射并接续 ERQA

用户明确要求修复 JSON 聊天参数到原生 prompt 的审计映射，仅用已有 GPQA 产物重新审计；证据有效后沿用当前同一 8010 执行尚未启动的原生 ERQA400/C32。并行使用已有证据诊断 GPQA174/198 和8题60K截断。保留 BF16 和全部生产修复，不重启、不重跑GPQA、不访问8035、不提交推送。

执行模式：本地 accuracy formal-gate 的已有产物 CPU 重新审计（不产生新GPQA请求），ERQA native score-only；diagnosis 冻结低分并继续既有证据分析，不叠加性能优化。原 GPQA FINAL_SUMMARY/FINISHED/incomplete 和首错均保留。修正审计不会改变174/198或签发通过gate。新资产计划 `acc-023.../commands/audit-map-erqa-20261031-v1`，重新审计计划 `repair-formal-003/diagnostics/audit-mapping-fix-001`；ERQA单项接续控制记录 `acc-024.../repair-formal-003/continuation-001`，不执行原双项suite。

已在07:57只读核同API1336953/start607626732/argvSHA c1b658b05137910a59f347c6fbb9048146d22f1274886b324b761803a9f30fbc，health200、running/waiting/KV/preempt全0；源、三库HEAD/staged和原启动脚本一致，ERQA确未执行。当前阶段：审计修复与CPU验证，尚无新ERQA请求。

CPU审计部署执行前绑定：新helper SHA `4213718f6230797ea57237449fdb57a8adc3ee09af6e6a614016a82972b3235a`，reaudit SHA `e4b9998364ac4348da4ca0206c3c636730181b7b557f1478351053120adba19f`；10项映射单测通过，完整 `scripts/validate-local --code` 通过（不含记录验收）。CPU命令固定已有GPQA评测容器、offline datasets/hub、CUDA_VISIBLE_DEVICES空，不调用原formal runner或模型；输出独立Q/audit.log和新parsed/native-audit。原件不覆盖。

重新审计完成：198unique/396filter行、198完整API唯一prompt映射，无token/usage缺证。Q/native-audit SHA `6df7dbd210266ef8846e6228437eb7ea875ae00eb5158c07c22346bd3ae604ee`，Q/manifest SHA `0a223a1132db20aa403b8491d78406b2c5bafb6b1a1bdf886541b41b9dec757f`。独立修订为valid-native-score/failed-score174/198；原incomplete/原manifest未变，无passgate。新ERQA-only controller SHA `c8cdf7d1bc44507aafa41509008627e140f784356e6adb972da9b278d4366ff2`，显式只调用原suite的只读身份/源/冻结输入核验函数、原native adapter/audit及原生单项命令，不执行原prepare/run_suite，不重复GPQA。先独占prepare检查同实例、空ERQA目录/原生源图像、原输入与新授权，再单次launch；新所有回执在EC，原准备controller SHA与新controller SHA分开绑定。

已有证据低分诊断执行前绑定：`commands/audit-map-erqa-20261031-v1/gpqa_low_score_analysis.py` SHA `950116261441f2f6b4bc68d50423c37eb5f34c593c8c50b082b2c76ec4c59963`，仅stdlib CPU读取已有198完整API和396样本、统计8length推理文本/16错题原生答案抽取/重复token窗口；不调用模型、tokenizer或评分runner、不修改采样/阈值/分母。新输出 `repair-formal-003/diagnostics/gpqa-low-score-analysis-001`，完整失败题推理和最终输出另存绑定原SHA。

08:07:56+08 ERQA FORMAL_STARTED epoch1793405276.3363018，原生400/C32单项已启动；唯一controller4141102/start612110094/argvSHA d118f283b79d6918cf7c619c6f8f5fb7e82614a89aed7ca8b47b9d7b2dccdb28，控制脚本SHA c8cdf7d1bc44507aafa41509008627e140f784356e6adb972da9b278d4366ff2。首32派发时0返回/0真实绑定，派发不算完成。本次0GPQA新请求/0重启。CPU终态等待器预保存 `erqa_terminal_watch.py` SHA `3b86627c5f8840666d981f2af886b2732ef0759865a6d9a7cab2af318e3106c9`，只等该controller自然退出后核全部manifest/400原生评分与真实wire映射、同源同API、完整最终日志；不发推理或启动任何评测。独立EC/terminal-audit-001及COMPLETED/AUDIT_ERROR保存终态，原GPQA产物不覆盖。

补充既有历史证据对照：已从acc021记录定位相同数据集旧175/198、9题60K截断（source/C64/prefix禁用/固定调优均与当前不同）。仅新CPU脚本 `gpqa_history_compare.py` SHA `94b2802dad11e99f9ef264115cf8458ab3f9d849b4fece2c8bcca11f0d6d4602`，读旧samples原SHA e607ad3d03bd5e07ccfce976e593472db33449c6009f0732d9d4d0160d449b04与当前原样本，逐doc检查doc/prompt/target hash再比较变化；输出当前诊断子目录history-comparison-001。不得当同配置baseline、复用答案或当前gate，更不据一题净差归因新fix。


2026-10-31 审计修复与ERQA接续已执行：修正CPU审计将serialized JSON聊天参数解码为完整原生user prompt，再唯一匹配返回prompt_text；拒绝重复doc/歧义和残缺API。10项新增单测、完整本地275项工具测试和`validate-local --code`通过，原始test资产11项SHA未变。已有GPQA离线重审198/198全映射、396filter行/完整token与usage有效，修订回执failed-score174/198（阈值.88，需175题），无通过gate。旧incomplete/原manifest/首错不覆盖。Q/native-audit SHA 6df7dbd210266ef8846e6228437eb7ea875ae00eb5158c07c22346bd3ae604ee，Q/REVISED_VERDICT SHA1535a648e6f118188f5015130962053e4b05cbf7ff23a13a50ff1791f543f0ee，Q/manifest SHA0a223a1132db20aa403b8491d78406b2c5bafb6b1a1bdf886541b41b9dec757f。

低分/截断的已有证据分析完成：24错=8真实length60000+16明确错误字母；16/16原生抽取与final明确字母一致，0解析误判/传输错误行。8题有15.2万–19.6万字符推理，均无thinkend/EOS/final，实际返回prompt含xhigh推理策略；反复检视化学结构/假设或枚举模式，不能等同固定token死循环。6/8无重复64-token窗口，全部未见1–512周期重复至少3次的尾部。190普通返回可正常终止，正确174题输出中位3873.5、最长58849tokens；16普通错答中位21984.5。原生注册OpenAIChatCompletion覆写payload字段为max_completion_tokens=60000，丢弃do_sample字段但保留T1；原API seed默认1234经self._seed传递，与评测seed42分层。继承parser仅取message.content，None由并发collector转TIMEOUT且保留usage，评分置0；不是RPC/HTTP超时，也不是审计映射导致失分。未改cap/采样/stop/评分或分母。

诊断报告 `G/diagnostics/gpqa-low-score-analysis-001/REPORT.json` SHA5343712fb85653dd42ee765b65fff67c8bb0af67b41a44eb0e8e2d97e467ff5b、manifest17d9042eb27adce6227352234f20a6ae840694cdabb6915b790e4c5c53996664，保存24失败题完整reasoning/final及原API引用。source-chain-001保留原生四源码，ACTUAL_REGISTERED_PAYLOAD.json SHA56ab5de5fcd249715032dd6c2a0af9d525580d6cbbc7eb84ebc4ffa573b1084d为实际注册子类/长度字段的权威说明；初始父类说明保留，不冒充wire（GPQA只有原生完整解析API）。

历史CPU对照：acc021旧175/198与当前198题doc/prompt/target hashes逐项全同、权重metadata/stat和tokenizer指纹相同；旧9题60K、当前8题，重叠doc32/71/145/147。7题由对变错、6题由错变对，不能用净差1题判定单一源码退化。两次并发64/32、源码版本、prefix策略、调优及服务均不同，非受控baseline；历史答案不复用、旧gate不绑定当前。history-comparison-001 REPORT SHAb8d4b3a0ffcaa1667666ab712f1bb823b157b171619f91612d63bf116bd4555b，manifest5ca563e3369490adaaee45ac4bc0e6229f37ccd6576a532a52f7b936c5d94fb8。现有证据支持“推理未收束而耗尽预算”为8题直接原因，尚不能证明底层BF16/RNG/Mamba数值因果或更大预算一定答对。

ERQA08:07:56+08已原生启动400/C32单次，唯一controller4141102/start612110094/argvSHAd118f283b79d6918cf7c619c6f8f5fb7e82614a89aed7ca8b47b9d7b2dccdb28。新CPU终态等待器76554/start612130549/argvSHA5431366423da028a9ba106df18d33e303bb48bff388c8144c63a335d9d63616a，只等原controller退出后审计完整证据；无新模型启动/GPQA/额外smoke。ERQA原native prompt/data/parser/BaseEvaluator/retry保留，完整wire及真实question_id-index-attempt逐项保存。当前尚无原生全量分数，不宣称通过。每小时monitor已更新到新授权/EC目录，仍只读不补启动。

最新只读进展 2026-10-31T08:15:34.151589+08:00：真实native question_id且完整末次HTTP证据核验 27/400；派发59attempt、HTTP200 27，0HTTP错误；running32/waiting0/preempt0。同一精确8010 health200，源与启动配置保留，磁盘余1402.71GiB。未重启/重跑GPQA/访问8035/提交推送。

已有产物CPU诊断收尾执行前：`finalize_cpu_diagnosis.py` SHA `52f881730b199ba7542fa3177e065808b68518d114a86e5674b9fcda70ed2dc2`，重新hash原GPQA113成员、新Q与三诊断manifest，核当前同源/同API；另存CPU_CONCLUSION、终态绝对路径manifest和READBACK_RECEIPT，无评测/推理/device动作。source_chain两个早先经stdin执行的纯CPU复制脚本现在原样归档标明实际时序，不再执行；不伪造事前回执。

CPU诊断已收尾：CPU_CONCLUSION SHA cde65749efd54128aa964cf61e3925d1e0fa797da39cf9e9359e53ea18b019c5，terminal-manifest-001 SHA7a48f25a8cf2ab8a4d0e859f08e9734b121c08fb544cd021a7c94291d809ef48，READBACK_RECEIPT SHA0c6ba2cace98ff628aa70ab29211c8a510274b68d713b33c89658ee24f13802f，74成员逐项SHA/size通过；原GPQA113成员与旧summary/manifest未变，修正Q及三诊断manifest全部验同，当前完整source/runtime/原startscript相同。直接截断/评分原因已定位，底层模型数值因果仍未证实，不作RNG/BF16/Mamba单因归因。全198真实prompt230–2933，低于6400边界，但不能据此排除并发budget导致的短prompt部分prefill；无实时分支trace不声称回退路径未执行。

最新 2026-10-31T08:21:50.324979+08:00：ERQA真实native question_id完成59/400，派发91attempt，完整HTTP200 59、0HTTP错误；同API健康200/running32/waiting0/preempt0，完整源/三库HEAD-index/原启动脚本核同。全量尚未终态，无ERQA分数或pass结论。小时监控继续。

可复用公共CPU观察器按项目规范参数化词表ID和长度阈值，不把Qwen token IDs/60000硬编码成所有模型默认。12项专用单测/277项全工具测试及validate-local --code通过；scoped state/schema/identity和75个实验文档链接核验通过，不称全仓记录验收。本轮已执行Q的冻结case-helper SHA4213718f不替换、不重审；新增公共副本/测试/验证日志与加强source/runtime/script核对的只读monitor-v2仅另存A新文件并在SUPPLEMENTAL-SHA256绑定，不修改当前原生评测源码。public helper SHA `d402bd94a84a757b1e1a255133265803ab0e26963bce4fd46eb3f73a329471e6`；monitor-v2 SHA `162d695aa95dfb98a80f53a463ae8ed32ebe6513f1a1842a4ccb26dae5fdf52c`。

2026-10-31T08:27:13.861290+08:00 只读最终进展快照：ERQA native question_id唯一完成81/400，已派发113attempt/完整HTTP200 81、0HTTP错误；当前API1336953/start607626732同一listener/argv，health200/running32/waiting0/preempt0，source/runtime/user-script逐项相同，当前无FIRST_HTTP_ERROR/EC错误/终态flag。快照EC/readonly-progress-20261031T082713.json SHA979cfe2eeb1762507d3db326a9eb3cb91aba8630f622fba341342187bb14bb52，绑定observer-v2 SHA162d695aa95dfb98a80f53a463ae8ed32ebe6513f1a1842a4ccb26dae5fdf52c；只归档已读取快照，不发新请求。服务/生产修复/BF16不动，GPQA不重跑。继续原唯一ERQA及终态CPU审计、每小时汇报。

2026-10-31T08:30:21.426714+08:00 heartbeat只读：ERQA真实native ID完成98/400，派发130attempt，完整HTTP20098/0HTTPerror；同API/controller/CPUwatch精确身份active，health200/running32/waiting0/KV0.126349710/preempt0，完整source/runtime/startscript相同。E绑定service新inode窗口213102bytes无新fatal/RPC错误，无EC错误/终态flag。GPQA修正174/198结论未变，无新增诊断、修复或测试。距08:27主动汇报仅几分钟，正常推进静默；小时监控保持ACTIVE，未发推理/重跑/重启/改源cache/访问8035。


### ERQA完整终态及后续边界（核验时间 2026-10-31T16:48:27.496254+08:00）

原唯一ERQA队列及CPU等待审计已于 2026-10-31T10:17:40.864966+08:00 自然结束。400唯一question_id、400native items/evaluated、真实question_id-index-attempt和全wire完整，原生正确252/400，accuracy=63.00%。ERQA无预冻结阈值，只报告native score，不签ERQA通过gate。FINISHED/EC SUITE_FINISHED/COMPLETED及独立终态审计齐全，controller4141102和CPUwatch76554均退出；原native evaluator/helper均退出，容器仅保留。当前精确同API1336953/start607626732/argv/listener健康200，running/waiting/KV/preemption全0，BF16/全部修复/启动脚本及完整源/三库HEAD-staged不变，保留8010，不做服务操作。

401次HTTP尝试均200，0真实HTTP/网络/RPC/设备fatal，0token或usage证据缺口；400逻辑题并非400次HTTP。唯一原生自动重试是ERQA_240/index239：第一次HTTP200但60000token length、final=None/no thinkend/EOS；原native `_single_infer` 在拼接None时TypeError，日志UTC2026-10-31 02:06:58.158（本地10:06:58.158）before_sleep.py:64，`can only concatenate str (not "NoneType") to str`，原Tenacity等待2.28s后第二次9968tokens/stop/thinkend/EOS/非空final。该题真实binding HTTP_attempts=2，未超过原最多5总尝试；这是原生重试，不是monitor/人工请求或整项复跑。最终接受的400答案均stop、0空answer；原始两次raw/header/token和原生日志完整保留。不能把此TypeError叫HTTP/RPC超时，亦不修改原parser或评分。

原生分项：Trajectory Reasoning60.61、Pointing85.29、Task Reasoning65.79、Multi-view Reasoning62.16、State Estimation52.73、Action Reasoning69.44、Other28.57、Spatial Reasoning61.90（均原生百分数，保留其分项分母定义）。不与旧251/400的不同C64/版本/缓存组合计算因果提升，不报性能收益。

终态证据绑定：E/FINAL_SUMMARY SHA7f8afb3c739d9884e16123079d399b8b44292a8ac0913e51da376dc9e7795c3e；E/manifest SHA415e90b59788262e90dc1404b9c1cc1df26cbeaa5cd554d2b275be3fc34efff0（3098成员）；E/evaluation/native-audit SHA028d4791b8784da309f50afed3233cda89fb51389f5ec738081f5c0dcc6d7a34；原生result SHAa155f09dac1a8d5c798b4e57778b054abe6fb7935041dda4dfcfd563ac458824，evaluated SHA834a742ba881b8d225f41dd18bf60d8811fab849722f2ebde807aef99f79e157。EC/terminal-audit-001/report SHA3d79eb71634311ae8aaf8b6a77c87b8410e8dad47454d89cb7dd579b94b07ee2、manifest8522692ef8c43ac052785657acbfd1be35e824e7fef4c751991b515b1d7fb097；EC/COMPLETED SHAc753941cc4ba57a2e17f56c528b280fa1125f16214c2eedd8cc684250626a580，EC/SUITE_FINISHED SHAb64ad9c1c6c2f47d52914660a1f035ef33fcd530f746a0667953c46ac1170497。原等待器6项终态检查均通过；本次仅CPU再读/hash核ERQA3098、原GPQA113、新Q7和终态audit6成员全部大小/SHA，原G/incomplete/summary保持不变；当前service窗口无fatal/RPC错误。没有重跑固定输出旧审计、新推理/GPU/变更/重启/8035/提交推送。

本轮用户新增授权的审计修正、既有证据诊断及ERQA执行已结束；GPQA仍是有效174/198=87.8788%低于88%，模型底层原因未确证，无新GPQA passgate，性能继续冻结。依据用户明确每小时跟踪整体修复进展、低分失败也不自动停止的要求，monitor保留ACTIVE并切换为终态后GPQA低分后续的只读跟踪；不能继续报告ERQA运行，不能自行新增评测、修复、复测或恢复。无后续变化时按小时如实说明无新增进展；整体闭环或用户停止才停用。

2026-10-31T16:54:07.221174+08:00 终态后快速只读：无新增修复/诊断/验证结果。ERQA252/400（63.00%）及GPQA174/198未达88%均不变，旧controller/CPUwatch均已退出、无新formal目录或错误flag；精确8010同API健康200/running0/waiting0/KV0/preempt0，完整source/runtime/原script一致。10份关键summary/manifest/audit/suite回执SHA验同；仅扫终态后service新窗口761bytes，无新fatal/RPC错误；free1402.37GiB。未重解析401份wire、重复full audit、发推理/改生产cache/操作服务/访问8035。距16:48完成通报仅数分钟，保持静默；小时整体GPQA低分后续跟踪ACTIVE，不补启动任何任务。


### 2026-10-31 新授权：仅既有证据深查 xhigh、采样与prefix修复

用户要求继续定位GPQA低分及8题60K，重点核xhigh/现有采样/prefix cache修复，先仅分析已有日志、源码和产物；不重启、不重跑GPQA、不访问8035、不提交推送。沿用同acc023 issue的diagnosis/static-existing-evidence分支，生产及评测配置不改、0模型/设备请求。准备新CPU资产G0/commands/xhigh-sampling-prefix-20261031-v1，输出G/diagnostics/xhigh-sampling-prefix-analysis-001，保留全部原分数/首错/审计。

采集脚本collect_existing.py SHA b364de6e3e8df39edec9121c0c079c93944f8641a4d061d46ad0531414163357，执行前保存外部副本/命令/SHA后，只读当前同API/source/metrics、现有模型template/generation_config、Plugin/native/Gems采样与KV源码、旧acc021原生日志及当前原产物引用；不导入模型/torch/triton，不调用runner。初读发现模板default xhigh、当前prefix_hits_total32000与R5最终32000相同，待绑定时间序列及完整prompt/源码验证后下结论。连接检查第一次因本机Ansible RPC控制进程沙箱失败，非模型RPC；相同PPU-07限定检查在允许本地控制进程后ok3/changed0。

附加CPU源码采集collect_extra.py SHA `d8bcefe25b6c29d4f02a527f7482eca04984899b5f2450dc1690249fa36ab8a6`：只复制当前renderers kwargs解析、model config、Qwen reasoning parser和min/thinking budget/停止判定源码到同诊断extra-sources-001。原28源码collection-manifest不覆盖，不执行模型或新采样。后续模板对照只做已存聊天参数的Jinja字符串渲染/原函数CPU元数据回放，不产生答案或新精度分。

CPU分析执行前绑定：analyze_existing.py SHA `934ff6a00235deb1fe59752b363d6fbfda43c0b1fb6645fc7c5bee6dbec4021a`；仅在既有CPU评测容器中import stdlib/Jinja2，读已冻结28+5份源码、两轮原样本/API，做模板字符串渲染、native payload原函数AST元数据和align分块原函数CPU回放。仅产出字符串/统计，不调用模型、tokenizer、torch/triton或原runner，不生成答案、不评分、不修改任何实际请求参数；CUDA_VISIBLE_DEVICES空、pycache关闭，前后精确8010/source守护。输出独立analysis-001，原COLLECTED/manifest不覆盖。

收尾CPU复核执行前：finalize_followup.py SHA `203decdcb38b98c414a928936068cc393cf062630597c2814c4fc7686280de56`，补实际Qwen parser adapter静态链、native prefix Counter累加/WorkerFL runner选择、已有长度推导边界对照、H/G源快照变更清单；只读/复制/hash，核原参考文件及当前同API/source，输出独立final-review-001/terminal-manifest/READBACK。不调用解析器模型或采样函数，不产生新答案、评分或设备trace。

CPU首收尾退出1：extra-sources-001/manifest原构建时先open再枚举，包含自身0bytes/空SHA；所有实际源码成员未发现漂移。原manifest/失败/已产出final-review-001全保留。改为独立final-review-002复核，严格验证全部非自身成员，并以新绝对路径terminal-manifest覆盖原manifest本身实际SHA，不覆盖首错。finalize_followup_v2.py执行前SHA `2e050670a8058360edf932dfb949c7705b4856dec6cb115b97cfffb67dc81d3d`；没有生产/模型异常或新推理。


### xhigh／采样／prefix 专项只读定位收尾（实际核验 2026-10-31T17:27:14.476441+08:00）

本轮仅分析已有日志、源码和产物。8010仍为API1336953/start607626732，同argv/source/runtime/start-model.sh，health200，running/waiting/KV/preemption均0。0新模型请求、0GPQA复跑、0GPU/编译、0生产或采样/cache修改、0服务动作、无8035/提交推送；BF16及已有修复保留。GPQA有效174/198（87.8788%）低于88%，不签gate、不恢复性能。

1. **xhigh是两轮共有默认策略，不是本轮新增prompt漂移。** 当前model template在enable_thinking未指定/为true时默认reasoning_effort=xhigh；server renderer合并kwargs时排除None，原198请求均无effort/thinking覆盖。逐题核当前和acc021历史198份真实返回的完整prompt与prompt_token_ids全部一致；两份冻结template对原native聊天参数的纯Jinja渲染也198/198等于实际prompt。xhigh加入“仔细验证假设、考虑替代”等指令并打开think；medium仍打开think但不加xhigh指令，low要求简短。模板支持xhigh/medium/low，high会被拒绝。离线对照仅字符串，没有发这些策略的新请求或生成答案。模板没有数值最小思考长度或强制60000；没有替代策略模型输出，不能确认其独立因果贡献或声称降低effort能修好精度。

2. **实际是固定seed的随机采样，不是do_sample=False对应的贪心。** 原native OpenAIChatCompletion纯函数对冻结参数重建：max_completion_tokens60000、temperature1、top_p.95、top_k20、min_p0、presence0、repetition1、seed1234，stop为`</s>`及`<|endoftext|>`。原adapter会移除do_sample=False，但保留T1；并发amodel_call使用TemplateAPI默认self._seed=1234，llmrun未传API seed，评测层42不等于请求seed。min_tokens默认0、ignore_eos默认false、thinking_token_budget默认None；xhigh没有映射成强制数值thinking budget。实际Qwen3 parser adapter进入thinking状态，遇thinkend后转content；8题原token没有thinkend/EOS，不能说它漏掉已存在的final。GPQA未抓raw request wire，上述是原函数+冻结参数重建，不冒充wire或live采样trace。

3. **prefix复用不是本轮直接解释，align状态路径仍需区分。** R5末次和当前prefix_hits_total均32000，两Counter created时间相同，queries从40284增加到303244；native Prometheus用`.inc()`累加。因此GPQA198及ERQA401没有增加prefix命中，不支持“本轮命中错误旧前缀”的解释。queries与唯一HTTP输入token不是同一概念：KV manager按lookup累计，查询token比独立请求prompt总量多516不能据此猜额外HTTP或具体题。零命中不等于align未执行，runner在align模式仍进入按MambaSpec分组的状态初始化/复制/分配路径；没有逐rank块表/状态值/首差logits，不能排除选择性数值影响。

4. **采样回退修复的作用范围已追到实际runner。** WorkerFL实际构造ModelRunnerFL；它自有_bookkeeping_sync已没有硬减4，sample_tokens只在一次真实_sample外为discarded seeded行保存原generator和entry offset并finally恢复，不改有效行/global RNG或采样数学。native GPUModelRunner源码仍有减4，但属于不同类，不能当作当前本地bookkeeping再次回退的证据。全部GPQA输入230–2933虽低于6400，原align split函数的纯CPU元数据回放证明：并发budget不足仍能产生短prompt部分prefill和discard。不能用短输入/零prefix命中断言回退未执行，也没有GPQA逐请求mask/offset证明其贡献。既有R5两长C1命中6400且553完整tokens一致、C8最小10/10通过，只是该范围回归。

5. **8题是输出预算耗尽，不是80000上下文上限或统一6400边界失败。** 最大已观测prompt+output62933，小于实际argv max-model-len80000。8题仍是60000 reasoning、无thinkend/EOS/final；16普通错题final提取均与原生评分一致。按已有真实长度计算，174正确题中69题总长超过6400、6题超过51200；最长正确doc81输出58849、总长59627，原生stop。这是长度暴露对照，不是设备copy事件trace；可排除“每次跨首边界必失败”的统一故障，不能排除选择性状态误差。

6. **历史对照仍不是修复因果实验。** acc021的175/198、9length与本轮174/198、8length共4题截断；完整prompt/token IDs相同，native engine源码、model metadata/tokenizer及权重stat同，但3库HEAD均已改变，Plugin/Gems/FGVLLM分别160/532/70条源路径SHA或存在性不同，另有C64→C32、prefix模式、旧bootstrap/pin047固定选参→当前默认选参等差异。安装包version字符串仍旧，不能把version相同误称源码相同；也不能把净少1题直接归因单一RNG/Mamba/BF16。

结论：已确认直接截断链是“xhigh思考仍未结束→60000输出预算耗尽→content-only为None→原生占位计错”；其中xhigh只是已确认的输入策略，**其导致未结束的独立因果贡献尚未确证**。现有材料排除了新prompt漂移、上下文上限、真实RPC/网络超时、漏掉已有final、以及本轮新prefix复用命中等解释。剩余是共有推理策略与shape/concurrency/算子/align状态数值路径的非独立变量；缺匹配的首差logits、RNG offset/mask和Mamba状态值，不能在不新增受控执行的范围内证明唯一模型底层根因。本轮不擅自扩展测试或调参。

证据：G/diagnostics/xhigh-sampling-prefix-analysis-001；analysis-001/REPORT SHA1bda477ae1eddabc45833b7d977b3ff59b9792ddb983982714c100c4add6b129；final-review-002/CPU_CONCLUSION SHA753065e8de51f6b311dc97a42f6599650931cd5cb6dd525d8af7a012009d8197；terminal-manifest-001 SHA4ab0a51af99bbe3554e9124dd7fe09e0431a6c1ce7595ec0f821cdcc607490ea，90成员大小/SHA全部回读；READBACK_RECEIPT SHA185c0b1a61fe5a4e214e71a2a18e6865f1b241a8d94f9bfa91f6df11f556013f。命令Anew/COMMANDS-TERMINAL-MANIFEST SHA77c39a162d6c1454f6a1f0f30ee92faff24db9df1504d4f38e794d7b8aeae1ef（24成员）。CPU extra采集manifest误收自身空条目及首finalizer退出1均保留；修正版严格验证全部实际成员，新的terminal manifest绑定旧manifest实际SHA，不掩盖首错、不当生产故障。原29参考产物、原分数/首错/修订Q均未覆盖。

2026-10-31T17:56:13.307164+08:00 heartbeat终态后快检：无新增修复/诊断/验证。精确同API1336953/start607626732/argv/listener健康200，running/waiting/KV/preempt均0，完整source/runtime/start-model.sh相同；原ERQA controller/CPUwatch仍退出，EC无FIRST_ERROR/FREEZE/TERMINAL/AUDIT_ERROR。7份既有GPQA/ERQA/新xhigh专项summary及manifest/结论/回执SHA验同，free1402.35GiB；未重解析401wire或重复full审计，0新推理/设备/生产cache变更/服务动作/8035。174/198与252/400不变，底层因果仍未确认。距刚结束的专项报告不足1小时，无新可处理事项，本次静默；整体小时跟踪ACTIVE，不新增执行。只读快检脚本本地SHA7974fe83ef03b974a3acebad2905b41013e29552d40140f3f8e7041b4ae3df45。

2026-10-31T18:53:31.526681+08:00 小时只读核验：无新增修复/诊断/验证。精确API1336953/start607626732/argv/listener保持，health200、running/waiting/KV/preempt全0；完整source/runtime/start-model.sh一致，原ERQA controller和CPUwatch均退出，EC无新FIRST_ERROR/FREEZE/TERMINAL/AUDIT_ERROR。7份冻结summary/manifest/专项结论回执SHA验同，free1402.09GiB。GPQA174/198低于88%、8题60K及ERQA252/400均不变；共有xhigh与align/RNG数值因果未独立确认。仅快检，未新增推理/GPU/重复审计/生产cache变更/服务动作/8035/提交推送。按用户明确小时要求主动汇报无新增结果，继续只读跟踪，未补启动队列或扩展测试。


### 新授权：8题xhigh/medium C1最小单变量对照（2026-10-31）

用户明确授权当前8010，仅针对doc32/71/79/88/127/145/147/185比较xhigh和medium；固定C1/相同seed、BF16、采样和已有修复，不重启、不全量GPQA/8035/提交推送。沿用同acc023 diagnosis issue，显式模式minimal-regression、范围版本化effort-xhigh-medium-c1-001。执行预算16 POST（每题每arm一次），seed1234/T1/p.95/k20/minp0/presence0/repetition1/max_completion_tokens60000、原stop两项、HTTP7200、0retry/0额外smoke/C8。唯一变量chat_template_kwargs.reasoning_effort；按排序题号交替xhigh先/medium先，同题两个body其余字段逐项相同。当前C1和历史C32不同，单次每arm只能证明该小范围影响，不生成新formal分/gate或直接确认底层数值修复。

原生冻结聊天输入/参数、显式xhigh离线Jinja渲染与原actual prompt SHA核同后才派发；每请求保存完整HTTP request头/body、完整response头/实体bytes、prompt/output token IDs、usage、reasoning/final、真实doc-effort绑定、服务新byte/inode日志窗口、源和指标前后。HTTP/网络/身份/证据异常或非预期prefix命中停止后续且无重试；普通length/空final自然收集。产物G0/diagnostics/effort-xhigh-medium-c1-001；脚本/observer/skill bundle先冻结在G0/commands/effort-c1-20261031-v1。

执行前controller SHA `e39944796804e1bc353ec94539939b3dde1ab1ed43527853f90213ba54976949`；复用公共CPU observer SHA `d402bd94a84a757b1e1a255133265803ab0e26963bce4fd46eb3f73a329471e6`，Skill bundle文件SHA `40605374230efd02ad9b4ba62f379c2b7038d5f9c00025d3c00de3194a34c538`。连接限定PPU-07：ok3/changed0/unreachable0/failed0。0模型请求的prepare阶段可修正文档/控制脚本，但不得重放已派发请求；唯一run由RUN_ATTEMPT独占文件保护。

0推理预检已通过：PREPARED SHAe710c428ad3ccbbcea158030777ba02cbe4f743afe354ec0e29c9c4e96934a57；plan SHA70f1a2a7a775b2bc7141e94b4fb4fe943e6e584cc1b21073be5f3ef24199252e。8题xhigh显式render均核原失败prompt同SHA，16payload只变effort、C1/seed/采样预算同。唯一launch脚本执行前SHA `3f6a0bc1557660f65b7ff7c88cd4edde386f4e1e3bc3fe5717adf54cdd37418a`，LAUNCH_ATTEMPT+RUN_ATTEMPT双独占防重放；无新服务启动/停止。

CPU独立终态审计/只读快检/单次等待器执行前SHA：{'audit_effort.py': '3e11b99a7d0e4ff3e97b296fd0d8f14ebe36918f0de1a3273f890cd682fcfd4e', 'readonly_effort_monitor.py': '4fa9f40f84e2e4590a97b7a1464dd4f8b8a736a3eb4cfe1f3f1f2cc5dd3c3389', 'terminal_watch.py': '4e0d1611580c3a604b414cc6c44328c23f7b6ff78b61241c84b29066f094c7f1'}。等待器只等精确driver退出，再对本case原16请求证据执行一次CPU审计；没有模型请求/服务动作/重试，失败只冻结，不恢复队列。stdout放A，不放D避免运行日志污染终态manifest。

最新2026-10-31T19:17:32.393913+08:00：已唯一launch16请求C1对照，driver1079662/start616110234/argvSHAd163bf0c04bc9cdc80a9b98fa5a3435b6a07fa1d56ed6719d3ae7bd6d34c3840；seq0/doc32/xhigh于19:14:37派发，1在途/0完整响应，不把生成token或派发计完成。同API健康200/running1/waiting0/preempt0，prefixhits仍32000，完整source/runtime同。CPU-only等待审计已单次启动，原队列没有并行或重试；不重启、不全量GPQA、不8035。小时monitor将仅监控这个新诊断和终态CPU审计，不再按旧终态空闲判断。

CPU等待器首启动因sha(__file__)的str/Path类型错误退出，尚未创建自身PID回执、0CPU审计/0模型请求；原脚本/terminal-watch.log/已知1130568退出证据保留。原模型driver1079662独立继续，绝不重新launch或补发推理。仅修正独立CPU等待器为v2（SHA `3b8a08e8ba1c2e7408fa9298650a42e4194392259c10e8da13e39aea58801685`），新CPU_WATCH2文件名；已在CPU校验str与Path输入SHA一致，再单次启动CPU等待，不改原推理controller/plan/observer。

2026-10-31T19:21:40.400867+08:00 新诊断真实快照：原driver1079662与CPU等待器2（1202459/start616146219/argvSHA97e1c628c44ce170bf6c32900a8de7f59049c3d7c33afc00f537be8434f3aaee）均精确active；同API健康200/running1/waiting0/preempt0、prefixhits32000不增；仅seq0/doc32/xhigh已派发、0完整响应，累计生成token仍上涨不作完成或ETA。完整source/runtime同，无FIRST_ANOMALY/终态或watch2错误。只读monitor-v2 SHA779f2f67e11f0e6229d4f84dd5824aea0190c956355c4ae4134e801ce051708c；本地progress-current.json SHAd111615462826bdeb949d02dc6ffe6b914caf6b91409af5e77ac8d863f37bf87。既有小时automation已更新到D/A新身份和16请求预算，仍只读不补发。首CPU等待器错误已单独保留并修正，不当模型失败；原16请求controller/plan始终未重启或改写。

2026-10-31T19:54:50.414968+08:00 heartbeat只读：driver1079662/CPUwatch2 1202459精确active，同API1336953/start607626732/argv/listener及完整source/runtime相同，health200/running1/waiting0/KV0.0317558/preempt0，prefixhits32000不增。仅seq0/doc32/xhigh派发，0/16完整响应；generation_tokens由4926686增至4960720仅证明活动，不当完成/得分/ETA，未见FIRST_ANOMALY或watch2错误。首条继续原生收集，不补发或重试。快照本地heartbeat-20261031T1954.json SHAe736bf8338507424b5b55c2f95744a18449d12573180233af8b67e565d4e034d。距启动通报不足1小时，本次正常推进静默；下个小时继续用户主动汇报。没有新推理/源码或采样cache变更/服务动作/8035/提交推送。

2026-10-31T20:57:14.239735+08:00 小时只读核验：原唯一driver1079662与CPUwatch2 1202459精确active；同API1336953/start607626732/argv/listener、完整source/runtime保持，health200/running1/waiting0/KV0.00462930/preempt0，prefixhits仍32000。4派发/3完整响应/1完整pair；当前seq3/doc71/xhigh在途。首对doc32：xhigh52466token/stop/非空final，medium1452token/stop/非空final；两者均thinkend1+EOS248046一次，真实prompt均核对应expected SHA，prefixhits_delta0。原C32该题60K截断在本次xhigh C1未复现，不能把差异直接当原C32根因或正式精度改善。seq2/doc71/medium45740token/stop/非空final也完整，仍待该题xhigh，不能称medium统一短输出。

本次另做纯CPU只读独立回读seq0..2完整request/body/response headers/raw、token IDs和usage，冻结observerSHA核同、三份observation逐项相等，doc32两body去掉effort后全同；原始response.raw SHA依次005724c2b97d463f3687c866be1ed900bd37c9cc6dc2bbaf16c89c0decd34e49 / 635e070302842bd2a415fcbb0cf87e76a04029c416d45dee8225dd4f53bcec24 / 4467a742cf2cd4c5cc7fa6db2e1a801b2b58f443ea2c30e1818e263526126893。不是抢跑16条终态审计，无新POST/设备/重试/源码cache变更/服务动作/8035/提交推送。快照本地heartbeat-20261031T2056.json SHAa7293ef5b07f0a19be87f4848cbdc8ab35e55d84a35402ef1a7ceec7a591041f；无FIRST_ANOMALY/终态或watch2错误，free1402.05GiB。继续原C1队列和自然终态CPU审计，不扩预算或签gate。按用户小时要求主动报告3/16及首pair局部事实。

2026-10-31T21:59:32.224674+08:00 小时只读：5派发/4完整响应/2完整pairs，seq4/doc79/xhigh在途。新完整第二对doc71（medium先、xhigh后）：medium45740/stop/非空final/thinkend1+EOS248046，xhigh60000/length/contentNone/thinkend0/EOS0；两HTTP均200、prompt/output token IDs及usage完整无缺项、prefix命中增量均0。同API1336953/start607626732/argv/listener、source/runtime同，health200/running1/waiting0/KV0.00765938/preempt0，driver1079662/CPUwatch2 1202459精确active，prefixhits32000，无FIRST_ANOMALY/终态/watch2错误，free1402.04GiB。

纯CPU读取seq2/3原完整request/body、response header/raw并复用冻结observer回读，observation逐项同原结果，actualprompt核expected SHA；同题body除effort外完全相同。xhigh raw470581bytes/SHA5a0c2a1a156543369ccb69ff800c8220dbf269349e51ca5f60e89981bfc64cda、output IDs SHA850fb8b9cf3a029fd59e8b0145f0e8b41546ef61e9784313f369c1cd7e98eb00；medium raw330906bytes/SHA4467a742cf2cd4c5cc7fa6db2e1a801b2b58f443ea2c30e1818e263526126893。该题本次C1 xhigh复现60K，medium本次未截断，是单对照局部事实；doc32 xhigh C1仍正常stop，两题不能推成8题统一结论、正式精度改善或排除数值路径。60K/None是有效诊断结果，不是HTTP/RPC超时或新流程错误，原队列自然继续，不重试/停/扩预算。

快照本地heartbeat-20261031T2159.json SHAf016a81f561acd8204d293e3ce48e7c6f8cee8f91a1c9a0bdf6ee2d5c6411d92；未抢跑全16终态审计、未由monitor发POST/改源采样cache/操作服务/8035/提交推送，原唯一controller按已冻结16预算继续。按用户小时要求通知4/16及第二pair事实，保持ACTIVE。

2026-10-31T22:59:48.128243+08:00 小时只读：7派发/6完整响应/3完整pairs，seq6/doc88/medium在途；原唯一driver1079662与CPUwatch2 1202459精确active，同API1336953/start607626732/argv/listener及完整source/runtime相同。health200/running1/waiting0/KV0.0151624/preempt0，prefixhits仍32000，无FIRST_ANOMALY/终态/watch2错误，free1391.86GiB。新第三对doc79：xhigh49012token、medium2506token，均HTTP200/stop/非空final/thinkend1/EOS248046一次、prefix增量0。当前3pairs中medium均更短；xhigh1/3 length而medium0/3，仅报告当前选定3对，不当8题总体或正式精度/唯一底层根因。doc79的历史C32截断在本次xhigh C1未复现，与doc32类似；doc71仍是xhigh60K/medium45740stop的局部截断差异。

只CPU独立回读seq4/5 request/body、response headers/raw、实际prompt与expected SHA、完整token及usage，冻结observer回读逐项一致且两body去effort后完全同。xhigh raw318121bytes/SHAc4ed3ae63253c25bddf7e854ec76a627ba89f522d4ca6789a4e94d1c8374a612；medium raw16611bytes/SHA044afc55367045658634d34319c79eae4ba5b39162f938bfff2a382a2579fdd9。快照本地heartbeat-20261031T2259.json SHA9eed4080c15fae6315d6aaecdb17ef067c03aeb9bb1a7fa662a2f9bf1e6f1545。monitor没有新POST/重试/抢跑终态审计/改源码采样cache/服务动作/8035/提交推送，原16请求controller自然继续；按用户小时要求通知6/16及第三pair结果，保持ACTIVE。

2026-11-01T00:02:47.044214+08:00 小时只读：8派发/7完整响应/3完整pairs；seq7/doc88/xhigh在途，尚不能报第4pair结果。新seq6/doc88/medium完整HTTP200/29330tokens/stop/非空final/thinkend1/EOS248046一次、prefix增量0；纯CPU独立回读request/body、response header/raw、实际prompt与expected SHA、完整token/usage均与冻结observer原结果一致。raw217250bytes/SHA1a28e61eed5ecfcd6f4c9eabe6310e74948f5d3c2755da2d3f6ef2c4055b46b1，output IDs SHA6f97c932c00cd273433f27f523b3ebb2ec426b622e27c5ba247e23b657c4bc8d。

同API1336953/start607626732/argv/listener及完整source/runtime保持，health200/running1/waiting0/KV0.0409903/preempt0，prefixhits32000未增；driver1079662/CPUwatch2 1202459精确active，无FIRST_ANOMALY/终态/watch2错误，free1391.80GiB。累计generation_tokens从5149676增至5213772仅证明原任务活动，不能把在途生成计完成或估ETA。已完成3pairs局部观察保持，未推广8题或formal精度。快照本地heartbeat-20261101T0002.json SHA954deba378d42f5bfa2d00801738e75229a4b1700aa50a0c08345a84b09bc334；monitor未发POST/重试/抢跑终态审计/改生产采样cache/服务动作/8035/提交推送，原16请求队列自然继续。按用户小时要求主动报告7/16与下一步等待doc88/xhigh。

2026-11-01T01:06:15.616128+08:00 小时只读：9派发/8完整响应/4完整pairs（16预算完成一半）；seq8/doc127/xhigh在途。第4对doc88（medium先）：xhigh60000/length/contentNone/thinkend0/EOS0，medium29330/stop/非空final/thinkend1/EOS248046；两HTTP200、prefix增量0。纯CPU回读seq6/7完整request/body、response headers/raw、实际prompt与expected SHA、token/usage均与冻结observer逐项相同，两body仅effort差异。xhigh raw459166bytes/SHA256dfd230724bec1c538c3757782acf4cb919355c795552ecb28e72aecc89e5b；medium raw217250bytes/SHA1a28e61eed5ecfcd6f4c9eabe6310e74948f5d3c2755da2d3f6ef2c4055b46b1。

当前4完整pairs medium均更短，xhigh2/4 length（71/88）而medium0/4，只报告这4题单次C1局部事实；32/79的xhigh本次正常stop，不能推广为8题/正式精度或唯一底层根因。两个length目前均在medium先的不同题中出现；每题只有一种arm顺序，题目与顺序不可独立区分，不能归因为顺序，也不因此擅自补测或改变冻结顺序。普通60K数据自然收集，不叫RPC/HTTP失败。

同API1336953/start607626732/argv/listener及完整source/runtime保持，health200/running1/waiting0/KV0.0469062/preempt0，prefixhits32000未增；driver1079662/CPUwatch2 1202459精确active，无FIRST_ANOMALY/终态/watch2错误，free1391.77GiB。另只读核controller/observer/auditor/watch2/plan/PREPARED共6关键SHA未变，当前doc127服务新inode27006868286/offset5067128窗口471261bytes、SHA51cff833e17ff829e2a675ac202a41c04370a095d1937356855e58d866326bc1，无fatal/RPC/Traceback匹配。快照本地heartbeat-20261101T0106.json SHA4a15e943b777e545254bc8724ca1fe4cfdbbdccc59782bc6a25d747f39efc0c0；monitor未发POST/重试/抢跑终态审计/改源码采样cache/服务动作/8035/提交推送，原16队列继续。按用户小时要求主动报告8/16及第4pair。

2026-11-01T02:00:46.027166+08:00 小时只读：12派发/11完整响应/5完整pairs；seq11/doc145/xhigh在途。新增第5对doc127（xhigh先）：xhigh60000/length/contentNone/thinkend0/EOS0，medium30418/stop/非空final/thinkend1/EOS248046；另seq10/doc145/medium1544/stop/非空final/thinkend+EOS已完整。三HTTP均200、usage/token/prompt证据完整，prefix增量0。只CPU独立回读seq8..10 request/body、response header/raw、expected实际prompt及冻结observer结果逐项核同；doc127两body去effort后全同。raw SHA：seq8 d97da7c96a0c0eeb78d40ec56a7f062325013cefd916f2664cfc16ee014e4375（460041bytes）；seq9 5361a6ccb785611ed053335d11f7ae9ab895dec981e86e39806c6878ab42f57c（217054bytes）；seq10 618421ebbe132ab5759879c0a9ed6aaa6da237b13d8a6492322a6bbeeec5af2c（15140bytes）。

已完成5pairs中medium均更短且0/5 length，xhigh3/5 length（71/88/127）；只限这5个选定题的单次C1结果，不推广8题或正式198精度/gate/唯一底层根因。此前前4对length都发生medium先只是早期观察，doc127本次xhigh先也60K，该简单顺序模式已不普遍；仍无同题反向重复，不能因此彻底排除顺序/时间或数值影响，不补测。普通60000是有效诊断数据非RPC/HTTP超时，原队列继续。

同API1336953/start607626732/argv/listener、完整source/runtime保持，health200/running1/waiting0/KV0.0180482/preempt0、prefixhits32000不增；driver1079662/CPUwatch2 1202459精确active，无FIRST_ANOMALY/终态/watch2错误，free1391.77GiB。快照本地heartbeat-20261101T0201.json SHAf4449bb5135dd465404e152220094af78c7c68d57081d28b6f66b7f2b394a800。monitor未发POST/重试/抢跑终态审计/改源码采样cache/服务动作/8035/提交推送，原16预算唯一controller自然继续。按用户小时要求通知11/16及第5pair结果，保持ACTIVE。

2026-11-01T03:05:17.872349+08:00 小时只读：13派发/12完整响应/6完整pairs；seq12/doc147/xhigh在途。新第6对doc145（medium先）：xhigh60000/length/contentNone/thinkend0/EOS0，medium1544/stop/非空final/thinkend1/EOS248046一次；两HTTP200、prefix增量0。只CPU独立回读seq10/11完整request/body、response header/raw、actualprompt与expected SHA、token/usage均与冻结observer逐项同，两body去effort后完全同。xhigh raw453462bytes/SHA8c049d3dbca3e27930d44f810fdf6ad410fddfbd00ddb31feb57c233021064d9；medium raw15140bytes/SHA618421ebbe132ab5759879c0a9ed6aaa6da237b13d8a6492322a6bbeeec5af2c。

当前6pairs medium均更短且0/6 length，xhigh4/6 length（71/88/127/145），只限这6个选定题单次C1；不能推广全部8题、正式198精度或唯一底层数值根因。正常60000/None诊断结果自然收集，不当RPC/HTTP超时，不重试、改变顺序或扩16预算。同API1336953/start607626732/argv/listener与完整source/runtime保持，health200/running1/waiting0/KV0.0219441/preempt0、prefixhits32000未增；driver1079662/CPUwatch2 1202459精确active，无FIRST_ANOMALY/终态/watch2错误，free1391.76GiB。

快照本地heartbeat-20261101T0305.json SHAc7f2010128e814bb0dc307c9b94ac67dd88165aeb888ef5820f50867f7d13a98；monitor没有新POST/抢跑终态审计/改源采样cache/服务动作/8035/提交推送，原唯一controller自然继续。按用户小时要求主动通知12/16与第6pair事实，保持ACTIVE。

2026-11-01T04:03:46.527518+08:00 小时只读：15派发/14完整响应/7完整pairs；最后第8对的seq14/doc185/medium在途，xhigh尚未派发，不把15派发当15完成。新第7对doc147（xhigh先）：xhigh60000/length/contentNone/thinkend0/EOS0，medium22376/stop/非空final/thinkend1/EOS248046一次；两HTTP200、prefix增量0。只CPU独立回读seq12/13完整request/body、response header/raw、actualprompt与expected SHA、token/usage均与冻结observer逐项一致，两body去effort后完全同；另5份controller/observer/auditor/watch2/plan SHA验同。xhigh raw402915bytes/SHA08681a52bf2abc49b7b3299ed0ea61ef92071dfd651a872d3bf8bfbec3342179；medium raw144497bytes/SHA9db684ffec7328828d112ced3eee21665953a03d4475e1275308de6589749562。

目前已完整7pairs medium均更短且0/7 length，xhigh5/7 length（71/88/127/145/147），只限当前7题单次C1，不推广未完成第8题/正式198精度或唯一底层数值根因。普通60000/None原流程继续，无retry/预算或顺序修改。同API1336953/start607626732/argv/listener及完整source/runtime保持，health200/running1/waiting0/KV0.00520645/preempt0、prefixhits32000未增；driver1079662/CPUwatch2 1202459精确active，无FIRST_ANOMALY/终态/watch2错误，free1391.73GiB。

快照本地heartbeat-20261101T0404.json SHA8c36f5ba2f4a420399877c060857be8765b756a89701bc36e7d6b56a2fba91e1；monitor未发POST/抢跑终态审计/改源采样cache/服务动作/8035/提交推送，原16请求唯一controller继续最后一对。按用户小时要求主动通知14/16，保持ACTIVE，等原driver和独立CPU审计自然终态才报全范围完成。


### 8题effort C1对照完整终态（2026-11-01 05:10–05:12核验）

本次8题对照16/16完整、独立CPU审计及300成员回读通过，原driver和CPUwatch2均退出。xhigh5/8截断，medium0/8，8题medium输出均更少；仅限该选定单次C1范围，不是完整GPQA精度通过。原GPQA174/198仍未达88%，ERQA252/400终态保留；同BF168010健康空闲，未重启、全量复测或改默认策略。小时监控转终态后只读整体跟踪，不再派发测试。

原唯一controller于2026-11-01T05:06:53.111828+08:00写入FINISHED；独立CPU等待审计于05:07:06.566740完成，CPU_AUDIT_EXIT=0。driver1079662和CPUwatch2 1202459自然退出，16次HTTP均200，0重试、0额外模型请求、0真实HTTP/RPC/device fatal证据。D/FINAL_SUMMARY为valid-paired-C1-diagnostic-complete，独立report为valid-paired-C1-diagnostic-evidence，无新formal gate。

| doc | xhigh输出token／结束 | medium输出token／结束 |
|---:|---:|---:|
| 32 | 52466／stop | 1452／stop |
| 71 | 60000／截断 | 45740／stop |
| 79 | 49012／stop | 2506／stop |
| 88 | 60000／截断 | 29330／stop |
| 127 | 60000／截断 | 30418／stop |
| 145 | 60000／截断 | 1544／stop |
| 147 | 60000／截断 | 22376／stop |
| 185 | 54011／stop | 16983／stop |

固定C1、seed1234、原T1/p.95/k20/minp0/presence0/repetition1/max60000与原stop、同BF16/现有修复及8010。同题body只有effort差异；4题xhigh先、4题medium先。5个xhigh length（71/88/127/145/147）均reasoning-only/no thinkend/EOS/final；medium8/8均stop/thinkend/EOS/非空final。输出总量xhigh455489、medium150349。支持当前选定8题C1中策略影响输出长度/终止的局部观察，5个本次重现截断题在medium下均得到final；没有计算/证明答案正确率提高，也没有部署medium为默认策略。

原C32的8题截断，本次xhigh C1只重现5题，32/79/185本次xhigh正常stop；不能据此单独确认原C32全量低分根因，或排除采样回退/align数值路径。每题每arm仅一次，无同题反向顺序/多seed重复；length在两种顺序均有，不支持仅一种顺序必致length，但不能彻底隔离顺序、时间或数值非确定性。没有补测、调参、额外smoke/C8或全量请求。原有效GPQA174/198<88%及failed-score、旧incomplete/首错与修订Q均保留，正式性能继续冻结。

独立CPU审计核16唯一seq/8唯一doc/2arms、完整原请求、仅effort变量、16HTTP200、所有实际prompt/token IDs/usage、源与runtime前后一致、全程prefixhits增量0。主任务本次只读再核45冻结输入、296原terminal manifest及300独立audit manifest全部成员size/SHA；没有重跑原审计。05:10同API1336953/start607626732/argv/listener/source/runtime相同，health200/running0/waiting0/KV0/preempt0；05:12另核7份controller/observer/auditor/watch2/plan/用户start-model.sh/monitor SHA均同，原脚本875788ff不变。

16份raw usage合计输入10746、输出605838；同实例prompt计数差10746、generation差605838、prefix查询差10746恰好相等，prefixhits仍32000。这是累计服务指标核账，不是独立TCP或逐rank trace。D/wire保留完整request.http、请求实体、完整解析response头及实体bytes、prompt/output IDs、reasoning/final/usage和真实seq-doc-effort绑定。完整服务窗口已冻结；其后只读尾部inode27006868286/start7447358/1758bytes/SHAf3a8023443add30ce8715c1bb02d02cd72dce5b82a6eea3b5e8188b4aff677f7无fatal/RPC/Traceback。0生产改动、0重启/8035/提交推送，保留BF168010健康空闲。

权威外部目录D=G0/diagnostics/effort-xhigh-medium-c1-001、A=G0/commands/effort-c1-20261031-v1：

- FINAL_SUMMARY SHA dc0619142837f85a0fd338eee6f372898a95d032b56a2d942614b9b6e850f241；FINISHED bd13ee1911af2ced4ecc26a7f7d17330f5ad2a0348103bd68ce592ee51525e24。
- terminal-manifest f4e807d65c56e05c4f13e1c9b929601f2560e5d1cf33d729133403ae8f70440f（296）；READBACK a9501096a69f09a5777e98e2acd51d67f90e8cd7fe52e748cfea77d127ee7cb0。
- 独立report 3002b8fbbeb57f76625c73e0b9eb67456aee7ec748e0a4eaa1ebef5d8ad369dd；audit manifest f719a49bf6d151567608d08470a484593eb56e6583f2a0b2d6140907e0792bd4（300）；audit READBACK 392d43dd93e2abf42af0843d25e0c722f1b6c4f8bb52c676e9320dd9f0596857。
- A/CPU_WATCH2_COMPLETED SHA78db7f1b82e2e2060fc2dd17a487c11982f52d2bf49c87cdd93744bd1e816208；CPU_AUDIT_EXIT=0。最终driver.log/cpu-audit.log SHA分别10c0487e27b8cf14532a0fba204c41759c13d3719340bd8ad33d196291d0ff01／e2a2d061f948bcdc07ad4c7d53f49a14fec10b3fbe1c8654078e296e7ce2923f。
- 本地补充只读复核/private/tmp/acc023-effort-c1-20261031/terminal-review-20261101T0509.json SHA8a055f6dde339bf81b13ee384611d23daf73bdec14006c9c15a66f0b40304b64；权威完整原件与审计均在远端D/A，不依赖临时文件。

本次对照已结束，不再派发或重跑审计，不改变默认effort。整体GPQA正式仍未达标；依据用户明确小时跟踪整体修复的要求，monitor保留ACTIVE并转为终态后只读后续，不能继续报告本对照运行或自行开展下一批测试/修复。全部整体任务完成或用户停止才停用。


2026-11-01T06:07:50.594645+08:00 终态后小时只读：本小时无新增诊断/修复/验证。16/16对照及独立CPU审计终态不变（xhigh5/8 length、medium0/8），原driver1079662/CPUwatch2 1202459保持退出；精确同API1336953/start607626732/argv/listener/source/runtime保持，health200/running0/waiting0/KV0/preempt0，generation5525333/prefixhits32000/prefixqueries313990均未增。7份关键summary/manifest/audit/GPQA修订回执/原启动脚本SHA核同；仅新增服务窗口inode27006868286/start7449116/end7449281/165bytes/SHA9bad384c2d4b96e8b76867e12532309087ece869a5356d551816874c2b0981a2，无新fatal/RPC/Traceback。未重读605838tokens/全300成员、未重复审计或发POST/改源采样cache/操作服务/8035/提交推送。快照本地heartbeat-20261101T0608.json SHA3f919664c84baefc7daadf13a0963791732ecf6cc2f4b9b9b41b0acdead8cb9e。原GPQA174/198仍未达88%，medium正确率/正式分未验证；保持用户小时只读后续，无新授权不开展下一项测试。

2026-11-01T07:06:52.825249+08:00 终态后小时只读：本小时无新增诊断/修复/验证。16/16小对照及审计保持完整终态，原driver1079662/CPUwatch2 1202459均退出；精确同API1336953/start607626732/argv/listener/source/runtime保持，health200/running0/waiting0/KV0/preempt0，generation5525333/prefixhits32000/prefixqueries313990未增。7份关键冻结回执与原脚本SHA一致；只读服务新窗口inode27006868286/start7449281/end7449446/165bytes/SHA877c20becf2f9c5833481c7a3881d648b6a1be927be15bdb598c15d17a1a2351，无新fatal/RPC/Traceback。未重新解析全token/300成员或重复审计，monitor未发POST/改源采样cache/操作服务/8035/提交推送。快照本地heartbeat-20261101T0707.json SHAee2b272686b59c0cf458c7c64a11bd95e820c4cf7d86814465172a86794009a9。GPQA174/198低于88%仍开放，medium正确率/正式分未验证；按用户要求继续小时只读后续，不自行开展新测试。

2026-11-01T08:03:27.965920+08:00 终态后小时只读：本小时无新增诊断/修复/验证。16/16对照及独立审计终态保持，driver/CPUwatch2均退出；精确同API1336953/start607626732/argv/listener/source/runtime不变，health200，running/waiting/KV/preempt均0，generation5525333/prefixhits32000/prefixqueries313990未增。7份关键冻结回执与原脚本SHA一致；服务新窗口inode27006868286/start7449446/end7449611/165bytes/SHAc507aee50ba9c3df0d817b3114a8f3dd4fe7a5282e2f9c2fbacf22bc750b58f2，无新fatal/RPC/Traceback。快照本地heartbeat-20261101T0803.json SHAfa597548e1437f0c9f9df1f9306bd451860e2cd4e2f99eaf6231104b91baa325。未重解析全token/300成员或重跑审计，未发POST/改策略源码cache/操作服务/8035/提交推送。正式GPQA174/198仍低于88%，唯一原C32模型根因未确证；继续用户要求的小时只读跟踪，不自行新增测试。

2026-11-01T09:10:56.413983+08:00 终态后小时只读：无新增诊断/修复/验证。16/16对照与独立审计保持终态，原driver/CPUwatch2均退出；同API1336953/start607626732/argv/listener/source/runtime保持，health200，running/waiting/KV/preempt均0，generation5525333/prefixhits32000/prefixqueries313990未增。7份关键冻结回执及原脚本SHA一致；新增服务窗口inode27006868286/start7449611/end7449776/165bytes/SHAcd713b395e04ecf3d36a53935517b9066f3ea31e420e1ef3b067c1fb5783a844，无新fatal/RPC/Traceback。快照本地heartbeat-20261101T0911.json SHAf17b8a65fab2737379d84ce99f04b820ca85d1ae2d8fda0d55e20d4967cefbee。未重新解析全部token/manifest成员或重跑审计；未发POST/改源码策略cache/操作服务/8035/提交推送。正式GPQA174/198仍未达88%，原C32唯一根因未确证；按用户要求继续小时只读跟踪，不新增测试。


### 已有8题final答案核对（用户新指令，纯CPU）

用户要求先核对已有xhigh/medium最终答案和标准答案，区分截断缓解与正确率变化，再提出最小验证方案。本轮仅CPU读取冻结16响应、native strict-match任务/样本与gold绑定，0新模型请求/0重启/0生产或评测代码修改/0访问8035/0提交推送。新分析脚本归档于G0/commands/effort-answer-review-20261101-v1/answer_review.py，SHA 3f135b9dd8703e7e0c19b727e3c93913b1eed981a3365adfcabcd252837449bd；结果使用独立G0/diagnostics/effort-answer-review-001，不覆盖原对照及审计。先以198原native样本逐项校准严格regex和exact-match，再对8题fixed-denominator计数；None/length计错，不从reasoning取答案。后续方案只记录，不执行新请求。

首个CPU核对在doc185 raw gold与预处理choice直接比较断言退出1（非生产故障，0新请求）；原生preprocess移除命名中的[c]，gold仍C。首脚本/日志/已输出7题保留；v2仅抽取SHA绑定原utils.py的preprocess函数，恢复精确原生预处理，独立输出effort-answer-review-002，脚本SHA 12c8a27a297b2768b578ad5e52379d091dc12594399e3f465dc05e9da2a61460，不覆盖001。


### 8题final与gold核对完成（2026-11-01T09:30:09.624303+08:00）

仅CPU复核已有16响应。冻结task strict-match regex最后匹配、take_first与忽略大小写/标点exact-match规则，先对原198 native filtered_resps和得分逐项校准198/198一致，再对本8题评分；None/length作为错误保留固定分母8，不从reasoning补答案。gold由原samples target/target_hash与同题冻结inputs绑定，选择顺序及原生preprocess后的正确选项逐项验同。doc185原Correct Answer中的[c]由原生预处理移除，gold仍C；不修改数据集、gold或parser。

| doc | 标准 | xhigh最终答案 | medium最终答案 | 结论 |
|---:|:---:|:---:|:---:|---|
| 32 | B | A（错） | A（错） | 均错 |
| 71 | A | 截断，无final | B（错） | 截断缓解但仍错 |
| 79 | D | D（对） | A（错） | 对→错 |
| 88 | A | 截断，无final | A（对） | 截断→对 |
| 127 | A | 截断，无final | A（对） | 截断→对 |
| 145 | A | 截断，无final | A（对） | 截断→对 |
| 147 | D | 截断，无final | C（错） | 截断缓解但仍错 |
| 185 | C | A（错） | A（错） | 均错 |

xhigh正确1/8=12.5%，medium正确3/8=37.5%；5个截断→有final中3个答对（88/127/145）、2个仍错（71/147），doc79由对变错。净增2题，仅属于这8个原截断难题、单seed单次C1；不代表全198分数提升，不能拼回旧正式174/198，也不说明medium可作为默认。原GPQA174/198<88%及所有旧incomplete/首错保留，无新gate，性能仍冻结。

下一步最小方案仅记录未执行：doc79（答案退化）与doc145（截断→正确）各做xhigh/medium一次，共4POST，C1/seed1234/原采样/max60000/BF16/现有修复及同8010保持，0retry、不重启或改变prefix/cache策略；逆转各自上轮顺序：79 medium→xhigh，145 xhigh→medium。逐arm完整token与旧结果比较并核正确率/length/thinkend/EOS、source/runtime和prefix/preempt。若同arm重复不一致，先记录数值/历史/顺序不确定性，不把effort当唯一根因；若一增一退可重复，确认局部策略取舍仍不推广全量。4条结束即停，不自动加seed/并发/全量；未来全量策略和正式gate另行冻结授权。

权威新证据G0/diagnostics/effort-answer-review-002/REPORT.json SHA 0a29ee5bc229a994dbba9a1ebe17b3251b22e930f415e0c22379266498957569；commands/effort-answer-review-20261101-v1/terminal-manifest.json SHA 9f4bbe92e298de322550d4491ab1c58b4bbdb4453aa6f260802a4bea64683aa1（37成员）、独立INDEPENDENT_READBACK SHA ba0a9109be3919819b91f5ccc8a33f1fb338a9d292c40914a638a551617b05c3；proposal SHA 5db264fdf6fec2b1dfab8f3763e276f8bab68b52ded02141aa203da8df8cd174。v2 CPU_EXIT=0，原始001 CPU格式断言失败、原脚本/7题partial/日志和FIRST_CPU_ERROR_REVIEW均保留。只CPU抽取SHA绑定native preprocess AST；没有重跑旧固定auditor、评测/模型、导入模型或设备操作。运行只读核验同API1336953/start607626732/source/runtime健康200且idle，generation5525333/prefixhits32000/prefixqueries313990不增。0新请求/生产或评测源码变更/服务动作/8035/提交推送。


### 用户授权4条反序C1复核（2026-11-01）

最新用户明确授权当前8010复核doc79和145，共4条，顺序79 medium→xhigh、145 xhigh→medium，C1/seed1234/原请求body采样/BF16及所有修复保持，4条即停。禁止重启/8035/全量/提交推送。调用项目精度minimal-regression及diagnosis方法，用户4条/C1边界覆盖默认额外smoke/C8，无补发重试。当前同API1336953/start607626732/source/runtime健康空闲，旧16请求driver及CPUwatch退出。独立D=G0/diagnostics/effort-reverse-c1-001、A=G0/commands/effort-reverse-c1-20261101-v1；controller SHA aaa4dc93846dedfbb653e9564f69de07b2123de62dc431f10e7c9602a5418afa，repeat helper SHA d1de43fb2f67e69a7fd6095fe4360ef8a89ff08299a9294635f6ba28ab5cdff5，独立CPU auditor SHA 1c112425fff64752eb3c30a953fd96e6c24b91ac2ac1d63aa6253ff35e94e5ca，只比较完整同arm prompt/output IDs、首差位置、final文本/gold、finish/thinkend/EOS及源前后。五项纯CPU首差边界检查与源码compile通过；0模型请求。先归档上述命令再prepare/唯一launch；旧D和审计保持只读不覆盖。新请求/CPU等待器PID和结果后续写回同记录，不凭派发宣称完成，不估ETA，无新formal gate。

prepare已原生退出0，PREPARED SHA46dc2d4e155f08e45c812f9a862682516a84c3efb822dfe2f72a5032af213c09，plan SHA1a800735d03cd0b034df02c96ac206b160cd345df22d82b3832760bcf0102a4c；归档唯一launch_once.py SHA 6891882fcd3289c9c4ee3029a4347f1044b46a08bbabc4d04883d0bc6b047fb3，A/LAUNCH_ATTEMPT及D/RUN_ATTEMPT双独占防重放。唯一模型driver只顺序4POST，独立CPUwatch等待该driver退出后调用一次审计，stdout均放A、不会绑定运行中stdout进入D终态manifest。现在执行已授权唯一launch；不启动/停止服务。


2026-11-01T09:38:57.515734+08:00 四条反序C1已唯一启动：2026-11-01T09:38:28.473242+08:00派发seq0/doc79/medium，1派发/0完整返回，0完整pair。唯一driver1701290/start621293347/argvSHA82c3470d6bcaba67f7c6717197c8884a6e615cc96cae8967b2509e99e448fe2f；独立CPUwatch1701313/start621293357/argvSHA571cc4596afaa57595b8d710e350167acdf91001c0b2db41d6c4ec61487a4ea8，两者精确active。当前同API1336953/start607626732/argv/listener及source/runtime保持，health200/running1/waiting0/KV0.00116634/preempt0，prefixhits32000未增。已CPU按原terminal-manifest核14个唯一基线raw/body/input/result成员、4新body逐字节同原arm、strict-scoring-contract与前次002manifest绑定一致；原start-model.sh SHA875788ff同。新服务窗口无fatal/RPC/Traceback。完整证据写独立D=G0/diagnostics/effort-reverse-c1-001，A=G0/commands/effort-reverse-c1-20261101-v1；独占LAUNCH_ATTEMPT/RUN_ATTEMPT已消费，不重放。0服务/生产改动、0额外smoke/C8/全量/8035/提交推送，正式GPQA174/198与ERQA252/400仍原终态。原唯一driver负责剩余3POST，4条即停；watcher仅CPU等driver自然退出后审计，不能手动补发。快照本地progress-initial.json SHA afec93f3afd74c1f8fdd18e23c8ba3150235c9c658e24d9c5f70925676075ec0。


2026-11-01T09:42:17.089499+08:00 当前4条反序C1：2派发/1完整响应，seq1/doc79/xhigh在途，0完整pair。首条seq0/doc79/medium=2506tokens/HTTP200/stop/非空final A（goldD，错），原arm同为A/错；完整2506输出IDs和prompt IDs均同，reasoning/final文本完全同，prefix增量0。只是首个arm已回读，不泛化剩余3条/正式198。driver1701290/CPUwatch1701313精确active，同API健康200/running1/waiting0/KV0.00203208/preempt0/prefixhits32000，source/runtime同，无FIRST_ANOMALY或终态/watch错误。原客户端继续剩余序列，4条即停；monitor已更新新D/A/PID及只读快检，不重放launch。快照SHA e919df0dd0c79fb2552cbca606756720cdf81d122d4ae2d7e4e7d3e9b36b7b27，仍0服务/生产改动、0额外请求/全量/8035/提交推送。


2026-11-01T10:15:05.315515+08:00 小时只读：本小时无新增完整响应，仍2派发/1完整/0完整pair；seq1/doc79/xhigh在途，不能用生成token增长当完成或估ETA。seq0 medium2506stop/答案A对goldD仍错、同arm完整token/prompt及文本一致事实保持。精确同API1336953/start607626732/argv/listener及完整source/runtime保持，health200/running1/waiting0/KV0.027282783829930546/preempt0，prefixhits32000未增；原唯一driver1701290/CPUwatch1701313精确active，无FIRST_ANOMALY/终态/watch错误。8份控制/plan/PREPARED/原script SHA均核同，当前seq1日志窗口inode27006868286/start7471251/end7749273/278022bytes/SHA7e25925e149f9ad7c9903ada4695578d540aad318b5d681275ee04a7f3b4e3c9无新fatal/RPC/Traceback。free1391.53GiB。快照heartbeat-20261101T1015.json SHA682f91d6f01bbf21e0ca1bd83039dd0159f99c4dceb0784101bddf70350733c9；monitor只读，0新POST/重试/审计抢跑/源配置cache变更/服务动作/8035/提交推送。原4预算唯一队列继续、4条结束即停，下一步等待原xhigh及doc145两arm自然完成后独立CPU审计；正式GPQA174/198/无gate与ERQA252/400不变，保持用户小时汇报ACTIVE。


2026-11-01T11:10:05.045937+08:00 小时只读：3派发/2完整/1完整pair，seq2/doc145/xhigh在途，doc145/medium尚未派发。新完成seq1/doc79/xhigh=49012tokens/HTTP200/stop/非空finalD（goldD，对）；同arm全部49012输出IDs与prompt IDs、完整message/reasoning/final均与原轮一致，无首差。已CPU独立回读raw/header/body/actualprompt/token/usage并与冻结observer逐项相同，raw SHA41418f014cbb469320aa7c1deaa36444637b810b7fb775cc9e318eacb9fc2401。doc79反序后仍xhighD对、mediumA错，两个arm均逐token重现原轮（medium2506、xhigh49012）、prefix增量0；该题较短medium答案退化在本次反序复核重现，只限此局部，不推广doc145/全198或唯一原C32根因。

同API1336953/start607626732/argv/listener/source/runtime保持，health200/running1/waiting0/KV0.033198662915133625/preempt0，prefixhits32000未增；原driver1701290/CPUwatch1701313精确active，无FIRST_ANOMALY/终态/watch错误。8控制资产、plan/PREPARED/原script SHA核同，当前seq2新日志窗口inode27006868286/start7847971/end8192367/344396bytes/SHAcc131c3ec0fad131c29c04c2d3b8f97d53ed1f737ae0ec6a2c86dc2f062ef5b0无fatal/RPC/Traceback，free1391.53GiB。快照heartbeat-20261101T1110.json SHAcb1ea7413703da762086d7d90e69ab063b9cab57c614ed78f9124685ff447ff6；monitor只CPU读原返回，0新POST/重试/全4审计抢跑/源配置cache变更/服务动作/8035/提交推送。原唯一4预算队列继续doc145两arm，4条结束即停，再原CPUwatch独立终态审计；正式GPQA174/198和ERQA252/400不变，保持小时ACTIVE。


### 4条反序C1复核完整终态（2026-11-01T12:24:23.599485+08:00只读回读）

原唯一driver于2026-11-01T11:27:40.380033+08:00结束，CPUwatch独立审计于2026-11-01T11:27:42.345490+08:00完成、CPU_AUDIT_EXIT=0；driver1701290与CPUwatch1701313均已退出，4派发/4完整HTTP200、2完整pairs、0retry、0额外请求。用户本次4请求预算已用完，不能补测或修改默认策略。

| doc/标准 | arm | 输出token | 最终答案/得分 | 结束 | 与原同arm重复性 |
|---|---|---:|---|---|---|
| 79/D | medium | 2506 | A，错 | stop | 完整prompt/output IDs及message完全相同 |
| 79/D | xhigh | 49012 | D，对 | stop | 完整prompt/output IDs及message完全相同 |
| 145/A | xhigh | 60000 | 无final，计错 | length | 完整prompt/output IDs及message完全相同 |
| 145/A | medium | 1544 | A，对 | stop | 完整prompt/output IDs及message完全相同 |

反转每题arm顺序后，4个arm全部逐token精确重现原轮，无首差（first_difference_index=null）；reasoning/final文本、请求body及实际prompt IDs均相同，prefix命中增量0。本轮两题xhigh1/2、medium1/2；medium在145避免截断并答对，在79仍把正确D变成错误A。因此观察到可重复的局部取舍，不能把“更短/不截断”当作“统一更准确”，也不把它拼入旧8题/198分。限定同实例、同seed1234、选定2题、每arm新增一次；尚不证明全量策略收益或原C32唯一底层根因，不据此单因归因/排除BF16、RNG修复或align路径。原正式GPQA174/198<88%及旧原incomplete/首错保持，无新gate，性能仍冻结。

独立CPU原审计验证4唯一seq/2doc/两arm、完整HTTP实体与解析头、原body/唯一effort变量、prompt/token/usage、source/runtime前后一致以及4比较结果；本小时只读再核16冻结输入、91原terminal-manifest及95独立manifest成员全部size/SHA，4raw/prompt/output IDs/final与标准答案逐项回读，未重跑固定auditor或发新请求。1324输入tokens与113062输出tokens恰等于同实例prompt/generation计数差，prefix查询差1324、prefixhits仍32000；累计指标核账不是独立TCP/逐rank trace。

12:23同API1336953/start607626732/argv/listener/source/runtime相同、BF16/原script875788ff/现有修复保持，health200/running0/waiting0/KV0/preempt0，原driver/CPUwatch退出。完整本轮service窗口无fatal/RPC/Traceback；结束后尾部inode27006868286/start8324831/end8325262/431bytes/SHA153a5fd4cbdefd4d0edc05261c735b363907cedbc7f144759033ae206f289189亦无新错误。0服务/生产源码/采样/cache策略操作，0额外smoke/C8/全量/8035/提交推送。

权威原件D=G0/diagnostics/effort-reverse-c1-001，A=G0/commands/effort-reverse-c1-20261101-v1：

- FINAL_SUMMARY SHA 00b1b6e61f81cbe8bdf8533df0e493eb549dcec83cd07504a92a3c7a56d56ee8；FINISHED c131badc88b5ddb5102b035104cb2da350cae36bc4dba117659c8bc94ed97da0。
- terminal-manifest SHA 21d992f6582a4ab860b1c1ceb7f1432030c0f62b828684d8f960f4786f024665（91），frozen-inputs 64bcf7edb14766858856f33b93086ab3943d1cb7dab6b443f78f7f5660ab8ad5（16）。
- 独立report 8d44854ab699dde49d06ae0567dbbbd57f1d055bb4ca8950d4f2ccd5ca3560e9；audit manifest 165b6a9542c32f1a7c3cc1b7e5d8a684aa624ecd75d17b98af844388bf6adac0（95）；audit READBACK 18608375ad0a0eb991815c46661f25abc57db993542cb0f313698dce740f4d64。
- CPU_WATCH_COMPLETED fccbe720f7e6d234bf00e83c9a6be8585b726c3941086981a0f69300be0be76b；最终driver.log ce45bfe189a311183371107dddaf1307fa71a262f4a3c8f943365fee676a7f5a；cpu-audit.log d55c2a0baa04ff2497ce59d88a8e555f484036b9374920acab7e52b1394878fd。
- 本地补充只读review /private/tmp/acc023-effort-reverse-c1-20261101/terminal-review-20261101T1224.json SHA d9589c31fd8ba77123513a57c409462ee9dc16057e6878a3cfab7e4e0831670a；权威完整原始请求/响应/token和独立audit均在远端D/A，不依赖临时文件。

本次4条任务完成并已停止，不再报告运行或等待审计。整体正式GPQA问题未闭环，依据用户要求保留ACTIVE每小时整体只读后续；没有下一批模型/代码/配置操作授权，始终保持当前8010。


2026-11-01T13:25:19.393088+08:00 终态后小时只读：无新增诊断/修复/验证。4/4复核及独立审计终态保持，原driver1701290/CPUwatch1701313均退出；同API1336953/start607626732/argv/listener/source/runtime保持，health200，running/waiting/KV/preempt全0，generation5638395/prefixhits32000/prefixqueries315314未增。7份关键冻结回执及原script SHA一致；服务新窗口inode27006868286/start8325262/end8325427/165bytes/SHAa41401b46c60bd6b146cb32c77c363f95f17e4053b323e243d1e2a7183da2bb1无新fatal/RPC/Traceback。快照heartbeat-20261101T1325.json SHAe0da562cbe80335305246752c1b05c534788f6f5db258211c76b22e41835ab60。未重读全113062tokens/95成员或重复审计，0新POST/源配置cache变更/服务动作/8035/提交推送。局部反序取舍与原正式GPQA174/198<88%结论保持，唯一原C32根因仍未确证；无下一批授权，继续用户要求的小时只读后续。


2026-11-01T14:29:47.846607+08:00 终态后小时只读：无新增诊断/修复/验证。4/4反序复核及独立审计保持完整终态，原driver/CPUwatch均退出；同API1336953/start607626732/argv/listener/source/runtime保持，health200、running/waiting/KV/preempt全0，generation5638395/prefixhits32000/prefixqueries315314未增。7份关键冻结回执及原script SHA一致；同inode27006868286日志窗口start8325427/end8325427/0bytes/SHAe3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855，本窗口无新增日志或新fatal/RPC/Traceback。快照heartbeat-20261101T1427.json SHA27a9091b3846324e6d44e2def4f64469f802d2e9e033e95b1f4f32c5e4ebf31b（记录时间以实际工具14:29为准）。未重读全raw/95成员或重复审计，0新POST/源配置cache变更/服务动作/8035/提交推送。正式GPQA174/198<88%及原C32唯一根因未确证仍开放；无下一批授权，保持小时只读跟踪，不新增测试或改变策略。


2026-11-01T15:28:09.954434+08:00 终态后小时只读：无新增诊断/修复/模型验证。4/4反序复核及CPU审计终态保持，原driver/CPUwatch均退出；同API1336953/start607626732/argv/listener/source/runtime保持，health200、running/waiting/KV/preempt全0，generation5638395/prefixhits32000/prefixqueries315314未增。7份关键冻结回执及原script SHA一致；服务窗口inode27006868286/start8325427/end8325757/330bytes/SHA912eb437ec245b2ad23c92babdff2a90383e985824295b45a6058e0f479be0c8无新fatal/RPC/Traceback。快照heartbeat-combined-20261101T1528.jsonl SHAcba22f1226280dc18efd3ae5f93179bd3384bf9a9179a54a895078e8eb069cbc。未重读全部raw/95成员或重复审计，0新POST/源码配置cache变更/服务动作/8035/提交推送。正式GPQA174/198未达88%、原C32唯一根因未确证仍开放；无下一批授权，继续用户小时只读后续，不新增测试或修改策略。


2026-11-01T16:32:20.991301+08:00 终态后小时只读：无新增诊断/修复/模型验证。4/4反序复核与独立审计终态保持，原driver/CPUwatch均退出；同API1336953/start607626732/argv/listener/source/runtime保持，health200、running/waiting/KV/preempt全0，generation5638395/prefixhits32000/prefixqueries315314未增。7份关键冻结回执及原script SHA一致；服务窗口inode27006868286/start8325757/end8325922/165bytes/SHAc74176c1a7a4aaaaddd3b84c6ffa8029b0c5d47c55b4606a95386f801325bf09无新fatal/RPC/Traceback。快照heartbeat-combined-20261101T1633.jsonl SHAa16dbd5a62e5217278c23704c94f87df2f21a3d5d055fcfcedf929a6b97de5a3（实际工具16:32）。未重读全部raw/95成员或重复审计，0新POST/源码配置cache变更/服务动作/8035/提交推送。正式GPQA174/198未达88%、原C32唯一根因未确证仍开放；无下一批授权，继续用户小时只读后续，不新增测试或修改策略。


2026-11-01T17:32:01.799146+08:00 终态后小时只读：无新增诊断/修复/模型验证。4/4反序复核与独立审计终态保持，原driver/CPUwatch均退出；同API1336953/start607626732/argv/listener/source/runtime保持，health200、running/waiting/KV/preempt全0，generation5638395/prefixhits32000/prefixqueries315314未增。7份关键冻结回执及原script SHA一致；服务窗口inode27006868286/start8325922/end8326087/165bytes/SHA64bcdaba91f18f916b10f02695847dcc2d968ad9645da6b71dc923fdb1994ab8无新fatal/RPC/Traceback。快照heartbeat-combined-20261101T1731.jsonl SHA525d6be4b19c819f9ca5c6ddb78ce9d02f25a024d63cb07d80825d58f046db0f（实际工具17:32）。未重读全部raw/95成员或重复审计，0新POST/源码配置cache变更/服务动作/8035/提交推送。正式GPQA174/198未达88%、原C32唯一根因未确证仍开放；无下一批授权，继续用户小时只读后续，不新增测试或修改策略。


### 新8题对照方案：仅已有产物选题，不执行（2026-11-01）

用户明确要求先制定方案，暂不新增模型请求。按项目精度定位方法，SHA绑定原198 strict样本（174对/24错），排除此前effort对照8题32/71/79/88/127/145/147/185后，候选为174正确+16普通错答；仅按原分数/学科/长度/doc ID冻结选择，不看新medium答案。每类按输出长度rank分4个近等分区间，各选1题，优先覆盖3学科/4子领域；原正确组Q4刻意覆盖最长正确长推理压力题。正确组96/111/176/81，错答组106/186/89/69。此heldout指未参加此前xhigh/medium对照，并非从未参与原198评测或任何历史无关诊断。

只计划后续16POST（8×2），C1/seed1234/原T1/p.95/k20/minp0/presence0/repetition1/max60000/原stop/BF16及现有修复保持，各arm一次、0retry。正确/错误题交替，每类各2题xhigh先/2题medium先；同题只effort变量。主要看同轮C1 xhigh正确而medium错误的paired loss；收益不能掩盖退化，截断缓解与答对分开，None/length计错且固定分母8/分组4。C32→C1本身的变化不能归因medium。不执行/部署策略/跑正式gate，不自动launch额外smoke/C8/全量。

归档CPU输入冻结器A=G0/commands/effort-heldout-plan-20261101-v1/freeze_plan.py，SHA d3b82e167fc9f62490edb74215e9bcb618b1d9269e2b68d51a1cc5509879c94f；仅标准库CPU读文件/AST原生预处理/写独立方案D=G0/diagnostics/effort-heldout-plan-001，不含HTTP/模型导入/launch代码。先保存命令和哈希再执行CPU冻结。


### 未参加此前effort对照的8题方案已冻结（2026-11-01T17:57:32.287735+08:00；未执行）

已基于SHA绑定的原198题native严格分数/完整396 filter行，确认174正确、24错误；排除当前effort对照8题（32/71/79/88/127/145/147/185）后为174正确+16普通错答，选择4对4错。选题只使用原native分数、High-level domain/Subdomain、输出长度和doc ID，没有观察这些题的medium结果。每类按长度rank四分层各1题，在每层每学科保留离目标rank最近2候选，组合优先覆盖3学科和4子领域，再最小化长度rank距离，最后doc ID确定性打破平局。原正确组Q4目标为最长正确样本doc81，作为medium可能省略必要推理的压力哨兵。它是特意平衡的诊断样本，不能视作198题分布抽样或无偏精度估计；heldout仅指未参加此前xhigh/medium对照，并非从未进入正式评测或任何其他历史诊断。

| 原native结果 | doc | 学科/子领域 | 长度层 | 原输出token |
|---|---:|---|---|---:|
| 对 | 96 | 生物/Molecular Biology | Q1 | 609 |
| 对 | 111 | 物理/Quantum Mechanics | Q2 | 2295 |
| 对 | 176 | 物理/Physics (general) | Q3 | 6437 |
| 对 | 81 | 化学/Organic Chemistry | Q4 | 58849 |
| 错 | 106 | 生物/Molecular Biology | Q1 | 1181 |
| 错 | 186 | 物理/Astrophysics | Q2 | 20031 |
| 错 | 89 | 化学/Organic Chemistry | Q3 | 27682 |
| 错 | 69 | 化学/Chemistry (general) | Q4 | 32210 |

最小提案：8题×xhigh/medium各1次，共16POST上限、C1、seed1234、原采样与max_completion_tokens60000/HTTP7200/原stop保持，0retry。原生user prompt/选项顺序不变，gold仅留离线核对文件，不加入请求。只变同题chat_template_kwargs.reasoning_effort。对/错组交替、两组各2题xhigh先/2题medium先，配对顺序冻结为：96 X→M、106 M→X、111 M→X、186 X→M、176 X→M、89 M→X、81 M→X、69 X→M。X=xhigh，M=medium。执行前另需用户授权、只读核同API/源/空闲，并以原template纯CPU render核显式xhigh实际prompt等于原返回promptSHA；不额外发smoke/C8或清cache/重启。

主要检查同轮C1 xhigh正确、medium错误的paired loss，尤其原正确4题；逐题列出损失、收益、最终字母/gold、长度/finish/thinkend/EOS，不用其他gain抵消已观察到的退化。原C32标签用于分层，不能代替同轮C1 xhigh：原正确题两个C1 arm都错，必须记为C32→C1参考变化，不能单归因medium；原错题也可能在xhigh C1恢复后被medium再次损害。两个arm均按固定8题计分，分组固定4题，None/length/no extract计错，不从reasoning补答案。截断缓解与正确率变化分开；每arm仅一次，无退化也只表明此小样本未见，不能签全量gate/部署medium或拼回174/198。普通错答/length自然收集，不据结果替换题/重试；仅真实HTTP/身份/源/缺证/非预期prefix/preempt时冻结，16预算结束即停，不自动扩测。

完整原生arguments/target/doc-prompt-target hash和重建native预处理/打乱选项校验已对8题通过；16个提案JSON仅保存，并未发送，未创建launcher、RUN_ATTEMPT或DRIVER_PID。冻结器CPU_EXIT=0，29成员size/SHA及8题唯一性/4对4错/3学科4子域4长度层/组内arm顺序均衡/16body只effort不同/无额外gold注入均经独立只读核验。

权威D=G0/diagnostics/effort-heldout-plan-001，A=G0/commands/effort-heldout-plan-20261101-v1：REPORT SHA d3f5a5cc37eebc941809d1ca02c7a99d9e9785534688215b1493da5dd81b66c5；manifest cc059255db34ebfd76324a29429f51cf64df30215c98f4652660182294eba96a（29成员）；proposed-plan b4a1c44d93c8f48cad6d16ab108e399a2ade58601f383004055d9c1f8ae8dfea；READBACK 5e0eb120014d9a0dc6ca6ce6179df90e569a46ed410195e63f8a115ee87ba7db。本地补充independent-readback.json SHA a4aeb331f00bb938127a73eead8754fb215a3a0b7956fcb4adccb92a78afbde4，完整方案/8输入/16未执行body和原native证据均在远端，不依赖临时文件。

本轮0新增模型请求、0GPU/编译、0生产或评测源码/采样/cache/服务操作、0重启/8035/提交推送。BF16及现有修复保留，最新只读同API1336953/start607626732/source/runtime健康空闲，generation5638395/prefixhits32000/prefixqueries315314保持。原正式GPQA174/198<88%和ERQA252/400不变；尚无这8题medium结果或新gate，本轮到方案为止。

2026-11-01T18:31:54.068578+08:00 终态后小时只读：无新增诊断/修复/模型验证。原4/4反序复核及独立审计终态保持，driver/CPUwatch均已退出；新8题方案仍未执行，未见RUN_ATTEMPT/DRIVER_PID/STARTED。精确API1336953/start607626732及source/runtime保持，health200、running/waiting/KV/preempt全0；generation5638395/prefixqueries315314/prefixhits32000未增。10份关键冻结回执（含新方案REPORT/manifest/proposed-plan）及原script SHA一致；服务新窗口inode27006868286/start8326087/end8326417/330bytes/SHAf2cecdb39ec163cff704daf7621878f210440ed5f522c3fa2c65b23933295915无新fatal/RPC/Traceback。只读快照heartbeat-combined-20261101T1832.jsonl SHA52a947c90f58f224c4ae73f402c9f39b0cd48af7f51b5522ed1513c5110b3035。0新POST/重试/生产配置或代码变更/服务动作/8035/提交推送，未重复全量raw/manifest审计。正式GPQA174/198仍未达88%，原C32唯一根因未确证；ERQA252/400保持。保留BF16及现有修复，继续用户要求的小时只读跟踪；下一批16POST仅提案，不自行执行。


### 新8题16条C1对照获用户授权，执行前记录（2026-11-01）

用户明确回复允许执行已冻结8题16条C1对照、结束即停。保持96 X→M、106 M→X、111 M→X、186 X→M、176 X→M、89 M→X、81 M→X、69 X→M，C1/seed1234/原采样/BF16及现有修复；0重试/额外smoke/C8/全量/服务操作/8035/提交推送。使用本地精度评测技能minimal-regression，完整响应、token/usage及原严格评分和gold独立CPU核对，原C32仅作分层；主要报告同轮paired loss，收益与截断缓解分开。新增执行目录diagnostics/effort-heldout-c1-001，控制资产commands/effort-heldout-c1-20261101-v1；原effort-heldout-plan-001只读保留。

先保存CPU预备命令python3 -B <A>/effort_heldout_control.py --mode prepare及SHA再执行，不发模型请求；控制器SHA dfd5e3d107fea883d6dd1d8ab665eb378174346ddba8e260c0b563840d3f954b，observer保持d402bd94a84a757b1e1a255133265803ab0e26963bce4fd46eb3f73a329471e6。新路径独占创建，拒绝重放。编译/原严格末匹配/None错误/paired gain-loss/未完成配对固定分母CPU检查通过。正式GPQA174/198失败状态保持，本次无gate或性能结论。

CPU预备001在历史audit的doc_id字符串与整数集合比较处选择0行，found断言退出1，0POST/0launch；原目录/prepare.log/退出回执保留。v2将doc_id显式int归一，8条字符串ID fixture通过，使用新目录effort-heldout-c1-002和新资产effort-heldout-c1-20261101-v2，不覆盖或重放001。控制器SHA 3a076fe96bcc3cb3aa9a2667b84a982463a5f2dd09cca11240f1a6e79465f8f7，发送范围仍是用户原授权16条。

v2纯CPU prepare退出0：16body保持提案字节、8显式xhigh Jinja渲染匹配原实际prompt、8历史native API完整绑定；plan SHA14b917b4dd37cecd351c0103b79267f808fa537d55753cdb1dd61067a451a477，PREPARED ebaf467395fa3804d29f6363094aa8a221ea2b0855b42e1c8084951f987d79ea。准备执行已保存命令python3 -B <A>/launch_once.py，launcher SHA63c8f1c206a8dad10f0a7a8ae14ae0d310904ba53961ba5458546dafc55f616e；先再次核冻结输入和同API/source/空闲，再独占LAUNCH_ATTEMPT、唯一driver和CPU终态watch。不得重放或增加16预算。

2026-11-01T19:27:21.003778+08:00 已启动用户明确授权的新8题16条C1对照，当前1派发/0完整（首seq0/doc96/xhigh在途），不将派发或生成中token计完成。原4条反序任务已结束；新唯一driver798086/start624823628/argvSHA6e64aa494a9226ae1d951db1d385db0d733ea41762e2907c85620cc0f2b9ae25及CPUwatch798171/start624823639/argvSHA05e5a8cd4da698e4ddb0015011f84d28446707cace1e38f38e006976eaffa930精确active，当前同API1336953/start607626732/source/runtime相同，health200/running1/waiting0/KV0.001454921482336502/preempt0，prefixhits32000未增，无FIRST_ANOMALY/终态/watch错误。

本次执行D=G0/diagnostics/effort-heldout-c1-002，A=G0/commands/effort-heldout-c1-20261101-v2，16body逐字节匹配原提案，原正确4题96/111/176/81与普通错4题106/186/89/69保持；只effort变量，C1/seed1234/原采样/BF16/现有修复不变。主要安全信号是同轮paired loss，收益不可抵消损失；截断缓解与答对分别报告。原C32标签只作分层；严格native regex/gold/None计错固定8和组内4分母，不从reasoning补答。完整HTTP请求/响应实体bytes、解析头、prompt/output IDs、usage、reasoning/final、新service byte窗口及严格评分归档；CPUwatch仅等driver自然退出后一次独立审计，不发模型请求。

plan SHA14b917b4dd37cecd351c0103b79267f808fa537d55753cdb1dd61067a451a477、PREPARED ebaf467395fa3804d29f6363094aa8a221ea2b0855b42e1c8084951f987d79ea、assetmanifest cf84cfeec61136236ba656b0135ba2e297690a32bf014e1e876702af4df97c9e；只读快照progress-initial.json SHA766ecdcfa2b58b76966f8d5518470ade4a214fb863194bc6cc4cfaf6bb371340。首CPU预备001的字符串doc_id筛选错误和0POST首错保留，新002已归一并验证8条映射、16输入及显式xhigh prompt渲染；不是新模型事故。16请求结束即停，0重试/额外smoke/C8/全量/服务动作/8035/提交推送。正式GPQA174/198<88%及ERQA252/400保持，尚无新模型分数或修复结论。

2026-11-01T19:29:15.496972+08:00 新8题队列3派发/2完整/1完整pair，seq2/doc106/medium在途。首对doc96：xhigh585tokens、medium855tokens，均HTTP200/stop/finalB（goldB、均对）/thinkend+EOS，prefix增量0。2026-11-01T19:29:56.035270+08:00 CPU独立回读原raw/request/body/prompt/output IDs/usage/native严格评分有效，SHA8f1254f7ee47e7ae8e106990653da161d430b875c88da4e108fb539d97bf3c61；原始材料在D=effort-heldout-c1-002，未抢跑全16审计或新增POST。当前首对medium反而多270tokens，不能说medium保证更短或由1题推广8题；原doc96 C32 xhigh609→本轮C1 585，prompt IDs相同但输出第136个0-based token开始不同，仅描述历史C32/C1差异，不作为唯一数值因果。

同API/driver/watch精确active、health200/running1/waiting0/KV0.001743500949907384/preempt0/prefixhits32000，source/runtime同、无FIRST_ANOMALY/终态/watch错误；快照progress-after-binding.json SHAd77535949f092c1ab3ce4a6c030bdfe7dbd6a114096664796ba0d7171ce5d86e。原16预算继续，不重试/重启/8035/全量/部署medium/提交推送。当前处于定位验证阶段，尚未确认通用修复；完整结果将分别报告paired loss/gain、截断与正确性，正式GPQA174/198及ERQA252/400保持。

2026-11-01T19:31:34.958406+08:00 主回复后数分钟只读快检：6派发/5完整/2pairs，seq5/doc111/xhigh在途，driver/watch精确active、同API/source/runtime，health200/running1/waiting0/KV0.00116634201476562/preempt0/prefixhits32000，无FIRST_ANOMALY/终态/watch错误。新完成元数据doc106 medium942/xhigh525均stop并答B（goldA，两者错），doc111 medium1151stop/B对，尚无第3完整pair。此次只读metadata未独立重新解析新raw，不抢跑终态审计；原16预算自然继续。快照heartbeat-20261101T1931.json SHAe7f0e6cdc73d510b39da7a67a46213c39534ce3ac39d2e4c9ff5070756c91b29。距19:29主通知仅数分钟、无新故障，不重复打扰，下一小时仍按用户要求主动报告；0新POST/重试/服务或源码变更/8035/提交推送。

### 小时只读进展：15/16完整，末条仍在途（2026-11-01T22:15:34.363747+08:00）

实际工具核验为2026-11-01T22:15:34.363747+08:00，延迟heartbeat触发20:40不作为核验时间。新8题16条C1已16派发/15完整/7pairs，最后seq15/doc69/medium在途；不报告8题最终分或终态。新完成seq2..14共13份原response.raw/request/body/prompt/output IDs/usage/native严格regex及gold于2026-11-01T22:16:16.543776+08:00独立CPU逐项回读有效，8关键控制/plan/原script SHA核同，未重跑auditor或抢跑16终态审计。

| doc | xhigh：输出token/finish/答案 | medium：输出token/finish/答案 |
|---:|---|---|
| 96 | 585/stop/B对 | 855/stop/B对 |
| 106 | 525/stop/B错 | 942/stop/B错 |
| 111 | 984/stop/B对 | 1151/stop/B对 |
| 186 | 23938/stop/B错 | 6606/stop/D对 |
| 176 | 6777/stop/C对 | 1833/stop/C对 |
| 89 | 18448/stop/B错 | 5672/stop/B错 |
| 81 | 60000/length/None错 | 2738/stop/B错 |

仅对已完成7对：同轮paired gain=doc186（xhighB错→mediumD对，goldD），paired loss暂0；不是8题无退化结论。原正确doc81由历史C32 D对58849变本轮xhigh60000length/no final/无thinkend-EOS、medium2738stop/B错，两个C1 arm都错，不能单归因medium；medium消除了此题截断但未恢复正确答案。其他非length均stop/thinkend/EOS/非空final，15响应均HTTP200、prefix命中增量0。69只完整xhigh25848/stop/B错，medium不作完成或正确率推断。固定每arm8/原分组4分母保留，尚有缺项不报最终百分比，不拼原174/198。

同API1336953/start607626732/source/runtime，driver798086与CPUwatch798171精确active；health200/running1/waiting0/KV0.012132361782459133/preempt0/prefixhits32000。无FIRST_ANOMALY/终态/watch错误；当前seq15新窗口inode27006868286/start9562480/end9686195/123715bytes/SHAc12769ccdb458170b87374fbb593bbc8011c5dd05aa3d2c703c795e2fd006ed4无fatal/RPC/Traceback。快照heartbeat-20261101T2040.json SHA358e4f0d3cdf1352d5dbfdb5a33f9ea48a59cebd428ac23fdd2c393ad7602f1c（文件名是触发时间，实际工具22:15）；独立回读hourly-independent-20261101T2215.json SHA633fbd3d76044abb11fc0863f41851001c6370d1ff92186d231eebd8644eb143。monitor本轮0POST/重试/生产源码或配置变更/服务动作/8035/提交推送。原唯一controller继续最后一条，16完成即停并等原CPUwatch一次审计。BF16与现有修复保持；整体GPQA174/198<88%、原C32唯一根因未确证和ERQA252/400不变，继续小时ACTIVE。

2026-11-01T22:18:31.575083+08:00 距22:16主通知仅数分钟，只读快检仍16派发/15完整/7pairs，末条seq15/doc69/medium在途；driver/watch精确active，同API/source/runtime、health200/running1/waiting0/KV0.014152418055455307/preempt0/prefixhits32000，无FIRST_ANOMALY/终态/watch错误。generation上涨仅表示在途活动，不计完成或ETA。快照heartbeat-20261101T2218.json SHA50eab19a7660cfb11b58296e5ecf05314b424db518277c3ce365baf67f946b47；0新增POST/重试/服务或生产改动/8035/提交推送，不重复原7pairs通知，下一小时仍主动。

### 新8题16条C1验证完整终态（2026-11-01T23:15:21.167554+08:00只读复核）

原driver于2026-11-01T22:25:33.525621+08:00完成16/16完整HTTP200、8pairs、0retry；独立CPUwatch/audit于2026-11-01T22:25:35.291547+08:00完成并退出0，driver798086/start624823628与watch798171/start624823639均自然退出，16预算结束即停。2026-11-01T23:14:02.642167+08:00核同API1336953/start607626732/argv/listener/source/runtime、health200/running0/waiting0/KV0/preempt0/prefixhits32000；没有运行中评测或下一批模型请求授权。

| doc | native gold | xhigh：token/finish/答案 | medium：token/finish/答案 |
|---:|---|---|---|
| 96 | (B) | 585/stop/B对 | 855/stop/B对 |
| 106 | (A) | 525/stop/B错 | 942/stop/B错 |
| 111 | (B) | 984/stop/B对 | 1151/stop/B对 |
| 186 | (D) | 23938/stop/B错 | 6606/stop/D对 |
| 176 | (C) | 6777/stop/C对 | 1833/stop/C对 |
| 89 | (D) | 18448/stop/B错 | 5672/stop/B错 |
| 81 | (D) | 60000/length/None错 | 2738/stop/B错 |
| 69 | (D) | 25848/stop/B错 | 25189/stop/D对 |

本次固定8题：xhigh3/8=37.50%，medium5/8=62.50%；同轮paired gain仅186和69，paired loss=0。原正确4题两arm均3/4，原普通错4题xhigh0/4、medium2/4。本次刻意按原对错/学科/长度平衡且各arm一次，未见配对损失仅限这8题，不能外推全198、覆盖旧doc79已反序重现的medium退化、部署默认medium或签formal gate。两个gain都是非截断stop答错→stop答对，不是单靠补final计分。

截断单独看：xhigh仅doc81为60000length/reasoning-only/无thinkend/EOS/final，medium0length。doc81 medium2738stop/有final/thinkend+EOS但B错，goldD，属于截断缓解却未答对；原C32 xhigh58849stop/D对，本轮C1 xhigh也错，不能单归因medium。其余15响应均stop/非空final/完整thinkend+EOS。medium并非每题更短：96/106/111反而比xhigh长，其余5题更短。总输出xhigh137105、medium44986，仅token观察，不作性能收益结论。

全16完整request.http/body、解析response头及精确HTTP实体bytes（非TCP分帧）、prompt/output IDs/usage/reasoning/final/真实seq-doc-effort/严格regex最后匹配和gold均在D=G0/diagnostics/effort-heldout-c1-002；独立CPU audit/report与本次CPU只读回读均核固定8和组内4分母、None/length计错、不从reasoning补答、仅effort变量/16body匹配提案、历史xhigh prompt IDs相同及完整output首差。55冻结输入/322terminal成员/326audit成员大小SHA全部通过，未重复执行固定auditor/watch。源/runtime前后当前及原script一致，16raw合计prompt6708/output182091与服务计数差一致，prefixquery增6708、prefixhits仍32000；累计核账不是独立TCP或逐rank trace。

权威SHA：FINAL_SUMMARY 263886e3e720e063cc8a38b18d5af74c2b99930ff71339301facd0605fd0161e；FINISHED 37305ebc1b54ac9d8dd36b8d2898bb28e2fc005da07b14e6769da47a9a8c15fe；terminal-manifest 5ac6f23f8d21cc1faf5bf9631a652cd02b58e6ffa8c31f2d122a82c6b932c7f5（322）；frozen-inputs 387c83aa6971c165087e8ca26cb3f6410a9d48338dda582d6983bc64710d0d94（55）；audit/report 4811493481ea875b484825d44b6e708123a1521f1a7ca0c26c7e3fe7cc67a6c8；audit/manifest dbf63107f4647e9b70ef19d94639d6f212cb7bc676cc3d179fb60a263bba99d9（326）；audit/READBACK 444266613e53fc502456adef0c3f034e7470befb22cbd58c14895dcbbb1ca3a9；A/CPU_WATCH_COMPLETED 60fd96718d6aed03ceede9c53f4c0b41d8e56a034833c7a9eb4e121e453d1b44，CPU_AUDIT_EXIT=0。最终driver.log 4ffa8d1fde89b629284aeda3f1eeda437aa26dab0203b7ad5e254dc20b645a8e、cpu-audit.log 52fba5099b9e0b54c8b8cf826732cd78c4b6d6ae02724fe7c884df640100a348；本地补充terminal-review-20261101T2315.json SHAdec3945483beddcf91eab8b94acc9394ce6e5eab26f8d7b2d8725a9f2bdf6cad，原件在远端D/A，不依赖临时文件。

本次最终新窗口inode27006868286/start9686195/end9761528/75333bytes/SHA1b91d5429c9ba5c3777b4edb4da08743def4db7af8b41dec6e973d8db16f8cdb无fatal/RPC/Traceback，全部16每seq窗口无新设备/RPC/HTTP fatal。首CPU预备001字符串ID类型错误的0POST历史原件保留，不当生产故障。monitor本轮0新增POST/手动retry/生产源码配置cache修改/编译/服务动作/8035/提交推送，BF16和现有修复保持。正式GPQA174/198<88%、原C32唯一模型根因未确证及ERQA252/400保持；本小对照完成不代表整体修复闭环。下一步先基于已保存doc81的早期输出分叉及现有源码继续限定原因；下一批模型/配置/源码操作没有新增授权。整体按用户要求继续ACTIVE小时只读后续，不重复全量raw/manifest审计。

### 终态后小时核验与doc81既有产物定位（2026-11-02T00:20:41.348937+08:00；0新增请求）

2026-11-02T00:19:20.021730+08:00同API1336953/start607626732/argv/listener/source/runtime保持，health200、running/waiting/KV/preempt全0，generation5820486/prefixqueries322022/prefixhits32000未增；16/16与独立审计终态保持、原driver/watch已退出。7关键summary/manifest/审计/原script回执SHA一致；日志inode27006868286/start9761528/end9761693/165bytes/SHAedec5f760d65d49e763978c58670bb8bb1ab9681cdab77d2228e9a6aae681b22无新fatal/RPC/Traceback。快照heartbeat-combined-20261102T0019.jsonl SHA163de3529d6e4d9df8a43131cf1c65478b1785a69f096ee0ac4eaa1b9561bd5e。

本轮额外仅CPU读取已保存doc81三个SHA绑定响应（历史C32 xhigh、当前C1 xhigh/medium），未重复完整16审计。历史/当前xhigh prompt IDs均778且完全相同，输出首次分叉0-based112，原token4992→当前7995；prompt+已生成位置890，reasoning文本首差字符490。差异早于总长6400的首次边界，因此“仅在之后长解码跨边界时才第一次分叉”不能完整解释本题；但原C32可能部分prefill、align初始化/复制及采样数值路径仍不能排除，也不能将表面措辞分叉当机制证据。

当前C1 xhigh60000tokens/196254推理字符/length、0thinkend/0EOS/无final；全输出没有重复64token窗口（最大出现1次），尾部周期1–512均未连续重复3次。历史答对C32 xhigh58849tokens/188638字符/stop倒有59个重复64token窗口、最高4次，且也没有该范围周期性尾部。当前medium2738tokens/7082推理字符/stop/B错，亦无重复64token窗口或周期性尾部。仅这些事实不足以称当前为“字面token死循环”，也不以重复统计排除语义上反复推演。当前xhigh尾部仍在变化并继续推演，与60K预算耗尽一致，不是HTTP/RPC故障；medium结束较早却给错答案，不能把强行更早结束当正确性修复。

三原件SHA：历史doc81 e37fa23f2fde170aabddf0554e7dc2da57fbf38a9a5e19878217ab9b2b6057e3；当前seq13/xhigh 0d67a32b935b87c6f7b05d962670d4f746ff3c3db5befb3285a77f4e3b31d4bb；当前seq12/medium 17d0a1c4a40a9e5fefe7629d4774cac13f1be3e40eed47f3a9d7572b1c1ba9b9，均在D=effort-heldout-c1-002内，受原终态manifest绑定。CPU方法=逐token首差、全滑动64token窗口Counter、末尾period1..512×3重复、reasoning字符串首差；本地补充doc81-existing-readonly-20261102T0020.json SHA818d7cb9ad113178b78b18c8e95ec1c3e9626ead1e8c09574b62f052d64b7fea，结构化摘要写同state，无原题/推理全文进入仓库。

这只是已有产物的新局部定位，尚缺首差前logits/实际RNG状态/Mamba状态的匹配受控证据，不能确认唯一源码根因或声称已修复。无新模型验证/生产修复/服务动作；0新POST/重试/GPU/编译/源配置cache变更/8035/提交推送，BF16与现有修复保持。原正式GPQA174/198<88%、ERQA252/400及本8题X3/8/M5/8均保持；后续先在现有调用链上明确取得首差机制证据所需的最窄验证设计，不自动扩请求、调参或部署medium。用户小时ACTIVE继续。

2026-11-02T01:23:23.734769+08:00 终态后小时只读：本小时无新增定位结论、修复或模型验证。16/16及独立审计终态保持、driver/watch退出；精确API1336953/start607626732/argv/listener/source/runtime同，health200、running/waiting/KV/preempt全0，generation5820486/prefixqueries322022/prefixhits32000未增。7关键冻结回执及原script SHA同；service窗口inode27006868286/start9761693/end9761858/165bytes/SHAb42022d5b134cb5c9916be71dd47d5ae20cbf73aec09728df0d6219ae05606d6无新fatal/RPC/Traceback。快照heartbeat-combined-20261102T0123.jsonl SHAde985165a6011f92b370ef719c40b41f5a1afb559ec61764a7a004e389313bf6。未重读16raw/全326成员或重复doc81固定分析，0新POST/重试/生产源码配置cache变更/编译/服务动作/8035/提交推送；保留BF16/现有修复。仍缺首差前logits/实际RNG/Mamba状态匹配受控证据，无可确认源码修复点；下一步是收窄验证设计，不自动扩测或部署medium。原GPQA174/198<88%、ERQA252/400、本8题X3/8-M5/8和doc81局部事实保持，整体小时ACTIVE继续。

2026-11-02T02:26:03.104050+08:00 终态后小时只读：本小时无新增定位、修复或模型验证。16/16及独立审计终态保持、driver/watch退出；同API1336953/start607626732/argv/listener/source/runtime，health200、running/waiting/KV/preempt全0，generation5820486/prefixqueries322022/prefixhits32000未增。7关键冻结回执及原script SHA同；service窗口inode27006868286/start9761858/end9762023/165bytes/SHAf047449e7a0d562c178dd9c51ef99a9b2d5634c483e92ac46b86305437098b03无新fatal/RPC/Traceback。快照heartbeat-combined-20261102T0226.jsonl SHA2ac0f137e436f27848945911bc4543c0ab7995fe40de6831ccd62b11bdba85b2。未重复全raw/manifest或doc81固定分析，0新增POST/重试/GPU/编译/生产源码配置cache变更/服务动作/8035/提交推送，保留BF16及已有修复。首差前logits/实际RNG/Mamba状态受控证据缺口不变，原正式GPQA174/198<88%仍开放；下一步收窄机制验证设计，不自动扩测或部署medium，整体小时ACTIVE保持。

2026-11-02T03:23:08.047561+08:00 终态后小时只读：无新增定位结论、修复或模型验证；原16条/8pairs及CPU审计完整、driver/watch退出。同API1336953/start607626732/argv/listener/source/runtime，health200/running0/waiting0/KV0/preempt0，generation5820486/prefixqueries322022/prefixhits32000未增。7份关键冻结回执及原script SHA一致；新窗口inode27006868286/start9762023/end9762188/165bytes/SHA2ab28e47b0b7c408a1c318a98c58416926e9a3e41195b5dbbde227b8a54b106f无新fatal/RPC/Traceback。快照heartbeat-combined-20261102T0323.jsonl SHA53462275876dbd5cad2c7bfc1a2567748d05293c868b9e86d068a7a7c8ef0398。未重复全raw/manifest或doc81固定分析，0新POST/重试/GPU/编译/生产源码配置cache变更/服务动作/8035/提交推送，BF16和现有修复保持。仍缺首差机制的受控证据，无确认源码修复点，正式GPQA174/198<88%不变；下一步收窄验证设计，不自动扩测或部署medium，整体小时ACTIVE继续。

2026-11-02T04:30:13.505946+08:00 终态后小时只读：无新增定位、修复或模型验证。原16/16、8pairs及CPU审计终态保持、driver/watch退出；精确API1336953/start607626732/argv/listener/source/runtime同，health200/running0/waiting0/KV0/preempt0，generation5820486/prefixqueries322022/prefixhits32000未增。7关键冻结回执及原script SHA一致；新窗口inode27006868286/start9762188/end9762353/165bytes/SHA2422754460a711d2597814becadfaada8a2f011a88ab0346cfee7d28f04087d8无新fatal/RPC/Traceback。快照heartbeat-combined-20261102T0430.jsonl SHAa7996e914bd0db48825cb2f8c171b34f9a92ea8f6cb19290889b9569df3b33c0。未重复原raw/全manifest或doc81固定分析，0新增POST/重试/GPU/编译/生产源码配置cache变更/服务动作/8035/提交推送；保留BF16和现有修复。首差前logits/实际RNG/Mamba状态的受控证据缺口保持，正式GPQA174/198<88%仍未闭环；下一步收窄机制验证设计，不自动扩测或部署medium，整体小时ACTIVE继续。

2026-11-02T05:27:40.170512+08:00 终态后小时只读：本小时无新增定位、修复或模型验证。16/16、8pairs和CPU独立审计终态保持、driver/watch退出。同API1336953/start607626732/argv/listener/source/runtime，health200/running0/waiting0/KV0/preempt0，generation5820486/prefixqueries322022/prefixhits32000未增；7关键回执及原script SHA同。日志inode27006868286/start9762353/end9762518/165bytes/SHAbf7eca0c01b34d64240c66f9aeba3a060b04e15c0953fc9acc28d75dcfef20fb无新fatal/RPC/Traceback。快照heartbeat-combined-20261102T0528.jsonl SHA2857acf611bfb5b33d153ea4120ef30a0646c286602b15190be27e1d3922064f，实际工具时间05:27。未重读全部raw/manifest或重复doc81分析，0新增POST/重试/GPU/编译/生产源码配置cache变更/服务动作/8035/提交推送，BF16/已有修复保持。仍缺首差前logits/实际RNG/Mamba状态的匹配受控证据，暂无确认源码修复点；正式GPQA174/198<88%仍开放，下一步收窄机制验证设计，不自动扩测或部署medium，整体小时ACTIVE继续。

2026-11-02T06:29:35.098104+08:00 终态后小时只读：无新增定位结论、修复或模型验证。16/16、8pairs及CPU独立审计终态保持、driver/watch退出；精确API1336953/start607626732/argv/listener/source/runtime同，health200/running0/waiting0/KV0/preempt0，generation5820486/prefixqueries322022/prefixhits32000未增。7关键冻结回执及原script SHA一致；service新窗口inode27006868286/start9762518/end9762683/165bytes/SHA141671c85f370db20e54f9b281a36beb5756fa07b9938b6c23f10b04df05c197无新fatal/RPC/Traceback。快照heartbeat-combined-20261102T0630.jsonl SHA5834e6eaca1221c809a0e46b114bfe4d9918bcd3c302d4c1483dfcd7c17f1667，实际工具06:29。未重读全raw/manifest或重复固定doc81分析，0新增POST/重试/GPU/编译/生产源码配置cache变更/服务动作/8035/提交推送；BF16及现有修复保持。首差前logits/实际RNG/Mamba状态的受控证据缺口未变，正式GPQA174/198<88%仍未闭环；下一步收窄机制验证设计，16请求预算已消费完，不自动扩测或部署medium。整体小时ACTIVE继续。

2026-11-02T07:28:38.333184+08:00 终态后小时只读：无新增定位、修复或模型验证。16/16、8pairs及CPU审计终态保持，driver/watch退出；精确API1336953/start607626732/argv/listener/source/runtime同，health200/running0/waiting0/KV0/preempt0，generation5820486/prefixqueries322022/prefixhits32000未增。7关键冻结回执及原script SHA一致；新窗口inode27006868286/start9762683/end9762848/165bytes/SHAd4a3b9187b5851bc3fe22ed1fbb70eeeaf5efc5b8b080e8074ff2b411ea8a29b无新fatal/RPC/Traceback。快照heartbeat-combined-20261102T0729.jsonl SHAa95d0a4ab48eba52e22d0b8f37761171fc4964257827ad26cff913b758bc4537，以实际07:28工具时间记录。未重读全raw/manifest或重复doc81固定分析，0新增POST/重试/GPU/编译/生产源码配置cache变更/服务动作/8035/提交推送，BF16与已有修复保持。当前只有只读跟踪，无新修复在执行；首差前logits/实际RNG/Mamba状态受控证据缺口仍是定位阻塞，正式GPQA174/198<88%不变。下一步需有范围明确的机制验证设计及对应新授权，不自动扩已用完的16预算或部署medium；整体小时ACTIVE继续。

2026-11-02T09:12:41.547384+08:00 小时只读：本次首只读SSH因连接服务未响应退出255（不是模型HTTP/RPC/device故障），最初快照heartbeat-combined-20261102T0838.jsonl为0bytes，未把07:28历史健康冒充当前。首错记录FIRST_MONITOR_SSH_TIMEOUT-20261102T0912.json SHA998d0a912d0bdd8080914199094d23d63526043a0c0b51a990097a46d165bb67保留，09:12:04本地记录时间；未保存未返回的远端身份/health/source/log证据。随后指定PPU-07 connectivity-check只读通过（ok3/changed0/unreachable0/failed0），补完一次带连接超时保护的同范围只读核验；不重发模型请求或执行服务恢复。

补核实际2026-11-02T09:12:41.547384+08:00：同API1336953/start607626732/argv/listener/source/runtime，health200/running0/waiting0/KV0/preempt0，generation5820486/prefixqueries322022/prefixhits32000未增；16/16和独立审计终态保持、driver/watch退出。7关键回执及原script SHA一致；接续service窗口inode27006868286/start9762848/end9763178/330bytes/SHA1773617c7ed79bba5cdba499423c24c626459fe3ebb5e4197b5017f67df3e9ad无新fatal/RPC/Traceback。快照heartbeat-combined-20261102T0912.jsonl SHA12a7779fce2363ee3265d6f6d6a201cbe8078d53a643cd1c4ec6e43fc809e0f9，连接后续回执MONITOR_SSH_TIMEOUT_FOLLOWUP-20261102T0913.json SHA7c525412c486bfa7f5de20c2e6f0a2a6468acbfe7e76d82a9ce6970f710ecaae。初次只读连接失败后缺失项现已由补核完整取得，未发现模型服务异常；首连接超时原件不覆盖、不当未来新故障重复通知。

本小时无新增定位/修复/模型验证；仅连接只读重检，0模型POST/推理重试/GPU/编译/生产源码配置cache变更/服务动作/8035/提交推送，未重读全raw/manifest或重复doc81分析。BF16/现有修复保持，正式GPQA174/198<88%及首差机制受控证据缺口不变；下一步收窄验证设计，不自动扩已用完16预算或部署medium，整体小时ACTIVE继续。

### doc81首差前logits/RNG/Mamba最小取证方案（2026-11-02T09:32:59.683585+08:00；仅方案，未执行）

用户要求列清请求数、埋点与区分机制，先不执行；本轮仅读本地已冻结且SHA核同的源码副本和原产物摘要，0模型请求、0远端命令、0生产源码/配置/埋点修改、0服务操作。当前绑定身份最后实际核验仍09:12，不用本规划时间冒充新health检查。保留BF16/全部修复/原prefix策略，不重启、无8035/物理0–7、无提交推送。

**建议完整预算为3条短请求，当前授权执行数0。** 全部doc81/xhigh、C1、seed1234、原采样T1/p.95/k20/minp0/presence0/repetition1和原stop；R0 trace-off，R1 trace-on，R2 trace-on重复一次；body相同。新诊断契约将max_completion_tokens60000限为128，3条最大输出384，不跑60K、medium、额外smoke/C8/全量或自动扩测。必须先核三条prompt相同、输出0..127与原已保存C1长请求前128个ID一致，才把短请求当该轨迹的前缀取证；短cap可能影响调度，不预先假定等价。若提前stop或前缀不同，标not-reproduced/incomplete并停，不自动延长。原首差是输出0-based112（第113个）；采样它之前已消费prompt778+输出0..111共890tokens，标准文本position末位889，具体positions以实际metadata为准。

**完整方案需要worker内埋点；当前无已核实的安全免重启开启入口，因此当前不可直接执行。** 保存Python文件不能让既有worker函数对象/已捕获graph自动生效，禁止拿改文件、attach/热注入、重启、抢占物理8–15另起实例来绕过约束。先只读证明已有动态trace控制存在且绑定到这些worker；没有则保持本方案未执行，不把只加HTTP logprobs叫完整取证。若仅想HTTP初筛，替代预算2条128-token请求（原请求 vs logprobs/top_logprobs20），只能看有限概率/输出前缀，取不到完整原始logits、实际q/RNG状态和Mamba；这与3条完整版二选一、不相加，本轮都未执行。

**采集位置与内容**（通用request trace ID+步窗口过滤，不能把doc编号/答案或题面特化进生产逻辑）：

| 层次 | 实际调用链/位置 | 必取内容 |
|---|---|---|
| 请求/执行 | ModelRunnerFL `_prepare_inputs`→hidden_states[logits_indices]→`compute_logits`→`_sample` | trace/request→row/slot映射、真实input IDs/positions、computed/scheduled、discard mask、padded/真实shape、graph/replay签名及命中实现；比较前缀必须相同 |
| logits | `compute_logits`之后、grammar/processor之前；`Sampler.forward`及`TopKTopPSampler.forward_native`过滤之后 | 输出步0..112每步完整原始vocab logits、原始dtype，实际grammar/penalty/T/minp/topk/topp配置，实际保留token集合/概率、胜者与次优margin；保留阈值并列项，不能硬截正好20个；API logprobs受raw/processed模式影响，不能替代两阶段logits |
| RNG/选择 | `preserve_discarded_generator_offsets`外包裹；`random_sample`实际`q.exponential_`前后；`sample_with_exponential_noise`破坏性div/reciprocal之前 | 请求generator对象/设备/实际seed、完整get_state及SHA、get_offset（wrapper entry、draw前、draw后、finally后）、generators行key/实际分支、discarded/valid标记；保存实际q和实际probs，重算p/q胜者；只有实际使用global分支才取global状态，不能为观测再抽随机数，不假设一次消耗4 |
| Mamba管理 | grouped `mamba_buffers.preprocess_mamba`→native `collect_mamba_copy_meta`/`do_mamba_copy_block`；deferred corrections及accepted CPU→GPU resync | TP8全部rank、全部异构partition/layer的spec/shape/dtype/stride、逻辑block/slot、computed/scheduled、分组独立state_idx、accepted重置前/各分组/最终值、src/dst/size/bias；记录初始化与真实copy命中，零命中也需记录 |
| Mamba数值 | 初始化/prefill末尾、窗口内每次真实copy前后，以及decode110/111/112各层输入/conv状态/SSM状态/输出 | 仅目标请求活跃state切片，按原始BF16/FP32 state dtype无损保存；同逻辑位置比较，不以跨请求物理地址不同当错误。若实际首差更早而完整state窗未覆盖，机制证据仍incomplete，另设计更早窗口，不能补推因果 |

复制类不变量可直接用捕获的源state与实际copy_func的切片、bias、dst布局生成CPU字节reference：copy必须逐字节一致；数值更新必须用同输入、同原始dtype的匹配native/reference检查，不能因为state不同就直接判算子错。完整raw logits与q按113×实际vocab×dtype字节×实际采样rank数预算；Mamba按活跃spec大小×rank×checkpoint数预算，不dump全KV或其它请求。埋点需有界预分配缓冲、正确stream/event时序，采到probs/q被原地修改前的值；不得改计算、RNG、cache或graph签名/转eager。所有实际采样rank要覆盖，Mamba全8rank，不能只抓API rank0。

**判别表：**

| 在相同input IDs/positions和共享前缀下观察到 | 优先归属与必要证明 |
|---|---|
| raw及processed logits/probs相同，但实际generator生命周期/q不同且解释了token变化 | RNG/seed-row绑定/offset回退/随机核路径；核valid行应正常推进、discarded seeded行finally恢复entry offset，不假定固定减4 |
| raw logits相同、processed logits/保留集合不同 | logits processor、topk/topp或metadata，不归Mamba |
| probs与q都相同，返回token却不同 | argmax/tie、row scatter或输出bookkeeping，不归seed漂移 |
| draw前raw logits已不同，且Mamba初始化/copy目的state偏离源切片reference | 状态初始化/索引/copy管理路径，才有具体修复靶点 |
| 初态/copy结果/层输入相同，但Mamba更新或层输出不符合匹配reference | Mamba数值/算子路径嫌疑，需要另外授权的同输入算子重放确认 |
| Mamba状态及输出都相同，后续hidden/logits不同 | 继续查attention/MoE/GEMM/TP归约/LM head，不能硬归Mamba |
| q相同，只有小logits扰动改变近并列候选胜者 | 上游数值差异被T1随机采样放大，不自动等于采样bug或Mamba bug |
| 三条token前缀和R1/R2内部轨迹均一致 | 仅证明当前C1稳定且未观察到token级埋点扰动，仍未解释旧C32首差 |

**覆盖与停止边界：** C1的778token prompt+128输出可能根本不触发discarded-row回退或align跨blockcopy；必须报告实际命中次数，没命中不能宣称这两项修复已验证，prefixhits0也不能等同无Mamba路径。原C32正确运行没有首差前内部快照，不能拿本3条C1与历史答案单独证明C32因果；两边token一旦不同，之后state差异属于不同输入历史，除非另行授权固定公共prefix的teacher-forced/张量重放。条件性采样器克隆RNG重放、Mamba同输入reference或32-lane shape重放均不计入/不自动执行本3条，当前额外HTTP授权0、额外设备重放授权0；明确0POST不等于0GPU成本，不能暗做。

对应修复条件：若确证offset/row错误再改请求本地RNG bookkeeping；若确证copy字节/accepted或slot映射错误再修对应group状态管理；若仅数值扰动，先定位首差层及reference再决定修复，不降effort/温度或扩大预算掩盖。修复后需重新验证原正式范围，原174/198和本8题3/8对5/8不被本计划改写。

方案JSON本地/private/tmp/acc023-doc81-evidence-plan-20261102/plan.json SHA70731c5d258bf736966fd84385c234516a93109e63453d606ae93be599c1116d，结构化摘要写同state。源码依据为上次已绑定实际导入路径的冻结副本，已对6文件逐项SHA核同：runner5c78833043957e14032fc065b0c1545c50e1fd46f5e174854b09083075c223dd、sampling_rng d0ea4e18f0e56618ac216efbcea463bf09b1a51d35f44a43b32173109f4547da、mamba_buffers d9a05fef68331f425bf60f3683c7b9da7956d2f3f55fe621a69bdf096a07816c、native mamba_utils934e9d2a919d71badc3beb7e474b1508483f6298a171e67ed153b3bb3c0e4a49、sampler1a2f18ddc91c89f3744ab5a93624be056bf20b7a8b2e6e13d0236182718a2253、topk_topp35b9a1ffeb1e50b73b0ddd1ffc0f968910ee21cf9cc5455dd879fde547b6ddc1。它们不是今天新执行或新部署的探针。当前没有launcher/RUN_ATTEMPT或新请求排队。

### doc81免重启取证入口只读实核（2026-11-02T09:43:06.430608+08:00；0模型/控制POST、0埋点/服务变更）

用户本次只授权核实当前8010是否已有安全入口，未授权执行此前3×128方案。结论：**已找到现有通用I/O dumper和源码内RPC/profiler，但当前绑定graph服务没有可用的完整logits/RNG/Mamba安全免重启取证入口；这不是已部署新修复。**

运行证据：API1336953/start607626732/argvSHA c1b658b05137910a59f347c6fbb9048146d22f1274886b324b761803a9f30fbc保持；沿该API的children关系仅检查其EngineCore1344788及TP0..7 workers1349115..1349122，NSpid与原8010日志1983444/1983731..1983738对应，未查其它服务。启动日志该实例line47明确dtype=torch.bfloat16、enforce_eager=False、FULL_AND_PIECEWISE；现argv仍BF16/TP8/原graph配置、无--profiler-config。12个入口/修复/原生采样源码SHA全部匹配D/source-before冻结原件，原start-model.sh SHA875788ff3053946c6f25232f8699a24027184d80c4375af1fe0bde75fa7a3f4b保持。未attach或读取worker函数对象内存；代码归属证据来自绑定实例、启动日志和源文件SHA，不冒称直接取到worker内存对象。/proc environ只能观察初始/可见环境，不把其缺字段当运行时Python os.environ的独立充分证明。

| 候选 | 当前实际代码与运行证据 | 判定 |
|---|---|---|
| Plugin I/O dumper | `/opt/vllm-plugin-FL/vllm_fl/dispatch/io_dumper.py:752..764`，第758行`if _enabled or not eager: return`；`model_runner.py:5431`在load_model传enforce_eager。当前False；第866行确有`enable_io_dump()`进程内API，但静态调用扫描未发现把它接入服务控制的调用者或热读配置/信号控制入口 | 现有库函数不等于当前worker安全开启入口；在另一个docker exec Python进程调用，只影响新进程，不能启用现有worker。改env/YAML不能自动跨进程/追溯生效。不能为用现成dumper擅自转eager |
| profiler | `entrypoints/serve/profile/api_router.py:40`仅profiler_config.profiler非None才注册；WorkerFL `worker.py:1050`无配置直接RuntimeError。当前OpenAPI无/start_profile、/stop_profile，实际只读GET均404 | 未启用；即便启用，时序/shape等通用profile也不等于全raw logits、实际noise q、generator生命周期和Mamba state快照 |
| collective RPC | `entrypoints/openai/api_server.py:197`仅VLLM_SERVER_DEV_MODE时注册dev router；`entrypoints/serve/__init__.py:49..51`再注册/collective_rpc。初始API环境无该变量、默认0，当前OpenAPI无路由，实际GET /collective_rpc=404 | 当前外部入口不存在；没有向内部IPC投递命令、序列化callable或注入代码，不以内部RPC实现存在推断可安全使用 |
| 既有修复 | `sampling_rng.py:29..35`只在discarded seeded行保存/恢复entry offset；runner4723包裹sample，native topk_topp_sampler.py:437..468构造q并在div_/reciprocal_前后消费，未导出actual q/RNG。mamba_buffers分组修复也没有完整生命周期快照出口 | 行为修复与取证接口不同；HTTP logprobs拿不到这些机制证据 |

**完整取证最少需要放宽的边界：** 保持当前绑定实例且不使用未核实热注入方案时，需同时允许“新增有界worker埋点”与“仅8010 engine/workers一次受控重启以加载埋点”；只放宽请求限制或只改文件不够，只启用dev-mode/profiler也不够。实施采集还需另行授权此前3条短C1请求（trace-off/on/on，cap128；当前授权0），不是自动追加。埋点可优先在Plugin包装扩展点实现，保持BF16、现有修复、数学/RNG/cache语义及FULL_AND_PIECEWISE，预分配有界缓冲并在新worker生命周期中完成必要graph捕获。若扩展点确实覆盖不到才另行提出vLLM源码例外；本次不修改vLLM或任何生产代码。不需要放宽8035/物理0–7/提交推送禁令。若坚持现8010零重启且禁止注入，则完整方案保持不可执行；没有把另起实例、抢占8–15或改eager当作默认替代。

重启会产生新服务身份，需重新绑定，并核doc81相同prompt及前128输出ID匹配原冻结C1轨迹；不匹配则不能声称取到旧轨迹。旧C32没有保存内部logits/RNG/state，任何未来采集不能补回历史内部事实，也不能单凭3条C1确认原C32唯一因果。

最新计数generation5820486/prefixqueries322022/prefixhits32000均未增。新服务窗口inode27006868286/start9763178/end9763719/541bytes/SHA67b54eba686fd27c592c1825130464192f208132710fabdfc6cde33e16012ed5无新fatal/RPC/Traceback；此为附带核验而非定位/修复成果。本地控制面沙箱Ansible RPC/DNS限制已改用同一获准只读检查完成，PPU-07 connectivity ok3/changed0；不是新模型故障。没有模型/控制POST、GPU重放/编译、远端文件写入、埋点、服务动作或提交推送。

只读证据/private/tmp/acc023-doc81-hook-check-20261102：entry-check-02（活OpenAPI及源码）SHA94a2f725c5f1dd8fa11e8aefc50575235446e0575248b2fdeebc10a2b076e2d9；entry-check-03（关联worker/启动日志/来源）SHA5698706113794de71aa7d2c011d586784df1594e39d026acc8274c2d21b70fa9；entry-check-04（3候选路由GET404/源码核同/计数）SHAfeae11d6d0d521785f9193a446d4bc25468ab00ae232687667a60a9111c35e6e。汇总readonly-hook-report.json SHA64795bee4845de328e6256be657c750cfc98e235c2e6ae6a195bf61cade7e221；只读收集脚本也在同目录，未安装到目标环境，不是运行中埋点或模型launcher。后续monitor不重复本次静态扫描，不因本报告推定执行授权。

