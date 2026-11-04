# 20260922-p32k-baseline-recovery-27：P32K稳态恢复

## 方向与冻结范围

- 状态：失败/不完整；`framework`，服务已停止。
- 父场景：`P32768/D1024/C64/N128`；恢复里程碑：
  `P32768/D128/C64/N128`。
- 当前组合不变：TP16/BF16/max-seqs64/MBT32768/max-model-len80000/
  FULL_DECODE_ONLY/前缀缓存关闭。
- point26失败证据保持原样，不复制或追认其中轮次为本点结果。

## 恢复契约

fresh服务先C1/C8，然后运行6 warmup+3 measured；warmup 4–6和measured 1–3的
输出吞吐相对极差均须不超过3%，全部请求成功。若再次失败，则停止并标记
`deferred-too-slow/incomplete`，不继续完整D1024。

控制脚本必须设置EXIT cleanup trap；无论启动后哪个步骤失败，都检查并停止当前
任务的vLLM服务。外层启动启用`pipefail`，不得再由`tee`掩盖退出码。

## 产物边界

- 命令根：`commands/p32k-baseline-recovery-27-20260922/`。
- 结果根：`full-scenarios/p32768-d1024-c64-n128/baseline/recovery-27/`。
- 不修改源码、DB或交付脚本，不提交或推送。

## 当前结果

fresh graph服务启动成功，C1与C8分别`1/1`、`8/8`通过。六轮
warmup均为`128/128`请求成功，输出吞吐为：

| 轮次 | output tok/s |
|---:|---:|
| 1 | 36.140520 |
| 2 | 36.192244 |
| 3 | 36.188176 |
| 4 | 36.195081 |
| 5 | 34.992783 |
| 6 | 36.178725 |

冻结窗口4–6的相对极差为`3.323217%`，超过`3%`，因此runner在
warmup门禁后以退出码1停止，没有measured轮次。这个结果不能作为
P32K baseline。`run-record.json` SHA-256为
`904f1c996a0daa2cc064aa126645150e624d3db6c701a90d3e834ee348b18d8d`。

六轮中1–4与6轮都在`36.14–36.20 tok/s`，只有第5轮降到
`34.99 tok/s`；同时第5轮TPOT/ITL/E2E整体变慢，TTFT反而略好。
服务日志只有启动时编译，轮次期间没有新的autotune、编译、OOM、
timeout或traceback。因此证据更支持不同seed的内容/MoE路由工作量
差异或一次性运行扰动，不支持“仍未热身完成”。

EXIT cleanup trap成功执行：没有`cleanup-failed`标记，容器内无目标
vLLM进程，8011关闭。下一步保留本点失败结论，用本项目其他长
prompt稳态恢复已使用的`5%`容差创建独立新契约；不事后修改本点。
