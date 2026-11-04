# accdiag-042：移除旧Gems路径覆盖后的19请求同前缀回归

用户2026-10-19明确授权：去掉旧PYTHONPATH覆盖，仅重启8010加载env041新版FlagGems，保留FP32归约/i64/QSA M16，按此前19请求/C<=8同前缀精度对照，完整证据，不访问8035，不重跑全量GPQA。模式`e2e/accuracy` `minimal-regression` + inference-accuracy-diagnosis，bundle6e94a080dd3b64544c535e1fd4bda506f55516374d14d0f8ca6aa148bba2c7b2。旧正式164/198 failed/no gate不改，不恢复性能优化。

## 范围与唯一变量

- 仅PPU-07容器qwen3.8-flash-opt-ppu07-20261015、8010、物理卡8–15；其他服务尤其8035完全不探测/访问/操作。旧8010只读解析为API3152794/start511117420/argv SHA5744d999；执行前重新核验原身份/空闲/source及镜像挂载，不能按历史PID直接停止。
- 新服务从当前安装绑定加载：Gems master f0aa7f12+env041兼容/i64，Plugin a696859b+PR4553cb373b1+本地显式及MoE FP32 helper，FGVLLMb4d3382原生PPU M16。无算法补丁新增、无依赖升级；保留当前安装所有文件。启动时清除继承旧PYTHONPATH，必要的run-scoped观察bootstrap只含本轮探针，不含旧Plugin/Gems路径；不编辑Docker不可变ENV、共享start-model.sh或旧源。
- 复用036窄观察机制（固定输入/位置/请求映射、12评分×8rank raw logits/过滤概率/noise/RNG/token、FP32/MoE实例/QSA函数来源、实际graph replay），只更新配置/源码SHA与本轮opaque标识。无新增逐层/全KV抓取；完整证据限定本次明确边界，不能冒称完整全池状态或无观察时序影响。
- 唯一停止操作是向精确原8010 API发一次SIGTERM，等待它的原树自然退出，端口及卡8–15资源门禁通过后唯一launch；不升级kill、不再重启/自动回退。启动/取证异常保留日志与编译产物，停止新增请求，在途自然返回，不自动修代码/重新启动。

## 冻结workload与判定

复用034 requests.json（SHA115e640c204845dd6043b255b8b91b5822377d5a2976c09b9be6a46d1c0aeb5e），只改header本轮042。8条C1评分（doc71/doc81四个固定前缀各两次，max_tokens1）、7条背景max512、4条Mixed评分max1，共19、并发最高8、0重试，无额外smoke/预热请求。原token-ID prompt、seed1234/temp1/top_p.95/top_k20/min_p0/presence0/repetition1/stop保持；单token评分的length为设计上限，不当60K无final症状。

前缀/位置/输出行/采样边界错位或真实HTTP/非有限/服务异常停止派发；有限分布差异保留全部原始PT，离线定位首组差异，不靠相同token判分布一致。实际Mixed必须各rank target slot7+七条真实Decode，提交前ADMISSION不能替代实际绑定；背景提前排空则本轮覆盖incomplete，不补发。原graph两类capture7/7及>=2实际replay、all8运行时包来源/修复SHA与MoE绑定分别核验；采样全向量与实际noise/argmax、HTTP完整token与usage及rank0 prefix独立核对。

同前缀passed仅指原12评分、重复/C1-Mixed完整logits/prob/noise64组相等和本轮证据/graph/来源覆盖有效；不代表60K/C64/正式198题或所有dtype/layout验证，不签formal gate。与034旧完整分布比较仅组合升级上下文，不能归因单一新算子。

## 外部产物与执行入口

CASE=/mnt/nfs/users/jinghao/qwen3.8-flash/20261015-qwen38-flash-next-ppu07-container/accuracy/acc-015-full-gpqa-ppu07-c64-current-i64-qsa-20261018；R=CASE/diagnostics/accdiag-042-env041-same-prefix-20261019/runtime-001；private bootstrap/cache=/opt/qwen38-accdiag042-env041-20261019。命令先apply_patch本地保存、传CASE/commands排他创建并核SHA后才执行；所有旧实验和日志保留。新独立编译cache/日志目录，未声称冷缓存与旧热缓存完全同一；不做性能结论。

状态terminal：19请求完整结束，但同前缀分布一致性目标未通过，FP32运行时事件证明另有缺口（原生CPU回执incomplete）。原heartbeat保持暂停，服务保留本轮健康候选，不自动回退/重启/追加；旧164/198/no gate不变。任何缺失或未覆盖如实记录，不修改原marker或隐藏失败。

## 执行前命令冻结

CASE/commands新增且排他保存：control SHA b2ff01bbf4d34dc01a2271d6160ad70ff36e563a27cd86fa6e0fdf25a8777e88、probe SHA4d05ec47d1280837e82fb54769dd3ebbb26115a9747e95b458379c1da1e8a84f、sitecustomize SHA2c86c0f1f93a25f63151b961362cb9edeeb2df6fbf8586272e23df0a6ff7780e、CPU SHA77de500d52b232ea9bb750b46c752e00c7691fecb4dd8e84f7f89b9bb4dc4192、offline audit SHA2e174114b980faf87bd53ba0bed6951f239504943e96e8ffcfcb70cfc800acd9。本地AST通过，原027三个调度方法与022记录/HTTP辅助按已冻结SHA选择复用；guard/protected/sources/freeze/ready/restart已覆盖为仅8010，不执行旧8035门禁。

新private只含042观察bootstrap与独立vLLM/Triton/Gems cache。原017 tuning DB以SQLite只读backup保存到本轮新cache，保留选择不共享可写DB，不清旧cache。唯一restart前marker拒绝二次启动，SIGTERM后仅query物理8–15空闲，禁止全卡或8035查询。终态另外保存本轮编译缓存manifest和<=4GiB时的原始归档；超预算明确incomplete留原cache，采样同步/窄Pythonwrapper可能改变编译与时序，不将本轮局部结果外推无埋点环境。

CPU18谓词/3脚本AST通过，CUDA_initialized=false，实际回执排他保存commands/accdiag042-cpu-result.json。prepare完成，PREPARED SHA90e5ec9575d6182f7e5df1e8691f0008ac1cbe3d31ef9b88a5157e7b0778e174。原8010当前API3152794/start511117420、health200/空闲零counter，master及8文件本地差异/Plugin/FGVLLM完整源、镜像/挂载/权重tokenizer事实校验通过。QSA调用签名只读确认首参确为位置q，原窄wrapper兼容；未修改观察数学。新launch清除旧路径，只设置042 bootstrap，三包从实际安装导入。接下来仅一次restart和唯一driver launch，不重复执行。

唯一restart已执行，旧树单SIGTERM后自然退出、仅8–15资源检查通过，LAUNCHED原件保留；唯一driver Host946774已启动，先ready再19，后续不得再次restart/launch。请求清单SHA832de825bed08ad7f64f4e4ae7d923530e306ba256b4af1379baced345c399d8，原19 payload不变。17:04:31+08只读仍worker初始化阶段、无READY/分发/完成，不将已启动冒充精度通过。

17:11:35+08只读：driver946774/start511646748仍原实例；all8 `implementation-loaded`实际Gems均为新master路径、critical SHA一致、各48个MoE FP32实例绑定。主图torch.compile完成，原生PIECEWISE capture7/7，FULL当前4/7，尚无READY/RUN_STARTED/模型请求或新错误。Docker全局ENV未改，但新启动显式只保留042观察bootstrap，旧Gems覆盖不参与本轮worker导入。

终态CPU审计入口`accdiag042-audit.py`已冻结上述SHA；原driver退出且FINISHED/FINAL_EVIDENCE齐全后，仅一次CUDA空/OMP-MKL1执行，核12评分×8rank、完整HTTP/token及8×8重复/C1-Mixed对照，保存首分布差异完整输入/采样PT；019/034等旧分数不代替本轮。Host终态入口`CASE/commands/accdiag042-host-final.py` SHA4cdeb1e8b40fdceef3b386d2a62f26b12e59c91849433eca639ced5b0b4c5d92只核旧manifest前缀、追加日志完整尾、新缓存archive顺序读SHA及当前8010/source/计数，不发新请求/信号；任何归档或完整性缺失明确保留，不自动重新freeze覆盖。

17:15:53终态：19分发/19完成/0在途/0错误，19原始HTTP均200；driver原实例退出、CLIENT_FINISHED/FINISHED/FINAL_EVIDENCE齐全。CPU审计001在usage汇总遇到可选`prompt_tokens_details=null`，`collections.Counter.update`触发`TypeError: unsupported operand type(s) for +: NoneType and NoneType`；退出1，原001目录和脚本保留，不当模型失败。仅离线工具修正：新增`CASE/commands/accdiag042-audit-v2.py` SHA55b35dd3e0050fcd2ec64ba6ebdf84acb1e6726ecd1312509156c5fc5eaf1772，只汇总数值usage、输出新cpu-audit-002，其他断言/原证据均不改。上传核SHA后同CPU-only环境执行一次；不发推理、不重启、不加埋点、不改原001或任何marker。当前all8实际replay至少256，QSA运行时命中；FP32 Python事件未捕获（实例绑定已核），该门禁缺口不绕过，完整分布结果与路径覆盖分别报告。

## 终态结果与判定

服务于17:12:11+08就绪，API Host941314/start511645150/原argv SHA5744d999，原控制器946774/start511646748已退出。19请求/C<=8/0重试均HTTP200，prompt9356/completion3596与服务counter匹配（12个评分各1token、7个背景各512token），所有length为本轮预设短上限，不是60K推理不收敛复现。没有新非法访存、真实HTTP失败、非有限/输入或采样异常marker。没有访问8035或全量GPQA。

all8实际输入与位置/query/logits-row正确，四Mixed目标均slot7+7真实Decode，192份PT=12输入+12采样/rank，完整HTTP token与rank0实际采样前缀吻合。两类原生capture7/7、每rank实际graph replay至少384、QSA原生PPU M16实际调用已核。各rank48个MoE FP32实例绑定且源码前后不变；**运行时`actual-FP32-helper-collective`事件为0**，可能受编译内联/观察边界影响，但未在本轮证明原因，不能把实例绑定提升为实际归约dtype证明，不能按通过处理。

8rank数值结果一致：32组C1重复比较的raw logits/prob/noise全向量逐位相同；32组C1/Mixed的raw logits均不同，其中两个point的过滤概率也不同；所有noise逐位相同、采样token仍相同。rank0代表数据如下（其余rank相同）：

| 冻结point | C1/Mixed raw logits最大绝对差 | 过滤概率L1 | token相同 |
|---|---:|---:|---|
| doc71 prompt343 | 1.241943359375 | 0 | 是 |
| doc71 prefix353 | 0.703125 | 0.06098020076751709 | 是 |
| doc81 prompt778 | 1.0625 | 0 | 是 |
| doc81 prefix808 | 0.5625 | 0.03248566947877407 | 是 |

这些point的think-end248069及EOS248046/248044过滤后概率均0，不代表60K末端概率或原问题已修复。首个比较顺序中的分布差异为rank0 seq0→15（不是按GPU时间已证明的首个分歧层）：244561个logit不同、max1.241943359375，概率与noise相同；完整两输入/两sampler PT已冻结到`R/cpu-audit-002/first-distribution-difference/`，原始PT和manifest保留。CPU检查326个原文件前缀SHA、96评分及64组比较、96组034上下文比较；CUDA未初始化。034和本轮之间同时更换过Plugin/FGVLLM/Gems，旧数据只作组合上下文，不得将本轮差异归因于新版Gems单一变更。

**判定：有限同前缀分布一致性目标failed；整体覆盖回执incomplete（FP32运行时事件缺失），非passed。** 旧034的成功不代本轮，19短请求不能证明长推理/C64/198题精度，不能签formal gate或恢复性能优化。当前源/权重tokenizer未改，服务健康idle保留，后续若需新埋点或重启先向用户说明并等待方向。

## 证据完整性

- `R/cpu-audit-002/report.json` SHA28864e3ed19bf7cb558d3c92f5dd089c8824aba593f87a62d9ce0ca28788b82c；manifest19856206ef170b17633f60802ca3e5bb50a1e5d187ea162b4f8317af926b04cd。001失败目录未覆盖。SFTP上传新audit路径失败、随后SSH排他传输核SHA成功，第一次找不到新文件的检查未执行模型/审计；这些控制工具失败不当模型错误。
- `R/post-controller-audit-001/report.json` SHAc70b0bf897e4e228299f0e6ea35860be5b12fe5f6e7be35c13f15501568679b4；manifestb4d96d31cfba47f12924ab149e5c87e9e8b553151d45e18de872caec990276ae。原326文件SHA/追加日志前缀、全8rank完整事件尾/服务及客户端日志、源前后一致核验通过。Host旧固定字段CPU_audit_SHA为null（它只找001报告），有效CPU报告是002，不能把null称未审计。
- 编译cache归档13286个文件独立逐项SHA通过、无失败，archive SHA c3635bd07c27a7318828ebcdde8c3ea21e61cc3dddac93bb6d654b043b18c4f2；原cache/完整service日志保留。17:18:31 API精确原绑定health200/running0/waiting0/preemption0，counter3596/9356，未发新推理或服务信号。
- READY SHA6e3537e368faadb013cc4514b04de39186e15ae1221fe6b4562fd30f61a5d107。只清本次8010的旧PYTHONPATH覆盖；容器不可变ENV和共享start-model.sh未改。无全KV/逐层状态快照，本轮全向量采样和输入证据完整不等于完整全池因果现场；观察同步及新编译cache时序限制仍保留。

## 2026-10-19用户授权的离线续查（执行计划）

只使用042既有compile manifest/归档、8rank日志/输入/完整sampler PT及当前源核验，确认FP32实际编译数据流，再定位doc81 C1/Mixed差异。0新推理/GPU测试/埋点/重启/8035访问，不改i64/QSA M16。继续同一042记录，不创建新模型测试或覆盖旧CPU回执。

只读初检发现rank0主FX图98个allreduce中96个f32、2个embedding bf16；attention和MoE都已见`.to(float32)→all_reduce→to(bfloat16)`，生成代码也有float32分配传入直接custom op。不能仅凭此代表all8或独立kernel trace。拟新增`CASE/commands/accdiag042-offline-compiled.py`：仅CPU标准库/torch解包旧PT、AST解析生成模块（不import/exec任何编译文件）、核冻结SHA并排他保存`R/offline-compiled-audit-001/`。复制8rank FX图/描述符、涉及归约的生成Python及当前相关模型/HC/helper源；解析全部dtype/路径/源码与图引用关系，核旧输入/位置/概率/noise/RNG、仅输出结构和指标、不重放模型。现有042未存逐层/TP两侧/GDN状态张量，若不能证明首分歧层则明确unknown并给最窄新增取证建议，等用户方向，不自行实现。

离线脚本SHAa91906987087fd93dd7bbc789b2832878aaa9fa0e79e8892cb0ab0819eac2adc，AST核验通过；先排他传CASE/commands并核SHA，再在现有模型容器CUDA_VISIBLE_DEVICES/PYTHONPATH空、OMP/MKL1执行一次。只读既有PT与冻结SHA对应的编译文本；AOT artifact仅读SHA，禁止import/unpickle/执行生成代码。新目录与报告只新增，不覆盖原002或Host终态回执；任何分析工具失败保留ERROR.txt，不作为模型事故或绕过断言。

补充CPU参考计划：新增`CASE/commands/accdiag042-offline-probability.py` SHA fda01cf2a5f9cb3ddc9ee8ced3189bc2ec06ec39f416dcb1783a351800acaad5；按当前vLLM原始top-k/top-p源码公式对96份旧raw logits重算，预冻结max_abs<=5e-7及支持集/token一致，输出新`R/offline-probability-audit-001/`。只CPU/旧张量，不执行原GPU sampler或生成模块，不发新推理、不改服务/采样；该检查只能解释概率是否由已有raw差异造成，不能识别首个模型分歧层。

### 离线续查终态：FP32编译执行链已确认，首个数值分歧层仍unknown

1. **不是FP32 helper未加载/主归约回退到BF16。** 8rank主FX图分别98个allreduce，均为48 attention+48 MoE的96个f32及2个embedding bf16。768个主分支site全部有明确pre-FP32 cast和post-BF16 cast。完整FX图逐rank与042已冻结cache manifest SHA匹配，缓存描述符320个artifact引用全部重核原SHA。
2. 56份实际Inductor生成模块覆盖逻辑device0–7（服务物理8–15），解析得到96个float32输入和16个bfloat16输入的独立代码site；模块会跨层复用，不能把这些静态site数当实际collective次数。FP32 site的真实代码是`empty_strided_cuda(...torch.float32)`→cast/fused-add写入→`torch.ops.vllm.all_reduce.default`→FP32到BF16转换，再交HC。MoE shared/routed合并后也走该链，不是只提高外层attention。两处BF16为主vocab/PLE的查表汇总，不是漏掉的attention/MoE branch。
3. 这些图/模块来自042启动日志指定的独立cache、已冻结manifest与实际8worker来源，042实际请求/两类capture/all8 replay>=384均已保留；因此**编译执行链层面可确认FP32修复生效**。这仍不是新增NCCL kernel trace、不是已保存本轮TP两侧实际数值，也不证明FP32所有中间结果天然逐位不受shape影响。
4. `actual-FP32-helper-collective=0`原件不改。probe是在Python helper中以`STEP>0`记事件，初次编译时STEP0；编译图内联转换并直接调用custom collective，生成图没有这个Python日志调用。因此“无Python事件”不能推出“实际仍BF16”。这补上了原002回执incomplete的编译路径证据，不改写原回执为passed；最终分布一致性仍失败。

**doc81差异的已确认来源边界：采样前的模型前向，而非随机种子/噪声/采样过滤。** 8rank的778/808目标完整input IDs及positions同值，C1 slot0、Mixed slot7+7真实Decode，query/logits-row检查正常、fresh computed0，目标首次Prefill均graphNONE。这里graphNONE只指该首次Prefill的运行模式，不等于没有Torch编译路径或背景graph执行。

- 778点raw max1.0625/RMS .210960；808点raw max.5625/RMS .103696。去除最佳线性比例+平移后残差最大仍约.99950/.59422，不是仅整体logit偏置或缩放。
- 两点RNG前/后状态、实际exponential noise、temperature均相同；变化在保存的raw logits中先于top-k/top-p与采样发生。808的5个有效token概率变化保存在doc81-distribution.json，例如token4082从.1327824146变成.1189442649；token13/494从各.4089985788变成.4151562750。相同noise使本次仍选token13，不等于分布一致。
- 独立CPU按原vLLM ascending top-k20/top-p.95公式重算96份保存raw，最大绝对误差1.4901161193847656e-8（预冻结容许5e-7），支持集与采样token全部匹配。由此当前概率差可以由已有raw差异解释，不需额外假设GPU采样过滤出错。短点think-end/EOS过滤后0不外推60K收敛行为。

### 剩余候选、不能下的结论与下一门禁

当前新Plugin已改为delayed HC combine/mix，FX图确有`qwen4_grouped_gemma_rmsnorm`/gate_reduce/combine_norm、36 GDN core、48 MoE及12 QSA的调用边界；这是调用/编译证据，不是这些算子中哪个先出现差异的数值证明。静态核对HC combine_norm实现保留combine后先舍入residual dtype再做norm的边界，未发现可以凭源码直接认定的漏舍入问题。其相邻BF16 GEMM、前向状态/PLE上下文、局部专家、后续层及最终LM-head的batch/目标row偏移都仍需数值证据，不能只因升级后出现差异就归因Gems、HC、QSA或某个collective。原034完整层张量属于旧Plugin/执行图，不能当042某层仍相同的证明。

042只保存模型实际输入与最终采样边界，没有LM-head前hidden、逐层输出、当前TP前后/HC/GDN状态/PT或完整ngram_context；所以**首分歧层与首个算子仍not-isolated**，不能通过继续静态推断伪造首差异。现有完整原始证据保持，i64/QSA M16不改；8010原Host941314/start511645150仍同实例，本轮0模型请求/0GPU测试/0源码变更/0埋点/0重启/0访问8035，原164/198failed/no gate保持，性能不能恢复。

下一最窄方案（**仅建议，未执行，需用户另授权新增埋点及一次8010重载**）：沿用19/C<=8/零重试，只对doc81两个固定前缀采最后LM-head输入完整向量及逐层窄边界，先分离body hidden漂移与末端投影shape漂移；layer0局部完整目标行重点为embedding→HC mixed→GDN local→attention FP32/castback→MoE local/pre/post FP32→layer output，背景元数据、输入/概率/noise/原始HTTP/token照旧。抓取预算与CPU正反例先冻结；若逐层只存末行，其结论必须限定末行，不能冒充整个Prefill最早分歧。需要扩大到完整目标区间/新状态现场时再明确范围，不自动全池或48层大抓取、不全量GPQA、不访问8035。

### 离线原始回执

- `R/offline-compiled-audit-001/report.json` SHA2d182e3698566bbe2cf44472f42487bd4c5baf86f6e96d3fe930eb389be0c18f；manifest37c2ddfa0f0443fefc672e760d7434e3f766d419876df82fb0bdb803647989a8，115份新增报告/复制源/完整生成模块SHA重核通过。192份旧PT和320个AOT引用SHA通过。包含graphs.json、generated-code.json、descriptors.json、doc81-distribution.json、PT/source/cache-copy manifest。
- `R/offline-probability-audit-001/report.json` SHA744ba254957574ce9878f4c574a9d3463466410efa7bb73477b0efcad35b29d3；manifesta85e8906d3c29f46cd3bb34dad6eb885f6602e567c9f4b97e871c30d5f10a1c9，2内容文件SHA通过；两个CPU报告均CUDA_initialized=false。
- 原002/Host报告仍分别SHA28864e3e/c70b0bf8，未覆盖或改判。前期只读探索有shell引号、猜错HC文件名的工具失败，及AOT二进制不支持pickletools解析；均未执行模型、未写原证据，未使用unpickle/import/exec恢复编译对象，也不当模型事故。有效确认来自已核SHA的FX/生成Python文本和既有运行日志。
- knowledge_delta=refined：从“Python事件缺失导致路径未证实”推进到“通过当前all8 FX/生成代码/缓存绑定确认FP32链，先排除采样后处理，再从尚未保存的前向边界定位”；不能把旧已修TP再次当剩余差异的默认根因。属于同候选的离线补证，不是新增模型精度pass或性能结论。
