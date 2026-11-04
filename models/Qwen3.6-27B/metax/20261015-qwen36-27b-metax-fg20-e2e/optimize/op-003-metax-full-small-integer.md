# op-003-metax-full-small-integer

最终状态：数值/graph/micro及本轮模型小整数full命中、Mixed稳态通过；本周期结束按约恢复原full，补丁归档未部署。metadata三阶段B/C/R已完成，Mixed仅+0.2646%未达2%、Decode因另一GDN重复JIT相关TTFT波动incomplete；所有角色共同使用本修复，不能将metadata增量计为full独立收益。原source18002已恢复/full20不变，监控暂停。详情见[FW002最终结果与Decode诊断](framework-002-mixed-batch-overlap.md)。以下保留原计划及验证过程。


目标：保持全20FG、GDN FP32/原atol.002 rtol.02和10%性能稳态门槛，消除服务运行中新批次尺寸触发的秒级full调优暂停。当前父目标P1024/D1024/C64/N128，milestone仍PF P1KD1C64N128、D P1KD512C64N64、Mixed P1KD256C64N128。源码仅C私有FlagGems，不改vLLM、源S、权重/tokenizer/FG注册。

## 根因证据与边界

FW002d1 profile4已在预热后复现4个约3s慢prefill。rank0迭代262/263/266/267，preprocess1.51–1.57s中的aten::full最大1.489–1.549s，forward仍1.50–1.52s；每步多约6000个native cache-clear kernel及数千full_kernel_scale试跑。rank1相同轮full N2114、2112、2128、2140，int32填-1耗1.448–1.501s。MetaX full_kernel_scale在运行中对每个新N做16组在线autotune，与数据到达/批次大小变化结合触发晚轮停顿；不属于模型数值下降或GDN数学变慢。原r3慢轮无trace，对旧每一轮不作未经追踪的逐调用断言，但新同配置轮已复现相同停顿机制。旧source restore和失败暖轮保留。

原MetaX full.py SHA a0979cd73ef42a22aaf433795dbefd3ae7caa257352468461ef442c1b9320218，FG7599dd1，原工作区只有继承sort修改，本文件干净；适用祖先AGENTS无额外文件。现有full_kernel是本仓库FG Triton kernel，标量路径可以直接使用。填充计算量O(N)、写N*itemsize，实际约8KiB，kernel仅微秒；16组调优的秒级缓存刷新不值得用于这种整数元数据。

## 最小候选

仅is_scale且0<N<=4096、dtype为int32/int64时，复用full_kernel，BLOCK_SIZE1024/warps4/stages4。保留原dtype推断、范围检查、tensorfill/item、空张量、较大N和浮点/其他dtype路径。没有新增vendor/native替换或关闭FG；当前full注册仍指FG MetaX。条件按尺寸/dtype/平台，不按模型或机器名。

候选full文件 SHA410fadafb8007cd530b4e702b78bf23ebe5c3352c7a40fdd892465f6e887d4fb；patch SHAc336b00bfa31c4c0d88ed6bc0f59b16207636dd4c4fb8ed4d9f8db29f3026824；当前仅本地草稿，安装需先过下述门禁。

## 冻结验证

先等唯一FW002d1采集结束且其原S恢复，不并行GPUprobe。独占GPU2/3再次精确暂停/结束恢复授权沿用。

1. standalone full对原生CPU torch.full：17种shape含scalar/empty/odd/1024/4096边界及4097fallback，int32五值/int64六值，共187整数用例逐位一致；另7个浮点/bool/uint8/FP64 fallback、默认dtype和6个溢出异常尝试。原模型容差不变，整数实际要求更严的逐位一致。
2. 八个真实GPU graph各两次覆盖写坏输出后的replay，含int32/int64/boundary/fallback。模型双rank graph/C8另测。
3. 未见过的N2114/2128/2140/2142/2150/2162，双方先编译等价dtype/标量对齐签名，保存首次完整调用墙钟，必须减少>=95%；四个缓存命中N的完整分配/调用/摊销sync，五组交错baseline/candidate/revert，每组50次，全部保留，candidate中位退化<=5%。微测不冒充E2E。
4. 全部通过后仅安装C私有一个full文件，重跑原metadata候选14prefix/5nativeFA数值，FG源码已变不能直接重绑旧证明；新服务双rankgraph/actualFG full/GDN/nativeattention和fresh10docC8后再性能。
5. 将full修复作为所有新B/C/R共同前置，仅Plugin c4 metadata hoist为对照变量。三phase均全新同配置记录，PF/D6warm+3measured、Mixed8warm+3measured，末3<=10%、所有measured保留；原2%Mixed收益/5%跨阶段guard/1%B-R漂移均保持。对照只解释metadata增量，相对旧未修full的累计吞吐收益仍需可比较anchor，不把旧失败轮用于百分比。

当前未安装，数值/graph/micro/E2E均pending。无正式198gate，无四场景验收，不提交推送。若任何门禁失败保留失败并恢复原件/原18002，不盲目扫参数或改阈值。

执行前外部产物SHA：
- `/public-flash/jinghao/qwen3.6-27B/optimize/flash_attention/20261015-qwen36-27b-metax-fg20-e2e/patches/op003/full.original.py` SHA `a0979cd73ef42a22aaf433795dbefd3ae7caa257352468461ef442c1b9320218`
- `/public-flash/jinghao/qwen3.6-27B/optimize/flash_attention/20261015-qwen36-27b-metax-fg20-e2e/patches/op003/full.candidate.py` SHA `410fadafb8007cd530b4e702b78bf23ebe5c3352c7a40fdd892465f6e887d4fb`
- `/public-flash/jinghao/qwen3.6-27B/optimize/flash_attention/20261015-qwen36-27b-metax-fg20-e2e/patches/op003/candidate.patch` SHA `c336b00bfa31c4c0d88ed6bc0f59b16207636dd4c4fb8ed4d9f8db29f3026824`
- `/public-flash/jinghao/qwen3.6-27B/optimize/flash_attention/20261015-qwen36-27b-metax-fg20-e2e/commands/op003-full-probe.py` SHA `3053c4f79f615fa7cdb9b61ad3e35958ab609f2cd81c023703cb5379578ee6af`

FW002d1采集与全量分析已完成：terminal SHA9167b768.../analysis SHA c1cd795b...，4profile轮共8份ranktrace全部核验，新请求每rank每轮128、kernel关联>=99.6979%；第4轮两rank各4个约3s慢prefill，CPUfull1.45–1.55s、模型forward1.50–1.58s，重复缓存刷新/调优kernel证实full在线调优根因。源18002实例946383/1792123272.69已恢复ready。全部旧失败保留。

新r4预注册：源四repo原件/20FG精确capture暂停；先独立full187integer+fallback数值、8graph两replay和6newN+4cachehit微测，通过才安装C私有full（FGtree a5184db5...），重跑metadata14prefix/5FA，再原2%/5%/10%/1%契约全新三角色三阶段。full修复在三角色中恒定，Plugin c4为唯一对照变量。最后C恢复Plugin/full原件和S18002原代码，避免直接部署未正式验收候选。每probe有精确PID/birth回执，900s有界，超时只取消其所属进程再恢复，不允许dockerexec子进程残留争抢GPU。静态AST及producer/consumer名称预检已过，尚未启动。

执行前命令SHA：
- `/public-flash/jinghao/qwen3.6-27B/optimize/flash_attention/20261015-qwen36-27b-metax-fg20-e2e/commands/fw002r4-controller.py` SHA `fc6aecaae7b8d1a303b7abdf54233d87e6b96eca8fa689278edfdad3a2393878`
- `/public-flash/jinghao/qwen3.6-27B/optimize/flash_attention/20261015-qwen36-27b-metax-fg20-e2e/commands/fw002r4-launch.py` SHA `930f8044620f42c1f6fb34e5f236b334806a305e99b01143a0dad4dfce8e8f00`
- `/public-flash/jinghao/qwen3.6-27B/optimize/flash_attention/20261015-qwen36-27b-metax-fg20-e2e/commands/fw002r4-source-service.py` SHA `ed0ac21ed6d22c42b1900f51f47dc137ec4560afba3d1dfb7273036e344f995b`
- `/public-flash/jinghao/qwen3.6-27B/optimize/flash_attention/20261015-qwen36-27b-metax-fg20-e2e/commands/fw002r4-model-service.py` SHA `a90f1669d98a26646ecb568386a42e893e08295430479488de6dfed80c189ddc`
- `/public-flash/jinghao/qwen3.6-27B/optimize/flash_attention/20261015-qwen36-27b-metax-fg20-e2e/commands/fw002r4-launch-probe.py` SHA `f97839efdad0991b2a9ba6e82e20c43e493e27e2f16dde4c885c8b8f4aa96c85`
- `/public-flash/jinghao/qwen3.6-27B/optimize/flash_attention/20261015-qwen36-27b-metax-fg20-e2e/commands/fw002r4-cancel-probe.py` SHA `2e11eba2f0eb58f395e223f7ae4d078cdf20afbb60cd7e7c65f4836fbe478b9e`
- `/public-flash/jinghao/qwen3.6-27B/optimize/flash_attention/20261015-qwen36-27b-metax-fg20-e2e/commands/fw002r4-apply-full.py` SHA `f74eb687aa8c4d767b4419101dc1322fd4d1b721b165f1b0c6c04b9e48f898c6`
- `/public-flash/jinghao/qwen3.6-27B/optimize/flash_attention/20261015-qwen36-27b-metax-fg20-e2e/commands/fw002r4-meta-numerical.py` SHA `2f7008ff087a5377ff532e840c6e08698643e2ab791189772a889c54c64b461c`
- `/public-flash/jinghao/qwen3.6-27B/optimize/flash_attention/20261015-qwen36-27b-metax-fg20-e2e/commands/fw002r4-baseline-c8-config.json` SHA `325e6f864b040b6280ccebd77539e7ad0a83a44aee2a3c59ebd28cd8b86460bc`
- `/public-flash/jinghao/qwen3.6-27B/optimize/flash_attention/20261015-qwen36-27b-metax-fg20-e2e/commands/fw002r4-candidate-c8-config.json` SHA `9f4e1c2d4f010b704dc92bccaee89782d4c488fbb8425024d8cdb613cba94043`
- `/public-flash/jinghao/qwen3.6-27B/optimize/flash_attention/20261015-qwen36-27b-metax-fg20-e2e/commands/fw002r4-revert-c8-config.json` SHA `d91d8261c657f88fb31a5c9c49ba5a6946deafbdbac599b4be41303600461251`
- `/public-flash/jinghao/qwen3.6-27B/optimize/flash_attention/20261015-qwen36-27b-metax-fg20-e2e/commands/fw002r4-prefill-plan.json` SHA `4375ddfcc3619b618a017fc5ffdeca96325ceeaba2b23076f544dfb8bac232fe`
- `/public-flash/jinghao/qwen3.6-27B/optimize/flash_attention/20261015-qwen36-27b-metax-fg20-e2e/commands/fw002r4-prefill-comparison.json` SHA `9cd1196b2e1b74e539fa0210311e2d9901416fe6cf01d1b75c508b9f63fc8481`
- `/public-flash/jinghao/qwen3.6-27B/optimize/flash_attention/20261015-qwen36-27b-metax-fg20-e2e/commands/fw002r4-decode-plan.json` SHA `df42552abeecd4904665de303c8f3604d4d65ae0033caf437d58423213bb9088`
- `/public-flash/jinghao/qwen3.6-27B/optimize/flash_attention/20261015-qwen36-27b-metax-fg20-e2e/commands/fw002r4-decode-comparison.json` SHA `324994c9c36fbfd6512cdadc732f93b6dfceb844cadab50e9b6032e24fd16a39`
- `/public-flash/jinghao/qwen3.6-27B/optimize/flash_attention/20261015-qwen36-27b-metax-fg20-e2e/commands/fw002r4-mixed-plan.json` SHA `e6e50f2bd1f98f758d7ae8d4f98939e5cdfd4ab8a19709c7b8aab8f0b6ca27f8`
- `/public-flash/jinghao/qwen3.6-27B/optimize/flash_attention/20261015-qwen36-27b-metax-fg20-e2e/commands/fw002r4-mixed-comparison.json` SHA `c5879725b1cee03ee079f0cbb93c03170a7c66218672bbcf2a1f5319fcca5f85`

执行前微调控制器的只读probe存活检查，容忍检查时恰好退出的NoSuchProcess竞态，不放宽PID出生校验；最终controller SHA `fb004c19b6b894f4a3bcfc34e4b8f67bfe35d7a9c27cd9bc2caff855f5487cb3`（上方未执行草稿SHA由此替代）。全部源/目标名称AST预检通过。

执行前静态收紧：最终使用controller-v2/launch-v2与input-shas-v2，额外冻结standalone probe、两组原件/候选、原生runner和父capture证据SHA，probe启动后再次对照已冻结workerSHA。此前v1控制文件仅预备、从未启动或发请求；不覆盖旧文件。最终controller SHA `7b8187149d1d9b8afcd66b4483a3962068a489d2032d0d64a71729fec5704218`，launcher SHA `17f33da8be692aff8862214920431f817660c31295801fa360f093310b14e0ad`。

## 已完成的算子门禁与模型接入

Full proof `results/op003-full-numerical-micro.json` SHA `4dd1b675e367b588062c502cb8132a228ec48347d6a5ba18bb69e62c91471e1d`；187整数逐位等+7fallback=194用例通过，默认dtype及6次溢出尝试符合预期，8graphs×2覆盖写坏输出后的replay通过。原模型数值容差不变。fullprobe receipt SHA238bd0ba...，无模型请求。

| 算子范围 | baseline | candidate | revert/边界 |
|---|---:|---:|---|
| 6个新N首次FGfull完整调用 | 1.391–1.403秒 | 0.110–0.167毫秒 | 降低至少99.988%；双方预编译等价类型/对齐签名，N调优key全新 |
| N2048缓存调用 | 40.090µs | 31.037µs | revert39.968µs |
| N2074缓存调用 | 39.318µs | 30.634µs | revert39.833µs |
| N2080缓存调用 | 40.515µs | 31.203µs | revert40.446µs |
| N4096缓存调用 | 39.622µs | 30.409µs | revert39.631µs |

缓存命中下降22.09–23.25%，通过预冻结“不退化>5%”门槛；五组交错/每组50完整函数调用全部保留。微测含分配/Python/kernel launch/摊销末尾同步，未包含上层Torch dispatcher；不是模型吞吐增量。微测B/R漂移-0.304%到+1.311%如实保留，微测未设原生E2E的1%判据；后续原生模型B/R<=1%依旧严格检查。

仅C私有full文件已安装SHA410fad...、整仓FGa5184db5...。为避免沿用旧FG数值证据，metadata14prefix+5真实nativeFA已重跑：`results/fw002r4-meta-numerical.json` SHA `5827be49644185da537dfb1d4c422fc3339c5327c512973318d5b9890dcf0a01`，全5FA输出逐位相同/maxerror0，prefix整数及地址复用快照通过。

实际新基线实例288787/create1792124252.15已集成：两rank各36个FG full_kernel、0 full_kernel_scale、32次graphreplay，精确WY/GDNpacked/原nativeattention路径检查及10docC8/20filter rows通过。模型steady Mixed尚在等待三phase顺序测量，不能现在宣布整轮基线稳定或E2E改善。后续B/C/R的FGa518恒定，仅Plugin98f36→bbc4→98f36；结果只归因metadata差异。


模型稳态检查更新（2026-10-16 05:13 UTC）：共同采用本修复的新baseline Mixed完成8暖3测，末3暖吞吐spread0.3011%、3测spread0.1794%，所有轮128成功/0失败，median700.4087 tok/s。recordSHA8f9998dc783255442520c6ef4aa6d8fab64a108f26a2ffcbd85be5cfed21a2d2；该记录的所有原始结果/校验/plan/client/contract SHA已复核。这是本轮稳定性证据，旧未通过准入的暖轮不用于计算full修复端到端收益。共同full前提下的metadata候选/回退对照仍运行，原服务尚未部署本修复。
