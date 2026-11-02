# MM 调参诊断证据卡

## GLM-5.3-Flash / PPU：新bucket触发请求内宽搜索

- case_id：20260911-glm53-flash-ppu-e2e / point51 / mm-cache-diagnosis-05。
- 完整事实：[点51记录](../../../../../models/GLM-5.3-Flash-BF16/ppu/optimize/20261021-sparse-mla-small-head-dual-backend-51.md)，[案例摘要](../../../../../docs/cases/20260911-glm53-flash-ppu-e2e/README.md)。原始源码、CPU探针、DB副本和请求栈留模型记录所列远端目录。
- status：blocked；evidence_level：reproduced（原生请求RPC失败、真实事件、CPU原生key/prune与只读DB差分），不是修复通过或正式性能。
- 环境：PPU-13 / ZW810E / TP16 / BF16 / vLLM0.24.0；FlagGems `9c9bff3979a6f90ef0d0c78aa6a1da2262723f31`。Plugin PR454基线加公共路径/H4临时诊断补丁，具体内容SHA见点51；`FULL_DECODE_ONLY`捕获通过，Prefill不是整段FULL。
- operator_path：Mixed中Prefill投影；`aten.mm.out → FlagGems _thead/ops/mm.py → LibTuner → mm_kernel_ppu`，主路径M20481和8198、多组N/K、dense NT B、BF16；本卡不改变MM数学或cache key。
- change：framework诊断，只读CPU方法/元数据/缓存对照；FGV SQL修复为既有前置，未改MM策略或kernel。

### 证据摘要

1. P4096/D16 C1完成后，C8约300s RPC超时；16worker在多个采样点处于MM在线benchmark，至少995次/rank、约129s/rank已记录。事件触上限，不能称全部300s独占归因。
2. 原生key CPU对照：M20480→bucket20480、M20481→21504、M8198→9216。其余flags/N/K/4个BF16 dtype不变，11组相邻旧bucket命中、新bucket冷缺失。
3. 原生候选114，合法性裁剪后104，与实际前9组各104次一致。裁剪不是请求期搜索预算。
4. 同一命名空间ConfigCache299→318（+19、删除0），BenchmarkCache30631→32671（+2040、删除0）。19组各104条完成，另M8198/K1536/N4096只写64条、无winner；缓存正常持久化，并非反复失效。
5. ConfigCache的bucket key命中会跳过搜索；BenchmarkCache保留raw key并不意味着每个raw M变化都重调。
6. 额外独立风险：当前构造器生成的20/100与25/50 `do_bench`闭包都标记custom/-1/-1。CPU原构造器与实际DB tag支持该元数据碰撞，不是本次冷bucket缺失的直接原因；需独立修复验证。

### 知识差量与限制

- prior_belief：MM长停顿可能来自缓存失效、形状差异、宽搜索或设备异常。
- outcome：refined；当前直接机制是新Config bucket冷缺失触发宽搜索，已有结果正常写回；协议tag是另一个问题。
- future_first_check：重建实际bucket key与raw benchmark key，比较前后winner/候选行和namespace，再检查候选数及搜索预算；不要先清库、弱化key或盲加预热。
- 首个整模策略证伪已执行（MM06）：相同SQL起点和P4096/C8，baseline冷M12293为237.634s通过、candidate冷M28673为58.937s通过、revert冷M20481+8198为300.728s RPC失败。三角色16rank均有实际事件，候选176次policy调用将104合法候选限4；但冷shape交集为0，严格因果比较incomplete，不据这些冷耗时报稳态加速。
- 新差量`refined`：异步接纳改变冷M投影组数，进而改变请求内搜索预算，即使SQL初始字节与HTTP契约相同。未来首个实验改为固定shape序列和实际输入hash，再作策略A/B/R，后续才验证原C64和完整minimal。
- MM06候选未保留，断网后09:40只读完整审计SQL-only/OFF/DB不变；下一固定shape07仅准备中，不能填写通过。
- 数值、精度与验收：本轮无GPU/MM数值修复，无新GPQA或性能；SQL修复保留，临时H4回退、服务OFF。没有证明降低搜索空间后的精度/graph/端到端收益，不外推其他平台、shape或revision。

## DeepSeek-V4-Flash W8A8 / MetaX：FP32投影绕过vendor并复制转置权重

- case_id：20261022-thinking-gpqa-metax103 / op-004。完整事实：[op-004](../../../../../models/DeepSeek-V4-Flash-W8A8/metax/20261022-thinking-gpqa-metax103/optimize/op-004.md)，[案例摘要](../../../../../docs/cases/20261022-thinking-gpqa-metax103/README.md)。status：kept；evidence_level：reproduced；仅当前MetaX硬件与版本，不外推PPU调参案例。
- 环境：mx-103、TP8 MetaX C550，vLLM0.24.0+empty、Torch2.10.0+metax3.8.2.2、FlagTree0.7.0+metax/Triton3.6；Plugin a696859b、FG8200f71f、FGVfa78ddee及未提交源码SHA见案例。graph为FULL_DECODE_ONLY，prefill走native compile，prefixOFF。
- operator_path：`cublas_gemm_bf16_bf16_fp32 → CachedOp(router_gemm_bf16_fp32) → default.flagos → flag_gems.router_gemm → weight.t().contiguous → general_mm`。名为router的primitive还承担attention投影；必须从父调用确定。x `[M4096,K4096]`、weight `[N512/1024/2048,K4096]`均stride`[4096,1]`，输出FP32；decode含M64等小M。
- 瓶颈：公开`flag_gems.mm_out`已解析到MetaX NT文件，不代表`router_gemm`也走vendor；后者仍通用并实体化转置。不同import名可能加载同一文件的不同函数对象，第一次以对象`is`作前置断言被拒绝且零GEMM；修正为源SHA、输入stride及实际kernel证明。
- change：operator/replace。现有MetaX backend内两处生产文件新增幂等opaque native FP32 GEMM及OpImpl；案例配置显式选vendor.metax，直接`torch.mm(x,weight.t(),out_dtype=torch.float32)`，保留flagos路径。全局默认策略配置、FG/FGV/vLLM源码本轮不改。
- 算子证据：同输入5shape、30候选行；M4096/N2048/K4096旧FG2.1495ms、无copy通用NT0.6943ms、MetaX NT0.6661ms、native0.3371ms（graph中位）；13数值/非对齐/带间距/零维/schema/fake/AOT/两次changed-input graph通过。FGV M64/N512需要96KiB共享内存，高于64KiB卡限，排除而不降格为静默fallback；非模型OOM。
- 实际命中：三阶段24条trace、全部8rank，新native custom-op和mcBLAS FP32命中；旧FG router/MM-general均0，rank0二维copy均0。attention三维headpack/strided输出复制仍存在。M4096/N2048 CPU inclusive中位324.757→119.331μs；不是关键路径或profiler-E2E收益。
- 端到端：新全量thinking GPQA172/198＝86.87%（冻结80%通过）；P32768/D1024/C64/N128同实例、prefixOFF三轮204.2301/203.7078/193.2881tok/s。中位203.7078相对fw003历史180.1870观察+13.05%，非独立B/C/R。384/384成功，无OOM/非法访存/抢占。
- 残余与负例：初始预热102.08/187.69、JIT138/35，未过5%准入，零测量且完整保留；新固定conditioning+两轮admission后3轮全部保留。测量JIT0/0/7，第三轮7项是量化/padding/qnorm-KV/MoE初始化/zeros，IR出现M2092。spread5.3714%通过冻结10%，但完全预编译稳态覆盖未闭合；未将第三轮剔除。原镜像208.91仅预热观察，不能声明正式一致。
- knowledge_delta：refined。vendor ATen导出、同名算子与全局prefer不能证明高层primitive派发；FP32输出契约和转置布局常比算子名称更有判别力。下一次先查真实调用、输出dtype、导入文件/注册key和Input Strides，再比较无copy通用NT、vendor NT及native FP32；微测通过后仍需真实八rank命中、完整精度和无profiler父场景。
- 后续首个证伪：M2091/2092/2093/4096同输入检查raw-M constexpr与runtime-M的编译key/数值/graph；不以预热重复到变快代替修复。尚未应用此方向。未知：其他平台、其他模型/shape性能、原镜像正式稳态baseline及本组合四场景最终验收。


## DeepSeek-V4-Flash / MetaX：去除量化等边界特化后，残余NT编译仍在

- 证据等级：原7项JIT修复与目标硬件数值/graph/三轮测量为reproduced；剩余NT慢段仅observation，尚未归因完成。详见[op-005主记录](../../../../../models/DeepSeek-V4-Flash-W8A8/metax/20261022-thinking-gpqa-metax103/optimize/op-005.md)。
- 匹配：MetaX C550/TP8、vLLM0.24empty/FlagTree-Triton3.6、BF16输入W8A8；P32768/D1024/C64/N128，prefixOFF，FULL_DECODE_ONLY。内部ragged M2092，K256/1024/4096；MoE E256/topk6/N12552。
- 机制：quant M、QNorm token/insert bounds、MoE stage1 N/CAP/ECAP、pad生成器elem counts/bounds改runtime；launch cache同步按动态整数类型建键；zeros仍保留三档tile并在libentry前显式选择，防止取消N值key后复用旧heuristic。量化reciprocal/FP64scale及int64地址未改。
- 验证：227项算子回归、两次变化输入graph、模型18/18及新完整GPQA170/198通过。未见M2094/2095/2101/2111的目标新增binary0；真实模型IR参数也为runtime。仅6个FG/FGV生产文件，未增加Plugin/vLLM patch；其他模型/平台not_run。
- 结果：三轮TPS201.3868/203.7935/194.3892，TPOT240.1629/237.1143/249.0065ms；spread4.6697/4.9518%勉强在冻结5%内。原7项0/0/0，但其他新binary3/0/3，第三轮下降仍在；全部384请求成功，0OOM/illegal/preemption。不是完全预编译稳态或独立B/C/R贡献结论。
- 反例/知识差量：删除原7个raw-shape特化没有完全消除慢段。第三轮3项实际是FG MetaX `mm_kernel_nt`，BF16 output，不是op004已接入native的FP32-output primitive；其M/N/K已经runtime，31是ceil-div的BLOCK_M−1常量。源码有ConfigCache miss→BenchmarkCache/候选测量路径，但真实policy/MNK/bench_time仍需现场证实；不能把binary mtime跨度当完整开销，也不能盲目DNS M破坏EVEN_M/tile cache条件。

## DeepSeek-V4-Flash / MetaX：NT候选试跑与ConfigCache分桶

- 来源：[op-006主记录](../../../../../models/DeepSeek-V4-Flash-W8A8/metax/20261022-thinking-gpqa-metax103/optimize/op-006.md)，承接op005；状态kept，证据reproduced（仅C550/TP8/当前版本）。
- 匹配：FG8200f71f+私有改动、vLLM0.24empty、BF16 dense NT N64/K4096/M<=4096；FULL_DECODE_ONLY服务，P32768/D1024/C64/N128、prefixOFF。FP32-output native router是另一条路径。
- 实际路径：8rank的CM因缺少xgboost AUTO回退Default；尾批M3688的A/B/C stride=(4096,1)/(1,4096)/(64,1)，每rank真实测6候选（总48），0.784–0.820s/rank，winner64x64x64/cpasync/stage3/warp4。旧第三轮3项basic二进制配置都匹配这些候选。源码benchmark分支、CM命名空间miss但0bench和实际Default请求期bench必须分开。
- 改动：仅FG MetaX ops/mm.py，Default ConfigCache按已有log2-M分桶，raw BenchmarkCache与实际M的LibEntry/EVEN键保留；请求前准备13桶及M1..4096完整编译域。Expanded/CM显式策略保留；其他模型/平台性能未测，PR仍experimental。
- 负面与正确性：跨tile的逐位对照在M2049有42/131136差异、max0.25；同tile新旧逐位相同、独立FP64误差相当。收紧独立FP64→BF16参考到atol1e-3/rtol8e-3，同时同tile及graph逐位验证。55项+清LibEntry后4096M域通过、0新binary/bench；模型18/18、完整GPQA169/198>=原80%阈值（比op005少1题，不称精度相同）。
- E2E：同实例W3/M3，TPS203.3665/203.5084/201.2218、TPOT237.2020/237.0885/239.9502ms；spread1.1244/1.2064%过冻结5%。384/384成功、0OOM/非法访存/抢占；NT0/0/0且NT配置/BenchmarkCache均未变。第三轮仍有index/mHC2编译，不能称全链路零JIT、旧31秒全部归因闭合或原镜像性能相同；没有新独立B/C/R。
- knowledge_delta：refined。新增binary可为搜索候选而非最终执行配置；默认精确M的配置cache也能在runtime-M内核中引起请求期搜索。未来先查真实mode、两类key、trial/winner/bench计数和布局，再设计有限预热/选择域；不要盲目DNS M破坏缓存的EVEN掩码，也不要要求不同合法tile的BF16逐位一致替代独立oracle/full gate。历史原始轮次不因本卡而删除或重标。
