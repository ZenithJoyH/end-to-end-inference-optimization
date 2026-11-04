# diag-002：拆分Prefill路由与decode splits

问题关联accdiag-opt14-c64-gpqa-001。用户要求继续定位、其他配置不变，已允许临停本任务opt14并完成后恢复。diag-001 B1/C1/R1全部完成且已恢复，65.15→60.10→65.15构成版本相关回切信号，但Attention文件包含两个因素，不能把任一项或底层vendor bug认定为根因。

## 预冻结新有限实验

本实验不是在原三轮中事后加轮或挑分，而是补齐两个未测的正交组合；各完整198题/C64/strict64一次，全部保留，结束后停止这组：

| 角色 | Prefill | decode | 单因素比较锚点 |
|---|---|---|---|
| D1 | 原paged | 显式split1 | 对C1（原paged/default0）隔离split；对B1/R1（PR638/split1）隔离Prefill |
| E1 | PR638连续KV | 默认split0 | 对C1隔离Prefill；对B1/R1隔离split |

同GPU0,1/TP2、模型权重与tokenizer、四仓其余源码、BF16、8030/qwen3vl-opt14、batch8192/seq64/.91、FULL_AND_PIECEWISE64/prefixON、模型默认T.7/P.8/K20/rep1、无requestseed、原taskseed42/停止词/18000cap及普通smoke/C8准备。复用diag-001已验证不可变镜像1c00be94，两个新私有容器fresh进程/KV；独立响应缓存UUID。原native/正式runner/评分不改；不跑ERQA/性能，不试新splits数值、不改MoE/采样、失败不自动加轮。

D1由已冻结f81原文件仅加native kvcache调用的num_splits=1一行；E1由旧4e12仅删该参数、要求精确等于此前PR638-only文件f49。AST比较剥离这唯一keyword后必须与对应源完全一致，公开vendor API支持已有1/0，禁止新kernel或按题目特化。高风险参数变化使用相同startup native双rank/graph16/观察移除/smoke/C8后完整formal-gate，>=64才签该测量实例gate，不能转给恢复source。

新的远端执行子根：/public-flash/jinghao/qwen3-VL/20261028-qwen3vl-gpqa-controlled-opt12-opt14/factor2，只保存本实验新configs/commands/manifests/logs/roles/results，不覆盖diag-001。准备只做CPU/source/mount/provenance，不临停或发模型请求。源当前为已恢复PID1697323/ticks1147653843、原f81/argv/env/prefixON。执行前重新取证/idle检查；新单控制器finally停止自己的D1/E1及代理，再恢复该原容器原文件/全部参数并核验新PID/source/models200/smokeC8。旧source-restored.json只是阶段1恢复，不能当阶段2现状。继续既有明确临停授权，不影响其他服务；系统盘约14GB，仅复用快照不再commit，创建前保留>=10GB余量，不清理无关缓存/镜像。

## 结论边界与停止条件

结合原B/C/R组成两因素对照，比较每项在另一项固定时的分数、逐题判分和全部原始响应，不相加加速比。默认采样未固定请求seed、批轨迹存在变化，单次新组合的阈值通过/失败不是数学kernel bug或所有输入确定性证明；保持rootcause confidence条件性，不以调低温度或挑问题掩盖失败。

如果两组共同支持split或Prefill因素，先据此缩小下一同前缀/真实算子输入和采样状态诊断；若有交互或不稳定，保留反证，不盲加完整轮次。只有机制/最小复现与修复正式原scope验证完整，才标根因confirmed。本阶段完成先恢复source f81，不自动把通过组合部署到用户生产服务。

状态：CPU preparing，尚未二次临停。继续使用inference-accuracy-diagnosis与formal-gate，原问题gate-blocking，无新增acceptedE2E收益。startup观察沿用diag-001已CPU/硬件验证的同字节observer，均在正式前移除；计数不是独立数值reference。工程归属为既有厂商薄适配参数单因素诊断，遵守A1–A4/B1–B4/C1/F1–F3，不新增算子或永久开关，不提交/推送。

执行前归档CPU准备器：远端parent commands/prepare_factor2.py，SHAfb9a14e9e00ad1507944b78ce0ca13d509df52a037a578c36f08522f2d5b7050，本地临时执行副本/private/tmp/qwen_factor_prepare_20261028.py。只建新隔离容器、变体、正式工具与双来源CPU核验；不临停source或发GPU/模型请求。新controller运行前另记录其SHA与独立有限plan。

## CPU准备终态与执行前冻结

prepared SHA0c81959cb63b713e9351f11a5853b83b0981e2712d8062d984a0fd1b66c44e45，plan SHA16b3523e7bb1c99bef32871cebb194ed13b688b2bb41b732bc3e339ffa037274。唯一新控制器factor2/commands/control.py SHA18d099054365068e044665c0de64624c0643d8b35e3972314a27be8aa84c0291，只支持start/run，不能重跑parent的prepare/controller。D1 Attention SHA2eaec0be03b16ad1d4b5e24851655eea53d0fb90db83a5ccaeff04011dcb3002；E1 SHAf49f4a5b401a5ca66f04f10b27e7b6f186e3efe1c8d214556efb0b1edaf36514。新容器D1/E1同镜像/挂载/source/import/模型tokenizer校验passed，每角色两份GPQA provenance一致且与原198题一致。独立CPU复核生成controller的常量/角色、source guard f81、唯一finally/原配置恢复逻辑和冻结全部artifactSHA通过。准备零模型请求，源未临停，Docker余量13.94GB。

已将命令与SHA归档并沿用用户继续定位/临停恢复明确授权，下一步仅启动该唯一有限controller；source-stop绑定1697323/ticks1147653843且要求原服务idle/source身份精确一致。

## 启动回执

唯一factor2 controller1738426/ticks1147819842，冻结脚本SHA18d099054365068e044665c0de64624c0643d8b35e3972314a27be8aa84c0291；14:04:13 source-stop-started只绑定已核验1697323/ticks1147653843。原第一组controller已退出。当前新模型/正式GPQA待其startup门禁，不沿用旧graph/native证明；本次恢复以factor2/results/source-restored.json为准。监控qwen3-vl-gpqa已更新为第二组唯一控制器及单finally协议。

14:04:31源精确实例已停止，D1新服务77/ticks1147821851开始加载；尚无startup门禁/正式分数，不拿BCR graph/native证明替代。当前无failure，原source仍按本controller临停。案例三阶段schema/identity/文档链接专项校验passed；仓库全量记录检查存在其他案例既有失败，不修改无关记录。


## 终态独立审计执行前归档

CPU-only 脚本 factor2/commands/independent_six_role_audit.py，SHAec0b8077c45d5fb839062d10320c7f73d0e564e628982ff919aa359aa92724a5。只复核既有六角色原生198样本/严格分数/来源/冻结配置、前后源码、逐条上游无采样覆盖及已有gate；输出新的results/independent-six-role-audit.json，不覆盖旧结果、不发模型请求、不签新gate。枚举全部配对与诊断候选doc_id，E67跨设备/资源/轨迹限制保留。


## 当前终态（2026-10-28 15:06后）

同GPU0/1 D1原paged＋split1为127/198=64.1414%，E1 PR638＋default0为129/198=65.1515%，均过64。辅助6/7 E67同E1代码为122/198=61.6162%，有效失败、无gate。三角色均完整198、来源/冻结配置/源码前后/上游无采样覆盖及seed审计通过；独立复核已有D1/E1 gate通过，仅绑定已停止的测量实例。

独立CPU核验 `factor2/results/independent-six-role-audit.json` SHA58f50fd6bcbc6efd9120bb75997f05dedfd26c3d4aeaa7861212fb504f18e28d。六角色全部15对的198doc/arguments一致、完整响应相同数全部0。E1/E67为107两者对、54两者错、22仅E1对、15仅E67对。设备/NUMA/CPU约束/时序不同，不是硬件单变量；D1仍可用全部CPU，隔离GPU/端口/私有缓存不等于证明宿主带宽零干扰。

原串行controller单finally于15:06:38恢复SOURCE opt14：PID1707852/ticks1148172233、f81/原argv/env/cwd/8030/prefixON，回执factor2/results/source-restored.json SHAa04389b01ab18b11e6d3e4eb210748af256ed16c675708689848d43725e60bc8。独立当前collect与恢复身份/源码/模型/tokenizer/版本逐项exact，容器PIDticks和models200实查passed；0额外generation。两个controller退出，D1/E1/E67模型容器均停止，source正常保留；没有把测试通过版本部署到source或转移gate。

## 规划复盘 plan-factorial-aux4-20261028

使用本地inference-optimization-planning，保持accdiag-opt14-c64-gpqa-001 rootcause unconfirmed。补齐组合后不能说只有split0或只有原Prefill导致下降：D1/E1都通过，且同E1代码跨设备辅助失败；未固定请求seed且逐题响应不同，机制和统计不确定性仍存在。原有效低分保留，不自动加完整轮/ERQA/性能，不改采样、MoE、阈值，不做生产修复。

Prefill：PR638条件为单prefill、decoder、seq>=2048、无KV量化；七个C1错而B/R/D/E全对的CPU诊断候选doc21/31/47/91/122/145/170，prompt分别222/241/239/289/308/392/319。不能由短初始prompt排除长输出后的重算或邻居影响，info_once日志也不能绑定题目。Decode：尚无本case同输入QKV/logits/实际noise因果证据；Mixed：批轨迹、无请求seed和并行宿主共享影响尚未排除。未测性能，无累计E2E收益，GPQA耗时不作吞吐。

下一步限CPU按最小doc_id规则选doc21，核对原factory请求、实际路径/缓存与token元数据可得性，设计有限同输入采样窗口；doc21是诊断材料，不得特化生产实现或冒充正式评测。先证明真实tokenIDs/窗口、原始logits和变换前probs/noise捕获可中性执行，再冻结独立有限协议、命令SHA、资源检查和唯一finally恢复。当前尚未启动新GPU观察或完整评测；发现缺映射/实际IDs/路径则记incomplete，不用旧文本重新分词冒充生成IDs。复盘触发为最小复现、设计不足或新的反证。保持原source运行。
