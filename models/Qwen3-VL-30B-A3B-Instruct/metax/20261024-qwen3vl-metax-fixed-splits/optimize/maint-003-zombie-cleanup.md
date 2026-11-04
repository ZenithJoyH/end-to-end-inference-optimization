# maint-003：独立验证容器僵尸进程清理

用户要求清理PID228774（Worker_TP）、269935（python3.12）等defunct进程。只读核验二者均位于mx-104独立验证容器`qwen3vl-fixed-splits-mx104-20261024`，共有81个Z进程，均为PID1 `sleep infinity`的直接子进程，当前仅sleep和既有bash存活，无模型/评测任务。当前18977的split1源服务位于另一个容器，保持原状。

复用项目先前维护脚本（原SHA e6856c7ac09396551120a1fd31990e6444cb5685cd03f96b2cf66aa310a744bc），在本案例归档副本并绑定精确容器ID/启动时间/PID1身份。先对临时sleep父进程执行4个僵尸子进程自测，再由空闲PID1执行非阻塞wait4仅回收事先记录的Z子进程，恢复完整通用寄存器并detach；不改代码/栈/信号配置，不终止存活进程，不重启容器或模型。若当前资源/身份/命令/线程/父子状态漂移则拒绝执行。

执行前后核验零僵尸、容器/父进程/既有bash身份保留，以及原split1服务精确PID/启动时间/配置/HTTP健康保持一致。执行结果见下文。所有脚本和回执保留当前远程case，完成后写入本文件。

执行前脚本归档：`commands/prepare_maint003.py` SHA `134740bef467b99c5e13c591d76df66729db646b47d5d814979acf180303a065`；控制脚本 `commands/maint003_run_cleanup.py` SHA `6bcae38c2675a1254f14eafe380659869245fe17b8066eb2ab6d4535f4a5a4e4`。后续准备仅复制旧回收器、增加精确目标保护并记录新SHA；控制脚本按selftest→apply→独立延迟复核顺序执行。

03:20:43 UTC准备完成：目标回收器SHA `6dea31e01f0bd03fa2913e2a73188e34d45548eae736de9da9431681c6d9e907`；绑定容器ID `e99d03ef91b818798790e188bebb548d5ffec9a2adfd8436b80cab05bee7fc1f`、容器启动时间及PID1/命令/线程/启动ticks，要求两个指定僵尸均在记录中且无活动工作负载。

## 完成与复核

2026-10-26 03:21:21 UTC（北京时间11:21）：临时父进程4个僵尸子进程自测通过；独立验证容器的81个僵尸全部回收，81→0，指定PID228774、269935均已消失。容器ID/启动时间、PID1及既有bash会话保持不变，寄存器恢复后PID1睡眠且未被跟踪；未重启容器、未终止存活进程。随后独立再次只读确认零僵尸。

当前源split1服务的进程/启动时间/启动参数/源码及正常helper保持一致，前后快照SHA同为 `9ad39da54777d16736937fcd727ae016ce79413e616ca6a276570f8293314fad`，modelsHTTP200。源服务未重启，未修改推理源码或配置，未触发新的精度/性能测量。

回收原始回执：`results/maint003-zombie-cleanup.json` SHA `1d2aa8df27ee0f91dd2ad6fd1992ced4d29166bb34ef603d5dc713181fdb0a1c`；独立验证回执：`results/maint003-independent-check.json` SHA `b8370a89fd64e64c4ec7a50c5893da5e4c195867a9c858e14a771454fef14a30`。selftest/apply日志均位于本案例logs/maint003-*.log。此次仅处理用户指定PID所在的空闲验证容器，未对运行split1的源容器执行回收，也未安装永久reaper。
