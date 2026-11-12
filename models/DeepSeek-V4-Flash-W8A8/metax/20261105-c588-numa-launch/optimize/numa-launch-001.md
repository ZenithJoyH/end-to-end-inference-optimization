# numa-launch-001：按 PCIe 拓扑绑定 TP worker

- 类型：framework；只交付用户要求的启动脚本配置，用户自行重启及端到端复测。
- 日期：2026-11-05；状态：delivered_for_manual_retest；acceptance_scope：diagnostic。
- 目标 Host：mxC588-5；脚本：`/data/jinghao/deepseek/start-model.sh`。
- 用户授权直接调整该原始脚本；本次不创建或启动优化服务，不改 vLLM/Plugin 源码，不改变正在运行的进程。
- 远程任务目录：`/data/jinghao/deepseek/numa-bind-20261105-01`；使用已授权的本模型工作根。
- 原脚本 SHA256：`9edac7b004ebd9aa6eb0722c98aa3e19e60021088e5275cc8ddc3af785f3f8e1`，原 mode 0644、owner 0:0。
- 候选：`/data/jinghao/deepseek/numa-bind-20261105-01/start-model.numa.sh`。保留原模型、可见设备、TP、KV、graph、批处理、端口和日志配置，增加 native vLLM `--numa-bind --numa-bind-nodes 7 7 4 4 4 4 6 6`。
- 容器当前缺少 numactl；从目标 Host 现有 `/usr/bin/numactl` 复制到任务私有 tools 目录供未来启动使用，不安装或替换系统包。
- EngineCore 由 native vLLM 绑定到节点 4/6/7 的并集；worker 按可见设备序号绑定 CPU 和内存。native NUMA 路径要求 spawn。

| TP rank | 可见物理逻辑设备 | PCI BDF | NUMA | CPU 集合 |
|---|---|---|---|---|
| 0/1 | 8/9 | 0000:73:00.0 | 7 | 98–111 |
| 2/3 | 10/11 | 0000:94:00.0 | 4 | 56–69 |
| 4/5 | 12/13 | 0000:99:00.0 | 4 | 56–69 |
| 6/7 | 14/15 | 0000:e6:00.0 | 6 | 84–97 |

## 验证与边界

已检查 bash 语法、原参数逐项保持、native worker/EngineCore 参数生成、CPU/内存绑定及私有 numactl 运行，均通过；8 个 worker 策略加 EngineCore 并集均由独立子进程实测 Cpus_allowed 和 MPOL_BIND，未初始化 GPU 或发推理请求。原生 numa_wrapper.sh 的 CPU-only 执行也通过，子进程 LD_LIBRARY_PATH 保持原值。不运行模型精度与性能测试，相关状态为 incomplete。四个正式场景均未验收。先前同平台 NUMA 短 prefill 探针与完整 E2E 的收益方向曾不同，因此本次不预判收益。

节点 7 空闲内存少但有大量可回收文件缓存；实际重启时可能出现回收开销。稳态测试需重新充分预热，保留各轮结果。CPU/内存 binding 只保证后续新进程策略，不迁移原服务已分配的页面，也不证明共享文件页全部本地。

## 执行与回退

已在 2026-11-05 18:33（Asia/Shanghai）完成原子替换，mode 0644、owner 0:0 保持；目标脚本 SHA256：`d11d5148f7a33c30fe42ebfebe1954159f9d68ad0741ebcb681917a9baf77e39`。原始脚本备份：`/data/jinghao/deepseek/numa-bind-20261105-01/start-model.original.sh`。回退执行 `python3 /data/jinghao/deepseek/numa-bind-20261105-01/commands/restore-original.py`，只恢复脚本，不停止或重启任何服务。

## 工具依赖及证据

首次 CPU-only 校验因容器 libnuma 缺少宿主机 numactl 需要的符号版本而停止，目标脚本未变。r1 将宿主机已有 libnuma 放入私有 `tools/lib`，用动态加载器 `--library-path` 仅作用于 numactl，自身不导出 LD_LIBRARY_PATH。再次校验和原生包装器执行通过；不更换系统库。

- 精确执行脚本：`/data/jinghao/deepseek/numa-bind-20261105-01/commands/apply-numa-r1.py`，SHA256 `fb5db21ff1ec4002bc544b9bfff20f2cdaf2c8f82a95dc407d12bd4435df3156`。
- 原始尝试：`/data/jinghao/deepseek/numa-bind-20261105-01/commands/apply-numa.py`（失败点和修正均保留）。
- 外部回执：`/data/jinghao/deepseek/numa-bind-20261105-01/manifest.json`（含短期进程身份，仅外部保存）。
- 工具、库、脚本及回退文件 SHA 见本目录 state.yml 的 artifacts。

## 性能效果与决定

本轮 baseline/candidate/revert 的端到端吞吐、TTFT、TPOT 均未测试；不计算加速比。决定为 incomplete，候选仅完成配置交付，等待用户重启与稳态同配置测试。无模型 graph replay、精度 gate 或正式四场景验收声明。

2026-11-05 更新：当前脚本已由 [独立 8 物理卡配置案例](../../20261105-c588-tp8-eight-cards/README.md) 替代；此实验状态 superseded。旧回退命令会拒绝覆盖更新后的 SHA，恢复前一版本请先使用新案例回退入口。
