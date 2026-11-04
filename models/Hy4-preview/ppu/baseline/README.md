# Hy4-preview / PPU 基线状态

Agent 结构化事实入口：[state.yml](state.yml)。

状态：`p4k_scout_complete`。

边界说明（2026-09-21）：本页是进入优化阶段时建立的 P4K scout 基线记录，
不随当前目标场景迁移而改写。P16K 的 scenario-entry 与缩减 milestone 记录在
[优化实验](../optimize/README.md)；它们尚不构成 anchor baseline 或正式 P16K
验收结果。

初始环境复刻、门禁、失败尝试和 scout 冻结过程详见
[20260914-isolated-p4k-baseline.md](20260914-isolated-p4k-baseline.md)。该文件从
旧 `optimize/history/` 迁入基线目录，不再作为优化点记录。

独立优化容器已通过镜像谱系、挂载一致性和运行参数门禁；固定 chat smoke + C8 正确性护栏 9/9 通过。

`P4096/D256/C64/N64` 在预热中因预计多小时单轮成本而中止；原生回执正确标记为 `failed`，不纳入性能数字。当时只有 5 个请求驻留、59 个排队，prompt 累计增量仅 16,384 tokens。

`P4096/D32/C8/N8` scout 的 1 轮预热 + 2 轮测量全部通过。两个测量轮的基线中位数为：耗时 773.173 s，output throughput 0.331103 tok/s，total-token throughput 42.7123 tok/s，P99 TTFT 764,650.05 ms，P99 TPOT 21,425.45 ms，P99 ITL 48,217.89 ms，P99 E2EL 773,149.30 ms。最大相对 spread 为 0.591%，低于 15% 门限。

远程主证据：`/mnt/nfs/users/jinghao/hy4-preview/optimize/20260914-hy4-preview-ppu-e2e/`。本阶段仅支持 P4K 结论，不建立 P16K/P32K/P64K 基线。

<!-- baseline-record-review:start -->
## 正式目标覆盖与历史测量

本节是记录审查：原测量状态与角色保持不变，不是新评测回执。`incomplete` 表示此表未闭合正式基线证据；历史、缩减或有观察器的结果须按原范围解释。

| 正式目标 | 正式基线证据状态 | 已记录指标数 | 边界 |
|---|---|---:|---|
| p1024-d1024-c64-n128 | incomplete | 0 | 本阶段没有可归属到此正式场景的汇总数值；不推断从未运行。 |
| p4096-d1024-c64-n128 | incomplete | 0 | 本阶段没有可归属到此正式场景的汇总数值；不推断从未运行。 |
| p16384-d1024-c64-n128 | incomplete | 0 | 本阶段没有可归属到此正式场景的汇总数值；不推断从未运行。 |
| p32768-d1024-c64-n128 | incomplete | 0 | 本阶段没有可归属到此正式场景的汇总数值；不推断从未运行。 |

| 场景 / 角色 | 已记录性能数值（附单位） | 证据范围 / 原字段 |
|---|---|---|
| p4096-d32-c8-n8-scout / baseline | duration_s = 773.1727508245967 s；output_throughput = 0.3311032363012472 token/s；total_token_throughput = 42.7123174828609 token/s；p99_ttft_ms = 764650.0544080033 ms；p99_tpot_ms = 21425.45135600537 ms；p99_itl_ms = 48217.88727579638 ms；p99_e2el_ms = 773149.2996059451 ms | P4K scout only；非 C64 正式目标；原文 conclusion_boundary 限定；`/performance_evaluation/measured_medians` |
<!-- baseline-record-review:end -->
