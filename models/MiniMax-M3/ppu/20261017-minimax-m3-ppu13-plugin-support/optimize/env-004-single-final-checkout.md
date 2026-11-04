# env-004：容器内只保留一套最终源码

用户要求整理当前minimaxM3容器内Plugin与FlagGems-vllm，只保留各一份最终版本；允许据此收敛源码目录和editable安装，仍不影响8011、不运行设备验证或模型服务。

## 冻结选择与操作计划

PPU-13/minimaxM3/fad201d7b6ec，两个bind mount仍为/mnt和/data；/workspace及site-packages均属容器私有层。
当前6份Plugin与3份FGV均只在/workspace，目标容器没有模型/pytest/pip进程使用它们。8011属于另一容器且health200。
选择上一轮CPU600通过的`vllm-plugin-FL.m3-router-oai-20261018`（43e0980+fw017/018/019未提交diff）和FGV46387d7+原packed SwiGLU。
统一真实目录为`/workspace/vllm-plugin-FL`与`/workspace/FlagGems-vllm`，不使用符号链接；FGV版本仍0.3.0.dev1。

先对明确列出的9个目录完整tar归档（含.git/dirty/untracked），执行tar compare和SHA校验后再移动旧canonical目录并rename最终候选。
使用离线、无依赖变更、无build隔离的editable安装更新路径，不改源代码、不升级其他依赖。
验证find_spec/direct_url和生产文件hash，再按canonical路径重跑原600项CPU/static/mock。
全部通过后才移除备份已验证的七份旧源码（含暂存的原canonical目录）；不使用广泛glob或删除/workspace根。

## 回退与验收边界

完整归档及精确恢复说明保存在`/mnt/nfs/users/jinghao/minimaxM3/20261017-minimax-m3-ppu13-plugin-support/consolidate-001-20261018`。
若路径整理或安装失败，保留现场并按归档恢复，不启动模型或处理8011。新回退入口替代旧实验中依赖已移走checkout路径的脚本；旧脚本只作历史证据，不再直接运行。
本项不修改thead.yaml、vLLM、权重、FlagGems源码，不提交/推送；PPU/graph/模型精度与性能仍未测，旧90.40% gate仅历史组合。

状态：completed_single_final_checkout_installed_CPU600_passed。首次连接预检在沙箱内因Ansible本机RPC超时失败，提升到正常本机权限后同Host预检通过；无关闭SSH校验或扩大连接范围。

归档已完整生成并通过tar compare，SHA256 `ca8575dbcf4dd5e4746d6cb31ba6534d391302a2122e39e3c1b4ff30dea7412b`。
两套源码已原地rename到canonical路径，离线editable安装成功。Plugin包版本现为`0.0.0+g43e0980de.d20261018`，HEAD43e0980+原fw017/018/019未提交变更；FGV仍`0.3.0.dev1`/46387d7+原packed SwiGLU。
direct_url与find_spec均指向canonical路径，保留源码逐文件SHA相同（安装自动生成的`vllm_fl/_version.py`元数据除外）。最终路径下CPU/static/mock重跑600项全部通过，失败/错误/跳过0，14.76秒；每项前后无GPU初始化断言通过。

## 最终结果与恢复

完整归档验证、安装和CPU回归通过后，七份旧副本已按精确路径移除；/workspace现仅各1份最终Plugin/FGV，Python安装元数据也各1份。未修改其他依赖、启动脚本、thead.yaml或算子代码，未提交/推送。
8011的原生API PID/start_ticks在本次整理前后相同，health200；目标minimaxM3没有运行模型，本项未做PPU/graph/模型验证。
旧脚本引用的dated目录已不存在，回退改用本次完整归档和RESTORE.md；归档保存全部9份原始目录，可恢复旧健康组合或最新CPU组合，不能直接执行旧路径的rollback脚本。

以下相对本次远端run目录：

- `checks/consolidation-result.json`：最终状态、版本、600项结果、归档SHA和无模型验证边界。
- `checks/sources-after.json` SHA256 `c1746c0ed981152be110eaa1b6b25b163e03de3ad7130f3c10cd0d72aa34d70b`；保留源码语义未变。
- `checks/cpu-final.xml` SHA256 `ec75dae6a91dcc1c422766335fc499a4f8492f0d3b5e1ac68c06e446870aad4e`；`logs/cpu-final.log`记录原生pytest输出。
- `checks/backup-verified.json`记录tar compare通过和归档SHA；`checks/sources-before.json`含全部历史revision/dirty/untracked摘要和源码hash。
- `checks/removed-old-paths.json`列明七个精确移除目标；`checks/service-before.json`/`service-final.json`保存8011实例一致证据。
- `commands/manage.py` SHA256 `25770cb9c42dd43e321b66e23cb349764d1679ae7777bd68cc792d49d91b6c92`。
- `commands/cleanup-in-container.py` SHA256 `6304673aed4b373f56363e0661479de549487a56a8b09a5bd46c3f63083bdcc5`；仅验证后删除7个精确目录，不作用于/workspace根或其他仓库。
- `commands/run-cpu.sh` SHA256 `deddbf9cdab9e630f7891fb0ce85eb421e25de9eeb97ae921889f114de19e299`。
- `RESTORE.md` SHA256 `bcce542c2799063026d4954395abdf5c5bf50a98e9df6d0bca6ffb474ef8267b`；说明先恢复到不存在的新目录并核对hash，再调整安装，不覆盖新编辑或处理8011。

本项只完成版本管理整理。最新算子组合仍是CPU通过、PPU/graph/模型与正式精度待验证，性能未测，旧90.40% gate不适用于当前组合。
