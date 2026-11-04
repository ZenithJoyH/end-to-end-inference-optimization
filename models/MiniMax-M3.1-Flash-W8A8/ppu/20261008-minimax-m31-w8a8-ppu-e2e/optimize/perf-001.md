# perf-001 P1K 入口稳态基线与阶段视图

- 模式：inference-performance-evaluation / baseline后targeted恢复；状态：complete诊断视图，原目标incomplete；场景：p1024-d1024-c64-n128；依赖：acc-001范围内通过。

## 优化方向与瓶颈依据

当前无可比端到端基线。先建立完整 P1K Mixed 基线，用 TTFT、TPOT/ITL 作为 Prefill/Decode 客户端代理，并以独立 P1024/D1/C64/N128 探针补充 Prefill 视图。TTFT 与 TPOT 不视为纯设备耗时。

## 优化内容与适用边界

无源码变化。输入/输出长度固定，finite batch，C64/N128，random workload，temperature=0、ignore_eos=true、seed=42、prefix cache disabled。3轮预热、3轮测量；预热3轮总吞吐 spread<=5%才准入，保留全部正式轮。每轮600秒预算、首次基线尝试总诊断预算3600秒；超预算保留partial证据并转hybrid recovery。正式累计比较最终必须有anchor/candidate/revert独立重复，本次首个入口测量不能单独成为完整比较。工程显著改善门槛预冻结为总吞吐+5%，TTFT/TPOT/ITL/E2E P99各允许最多5%回退；无业务绝对SLO，不宣称业务达标。

## 正确性与路径命中

两次 graph-eligible smoke通过，C8前十题sanity正在运行；未结束前不发送性能流量。

## 性能效果

| 场景 | 范围 | 状态 | 总吞吐 tok/s | TTFT/TPOT/ITL/E2E |
|---|---|---|---|---|
| p1024-d1024-c64-n128 | Mixed入口基线 | not_run | — | — |
| p1024-d1-c64-n128-prefill | 阶段探针 | not_run | — | — |

## 决定、风险与回退

先测当前服务。capture32/seq64路径是待确认线索，不因配置静态差异直接选定优化或宣称收益。Baseline/Candidate/Revert变更启动参数后分别取证；纯重启不得自动继承精度gate。

## 外部证据

/mnt/nfs/users/jinghao/minimaxM3.1/optimize/20261008-minimax-m31-w8a8-ppu-e2e/performance/entry-p1k/。配置准备脚本 `commands/perf001-prepare.py` SHA256 `9333a819eb663dbfcbbdd1b93929eab80006e383273f41670571a281cdc98c1a`，执行前保存；先dry-run再测量。

测量前 dry-run 拦下 comparison.json 的非法 scope=diagnostic。比较契约只接受 formal/performance_only；本任务保持 formal，comparison-v2.json 改为 formal，并将宽泛 /launch_config 指针收窄到 /launch_config/cudagraph_capture_sizes，供后续候选比较绑定。基线实际运行仍是 diagnostic，无正式精度gate时不得签发formal候选结论。未产生性能测量结果，保留原无效准备文件。修复同由 commands/repair001.py 完成。

待sanity核验后执行 commands/perf001-launch.py，SHA256 `099b281c61d84113333230e51fe5a26755da3dfd8b719bd21104ec88210cd951`：核对当前service PID/starttime、health和无重叠评测客户端，再以已dry-run的冻结计划启动baseline-p1k-01。每轮600秒预算、整个首次基线3600秒诊断上限。

C8 sanity已exit0且10唯一ID/20filter行核验完整，strict7/10仅作范围内观察，无正式gate；开始scope=diagnostic baseline-p1k-01，不签发正式候选或收益比较。

启动器 commands/perf001-run-baseline-p1k-01.sh SHA256 c207808d506779464af3691bf2c3b554e1724268931debee339aa256767aec3c。原生GPU KV容量1026176 token；P16K/C64与P32K/C64后续可能受容量/调度影响，按顺序到达场景时诊断，不删减正式矩阵。首次P1K预热见ppu-llc编译新shape，不据此优化冷启动路径。

预先准备baseline-recovery的targeted milestone：p1024-d128-c64-n64-recovery，映射P1K原目标，保留P1024/C64，仅D1024→128、N128→64，3预热+3测量与准入规则不变。只有原目标600秒轮预算超时/证据无效后才启用；成功条件为同配置完整基线与候选总吞吐+5%、延迟守护≤5%，停止条件600秒/轮及3600秒总诊断预算；晋级须回到原P1K场景并补正式精度/独立重复。准备脚本 commands/perf001-recovery-prepare.py，SHA256 f98241e5cf6e6bedbe82ef5a7f29997e98507e16b199af8e79f5d70664636104。尚未启用或发送缩减流量，不能以它替代原目标结果。

2026-10-08 04:05 UTC慢基线C64 decode只读1秒采样：16个worker各约96.8–99.8%单CPU；PPU单次快照大多util100%、约144–163W，卡0该次util0%。样本不能代表持续利用率或证明CPU/device临界路径；保留CPU组织开销与device/同步热点两种解释，后续以阶段数据及单变量graph实验区分。服务日志持续Running64、Waiting0、output约115.2tok/s；此为低开销观察，不能代替原生完整性能结果。

恢复计划SHA：recovery-plan.json 5544660a5541ccdeacba486ac69d079b51625016610fbd5fea57cdfa51b235d4，recovery-contract.json a400b40eeb6fc0558efb37d7ad469d35d517c9b35adbd5c15f6301ce37df48f5。准备 commands/perf001-recovery-dryrun.py（SHAd30264ac0e897a8fa9559a6d00f513105f120deff5e1ffa737323c15645c7c24）校验两个阶段命令，不发请求；commands/perf001-recovery-launch.py（SHAa09a0cca35bd098c8adbf023728fabfe289e2e6e0e7c8743e4de60d849066e5e）保存后待原600秒timeout终态、无重叠客户端、running/waiting=0且实例身份一致，才顺序启动Prefill探针与缩减Mixed基线。任一阶段失败即停止后续阶段，保留原始证据。性能Skill下一调用显式targeted，bundle SHA与baseline相同，操作选择独立冻结。

原P1K首轮预热按600秒预算终止，客户端exit1，原始run-record与round output/validation均保留；未产生完整原生benchmark JSON，不存在可报告目标吞吐值，状态deferred-too-slow/incomplete。两个恢复阶段dry-run均通过，尚需running/waiting=0后执行已归档启动器。

超时核验：round returncode124，stderr progress0/128，未完成任何请求且缺原生JSON；缺计数/指标等validation错误均源于timeout后无原生结果，不掩盖。2026-10-08 04:10:25 UTC当前metrics running0/waiting0；准备按已审dry-run启动顺序探针。

顺序恢复启动器SHA 6a45711a380ad39ec891ec7accc2bccaab05936e61f0cb1a6899173a37da6c7e，wrapper SHA f336754f8e8814ff096a7b00f6b7fbf01bd41518aeabd77726ca5d83c4f4cfc3。Prefill原生独立run baseline-p1k-prefill-01先运行，成功才启动baseline-p1k-recovery-01；原目标仍incomplete。

### 稳态与绑定修正

Prefill-01三个有效预热轮为4005.9989、10196.0529、10301.8537 total token/s，spread61.74796%超过5%，整run incomplete，未进入测量，缩减Mixed未启动。新计划采用5轮预热、3轮测量，末3预热轮仍须spread≤5%；原首轮保留，不删轮。

严格比较预检还发现设备ID需为唯一字符串，原清单为对象；capture参数同时存在于标准字段与launch_args，需把两处表示绑定为同一变量。修复脚本 commands/perf001-fix-bindings.py SHA256 `67d844c179e4a17c0e63dcc2d608bc87923a0323b2b9dd6befd8058af8abe47c` 已归档执行，核验同一PID/starttime/cmdline与PCI ID后仅新增配置，不改服务、设备、源码、阈值或旧产物。执行前的本地登记写入命令因编码错误失败，该命令的工具调用与SHA仍可追溯；此处补记，后续分离登记与执行并检查成功。

新增baseline-service-v2.json SHA `4fe65ac49984ce0a92eb8d483c49fd3b1f2b3fa294b53f4eb4a37cab1cfcaa3d`，严格service_identity通过；comparison-v3.json SHA `569d01961b1b464fba1742b6b88c30816ade270387ed059dc06c68cabd2d93b6`；prefill-plan-v2.json SHA `4559d835153b4bf7b3d28af8302b0adfc53682e37a6829b38d1c88e9c758c0cd`；recovery-plan-v2.json SHA `b5e16e68df647cc22db03389796d179197456a3c9cd503f59eeaf2eac1364843`。两阶段新dry-run均通过，在任何可比缩减Mixed测量前冻结。

执行前登记 commands/perf001-recovery-launch-v2.py SHA `f02cd5bae36433546b12bf65c3ded872d3bb6eaa3e847f5c14fc98a1cb1ee12e`。只在旧流程终态、Mixed-01未启动、same instance及无活动请求/客户端时，使用上述新manifest/计划顺序启动prefill-02与recovery-02。任何失败停止后续阶段，保留全部预热和测量证据。

执行前登记 commands/perf001-summarize.py SHA `c0359de4ebe690e2aaea5a6f97e363e161c16cce25481cb0a108db87402f239b`：仅在原生run-record完整后重验输入/结果/输出SHA与原生schema、配置、计数、3测量轮，保留全部轮；按metric计算中位数和spread。缩减Mixed额外调用严格check_run，单实例回执不冒充独立重复比较。阶段摘要仅新增外部文件，不能替代原目标或formal结论。

实际路径补核：PlatformFL选择WorkerFL，WorkerFL实例化ModelRunnerFL；API环境未设置BREAKABLE/GRAPH开关，当前vLLM默认VLLM_USE_BREAKABLE_CUDAGRAPH=0，因此ModelRunnerFL使用Plugin GraphWrapper。其FULL分派复用当前vLLM CudagraphDispatcher，已捕获entry通过Plugin graph.py:297执行replay。此前仅查看上游CUDAGraphWrapper不足以证明Plugin wrapper路径，这里以当前Plugin源码与有效开关补正；仍无直接replay计数器。

上述wrapper推断被后续原生启动日志纠正：MiniMax架构在vLLM配置初始化中自动启用BREAKABLE=1，基线Worker明确breakable启用。实际ModelRunnerFL:5450选BreakableCUDAGraphWrapper，其NONE分支:322和replay:423；C64>capture32回退结论保留。/proc初始environ不能证明运行中自动设置的有效开关，候选fw-001以原生日志+实际源码核验。

预先保存正确性夹具 commands/graph-regression.py，SHA `e01c799713815cfc225e7a111061827b8764e6084f92ea2f9a128304b9ceaea0`，本地语法检查通过。只有本轮性能客户端结束并创建对应accuracy heartbeat后才可执行：固定算术105请求，分别C8/C33/C64，当前实例/argv/endpoint核验，记录自然stop、准确RESULT以及running高水位和generation计数变化。用于后续候选的同请求参考、graph边界与drain覆盖，不替代GPQA门禁，不以客户端并发上限代替实际batch证据。当前仅归档不发送请求。

v2顺序流程exit0。Prefill三测量总吞吐中位9502.85token/s、spread10.74%，P99 TTFT7088.16ms、spread17.55%，保留全部轮，只能作阶段观察。缩减Mixed三轮总吞吐991.7275/988.8267/987.1240token/s，中位988.8267、spread0.4656%；P99 TTFT6722.17ms、TPOT562.35ms、ITL774.15ms、E2E74548.02ms。五轮预热末三轮spread0.9452%通过，严格单run绑定重验通过。摘要 mixed-recovery-baseline-summary-v2.json SHA fd6decbeccac453e011859ac40ec719e4ab27b6accb68abe4c68b864216150eb。三阶段视图支持选择fw-001证伪graph覆盖假设，无候选收益或原目标完整结果。
