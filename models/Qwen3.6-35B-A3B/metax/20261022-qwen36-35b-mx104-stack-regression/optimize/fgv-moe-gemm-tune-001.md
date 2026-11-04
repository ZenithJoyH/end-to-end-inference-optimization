# FGV MoE GEMM1 / GEMM2配置调优

**当前状态：apply-004已按用户要求写入私有FGV算子源码，新进程实际选参验证通过；现有服务未重启，新参数在运行服务中的命中尚未验证。**

用户2026-10-26明确要求：以`/public-flash/jinghao/qwen3.6-35B/test/perf_test/benchmark_results/qwen36-35b`当前端到端性能为观察，寻找当前FlagGems-vllm GEMM1/2更好的配置。延续本案例独立B，保留已有MoE接入和PR638；不修改vLLM、模型或采样实现，不提交推送。

## 执行前记录

实验`fgv-moe-gemm-tune-001`，operator/improve/config。先纯CPU/只读取证，随后有限真实shape算子搜索；初始目标P1K/D1K/C64/N128，Prefill大M守护。性能Skill若测端到端调用targeted，算子微测不冒充端到端Skill正式结果。精度Skill后续minimal-regression。

当前手工B服务PID2431243/start1131804515，物理GPU4/5、TP2、served qwen36-35b、port18135、seed0，已区别于历史r39 GPU0/1/seed42；历史gate不重绑。原用户GPU0/1范围不能默认为扩到4/5；当前先准备可审阅有限计划，不停止服务或共卡搜索。

当前FGV source c575c8a798232cd86e18e1239d2a314cd0e3afe21faf5951c45798c84f706679，Plugin MoE utils b03c3c3d880c9ef7f1e0c0f2639d8ef9ecbdadb4400bd6dada2e2478c027479c。真实每rank w1(256,512,2048)/w2(256,2048,256)、BF16/topk8。GEMM2原生日志M65536对应selector tokenM8192乘topk8，不把这两个M混用。两个GEMM复用sorted-token alignment，初始搜索固定原BM，只变BN/BK/warps/stages；PAIR/SWAP/激活/归约保持。

用户CSV五项均保留三轮。原客户端RUNS3/SKIP_FIRST1预设存在，但没有新正式契约要求的准入/原生JSON/SHA与独立服务对照，故只作为用户观察，不事后把慢轮删除或借SUMMARY宣布新收益。Prefill视图TTFT、Decode视图TPOT/ITL为客户端代理，Mixed为完整批次吞吐，阶段实际设备占比未知。

CPU审计命令：`commands/fgv-moe-gemm-readonly-audit-001.py` SHA `0a8cdeab922a25a6cf0072f98b781ce19055924f5d8846cf1b90da448514284f`。只执行一次，写独立`operator/fgv-moe-gemm-tune-001`，0GPU/模型/服务操作；冻结实际selector AST和有限搜索矩阵。

## 有限真实硬件搜索前冻结

资源授权：用户明确回复“允许使用当前 GPU4/5，测试后恢复服务”。覆盖原GPU范围，其他任务/卡不动。CPU audit报告SHA`6bc4dc11b2daefe5eacc51278c44e47898669089e7b56e8077304b21a290c1e0`；search-plan SHA`510e4279390cfaeaa7973d705458aaf0d82ae249838a32912b8a46812008ef9d`，53组固定BM/PAIR/SWAP的参数。

首次SSH归档-c引号失败、随后的未归档入口查无文件，均未写产物/执行GPU或服务操作；随后完整stdin上传SHA成功，CPU audit只执行一次exit0。不是模型失败或GPU重跑。原FGV源码中embedded路径不存在，实际选择default，原VLLM配置目录不消费。

执行前原服务空闲3次观察；API PID2431243/start1131804515、engine2435207/start1131808260、rank2435689/2435690/start1131811059精确保护。SIGTERM仅原API，等待全部旧家族退出与4/5空卡；不宽泛kill。GPU客户端仅4，2400秒预算，无真实模型请求。完整原环境只保存在controller内存和恢复stdin，不落完整env；新日志独立。finally先确认GPU客户端退出和4/5空卡，再原argv/env/cwd恢复，核验新PID和精确环境相等/readiness/源码无变，不偷绑旧gate。

- `commands/fgv-moe-gemm-sweep-001.py` SHA`d4709eb5cced0a497e4a94780ded00ccc6bbf4f86443d07100f0c5c5a36e485a`。
- `commands/run-fgv-moe-gemm-sweep-001.py` SHA`750ba7573f998091f58dff2da869b952393f844aed0b55d57c24b45be6bd26b0`。

单次controller已启动：PID2785904/start1133440321，execution-plan SHA`a12792888de74e3de4fe9f7805b8c3e93e6b19421ac4a7050a441c1dd00f9a9b`，command SHA`e76547a2c323a27375ac26e80404f7cb6689d21d14cec24a1715e329ef4227d7`。精确排空/原API家族退出及4/5空卡通过，GPU4独立客户端namespace PID393069/start1133443559，仅一次有限53组。首个M64/G1原配置独立FP32参考和变化输入graph通过，尚无完整配置结论；不重放此controller/旧输出。

53组GPU全部完成/0数值失败，原controller GPUexit0，但finally恢复辅助代码的全局LOG替换误改XML_CATALOG_FILES产生SyntaxError，原恢复0启动。错误保留，不重放GPU。新唯一commands/fgv-moe-gemm-restore-only-002.py SHA 09da9f75c8d12e846c3dad5085ca24c4fbde31215c84c311599e791521a8710d 仅恢复：精确逆转该单处替换，原环境SHA必须等于stop前SHA；用结构化base64 JSON传参并compile-before-exec。0新GPU/模型，原argv/env/cwd恢复并记录新身份。原大错误含完整非敏感shell env，后续不再回显，只记录指纹及过滤字段。

原服务已单独恢复通过，report SHA12b0f48e620bdac5e3c97704518e6454c7786b6c107cd9e7276a033efaf17e36，API2793137/start1133472155。全部53通过，GPU report SHA755dc3718ac94b670e820b0a9d6f88bedc047f13159120757470dbe19db87731。后续新进程确认阶段前3各一次共12对，外加14完整MoE BF16/FP16边界和路由哨兵；seed20261027。变化只限BF16目标权重shape的M64/8192两点，纯CPU全M0..32768证明其余原选参和BM一致。无任何生产源码写入，无新增E2E/正式gate。远端workflow.md已读，optimization.md缺失；此阶段仅配置微测，不新写算子/kernel或调整全平台入口。
- fgv-moe-gemm-validation-002.py SHA be5e5ad22ef31d84f3c75bf2fcbd9a0aa59591d205d824e394add717c4523135
- run-fgv-moe-gemm-validation-002.py SHA d9e1b9976c70a3031b4f1691c62e8404fdab3a8bdb7d7a7562206ba8b78162f3
- validation-002-plan.json SHA 7b5fec71510c6de63ed3555434c48f74a7d5902b356dcb7cc9cf37db8baf63f7

26项独立新进程确认和完整MoE全部完成，controller002 finally恢复成功。唯一零GPU最终核验/候选归档入口commands/verify-and-stage-fgv-moe-gemm-003.py SHA 5a6db4ebdfccb53eda15b9f9b656cd5f53116e7fdc01326d3ab7c5b19608ba28。核对53+12+14原生行/时延中位数/SHA/restore身份；生成尚未应用的单函数四标量配置差异，CPU重放M0..32768及非目标shape/dtype证明与GPU进程内已测selector完全同字典，其他路径不变。仅产物目录写补丁，不修改实际库、启动脚本或旧gate。正式GPQA和模型端到端候选复测not_run。

独立最终核验exit0，report SHA f7b74a0c01ba3999b795e2d80df0d20048dc31ef8c41722d3d927b3458321eee。推荐候选源码SHA49f3a5040afef93bda7e71c43ca31fbd0f68fc15497235ecec4aa0283d9eee49，未应用patch SHA480294a0b30ae291265114ede6374df0c20684c2b3a92f73a7166c3c54381536，recommended JSON SHA79788f8a5c16209f178762bfef3e53269798b1f551a5907b4c848cc163fbc39b。最后恢复API2813245/start1133529044，原argv/env/cwd和source完全一致。唯一只读/状态收尾commands/fgv-moe-gemm-closeout-003.py SHA 5297fe1ea310de7efb0a2510254601bdcab1c7cec9fb043ad3f2832f21bdd51e；仅CAS写continuation并保存版本/结论，无GPU/模型/源码改动。未创建新monitor。

## 已完成结果与适用边界

53组初筛全部通过，独立进程12项前3复核与14项完整MoE/路由/边界/FP16哨兵全部通过。FP32专家参考沿用原rtol0.1/atol至少0.01，未放宽；原输入/变更输入graph均校验。纯CPU65688次选择器比较证明新补丁与已测进程内选择器同字典，仅BF16/E256/H2048/I256/topk8/M64或8192变化，BM/SWAP/pipeline/激活/归约原样。

| tokens | stage | BM/BN/BK | warps/stages | 独立基线ms | 候选ms | 加速比 |
|---:|---|---|---|---:|---:|---:|
|64|gemm1|16/64/64|4/2|0.437414|0.324032|1.350x|
|64|gemm2|16/64/64|4/2|0.178304|0.166259|1.072x|
|8192|gemm1|128/128/64|8/2|6.347072|1.806029|3.514x|
|8192|gemm2|128/128/64|4/1|1.169818|1.038106|1.127x|

所有GROUP_SIZE_M=1。G2/M64保留SWAP_AB=True；G2/M8192保留pipeline=basic/pipeline_load_num=-1；PAIR=false/归约时机和其他参数保持源实现。

| M | 路由 | 完整MoE原ms | 新ms | 加速比 |
|---:|---|---:|---:|---:|
|64|uniform|0.611008|0.484966|1.260x|
|8192|uniform|7.821632|2.984435|2.621x|
|64|concentrated|0.135219|0.125926|1.074x|
|8192|concentrated|2.356314|2.004352|1.176x|

其他14项矩阵中的相邻/小M及FP16配置均未改变，测得延迟改善约-1.04%到+0.43%，没有超过预声明3%回退守护；目标阶段各5样本计时spread均<1%。均匀与集中合成路由的收益差异证明路由分布是重要边界，不能把2.62x外推整模型。

## 决定、风险与回退

结论为已找到并验证的算子候选，production status=not_applied。候选只改get_default_config里的四处标量选择，源patch未应用；当前服务仍加载c575原FGV和b03 MoE接入/PR638。已按原启动参数、完整环境SHA、工作目录在GPU4/5恢复，API2813245/start1133529044，18135/qwen36-35b就绪。无活动job，无新monitor，未操作其他GPU/容器，未修改启动脚本，0模型请求/0新正式GPQA/0模型E2E复测。

本轮任务的配置搜索完成。未来若集成候选，须独立证明新服务实际命中和最小回归，再用同契约、预冻结稳态规则做模型Mixed对照；最终生产/正式性能晋级还需适用的正式精度gate，不复用旧r39。原性能CSV/旧精度事实及本轮恢复失败证据完整保留。

## 知识差量

refined：从Plugin分步入口切完整FGV API后，应重新追踪真实selector，不能认为VLLM_TUNED_CONFIG_FOLDER继续控制GEMM；原生G2日志的M是routed rows(原tokens×topk)，不是selector tokens。固定共享BM先独立调阶段几何，再用包含align/silu/sum的完整MoE及集中路由复核，能排除将孤立GEMM收益直接相加的错误。本例仅限C550/BF16/当前库字节和两个M；E2E/真实模型路由分布及其他模型/芯片未知。

收尾已通过：closeout SHA4c17b26e7c18c9e03763817d7d7b4d0714e76a18315f7a3e4bf5aaf541e682e4，continuation SHA27c035553df2880195b51126af439793b77f22b36958f7baf47d22c229c962b6/current_job=null；版本Torch2.8.0+metax3.7.0.7、FlagTree/Triton3.6.0、MACA3.7.1.5/driver3.8.1。两次恢复均最终成功，生产源码仍c575，补丁未应用，无后台评测/monitor。

## 外部产物与本地检查

远端根为/public-flash/jinghao/qwen3.6-35B/20261022-qwen36-35b-mx104-stack-regression/operator/fgv-moe-gemm-tune-001：

- gpu-sweep.json：53组原生完整输出。
- validation-002/gpu-sweep.json：12独立阶段复核+14完整MoE/graph。
- independent-final-003.json：零新GPU最终逐行/计时/SHA/恢复身份核验。
- candidate-003/recommended-configs.json：完整GEMM配置字典及原/新时延（此JSON不是运行时配置加载入口）。
- candidate-003/fgv-moe-gemm-configs.patch：单函数、四标量限域候选补丁，尚未应用。
- validation-002/restoration.json与closeout-003.json：原服务参数/环境/源码恢复以及终态证明。

本案例三state唯一键/schema4一致、实验ID/文档/README链接检查通过。全仓record checker另报372项工作区其他既有/并发案例与过程材料问题，本案例0项；不修改无关模型去消除这些报告。未运行与本次记录/参数候选无关的全仓测试。

## 用户要求写入当前容器（2026-10-26，apply-004执行前）

授权：用户明确要求直接写入容器FlagGems-vllm对应算子代码。本次只写当前B私有安装源文件，不自动停止/重启服务，不发送模型请求或重跑旧53/26矩阵。当前source仍c575、服务API2813245/start1133529044、continuation current_job=null；/opt不在共享挂载中。

| 项目事实 | 本次限定 |
|---|---|
| API/可写 | 已有MetaX fused_experts_impl使用的get_default_config；只修改对应fused_moe.py |
| 只读/构建 | vLLM、Plugin、Gems、FGV kernel/其余文件、旧验证入口全部保留；editable Python无需编译安装 |
| 数值/benchmark | 沿用已完成53+12+14硬件证据，最终字节做AST等价和新进程实际import/selector检查；不重放旧GPU |
| active set | BF16/E256/H2048/I256/topk8，仅tokens64/8192；config BM及非目标dtype/shape保持 |
| autotune/profiler | 复用现有MetaX内联配置函数；不新建kernel/NVIDIA路径，NV libtuner不适用；不采新profile |
| 超时与落盘 | CPU检查预算120秒；原字节/完整受保护源码SHA/新文件/唯一命令在远端案例归档；原子替换 |

| 语义契约 | 边界 |
|---|---|
| 输入/输出 | 原API/连续BF16目标权重形状、TP2有效每rank维度；不改签名/alias/输出shape或dtype |
| 累加/融合 | 原FP32累加、SiLU融合、路由权重时机、归约和SWAP/pipeline保持；仅tile/warps选择 |
| 非目标 | FP16/FP32/量化/其他专家形状及其他M走原配置；没有新增torch compute fallback |
| 未新测 | 本次不新测NaN/Inf/训练/模型端到端/GPQA；沿用原支持范围，不扩张声明 |

| 路径 | 实现与验证 |
|---|---|
| 命中BF16目标两个M | get_default_config四标量调整；与已测候选全域字典相等 |
| 其余路径 | 原函数其余AST及所有kernel不变；共享BM/非目标dtype与shape CPU验证 |
| 运行实例 | 正在运行的Python worker不会因写文件自动热重载；本次保留实例，重启后加载新配置，旧gate不重绑 |

当前这条路径保留embedded YAML loader，但实际路径不存在/未命中，故走同文件get_default_config；原VLLM_TUNED_CONFIG_FOLDER不消费于此FGV路径，不能扩展为所有vendor/算子都无外部配置。FGV HEAD e1a02b6b2e47abea9a6cfeaaf3431f50f7f476f8，Plugin release/0.2@7cb559947，vLLM bc150f5只读干净；FGV原MoE/GDN以及Plugin本地改动保留。Gems私有源码没有.git，版本不伪造，靠内容指纹保护。

apply-004执行前：commands/apply-fgv-moe-gemm-configs-004.py SHA 242ee734c87c684eaf67465375a01472fcc463c93773890bec4ac8bbec5ed1a7；最终候选仅去多余空行和调整注释，AST与已验证49f3完全相同，最终SHA c4673aea289a2ad815ca20a01046c014add163756846675556027781a8aa7c73。先归档最终文件和原始备份、所有四包私有源SHA，再原子写入；新进程真实import/4组最终selector检查，前后仅此文件变化，原服务PID/start不变。失败只在目标仍为本次新SHA时恢复原备份，不覆盖并发用户修改。

### apply-004已完成

仅B容器/opt/FlagGems-vllm/src/flaggems_vllm/runtime/backend/_metax/fused/fused_moe.py由c575更新为c4673aea289a2ad815ca20a01046c014add163756846675556027781a8aa7c73。最终文件与已验证49f3候选AST相同，仅注释/空行整理。新进程实际导入该私有文件，try_get_optimal_moe_config四组最终字典均与已测候选逐项相同、embedded_table=false。跨四包本次5730份py/yaml/json保护快照前后仅这一文件变化，原0644/root权限保留，原字节备份于apply-004/fused_moe.before.py。

application.json SHA9197dcc25593ea13cb196fe2bf995bbade7c222d5f0fca1795fd2034baf23b7b；command SHA35ed881cf824bb48a29b67b6f14da8d6d3b101758a2672122ecb83ee04193ed4；continuation SHA1bc158f17a617080be9bf07971e6501fd8b71e4d8adab2aedc619dc43ab8b4b6。原API2813245/start1133529044保持，没有重启、模型请求或旧GPU矩阵重放。旧运行实例没有热重载，后续重启后才能使用磁盘新配置；未新签gate或宣称模型精度/端到端收益。前面的“未应用”段落是调参/归档阶段历史事实，已被本次明确写入指令与回执更新。


## 当前组合 sampler-shortlist-C64 正式回归补充

保留本实验原有结果与范围。当前组合（FGV guarded shortlist49e9、既有MoE/GDN调优、FlagTree fe1d24f6、Gems a456）在新独立回答缓存的一次原生rolling C64/fullGPQA198中得分158/198=79.7979798%，通过流量前冻结的用户NV77.53%阈值；198唯一doc/396filter行、旧160/147/161/154离线复算、当前同c2/source/manifest已独立通过。新gate SHA13b72e7e2035e0fd28e44f2c1c809e7532c109759978a7a6f83e1e85fc450deb，独立report SHAab644f95c7160ad791e74d844b67aa6cad23aefbd7aef6d6360ef5eb337dc46d；远端operator/sampler-shortlist-001/formal-c64-002/independent-verification-001。该分数证明当前组合，不声称本实验孤立精度收益，也不改历史C32/旧160绝对参考；完整四场景正式性能未运行。完整记录见[sampler-shortlist-001.md](sampler-shortlist-001.md)。


## 2026-10-28 当前 opt3 组合精度复测

用户重启后的当前组合、实际prefix-on/GPU4/5/TP2，原生GPQA198/滚动C64独立通过**161/198=81.3131% >= 77.53%**。198唯一doc/396filter行/原prompt-target-args/无旧回答缓存/前后fresh源码一致，旧160/147/161/154逐题重现。验证：`/public-flash/jinghao/qwen3.6-35B/20261022-qwen36-35b-mx104-stack-regression/accuracy/user-gpqa-erqa-c64-20261028-001/gpqa-followup-001/independent-verification-001/verification.json` SHA c9437b838bd089152dc01a11c3f32076e89941334e545a89b8f175606366ebb9。此为保留组合精度，不证明本点独立贡献，不与旧prefix-off不同配置计算收益。随后官方ERQA多模态C64发生FGV MoE临时cache13申请256MiB OOM，服务退出；GPQA已测通过分数仍有效，旧实例gate不可直接用于新实例/新参数。ERQA部分证据保留、完整400分数缺失，不自动恢复/补跑/性能。详见[user-gpqa-erqa-c64-20261028-001.md](user-gpqa-erqa-c64-20261028-001.md)。
