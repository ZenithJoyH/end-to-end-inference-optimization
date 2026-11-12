# op-002-single-batch-sort 单行排序开销优化

- 状态：完成，keep PR only；operator/improve；[PR #1069](https://github.com/flagos-ai/FlagGems-vllm/pull/1069) head e635daac，数值实现commit 2e157ea4。

## 优化方向与瓶颈依据

原PR675b36e的M1吞吐回退，M1/V4096耗时约0.56ms、M1/V151936约0.57–0.61ms。先冻结原路径并profiling分解，排查与batch64通用排序路径有关的多次guarded kernel发射、workspace及排序工作量。

## 优化内容与适用边界

先从mx-59/qwen3vl当前有效状态复刻专用独立容器，核验挂载和源码。首个证伪是原有FlagGems排序能力及当前设备trace；若仍存在大量发射开销，评估仅M1的整数有序key tile-sort/merge，保持原softmax、cumsum及阈值mask不变。普通Triton与TLE能力均按当前编译器实查，不升级依赖。不能增加Torch compute fallback或读取GPU参数回host。

## 正确性与路径命中

延续原PR契约、容差及语义。增加排序值位级对照、边界tile/非对齐N与原完整68项、变化输入graph。输入与RNG不变，batch8/64原路径为守护项。

## 性能效果

采用上游benchmark框架，固定k20/p0.8、两种FP32分布、M1/8/64及4096/151936目标。无profiler原始轮次全部保留；至少3轮同进程轮换B/C/R，稳态预热后中位数比较。性能目标采用上游0.9x参考线及相对原PR明确改善；不存在模型/E2E结论。

## 决定、风险与回退

保留M1专用排序，已更新PR及测量说明，Draft待review且无合并冲突。只提交实现、测试和相应文档；原qwen3vl源码及其他配置未回写，专用容器已停止，原始证据远端保留。回退PR实现可revert 2e157ea4及后续文档同步commit，不需要改生产服务。

## 外部证据

同case远端子目录op002，命令和SHA执行前归档。模型精度/正式性能Skill不适用于本次纯算子场景，不编造服务验收。

## 隔离与候选验证

- 专用容器：qwen3vl-topk-opt1069-20261104；有效状态镜像eb9b5b9f6a2a；image_lineage verified、mount_parity passed、源源码未变。GPU0独占测试，其他服务不动。
- 原版trace命令：op002/commands/profile_baseline.py 与run-baseline-profile.json；结果保留op002/profiles，profiler-on时间只用于归因。
- 候选v1：仅M1改为有序uint32 key tile-sort及stable merge；不改变后续softmax/cumsum/top-p阈值处理，M>1原路径保持。候选、原版和有限验证脚本执行前保存在op002/commands/backend-candidate-v1.py、backend-before.py、smoke-v1.py，按原版位级比较排序及三种过滤模式。

原版trace：每次33（V4096）/35（V151936）个device kernels，实际_sort阶段包含8次guarded radix sweep及对应zero等发射。Triton3.6.0实有tl.sort和TLE模块；本次瓶颈是多次排序发射，先使用实际已编译验证的整数tl.sort与向量binary-search merge，无需新TLE原语或升级依赖。既有FlagGems公开sort仍8pass并计算indices，不直接解决values-only M1发射浪费。

候选v1有限回归：20组（10个N×两分布），每组排序int32视图及k-only/p-only/combined最终输出全部对原PR逐位相同，输入不变。smoke-v1.log/results/smoke-v1.json保留。后续完整测试和三轮性能结果见下文。

三轮无profiler B/C/R+Torch（每路径20次预热，benchmark/base.Benchmark kernel、20ms/50ms、保留全部轮）：M1/V4096 BF16-grid 0.567296→0.120320ms，arbitrary 0.592896→0.120064ms；M1/V151936 BF16-grid 0.635136→0.279808ms，arbitrary 0.648448→0.279808ms。同轮相对Torch分别1.100/1.113/1.061/1.054x。B/R中位比0.987–1.003（M1），保留首轮B较慢事实，不丢轮。M8 BF16-grid 0.647680→0.659584ms（约1.8%波动），其余M8/64约持平；所有case高于0.9x参考线。不属于E2E收益。

数值烟测和benchmark候选SHA e7a2ce2dc71561d4e89fe32ade5f33f899621ce6e2555148557854ecb1f9f5bd；最终提交只整理docstring/导入格式，不改执行代码，完整pytest使用最终文件再核验。

最终测试：91 passed（含原68项、新18个bit-key排序、1个M1 dispatch、4个新增graph shape组合），共6captures/18次变化输入replay。预提交九文件所有hook通过。候选profile实际_sort_value_tiles/_merge_value_runs命中，完整filter发射数33→8（V4096）、35→16（V151936），RNG前后不变。最终backend SHA3513e43713ca0dced706dfbc8369a7291c4759e338235586dca59cd7599cb279，tests SHAea99f9209a9601a4842cf7b41fa8850a8fa5438e15e38a49c9be6f9351fe45ec。

新排序并非所有输入都降低纯device算术耗时；BF16-grid的tile/merge可比counting做更多device工作，实际收益来自减少发射及通用路径开销。只以无profiler同契约测量判断收益。固定tile4096、merge block256，无新autotune空间或依赖升级；原M>1配置保持。生产实现只做Torch allocation/clone，新增数值实现全部Triton，无Torch compute fallback、GPU值回传host、RNG或sampling变更。

## 发布与独立复核

- 实现commit `2e157ea485ccd0704f5542f782c43b83ded7be20`；文档同步head `e635daac04def3f603714928858a977a1a31ea9f`，仅API docstring/inventory调整，去docstring后的可执行AST逐项相同。发布backend SHA0f3f4eeb160032a6832e0ac214e947bb9fe435570f4de22eb1791f63d4befbb4。
- 九个PR文件均从GitHub指定head读回，与提交内容完全一致；仍9个changed files，mergeable=true。未合并PR。
- 独立audit复核91测试/18replay/20bitwise cases、全部8性能项与所有3轮、实际kernel命中和RNG不变；op002/results/final-audit.json passed。
- 当前qwen3vl三个保护文件SHA与开始时精确一致，容器仍running；只停止自有qwen3vl-topk-opt1069-20261104，无源服务stop/restart、GPU4/5或其他服务操作。未部署候选回源。
- 决定：单行回退在固定测项中已消除，停止继续调参。下一步为PR review；模型/E2E效果须另立契约，不能从组件2.27–4.94x推算。

Final audit SHA256: ac87c3243f5a68d1f43083511001d2ee957308b63d6582c3cd71dbcf85369308. Remote completion: op002/results/completed.json.
