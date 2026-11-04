# env-006 · Qwen3.6-27B 容器清理

用户明确要求：除 `qwen36-27b-regression-b-20261022` 外清理 mx-104 所有 Qwen3.6-27B 相关容器，包含原 verify。该新指令覆盖此前原 verify 保留要求。

执行已完成；只删除核验后的17个容器，不删除镜像、volume、挂载目录、模型或评测产物。4个运行目标仅空闲bash/sleep，其余13个已退出。保留 B 容器及当前9998服务，核验进程启动时间和health；无性能/精度作业启动。

命令：`/public-flash/jinghao/qwen3.6-27B/20261022-qwen36-27b-mx104-plugin-regression/commands/cleanup-qwen27-containers-20261027.py`

SHA256：`ac22174bb5b9b2d17a4f4a6e74b3cde8a7486e58782ac9c810aaf6e1d779b165`。命令语法校验通过。执行先保存精确ID清单与挂载/镜像信息，再以清单SHA显式进入apply；每次删除前核验ID/名字，运行目标拒绝非空闲进程，精确stop后rm，不使用force、-v或prune。

外部证据：`/public-flash/jinghao/qwen3.6-27B/20261022-qwen36-27b-mx104-plugin-regression/manifests/container-cleanup-20261027/`。

已审阅删除前plan：17个目标，保留B当前API/Engine/2worker启动时间相同且health200。plan SHA256 `5d006a2c42c5900da651c81a28ca41d05439e578d2c0ba0b6f255429bf4c8f18`。执行同命令加 `--apply-plan-sha256 5d006a2c42c5900da651c81a28ca41d05439e578d2c0ba0b6f255429bf4c8f18`。

## 完成结果

2026-10-27 12:18 CST：按用户最新明确要求，已删除 mx-104 其余17个 Qwen3.6-27B 相关容器（含原 verify、A clone、两个评测容器、13个已退出历史 dense 容器），仅保留 `qwen36-27b-regression-b-20261022`。保留B的API/Engine/两worker启动时间未变，9998 health200；271个无关容器身份/运行状态无变化。镜像、volume、挂载数据、模型、结果与备份均保留；性能仍暂停。

已删除4个空闲运行容器和13个已退出容器；未创建环境快照镜像，删除容器的私有writable layer随容器删除。现存原镜像、挂载中的源码/历史补丁与结果不变。

回执：`/public-flash/jinghao/qwen3.6-27B/20261022-qwen36-27b-mx104-plugin-regression/manifests/container-cleanup-20261027/receipt.json`，SHA256 `53214ab1acb73f8c0141aebcef3a4ed3a98d51c6dae25f234f021531d80b340a`；逐容器操作在同目录 `operations.jsonl`，原计划在 `plan.json`。清理前289个容器、清理后272个，全部剩余无关容器及保留B均核验未变。

后续若重新评测，CPU GPQA/ERQA评测容器需按新任务重新准备，不能再执行引用已删除容器的旧启动命令；历史正式精度产物与验收回执仍保留。
