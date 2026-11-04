# fw-002：增加 KV 预算，避免 P64K/D1K 抢占重算

## 2026-10-16 opt4 启动核验

用户提供`qwen3vl-opt4`后进行了只读诊断。当前同一独立容器被用户重新启动为`qwen3vl-opt4`/8111、GPU0/1，原18431已不监听。实际进程参数和`/public-flash/jinghao/qwen3-VL/start-model.sh:21`均为`--gpu-memory-utilization 0.90`；本次`service.log`的09:36:57启动记录显示KV529808 tokens，低于八条完整P64K/D1K的532480。此前验证的0.91/KV543712配置没有在opt4中启用。

opt4在核验时有两轮已完成的原始P64K结果68.25/68.59 token/s，均128成功，第三轮benchmark仍运行；尚无最终SUMMARY，不把这些数据签发为正式稳态比较。当前进程累计抢占指标非零，但包含其他场景及在途轮次，不归为单个P64K轮次计数。

Plugin的JSON、adapter和配套库源码哈希与op003一致，标准导入解析仍指向私有workspace；未向在途worker注入取证，不宣称直接观测其缓存。当前缺失的是KV启动配置，不是JSON迁移本身产生的新收益。审计未改启动文件、源码、服务或benchmark。

待用户本轮结束后，可将上述第21行改为0.91并重启其服务，再核验实际KV至少532480；新的性能轮次应进入新结果目录，不能混入当前0.90的opt4数据。审计回执：`/public-flash/jinghao/qwen3-VL/20261015-qwen3vl-metax-p64k-opt3/results/opt4-startup-audit-20261016.json`，SHA256 `0c5c8259f026b23a3956c38b29d53ca5b33ade31b8929db1a75310306151e6cc`。

## 此前受控验证

原 P65536/D1024/C64/N128 的同设备 B/C/R 确认通过：输出吞吐 68.772 → 76.279 → 68.657 token/s，候选相对基线 +10.92%。仅将 gpu_memory_utilization 从 0.90 改为 0.91，保留 max_num_seqs=64、graph capture ceiling=64 和所有 FlagGems 选择。候选已留在独立容器；源服务没有回写。

## 原因与改动

完整原场景三服务启动 KV 容量分别为 529824/543712/529808 token。8 条请求走完 P65536+D1024 需 532480 token，原 0.90 容量略低于此值，0.91 多出 11232 token。当前 vLLM 默认 scheduler_reserve_full_isl=True，但仅为已知输入预留空间，没有提前预留未来 max_tokens。scheduler.py:1107–1128 抢占时释放 KV、将 num_computed_tokens 清零并重新排队；本配置关闭 prefix cache，因而会重复 Prefill。

每卡每 token KV 为 48 layers × 2(K/V) × 2 KV heads/rank × 128 × 2 bytes = 48 KiB。C8 milestone 原容量差 2672 token，即 125.25 MiB/卡；此前重复乘 2 的估算已在执行前更正。所有容量结论以启动实测为准。

## 冻结契约与结果

性能 Skill：targeted/performance_only。先做 P65536/D1024/C8/N8：B/C/R 各 3warm+3measure，中位吞吐 66.680253/75.796377/67.059475，+13.6714%，全成功，抢占增量 6/0/6（各含六轮）。该收益仅属于 milestone，未加到原目标收益。

原目标每 role 使用一个新服务，先 C8/N8 的 1warm+2measure 三轮全部进入原生稳态检查，要求精确 tokens、全部成功、TPS spread≤10%；然后原 C64/N128 执行 1 个声明预热轮和 1 个测量轮。所有原始轮次保留，主比较只用声明的测量轮，各完整轮均128/128成功并核验精确token总量。冻结门槛：吞吐至少+5%，P99 TTFT/TPOT回退≤5%、ITL≤10%，B/R TPS 漂移≤10%。

| 指标 | 基线 | 候选 | 回退 | 候选相对基线变化 |
|---|---:|---:|---:|---:|
| 输出吞吐 token/s | 68.772 | 76.279 | 68.657 | +10.92% |
| P99 TTFT 秒 | 917.728 | 812.556 | 919.620 | -11.46% |
| P99 TPOT ms | 115.608 | 96.524 | 115.469 | -16.51% |
| P99 ITL ms | 1548.425 | 1559.635 | 1554.231 | +0.72% |

原目标各 role 预热+测量两轮的抢占增量为 36/0/36，每 role 合计输入 16777216、输出 262144 token；这些计数排除了 C8 准备及健康请求，不能说成单个测量轮的计数。原生比较 passed、issues=[]，B/R TPS 漂移 0.167%。

## 隔离、正确性与保留

独立容器 qwen3vl-p64k-opt-20261015、GPU0/1、端口18431，镜像来源和完全相同挂载门禁 passed。每 role 完成健康输出检查、两 rank graph capture 与重复 replay，边界观察 hook 已恢复。实际 Attention 仍为 vendor.metax，MoE 为 FlagGems-vllm fused_experts_impl；算子选择、黑名单、四仓库代码、MoE JSON、sort int32 均保持 opt3 状态。没有修改 vLLM。

源保护复查通过：四源码树、MoE JSON 和 sort SHA 与初始快照一致；源容器 qwen3vl-flaggems-e2e-20261013 的端口8000/GPU4,5未停止或重启。仅在原目标比较通过后，以相同源码与启动配置新建 retained 服务并重新检查健康/graph/稳定身份。性能数字属于此前受控候选实例，新 retained 实例只做交付健康验证：16请求/C8成功，GPU0/1各委托原始graph replay16次，观察hook全部恢复，KV543712 tokens，served-model-name=qwen3vl-p64k-opt3。

回退本优化只需在本独立服务下次启动时将 --gpu-memory-utilization 0.91 改回 0.90；不需回退源码或用户 JSON。PR readiness：本点只有启动配置变化，无新增 Plugin/算子补丁；继承的 opt3 改动不在此重新声明 PR ready。

## 结论边界与经验

这是原目标的有限 B/C/R 性能确认，每 role 一个测量轮，另有完整预热及重复 C8 生命周期实验，未测原目标长期方差。用户已明确暂缓正式精度，不签发精度 gate，也不宣称四场景最终验收。TTFT包含排队/调度，不能当纯设备 Prefill。

cap8/graph8 的 fw001 仅+0.3369%，已回退；三阶段 trace 中 Attention 约65%是累计 kernel 活动，不能直接等同关键路径或收益。本轮先解决已证实的重复计算浪费，没有叠加新 kernel；不将旧 P1K sort 收益、C8 收益与本轮相加。单案例 performance_only 证据不足以修订全局 SOP。

## 控制与原生证据

初始 W0 计划在 dryrun、任何流量前被原生工具拒绝；前瞻性改为当前 W1/M1，没有修改公共工具。长 SSH 断开后原控制及基准持续运行，只读 pipe bridge接管日志，无信号、服务/客户端重启或测量重跑。弃用计划、准备修复和执行命令 SHA 保留于 state.yml 与远端 commands，原始证据完整保留。

远端根目录：`/public-flash/jinghao/qwen3-VL/20261015-qwen3vl-metax-p64k-opt3`。原生 run-record 的路径及 SHA 见 comparison 的 runs；当前 retained manifest 路径和 SHA 见 retained 回执。

- `/public-flash/jinghao/qwen3-VL/20261015-qwen3vl-metax-p64k-opt3/results/fw002full-comparison.json` SHA256 `d71f76aa21853f75fa756727a1ff5ae63c2749501c0b80b58275ea1b5a4a127a`
- `/public-flash/jinghao/qwen3-VL/20261015-qwen3vl-metax-p64k-opt3/results/fw002full-execution.json` SHA256 `73ad6856ca7361ddab661251227411386e5c0d97042c3a5ea2c291d10a36db0d`
- `/public-flash/jinghao/qwen3-VL/20261015-qwen3vl-metax-p64k-opt3/results/fw002full-preparation-v2.json` SHA256 `2d7d106282e62ee74d0a257c9ff56e11ab38c02147b672053c72120a168f8204`
- `/public-flash/jinghao/qwen3-VL/20261015-qwen3vl-metax-p64k-opt3/results/fw002full-baseline-target-counter-delta.json` SHA256 `b62c72398d9ef4a6581cd9156b045456f6bba99cbd05b5496d5f812cd4112af1`
- `/public-flash/jinghao/qwen3-VL/20261015-qwen3vl-metax-p64k-opt3/results/fw002full-candidate-target-counter-delta.json` SHA256 `0c4466e3bc06396cc586f12d638431951eec49a7b16c12b4ef0b349a44a4ccc3`
- `/public-flash/jinghao/qwen3-VL/20261015-qwen3vl-metax-p64k-opt3/results/fw002full-revert-target-counter-delta.json` SHA256 `b62c72398d9ef4a6581cd9156b045456f6bba99cbd05b5496d5f812cd4112af1`
- `/public-flash/jinghao/qwen3-VL/20261015-qwen3vl-metax-p64k-opt3/results/fw002full-baseline-steady-admission.json` SHA256 `31bee4c10be71cfc631d20cd34a67ea89bc110da4eb4ef0219f164a78b976999`
- `/public-flash/jinghao/qwen3-VL/20261015-qwen3vl-metax-p64k-opt3/results/fw002full-candidate-steady-admission.json` SHA256 `4f82888516f2b102a5a69693a06473a7cf6a3ac04fe8cd0eaf80875b799eb658`
- `/public-flash/jinghao/qwen3-VL/20261015-qwen3vl-metax-p64k-opt3/results/fw002full-revert-steady-admission.json` SHA256 `f32d14a28d3901c7a7f16c7cca4bffd6e824c0f1c0fbe7b1b2effdc64e0f202a`
- `/public-flash/jinghao/qwen3-VL/20261015-qwen3vl-metax-p64k-opt3/results/fw002full-retained.json` SHA256 `42a328bdd167717ee26f1016c295be5fd7e6c18264e83c1df58728e2fb1cf355`
- `/public-flash/jinghao/qwen3-VL/20261015-qwen3vl-metax-p64k-opt3/results/source-protection-recheck.json` SHA256 `348afa9b95e68444ff6e15292c8de16a5623dd483b5448e570693fc88830b9a3`
- `/public-flash/jinghao/qwen3-VL/20261015-qwen3vl-metax-p64k-opt3/results/fw002full-log-bridge-complete.json` SHA256 `73241b14c76f3e456fb1073be5b67431a7a840434469a2af6b6bfc28d1043501`

保留实例健康回执：`/public-flash/jinghao/qwen3-VL/20261015-qwen3vl-metax-p64k-opt3/results/fw002full-retained-health.json` SHA256 `905221e3f2ff4b294b9928a89a46666bc4247561c8c8ed7dadfe1639baa40c78`。
