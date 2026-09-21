# 20260921-minimax-m3-ppu-e2e：MiniMax-M3 / PPU 端到端推理优化

## 1. 摘要

- 执行规则：`0.39` / `2026-09-20`
- 验收范围：`formal`
- 状态：`running`
- 精度/性能状态：`incomplete` / `incomplete`
- 目标：对 PPU-07 上已适配的 MiniMax-M3 建立可比基线，按 P1K→P4K→P16K→P32K 优化端到端推理。
- 主指标：output-token throughput；守护指标：TTFT、TPOT/ITL、E2E、失败率、显存与正确性。
- 通过门槛：用户未指定相对提升或 SLO；只作客观改善/回退判定，不宣称“达标”。
- 证据等级：`observation`
- 模型产物：`models/MiniMax-M3/ppu/{baseline,optimize,acceptance}/`

## 2. 目标与运行事实

- 模型：`/mnt/cpfs/models/MiniMax-M3`
- 平台/Host：T-Head PPU / `PPU-07`（inventory 实机 `bm-aliyun-wlcb-zonea3-c-810e-96g-10-7`）
- 源适配容器：`minimaxM3`；容器保持运行且未修改、未重启。经用户明确授权，仅停止了其中监听 `8013` 的 MiniMax-M3 服务树以释放设备。
- 独立优化容器：`minimaxM3-opt-20260921`，已从当前有效适配镜像创建；基线服务正在独立端口 `8023` 以同配置 graph 模式启动。
- 用户工作根：`/mnt/nfs/users/jinghao/minimaxM3`
- 案例远程目录：`/mnt/nfs/users/jinghao/minimaxM3/20260921-minimax-m3-ppu-e2e`
- 历史端到端结果：`/mnt/nfs/users/jinghao/minimaxM3/test/perf_test/benchmark_results/MiniMax-M3`，待核验 workload/客户端/缓存与当前服务身份后决定可否作为诊断基线。

## 3. 上游适配交付快照

- 来源：`/Users/baai/Documents/ChatGPT/新模型适配/models/MiniMax-M3/`，只读于 2026-09-21。
- `model.yml` SHA-256：`b038b636991c55d914361afe95e3473eee8b7129bdd960f1b876d679c4d3648c`。
- `ppu/platform.yml` SHA-256：`bbb996bd3afd592a654a4606ac2a5a58be28d0ef7af3ab1309e5a52cdb9e2113`。
- 导入事实：上游记录为 PPU-13 / TP16 / vLLM 0.24.0 / graph，Plugin 适配记录指向 `7e412e6f8b6d8a5e4350e0237e1a8548dfaf7b94`；历史 GPQA 177/198=89.39%，门槛 80%。
- 运行时复核：用户当前指定 PPU-07，与上游 Host 不一致；当前 PPU-07 容器使用更新的 MiniMax 专用镜像 `sha256:41d96d...`。上游精度不直接作为本任务当前 gate。

## 4. 当前门禁

- inventory/connectivity：`passed`（PPU-07）。
- 远程工作根：规范路径与权限/空间已检查，case 子目录已创建并用于命令、清单、日志和结果。
- 源容器：运行中，单一 `/mnt` bind mount；实际代码均来自镜像，writable layer 仅观察到 runtime/cache 产物。
- 资源：源服务已按授权停止，`8013` 已释放且源容器保持运行；停止后 16 张 PPU 无计算进程。优化容器的 TP16 基线服务已启动，正在加载权重并初始化 graph。
- `image_lineage=verified`；`mount_parity=passed`；源/优化容器的三个代码仓 revision 和工作区状态无差异。
- Host 纠正：曾因上游记录首先在 PPU-13 创建了一个空闲容器和快照；已将证据移至 `hosts/PPU-13-off-target/`，未启动服务、未改源码、未占卡，镜像/容器保留待后续确认是否清理。

## 5. 下一步

1. 等待独立优化容器的同配置 graph 服务通过 readiness，并保存服务清单及至少两次 graph replay 证据。
2. 执行 baseline-sanity。
3. 用维护版性能工具补齐 P1K Prefill/Decode/Mixed 和可比的 P4K/P16K/P32K baseline。
