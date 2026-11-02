# 容器僵尸进程清理（维护任务）

用户明确要求清理mx-103/deepseekV4-flash容器僵尸。inventory/指定Host连接已通过。只读检查254个Z，全PPID1，PID1为sleep/infinity、单线程、无SIGCHLD handler、无init reaper；当前18001在清理前已未监听，无存活vLLM worker。其他5个活进程主要既有bash和检查进程，不终止它们，不重启容器或启动模型。

远程用户根/public-flash/jinghao/deepseekV4，复用既有案例根20261022-thinking-gpqa-metax103，新独立子目录zombie-cleanup-20261026-01（读取时不存在，规范路径、owner0/mode0700及14.4TB可用空间已核验），commands/保存控制程序。仅维护进程，不建立新优化点/精度gate。

方案：宿主机有CAP_SYS_PTRACE，Linux x86_64。对严格核实的单线程sleep，用SEIZE/INTERRUPT临时取得寄存器，复用其现有syscall指令，对精确Z子PID执行wait4(pid,NULL,WNOHANG,NULL)，恢复全部通用寄存器并DETACH。无tracee代码/数据内存写入、不替换PID1、不发送退出信号、不修改宿主机ptrace策略。每个目标核PID namespace/PPID/Z/startticks，拒绝存活子进程与PID复用。先在本次创建的临时sleep+2僵尸+1存活子进程验证；测试失败不应用真实容器。

依据：[Linux ptrace手册](https://man7.org/linux/man-pages/man2/ptrace.2.html)、[waitpid手册](https://man7.org/linux/man-pages/man2/waitpid.2.html)。PID1非重启回收的临时控制需要恢复并验证，不能把kill僵尸当成清理。

执行前登记（先创建新子目录与commands，再逐文件SHA校验传输，先仅执行临时验证）：
- commands/reap_sleep.py SHA `17820a82f46ea949a3fbbd946789c4c44e27d08ade03674788ec452e2fd0e69b`
- commands/test_reap_sleep.py SHA `d10ac451fbd4a09dfe266897ad7b63f382125d9019502282c529f718737e9df4`

受控验证已通过：两个僵尸精确回收，另一个存活子进程 guard拒绝且未受影响；测试父sleep恢复原寄存器后继续休眠，测试进程最终全部清理。真实清理执行前登记：commands/clean_container.py SHA `e87629873170b7c4f9bf36bd37d4120cfd300e9a8b39018da4a3f58c23eec513`。精确约束原容器image/hostInitPID/startticks/private PID namespace/单线程sleep；映射并核每个hostPID↔containerPID与Z/PPID/startticks。先定向3个pilot恢复父状态，再回收余量；核所有既存live进程身份、容器StartedAt、源码/launcher SHA、18001原状态。无重启/替换容器，无服务启停/源码变更。

首版在任何真实ptrace前被数量守护拒绝：docker top/cgroup live task列表没有这些Z，故不匹配容器/proc的254。未进行真实回收。只读宿主机/proc复核确认254个Z的PPID均精确目标hostInitPID，全部PID namespace inode匹配，NSpid可逐项映射。v2改为/proc过滤PPID+Z+namespace+双层NSpid+startticks，其他回收和恢复逻辑不变。commands/clean_container_v2.py执行前SHA `40e24b55a87a3a2077f6c5ba4edcccc4b19b5a473cc20ae68adbb851abf06f55`。

## 结果

2026-10-26 22:44:03 Asia/Shanghai（UTC14:44:03）清理通过：**254→0**，先3后251个特定Z子进程，两个批次总控制耗时约0.392秒。全部通用寄存器恢复，PID1仍原sleep/startticks/namespace，TracerPid=0。未重启容器、未终止5个原存活进程、未改源码/launcher。独立后验再次确认0僵尸、PID1正常S休眠及调试已脱离。

- 原始材料：/public-flash/jinghao/deepseekV4/20261022-thinking-gpqa-metax103/zombie-cleanup-20261026-01/，before.json/after.json/pilot.json/remaining.json/test/result.json及commands/，完整进程身份只保留远端，不复制到模型记录。
- 结果：/public-flash/jinghao/deepseekV4/20261022-thinking-gpqa-metax103/zombie-cleanup-20261026-01/result.json，SHA `1f0aa931ecafedf99d710e83ad62a45cbb4d11db59e8610b61f327aac638d7a0`。
- 清理前后18001均未监听，无存活vLLM worker；本维护任务没有启动或停止模型服务。上一个fw005精度/性能结果作为对应已结束实例的历史有效证据保留，不绑定不存在的新实例。
- 限制：只清理当前积累，PID1仍sleep且未安装长期reaper；未来孤儿退出可能再积累。不擅自重启/重建容器、修改初始化程序或增加守护进程。
