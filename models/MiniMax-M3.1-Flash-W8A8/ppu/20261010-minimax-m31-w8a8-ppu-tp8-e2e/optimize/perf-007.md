# perf-007：opt4 长输入阶段诊断

规划复盘plan-040：用户opt4全部3原始轮总TPS均值P4=3869.11（相对opt3-retry +2.5903%）、P16=4159.04（+0.1245%）、P32=4274.20（基本持平）。仅观察数据，不删除首轮、不用SUMMARY尾两轮替代。当前源码与已测splitK完全一致；用户改name为opt4并重启，rootSHA cd11f0...9d94仍11exports，旧name精度gate不能直接移用。

先fresh baseline-sanity107，再capture/analyze P16 Prefill16384/2/8/8、Decode16384/128/8/8、Mixed16384/64/64/64；各1warm+2nonwarm，仅lastprofile，seed42/temp0，900s/round，期望8rank+frontend。分别从token/query/iteration/graph及实际kernelshape拆分，未知边界保留unknown；profiler duration不计算E2E收益。最近P4 CPU/trace历史不能替代当前P16事实。

当前54次累计KV抢占不能按场景归因；采集前后记录counter差值，检查算子vs容量重算的竞争解释。另8卡忙于其它模型，完全不动。仅当前0..7模型服务精确PID/startticks/family停止/启动，CLI临时profiler配置，根脚本及原11exports与全部源码保持；capture后恢复root配置并fresh107。首个dryrun/实际capture错误即保留证据并恢复，不盲重试。尚无新算子改动或性能增益。

远端：/mnt/nfs/users/jinghao/minimaxM3.1/optimize/20261010-minimax-m31-w8a8-ppu-tp8-e2e/profiles/perf007-opt4-p16-20261015-01；控制：/mnt/nfs/users/jinghao/minimaxM3.1/optimize/20261010-minimax-m31-w8a8-ppu-tp8-e2e/commands/perf007-opt4-control-20261015-01.py，SHA 9f2367f6b373c1d36c2f57c043c3d29fcaac9d858f3bf2306a7ee22e8362d272。

三阶段nativecapture均complete，逐阶段preemptiondelta全部0；Mixed64/64全部成功，原生diagnostic SHA708f029...759c。capturestatus SHA8d558e...1a52。已启动control02恢复root原配置，随后fresh107；Mixed优先analysis核对真实graphM/热点。当前仅观察日志resident约25–26/KV95%，不能由此代替kernelshape证明。

恢复完成：root配置新实例graphcapture完整，105+2通过，verifiedMF a765186...cef4、minimal ed8b9e...f4f2。PF/Decode各8rank+frontend覆盖校验通过；本次8192token Prefill实际非graph，PFgraph0如实保留。旧analysis label字段仍为perf006，路径/原生run/manifest均绑定当前perf007；此元数据errata明确记录。Mixed全rank分析仍运行。

阶段诊断完成：phase-review-02 SHA f6086a...e111，PF/Decode/Mixed每组8rank+frontend通过。Mixed各rank一致32×42/16×31/8×8/4×4/2×2/1×2 graphrows，M16/32覆盖73/89个尾部纯decode-compatible graph；其余Prefill+Decode混合迭代仍包含8192大M，不冒充纯Decode。三组抢占均0；因此容量影响resident/graphshape得到证据，但这组短D64不能排除完整D1024抢占。已有M64 guard漏选小M，进入op014；源码未改，root恢复回归通过。
