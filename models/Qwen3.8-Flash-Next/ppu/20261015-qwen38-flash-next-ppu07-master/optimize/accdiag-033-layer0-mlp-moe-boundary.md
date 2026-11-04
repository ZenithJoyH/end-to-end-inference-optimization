# accdiag-033：第0层MLP/MoE首分歧窄取证

2026-10-19用户明确授权仅8010新增MLP mix/router/专家输出/内部归约前后窄埋点并重启一次，同19请求/C<=8，FP32/i64/QSA M16保持，保存首次差异完整证据，不访问8035、不全量GPQA。方法inference-accuracy-diagnosis + accuracy minimal-regression + key-operator-analysis。原acc015164/198 failed-score/no gate不改，不作性能优化。

## 冻结设计（执行前）

- 当前原API259670/start509233696/argv5744d999，idle/counters9356-3399；031 model692dc3e1、probe5fd2b024。从private031真实复制private033（不在mount内），旧副本不改；vLLM安装源码保持只读。
- Plugin模型只增layer0 MLP HC六个诊断tap，去诊断if后AST与031一致，包括FP32 helper完全保留。私有observer幂等包裹MoERunner和FusedMoERouter：compiled外层late-reduce两侧只插入diag customop；opaque内部入口、router/topk与shared/routed返回值由CPU快照取证，数学函数原样调用一次、原对象返回，不变cast/加法/collective/dispatch。
- scope仅六个doc81 freshPrefix评分的layer0，既有15个attn/TP/HC frontiers加MLP mix/residual/output、HC输入/权重/输出、MoE入口/router/topk/两local输出/late TP两侧，共32个固定阶段；doc71保留完整sampler/input阴性对照，背景只轻量metadata。
- shared+routed在编译器中会原地复用shared；必须在opaque返回前对两local输出完成CPU副本，保存原pointer/stride/shape和alias时点。沿用原流同步契约，不读取有消费语义的`SharedExperts.output`属性第二次，不改变任何math/状态；_apply_quant_method原返回tuple直接返回。
- 同031原19payload，仅header改033：8C1单token评分、7背景max512、4真实Mixed评分，C<=8/零重试/无补位/无额外smoke。真实Mixed须all8rank完整fresh778/808目标slot7+7Decode peers。有限差保全首marker继续既定计划；非有限/HTTP/输入/observer异常停新派发，在途自然取证。范围耗尽不追加。
- math FP32 helper/i64/QSA M16不变，MoE内部仍保持原BF16归约用于观察，不在本轮修其精度。CPU mock/AST/别名/异常restore/幂等测试先过；仅一次8010 SIGTERM/重载、一次client，graph两类7/7+>=2实际replay。任何第二次重载/埋点修订先报用户，不自动执行。
- 全部raw HTTP/token/logits/prob/noise/RNG、32阶段全目标行/all8rank、首次post-attn差异完整reference/current和日志/SHA外部保存。全局FIRST_DIFFERENCE可能先记已知FP32末位差；另设FIRST_POST_ATTN_DIFFERENCE记录用户目标区间首观察差，CPU再按依赖边界判定，shared/routed并行不能凭保存先后定因果。
- 请求列表/脚本/配置/源身份在执行前保存并SHA，root=`CASE/diagnostics/accdiag-033-layer0-MLP-MoE-20261019/runtime-001`，CASE为acc015目录；private=`/opt/qwen38-accdiag033-mlp-moe-20261019`。不访问8035（包括HTTP/listener/proc），不改shared镜像或container，不提交/推送。

## 结论边界

执行前未把编译BF16路径当数值根因。当前终态已通过实际张量确认all8 local及preTP同而postTP先不同，详见下方最终结论。短前缀19请求不证明60K不收敛或正式GPQA修复，pr_readiness=experimental，正式性能仍阻塞。

## 执行前命令身份

CASE/commands排他保存：`accdiag033-probe.py` SHA `3cf3379049730a90744009e57f216a6893353bf791563d24d0ac061410b3b83f`；deploy `aafe0893a93250c2b6fb1016405661c4f4fd5f75e81bf29e66e17c53db8ce4bc`；control `afae35ca342c4e11b94951f3f2eadc34dd0d93928db210481b4f1fe92fe14566`；cpu-test `ef05ad5d8a2cea05d19aaff268a3209a7169b705ed694b0673763e71f1532fbf`。

先优化容器CUDA_VISIBLE_DEVICES空/OMP-MKL1执行cpu-test，覆盖幂等/原tuple返回/原函数一次调用/异常context还原/副本先于in-place sum/背景与其他层不捕获、首marker不覆盖、数学AST与FP32 helper不变。CPU通过后Host `python3 CASE/commands/accdiag033-control.py --case CASE --mode prepare` 冻结requests/config/launch/镜像挂载和source；再各一次`--mode restart`和`--mode launch`，单SIGTERM只给核验的原8010 API，旧树不退出则停不升级信号；唯一driver等graph/8rank hooks READY再运行原19。无8035探测/全量GPQA/隐藏预热。

CPU30项已通过，未初始化CUDA；PREPARED SHA `e92241252081c6f463504d99f9264d3ce0398096c7bf09492da7985eaae010f1`。候选model `9500834c62f6615a68241841e7af533be5d31f3cd961fc625a163de642b63cba`，patch `5a2807ee04af07b44af2543252a3e196490d320b45a401963f0207cb40d0f0c2`，runner c3537353未改；镜像/挂载/source门禁通过，实际diff已复核。已提交唯一restart mode，等待回执；不追加重载。

唯一restart已完成；11:05:19+08唯一driver1195055/start509494650启动，等待加载/编译/graph，尚未发模型请求。之后只监控现有driver，不再调用launch/run/restart。终态CPU审计预存`accdiag033-offline-audit.py` SHA `99d6315e2c15efe4203ccc9ad878303aeb9a5f03ede690b8ccf086e7776431b3`：只有19均返回且FINISHED/FINAL_EVIDENCE齐全后在CPU eval容器执行一次，核1536边界+192sampler/input PT、原始19raw/token、actual Mixed/全部rank、shared+route/preTP、FP64归约与MLP HC参考、首post-attn分歧，不发GPU/推理。

11:08:54后graph及8rank hooks READY，原driver已开始固定19。11:09:48.492953+08首post-attn排他marker为rank4/step40/seq17/doc81-778实际MixedC8，stage `moe-post-tp`，582781/1991680元素不同、首flat20480、max0.0078125，reference/current原PT和SHA已保存。19已派发/12真实HTTP200/7背景在途/errors0；这是有限差，按原计划继续自然收集，不追加请求。归约前一致性待独立CPU审计，暂不认定实现bug或60K原因。

执行前发现原CPU审计引用未保存的冗余`mlp-branch`名；运行32阶段已有`moe-post-tp`和`mlp-hc-block`足以核对应参数链，故仅另存未执行后处理`accdiag033-offline-audit-v2.py` SHA `6e5d3b9732dcb71d74b08e883a9699b9553b2b7542164124c709df708ea8525c`，直接比较这两已保存阶段，不改埋点/服务/marker。原后处理未执行、保留，不是模型故障。终态只执行v2一次。Host-only `accdiag033-host-final.py` SHA `60fae83dab4efda6d3f1b04c9e1565bcb7a8047fb0b3406307a1c13f2ff344c0`，在原driver退出及终态齐全后核全部原manifest、补8rank日志尾/服务日志、8010身份与source/counters，无8035访问/推理。manifest先计算后排他打开，避免032旧self-entry问题。

终态19/19 HTTP200、0错误/重试、19原始API token与rank0前缀一致，实际计数9356prompt/3596generation；原driver退出。CPU独立解包1536完整边界PT+192 sampler/input PT，report `f55c7b66e21275fc9c221f6a3f21423c17372bf8b33a3227acbba64c5a275fdc`、manifest `c7f696937449454d4be0fc8564b50d35880b281517ee1493eeba4140eb894e35`。all8两point同前缀首次post-attn分歧都为moe-post-tp，之前mix/router/topk/shared/routed/preTP均exact，C1重复32阶段均exact。778差582781/1991680，808差607605/2068480，首flat20480/max0.0078125。最终raw logits最大1.15625/.84765625、808概率L1=.0671414826；tokens仍相同，非最终一致性通过。

Host report `ada0df29d8a6257aa886ba18ce9ec785477e3e277bbfb1715c8e55d471b0c5a7`、manifest `b372ec35b2b827f7901a8fb7469a737729ffea8aca3432ff5316dcd2e762e3d1`：1951原清单文件核验、日志尾/source一致，8010 API1170040/start509488080健康idle、counter匹配、无preemption/8035访问。只剩CPU归约机制对照：执行前冻结`accdiag033-cpu-moe-real-rings.py` SHA `a45bd073060bd5ab3fc22a88840ae88a13c5c2efd8076f90a67139eea95dfa2e`，在CPU eval容器CUDA空/OMP-MKL1，对本轮保存8rank preTP及真实service日志4ring的32rotations计算BF16舍入候选、逐元素与256块覆盖/FP64参考。只写新`runtime-001/cpu-moe-real-rings-001`、不推理/GPU/服务操作；算术匹配不冒充该次kernel trace或独立GPU shape因果验证，不自动修改MoE。

## 最终结论：首分歧是MoE自有late BF16 TP，非本次router/专家局部输出先变

19/19 HTTP200、C<=8、0重试/错误，只有获批一次8010重载；driver已退出。两类graph各7/7 capture、all8实际FULL replay507；每rank IndexFunction/IndexPutFunction运行时来源均为private017 i64且`verified_i64_load_before_multiply=true`，QSA M16 SHA/source前后不变。requests SHA `19287c813c7a22c37386997d9e2bcfa7a9007639f76b079a259b43b4d7b20615`，READY `23db701184a5b9fc9a5dcdc777e083b44866cc23df35ae4f7207a102e6d01a5e`，FINAL_EVIDENCE `120ce9617c3378ae19db2411da33f913b8477d9744245dbc21a8334ab05ac57a`。

- all8rank/两point的实际完整目标行：post-attn→MLP mix/residual→MoE入口→router logits→topk weights/IDs→shared local/routed local→preTP sum，C1/Mixed逐位相同；两次C1的全部32阶段及完整logits/prob/noise也相同。
- 48份shared+routed合并均与保存两输入的FP64加法最后BF16舍入完全相同；shared在compiled原地加法前复制，未把复用后sum误当shared。首新分歧始于`moe-post-tp`，并且每次归约结果all8rank一致。
- 当前attention FP32 reduced仍有30/33个max1.49e-8末位差，但cast BF16后的postTP/post-attn完全相同，不是此次下游首分歧。MoE内部late TP依旧BF16，未被031外层helper覆盖。
- MLP HC residual/norm/logits/weight仍同，只有block分歧传播；全部48份MLP HC及32份attn HC在线输出精确匹配保存输入的FP64公式一次BF16舍入。没有当前HC新增计算错位证据。

| 同前缀 | 首MoE postTP不同元素 | 最大差 | 层输出不同元素/max | 最终logits最大差 / 概率L1 |
|---|---:|---:|---:|---:|
| doc81 778 | 582781/1991680 | .0078125 | 1064481/7966720 / .00390625 | 1.15625 / 0 |
| doc81 808 | 607605/2068480 | .0078125 | 1108801/8273920 / .00390625 | .84765625 / .06714148260653019 |

首post-attn排他marker原件为runtime/FIRST_POST_ATTN_DIFFERENCE033.json；原始reference/current PT、全8rank各自marker、1536层PT、192实际输入与采样PT、19原始HTTP/完整token及服务/driver日志全部按原manifest+Host日志尾审计保全。首flat20480（target row8，0-based）与Mixed target起点7对应；实际778/808目标均slot7+7真实Decode peers、graphNONE首次Prefill。新first marker为有限差，不是非法访存或新服务事故；本轮无FIRST_ANOMALY。

实际运行对象：MoERunner d11a841e、UnquantizedFusedMoEMethod d365f21f、FusedMoEKernel 78f33203；router对象FusedTopKRouter但实际compute为私有Plugin FusedTopKRouterFL 7d32bf00，experts对象/执行apply为TritonExpertsFL d16781c9。TP8/EP1、SP=false、fused_output_is_reduced=false。generic nn.Module.apply元数据不是专家kernel命中，不混用；此处是运行时实例/函数来源+实际边界张量证据，不声称已捕获所有内部专家GEMM kernel。

### 舍入机制CPU证据及限制

CPU真实环分析完成，report `87779b866232bdd2745e08f9137c815a2e840cab90d9d01c0078c66449e63696`、manifest `a06e654f6118b9579f8d9e5503db9b542bcb3217c2fff056984dcf8b629dc2ad`，0新请求/服务操作/CUDA。以本次真实service日志4ring各8旋转共32序列，对两个point保存8rank preTP做逐步BF16舍入：四份在线postTP全部元素均可解释，每256元素块均存在一个共同可行顺序（7780/7780、8080/8080），全在gamma7×sumabs误差界内。与030位置改变分块顺序机制一致，支持BF16非结合舍入，而非当前数据下router错选/专家先变/跨rank不一致。

但这是CPU算术可行序列，不是本次MoE collective kernel trace或新的GPU offset独立消融；不把“匹配FP64一次舍入的差值”当通信bug。输入是完整目标行而非7个peer全部tensor，不代表全KV/GDN历史。新增tap/CPU同步/缓存分割仍改变fusion/时序，033最终概率L1变小不能算精度修复或性能收益。

本轮同前缀最终一致性目标仍未通过；采样noise/下一token相同不等于分布相同。全部短评分think-end/EOS实际过滤概率0不证明长48K–60K结束行为；未重跑正式GPQA，旧164/198 failed-score/no gate不改。

### 下一最窄验证（未执行）

若用户再授权，仅对MoE实际自有late TP增加FP32归约→BF16候选，避免已归约分支二次归约，保持router/专家/shared+routed/math其他路径不变；再次仅8010一次重载、同19/C8检验该边界及最终logits/prob。先设计最窄Plugin/instance扩展点和非BF16 fallback，不修改共享vLLM安装；不能沿用旧graph或gate。当前未改内部归约、未追加请求/第二次重载，8010留在本轮诊断候选健康idle，heartbeat保持PAUSED，等待用户方向。

收尾复核：三份CPU/Host报告及manifest SHA再次一致，分别5/10/9份内容文件独立重哈希通过且无manifest自条目；原driver确已退出，8010精确实例/argv不变、health200、running/waiting/preemption均0，counter仍9356/3596。未发任何额外推理或8035访问。本地state YAML/19-C8/一次重载/禁止8035字段校验与`git diff --check`通过；未提交/推送。
