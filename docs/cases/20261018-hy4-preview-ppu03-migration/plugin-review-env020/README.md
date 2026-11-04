# env020：短上下文索引行布局的一行修复

已部署到 PPU-03 / hy4-preview 实际安装的 `/workspace/vllm-plugin-FL`。相对 env018 只修改 `vllm_fl/models/hy4/bf16_indexer.py:170` 一行，其他源码字节保持一致。两个 gems-opt 的 HEAD、clean 状态及 tracked-file 摘要前后不变：FGV `46387d7f96050204c1b932f35680a3ea03896fa6`，FG `3ba1d1d99010de56d12088992f8b0da3444d90ca`。

```diff
-        count = min(topk_tokens, max_model_len)
+        count = topk_tokens
```

必要性：FGV decode TopK 以 `row_id * TOPK` 寻址，不接收输出行 stride。原来在短上下文截列后，视图的 stride 仍是原 buffer 宽度，第二行会写入第一行尾部。保留完整 TopK 宽度让传入宽度与实际行距一致，有效范围仍由 seq_lens 控制，无效索引保持 -1；无需新增连续化拷贝、包装、dispatch 或修改 Gems。当前100K/2048配置两表达式等价。

## 真实 PPU 验证

通过实际 opaque HY4 Indexer 入口、真实 cache/logits/TopK；只由独立进程 fixture 提供 forward_context 和实际 vLLM metadata 类型。seed821，device0，allocator1%，启动空闲 5659120624 bytes。不发送整模型请求。

| 范围 | 结果 |
|---|---|
| 旧版1024/B2/TopK2048无padding | 首次执行及2次graph replay均重现跨行污染：原应[65,1024]，实际有效数[1089,0]。 |
| 候选64、1024、2048、100000无padding | 4例均通过索引集合/有效个数/-1尾部检查，各capture及2次改变页表/峰值输入的replay。 |
| 候选相同4种上下文，padding含0-token请求 | 真实pack/unpack，4例各3次改变输入的eager数值检查通过；graph未通过，见下述继承限制。 |
| 部署后fresh import短1024无padding | 实际安装路径/SHA正确，数值及capture/2replay通过。 |
| 工程和身份 | 614文件精确核验、仅一行delta；完整patch对官方和delta对env018 strict apply通过；Python语法通过，Plugin tests仍为官方字节。Gems、服务实例、模型配置身份不变；health200。 |

**保留的限制**：padding路径在当前安装vLLM的 `pack_seq_triton` 中执行GPU `lengths.max().item()`，raw graph capture会报stream-capture错误。旧env018与一行候选在同条件下均复现，issue `review-padding-capture-004`，本轮不修改该独立路径，也不把eager通过写成graph通过。相应原始失败证据保留，未进行整模型启动验证。

env019 R2（BF16 prefill/FP32 decode舍入和TopK差异）未改，正式精度影响仍未测。R1仅在源码和受影响算子范围修复；不据此宣称整模型或87%精度通过。现有service07仍运行历史env011内存代码，未重启；模型请求0、GPQA未启动、heartbeat保持暂停。新服务级minimal-regression仍 `incomplete_user_hold`。

Ruff发现的I001导入排序告警在原env018与候选完全相同，未为格式化扩展本轮一行修改。没有提交/推送，`pr_readiness=needs_revision`（继承padding graph限制、R2数值参考及新服务/正式精度待验证）。

## Diff、证据与回退

当前相对官方的完整 diff（本地文件 `docs/cases/20261018-hy4-preview-ppu03-migration/plugin-review-env020/full-diff.md`）。官方HEAD `8b2033e417a535a828a1d7594d36bd33e36e3b57`，累计11文件（5新增/6修改）+1021/-20；其余10文件继续使用[env018逐文件理由](../plugin-review-env018/README.md)，此次不增加修改。

完整patch `/workspace/.hy4-preview-migration-20261018-01/layout-fix-20261020-01/full.patch`，SHA `4bb15f7e480eb4baf9234e781cf65a555a2269ce31c1254a76c6bd07692a27f5`；单行delta `/workspace/.hy4-preview-migration-20261018-01/layout-fix-20261020-01/from-env018.patch`，SHA `9d2af232f3a056d1147a8cf6ff70ecfd9b64c021ab82364876dda8890b4b643e`。614文件manifest、deployment-result、installed-finished、probe-finished、results及commands均在同一私有证据根。前两轮harness/graph失败证据未覆盖，最终结果使用v3文件。

只备份此次单文件 `/workspace/.hy4-preview-migration-20261018-01/layout-fix-20261020-01/plugin-env018-before.tar.gz`，SHA `ce416eea980da736c65de1f740cd6417f33a2509dc3ef06d7aa1ce25c142a13d`。守卫回退 `docker exec hy4-preview python -B /workspace/.hy4-preview-migration-20261018-01/layout-fix-20261020-01/commands/rollback.py`，校验当前after-SHA与backup-SHA后恢复env018单文件，无服务动作。本地原始产物 `/tmp/hy4-layout-fix-20261020-01`。
