# 点42：有界 Prefill 合批与晚到接纳

- 实验 ID：`20261019-ready-prefill-coalescing-42`；分类 `framework`；状态：三臂闭环，Mixed `failed`、Decode guard `incomplete`，整体`incomplete`，候选不保留；原服务恢复审计通过，monitor已暂停。原日志失败轮单独保留。
- 精确范围：PPU-13 / `glm5.3-flash-opt-20260911` / 8011；延续既有隔离案例，不触碰适配容器。
- 父目标 `p32768-d1024-c64-n128`。不组合点41的 threshold16384，MBT32768、maxseq64、threshold0 保持。

## 优化方向与瓶颈依据

点41已关联 HTTP/render→核心接纳→批次 shape→执行跨度。三轮含 Prefill step 数5/3/4，后段 Decode step 中位数约34.6–34.8ms；额外零碎 Prefill 与晚到请求错过 step 边界，而非已证明的单算子随机失速。不同 seed/探针开销限制因果比例结论。

规划复盘保留点39基线、点40暂存未安装、点41 Mixed +5.3491%且 Decode guard incomplete 的区别；没有新 anchor→组合累计收益，不能相加单点数字。

## 优化内容与适用边界

拟通过原生 `--scheduler-cls` 显式选择 Plugin 内 AsyncScheduler 子类，默认服务不变。复用原生 `schedule(throttle_prefills=...)`，不改 vLLM、不 patch EngineCore，不 sleep、不建立第二套 KV 分配或输出更新。已有可执行 Decode、无部分 Prefill、普通 FCFS 文本请求时，最多100ms/8步合批；满 maxseq 或到期释放，不因新请求到来无限延长。没有 Decode、单请求、部分 Prefill、复杂 connector/MM/LoRA/恢复/推测路径均回原逻辑。原生 capacity/DP 节流语义保持。

这些是实验边界而非跨平台性能结论。必须测试超时释放、持续来流、取消、空队列、达到输出上限、非目标路径和无空转；当前仅 PPU TP16 硬件范围，其他平台未测。只新增独立 Plugin 模块/聚焦测试，保存已有工作树，不改共享默认配置或交付脚本。

## 正确性与路径命中

使用 `inference-accuracy-evaluation/minimal-regression`：先行为单测，再同配置 C1/C8、固定 token 边界、迟到/取消服务探针；核验 graph capture 和至少两次 replay。baseline、candidate及恢复实例的请求语义回归均通过；capture与多token C1/C8覆盖至少两次Decode replay，不是逐replay设备trace。实际新 Prefill 延后且 Decode token 已调度的hit日志缺证，不能仅以类已选中证明命中。不签发完整精度 gate。历史用户认可补充合并173/198与原生169/198仍分开保存。

## 性能效果

使用 `inference-performance-evaluation/targeted`，预冻结 baseline→candidate→revert 各独立实例，每角色先 Mixed `P32768/D128/C64/N64` 再 Decode `P1024/D512/C64/N64`，8 warmup+3 measured，末3 warmup 吞吐极差≤5%。Mixed 吞吐改善≥3%，P99 TTFT/TPOT/ITL 退化≤5%；Decode 吞吐及各 P99 退化≤5%。两阶段 measured 极差≤5%、baseline/revert 漂移≤3%，保留全部 measured，不挑种子/慢轮。每轮1800s、规划14400s。

以下为每臂3个measured轮中位数，P99不是跨轮合并分位数。baseline来自原轮，candidate/revert来自日志修复接续；最初因日志断言中止的候选没有性能数据。三臂均完成两阶段各8warmup+3measured，未删慢轮、未更换种子或放宽原门槛；原生比较与独立审计已完成。

| 阶段 | 角色 | 输出吞吐 token/s | P99 TTFT ms | P99 TPOT ms | P99 ITL ms |
| --- | --- | ---: | ---: | ---: | ---: |
| Mixed | baseline | 36.007581 | 222728.086 | 1712.696 | 3498.246 |
| Mixed | candidate | 36.020500 | 222635.819 | 1711.960 | 3499.350 |
| Mixed | revert | 36.006874 | 222718.988 | 1712.634 | 3500.324 |
| Decode | baseline | 1414.056136 | 5251.007 | 43.466 | 36.070 |
| Decode | candidate | 1365.184691 | 6079.732 | 43.041 | 35.813 |
| Decode | revert | 1433.381873 | 4980.839 | 41.068 | 36.000 |

baseline两阶段各8warmup+3measured完成，measured共384成功、0失败。Mixed测量吞吐极差0.00917%，TTFT/TPOT/ITL极差分别0.02121%/0.00585%/0.07426%，末3warmup吞吐极差0.04046%；原生check_run重验通过。

baseline Decode吞吐/TTFT/TPOT/ITL measured极差分别2.95996%/6.62326%/3.49915%/1.84390%。TTFT三轮5199.975614/5547.763686/5251.006858ms，**原路径基线仍超过冻结5%稳定性门槛**；全部保留，不删除或放宽。这不是候选造成的退化，也不能用它声称合批已改善波动。

candidate两阶段各8+3完整完成，measured共384成功、0失败。Mixed吞吐相对baseline仅+0.035879%，低于冻结+3%；P99 TTFT/TPOT/ITL变化分别−0.041426%/−0.042977%/+0.031580%。Decode吞吐−3.456118%，P99 TTFT **+15.782213%**超过5%守护，TPOT/ITL为−0.976669%/−0.714099%。Mixed原生比较明确`failed`，唯一失败项为主指标提升不足；回退吞吐相对baseline仅−0.001964%，不能把此结果说成有显著端到端收益。

candidate Mixed吞吐/TTFT/TPOT/ITL measured极差为0.027829%/0.013577%/0.024200%/0.215731%；Decode为0.658435%/1.539956%/0.714755%/1.988696%。候选轮间波动较小不等于整体更好：TTFT中位数已变慢。末3轮warmup吞吐极差Mixed0.028824%、Decode4.574369%，均按原5%准入通过。

revert Mixed吞吐/TTFT/TPOT/ITL measured极差为0.009446%/0.008060%/0.007131%/0.069961%，相对baseline的绝对漂移分别0.001964%/0.004085%/0.003654%/0.059414%，均小于3%。Decode回退四指标极差为1.743916%/**7.100835%**/1.946818%/2.187059%；绝对回退漂移为1.366688%/**5.145070%**/**5.515713%**/0.193604%。TTFT的baseline/revert波动超过5%、TTFT/TPOT漂移超过3%，同时候选TTFT退化超过5%，故Decode guard保持`incomplete`，没有解决本场景的尾延迟波动/漂移。该指标含填充/排队/接纳，不能据此推断纯Decode kernel不稳定或分离候选的精确因果份额。

revert末3轮warmup吞吐极差Mixed0.041843%、Decode4.985608%，均在冻结5%内；不能因后续measured问题改写预热判定。六组测量共1152个measured请求成功、0失败（含复用baseline）；加预热共4224成功，完整66轮均保留。整体completion为`incomplete`而非成功，Mixed失败和Decode证据/稳定性缺口分别保存。

Mixed于10:37:44完成，run-record SHA `e7fc7226519af8a67d02612cd5612d802703e25dfc7ebaad5151ca81e6b3e095`；Decode于10:45:12完成，run-record SHA `33b1f3b57b7dd2b9417cdca1f57ea4b6bb791c7a90b69a4dffa1d3fba26ffd12`，11轮原生validation/输入输出引用SHA和64×512计数均复核有效。

仅原生预热稳定性失败且服务健康空闲时，保留 incomplete，继续其他预声明阶段/角色；数值、服务、原生有效性失败则停止并恢复。缩减三臂不是正式 D1024/N128、四场景或长期容量验收。

## 决定、风险与回退

决定：**不保留有界合批候选**。真实短探针命中和较小的候选轮间波动都没有转化为可保留的Mixed收益，Decode守护仍不通过。100ms等待可能增加TTFT，目标性能流量内的hold命中率尚无分段计数，不能据短探针命中推断稳态成本占比或把所有退化精确归因于该策略。原Scheduler、原源码内容及用户参数已恢复，恢复审计通过；仅本点新增的三个SHA匹配文件被移除、外部原本可恢复，原有dirty不动。交付脚本/vLLM/权重/tokenizer未改，无提交/推送；本轮闭环，monitor暂停，不自动叠加新优化。

## 外部证据

远端新目录（创建前确认不覆盖）：`/mnt/nfs/users/jinghao/glm5.3-flash/optimize/e2e-opt-20260911/resume-20261019-point42-ready-prefill`。命令/原始结果/补丁外置，执行前补充路径与 SHA。

变更前当前实例 `PPU-13:glm5.3-flash-opt-20260911:2536898:505188227` 健康空闲，Plugin SHA `25362361572ea6dc6d6bc62dbac4e3ff31cbff2c50d032c1ebbb2ab47cc16ce0`；其余源码/DB/权重/tokenizer与点41恢复事实一致。完整当期快照在远端 prepare 保存，旧最小回归不自动绑定新实例。

执行前保存的命令为新目录 `commands/control-v1.py prepare/dispatch`，SHA `b9b2d64349130aad5af4ff29f59042182299fb2ad15a41489d841b7a709eb98b`。先只读核验父目录owner/权限/空间/规范路径及新目录不存在，再通过限定PPU-13的Ansible file/copy创建唯一commands目录并保存控制器、候选与测试；prepare只冻结证据、原生dry-run，不修改服务。dispatch只派发一次，运行日志与操作保存在该新目录。

候选源文件（均先暂存到commands，不直接写运行源码）：`prefill_coalescing_policy.py` SHA `7680fc60887ddff97a3337ee5ab01491c0d404db639deb7943acf862bab674e5`；`ready_prefill_scheduler.py` SHA `810d2ac339face89fb3ff880169179310901af6562014f8cc207242788e18acb`；`test_ready_prefill_coalescing.py` SHA `2b1145af6fe0e9be4c9d970a0b37186059c0fa8cc6bf284a05ad608de257e2e0`。CPU行为14项通过，只证明策略与路由，不证明硬件/模型性能。运行时逐臂切换：baseline用原源码/原Scheduler；candidate仅新增这三文件并显式选类；revert只在SHA一致时移除这三项，原有dirty内容不动。结束恢复原源码内容指纹、参数、权重/tokenizer/DB/thead/环境及最小回归。

当前维护版工具全量Python文件打包 `commands/evaluation-tools.tgz` SHA `aec075144a7fb6b05b5ff4b60928e3b11c6745566c203dd909ec6a2470192426`，解包到新任务workspace并逐文件核验，不改旧轮工具。Skill完整bundle：performance `872b65dd0e7a4e8c5b342c37b1c34729f14154d1e68be01ed60938d5b22dc8d1`；accuracy `6e94a080dd3b64544c535e1fd4bda506f55516374d14d0f8ca6aa148bba2c7b2`；完整绑定 `commands/skill-binding.json` SHA `f65078b63ea974bab0f6a28d7f9b01fba8fdc6b017b5f845b41a628f5f6fd401`。

prepare v1在服务变更/请求之前因macOS tar携带16个AppleDouble `._*.py`元数据条目，触发严格代码清单不一致而停止。16个真实代码文件SHA全部相同；旧archive/workspace保留，不以忽略错误放行。v2使用不含元数据且16文件逐项相同的新archive `commands/evaluation-tools-v2.tgz` SHA `e1d13932568d0e0ead071d69a6074b64374c25b14b31378a5b46e84bc24c1e3c`，新解包路径`tools-v2/workspace/`。恢复控制器 `commands/control-v2.py prepare/dispatch` SHA `3a69f1123a01f43bf0df7e254526235e257fc95251ef72ebf1dc9be6f5409ca8`，只复用并校验已保存原始身份/隔离/补丁证据，继续未执行的单测/CLI/dry-run；不重复任何模型采样。

09:47已唯一派发宿主控制器PID1898031，`controller-dispatched.json`与`operations.jsonl`对应；原实例2536898按空闲检查退出，baseline正在初始化。候选源码尚未安装，candidate/revert未运行，当前没有新性能数值或正确性结果。新freeze SHA `8b5773449c5247f629a57da1d7cd80ee70f613926d7ad21cc83ebf3a27d8f16e`，隔离刷新SHA `138fe8ee259c91abf604d445ac818583c8d7d5a4bd84b49a9744c73552eaf210`。两阶段原生dry-run各11轮逐项核对长度/C/N/EOS/seed，SHA分别`f1b5fbed1729b0343c5507bb2b6e66034ccac506b757f82b0ca930ea340bed7a`、`c578009046b56e606303e7fe3fcdf2ec070834f5c36bfdbd6da16ebaadce3855`。

复用30分钟heartbeat `glm-performance-20261018`，监控目标已切为点42，只有实质进度/失败/完成/需操作才通知，终态恢复审计后暂停；不再操作点41。单独Decode guard沿用的说明文字仍提及旧threshold实验，该文字不是本轮变量声明；实际变量由本轮comparison及逐臂runtime断言限定为Plugin文件/显式Scheduler类，threshold固定0，不能按旧说明擅改参数。

补充只读安全快照命令 `commands/db-snapshot-v1.py`（SHA `133ac1477023a65cc922fd15a8a9927ca970b71d525f8be4188bf97af66c0da4`）：在基线初始化阶段仅复制精确私有FlagGems调优DB到本点`patches/flaggems-db-before.sqlite`，先后核验原SHA，不改数据库/服务。用于未知shape调优意外写DB时保有原内容回退来源，不是性能变量或重跑；结果另存`db-backup-receipt.json`。

09:55核验：baseline实例`PPU-13:glm5.3-flash-opt-20260911:2544568:509025462`于09:51 ready、完成11个FULL Decode capture sizes；C1/C8、16383/16384/16385边界、50ms迟到C8及主动断流取消清队列检查全部通过，health200。当前Mixed预热进行中，candidate尚未安装/测量，没有新收益结论。runtime/service/minimal/late/cancel SHA分别`e7d088a760f7266969e6ef805cf7601675afa9be44b0148406ec8e33d7fdca49`、`ac60d5a035b996134067ad91677e22bae9fb292389a59f4acf1f50d79cd2a776`、`c80adf4e96e9f4ef7cbf9ca444d8f46cadf6d55df4d82d1e6cc0e6ed7e09c350`、`3117bcce54149b54b55b578dceffeecbe84367511e06589d95664f501368fe2d`、`181bdcffa2e8479ef355d1d7d576943a54ed2a0c069f113ed35d4f3a559c21fe`。

DB只读备份完成，22,175,744字节，SHA仍为原`1917ccd26c170ca3d7c76197e662a862d3bfbdb1b6da064259bf2202eca38a83`，receipt SHA `87e11db703fd37323cfbb54c14be10f3d0e6941b9691e78eab1e8cd71eddf5d3`。本地YAML/链接及diff检查通过；全项目记录审计仍有292项其他案例/既有过程文件问题、GLM相关0项，未修改其他案例以掩盖债务。

10:20只读跟进：baseline Mixed已完成6/8轮warmup，384请求成功、0失败，每请求128输出token；原生validation与其引用的output/raw SHA逐项通过。第7轮原生benchmark进程参数为冻结的seed391729/P32768/D128/C64/N64。当前实例PID/start_ticks/argv仍精确匹配baseline runtime，控制器PID1898031存活且命令SHA未变，health200。尚无measured、candidate/revert或比较结果；预热不作为收益/稳态通过。继续既有唯一控制器，不修改服务、不重跑或放宽规则。

10:47只读核验：baseline两阶段完成，10:45:16控制器按原计划安装三个候选文件，安装后CPU14项通过，启动candidate。当前仍加载权重、readiness待完成，尚无候选最小回归/命中或性能结果；未启动revert/最终恢复，不把启动期间health未开放视为已确认服务故障。此轮未新增请求或修改控制器，继续既有三臂；本轮新基线TTFT波动较早前基线的变化不归因于尚未启用的合批候选。

10:53：candidate于10:48:47 ready，C1/C8、边界、迟到和取消最小回归通过，但控制器10:49因缺少激活INFO日志断言`AssertionError('scheduler not loaded')`中止，未开始candidate性能采样；revert也未运行。候选日志已有EngineCore选择该自定义Scheduler类的WARNING。新解释器同容器只读探针发现`vllm_fl.worker.ready_prefill_scheduler`有效级别30、INFO关闭，而`vllm`命名空间INFO开启；这是日志观测断言问题，不能据报错断定类未加载，也不能用类选择代替实际合批命中。实际hit仍缺证，候选不晋级。控制器已SHA校验移除仅新增的三个文件并在10:52:51恢复原服务与最小回归。

执行前保存终态只读审计命令`commands/terminal-audit-v1.py`，SHA `f430aa0813b815ac33c88498327fd619c857c83b93fb601dbd68323aaaa357a1`。只核验身份、既有回执、健康和路径证据并写新`terminal-audit-v1.json`，不发模型请求、不改源码/服务、不重复性能采样；原始completion与错误保留。

10:55终态审计通过：当前原配置实例`PPU-13:glm5.3-flash-opt-20260911:2584396:509395265`，argv、环境、源码内容（含原有dirty）、权重/tokenizer/DB/thead均与实验前一致，启动脚本SHA未变、health200且空闲。仅本点新增且SHA匹配的三个Plugin文件已移除，外部commands原本仍在、可恢复；未动用户原有改动。恢复实例完成11个FULL Decode capture sizes和C1/C8/边界/迟到/取消回归。`completion.json` SHA `8e6f9d41aca2b4af36baa61b4f7a9d74d2089c4512ae06960a0e8ea510795491`；`terminal-audit-v1.json` SHA `37921b6c20a3fb4c1f0a05e66fe5c663dd3cd9efecb69508660f1ee2ef3eae07`；恢复runtime SHA `ab127f22bade4dd7301bc8b52aca5e31c18269c6e06b628a05d5e08a209bbae5`，minimal SHA `8ab9598a92b07cf6e07ecabc815dfa5a6c1744472de253470705f05d4ae29a3b`。审计未发模型请求。

结论：本轮整体`incomplete`，不是候选变慢或数值失败；Mixed/Decode只有baseline，无端到端收益或回退漂移结论，原Decode TTFT稳定性缺口保留。monitor已暂停。下一步尚未执行：以新版本修复Plugin日志可见性，先证明真实hold且Decode继续/new_prefills=0的命中，再复用已有baseline、仅恢复未运行角色；不盲目重跑整套、不追认guard通过。交付配置未变，候选未保留。

## 日志修复与接续：logging-recovery-01

用户明确授权修复日志观测、确认真实命中后继续Mixed/Decode三臂，MBT与门槛不变。新产物只写同一远端根下`logging-recovery-01/`，旧错误/completion/审计/原始baseline保留。只改logger赋值为`init_logger("vllm." + __name__)`，使用已有vLLM日志handler，不改root级别、不逐step刷日志；prepare用AST剔除logger赋值后对比旧候选，要求策略代码完全相同。新增logger命名测试后15项CPU测试通过，仍不是硬件命中证明。

执行前保存新控制器`logging-recovery-01/commands/control-v1.py` SHA `2b39fdea98e6c494c5b64ee7b23f94dbb784c772fe95a2e7473e6d894c21d80c`；修复adapter SHA `0766a425bb4e8ffcfc80d3f4e6da685feb3446eb52be8d2250c735a605a22828`，测试SHA `fcc734cd515a52a22f9cd5f630cf0d760426f74016dbbcec6c6bc13e20e3fac3`。Decode守护路径适配器`commands/decode-guard-paths-v1.py` SHA `f5bba493411667fe0d2fe49d47380aa22765d992042ce34bd8b0ffb938291610`只支持baseline留在旧根、candidate/revert在新根，原有原生SHA/计数/指标/守护逻辑不变。控制器prepare不发模型请求、不改运行源码，先核对当前恢复实例、隔离和原生baseline回执。

继续采用`minimal-regression`与`targeted/performance_only`，复用原Mixed/Decode计划、比较与守护契约的原始字节和工具bundle，baseline使用原路径而非伪造新测量。只执行尚未采样的candidate与revert，仍各Mixed后Decode、8warmup+3measured、末3预热吞吐极差≤5%，Mixed≥3%、尾延迟/Decode退化≤5%、measured极差≤5%、回退漂移≤3%，原baseline Decode TTFT6.623%缺口不消失。此前173/198补充精度与169/198原生结果边界保持，不签新gate。

candidate最小回归后、性能前只执行一组命中探针：先P1024/D128流式请求，在收到首个有效text token后加入7个P1024/D16请求；检查真实日志waiting/running/Decode tokens均>0且new_prefills=0，记录释放和所有请求完成。该探针不进入性能聚合，不通过则停止晋级并恢复，不改策略阈值或盲目重试。结束无论性能结果如何，移除仅新增的三个SHA匹配文件、恢复原服务并审计，不自动部署候选，不改vLLM/交付脚本、不推送。

接续预检完成：仍为上一恢复实例且空闲，源码/revision/安装导入与DB等稳定身份未变，镜像及完整挂载匹配；新logger有效级别20、INFO开启，root仍30。AST与15项远端CPU测试通过，原baseline Mixed经原生check_run重验、两阶段11轮依赖SHA有效；工具/Skill内容与原冻结bundle完全相同。未发模型请求或改运行源码。新freeze SHA `8035ebf6578b3ebaff2f5fe712f92d7836815994e2917e3a9abb27b5b507af99`，随后唯一执行`commands/control-v1.py dispatch`接续尚未运行角色，不重跑baseline。

11:14:04唯一接续控制器PID3688851开始，精确停止空闲的上一恢复实例，再安装三个SHA匹配候选文件，安装后15项CPU测试通过，candidate启动。当前等待capture/readiness、最小回归与实际hit，没有新性能数据。原30分钟heartbeat已复用为该子目录监控，状态未变安静，终态恢复审计后暂停。

11:17:54路径护栏完成：candidate实例`PPU-13:glm5.3-flash-opt-20260911:2598371:509545712`于11:17:38 ready，11个FULL Decode capture sizes完成；C1/C8、16383/16384/16385边界与baseline完全一致，迟到C8和断流取消回归通过。EngineCore INFO激活日志已出现；11:17:40在候选最小回归流量中真实命中`waiting=1 running=1 decode_tokens=1 new_prefills=0`，随后`reason=deadline tokens=64`释放。后续专门8请求probe也完成后，11:17:54保存passed命中回执，再启动candidate Mixed。首次命中来自此前最小回归，不能误记为后续探针触发；该证据证明调度分支实际运行，不是端到端收益。

对应`logging-recovery-01/candidate/hit-evidence.json` SHA `97c0ddb8f6b6bf4868731cce260562f9f83ddfc7dd31a5a6fd753e21997d8c43`，raw probe SHA `9bc2527638016f497df362d6c51b8760409e220b4a24caf2f8ab40212cc71378`。runtime/service/minimal SHA分别`aeab21a4a6ebb167292e446f9b2eba26c5b5c7704453f007b4a026355cdc2023`、`83ebd3da2b902efaab86e391f8fc9fe5b8788af11eb81d834c9d454bd555d02f`、`32ed29d1bf830a4aaac56cd7f5652b74dd8e19b9d6daf83f536fd9bae76d6382`；Plugin当前内容SHA `0662e1c2f7bb2a973acc69c6cd525b997934f9d1387bdaa990b69a961da19f84`，其余稳定身份与原配置相同。

按`inference-accuracy-diagnosis`将`point42-activation-info-filter`归为`measurement-invalid/observability`，不是数值失败；以logger唯一改动、远端级别探针、真实EngineCore激活/hold/release日志及最小回归闭合该观测问题。旧completion保持incomplete、不重签全量gate。当前性能尚无measured或candidate/revert比较值，不能预判波动/漂移改善。YAML与diff检查通过；全项目记录审计仍有291项其他记录/过程文件问题，GLM相关0项，未修改无关模型或白名单。

性能启动后只读确认：原生benchmark PID2605312的首轮预热参数为P32768/D128/C64/N64、seed391723、temperature0/ignore_eos、random-range-ratio0，服务health200；外层runner绑定原始Mixed计划和原始comparison契约，未改变采样或门槛。尚无measured结果，后续仍由唯一控制器完成候选Decode、revert两阶段与恢复审计。

11:47只读监控：candidate Mixed完成6/8轮warmup，384成功、0失败，各请求128输出token，原生validation、其引用output SHA、raw计数及有限指标复核有效；第7轮seed391729仍在运行。当前实例PID/start_ticks及所有稳定身份键与候选runtime一致，控制器命令/冻结SHA和命中回执SHA未变、health200。尚无measured/Decode/revert或比较结果，预热不计收益，也不等于末3轮稳态准入已通过；继续原唯一控制器，未新增请求/变更，未重复派发。

12:17监控：candidate Mixed于12:04:18、Decode于12:11:47完成，回执SHA分别`54e2ac345e5243df258c73339055be9973f3d382ede3127b5d8c5a40c05e1475`、`db2eeeadaf118d32b9ffb34e0ccea78ec6c573f5724a34e23993ed641d9e2b0e`。两阶段原始输入/产物SHA、11轮validation及每轮64请求/固定输出计数全部复核；Mixed原生check_run通过。各轮保留，数值见性能表；未创建比较/guard结果，不把回退缺失当作性能通过。

控制器12:11:51仅SHA校验移除本点新增的三个Plugin文件（外部原本仍可恢复，原dirty不动），12:15:12 revert ready，12:15:26 C1/C8/边界/迟到/取消回归全部通过。当前回退实例`PPU-13:glm5.3-flash-opt-20260911:2631842:509892158`，所有稳定身份键与实验前一致、health200且11个FULL Decode capture sizes完成，Mixed已启动，最终恢复尚未执行。runtime/service/minimal SHA分别`8e807396614bba26c48577571d1213bf9c2493c7c4136192ed774078646c6eb9`、`e9cfc3ca5ad086021226cf6bb289525b6a5bc712f69f0e3ce38fe0b380a8a7f4`、`c9fc20094b00e85c4efb22fdc59d85abd1207f084ff1fdece348d88e43026369`。只读监控的wrapper属性名误用已改为正确的嵌套helper调用后复核，未修改控制器、请求、采样或原始结果；monitor继续同一任务。

12:47监控受工具基础设施阻断：首次限定PPU-13的inventory/连接验证在执行前因自动权限审核模型容量不足被拒；仅重试连接验证又在审核阶段超过deadline。两次远端命令均未执行，未绕过审核、发新模型请求、重复任务或修改服务。当前仅能保留12:17的最后核验事实，不能据此确认后续回退轮次、健康、漂移或终态，也不把工具故障判为服务/实验失败。heartbeat保持active，待下次只读检查；旧A/B数值与门槛不变，终态恢复审计前不暂停monitor。

13:15轮监控恢复连接：revert Mixed于13:01:49、Decode于13:09:14完成。原生Mixed比较`failed`（吞吐改善低于3%），Decode守护`incomplete`（基线/回退TTFT波动、TTFT退化和TTFT/TPOT漂移）。控制器无编排异常，整体`incomplete`，13:13:04报告原服务/源码恢复、最小回归通过；候选未保留。执行前保存只读终态审计`logging-recovery-01/commands/terminal-audit-v1.py`，SHA `667d9c94a1b53f9d572de3eaf08bdca6ca05c8f901b57b6b25f09144b65ea188`：重新消费全部既有原生结果并在内存重验原比较/guard，核对当前恢复身份、graph与最小回归，不发模型请求、不改源码/服务、不改原结果，只写新的审计回执。审计通过后才暂停monitor。

13:18:35终态审计通过，13:19暂停heartbeat。原生Mixed比较与Decode守护重新消费既有原始回执后在内存重算完全一致；没有新模型请求。当前恢复实例`PPU-13:glm5.3-flash-opt-20260911:2657999:510236917`，argv/环境/全部源码及原dirty/DB/thead/权重/tokenizer逐项与实验前一致，镜像/挂载相等，原脚本SHA仍`5b1d0a52b129ada50cf38f2ba35194cb43d67a41901d2876e1150e4e7eef31ca`，health200且空闲，控制器进程已退出。FULL Decode 11个capture sizes及C1/C8多token覆盖至少两次replay，边界、迟到、取消回归均通过；不是逐rank设备trace，也不签新精度gate。

新根`logging-recovery-01/`的最终证据：`comparison-result.json` SHA `185588bd2a3b8078bbcb75b84f833b34bad41830ef0cf4a43db4852567228923`；`decode-guard-result.json` SHA `555fac9424cae2fd80de864b83b2fb97ddeff59723b9efb68f8252e6cc4f6276`；`completion.json` SHA `23ccf19602fec4919da1e5f68de128b581ded656f5378bdae6a53209522c6683`；`terminal-audit-v1.json` SHA `a0526e92c63767fcda69829369d224e22381c1f2e5c4c7ca42906eb1991bc208`。revert Mixed/Decode回执SHA分别`54984cdd4a3d3d4fa336a6fb270334d6c15d89ea5e3f1f47cadcb839a15e57c8`、`614c400db9c8785172ee61ac4b145badc009edede85eb21dbca5a8421864f434`；恢复runtime/minimal SHA分别`1424b7e8f4426b4c54c8a49819f0342e81602cdca1fc3cacb3defb77f61d655c`、`1f5c83da3ba271ec3c0b6df50a9b647a52b7b15003c5db84841c7e28f8e98f16`。

### 终态规划复盘（仅记录，未启动新实验）

`planning-20261019-point42-close`按规划Skill执行，覆盖上次复盘后唯一点42及其日志失败/修复/完整三臂。当前组合恢复为点42前相同源码与MBT32768；没有加入点40、点41 threshold16384或点42，不增加累计收益，不把点41 +5.3491%或局部算子收益相加。P32K正式D1024/N128及四场景验收仍未关闭。

阶段判断：Prefill没有新增隔离测量，TTFT仍混入接纳/排队；Decode较小候选spread伴随TTFT变慢且回退漂移，不能证明纯设备循环不稳；Mixed比较稳定但无显著收益。短探针有真实hold日志，正式measured轮的hold率/shape变化尚无分段计数，因此既不能声称性能流量从未命中，也不能把短探针当收益机制闭合。

下一步仅列两项、均未派发：①优先细分frontend render/IPC/核心接纳，并在需要时冻结低开销Plugin计数的off/on开销验证，确认稳态目标流量中何时hold、shape怎样变化；证据不足/探针扰动过大则停止，不扩大等待窗口。②只有当前shape热点已确认后，再做小Mixed形状的算子完整交易特化，先比较prepare/kernel/merge/copy总成本、reference/graph/fallback，再用原Mixed≥3%与所有守护验证。具体边界、Skill、首个证伪和回退在state的同名规划条目；均保持原Host/模型/MBT，不改vLLM。点40小量级host-sync探针、盲加预热/换seed/扩大合批窗口和MBT扫描暂缓。下一次新因果或live-shape证据出现后再复盘。
