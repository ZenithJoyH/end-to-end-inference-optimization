# Qwen3.6-35B-A3B / mx-59 当前容器端到端优化

2026-10-15 当前结论（review015）：attention非Split-KV无用Q_TILES导致动态batch重复专化已证明；私有修复25数值/CPU、8graph×2、编译新增5→0、Event24及新原生CG24均通过。按批准仅加载TN单文件，源码12252其余文件、GDN/全FlagGems及原启动环境保持。服务中断339.013524s后API982315正常，C1/C8通过。新源GPQA UUIDbcbef8f8ac274343b48751537e080c5c（198/65536/80）已170/198=85.8586%、0超时，当前原生gate验证通过；旧164/198不复用。D128短场景3测量801.7–809.9tok/s、波动1.02%，未观察compiler/ITL>1s/新主cache；004首轮编译的失败保留。完整D1024 P1K006运行中，其他正式场景/同配置ABR未完成，无因果E2E收益结论。详见[op005](../../../models/Qwen3.6-35B-A3B/metax/20261013-qwen36-35b-metax-e2e-current/optimize/op-005-attention-compile-key-normalization.md)和同state。旧窗口/评测完成不可重放。

## 以下为带日期的历史阶段记录


2026-10-14 恢复：用户以手工启动的gdnopt版本继续E2E优化。当前952702与两个TP packed kernel/capture已核验；新全量GPQA acc004正在运行（198/65536/80），不能复用旧anchor gate。P1K新三轮平均1106.05tok/s且存在慢轮，P4K911–916tok/s较稳；CSV观察不签因果收益。后台30分钟跟进已恢复；新P1K CPUtimeline计划/dryrun准备完成，尚未发性能流量。

2026-10-14最新：按用户要求删除额外旧GDN兼容和64-token限制，decode三方法/hook/kernel已与27B参考一致；18单测+15数值测试（含65-token非连续输入）通过。只保留代码，8010不重启，旧任务与后台保持暂停。

2026-10-14 人工调整：用户暂停此前全部优化和后台跟进，转为完善 GDN decode 公共调用。改动已保存于当前容器，25 项路由/兼容单测与 GPU6 的14项数值回归通过；用户选择暂不重启，8010 仍为原实例944104。新代码的服务命中、graph、C1/C8及正式精度待授权后验证，旧 GPQA 分数只属于历史 anchor；此前所有 E2E 实验保持暂停。详见当前案例 optimize/op-004-gdn-decode-call-transfer.md 和 state 的 gdn_call_transfer。


当前服务为 `qwen3.6-35B` 容器、8010端口、MetaX C550 6/7、BF16/TP2。用户明确要求当前容器优化，已记录独立容器规则的例外；原有公共MoE调用与workspace复用保持。四仓库完整源码/已有dirty补丁已快照；同镜像和规范化挂载连续性验证通过。不改vLLM、权重/tokenizer，不提交推送，不关闭或绕过FlagGems算子来取得性能收益。

所有远端原始产物集中在 `/public-flash/jinghao/qwen3.6-35B/20261013-qwen36-35b-metax-e2e-current`。权威记录见[模型案例](/Users/baai/Documents/ChatGPT/端到端推理优化/models/Qwen3.6-35B-A3B/metax/20261013-qwen36-35b-metax-e2e-current/README.md)。

## 当前精度

用户2026-10-14批准仅将精度输出上限30000提高到65536，其余temperature1/top_p0.95/top_k20/seed42/C32、198题、原生strict-match和80%门槛保持。

| 输出上限 | 正确题数 | 正式分数 | 原生证据/结论 |
|---|---:|---:|---|
| 30000 | 149/198 | 75.2525% | 完整来源及样本有效，未达门槛，旧失败完整保留 |
| 65536 | 164/198 | 82.8283% | 来源、全部filter、198唯一题及服务连续性通过，gate已签发/check |

新轮195stop/3length、timeout0；旧轮30length/25未完成答案。输出预算影响得到支持，但随机全量复测不能单独证明每条答案变化的因果来源。当前已达标anchor源码与启动/FlagGems配置未改变；真正的采样候选部署仍须新的高风险完整精度gate。

## 当前性能与候选

正式目标按P1K→P4K→P16K→P32K、D1024/C64/N128推进；当前P1K milestone为P1024/D128/C64/N128。新baseline003三轮预热20.12/29.99/20.36s、吞吐814.28/546.28/804.72tok/s，spread33.30%高于冻结5%，没有admitted测量轮。慢轮106个client ITL>1s、最长4.64s，另外两轮0个；先定位长间隔并补Prefill/Decode/Mixed阶段视图，不丢弃慢轮、放宽已冻结规则或宣称收益。

Gems采样私有候选20项actual-hook数值检查一致，但graph仍待验证。最小控制在尚未调用候选时已卡在原生`torch.cuda.Stream()`构造，Python栈与沐曦queue block创建超时已保存；不能据此宣称Gems kernel出错。所有私有GPU验证进程已精确退出，原模型服务继续运行。MoE大M tile与旧采样原型只有局部算子证据，未部署，无可声明累计端到端收益。

为验证队列资源假设，已准备只暂停目标8010服务约10–15分钟、独占验证后按原参数恢复的方案，未授权/未执行。自动审批拒绝了未来停止服务的自动化扩展，已请求用户明确服务中断授权；后台继续不停止服务的工作。用户已允许每30分钟跟进，automation `qwen36-35b` ACTIVE。最终四场景性能验收未完成，acceptance保持incomplete。

2026-10-14阶段诊断：Prefill D1与Decode D512/N64均未通过预冻结5%稳态，spread10.59%/79.31%，全轮保留0admitted。client原生时间线重建有42/56/57请求同步暂停，持续decode中位ITL基本不变；尚不能定位MoE/buffer或私有queue故障。prof-002两轮4新rank trace有效但未重现原暂停，24step后export约28.5s会污染E2E时间。已回到完整时间线低开销观测/变更capture窗口规划，当前source/FG/服务未变，精度gate有效、性能未验收。

2026-10-14用户批准短暂停服后，同源private采样20numeric+8graph全等，释放本服务资源后Stream/capture可完成，支持资源压力关联但不能确定显存/queue-count或原E2E停顿根因。仅本服务中断285.98s，原参数/source/FG恢复；新PID905636、C1/C8和两rankgraph通过，原164/198通过native rebind/check。无采样部署/新post-fix性能收益，review-004继续工程边界和低开销停顿定位。

2026-10-14 06:28UTC：私有采样engineering-v4补公共capability/旧API保护与标准tests/benchmark；CPU7项mock通过，真实public MetaX路径默认stream完成68数值+2empty alias，两独立Torch/服务白名单参考均全等、maskdiff0。新版本graph/标准benchmark/E2E待执行，无服务改动或累计性能收益；原905636及82.8283% rebind保持，私有进程已全部退出。完整新hash/回退/三次utility失败及终态见[op-003](../../../models/Qwen3.6-35B-A3B/metax/20261013-qwen36-35b-metax-e2e-current/optimize/op-003-gems-sampling-prototype.md)。后台跟进已更新且ACTIVE。

2026-10-14 review005：私有v4.1标准非graph182项174通过/8失败，集中p-only M32/64 BF16/masked；候选未部署，anchor82.8283%绑定仍有效。acc003同冻结tensor稳定复现1token差异，已隔离真`cumsum.out`累计概率边界（nativeCDF进同后半mask=0差异，GemsCDF=1）；alias/tie不是此次已确认根因，FP64输出未改善。下一步Gems算术次序修复试验，暂停候选晋级/新performance；正式四场景未完成。CPUobs002 20s纯CPUpilot准入通过但0模型性能请求，完整E2E观测deferred。详见[op003](../../../models/Qwen3.6-35B-A3B/metax/20261013-qwen36-35b-metax-e2e-current/optimize/op-003-gems-sampling-prototype.md)与同state。后台ACTIVE持续诊断，不停服务。

2026-10-14 07:33 UTC 更新：acc003 的 true cumsum.out 算术顺序已由同概率全向量/A-B-A与实际dispatch key证明；私有v4.2 backend6d07修复后原182非graph及扩展132全部通过。当前905636 anchor和GPQA164/198绑定未变。review-006保留新source graph/原生microperf资格债务，新停服验证方案仅准备未执行；原服务未部署候选，E2E收益仍无，正式验收incomplete。

2026-10-14 更新：qualification3实际服务reference graph96+native2全部通过，算术精度定位对已测scope完成；standardbenchmark仅13/18case、52/72pairs在300s预算后结束，整体incomplete。M1普通FP32两次测量约0.29ms→0.81ms，私有采样候选不部署。原服务恢复并用原正式GPQA164/198重新绑定到API944104/birth490527206、TP GPU6/7 host375983/4；currentgate q3-restored-anchor SHA888ce37b…，source12249/权重/镜像/挂载/全env保持，所有控制器退出。review007优先回到原生P1K全时间线CPU观测与稳态停顿定位，FG全启用，无已确认E2E收益，正式验收incomplete。

review019：P1K006全D1024三测量1133.4/991.2/1146.2tok/s，13.68%spread超10%门槛；晚出现attention SplitKV/MoE编译与13请求共同8.90s停顿已保留。无服务/源变化、正式精度gate有效；先CPU核专化/实际路径，不能将D128短场景稳定推广为P1K通过。详见模型op005/state。

review020：已从真实编译IR确认可优化维度为boundary SplitKV的TAIL_ROWS、MoE stage1的两个buffer mask界限；它们随实际批次/长度变化进入constexpr键，稳态预热不等于形状覆盖。两独立私有候选已规划，当前生产未改，尚无新实现性能/精度/graph结果；详见optimize/op005、op006、op007及state。

当前op011-v3：按用户收窄范围，topk恢复目标分支原5参/4参兼容及renormalize，仅更换公共导入库；fused_experts快路径只对NV/MetaX放开，其他平台保留原分步或原独立路径。77CPU回归通过，仅两生产+两测试变动，其他算子/Gems/vLLM/模型/原服务保持；无callerworkspace复用。源已保存，未重启/热重载，设备graph/新fullGPQA/E2E待验证；automation维持PAUSED。见[op011完整记录](../../../models/Qwen3.6-35B-A3B/metax/20261013-qwen36-35b-metax-e2e-current/optimize/op-011-moe-library-owned-dispatch.md)。

用户授权发布已完成：当前两处MoE源码及两份测试已推送至020plugin-opt-metax，[提交b8f2734](https://github.com/ZenithJoyH/vllm-plugin-FL/commit/b8f2734beb80738ce5e4f7c61c2056f41e5c9ba5)。远端SHA已核，提交字节与容器源一致；服务/容器Git索引及其他代码未改，无重启。77CPU回归已通过，新source设备graph/fullGPQA/E2E未执行，automation保持PAUSED。

FlagGems-vllm version update completed: official main05d0ff05->de2298be, editable0.3.0.dev1, existing GDN/attention/MoE local changes preserved. Syntax/API/nativeCPU34 passed, otherdependencies/Plugin/model/service unchanged, no restart. New graph/fullGPQA/E2E not_run; automationPAUSED. Seeop012 record.
