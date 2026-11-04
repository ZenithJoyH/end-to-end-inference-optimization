# accformal-004：当前 131K 服务全量 GPQA 正式精度

## 契约

- 模式：`formal-gate`。
- 覆盖候选：`fw-006-flaggems-targeted-schema-reflection` + `op-003-conv3d-blacklist-131k-startup`。
- 服务：`bd37abcbf719:8023:895010:279945667`，TP16 BF16，`max_model_len=131072`，prefix cache 关闭，FULL_DECODE_ONLY graph sizes 1/2/4/8/16/32。
- Plugin 私有副本 `thead.yaml` 黑名单：`conv3d`、`cudnn_convolution`。
- 任务：`gpqa_diamond_generative_cot`，198 个唯一题，`limit=0`。
- 请求：并发 64，seed 42，`temperature=1, top_p=0.95, top_k=20, max_gen_toks=60000`。
- 指标：`exact_match,strict-match`；阈值 `0.88`，`score >= threshold` 通过。

## 证据与状态

- 远程根：`/mnt/nfs/users/jinghao/minimaxM3/20260921-minimax-m3-ppu-e2e/accuracy/accformal-004-gpqa-c64-60k-131k-threshold88`。
- 规定评测容器：`harbor.baai.ac.cn/flageval/flageval-llmeval:v1`。
- provenance 与 preflight 已通过；数据 revision 为 `content-sha256:167548b01bcfd7d38d0eb80bb01bd1e6dded4d3aa14b41a4bdba0beb5423dadc`。
- heartbeat：`minimax-m3-accformal004-gpqa-c64-60k`，30 分钟间隔，启动前已创建。
- 启动时间：`2026-09-23T10:03:00+08:00`；launcher PID `3074644`。
- 原生 `run-record.json` 状态 `evaluated`，`process_succeeded=true`；`accuracy-gate.json` 的 `passed=true`，strict-match `180/198=0.9090909091 >= 0.88`。
- gate：`/mnt/nfs/users/jinghao/minimaxM3/20260921-minimax-m3-ppu-e2e/accuracy/accformal-004-gpqa-c64-60k-131k-threshold88/accuracy-gate.json`。
- run record：`/mnt/nfs/users/jinghao/minimaxM3/20260921-minimax-m3-ppu-e2e/accuracy/accformal-004-gpqa-c64-60k-131k-threshold88/native/minimax-m3-fw006-op003-gpqa-full-graph-c64-60k-threshold88/9d48576bbb4441079fe1e30dca73ce99/run-record.json`。
- 服务后续状态：绑定的 8023 EngineCore 在 `2026-09-23T11:44:25+08:00` 退出；`13:46+08` 健康端口连接被拒。当前容器另有 `8013/max_model_len=100000` 服务，不能自动继承本 gate。只重启同候选也须按精度 Skill 的 rebind 规则核验；若源码或配置变化则重新正式评测。
