# 20260921-minimax-m3-ppu-e2e：MiniMax-M3 / PPU 端到端推理优化

## 1. 摘要

- 执行规则：`0.39` / `2026-09-20`
- 验收范围：`formal`
- 状态：`op010_incomplete_reverted_mixed_itl_partially_attributed`（以下旧诊断保留历史时序）
- 精度/性能状态：历史 131K/60K 正式 GPQA `180/198=90.91%` 达 88% 阈值，但绑定旧退出服务；当前原路径服务无新 gate。`fw006` 保留；`op010` 两次 D256 A/B/A 观察约 +8% 输出吞吐，均因 P99 ITL 轮间 spread 判为 `incomplete` 并回退。
- 目标：对 PPU-07 上已适配的 MiniMax-M3 建立可比基线，按 P1K→P4K→P16K→P32K 优化端到端推理。
- 主指标：output-token throughput；守护指标：TTFT、TPOT/ITL、E2E、失败率、显存与正确性。
- 通过门槛：用户未指定相对提升或 SLO；只作客观改善/回退判定，不宣称“达标”。
- 证据等级：`observation`
- 模型产物：`models/MiniMax-M3/ppu/{baseline,optimize,acceptance}/`

## 2. 目标与运行事实

- 模型：`/mnt/cpfs/models/MiniMax-M3`
- 平台/Host：T-Head PPU / `PPU-07`（inventory 实机 `bm-aliyun-wlcb-zonea3-c-810e-96g-10-7`）
- 源适配容器：`minimaxM3`；容器保持运行且未修改、未重启。经用户明确授权，仅停止了其中监听 `8013` 的 MiniMax-M3 服务树以释放设备。
- 独立优化容器：`minimaxM3-opt-20260921`，已从有效适配镜像创建；当前原路径回退服务实例 `bd37abcbf719:8023:1368844:288789027` 健康，TP16 BF16、131K、max-seqs32、FULL_DECODE_ONLY 6 个 capture size、prefix cache off。旧 65K 配置仅属前期历史实验。
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
- 资源：源服务已按授权停止，`8013` 已释放且源容器保持运行；当前 16 张 PPU 仅由独立优化服务使用。
- `image_lineage=verified`；`mount_parity=passed`；源/优化容器的三个代码仓 revision 和工作区状态无差异。
- 配置漂移诊断：漂移的 AABS1/100K/no-prefix/默认 51-capture 组合稳定生成 NUL；恢复已验证交付组合后输出正确，再单变量关闭 prefix cache 仍通过 6/6 capture 与北京/巴黎双 replay。单个漂移变量未完全隔离，不把 AABS、100K 或 capture 数量中的任一项单独宣称为根因。
- baseline-sanity：固定 GPQA 前十题、greedy、C8，strict-match `10/10=1.0`、0 timeout、服务前后身份一致。doc_id 7/8 各达到 30K 上限，按项目规则作为非门禁输出健康观察保留。证据：`/mnt/nfs/users/jinghao/minimaxM3/20260921-minimax-m3-ppu-e2e/accuracy/baseline-sanity/`。
- `fw-006` 正式 GPQA：198 题 C64，`temperature=1/top_p=0.95/top_k=20/max_gen_toks=30000`，得分 `172/198=0.8686868687 < 0.88`；0 timeout、0 request error，证据有效。相对上游 PPU-13 历史 177/198，净失分全部来自 30K 截断组，非截断组多对 1 题。同服务、同 prompt、同 `seed=1234` 的 6 个并发重复响应哈希全部不同，三道 formal 错题都可在重复中翻转为正确答案。已确认当前单次 C64 采样契约不可复现，30K 截断放大了轨迹漂移；`fw-006` 尚未做 formal 级因果二分，但当前没有它改变数值/答案语义的证据。
- Host 纠正：曾因上游记录首先在 PPU-13 创建了一个空闲容器和快照；已将证据移至 `hosts/PPU-13-off-target/`，未启动服务、未改源码、未占卡，镜像/容器保留待后续确认是否清理。

## 5. 下一步

1. [op010 实验](../../../models/MiniMax-M3/ppu/optimize/op-010-thead-invoke-m32-gemm2-bk64.md) 已完成并精确回退：单卡 stage +37.19%、TP16 16/16 worker 命中、10 题最小 GPQA strict 10/10；两轮独立 D256 A/B/A 观察 +7.98%/+7.79% 输出吞吐且回退复现，但冻结比较均 `incomplete`，未运行候选的 198 题 formal gate，不能宣称端到端优化完成。
2. [perfdiag-001](../../../models/MiniMax-M3/ppu/optimize/perfdiag-001-p1k-mixed-first-token-itl-variance.md) 只读分析全部 18 个测量轮：原路径和候选都可能出现请求波次前/末 token 的 300–500ms 额外 ITL；现有服务聚合日志不足以证明唯一根因。若继续此候选，应先冻结新的 Mixed 长尾判定方法或采有界时序 trace，再对三角色同配置重测，不追改旧结果。
3. 当前组合只有 fw006 + 私有 blacklist；仍需当前服务的新精度 gate、P1K/D1024 与四正式场景验收后才能发布任何正式收益结论。当前原路径服务未被本轮诊断修改。

## 6. 外部过程材料

性能基线的可执行脚本和计划只保存在用户指定的远程案例目录
`/mnt/nfs/users/jinghao/minimaxM3/20260921-minimax-m3-ppu-e2e/commands/performance/`，不在本地
案例目录保留副本。2026-09-21 在 PPU-07 只读复核的 SHA-256 如下：

| 文件 | SHA-256 |
|---|---|
| `build-baseline-service-manifest.py` | `f794a8396ed7fe8fe0819d8880497a46055274896da021a284ad40cd927c5c69` |
| `capture-baseline-service.py` | `e8bd0ec0373100cbf163a20bfe05d48f65b81616495b54aaa85a2e643301e0d8` |
| `perf-p1k-decode-plan.json` | `35d3e81c40b7fb0125e5cd584068f6b827c4feacc1fefee93d3098588fff59b4` |
| `perf-p1k-mixed-plan.json` | `d35d5b454b72e865f9a1f132f8d82fbcedb3e86f222654fc6b0db4763664fba7` |
| `perf-p1k-prefill-plan.json` | `adfe09db60321eefc18ec3b5d26e62684abb87eeba2c12d86fe4f6d97a36eade` |
| `perf-p1k-prefill-warmup3-plan.json` | `b997df82a80c6938d8f3bc4b88fe28289a495ba8192c208d7a3c7dce534fb74c` |
| `run-p1k-baseline-view.sh` | `328ae4aaf75f3c5d1bfe82474a2f821f67014383303560ebc0812d555e87dedf` |
| `verify-live-baseline-service.py` | `7986543686d86f3481f96c1248c9865352caa70ba949a09b6a054b2d804db1e8` |

远端目录中的文件仍是活跃任务材料；本次仅在确认路径和内容哈希一致后移除本地重复副本，未改写、
删除或归档远端内容。
