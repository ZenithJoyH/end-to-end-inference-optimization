# op-002 MetaX MoE Decode 流水线 stage 配置

当前结论（2026-10-14）：按用户要求保留的 GEMM2 调优已在独立容器磁盘改为 JSON 加载，硬编码分支移除；运行中的 qwen3vl-opt2 未重启，新的加载方式等待用户重启。159,840 组 CPU 配置等价性通过，五个 Triton JIT 函数不变；新文件身份的硬件 graph/端到端复测未运行。源 qwen-vl 和其他私有仓库内容审计未改。既有六进程 P1K 观察吞吐1755.01→1900.66 token/s（+8.30%），比较仍 incomplete：B03 尾延迟波动超限，正式精度未评测；不宣称正式验收通过。

设计归属 operator/improve：只调 FlagGems-vllm `_metax/ops/fused_moe.py` 的既有配置边界，不改 Plugin apply、vLLM、实现选择、黑名单、采样或精度。首轮在独立进程临时替换配置函数，生产源码暂不写入。实际公共 fused_experts_impl 是该 MetaX 自有 Triton 后端；E128/H2048/本地I384/top8/BF16，w1=[128,768,2048]，w2=[128,2048,384]，C550/warp64/shared64KiB/104SM，版本及镜像沿用op001清单。

三阶段 trace 两rank有效、MoE correlation 全部映射。rank0 pure-new Prefill MoE活动212.22ms/总设备活动381.08ms；Decode full graph 1067.44ms/1653.04ms；P1K/D8 Mixed new+cached为1675.93ms/3025.19ms。约55.7%/64.6%/55.4%，均为可能重叠的累计活动比例，不是critical path或收益上限。两rank MoE相近，通信等待存在不对称；host/client初始单请求已剔除，cached中partial-prefill歧义保留。

Decode M64每步48层×2 GEMM，GEMM1 grid912、GEMM2 grid4864，各256threads、40KiB shared；register176/132，kernel均值186.56/166.43us。GPU记录估计occupancy13%，与shared限制每SM一个CTA一致。既有3-stage配置以较大暂存换流水线，减少stage可能容纳更多CTA；带宽/寄存器仍可能限制收益，必须完整算子实测。

M64的有效计算约2.42GFLOPs；均匀top8预计激活约126/128 experts，权重约576MiB，理想最少权重读对应约4FLOP/byte。BM16将每expert平均4路由行填充，实际计算/权重重读比有效模型更大，不能把估算流量当作硬件计数。cache13约2MiB、cache2约384KiB，其他副本/align/归约计入完整transaction。M8192有更高密度、trace GEMM1约2.98ms/GEMM2约1.41ms；该分支本轮保持。

首个证伪实验：只扫描GEMM1/2 num_stages各1/2/3共9组合；保持BM16/BN64/BK128、GROUP1、warps4、对齐padding与原SiLU/归约数学。图计时每组合5次warmup、200次graph warmup、3块×200replays，种子20261013/20261014，均匀与集中路由，固定600s预算。原FG完整调用及CPU FP64是oracle，atol0.002/rtol0.02/NRMSE≤0.015，stage-only结果还检查逐位相等，变化输入/路由两次replay。至少5%完整算子改善，其他M8/16/32/48/64退化不超3%，baseline前后drift≤5%才晋级；所有原始结果保留，失败候选不回退成别的实现来测速度。

候选作用域拟限制C550/BF16/E128/H2048/I384/top8/M8..64、非量化；其他M/形状/dtype/platform沿原路径。知识库GLM/PPU参数不迁移，只复用按live M/stage和padding做对照的方法。Plugin/NVIDIA/LoRA入口不变。graph服务及原固定十问回归、无profiler同配置Prefill/Decode/Mixed与parentP1K A/B/R尚待执行；正式GPQA阈值等待用户，无正式gate或收益声明。

状态micro-prototype-running，pr_readiness=experimental。产物根 /public-flash/jinghao/qwen3-VL/20261013-qwen3vl-metax-flaggems-e2e-opt1。

执行前将graph预热固定为200replays以减少时钟/加载暂态；尚未读取任何测速结果。源码只在benchmark进程内临时改变num_stages，函数结束恢复原配置引用，独立18430服务仅在idle期间驻留，不发送模型流量；本轮没有生产源码补丁。

首轮micro在首组结果前等待（CPU线程futex、GPU0空闲），没有形成数值/性能结果。内部600s预算无法打断阻塞调用，784.08s时精确SIGTERM仅PID33221；源码/模型服务未修改，原日志与stop回执保留。gdb/py-spy不存在。v2同契约增加逐步日志、90s faulthandler与host侧600s watchdog，定位等待而非切换实现。

## 完整算子结果

faulthandler定位等待在torch.cuda.Stream创建（首个graph，stage候选尚未执行）。仅停止独立18430/API21501及其关联worker释放0/1后，同一v2进程恢复，411.05s内完整完成；这是资源共存相关观察，不直接断言驱动OOM根因。后续micro使用独占空卡。40项扫描均通过，选择GEMM1/2 stages=[3,1]，最小扫描加速1.15281×；无需修改GEMM1。CPU FP64最大NRMSE0.002896、最大绝对误差0.0004904；候选与原FG逐位一致、变化输入和路由的两次graph replay通过。

M8/16/32/48/64、均匀及集中路由共10项均无退化，加速1.13039–1.21997×，A→R漂移最大0.073%。M64均匀完整MoE 0.534303→0.464124ms（1.15121×），集中0.193943→0.158973ms（1.21997×）。包含align/activation/GEMMs/reduction/graph dispatch；不代表模型端到端收益。原源码SHA56f01e6cba00f4c9db2091edfce17c9760efce5a46695bf1a74e5384a2a49f04保持，只有独立测试进程内配置替换且已恢复/退出。完整结果results/op002-stage-scan-v2.json，SHA6efc541f530e1eb40862fd1e433e4a7ac193df6bc16b1d6d38362da1b5cbc411。

现在重新启动原FG模型baseline03（同snapshot/挂载/0,1/18430/原graph参数/黑名单），先做P1024/D1024/C64/N128无profiler比较基线，再写仅GEMM2stage1的private库候选。正式阈值仍pending，未签发精度或正式性能gate。

候选diff仅MetaX backend半精度配置中11行，限制dtype=bf16、block_shape=None、stage=gemm2、(E,N,K,topk)=(128,2048,384,8)、8≤M≤64、device=MetaX_C550；只覆写num_stages=1，其余field一致。静态/mocked配置1008组合passed，6正例改变单字段、1002反例保持，不代表非目标硬件实测。补丁和before/after原件已存patches/，after SHA4bac1ee1100fcaeb28f9204715e32fcbcd6807c1da4bf128c8f9d69735ead7f1，尚未写production。baseline03 graph/C8通过、两worker声明M64 G2stage3、图/导入/apply观察均撤销；P1K plan-v2五预热+三测量执行中。

## 模型基线与最终实现验证

baseline03完整P1K/D1K/C64/N128五轮预热通过（末三轮spread3.535%），三轮稳态输出1761.87/1838.39/1701.52 token/s，全部保留。原生run-record complete且无error，SHA02196204bebc4a63a3606aed9054c259c43ee50a13d998721766052f6a27364e；当前仅一个独立进程，不能提前通过两进程比较契约。随后精确停止该own服务，SHA/私有非挂载路径门禁通过，11行候选仅写独立clone，git diff --check通过、源qwen-vl未动。最终实际源文件再跑10项硬件完整FG回归：M8/64×strided/bias/router-input/EP-map/inplace，各两次变化输入graph replay、输出逐位同原FG，全部passed。candidate01以同样args、设备、bounded observer路径重新启动，FG选择/blacklist/采样不变；模型候选C8、P1K测量与回退尚待完成。

候选API50402、worker50891/50892启动/capture与16次replay通过，实际M64配置G2stage1，取证恢复。固定十问/C8请求完全相同，10/10非空且均256token截断；6段逐字同baseline、4段不同，仅最小回归观察、不作为正式precision通过/失败。model/tokenizer、engine/Plugin/FlagGems、全部launch_config相同，FG-vllm仅目标文件变化，完整内容指纹efdf2e...→a3a271684679628c7574eb0040a9fe8988141ffdc99b516d973849af66a3ba73。当前candidate01同P1K plan-v2/source role=candidate执行中，尚无端到端提升结论。

## 初组模型 A/B（尚待R与独立重复）

两侧同P1024/D1024/C64/N128、五预热+三测量，各complete、全部准入轮保留。baseline输出1761.872/1838.387/1701.517、均值1767.259 token/s；candidate1891.457/1984.041/1872.097、均值1915.865 token/s（+8.409%）。平均TPOT34.5049→31.7284ms（-8.047%），P99 TTFT3640.489→3597.736ms（-1.174%）、P99 TPOT36.1900→33.1709ms（-8.342%）、P99 ITL36.0237→33.4718ms（-7.083%）。scope=diagnostic/performance_only，当前一独立进程/role，缺回退漂移与第二进程，不能通过冻结比较契约或宣称正式P1K/四场景验收。candidate run SHA6af381bcffd3be76bfbdc2e0274da6d4f1fc6e3e82802f4717d6057d6cdbbfcc。性能测量结束后开始相同三阶段reprofile，计时不并入A/B。

## planning-op002-firstAB-20261014

当前组合只有op002一项私有候选，P1K初组+8.409%为同配置模型测量，不与算子1.15×相加；尚缺回退、两独立进程/role与正式GPQA gate，复盘状态incomplete。先完成candidate reprofile（verify actual stage1 geometry）→同FG原路径revert01→独立baseline04/candidate02/revert02，按既定吞吐/延迟/漂移阈值决定保留。之后需用户冻结GPQA阈值、补fullweights身份，正式198题及P1K单场景formal才能推进P4K/P16K/P32K。下一算子仅候选大M8192 G1tile/stage/warp完整transaction，预期E2E未知；若完整算子不到5%、数值/graph或parentMixed守护失败就停。暂不叠加新代码，不新增blacklist/native选择，不修改vLLM。失败warmup、取证回调与stream等待均保留，当前版本对照未关闭任何FG选择。下一复盘在R/独立重复完成或热点迁移时触发。

相同三阶段candidate reprofile两rankpassed、所有MoE correlation映射。M64 actual G2 grid4864/block256保持，shared40960→20480 bytes、register132→64、均值166.425→109.855us；G1 grid912/shared40960/register176保持，均值186.563→186.289us。大量Prefill/Mixed kernel未改变。Decode MoE累计活动减少、仍为首热点，说明实际graph进入新stage1；这些profiler数字仅归因，不加入8.409%无profiler收益。native report results/profiling-candidate01/.../diagnostic-88d7b6c481f74041adee33daa934ed12/diagnostic.json，分析results/candidate01-phase-profile-analysis.json。然后精确停止C1，仅private文件恢复原56f01...SHA，revert01同参数启动中。

首组revert01 complete，三轮1770.887/1823.740/1727.984，均值1774.204 token/s，较B1漂移+0.393%，全部保留。下一步按原冻结契约启用fresh baseline04/candidate02/revert02；控制脚本执行前归档，任一检查失败停止后续切换，不修改源qwen-vl。

正式精度准备：新CPU evaluator用规定镜像引用创建且实际ID同已验证62dac...，原digest-created sanity容器保留。真实gpqa_diamond_generative_cot注册路径/app/lm_eval/tasks/gpqa/generative_cot；两次provenance完全一致，raw/eval各198题、dataset revision content-sha256:167548b01bcfd7d38d0eb80bb01bd1e6dded4d3aa14b41a4bdba0beb5423dadc。零模型请求；阈值仍pending、没有正式运行/分数/gate。

## planning-op002-spread-audit-20261014

首组逐轮audit发现B03 P99TPOT35.9993/34.3307/38.2401ms，relative spread10.8597%超过冻结10%，其余主指标/守护及C1/R1轮间波动均在阈值内。既有比较应incomplete，不能用均值改善或追加进程清除这个既有违规。保留全部轮次，不放宽门槛，不回写源服务；完成已经启动的B04/C02/R02以确认候选重复性及seed/role模式。完成后再复盘噪声来源与后续前瞻契约，尚无candidate晋级或正式gate。

同请求十问文本对照：C1 vs B03为6同/4异；原实现R1 vs B03也6同/4异；原实现独立B04 vs B03为3同/7异。逐项请求完全相同。原stage3重复也存在文本差异，不能仅凭不同文本归因stage1或判定正式精度；不据此推定具体批处理/数值根因，仍需完整评分与阈值。

第二个基线B04 complete：三轮1748.149/1829.166/1743.525，均值1773.613 token/s，P99 TPOT波动6.110%。控制脚本切C02前退出1，源文件仍为56f01、后续只读前置检查passed；首次包装器没有输出stderr，无法断言具体原因。恢复控制额外等待ownAPI彻底退出并保存stderr，唯一retry1产物，基线数据未重跑/覆盖，C02正常启动/C8/capture/replay后进入同一计划测量。

比较工具发现api_pid/runtime_evidence_files误计入稳定身份；公共compare_performance修正仅这两个瞬态字段，check_run同时逐项SHA重验runtime取证文件，不忽略其他未声明字段。31项针对性测试与项目207项测试passed（3skip），完整--code检查passed。远端旧比较器、冻结manifest/contract/run记录保留，新副本compare_performance_v2.py。B03/C01/R01/B04/C02稳定身份核验passed，跨角色唯一变量/flaggems_vllm_sha256；这个工具修复不消除B03尾延迟波动超限。

C02 complete：三轮1909.857/1991.364/1867.536、均值1922.919 token/s，对B04均值1773.613改善8.419%；平均TPOT31.6246ms、P99TPOT均值32.9017ms、其轮间波动6.976%。第二次候选性能方向一致，尚待R02和全六进程比较。R02源文件恢复56f01，同计划启动；本轮补强的API退出等待约25s后切换成功。全局比较仍保留B03波动超限，不提前签发passed。

## planning-op002-six-process-20261014

六进程完整report results/op002-p1k-comparison-v3.json，SHA8fb5edc1088c7aa5f1fcfc2d1074030588d281cb1c0bfee37951bc64ca563379。B/C/R吞吐1755.011/1900.657/1763.696，观察改善8.299%，回退漂移0.495%；P99TTFT3628.921/3600.043/3601.203、P99TPOT36.0295/33.3532/35.9503、P99ITL36.4071/33.8694/36.4614ms。唯一统计issue为B03 P99TPOT轮间10.8597%超冻结10%。保留全部轮次、不改契约，结论incomplete，候选不晋级/不部署；不以两次均值+8.4%覆盖该证据缺口。

取证元数据比较修复后的首控制脚本复用旧日志basename，安全FileExistsError；新唯一v3路径生成完整报告。初finalizer已完成关停/源码/权重，但末回执读缺失v2路径失败；op002-finalization-recovered.json绑定实际v3、原始失败和旧报告不覆盖。source-audit passed（SHA f8c60804636f96f97c25f045fb801b7bbf409cbbeb895abfb383884c02715006），qwen-vl与private clone的vLLM/Plugin/FG/FGvv全部等于初始指纹，8000 served qwen3vl-opt1；18430 API退出、端口释放、GPU0/1均idle860MiB。

全13个权重分片62,141,618,016bytes及config/generation/index逐文件SHA完成（测量结束后nice19读取57.22s），model身份8c9fd334f4a308f9311906c6005cf2bbb25a6fd17da056e6d4a167eec3f139f6，manifest SHA6db4b16c1d50b055c610e4d55a75c6d5174539aa6970593bfc0398272a3d7996；旧诊断manifest不改写。GPQA raw/eval198题来源准备完成，但threshold仍null、正式未运行。下一步先前瞻性稳定性恢复设计和阈值/gate；未关闭P1K，P4K/P16K/P32K尚未形成新可比验收。当前只有归档op002候选，不能累加局部1.15×当累计E2E收益；大M8192 G1优化继续deferred，vLLM/Plugin与所有FG选择不变。

本地代码验证--code通过（207 tests/3skip、31针对性comparison tests），git diff --check通过。全局--records失败均为其他MiniMax/Qwen3.6缺失链接和历史case过程产物，当前case无报错；不修改或清理无关记录，不把全局records标为passed。

## 2026-10-14 JSON 配置迁移（op002-json-cfg01）

用户在侧对话明确要求在现有独立容器实施配置表，并授权仅修改磁盘文件、由用户稍后重启。当前 qwen3vl-opt2/8000 和 P64K benchmark 属于用户正在运行的测量，不停止、不重启、不发起 GPU 测试。此操作是 op002 同一优化点的工程整理，不新增性能收益，也不改写旧测量身份。

| 项目真相 | 本次约束 |
|---|---|
| 当前实现 | 私有 FlagGems-vllm MetaX fused_experts_impl；revision f6fdb9b120787e12892ac67e54979cbf829c7d64；保留文件 SHA 4bac1ee1100fcaeb28f9204715e32fcbcd6807c1da4bf128c8f9d69735ead7f1 |
| 可改文件 | MetaX fused_moe.py、相邻 stage JSON 配置、pyproject.toml 包资源声明 |
| 只读范围 | Plugin、vLLM、FlagGems、原测量/trace/回执、源 qwen-vl；保留已有采样等未提交改动 |
| Build / validation | 当前 editable 安装不重装；CPU 配置等价性、精确范围/缓存/回退/包资源及语法检查；单项预算60秒 |
| Benchmark / profiler | 本次不运行；保留既有 op002 性能证据，新文件身份的硬件和端到端验证等待用户重启 |
| Autotune / fallback | 已离线扫描选出的 stages=1 转成 JSON；不是新增 NVIDIA kernel，不新增运行期 autotune；未命中沿原配置，不新增 torch compute fallback |

| 契约 | 本次行为 |
|---|---|
| 输入 / 输出 / 语义 | MoE 张量、量化、bias、alias、router、layout、accumulate、forward-only 契约均沿原实现；配置迁移不更改数学操作 |
| 支持边界 | C550/BF16/E128/N2048/K384/top8/GEMM2/M8..64/block_shape=None；不扩大已保留范围 |
| 参考 | 当前保留候选真实配置函数；与未优化原文件的差异只能是同范围的 num_stages |

| 路径 | 配置与验证 |
|---|---|
| 既有 embedded YAML | 保持原优先级、最近M规则与 is_embedded=True 语义 |
| 默认配置 + stage JSON | 文件按设备/shape/dtype/topk/stage定位，精确M选择并缓存；只覆写 num_stages，is_embedded 保持 False，避免改变融合/对齐路径 |
| 未命中 / 缺文件 / 量化 | 原默认配置；不跨 batch 外推，不增加新 compute fallback |

目标仓库 AGENTS/workflow 已读取。该 revision 缺少其引用的 optimization.md/deep_opt.md；本次仅整理既有配置，不写新 kernel、不做深度优化、不签发性能验收。

### 实施结果

已仅写入 qwen3vl-flaggems-e2e-20261013 的私有 FlagGems-vllm：
- fused_moe.py：移除旧 C550/shape 硬编码分支，在现有 try_get_optimal_moe_config 的默认路径读取缓存的 stage JSON；原 embedded YAML 优先级、is_embedded=False 下的融合/对齐组织均保留。
- utils/configs/moe/E=128,N=2048,K=384,topk=8,device_name=MetaX_C550,dtype=bf16,gemm_stage=gemm2.json：57 个精确 M 条目（8..64），每项仅覆盖 num_stages=1，不固定或修改 tile/warp 等其他字段。
- pyproject.toml：将上述 JSON 加入 package-data；当前 editable 导入无需重装，未来打包不会因仅包含 YAML 而遗漏该资源。只做资源规则验证，未构建 wheel。

新旧最终配置 159,840 组 CPU/static/mocked 对照全部一致；覆盖目标区间、边界、其他硬件名称/shape/dtype/topk、量化 block_shape、GEMM1/2、fast-path 标志；未实测其他硬件。100 次重复查表只有一次文件读取，返回配置的修改不污染缓存；缺文件回退、坏 JSON 显式报错、legacy embedded 优先级均通过。AST 审计仅三个配置函数变化，五个 Triton JIT 函数不变。git diff --check 通过，Black/isort/flake8 未安装，不改依赖环境。

源容器四仓库和独立容器其余三个仓库的前后完整内容指纹相同；独立 FG-vllm 仅上述三个文件变化。新源码 SHA bcc9a3b15337c192c6eb43229659d73e92e9a7813937cb3bf3b6ef8ad2a486b0；JSON SHA ad5bf196af20be5f9bb2916527a9fd061172e7fbbc93ed329a3e925758654261；完整私有仓库 SHA ef38f46c8a719c7f64ba7c51cc95c895b8667de6bcf9e40b9561c365b4bda99b。

用户现有 qwen3vl-opt2/8000 进程及配置前后相同，当前手工使用 GPU4/5；该运行不与本案例原 GPU0/1 测量混合计算收益。此次没有停止/重启服务、GPU 调用、profiler、模型精度或性能评测。CPU 配置检查不能替代重启后的 worker 命中、graph replay 和端到端复测，pr_readiness 仍 experimental。

执行脚本与前后源码、补丁、配置都在远端 commands/op002-json-cfg01；apply 脚本 SHA 1b1ec05c6a339c3e006b178f92d4e3b53f7fb9c7babceebf7691304c00d9892a，patch SHA 879fc48491068001c1ef1b41b4eb4afa038ffe7e579db94da6fbffb62398dfce。原生验证 results/op002-json-cfg01-validation.json SHA 7639a2a78ab98d64f9da3ecc550680861469d960200d727e67ea23d385b50534；收尾 results/op002-json-cfg01-final.json SHA 4a2ecb316d10235acff017e45da92d395a5fa92801b7eefc427573c19357deb5。回退到迁移前保留版本，可恢复归档 fused_moe.before.py 与 pyproject.before.toml，旧代码不读取新 JSON；重启由用户控制。

准备过程中本地默认 Python3.9 不支持目标仓库注解，改用项目 Python3.12；边界验证初稿误把所有范围外默认值当作 stage3，修正为真实迁移前配置 oracle（原大M资源启发式可能选1/2等），随后完整等价性通过。SFTP 路径查询失败未写入目标，改用已核验 SSH 通道独占创建传输归档，SHA 一致；无源码或 benchmark 重跑/覆盖。

## 用户 opt2-retry 结果导入（2026-10-14）

当前用户服务 qwen3vl-opt2-retry/8000 使用GPU4/5。JSON实际磁盘SHA仍ad5bf...、private完整指纹ef38f...，新隔离容器完整MoE实际读取G2 stage1；不声称已直接观测用户worker缓存。以下均为全部三轮中位数，不使用原SUMMARY删除首轮的统计。

| 输入 | opt1 TPS | opt2-retry TPS | 观察变化 |
|---|---:|---:|---:|
| 4096 | 827.29 | 851.94 | +2.98% |
| 16384 | 321.43 | 328.71 | +2.26% |
| 65536 | 66.56 | 66.91 | +0.53% |

缺原生run-record、冻结准入和回退，不形成新精确因果或formal gate。P1K/P32K未补齐；P64K不替代P32K。
