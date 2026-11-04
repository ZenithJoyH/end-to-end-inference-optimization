# env025：直接更新容器实际安装 Plugin

已按用户要求，将 env023 的模型/后端职责整理及 env024 的 MLA 获取收敛，直接应用到 **PPU-03 / hy4-preview / `/workspace/vllm-plugin-FL`**。本任务后续源码修改以该安装目录为主；本地候选仅作快照、diff 和回退参考。没有重启服务或开始评测。

本轮实际安装四文件 diff（本地文件 `docs/cases/20261018-hy4-preview-ppu03-migration/plugin-installed-env025/from-env021-diff.md`） · 相对官方完整 diff（本地文件 `docs/cases/20261018-hy4-preview-ppu03-migration/plugin-installed-env025/full-diff.md`）

## 已安装的改动

| 文件 | 内容 |
|---|---|
| `models/hy4/bf16_indexer.py` | 保留模型 cache/metadata/chunk 编排和 opaque op，移出算子计算及 Gems 直接导入。 |
| `dispatch/backends/flaggems/impl/bf16_indexer.py` | 承接原 prefill 数学、分页 key gather、TopK 和 decode packing/unpacking，保留原精度/行宽/显式尺寸。 |
| `dispatch/backends/flaggems/impl/mla_ops.py` | 删除独立 `_get_bf16_operator`，必要适配映射进入 `get_operator`，普通算子恢复官方获取路径。 |
| `models/hy4/runtime.py` | 增加 BF16 prefill 组合入口的启动能力检查。 |

完整安装内容与已审阅 env024 逐文件一致，累计仍是官方 main `8b2033e417a535a828a1d7594d36bd33e36e3b57` 上的 11 个生产文件 +1058/−20；Plugin tests 保持官方字节。FGV gems-opt `46387d7f96050204c1b932f35680a3ea03896fa6` 和 FG gems-opt `3ba1d1d99010de56d12088992f8b0da3444d90ca` 前后 HEAD、clean 与 tracked SHA 均相同。vLLM、权重/tokenizer、启动参数与 dispatch 文件未变。

## 现场核验与边界

- fresh inspect 证明 Plugin/Gems/证据目录不在任何共享挂载下，属于本容器私有层；镜像和挂载前后未改。
- 写入前完整614文件与 env021 基线匹配，没有覆盖额外用户改动。仅四个目标文件备份并按原 mode 原子替换；其他所有源码逐字节保留。
- 写后全614文件与候选一致；全部 Python 语法检查通过、测试目录仍官方。安装前 env023 的9组 CPU/mock 数学比对及 env024 的22项 routing/mock 检查保留原证明范围，最终源码 SHA 一致，不冒充设备执行。
- 安装后 fresh process 从实际安装文件直接导入 BF16 backend，三个导出函数均指向安装路径，lazy provider 未导入，GPU 未初始化。该检查未加载完整 vLLM/平台/Gems provider 或执行模型/算子，不证明整套 package 注册或硬件兼容通过。
- 服务 PID/start_ticks 与原实例一致、health200，running/waiting 均0。本轮服务操作0、模型请求0、GPU 算子执行0、精度/性能评测0。

**磁盘安装已更新；现有服务未重启，进程内新源码激活尚未验证。** env022 的51capture/16rank两次replay/分页结果仅证明旧 env021，不能覆盖新安装。新源码启动/graph/分页与198题/87%正式精度仍待后续安排，heartbeat继续暂停。R2 数值观察未改，`pr_readiness=needs_revision`，无提交/推送或性能收益结论。

## 证据与回退

远端根 `/workspace/.hy4-preview-migration-20261018-01/installed-update-20261020-01` 保存 commands、四文件 payload、完整前后清单、原始回执、patch、评审快照及备份；本地控制根 `/tmp/hy4-installed-update-20261020-01`。完整安装回执 `/workspace/.hy4-preview-migration-20261018-01/installed-update-20261020-01/deployment-result.json`，SHA `7c420963d83d017e9d7438b7c6f142d828307b08d81a3349b84d084ee842ec7a`；安装检查 `/workspace/.hy4-preview-migration-20261018-01/installed-update-20261020-01/installed-check.json`，SHA `124eae47c0ad6d9aebc1b26cc542fff13bc3b7706ef16d8c63c5ad003a6150d2`。

四文件备份 `/workspace/.hy4-preview-migration-20261018-01/installed-update-20261020-01/plugin-env021-before.tar.gz`，SHA `6ea4731a20d683c3691ac280ad2952181aa9385a99833b1809b6d8bd4b1ff5ca`。必要回退入口 `docker exec hy4-preview python -B /workspace/.hy4-preview-migration-20261018-01/installed-update-20261020-01/commands/rollback.py`，只在目标文件仍为本次 before/after SHA 时恢复四文件，不操作服务。后续如有新改动，不可盲目运行此回退。

完整 patch SHA `fc652cb227d43425d20296d1bb37712000bbd8b667f0b44bb65fd7a4e87ab4c7`；本轮相对 env021 delta SHA `c10919c228e20fd7499804bfd0690bee6916e1cc502bfe43db72a822d6067d8d`。当前完整清单 `/workspace/.hy4-preview-migration-20261018-01/installed-update-20261020-01/current-source-manifest.json`，SHA `c57b953c4303db48e471f1797bc5f0661eb278674f102ba1c3657024764534e3`。
