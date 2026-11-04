# accdiag-020：7条空最终答案的离线证据分析

## 授权和范围

用户2026-10-17明确要求继续定位7题，重点doc178提前EOS，先分析已保存索引/状态/token，不重跑全量GPQA；需要重启或新埋点先报告。本实验使用`inference-accuracy-diagnosis`、request/output-health分类，仅CPU分析冻结证据与匹配源码。不发任何新推理，不改服务/模型/采样，不操作8035，不执行GPU单测，不恢复heartbeat。

来源为[acc014正式评测](acc-014-full-gpqa-qsa-m16-i64.md)，有效分数176/198=88.89%和原gate不改写；7个空输出为doc79/88/90/127/145/164长度60000，doc178在24token后提前EOS。首次异常已确认出现在rank0实际采样前缀，非HTTP超时、评测器凭空制造或60K截断。

当前分析对象是当时实例`ppu07-8010-4022615-487850554`的QSA M16+i64带诊断组合。只有原生/冻结证据支持的路径可作为结论；共享pool的record/pre-post只保留最后执行者，不能将36份文件当成36层独立完整历史。读取PT使用CPU评测容器、CUDA_VISIBLE_DEVICES空、torch.load(map_location='cpu', weights_only=True)、限制CPU线程，不加载模型权重或执行GPU计算。

## 原始证据与计划

CASE=`/mnt/nfs/users/jinghao/qwen3.8-flash/20261015-qwen38-flash-next-ppu07-container/accuracy/acc-014-full-gpqa-ppu07-c64-qsa-m16-i64-20261017`；本次新输出目录`CASE/diagnostics/accdiag-020-output7-offline-20261017`，准备时只做排他创建。脚本先保存到`CASE/commands/`，执行前记录SHA和命令，不能覆盖前三份freeze。

只分析如下已有材料：

- `diagnostics/terminal-audit-001/`：7异常完整返回dict/token/原日志行，与198唯一doc的匹配，report SHA `f9da89cb7b882e870dce879685986807da63484ef2e25a88a7cbc5a7ed47aa5a`。
- `diagnostics/first-output-anomaly-freeze-001/`：doc178 8rank状态、完整日志前缀、原始采样token，report SHA `4f365c1b23175be7139b47c27080d90f98b92dbfd305c8188e7faa6aea9c1690`。
- terminal observer delta、before/source manifest以及与已冻结SHA一致的私有Plugin/observer源码，只读使用。

先建立7题输出形态、预算耗尽前的有效推理/重复/答案措辞概况；再将doc178 step71340–71363的请求/slot、computed tokens、generic gather→clear→scatter、真实device indices/graph replay及首个采样token对齐。对已有288个选中状态快照核查CPU metadata、索引对应、有限值及可解释的一致性，不把无NaN当作状态数值正确。只有出现明确单变量/执行边界因果证据才确认根因，否则报告剩余证据缺口和下一步受控验证所需授权。

状态：本轮离线分析完成；零新模型请求/重启/埋点；原gate有效，root cause未隔离。下一阶段缺少的运行证据需要另行告知并获得用户方向，不能自动加埋点或重载。

## 执行前冻结

离线脚本`CASE/commands/accdiag020-offline.py` SHA256 `e82a033eeeb9d3c131903759c9c4bbdbaf38fc77f1191c67bb9224edcd4f02f1`。先以`scp -O`放入新文件并核验SHA，随后Host运行`python3 CASE/commands/accdiag020-offline.py --mode host`，新目录排他创建；CPU状态检查为`docker exec -e CUDA_VISIBLE_DEVICES= -e OMP_NUM_THREADS=1 -e MKL_NUM_THREADS=1 qwen38-eval-ppu07-acc014-c64-20261017 python CASE/commands/accdiag020-offline.py --mode cpu-tensors`。脚本仅读冻结日志/PT，写本次派生JSON；不修改任何服务、原始证据、模型权重或采样配置。

补充可复现检查`CASE/commands/accdiag020-history.py` SHA256 `09aa1f26e1b3baf7ca30726ca96ba5b39562a09292fa1a25b15f1e64e84c8b99`。Host执行`python3 .../accdiag020-history.py --mode history`追踪slot63迁移及native gold；同一CPU-only评测容器、同上空CUDA环境与线程限制执行`python .../accdiag020-history.py --mode compare`，只比较真正last-writer层46的selected snapshot和对应pool行，不跨层比较共享record。两者均零模型请求。

## 结果：7题需要拆成两类

| doc | 已确认的直接机制 | reasoning离线观察（不是重新评分） |
|---|---|---|
| 79 | 60000 token/length，无think-end/EOS | 持续尝试DNA字符串到数字的不同编码规则，末尾仍在推导，未发现答案措辞。 |
| 88 | 同上 | 有过“final answer D”等候选措辞，随后继续结构/耦合分析；native gold A，不能把该措辞当恢复正确答案。 |
| 90 | 同上 | reasoning内已出现“The best answer is D.”，随后又复查反应，最终被截断；native gold B，不是仅parser漏掉一个正确答案。 |
| 127 | 同上 | 长时间翻译/比较DNA序列，末尾仍比较候选，曾倾向A（gold A）；没有输出通道切换。 |
| 145 | 同上 | 持续反复分析endo/exo和立体命名，曾在B/C间犹豫，gold A。 |
| 164 | 同上 | 多次准备给出答案又反悔，A/B/D有不同措辞，末尾还在质疑，gold A。 |
| 178 | 24 token/stop，EOS248046，无think-end | 量子矩阵题却生成无关的“reference lines”重复句，属于短输出退化/提前终止，非预算耗尽。 |

六条60K回复仍有大段与原题对应的化学/生物/编码分析，尾4096 token的重复8-gram占比约1.2%–12.3%，不支持把它们一律描述为短周期乱码循环。这个统计只描述重复形态，不证明推理正确或算子正常。`xhigh`提示和不断自我复查与预算耗尽相容，但未做单变量对照，不能认定xhigh是根因。七条都没有248069，因此content=None符合既定reasoning parser；TIMEOUT是评测占位，不是网络错误。不能靠从reasoning任取字母“修正”正式分数。

## doc178：边界已前移到Prefill输出→采样

1. 原prompt包含完整矩阵、四选项和最终答案格式，455个prompt token；API返回24个完整token与rank0实际非discard采样前缀一致。首token91（`|`）来自step71340的混合Prefill：63个Decode token+455个新prompt token，总518，`graph_runtime_mode=NONE`。后续23轮才是FULL batch64，computed由455递增到477，最后采样EOS248046。原文为`| \nThe lines in the reference lines indicate that the reference lines represent lines, and the reference lines represent lines.`，没有可恢复的最终答案。
2. 因此“纯粹由后续FULL Decode graph复用才开始出错”解释不完整：首轮采样已经偏离问题。但NONE不代表整个进程从未用graph，也不能排除此前负载留下的状态污染；第一token的`|`单独并非充分数值错误判据，完整24token的离题/短终止才是症状。
3. step71338旧batch slot63请求`chatcmpl-97ccdaf8778a0d0d-a35720c4`，设备last-writer GDN state index8800；step71339它正常迁到slot9/index8800，slot63实际device index为padding0；step71341新doc178 slot63为26991。8rank后续23轮都保持26991，与真实最后GDN层46的Prefill/freeze索引相同。旧slot63请求自身正常输出434token及最终A；198份回复中“reference lines”仅doc178出现，不支持直接复制另一份已返回回复，但这不能排除隐藏状态/输入行错配。

## GDN索引/清零/写回：已核验及未覆盖

- 8rank × 36层 × gather/clear/scatter，共864条operator-post全部mismatch=false；每层Prefill仅1条新请求、has_initial_state=false，clear对临时行0完整CPU期望逐字节比较通过，gather/scatter该次所选行均检查。匹配的原生GDN代码在chunk计算前执行`initial_state[~prefill_has_initial_state]=0`，之后写回`last_recurrent_state`；这里只证明搬运/清零按实际mask正确，**没有独立重算chunk GDN的数值结果**。
- doc178各层真实generic索引313–32752，全部storage合法；8rank固定i64实现SHA命中。每个rank的36个Prefill索引与EOS时对应目标状态索引一致。未见这次仍使用旧32位乘法、重复目标行、越界或清零遗漏的证据；不将反事实i32溢出当新错误。
- CPU安全加载全部288个PT（8×36），target position63/request绑定一致，目标行均存在、有限、非全零；所有保存行也finite。仅EOS时有限并不能证明Prefill各层或此前23步都数值正确。
- 36份record确实都来自同一共享pool最后执行的**层46**，并非层0真实索引错成26991。各层metadata与共享record不相等属于观察器覆盖限制，不是模型异常。层46 selected index29061的post快照与pool对应行8rank逐字节一致；该selected行不是doc178的26991，不能称为doc178逐步pre/post一致性证明。
- 未保存：首token的实际device input IDs/positions/logits行选择、逐层QSA选择和Q/K/V、GDN卷积/门控/chunk输出、PLE/HC及末层hidden、sampler前完整logits/概率/RNG；其余35层每步实际graph索引也没有独立device record。故目前不能从“finite、地址合法、写回一致”推导算子数值或采样正确，不能指定QSA/GDN/compiler为根因。

## 判定与下一步（尚未授权执行）

直接机制置信度高：六题预算耗尽未离开reasoning，doc178真实采样EOS且无think-end；不是7次网络超时、原始答复被评测器截短或一个共同parser漏答案。GDN generic索引搬运/清零检查和last-writer graph索引均正常，降低了这些具体机制的优先级；**根因仍not-isolated，无模型修复声明**。

最窄下一步是doc178首轮Prefill的定点取证/数值对照，先C1再带少量固定对照的mixed C8，保留相同prompt/采样/seed/i64与QSA M16，保存实际输入/位置/请求→logits行、相关逐层输入输出及原始logits、top-k/top-p概率/RNG、EOS决策。先核对模型输出与采样边界，再对首个分歧层做单变量算子比较；不同时切多组算子、不重跑198题。若必须补hook，需**先告知用户并获准仅8010重载**；本次没有部署、重启、推理、GPU单测或恢复heartbeat，也没有修改8035。

## 派生产物（均在本次D，不覆盖原证据）

| 文件 | SHA256 |
|---|---|
| output7.json | b463be37a1ef717bafbc4f6b22002c11ef153638088ccab0390f9bb1434963ef |
| rank-summary.json | 460a1b2a88c262bb00ea116e78a937e3ff058c6e9d6ca05de0e83ea9ff718039 |
| cpu-state-audit.json | 57ed5824735a495a66f385cd3bbbbd63d7d97f9a25cbeacbd7deabda9c187dd5 |
| doc178-history.json | 22050422d54a94a7411b376c8229aaa343c82b250368e9f3b8ed90bc319e95f5 |
| lastwriter-cpu-compare.json | ebec483c03870c9171fa54bb6599d87c8427766ae8f1657ce08757a2e2102c4d |
| native-golds.json | 332344b1140a031dbc9135d1c8e1b56ae7259867b9f1c045f9171d1f74dbc1f2 |

另有每rank完整目标窗口事件、前一batch绑定、唯一reference-lines匹配记录和HOST/CPU完成回执。原始响应是服务日志中保存的Python dict表示，不冒称HTTP wire bytes；EOS快照是选择行/共享pool last-writer，不冒称完整逐层因果现场。未在PPU-07当前路径找到旧`gpqa_nv.jsonl`，本轮未用NV侧代码或对照数据作因果推断。
