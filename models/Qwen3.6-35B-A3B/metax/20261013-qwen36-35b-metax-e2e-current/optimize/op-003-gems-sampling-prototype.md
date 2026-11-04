# op-003-gems-sampling-prototype：采样过滤在 Gems 中优化的独立原型

状态 private_standard_regression_failed_acc003_cdf_repair_pending_not_deployed；operator/improve；正式目标P1024/D1024/C64/N128。当前服务源码保持anchor，所有既有FlagGems算子启用与白名单保留；不改温度、top-k/top-p、RNG、模型权重或vLLM源码。

## 依据与参考来源

prof-001模型外每个采样步scatter累计约8ms（24calls192ms），与排序/概率累计同在模型外，不能当作纯Decode模型kernel。实际Plugin MetaX patch明确调用vLLM apply_top_k_top_p_pytorch，未使用vLLM Triton过滤。Qwen3-VL案例已有FlagGems-vllm MetaX values-only/counting算法归档补丁，可只读复用；它的旧数据和收益不是当前模型证据。支持M<=64/V<=262144，当前模型V248320须重新核验。

## 原型和必要语义验证

先从归档补丁提取Gems实现到本案例外部临时模块，独立进程使用当前Qwen3.6依赖测试，不加载其他模型、不修改其他案例/容器。计数算法仅在设备端证明FP32值可无损表示为BF16时执行，否则走精确FP32值排序；不能因为模型BF16或temperature1而假设该前提。排序去掉token索引和回散，但须与当前服务reference的过滤mask完全一致，不能只比较分布相近或最终text。

首个证伪覆盖本模型V248320、M1/8/32/64；BF16网格/任意FP32、大量ties、-inf mask、温度非1导致离开网格、p0/p1/0.95、k1/20及k-only/p-only，graph capture后切换值域至少两次replay。小词表tie reference如与生产排序不同保持单列，不扩大支持范围。数值不一致则停止部署并定位，不能以fallback掩盖已选择路径的错误。

## 计时、晋级与回退

只用独立空闲设备，与原native过滤同输入、同clone开销做graph完整过滤计时，三组成对结果全部保留。整体流程>=1.05且语义验证通过后，才整理Gems库公共API/backend导出和Plugin既有patch接入。库API支持条件按dtype/layout/shape，平台特化由Gems选择；非目标形状保持现有正确路径。不将旧V151936加速比外推。

采样为高风险点，任何真实服务候选必须完成最小回归、两rank graph和正式GPQA>=0.8，然后无profiler同配置A/B/R。当前原型无服务补丁，进程退出即恢复；所有新增文件/补丁/命令与SHA保护回退保存远端本case。

## 外部产物

当前参考归档 `/public-flash/jinghao/qwen3-VL/20261012-qwen3vl-metax-sampling-migration/patches/op005-final-FlagGems-vllm.patch` 只读读取。当前案例根 `/public-flash/jinghao/qwen3.6-35B/20261013-qwen36-35b-metax-e2e-current`；执行前记录commands，raw结果置results，尚未发起原型算子测试。

## 原型结果与工程门禁

25项当前reference对拍/graph检查通过，mask差异0。M64/V248320三组成对完整graph过滤：BF16网格baseline中位15.4289ms、candidate2.81614ms，加速5.47878x；任意FP32约15.46/12.5463ms，1.23220x；温度0.7离开网格约15.1551/12.5498ms，1.20759x。双方clone成本相同。这只是独立算子结果；当前模型仍运行anchor。

目标仓库AGENTS/workflow要求G0–G7。已读取当前文件；其引用optimization.md实际不存在，记录限制，不运行安装/环境重构。此为复用已归档MetaX实现，仍补齐当前契约、公共导出、路由及测试。NVIDIA kernel/autotune不适用：新增API在非MetaX明确unsupported，没有NVIDIA实现；MetaX沿用已验证固定配置，暂不扩大调参，PR状态experimental/needs_revision。

### 项目真相表（私有候选落盘前）

| 字段 | 当前契约 |
|---|---|
| Current op | vLLM bc150f50 apply_top_k_top_p_pytorch；torch2.8 sort/softmax/cumsum/scatter 复合过滤；新Gems公共API apply_top_k_top_p |
| Editable | 本case未挂载私有目录的Gems API/backend/exports/tests/benchmark与Plugin MetaX patch；原服务暂不修改 |
| Read-only | 原vLLM、weights/tokenizer、当前服务/source anchor、冻结GPQA/性能reference与原始结果 |
| Build | private PYTHONPATH导入与py_compile，不重装包；build120s |
| Validation | native pytest单算子+Plugin路由+当前目标reference对拍，mask完全相同；600s预算 |
| Benchmark | 原生Benchmark.get_latency graph，完整过滤含相同clone，ms越低越好，3对全部保留；600s |
| Active set | M1/8/32/64、V248320、FP32 contiguous CUDA；网格/非网格/temperature0.7；k20/p0.95，边界另测 |
| Aggregation | 每shape/domain成对speedup中位，不把不同值域/阶段相加 |
| Profiler | 原prof-001有两rank trace；后续实际公共API/kernel命中，profiler时间不作收益 |
| Autotune | MetaX迁移固定配置豁免；无NVIDIA实现，generic unsupported；shape/mode边界继续受实测限制 |
| Fallback | Gems生产实现NO_TORCH_COMPUTE_FALLBACK；Plugin非目标metadata保留原PyTorch入口，不吞已选kernel错误；不关闭任何已有Gems算子 |

### Torch 对齐契约

| 字段 | 内容 |
|---|---|
| Reference | 当前bc150f50源码+目标torch2.8行为；[sort](https://docs.pytorch.org/docs/2.8/generated/torch.sort.html)、[cumsum](https://docs.pytorch.org/docs/2.8/generated/torch.cumsum.html)、[scatter](https://docs.pytorch.org/docs/2.8/generated/torch.Tensor.scatter_.html)；sort默认stable=False，不能宣称跨后端tie顺序承诺 |
| Backend | MetaX C550/MACA3.7.1.5/driver3.8.1/当前FlagTree；NV未测且APIunsupported |
| Inputs | 库M<=64、1<=V<=262144，FP32 CUDA contiguous；k可None或同设备contiguous int32/int64[M]且1<=k<=V，p可None或FP32[M]且0<=p<=1；Plugin初始仅V248320 |
| Output/alias | 同一logits tensor原地filter，未保留位置写-inf，dtype/device/shape不变；无新out参数 |
| Dtype/promotion | 生产FP32 logits，过滤概率与累计FP32；BF16网格仅设备端无损性成立时计数，不舍入任意FP32；其余dtype显式unsupported/Plugin保持原入口 |
| Semantics | top-k严格小于kth阈值，ties可能保留多于k项；top-p升序cdf<=1-p移除，保留至少一项；k/p参数不广播；finite和-inf mask至少一项finite为有效目标输入 |
| Exceptional values | signed zero/ties补充当前native测试；NaN/+inf/全-inf的参考行为另列诊断，未证明前不宣称支持；合法采样输入由上游验证，不加入同步读值host gate |
| Autograd | forward/inference only，不支持训练/梯度 |
| Unsupported | 元数据不支持在Gems抛NotImplementedError；不以Torch计算补洞；空M/双None只返回原对象 |
| Torch reference | 仅tests/benchmark可计算或clone；生产仅元数据、torch.empty/empty_like和无复制view，实际计算为Triton/Gems |

### 路径设计

| 路径 | 条件 | 实现/config | 验证/风险 |
|---|---|---|---|
| identity/empty | 双None或M0 | return同对象，无kernel | alias/空tensor |
| fast | 设备无损BF16网格检查通过 | counting+Gems cumsum/softmax+阈值mask，固定MetaX参数 | ties/边界/graph值域切换；非网格不可近似 |
| general FP32 | 检查失败 | 值排序radix/Gems JIT helper，8pass，精确键 | arbitrary-FP32/温度；Gems内部JIT接口为跨仓库依赖 |
| unsupported | dtype/layout/device/shape不支持 | 明确异常，no Torch compute fallback | metadata反例，NVgeneric路径 |
| Plugin fallback | 非目标geometry或不支持metadata | 原existing PyTorch sampler入口 | 非目标模型/平台默认不变；非候选收益 |

## 额外发现：辅助精度进度 regex

原score_progress.py比冻结原生RegexFilter多了结尾标点限制，会漏掉结尾只有字母的答案。只读原生filter对104题为87正确(83.65%)、旧辅助为77正确；差10题已记录docids。正式任务/filter/contract没有修改；本地进度工具修复和4项回归通过，总203项工具测试/3跳过，正式结论仍等198题原生结果。

外部：results/op-003-sampling-prototype.json、accuracy/anchor-native-progress.json、commands/op-003-candidate-payload.json。私有候选7文件补丁SHA ca1a2c18d425478b10dca6f5788bab876054f5dcf0d1a94e0d73486555bad23f，尚未部署。

## 历史精度阻碍与决定（30000上限旧轮，现已由65536达标gate解除）

原服务未改动，完整GPQA strict-match为149/198=75.2525%，低于冻结0.8；198唯一题及两个filter/结果provenance验证通过，未签发gate。本点候选未进入当前服务，不能归因于尚未部署的优化。暂停新增性能改动，先按inference-accuracy-diagnosis核验。API原生198响应中30个finish_reason=length且completion_tokens=30000，其中25没有原生answer标记；168个正常stop都有标记。这支持输出预算阻碍，但尚未证明扩展预算会达到80，不把健康症状单独当作score失败规则。

当前新65536预算proposal只改max_gen_toks，保留全部198/严格metric/0.8/其他采样/模型source。两次provenance一致、命令和contract已准备，尚未执行；等待用户确认变更已冻结契约。原低分及所有历史原始数据保留。额外发现12题选项被原生helper去括号改写、171题出现重复选项；未自行改helper/filter/数据。

证据：远端accuracy/anchor-failure-evidence.json、anchor-output-budget-diagnosis.json、anchor-evaluation-diagnosis.json；proposal见accuracy/proposed-g64k-{config,contract}.json和commands/proposed-g64k-full-command.json。

acc-001：私有API接入补充signed-zero对当前native参考12416 mask差异；只在_order_key中将两种零sign归一化，四batch×五域20对拍差异0。原私有失败/旧source仍保留。后续实际hook graph验证时GPU0被另一VLLM worker占用，停止的仅本任务精确进程，未动任何服务；原生stop证据为manifests/op-003-private-stop.json。因此graph和post-fix性能incomplete，未接受候选。服务FlagGems白名单/启用及MoEbuffer复用全部保持。

2026-10-14：用户批准65536精度预算并明确允许30分钟后台跟进。原服务新full GPQA UUID26ffe88dd2554513a85a711849d56d63已运行；本候选仍未部署，不进行并发GPU实验，完整精度gate达标后恢复私有signed-zero修复的graph/边界与实际hook验证。

2026-10-14 11:09 CST：65536正式全量164/198=82.8283%，原生证据和服务连续性通过，gate签发/check成功（accuracy/g64k-accuracy-gate-20261014.json）。acc-002原基线精度阻碍解除；保留旧30000失败，不能仅凭随机复测证明所有答案变化来自预算。先恢复私有op003最小回归，不直接部署或宣称性能提升。资源策略：可在目标服务无请求时借GPU6做私有数值/graph验证，驻留模型仍占显存，结果只作为正确性证据；不据此接受新的独占设备性能结果。

同日恢复检查：目标GPU6只有本任务模型worker驻留、util0、API无请求，私有实际hook20项数值检查全等。graph预热再次停滞（打印actual-hook graph warmup后无进度、私有进程futex、GPU util0），因此不能再将旧GPU0冲突作为充分根因。仅停止私有进程，原服务未动；保留results/op-003-private-graph-20261014.json与manifests/op-003-private-graph-stop-20261014.json。新commands/debug-private-graph-20261014.py对每步stream/candidate/capture标记并定时dump Python栈，180s预算，尚未部署候选。

最小控制结果：将torch.cuda.Stream()前移到任何张量/候选调用之前仍停滞；faulthandler主线程为torch/cuda/streams.py:37，驱动重复mxkwCreateQueueBlock ioctl create queue block timeout。可确认失败边界为原生stream/队列创建，而不是此次Gems kernel执行；资源耗尽仍为待隔离证明的假设。所有私有GPU进程已精确停止。先完成达标anchor的P1K baseline003（无profiler、同既有3warm/3meas/5%稳态），再在资源隔离条件下验证graph，禁止并发设备实验或为此关闭Gems。

2026-10-14 CPU静态工程审查：私有标准tests的reference使用`flag_gems.use_gems()`全量ATen注册，与真实服务冻结白名单及native sort不一致。标准数值oracle与实际hook集成oracle应明确分开并分别冻结；已有20actualhook检查仍有效，未把未执行的标准tests判为通过。MetaX patch直接依赖新公共API符号，须补依赖能力兼容；所选kernel错误不得静默fallback。标准benchmark、非目标平台硬件测试skip及NaN/+inf/全-inf边界、post-fix graph/timing仍缺。仅审查准备快照（test SHA a113717292921bc081c03edcfbb2bf6581d9a27c95bba56773c70138659c08f8，plugin SHA 1c136e277c96b3f604d650f5157d48c54d7b7075e5005cbdc76942aa977ff208），本轮未修改私有或真实服务源码。

2026-10-14用户明确回复“允许短暂停服务，验证后恢复”。原始baseline/profile全部已退出，新CPUobserver未执行。准备一次8010精确PID828361/birth483795748临时停止以释放GPU6/7，容器与其他任务不动；private graph timeout180s，失败亦finally恢复原args、cwd、完整env（仅内存传递，不落完整环境）；readiness600s。不部署任何源码。随后C1/C8固定doc0..7、诊断输出64，当前两rank实际graph32token>=2replay，源/配置/设备/镜像一致性核验和原生precision rebind/check；原164/198是被复用的实测分数，不是新评测。已准备commands及SHA：{'validate-isolated-sampling-graph-20261014.py': '0e8ac8a19b804ad1646a2d9953359f4e036bcafd597c3114cddcf478ecd165ec', 'isolated-graph-lifecycle-20261014.py': 'ef1823688dee44ff966c0fb7c7bc306edcd90145040150c4bd3bdb7805fb8154', 'launch-isolated-graph-20261014.py': '9969e78c57a3a1bc123bb36c2521f321d72bc9df7c5518f8b6a6e619bcbb404c', 'rebind-restored-anchor-20261014.py': 'ac7e8a5c984fa6b379bb91b26ea73d38135a227937ecffa1f14745452180f325', 'prepare-approved-graph-isolation-20261014.py': '8e9e47054ced9efd58d1ffff6d076e9533dca037a760a72d1b51fbfb6ff58553'}。未开始停服务。

2026-10-14资源隔离终态：仅旧API828361正常SIGTERM及自然退出关联worker，GPU6/7空闲后私有same backend535fe4bd/plugin1c136e27实际hook20数值+4域各2replay共28项全等，private进程902367已退出；结果SHA10ffb16f24f450685f078ea4cfbb5d6f9c0823e732ad7ab95d682ee59ffc8303。默认/新增Stream与capture在释放本服务资源后通过，支持资源压力关联；不能区分显存与queue-count，也不能解释原无profiler停顿。没有部署源码/关闭Gems/操作其他负载，post-fix standardmicroperf及E2E仍not_run。

原服务按完全相同args/cwd/env恢复，05:16:20停止→05:21:06ready，285.98s；新namespacePID905636/birth489464369，TP0/1 namespace906181/906182（host83365/83366,birth489470994）。C1/C8固定doc0..7 health全部passed，两rank各64实际mcGraphLaunch；4repo12249文件/权重清单/原启动和环境连续性passed、profilerOFF/API0。原生acceptance rebind/check原schema3通过，schema4新gate SHA161d7ffaf02ba451b36255fc3ec318c342d64302fbc441212c598a8567c0353e，复用原UUID26ffe...164/198分数，不是新评测，也不适用于未来改代码候选。旧manifest/hash/PID证据保持不变。

review-004：先补API兼容/标准tests和benchmark准备、支持边界；再低开销观测新实例P1K集中暂停。所有E2E/正式四场景仍未通过，无保留优化或累计收益。精度新绑定路径accuracy/restored-anchor-accuracy-gate-20261014.json，服务manifests/restored-anchor-service-20261014.json；完整终态results/graph-isolation-restoration-final-20261014.json。

2026-10-14 engineering-v4实施前设计：公共`supports_apply_top_k_top_p`使用既有runtime backend replacement，不进入ATen `_FULL_CONFIG`；平台后端集中metadata条件，Plugin只按callable能力query调用公共API，旧Gems缺符号/真正缺包保留现有MetaX PyTorch入口，transitive依赖错误、能力query错误与已选kernel错误均上抛。非identity覆盖收紧至当前实测V248320/M1..64/FP32 contiguous CUDA/inference，空batch和双None保持别名；小V native tie顺序未证明因此排除，NaN/+inf/全masked无有效值输入不在承诺内，不加host同步读值。没有改变kernel算法或采样参数。

标准tests分开纯Torch与冻结服务白名单reference（不启用Gems sort），加入目标geometry、k/p边界/metadata/alias/graph域切换；标准benchmark使用原生Benchmark graph模式、双方相同clone、M1/8/32/64×网格/FP32/temperature0.7×两个oracle×3paired trials。该测试矩阵是待执行契约，不是新的通过报告。7个CPU mock测试已覆盖新/旧/缺失API、transitive missing、支持边界、非目标generic、重复hook和执行错误传播；只证明路由/导入隔离。仅改私有副本，先保存逐文件旧SHA和tar回退，真实服务源/gate保持原状；新版本仍需目标数值/actualhook/graph>=2、标准benchmark及部署后的完整GPQA。

准备执行命令`commands/apply-op003-engineering-v4-20261014.py` SHA55f30b0d9adbb049ecfb3e3de7c7d5bf70ae947fda1db33707758d0c8903abcf，冻结payload SHAfb5f3d74f12d69feea34ad0cbe3169669ef35793fa376d9820ba2ef2223a6213；source读取命令SHA277c95eae9a0b43bd28b3371fc8c6a1f0b0a9511939c92b1ee0a7b7dee1b8943。

engineering-v4私有落盘后：远端7个CPU mock检查passed，当前backend SHA c4b07fb0852fd3cac4dbc8e444758f65d03e28162a0c53cb8eae36e6c4826b9b，plugin SHA7a3129406f669f22147a3edd3ae8fe0fbce1daadc080438ee66ce450f1324e21。回退tar SHA1946d73a0038b878533c8d703fd1236f9f94303bc0a49e70b0247745133f21a7，增量patch SHA4e82905fbfb16c1dd3b804bf3496f0b1b97207c7aa081e064ebbb9b3ef78a336。black/isort/flake8在当前环境不存在，标准CI/lint待执行；未安装全局依赖。新源不继承旧28项graph通过。下一步默认stream私有GPU6数值检查，仅在当前anchor实例/12249源文件/有效gate/APIidle/只有自己worker通过后启动，180s预算并仅精确停止私有进程；不创建Stream、不profile、不进行性能计时。命令SHA bb6aa20e368d0e6c7f7aec5d6a14e6c8e6354ed5cae08b748b543b97818253f1/27d2374f7e6e02b8aa640af66fba0889deabd988be4aa487c6df9dc4e07db892，结果计划results/op003-v4-numeric-20261014.json。

2026-10-14 06:28UTC工程与数值终态：新私有公共API/backend helper实际import及MetaX分发命中通过，capability helper未误入ATen `_FULL_CONFIG`。GPU6在原model驻留/APIidle条件下默认stream完成70项（68数值+2empty alias）；纯Torch和冻结服务白名单各35项，全`torch.equal`且mask差异0，原地返回同对象。覆盖M1/8/32/64、BF16网格、任意FP32、signed-zero、ties、-inf mask、temperature0.7及k-only/p-only、k1/V、p0/1边界。不将`torch.equal`扩张为sign-zero位级证明。没有创建Stream或做timing，标准完整pytest矩阵/新源graph>=2/独占benchmark仍待执行。

数值结果`results/op003-v4-numeric-v2-20261014.json` SHA4f3ee3ff7e05d958a7437659ca2454b0ab0d1b502e32db66905717b976de66c2；终态SHA9b2feccda813996e426218684ead85ba763c7460aebf5211e25753800ea61608，hostcontroller156048/private911981均退出，原905636/birth489464369和GPU6/7原workers保持/APIidle。执行validator SHAe6e8fae71731e64e7a1601461881daa6746e070f8e76b177d5555f81840f24ed、controller SHA51fa01c649e02f08e7297b0b595aaa59654ec734480f355675c1e532611ed598、可复用只读monitor SHA65886a9e75254800c9e2379878487d05a9bce5d8d4c5d01ae85f95dc4686e123。静态审计库host Torch调用只有11处empty/empty_like分配，no compute fallback；`--mode cudagraph`已核原生CLI。

保留3次校验控制面失败：native gate-check成功文本被误按JSON解析（未启动私有GPU）、恢复manifest字段错读（import成功，0数值输入）、文件名重复v2后缀（exit2未打开validator）；均修复于新唯一脚本/回执，无数值差异、无服务变更，不归因算子或精度下降。完整black/isort/flake8缺失未安装，full CI待执行，CPU测试2个超120行待整理。新候选仍未部署，原82.8283% anchor gate有效且不为新候选提供精度验收，acceptance继续incomplete；旧局部5.48x不算本版或E2E收益。

2026-10-14 engineering-v4.1（实施前）：案例本地临时venv安装仓库指定black24.8/isort5.12/flake8 7.1，只对当前私有候选8文件执行format/lint检查并passed，不改变模型容器依赖/全局环境。需落5个import/format文件，kernel backend与Plugin SHA完全不变；CPUmock7本地再通过。不是完整repo precommit，也不继承graph通过。先旧SHA核验/tar回退，再私有落盘与native标准非graph tests。payload SHA845a46be19e56becdbe415b7f89b00a572c14f4db37d2ba9212705ab09ae1cc1、apply SHA4623bd11490411a7d72664f4fb7dab99ac4a8ea4fead0a9af85a3151a5bd39a6。

工程v4.1标准验证契约：使用private真实Gems import/MetaX分发和原生pytest，`tests/test_top_k_top_p.py -k 'not graph'`，预计182非graph项；2个graph明确deselected，避免在同一驻留资源状态重复Stream。GPU6/anchoridle、600s、同源68数值历史保留，新测试包含pureTorch/服务参考、所有4batch×6域×3filters及36k/p边界、元数据/empty/alias/generic。仅对比值/过滤mask，未计时，不是E2E或完整graph通过。测试SHA4933715d36f39c956725f995b1bedc427d3b008ed779def35a97ec034bde47e4、controller SHAdb14c9017bfca06601dbbd3d087045a130ca3036e284e0d3dd87bd7004d3661e；执行前核12249anchor文件/精确实例/gate/闲卡资源，失败冻结并诊断，超时只精确停止私有。

acc-003（06:42UTC）标准非graph182项实测174passed/8failed/2graphdeselected，非harness错误。全部8项为p-only、M32/64、bf16/masked域、Torch/service两个reference均差异；所有kp/k-only和其他域通过。旧70项仅在M1测p-only，不能推广API全部边界。真实MetaX路径import证明通过；private916089退出，未部署/未改变8010服务。按inference-accuracy-diagnosis冻结失败并暂停新性能/候选晋级；先同seed19/M32/V248320/bf16/kNone/p.95分解sortedvalue/CDF firstkeep/tie index，再决定必要修复或回退，不能事后删除p-only测试/放宽mask标准。现有anchor82.8283%gate仍有效。JUnit SHA793dfef38b908b446a605a744af35d9bc4703e9d7997c0556d6c29fe5febdf4c、terminal results/op003-v41-standard-terminal-20261014.json；rootcause尚unknown。

acc003阶段证伪冻结：同M32/V248320/seed19/bf16/kNone/p.95，每oracle2次重复。保存synthetic失败input于accuracy，分解native sorted values/indices与计数sorted values、native/Gems softmax、Gems cumsum in-place/out-of-place、first_keep向量和阈值tie原始index序；仅诊断不同阶段对mask的贡献，不改源码、不放宽契约、不测性能。source/backend及publichook命中必须同v4.1；GPU6默认stream/当前anchoridle/240s，源/实例/gate核验后执行。script SHAf9fa75abcb205965b8afc28de86bd49f6e7c4b6f086603b98f437d2f2d16c8b0，controller SHA35fe0ba5ad995a868902e3720b7c96d4a9da81794348a78dd7d16b9b4c25787d。rootcause尚待证据。

acc003首个阶段诊断：同冻结M32 BF16，两个oracle各2次均1个token maskdiff，row16/token87922，排序值全等/tie原序一致，Gems in/out CDF全等；原Torch无out手工CDF cutoff64400、Gems64401差1。service无out手工CDF与Gems相同却仍不能解释真实reference输出，已核真实vLLM使用`torch.cumsum(...,out=probs_sort)`，原阶段不能把不同out变体当作同一路径，不把alias判为根因。复现input SHA4c8f53ea5ee5b054dc1cce437c7310fc0e3f3326f3c357dc3698198c4d3230cd，stage结果SHA453c32f76fac5449df56f29ddfa0a6933cbae92b7601c8885feecd0acfbee047。补真out诊断：同input、真nativeout、GemsFP32与FP64后FP32round仅诊断，检查已注册cumsum项，不改生产实现、不做performance。新command SHA02043712a13969de4996d5a60e4dfb36be493c8b5597bd2e40d5b8936341a3fa/controller SHAb61b58e2344b265bbfd082b5994681509b1086806505afb0175a9483c182971d。

acc003真out终态：同冻结input，两oracle各2次public仍1token差异；真实native`torch.cumsum(...,out=alias)`prefix firstkeep64400，Gems累计64401。换真实nativeoutCDF到同candidate后半mask阶段差异0，保持GemsCDF差异1；sortedvalues/tie原序一致，CDFin/outalias一致，定位到累计算子实现边界。服务白名单只注册`cumsum`，不含out变体；不能用无out手工CDF冒充实际reference。outputdtypeFP64结果未改善，当前Gems按inputdtype选acc_type，不是已证明FP64累计的修复。

结果accuracy/acc003-nativeout-diagnosis-20261014.json SHAd5416ae82a4ed0e0707711d22066c6123ccd684a4c934093234236c3b4424cbb、terminal SHA68af68ad3c06148c0d5501366850b90a34431039b5b91447050e1e27267ecddc；private920726和host215282均退出，原905636/APIidle/GPU6/7原workers保持。当前FlagGems cumsum源SHAef7f010fdc53b3eacef469326bffd030c961887e5fa0ec1c71f861a62793a502，安装Torch ScanUtils.cuh SHAcad3f457a58a38043ff547821abb29fdb5fabe489e7edeff8dc5d9ec494e59ac。Torch头文件M>1内层逐blockcarry先加到首元素再Sklansky scan，M1为CUB路径；Gems多块prefix采用不同加法树（inputF32指定FP64输出未改变acc）。下一步用相同prob输入做Gems/Triton数学次序试验，源码机制仍待实际输出证明，不直接把安装头文件当binary执行证明。

review005：候选晋级/新performance暂停，首要acc003数值修复（不可删p-only测试/加epsilon/放宽mask/缩白名单或改Torch生产fallback），次要CPUobs已准备但0性能请求，第三MoE实际routing deferred。没有部署或新的E2E收益，正式acceptance incomplete；新源还须原182+graph>=2、标准benchmark、高风险候选fullGPQA。

acc003算术试验实施前：不改任何repo，仅进程私有Triton row scan（BLOCK1024=2×Torch当前512 threads_x）、每块carry先加首元素、10级Sklansky，然后输出/取末元素carry；numwarps4，禁止改变数值加法树的autotune。输入是同SHA冻结M32/BF16/seed19，以同Gems概率tensor分别算真nativeout和试验CDF，对整个CDF严格torch.equal各oracle2次，并仅在独立进程临时接管cumsum_out做实际hook A/B/A（原实现→trial→恢复原实现）。不添加epsilon、不改变支持范围、无Torch计算生产fallback、无性能计时/graph/服务更改；实际CUDA dispatch table记录确认cumsum与out是否命中不同注册。command SHA5a2307313a3a28d22f58fdf26ee5e96bd2c165289ed747fc08701e0988afc02d，controller SHA76f41e408ee388cdb0410fa674f9fda03679cb9bb0e2f867d72a4b2be8391dbb，240s预算。

07:13UTC acc003算术trial结果：两个oracle各2次整个CDF torch.equal、max_abs0；实际hook两次maskdiff0；原实现→trial→恢复原实现严格A/B/A前后都是1diff，原输出前后一致。实际CUDA表证明white上下文cumsum为/dev/null:51，而cumsum.out仍RegisterCUDA_0.cpp:8524，早先仅函数列表推论现在有dispatch证明。trial source/resultSHAe3b849ad7059e5782a43390b54e6dd93a98fbcffefab423744409cf9da6fd52b、terminal SHAb2c147445b17f0b949ce66efc8aad6fe5accb11f1ef97948c1ea675f26d3ad71，private921962/host249983退出，未改库文件或模型service。机制已隔离到scan加法树；尚不是完整修复验收。

准备privatev4.2：只在Gems-vllm MetaX采样backend加FP32 row scan M>1，固定1024（512×2）Sklansky/carry-before-scan；M1保留不同CUB参考路径的既有Gems实现。维持支持范围/采样参数/所有失败测试，非Torchcompute、非vendor绕过，不改Plugin或服务。shape固定V248320、M<=64，autotune不可改变数值BLOCK/tree；generic/NV实现不动且硬件未测。kernel本地black/isort/flake8 passed，beforeSHAc4b07fb...afterSHA6d07cbc64ec94aa66b938590f1dd5605ba378bd9e06fee665a7423f5ddccfad3。先单文件回退snapshot/patch再落盘，原182必须复测并加CDF/M边界，graph至少2和原生microperf仍后续，不将trial当新源graph验证。payloadSHAfb136fa0d8d80fedd032f177186cb250a914621d451d35c70647d88795ba8954/applySHA8bba251529a48d4a1e15b18fd9024a781f2e8a03f6cfa543facc9bc0df641922。

privatev4.2单文件修复落盘/CPUmock7passed，回退oldbackend保存patches/op003-v42-before-backend-20261014.py SHA同c4b...，增量patch SHA8aafe84342997eb16fe0941d24e16a1c29e0fc0d2ac1ecd9d921e55d9a229a08。下一步完全不改原tests SHAe507...，同原182非graph范围/2graph明确deselected/600s重新原生pytest；新唯一script SHAe6eceb2e9cafaea3c6d61f9161a7aa865f210848064a2f86f163f94f1cd15bf3/controller SHAca997d92fb2eb5347e66151554311c13a7aab13cef7ad03b409a0c1eee2fcbf7。未进入真实service，未测performance，graph新源仍待验证。

### 2026-10-14 07:29 UTC：v4.2 原 182 项非 graph 回归全部通过

保持测试文件 e5078804… 和完整范围不变，native pytest 为 182 passed、0 failed/error、2 graph deselected。JUnit SHA `d0182c4f4eb2f6f8a22f9ae141105cbab9335abf05ed753d8215b3bba65e8be3`；原 v4.1 的 8 个失败保留，未放宽 mask 或加入 epsilon。新终态 `results/op003-v42-standard-terminal-20261014.json` 核验 private/controller 已退出、私有 8 文件未漂移、API905636 原 birth 不变、GPU6/7 只含原 worker、API idle。新 read 命令 `commands/read-op003-v42-standard-terminal-20261014.py` SHA038b1ec7…，完整证据留远端。

数值修复已覆盖原非 graph 范围，整体 minimal-regression 仍 incomplete：补 M1/2/3/63、seed42/2026、逐行不同 k/p 与新 scan 同 probability 全 CDF 对照（两 oracle，300s），再新 source graph >=2 replay。下一步 commands/validate-op003-v42-boundaries-20261014.py 和 run-op003-v42-boundaries-20261014.py 已预记录 SHA；不创建新 Stream、不测 timing、不部署到当前服务。

### 2026-10-14 07:33 UTC：v4.2 扩展数值矩阵通过，review-006

新增132 checks = 96 actualhook 数值/alias检查 + 36 同概率完整CDF检查，覆盖 M1/2/3/63、seed42/2026、BF16/FP32/skew+masked、p-only/逐行不同 k/p、Torch和服务两oracle。全部torch.equal，CDF maxabs0；不是所有可能浮点输入的普遍证明，也不宣称signedzero按位相等。结果 `results/op003-v42-boundaries-20261014.json` SHA f79f790926b88b076164052f8a6dc4df14fb1efb48f9cf2085e332adbbad7684，终态 SHA e565913c7f7fa6461023d1e123b393e3b3909def86983697fdf7202a49149a77。controller/private均退出、当前905636/原GPU worker不变且idle。标准182终态文件远端实际SHA `88afe6183928ee6260564358b6e0fdf8d5859ce0db793f723cb30a8308ec8208`，不使用本地stdout末尾换行的hash替代。

review-006：原失败范围数值修复通过，整体minimal-regression仍incomplete；无生产源码改动和E2E收益。下一步为新source graph与标准microperf资格验证，随后才是实际部署/新fullGPQA/单变量E2E。若局部性能无价值，则延期采样候选，回到CPU全时间线诊断。旧535 source图验证不能证明新6d07修复。

新资源验证具体方案已准备，当前未获新中断授权、未执行。目标仅当前API905636/birth489464369关联进程和GPU6/7；私有GPU6总预算300s，先96 actualhook graph replay checks和原生2graph tests，再现有Benchmark类的 `--mode cudagraph --warmup 1000 --iter 100 --record json`（M1/8/32/64×3domains×2oracles×3paired，共72 shape pairs），不部署任何候选。失败/超预算只终止本次精确private进程并立即恢复原anchor。args/cwd完整env原样恢复（env只存内存/hash），readiness预算600s，预计服务中断10–15min；超过恢复预算报告并保留恢复进程，不再次重启。之后C1/C8及当前两rank graph>=2、源码/权重/镜像/挂载连续性核验、使用原schema3 sourcegate进行native rebind/check；不是新GPQA分数。原已批准并执行的资源窗口已结束，本方案是一次新的独立窗口，需要用户明确授权。

用户明确回复“允许本次验证窗口，完成后恢复”。第一control preflight在任何模型signal之前因container mx-smi返回namespace906181/2而期望host83365/6失败；原905636/birth不变、private未启动。failed lifecycle930623已退出，精确host waiter318867由已保存命令仅SIGTERM清理，失败证据保留 results/op003-v42-isolation-preflight-failure-20261014.json。新v2控制计划/脚本独立保存，改用容器namespace worker ID；同一次已授权但尚未发生的窗口，无扩大范围，不重放旧creator或覆盖SHA。

2026-10-14 07:46 UTC：已授权v2窗口在M32/FP32/seed42/pOnly .95/Torchoracle第一replay发现1maskdiff。26checks通过、27th失败；不能用原182/扩展132通过覆盖新失败。native2graphpytest和standardbenchmark按失败前置规则均未运行。失败冻结为acc003新边界，尚不能断定graph特有；验证脚本finally正在原args/env/source恢复anchor。恢复/新绑定完成后先同生成代码和seed冻结输入，用默认stream比较reference/public/实际hook与softmax/CDF/mask阶段，不在model驻留时创建Stream，不启动新性能优化。

2026-10-14 07:52 UTC 恢复终态：中断272.257963s（07:45:43→07:50:15），当前API933303/birth490360029，TP0GPU6 host324535/ns933842、TP1GPU7 host324536/ns933843，workerbirth490366638。原args/cwd/完整env精确恢复、production12249文件/weights/镜像/两bind mount不变、API idle/profilerOFF，private及两尝试controller全退出。新C1/C8通过、两TP各64graphLaunch，native originalschema3→schema4 rebind/check成功。service SHAfe9d33fd…，runtime6eb25c4f…，currentgate accuracy/v42-restored-anchor-accuracy-gate-20261014.json SHA8e691c5a08bc527a53cab569e0389898525c8e30b0f702df609eb57c5a2f2fbb，复用原164/198而非新分数。最终 results/op003-v42-restoration-final-20261014.json SHAfed30e3ed203b33ad2d29811023ba542c6bb7792be556c0467d341e8d59a20bc；private graph失败SHAcafe8039…保留，未benchmark/部署。此次许可单窗已完成，不能再次重放或扩展未来中断。

下一步已预记录同generator seed42/M32FP32新输入 defaultstream 阶段诊断命令及SHA：只freeze synthetictensor、两oracle各2repeat，比较sortedvalues、native/Gems softmax、同probability修复scan与trueoutCDF、下游同一mask、两reference是否自身一致；300s，GPU6默认stream，不创建新Stream或做graph/timing/source改动。

2026-10-14 07:56 UTC：新输入差异在默认stream稳定复现，排除“graph专属”解释。冻结 accuracy/acc003-seed42-m32-fp32-input-20261014.pt SHAbe9be18d257b9b18e2897bcf09af12ff4ff911a0ab32b0557335f8f8181ad06f。Torch ref对candidate两次1diff，service ref对candidate两次0diff；两ref自身1diff。row26/token201366，Torch/Gems softmax maxabs5.82e-11，使CDF边界0.05000001937 vs0.05000001192；给相同probability的新scan与true nativeout CDF完整相等，maxabs0，服务probability也相同。下游同mask用nativeCDF0diff/用candidateCDF对Torch1diff，对service0diff；candidate与自身stage完全相同。诊断结果SHA21ae42499d273d9655ff06d1f1358418cec8c130742742a443942594896f37e7，终态0f336497d4cd314b1f5cdea538992a53d2083889a31d2667930e8d14009d9e0b；host/private退出、原933303/birth与GPU324535/6不变/idle。

用户明确回复“以当前服务原路径一致为准，保留裸 Torch 对照”。因此单独冻结数值契约v2：actualservice原sampler+完整whitelist逐元素一致为数值回归准则；裸Torch对照保留，原失败/差异不重判或删除，没有epsilon/缩p-only/删shape。完整GPQA仍198/65536/80及其余采样不变。新graph验证按服务ref断言，同时记录bare/context ref的maskdiff；kernel/plugin/source/test文件不改。旧pure-contract graph仍failed，新契约结果另存，不用新口径伪造旧通过。

补齐剩余graph matrix与nativebenchmark的qualification3方案/脚本已准备，计划SHA4ce8e9542532b1e9772fd0d691a663380cb480964b3881eed23eea578cbaab8b；该计划只提议新的单次资源窗口、未停服、未获窗口许可。原已批准v2窗口已完成，不能因为用户确认参考标准而推定再停服务授权。candidate整体资格仍incomplete，未部署、无E2E收益。

### qualification3 终态与 review-007（2026-10-14）

用户批准的实际服务 reference 契约下，96 actualhook graph checks（含完整两次replay）及原生2graph pytest均通过；JUnit SHAed3dffab1d552f2eca7d48e498eee707c583678dd523385215753b3118490165。bareTorch差异保留为M32/M64 FP32 pOnly各2replay、各1token；服务reference0diff，不改旧pure-contract失败。

300s private预算到后按约结束，仅完成13/18 case、52/72 shape pairs；原生benchmarkJSON/XML未生成，整体timing incomplete，不挑完成子集作为通过或E2E收益。全部52打印值和5缺失case由CPU解析保存 results/op003-v42-qualification3-partial-analysis-20261014.json SHA5f0024204c7bdcc4f45ed63fb3122ac5a9b4813e07a3335670ed9cb86db1fe7e。两次已测service M1 FP32参考0.292194/0.292981ms、候选0.809513/0.809489ms；temperature.7也退化，不部署该通用候选。BF16大batch较快仅是局部诊断，未构成完整microperf资格，更非E2E收益。

原8010已恢复（中断497.729322s，08:09:47→08:18:05UTC），当前API944104/birth490527206，TP0physical6 host375983/ns944643、TP1physical7 host375984/ns944644，workerbirth490533732。args/cwd/全env精确恢复、12249源码/权重/镜像/挂载不变、profilerOFF/APIidle、所有private/controller退出。C1/C8与两rank各64graphLaunch通过，native原schema3→新schema4 rebind/check通过。当前gate accuracy/q3-restored-anchor-accuracy-gate-20261014.json SHA888ce37bcfa48e5d6c01d562c3e552227ed804311d075c9dced99e0cdebcc9de；servicea5ef8d44…、runtime250732c5…；最终results/op003-v42-qualification3-restoration-final-20261014.json SHA60e6ec18142a646119930c5c984d3ed90862ca0fc3b276b9d6916cb1e847c265。复用原164/198，不称新GPQA；本窗口已结束，不重放或扩展未来中断。

review-007：精度数值定位对已测实际服务范围已完成，当前无部署变更/累计E2E收益。采样候选延期，优先重建当前944104原生P1K全时间线CPU/调度/driver等待观测，保持原3warm/window3<=5%契约与全部轮；private采样第二优先修M1普通FP32成本，并在独立预冻结预算补全standardbenchmark，不通过关闭FG或vendor/native绕过获取收益。真实候选部署仍需full198/65536/80。

2026-10-16 review027 current-source follow-up: prof003 postforward CPU/GPU Externalid proves aten::scatter_ FP32[64,248320],24capturedcalls192.203/190.949ms totals; slowcalls~10ms. Current Plugin vendor/metax/patches/topk_topp_sampler.py SHA347cd1353bdd485a75b089db6148ec9c15caf0f7bfde758b43a371e0e4179af7 unconditionally redirects apply_top_k_top_p to PyTorch implementation because historical Triton failure. This fresh result reconfirms historicalop003 mechanism under newsource/script19/cache; no new sampler implementation or GPU sampling test has run. Artifact results/prof003-postforward-sampling-20261016.json SHA709a546cff14a279055ed6fc2b39fe0980ccccbed4baa78d37136973ea838619; CPU incremental dependency audit results/op003-current-scope-transfer-audit-20261016.json SHA0e7a7b44a2266c99af000666977cf5ed55fc18b3b0cf9a4f5b73c454463a0dd6. Current service API1025146/TP6,7 exactbirth and APIidle reconfirmed, no sourcechange.

Highest next priority is existing op003 current-scope variant, not a duplicate optimization ID: migrate only necessary MetaX top_k_top_p backend + small existing-boundary adapter into private current baseline; legacy backend6d07cbc64ec94aa66b938590f1dd5605ba378bd9e06fee665a7423f5ddccfad3 read-only reference. NEVER switch whole old private package/PYTHONPATH and lose GDN/attention/userMoE changes. Exact M64 FP32/V248320 metadata gate keeps old slowM1 originalcurrentfallback, withM1 sentinel and historicalnegative preserved. No library production edits or whitelistscope changes. First freeze current generationk/p and true reference/finite-value/tie/CDF/alias contract; old182/132/graph andpartialBF16fastrows do not qualify newsource. Then fresh current17ATen-FG reference numerics, fullnativebench acrossall declaredtarget/fallback rows, >=2graph, newfull198/.8 and sameP1KMixedA/B/R before retention. No automatic newStream under modelresident pressure or any future service interruption from old authorization.

### 当前 scope 的私有增量前契约核验（2026-10-16）

先执行纯 CPU 只读脚本 `ROOT/commands/inspect-op003-current-contract-source-20261016.py`，SHA `03bb132a143667e90cf4fa0754c099946d1239b1ce3772a7d3480af2b39ae209`，保存 generation_config、原生 P1K sampling 参数来源、完整旧采样函数和当前参考路径。无生成/benchmark/部署/重启；先冻结支持语义与参考后再制作私有增量。

CPU 契约读取 v1 因当前 vLLM 无旧路径 `entrypoints/openai/serving_engine.py` 退出，未创建结果、未初始化 GPU。保留失败；v2 仅把不存在路径显式记 missing，不推断旧路径存在。新脚本 `commands/inspect-op003-current-contract-source-v2-20261016.py` SHA `ff7bcb3e58a081f7556b8cfca826199890f3b4bd122b52593dcf29fe318db100`，新结果路径 `results/op003-current-contract-source-v2-20261016.json`。

#### 当前 M64 私有增量编码前契约

| 项目真相 | 冻结内容 |
| --- | --- |
| 目标/证据 | op003；FP32[64,248320] post-forward采样/scatter，父场景P1K Mixed |
| 可写/只读 | 仅ROOT/private/op003_script19_m64新命名空间；生产四repo、当前参考、旧私有包只读 |
| 构建/验证 | AST+当前包导入；默认stream精确mask/存活值/alias、metadata/fallback/CDF边界；600s预算 |
| 性能/聚合 | 后续原生kernel/operator全部预冻行；current/candidate，primary median>=1.05、逐行>=.95、M1 sentinel；未测 |
| 环境/Profiler | 当前source12355/API1025146/19FG；prof003既有证据，不新采集 |
| autotune | MetaX历史算术原样；CDF tree/block1024/warps4为语义不调参；NV不支持/未测 |

| 对齐契约 | 冻结内容 |
| --- | --- |
| 输入/API | 当前vLLM apply_top_k_top_p_pytorch；FP32 contiguous CUDA[64,248320]；k int32/64[64]1..V，p FP32[64]0..1 |
| 输出/累加 | 原位alias，排除置-inf、存活值逐bit保持；FP32softmax/CDF。实际17ATen FG原路径oracle，裸Torch仅诊断 |
| 语义/边界 | tie/signed-zero/-inf精确；forward-only。NaN/+Inf/all-masked未知、私有域外，生产晋级阻塞；不承诺metadata能判断值 |
| Torch边界 | Gems仅metadata/empty分配，无Torch计算fallback；Plugin未选中时沿用当前原参考 |

| 路径 | 条件/行为 |
| --- | --- |
| identity | k/p均None返回同tensor |
| fast/special | 仅M64 FP32 V248320，计数或values radix；kernel计算体原样 |
| M1/general | Gems拒绝，Plugin当前原路径；M1数值/性能sentinel |
| exceptional | 待诊断，不用于生产，不吞selected异常 |
| exports/graph | 仅新私有命名空间、导入当前GDN/attention/MoE；公共接入未完成。resident资源下不再盲建Stream；晋级前>=2replay |

CPU creator `commands/prepare-op003-script19-m64-private-20261016.py` SHA `2ce13be3f6f552a73be4cdb66e519a4bada8cd1ebc43a4a4834aa07e9287f2f6` 保存计划/dirty/原文件/差异，不初始化GPU/部署/重启。执行前本地AST发现嵌套引号错误已修，无远端执行或输出。旧负面与不完整结果保留。

当前私有计划SHA `0fe7d3ef9b99b4699a722c9067329cb05308148304214ba44b0da015d8d57db4`，backendSHA `80529bc51de09b21d20658141b1672e6cde641df56353798e4b91fb5195cc4ee`，adapterSHA `d965a98b2f0f8c56f7be946bde8a299489125dcd472da76e0f2142587c3bf5e1`。模型generation_config及本次API启动日志共同证明默认k20/p.95；请求payload另核，不冒充live tensor hook。

最小数值脚本 `commands/test-op003-script19-m64-numeric-20261016.py` SHA `afec7d42b9e9e03f635b26a4327812b6ef5ac73e95ba985858a327407f22972e`：72有限域case、5fallback、3CDF临界值case、5metadata拒绝、identity及3异常值诊断；全部原始结果保留，任一有限域失败停止晋级。新launcher `commands/run-op003-script19-m64-numeric-20261016.py` SHA `13ab282e05241610cf196a24d6d88a68feccea502cd9cb968ff7e44e1532e8ca`，先fresh12355源/model/env/精确实例/gate/APIidle/GPU6独占核验；仅私有默认stream、600s/只停止自己客户端，后验生产连续性。无graph/newStream/服务请求/源码部署。

只读进度脚本 `commands/monitor-op003-script19-m64-numeric-20261016.py` SHA `9edf253663dba9d7b6a612fa803156703e21f5fd1713462a6f7c84c25acdf022`；读取唯一数值输出、精确controller及原生短日志，不发GPU/模型请求。数值launcher已dispatch，终态待核，不重复启动。

当前源最小数值已终态：72有限域+5fallback+3CDF边界=80case全逐bit一致，5metadata拒绝及identity通过；3异常probe nan-equal差异0，仍不是完整异常域支持证明。当前包GDN/MoE导出保持；裸Torch p-only有1token差异，按用户原契约保留为诊断，current17ATen oracle差异0。numericSHA `b234f2aeb529e4a5d8f554696e4c6631c3478e456ab1468bc16f32504a16fa37`，supervisorSHA `ed7fe659e621705f983ecde0b74c750a6ddc30ca566bbaadfbc2441b5249083b`；原controller已退出，12355源/env/model/精确服务连续/APIidle。continuity中graph22/profiler_off是历史字段，不能当新候选replay或live状态。

下一项为私有有限域原生microbenchmark（非E2E passed）：`commands/test_op003_script19_m64_benchmark_20261016.py` SHA `e4052c9176067d2425d067b8b04076162fd86279d87b7f1f0557a4df7abb01da`；新launcher `commands/run-op003-script19-m64-native-benchmark-20261016.py` SHA `7dc6429eda0cc9a87b4f38ebc3fa54984a0c3c9f27050135eee50164fcae2741`。kernel/operator各3seed×10case=30行，2mode共60行全部保留；M64 bf16-exact/generalFP32 k20/p.95为primary，k-only/p-only/ties/masked与M1/8/63/65为guard。每次timed transaction含相同clone-reset再完整filter，避免in-place多轮重复过滤污染。20mswarm/100msmeasure/300s每mode；primary每mode median>=1.05且每行>=.95；noGraph/newStream，先collect-only三test确认再原生Benchmark.run。source/gate/idle/GPU6fresh后才执行，负面/缺行/超时不丢弃或延长预算。

原生benchmark launcher已dispatch；只读monitor `commands/monitor-op003-script19-m64-native-20261016.py` SHA `47f0c77543cbf32016a39504fd7f6446ba1d1c76b66479c1d598e30c50281060` 仅读当前唯一kernel/operator精确进程与短日志；不发新GPU工作。终态未核前不重复测试。

纯CPU收齐校验脚本已准备 `commands/analyze-op003-script19-m64-native-20261016.py` SHA `20522c8474198cb8943850a6d9f729cef6c6f3b7b06279e526e536b683d3a8c7`，仅在唯一native supervisor终态成功后执行一次；检查原生JSON/XML/3pytest/30行每mode、tag和有限值，全部60行聚合，冻结primary/逐行guard。未执行，输出存在不可重放。

原生benchmark v1三组pytest失败，短日志为`current_transaction() missing required positional argument label`。kernel退出1/非timeout；operator未启动，生产连续性通过，保留JSON/XML/全部日志，不算性能退化。CPU新脚本 `commands/inspect-op003-native-harness-boundary-20261016.py` SHA `af39f2a8ee830d5629f0507cc692b4bdd87f42fac4b0dc41571bc7ef0727438b` 仅读实际Benchmark入参处理和失败原生JSON，先核0有效计时边界再决定工具修正；不重放v1。

CPU实际base.py:382-395证明字符串positional item被丢弃，dict会传kwargs，record_shapes保留dict标签。失败JSON只含3失败、0有效timing；artifact `results/op003-native-harness-boundary-20261016.json` SHA `cc360182be7c8a13597a80f027bd8c720ae76d40c12e02cb8c784187bb2909e2`。v2仅将yield的label换为`{label: label}`，不改实现/矩阵/阈值/预算。新benchmark SHA `5c7f9fb5426fb7ee19823dc24e1605e9b5d868c50b7abd038d4d8a21fccbe063`，launcher SHA `ff1cf865241041dd01dbaf69602e5a4094fc188c28b41798c4c3541464cbbb4e`，monitor SHA `3e23333e1e03500451128af112d40841ec725a6d363998088da691ee51934917`，analysis SHA `b0e409f035a5f60f9022862eb78fb07231e942047516eef4520718674707b532`；均commands下同名v2脚本，所有产物native-v2前缀，原v1保留。

v2在fresh全源/model连续性预检中退出：旧精度validator内的权重根 `/public-flash/models/Qwen3.6-35B-A3B` FileNotFoundError；没有v2原生plan/controller/results创建，0v2 GPU timing。禁止旁路gate，先只读诊断host/container目录、mount与精确API/TP进程。新CPU脚本 `commands/inspect-op003-model-path-disappearance-20261016.py` SHA `764eb658f2244ace6b47b6e83d927bdd4682cd298ffe94d4032993b8ee82d51a`，无源码/挂载/服务操作，不重放v2。

### review028：当前采样数值通过；原生性能未形成有效计时，权重目录缺失阻塞

- 私有当前源增量80组有限域/fallback/CDF逐bit一致，5metadata拒绝与identity通过。3异常probe相同仅诊断；裸Torch p-only 1token差异保留。M1仍当前原路径，当前包GDN/MoE导出未丢失。
- native v1三组失败源于harness丢字符串label，0有效计时；固定为dict kwargs的v2尚未运行GPU，即被fresh模型连续性检查拦住。所有失败保留，不归因kernel退化，不运行预备analysis或重放任何creator。
- 02:20:16Z只读同时确认Host/容器 `/public-flash/models/Qwen3.6-35B-A3B` 及config/generation_config不存在；父目录和NFS挂载仍存在，同名Qwen3.6子目录列表为空。父目录mtime02:13:24.726443Z只证明目录变动，不能推断操作者/删除或移动原因。
- 原API1025146/birth501435120及两个TP1025947/8/birth501445784仍活，API running/waiting=0/0。agent未改生产源码、权重、模型路径、挂载或服务；没有新模型生成/重启。没有声称路径缺失后新的health或模型精度通过。
- 事故 `identity-001-model-path-unavailable` 按本地[inference-accuracy-diagnosis](../../../../../skills/inference-accuracy-diagnosis/SKILL.md) 的identity/configuration drift处理：先恢复可比较model/manifest。历史GPQA164/198与gate文件不改判，但当前model/tokenizer绑定不可fresh核验，停止新性能工作。不是新的分数失败，不盲重跑GPQA。
- 证据ROOT/results/op003-model-path-disappearance-20261016.json SHA `c4fab0ce95ce7144f18e4af1e443b006109bef86e11348b06f78023736254402`。已请求用户确认是否移动并恢复原目录或给出真实新路径；不猜替代位置/建链接/下载权重/修改args。按既有“真正需人类时暂停”授权暂停automation。
- 当前累计E2E收益unknown；原P1K1132.941509tok/s场景入口baseline不代替A/B/R。Prefill仍早期有限trace，Decode-forward MoE配对方案已拒绝，post-forward采样数值有依据但性能未知，Mixed无新候选数据。P1K正式closure及后续三场景/最终精度仍incomplete。
- 恢复后先fresh全model/tokenizer/12355源/fullenv/精确实例/native gatecheck；若配置/实际模型/实例改变按契约执行新full/严格restart授权。然后新唯一安全native续接沿用已固定的60行契约，不重放v1/v2launcher。完整异常语义、graph>=2、公共增量设计/newfullGPQA/P1K MixedA/B/R全部待做。无未来停服授权。

用户明确回复“正在下载权重，还是这个目录”，随后回复“已经下载完了”。恢复只读核验，不能把目录存在当原权重相同；automation暂维持PAUSED直到门禁判断。新CPU脚本 `commands/inspect-op003-model-restored-20261016.py` SHA `113d36e86790b18be7997313f9de0f6aea73825a5e765ae2894dac023a1f1016` 读取原/现分片、配置/tokenizerSHA、index完整性、HF下载metadata并执行原始精确continuity（非完整terminal/issue）；不放宽mtime/模型绑定，不发GPU或模型请求，不重启。

下载恢复inspection SHA `d1ed27f350225bc3afbbac1376ba50e6e3256ae349b7cbf68d86f8bc4f118692`：35记录/26shard齐全、所有已冻结非权重SHA一致、分片size一致，但mtime改变，原strictcontinuity退出1，未放宽。继续只读查原始权重SHA凭据/当前进程仍打开的原分片（若存在），不假定相同size等于相同内容。新CPU脚本 `commands/inspect-op003-restored-weight-provenance-20261016.py` SHA `1fec1e5437539b66279564b3b06cf9c54c5a448538d987d379d741dbf6380446`；.msc只用pickletools解析字符串，禁止反序列化执行。无GPU/模型流量/服务变更。

2026-10-16T02:52:46UTC（北京时间10:52）同acc007 UUID198b58e3e9a3457094744f9c7f9f1f80已21/198、0timeout、32active/0waiting，无native结果/回执/gate；不是正式分数。CPU收尾1880246精确实例alive/waiting_exact_formal_controller，禁止重复terminal。后台ACTIVE/30min已核，保持安静；无source部署/服务中断/newdownload加载。

### 用户确认：达标后继续M64/M1性能复测

本次只读GPQA检查2026-10-16T03:12UTC=64/198、0timeout、32active/0waiting，唯一controller/CPUfinalizer均alive/waiting，无native结果/gate；不启动性能。用户明确要求达标后继续、重点M64收益/M1退化、全部FlagGems启用，沿用完整60行契约，不改采样/白名单/矩阵。
预备新唯一v3 launcher `commands/run-op003-script19-m64-native-benchmark-v3-20261016.py` SHA `62d4a3f8c8f3d5f604f2d10fd4a375a84311cfabf0448b85c72a2b56fa3a5425`：必须先acc007真terminal gate通过、GPQA和CPU收尾器精确进程均退出，再fresh只读resident/disk双绑定、12355源/env/APIidle/GPU6与原生gatecheck；用已修复v2测试SHA5c7f...。新plan/results/controller/log均native-v3路径，未执行GPU；不重放旧v1/v2。计时/primary/allrow/M1门槛与既有60行冻结契约完全相同。

2026-10-16T03:21:28UTC只读核验：同acc007 UUID198b58e3e9a3457094744f9c7f9f1f80完成87/198、0timeout、32active/0waiting；唯一GPQA和CPU收尾精确进程均alive，收尾waiting_exact_formal_controller，无native结果/run-record/正式gate。未启动native-v3/新GPU/部署/服务操作，保持19项FlagGems及原采样契约；达标后按既有条件续接。

2026-10-16T03:26:43UTC（北京时间11:26）按用户查询只读检查：同acc007已98/198、0timeout、32active/0waiting，GPQA1870666及CPU收尾1880246精确实例仍活，收尾waiting；无原生结果/run-record/正式gate。M64/M1完整60行native-v3仍未执行，待正式>=80%及证据有效后续接，全部19项FlagGems保持，无生产源码/服务变更。

2026-10-16T03:51:13UTC只读监控：同acc007已176/198、0timeout、22active/0waiting，GPQA与CPU收尾精确实例alive/waiting；尚无原生results/run-record/正式gate，中途分数不作为结论。native-v3仍未启动，未重复GPQA/validator/numeric或增加GPU流量；保持19项FG/无callerworkspace/原服务与源码，正式终态达标且核验后续接M64/M1完整矩阵。

acc007正式159/198=.8030303通过、0timeout，原生terminal issue/check已完成，原GPQA/CPU收尾退出。执行前只读boundary脚本 commands/inspect-acc007-pass-native-v3-boundary-20261016.py SHA 69aff1f1cef44447c1d6b202bac0d1da8d8499b70ad5089c789b64dbfe35de51，核真实gate/continuity/validationSHA及native-v3未启动边界，再用已保存v3启动一次；不重复GPQA/validator，不改生产。

2026-10-16北京时间12:21确认acc007完整198题已于12:10完成：strict159/198=80.3030303%>=80、0timeout，真实原生issue/check通过；gate SHA6417ba2d5e82eb193b00c0e06377f86984e4f8afeac6a75327bdebeee8363b1f、terminalvalidation4214b14b81fd8dfef6caf241c8917726f586132e9c6bd884d4308eb3426811b6、continuity7afcd37fa9d6c6484fe9ae7795105669070008496b7808c93f89dd290785a5fe。GPQA/CPU收尾均退出，API0/0；仅资格原resident模型，非重新下载权重或私有候选。已确认native-v3所有启动边界为空，核SHA执行已保存launcher一次；只跟随现有进程，不重放。完整60行M64/M1微基准全FG保持，无生产修改/部署/重启，未提前宣称收益。

已分发v3尚未返回有效计时，先仅CPU定位本次预检/原生进程（非重跑）：commands/inspect-op003-native-v3-preflight-process-20261016.py SHA ab7a1c1d8dbd88729bb7afe1ba1a9a80f707676f4e7d4c26f84763f9c1270fa3；仅读精确脚本匹配进程状态及既有边界。

完整native-v3每mode30行/3pytest均成功退出；analysis SHAcd69a225...判M1 kernel单行.94612357<.95护栏失败，不能晋级。新增仅CPU AST/既有M1计时行核查 commands/inspect-op003-native-v3-m1-path-20261016.py SHA c212fc6cca282367665a0b8626ab25ab57d4022bcdbe6621df0f7239137e6b3f，区分M1 fallback/metadata与计时方法，不重复GPU测试，不把猜测当因果。

### review030：完整采样微基准已齐，M1 kernel护栏失败，暂不晋级

acc007正式198题159正确＝80.3030303%，0timeout，原生issue/check通过。仅绑定原驻留实例，非新下载模型重载或未部署私有候选。全19项FlagGems/公共MoE无callerworkspace/12355源码/完整env/API实例均保持；P1K组合E2E收益仍未知。

native-v3一次完成kernel/operator各3pytest，6测试通过，3seed×10case×2mode＝60行全部保留，未超时、未缺行、未重跑。每次计时含同clone-reset+完整filter；current17ATen FG服务路径为reference，原生Torch列并非裸Torch。20ms warm/100ms measure，kernel为原生Event模式，operator为同步wall模式；无graph/新Stream/模型请求。

| 输入case | kernel中位speedup | operator中位speedup |
|---|---:|---:|
| M64 BF16可精确表示的FP32，k20/p.95 | 4.502462x | 4.483891x |
| M64 通用FP32，k20/p.95 | 1.178364x | 1.171052x |
| M64 FP32 k-only20 | 1.195876x | 1.196726x |
| M64 FP32 p-only.95 | 1.178654x | 1.182675x |
| M64 ties，k20/p.95 | 2.525632x | 2.502927x |
| M64 masked，k20/p.95 | 1.139421x | 1.129703x |
| M1 FP32 fallback | 0.968558x | 1.032765x |
| M8 FP32 fallback | 0.998591x | 1.000130x |
| M63 FP32 fallback | 1.000443x | 0.997776x |
| M65 FP32 fallback | 1.004915x | 0.998196x |

M64通用FP32绝对时间：kernel current15.511424→candidate13.158144ms；operator15.444835→13.207640ms。BF16行是特定输入域，不证明真实FP32 logits可获得4.5x，更不证明模型E2E收益。primary六行中位分别2.842915/2.820528x>=1.05，但每声明行>=.95护栏仍必须全过。

**M1不能宣布无退化**：kernel三行0.968558/0.946124/0.977023x（seed42/43/44），seed43 current.368640ms/candidate.389632ms，即约5.69%变慢，低于冻结.95；operator三行1.066577/1.032765/1.018655x通过。保留该负面，不丢慢行、不追加warm、不放宽阈值，不因此晋级/部署或补昂贵graph。历史M1 .2926/.8095ms退化仍保留。

纯CPU AST及原生行审计确认M1未选M64 kernel：先metadata supports查询，再Plugin外部当前vLLM apply_top_k_top_p_pytorch原路径；reference也调用同原函数。metadata查询在batch拒绝前读ndim/dtype/device/contiguous/requires_grad，fallback含局部import。可疑CPU开销/Event提交间隙只是待证假设；operator方向相反，不能直接归因为已证metadata开销，也不能把护栏失败当噪声忽略。API0/0；数值/源码未改。

下一轮按review030：先设计最窄私有非M64快速拒绝候选，保存source/SHA/回退和新唯一plan后再改；先最小数值/边界验证，若执行性能仍完整相同60行、相同预算与护栏，禁止重放v3或仅挑M1快轮。异常语义/公共集成/graph>=2/新候选fullGPQA/P1K Mixed A/B/R仍待，旧停服窗口不复用。当前生产未部署op003，四场景acceptance incomplete。

远端证据均在ROOT：
- manifests/op003-script19-m64-native-v3-plan-20261016.json SHA87d411702e3b9474fb6b01d55b572aa94a349d0739c8921d2296ff051ecbe30d。
- results/op003-script19-m64-native-v3-kernel-20261016.json SHA58663a5b820cadae2f96243cd89d44cc64d4f7e33dafa67921222284cd762c03；XML116a1ef97229332c2896a635b778164d157c848d69f6f0836be975ffab6b48a0。
- operator JSON40bc6a6da969297efe095d5afaf18d70a51bf7c292f8144afe451992c836e346；XMLc04f42cc5e86a37c7caaf77a53733936798572877b699c176113318d73d36c89。
- supervisor SHA354936ee677d2e375c7eaea9b293534e4f249e7e60336971e93fc1a34a6640f1，postsource12355/env/resident/disk均通过；结束2026-10-16T04:26:44.967292Z。
- analysis SHAcd69a225bc901f64bad571c7bc1782bde00a8206d0c3ebcfc11e519d964f19fa，结果reject_or_incomplete_guard_failed_not_deployed。
- results/op003-native-v3-m1-path-inspection-20261016.json SHAac02d972f65ee551f7fde19e82ecc6b059a9fab4d618586d691a5fa19d764503，CPU AST/case数据审计，无GPU。

### earlygate变体：编码前冻结（2026-10-16，review030）

独立私有namespace `ROOT/private/op003_script19_m64_earlygate`，仍属稳定op003，生产未部署。唯一变化是backend的metadata-only supports查询顺序：identity优先不变；ndim==2后先按M64/V248320拒绝，再读dtype/device/contiguous/requires_grad；M64 kernel、CDF树/launch/adapter/import/fallback/算法完全不动。不能把本变体通过等同证明v3慢行的机制。

| 项目真相 | 冻结内容 |
|---|---|
| Current op/任务 | 当前vLLM top-k/top-p filtering；M64 FP32[64,248320]，M1 fallback sentinel；仅MetaX GPU6私有测试 |
| Editable/read-only | 仅新私有backend.py中supports顺序；旧private所有文件、生产四repo/测试参考只读；新benchmark仅绑定新plan/namespace |
| Build/validation | AST确认除了supports函数其他节点逐字AST相同，3py语法检查；CPU假tensor验证访问顺序；真实17ATen FG参考最小数值/alias/metadata/fallback |
| Benchmark/active set | 原生Benchmark kernel/operator各3seed×10case＝60行，原clone-reset+完整filter交易；M64 bf16exact/fp32 k20p.95/kOnly/pOnly/ties/masked及M1/8/63/65 |
| 聚合/停止/超时 | 每mode primary6行median>=1.05，每行>=.95；20mswarm100msmeasure300s/mode；数值失败/缺行/超时/护栏失败保留停止；不能重跑v3或加warm凑过 |
| Profiler/autotune | 已有prof003证据；本轮不新profile或Stream；仅hostmetadata次序，不改kernel性能参数，故不新增autotune；NV未测/不宣称通用集成 |
| Fallback/回退 | Gems仍NotImplementedError，无Torch compute新增；Plugin外私有adapter保持原当前FG参考；旧副本完全不动，丢弃earlygate import即可回退 |

| 对齐契约 | 冻结内容 |
|---|---|
| 输入与dtype | 自定义仅连续cuda FP32[64,248320]、no-grad；k int32/int64[64]、p FP32[64]同设备；至少一个finite、其他可-inf；具体值范围沿旧plan |
| 输出 | 原输入alias、survivor bitwise、不改k/p；采样算法未改，CDF1024/warps4不改 |
| 语义与例外 | finite/ties/signedzero沿已80组oracle；NaN/+Inf/allmasked仍不完整且阻止生产晋级；identity任意shape不变；rank不2/非M64/错误metadata明确unsupported后由现有外层走原path |
| 空/非连续/Autograd | identity empty返回原对象；非identity空自定义拒绝，不扩大fallback承诺；非连续自定义拒绝；inference-only不支持训练新语义 |
| reference | 当前Plugin同版本17ATen FG路径；非裸Torch；生产Gems路径不引入Torch计算，测试对照可用 |

| 路径 | 触发/实现 | 验证 |
|---|---|---|
| identity | k/p均None，原对象直接返回 | empty/alias |
| unsupported fast rejection | ndim!=2或M/N不支持，metadata拒绝，不读dtype/device/contiguous/grad；adapter仍原path | 访问顺序CPU证据+M1/8/63/65真实fallback逐bit |
| M64 finite | 原supports剩余校验后原Triton算法，不改变kernel AST | target数值与完整60行性能 |
| unsupported metadata | M64 dtype/device/stride/kp布局错误，原NotImplementedError | 新旧supports一致、显式拒绝 |
| exceptional/graph | 尚未完整证明；不启用新的选中异常fallback或重试Stream | 晋级前另行方案，不因微基准通过跳过 |

CPU-only creator commands/prepare-op003-script19-earlygate-20261016.py SHA 995b7e47288121f543ba2789ff9b536471a52eaa45419dea06786bc345779732，唯一新private副本/只改supports检查次序；先冻结plan与原3py快照再写候选，36组CPU元信息等价/访问次序检查不是GPU数值通过。原生产源/旧variant/旧证据只读；本地嵌套引号语法在上传前修复，无远端创建/执行，outer/inner AST均通过。

earlygate CPU制作完成：plane270d34a...，backend5a9ebfec...，adapter与旧d965a98b...一致；其他AST一致，36CPU控制流case等价，M1访问6项→2项，不当性能证据。新真实GPU最小数值脚本commands/test-op003-script19-earlygate-numeric-20261016.py SHA da523b2ecd086ac74bf5bae90868ef2bf3338fe0d86622ac18c3b7ded36223e6，20case对照当前FG与旧variant精确值/alias/kp/命中，5metadata及2identity，默认stream不graph，600s预冻，失败保留不晋级。

数值launcher commands/run-op003-script19-earlygate-numeric-20261016.py SHA 6d00726054f4e1b41b480c7b0b6b7cc121852ce652ac15d6e92c347478a62f8d；先mx-smi仅GPU6原worker、fresh双绑定12355/env/APIidle/newgatecheck，再唯一私有默认stream child；600s受控预算和精确PID/出生时间，不重放旧numeric，退出后再次连续性核验。

预备新benchmark commands/test_op003_script19_m64_benchmark_v4_20261016.py SHA 65efdb5f4e4b58135329b2cee6031502cbad21dad9bd45c9ad7819b6b20cc07d：仅plan SHA/路径与private namespace从v2改绑，CASES/clone-reset/seed/计时体完全一致；尚未执行，必须新numeric真通过且退出。

可重复只读新variant监控 commands/monitor-op003-script19-earlygate-20261016.py SHA 45ef8a30beafc44bef0ab477c25d08314109ea3b3bbcb69d86404395de5c3646；只读取本次earlygate/numeric/native-v4既有文件与精确进程，无GPU/模型请求，不启动creator。

earlygate真实数值20case/5metadata/2identity通过，numeric SHA5c3fa0449374ed98f54a09833f43112e8ac5454fb6b85442d46b42e342627bd9，supervisor776a796693dd82fcb0048cce808d0b937a874af209ccd9b95278fc7153735bdb，私有PID1051868/birth506618180已退出，postsource12355/resident/disk/env通过。预备native-v4新唯一launcher commands/run-op003-script19-m64-native-benchmark-v4-20261016.py SHA d9059d59002bc013f649ca19cebe868d471408891c2daf00c8965cad424bd59e 与纯CPUanalysis analyze-op003-script19-m64-native-v4-20261016.py SHA 71222102026d05cbb3133b86ef7d0532f5099cb854187e91110b13af9388864c；同60行/20mswarm100msmeasure/300smode、同primary与每行.95，只有新source/数值/plan绑定变化。执行前fresh资源/APIidle/全源/gate，已有v4边界拒绝重放。不能用跨run结果证明metadata因果，旧v3负面保持。

earlygate native-v4完整60行/6pytest成功，但M1 kernel最小.9431534仍低于.95，原护栏失败保持、不重测。新增只读CPU实际timing源码审计 commands/inspect-op003-native-v4-m1-timing-20261016.py SHA af42ad31bb87679ffdafb324aa4439dd221c0f5a8690499d8ab19385ab1d0c10，读取新M1全部行、supports/adapter、原生get_latency/get_iter_count和当前do_bench源码，0GPU/模型请求。

下一轮A/A负控制仅本地草案 test_op003_script19_sampler_aa_control_20261016.py SHA f39a0a35be9a981ec1763003dc1e9bb1be8c816afebda89468cee660a99ce671，原生Benchmark的base/gems两侧设置完全相同current_transaction函数对象，均当前17FG原path及clone-reset，不导入私有candidate。完整相同10case×3seed×2mode=60行、20mswarm/100msmeasure/300smode；测量前冻结每行ratio区间[.95,1/.95]以识别计时/顺序偏差（非候选晋级阈值）。A/A失败不抹掉v3/v4负面，A/A通过也不能证明候选过护栏。不启动GPU，下一轮先fresh/source/idle/gate及原生run路径审查后建独立controlplan/outputs，不复用旧launcher。

### review031：单变量metadata早拒绝未通过M1护栏

仅新private/op003_script19_m64_earlygate/backend.py的supports检查次序改变；原adapter SHA d965a98b...和所有kernel AST保持。先写plan/原3py快照再写候选，plan SHAe270d34a5f5e6f0155ed082efbd52d1a59dc9f8cc394dd0c6dd1da1b4e3a0510；backend5a9ebfeca4c09cc2708d163c736d98caa5ca5a371a8f05acf999cf660db1a919。36CPU选择一致、M1元信息读取6→2只说明控制流；20真实GPU数值对当前17FG和旧variant逐bit一致，5metadata拒绝与empty/M64两identity通过。numeric SHA5c3fa044.../supervisor776a7966...。未扩展异常域/graph/模型级语义。

完整native-v4仍各3pytest/30行，两mode共60行和6pass、0timeout，全部保留，结束05:06:23UTC。kernel M64bf16exact4.513181x、通用FP32 1.174380x（15.454464→13.159680ms）；operator对应4.477550x/1.167359x（15.490731→13.209309ms）。M1kernel三seed1.000697/.943153/.989146x，最差seed43 .337664→.358016ms，约6.03%变慢，仍低于冻结.95护栏；operator .979857/1.042730/1.040006x通过。M8/63/65 guard通过。primary达标不能覆盖该失败，拒绝earlygate私有变体晋级/部署，不追加warm/预算或挑快行。不能把跨run median .9686→.9891当单变量因果证明。

| v4证据（ROOT） | SHA |
|---|---|
| manifests/op003-script19-m64-native-v4-plan-20261016.json | ed27e6dceecc7b8a2bff74540a17c3817db9995afa1a489c69bdf801a8823753 |
| results/op003-script19-m64-native-v4-kernel-20261016.json | 4f2a6cc8ef9a2e5bdcb13a6c3e2e3f65ecb8133a8e2627f4e24635031527c69a |
| kernel XML | a936ddf2d6558b7be4d30be7e6f0678f17941cf8ffdd9075f46488d5832b40de |
| operator JSON | 506445730ba144d8a5b1e0239347f410eb20c1923b6e9ba8ef3950657cf98d58 |
| operator XML | 2206eb8e5bcb361217c325603838f7bed288995c9412f4f86aa7b81ec1a09a47 |
| supervisor | eef480a5597f12f10a5599d43d75d26e63eb7292190e17abb924bb20887f8ffb |
| analysis | 67fcf26c2fe5b973da4836e13920751aa2ac6dace8024655cd645e480e19ceef |
| results/op003-native-v4-m1-timing-inspection-20261016.json | b70da0a0b6d13033445df867841a0c2fd0d75bcdb7d15f5458d2621aae02b609 |

CPU审计实际Triton do_bench源码SHA387f440b098b394a18c14127874f88a8003c4b82d11475f2d6c4b94e7328f2a5：Event模式每次测量前clear_cache，估计环节也包含clearcache并决定warm/repeat数量；operator模式同步wall批量重复调用，没有逐次clearcache。两者缓存策略/host提交观测不同；尚未证明哪项导致M1慢行，不将Event数值冒充纯设备criticalpath或以“噪声”改判。原M1确实fallback同当前vLLM PyTorch/FG函数，earlygate未解决护栏，因此先做测量A/A控制，不继续盲改kernel。

下一轮已本地准备A/A测试草案 f39a0a35be9a981ec1763003dc1e9bb1be8c816afebda89468cee660a99ce671，未上传/未执行。先复核原生Benchmark.run/set_gems两侧callable/FG上下文一致，再新唯一plan/launcher/output；两侧同一个current_transaction，原10case×3seed×2mode60行和20mswarm100msmeasure/300smode，预冻ratio区间[.95,1/.95]。它只诊断测量稳定性/顺序影响，不能签发候选晋级或抹去v3/v4失败。A/A若有缺行/错误保留incomplete，不自动重复；后续用实际证据选择dispatch调查或新的同配置测量契约，禁止事后放宽旧门槛。

所有新creator/numeric/native-v4/analysis/CPUaudit已完成，不重放。GPU私有进程1051868/1053497/1054779均退出，postsource12355/env/resident/disk通过且APIidle。生产19FG/公共MoE无callerworkspace/当前GDN与attention保持，无源码部署或服务中断。当前resident GPQA159/198门禁仍有效但不资格私有候选或下载权重重载。graph>=2/异常语义/公共集成/新候选fullGPQA/P1KMixedABR与四场景最终验收仍incomplete。

A/A执行前CPU只读原生调用路径审计 commands/inspect-op003-aa-native-call-path-20261016.py SHA 3895efdb1d26745eb1d02f16452e422bbc7b5c3edd09af64865cdcff203bf83f，仅读Benchmark.run/set_gems/get_latency及当前FG use_gems上下文，不初始化设备/改源码。

A/A CPU审计通过：原生run先base后显式gems，两者相同get_latency；显式gems不进入额外flaggems_vllm.use_gems，外层17FG同作用域。审计SHA05419514168c3b5f53cf74f12fff0a4a12ed249039a345dce15702460c2ba08a，baseb7cbf2ab.../FG上下文d0135406...。本地草案v1未执行，v2仅增加真实同函数对象assert并去掉无用private sys.path插入：commands/test_op003_script19_sampler_aa_control_v2_20261016.py SHA 7724cd09234763cca52a02b4254ddcc86dbadc6aeefb9798491f33dc75a9a922。相同10case×3seed×2mode60行、原预算及ratio区间[.95,1/.95]测前冻结；仅负控制，非候选晋级。

A/A唯一launcher commands/run-op003-script19-sampler-aa001-20261016.py SHA d8b5fea3f5d9a59b3cddefde295634e5adb960cd546e3a6b47458b4680bf53d1，原同native两mode/3seed/10case，独立sampler-aa001计划/controller/results/log前缀；旧GPU进程精确退出/无AA边界、fresh12355源/env/resident/disk/资源/APIidle/nativegatecheck后才计时。计划在计时前冻结ratio区间[.95,1/.95]及同函数对象/无候选import/0模型请求。参考上下文snapshot仍校核原17FG路径，不把候选数值当A/A收益。300smode预算不变，无新Stream/graph。

A/A纯CPU一次性分析 commands/analyze-op003-script19-sampler-aa001-20261016.py SHA 65c6dd676ba347a8cd52687f55b23debafb0eaeec4c509c1b5ebd61f5aacbae8：核60行/两XML/同callableassert及测前区间；报告每行ratio与越界，保留旧v3/v4失败。仅control诊断，不输出candidate晋级。

A/A可重复只读monitor commands/monitor-op003-script19-sampler-aa001-20261016.py SHA ae878b0d6839ca56bd44b3b7129e9b4bf0010fe9bd3457d4d38ae422cee7eda3；只读本次AA独立进程/controller/短日志，不重放旧creator或查询GPU。

A/A测试v2、monitor和analysis已保存；launcher已唯一执行，等待本次sampler-aa001，不能重复启动。测试pointerassert验证samecallable，60行/20mswarm100msmeasure/300smode和预冻ratio区间不变；currentGPQA/source实例门禁用于安全运行资格，不是私有候选精度。

### review032：同函数A/A负控制显示M1计时不稳定

原生调用路径CPU审计SHA05419514...确认Benchmark.run先base后显式gems，两个get_latency都处于外层17ATen FG上下文，没有额外嵌套FlagGems-vllm上下文；set_gems直接保存函数。A/A v2运行时assert两侧是同一个current_transaction对象，两个输入数值检查也只调用同一原参考函数，未导入私有candidate。原10case×3seed×2mode=60行、20mswarm100msmeasure/300smode，测前ratio区间[.95,1/.95]保持。没有改生产实现/服务或重复v3/v4。

A/A001于05:29:41UTC完成，两mode各3pytest/30行，共60行/6pass、exit0、无超时/缺行，全部保留。只有M1越界，M>=8其余54行均在区间内：

| A/A当前FG原路径 | 中位ratio | min..max ratio | 控制越界 |
|---|---:|---:|---|
| M1 kernel/Event | 1.029412 | 0.666137..1.071585 | seed42、43 |
| M1 operator/wall | 1.053324 | 1.018707..1.065756 | seed42、43 |
| M64通用FP32 kernel | 1.000639 | 0.992920..1.002674 | 无 |
| M64通用FP32 operator | 0.999250 | 0.998717..1.001464 | 无 |

M1 kernel seed43是相同实现.321792→.483072ms，约50.12%计时差异；seed42反向出现1.071585x。wall对同一实现也出现1.065756x的表观加速。**证实M1当前成对计时观测本身不够稳定，不能把旧约6%差异唯一归因候选或以单次A/B确认无退化。** 该控制不抹掉/改判v3与v4的原.95护栏失败，也不能签发候选晋级。M64 A/A稳定只是支持既有微基准观测，非实际模型E2E收益。cacheclear/host提交/调度哪项导致漂移仍unknown，不把“有测量漂移”夸大成所有旧慢行均是噪声。

| A/A001远端证据（ROOT） | SHA |
|---|---|
| manifests/op003-script19-sampler-aa001-plan-20261016.json | fd634ffd73daa1ee92d62303e4a5becdb31e024d24639f5712635a0267c83e35 |
| results/op003-script19-sampler-aa001-kernel-20261016.json | afdad74805d259496471e02fa4a0d9e6a310becdb527afd8d0d83e9b8d1940cb |
| kernel XML | f9d1329e06043f5b13501d9192c00358c2cad7c647fdaf915b296d8116ed127a |
| operator JSON | 1a4ae67065d4e7c288a9e86db7ddbc9b5a3f953d2efee2240c08d58012c3649e |
| operator XML | 6bb0394abcfdd4fe3915cc779e9d78cdb0e3fcecc4835075b8bc2e56e409c775 |
| supervisor | 09614633a366631dd1f36020854df65d23f5daf198e562870f91e472a840c485 |
| analysis | 64d43275405c2d159a7876ef787114ee57be37a963206b4382b0c4f0b7bdc7ba |

commands/run-op003-script19-sampler-aa001-20261016.py SHAd8b5fea3...、test_v2 7724cd09...、analysis65c6dd67...均已执行结束，不重放。private PID1056500/birth506796813和1057014/birth506805460退出；post source12355/resident/disk/env通过。当前无本任务GPU客户端，生产仍原19FG/无MoEcallerworkspace/源码未部署，acc007159/198仅resident门禁有效。

review032下一轮先CPU设计唯一带原始计时观测的AA002：保持原get_latency/do_bench/get_iter_count计算和返回值不变，只在计时区域外记录原始Event分布/样本数，以及自身process CPU时间/上下文切换/cgroup throttling前后值。禁止逐样本GPUprobe/新Stream/graph/写盘扰动；原60行/20mswarm100msmeasure/300smode不增加、不自动追加warm。必须先审查wrapper能否逐字调用原方法并返回原median，冻结额外CPU观测开销及停止条件，再保存新唯一plan/命令/产物。无法保证低扰动则仅CPU设计，不盲重测。若后续据实需要新测量契约，需事前冻结A/A准入及同配置baseline/candidate/revert，不能放宽旧门槛/丢慢行/将旧结果改判通过。异常语义/公共集成/graph>=2/新候选fullGPQA/P1KMixedABR与四full最终精度均仍待。

### review032续接：AA002计时委托审查（执行前记录）

仅CPU读取当前Triton `_summarize_statistics/do_bench` 与原生 `get_iter_count/get_latency` 的实际AST，保存 `ROOT/results/op003-aa002-delegate-source-audit-20261016.json`；脚本 `ROOT/commands/inspect-op003-aa002-timing-delegates-20261016.py` SHA `bee0ba6ae51905a658167ac68bda04edaa243e3d6271c90fda7439d302a2c8aa`。不导入运行栈、不创建GPU请求，不重放任何旧creator。

### AA002预冻结与CPU审查

新诊断与AA001分开，60行/三seed/两mode、20ms warm/100ms measure/300s mode不变。仅新私有benchmark override调用原生get_latency；summary wrapper先调用原汇总再复制现成Event样本，并返回同一返回对象；get_iter_count原调用/tuple不变，finally恢复两方法。前后各一次自身rusage与挂载cgroup cpu.stat（aggregate范围，不能归因单进程），无逐样本探针/新Stream/graph/计时内写盘；每seed全部运行结束后保存raw。

预冻观测准入：额外CPU/总group时间<=0.05core，额外观测wall p99<=2ms；超限/缺行/错误/超时保留incomplete，不追加或重跑。A/A区间仍[.95,1/.95]，不改变旧candidate晋级失败。三项本地CPU单测验证原args/kwargs与返回对象、计数tuple、异常finally恢复，不能替代硬件验证。源码AST审查产物SHA `0bae8df3c9eb5c003ac69c8a915196fb8a534adfeb0c73243ce99aeae0fb62c7`。执行前脚本均保存ROOT/commands：

- `op003_aa002_observer_20261016.py` SHA `d436a310ad2a5a147b5568a4a99743f7f506541da7770c2aae5953632a2b3a77`
- `test_op003_aa002_observer_cpu_20261016.py` SHA `f0c4e2ed600510a427824a1a1a4f269e8d812880c6bc428a87a6ae35acf48d08`
- `test_op003_script19_sampler_aa002_20261016.py` SHA `8192a5ac32eba28cca9c070ede7793405a9d2c57742552628bf6e4399affca98`
- `run-op003-script19-sampler-aa002-20261016.py` SHA `ca033588b602c1bda1da6ce50a7bdd659c2ee84d482536b3d5ea593bb6a6761d`

执行前补强：launcher明确核冻结gate与terminalvalidation的真实SHA，plan保存fresh source_before和CPU资源快照；最终launcher SHA `78005cf46f4dc82a7d6f594288303a861ec5f30065acd451c2e787cb8324b407`（旧本地未上传版本未执行）。远端三项CPU委托单测通过，未导入Torch/GPU。

AA002只读monitor `ROOT/commands/monitor-op003-script19-sampler-aa002-20261016.py` SHA `d1c90579897b24e2b4606455a64fb3f66e042ce13b6815b2c94d2013a89b6679`，只读精确子进程与短日志。CPU analysis `ROOT/commands/analyze-op003-script19-sampler-aa002-20261016.py` SHA `07f0a21780b4bef59efd71bad029b491792188b1211365bdf7774b6ccc7b18db`；仅两mode齐全退出后执行一次，核原60行/6pytest、120次委托返回与raw中位数/原JSON一致、观测预算、ownCPU和cgroup范围。缺行/观察超预算保留incomplete，不重放。

AA002首次monitor尚无native边界，增加只读预检边界monitor `ROOT/commands/monitor-op003-aa002-preflight-boundary-20261016.py` SHA `4085f7c0b934bd70b3ad27776f9479a70363abb200b8e5a034ec8ab6f5a0f368`，仅精确launcher路径、容器checker/native路径对应进程状态和AA002文件名，不操作GPU或重放launcher。

06:00:10UTC只读快照：kernel1057963/birth506987691已退出，3pytest passed；operator1058477/birth506996416正在运行。Host launcher2123273/birth506979981；单次启动保持，不因进程退出或临时缺supervisor重放。

AA002已06:01:30UTC两mode结束，6pytest/60行均保留，CPU分析SHA `69951ddf5adb70f2e65219174a486ba8fcfec539a0d001e039a581f030568956`。观察CPU0.00300057core但额外wall p99 2.526405ms>预冻2ms，故incomplete；120次返回值核验一致不豁免observer失败。不重跑、不提高预算。只读CPU边界汇总 `ROOT/commands/inspect-op003-aa002-observer-admission-20261016.py` SHA `2f6d14aa1c2e5d63be14699ea73a2b3b7e60b7b22a5a54b6b83bf3dfdab45354`，检查超预算调用、已记录throttling增量与APIidle，不新建GPU工作。

### AA002失败后的CPU设计（不启动新GPU）

保持2ms/0.05core准入不变。新草案仅将每call snapshot改成getrusage+monotonic，不读文件；未来cgroup只能组前/组后读取，粒度变粗必须明确。`ROOT/commands/op003_aa003_observer_cpu_draft_20261016.py` SHA `3305eaea290eab0287c609c5c208fe2709ea090e6ec8f63021ef4468130487d4`；不是native AA003 benchmark/launcher，尚无新GPU计划或结果。CPU成本检查 `ROOT/commands/inspect-op003-cheaper-observer-CPU-cost-20261016.py` SHA `dbc2ddb50b2ad358b24f85c7ba442995e1102c0ee93fd9d01fd406f2028d2d74`，分别120次合成原生委托、保留返回identity与finally恢复，不导入Torch/不调用GPU。CPU成本不代替真实CUDA负载下observer资格。

### review033：AA002终态与CPU低成本草案

AA002于06:01:30.989560UTC结束，kernel/operator各3pytest/30行，合60行全部保留，无timeout；120次原生返回均与保存raw/nativeJSON一致，source12355/env/原resident/恢复磁盘连续性全部通过。两native精确进程均退出，06:03:24UTC API0/0，无本任务GPU客户端。

但observer额外CPU为0.003000571core，额外wall p99 **2.526405ms > 2ms**，max4.373764ms，45/120call超过2ms。因此本轮 **incomplete_observer_overhead_exceeded**，不以6pytest或kernel A/A接近1代替准入，不重跑、不改门槛。

| 模式 | M1 seed42/43/44 A/A ratio | M64通用FP32 A/A range | 边界 |
|---|---|---|---|
| Event | 1.036396 / 1.025087 / 1.042783 | .991467..1.000861 | 本次ratio在区间，但observer不合格 |
| wall | 1.023380 / 1.066510 / 1.019227 | .996799..1.000349 | M1 seed43越界，observer也不合格 |

M1 Event样本数168/175/173/174/170/177，p99约.422–1.377ms，max2.513ms；本次不能归因于仅1–2个样本。已观察区间挂载cgroup throttling增量均0，但cgroup为aggregate，缺每Event CPU时间线，不能排除host提交/调度/cache/driver，也不能证明M1旧慢行纯噪声。全部旧v3/v4失败保持，未晋级/未部署。

CPU新草案去掉逐call文件读取，只保留rusage与monotonic；未来cgroup在seed组前/后读取（更粗，不能定位每call）。240次mock委托identity/恢复检查通过；纯CPU环境旧observer p99 .206647ms、草案 .023687ms，分别meanCPU .109198/.009144ms。这说明CPU路径更轻，但真实GPU后台线程/调度未测试，**不构成新AA003或候选通过**。目前没有AA003 benchmark/plan/launcher/GPU结果。

下一步先完成新草案集成的CPU审查和唯一AA003计划，完整60行/20ms/100ms/300s、2ms/.05core、[.95,1/.95]保持；如果仍失败或M1不稳，停止本observer路线，先形成事前冻结的顺序/精度测量契约及A/A准入，不盲加AA004或改kernel。graph/异常域/公共集成/新候选fullGPQA/P1K ABR继续待做，无E2E累计收益。

外部证据（均ROOT下；raw六文件SHA见state）：

- plan SHA `6f403da9675b8b17f6c16d84a6d18d87101e29f5b588f4a89584fb43386980d5`
- supervisor SHA `2cf1358cc0ce1bcbac3afbda02aa1c3573816f92e4295ee20c75721be3c579f3`
- analysis SHA `69951ddf5adb70f2e65219174a486ba8fcfec539a0d001e039a581f030568956`
- CPU admission inspection SHA `0b8b31ee9c9445759c5f29e0cae7cdaf5f73ced06deb753d211375e51e86cdbd`
- CPU cheaper-observer cost SHA `b7112c410380f66632ac00ab5d2328c423807a3f20daf45a38f1243152bca582`
- kernel native SHA `fb8e4e001f52f601eecc8e0839400f992d92fe75e8173e4aeb22e0702bfff723`；XML SHA `c061faa3992af5ffc97293fd0649a4288e2456d137b4ca33f5f45cb53775dd1a`
- operator native SHA `bf1a7560cb09dfd3bf44fd4e4ab19a1fedf7e9aa35eb2fb73c044beb34f3e776`；XML SHA `d0a6022d34e3bc860d8c13077b4c20ac62f48ad2ee82fdc3f1275c97fd68e879`

### review033续接：AA003集成执行前冻结

仅新私有计时诊断：capture AST与CPU草案相同，percall snapshot无Path/read_text；current_transaction/get_input_iter/set_shapes AST与AA002一致。新增group_snapshot每seed组前/后各一次，仅此处读取cgroup。四项本地CPU检查（委托参数/返回对象、count tuple、异常恢复、AST/矩阵/组级位置）通过，不替代硬件资格。完整60行/20mswarm100msmeasure/300s mode、A/A[.95,1/.95]保持；observer CPU<=.05core、percall p99<=2ms，另加groupboundary p99<=2ms，组观测CPU也计入总预算。逐call记录append成本额外纳入，预算不放宽。无新Stream/graph/模型请求/候选导入。

新plan/output前缀`op003-script19-sampler-aa003-`，启动前先确认无已有边界，fresh核12355/fullenv/原resident+恢复disk/原生gatecheck/APIidle/资源/旧AA002精确进程退出。任一失败保留边界，不重放launcher；AA003若缺行/错误/observer超限或M1不稳即停止此observer路线，不盲加AA004。以下保存ROOT/commands后才执行：

- `op003_aa003_observer_20261016.py` SHA `89f9ebfc4077940e7910ca2310244507c4b4663b774cdb4503d5ea9d8980f3ea`
- `test_op003_script19_sampler_aa003_20261016.py` SHA `37c9c88989b0a872a25dbdaacba165210974a0a9e429be43637c3c11ae4ca812`
- `test_op003_aa003_integration_cpu_20261016.py` SHA `7e44667df20e3b9a7208707b76c78e051a7b8bdbad3e4255a925331e1023b21e`
- `run-op003-script19-sampler-aa003-20261016.py` SHA `739285705fe2bd0d2cd11caf5de5966078d6ec486bca61e665135c260e9797b1`

### AA003启动器工具失败：按停止条件结束observer路线

远端CPU四检查通过（review SHA `cc864231db119ada74bb4e44150ac2933a9a64d26c508a619abe977c02a79098`），但我生成的launcher在写plan前把`plan['observer_budget']['group_boundary_p99_wall_ms_max']`赋值放到了observer_budget初始化前，stdin第35行KeyError。同步launcher exit1，失败stdout保留TEMP/aa003-native-run.stdout；不是数值/性能失败。按已冻结工具失败规则停止observer路线，不修正重启AA003、不加AA004，不重复任何旧评测。新只读CPU边界脚本 `ROOT/commands/inspect-op003-aa003-preflight-failure-20261016.py` SHA `f1d01750c07fdae3d576ffa54658a1168bf9947fd348f6b7fe639232142a5726`：核错误顺序AST、AA003 plan/controller/log/results边界和精确native客户端/APIidle，再保存失败inspection；不生成请求。未上传/执行本地AA003 analysis/monitor草案。

### 新测量契约001：仅CPU草案，不执行GPU

AA003边界inspection SHA `5089c84a027ef83a76995b27a78972b8c80882f0363cbb58d1b05d1682d8082b` 已确认没有plan/controller/log/results或native客户端，API0/0、模型请求0。observer路线结束。

转向独立事前契约：短20/100ms A/A不稳→提议所有角色统一100ms warm/1000ms measure，并对每seed42/43/44同时AB/BA两顺序分层；不修改原生timer，不引入逐call观察器。每mode6组60行、每角色120行，admission/current-current→candidate/current-private→revert/current-current三角色总360行，全部事前列出，permode300s保持、总预算1800s，不自动追加。原硬护栏**每行>=.95不变**，A/A每行[.95,1/.95]不变；不以CI/中位覆盖失败行。M64主指标单列generalFP32 k20/.95每mode中位>=1.05，BF16exact仅另报。顺序平衡和更长计时只是可证伪设计，未证明解决不稳。该新范围/参数不覆盖或改判原60行契约。

CPU保存脚本 `ROOT/commands/build-op003-measurement-contract001-draft-20261016.py` SHA `a617179b372f3c75f40c9ae200ef9002fabd5e793c92d38b5dd68d50e0aa3e72`，输出 `ROOT/manifests/op003-measurement-contract001-draft-20261016.json`、execution_ready=false。只做字段/矩阵/顺序CPU自检，不导入运行栈。仍待actual native角色映射、相同输入/FG作用域、CLI六组验证及CPU归一化边界检查，之后另冻结final契约/唯一启动包；当前不允许运行此草案，也不重启AA003/加AA004。旧v3/v4/AA001/AA002失败全部不改判，无生产部署/新GPQA/模型ABR收益。

新契约CPU归一化检查模块 `ROOT/commands/op003_measurement001_contract_checks_20261016.py` SHA `fbaf6bb58a9a4f37f4a00a153f9433800aaf7341956a0026f398ad8bc5aad08f`；CPU审查脚本 `ROOT/commands/test_op003_measurement001_contract_cpu_20261016.py` SHA `f3482ae552db719bcb9a7e783be74fb21184d424401f76c227cc2b553c8a53e2`。本地七项检查通过：AB/BA归一化相同收益、真实回退不被倒数变成收益、identity、闭区间边界、非有限/缺字段/未知order拒绝、快行不能覆盖失败、矩阵重复/缺失拒绝。远端仅AST核当前Benchmark.run first=torch_op/second=explicit gems_op与CLI参数定义；不import Torch/不计时。CPU通过也仍execution_ready=false，待实际六组benchmark源与相同FG/输入及原生collect-only资格，才另冻结final包。

契约CPU审查v1七项unit通过，但native静态取证用单行substring匹配实际跨行`get_latency(\n self.torch_op...)`而失败，0GPU、未生成review JSON；保留v1失败。新唯一CPU续接 `ROOT/commands/inspect-op003-measurement001-native-CPU-review-v2-20261016.py` SHA `1b20f1baeb5f571d1652fd90278cca875dd75535832e0630c9f87408342dc9cb`，只按AST Call节点/lineno核实前两次get_latency参数并读取CLI addoption，不重跑旧creator/benchmark或7项unit，execution_ready继续false。

CPU native审查v2的first/second AST已通过，但对conftest应有4个CLI addoption的假设不成立，在CLI断言退出，0GPU/无review结果；失败保留，不推测支持情况。新只读源码脚本 `ROOT/commands/read-op003-measurement001-CLI-source-20261016.py` SHA `9f0d4df3348443e0c89ba1322efbd44f96e3fd96aec9c048302a3735c450a1e3`，直接读取真实conftest源码确认定义入口，不启动测量。

真实conftest确认warmup/iter/metrics为直接参数，`--mode`是原有IfExp分支（MetaX使用--mode，kunlunxin分支--fg_mode），v2只找顶层literal所以遗漏；没有CLI缺失/运行栈修改。新v3仅静态遍历参数AST子节点，已在保存的真实conftest与历史同SHA base.run本地fixture验证4声明及first/second顺序。只读CPU续接 `ROOT/commands/inspect-op003-measurement001-native-CPU-review-v3-20261016.py` SHA `f20f966d019753f63db04d1a1df589e21222c215071543909d63159919f0a39f`；v1/v2失败保留，0GPU，无旧creator重放。

### review034结论

AA003未产生任何native计时，原因是本次生成launcher的plan字段初始化顺序错误；按预冻结工具失败条件停止observer路线。四CPU检查/更轻CPU开销不能代替实际硬件资格。不会修正重启AA003，也不加AA004；原v3/v4/AA001/AA002失败保持。

新契约001仅CPU设计：每seed同时AB/BA、统一100ms预热/1000ms测量、每mode60行、每角色120行，三个预声明角色共360行。permode300s不变；每行.95硬护栏、A/A闭区间不变，generalFP32 M64主指标单列，不用BF16快行/中位/CI覆盖慢行。此为新范围，所有角色必须同配置测，不能与旧20/100ms结果算精确gain。新契约不使用逐call observer，也尚未执行。

CPU七项归一化/边界/失败不掩盖检查通过；native源码AST最终核实first=torch_op/second=explicitgems_op，CLI warmup/iter为ms并转int，metrics append，--mode原有IfExp MetaX分支。前两CPU静态取证脚本失败保留，v3安全续接只读源码，无GPU。当前draft execution_ready=false，尚缺实际六组benchmark的同输入/FG/角色映射证明、完整plan构建CPU模拟（捕获初始化顺序错误）、最终独立契约/启动包与原生collect-only六组。下一轮先完成这些CPU工作，不能直接消费draft运行。

- AA003 failure inspection: `/public-flash/jinghao/qwen3.6-35B/20261013-qwen36-35b-metax-e2e-current/results/op003-aa003-preflight-failure-inspection-20261016.json` SHA `5089c84a027ef83a76995b27a78972b8c80882f0363cbb58d1b05d1682d8082b`
- measurement001 draft: `/public-flash/jinghao/qwen3.6-35B/20261013-qwen36-35b-metax-e2e-current/manifests/op003-measurement-contract001-draft-20261016.json` SHA `e104c6953c1f46742c62c91f489eaae38787c3ad6c9dbf5120e9b0a02ba30199`
- native CPU review v3: `/public-flash/jinghao/qwen3.6-35B/20261013-qwen36-35b-metax-e2e-current/results/op003-measurement001-native-CPU-review-v3-20261016.json` SHA `944e63f9d22e798a61250758d456719ec213ba6361d83458d242e5a6172990ce`

### contract001实际原生包：执行前记录

六组benchmark源已完成；保持旧get_input_iter数据构造AST（仅private_transaction→comparison_transaction别名）、完整clone/filter交易；未定义/覆盖run/get_latency/do_bench/get_iter_count。候选只在ROLE=candidate条件导入私有adapter，admission/revert的两个callable断言同对象；每seed/order元数据在bench.run后一次性写，计时内无observer/写盘。

纯CPU计划函数先deepcopy完整draft并验证字段/矩阵/6组collect/12CPU checks/fresh事实再设execution_ready，避免字段初始化顺序错误。12本地检查覆盖完整构建无副作用、缺字段/facts/hash/collect/已有边界拒绝、两种角色映射、CLI flags、AB/BA归一化、不掩盖慢行、非有限/缺行/映射失配拒绝、原输入AST/继承计时器。远端执行前ROOT/commands新文件/SHA如下（除CPU测试外只上传，不启动）：

- `op003_measurement001_packet_20261016.py` SHA `ada116bf10cc43a5ee3099db548df63f2bd2de836a3a92253856c2d295d766f8`
- `test_op003_measurement001_native_20261016.py` SHA `42e907951836afdd8224ab796326e90301f5753baddfc12618404f33827c2bee`
- `op003_measurement001_worker_20261016.py` SHA `5c02484e1e0d00c83580c9d4413e7590d7c78a03b058592fff416edbbeeb229c`
- `test_op003_measurement001_packet_cpu_20261016.py` SHA `d782761171cc1a2059781d68df511ad3e2a95d38ab9860cdecf46929312adfa8`
- `run-op003-measurement001-admission-20261016.py` SHA `d680477ef737002f8fd21bfb92ba1bc066cbbc3c114cc0c31da5629ec44858d0`
- `run-op003-measurement001-candidate-20261016.py` SHA `c6a514ba60c5d7042395fa1b0612bbcfe1718887342c21728503bcdde2a82f8f`
- `run-op003-measurement001-revert-20261016.py` SHA `aa512922033ff3b81e51a4dbbd465a0f429e6c5ee508edbd6ab9275f7f9afc5f`

worker只编排原生pytest；每mode300s且三角色整体1800s，不延期。只能终止其精确birth/pgid私有子进程。所有native行/XML/六组身份记录/SHA保留，原生6pytest/60行每mode不全则incomplete；admission全部120行闭区间通过才允candidate，candidate后固定revert做漂移守护。当前没有final契约/collect资格/新GPU数据。

远端12项CPU包审查通过，receipt `ROOT/results/op003-measurement001-packet-CPU-review-20261016.json` SHA `f8203e20efa397fa6e3593fcd6d7caf37c2090d37632709f729c6d0fa7273a6b`。新一次性final冻结脚本 `ROOT/commands/freeze-op003-measurement001-final-20261016.py` SHA `7b7ee9505482f3238b72bf2b7b78db789f443e427052aaf14dbfcd1a00cda144`：先核GPU6/7仅原TP、所有包SHA/无final或role边界，fresh source/env/resident/disk/gate/APIidle；原native collect-only kernel六组成功再fresh；最后调用已CPU完整构建测试的同一make_final函数，exclusive写final/collect receipt。此步只有collect，不计时/不发模型请求；任何已有输出不重放。新final路径 `ROOT/manifests/op003-measurement001-final-20261016.json`，未创建前原draft继续execution_ready=false，不直接消费旧AA003/creator。

新只读monitor `ROOT/commands/monitor-op003-measurement001-20261016.py` SHA `441d916763ba9fb9eaa21058b37c0be3290144cbcaa9b813ea40c630064b164c`：仅读取final/collect/各role已有controller、短日志、真实analysis摘要及精确PID birth/APImetrics，不写结果、不发送生成或GPUprobe，可核SHA复用。

07:04:15UTC final冻结成功（只有collect，尚未计时）：`ROOT/manifests/op003-measurement001-final-20261016.json` SHA `015b19f3375b538a1ef3a524f2c85945d25b69e0c540d911bebdd7ef951a88ff`；collect receipt SHA `0c46f8df6451b73b32681cee92e78e0e0f0730f1e58e610615924e28caef59be`，真实6tests/rc0/12CPUchecks，前后fresh source12355/fullenv/原resident/恢复disk/gate/APIidle通过、GPU6/7仅原TP；07:04:32只读monitor确认三role边界为空，API0/0。

现按已冻结final执行唯一admission（不是旧AA003/AA004），命令：`python3 ROOT/commands/run-op003-measurement001-admission-20261016.py 015b19f3375b538a1ef3a524f2c85945d25b69e0c540d911bebdd7ef951a88ff`，launcher SHA `d680477ef737002f8fd21bfb92ba1bc066cbbc3c114cc0c31da5629ec44858d0`。只准入120行全部通过才candidate，admission一旦有边界不可重放；worker两mode退出后自动一次CPU解析/XML/身份/每行guard及post连续性，真实analysis status优先，不以pytest通过代替A/A控制。全部预声明参数/1800s总预算保持，0模型请求，原生产19FG无修改。

07:05:56UTC只读monitor：admission host2170117/birth507386389已退出，未见worker/nativecontroller/analysis；当前不重启或推进candidate。新CPU边界脚本 `ROOT/commands/inspect-op003-measurement001-admission-startup-20261016.py` SHA `4fec3a0002a97c422f075d16f3e2c422c958ac960b6b95f892051b9ab167017d`，只读已退出host identity与短host日志/现有文件列表，保存独立tool前缀证据，不伪造计时结果或重复原launcher。

### 仅控制面的安全续接（执行前记录，原契约不改）

真实失败inspection SHA `fcd1d2e16cb246afc2c6a2c264c8ebf90d4b5f60a282b42f35230e9ff8288625` 证明worker只因启动器自身日志误入旧产物保护而在reserve/native前退出；results为空，只有已退出host controller和控制日志。原host SHA `671751ad95cc5f19e7154f96805096e171d864ecf3c944be4bf3f61061669731`/日志 SHA `76f66eae81f389c0a74410e97ad34fef361a4dd1192a9ece556da2a3879a61ca` 保留，不覆盖/移动/删除。

新唯一CPU控制面amendment仅允许这个精确路径且双SHA/原host身份/原final015...一致的失败控制日志；任何native/result/unknown/重复/篡改证据仍拒绝。派生admission worker其他函数与native_args/Popen/wait/killpg AST不变；现有benchmark/packet/算法/数据/计时/护栏源完全不改。新host控制日志置于`op003-tool-m001-*`而非native role命名空间，candidate/revert沿用原worker。原host起点07:05:05.429426/1800s截止07:35:05.429412 **不延长**，新控制面耗时同样消耗原预算。native行从未开始，因此这是首次完成原计划admission的安全控制续接，不重放已产出的计时/原creator。

九项CPU协议测试本地通过：精确旧控制日志、native/unknown/重复/缺失/篡改/错误final拒绝、native调用及其他函数AST一致、三role控制日志分离、原截止不变。远端CPU测试仅复制新临时fixture到ROOT/private，不操作原证据/服务/GPU。随后须另冻结amendment/SHA并fresh才能首次native。ROOT/commands文件：

- `op003_measurement001_control_guard_20261016.py` SHA `799e8efc57554ebb03abb43b87754adfbde1a26c2a19f25ded24942520e10e16`
- `op003_measurement001_worker_control_continuation_20261016.py` SHA `ffdc7449586e20c8a47a6d4b4b26f245baf94d0f3d4f882c4a799bf1b00a5382`
- `continue-op003-measurement001-admission-20261016.py` SHA `e1e8e8dfe2a7aa6b5debefda7909c187ce96fdc8710f75c7a0a78ab8c2932371`
- `continue-op003-measurement001-candidate-20261016.py` SHA `ece660bc2f310a9ab2dfb5a791e20f67cafa0d9caf611d9eeba0b2d85307af42`
- `continue-op003-measurement001-revert-20261016.py` SHA `efe595a563d6035345d4e683a6a971a8b013d4afe91ae1d156e0ffab4ba486db`
- `test_op003_measurement001_control_continuation_cpu_20261016.py` SHA `86e10f5c17b7725fa81f20d98c9c5241fe0855bdd52c1c66b49451f0e1539102`

控制面CPU九测试远端通过，`ROOT/results/op003-tool-m001-control-CPU-review-20261016.json` SHA `30c621dd8c5f30616212d1416bde89a2abfedb6db750ec5dea5c15584575e465`。新唯一CPU冻结脚本 `ROOT/commands/freeze-op003-measurement001-control-amendment-20261016.py` SHA `3b05195503af0c2c3f14d144b4cf06e7c65f3af09682db79a8102e42f45fc34b`，核所有旧final文件/原失败host/log SHA、0native边界、9CPU receipt及未过原07:35:05截止，exclusive写`ROOT/manifests/op003-tool-m001-control-amendment-20261016.json`。不改final015...及原证据，不改变性能/精度阈值。后续仅执行新continue脚本且需amendment真SHA，不执行原已失败admission launcher；candidate/revert原旧hostlauncher因日志布局问题也不执行，改用已CPU审查的新工具日志布局，实际worker原代码保持。

控制面amendment已冻结SHA 8a801a068cd39e6c5cced5a314c0ce17118d56c9d974d7ff607aa85e06738e26，原截止仍07:35:05.429412UTC。执行新唯一continue-op003-measurement001-admission-20261016.py，SHA e1e8e8dfe2a7aa6b5debefda7909c187ce96fdc8710f75c7a0a78ab8c2932371，唯一参数为上述amendmentSHA；只识别精确原失败控制日志，不重复原launcher或任何已产出计时。新边界创建后不再执行该continue。

07:17:26UTC只读确认首次原生admission实际运行：worker ns1059518/birth507452997、kernel ns1059535/birth507453148 alive；API0/0，candidate/revert尚无边界。新增只读monitor `ROOT/commands/monitor-op003-measurement001-control-continuation-20261016.py` SHA `cc179fd8055be71ab0cc4eb0ee95ba2235d2ce27843f916d1431eae69060d155`，同时显示新续接host、原已退出host与native精确进程/原deadline；只读，可核SHA复用，不以旧host退出推定native失败。

### measurement001终态CPU审计（review036执行前记录）

原生admission已完整结束，analysis SHA cff6dffbc1ee6ee6a01d6c3c78d2acfa724856cc005c3f68db92f0af4e4d9359 / supervisor dc354edfb70730b100ab41158d5947214304227d47f53de6c50cb231682fe4db：120行/12pytest、119行A/A通过，M1 operator seed42 AB=1.055332529超过1/.95，candidate/revert禁止启动。新唯一 `ROOT/commands/inspect-op003-measurement001-terminal-order-CPU-20261016.py` SHA `5aa4b4841c403e1389f7ae2398510b521c54b20793b5ee973f61d8b23c041cc6`，仅读已完成JSON及其引用SHA、归一化和slot分布，另读当前CPU资源配置和已固定原生计时源码；exclusive保存独立CPU inspection。无Torch/GPU导入、计时、模型请求、服务变更。当前CPU快照不能当运行时调度因果证明，旧M1失败不改判。不重跑analysis、admission、GPQA或旧observer路线。

终态CPU审计已完成：inspection SHA 9312ae4faf074f2c8bfde7823bbef2c6485f88c6c00408a98ebb336d2e0c0f5b；post source12355/fullenv/resident/disk各自通过，12/12 M1 first-slot较慢。当前CPU无quota/cpuset限制、挂载cgroup cpu.max=max100000/nr_throttled0，只是事后快照，不证明运行时原因。

新增仅分析既有prof003两rank trace的CPU脚本 `ROOT/commands/inspect-prof003-sampling-M1-M64-existing-CPU-20261016.py` SHA `ab737d525534e64f41bf69bbab05914b6db048fd3c03d7ff273443135388b13d`：核旧validation及traceSHA，按External id匹配aten::scatter_与GPU，逐实际M shape报告，区分model marker外采样。无新采集/请求/GPU导入/性能重测。单kernel/profile-on/早24step的小样本不能证明整采样交易、M1稳态护栏或新控制顺序原因，旧失败保持。

### review036：准入终态与下一轮边界

07:23:40.480293UTC原生admission结束，kernel/operator各6pytest60行，全部exit0、无timeout、SHA/映射/配置/source12355/fullenv/resident/disk验证通过。analysis `ROOT/results/op003-measurement001-admission-analysis-20261016.json` SHA `cff6dffbc1ee6ee6a01d6c3c78d2acfa724856cc005c3f68db92f0af4e4d9359`；supervisor SHA `dc354edfb70730b100ab41158d5947214304227d47f53de6c50cb231682fe4db`。119/120行A/A通过，唯一M1 operator seed42 AB：first=.5514196091634365ms/second=.5225079244674613ms，ratio=1.05533252864144高于1/.95。真实status=admission_failed_control，pytest通过不替代控制。candidate/revert未启动且阻止执行；07:25只读核精确host/worker/native全退出、API0/0，0模型请求/0生产改动。

终态CPU审计9312ae4f...确认两mode各6/6 M1 raw first/second>1，AB/BA归一化无误。M64通用FP32 A/A中位kernel1.001298/operator1.001124；不能把接近1的M64覆盖M1失败。当前CPU quota无上限/affinity0-159/throttle0为事后快照，不能证明此前host/cache/driver机制，更不能改判v3/v4失败或签发候选无退化。原生源码保持，run先base后explicitgems，无额外Gems context，gc在整pair后；各侧独立原生预估/预热/计时，实际新run未记录逐样本/迭代数，保持unknown。

既有trace新CPU分析 `ROOT/results/prof003-sampling-M1-M64-existing-CPU-inspection-20261016.json` SHA `20c92f01996a991cd98e2b9050847bf70831ebb22a3f4fac3352dc9d5b6cd14d`：各rank24个与CPU aten::scatter_ Externalid精确匹配且在model-marker外；M1各2次，GPU中位13.568us，CPU submit中位32.187/35.791us；M64各15次，中位10372.864/10302.976us；M9/17/25/33/41/49/57各1次。这是早期profile-on单kernel，不能和整个采样交易.3-.5ms混算或证明A/A原因；不能称新phase捕获或全run稳态。

后续仅CPU核对固定计时调用生命周期与私有/当前sampler支持语义（finite/-Inf/NaN/+Inf/allmasked/tie/CDF/alias/metadata及选中kernel异常传播），生成可证伪的窄矩阵与真实调用证明；没有因果设计前不再新A/A或改kernel。原候选M1失败、原权重等价unknown、19FG/no callerworkspace/原服务、最终graph/full198/P1KMixedABR等缺口保持。

### review037 CPU调用与语义边界审查（执行前记录）

仅执行新唯一 `ROOT/commands/inspect-op003-sampler-semantic-boundary-CPU-20261016.py` SHA `fcdf64ad96a5240918bfa0f3ce0592130c870ab25ac15a336b174a92731d800c`。固定当前earlygate/backend、adapter、原vLLM/Plugin/reference、原生Benchmark及已完成measurement001测试源SHA；只AST抽取及执行原selector/adapter函数体的CPU metadata/异常传播stub，不导入Torch/Triton，不运行原creator/数值/GPU/模型请求。保存独立CPU审查，明确mock只证明支持选择/路由，不当实际数值、alias、kernel异常或graph证明。检查同函数计时两slot是否有确定不同计算；若未找到仍为unknown，不新建GPU控制。另列finite/-Inf/NaN/+Inf/allmasked/k/p值范围、tie/CDF与公共API边界，事前冻结后续窄counterexample矩阵，旧数字/护栏不改。

CPU语义审查已完成 `ROOT/results/op003-sampler-semantic-boundary-CPU-inspection-20261016.json` SHA `ea617afda1f51996d7a8fc09b8d1ed0fd520131287e31930b39c601a15648aa5`：12类符号值标签同metadata均可选（非数值测试），4项实际adapter函数体CPU路由/异常传播检查通过；未找到两slot确定不同计算，历史逐slot迭代/调度线缺失。metadata支持与文档finite/-Inf/每行至少1finite/k合法/p合法前提未绑定是实际晋级缺口，不能以当前20/.95证明所有logits符合。

执行新唯一CPU设计冻结脚本 `ROOT/commands/freeze-op003-sampler-domain-CPU-design-20261016.py` SHA `755ff959c630c2f6cd1f9a8970c7d0555070eab12a694b5983003aeb5e89d200`：仅只读三处当前caller源码并保存SHA/片段，exclusive冻结18项finite/exception/tie/CDF/alias/metadata counterexample设计，execution_ready=false/GPU_launch_allowed=false。非法k指针测试只设计，未实现guard前绝不实际调用。固定current17FG为唯一数值oracle；不新GPU测试、不解锁measurement001失败契约、不改生产/算法/19FG。

### review037结论与调用方边界

CPU审查ea617afd...与18项设计 `ROOT/manifests/op003-sampler-domain-design-20261016.json` SHA `3c2cd3acf4335806f5058fdd54e1f14121e8b3e66f005d591ce69b7b48ae8c72` 均完成，无GPU导入/运行/请求。设计execution_ready=false/GPU_launch_allowed=false，不能解锁失败的measurement001。

原生计时同函数两slot的clone/fullfilter/17FG路径相同，没有源码证据证明第二段少算；各侧独立5-call估计/预热/计时可能产生不同迭代数，但本run没采实际计数，不能归因或改判。CPU四项adapter检查只证明stub路由/异常传播，不能替实际alias/数值/graph。

当前调用方：sampling_params.py SHA3d88aed01aa706ce6a1d0cec5aeaaf15d8606aae3c2734e652ae345455ea23aa L472附近拒绝p不在(0,1]；gpu_input_batch.py SHAa371c9831d7ee248b42d284cffe96a31bcb3d59b7900b9adafdcb5d0272ae943 L369附近将非0<k<V归一到V。因此 `_extract_top_k` 对非法k缺列mask属于直接backend/API预条件风险，并非当前服务已发生OOB。sampler.py SHAb8c03e99ea099f710440a1390e1495772a563477a5eafaf3f6d75af194024f76 L376附近先allowed-token -Inf mask再badwords及nonargmax processor；allowed列表非空不证明组合后至少1finite。当前20/.95正式配置和历史3异常probe不资格任意NaN/payload/+Inf/allmasked域。未观察到生产异常值，此处是支持边界缺口。

18项未运行矩阵覆盖finite极值/-Inf稀疏、单行/全部allmasked、正负payload NaN、单/多+Inf、混合异常行、signedzero tie、CDF精确/相邻、kOnly/pOnly异常、合法异构k/p、非法k/p只设计、安全alias/metadata/选中异常与mask关系。实际current17FG为唯一硬件oracle，不用bareTorch或CPU模拟顶替；选中异常必须上传，Gems内不加Torchcompute补洞，也不加host值同步/缩19FG。后续先CPU追当前Gems排序/softmax/CDF的异常机制，若不能证明则明确incomplete并仅准备最小安全验证方案，不能自行追加GPU控制。

07:49:50UTC只读continuity核12355源/fullenv/resident/disk/prefixoff通过；原权重内容等价unknown、future_restart_rebind_allowed=false与历史graph证据边界不变。原19FG/服务/生产源码未改。

### review038异常helper源码取证（执行前）

新唯一CPU脚本 `ROOT/commands/inspect-op003-exception-helper-source-CPU-20261016.py` SHA `cf19a87ef78b77ee2697d96d2f4e054cce0e82fd8ffbed8bc322380b1db2707f`：核domain-design3c2cd3ac...，只读当前FlagGems generic/MetaX sort/softmax/cumsum与backend导出源码、privatebackend并保存SHA/函数/必要片段；不import Torch/FlagGems/Triton，不访问GPU/模型或修改源。静态候选路径不自动等于当前运行时函数对象；后续数学推理与真实硬件资格分开。旧creator不重放，measurement001仍blocked。

当前helper快照已完成 `ROOT/results/op003-exception-helper-source-CPU-inspection-20261016.json` SHA `b492352f5145cc07d74be86a913806cd78bd10cddbf49375a4de1883ee087262`。固定generic sort SHA4f63aadbe42f7dbfab0f0fb295c9dea09d749e292ce1b1e61340f68978e8fab9/softmax d7c6eef628fba956403c1f43f4a2c94dea1142ec8fa532359de5016e3bf9488d/cumsum ef7f010fdc53b3eacef469326bffd030c961887e5fa0ec1c71f861a62793a502；MetaX目录没有同名softmax/sort/cumsum覆盖文件，但不能替运行时函数对象证明。

仅执行新唯一CPU推理/草案冻结脚本 `ROOT/commands/freeze-op003-exception-math-and-validation-CPU-20261016.py` SHA `f8cd6adb9b3e25a064fab044a69b6b38f4f6d2a55959254692547e40542f5188`：核快照及当前依赖SHA，纯整数位键计算、抽取私有/softmax源码与已安装Torch排序header（header非编译内核证据）；独立保存incomplete CPUanalysis。另冻结11组新的最小安全数值验证草案，仅合法k/p，非法指针排除，finite控制+正负NaNpayload/+Inf/allmasked/tieCDF/mixed/kOnly/pOnly；execution_ready=false/GPU_launch_allowed=false，没有启动器，不执行GPU。全部旧计时/数值失败和19FG保持。

### review038：CPU静态边界与最小安全验证草案

CPUanalysis `ROOT/results/op003-exception-math-CPU-analysis-20261016.json` SHA `9eac22082fa890a9741416a6c12a5472023a16dea049d8786d697c349752d960`，verdict=incomplete_hardware_exception_semantics_not_determined。当前generic `floating_to_uint` 原始位键计算：负NaN(ffc00001)→003ffffe低于-Inf→007fffff，正NaN(7fc00001)→ffc00001高于+Inf→ff800000；±0 generic键分别7fffffff/80000000，私有thresholdkey都80000000。这只是CPU整数等式，不证明native CUDA/MetaX sort的NaN/tie次序。Torch已安装SortingCommon存在handleNaN comparator、cub.cuh存在segmented-sort接口，但header不是编译内核/本shape路径证据，不能假设NaN一定排最后。

softmax_inner在线分支确有all_neg_inf局部保护；最终globalmax/reduction/output的全屏蔽或Inf行仍涉及IEEE不定式与后端lowering，不能声称源码完全没有保护或已经错误。BF16exact的!=判断、NaNpayload转换和radix路径、私有first_keep的monotoneCDF前提与原参考逐元素<=/last-token保留等价仍需硬件oracle。没有复现任何新数值counterexample，也没有定位M1计时原因。

新最小数值草案 `ROOT/manifests/op003-exception-numeric-validation-draft-20261016.json` SHA `339b3f03401bc56158eda081476d9a64d583c2773eb5daa33b67ca7af246e60d`：execution_ready=false/GPU_launch_allowed=false；11fixturegroups（CDF组3方向，实际须冻结13比较行），两finite控制+正负payloadNaN/mixed/+Inf/allmasked/合法异构/kOnly/pOnly，单seed42。非法k/p指针完全排除，只设计CPU guard；真实current17FG oracle、同clone/fullfilter、int32位值及NaN/Inf/mask分项/alias/kp未变/选中错误上传全保留。未来总预算180s/默认stream/至少1.6GiB可用与实际allocation审查，无Stream/graph/benchmark/模型请求；尚无实际testsource/启动包/结果，本轮不启动。

下一步仅CPU形成实际fixture、13行精确表、内存/输出边界/无非法k/p/原oracle/异常传播检查，未完成前草案不可执行；不能默改执行标志/自主立即GPU，measurement001 candidate/revert不因未来数值成功解锁。当前服务/源/19FG/无callerworkspace未动，最近07:49resident/fullenv/source/disk通过仅作为明确时间的历史事实，不冒充当前空闲或新graph。

### review039实际fixture与CPU准备包（执行前记录）

仅准备11组/13比较的独立数值诊断，GPU入口和watchdog均硬关闭（False在import/GPU/输出前检查）。本地22项CPU检查通过：payload exactbits/非法k-p拒绝/行列边界/单与多全屏蔽覆盖/完整plan构建缺字段/SHA/已有输出拒绝/精确PID-birth/私有PGID清理/模块不导入GPU库。mock只证明控制面与fixture元数据，非数值/graph/性能。

CDF中心固定为actual17FG CDF[V//2]，below/exact/above单列3行；allmasked组为全部64行，mixed组多行全屏蔽，kOnly/pOnly各仅第0行全屏蔽，完成one/some/all覆盖。非法k0/k<0/k>V/pNaN不实际launch。结果比较与CDF64个p值校验需要显式诊断同步/readback；此行为不计时，不在生产backend/support新增同步。reference/candidate同clone/17FG/fullfilter，每项错误和bit差异保留并停止，选中错误向上传。

预计4份常驻FP32大张量254279680bytes，knownprivate scratch估计287834112bytes；vendor sortworkspace/allocator碎片不能由CPU完全界定，未来需1.6GiB准入、1.25GiB私有peak停止条件，不能把CPU估算当硬件显存通过。未来180s总诊断预算与仅新私有PID/birth/PGID超时清理已编码，当前两执行门保持False，无GPU运行/计时/请求/重启。

所有新ROOT/commands文件（前三只上传，不执行GPU入口；第四只CPU审查/冻结plan，不翻转flag）：
- `op003_exception_numeric001_prepared_20261016.py` SHA `35b95c855f1c678cac81f5b64b995fd0c3312d9a2dd655714e4a9aa6b0e76c43`
- `op003_exception_numeric001_watchdog_prepared_20261016.py` SHA `46eab6691ef35610685ae5306d4e1cc3c348dd7b392757683c7f282f480c1b05`
- `test_op003_exception_numeric001_CPU_20261016.py` SHA `0bf632cae52baaca87f8c41641dd83a0ede5bc32d465b402b5a742164afd6213`
- `freeze-op003-exception-numeric001-CPU-packet-20261016.py` SHA `b24136c33066319cfea6fee40ffc73d365d1d6a58c49c1ebfd60a20fa3e399e3`

CPUreview/准备plan使用op003-exception-tool001命名空间，避免被未来数值输出保护误判成既有native结果；既有measurement001/旧GPQA/数值creator全部保持不可重放。本轮仅执行CPU单测与计划冻结，不执行prepared数值入口。

CPU归档v1在已核22项CPU单测断言之后、写plan/review之前因sha helper直接对str调用read_bytes失败，0GPU；源b24136c3...与错误stdout保留，不重放creator或旧CPU单测。新唯一 `ROOT/commands/continue-op003-exception-numeric001-CPU-packet-20261016.py` SHA `1a6a2af26eb09063fede67c5d9117aeb474bcb9f97dfc3c90b62702e82b86e1a`：先断言plan/review/numeric边界全空与原失败sourceSHA，exclusive保存原错误log，只把helper规范化为Path，并核str/Path两输入一致；复用已审查的不变测试代码/完整构建（不重跑22单测），冻结GPU双关闭计划和CPUreview。原22项本地通过、先前远端通过断言但raw单测stdout未持久化，明确保留此证据边界，不伪造原始日志。新CPU脚本及内嵌代码AST均已本地检查。

### review039：准备完成，等待单次有界硬件诊断决定

CPU准备plan `ROOT/manifests/op003-exception-tool001-prepared-plan-20261016.json` SHA `8463434d5625e6afcae653965a0e347ef5b35cbd72969f6838b8f7fd44714a05`；CPUreview `ROOT/results/op003-exception-tool001-CPU-review-20261016.json` SHA `158a7201fcca7f431bc6b44f6dfe11719a4362399ebc3d7c1902c0784ee8c192`。两source执行门均False，完整plan execution_ready=false/GPU_launch_allowed=false。旧归档错误及raw单测stdout缺失边界在review中如实记录；没有新GPU、数值/计时/服务请求。

08:55:43.665650UTC fresh核原API1025146/birth501435120、12355源/fullenv/resident/恢复disk/prefixoff通过、API0/0/startscript SHA6b96...保持19FG，下载内容等价unknown/不允许reload rebind/历史graph不作新证明。下一步只有实际硬件能补异常域证据，继续CPU循环没有等价证明价值，按用户“不自行立即启动GPU”约束暂停automation待决定。

**可批准的具体行动**：仅mx-59/qwen3.6-35B/private GPU6默认stream，对固定M64/V248320/FP32/seed42进行11组13比较，最多180秒；执行前重新核源/env/实例/resident+disk/nativegate/APIidle、GPU6/7仅原TP进程及至少1.6GiB可用，资源不足/任意错误/bit差异即停并保留。只清理本次private PID/birth/PGID；无生成请求、benchmark、graph、新Stream、停服/重启或生产修改，完整19FG/no callerworkspace保持。数值比较和64个CDF参数显式诊断readback不计时，不在生产backend加hostsync；vendorworkspace未知有私有1.25GiBpeak停止线。

若用户授权，先新建不可变执行副本（仅两硬关闭flag改为开启，其他AST/fixture/SHA映射检查相同），冻结独立final运行绑定和实时资源门禁；不能改写这次closed源码/plan，不运行任何旧numeric/GPQA/采样v3-v4/AA/measurement001角色脚本。即使13行数值通过，M1性能unknown/旧计时失败及measurement001永久blocked不变，不能部署或宣称E2E收益。等待期间automation PAUSED，不继续无效轮询/重复CPU审查。
