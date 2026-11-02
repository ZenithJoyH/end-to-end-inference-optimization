# MiniMax Flash 新 topk-sigmoid 容器精度

历史acc-001三项完整评测已完成并于2026-10-22连接恢复后核验：GPQA167/198=84.34%（阈值81%，原生gate复验通过）、Math500467/500=93.40%、ERQA267/400=66.75%（后两项无指定阈值）。原生队列北京时间02:13完成，无重跑。

[结构化状态](../../../models/MiniMax-M3.1-Flash-W8A8/ppu/20261021-topk-sigmoid-tp8-accuracy/optimize/state.yml) · [实验说明](../../../models/MiniMax-M3.1-Flash-W8A8/ppu/20261021-topk-sigmoid-tp8-accuracy/optimize/acc-001.md)

远端：`/mnt/nfs/users/jinghao/minimaxM3.1/optimize/20261021-minimax-m31-topk-sigmoid-tp8-accuracy`；原生gate：`/mnt/nfs/users/jinghao/minimaxM3.1/optimize/20261021-minimax-m31-topk-sigmoid-tp8-accuracy/accuracy/topk-sigmoid-first8-t1-suite-20261021-01/gpqa/accuracy-gate.json`。

设备数值/graph、模型graph105+2均通过；精度完成时服务/源码/编译器身份与评测一致，健康HTTP200。Plugin仍走split桥接，完整FV API仅独立GPU验证。ERQA400题ID集合完整一致，原始NUL-only0、空响应0、生成触顶7。

采样1/.95/-1，生成18000/28000/30000，并发32/32/16，TP8物理0–7，prefixcache关闭。精度监控PAUSED，服务保留；该精度阶段未启动性能或新优化。网关中断期间原生队列独立完成，未复用历史分数。

## 后续完整与分步入口性能对照

[perf-002](../../../models/MiniMax-M3.1-Flash-W8A8/ppu/20261021-topk-sigmoid-tp8-accuracy/optimize/perf-002.md)：PPU810E/TP后E128H6144I384/topk4/W8A8/BF16，原样7个M×两路由×两独立进程，及小M统一GEMM选参归因均完成，所测输出逐位一致。原样均匀路由M1完整入口慢42.43%，M8/16/32慢6.08%/11.13%/9.84%，M64/1024/8192基本持平；集中路由M16/32可快5.12%/11.13%。统一配置后小M差距缩小，支持配置策略主因；没有模型端到端吞吐结论。当前保留split桥接，原服务和源码未改。

## 后续选参与初始化收敛（2026-10-22）

[op-003](../../../models/MiniMax-M3.1-Flash-W8A8/ppu/20261021-topk-sigmoid-tp8-accuracy/optimize/op-003.md)：按用户要求对齐完整入口动态W8A8 GEMM策略，保留原有受限调优。首次量化单变量替换为原vLLM实现没有消除差距；进一步复用分步路径已有alignment合并清零，最终完整调用graph相对split为−0.57%～+0.16%，基本持平。28个shape/路由case输出逐位相同；候选和安装后测试均102 passed、7 skipped（仅物理0，不能称新8卡验证）。

FV曾安装两文件增量，随后用户因收益基本持平要求回退；现已恢复实验前topk-sigmoid版本，原8045模型实例未重启、仍走split。旧精度分数保留为旧实例历史，不当作新完整入口模型gate；没有本轮模型E2E吞吐结论。准确文件/源码tree、命令SHA及可校验回退备份见state，原始材料在本远端case的performance/op003-*、patches/op003-installed-20261022-01。

## 最终 PR 清理（review-004）

[最终保留范围](../../../models/MiniMax-M3.1-Flash-W8A8/ppu/20261021-topk-sigmoid-tp8-accuracy/optimize/review-004.md)：进一步撤除集成阶段较早的完整入口扩展/量化辅助实现和实验测试，Thead完整入口恢复官方HEAD语义；保留原split算子及topk-sigmoid。必要融合测试并入既有test_fused_moe.py，原实验测试文件已删除。118 CPU+75物理0设备测试通过，样式/真实导入/dispatch、完整最终补丁及reverse-check通过；23个Plugin差异文件、8个FV差异文件已归档为两库PR补丁。原8045仍同实例健康，不重启、不跑新全量精度/压测、不提交推送。正式分数仍仅属于原评测组合。

## Plugin进一步局部收敛（review-005）

[本轮记录](../../../models/MiniMax-M3.1-Flash-W8A8/ppu/20261021-topk-sigmoid-tp8-accuracy/optimize/review-005.md)：W8A8三个激活参数统一为实例内kwargs，私有activation helper集中可选融合及普通回退，测试复用fixture/参数化。3生产+2测试文件，无新增dispatch/源码文件/环境变量。119 CPU合同、4物理0设备测试通过，graph覆盖非融合/融合/shape回退、每项两次变输入回放；AST及完整补丁reverse check通过。FV/FG/compiler不变。8045保持原实例健康、没有重启/推理请求或新模型精度/性能；旧正式分数仅为历史。

## 用户根脚本启动失败（diag-006）

[诊断记录](../../../models/MiniMax-M3.1-Flash-W8A8/ppu/20261021-topk-sigmoid-tp8-accuracy/optimize/diag-006.md)：根脚本/容器默认环境缺少既有FV=1开关，topk_sigmoid选择reference.torch并调用不存在的_moe_C.topk_sigmoid，导致15:00启动失败。独立进程复现缺符号错误，开启原开关后选择default.flagos；没有重启模型或修改脚本/源码，也未证明修正后完整服务已启动。原8045与用户新8035均不可访问；历史精度不变。

## new2重启服务全量精度（acc-007，完成）

[本轮记录](../../../models/MiniMax-M3.1-Flash-W8A8/ppu/20261021-topk-sigmoid-tp8-accuracy/optimize/acc-007.md)：用户MiniMax-M3.1-new2/8035/TP8物理0–7，保留开启的prefix cache。105+2模型最小通过，单次GPQA198→Math500500→ERQA400全部正常完成，原生控制终态2026-10-22T20:56:39.272953+08:00。采样1/.95/-1，生成预算18000/28000/30000，并发32/32/16，独立response cache。

本轮GPQA167/198=84.34%（strict-match达到81%，原生gate再次check通过），Math500464/500=92.80%，ERQA259/400=64.75%（后两项无阈值）。实际唯一ID分别198/500/400，ERQA冻结集合与evaluated400项一致；原始NUL-only0、空响应0、触顶8。Math500原生generation_kwargs与冻结proof一致。

原生gate：`/mnt/nfs/users/jinghao/minimaxM3.1/optimize/20261021-minimax-m31-topk-sigmoid-tp8-accuracy/accuracy/new2-t1-suite-20261022-01/gpqa/accuracy-gate.json`，SHA `2e21ae469db8910f775fd3f425e53edeb769c4ad509130f80cf8a07abd24bde1`；完整结果SHA `f4d8904649193d4c266b5487f1ec90b7225e4ac0a87638a8288b525a76d60e51`。其余原生路径/SHA见state的acc-007.native_evidence。终态同一8035实例健康且源码/编译器/runtime未漂移，没有重启或远端变更、性能测试；监控`minimax-m3-1-acc-001`已通过应用工具删除。旧acc-001与各优化/回退历史保留，不混用分数或推导吞吐收益。

## 原容器精度差异对照（diag-008）

[对照记录](../../../models/MiniMax-M3.1-Flash-W8A8/ppu/20261021-topk-sigmoid-tp8-accuracy/optimize/diag-008.md)：现有旧档GPQA171→new2 167，正确转错7、错转对3，7个新错均可提取答案；Math461→464，正确转错7、错转对10。题目/prompt/target指纹及实际payload相同，两个归档都为100000上下文/C32/prefixcache开启，源码组合不同，未确认根因。用户另报32768上下文最高GPQA89.90%/Math93.80%/ERQA66.25，原生产物待定位，不能用该旧档冒充最高分轮次。必要重测将使用64并发；本轮仅分析原产物，未发模型请求、重启或改源码。

## 新旧容器既有性能比较

[perf-009](../../../models/MiniMax-M3.1-Flash-W8A8/ppu/20261021-topk-sigmoid-tp8-accuracy/optimize/perf-009.md)：读取10月20日旧Flash MiniMax-M3.1-new与10月22日new2的D1024/C64/N128三场景CSV，新版总吞吐4K +0.91%、16K +0.82%、32K +0.86%。每项3轮成功128请求，历史SUMMARY仅第2/3轮均值；无完整稳态/独立服务重复/原始身份和cache命中证据，属于小幅观察，正式性能收益未证实。旧opt7预览时期系列另列，不混为同Flash基线。本轮纯只读，没有新压测或服务变更。

## 用户历史GPQA样本与最新实例

[diag-010](../../../models/MiniMax-M3.1-Flash-W8A8/ppu/20261021-topk-sigmoid-tp8-accuracy/optimize/diag-010.md)：用户文件实际仅doc0一题，上限95109/T1/.95；最新容器当前MiniMax-M3.1-new-new/8035，以还原的原messages单题实测输入395/输出1335/strict-match1.0，旧文件同题也正确（输出1028）。近期全量GPQA18000上限与该旧记录不同，单题不能解释或复核历史89.90%总分。首个重复JSON封装探针输入428，不可比，已保留；仅修正后395输入的一次请求用于结论。未改服务/源码、未全量重测或签gate；当前实例已重启，acc-007仍为历史全量证据。

## 用户完整历史GPQA样本更新

[diag-011](../../../models/MiniMax-M3.1-Flash-W8A8/ppu/20261021-topk-sigmoid-tp8-accuracy/optimize/diag-011.md)：同一路径新版本有完整198题/396记录，strict-match180/198=90.91%，原生离线复核全部一致；旧95109生成预算，近期new2/旧C64均18000且167/198。题目、prompt、target全一致，new2少13题中11触顶、10旧输出>18k，预算差异优先但不能归因全部或认定版本回归。本轮无模型请求或全量重跑；完整文件上传被自动审批拒绝未执行，保留本地路径/SHA和安全汇总。

## 上游Plugin PR

用户报告重启后对齐评测配置精度可对齐并明确授权提交，现已创建[flagos-ai/vllm-plugin-FL #634](https://github.com/flagos-ai/vllm-plugin-FL/pull/634)。当前容器23文件只读导出，基于main f41b7de解决单个注册冲突（保留Ascend及MiniMax），119CPU合同、10项隔离元数据测试和样式检查通过。无FV/FG/compiler源码、私有产物或性能声明；未改生产、重启服务或新发模型请求。详情见[pr-012](../../../models/MiniMax-M3.1-Flash-W8A8/ppu/20261021-topk-sigmoid-tp8-accuracy/optimize/pr-012.md)。

PR #634 CI跟进：初始多平台unit测试前提问题已修复，提交`92682e3`仅改5测试文件，23项隔离逻辑及Ruff通过，新平台CI正在复验；本次未访问或改动运行容器，未改生产代码或CI门禁。完整证据见pr-012。

CI截至20:19：五平台functional（NVIDIA/天数/PPU/MUSA/沐曦）和静态/安全检查均通过；昆仑芯/燧原运行、海光排队、下游E2E未终态，尚不能确认全绿。修复后无新失败，运行容器未访问或改动。

PR #634 terminal CI review: 42 success / 6 skipped / 5 failure including gate. Three dependency-fetch network failures and T-Head KV admission with external device occupation remain. PR description updated. CLI and GitHub integration lack official Actions rerun permission; administrator retry required. CI is not green. No running container accessed or modified. See pr-012.

2026-10-24: PR #634 merged main aae3c1c, resolving two MoE conflicts in1172e4b. Preserved upstream native modular fallback and FlagGems split path;67 scoped checks passed, full CI pending. Title changed to feat(thead): support MiniMax-M3.1 W8A8 inference. No running-container changes.
