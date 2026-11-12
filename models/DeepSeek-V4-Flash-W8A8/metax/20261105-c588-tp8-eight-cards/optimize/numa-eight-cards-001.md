# numa-eight-cards-001：TP8 分布到 8 张物理卡并逐 worker 绑定 NUMA

- 分类 framework，状态 delivered_for_manual_retest；范围为用户指定启动脚本配置交付，不运行模型测试。
- 用户要求将 `/data/jinghao/deepseek/start-model.sh` 调整为 TP8 使用 8 张卡，并绑定对应 NUMA。
- Host mxC588-5；源容器 deepseekV4-flash；远程工作根沿用已授权 `/data/jinghao/deepseek`。
- 独立产物目录：`/data/jinghao/deepseek/numa-bind-8cards-20261105-01`。
- 原脚本 SHA256 `d11d5148f7a33c30fe42ebfebe1954159f9d68ad0741ebcb681917a9baf77e39`，即上一轮 4 模组/8 die NUMA 版本；新拓扑独立建案，不沿用原拓扑性能结果。

## 优化方向与配置

每张物理卡选 die0：CUDA_VISIBLE_DEVICES 和 MACA_VISIBLE_DEVICES 均改为 `0,2,4,6,8,10,12,14`；TP 保持 8；native vLLM `--numa-bind-nodes` 改为 `3 0 0 2 7 4 4 6`。EngineCore 的 CPU/内存绑定为节点 0/2/3/4/6/7 并集。模型、端口、KV、graph、batch、显存比例等参数保持。私有 numactl 工具从上一轮已校验工具复制到本轮独立目录，不修改系统安装或 LD_LIBRARY_PATH。

| rank | 物理卡 | 逻辑 die | PCI BDF | NUMA | CPUs |
|---|---|---|---|---|---|
| 0 | 0 | 0 | 0000:03:00.0 | 3 | 42–55 |
| 1 | 1 | 2 | 0000:24:00.0 | 0 | 0–13 |
| 2 | 2 | 4 | 0000:29:00.0 | 0 | 0–13 |
| 3 | 3 | 6 | 0000:54:00.0 | 2 | 28–41 |
| 4 | 4 | 8 | 0000:73:00.0 | 7 | 98–111 |
| 5 | 5 | 10 | 0000:94:00.0 | 4 | 56–69 |
| 6 | 6 | 12 | 0000:99:00.0 | 4 | 56–69 |
| 7 | 7 | 14 | 0000:e6:00.0 | 6 | 84–97 |

## 正确性与路径验证

映射已由 MetaX runtime mcDeviceGetPCIBusId 的 16 逻辑设备枚举与 sysfs numa_node/local_cpulist 交叉核对。枚举未调用显存分配或 kernel。替换前已检查 bash 语法、新可见设备下 runtime 枚举、native vLLM NUMA 参数生成、CPU affinity/MPOL_BIND、原生包装器、完整 argv 和允许变动以外环境保持，均通过。只做 CPU 子进程与设备元数据检查，不启动新模型或发送请求。

## 性能效果与决定

当前 Prefill/Decode/Mixed 和正式四场景均未测，无 baseline/candidate/revert 比例。实验只交付配置，不证明收益。8 die 数量不变，物理模块由 4 增为 8，不能把结果单独归因于 NUMA，需与上一轮拓扑分开记录。

## 风险、回退与外部证据

预检时物理卡 0/1/2 的两个 die 均有其他 vLLM 占用；现有 DeepSeek 在物理卡 4–7 上运行，且有用户 benchmark 正在进行。本次只编辑后续启动脚本，不停止或重启这些服务。新拓扑实际启动前需释放选中 die 的显存并处理同卡其他 die 的资源竞争。

替换前独立保存 `start-model.original.sh`，指向本轮之前的 4 模组 NUMA 版本；回退仅恢复脚本，不触碰现有服务。精确命令、私有工具与 SHA、验证回执保存在远程本轮目录，记录于 state.yml。

## 交付结果

- 完成时间（UTC）：`2026-11-05T11:24:24.709031+00:00`；原子替换、mode 0644、owner 0:0 保持。
- 新脚本 SHA256：`3f47d744397ccab0ab9d664a29f233a3ee7f41d4169c4a2dd91aec6541e31b6d`。
- 新可见列表在当前运行时确实枚举为 8 个不同的物理卡 BDF；未调用设备显存分配和 kernel。
- 8 worker 策略与 EngineCore 并集均已由 CPU 子进程读取 affinity、MPOL_BIND mode 和 mask 验证，原生 vLLM numa_wrapper.sh 执行通过，子进程 LD_LIBRARY_PATH 不变。
- 原服务进程身份和 affinity 前后相同；服务与用户 benchmark 未停止或重启。
- 备份：`/data/jinghao/deepseek/numa-bind-8cards-20261105-01/start-model.original.sh`（上一轮 4 模组/8 die 版本）。
- 回退：`python3 /data/jinghao/deepseek/numa-bind-8cards-20261105-01/commands/restore-original.py`，带 SHA 防护，不重启服务。
- 精确命令：`/data/jinghao/deepseek/numa-bind-8cards-20261105-01/commands/apply-eight-cards.py`，SHA256 `3e02e91e05584427d88ee7964362d39c3494693fd416731139484ecd6598542b`。
- 原始回执：`/data/jinghao/deepseek/numa-bind-8cards-20261105-01/manifest.json`，短期进程身份仅保存在外部。
- 决定 incomplete，仅配置交付完成；实际模型启动、graph、精度和端到端性能待用户执行。
