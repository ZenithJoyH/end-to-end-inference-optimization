# op-006：attention 边界工作区长度取消值专化（私有验证）

方向：operator/improve；父场景P1024/D1024/C64/N128，目标为Mixed中预热后仍出现的CPU编译停顿。已完成源/IR诊断及私有单变量实现；生产源码和服务未改动。

实际调用由当前源码和自有TP编译IR还原为tn_direct.launch_d256_tn_direct→tn_boundary.launch_tail_split→tn_direct.flash_varlen_fwd_d256_tn_kernel；是bulk前缀/尾部SplitKV边界，不是普通splitkv.py:648入口。TAIL_ROWS=batch_size*(64//HEAD_RATIO)或batch_size*128，现为tl.constexpr。所捕获Hratio8/H8/D256：prefix B13/21给104/168，Q_TILES2、NUM_SPLITS16；tail给1664/2688，Q_TILES32、NUM_SPLITS4。每组去debugloc并只替换三个TAIL_ROWS仿射常量后，完整TTIR逐字相同。TAIL_ROWS在主kernel仅赋给output_total_q参与输出/LSE地址计算，不用于tl.arange、tile尺寸或分支。

拟议最小改动：仅私有主TN partialkernel将TAIL_ROWS改为普通运行时整数，并加入do_not_specialize。当前LibEntry的constexpr值进入const_args；普通specialize标量也按(type,value)取key，而do_not_specialize整数按i32/i64/u64类型取key，所以两项必须同时处理。Q_TILES、NUM_SPLITS、分支flag、PAGE_SIZE/headratio/headcount/tile/warps/stages保持原样。merge及独立prefix/alignedkernel也有类似字段，但未在本轮捕获的8个attention根事务中证明需要修改，不一并改动。

首个证伪：私有源静态/API分类检查，既有真实B13/21与B1/2/32/64边界输出/LSE精确对照；同family内跨B编译键应4份归为2类，保留实际prefix/tail区别。单变量数值、边界、graph capture与>=2replay、标准原生benchmark全通过后才考虑部署；native micro守护old/current每已声明case>=0.95，任何失败停止，不靠删case或回退native隐藏。已知模型驻留时新Stream有资源问题，不能重复同一受限状态盲试；需要独占graph时另行准备具体窗口并依据实际授权处理。

完整E2E和同配置A/B/R/阶段guard仍须按性能Skill冻结与验证，不能把编译键归并倍数当吞吐收益。

当前环境：mx-59/qwen3.6-35B/8010/TP2物理GPU6/7，当前源gdn-current-plus-op005-bca465d2。用户要求保持FlagGems全部启用；attention/GDN/MoE workspace复用保持。原地例外有效，vLLM/模型/tokenizer只读，不停容器/其他负载。已有单次停服窗口均结束；本计划不含自动重启/部署授权扩展。

当前正式GPQA170/198=85.8586% gate仍有效；但只属于已加载source。新候选无已执行精度/graph/benchmark/E2E数据，不能复用当前gate签发新source；正式加载后按198/max65536/temp1/top_p.95/top_k20/seed42/C32/80门槛重新验证。最小回归先执行，失败保留并诊断，不叠加优化。

完整P1K006的1133.427/991.227/1146.247tok/s、13.677%spread>10%以及慢轮全部保留，不能挑快轮算收益、改warmup、重跑creator或直接切P4K。全部原始产物留唯一ROOT；下一步私有候选必须从当前GDN+op005源码复制并保存现有dirty/SHA/补丁/回退，不能使用旧sampler整包覆盖。

当前结果以文末更新为准；生产code_change=none，graph/standardbenchmark/E2E尚未运行，非目标硬件未测。失败仅保留私有产物，不动运行服务。

外部结论：/public-flash/jinghao/qwen3.6-35B/20261013-qwen36-35b-metax-e2e-current/results/op005-residual-specialization-conclusion-20261015.json SHA75bbd364697597101ce2562acdb936a92e49c4a7ee928ce7af583f8e6a1028ec；tuple proof SHA2162268ffb833ff9e2101873414bf837b204e407cac39f6166a3b1d5fb14fc10。

## 编码前冻结：项目真相

| 字段 | 本轮事实/计划 |
|---|---|
| API/来源 | 既有MetaX paged D256 causal GQA attention边界；用户要求消除预热后编译；无新增Torch公共API |
| Editable | 仅新私有副本主TN kernel的TAIL_ROWS注解与do_not_specialize；配套私有tests/benchmark |
| Read-only | 当前/workspace/FlagGems-vllm及Plugin/FlagGems/vLLM、权重/tokenizer、冻结reference源码/既有原始评测 |
| Build | Python源码AST编译与实际导入，Triton按需编译；不安装/升级环境 |
| Validation | 原生pytest CPU结构/参数契约、默认stream数值与实际LibEntry key数量；后续独占graph>=2replay，当前不建Stream |
| Active set | BF16/page32/GQA8/H8/D256，B1/2/13/21/32/64各prefix16splits、tail4splits；strided B2及page16/GQA4 B3；非Split FP16/BF16×page16/32 |
| References | 当前源冻结Gems kernel精确output/LSE全张量比较；测试专用FP32 causal reference核有效前缀/尾部行，atol.02/rtol.01沿用既有范围 |
| Compile key | 先B13预热两次再B21，每family当前2键、候选1键；prefix/tail真实区别不归并；其他merge键单列不宣称全编译归零 |
| Timeouts | CPU准备90s，默认stream数值/编译验证总240s，提前写进运行contract；graph和性能未启动 |
| Benchmark | 原生base.Benchmark，baseline明确oldGems、candidate新Gems，同boundary partial+merge事务；每已声明case old/current>=.95。Torch完整attention只作功能reference，不与局部boundary混算速度 |
| Autotune | no-autotune豁免：现有MetaX专用固定tile/warp/stage原封不动，非NVIDIA路径，无新增调参或算法；不改tune_config |
| Profiler | 本轮不采集，已有CPU编译/源码IR证据；无profiler-on数据混入性能 |
| Fallback | 保持既有dispatch/error；没有新增Torch或native计算fallback |

目标repo AGENTS/workflow已完整读取，HEAD05d0ff0547dc9cc7cce18f47c6f57cc9d04f0777/main。dirty7tracked及既有untracked均保留；optimization.md/deep_opt.md在目标repo缺失，AGENTS说明when present，已有op005同事实，不创建替代规范。workflow末尾conv1d任务模板不覆盖用户明确attention目标。新算子导出/注册/tune_config不适用，因为只改既有MetaX kernel参数分类。全repoCI与非MetaX硬件not_run。

## 编码前冻结：数值契约

| 字段 | 范围 |
|---|---|
| 语义 | 每请求global causal paged attention，Q/K/V已量化到输入dtype，D256、有效query/head/kv映射同当前实现；prefix/tail未写行保持原输出值 |
| dtype | 主SplitKV boundary BF16，acc/partial/LSE FP32、最终BF16；非Split既有FP16/BF16作为守护，不扩大原support |
| layout | 主case contiguous；strided Q/Out与pagedKV/page-table pitch32作为边界；LSE保持既有连续布局契约 |
| 数值 | 随机有限QKV；原/候选output/LSE必须精确相同；NaN/Inf/signed-zero算法处理没有修改，异常输入不新增支持或放宽 |
| alias/out | caller output/LSE继续原地写入、同shape/dtype/device；输出tensor的未写区域与strided canary必须保持 |
| empty/error | 现有总token0的上层early return及原错误guard保持；不直接对不承诺的空boundary grid强加支持 |
| autodiff | 推理forward-only，未扩展autograd |
| unsupported | 原有D/page/dtype/feature guards原样；不引入fallback计算 |
| Torch使用 | 仅tests/benchmark输入生成、比较、独立reference；生产改动只为参数分类，不新增任何torch调用 |

## 编码前冻结：路径与阶段

| 路径 | 行为 | 首次验证 |
|---|---|---|
| prefix SplitKV | 原grid、Q_TILES2、NUM_SPLITS16，动态TAIL_ROWS=B*8 | B13->21 exact output/LSE和1键复用 |
| tail SplitKV | 原grid、Q_TILES32、NUM_SPLITS4，动态TAIL_ROWS=B*128 | 同上，保留prefix/tail两独立模板 |
| nonSplit | TAIL_ROWS默认0不参与结果，原base Q_TILES1保持 | FP16/BF16,page16/32守护 |
| shared边界 | page16/GQA4及strided保留原选择 | 原路径精确对照，未测设备不外推 |
| graph/标准性能 | 尚未启动，不用默认stream数值替代graph | 已知Stream资源压力，不重复模型驻留状态造Stream；需具体独占方案/实际授权后再做 |

本轮mode=minimal-regression，scope=private operator path；graph未完成时总体minimal状态仍incomplete，不声称候选已验收或GPQA通过。

## 私有实现及唯一默认stream回归（2026-10-15 08:54UTC）

从当前GDN+op005源码复制928个已跟踪及非忽略文件到`/workspace/qwen36-e2e-op006/FlagGems-vllm`，私有生产文件仅主TN参数分类变动，SHA088e684fdc9a4f6105a535c7fcfd8ab99e26fb083d988b551d6e472d0a168040。主体AST/其他函数不变，当前生产928文件校验未变，CPU契约通过。未安装私有包，只有单进程PYTHONPATH指向私有src。

源码/回退证据`/public-flash/jinghao/qwen3.6-35B/20261013-qwen36-35b-metax-e2e-current/results/op006-private-source-20261015.json` SHA144c5606be45b5a3af0f6d6907932cdd3ad83888dd1488aefa7be8830b097432；原dirty补丁70c05b52...、原TN归档00c46bff...、增量补丁b565b03e...，完整SHA见state。源创建脚本285cf3be...已完成不可重放。

标准test2797b9eb...及benchmark33b8e4bc...已落私有repo，local black/isort/flake8通过，full CI未执行。默认stream只选原生pytest `cpu or nongraph`，预冻结8tests/22次对照，graph4项明确不运行；主TN预期12键归并为2，merge键另外存在，不宣称全部编译归零。

唯一回归hostcontroller1207633/birth499402780，manifest `/public-flash/jinghao/qwen3.6-35B/20261013-qwen36-35b-metax-e2e-current/manifests/op006-nongraph-controller-20261015.json`，总预算240s。client3d0b5454.../controller e638290c...已保存执行，不重复启动；前置12252源码/fullenv/model/APIidle/原GPU6/7 worker独占检查通过，preflight753c2920...。当前未取得数值终态，graph/标准benchmark/模型精度/E2E均未做。

## 回归终态与review021（2026-10-15 08:58UTC）

原生collect成功：8非graph/4graph deselected。实际pytest **8 passed，22次输出/LSE精确对照全部通过**，包含strided/page16/GQA4及非Split FP16/BF16守护；全部预声明case保留。pytest111.13s，client134.12s，controller143.56s，240s预算内，未超时；全部私有进程已退出。

主TN单独控制prefix/tail两family，每个按B13、13repeat、21、1、2、32、64调用。原路径每family新增键[1,0,1,1,1,1,1]，候选[1,0,0,0,0,0,0]，合计**12→2**；B13预热后B21新增1→0。真实prefix/tail模板仍各保留一份。加入共享layout/page/ratio/dtype及非Split守护后，最终mainkeys20→10另列；不能拿它与受控12→2混算。merge及其他kernel仍有自身key，本结果不声称全链路编译归零。

原生结果`/public-flash/jinghao/qwen3.6-35B/20261013-qwen36-35b-metax-e2e-current/results/op006-nongraph-20261015.json` SHA9f889c67a863aa97970261de05f04179dfd2dc6e27729972c51e182176f7b4c0；XML8e4a4e84...，runnerd7d635d2...。核验摘要`/public-flash/jinghao/qwen3.6-35B/20261013-qwen36-35b-metax-e2e-current/results/op006-nongraph-summary-20261015.json` SHAd2fb4e5b0787faf8d372fccce5c212562d257939995fbbffeef6ddfbb3482259；summarycommand c5e82ca5...，均已完成不可重放。

postcontinuity01fb7b0b...再次核源码12252文件/fullenv/model/精确实例保持、APIidle、GPU6/7仅原worker。生产未修改/重启，FlagGems全开和当前170/198 gate保持。私有source088e...只证明本范围数值/键复用；graph与标准benchmark未跑，模型GPQA/E2E未测，**overall minimal-regression=incomplete_graph_pending**，PR=experimental。

review021：Prefill/Decode/Mixed仍采用006实际客户端代理和编译停顿证据，不能因私有键缩减写模型收益。下一优先准备同一088e源码的4graph×至少2replay及原生CG8shapes×3paired完整24row、逐case>=.95护栏；先保存具体恢复/精度重绑定方案，再根据实际授权处理资源窗口，不复用旧停服许可。op007保持独立planned未实施，禁止叠加生产源码。后续加载任一新source必须新全198/65536/80 GPQA；正式P1K A/B/R、阶段guard、四场景验收仍欠。
