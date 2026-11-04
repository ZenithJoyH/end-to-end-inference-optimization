# op-005：移除采样实验开关并精简 Worker 条件

已完成并回写 mx-59 / qwen-vl；源服务未启动或重启。按用户2026-10-13指示整理 op004，属于既有 operator/replace 接入整理，retained-code-only，不新增 kernel，不宣称端到端收益。

## 最终代码及必要性

- MetaX topk_topp_sampler.py 删除 VLLM_FL_METAX_QWEN3VL_EXACT_TOPK_TOPP_M64 条件与未使用的 os import。按原支持范围自动选择库 API：连续 FP32 logits [64,151936]、同设备连续 k/p [64]、正确 dtype；其他输入走原 reference。采样 kernel 未改。
- 测试不再设置旧开关；删除 disabled 测试、增加 missing_k/missing_p，最终8项。共享挂载 start-model.sh 仅删除一行 export，设备4/5与其他参数不变，SHA防漂移并保存备份。
- Worker 保留当前必要的 MetaX 条件，删掉额外日志/else。source/clone原始导入均复现 kernel_warmup → minimax_m3_msa_warmup → MiniMax NVIDIA model → index_topk 的 TypeError: jit() got an unexpected keyword argument 'do_not_specialize_on_alignment'。无条件导入发生在模型检查前，会阻止 graph capture。原有 warmup 兼容环境变量没有 Python 启动 hook，不能解决错误。实际模型 dummy-run/compile/capture 保留；上游兼容修复后可删除条件。

Worker 最终只保留：

    if current_platform.vendor_name != "metax":
        kernel_warmup(self)

_can_use_metax_fused_experts 保持字节不变，是完整 MoE 的支持范围/dispatch 判断，并非新算子：确认 MetaX、支持的原生浮点 SiLU、无量化，且 invoke_fused_moe_triton_kernel/moe_align_block_size/silu_and_mul/moe_sum 均实际选择 default.flagos。不绕过显式 vendor/reference 或 failed-impl fallback。无 LoRA、没有预加 router 权重的限制在 apply 调用处；其他路径保持原实现。helper 不执行设备计算或另建 dispatch manager。

## 环境和验证

源镜像、独立 qwen-vl-sampling-opt-20261012 快照与规范化挂载门禁通过，沿用 op004；/workspace 为两个容器的私有目录。四仓库HEAD/工作区与修改前SHA存于 commands/op005/audit.json、current.json。vLLM/FlagGems只读，本轮未改库kernel和完整MoE adapter。

原4/5被无关服务占用，未争抢/停止其负载。用户随后明确释放两卡，实际为0/1；本轮单卡算子用0、TP2模型用0/1，源配置保持4/5。只验证功能，不比较性能或追认为4/5服务的正式精度gate。

按项目 inference-accuracy-evaluation 的 minimal-regression：

- 49项采样数值/graph与8项Plugin选择/边界测试通过。实际hook在无旧开关环境命中库MetaX API；M64 capture后BF16网格/任意FP32/正值ties各 replay 两次，和reference bitwise一致。
- TP2 BF16、max-num-seqs64、max-batched-tokens8192、原FULL_AND_PIECEWISE/max-capture128成功启动。原生 PIECEWISE 19/19、FULL 11/11 capture完成；两worker实际完整MoE调用及至少两次原生replay。观察计数含startup/warmup，不解释为逐请求次数。
- 2 single + 2×C8 =18请求成功且非空。single temperature0；C8 temperature0.7/top_k20/top_p0.8，max_tokens96。15项因长度上限截断，属于健康观察，不冒充正式分数。
- 整文件AST核验仅采样env/os删除、Worker等价条件改写和日志删除。采样/路由测试Black/isort/flake8通过，Plugin git diff --check通过，vLLM工作区干净。
- Source四文件SHA匹配，生产Plugin/测试/配置无旧开关引用，MoE helper SHA未变。回退dry-run验证3私有文件+1启动脚本，mutated=false。

控制检查先后因误选AST条件、引用其他vLLM日志措辞失败，保留旧脚本。前者在部署前被门禁阻止；后者按当前原生capture/replay核验同一批18响应，未重复请求、未降低graph要求。没有数值测试失败。最初拟在资源忙时仅做代码整理的降级方案未采用；用户释放设备后完成完整门禁才部署。

正式GPQA/无profiler端到端性能 not_run/not_measured；pr_readiness=needs_revision，其他MetaX模型warmup和非目标硬件未测。结束只停止本轮18405验证服务，0/1释放，两个目标容器无剩余vLLM进程；未停止/重启源服务或无关服务，未提交/推送/创建PR。

## 产物与回退

远端案例 /public-flash/jinghao/qwen3-VL/20261012-qwen3vl-metax-sampling-migration；66项原件及SHA见 manifests/op005-artifacts.json，关键证据及最终四文件SHA见 state.yml。

- 算子/实际hook graph：results/op005-operator-validation.json、op005-dispatch-graph.json。
- TP2/原始响应：results/op005-model-graph-validation.json、op005-service-responses.json；logs/op005-model-service.log。
- 部署：commands/op005/apply-v3.py deploy；results/op005-deploy-v2-manifest.json、op005-deploy-v2-mounts.json、op005-source-postverify.json。
- commands/op005/cleanup.patch 是本轮4文件差异；patches/op005-final-Plugin.patch / op005-final-FlagGems-vllm.patch 为完整工作区补丁，包含前序与已有改动。
- 回退：python3 /public-flash/jinghao/qwen3-VL/20261012-qwen3vl-metax-sampling-migration/commands/op005/rollback-v2.py 默认dry-run；显式 --execute 才恢复四文件，候选SHA防漂移、拒绝active source service，不自动重启。旧op004回退脚本不可直接当本轮回退。

## 后续 r2：按用户反馈移除独立 MoE helper

用户进一步要求判断 helper 能否去掉，认为独立写法奇怪。本次不改变完整算子支持范围，把原条件合并进 TritonExpertsFL.apply 的既有入口，删除函数定义；使用既有 cached get_default_manager 查询各相关 op，保留原策略。Worker 仅把“不兼容的NVIDIA-only kernel”注释纠正为“不兼容的MiniMax kernel”，逻辑不变。

报错准确符号是 vLLM models/minimax_m3/common/ops/index_topk.py:82 的 _index_block_score_kernel，装饰器在81行；它对128-token KV block计算index query/key得分，用于MiniMax稀疏attention选择block，并非Qwen采样top-k/top-p。入口 kernel_warmup.py 无条件导入 minimax_m3_msa_warmup，后者第7行导入 nvidia.model.MiniMaxM3SparseAttention，继而导入common.indexer/common.ops.index_topk；jit在导入期因不支持do_not_specialize_on_alignment报错。尚未执行kernel，也没进入warmup函数内部针对模型/SM100的判断。此前“NVIDIA kernel”描述过宽，代码注释一并纠正，不改vLLM。

r2计划：独立容器先执行旧helper版与inline版的实际apply路由对照，覆盖平台/LoRA/dtype/激活/量化/预加权/逐op策略；两组目标shape native MoE数值及graph变化输入两次replay；原TP2 FULL_AND_PIECEWISE服务capture/两rank replay和smoke/C8；成功后SHA门禁回写qwen-vl并保存新回退。沿用同一op005整理点，不作为新优化收益；formal GPQA/性能仍未测。


### r2最终结果

独立helper已删除，支持范围/dispatch条件内联到apply既有完整MoE分支，生产文件净减少15行。manager是现有全局缓存实例，各op通过缓存getter查询，无新manager/设备计算；完整计算尾部字节未变。Worker只纠正注释，“NVIDIA-only kernels”改为“MiniMax kernels”，完整AST与r1相同。

旧helper版与inline版实际apply对照20项通过：MetaX/NVIDIA/Hygon及LoRA（后两者为控制路由，不代表硬件通过）、三种原生浮点、float8/int32、GELU、量化、输入预加权、四项逐op vendor选择、实际policy context覆盖及恢复。实际MetaX BF16 T64、FP16 T1（E128/H2048/I384/K8）数值和各两次变化输入graph replay通过；容差沿用op004 BF16 .03/.03、FP16 .006/.01，最后replay均bitwise相同。没有新增kernel或性能测量。

原TP2 FULL_AND_PIECEWISE独立服务（设备0/1，端口18406）成功capture，两worker实际库完整MoE命中及至少两次原生replay（含startup/warmup）；2single+2×C8共18请求成功非空，15项因96token上限截断。样例问答连贯、无空输出/客户端错误。然后完整门禁回写qwen-vl两个私有文件。source helper无定义/引用、Worker AST不变、采样SHA/旧开关删除保持，vLLM工作区干净；两文件回退dry-run verified_files=2/mutated=false。源服务未重启，验证服务停止，0/1释放。正式GPQA/性能未测，PR未测范围保持。

新控制目录 commands/op005-inline；45项产物/SHA见 manifests/op005-inline-artifacts.json。关键结果为 results/op005-inline-validation.json、op005-inline-model-graph-validation.json、op005-inline-deploy-manifest.json、op005-inline-source-postverify.json、op005-inline-rollback-dryrun.json；当前完整补丁为 patches/op005-inline-final-Plugin.patch / op005-inline-final-FlagGems-vllm.patch。

当前回退使用 commands/op005-inline/rollback.py，默认dry-run，--execute恢复本次两文件到r1。旧r1/op004回退的SHA守卫会拒绝覆盖r2；如要回退更早版本须先恢复r2再核验原回退。归档中的helper定义不参与生产执行，前文“helper保持不变”是r1验证事实，当前以此r2结果为准。没有提交/推送/创建PR。

## 当前后续状态（op007）

2026-10-13：[op007](op-007-worker-moe-cleanup.md)已验证并回写默认FlagTree3.6链路，恢复正常Worker warmup、删除旧vendor MCTLLASS代码与启动export。本文上述版本/保护状态为当时实验事实，当前运行以op007/state为准；原采样与完整MoE算法保持。
