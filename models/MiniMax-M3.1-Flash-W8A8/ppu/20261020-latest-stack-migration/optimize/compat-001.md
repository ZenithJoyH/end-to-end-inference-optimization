# compat-001 复核 top-k autotune 兼容必要性

结论：当前默认编译栈仍需要保留 topk16 的绕过。用户要求保留的 GQA head-tile 兼容也未改。本轮未改 Plugin、FV、FG、vLLM 或 FlagTree 源码、安装、启动脚本；没有启动模型、设备计算、评测、压测或停止其他工作负载。

## 实际证据

目标为 `minimaxM3.1-opt-latest-20261020`，Plugin官方main a696859b工作区，FlagTree `0.6.2a1+ppu3.6` / Triton3.6.0 / PPU sm80、warp32。使用当前vLLM0.24安装的原生 `_topk_index_kernel`，源SHA `08a1ecfee1a8890dbca7934fdd474cb19f8f38d475c1cced938145d1a177d874`。提取三个相关函数时保留完整函数体和原始decorator；以原生JIT binder核对signature/constexpr/非空attributes，六项一致。

1. 直接编译原始六候选 K=2048/1024/512/256/128/64，全部生成PPU hgbin；另有K128未特化对照也通过。这只排除了原始配置本身无法编译，不能证明autotune可用。
2. 当前 `FLAGTREE_AABS` 默认True，独立启动脚本也未关闭它，source PPU SDK env后只读核对仍为True。执行当前编译器真实的 `auto_adjust_block_sizes`，对score块数1/8/16/17/32/128/256检查，六个候选的调整副本均被改为K=1；T仍为16。依赖映射为 `{"BLOCK_SIZE_K": "init_blocks"}`，错误调整不维护kernel的K>T约束。
3. 继续执行原生Heuristics→Autotuner.run/_bench→配置调整/异常过滤/最终调用的控制流。仅将benchmark回调替为一次编译、JIT launch替为相同原生JIT的ASTSource编译，GPU不可见并禁止runtime driver访问。六原候选的调整副本合并为三组num_warps=8/4/2，三组编译均触发 `tl.static_assert(BLOCK_SIZE_K > BLOCK_SIZE_T)`；bench会把CompileTimeAssertionFailure变为无穷代价，但最终仍选中非法K1，最终编译在bench异常过滤之外再次抛错。因此捕获坏候选并不能救回原生路径。
4. 用完全相同输入和原生JIT直接固定K128/T16/4warps/2stages编译，成功生成PPU二进制。没有执行二进制；未初始化CUDA、未运行kernel、没有测量耗时。

这证明当前默认AABS路径存在确定的编译阻塞，并证明现有绕过避开了它。**不证明K128是唯一或最快配置，也不证明当前adapter-001已通过设备数值/graph/模型回归。** 原生kernel仍由vLLM维护；保留必要的窄范围Plugin launch兼容，不全局关闭AABS，不修改编译器或添加新平台分支。

## 保留与后续删除条件

现有 `_PrefillIndexTopK` 和 GQA `_PrefillHeadTile` 均逐字未变；Plugin tree `e905573a1382492b3c1dfc16ee8113d4610980cc30be031c158c54898571f1f5`，三库完整文件指纹与adapter-001冻结版本一致。以后只有当前编译器原生AABS保留K>T等约束、冷autotune编译先通过，并在空闲设备上完成原生同shape数值、graph及模型回归后，才可去掉该top-k兼容。8–15卡仍有其他服务占用，未争抢资源；当前新容器未启动模型服务，旧8035健康。

原生证据根 `/mnt/nfs/users/jinghao/minimaxM3.1/optimize/20261020-minimax-m31-latest-stack-migration/profiles/compat-001-20261020-01`：`result.json`保留六原始配置编译结果；`audit-v2.json`记录binder及编译器文件SHA；`aabs/adjustment.json`与`aabs/dependency-map.json`记录真实调整；`native-autotune-v4/result.json`、`native-traceback.log`记录最终失败和固定JIT成功对照；`review.json`汇总，SHA `77b188167689e126d3f8f80511188c0b1e373dab586e68e52b4efb040566a60d`。各证据与执行命令SHA见 [state.yml](state.yml)。初版binder严格比较空attribute键，以及初版native控制证明对原配置/深拷贝配置/去重条目数量的断言过严，已修正诊断断言；初始日志保留，不冒充模型或设备数值失败。

当前监控仍PAUSED，pr_readiness=experimental；没有新正式精度分数、gate或端到端收益。

## 当前权重配置复核

进一步只读核对独立入口所用Flash1019权重config，topk=16、init_blocks=0、local_blocks=1（源config SHA `4e2af0481fe5bbd009b1ed9a43c2a83ca59d17ad3249245f433a8a7520ad1ff2`）。依赖分析误把init_blocks作为BLOCK_SIZE_K的尺寸约束，next_power_of_2(0)=1。已按这三个真实配置值重新运行同一原生autotune控制流的编译对照，最终仍触发K>T断言；同输入固定K128/T16仍编译通过。此项仍为离线编译，无GPU执行。原先最小复现local_blocks=0证据独立保留。最终汇总 `/mnt/nfs/users/jinghao/minimaxM3.1/optimize/20261020-minimax-m31-latest-stack-migration/profiles/compat-001-20261020-01/review-model-verified.json`，SHA `67494f5e1d62c5efb79ee96c53080580e3853421b866f28afe59dd7ec926e34c`，native证据为 `native-autotune-model/result.json`及其trace，完整引用写入state。

后续[env-002](env-002.md)已将最新容器升级为FlagTree0.7.0+ppu3.6；同配置新缓存复现仍失败，固定K128编译通过。当前安装及最新缺陷验证以env-002为准，本文0.6.2a1证据保持历史原样。
