# fw-004：Worker CPU 慢路径触发式栈捕获

## 契约

- 分类：`framework`
- 父目标：`p1024-d1024-c64-n128`
- 状态：`complete`
- 决定：`diagnostic_complete_no_code_change`
- 假设：`fw-003` 中“16 个 Worker 各占一核、PPU 一度全空闲”的慢路径，可通过少量代表 rank 的用户态栈区分为编译/懒导入、allocator/page fault、collective busy wait 或其他 worker CPU 路径。

## 有界诊断

- workload：`P1024/D256/C64/N128`，无 profiler，最多 6 轮，只用于为正式 P1K Mixed 慢路径定位。
- 触发前必须在同一客户端轮次中观察到 PPU 最大利用率 `>=50%`，排除请求尚未开始。
- 触发条件：客户端 `vllm bench serve` 进程活跃，且 16 卡连续两个 1 s 采样点的最大利用率 `<=20%`。
- 每个实验最多触发一次：保留 16 卡利用率、进程列表、代表 Worker 的 `/proc` 状态，对 4 个 Worker 执行有超时的 `eu-stack`，对第 1 个 Worker 补充一次有超时的 `gstack`。
- attach 会扰动本轮；本实验的吞吐、TTFT、TPOT 和 ITL 不能与 baseline 计算收益。
- 停止：首次触发并完成栈采样，或 6 轮均未触发；不扩大轮次。

## 结果

- 6 轮全部完成且请求有效。r1 为慢轮：326.28 output tok/s，最大单次 ITL 6.924 s；r2–r6 为 462.79–466.52 tok/s，最大 ITL 约 0.777 s。attach 之后的时延仅用于诊断。
- 触发逻辑在 r1 中先观察到 PPU 最大利用率 100%，随后连续两秒 16 卡全部 0%；只触发一次。
- 4 个代表 Worker 的主线程全部位于 CPython 用户态路径，符号化分别命中 `PySequence_Tuple`、`_PyEval_EvalFrameDefault`、`dictresize` 和 `_PyUnicode_JoinArray`。
- rank0 的补充 gstack 还命中 `PyObject_Malloc` 和 `_PyObject_GC_NewVar`。这与 fw-003 的 minor faults/RSS 增长一致，支持“Worker 在构建大量 Python tuple/dict/string/object”，而不支持 PCCL/NCCL busy-wait 或设备 kernel 成为该间隔直接原因。
- 当前 GDB 未加载 Python helper，`py-bt` 不可用；C 栈因该 Python 构建的 unwind 信息不完整，尚未得到具体 Python 文件/函数。
- 服务未重启或修改，实验后 health 与“北京” smoke 通过。

## 证据

- `/mnt/nfs/users/jinghao/minimaxM3/20260921-minimax-m3-ppu-e2e/profiling/fw-004-bounded-worker-stack-on-stall`
- `/mnt/nfs/users/jinghao/minimaxM3/20260921-minimax-m3-ppu-e2e/profiling/fw-004-bounded-worker-stack-on-stall/trigger/symbolized-main-threads.json`

## 下一步

用一个独立诊断服务实验通过 `sitecustomize` 为每个 Python worker 注册受控信号的 `faulthandler` Python 栈转储。复用同一有界低利用率触发，命中时仅向代表 Worker 发送一次信号；完成后恢复无诊断环境的服务。
