# accdiag-031：模型FP32 TP归约后转BF16的同前缀对照

2026-10-20后续正式组合验收：[acc-017](acc-017-full-gpqa-ple-fixed.md#终态177198通过正式阈值7条60k问题仍存在)保留attention/MoE FP32与i64/QSA M16/051 PLE组合，177/198（89.39%）通过0.88阈值，原生gate核验通过。7条60K仍存在，旧031同前缀失败结论不改，不将组合通过当单变量因果证明。

## 执行前契约（2026-10-19）

- 用户明确授权：仅8010一次重启，19请求、并发<=8，保留i64/QSA M16，完整输入、逐层边界、logits/概率/noise/RNG、原始HTTP/token/日志留证；不访问8035、不跑全量GPQA。
- 方法：inference-accuracy-diagnosis + inference-accuracy-evaluation minimal-regression + key-operator-analysis。高风险数值语义候选，非正式精度通过，不解除acc015 164/198 failed-score/no gate和性能阻塞。
- 参照：[029](accdiag-029-tp-hc-boundary.md)原模型同19payload及[030](accdiag-030-tp-reduction-order-shape-offset.md)固定8rank输入机制。030只证明当前矩阵下FP32归约转BF16消除offset差；模型结果未知。
- 远端：PPU-07，容器qwen3.8-flash-opt-ppu07-20261015，8010/物理8–15。只读核验API2727961/start504948954/argv5744d999，idle，counter9356/3523。不查询8035 listener/HTTP/proc，不把历史保护元数据称实时检查。
- 原始产物根：`/mnt/nfs/users/jinghao/qwen3.8-flash/20261015-qwen38-flash-next-ppu07-container/accuracy/acc-015-full-gpqa-ppu07-c64-current-i64-qsa-20261018/diagnostics/accdiag-031-model-fp32-tp-reduction-20261019/runtime-001`；可执行命令先保存到该case的commands，再记录SHA并执行。

## 单变量与设计边界

从真实未挂载private029复制独立private031，不编辑029或共享安装。Plugin模型shim中的两处显式tensor_model_parallel_all_reduce调用改用局部helper：输入BF16时cast FP32→原TP allreduce→cast原dtype；其他dtype维持旧调用；TP1/MLP原有requires_tp_all_reduce条件保持。不修改vLLM、权重、tokenizer、采样、底层collective或MoE内部归约。该实验不声称覆盖embedding/MoE内部其他通信。

helper在模型结构边界内统一实现，不按doc/机器名选择数学路径；目标observer仍仅六个doc81首Prefill、第0层，增加FP32 input/output两边界，doc71为阴性控制。源码scope反变换须与029 AST相同；这仅证明补丁范围，不证明数值语义相同。FP32临时内存和通信字节翻倍有成本，本轮不测性能、不晋级PR，pr_readiness=experimental。

## 冻结请求与停止条件

原029 requests SHA570951ceb0f5296aed86afe55c94f06ca9e73e9c5c3c467e04269183c5e9e690：8个C1单token评分、7个512-token背景、4个真实Mixed C8评分，总19、零重试/无补位/无隐藏预热；仅opaque header变031。完整token前缀/采样/stop保持。评分max1及背景max512的length是预期预算，不等同60K异常。

实际Mixed须all8rank目标slot7/computed0+7真实Decode；两类graph7/7 capture及>=2实际FULL replay。先CPU helper/AST正反例，再一次reload和一次client。有限数值差保存首差异但不提前停止；非有限/输入错位/HTTP或observer错误由现有控制器停新派发，在途自然取证。覆盖不足不追加。任何第二次重启、改埋点或全量请求须另获方向。

## 验证和判定（待执行）

比较C1重复、同前缀C1/Mixed完整目标行、FP32实际collective两侧dtype与BF16 castback、FP64参考、首分歧stage、最终完整logits最大差/RMSE、概率L1/max/think-end/EOS、noise/RNG和API token。与029并列，不能把采样token恰好相同当概率相同。保存原始文件SHA和终态日志尾部，selected pool last-writer不是全历史。未跑长Decode/C64/198题，不能宣称60K问题修复。

结论：terminal，19/19受控请求已完成；第0层TP castback BF16与HC差异消除，但最终doc81 logits/概率差异仍在。候选未达到同前缀最终一致性目标，不晋级正式精度或性能候选；当前8010留在本轮FP32诊断版本，不自动回退或二次重载。

准备门禁已过：CPU32 helper +18 observer/scope检查通过，CUDA未初始化；PREPARED `3bcdcf02459380f5eff8822e08a1c46769bbce6d93cc52a44588f7cbaa364ee1`。候选model `692dc3e1ebe2a7109747c7b4ce168104fcd561863efe7c9d144f2540b0417f7c`，patch `5420e69e91f9937103bea5a190d0b17d9dec9f0a5d09636519aec6975a60f5ec`，runner c3537353不变。18项CPU报告在实验根cpu-tests-001/report.json。已提交唯一restart mode，等待停止/启动回执；未派发模型请求。

10:22:36+08唯一客户端277728/start509238281已启动，等待编译/graph就绪；本轮8010重载已执行，不允许第二次自动重载。终态CPU审计脚本 `CASE/commands/accdiag031-offline-audit.py` SHA `3c6595a964316eaa05ef906dcb5d5a9d3e5ed77bc3b5fc5fa61bdba57dd0b93a` 已排他保存，只有FINISHED/CLIENT_FINISHED/FINAL_EVIDENCE均齐全后在CPU eval容器执行一次，核720边界PT、192输入采样PT、19raw与counter、actual Mixed和029基线对照；无GPU/额外推理。

终态只读Host审计命令先冻结：`CASE/commands/accdiag031-host-final.py` SHA `de2de3ccbbcab6625a8dc2532c3b7c5134ff7c0b31e6539fe7a94c4ea99fc63a`，只核8010当前身份/source/idle、原driver退出、FINAL文件SHA及8rank日志尾部，复制到新post-controller-audit-001，不访问8035/不推理/不重启。原marker/快照不覆盖。

## 终态与实际路径

- 10:26就绪，10:28:17+08全部19完成/HTTP200/0错误与重试/最大C8，4条Mixed均all8实际slot7/computed0+7真实Decode peers；两类graph7/7，全部8rank有508条实际FULL回放。唯一driver277728已退出；stop receipt单SIGTERM原2727961、旧树自然退出、0其他信号。
- 新8010 API Host259670/start509233696，argv仍5744d999；10:30:13健康200、running0/waiting0/preemption0，counter9356/3399与本轮原始API usage总和一致。i64/M16和source前后/当前保持，不访问8035，没有第二次重载/全量GPQA。
- 独立CPU逐份解包核720完整边界PT+192输入采样PT、19原始HTTP/SHA/完整已返回token、实际rank0 non-discard前缀及source/counter。all8rank/six requests的FP32 input精确等于保存BF16 branch上转，FP32 output转BF16精确等于postTP；不是仅按安装路径推断命中。
- layer0两点原branch相同，FP32归约输出仍有30/33个末位不同（max1.4901161193847656e-8），cast BF16后all8rank完整目标行逐位一致，且等于8rank输入FP64求和一次BF16舍入reference；HC output、post-attn也逐位一致。C1重复全部15frontier一致。首有限差异排他marker原时间1792376845.347297/rank5/step39，stage=tp-fp32-output；reference/current PT及所有rank marker均已原样复制，有限末位差不是FIRST_ANOMALY/非法访问。

## 最终logits/概率：没有消除

| 同前缀点，C1 vs Mixed C8 | 029原BF16 raw最大差 | 031 FP32→BF16 raw最大差 | 029→031概率L1 |
|---|---:|---:|---:|
| doc71/343 | 0 | 0 | 0→0 |
| doc71/353 | 0 | 0 | 0→0 |
| doc81/778 | 1.1875 | 1.146484375 | 0→0（该点过滤后单支持token） |
| doc81/808 | 0.9375 | 0.9375 | 0.0923222005367279→0.09724374115467072 |

031 raw RMSE分别0.22670119405657663、0.15376573013237207；808最大概率差0.0449334979057312。全部C1重复raw/prob/noise逐位相同，四个C1/Mixed实际noise也相同；采样token分别1596/4543/1596/494保持，不能用token相同掩盖分布差。doc81 think-end raw logits：778为13.9375/14.1875，808为0.050537109375/0.1484375；实际过滤后think-end与EOS概率均0。这些只是短前缀点，不解释48K–60K的概率轨迹。

因此局部已确认TP分块BF16舍入贡献被阻断，但“只修当前显式TP归约即可消除最终差异”被本轮否证，后续分歧尚未定位。源码另确认`Qwen3_8FlashNextSparseMoeBlock.requires_tp_all_reduce=False`，FusedMoEFactory拥有内部最终归约，本轮外部MLP条件不进入，未改该内部通信；它与其他后续算子均只是待查路径，不能据此认定MoE根因。现有窄PT不包含完整48层新现场，继续定位需另冻结窄观察边界及必要重载范围，不能自动改/重启。

## 完整性回执与限制

- requests SHA `83abcab69cf9fcfa9123c7ede498eeb40fb8df79af0e04a907e00deebeaf902a`；READY `777e27b5c5923adccf3d2fa2ece387e836976c7d44545259c49e4f9afc14c9de`。
- FINISHED `57a575b9c043c78ac3784528dead63f4765010a5412f6a67ade6a5b84f89da84`；FINAL_EVIDENCE `db564a8bfc792d382a6542d69f7835788d4a4aac030df8fff46f80390084d56b`；FIRST_DIFFERENCE_EVIDENCE `de6a25702d7e149c5b3150d5fd9b3698788a302516ec065a72d004c16f47e9cf`。
- `cpu-boundary-audit-001/report.json` SHA `c40eb22715c7bc73f9faaf766599cd35960a34e90f87cd7b50bcfd9aac75436e`，manifest `4d13a259c9e4eab9fbdcdce18886fca8522057dfbde3b6bb62eba05afd26d3e8`。
- `post-controller-audit-001/report.json` SHA `b884fb0e0d681c14c329df65f897ffd163371c3145117caa155d02262c2efe96`，manifest `e664eea5a54a6c04a5b64c22b01d1dd981ca040ce54a22bc031e17336ed598ab`；1098原始文件SHA/大小核验，唯一活service日志追加但原始前缀匹配，另复制完整8rank尾部和service日志。
- 本轮无FIRST_ANOMALY/非有限/非法访问/HTTP错误；有限首差异完整已取证。评分max1、六个背景max512是冻结预算，另一背景315正常stop；不称60K问题复现或修复。完整证据指本轮既有选定范围；没有全KV/GDN pool历史或未捕获的逐层输出，不称完整全模型因果现场。
- 数值/路径检查executed_passed；最终同前缀一致性目标failed；正式精度not_run（用户禁止）、性能not_run，formal_gate=null，root_cause_confidence=local-rounding-confirmed/downstream-not-isolated。原acc015164/198 failed-score不改；监控保持PAUSED，等用户方向，不自动追加/恢复/回退/全量。

知识差量refined：独立算子FP32 castback消除offset误差成功迁移到实际模型layer0/HC，但未迁移到最终logits一致性；未来必须分开“局部边界被修正”和“模型全部差异/长推理根因已消除”，不要仅凭FP64参考一致就宣称模型修复。

工程验证矩阵：目标PPU TP8/BF16 graph=hardware/executed_passed（数值路径及运行稳定）；最终同前缀一致性=hardware/executed_failed；非BF16/空/非连续及补丁范围=CPU mock/static executed_passed，不作设备精度结论；其他模型/平台硬件=not_run（仅本模型私有shim，无共享改动）；独立eager=not_run（非本契约要求）；Plugin正式lint/CI及PR整理=not_run（实验私有补丁），PR readiness保持experimental，不提交/推送。

## 可复现命令（先冻结再执行）

以下文件均已排他上传到CASE/commands：control `1149c69695c820df9c6cc036fb6448ed2fc4e83b224ba4afcfeca547001b4387`，deploy `240602ef9a85be1f50099ad81043c3d034116a51bf81d0975f34d335e14f388c`，probe `5fd2b02498156304b1ce8ce0e7789446450da3bc749510d7acbe372083f2ca01`，cpu-test `ab1f18cfa5cbe0991d2a41e174ceb61e5776924c4744998dff59126bfadfd65d`。精度Skill完整bundle `6e94a080dd3b64544c535e1fd4bda506f55516374d14d0f8ca6aa148bba2c7b2`。

Host依次调用 `python3 CASE/commands/accdiag031-control.py --case CASE --mode prepare`、`--mode restart`、`--mode launch`；每个mode排他marker，prepare不重启/推理，restart仅一次SIGTERM给精确原API，launch只启动一个19请求driver。没有自动恢复/重试。CPU仅容器中CUDA_VISIBLE_DEVICES空、OMP/MKL1执行cpu-test，非GPU/模型精度通过。新private路径 `/opt/qwen38-accdiag031-tp-fp32-20261019`。
