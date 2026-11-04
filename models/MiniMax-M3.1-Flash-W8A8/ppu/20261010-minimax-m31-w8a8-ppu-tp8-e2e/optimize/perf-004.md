# perf-004 opt2 当前服务阶段入口

用户2026-10-13提供最新MiniMax-M3.1-opt2并明确接受当前优化、要求继续。当前8035/nameopt2，TP8/7graph/原11exports，四源码保持FVf924/Plugin011f/FG1e56/engine5e7。原169/198 gate属于旧8025/name，不能rebind；当前新实例最小回归后可做诊断baseline，下一候选在formal前新跑完整198。

mode baseline：已核对结构化当前场景为P4（旧FG P1正式闭环之后切换），现在建立当前FV代码P4 Prefill/Decode/Mixed三个阶段代理；旧P1仓库迁移sentinel失败仍保留，不冒称新FV的四场景验收。6warm+3measure，全轮保留，latewarm3 TPSspread<=5%，测量指标spread<=10%；native错误或未稳态立即incomplete，不选好轮/自动重试。纯Prefill低并发短输出、Decode短输入长输出，记录不同KV/调度残差；Mixed作为最终晋级守护。root用户修改保持，不改env、端口/servedname。

旧op004候选在第二预热轮只完成64、失败64，0测量，原端口服务后来退出；保留native失败，不宣称性能退化或仓库迁移问题。用户CSV三场景全部3轮/128成功，全轮mean TPS3728.56/4060.80/4163.90；相对opt1观察+7.69%/+5.87%/+6.44%。CSV缺当前精确service/client/稳态准入证据，P1缺失；不作为新的正式验收或跨16卡旧base精确收益。

计划plan-031：第一优先当前阶段baseline；第二为smallM MoE非TLE对齐launch压缩；第三为SwiGLU+INT8quant融合但需新数值/成本证据。尚无新production改动或新增收益。

perf004-validation-001：旧最小回归工具硬编码MiniMax-M3.1/8025，在服务名断言处退出，发生在任何模型请求前，属于harness measurement-invalid。当前runtime取证已成功；保留entry01失败日志，生成新服务locator副本后在唯一entry02重新执行同105+2标准，不修改生产源码或放宽数值标准。

测量前最终冻结：PF P4096/D1/C8/N16、Decode P4096/D256/C64/N64、Mixed P4096/D128/C64/N64，各6warm3measure；最后3warm TPSspread<=5%，所有3measure与指标spread<=10%，600秒/轮、阶段控制预算1800秒。初始10warm5草案未执行，选择最终缩减计划发生在结果前。阶段代理均含client/queue/scheduler，Decode包含4096prompt与firsttoken；originalP4D1024/N128和最终4场景仍待正式测量。

当前opt2取证及105+2全部passed，C8/C33/C64 graph迭代下界40/37/36、所有8worker H16/FVINT8命中。当前MF SHA6c363d1f7daa44f1a96b102dbd53be094f4fa3e65f4364a2a94c7deb9e2e322e，minimal SHA f7c7b6fadb3ca7029f5cf6cee337b53fa7854c6b52834ab5813499beb5b309e0；runtime SHA b65325b2d33ba86542f8131b3880e015ca7a15e8e096139949d86ae5ee5e9b02。前置harness问题已解决，当前仍无新的formal分数绑定。

perf004-validation-002：phase01原生dry-run拒绝比较contract的diagnostic scope（只允许formal/performance_only），尚无性能请求/轮。新phase02仅修正比较scope=formal，runner仍diagnostic baseline，未来候选仍要求精度gate；所有workload/6warm3measure/波动/收益阈值保持。保留旧plan，不补写或改变任何已测数据。

三阶段基线已实际launch（all3 native dry-run通过），command SHAaacdc202591ec17dfe7c3a492336f79fd433a50ec392e06bf50f0801caea1df4，contract SHA2523beed06d97f65ecf4141a01476e1cd6dc02cbd339dac4e8038ddbe7667c69。性能采集期间不并行运行PPU8 micro计时，防止主机/设备共享资源干扰。P16/P32并发prompt总量超过435584 KV容量，仅为潜在admission压力；当前log没有显式preempt，不能推定重算是根因。

Prefill P4096/D1/C8/N16全部6warm+3measure原生审查passed，中位totalTPS7103.4477；末3warm spread0.031459%，守护测量波动均通过。review SHA5750425f664c997e45772027973617f1ec0c94a54c4865b799b40eda30946933。reviewv2曾对D1非必需TPOT/ITL=null求mean而报控制异常，v3严格按冻结required_metrics统计，并记录optionalnull；未改原始数据或删轮/守护。

三阶段全部完整6warm3measure+原生单角色审查passed，pipeline exit0。medianTPS PF7103.45、Decode5551.33、Mixed6259.07；各负载D/C/N不同，不能互算阶段加速比或纯设备时间。Decode/Mixed的P99ITL约1139/1140ms、P99TTFT约36711/36709ms；currentfullD1024需要自身Matched测量，smallM只改变query1后段，不能把本缩短Mixed耗时视为全部潜在decode贡献。库源码/服务/根脚本均保持。
