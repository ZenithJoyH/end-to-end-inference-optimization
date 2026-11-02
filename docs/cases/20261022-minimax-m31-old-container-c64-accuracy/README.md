# MiniMax Flash 原容器64并发精度重测

用户要求PPU-07/minimaxM3.1-opt-20261008执行原start-model.sh，三项全量C64。实际Flash1019/nameMiniMax-M3.1-new2/8035/TP8物理0–7/maxlen100000/prefixcacheenabled；采样1/.95/-1，生成18000/28000/ERQA30000，单次串行独立响应cache。105+2模型最小及FULL/PIECEWISE capture通过；源码、配置及8–15无关工作负载未变。

整套原生controller于 2026-10-22T23:40:26.729359+08:00 完成；400个ERQA实际唯一ID与冻结集合一致，evaluated400和原生正确数一致，原始空/NUL均0、触顶6。终态源码/compiler/runtime/argv不漂移，模型health200；监控minimax-c64已删除，模型服务保留。无额外评测、重评分或性能任务。

| 数据集 | 旧容器C64 | new2（32/32/16并发） | 旧减new2 |
|---|---:|---:|---:|
| GPQA | 167/198，84.34% | 167/198，84.34% | 0 |
| Math500 | 469/500，93.80% | 464/500，92.80% | +1.00个百分点 |
| ERQA | 252/400，63.00% | 259/400，64.75% | −1.75个百分点 |

GPQA原生gate通过81%；Math500/ERQA无指定阈值。GPQA互换7对7，Math500旧多5题（几何净4），ERQA旧对新错31/反向38。权重/tokenizer/vLLM及启动参数相同，客户端并发与Plugin/FV/FG/compiler均不同，不能当单变量代码A/B。用户历史最高分32768契约及所有旧分数保留独立。

[实验说明](../../../models/MiniMax-M3.1-Flash-W8A8/ppu/20261022-old-container-c64-accuracy/optimize/acc-001.md) · [完整逐题比较](../../../models/MiniMax-M3.1-Flash-W8A8/ppu/20261022-old-container-c64-accuracy/optimize/diag-002.md) · [结构化状态](../../../models/MiniMax-M3.1-Flash-W8A8/ppu/20261022-old-container-c64-accuracy/optimize/state.yml)

远端run：`/mnt/nfs/users/jinghao/minimaxM3.1/optimize/20261022-minimax-m31-old-container-c64-accuracy/accuracy/old-container-c64-t1-suite-20261022-01`。整套result SHA `b3610b28c5ca07c225987749442060c1ce14fae60c05baf53f8668c93ba740fc`，controller SHA `9c84552a907b002b652d76e65e0d726d5329309661a6e43df851a17e3d97bbd7`；ERQA原生result SHA `9b02c678f831bd5f66ab65676becd7c7b43e7e38799c77f116eb71dfa3fb24b6`，evaluated SHA `bce68c98594819b9001e508969cdcceb625404b73d528f90299da6368fd83288`。其他原生产物与SHA见state。
