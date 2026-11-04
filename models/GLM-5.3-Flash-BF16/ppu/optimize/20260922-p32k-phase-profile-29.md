# 20260922-p32k-phase-profile-29 P32K Prefill/Decode/Mixed 热点定位

- 状态：`complete_service_stopped`
- 分类：`framework`（诊断）
- 父场景：`P32768/D1024/C64/N128`
- 采集里程碑：`P32768/D128/C64/N128`
- profile模式：`capture_then_analyze`

## 优化方向与瓶颈依据

point28已建立当前保留组合的P32K/D128稳态入口基线：
36.174157 output tok/s，P99 TTFT 221.608 s，P99 TPOT 1730.091 ms。
这些端到端指标不能区分Prefill、Decode和Mixed admission干扰，也不能
直接把P16K热点外推到P32K，因此重新采集16-rank trace。

## 采集契约

服务使用与point28相同的TP16/BF16/max64/MBT32768/
FULL_DECODE_ONLY/前缀缓存关闭配置，仅新增torch profiler。先执行
C1/C8最小回归，再完成一轮profiler-off和一轮profiler-on的
P32768/D128/C64/N128。profiler记录shape并gzip输出，不记stack/
flops/memory，最多120个model iteration。

分析使用`execute_new_<new>_cached_<cached>`成对marker：new-only为
Prefill，cached-only为Decode，同时存在为Mixed。inclusive device activity
可以重叠，只用于热点排序，不解释为关键路径时间。profiler-on吞吐
不作为正式性能结论。

## 门禁与停止条件

- 两轮各`128/128`请求成功，C1/C8通过。
- FlagGems DB SHA不变，源码身份与预期dirty集一致。
- 16/16 rank trace新鲜、非空且可解析，Prefill/Decode/Mixed marker齐全。
- 任一rank/阶段缺失、trace无效、DB/源码漂移、请求失败或服务异常则停止。
- 全路径保留EXIT cleanup trap、外层`pipefail`与停服前空闲检查。

## 产物边界

- 命令根：`commands/p32k-phase-profile-29-20260922/`。
- 证据根：`full-scenarios/p32768-d1024-c64-n128/profiling/p32k-d128-maxseq64-retained-29/`。
- 不修改源码、DB或交付脚本，不提交或推送。

## 当前结果

C1/C8分别`1/1`、`8/8`通过。profiler-off与profiler-on两轮均
`128/128`请求成功，输出吞吐分别为36.146355和24.280119 tok/s；
on数字只表示profiler开销。FlagGems DB前后SHA一致，16/16 rank trace
新鲜、非空且可解析。

rank0共获得120个CPU marker和120个device marker：1 Prefill、
63 Mixed、56 Decode。63个Mixed marker全部是
`execute_new_1_cached_{1..63}`，证明MBT32768在P32K下每波只能
admission 1个新请求。

rank0 summed device activity（允许重叠）的主要热点为：

- Prefill：Sparse MLA 27.368%、fused MoE 17.823%、MQA logits
  14.065%、large-M GEMM 10.636%、Ring all-reduce 5.126%；
- Mixed：Sparse MLA 27.086%、fused MoE 17.576%、MQA logits 13.106%、
  large-M GEMM 10.516%、Ring all-reduce 5.592%、KDA `h_o` 4.472%；
- Decode：fused MoE 37.960%、Sparse MLA 7.465%、mHC pre 5.429%、
  two-shot all-reduce 4.989%、reduction 4.983%、MoE align 4.763%。

Prefill/Mixed/Decode的跨rank device activity相对极差分别为
0.329%/0.243%/2.191%，没有单rank拖尾证据。所以首个P32K单变量
选择`max_num_batched_tokens=32768→65536`，直接针对每波1个新请求
的63波Mixed admission；先做容量/短程探针，再决定是否进入长时A/B/R。

控制SSH在profiler-on完成后、`run.sh`写入DB-after/trace manifest之前
`Broken pipe`。原生diagnostic和16个trace已完整落盘，EXIT cleanup也已
停服。后续通过已归档的`resume-after-ssh-drop.sh`在服务停止状态下
补齐DB比对、trace SHA和离线分析，脚本与分析均退出0。

## 外部证据

`/mnt/nfs/users/jinghao/glm5.3-flash/optimize/e2e-opt-20260911/full-scenarios/p32768-d1024-c64-n128/profiling/p32k-d128-maxseq64-retained-29/`

- phase analysis SHA-256：`10418b69ff130faf850a9f97141e2993eb4ac97d610e8128c4d8fd284902c7db`
- runtime evidence SHA-256：`46f4aaf3370c5cd0009044fecd5c80822c2d75c8b7db2c84896ce49a0bf5fa18`
- trace manifest SHA-256：`9961d549b6c864bddb6ee592a37577cebf7feebc7c152555af30d8517d16da15`
- diagnostic SHA-256：`db814bcf5b7011d74d023046d07aad41440b7c6fe60cfc2d52b1fb1b916fd93d`
