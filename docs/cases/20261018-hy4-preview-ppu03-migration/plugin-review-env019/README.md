# env019：当前 env018 的整体 review（源码未修改）

当前容器 PPU-03 / hy4-preview 实际安装 `/workspace/vllm-plugin-FL` 仍为官方8b2033e4加env018补丁，11文件+1021/-20，完整patch SHA `90ec637b7ea554042a0e5ba87948a6377794a80677bf1edc90226ecfc240f0f9`。614文件清单、实际import、两个gems-opt clean/HEAD/逐文件摘要及服务身份重新核验。本轮没有任何安装源码、Gems、权重或服务变更，未重启、模型请求0、未开始GPQA，heartbeat仍暂停。

本次按实际调用方和kernel指针ABI检查，不以旧的单算子通过或旧服务健康作为整体通过。发现一项确认的布局缺陷、一项确认数值差异但精度影响待定的审查观察。

## R1 / P2：短上下文配置下，decode 的输出行布局会写错

位置：models/hy4/bf16_indexer.py:170（历史路径当前不可用：`/tmp/hy4-review-20261020-01/source/vllm_fl/models/hy4/bf16_indexer.py:170`；须从原 revision 或远端证据恢复），对应 `count=min(topk_tokens,max_model_len)` 与无padding时的 `topk_indices_buffer[:, :count]`。

当max_model_len=1024、index_topk=2048、两行正常单token decode且requires_padding=False时，buffer形状[2,2048]，截出的输出[2,1024]仍有stride(2048,1)。固定FGV decode内核按 `out_indices_ptr += row_id * TOPK` 写入，不接收输出stride。因此第二行实际写在第一行后1024列，第二行保持-1，第一行原本应屏蔽的尾部被污染。这是支持条件内的行地址错误，不是随机TopK并列顺序。

真实PPU复现：当前路径首次执行及2次raw graph replay均为row0有效前缀1024、尾部错误写入1024个非负值、row1有效前缀0。对照只把传入输出恢复为完整[2,2048]，同一个库函数、同一输入、同样2次replay均为两行各1024个有效索引、尾部全-1。没有改安装源码。

当前冻结的100K/2048配置中count与buffer宽度相同，不触发此条件；但现有runtime没有排除上述短上下文配置。不能把它说成当前100K模型已经错误，也不能声称该分支已普遍安全。

最小建议与原生vLLM做法对齐：保持 `count=topk_tokens`，由seq_lens控制有效范围，避免产生窄列视图。一行建议patch（历史路径当前不可用：`/tmp/hy4-review-20261020-01/proposed-layout-fix.patch`；须从原 revision 或远端证据恢复）仅生成并通过git apply --check，**未应用/未部署**。若要支持更宽的外部stride输入，也可在backend要求连续输出，但那会增加拷贝或契约分支；当前无需扩展为新adapter文件。

## R2 / 数值审查观察：prefill 和 decode 的中间精度会改变 TopK

位置：models/hy4/bf16_indexer.py:53（历史路径当前不可用：`/tmp/hy4-review-20261020-01/source/vllm_fl/models/hy4/bf16_indexer.py:53`；须从原 revision 或远端证据恢复）。prefill的BF16 matmul输出、加权乘法、sum输出均经过BF16舍入，最后`.float()`不能恢复丢失的信息。FG的BF16 paged-MQA在FP32中累加/加权。两者输入均为BF16，这与是否支持FP8无关。

构造4097个key、TopK2048、32heads/D128：2047个明显高分key，加两个边界key。Q前两维为[1,1/128]，边界K之间多一个1/128分量，weight=1/64。prefill两分数均为0.015625，decode对应为0.015625与0.015625953674316406。把微小增量放在index2048时，实际prefill选2047，decode选2048。使用**同一个FGV prefill TopK**处理decode FP32 logits，也选2048，排除了只由两套TopK tie-break算法不同导致的解释。

结论仅为confirmed rounding/selection divergence；**不是已经证明的87%精度失败，也不凭一次临界样例强行规定prefill/decode必须bitwise一致**。已有BF16 prefill实现有意保留BF16运算顺序，不能无依据把它全部改成FP32。建议先明确Indexer的数值参考/允许差异，再决定是否统一累加精度，最后仍按原198题/87%正式契约验证。此次不提供或部署数值改写，也不引入新的正式精度门槛。

## 其余11文件整体审查结论

| 文件（vllm_fl/） | 当前审查结论 |
|---|---|
| models/hy4/bf16_indexer.py | 上述R1与R2集中在这里；metadata/paged read/pack/unpack/opaque边界未发现新的已证实错误，不能据此宣称新模型级回归通过。 |
| dispatch/backends/flaggems/impl/bf16_indexer.py | FG BF16 logits + FGV TopK来源符合用户要求；H/D/block/单token/type等保护存在，但输出行连续性契约没有覆盖R1。宜优先修caller，不扩展新共享ABI。 |
| dispatch/backends/flaggems/impl/mla_ops.py | 两个共享TopK已恢复原8参FGV函数；未重现上一轮ABI问题。FGV开关、缺失BF16 logits使用FG、三类必要适配仍清楚。保留，不再机械压缩为更复杂的条件表达式。 |
| dispatch/backends/flaggems/impl/bf16_mla.py | Q/sink头数补齐与输出裁回属于固定FGV接口要求；未发现可直接删除且不改变作用域的部分。其他shape/平台未扩展实测。 |
| models/hy4/bf16_sparse.py | 复用原metadata及sink，只替换当前缺原生实现的cache/concat/sparse调用；没有把FGV实现放进vendor。未发现本轮应额外合并的证据。 |
| models/hy4/attention.py | BF16 factory/prepare/backend hook仍只由PPU计划触发，非PPU默认路径保持；本轮不再改dtype策略。dense+sinks等非目标配置不扩大支持，也没有实测。 |
| models/hy4/runtime.py | PPU无原生FP8的选择边界、H/D/block/dtype约束保留；当前100K路径与R1短配置边界须区分。prefill实例/worker全局替换仍为官方现有架构，本轮未扩大。 |
| dispatch/backends/flaggems/impl/quantization.py | env016已验证FGV量化需最窄编译边界，当前源码字节保持，没找到可安全删除边界的新增证据。fake与调用输出2D/int8+FP32 scale契约相符。 |
| quantization/w8a8/linear.py | 原quant CachedOp→用户指定FGV triton_scaled_mm、zero-token guard保持，没再加入整层包装或GEMM dispatch。 |
| models/hy4/registration.py | lazy parser注册仍必要；未重复引入模型/loader适配。 |
| reasoning/hy_v4_reasoning.py | SHA继续匹配已证明的主线backport；实际vLLM0.24 serving/structured-output路径会传递chat_template_kwargs，未发现“只改import但收不到请求模式”的新问题。保留主线语义，不为少行重写。 |

尚未验证：新源码整模型TP16启动/capture/C8/分页/198题和其他平台。两个Gems均保持原revision和源码摘要；Plugin tests仍与官方字节相同。此次只读review没有宣布整体通过或性能收益。

## 证据与状态

远端证据根 `/workspace/.hy4-preview-migration-20261018-01/review-20261020-01`：results/review.json、probe-finished.json、identity-before.json、identity-after-probe.json、logs/review.log及commands/。seed820，PPU-ZW810E device0，allocator1%、启动空闲5659120624bytes，峰值allocator12049920bytes/reserved58720256bytes；没有改服务缓存或调度参数。R1缺陷及full-width对照各2次raw graph replay，R2为独立边界数值诊断，不冒充完整回归。

[inference-accuracy-diagnosis](../../../../skills/inference-accuracy-diagnosis/SKILL.md)用于冻结/定位：review-layout-002（confirmed address/layout defect）、review-precision-003（confirmed rounding/TopK difference，formal effect unknown）。e2e/accuracy minimal-regression仅选了算子诊断范围，整体模型incomplete_user_hold；不签发gate，原87%阈值不变。

当前完整diff（仍env018，未改变）（本地文件 `docs/cases/20261018-hy4-preview-ppu03-migration/plugin-review-env018/full-diff.md`） · [当前已安装版本的逐文件保留理由](../plugin-review-env018/README.md)
