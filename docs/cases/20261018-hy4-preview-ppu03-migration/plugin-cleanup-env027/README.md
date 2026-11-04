# env027：直接收敛安装 Plugin 的三项局部重复

已直接修改 PPU-03 / hy4-preview 实际安装 `/workspace/vllm-plugin-FL`，仅3文件 +1/−6，净减5行。两个 gems-opt 不变，没有修改 prefill 数学/精度、量化编译边界、parser、TopK 完整行宽或 padding 显式尺寸，没有重启或开始评测。

本轮完整 diff（本地文件 `docs/cases/20261018-hy4-preview-ppu03-migration/plugin-cleanup-env027/from-env025-diff.md`） · 当前安装相对官方完整 diff（本地文件 `docs/cases/20261018-hy4-preview-ppu03-migration/plugin-cleanup-env027/full-diff.md`）

| 文件 | 最小调整 |
|---|---|
| models/hy4/runtime.py | 删除PPU BF16启动中两个未用于实际执行的raw TopK独立解析；保留真实组合入口、MLA入口及其provider检查。 |
| dispatch/backends/flaggems/impl/bf16_indexer.py | 末尾copy_收进padding分支；non-padding TopK已原地写入目标buffer，不再自拷贝。 |
| models/hy4/attention.py | BF16 factory分支移除外层k_cache/max_model_len/prefix三个未读取别名；cache与配置仍由indexer_op持有，FP8分支不变。 |

策略说明：PPU BF16组合入口使用其自身dispatch和provider能力检查；单独关闭raw TopK注册项不会再误阻止独立组合入口。组合入口本身禁用、缺少FGV provider等仍通过既有检查报错。未改shared raw TopK ABI、非PPU原生路径或底层库实现。

## 检查结果与边界

- 前后614文件清单精确核验，仅上述3文件变化；三文件备份后按原mode原子替换，模型/tokenizer/vLLM/import/启动配置/服务实例及两个Gems HEAD、clean、tracked SHA均不变。tests仍官方字节，全部Python语法通过，三文件Ruff无诊断。
- CPU/mock decode对照6组：无padding、zero-row位于首/中/尾、mixed和empty。重构前后输出与cache逐元素一致、provider输入/shape/stride/调用顺序相同、返回buffer别名与未触及行保持。FG/FGV GPU kernel以CPU mock替代，不是设备验证。
- 独立CPU进程执行实际Indexer构造代码与实际vLLM DeepseekV32IndexerCache构造代码（linear及配置上下文为fixture），验证prefix static_forward_context注册、cache绑定、cache spec不变，真实nn.Module默认named_modules去重结果及fixture参数名/值不变。remove_duplicate=False遍历从两个cache别名变为一个，正是删除重复引用；没有减少或复制KV数据。
- runtime fixture验证可用时原计划不变、raw TopK独立禁用不再阻止组合入口、8类真正需要的入口缺失仍报错。该fixture不等于完整package/SDK可用性或模型运行通过。
- 服务实例未变，health200、running/waiting0；GPU未初始化/未执行，模型请求0、服务操作0、评测0。旧env022仍只覆盖启动时env021，不能当作新安装代码的graph/分页通过证据。

当前累计11个生产文件，相对官方+1053/−20。prefill三个tolist/逐行计算和R2数值口径保持，正式影响未测；完整198题/87%及heartbeat继续暂停，`pr_readiness=needs_revision`。没有性能测量或收益主张，没有提交/推送。

## 源码、证据与回退

当前源修改目标仍是容器 `/workspace/vllm-plugin-FL`；本地 `/tmp/hy4-installed-cleanup-20261020-01/files` 仅为传输/patch材料，不作为运行源码或新的离线候选。

远端 `/workspace/.hy4-preview-migration-20261018-01/installed-cleanup-20261020-01` 保存commands、补丁、614文件前后清单、原始CPU结果/stdout/stderr、部署与检查回执。部署回执SHA `03b5ac81b19ecc4af19f69df47b939c637cf631369480d2bceb06abb1b1adafe`；安装检查SHA `879d1510a6f728b35b7f0a0a3464df3db5e881ea4f3cdeb9cc32d013d7583b16`。全patch SHA `dab9c9eca5dfc26f08e7661d1f7c5900210063007452a20dd2d8e785cb2d2a95`，本轮delta SHA `69fb8f160475b2c9b38aa5419aa1215444121d9a0fc181a1b1fe0f41391570c5`。

备份 `/workspace/.hy4-preview-migration-20261018-01/installed-cleanup-20261020-01/plugin-env025-before.tar.gz`，SHA `3a07136a6ea24807ef362f167fa5666a75d094857dcb7eb5f755dc440b54ebf9`。仅在三个目标文件仍为本轮before/after SHA时可运行 `docker exec hy4-preview python -B /workspace/.hy4-preview-migration-20261018-01/installed-cleanup-20261020-01/commands/rollback.py` 恢复env025三文件，不操作服务；后续已有新改动则不能盲目回退。
