# op010：直接采用MetaX分支并保留MoE无workspace调用

用户明确要求容器直接使用020plugin-opt-metax分支代码，并带上MoE无workspace复用、公共fused_experts_impl按NV模式调用的修改。本轮候选完整基线f99f9dbbb4db72ea3ba93aa53e19a48f1ad4f641（Git ls-remote新核一致），不是上轮仅切020plugin-opt分支名。除两处MoE生产文件，目标分支tracked源码和测试保持原样；当前额外5个本地测试保留不删除。MoE覆盖：impl/fused_moe.py保留既有MetaX库接线/no_tle与相关适用条件；fused_moe_utils.py沿用297da499直接public call+output.copy，无callerworkspace/能力探测/旧API分支。

当前环境仍mx59/qwen3.6-35B/8010/TP2 GPU6/7，原地例外；不重启/停止服务或容器，不碰其他负载，vLLM/Gems-vllm/FlagGems/模型/tokenizer/启动脚本只读。方向framework/version baseline transition+operator call contract，用户明示选择版本，不预设收益。依赖API此前当前真实import探针全存在；新分支GDN prefill布局/日志和vendor optionalcontiguousprefill采用原样，完整FG白名单不变，不设置新环境开关。register_ops按分支原样，不额外移植旧strict-importguard。

全部备份 `/public-flash/jinghao/qwen3.6-35B/20261013-qwen36-35b-metax-e2e-current/patches/op010-before-plugin-source-20261015.tar.gz` SHAf7be9ab6fcf983b666799f3db0c3fb2febd497ecdb1b5585ec0af2ce73d4bb73，refs bundle/index/dirty patch均已保存，完整SHA见before `/public-flash/jinghao/qwen3.6-35B/20261013-qwen36-35b-metax-e2e-current/manifests/op010-before-20261015.json` SHA61261d9afb628ed3fb58857b51f4810344b867d143a608a83b1375b448425a8e。新候选518files=513targettracked+5保留额外tests，分支偏离仅两MoE生产文件，其他与target逐字一致；与当前生产候选预期改变4原文件并新增1test，MoE297da499本身保持。Git原index/branch可精确回退，不用reset--hard/clean，不删除用户未提交代码。

先在容器私有目录stage候选跑原生CPU regression：分支test_gdn_latest_routing/test_metax_gdn与MoE public API/contract四文件；GPU functional/graph/真实模型GPQA/P1K不跑。mode minimal-regression/scope CPUcontracts，整体graph/设备验证仍incomplete。必须全收集/无fail/无skip后才能更新源码。执行前保存manifest和bundle/source tarSHA；应用只同步明确target文件，保留其他本地测试和忽略产物，Git sourcebase/head切到真实f99，不改其他仓库。

用户授权只涉及本次代码，不新增服务中断窗口；最终磁盘候选与运行中982315旧加载实例分开记录。170/198只属旧source，不能沿用为新branch gate；新source以后真正加载需graph/至少2replay、最小数值与新全198/65536/temp1/top_p.95/top_k20/seed42/C32/80 gate后再性能。当前正式P1K006失败保留，op006/007私有研究不叠加。

状态candidate_prepared_CPU_pending，PR experimental，没有模型收益结论。

## 已应用（2026-10-15 18:15 CST）

当前容器 `/workspace/vllm-plugin-FL` 真正采用分支`020plugin-opt-metax`，HEADf99f9dbbb4db72ea3ba93aa53e19a48f1ad4f641。513个targettracked文件中，仅impl/fused_moe.py和ops/fused_moe/fused_moe_utils.py两处保留本地MoE补丁；其余与分支逐字一致。5个额外本地测试保留，工作文件集合518。git diff相对f99仅两MoE文件，其余分支代码干净；无提交、推送、reset或clean。

MoE调用仍297da499：直接公共gems.fused_experts_impl，再output.copy，不传out/workspace、不探测能力/旧API；MetaX namespace和既有能力边界留在原MoE接线。实际写入当前工作树5路径（GDN prefill/注册、vendor attention、新prefill test、分支GDN routing test），MoE改动已在op009所以字节不再变化。

精确候选私有stage原生pytest **49passed/0failed/0skip，29.75s**：target GDN latest5/GDN8，MoE public28/contract8。CPU张量/mocks，未执行GPU算子/模型请求；不代表设备graph/完整精度。CPU回执 `/public-flash/jinghao/qwen3.6-35B/20261013-qwen36-35b-metax-e2e-current/results/op010-CPU-contract-20261015.json` SHA00c209927136abf90e060f12708a610174766da6f42241e6e4828975891ebf83；XML531c68907e208cc02ce6349d3ad531d59f470b65fabc7c43f6a86cd751eedde9，command ccf5778a49d4afea145d3e2a5a1391873347330420da02280f8a164dc3d31805。

最终应用回执 `/public-flash/jinghao/qwen3.6-35B/20261013-qwen36-35b-metax-e2e-current/manifests/op010-applied-20261015.json` SHA79e783e45c525bd9a72a6a1479062bbb099c4114de2ec77eb3fff11313c4b7c1；source manifest `/public-flash/jinghao/qwen3.6-35B/20261013-qwen36-35b-metax-e2e-current/manifests/op010-plugin-files-20261015.json` SHAb6dacd53e3a588ecb96054e3ac8d36437233da25b5a530f4774099453f9b3756；applycommand722c9fa8bda17129121bb9f46313aa14624273a03b05551ba685bfc1c0063b49已执行不可重放。MoE单独patch `/public-flash/jinghao/qwen3.6-35B/20261013-qwen36-35b-metax-e2e-current/patches/op010-branch-moe-overrides-20261015.patch` SHA1551667a10e4ce203d03e528931523342206432ed961d3460f264d7f0266cb9e；相对旧工作树patch `/public-flash/jinghao/qwen3.6-35B/20261013-qwen36-35b-metax-e2e-current/patches/op010-from-previous-worktree-20261015.patch` SHA75b9722b204425101e590a556c2d245610eb406703c24d0c90f126d5b83fb306。rollback-op010-metax-branch-20261015.py SHAf94f3b56ae72c358436879e3a4364535e5c0e24bad48667ada77c05f711ea7e3仅保存未执行，保护每文件/branch/index，能回到op009源码，不能随意重放。

Git基线更新通过导入已核SHA的f99 bundle、设置新分支和其index完成；没有用forcecheckout覆盖dirty，原source/index/refs归档可回退，既有5额外测试和ignored构建产物不清理。未pip安装/升级依赖，源码HEAD与已安装distribution版本字符串分别看待，实际源码以Git/source SHA为准。

post核12253文件：Plugin为明确新candidate，其他3repo、权重/tokenizer、完整env/prefixoff/FG完整白名单和原API982315/497862111保持，服务未重启/未hotreload。当前磁盘candidate=gdn-op005-plugin-f99f9dbb-moe-public-297da499；原加载source gdn+op005及170/198只作历史，不绑定新分支。不执行新GPQA/性能/设备graph；后续新source实际加载需单独服务生命周期方案及必要授权、graph/两replay/数值/新全198/65536/80 gate后才能正式性能。当前整体minimal incomplete、PR experimental、无E2E收益。

2026-10-15 16:23UTC最新：隔离缓存后的正式GPQA已完成，UUID d7e72aff3e6a4a7c8809d3ae7113be32 strict164/198=82.8283%>=80，0timeout；全198/65536/temp1/top_p.95/top_k20/seed42/C32不变，全部filter/原生来源/config/12355源码/当前service/env/model/tokenizer/镜像挂载连续性通过。CPU收尾15:56:07完成，nativeissue/check成功：gate accuracy/acc006-isolated-cache-g64k-accuracy-gate-20261015.json SHA9fdcc14eec68a6203a3c46cbf7e45c46fdcea5474ba4def838119fedaf98a642；terminalcontinuity06b0a111d267331fd8525ed33c6be9b66add1385f36273844fd7c725683b8fb7，terminalvalidation4f6834150a253a745c977c3254a54fd3ba48a6ee734669d5f8e3d30c9e6940d8。未重复GPQA或issue/validator。当前API1025146及GPU6/7workers保持，旧cache/source未动，原19FG范围不变。

缓存隔离执行边界得到反事实支持：相同源码/参数，旧cache启动Vheads8且0/198，新增VLLM_CACHE_ROOT后K/V均1head、两TP各22actualgraphreplay、C1/C8和新full164/198通过；可恢复性能工作，内部缓存key/二进制失效机制仍不作过度确定归因。原始0/198、C1无关输出及私有负面/utility失败全部保留，不改判为通过。该分数只绑定当前组合/环境，不能归因单个Plugin/MoE/library改动或冒充NV验证。原用户启动脚本尚未写入cacheRoot；下次reload须保持隔离策略，不授权未来停服。

P1K新scene-entry基线已16:21:45启动：run-idop013-p1k-full-001，modebaseline/rolebaseline，controller1531875/birth502086404，nativeclientns1032848/birth502086510。完整P1024/D1024/C64/N128/temp1/ignoreEOS/seed42/range0，4warm末3spread<=5%/3measuredspread<=10%/600sround/全轮保留/无profiler。当前仅新scope单实例基线，不能与旧20scope不稳轮算精确gain。新planSHAf0a5bac2...、comparison8bbbadbd...、v2identityb5be1a8c...、observer1dfbb147...、v2launch36841b6f...。Freshsource/gate/APIidle/资源/镜像挂载/timeNS/cgroup通过。首版dryrun因baseline不能传--accuracy-gate而拒绝，0benchmarkrequests/无run目录，原文件日志保留；v2仅修原生接口，外部nativecheck+gateSHA仍冻结在identity/launch，七轮dryrun通过，不放宽测量/精度标准。真实测量尚无结果。

CPU收尾器1533067/birth502096784已16:23:29启动，commands/wait-finalize-op013-p1k-full-001-20261015.py SHAde78eacd2efda4335ae607c3812398f241dca454fc922a37ada40ac5b149d4d3；launcher11b45361...已执行，不可重放。只等现有native退出后finishd14dd85a...与analyzef929f151...，不产生新GPU工作。监控monitor-op013-p1k-full-001-20261015.py SHA3ffd90624dde2d41c84fb96fbe3a88ef0cafdb9b1a5d4775e8ec20e8f5c911d4。终态核native全部轮+稳定性+observer开销+source/gate连续性+compiler/共同停顿时间线；未达稳态/incomplete保留，不丢慢轮/自动加warm。review024首优先本轮baseline，其后按实际当前owner/routing/compiler证据重排；不能切P4K/最终acceptance通过。所有旧creator均不重放，heartbeat继续ACTIVE。
