# accdiag-043：doc81逐层三元状态与LM-head前隐藏状态

2026-10-19用户明确授权：仅8010新增doc81窄埋点、重启一次，19请求/C<=8，保留FP32/i64/QSA M16，首差完整证据，不访问8035/不全量GPQA。方法inference-accuracy-diagnosis及e2e/accuracy minimal-regression；不签formal gate/性能结论，旧164/198 failed/no gate保持。

**终态：19/19 HTTP200、零错误，首次差异已定位到第38层（0-based）MLP分支返回的`output-block`，两种doc81前缀/all8 rank同一元素相差1 BF16 ULP。LM-head前hidden与最终logits仍不同，不能通过C1/Mixed数值一致性回归。** 只完成一次授权重启及预冻结19请求；两类graph7/7、all8实际replay>=384。7248 PT、7434原始证据文件与14590编译成员SHA核验通过，源前后一致，终态8010健康idle；无8035访问、无正式GPQA。以下设计/执行前状态为历史窗口，末节为最终判断。

## 当前事实、设计与门禁

042离线已证all8 attention48+MoE48 FP32编译链，doc81输入/位置/RNG/noise同、CPU概率参考吻合，但C1/Mixed最终raw max1.0625/.5625，缺层和LM-head前hidden。当前只读8010 API941314/start511645150/argv5744d999，health200/空闲，counter9356/3596；执行前再次核验，不操作历史PID。其他服务/物理0–7尤其8035完全不访问。模型容器qwen3.8-flash-opt-ppu07-20261015，物理8–15，沿用既有镜像/挂载门禁。

私有新目录`/opt/qwen38-accdiag043-doc81-frontier-20261019`真实复制当前Plugin，只有model.py新增无返回值观察custom op；去掉这些tap/纯tap条件后的AST必须逐字结构等于当前源。Gems/FGVLLM/engine/权重/tokenizer及FP32 helper原字节保持，不改安装、共享启动脚本或旧私有目录。用现有direct_register_custom_op模式（fake无操作、mutates用于约束producer顺序，实际不改张量），仅新服务bootstrap注册，幂等窄实例；不为其他服务/模型加hook。新tap可能改变融合/同步/时序，定位结论限定本轮，不冒称无埋点因果复现。

逐层返回的是delayed HC三元状态，不把单个residual当完整layer output：保存embedding多流输入；48层各output residual、block、injection；最终mixer hidden及实际选行后的LM-head输入。只为六个doc81 freshPrefix评分请求启用（两个前缀各C1两次/Mixed一次），doc71与背景只原轻量输入/采样/metadata。每个前缀首条C1保存完整目标区间作为reference；后续完整比较直到本请求首个有限差，首差保存全参考/当前值与dtype/shape/stride/请求slot/graph/SHA，此后逐层只保存末token与完整比较已停止的标记。不能用末token一致冒称后续全区间一致。所有层的末token边界及LM-head完整选中行仍保留。每rank参考/首差/窄边界PT预算4GiB，Host自由空间>=96GiB；超预算或缺失记incomplete，不删证据/扩范围。

工作负载严格复用042原19payload，只改opaque header043：8C1评分、7背景max512、4实际Mixed评分max1，max_concurrency8/0重试/无额外smoke或warmup；原seed1234/temp1/top_p.95/top_k20/min_p0/penalties0与1/stop/完整tokens不变。Mixed须目标slot7+7真实Decode，实际input/positions/query/logits-row核验；两类native graph capture7/7、all8至少2真实replay。首有限层差只冻结/报告，不停止预冻结19；真正输入错位/非有限/observer/HTTP/service异常停新补位，在途自然取证，不自动修复/重启。

## 执行与证据计划

CASE=/mnt/nfs/users/jinghao/qwen3.8-flash/20261015-qwen38-flash-next-ppu07-container/accuracy/acc-015-full-gpqa-ppu07-c64-current-i64-qsa-20261018；R=CASE/diagnostics/accdiag-043-doc81-layer-lmhead-20261019/runtime-001。新脚本先在CASE/commands排他保存并核SHA。CPU正反例/AST数学等价/基线完整source检查通过，再唯一SIGTERM至精确原8010 API、等待原树自然退出、仅8–15资源门禁后启动；任何失败都不二次重启、不升级kill。唯一控制器自然ready→19→freeze，禁止重复launch/run。

终态核19raw完整HTTP/token与usage、192输入采样PT、逐rank逐点每边界coverage/reference及首差原始张量、LM-head输入/最终raw是否先变；冻结源与完整日志/编译产物，CPU离线比较，报告第一已观测全目标区间差异和末token差异分别到哪层。缺少内部算子张量则只定位层、不能称具体kernel根因。前台跟进，旧heartbeat保持PAUSED，必要长任务再更新同一监控不建重复。后续埋点扩大、数学修复或再次重启需新用户方向。

状态planned，尚未新建private、重启或发请求。回退入口为042启动与原Plugin源码，用户只授权本轮一次重载，失败不自动回退。

## 执行前脚本冻结

CASE/commands排他保存：control SHA74c47c2dbbf140cdf03527a9133b0c2073c746b0657f4ca398a3de0a6ecba9c3、probe62113a5221eed184a33ca46c0662e883761132619cbf08b5cde8082907af4c11、deployac895b255da30e4b068af37610719390bf27be97fb92c5594734c2c6ae9a2e66、sitecustomize51ba32e9de74828a8db9c85c439a18c73e28a2890a9aa33efbc8b73e82e86273、CPU237734fd33c5ce9e3bda483e676eeb43d4786741b6d12810c5b87b744d87e0e0。042 controller/base probe与027 request/run/launch按既有SHA冻结复用，调用全局只重绑本轮R/API/脚本入口；guard/protected保持只8010，不执行旧8035逻辑。

控制入口依次仅一次`--mode prepare`（CPU谓词/数学AST→私有复制与probe/source/计划/launch），成功后`restart`（唯一SIGTERM/原树退出/8–15资源检查/唯一service launch）、`launch`（唯一controller自然ready→19→freeze）。新private只含tap修改Plugin、run-scoped bootstrap和新独立cache，原Gems调优DB只读backup；模型实际Gems从env041安装加载，PYTHONPATH仅新private及其plugin，不含旧Gems覆盖。原graph/CLI/采样字节保持，启动/运行异常不再重载或自动发额外请求。

prepare已完成：CPU20项/147边界预期/数学AST相等通过，CUDA_initialized=false，回执SHA31c29825702a8ec813df66c1c0f0b0f7f32d210651cf1930483aa01e2d13abe5；deployment36434b67c51880608bf7bf5b117d62cb21cf3c213f3c969698f58721b0a29ecf。仅model.py不同，新model SHAab9b1bfb43880e0b3b3a8b7d15c76725d2e0adfbe4927b766fc3e128c39a5bf1；原FP32 helper及Gems/FGVLLM全源未改。PREPARED SHA bf92619838c08e946c2de639852ae512a8c9b2f10054d2a33391fafa81a12b21，requests9a06ac06a22a59a5f148b10b5ace6871e42893020539d23e89f939d0498e8690，启动脚本原CLI/显存/卡8–15/graph不变，只有private/caches/观察配置改变。接下来执行唯一restart和唯一launch，不再重复。

唯一restart已执行，旧API941314单SIGTERM后原树自然退出，8–15资源门禁通过；唯一driver Host2211997已启动，等待本次ready再自然执行19。后续不得再次restart/launch/run。新stop/launch/CLIENT_PID原件保留，不用日志container PID冒充Host API。监控前台，旧heartbeat仍PAUSED。

终态CPU审计预存`CASE/commands/accdiag043-audit.py` SHA00ef3008ab5a1772b0cae8513f9c8c86a99201a45c70324abb646cea4723b1c4，等原driver退出、FINISHED/FINAL_EVIDENCE及已派发响应齐全后只CPU/OMP-MKL1执行一次，新cpu-frontier-audit-001。核原始HTTP/token/96评分/64组分布、6doc81×147×8边界coverage及全部PT SHA、首差两侧完整张量、末token各层及LM-head差异、完整日志前缀。相等current full张量未另存，故先前全目标区间同值是在线torch.equal证据，CPU独立可复核末向量及首次差异两全张量，不冒称所有相等区间都有独立current全量重审。新增审计脚本不触及正在运行的probe/控制器/采样或服务。

终态Host审计预存`CASE/commands/accdiag043-host-final.py` SHAce3648225294620d2cf26ead74eeb871b651d46521bf5b2c6e5b0811de24467b，只在driver退出且FINAL完整后执行一次；核源前后/原冻结manifest、补全8rank与service/client日志尾、顺序读取已保存编译archive核每文件SHA及FX归约dtype计数、当前8010精确绑定/health/idle，不发推理/信号或访问8035。归档缺失/预算超限如实记录，不重复冻结覆盖原件。

## 终态与CPU离线审计（2026-10-19）

- READY18:03:39+08；8010 API2199565/start511947447/argv SHA5744d999，与终态完全一致。唯一driver2211997/start511950937自然退出；CLIENT_FINISHED18:07:29、FINISHED18:08:49，FINAL_EVIDENCE齐全，未自动重启/修复/追加请求。
- 19请求全部HTTP200、errors0、0重试；prompt9356/completion3596与API counter及完整token一致。12评分请求max1、7背景max512的`length`为预定短探针，不是60K不收敛/完整答案复现，不能以本轮token一致认定旧症状已解决。
- 六个doc81评分×147边界×8rank=7056 frontier PT，另192实际输入/采样PT，合计7248逐一SHA/尺寸/可加载性核验。每rank882边界PT、完整coverage；64组采样对照、96 sampler PT及全部API token与rank0非discard实际采样前缀核验通过。C1重复hidden/raw/prob/noise/token exact，Mixed四点均实际slot7+7真实Decode、目标computed0/完整prefix/graphNONE，无输入绑定问题。
- 原7434冻结文件前缀SHA均匹配，完整service/client/8rank日志尾已另存`post-controller-audit-001/`；14590编译archive成员全部核验，all8 FX均96 f32 branch collective+2 bf16 embedding（静态图节点，不是运行调用计数），FP32不是仅Python绑定。all8 native实际graph replay>=384；i64/M16与FP32 helper源保持、private模型除tap外数学AST相等。无真实FIRST_ANOMALY/HTTP故障/非有限/非法内存访问。

### 首次完整目标区域差异

两种前缀778与808，对照seq4→17及6→18，全部8rank首次记录都在layer38/`output-block`：仅1元素不同，目标区域相对row254/channel1407（flat651647），C1=.0093994140625，Mixed=.00946044921875，abs=6.103515625e-05（1 BF16 ULP）。global排他marker最早18:06:30.655898+08/rank1/seq17/step38；不是rank1独有故障，8rank首差张量值与位置一致。两侧完整张量、原始shape/stride/storage与实际请求/slot/graph绑定和SHA已保存；seq17目标全区域778×2560、seq18为808×2560。

最早marker原件`R/runtime/FIRST_DIFFERENCE043.json`；示例原始完整两侧：

```text
R/runtime/rank1/frontiers043/cmpl-accdiag043-q017-0-9e3023a3/first-difference/reference.pt
  SHA f6234816fda9017243d8e468ffa93f44898b0f0479a658dd6b24d6001cbe9bfd
R/runtime/rank1/frontiers043/cmpl-accdiag043-q017-0-9e3023a3/layer038-output-block.pt
  SHA dc8ee2228c5310461029c581bf571c5177cf05bd709817b2b81e6b5dc2d14356
```

源码确认`output-block`是`self.mlp(mixed)`返回并完成其适用TP归约后的值，前面仍包含MLP HC mix→router/专家/合并路径。它不是完整三元HC状态，也没有当前层MLP mix/router/专家/pre-reduce中间张量，**不能把边界首差直接归因到MoE collective或某个kernel**。layer38此前完整输入状态/各边界相等由在线torch.equal证明，equal current全张量未保存，独立CPU只复核其末向量与首次不同两侧全张量；不冒称此前所有current全区域可离线重放。

### 末token、LM-head与分布

| doc81前缀 | 末token首个观测差异（0-based） | LM-head前hidden差异 | raw logits最大差 | 过滤后概率L1 |
|---|---|---|---|---|
| 778 | layer39/output-residual，71元素，max .0009765625 | 2385/2560元素，max1.0 | .34375 | 0 |
| 808 | layer40/output-injection，1元素，max .0625 | 2405/2560元素，max .75 | .296875 | .062101779505610466 |

全8rank上述边界和最终hidden/分布比较一致，跨rank所有已保存末tokenfrontier差异为0。rank0六个请求各自model-final-hidden末行与实际选中的lmhead-input逐位相等；combined all8末向量一致证据表明没有目标logits行选错的信号。**进入LM-head之前就已经不同**，所以不能用“只是LM-head shape或采样器”解释本轮；也未证明LM-head本身绝无附加误差。12评分token/noise C1/Mixed仍相同，不代表概率分布相同；808概率5项不同、max .029392659664154053。doc71 343/353 raw max .9375/.65625、概率均相等，未对doc71做本轮逐层capture。

### 判断、限制和下一证伪点

分类numerical/execution-shape divergence，**层级边界reproduced，具体内部算子根因unconfirmed**。本轮观察链支持context行38层1ULP差异之后、末token后续层及最终hidden/logits出现偏离，但未通过只替换该元素/算子reference的干预证明单一因果，不能称该1ULP已解释原60K循环或正式低分。下一优先点是layer38 MLP HC mix输入、router/专家输出及内部FP32归约前后，用同输入CPU/独立reference区分舍入放大、shape路径差异和实现错误；需要新增在线埋点/再重载时必须先向用户申请，不自动执行。

本轮tap/custom-op屏障和CPU同步改变图切分/融合，数值不同幅度较042改变但未消除，不按“变小”称修复或性能收益。首差后其余上下文只存last-token，不保留全池KV/GDN历史，不能声称完整内部因果现场。所有原始请求/HTTP bytes/完整API token、96完整logits/prob/noise/RNG、首次差异及各末行、编译/日志已保全；无新formal gate，旧acc015164/198 failed-score/no gate与性能阻塞保持。服务留在本轮同实例，heartbeat仍PAUSED，不追加请求/自动重启。

审计回执：

- `R/cpu-frontier-audit-001/report.json` SHA49fdef30d56afccc47c283526894174029c08164aa74cc22746155604ca10f81；manifest8044b566d0229998c7ba4a25100fb53211909424ad44b1ce665361cd5ad2e09f，status complete-scoped-layer-localization（证据完整，不是数值一致或正式精度通过），CUDA_initialized=false。
- `R/post-controller-audit-001/report.json` SHAdb74debd7a64f095c6882422d22447fe0841153d7fed19c90c1ba856514f177b；manifest29b823e06dbd1743055cb16568ebd0178dda1b9894187977209c3ff0e7359866。
- 编译archive SHAa0e50749e09e80c5df2280f3a54b584fe2fb6d18bcd64bb71e7fd1ad06cd5fe1。终态8010 health200/running0/waiting0/preemption0；新推理请求19、服务重启1、审计新增推理/信号/8035访问均0。
