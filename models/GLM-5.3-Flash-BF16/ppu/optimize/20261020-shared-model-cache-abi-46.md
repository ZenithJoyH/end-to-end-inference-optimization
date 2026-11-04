# 点46：复用PR454公共模型、收敛BF16缓存ABI适配

- 当前已闭环：直接修改实际安装目录，CPU498通过/4跳过；model06整模/graph最小回归通过；新身份独立全量GPQA198题/C64的strict为175/198＝88.383838%，高于86%门槛，原生schema3 gate与最终只读身份/样本审计通过，监控已暂停。源SHA `4fd1f9437257b3ac0728e1099c026e445c8827c4ca9c3f781f712dd14b592193`。不是补充替换或best-of；分类framework/工程收敛，无新性能收益，前五轮失败与精确恢复全部保留。
- 历史15:29：apply03为489通过/4跳过；model01/02失败及精确源码/服务恢复证据均保留，不用旧CPU或cache子图通过代替新整模验收。
- 精确范围：PPU-13 / glm5.3-flash-opt-20260911 / 8011，实际editable Plugin `vllm-plugin-FL-review-20261020-p45-v4`。
- 依赖：PR454 f769696；点45实际磁盘SHA fa1ec556b1b938e700f38de1e40e9c2db466fa0b6f6723185794eaa223c27339，SCM42项。

## 优化方向与瓶颈依据

用户明确要求直接修改安装源码，把旧BF16模型/兼容patch尽量收敛成公共模型的小型缓存ABI适配层，完成模型/graph回归。旧`models/glm5next.py`2492行、`patches/glm5next.py`774行与PR454的模型/KPool/引擎hook有大量重叠，不应作为独立平台模型继续演进。修改前服务仍加载较早点45代码，不能用点45新磁盘CPU测试冒充运行验证。

规划复盘46：点41有缩减Mixed收益但Decode守护不完整；点42真实合批命中但Mixed无显著收益且Decode TTFT退化，已回退；点43新上游迁移原生169/198及用户补充171/198为旧身份；点44/45进行工程整理，当前没有新身份完整gate或端到端测量。历史阶段热点不支持给当前整理代码计算收益。此次优先消除重复模型与cache hook，完成必要正确性验证；不组合调度/MBT/算子新优化。

## 优化内容与适用边界

当前冻结源码工程量（不代表模型或性能验收）：旧模型2492→321行，其中多模态wrapper保持原样，文本部分只是共享类绑定；旧cache/runner patch 774→162行，独立BF16 cache ABI含布局/槽位/地址生命周期适配共176行。全delta13文件、696增/2948删，净减2252行。相对PR454的SCM项42→50，原因是8个原本无需修改的公共文件/回归测试现在参与真正的公共复用，不是又增加8套平台实现；不能以文件数减少替代代码去重。保留config/processor的已知非等价行为，未把这些未验证部分强行替换。

1. 公共模型保留默认类/函数，增加局部组件工厂/方法边界，供BF16适配复用MLP/MoE/Decoder/主模型与权重加载。默认FP8实现选择不变，不全局替换公共类、不按vendor切整套模型。
2. 共享稀疏indexer流程；BF16 query/cache/identity-scale、top-k调用签名与tail写入留在明确的ABI adapter，公共FP8调用保留原样。保持原有数值kernel和dispatch优先级，cache dtype/layout选择不能用served name、机器或厂商替代。
3. 复用PR454 KPool spec/manager与公共物理cache layout，复用已有owned engine/runtime patches；删除复制的整个runner reshape，BF16仅提供所需page alignment/layout与初始化。worker本地初始化与graph地址稳定性必须保留。
4. config与processor已知非等价，未验证前不直接替换或删除；不以减少文件数作为唯一成功条件。非目标平台硬件未测，不把CPU/mock测试写成跨平台验收。

## 正确性与路径命中

最终最小回归：`model06/completion.json`状态`passed_model_minimal_and_graph_not_full_accuracy`，SHA `074fd5837cbce4bc9e2354b8fad2346604160ea67fb060101463bbf94a3668d0`。当前实例`PPU-13:glm5.3-flash-opt-20260911:3532782:520258022`。C1/C8与16383/16384/16385边界原文/usage对照通过；固定11题明确答案11/11。`candidate/final-audit.json`核对真实导入、源码/argv/环境、权重/tokenizer/DB/thead、health200和idle；FULL_DECODE_ONLY capture及9个C1/C8多token请求、三个8-token边界请求覆盖实际回放，不宣称逐rank trace。设备5组bitwise对照各capture/两次replay，真实metadata builder在图外更新固定slot输入、图内只消费，第二次回放改变block table数据，主DB不变。

此次精度诊断技能影响最终设计：整模C8暴露公共builder每步clone与原生图内缓存指针的生命周期差异，因此BF16 ABI子builder复用既有input-batch固定slot buffer并更新数据；物理槽位编码同样显式留在ABI层。未复制runner/manager或修改数值kernel。子图通过不能代替真实builder时序和整模回归；该故障链已在原失败C8范围得到通过证据，正式精度另由下述新198题证明，不冒充长期稳定。公共默认FP8、非PPU与多模态硬件未验，`pr_readiness=needs_revision`，尚不宣称可直接上游合入。

完整精度显式mode=formal-gate：两次原生task/data provenance一致，预检通过且当前稳定身份逐项匹配model06。沿冻结198唯一doc/C64/seed42/temperature1/top_p.95/60K/strict>=.86，独立UUID缓存，无补充/best-of。证据集中`formal-gpqa-01/`，仅由`commands/formal-v4.py`唯一派发；旧formal-v1/v2/v3均未运行。原生请求34:58完成、formal.exit=0，strict=175/198=0.8838383838383839>=0.86。不是沿用点43的169/198、补充171/198或更早173/198。原生8题timeout标记、0空/乱码，显式truncation字段0，仅表示这些样本字段的观察，不等于证明零60K触顶，也不增加精度门槛、不自动重跑。

18:14:32 +08最终只读审计通过：198唯一doc、strict-match/flexible-extract共396行完整，所有原始题目/provenance/filter/分数与冻结契约匹配；重新统计strict答对175。当前实例仍为3532782/520258022，真实源码/argv/环境/权重文件清单/tokenizer/DB/thead逐项与评测开始一致，health200、镜像谱系/挂载一致。原gate用原评测manifest重验；fresh runtime因采集时点不同另存新hash，只比较稳定身份，不修改旧证据或签发伪造rebind。`final-readonly-audit-v2.json` SHA `acd0605c1c6f1d2edf5f2c3e0de2b24d3ddb88935e42ec5f58c5c26026ce8ae2`，gate SHA `7235b3b77c6b886289afb54c9a742caea4890bb9e2603bc05bc3c178952d42b0`。heartbeat `glm-performance-20261018`已收到PAUSED回执。本点保留并停止，无性能测量、自动补跑、源码/服务变更或提交推送；后续正式性能仍须先做当时身份/gate检查，源身份改变则重新精度评测。

2026-10-20 17:42 +08只读跟进：原生日志已完成187/198（94%，elapsed29:35）；评测控制器PID/start_ticks与冻结派发一致，模型实例3532782/520258022仍一致、health200。尚无formal.exit/completion/run-record/accuracy-gate，不提前计算或判断达标；没有发新模型请求、修改源码/参数或重启服务。监控继续，待原生正式计分与最终身份核验。

以下为按发生顺序保留的诊断记录，各轮“待验证”只描述当时状态，不覆盖上述最终最小回归结论。

15:38更新：model01设备cache数值对照通过，GPU0 T8/T9均与原函数bitwise一致，每个shape真实capture及两次replay通过；但新整模在worker init_device、权重加载前失败，TileLang `libcudart_stub.so`缺失`cudaDeviceReset`。控制器已精确恢复13路径/index至原fa1ec556…及原参数服务，rollback最小回归/11明确答案/graph审计通过。只读独立进程证实：原注册只映射PPU libcudart（符号存在），再导入公共runtime新增TileLang stub（符号缺失）。根因是新增公共activation plan注册过早导入公共runtime/_capture_baselines/MHC可选依赖；拟改为懒回调，BF16标记或非GLM直接返回，不加载不用的FP8计划。保留公共模型复用，不修改CUDA库、环境变量或vLLM；新CPU契约须在fresh process验证早期注册未加载公共runtime/MHC。失败和回退证据保留于model01，不把cache子图通过当作整模通过。

首轮实际安装目录490项CPU检查：481通过、5失败、4跳过（150.43秒），新增21项共享模型/缓存ABI检查通过。失败触发精确9路径/index回退，源SHA恢复fa1ec556…、原服务未重启且health200；未进入模型验证。原失败`cpu.xml/log`、`apply-failure.json`与`cpu-rollback.json`保留。

调用inference-accuracy-diagnosis，incident=p46-shared-public-CPU-contract，先区分继承问题/新增回退。源码发现三项MHCPost失败：公共API为obj+4张量，点45BF16的4张量API却复用了`mhc_post`键并被thead策略强制选择。另两项失败涉及公共engine hooks/activation plan未注册。先在已恢复点45精确源码上复现同5项，不拿静态怀疑当根因；诊断命令`commands/diagnose-baseline-v1.py` SHA `e33da6f889379e6be25435844e68b250d418446a7b28aa83eef253585f414102`，无模型请求/服务修改。必要修复仅拆分BF16 MHC键并复用公共注册，保持BF16 marker隔离FP8 worker plan；仍属点46正确性闭环，不叠加性能改动。

复现命令已在恢复后的原点45版本执行并返回失败，v2执行前还将读取原生XML严格确认5个failure。准备v2：`commands/apply-v2.py` SHA `b40dd883a0e2e3af34793c0d3ee1b3ec4f833974f710002344768a666e7a4d15`，`shared-model-v2.patch` SHA `93e1daf70081e792741a53496d9c031b1487b9715b14a3abc9e2214feeef611b`。全13路径、净减2493行；补充三项ABI/plan隔离测试，同原范围预计493项，不跳过原失败项、不放宽断言。thead.yaml唯一必要变更是将四张量`mhc_post`改为`bf16_mhc_post`，使公共obj+4张量接口不再被BF16候选抢占；数值provider不变。其余服务参数/DB/其他库不变。失败仍精确回退，不自动重启。

原点45诊断5/5均复现同错误（39.137秒），明确继承的CPU契约问题，不是点46首次引入。apply02在CPU前停止：编排错误把新增变更清单中的YAML也交给Python AST解析；已完整恢复13路径/index、原服务健康，未发模型请求。准备`commands/apply-v3.py` SHA `754c8babc193c391d99a35833aeac2582d978beac211b749afd6d8baeba67673`，源码补丁与v2完全相同，仅按文件类型使用AST或YAML解析，输出独立apply03目录；不盲重跑模型或更改门槛。

调用本地inference-accuracy-evaluation，显式mode=minimal-regression。先CPU/注册/可选依赖/缓存shape与参考数值，再在实际安装目录应用补丁、重启精确目标，核对真实导入、参数、权重/tokenizer/DB/thead及其他库不变。冻结C1/C8、多token重复、明确答案和16383/16384/16385边界；保留原响应和候选响应、graph capture及至少两次replay证据。模型/graph失败时调用accuracy-diagnosis，停止晋级，必要时恢复精确文件/index和原服务。

缓存/调度与attention实现整理按高风险处理：最小回归通过不签发正式gate，完整GPQA仍需新身份formal-gate（198唯一题、strict>=0.86，冻结生成参数沿既有契约）；不复用旧171/198或173/198证明新代码。未获得有效新gate不进入正式性能比较。本轮不承诺完整性能验收。

## 性能效果

not_run：本轮不改MBT32768/maxseq64/TP16/BF16/FULL_DECODE_ONLY/关闭前缀缓存，不把减少代码量或CPU测试当作端到端收益。正式四场景仍未验收。

## 决定、风险与回退

planning46-lifecycle复盘：model01/02导入时机故障、model03 factory编译故障、model04/05整模C8的cache ABI/lifetime故障均在model06最小范围闭环。先前几何/组合设备图没有覆盖“图外build新张量、图内旧地址”，最终设备测试与真实builder生命周期对齐后整模通过。Prefill与Decode已有正确性证据；Mixed/稳态性能未测，新身份累计性能收益未知。新身份正式GPQA175/198与最终审计已通过，本优化点保留并停下，不自动开性能新实验；后续性能比较不能将代码减少量或历史收益归属于本版本。

用户授权修改目标私有Plugin、重启目标服务及模型/graph回归，不含commit/push。保留原42项dirty；实施前冻结全部源文件/index、实际安装身份及启动参数，精确备份受影响路径。服务生命周期仅作用这个目标容器/8011及其关联进程，不碰源适配容器、vLLM、FlagGems、FlagGems-vllm、权重/tokenizer或交付脚本。无证据不得删旧路径；未完成时记录incomplete，不宣称小适配层已验证。

## 外部证据

2026-10-20 18:12 +08：原生全量结束，formal.exit=0，strict=175/198=0.8838383838383839>=0.86，已生成schema3 gate。gate SHA `7235b3b77c6b886289afb54c9a742caea4890bb9e2603bc05bc3c178952d42b0`，run-record SHA `7e0d59a232bca15f9a8819295aa04a11dc82557b69ee0104a0c823c2f15f5c56`，completion记录前后身份不变。准备终态只读复核`commands/final-readonly-audit-v1.py`，SHA `93041e738159b98bc8a68679b88c16827ffa1a30956a77be1c61e434ae1925b9`；只重新采集身份、重验既有gate/198题所有filter和计分，不生成、不补跑、不修改任何服务/源码/采样字段。最终审计完成前不将本段当作当前实例最终绑定结论。

审计v1尚未执行，静态检查发现native gate-check要求manifest整文件SHA一致，不能把新采集runtime证据hash直接当作原gate绑定。保存v2 `commands/final-readonly-audit-v2.py`，SHA `20209b1fada9d5ba5815c23f3b57ef0c6ca4ffeb5f26b61060c1a0e044878280`：原gate使用原评测manifest重验全部原生证据，另外独立比较当前fresh manifest的全部稳定身份和原实例/源码/权重等运行键。不改任何旧hash、gate或manifest，也不伪造rebind；仅只读采集和证据验证。

正式GPQA先前各命令均未执行；v4仅把前置条件改为model06原生passed，SHA `1296c8c3b16b72e5baa5b9c67a82c001683bb86c606137fc0d9611b8bab251c9`，契约/数据/计分规则与工具包仍完全不变。

model05的组合producer+kernel设备图5组通过，但整模C8仍复现同一KPool decode invalid page；因此布局假设不足以解释整模失败，不宣称已定位完成。新的静态差异：公共TailBuilder每build返回clone，而旧BF16使用input-batch固定slot地址。apply08拟仅在BF16 cache ABI子builder中把公共结果copy回既有固定input buffer，保持逻辑值并复用原内存；不复制计算、manager或runner。新增B1/B8/重复build地址和值CPU对照（公共clone地址不同、BF16固定原buffer），设备v7改为**真实builder在图外更新固定slot buffer，图内仅执行消费者kernel**，避免前版producer也被捕获而漏掉生命周期问题。正式GPQA继续未启动。

准备`commands/apply-v8.py` SHA `d5149e4ce4f0267b5edf6c5a41b4b21acc927f37085a83c1797832be2f21acaf`，v7补丁SHA `da7707a80dc79765b573f91f0ca099baeb8f7ca32ae23a9dd429910feb7351bf`；model06控制器SHA `5eab4150b56f41902c3268c0cdaa8465295e994f5d699eed3ff6edb6f07e0197`，设备SHA `5e2ac97d351478bbacdbab2f8330749493fa17fcddc032bf1d64092698cefb6e`。仅model05精确恢复完整审计后应用；硬件模型未过前保持问题开放。

apply07原生501项CPU完成：497通过/4跳过，新源SHA `aa2b36faf5d691f5e7e35553b8d50f25265efb444d453484460ba9ea6274ff16`。重启前将设备测试增强为**实际公共slot producer+服务同FlagGems白/黑名单策略**，第二次replay改变block-table数据，避免手填slot掩盖producer或地址更新问题。私有micro DB从服务DB同SHA复制，隔离新micro shape可能的调优写入，主DB不变；只做正确性、不比较性能。原v5控制器/设备命令未执行，准备`commands/model-control-v6.py` SHA `7d95407d6cadd628e46dcb7d07832d8dc87c9fc3261c2ac1948c4b412d72e050`、`commands/cache-graph-v6.py` SHA `e1464e759d002c29826c42bea441b48781ef0dc07c5c97ece58d7e4a772f4d87`，目录仍唯一model05，其他契约与阈值不变。

正式精度仍未运行：model04失败后v2未执行，v3草案仅改为必须依赖model05 passed回执，命令SHA `8ae3ed7d1ea128bc0ebcb66cd391dc2b30d03470ecd1bc114468a2b57be182c4`；不放宽任何精度或最小回归条件。

model04已完成真实11/11 FULL decode capture（compile208.44秒、profile/cache/warmup337.78秒，非稳态性能）；但C8纯Decode（序列位置不一致、输出2–4token）触发设备invalid page，UMD明确函数`_kpool_decode_update_batched_kernel`，NCCL是后续上报。回归失败触发原服务/源码自动恢复，正式GPQA未启动。已调用key-operator-analysis，按实际FGV `_thead/ops/kpool_compress.py`核对：内核按`tail_slot // (tail.stride(1)//tail.stride(2))`解码物理页，公共TailBuilder按自身spec.block_size生成逻辑ring slots；vLLM原builder又会copy传入kernel block size，缺少显式tail ABI约束。当前这是有源码/设备指向的布局假设，不能仅凭NCCL或capture成功判根因闭环。

准备apply07：BF16专属TailBackend通过既有PhysicalCacheLayout描述符统一builder与公共runner的环粒度，不复制公共manager/runner；ABI将公共逻辑slot转为数值provider所需物理slot，packed ring直接原样返回、无新kernel。新增CPU6组覆盖物理页宽4/16/384、非零block/负slot、真实公共reshape和builder入口；设备扩展为C8、block最高29、1无效行，比较原内核显式physical-slot oracle和新logical adapter，prefill seed/Decode均bitwise并各两次replay。原kernel/vLLM/其他库不动。`commands/apply-v7.py` SHA `f9a351ce29212548128c5f40298f2ffc0fe08e28cbc685992e264be2e3c5185c`，v6补丁SHA `e73d6993a16b56b0399755f0bdc4e9ede3adde26aef6f726dbe08a2612295968`；model05命令SHA `911025beb7902245f96e3656dcb87bc827410ec076b3da810d89407ccaf6b955`，设备命令SHA `8d3c38cc8e442e1aedf1f28dba42edb607022e4809aab1b18c644c8e0956ace3`。仅model04恢复审计完成后执行；未验证前不晋级或启动GPQA。

apply06实际完整CPU通过，源SHA `4f5f04f880d42a3faf2d93c463a1766eb1fc6051989e28c210600fa797b2d36c`；重启前机制证伪探针保留真实staticmethod/CachedOp描述符，factory分支复现相同SourcelessBuilder Unsupported，构造绑定分支fullgraph两次调用通过。该对照不替代硬件graph，但证实绑定时机是可控制的编译差异，不需要再改描述符或数值实现。model04唯一派发，冻结同一模型/graph回归契约。

在再次重启整模前增加CPU机制证伪探针`commands/abi-dynamo-probe-v1.py` SHA `8a2f08cf9e2a2a03b608e66b9ab0c335e577e8dd08302c254522ccb1574101a8`，保留真实class-level staticmethod/CachedOp描述符，仅替换数值叶子为CPU乘法；分别比较factory查找与模块属性绑定的fullgraph两次调用，避免只mock实例属性而漏掉描述符问题。不执行设备kernel或模型请求。

正式GPQA命令v1未prepare/dispatch，因model03失败保持未运行；准备v2仅改为依赖model04原生passed回执，SHA `05a2cb10f523385fef25ebbe350ea08d337b1741e8eb4a9c61e6d67ab71b2742`，其余冻结测试/计分/身份规则与工具归档不变。

model03越过设备/通信初始化并完成权重加载，证实可选依赖故障边界已消除；新故障发生于Dynamo编译：`indexer_forward_bf16 -> ops.rotate_indexer_query`，缓存factory返回的ABI对象没有追踪source，`CachedOp`触发SourcelessBuilder Unsupported。已冻结`model03/failure.json`及原日志，自动恢复中，未启动正式GPQA。修复仅在构造indexer时一次绑定原ABI对象，forward从模块属性读取，不动态取factory、不改数值provider，增加CPU fullgraph/two-call最小复现测试。准备`commands/apply-v6.py` SHA `6c250c29f20426d6a2120fbc060cb4b79c35c1b548673804bae5c52d09c6592e`、v5补丁SHA `57bdb1c1c95eb11a24ff6cbf3c11b31b9b94af1c48219210fbff59df00d07e44`；model04命令SHA `6b389a0c6843dc8bd94a4edef2b73e3bb9fb77a58c60109dcb31aa000298ad96`，cache命令SHA `36223c1e038b9590fee96fd4a3772ebd945637a187989531de9f2253a24a9f57`。仅model03完整回退审计通过后执行，不把调通前步骤当整模通过。

apply05已实际CPU通过，新源SHA `20fd63183bbdf65aa334ba0b10e786c73d5dc315df1e1b4dae3b7777217f04ed`，model03唯一派发。增加无device函数调用的机制探针`commands/import-lifecycle-v1.py` SHA `b82305c245bc1e9194d57e3548089a68dda99891c0294f8a463dc482710151af`：真实安装目录提前导入模型类→核对未用MHC/runtime及stub未加载→执行故障边界的FlashInfer CudaRTLibrary符号绑定，只保存证据、不调用reset/分配/通信/模型。formal脚本尚未传输执行，草案修订为仅接受model03完成回执，当前SHA `be169c5ae2bcd5f20ca2d287fbe657e5554d229ff87a6ca56fc4159bc71c4c97`，替代前述未执行草案SHA；正式契约不变。

model02仍在worker分布式初始化阶段出现同一TileLang stub符号错误，原自动恢复进行中；此前“注册提前导入”只覆盖了一个入口，不能宣布根因已完整修复。新的具体入口是共享model.py顶层直接导入公共MHC：vLLM在init_device前查询模型状态/shape也会导入模型类。修订为共享Decoder的三个默认MHC构造factory内部才导入原公共类，BF16仅覆盖factory，不复制forward/数值实现。fresh-process契约扩展为提前导入实际BF16模型类后，runtime/MHC均未导入且`/proc/self/maps`不出现TileLang stub。准备apply05 `commands/apply-v5.py` SHA `fb444ebbd5fff3a8e9cccd3bf27ec5ba490cb101efb9f66c7267fa980e8c91c7`，补丁v4 SHA `89feffeb763963f12dff392614205a43c0440a3f92dfdc886d4e3cd16ea45b9c`；仅model02恢复完成后执行。model03命令SHA `abd25e7b97f2bb24852f069d912f2c5ecc6879c64a55e1201d0c80b27e6ac5fa`、cache命令SHA `8a17a530eb7b05144492893e4ae88736d70702946849b7cb9e4f5093d22cf121`，保留同一回归契约、不发GPQA直到整模通过。

apply04已实际通过494项CPU（490通过、4跳过、0失败，117.31秒），源SHA `e608fd32cd22320892ce48c58cdb26367c0905ab32025d9379451999dd697d59`。新增fresh-process懒导入隔离断言通过；model02已唯一派发，设备cache T8/T9旧新bitwise及各capture/两次replay再次通过，整模启动/请求回归进行中。

按高风险cache重构的formal-gate触发规则，准备新身份198题命令`commands/formal-v1.py` SHA `9ce63ec8197b9fbb68b7f1f039a5a0d57ea482547b40407dbd57e5e3b839d639`，工具归档SHA `d94c622d75ad63101979ece809c1c8e111b12df02bbd36648191d5f77eb4814e`。只有model02原生完成passed、当前身份逐项一致才允许prepare/dispatch。冻结198唯一题/C64/seed42/temperature1/top_p.95/60K/strict>=.86，独立UUID缓存、无补充或best-of；先原生task两次provenance和preflight，再唯一正式执行。本地精度Skill bundle `6e94a080dd3b64544c535e1fd4bda506f55516374d14d0f8ca6aa148bba2c7b2`，显式mode=formal-gate覆盖点46，不复用历史分数，不自动性能优化。

model01回退闭环后，准备独立apply04/model02：`commands/apply-v4.py` SHA `61fbd0a44063bdf9409211100decb05fed5fca956e41caca74d74cea3f859224`，`shared-model-v3.patch` SHA `bc9e3ac439374e36190aa9e8fbad37e075df1bf23754257c741a9f4a43570bf3`。增加fresh-process注册懒导入契约，原493项全部保留；仅改plan导入时机，不修改数值provider/测试门槛/服务环境。CPU通过后唯一`commands/model-control-v2.py` SHA `9da44922670b84d1c827bc977c685b73cc202096ec807101d7f69b9b59a89361`和`commands/cache-graph-v2.py` SHA `48c1d96606a4940b3d3855e53c368a57df36bd10bb7d5e7e0e84bd3d978ad6fd`执行同model01模型/graph契约；原轮所有证据不覆盖。

模型回归控制器执行前保存`commands/model-control-v1.py` SHA `fe61e8aa0ba5f2dd36cee1b4503c850f6ba28bd2ae96a0227132360788c669a7`，设备cache回归`commands/cache-graph-v1.py` SHA `cd22699101603e46b59baeb2ba758cbfe9e7f21bf332c21775ab474c56cd2b08`。只有apply03 CPU通过才允许唯一派发model01：先对仍加载旧代码的原实例跑固定C1/C8、三个16K边界和11明确答案并留原始响应，再停精确目标；用原函数AST/同数值provider对照新共享cache，GPU0 T8/T9各bitwise对比、真实capture和两次replay；再用完全相同argv/环境启动新模型，复验全部边界原文/usage及11答案、capture日志和多token Decode覆盖。CPU源码检查不是这组设备/模型验证。cache预算600秒、启动1200秒，失败恢复13路径/index及原参数、再次最小回归。此控制器不发正式GPQA、不测性能、不提交推送。

首版源码已形成：原2492行模型收敛至314行（其中原多模态wrapper未变），原774行cache/runner patch收敛至136行，BF16 cache ABI独立122行；公共模型仅增加局部工厂/方法、共享indexer按物理dtype适配。全delta9文件，414增/2949删，净减2535行，不以文件计数代替复用程度。尚未应用/模型验证。

执行前冻结`commands/apply-v1.py` SHA `d15ebebf5c5d33de8523bd3e05f72100e474ffa31e94c2ab60edc83675955ee6`，`shared-model-v1.patch` SHA `e42b2fa83c7088da7f1f6083096dc27a204b8add8125ee60b7ac7aab583066cd`。仅修改实际安装目录9路径、原index与7个既有文件有备份，新2文件按SHA回退；在安装目录运行全部glm5 CPU及原95契约，失败恢复精确路径/index且不重启服务。通过后另保存重启/回归命令再执行，不由此命令发模型请求。

唯一新远端根：`/mnt/nfs/users/jinghao/glm5.3-flash/optimize/e2e-opt-20260911/resume-20261020-point46-shared-model-cache-abi`。新执行命令与补丁须先保存并记录SHA；当前源身份与只读预检复用点45file-consolidation-04的已核验回执，实际运行再次对照无漂移、health200。后续执行/回归证据持续写入本记录，不建history或每命令MD。
