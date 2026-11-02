# MiniMax Flash1019 编译器dot-K16精度复测

清缓存后用户明确恢复的resume02三项全量已完成：PPU-07最新容器8045，物理0–7，Flash1019，FlagTree0.7.1.dev1+ppu3.6，adjust SHA bffec8…c832。父目录人工暂停run及所有旧分数保留，不计作精度失败。

| 数据集 | 正确/全量 | 分数 |
|---|---:|---:|
| GPQA Diamond | 166/198 | 83.84%（通过81%） |
| Math500 | 467/500 | 93.40% |
| ERQA | 252/400 | 63.00% |

原生gate只读复验PASS；Math500生成参数匹配冻结proof；ERQA400实际items/evaluated ID集合均等于冻结400，NUL-only0、原始空响应0、30000触顶4。三项/queue成功退出，模型health200且空闲。monitor已PAUSED、模型服务保留，无性能或新优化。

[结构化状态](../../../models/MiniMax-M3.1-Flash-W8A8/ppu/20261021-dot-k16-tp8-accuracy/optimize/state.yml) · [实验说明](../../../models/MiniMax-M3.1-Flash-W8A8/ppu/20261021-dot-k16-tp8-accuracy/optimize/acc-001.md)

当前执行：`/mnt/nfs/users/jinghao/minimaxM3.1/optimize/20261021-minimax-m31-dot-k16-tp8-accuracy/resume-20261021-02`；run `accuracy/dot-k16-first8-t1-suite-20261021-02`。路径/SHA见结构化状态。设备回归证据同源码/compiler/拓扑复用，新模型graph105+2实际通过。单次采样分数变化不作单一改动因果或性能结论。
