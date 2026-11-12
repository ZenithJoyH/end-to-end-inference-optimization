# acc-006 ERQA超时7200秒，仅续跑剩余36题

- 状态：**completed / accuracy passed**。最终原生ERQA **165/400=41.25% >=40**，0拒答；native和全部400计错口径一致。
- 范围：精度评测续跑，C上限64，输出cap131072；不是性能优化或新的GPQA评测。
- 同案例GPQA：acc-005原生完整198题 **129/198=65.151515% >=64**，独立复核与原gate-check通过。
- 监控已删除，本轮已结束。

## 用户指令与唯一变量

用户明确要求ERQA客户端超时调为7200秒、其他配置不变，继续未完成题且不重复已完成题，每半小时通知。旧父任务已自然结束：364正常原生items，36超时错误；旧native156/364=42.86%，全部400计错39.0。旧输出和分数全部保留。

本次只将实际OpenAI客户端**read timeout从600改为7200秒**；connect5/write600/pool600、SDK max_retries2及原生5次尝试规则不变。采用外部入口client.with_options，不修改原生适配器或推理源码。默认T.7/P.8/K20/repetition1、无requestseed、prefixON、C64、cap131072、messages/images/stops、responsecacheOFF保持。

## 续跑与CPU验证

原生ModelAdapter.process_single_item读取items后先跳过已有ID。将364题原始items复制到独立续跑目录并冻结SHA；原生处理400题时364题只读已有结果，36题才进入原推理路径。外部ID guard、实际body SHA白名单及原SDK MockTransport CPU预检共同约束仅剩余36题。364个缓存分支验证不触发模型调用，36份实际SDK请求与父任务上游SHA一致。

最初CPU校验仅模拟create kwargs，其键序列化与实际SDK wire不同，预检在0模型请求时拒绝；修正为原SDK MockTransport后全部通过，旧日志保留。V1/V2未发送真实续跑流量，最终采用v3；没有放宽数据、参数、阈值或评分。

## 最终结果与证据

| 项目 | 结果 |
|---|---:|
| 保留364题 | 全部原响应、原分数不变；156正确 |
| 仅续跑36题 | 36题全部形成原生结果；9正确 |
| 原生完整ERQA | 165/400=41.25%，0拒答，通过40 |
| 实际HTTP | 48次尝试、36次成功、12次TimeoutError；仅原生SDK重试 |
| 新增GPQA或smoke | 0 |

原生续跑于2026-11-06 **13:37:27**开始、**16:35:57**结束（Asia/Shanghai）。最终独立CPU复核400unique、原filter_rejected零拒答schema、400逐题判分及原生总分；数据400题/630图与评分/适配器源码SHA未变。364题旧items字节SHA保持，续跑结果中的364题响应及判分逐题相等；所有实际请求均在原36题请求白名单且cap131072，无采样/seed覆盖。实际client runtime read7200，其他超时和重试保持。

源qwen3vl容器opt17/8030，GPU0,1 TP2及原PID346908/startticks681351047均保持。父任务、续跑、finally及当前源码/argv/env/cwd/模型/tokenizer/版本指纹逐项相等，modelsHTTP200；所有自有控制器与adapter退出，用户模型仍运行。只读核验没有新增模型请求。

## 结论边界与决定

本次是原生400题续跑，复用364题并重新生成36个先前超时题；不是另一次不间断400题生成，也不是按最好分拼接。旧结果保留，warmcache/no seed的轨迹变化不能单独归因于超时或输出cap。该成绩不证明PR1069、数值路径或所有输入无问题。原GPQA gate仅绑定其实际测量实例/传输契约，没有给续跑或未来服务签发新GPQA gate。

准确率两项均达当前阈值；本次未进行性能评测或PR代码变更，不宣称端到端优化验收。没有自动追加评测、修复或重试的待办。

## 外部证据

远端续跑根目录：`/public-flash/jinghao/qwen3-VL/20261105-qwen3vl-c64-accuracy-mx59-001/full-c64-cap131072-20261106/erqa-resume-timeout7200-20261106`。所有原始响应/日志/配置留在远端。

- `erqa-completed`: `/public-flash/jinghao/qwen3-VL/20261105-qwen3vl-c64-accuracy-mx59-001/full-c64-cap131072-20261106/erqa-resume-timeout7200-20261106/results/erqa-completed.json`，SHA `ffde68cb34323f1bdcfd871181fa80880892affd2ffe1840cb611ca1cb4341d5`。
- `completed`: `/public-flash/jinghao/qwen3-VL/20261105-qwen3vl-c64-accuracy-mx59-001/full-c64-cap131072-20261106/erqa-resume-timeout7200-20261106/results/completed.json`，SHA `e784c9f206eee88312d8838d4752e5da3c9602f1ca6cf35a8879aea8f7d2c6c2`。
- `user-service-final`: `/public-flash/jinghao/qwen3-VL/20261105-qwen3vl-c64-accuracy-mx59-001/full-c64-cap131072-20261106/erqa-resume-timeout7200-20261106/results/user-service-final.json`，SHA `579824a2e810b8e53803ee35d2f5c8485e41ece71fee4bd34a3a0d4b94669403`。
- `sampling-and-skip-audit`: `/public-flash/jinghao/qwen3-VL/20261105-qwen3vl-c64-accuracy-mx59-001/full-c64-cap131072-20261106/erqa-resume-timeout7200-20261106/results/sampling-and-skip-audit.json`，SHA `9a84f5ffb9f3deb0a04d5c784605ae88451d85f8409de9c4d6e24c8478f91f20`。
- `native-run-completed`: `/public-flash/jinghao/qwen3-VL/20261105-qwen3vl-c64-accuracy-mx59-001/full-c64-cap131072-20261106/erqa-resume-timeout7200-20261106/results/native-run-completed.json`，SHA `c5a6fe8cd5090f972ab46a3196f0f6a67f4f227b62301e0e48a68ff22fe76f67`。
- 独立最终审计：`/public-flash/jinghao/qwen3-VL/20261105-qwen3vl-c64-accuracy-mx59-001/full-c64-cap131072-20261106/erqa-resume-timeout7200-20261106/results/independent-final-audit.json`，SHA `3e459f53ce19c61a789fa774e8212b740e77d5a6606ce61dd866ebdb865b423f`。

最终入口脚本：

- `commands/native_resume_v3.py`: `ebf2216b180868ee28c43f88f1efc46d81ea72e2aedd933d120808c189768f8e`。
- `commands/controller_v3.py`: `7f152b4bee0f4ab9b34cd21a2d2c434ba9549a830e509f4ccc5e9b2c6159fe30`。
- `commands/start_v3.py`: `dbdd0723f366db00f50648cc41a065d296e429fb7d43005e107560a8659ba5ed`。
- `commands/finish_prepare_v3.py`: `b50812e614b0f3191138dceca6cb944d5cfd0ae60f23374682e46458c1246d3a`。
- `commands/default_sampling_proxy.py`: `01777378dd1e266d194d6914957e0690f9a7897627da511c37be55e7a78219fa`。
- `commands/independent_final_audit.py`: `61edcfe9eb09481e7d16dc3e818e57579e1da4fe1aee8152cbf4f2fa24e3a227`。

准备契约SHA `44bf19a8140ee7bda1b01422121728150ed3e8ffc48945cc8dc04f8572ea53ff`；36请求SHA清单 `435f1dc2ddfba5bf55e84426b60aefaf8b662081af5c0c8e96e705decc7fea9b`；CPU预检SHA `320b27def2aea52fea1827da43fa4795fe78b754800adc405ae6cac59e774766`。此前未执行版本和CPU事件的完整指纹保存在同state及远端commands/logs，未覆盖旧证据。
