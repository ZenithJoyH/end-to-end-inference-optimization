# DeepSeek TP8：8 张物理卡各使用 1 个 die，并绑定对应 NUMA

- 日期：2026-11-05；SOP 0.44（2026-11-04）；验收范围 diagnostic。
- 用户要求修改 mxC588-5 上 `/data/jinghao/deepseek/start-model.sh`。原先设备 8–15 为 4 张双 die 物理卡；本轮改为逻辑设备 `0,2,4,6,8,10,12,14`，在 8 张物理卡上各使用 die0，TP 仍为 8。
- 状态：脚本配置已交付，模型精度/性能 incomplete；未停止或重启任何服务，现有 benchmark 保持运行。
- 记录：[模型案例](../../../models/DeepSeek-V4-Flash-W8A8/metax/20261105-c588-tp8-eight-cards/README.md)；[numa-eight-cards-001](../../../models/DeepSeek-V4-Flash-W8A8/metax/20261105-c588-tp8-eight-cards/optimize/numa-eight-cards-001.md)。

| TP rank | 物理卡 | 逻辑设备 | NUMA |
|---|---|---|---|
| 0 | 0 | 0 | 3 |
| 1 | 1 | 2 | 0 |
| 2 | 2 | 4 | 0 |
| 3 | 3 | 6 | 2 |
| 4 | 4 | 8 | 7 |
| 5 | 5 | 10 | 4 |
| 6 | 6 | 12 | 4 |
| 7 | 7 | 14 | 6 |

NUMA 映射由当前 mcDeviceGetPCIBusId 枚举与 sysfs 交叉核验，使用 native vLLM `--numa-bind --numa-bind-nodes 3 0 0 2 7 4 4 6`，同时约束 worker CPU 和新分配内存。EngineCore 使用节点 0/2/3/4/6/7 并集。保留模型、端口、KV、graph、batch、显存比例及其他模型参数；私有 numactl 工具复制到本轮目录，不修改系统库或子进程 LD_LIBRARY_PATH。

验证：bash 语法、允许变动以外 argv/环境保持、新可见列表的 8 个不同物理 BDF、8 worker 加 EngineCore 的 CPU affinity/MPOL_BIND、原生 numa_wrapper.sh 均通过；未调用设备显存分配或 kernel。原服务身份与 affinity 前后不变。真实模型启动、graph replay、精度与端到端性能均未执行，不能声明收益。

远程目录：`/data/jinghao/deepseek/numa-bind-8cards-20261105-01`。原脚本备份 `start-model.original.sh`，SHA256 `d11d5148f7a33c30fe42ebfebe1954159f9d68ad0741ebcb681917a9baf77e39`；新脚本 SHA256 `3f47d744397ccab0ab9d664a29f233a3ee7f41d4169c4a2dd91aec6541e31b6d`。精确执行命令与回执在 `commands/apply-eight-cards.py`、`manifest.json`，SHA 见模型 optimize/state.yml。

回退到本轮修改前的 4 卡/8 die NUMA 脚本：`python3 /data/jinghao/deepseek/numa-bind-8cards-20261105-01/commands/restore-original.py`。只恢复文件，不重启服务。

实际启动前需释放所选 die 的显存；预检时物理卡 0/1/2 仍有其他 vLLM 占用，本次未操作它们。对比时还应控制同卡另一 die 的资源竞争。物理卡数由 4 变 8，不能将后续差异单独归因为 NUMA；按独立拓扑记录，与上一轮性能分开。
