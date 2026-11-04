# FlagTree 0.7.1.dev1+ppu3.6：issue #1407 复验

用户于2026-10-21明确要求在当前容器安装指定版本并核验issue #1407。目标仅为PPU-07的`minimaxM3.1-opt-latest-20261020`，不修改其他容器、Plugin/FV/FG源码、现有兼容补丁或模型权重。

预检确认默认FlagTree为0.7.0+ppu3.6，8045服务仍在运行。先在容器私有`/workspace/flagtree-0.7.1.dev1-ppu3.6-20261021-01`隔离安装，独立进程使用新PYTHONPATH与全新编译缓存复验。用户随后明确允许仅重启8045并切换默认安装。已完成旧安装的逐文件哈希备份、归档校验、默认无依赖安装；发行包差异仅FlagTree，Plugin/FV/FG完整源码指纹前后一致。

远端独立案例：`/mnt/nfs/users/jinghao/minimaxM3.1/optimize/20261021-minimax-m31-flagtree071-issue1407-01`。正式执行命令先归档到该案例`commands/`并记录SHA。沿用原生vLLM top-k compile-only控制流和公开最小复现，禁止设备launch；本次不启动精度或性能评测。

官方wheel：`https://resource.flagos.net/repository/flagos-pypi-hosted/packages/flagtree/0.7.1.dev1+ppu3.6/flagtree-0.7.1.dev1+ppu3.6-cp312-cp312-linux_x86_64.whl`，索引SHA256：`5b00533b90d58e67bae5ce16a3c87b2f3032a3dbeed2d4572f48b160af7e661d`。

## 实际复现结果

| 检查 | 原默认0.7.0+ppu3.6 | 新默认0.7.1.dev1+ppu3.6 |
|---|---|---|
| AABS默认开启 | 是 | 是 |
| 真实vLLM top-k依赖映射 | BLOCK_SIZE_K→init_blocks | 空映射，避免该错误配对 |
| 原生六配置及最终选择 | K缩为1，最终CompileTimeAssertionFailure | K保持2048/1024/512/256/128/64，全部编译成功 |
| 同JIT固定K128控制 | 编译成功 | 编译成功 |
| issue公开简化复现 | 历史失败 | 仍K→1并CompileTimeAssertionFailure；固定K128通过 |

隔离安装与切换后的`/usr/local/lib/python3.12/site-packages/triton`默认安装分别复验，结果一致。复现均禁止runtime driver与设备launch、独立全新编译缓存，无性能计时或模型回答。结论：**当前真实vLLM top-k编译阻塞已消失，但issue #1407的通用非正extent问题尚未完全修复**。本轮不删除Plugin原有top-k或GQA兼容。

源码对比显示，新分析器把比较表达式证据限制到对应`tl.load`的mask，因而不再从真实top-k内无关语义比较推导init_blocks约束；公开简化kernel恰好在load mask中直接使用init_blocks=0，仍触发旧问题。此结论来自实际wheel源码和编译对照，不以issue是否关闭推断修复。

## 服务与证据

只停止了重新解析并按argv/startticks绑定的8045及其8个worker和关联resource tracker，0–7设备配置保持。源8035与8–15其他工作负载未操作；全局`start-model.sh`、原first8启动文件、三库源码均未修改。新案例启动副本仅改日志和独立编译缓存路径。第一次重启的原bind预检把旧连接TIME_WAIT误判为占用；确认无监听者、复用地址bind通过后，仅在新副本补上SO_REUSEADDR并启动，原失败及修正证据均保留。

旧安装备份：远端`flagtree-0.7.0-installed-backup.tar.gz`及`backup-files.json`。默认安装回执：`default-installed-verified.json`。编译结论：`compiler-verification-result.json`；真实原生控制流：`default/native-model-repro/result.json`（SHA256 `3d09a48d954cda83457e6665a73a1ed390450f0a43f20ffa85c4d58d313e4c4f`）；公开简化复现：`default-public-probe.log`（SHA256 `a0a2eb99e437d4207f7f872d47684fbce33c62d64822acb3f147c10c6983183a`）。命令与SHA见本目录`commands/*-receipt.json`，原件在远端`commands/`。

最终状态：**新版已成为默认安装，8045服务已恢复健康HTTP200，8个worker重新绑定，PIECEWISE与FULL各7/7档graph捕获完成**。本次未验证graph replay，也没有重跑正式精度或性能；既往83.84%/94.00%/61.00%只保留为旧编译器历史分数，不作为新编译器的gate。

远端终态`result.json` SHA256：`fa69338ae38e9d84ac94ac576bec0d5d231c439d78f8e1d4e52d322078769ba6`。本地机器可读摘要见[state.yml](/Users/baai/Documents/ChatGPT/端到端推理优化/.cache/model-record-archives/20261102-record-reconciliation-01/files/models/MiniMax-M3.1-Flash-W8A8/ppu/20261021-flagtree071-issue1407/state.yml)。源容器、其他服务、原启动文件和父任务监控状态均未修改。后续若需要移除top-k兼容，仍需单独完成去补丁后的设备数值、graph replay与模型回归，不能只据本次编译成功删除。
