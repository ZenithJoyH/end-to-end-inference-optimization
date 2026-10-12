# MiniMax-M3.1 W8A8 / PPU-07 / TP8 优化

用户2026-10-10明确恢复任务并切换8卡；继承模型适配和已隔离容器，不继承16卡性能或精度gate。目标稳态总吞吐，GPQA198题strict-match>=81%。正式场景顺序P1K/P4K/P16K/P32K，均D1024/C64/N128。

当前输入为用户start-model.sh SHA57442d5a08af565dcc317749536d7bf18e5ca63e61fb9614a1590eedbcc7f747，基线服务8025、TP8、7Mixed+7Decode buckets、原11exports；fw-004临时14Mixed/7Decode候选仅在案例启动副本测量。

外部案例：/mnt/nfs/users/jinghao/minimaxM3.1/optimize/20261010-minimax-m31-w8a8-ppu-tp8-e2e。镜像谱系和挂载一致性通过。原 TP8 路径 C8 0/8、C1 0/3；[diag-001](../../../models/MiniMax-M3.1-W8A8/ppu/optimize/diag-001.md) 将首次数值分歧定位到 PPU GQA8 sparse Prefill attention。私有 Plugin 的 [fix-001](../../../models/MiniMax-M3.1-W8A8/ppu/optimize/fix-001.md) 只为受支持形状将内部 head tile 补齐到16，24组算子检查、graph两次replay、当前105+2最小回归及8rank命中通过。临时观察补丁已撤除，完整TP8 GPQA Diamond198已通过：170/198=85.86%，strict-match>=81%；原实例native issue/check通过；profiling后恢复7桶服务 fresh105+2及native rebind/check通过，沿用原170/198；14桶新配置不能复用原gate；本轮新完整198为169/198=85.35%，native gate已绑定当前候选，门槛81%通过。

FG、FG-vllm、vLLM、源容器和根脚本保持原状态。[perf-002](../../../models/MiniMax-M3.1-W8A8/ppu/optimize/perf-002.md) 已完成P1K稳态单实例基线：三轮总TPS均值1968.23、相对极差0.1384%、延迟守护波动通过。纯Prefill未准入，last3warm spread6.68%>5%，零测量并停止原控制；[perf-003](../../../models/MiniMax-M3.1-W8A8/ppu/optimize/perf-003.md) 已补齐Decode/Mixed-short基线并完成两场景全部8rank与frontend trace归因，保留纯Prefill未准入证据；[fw-004](../../../models/MiniMax-M3.1-W8A8/ppu/optimize/fw-004.md) 新契约8warm+5measure的基线校验通过，Mixed4651.50、Decode1647.33TPS，14桶候选capture与105+2通过，因graph覆盖变化先新完整198（169/198，85.35%通过），候选Mixed五测量均值+0.60%、中位+1.29%低于3%，Decode8warm稳态5.19%>5%、零测量，固定序列停止并不保留。已恢复7桶，fresh105+2及原7桶170/198 native重绑定通过；plan-022转MoE实际shape/backend发现。用户CSV有P4K/P16K/P32K，缺P1K，且缺少服务绑定与稳态准入证据，保留为观察数据；目前没有8卡吞吐收益结论。

模型入口：[baseline](../../../models/MiniMax-M3.1-W8A8/ppu/baseline/README.md)、[optimize](../../../models/MiniMax-M3.1-W8A8/ppu/optimize/README.md)、[acceptance](../../../models/MiniMax-M3.1-W8A8/ppu/acceptance/README.md)。

2026-10-12 根因机制：[diag-003](../../../models/MiniMax-M3.1-W8A8/ppu/optimize/diag-003.md) 已用原始→仅修正A加载地址→原始证明PPU BF16 M8 shared-to-MMA路径漏lane16 K坐标；现有H16绕行的正确性来源已明确。全程独立空闲PPU8，生产服务与源码保持不变；编译器C++源码修复未实施，性能四场景仍未验收。

2026-10-12：diag-004已提交[FlagTree #1350](https://github.com/flagos-ai/FlagTree/issues/1350)。官方最新PPU wheel0.7.0+ppu3.6在独立进程/空闲设备同脚本复测仍失败；主分支未硬件验证。生产服务/源码/根脚本均保持，H16绕行继续保留。
