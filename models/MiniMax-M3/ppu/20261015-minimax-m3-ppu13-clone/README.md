# 20261015-minimax-m3-ppu13-clone

PPU-13 的 `minimaxM3-latest-20260924` 已运行；当前模型服务为 8024 / TP16 BF16 / 100K / max-num-seqs64 / FULL_AND_PIECEWISE / prefix cache enabled。2026-10-15 14:14（北京时间）完成全量 GPQA 198题、并发64、60K生成上限：strict-match 183/198=92.42%，超过88%阈值，正式gate签发及复验通过；性能未测。

- [baseline](baseline/README.md)
- [optimize](optimize/README.md)
- [acceptance](acceptance/README.md)
