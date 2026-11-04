# op008：Plugin基于020plugin-opt分支

用户明确要求当前qwen3.6-35B容器Plugin基于 https://github.com/ZenithJoyH/vllm-plugin-FL/tree/020plugin-opt 修改。本轮优先处理该请求，op006 graph/微测与op007暂停推进，不重复已有回归。mx59/当前容器/8010范围不变，服务不重启，FlagGems完整启用。

Git只读clone固定targetcommit 8b059122e32b9ac47b9820a9c7b1bb95077481a4，与当前容器HEAD完全相同；完整git ls-tree逐字相同。当前处于detached HEAD，9个tracked未提交修改和10个untracked文件均保留。目标是命名分支020plugin-opt与现有基线对齐，源码内容无替换。既有GDN decode、MoE workspace/publicAPI及attention接线保持。未修改vLLM/FlagGems-vllm/FlagGems、模型和启动脚本。

归属：framework/source provenance，复用现有Plugin结构与Git分支，无新增dispatch或运行语义。所有模型/平台源码均不变；无需新增GPU/graph/GPQA。验证以分支commit/fulltree、变更前后每文件SHA/文件集、原dirty与git index及精确生产实例/source连续性为准。源码没变时不把分支名视为新性能候选；不声称性能改善。

快照 `/public-flash/jinghao/qwen3.6-35B/20261013-qwen36-35b-metax-e2e-current/patches/plugin020-before-source-20261015.tar.gz` SHAf6bf12c603ce889cf012548a34e0f3cc2307ce2cfbd2431a982e1cfba7ecbec1；before evidence `/public-flash/jinghao/qwen3.6-35B/20261013-qwen36-35b-metax-e2e-current/manifests/plugin020-before-20261015.json` SHA89db31ec231566cf9ccb491b3a5712497436b31c32183e313a629242a82d0d4a。回退方案：仅detach回同一8b059...，文件/index不改；不得reset/clean或丢弃用户dirty。若已存在同名分支但指向不同提交，停止并保存冲突，不强制覆盖。

状态：planned namedbranch alignment，尚未执行分支变更。当前已加载候选仍gdn+op005，GPQA170/198属于其现有源，privateop006088e未部署。

## 执行结果（2026-10-15 17:13 CST）

已在qwen3.6-35B容器 `/workspace/vllm-plugin-FL` 将detached HEAD切为`020plugin-opt`，HEAD仍8b059122e32b9ac47b9820a9c7b1bb95077481a4。目标分支与原基线完整git tree一致，没有新提交需要合入；未将本地优化错误描述为分支新增代码。517个源码文件的SHA/文件集合、index与dirty patch逐项保持，既有9tracked/10untracked修改全部保留。

分支操作前后，原只读取证代码完整核验四repo12252文件/model/fullenv/精确服务实例均保持；未重启服务、未改启动脚本或其他仓库，当前源和170/198 gate未变化。无新增GPU/graph/GPQA/性能测试，因无源码/运行行为变化而不重复跑模型。

回执 `/public-flash/jinghao/qwen3.6-35B/20261013-qwen36-35b-metax-e2e-current/manifests/plugin020-aligned-20261015.json` SHA9b4a5aedd9519c0fcb4cb899ff9f1f4ae23d6fb5f98f53c2d8f561ee6366d428。执行命令commands/align-plugin020-branch-20261015.py SHAe4ad7c65335e3252d79b49ffbf414c1dedd8c9682076ca7ba55afb85f4811cbc。回退commands/rollback-plugin020-branch-20261015.py SHA0e29a3bad0cdd0c6a1f20a1aca0d8a408e27113968b2b614ad8f595620f1b74b仅保存未执行，严格保护原文件/index，只恢复detachedHEAD；不删除本次branch或其他分支。

结论completed/source unchanged，无E2E收益；本次请求已完成。op006仍private088e、数值/键证明通过、graph/nativebenchmark pending，未部署；op007尚未实施。后续既有优化只继续准备具体资格/恢复方案，不能把本次分支操作作为新停服授权。

## 用户询问020plugin-opt-metax兼容性（只读，2026-10-15）

新分支 https://github.com/ZenithJoyH/vllm-plugin-FL/tree/020plugin-opt-metax 已固定为f99f9dbbb4db72ea3ba93aa53e19a48f1ad4f641，区别于上次020plugin-opt的8b059。当前容器仍020plugin-opt/8b059加原dirty，未切换/覆盖/重启。本轮完整12252 source/model/env/实例只读取证保持。

目标513tracked文件与当前517工作文件比较：506同，6改（5生产+1test），目标新增1test，当前额外5test不在目标。目标396个Python文件语法compile通过，不代表设备测试。GDN decode与packed方法AST一致、GDN hook/FlagOS attention adapter/MetaX配置逐字相同；prefill新增vendor_name/state布局和日志，MetaX仍V-major；vendorFlashAttention新增默认关闭的VLLM020_CONTIGUOUS_SINGLE_PREFILL，不属于当前FlagOSAttentionFLImpl自动路径。

关键差异：目标没有当前fused_moe_utils.py中的MetaX public fused_experts_impl+caller output/workspace复用，MetaX会进入分步MoE；impl/fused_moe.py的MetaX/no_tle与flaggems_vllm包装改回flag_gems公共符号。另外register_ops可选导入改为宽泛ImportError捕获，当前严格区分缺包/内部依赖错误。不能把整分支当无差异替换，不能沿用当前source GPQA/性能结论。

只导入/getattr实际API探针返回0：当前FlagGems-vllm的vendor_name=metax、chunk、recurrent/packed、fused_experts_impl/workspace能力均存在，来自现MetaX实现；目标MoE所需flag_gems topk_softmax、moe_align_block_size_triton、invoke_fused_moe_triton_kernel、topk_softplus_sqrt、grouped_topk、moe_sum也全部存在。此前AST未直接声明仅因动态/星号导出，不能将ASTFalse视为缺失。没有执行张量/算子/Stream或发送请求，未报ImportError。

判断：接口侧可作为当前容器的新基线；原样替换会改变MoE路径，尚无新branch模型启动/graph/GPQA/P1K运行证明。建议基于新分支保留当前两处MoE接线及必要importguard；若选择原样分支作为新候选，也必须重新验证，不能默认等价。用户本轮仅询问，未授权实际切换，未做变更。

比较回执 `/public-flash/jinghao/qwen3.6-35B/20261013-qwen36-35b-metax-e2e-current/results/plugin020-metax-comparison-20261015.json` SHA703d1c312456f73803923f778a2a1abc30cfc819a783ad238616351a4e437673；当前证据results/plugin020-metax-compat-current-20261015.json SHA4ea1d144ebe6f6b30b21a73dec66d6ab205d98dbc0b82880817566cf27ef8494。API实际导入 `/public-flash/jinghao/qwen3.6-35B/20261013-qwen36-35b-metax-e2e-current/results/plugin020-metax-import-api-20261015.json` SHA10bbbde8caa383258dd348e1d7c3dc0b51bb01e735e86cc6456af4578a9df249，probe commandff75181187365631e5693bb4d83c58faf1fb2268533a0d7b0eeef90d93ad8dc1。所有creator已完成不要重复；只读static符号声明45efecee...为较弱证据，实际API导入为最终导出事实。
