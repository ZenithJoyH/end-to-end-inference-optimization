# accdiag-032：post-attn之后MLP/MoE路径只读定位

## 范围与先验（2026-10-19）

用户要求继续定位第0层post-attn之后首分歧、重点MLP/MoE内部归约，保持FP32显式TP、i64及QSA M16，不访问8035/不全量GPQA；新增埋点或8010重启须先告知。本轮只读当前源码/本轮缓存和已保存PT，允许CPU离线核验和排他保存新审计产物，0新推理/GPU测试/重启/运行时修改。方法inference-accuracy-diagnosis、key-operator-analysis；不是模型精度评测新轮次，不签gate。

031已核all8rank两个doc81点：layer0 postTP castBF16、HC output、post-attn相同；最终logits仍不同。内部MoE归约未改是待查假设，不可直接认定首分歧或60K根因。TP算子029–031知识只用于选检查边界；其他模型/平台的MoE调参结论不迁移到本例。

## 当前事实及证据计划

8010 API259670/start509233696/argv5744d999，health200、idle，计数9356/3399与031终态一致。私有model SHA692dc3e1、probe5fd2b024、runnerc3537353；源码不改、i64/M16保持。静态链：post-attn → mlp HC mix → Qwen3_8FlashNextSparseMoeBlock/Qwen3NextSparseMoeBlock → MoERunner → shared+routed输出相加 → runner内部TP归约 → MLP HC combine → layer0 output。外层requires_tp_all_reduce=False避免二次归约，也使031外层MLP FP32 helper不进入。

初步只读检出031 private cache共8份带layer0 post-attn的生成模块，包含moe_forward_shared与其后all_reduce；需排他复制完整模块、源文件及descriptor，CPU解析dtype/数据流，核实际graph/rank绑定与未覆盖数值边界。先保存命令/SHA再执行，远端root为 `CASE/diagnostics/accdiag-032-post-attn-moe-reduction-20261019`，CASE仍是acc-015-full-gpqa-ppu07-c64-current-i64-qsa-20261018。原始031文件不修改。

现有probe STAGES031仅15个attn/TP/HC阶段，mlp-mixed/mlp-branch/output即使源码有tap也被save过滤；不能将编译tap存在当已保存张量。审计将枚举所有已存031 PT/manifest，避免误用028未带FP32候选的旧MLP张量。若不足以定位，冻结最窄新埋点建议，等待用户方向，不自动重启/改probe/发请求。

状态：terminal-offline-analysis-complete / 首个MLP数值分歧未定位 / 等待新增窄埋点及一次8010重载授权。

执行前保存命令到CASE/commands：`accdiag032-snapshot.py` SHA `6c64d1d162383c98a555b4551a7995bda69257675cbb1249cbee449ed24b9899` 在优化容器CUDA_VISIBLE_DEVICES空以标准库读取/复制既有源码和cache（不import/执行模型或生成模块）；`accdiag032-cpu-audit.py` SHA `2e8bd45fb5325c8c919b9e07f6d1691dcc91d3b624dd1a8c13a82bb58da2f505` 在现有eval容器CUDA空、OMP/MKL1解包旧031 post-attn PT、核SHA/全目标行/跨rank及MLP保存缺口。产物snapshot-001和cpu-001均排他新建，失败保留现场、不自动覆盖/重跑；没有GPU/推理或新服务埋点。

终态只读命令先保存：`accdiag032-host-final.py` SHA `ac964ff022a64765986747edb9c4ab6503456171b76c2bdfa85746eea341a905`，精确读取8010原API身份/health/counter、snapshot源和编译文件SHA，并核CPU/快照manifest，排他保存HOST_FINAL.json，不访问8035、不推理、不修改源/埋点。

离线工具问题：Host v1校验失败于两份manifest的自身条目（open('x')先创建空manifest，再计算包含自身的dict，故自条目bytes0/SHA空文件）。只读逐项诊断确认仅`manifest.json`自身不匹配，全部源码、8cache模块及报告无变化；不是模型/HTTP事故。旧脚本和manifest保留，不改写。新增`accdiag032-host-final-v2.py` SHA `6b5945182cfa128c238e4c4304501c0922e563a1edb767559600068d53cbf7fe`，仅对精确已确认的空自条目显式记录原因，其他文件仍逐项严格匹配，排他生成verified-content-manifest-v2.json与HOST_FINAL_v2.json。不是重跑模型或更改原始证据。

## 已证实、待证实与源码边界

1. CPU重新逐份解包48份031 post-attn PT：全目标778/808行（BF16×10240），6请求×8rank。C1重复、C1 vs Mixed及跨rank均逐位相同，SHA与031终态清单匹配。因此最后已证明一致的数值边界仍是layer0 post-attn。
2. 模型model SHA692dc3e1的3937–3949行：MLP HC mix → `self.mlp(mixed)` → `requires_tp_all_reduce`条件 → MLP HC combine。SparseMoeBlock把该条件设False，不能把外层helper当全模型TP精度覆盖。
3. 当前engine `model_executor/layers/fused_moe/runner/moe_runner.py` SHA `d11a841e24f46a14884d36334b83387370cd8232679d8569a6a06eb3a6918eb2`：_forward_impl内gate/router/专家计算；forward解包shared/fused，行709–714先相加，再_maybe_reduce_final_output，行451直接`tensor_model_parallel_all_reduce(states)`，没有上转FP32。shared单独early reduce与late reduce互斥，不应把两者算成双重归约。qwen3_next.py SHA885ce324、Plugin MoE factory SHA d39eee91的完整副本已保存，未修改engine。
4. 实际本轮private031 cache中8份layer0生成模块均精确匹配`post-attn`层号0（不是先前误看到的layer10），每逻辑设备一份。每份包含`moe_forward_shared(mixed,mixed,mixed,...)` → shared/routed两个返回值 → fused_add原地复用shared缓冲 → all_reduce(`tp:0`) → mlp-branch。fused_add kernel的`in_out_ptr0`与`in_ptr0`签名均`*bf16`，store回BF16，再无cast直接归约；rank0编译文件SHA `0711f2c83042bc469c652375f6e386148d230b3bed4186295c7cb7853a47beed`，归约行4092。完整模块及8份签名/数据流/SHA见snapshot报告。**这是编译数据流证据，不是该归约前后数值不同的证明，也不是独立kernel trace。**
5. 当前模型配置hidden2560、512 routed experts、topk10、routed/shared intermediate均640。Plugin可能替换router/quantmethod/experts dispatch，opaque MoE customop遮蔽内部张量；仅凭源码选择器不能宣称TritonExpertsFL或某vendor kernel已在线命中，后续需保存实际类型/函数source/impl_id。不要只观测topk加权moe_sum而漏掉shared+routed相加后的TP归约。

| 数据流边界 | 本轮已有数值证据 | 首分歧判定 |
|---|---|---|
| layer0 post-attn | 48 PT重新CPU核验，全目标行/跨rank相同 | 已排除到此处 |
| MLP HC mix / normed residual | 原代码有tap，但031 save过滤未存值 | unknown |
| router logits / topk IDs / weights | 在opaque MoE入口内部，031无张量 | unknown |
| shared / routed local outputs | 只有编译返回值和BF16签名，无实际值 | unknown |
| shared+routed preTP / 内部postTP | 8编译模块确认BF16直归约，未取两侧值 | 高优先级嫌疑，未证明首差异 |
| MLP HC combine / layer0 output | 031未存值 | unknown |
| 最终logits | 031已核仍不同 | 分歧必在最后已同边界之后的某处，尚不能保证在layer0 |

原028带48层MLP PT对应不同数学候选，031已改变attention TP，不能拿旧028的MLP首差异直接套当前031。有限BF16舍入与实现错误须等实际all8 preTP输入及postTP输出后，以FP64参考/真实布局及归约顺序再区分。

## 原始回执

远端根（完整）：`/mnt/nfs/users/jinghao/qwen3.8-flash/20261015-qwen38-flash-next-ppu07-container/accuracy/acc-015-full-gpqa-ppu07-c64-current-i64-qsa-20261018/diagnostics/accdiag-032-post-attn-moe-reduction-20261019`。

- snapshot-001/report.json SHA `6190b125e072b01e8cce62df4b94044762d26d0cc585913e67d0b65ac9f6cbbe`；25份复制文件含8rank完整模块及当前源，verified-content-manifest-v2 SHA `b03ffa293cae9f890dc288b39e47303572c22bc9993835fdeff9ed99923f4d8c`。
- cpu-001/report.json SHA `b060c6c95e0f44ab7308ca0652fd90467fa749f10c108037a1377e04258c95ab`；CPU1线程、CUDA未初始化；verified-content-manifest-v2 SHA `ba14c28adacc4c5d5e0cf6a80449233680c78e8f730e4e8d92e5d9dac75a77ed`。
- HOST_FINAL_v2.json SHA `17b9a38781ab216dd0492f158b6064e8768a0ea984ae032bab1bac16ea9382af`；API259670/start509233696不变、health200/idle/counter9356-3399不变；25份源/cache原件与副本SHA仍同，FP32/i64/M16保持，新增推理0/重载0/8035访问0。旧清单自条目错误单独记录，未伪装原manifest全通过。

## 最窄下一步（仅方案，尚未授权执行）

需要仅8010私有observer增加layer0窄边界、重载一次，保持原数学/FP32/i64/M16不动，建议沿用031相同19请求/C<=8/零重试/不追加：

- MLP HC mix的mixed和normed residual；router logits/topk IDs/weights。
- MoERunner实际类与quantmethod/experts_cls/impl来源；shared local、routed local、二者相加preTP及内部postTP的完整目标行，含dtype/shape/stride/目标偏移、rank/请求/graph绑定。若已有early-reduce分支实际进入，也须明确记录选择，不能假定。
- MLP HC combine输入及layer0 output；保留031 layer0 post-attn、最终完整logits/概率/noise/RNG/原始HTTP/token对照。仅现有六个doc81 freshPrefix目标写全张量，背景只轻量元数据，不扩成48层大抓取。
- **必须在原地shared+routed相加前立即复制shared/routed**，否则编译复用shared缓冲会把事后“shared快照”变成sum，失去局部归因。alias/copy时点也保存。数值差保存排他首差异原件；真实非有限/输入错位/HTTP/observer错误才停止新派发，在途自然取证；19范围未覆盖不补位。
- hook优先放Plugin私有observer、幂等窄实例/真实源校验，不编辑vLLM源码或共享安装。新埋点可能改变同步/融合和时序，须CPU正反例、graph capture和两replay后判定；若全部layer0 MLP仍同，则记未覆盖后层，不自动再扩/重启。

目前仅可报告编译路径确认和数值证据不足，root_cause_confidence=not-isolated。原acc015164/198 failed-score/no gate/性能阻塞保持；不修MoE精度、不加埋点/重启、不新发19请求，先等用户方向。知识差量refined：将“内部MoE自有归约未覆盖”从源码嫌疑推进至当前8rank生成代码的BF16晚归约数据流；仍不能把编译路径或注释当首个数值差异。

精度表述补充：fused_add本身把BF16指针load上转FP32做加法，再store回BF16；本轮证实的是**该BF16存储结果被直接作为TP归约输入**，不是“加法所有中间算术都在BF16”。最先分歧也可能在更早mix/route/GEMM或后层，待新增窄取证才能判断。
