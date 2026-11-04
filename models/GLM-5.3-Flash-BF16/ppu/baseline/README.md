# 基线结果

Agent 结构化事实入口：[state.yml](state.yml)。

状态：`external_user_baseline_partially_failed`（2026-09-24 用户提供结果已归档；不是项目正式四场景 anchor 验收）。

## 性能结果状态

用户在未优化版本上运行了 3 轮随机长度 finite-batch 测试，脚本将 Run1 排除，以 Run2/Run3 的算术平均生成 `SUMMARY`。本项目四个固定场景中的 P1K 未在该脚本的默认列表中；另测了 P64K。结果如下，失败项保留为失败，不把 CSV 中的 0 当成吞吐：

| 场景 | 实际状态 | Run1/2/3 成功请求 | Run2/3 输出吞吐均值 | Run2/3 P99 TTFT/TPOT/ITL 均值 |
|---|---|---:|---:|---:|
| P1K/D1K/C64/N128 | `not_run` | — | — | — |
| P4K/D1K/C64/N128 | `success`（外部诊断基线） | 128/128、128/128、128/128 | 497.78 tok/s | 87,924.65 / 63.30 / 1,319.69 ms |
| P16K/D1K/C64/N128 | `success`（外部诊断基线） | 128/128、128/128、128/128 | 193.66 tok/s | 288,390.65 / 161.57 / 2,052.26 ms |
| P32K/D1K/C64/N128 | `failed` | 27/128、0/128、0/128 | — | — |
| P64K/D1K/C64/N128（额外场景） | `failed` | 0/128、0/128、0/128 | — | — |

P4K/P16K 的 Run1 虽为 128/128 成功，但耗时分别为 8,136.95 s、9,793.53 s，远高于 Run2/Run3 的约 263 s、677 s；表中均值严格沿用脚本的 `SKIP_FIRST=1` 口径，不能据此证明项目要求的稳态准入。P32K Run1 运行 4,859.65 s，仅 27/128 成功、共生成 1,453 tokens；随后 Run2/Run3 均因 `127.0.0.1:8010` 连接被拒而 0/128。P64K 三轮也均因该端口无法连接而失败。现有客户端日志证明服务在后续轮次不可访问，但不足以判定 P32K 首轮导致服务退出的根因。

原始目录：`/mnt/nfs/users/jinghao/glm5.3-flash/test/benchmark_results/glm5.3-flash-base`；入口脚本：`/mnt/nfs/users/jinghao/glm5.3-flash/test/vllm_perf.py`（SHA-256 `0d733162ff69c6b7a74262c1bf422a492115a2156ce10249fd56f82bf4424f36`）；运行日志：`/mnt/nfs/users/jinghao/glm5.3-flash/test/perf.log`（SHA-256 `702dcc694f818052bc39a7bd28765cbd5e8d8ab9fbcc1bc0ff81d38ea68ed331`）。四份 CSV 和六份错误日志的逐项路径/SHA 见 [state.yml](state.yml)。命令使用 `vllm bench serve`、`/v1/completions`、`--ignore-eos`、C64/N128、固定随机长度；原生客户端显示 seed 0、无限请求率。结果目录没有绑定当时服务身份、启动配置及前缀缓存状态的 manifest，且使用用户脚本而非本项目维护版 runner。因此成功两项可作为外部诊断数值，尚不能签发项目正式 anchor baseline、四场景完成结论或相对优化版的精确加速比。

已经取得的历史 checkpoint baseline 数字如下；这些 workload 与正式四场景不同，只作为局部诊断基线：

| 诊断场景 | baseline 输出吞吐 tok/s | 状态与边界 |
|---|---:|---|
| P4096/D128/C32 | 157.442 | causal-conv checkpoint 原路径 |
| P1024/D512/C32 | 691.814 | causal-conv checkpoint 原路径 |
| P4096/D512/C8 | 207.609 | causal-conv checkpoint 原路径 |

完整结构化数值已合并到 `state.yml`；这里不把诊断场景冒充正式
anchor baseline。

2026-09-11 曾核验 `PPU-13`、源容器、模型端点、实际进程、revision 与空闲队列。独立优化
容器已经创建；镜像 ID 相同、挂载比较通过，私有 Plugin/FlagGems/FlagGems-vllm 副本与
源 revision 一致。用户授权后已暂停源 vLLM 服务，源容器保持运行，16 张 PPU 已释放到
1 MiB/卡。该时间点尚无正式基线；2026-09-24 的用户外部结果如上单独记录，不用适配阶段的 c8 sanity 数字代替。

原始 inspect、运行时回执和测量结果保留在 `state.yml` 列出的远端路径；
本目录不再保留重复 JSON 快照。
