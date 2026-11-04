# 20261018-p32k-phase-refresh-39 当前服务的阶段基线与候选重排

- 状态：基线完成；方向：算子/框架调度诊断入口；父场景 `p32768-d1024-c64-n128`。
- 使用 `inference-performance-evaluation/baseline` 与 `inference-optimization-planning`。沿用已有独立优化容器，属于同一案例的继续工作。

## 优化方向与瓶颈依据

用户在认可补跑后173/198（87.37%≥86%）后要求继续优化，重点算子与框架调度。当前MBT32768/maxseq64/TP16保持，先建立当前服务的Prefill/Decode/Mixed视图。点36真实命中的align候选仅有+0.0822% Mixed收益；点37阈值8192没有稳定measured结果，不能重复引用其warmup为收益。Sparse MLA/MQA/MoE和准入串行化是待验证方向。

## 优化内容与适用边界

本点不改模型代码，先用维护版公共runner测三个milestone：Prefill P32768/D2/C16/N16、Decode P1024/D512/C64/N64、Mixed P32768/D128/C64/N64。各2轮warmup+2轮measured；warmup末2轮output throughput相对极差≤5%才准入，单轮timeout1800秒，总诊断预算3600秒。预热和准入后的所有轮均保留。主指标output throughput，后续候选以+3%为晋级条件，P99 TTFT/TPOT/ITL各守护≤5%回退。

三个milestone的长度/请求量与正式D1024/N128不同，不计算跨workload加速比。TTFT/TPOT只作含网络/排队/调度成本的阶段代理；需要进一步归因再采trace。MBT不是本轮主要候选。

## 正确性与路径命中

当前服务身份`PPU-13:glm5.3-flash-opt-20260911:2134064:500189302`，实际vLLM来自site-packages（0.24.0+empty）。Plugin@95b04f7、FlagGems@9c9bff3、FlagGems-vllm@f7443e7含既有未提交候选；源码内容与本日精度时相同。用户认可的补充汇总精度仅支持当前组合，不伪造新的原生全量gate；本轮为performance-only研究，正式性能验收另补工具所需绑定。新改动仍做最小正确性回归。

## 性能效果

12轮全部完成：各场景2轮warmup、2轮measured；原生校验有效、输入前后校验通过。三个场景warmup相对极差依次1.5626%、2.8696%、0.0848%，均满足≤5%。下表为全部measured轮的中位数，延迟是客户端代理，不是纯设备时间。

| 阶段与milestone | 输入吞吐 token/s | 输出吞吐 token/s | P99 TTFT ms | P99 TPOT ms | P99 ITL ms | measured吞吐极差 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Prefill P32768/D2/C16/N16 | 9539.923 | 0.582271 | 54913.534 | 3425.448 | 3425.448 | 0.0291% |
| Decode P1024/D512/C64/N64 | 2711.510 | 1355.755 | 6360.426 | 44.453 | 36.184 | 4.3723% |
| Mixed P32768/D128/C64/N64 | 9220.552 | 36.017783 | 222632.067 | 1712.170 | 3497.820 | 0.00417% |

measured分别32/128/128请求，全部成功。Decode两轮输出吞吐1385.394和1326.116均保留，没有挑选快轮。长输入Mixed的TTFT与ITL明显含排队和Prefill干扰；本次无trace，不能进一步归因为纯设备算子时间。没有候选加速比，也不代表正式D1024/N128验收。

## 决定、风险与回退

阶段基线保留。点40设备微基准已完成但暂不安装；点41正执行独立Prefill A/B/R，之后以其结果决定是否晋级Mixed。无显著潜力或必须改vLLM源码的方向停止；不提交或推送。

## 外部证据

远端任务目录：`/mnt/nfs/users/jinghao/glm5.3-flash/optimize/e2e-opt-20260911/resume-20261018-point39`。执行脚本`commands/control.py`，配置`plan.json`，运行身份`runtime-before.json`/`service-before.json`，原始结果`results/`。

`measure.exit=0`；`results/phase-refresh39-baseline01/run-record.json` SHA `905023376ddeeb565ff45dee3aa97fb8e2f776226a0275e6b5f850a32cc515f5`。12轮raw、validation与输出文件SHA已核对。该实例在点41测试开始后正常停止，当前临时测试实例身份见点41，不将旧实例绑定沿用为新gate。
