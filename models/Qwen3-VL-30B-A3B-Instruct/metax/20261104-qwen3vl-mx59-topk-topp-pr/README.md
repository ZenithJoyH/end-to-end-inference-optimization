# Qwen3-VL / mx-59 top-k/top-p PR

2026-11-09最新：[signed-zero修复已更新PR1069](optimize/fix-012-signed-zero.md)，commit `b1287f17`。保留原排序和prefix guard；258设备测试、34capture/102变输入replay、44行×双计时×5固定B/C/R通过，最大耗时增加0.547%。源qwen3vl/opt18服务、源码和配置保持原样（仍039f03ed），本轮未部署；自有测试clone已删除。远端CI已排队，未称全部通过。以下均为历史阶段记录。

2026-11-06最新：[容器已同步PR039f03ed](optimize/deploy-010-pr1069-guard.md)。mx-59/qwen3vl的top-k/top-p实现、测试和benchmark三个文件与PR逐字一致；实际Plugin调用12次capture/36次变输入replay及独立最终审计通过。其他MoE/Plugin/Gems/engine代码、模型配置和PID不变。仅磁盘代码同步，当前opt17服务未重启，不能称新guard已在运行服务中生效；下次启动加载新代码。以下为先前阶段记录。

2026-11-06最新：[shape guard已更新PR1069](optimize/op-009-shape-guard.md)，commit039f03ed，M>=32且V>=131072才预计算前缀；其他小shape和k-only保留原路径。134单测、48位级对照、额外24次变输入graph与44项受控性能对照通过。B32/B64大词表普通调用约快2.3%–3.9%，小shape变化不超过1.02%。额外原生参考检查有两项既有B64/V4096缺口，已保留失败并在PR披露；不称全场景参考性能达标。用户opt17服务/容器配置未改，私有GPU3容器已恢复并停止。

2026-11-06：[review统计前缀实测](optimize/op-008-threshold-prefix.md)已完成，B64/V151936与262144/BF16-grid完整接口延迟约降低4.08%与4.52%；小shape及部分B8普通调用存在回退，未采用统一替换。36形状的三种计时方法、91单测、42位级对照和额外18次变化输入graph回放通过。当前qwen3vl opt17/8030原服务保持运行、源码与配置不变；私有GPU6候选已恢复并停止，PR未更新。以下为此前交付历史。

2026-11-04：[PR #1069](https://github.com/flagos-ai/FlagGems-vllm/pull/1069) head `ce0fedd` 已同步到mx-59的 `qwen3vl`。单行整数key tile-sort/merge实现与PR精确一致，保持softmax/cumsum/mask与M>1原路径；容器保留原bad340d6基础，采用限文件补丁，没有整体切换仓库。

最新 [MoE 修复与同步](optimize/fix-007-int8-large-stride.md)：通用MoE大stride非法访问已定位到当前编译路径的链式指针加法，改为先归并64位元素偏移再加基址。已同步main208ab通用MoE加这份修复，MetaX文件保持精确主线；PR1069和其他推理配置保持。原主线48项加新增14项、42次变化输入graph回放，以及实际MetaX/PR1069护栏通过。前轮[局部同步](optimize/sync-006-moe-main.md)的失败与回滚记录保留，独立最终审计通过。

单batch三轮中位延迟：V4096约0.57–0.59→0.12ms，V151936约0.64–0.65→0.28ms，比原PR快2.27–4.94x；全部8个测项高于0.9x Torch参考线。91项设备测试、18次变化输入graph replay、20组对原PR的位级对照通过。无新模型/E2E结论。

部署后的qwen3vl实际安装路径上，91项组件测试、20组同步前后逐位对照、18次算子及18次实际Plugin变化输入graph replay通过。调用方保持 `top_k_top_p(logits, p=p, k=k)`，输入/RNG、fallback和幂等均验证。

其他运行配置、依赖及Plugin源码保持。原start-model.sh已包含 `VLLM_FL_USE_FLAGGEMS_VLLM=1`，脚本未改；裸进程默认开关不变。当前没有运行模型，本轮未启动/重启模型，不构成模型graph、全量精度或新性能验收。

[容器部署](optimize/deploy-004-container-sync.md) · [单行优化](optimize/op-002-single-batch-sort.md) · [接口整理历史](optimize/pr-001-topk-topp.md) · [环境](baseline/README.md) · [交付边界](acceptance/README.md)

CI导出顺序修复commit `ce0fedd`：rule-check及basic ci均通过，原数值/性能优化不变；[修复记录](optimize/ci-003-export-order.md)。
