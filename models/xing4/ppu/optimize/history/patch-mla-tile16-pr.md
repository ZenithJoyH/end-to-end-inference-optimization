# PR 建议：为小 head MLA dense decode 自动选择更小的 head tile

## 建议标题

`perf: use a smaller head tile for validated MLA dense decode shapes`

## 问题与改动

MLA dense decode 原实现固定使用 `BLOCK_H=64`。当 tensor parallel 后每 rank 只有少量 query heads 时，一个 program 会为大量无效 head 保留计算和共享内存资源。

本改动把 kernel 主体抽成共享的 Triton JIT，并保留两个相互独立的 autotuner：原 BH64 配置和小 head BH16 配置。dispatch 只在以下已验证条件全部满足时自动选择 BH16：

- 单 token decode，`SQ=1`
- `0 < H_q <= 16`
- `DQK=576`、`DV=512`
- Q 和 KV cache 均为 BF16
- page size 为 16 或 64
- Q 最后一维连续

其他输入继续使用原 BH64 autotuner，TLE 路径优先级不变。选择逻辑不依赖模型名、机器、容器或环境变量。

## 验证

- 选择测试：H8/page16、H16/page64 命中；H32 和 page32 回到原路径。
- 数值测试：H8/page16、H16/page64 对 PyTorch FP32 reference，通过 output `atol/rtol=0.02` 和 LSE `atol=0.03, rtol=0.01`。
- PPU硬件边界：page16/64、H8/H16、H32 fallback、空 batch、零长度 padding、eager、graph capture 和两次 replay 均通过。
- xing4 TP4 graph 服务：固定 C8 为 8/8，请求内容和结束原因一致。
- 同设备端到端性能研究：P1024/D1024/C64/N128 下，candidate 相对 revert 的输出与总 token 吞吐中位数均提高 73.15%。revert 两轮波动约 25.5%，该数据用于确认明显正收益，不作为容量或统计置信度结论。

上游测试文件在当前 PPU 环境受模块级 NVIDIA FlashMLA reference 条件影响而跳过；独立 PPU 硬件测试覆盖了本次路径。合入前仍建议在上游支持的 CI 环境执行完整测试。

## 产物

- 完整历史补丁：目标环境 `/workspace/e2e-artifacts/patches/mla-tile16/`；应用前按本页记录的
  revision 与 SHA 核验目标源码。
- 实验与原始产物位置：[PR重构实验](../history/20260907-mla-pr-refactor.md)
- 回退：反向应用补丁并按相同配置重启服务。

未验证其他平台、FP16、其他 DQK/DV/page、不同 TP 后 head shape 和完整模型精度；这些范围不作性能声明。
