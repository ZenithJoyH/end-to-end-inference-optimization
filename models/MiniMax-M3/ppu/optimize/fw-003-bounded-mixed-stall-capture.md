# fw-003：Mixed 慢路径有界捕获

## 契约

- 分类：`framework`
- 父目标：`p1024-d1024-c64-n128`
- 状态：`complete`
- 决定：`diagnostic_complete_no_code_change`
- 假设：Decode/Mixed 轮次中 16–21 秒单请求间隔是可在服务端 trace 与同步主机/PPU 时间线中观测的间歇性慢路径，可区分 host gap、device gap、collective wait 或 scheduler admission。

## 有界实验

- milestone：`P1024/D256/C64/N128`，服务配置与当前 P1K baseline 一致，仅增加 PyTorch profiler；它服务于正式 `P1024/D1024/C64/N128` 的长停顿定位，不是正式性能结果。
- 1 次无 profiler 预热，随后 2 次 profiled 测量；不追加第三次。
- 慢路径命中标准：任一请求的单次 ITL `>= 5 s`。
- 证据：客户端 per-request TTFT/ITL，服务日志，TP16 trace，主机 `vmstat`/`pidstat`，PPU 利用率/显存/功耗/温度/时钟时间线。
- profiler-on 时延仅用于定位，不用于计算性能收益。

## 停止与后续

- 若命中 `>=5 s` 单次 ITL，先完成 rank/phase/timeline 完整性核验，再归因；未经 timeline 证明不宣称根因。
- 若两次均未命中，标记 `incomplete_for_stall_attribution`，保留已有证据并转向下一个独立框架候选，不扩大捕获预算。
- 捕获后必须恢复无 profiler 服务，重新通过 health、graph capture 和文本 smoke。

## 结果

- diagnostic 完整通过：预热 1 轮和 profiled 2 轮均完成；每个 profiled 轮次都生成 16 个 TP rank trace 和 1 个 API trace，共 34 份、2.2 GB，无校验错误。
- 两个 profiled 轮次分别为 463.01/461.95 output tok/s，最大单次 ITL 为 0.780/0.781 s，均未命中 5 s 慢路径。因此不存在可用于慢路径函数级归因的 device trace。
- 无 profiler 预热轮命中慢路径：325.46 output tok/s，35 个请求的单次 ITL `>=5 s`，最大 6.946 s。
- 同步低开销时间线显示，在约 6.95 s 间隔中主机整体 CPU 约 90% idle、I/O wait 为 0；16 个 `VLLM::Worker_TP` 进程各自持续占用约 1 个 CPU 核。PPU 在 2 s 采样中出现一次 16 卡全部 0% 利用率，然后各 rank 不同步恢复；Worker 同时出现 minor faults 和 RSS 增长。
- 该证据排除客户端、整机 CPU 饱和与存储 I/O wait，并把范围缩小到 worker 侧 CPU 工作/自旋/懒初始化或内存缺页路径；尚未取得用户态函数栈，不宣称精确根因。
- 历史慢轮并非只有服务首轮：正式 P1K Mixed 在前 4 轮稳定后的 r5 出现 20.73 s ITL；fw-001 baseline 的 r4/r6 也会再现。因此单纯增加启动 warmup 不能作为已证明的优化。
- 捕获后已恢复无 profiler 的 8192/AABS0 服务，health、6 个 graph capture 和北京 smoke 全部通过。

## 证据路径

- `/mnt/nfs/users/jinghao/minimaxM3/20260921-minimax-m3-ppu-e2e/profiling/fw-003-bounded-mixed-stall-capture`
- `/mnt/nfs/users/jinghao/minimaxM3/20260921-minimax-m3-ppu-e2e/results/fw003-timeline-correlation-v5.json`
- `/mnt/nfs/users/jinghao/minimaxM3/20260921-minimax-m3-ppu-e2e/transitions/fw003-restore-no-profiler-service`

## 下一步

以独立 `fw-004` 做有界的 worker CPU 栈捕获：在无 profiler 的 P1024/D256/C64/N128 诊断轮中，仅当客户端活跃且 16 卡连续低利用率时，捕获少量代表 rank 的用户态/内核栈。时延仅用于定位，不做性能对比。
