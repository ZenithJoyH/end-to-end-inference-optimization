# env021：padding graph capture 最小修复

已部署 PPU-03 / hy4-preview 实际安装 `/workspace/vllm-plugin-FL`。相对env020仅修改 `vllm_fl/models/hy4/bf16_indexer.py`，+9/-4行：删除原vLLM helper导入，在padding分支lazy导入固定FGV的pack/unpack，分别传入 `max_length=1` 和 `total_tokens=metadata.num_decode_tokens`。未新增kernel、包装层、dispatch、测试或配置。

## 原因与必要性

真实PPU中当前env020完整入口在vLLM `pack_seq_triton` 的 `lengths.max().item()` 处capture失败。只在独立进程把pack改为带固定max_length的FGV版本，继续执行会在原vLLM `unpack_seq_triton` 的 `lengths.sum().item()` 处失败。两处都是GPU长度向CPU读回，用于决定输出形状；不能仅替换pack。

固定FGV gems-opt已支持显式尺寸，无需升级或修改Gems。当前BF16 runtime明确拒绝speculative_config、backend只支持next_n=1，故pack最大decode长度已知为1；num_decode_tokens由原metadata builder提供，原CPU query_start_loc和对应GPU decode_lens定义相同的decode token总数。显式传入二者，GPU lengths仍在kernel中用于真实packing，不冻结0-token请求位置或长度值。复用现有模型布局编排边界，nonpadding、cache/TopK/provider、R1完整行宽及R2计算口径不变；不修改vLLM helper或metadata builder。

两个gems-opt前后HEAD、clean和tracked-file摘要一致：FGV `46387d7f96050204c1b932f35680a3ea03896fa6`，FG `3ba1d1d99010de56d12088992f8b0da3444d90ca`。FGV真实函数来源：`flaggems_vllm.ops.pack_seq` / `flaggems_vllm.ops.unpack_seq`。

## 验证与边界

使用本地inference-accuracy-diagnosis及e2e/accuracy minimal-regression算子范围；fixture仅提供forward_context和真实vLLM metadata类型，实际opaque HY4 Indexer、cache、paged logits、TopK、pack/unpack均执行。seed821/device0、allocator1%、启动空闲5659120624bytes。

| 范围 | 结果 |
|---|---|
| 旧env020完整padding入口 | 稳定复现pack max.item capture失败。 |
| 独立pack-only控制 | 稳定复现原unpack sum.item capture失败。未修改安装源码。 |
| 候选64/1024/2048/100K，padding与nonpadding | 8例数值、capture及各2次改变物理页/峰值的replay通过。padding的0-token请求在capture后从中间移到首位/末位，排除缓存旧packing位置。 |
| 候选100K，8活跃+1个0-token请求 | 完整入口数值、capture及2replay通过；这是算子batch覆盖，未冒充服务C8。 |
| BF16 Q / FP32 weights / INT32 indices packing oracle | 3种dtype逐元素CPU oracle通过；各capture/2replay，零行位置与payload均改变。 |
| 安装后fresh process，1024 padding | 实际安装路径/SHA正确，完整入口数值/capture/2replay通过。 |
| 工程与身份 | 614文件精确比较，仅本文件变化；两基线strict apply/Python语法通过，Plugin tests仍官方字节；Gems/旧服务实例/模型配置不变，health200。 |

`review-padding-capture-004` 在当前单tokenBF16算子范围已修复，未扩展多token/speculative支持。整模型TP16启动、服务C8、分页请求及198题GPQA仍未运行；原service07仍运行env011内存代码，未重启/请求模型，heartbeat仍暂停，无新87% gate。R2数值观察未改，正式精度影响未知；其他平台未实测。`pr_readiness=needs_revision`，新服务和正式精度仍是缺口。没有性能测量、收益主张或提交/推送。Ruff与env020对照无新增诊断，保留原有I001导入排序告警，不为格式化扩大补丁。

## Diff与回退

完整相对官方diff（本地文件 `docs/cases/20261018-hy4-preview-ppu03-migration/plugin-review-env021/full-diff.md`）。官方HEAD `8b2033e417a535a828a1d7594d36bd33e36e3b57`，累计11生产文件+1026/-20。此次单文件delta `/workspace/.hy4-preview-migration-20261018-01/padding-fix-20261020-01/from-env020.patch`，SHA `b29c050adccf4868b77c235cff6e1c511440e03cc1c0acb724f6e3f4af851599`；完整patch `/workspace/.hy4-preview-migration-20261018-01/padding-fix-20261020-01/full.patch`，SHA `e66c0b38c3f70d7135b2cb7bd8a5194455f0ae42e665016ea50c4f7d4ad14310`。

证据根 `/workspace/.hy4-preview-migration-20261018-01/padding-fix-20261020-01` 包含commands、baseline/pack_only/candidate/installed原始结果与日志、前后identity、614文件manifest和部署回执。只备份本次单文件 `/workspace/.hy4-preview-migration-20261018-01/padding-fix-20261020-01/plugin-env020-before.tar.gz`，SHA `1db8217faec7645a3bc08aaeda986e509468ea59bb45e72f23eaf35261b72ba8`；回退 `docker exec hy4-preview python -B /workspace/.hy4-preview-migration-20261018-01/padding-fix-20261020-01/commands/rollback.py`，检查after-SHA和backup-SHA后恢复env020单文件，不动作服务。本地原始产物 `/tmp/hy4-padding-fix-20261020-01`。
