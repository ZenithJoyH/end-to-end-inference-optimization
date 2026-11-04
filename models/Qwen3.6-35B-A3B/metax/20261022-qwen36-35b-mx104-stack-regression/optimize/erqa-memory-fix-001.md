# ERQA KV预算与图像编码拆批修复

**当前结论：仅KV预算修正保留并通过限定短测；图像拆批候选未通过冻结数值检查，已经回退。两项并未全部完成。** 当前B普通服务API1547274/start1157237411，GPU4/5/8020/opt4、util0.9/prefix-on/原graph与argv/env；MoE/GDN/采样/LibTuner保持。没有新全量GPQA/ERQA或性能测试，无新gate。


用户授权保持显存利用率0.9，修复KV预算和图像编码批次，保留MoE/GDN/采样，仅短程验证。当前API已退出、GPU4/5空闲；B镜像bf9/容器40794ce，私有Plugin /workspace/vllm-plugin-FL不位于/data或/public-flash挂载内，隔离沿用当前专用B，其他服务不动。

两个关联framework子项：budget-001只在MetaX自动预算扣除初始nonTorch占用，其他平台与显式KV覆盖不变；image-batch-001只在MetaX/无encodergraph/无LoRA的flat pixel+grid图片路径，将完整图片按raw patch上限max_num_batched_tokens分组。当前8192；单图超限完整执行（不能切断attention），不改图像分辨率/顺序/数值算子/采样。未知layout、video、其他平台走原路径。原prefix-on、maxseq64、graph64、memory0.9不变。新增纯CPU memory_policy helper，无新环境开关。

修改只允许Plugin worker.py、model_runner.py、新memory_policy.py及对应测试。旧6850源码清单其余逐文件SHA锁定。保存原文件及diff，运行前CPU边界和实际入口不重试测试；数值验证用真实worker原生整批embed作为独立参考与新分批结果比较，两个发生实际拆分的批次逐元素atol=0.01/rtol=0.01（BF16，冻结不随结果放宽），记录最大误差。新service两rank预算与原生图capture证据+两C8检查。

短程协议预冻结：probe两C8共16文本；32个固定长度文本；原ERQA148..211共64题（包含本次失败窗口）加尚未包含的首个max16图题1个，C32单次无重试、保留原request temp0/max300/thinkingFalse，不计正式分数；失败停止新增。observer只记录内存/实际encoder patch，并做最多两个整批/拆批数值对照，不改输出；默认无输出/仅诊断进程启用，结束后重启为无observer同候选服务，两C8与三条图文最小检查。无GPQA/ERQA全量、无正式性能。若必需检查失败，保留证据，回退本次两处改动，已保留优化不动。

工程：A1/A3框架预算与编排，A4复用native grouping；B4失败直接上抛；C1顺序/dtype/cache契约保持；D1无新开关；E1/E2不改KV数值写入与stream/graph地址；F1 CPU边界/真实入口/失败无重试，F2真实视觉参考，F3原服务图capture+两C8 replay下界，F4其他平台硬件未测；不提交推送或公开PR。

远端ROOT=CASE/operator/erqa-memory-fix-001。所有新工具、执行命令与SHA在执行前唯一归档；旧脚本不执行，不覆盖旧结果。当前仅准备，未应用/启动。

## 执行前冻结
- `operator/erqa-memory-fix-001/patch-bundle.json` SHA `e1f4126ecfee73ba1dc3336cae6b2c7062372ac5bc77b3ee0c1ae90c13a7438d`
- `commands/erqa-memory-fix-apply-001.py` SHA `029af0bf4df7af2a1fea1b71c335fc4dd06f2c13f5c0475c597fc180f69646ee`

## 短程工具冻结

CPU9项通过。目标环境未安装ruff，格式工具检查未执行，未更改依赖。以下新工具AST通过、未执行；先归档再启动。若必要验证失败，停止新模型流量并保留失败，先定位修复或精确回退，不自动重复当前测试。
- `operator/erqa-memory-fix-001/runtime/fix_observer.py` SHA `f7d9ed8ac37d1ae02420c0ce3542e970ece61633c4884fc1b9cbdb23e0ff1d53`
- `operator/erqa-memory-fix-001/runtime/sitecustomize.py` SHA `236a42a94dae6297152dd94323b6a4bdab55d129afc7b7dd6b0745f7457e4c8e`
- `commands/erqa-memory-fix-service-001.py` SHA `da8544be022a3cb640623b8be1865a4d7974407162a5feedb8a1e9b6ec91fe6b`
- `commands/erqa-memory-fix-client-001.py` SHA `2f9a0e1d3afe402bbece5b4104a043560a3f8d25c5daff5217bad4a80320dd95`
- `commands/erqa-memory-fix-controller-001.py` SHA `15bb8ff854b958c6e0afd67b4055035970c2418d0ea84f582171cec3b9eccd76`

## 已启动一次短程验证

Plan SHA `9c84e297288b9bca52efac56e8815be88a7bd42f7b2ba2fdb84d81d41834ab38`；首个16图doc167已包含在148..211中，因此probe图片恰为64题，probe最多112请求、clean19请求；不是新增第65题。Controller PID3630175/start1157015848，command SHA `5cdb8e1ccbb4f5540bff3afef87f0ba2e630d2bcc44a8ac59a2ccc1fe1caeb79`，已启动一次不可重放。ROOT/controller.log、native-result.json和summary.json为原生证据；controller拥有continuation CAS，活动时只读观察。

实际源码：worker.py SHA1ad4d858dd6a88acbd76a9f19596ff442cd98396f19fa7782a4b1a9de10d0422；model_runner.py SHAe8db9316a7c8c12e3a0cfc75e33ad17b5ad712d98cefe50203edb82c8191babd；memory_policy.py SHA57d1d91109641691ffe75a6b884616aacdd7a6e9dfd34f4e28e8369dd89c9c93。已保护原6850文件，只有上述原有两文件改动，新增helper/test。旧源码与预先存在的Plugin diff完整保留，未提交推送。

## 首轮短程失败与限定数值定位

首轮native exit2，48文本通过，图像32已提交/32 HTTP失败/32未提交；无OOM，observer原冻结atol/rtol=.01拒绝整批/拆批视觉结果（19396/2351104元素，maxabs.6328125）。原结果保留、不重放或拼分。两rank新KV预算18573061120B，初始nonTorch4385587200B；实际KV18566676480B，capture后free7573454848B。不能宣布图像修复通过。probe已经精确停止；clean未启动。

下一步vision-diagnosis-001只1条原doc167（16图，C1/max300），同补丁/同0.9/同服务参数，通过临时observer做原生整批两次及拆批的逐层CPU快照对比。只定位首差，不放宽原阈值、不签gate、不重放64题或全量评测；结束精确停止临时服务。新controller SHA777f308e95e9ad3a812c1f658a98218671e434ab166c6e9eac367506087ef0fb，observer6a78c795fb8aff8a3480c32f5f6715c8d578745f9fa4fc9794b5d59c266d73e3，servicec85b160c4c8b48f8267b82129c4760205ae593b502fd2b9a7d879348448fb29d，client47f78c148af69f2a140a0ae81e56d8791f3d78c55861ca263e8cc07b90181950。执行前唯一归档。

## 数值定位结果与保守回退

单条doc167真实16图32604patch两rank定位完成exit0（诊断不签通过）：原整批两次在已采集每层逐位一致，拆批首差patch_embed max.015625/RMS5.3678e-6；最终merger max.4921875/RMS.002349。证明批量边界影响原生BF16路径并沿层传播，不是OOM；尚未证明可以满足原冻结视觉结果阈值。不能将该候选晋级。本次图像拆批回退到原model_runner.py SHA d80dc95ddea809e9c878ead6960ffb77c3c05b9298b752758911552a97685ee5，并去除未采用helper/test；仅保留KV预算修正。

预算单变量短程预声明：budget-only-001，同0.9与原env/argv；两C8、原失败窗口180..211的32题C32；追加1条诊断性17图（doc167+176原图，非评测）以覆盖至少33148 rawpatch工作区，不计分。结束移除observer，clean同参数两C8和3条C1图片；最多68HTTP，不全量、不重放旧64题结果。数值路径完全恢复原版；这仅验证预算修正与显存边界，图像拆批仍未交付。准备controller91e5456f0e24984ffa0c72178b6f584e8bfa171882ea4519aa5dbda9e9ca9913、servicea620a1befb60294090a0915f0755f9be6fcd19d16780abb5d8554f54173549f5、observeref84aa002eb189f02702f77e9f38c3130bcb144a80430c36569c0684eb50d17e、clientf6382c7af5a6bd4ce3157a25370a1653078a4ed8bc93c082445664eaf356ab4a，执行前唯一归档。

预算版已应用且CPU2通过；model_runner恢复原SHA，memory_policy仅保留预算函数SHA30ca53ebd68fa3d685965c1a17c75a7899b5f4a5c70dcf6cd0147a211d620dac。budget-only-001 controller PID3688595/start1157164825已启动一次；不重放。独立入口commands/erqa-memory-budget-independent-001.py SHA cde61240a7feaebe3903766add80697e2f5d3be67775ccd4a4a9b315a7415333已准备归档，只有本短测native0/clean服务完成才能执行；0新生成，核验68HTTP原始请求/响应、两rank预算/大图patch/零OOM/前后源码/clean当前API和无observer环境。准备不等于通过。

## 预算版短测与覆盖修正

budget-only-001的49请求全部完成/0OOM/0HTTP失败；原C32失败窗口32题已完成，无需重放。两rank最大原生编码32604patch，最小采样free分别6016495616/4808536064B。预声明17图HTTP被原生调度拆步，未覆盖33148门槛；controller正确exit2并停probe，保留coverage不足，clean尚未启动。不是模型失败或完整通过。

新增budget-boundary-001只补1条doc167 C1，在两rank原生embed入口额外执行一次固定17图工作区（原16图输入加第1张已处理图副本，rawpatch须33148..42000），输出丢弃、不进cache/LLM、不评分；再由原路径完成该请求。未改源码、0.9/argv/env保持。成功后clean两C8+3图共19，最多20HTTP；不重放已完成49或任何全量。controller0db139aef923c4c802ef5c45ea5ea2bacfd9589925434010756d9f118792555a，observer2d45fcee5e1c29e5b28fd75ec11e95af40352a50c50c55d69f2445cb40f8db16。所有旧不通过证据保留，不拼分。

## 最终独立核验与当前部署

budget-boundary-001 native0、summary无error/restore_error，独立入口exit0，报告`budget-boundary-001/independent-001/verification.json` SHA **9d88ecf7d18840dfa4705131b294176e79b505e8c5cac017f4c2197726e7b5b6**。独立入口SHA536c4c1bec29b706ecedd747ea5eeb3447e8057cc482e4f5aa528ac0237f2fb9，只读核验无生成。预算版前49成功HTTP及补充/clean20合计69，原C32窗口32题每条wire一次且全部HTTP200；raw文本/usage/finish和输入SHA逐条匹配，不是正式评分。原拆批失败80HTTP（48文本成功/32图失败）与诊断1条分别保留，不混入预算版成功范围。

受控边界实际是该调度轮13个处理后图输入加第1个副本，共14图/35,112 rawpatch；计划描述中的17并非实际单调用图数，以native证据为准。满足冻结33148..42000 patch覆盖条件，两rank各1次额外原生视觉forward完成，输出丢弃、不进入答案、无OOM；不将其称为17张图的同一GPU批次。普通原生路径的C32窗口也已完成，不拼ERQA分数。

两rank当前取证初始nonTorch4,385,124,352B（约4.08GiB），自动KV预算18,573,532,160B，实际KV18,566,676,480B（约17.29GiB）；capture后free7,573,921,792B（约7.05GiB）。边界探针采样最低free6,392,569,856B（约5.95GiB）；之前C32阶段最低采样free4,808,536,064B（约4.48GiB）。这些是采样余量，非每次分配的连续最低值；原生OOM计数0、所有预算版请求成功。预算修正会减少KV可用容量，长上下文并发及性能影响未评测。

clean服务去除了PYTHONPATH/Q35 observer变量，原启动argv、选定env、cwd一致；API精确start/argv、health/models、两C8全部exact且completion>=2、3图文原请求均通过。native graph capture + 两独立C8只给replay下界，不冒充直接设备计数。6850原有源码逐文件核验仅worker.py变化，model_runner.py已还原原SHA；新增预算helper/test预期SHA一致。FGV/Gems/vLLM/编译器等原有保护文件保持。当前服务日志位于`budget-boundary-001/restored/service.log`。

回退：只在当前API+start+argv精确确认并停止其服务后，将`source-before/worker.py`恢复原worker SHA51a168eae6dbe45b3598eefb1dba7fb5ce6bfb9344ffe3ec5d9df4d725cd2bc5，移除本次新建budget helper/test（先核对上述SHA），再按`original-binding.json`原参数启动。原有MoE/GDN/采样和其他历史本地差异不得覆盖。失败拆批候选及全部命令/报告留在远端，未提交推送。

未完成项：图像批次限制仍需解决原生视觉批量形状带来的数值差异后另做同阈值验证。本轮不放宽数值门槛，不把短程无OOM外推为全量ERQA稳定或正式精度通过。
