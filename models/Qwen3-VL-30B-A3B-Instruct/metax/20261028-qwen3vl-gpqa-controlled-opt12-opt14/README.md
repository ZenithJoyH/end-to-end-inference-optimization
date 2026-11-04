# GPQA59.60：Attention版本受控诊断

第一组三角色已完成：旧版B1（PR638+split1）129/198=65.15，当前C1（paged/default0）119/198=60.10，回切旧版R1 129/198=65.15。全部198原生来源、逐题判分、源码与默认采样审计有效，源服务13:40:15已恢复f81/原配置/prefixON并独立核验。B/R总分相同但完整响应0相同，保留采样/批轨迹限制；目前支持Attention版本相关可逆信号，尚未确认Prefill或splits根因。

[第一组结果](optimize/diag-001-controlled-attention.md) · [第二组预冻结方案](optimize/diag-002-factorial-bridges.md) · [结构化状态](optimize/state.yml)

当前第二组diag-002补齐两个正交组合：D1原paged+split1、E1 PR638+default0，各新私有实例GPQA198/C64一次，其他配置和prefixON不变，不跑ERQA/性能。CPU镜像/挂载/source/双来源核验通过；唯一factor2 controller1738426/ticks1147819842于14:04启动并开始绑定原服务1697323的临停。每角色实际native/graph/观察移除/smoke后才正式评测，单finally恢复原f81/source容器全部配置。当前未有D1/E1分数，不能把第一组历史恢复当本次现状。

远端原始证据：/public-flash/jinghao/qwen3-VL/20261028-qwen3vl-gpqa-controlled-opt12-opt14；第二组在factor2子目录。原服务源码不修改、其他服务不动、不提交推送。监控qwen3-vl-gpqa每30分钟报告实际进度。

用户新增GPU6/7并行授权并释放资源后，[diag-003辅助E67](optimize/diag-003-parallel67-auxiliary.md)已独立启动：14:26模型加载，8037/19967/private caches/CPU NUMA1隔离，原D1与同设备E1串行计划保持不变，恢复仍只有原controller负责。E67只额外198题一次，硬件与共享宿主差异明确单列，不冒充同设备单变量。


2026-10-28 15:06后：D1 64.14、E1 65.15通过；辅助E67 61.62失败。全部冻结评测结束，原opt14 f81/default0/prefixON已恢复并独立核验。根因仍未确认，进入CPU最小复现设计；见同一diag002/003和state。无新性能结论或生产变更。
