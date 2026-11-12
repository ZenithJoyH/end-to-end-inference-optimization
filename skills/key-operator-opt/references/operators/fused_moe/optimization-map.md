# Fused MoE 检查图

## 充分预热后仍重复出现MoE alignment编译前缀

- 匹配/信号：PPU、FlagTree当前后端、Gems f0aa7f12 alignment、int32/topk10/E512；M8065 Mixed前缀期间重复source写入而缺成功metadata/binary。HAS_TLE只证明版本/import，不证明该backend支持distributed barrier。
- 首查真实旧IR与backend拒绝函数、try/fallback异常路径、成功前才写cache的条件；debug-only fallback可能隐藏反复失败。先用CPU解析旧产物，不在活跃服务额外触发不支持编译。
- 最窄候选：已知缺能力后端在原选择入口绕过TLE，保留原四阶段fallback和非目标原语义；CPU vendor/CUDA/experts/异常fallback契约后，仍须实际GPU数值、零/非对齐、changed-input graph与模型C1/C8，再同契约测阶段净收益。
- 停止/反例：op061第一项M0进入原fallback后tokens_per_thread0→arange(0,0)编译失败；原/候选该AST相同，生产零输入ABI未知。记录继承边界并停止，不暗删M0或当成TLE新回归；模型与性能未跑，TTFT因果比例未知。证据与范围见[op061案例卡](case-index.md#qwen38-flash-next--pputle能力不匹配与原alignment空输入边界)。

  v2将上述ABI未知收窄：native vLLM会把M0的sorted/expert容量压到0，因此需同时检查输入与两输出三处launch extent，而非只修tokens_per_thread；正extent完全保持、零extent取1且原mask屏蔽。应增加compact M0/M1、毒化count后的空graph replay，不能仅用full-capacity oracle分配替代实际caller。当前83项GPU边界/graph已过、模型/性能尚pending；仅迁移该ABI/当前backend，不推导其他TLE能力或端到端收益。

  v2随后10短doc2/C8及capture/replay接入护栏通过，当前模型cache有19份四阶段MLIR来源，无TLE字串；这些只允许结束本最小回归并保留候选，下一证伪应为预冻结同条件阶段性能对照，不是继续增加短题直到“稳定”。编译.source可为MLIR而非Python，查`tt.func`及source loc，并保留binary/metadata/SHA；不能因`def kernel`搜不到就判未命中，也不能把编译产物当逐步trace。正式精度与大M/C64性能均未由本小范围签发。

先核外层完整API选择条件：Qwen3.8/PPU env065的Plugin `PlatformFL.is_cuda()`明确仅NVIDIA为真，虽然PPU is_cuda_alike=true，完整FGVLLM fused_experts快路径仍不进入。当前分步CachedOp可调用FGVLLM通用alignment，因此库内thead完整入口使用no_tle不能证明通用门禁多余；空输入则须另查实际caller的naive/early-return，公共API零边界缺陷不等于当前模型触发。匹配revision、源码SHA/启动冻结、既有编译产物与CPU条件对照见[env065补证](case-index.md#qwen38-flash-next--pputle能力不匹配与原alignment空输入边界)，无新GPU/性能实测。

入口后续状态：[eng066](../../../../../models/Qwen3.8-Flash-Next/ppu/20261015-qwen38-flash-next-ppu07-master/optimize/eng-066-thead-full-moe-entry.md)已在磁盘候选开放thead＋FGVLLM开关1，保留其他guards/global-platform语义；126 CPU AST/mock仅证明选择和参数兼容。服务未重载，不能替代新实例完整API命中、graph和数值/模型回归，也不能由完整vendor no_tle外推通用alignment的门禁无必要。下一检查是受控重载后的路径/数值证明，非继续静态推定性能。

## 完整MoE入口的权重转置是否真的被缓存

- 信号/匹配：Qwen3.8-Flash-Next/PPU810E TP8/BF16、48语言层/E512/topk10、graph；切完整thead入口后已有Decode日志慢速，非同配置性能验收。vendor807d12ce的模块级cache最多4个张量，每层w1/w2共96个稳定权重；不外推其他revision。
- 首查cache是每层还是全局、key/weakref生命周期、容量/淘汰和显存门禁，再核IR权重stride与graph边界。Python warmup/capture一次不证明device权重转换只运行一次；FULL replay也不能被解释为每步Python mem_get_info的成本。
- 机制证据：原cache AST对96稳定CPU对象轮转三轮均100%miss（reproduced机制）；旧14个GEMM IR原布局，新17GEMM＋2GEMV转置布局（observation）。全部层若每步复制，条件payload28.125GiB/rank、逻辑读写56.25GiB，实际graph copy频率/时长未测。
- 首个证伪：获准后保持完整入口/采样/所有修复及相同tile，只对比原转置策略与关闭转换，或有明确额外显存预算的一次性预转换；先完整MoE数值/changed-input graph，再交错固定shape时延。之后才独立改tile，覆盖M1/8/12/13/64及Prefill，不将C8 GEMV或M64 SiLU融合混作相同kernel。
- 通过/停止：必须证明实际分支、copy工作与数值/graph，随后同契约端到端；无节点/时间证据只记疑因，不报收益。若为留住全层简单扩容需另增约28GiB/rank，应先核KV/显存而非直接实施；增预热不能改变4项容量不匹配。正式精度failed-score仍阻止性能晋级。
- 来源与边界：[Qwen3.8案例补证](case-index.md#qwen38-flash-next--pputle能力不匹配与原alignment空输入边界)。本次仅CPU分析，无新设备实验/修复，具体性能根因not-proven；不是通用PPU结论。

  后续op067已限域reproduced：同vendor/形状、单层合成权重、原门禁和选参，两独立B/C/R冷缓存graph下关闭自动转置每调用少约2.47–2.54ms，回退恢复；数值/变化及恢复replay通过。此证据允许把策略成本列为优先候选，不能直接推断当前TP8服务恢复或旧超时修复。后续首查当前生产graph是否含相同copy工作；若要拆分转置布局收益与copy成本，另冻结热转置graph控制，而不是把on/off差值全部归到permute。线上重载/端到端/正式精度仍须新授权，范围详见同一证据卡。

  最终删除版op068补证：保留selector／kernel后，用超过原cache容量的多个live权重对、同址权重更新／恢复和变化输入分别验证；FP16/BF16两布局、naive/aligned及M8/H1024 GEMV哨兵的50项数值／16capture／64replay通过，非模型精度或性能结论。布局缓存修复的首个正确性实验应包含这些生命周期条件；静态输入下两次相同replay不足以排除陈旧副本。设备需隔离，原共卡计划被拒后获准停8010才执行，不能用资源guard代替隔离授权。证据见同一卡op068及主记录。

## 外层TP精度修改后，MLP/MoE路径仍有数值差异

- 信号/匹配：Qwen3.8-Flash-Next/PPU TP8/BF16、hidden2560/topk10、fresh778/808目标行、Mixed前7Decode；031已证明layer0 post-attn完整目标行相同，最终logits仍不同。其他模型/后端须现场重核。
- 首查：模型外层requires_tp_all_reduce与runner内部early/late reduce是否互斥；当前8份生成代码证明shared+routed相加后仍有BF16 TP输入，不能从外层helper推断全MoE FP32。
- 最小证伪：真实mix/router/topk、shared/routed local、sum及TP前后同时取证，区分专家/路由先变与同输入归约后才变。shared若被sum原地复用，必须在相加前复制；同时记录dtype、alias/shape/stride、请求/row offset/rank/graph。
- 停止/证据：没有内部实际值时只记compiled observation，不定首分歧或实现bug；新增probe/重载先获本任务授权，不能靠旧不同候选PT补齐。局部通过不签正式GPQA或性能结论。
- 来源：[accdiag032案例卡](case-index.md)，机制边界为当前MoERunner源码/私有candidate；并非通用所有MoE自有归约均BF16。

运行时补证033给出更窄分支：在相同PPU TP8/fresh778、808/Mixed起点7范围，若mix/router/topk/两local专家/preTP全同而postTP首先不同，先对真实ring累加舍入及通信实际拥有者做核验，不回退路由或专家kernel。现有CPU32真实环序可解释全部元素/256块，但不是该次GPU order trace。下一单变量候选应仅提高MoE自有late collective精度、保持early-reduced分支互斥及非BF16 fallback；必须证明实际前后dtype/graph/source和最终logits/概率，而非仅下一token相同。未改候选前先遵守重载授权，未做长Decode/正式精度前不宣称不收敛修复。证据reproduced且限域，见同一卡033补充。

034已在同一限域验证上述候选：model-instance late归约FP32→BF16、跨baseline288项上游同值、48份真实FP32边界及FP64参考成立，最终raw/prob也相同。因此此分支的后续首个检查可转向原长Decode/C64/正式契约的覆盖，不必仅因局部差异消除又盲改router/专家。它不是跨shape/平台不变量，也不代表60K症状已修复；非BF16/SP/已归约fallback只有CPU契约或未测硬件，扩大前仍须明确预算与授权，不自动签gate/恢复性能。具体证据见034卡。

## 配置格式迁移后的持续性能差距

| 项目 | 有限域检查 |
|---|---|
| 信号 | 回退相邻算子后性能仍下降，期间更换过 MoE JSON 或加载器 |
| 匹配键 | MetaX C550、BF16、TP2；每rank w1=(128,768,2048)、w2=(128,2048,384)、topk8；记录中 FlagGems-vllm f6fdb9b 加私有补丁 |
| 首查 | 实际目录/文件SHA、精确或最近M、GEMM1/2是否共用完整表、tuned/default标志及由此控制的路径 |
| 机制 | 旧局部字段覆盖与新完整表替换可能改变两个GEMM的tile/stage以及默认fast配置选择，不能视为单纯搬目录 |
| 首个实验 | 先CPU重放真实选择函数，后在同环境只切换旧/新MoE选参，验证数值、生产graph与P4K Mixed B/C/R；保持采样参考、gems-opt、sort和黑名单 |
| 通过证据 | 真实配置命中、同shape算子/阶段证据、充分预热与无profiler Mixed净收益；不能只看配置字典或profile累计时间 |
| 停止条件 | 未命中、数学/graph失败、测量仍有新编译、收益未确认；不以关闭FlagGems或同时回退整个版本解释贡献 |
| 反例边界 | 本例direct_sum阈值始终1<<60，未实际开启；不能因外层布尔分支变化就声称它造成退化。SiLU融合也不能与默认fast选参混为一谈 |
| 证据等级 | 配置分支变化已静态复现；E2E贡献为observation，尚未独立量化 |
| 来源 | [diag014证据卡](case-index.md) |

## 只调整 GEMM2 的调度参数

| 项目 | 有限域决策 |
|---|---|
| 信号/匹配键 | 上述MetaX C550/TP2/每rank形状；共享JSON中GEMM1需保持，GEMM2需要不同stage |
| 机制 | 可选gemm2子目录保存同格式完整表；共享表及默认入口不变，显式让GEMM2重新选择阶段表 |
| 首个实验 | 检查最近M边界，而非只看M64单点；本例M65恢复行避免覆盖泄漏到较大M；M0..65536及所有非stage字段逐项比较 |
| 对齐条件 | 两个GEMM复用sorted token alignment时，BLOCK_SIZE_M必须相同；阶段表不符应明确失败 |
| 通过/停止 | 实际dispatch、完整MoE数值、双rank生产capture/replay通过后才保留接入；阶段表缺失沿共享表，数值/graph/对齐失败停止；收益另做同配置Mixed测量 |
| 证据/来源 | op015为限域reproduced（CPU/数值/graph），端到端增益未测；见同一case card的op015补充 |

## stage 与几何必须配套验证

- 匹配边界仍为上述MetaX C550/TP2/BF16形状。op017对照将当前源码保持，仅切G2阶段表并保护M7/M65，不视为完整旧栈回退。
- 首个实验加入当前stage1、同tile stage3、旧完整G2 profile三个点；先完整MoE数值与graph，再交错同shape微测及同配置Mixed B/C/R。不要从BK循环数直接预测收益。
- 反例：旧完整profile在M64加快，但M8/M32可稍慢；同tile stage3的M64微测又快于旧profile，stage1不是普遍最优。范围决策应按真实shape分布和端到端净收益，不能只凭单点或恢复旧数值。
- 范围与测量具体结果见case-index的op017；数值/graph及目标P4K受控结果不能自动转移为P64、其他匹配模型/芯片或完整精度通过。

## GEMM2恢复后仍有差距：隔离GEMM1

在上述MetaX/TP2/BF16和实际shape边界，完整阶段G2表已覆盖时，可仅改根表G1非BM字段，并用M7/65保护最近M范围；全M重放证明全部G2与范围外G1不变。两个GEMM共享alignment，BM仍须相同。完整MoE数值与双worker生产graph后，再做相同Mixed B/C/R；不能从K-loop数量或G1/G2各自收益相加推导恢复。op018提供这一首个实验的局部证据，P64/大M/其他芯片仍需独立验证。

## 小M保留后检查Prefill大M

上述MetaX C550/TP2/BF16和每rank形状，先核实实际shared-memory分支，再比较G1/G2有效参数；显式False与缺省False不构成pair-kernel差异。共享对齐约束使中间M旧BM64不能独立复制；可先限域只恢复BM一致的G1 warp/group，用边界行保护最近M并CPU全域证明G2及小M不变。数值/graph和大M真实dispatch后，必须跑原长上下文Mixed B/C/R。P64准入短批只作准备，完整目标预热/测量及其计数分别保存；不能用局部微测或P4净收益替代P64。具体结果与适用范围见op019证据卡。

## 将分步 MoE 调用收敛到完整库 API

- 信号/匹配：PPU810E、BF16动态W8A8、E128/H6144/I384/topk4、graph；MiniMax Flash记录中的两条入口均已包含激活量化融合，不能把完整Python API直接当新融合kernel。
- 首查两个GEMM的实际base/最终tile、bounded覆盖范围、alignment、量化和归约，区分统一接口与设备工作减少。按小M/大M和路由集中度分别测完整调用，不加总局部kernel百分比。
- 首个实验：原样split/full/revert交错、两独立进程、changed-input graph数值；若小M配置不同，在独立进程中仅统一selector做归因，原样结果保留。
- 通过/停止：若large-M持平且small-M无一致收益，保持已验证模型路径；不要只为API统一就宣称性能晋级。接入模型仍需自身graph/精度和同契约Mixed，不能借split模型gate。
- 限域reproduced：原样小M均匀路由有回退、集中路由个别加快；统一配置后差距大幅缩小。剩余微小开销未逐kernel归因，模型E2E未测。来源：[MiniMax perf002证据卡](case-index.md#minimax-m31-flash--ppu完整入口不等于更少设备工作)。

该MiniMax案例op003进一步收窄上述残余成本：quant1-only换回原vLLM未消除差距；generic no-TLE默认两块workspace分开清零、split vendor合并初始化的差异才是已复现有效分支。首查scratch分配/初始化和现成workspace参数，优先复用已有kernel，不先新写量化器。复用前仍核对round-away/even、FP32 floor和FP16零行规则；完整调用graph持平不自动晋级模型入口或声明E2E加速。证据/限制见同一证据卡op003补充。

## 上游新增共享内存修复后能否删除本地保护

- 匹配：MetaX C55064KiB、Qwen3-VL每rank E128/H2048/I384/topk8、BF16/FP16，旧f6fdb9b私有保护与最新bad340d/PR977。
- 首查专用shape白名单和未命中后的generic路径；977的E256/TP2修复不能证明E128受到保护。重放两个GEMM实际config，并读取编译后metadata或OutOfResources中的required/limit；host粗估不能替代实际资源。
- 首个证伪：原/最新/回退同卡、同seed的M4096/8192完整MoE及graph矩阵。当前已复现最新GEMM1选择BM128/BN128/BK64/stages4/PAIR=true，要求98304B超65536B，B/R正常。
- 停止：任何生产大M资源或graph失败时，停止候选晋级和E2E；不要因小M可运行就撤生产保护，也不关闭FlagGems算子绕过。最新+最小guard是另一候选，必须重新验证，不称为纯上游通过。
- 限域reproduced；[PR977案例卡](case-index.md#qwen3-vl--metaxpr977-未覆盖-e128-通用共享内存分支)。无性能数字，不外推其他模型/芯片。

## 完整 MetaX API 接入后的阶段选参

- 信号/匹配：C550、BF16、E256/H2048/I256/topk8、私有FGV c575；用户要求调GEMM1/2，不能从原Plugin分步配置目录推定完整库API已消费配置。
- 首查实际loader/default函数、dtype及每rank形状，区分selector tokens与G2输入routed rows；共享alignment的BM保持，再独立比较N/K tile、warps/stages。生产候选按能力/形状/M限域，不按模型名/Host选择。
- 首个证伪：冻结有限配置、真实核导出与原数值容差，交错graph基线/候选计时，fresh-process确认后测完整MoE，至少包含uniform与集中路由、变化输入replay及未修改路径哨兵。未命中/数值或资源失败停止晋级，不盲加tile。
- 本例在M64和M8192的GEMM与完整MoE均有收益，但集中路由的增益明显小于uniform；这是严格限域的operator证据，E2E贡献未知。生产保留仍须同契约模型Mixed与正确性门禁，不以微测过门槛替代。[证据卡](case-index.md)、[原实验](../../../../../models/qwen3.6-35b-a3b/metax/20261022-qwen36-35b-mx104-stack-regression/optimize/fgv-moe-gemm-tune-001.md)。
