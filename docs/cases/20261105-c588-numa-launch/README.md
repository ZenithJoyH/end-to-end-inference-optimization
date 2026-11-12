# DeepSeek-V4-Flash：用户指定启动脚本的 NUMA 绑定

2026-11-05 后续更新：当前启动脚本已切换为 [TP8 跨 8 张物理卡各 1 die](../20261105-c588-tp8-eight-cards/README.md)。本页保留前一轮 4 张卡/8 die 配置的历史验证，不能代表当前文件。

- 日期：2026-11-05；SOP 0.44（2026-11-04）；验收范围 diagnostic。
- 状态：已交付配置，模型精度及性能 incomplete；证据等级 observation。
- 用户要求修改 mxC588-5 的 `/data/jinghao/deepseek/start-model.sh`，自行运行端到端复测。仅对该文件落实明确授权，不启动优化容器或模型、不修改正在运行的进程、不修改 vLLM/Plugin/系统安装。
- 模型记录：[案例入口](../../../models/DeepSeek-V4-Flash-W8A8/metax/20261105-c588-numa-launch/README.md)；[实验 numa-launch-001](../../../models/DeepSeek-V4-Flash-W8A8/metax/20261105-c588-numa-launch/optimize/numa-launch-001.md)。

## 配置与验证

当前容器 `deepseekV4-flash`，vLLM 0.24.0+empty；可见逻辑设备 8–15、TP8。运行时 PCI BDF 与 sysfs 节点重新核验，使用 native `--numa-bind --numa-bind-nodes 7 7 4 4 4 4 6 6`，worker 绑定 CPU 和内存；EngineCore 使用节点 4/6/7 并集。保留原模型、端口、KV、graph、batch、显存比例、prefix cache、日志和可见设备配置。

| TP rank | 物理逻辑设备 | NUMA | CPU 集合 |
|---|---|---|---|
| 0/1 | 8/9 | 7 | 98–111 |
| 2–5 | 10–13 | 4 | 56–69 |
| 6/7 | 14/15 | 6 | 84–97 |

容器缺少 numactl，第一次宿主机工具复制后的 CPU-only 验证因 libnuma 符号版本不匹配中止，原脚本未替换。随后将匹配库放在任务私有目录，仅通过动态加载器的 library-path 供工具使用；不改变子进程 LD_LIBRARY_PATH。bash 语法、原参数/模型环境保持、8 worker 加 EngineCore 的 CPU affinity/MPOL_BIND 实测、原生 numa_wrapper.sh 执行均通过，未初始化 GPU。

2026-11-05 18:33 完成原子替换，保留 mode 0644、owner 0:0。原服务进程身份和允许 CPU/内存节点集合前后相同，未重启服务；新配置只在下次启动生效。节点 7 当前空闲内存较少但有较多可回收文件缓存，启动后需重新充分预热；绑定不迁移原进程已分配页面，也不保证已有共享文件页全部本地。

## 外部证据与回退

- 任务根：`/data/jinghao/deepseek/numa-bind-20261105-01`，规范路径、owner、空间和唯一目录已检查。
- 原脚本：`start-model.original.sh`，SHA256 `9edac7b004ebd9aa6eb0722c98aa3e19e60021088e5275cc8ddc3af785f3f8e1`。
- 新脚本：`start-model.numa.sh`，SHA256 `d11d5148f7a33c30fe42ebfebe1954159f9d68ad0741ebcb681917a9baf77e39`。
- 精确命令与验证回执：该目录 `commands/apply-numa.py`、`commands/apply-numa-r1.py`、`manifest.json`；必要 SHA 在模型 optimize/state.yml。
- 回退：`python3 /data/jinghao/deepseek/numa-bind-20261105-01/commands/restore-original.py`，带 SHA 防护，不停止或重启服务。
- 本次不形成优化收益结论；Prefill/Decode/Mixed 及四个正式端到端场景均未测，等待用户复测。此前 NUMA 短探针和完整 E2E 曾出现不同收益方向，不能预判本次增益。
