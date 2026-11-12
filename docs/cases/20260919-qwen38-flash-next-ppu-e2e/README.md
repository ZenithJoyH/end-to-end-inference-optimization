# Qwen3.8-Flash-Next / PPU-01 · 调度、算子与端到端性能

**目标**　在 TP8 graph 服务上，分开定位 Prefill、Decode 和 Mixed 的吞吐与尾延迟瓶颈。

**结论**　P1024/D1024/C64/N128 筛选中，`max-num-seqs` 从 32 调到 64 后，Mixed 输出吞吐由 330.73 升至 570.53 tok/s，P99 TTFT 从 104.90 降至 12.44 秒，P99 ITL 却增加了 561.37%。后续将 batched-token 预算从 4096 降至 2048 未达到预定的 ITL 恢复目标，已回退。[并发配置对照](../../../models/Qwen3.8-Flash-Next/ppu/optimize/fw-001-max-num-seqs-64-screen.md) · [预算回退](../../../models/Qwen3.8-Flash-Next/ppu/optimize/fw-003-maxseq64-max-batched-tokens2048.md)

**适用边界**　这些数字属于早期 P1K 筛选。后续 SQLite 缓存修复组合在 acc-011 绑定的服务上达到 GPQA 175/198，重启后的实例需单独核验。四场景最终性能验收仍记为未完成。[精度记录](../../../models/Qwen3.8-Flash-Next/ppu/optimize/acc-011-full-gpqa-dual-cachefix-20260924.md) · [验收记录](../../../models/Qwen3.8-Flash-Next/ppu/acceptance/README.md)

**证据入口**　[模型实验总览](../../../models/Qwen3.8-Flash-Next/ppu/optimize/README.md) · [结构化账本](../../../models/Qwen3.8-Flash-Next/ppu/optimize/state.yml) · [本地过程材料、旧版差异与恢复包](../../../.cache/model-record-archives/20261112-qwen38-hy4-case-materials/20260919-qwen38-flash-next-ppu-e2e.md)

在其他工作区可用 `git ls-tree -r --name-only 9aea55eb -- docs/cases/20260919-qwen38-flash-next-ppu-e2e/` 查找归档前的 288 个文件，用 `git show 9aea55eb:<仓库相对路径>` 读取原文。
