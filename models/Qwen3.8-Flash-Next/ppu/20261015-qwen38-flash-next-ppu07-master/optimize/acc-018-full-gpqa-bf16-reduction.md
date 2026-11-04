# acc-018：BF16 TP归约完整GPQA复测

## 授权、变量与范围

用户2026-10-21明确要求“改成BF16跑轮全量精度测试看看是否异常”。承接perf060对照，仅将8010的attention/MoE TP归约从FP32转回BF16；模型权重与激活本来就是BF16。使用已验证的真实私有BF16 Plugin `/opt/qwen38-perf060-op061-warm8-20261021/bf16-plugin`，不修改安装的`/opt/vllm-plugin-FL` FP32工作树。op061v2 Gems、i64/randn、QSA M16、PLE i64+CTA、normal_/index_select黑名单和pin047固定调优全部保留，不加模型埋点。

目标PPU-07 / `qwen3.8-flash-opt-ppu07-20261015` / 8010 / TP8物理8–15；**不访问8035或其PID/health/物理0–7**，不停止容器。只对已核验的当前FP32 API3852394/start530581998/argvSHA`c146e2da4762690185e9b3573c5f48796a5cb42aa2037de0d08d9ada40595010`正常SIGTERM排空，最多1次BF16启动，禁止强杀、重复启动和自动重跑。完成后保持BF16服务，不自动恢复FP32；后者原源码和perf060证据保留可供后续方向。

## 冻结精度契约

- 本地`inference-accuracy-evaluation`：`formal-gate`，启动后先`minimal-regression`。完整Skill bundle SHA`6e94a080dd3b64544c535e1fd4bda506f55516374d14d0f8ca6aa148bba2c7b2`。
- 单服务`gpqa_diamond_generative_cot`、198唯一doc/limit0/C64，`exact_match,strict-match >= 0.88`；完整原多filter，每个(doc,filter)恰一次，同题原文/回复一致。
- temperature1/top_p.95/top_k20/min_p0/presence0/repetition1/max_gen_toks60000，evaluatorseed42/API原默认seed与stop不变；return_token_ids/return_prompt_text。API retries3、eval retries0、timeout7200，不改变原runner语义。198逻辑题不冒充零重试HTTP总数。
- 新评测容器`qwen38-eval-ppu07-acc018-c64-bf16-20261021`，规定`harbor.baai.ac.cn/flageval/flageval-llmeval:v1`镜像；独立UUID/本地SQLite响应cache，不借用旧答案。
- 新实例独立空编译cache `/opt/qwen38-acc018-bf16-20261021/baseline/cache`，原argv/禁prefixcache/graph sizes1..64保持。两类capture7/7、至少2真实FULL执行、2C1＋8C8原短doc2/max2048护栏正常后才正式；这10请求不是正式分数。
- 正式原始runner仍由维护`formal_accuracy.py`调用；wrapper/acceptance/sample_validation/原runner分别SHA`d345525c...`/`06e4a035...`/`9799f2df...`/`82cf6e83...`已与本地现维护入口核对相同。两次新provenance需一致、dataset revision与原固定198题一致，再冻结schema3契约和新服务manifest、执行preflight。
- score达阈值且绑定/样本证据有效才由维护acceptance签发新gate；低分failed-score，故障污染/缺证incomplete。旧acc017177/198及其他历史分数不替代，不自动签发/继承gate。空final/60K截断/真实HTTP失败/EOS异常分别保留，不修改评分指标或提前重跑。

## 执行、来源与证据

远端唯一CASE：`/mnt/nfs/users/jinghao/qwen3.8-flash/20261015-qwen38-flash-next-ppu07-container/accuracy/acc-018-full-gpqa-ppu07-c64-bf16-reduction-20261021`。新目录初检不存在，约6.38TiB空间；当前8010健康空闲、source/Git与perf060终态一致，连接验证通过。

执行前命令在本地`/private/tmp/qwen38-acc018.s1MwBX`：`acc018.py` SHA`82995cef1b83902c9aeb06c8d06f3ffc6283b87195f5dd98e041fe8f1a0e9e02`、`source_probe.py` SHA`2a90b3f5998b3e59ee169201c40fccdb4df7f09f50b7b01fa84e3ae07d40f833`、`stage.py` SHA`e892ded7d61b697ffe226d91427223732a06495872454a708a0755af3db80b60`。排他建CASE/commands并上传；`acc018.py --mode prepare`仅创建新eval、来源/计划/新cache父目录、两次provenance，0模型请求/0服务动作。核PREPARED后仅一次`--mode launch`，唯一controller依次排空8010→新BF16启动→10护栏→实际BF16编译图/source绑定→preflight→一轮formal→自然冻结/签gate，失败不重试。

编排复用perf060 helper（SHA`f3d77224...`）的精确8010切换/graph/HTTP采集、acc015冻结formal函数（SHA`9e0a2b7d...`）的原始wrapper/计分/签gate，不另写评测器。仅纠正新实例`restarted_model=true`、`instrumented_service=false`，没有老observer，终态只冻结新服务/客户端原始日志前缀。实际imports/完整源码树、权重清单与metadata、tokenizer、engine在新CPU source probe前后核验；8rank编译图需各98BF16/0FP32归约。CPU解析/launch继承/native dispatch不是独立每rank函数对象trace。

正式INFO保存完整解析后API对象/tokenIDs，**不是HTTP wire bytes**；10护栏有wire原件。新服务无旧047模型observer、逐层state/QK/logits或采样journal，不虚称198题有完整GPU因果现场。不改旧marker/日志，不清cache，不做额外推理/GPU测试/性能/提交推送。

复用原heartbeat每30分钟监控，启动唯一driver后更新身份/CASE；仅实质结果、首次异常/服务故障、明显停滞、完成或需处理通知，正常推进静默。终态先核198唯一题/每filter完整、绑定和source前后、原controller/eval/helper退出及冻结，再写回本记录/state/README并暂停监控，保持BF16等待用户方向。若低分，按精度诊断流程冻结本轮，不叠加优化。

## 当前结果

### 用户决策：保留当前BF16代码

后续源码位置更新：用户同日授权[env-062归并](env-062-bf16-source-sync.md)，标准`/opt/vllm-plugin-FL`已为BF16，原FP32完整副本改存`/opt/qwen38-env062-bf16-sync-20261022/fp32-source-backup`。以下保留决策时的目录描述为历史；本轮acc018实际运行目录未改、服务未重启，原正式结果/gate不重写，也不自动给归并后的标准目录签新gate。

2026-10-22用户明确选择保留当前BF16方案，依据为本轮176/198正式达标，以及perf060 attempt004同软件受控C64短批次中FP32吞吐约低1.05%–1.59%的证据。该决策不是BF16/FP32精度等价证明，也不关闭9题60K长推理问题或外推正式四场景性能。

当前选用源码继续为容器内`/opt/qwen38-perf060-op061-warm8-20261021/bf16-plugin`，实际`vllm_fl/models/qwen3_8_flash_next/gpu/model.py` SHA`d458a1ceaa914945262e255ea1deb702766921fd7d3074ed9b37a9123e34517c`。只读复核SHA、8010原PID/start/argv及PYTHONPATH均与acc018一致，health200；原i64/randn/QSA M16/PLE/op061v2/黑名单/固定调优保留。`/opt/vllm-plugin-FL`的FP32工作树仅作原样回退备份，当前8010未选用它；本次不迁移或覆盖目录、不重新安装、不重启、不发推理、不访问8035、不提交推送。监控保持PAUSED。

### 终态：正式精度通过，9题长推理仍未收敛

原控制器于10月22日00:59:58+08自然完成，恢复连接后09:38–09:44执行只读终态核验。`exact_match,strict-match = 176/198 = 0.8888888888888888`，达到预冻结0.88门槛；维护acceptance已签发`evaluation/accuracy-gate.json`，再次`check`返回PASS。完整198题各strict/flexible filter恰一次，共396行，题目/原始回复/target/arguments跨filter一致。普通13题错答加9题空final共22题未匹配；不把子集helper得分替代正式分数。

- 189条API回复正常stop、非空final、think-end248069及末EOS248046/248044；9条均60000 tokens/finish length、无think-end或最终content，doc71/88/90/121/127/130/145/147/164。首条于00:48:30+08返回，doc71 / `chatcmpl-90fb007bbfc054b6` / 60000 / last token11 / content null，reasoning188953字符。首次输出异常发生在网关失联窗口，现仅分析已保存证据，没有补发复现。
- 198完整API对象/唯一ID与返回token均齐全，token/prompt长度与usage一致，含10护栏后的服务计数prompt82925/generated2446388全部核对。9个samples TIMEOUT为content None占位，不能称真实网络超时；样本schema未标truncation，实际9个60K截断以API finish/usage/token为准。
- 完整可读service/formal日志无Traceback、HTTP超时、HTTPStatusError、ERROR或illegal-memory证据；未发现189条stop回复提前EOS。没有逐层state/logits/采样journal，不能将“无报错/有限输出”当作数值正确或定位到某kernel。正式INFO是解析API对象，不是wire bytes；10护栏wire原件完整。
- 原controller/evaluator/helper已退出，8010仍API1924405/start531054985、health200/running0/waiting0/preemptions0，前后/当前source完全相等，安装FP32工作树未改。8rank编译图各98BF16/0FP32、两类capture7/7及护栏FULL1819已复验；保留BF16和i64/randn/QSA M16/PLE/op061v2/黑名单/固定调优，不自动恢复FP32。

补冻`diagnostics/cpu-terminal-audit-002`已完成：76份现有文件/8rank编译图及独立保存的198完整解析API对象；核controller旧冻结前缀SHA不变，并补齐终态controller日志尾部。summary SHA`ff7fc55301b267e9626c5a6f973be71744302023b82c30db3456fce3a3f6d396`、manifest SHA`a5d609e04cb3ce25b9029ec5673ecf59527935de1b023090860b563d12116430`、parsed API SHA`c82e8ec6db54c01f0f5238f8cf5f231b862cb0517c4c3e5d6bca2150be10fc4c`、AUDIT_FINISHED SHA`df4fc9bc23c44427a64f305dcf3e780ded5154aa8faaad5b27b4774ce887b360`。v1工具映射失败原件/部分产物保留，不称v1完整；v2修正仅CPU审计，没有新增推理/GPU测试/服务动作或8035访问。

原始结果位于CASE `results/Qwen3.8-Flash-Next-ppu07-acc018-c64-bf16/655b93965d064365a3e698f5ff9c71e9/gpqa_diamond_generative_cot/Qwen3.8-Flash-Next/`：`results_2026-10-21T16-59-47.163719.json` SHA`7d67adcbad5f5c009fa0312de0209b7a707a092774185ec52f631a244edbc53b`；对应samples SHA`810867dff6e433bd2cccd52dbfda6ce26ac2036c5b7ed075588a09ee32bee5cf`。run-record SHA`43d62c436e667bea700c447549de7e4144989d7589a66cbf0b7fcd18a1e79c79`，gate SHA`5e1dca877dcfcb74b10aed286309b343cbec842df79cf3e75c290a058d41c5c7`；FINAL_SUMMARY SHA`9784db1f1e2d0dd58f46dbfc1b09267dd09fb30458c02653d44bb7c498a0383e`、FINISHED SHA`eeb3c06e0131482740f32ca2c7cfe49f735170afef77411938b3efef6cd34e49`。

结论仅是该BF16组合/实例正式分数达标，不证明长推理全部修复，也不与不同旧源码177/198直接归因BF16/FP32。9题60K症状为高置信事实；首个内部数值分歧与根因未定位，缺逐层现场。无新性能结论，旧历史分数不改；终态更新记录后，同一heartbeat经产品工具确认PAUSED，保留当前BF16等待方向，不自动复测。

### 过程记录（历史快照，以下不作为当前状态）

10月22日用户确认恢复连接后，09:38+08已实际重连：原controller已退出，FINAL_SUMMARY/FINISHED齐全；原生strict-match为176/198＝0.8888888889≥0.88，现有gate的维护`acceptance.py check`只读复验通过。198唯一题/396双filter行、无重复或跨filter原始内容冲突；189条stop/9条60K length且空final，全部已返回token长度与usage一致；9题samples含TIMEOUT占位为doc71/88/90/121/127/130/145/147/164，不是已证网络超时。没有HTTP超时/非法访问/ERROR日志。新API身份仍1924405/start531054985且health200、空闲，无源码或Git变化；没有重启、重发或访问8035。

终态补冻方案（执行前记录）：仅一次CPU审计脚本从`/private/tmp/qwen38-acc018-terminal.Iez9RP/terminal-audit.py`排他上传到原CASE `commands/acc018-terminal-audit-v1.py`，先校SHA再Host `PYTHONDONTWRITEBYTECODE=1 python3 <script>`。只读取已有raw/log/token/samples/gate/source和8rank编译图、复验计数与prompt-doc映射，并复制已有证据到新`diagnostics/cpu-terminal-audit-001`；拒绝覆盖或重复目录，不发推理/GPU/服务动作。已有controller冻结原件不变，后处理不是新的模型测试或逐层因果现场。审计工具的splitlines Unicode分隔误切已改用维护iter_sample_records；模型原件未改。

上述审计脚本冻结SHA`824ebc29da178d32ceabb9f31e2d299596dc06958ee30bb32eb56c066790ee57`；本地AST通过。`py_compile`曾因macOS默认pycache指向只读目录失败，仅本地工具问题，改用不写cache的AST检查，不影响目标服务或评测。

CPU补审计v1在prompt-doc映射处停止：samples arguments为嵌套dict中的JSON messages字符串，不能把其外层JSON字串直接与渲染后的prompt比。已保存v1脚本/STARTED及部分parsed-API文件，不能称v1审计完整。仅修正CPU解包映射，在新`commands/acc018-terminal-audit-v2.py`与新`diagnostics/cpu-terminal-audit-002`执行完整审计，SHA`124d910954b1b015236353d65be7002e3ed8687c5e59cfe54104552538050821`；AST通过，不覆盖v1、不改模型/评测/原始响应或重跑精度。此为审计工具修正，不是模型事故。

10月22日00:30至07:30+08每30分钟及08:24、09:09检查，监控通道均不可用：限定PPU-07的连接验证虽返回ok/退出码0，但远端hostname正文实际为`no available gateway`；00:30随后只读SSH同样只返回该提示，没有执行预定状态或token审计。后续验证仍未恢复，未继续发远端审计命令。不能将其视为有效连接、模型HTTP错误或服务故障；没有获得controller/8010/正式产物的新事实。最近有效快照仍为00:01:48（见下），当前运行/完成状态未知，不能沿用旧health称当前健康或判定明显停滞。00:30已通知监控受阻，后续无变化不重复通知；heartbeat保持ACTIVE等待下轮只读恢复。不发模型请求、不重启、不访问8035、不更改远端证据。

10月22日00:01:48+08只读快照：10护栏已通过，唯一controller正执行新198题/C64正式评测，尚无FINAL_SUMMARY/FINISHED或可签发的新正式分数。新实例READY SHA`27945e52a346a316a27f0f698a01fa4350aed8e69a89a1fb3bcb370ff6e3e221`；SANITY_FINISHED SHA`d4a5f77efd02eecf61d2615a43b43ac069cacc5d04f4eec555a1370af82894a6`，两C1均B602且完整序列一致，C8另外8条均B、无issues，native FULL累计1819。8rank实际编译图均98BF16/0FP32，`evidence/compiled-BF16-graphs.json` SHA`1fbd6a7fe6e837fe9dad6a2adc12d193a124b8ab0c1865faec511c9de497b01f`；此为编译来源证据，不冒充逐rank运行函数trace。

FORMAL_READY SHA`169fff7040db812abb575eadd9ceef2f0d761ae79b98c3d70169971c6adf1a7c`绑定当前实例与manifest SHA`5c1493835e6d9484a8ee8e212ed1fafd8cfcfa9a4f3d02058dd1ce2fa343f758`；FORMAL_STARTED SHA`459314e36f09202748f2adc519a553f9531ed25f7546bc5f9fa5da9d2e1d264c`。API1924405/start531054985/argv一致、health200，running64/waiting0/preemptions0，source/dependencies/安装Git未变，可用空间约7.02TB。原生progress helper有子集计数，但本次尚未核验其cache/prompt-doc映射，不将其作为198唯一题进度或正式分数。正式与服务日志未见Traceback/HTTP超时/ERROR/illegal-memory；正式正文中NaNH₂等化学名称含有NaN字串，不作NaN故障。完整API token/结束健康审计仍pending，不能仅据错误关键词缺失就宣称所有输出正常。

本次监控脚本误调用不存在的health辅助函数，产生的AttributeError仅属只读查询工具错误，随后直接8010/health核验200，非模型或controller故障。后续既有API对象解析查询两次遇到堡垒`no available gateway`（SSH返回码仍0），没有执行模型请求，不作为HTTP推理故障；保留监控ACTIVE，下次恢复只读核验，不追加推理或重启。

23:30:57+08只读快照：新BF16实例已READY，两类capture各7/7；唯一controller运行，报告护栏9/10正常完成、1在途，SANITY_FINISHED/FORMAL_STARTED尚无。没有正式分数、新精度gate或性能结论。

当前8010 API1924405/start531054985/argvSHA`c146e2da4762690185e9b3573c5f48796a5cb42aa2037de0d08d9ada40595010`与READY一致，health200/running1/waiting0/preemptions0；source/dependencies/安装Git核验未变。controller报告seq0/1两C1均B602、其余已结束seq2/3/5/6/7/8/9均B且issues为空；剩余seq4未返回，不将其记为已完成或reasoning-only。9份完成数为本次controller日志记录，全部raw/token与重复序列、实际replay最终以原SANITY_FINISHED和终态审计核验，不提前声称10护栏通过。原controller1922807身份/SHA不变，无CLIENT_ERROR；未重发、未重启、未访问8035，继续仅监控原进程。

22:58:38+08唯一launch：Host1922807/start531054520/argvSHA`d2fee9b64c2fc30289e765523d6cf9de0586697ed33e6596bf0140507adb8d58`，CLIENT_PID SHA`cd6d2db641dc89a30265a5768e1279c3eab1149e4efcded77cacaaf092d7aa74`，CLIENT_LAUNCH SHA`363f49b49500c4f06e36439ea9b7839ceb4430496a00db2e4d0e3518426b4132`。原FP32精确SIGTERM正常排空；22:58:43仅一次START_ATTEMPT（SHA`fc7c47678a01fa34bade622b8c46ff1dd7f38cf601bd234fdad695295b0e6c8a`）、docker-exec1924376/start531054982。新服务日志worker注册/加载推进，尚无8010listener/READY/模型请求，无CLIENT_ERROR。旧FP32 health不当新服务可用性。后续仅监控此controller自然执行，不再次启动。

同一heartbeat已更新为“Qwen3.8 PPU07 BF16全量GPQA”，产品确认ACTIVE/每30分钟；仅实质结果、首异常/故障、明显停滞、完成或需处理通知，正常加载不反复通知。终态保持BF16，不恢复FP32或增加正式轮次。

启动前准备/来源/冻结文件核验通过：`PREPARED` SHA`a1a0753acc95546221735e5a665aa770c69909fce6fc64fe253c80219af4004e`，两次provenance逐字相同，SHA`c39228d57fd391a9f723496f54fa2fb3f0d7aeb17810a2edf63559152dc63523`，dataset revision `content-sha256:167548b01bcfd7d38d0eb80bb01bd1e6dded4d3aa14b41a4bdba0beb5423dadc`。contract SHA`a47b6873b89befce29ae398b2a85a1fd2895be76038c1ed6503075c5204eb2aa`，llm-config SHA`3091623a0244d170ba1432be1b039514ef987866854dfcc16907e5972782c571`，新BF16 launch SHA`6e1be4651cdcd31a698c491bd73946aa867db1907c84fc677572f94153f938ea`。原FP32仍精确健康空闲、source/Git未变，准备过程0模型/0服务动作。下一步只执行一次`PYTHONDONTWRITEBYTECODE=1 python3 <CASE>/commands/acc018.py --mode launch`，随后仅监控原driver自动完成启动/护栏/正式评测。
