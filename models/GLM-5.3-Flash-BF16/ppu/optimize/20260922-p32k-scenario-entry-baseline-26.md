# 20260922-p32k-scenario-entry-baseline-26：P32K入口里程碑

## 场景与契约

- 状态：`failed/incomplete`；转入 baseline-recovery，服务已停止。
- 正式父场景：`P32768/D1024/C64/N128`；入口里程碑：
  `P32768/D128/C64/N128`。
- 当前组合：TP16/BF16/max-seqs64/MBT32768/max-model-len80000/
  FULL_DECODE_ONLY/前缀缓存关闭，以及此前保留的FlagGems-vllm小M/M64配置。
- 本点只建立当前组合baseline，不引入候选变量，不修改交付脚本或源码。

## 首个可证伪实验

fresh graph服务先完成C1/C8最小回归，再运行3轮warmup+3轮measured。全部请求必须
成功，warmup最后3轮和measured输出吞吐相对极差均不超过3%；完整记录TTFT、TPOT、
ITL、E2E、请求/输出/总token吞吐。若在诊断时间预算内无法完成、OOM、graph失败、
服务退出或离散超限，则停止客户端并进入P32K baseline-recovery，不把D128结果冒充
D1024正式baseline。

里程碑通过后再评估完整`P32768/D1024/C64/N128`的预计时长和资源；它只是进入
P32K优化的可比起点，不是四场景最终验收。

## 产物边界

- 命令根：`commands/p32k-scenario-entry-26-20260922/`。
- 结果根：`full-scenarios/p32768-d1024-c64-n128/baseline/entry-26/`。
- 过程脚本仅在`/private/tmp`生成并归档，不写项目`scripts/`。

## 当前结果

fresh服务成功启动，FULL_DECODE_ONLY graph capture和replay完成；C1 1/1、C8 8/8
通过。三个warmup均128/128请求成功，但输出吞吐为
33.036130/36.177890/36.173421 tok/s，相对极差8.6853%，超过冻结3%门槛；
runner正确标记`failed`并未运行measured，因此本点不能作为P32K baseline。

后两轮只相差约0.012%，证据指向首轮冷态，进入独立baseline-recovery而不追认
本次通过。原run-record SHA256为
`f6e783274410b23624a3c5e7ea1ba7282c78b4d030d7dce09adfe1232712341f`；
C1/C8 SHA256为`b85715585f45af173fa846a0fba7679b4245b1d8c23a6deddc2a19761fe1a454`、
`24a1f2d5955dfe63402d685941b8e13e338aa2ab00213ebfbf2dfaa76771bacc`。

控制面还暴露一个独立问题：外层`ssh 'orchestrate 2>&1 | tee ...'`未开启
`pipefail`，掩盖了orchestrate非零退出并跳过后续stop。发现后已手动执行冻结的
`stop.sh`，服务于`2026-09-22T15:20:55+08:00`停止，8011和worker均关闭。
baseline-recovery将增加EXIT cleanup trap并用pipefail启动，避免复发。
