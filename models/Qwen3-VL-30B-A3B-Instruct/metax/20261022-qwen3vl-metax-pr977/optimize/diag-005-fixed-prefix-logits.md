# diag-005 固定token前缀下的C1/C8首次数值分歧

**已将独立环境按PR943 `a1570df` 更新，并把首个数值分歧定位到首层 MACA `flash_attn_with_kvcache` 的默认 `num_splits=0` 自动路径。** 模型服务的其他配置保持原值，没有把固定split控制写入服务；临时激活探针和入队屏障已移除。原GPQA123/198失败仍保留，本轮没有新分数、gate或端到端性能。

Issue `diag-acc003-gpqa`，范围diagnostic / minimal-regression。算子边界为`reproduced`；它对原完整GPQA评分失败的全部贡献尚未证实，不能宣称问题已修复。

## 版本更新与保留范围

冻结[PR #943](https://github.com/flagos-ai/FlagGems-vllm/pull/943) head `a1570dfb367d186f9b07b7173e3b362c19dd5b8d`。目标是mx-59独立容器`qwen3vl-pr977-20261022`实际导入的`/workspace/FlagGems-vllm-pr943-runtime/src`，不是9999生产副本。

- 实际MoE由SHA `749e81cfdbb4032aaa23648c53f32e3486d1e93c5aa03e41f2cb59d27f77b9e9`更新为PR字节一致的`bbc2eddedc93a608a899653c5acca0b1cb4f5293436a5d6136a06401ce50e462`；测试文件原本已与PR一致。运行副本git base仍是bad340d，不能只用HEAD代表实际代码；四个原采样兼容覆盖不变。
- 更新前后源码逐文件核验，仅package中的`runtime/backend/_metax/ops/fused_moe.py`改变。gems-opt c3c5f5ab、Plugin08da21cb、vLLMee0da84a、权重/tokenizer、sampling、黑名单、safe启动env和argv均未改变。
- BF16 E128/H2048/I384/topk8，M1/7/8/32/64/65/256/512/1024/4096/8192的更新前后输出全部逐位一致，版本内重复一致；6次capture/12次replay通过。最新正常TP2服务也通过双worker命中、capture/至少16次replay及smoke/C8。这里没有声称当前helper版本已重跑此前63项GPU或FP16全部验证。

备份在远端`configs/before-fused_moe.py`；回退只需恢复本文件并按冻结recovery配置重启独立18977。此次未执行回退，保留用户要求的PR更新，未提交/推送或修改公开PR。

## 固定前缀与真实batch控制

使用已冻结原生GPQA样本doc0的chat模板token IDs和固定参考续写；逐前缀扫描预声明0..64。本次在**step0，即生成首token之前**已发现差异，因此无需继续扫描后续生成分支。

输入前缀233token，最后position232，prefix cache开启且目标已缓存224token，实际query尾块9token；C1/C8的token、位置、缓存前缀和query长度均相同。temperature0.7/top_p0.8/top_k20/APIseed1234不变。原始seed审计和四轮完整GPQA见[diag-004](diag-004-gpqa-controlled.md)。本轮单token请求只用于固定前缀数值定位，不是缩预算的精度分数。

提交8个请求或`n=8`并不保证实际batch8；初始请求被拆成1+7等，严格校验拒绝将它们当作C8。临时observer仅对本轮诊断cohort使用既有空SchedulerOutput等待8请求入队（最长15s，实际约毫秒），原token budget8192不变。随后真实C1=1、C8=8逐次验证，全部重复保留。该入队屏障未进入最终服务。

关键调用链：

`首层Q/K/V → Plugin MacaFlashAttentionImpl.forward → flash_attn.flash_attn_interface.flash_attn_with_kvcache → MACA native kernel`。

MetaX builder的`reorder_batch_threshold=128`把≤128 query的小Prefill送入decode通道。当前cache命中后只剩9query，实际是kvcache接口，不是varlen。实际捕获caller为`language_model.model.layers.0.self_attn.attn`，Python接口SHA `a0ce682debda2e3b0457d3716e3c4bdc905d7d759238800494a5619f5a1d37c6`。这不是FlagGems-vllm内部Attention或新MoE首次造成差异的证据。

## 完整输入与首个算子输出

窄观测放在既有opaque Attention边界，原native调用完成后读取数据，没有往模型编译图插入快照算子。先用同实例“关闭观测→开启→关闭”核验：C1和C8全部logits/hidden逐元素一致，排除了探针读取造成结果变化。

目标请求完整9query的Q（18432元素），以及233位置的K/V（各59648元素）在双rank上均逐元素相同，涵盖全部224缓存位置和9个当前位置；不是只比较最后一个query。scale、causal、window、softcap等参数一致。随后native Attention输出才不同：

| 指标 | rank0 | rank1 |
|---|---:|---:|
| 目标末query Attention不同元素 | 300/2048 | 325/2048 |
| Attention最大绝对差 | 0.0001220703125 | 0.000030517578125 |
| C1/C8各自距FP64参考最大绝对差 | 0.0000699968 | 0.0001186675 |
| 最终logits不同元素 | 141268/151936 | 141268/151936 |
| 最终logits最大绝对差 | 0.3125 | 0.3125 |

因此，首个已隔离的batch数值分歧位于首层native kvcache Attention内部；它产生的小差异可在后续模型计算中放大。FP64误差只作为数值观察，不能据此将浮点路径差异直接称为kernel语义错误，也不能替代正式GPQA门槛。

## 忠实重放与自动路径控制

在空闲GPU2使用完全相同API、实测Q、物理KV大小/stride/页号及参数做独立重放。最终v4重建按CPU物理storage传输并恢复原stride，逐元素核验输入与batch复制。**双rank的实际C1输出18432元素、C8输出147456元素均与服务抓包逐位相同**，才接受后续机制对照。

以相同完整输入复制成1/8序列，A1→B8→A1只改变batch：默认自动路径再次产生差异，回到C1则恢复原输出；所有8个相同序列内部输出一致。在独立组件中指定`num_splits=1`后，C1/C8输出全部逐位相同；固定2/4也得到batch一致结果。默认/固定1下两种batch、两rank共8次capture/16次replay，均与未capture结果一致，故graph不是这个算子差异的必要条件。

这把机制收敛到**native kvcache默认自动配置的batch相关数值路径**。默认结果没有与已测显式1/2/4完整匹配，不能据输出相似度推断内部自动实际split数或具体kernel选择。固定split只是组件控制变量，**没有应用到模型服务**；是否适合作为模型级修复及其性能代价尚未评测。

## 恢复、证据和未完成项

18977已恢复正常配置，最终实例`qwen3vl-pr977-20261022:561559:561993825`；FIXED_PREFIX系列环境均关闭，临时调度/激活挂钩不再加载，prefix cache仍开启，双worker最新MoE实际命中与graph/C8通过。9999原生产服务未改。正式验收仍保留acc-003的GPQA123/198低于64和ERQA164/400达到40，没有用诊断重跑替换失败或签发新gate。

远端根目录`/public-flash/jinghao/qwen3-VL/20261022-qwen3vl-fixed-prefix-logits`，完整Q/K/V、缓存页、源码/配置、脚本及原始响应只保存在远端；结构化状态保存必要SHA。最终回执`results/diag-005-completed.json`，SHA `a803d37ed4ff6bfe2393bbb3b3a77cdda452753605f0d7f2323cdcf47405fc5f`。核心证据：

- `manifests/pr-update.json`、`source-before.json`、`source-final.json`及`environment-gates.json`。
- `results/operator-replay-summary.json`：最新MoE更新前后/graph。
- `attention-v2/results/attention-analysis.json`：同实例探针中性、完整输入一致、首层native输出差。
- `attention-v2/results/native-attention-replay-v4.json`：与真实抓取逐位匹配、batch A/B/A、固定split及graph。
- `attention-v2/snapshots/`：首层实际接口Q/cache/output，真实调用层名、页映射及参数。
- `final/results/service-minimal-raw.json`及`final/graph/`：清除临时探针后的正常服务回归。

控制失败均保留且不作为算子根因证据：挂载列表排序已规范化；tokenizer BatchEncoding在线请求前改为token list；首版异步调度屏障漏转发bool参数导致smoke失败，修正完整签名后通过；全层RoPE模块hook被48层共享实例覆盖，且跨重启C1不相同，故不作为首处归因/探针中性证明；原varlen-only捕获未命中实际kvcache；首版重放KV恢复字节不一致、随后V-cache设备传输stride不保留，均拒绝，最终物理storage重建才通过真实输出匹配。没有因此修改生产算子、关闭FlagGems或放宽比较。

监控`qwen3-vl-gpqa-erqa`已暂停，回执PAUSED。下一步若要修复，需要单独评估native自动路径的batch不变性方案，完成模型/graph回归及原正式全量精度；本次只完成版本更新和具体算子定位。

知识差量`refined`：先核验缓存后真实query长度及native接口，再做完整Q/K/V与KV页对照；同seed的动态batch漂移不能直接归因新MoE/采样，最后一个token的输入相同也不能替代完整依赖比较。重放必须保留物理页storage/stride并逐位还原原输出。
