# LibTuner 参数引用生命周期修复

2026-10-28；用户授权“那你来处理下这个问题吧”。分类framework/host资源生命周期（实现位于FlagGems公共调优基础设施）。依据 erqa-tuner-retention-001 实际清理每rank释放244093440B；不把共享KV计为泄漏，不宣称ERQA OOM唯一根因。

目标B私有 /opt/FlagGems-master-20261027-001 @a456722a；修复普通run自动强引用args/meta和异常残留nargs。新增显式capture_benchmark_context作用域供离线executor使用；benchmark_config显式args/meta保持，嵌套和异常恢复；kernel/config/cache选择/benchmark协议不变。保护Plugin/vLLM/FGV/MoE/GDN/shortlist及原GPU4/5 TP2、0.9、prefix-on、argv/env。

远端CASE/operator/libtuner-context-lifetime-001，命令先CASE/commands唯一归档SHA。先静态/CPU生命周期与现有cache/benchmark测试；服务空闲且精确核验1192153/start1151143236后停止，保存原文件再应用。GPU实际LibTuner正常/显式benchmark/两次新输入graph replay；原参数重启，C8两轮16条+冻结官方ERQA中16图样本所在连续8题，最多24模型请求，零重试，保留raw。小回归不等于全量精度/ERQA400无OOM，不签gate、不自动性能。失败保留并精确回退源和服务。

当前准备中，尚未修改远端生产源码/停止服务。

## 完成结果（2026-10-29 北京时间）

已永久应用到当前B私有FlagGems源码，并按原参数重启：API1204672/start1151443227，8020，GPU4/5，TP2，显存利用率0.9，prefix-on；无观察器/新增环境开关。仅两处生产源码变化：`src/flag_gems/utils/libentry.py` 与 `src/flag_gems/flagtune/offline/runtime/executor.py`；原6850源码清单逐项校验，其余全部一致。

- 普通run不再保存benchmark参数；nargs在finally清理，包括异常退出。
- 显式`capture_benchmark_context()`仅在调用方指定作用域内保留，嵌套恢复，退出自动释放。离线executor已接入该作用域；`benchmark_config(args=...,meta=...)`继续可用。不使用环境变量关闭调优器。
- 独立AST比较确认run的kernel、配置选择、cache逻辑与原版一致（仅移除引用赋值并增加生命周期包装）。
- CPU15项通过：正常/异常释放、嵌套捕获作用域、现有cache/protocol/离线worker接口。
- FP32/BF16真实GPU2项通过：底层view释放、显式benchmark、capture和两次更新输入/清哨兵后的graph replay，逐位数值一致。
- 实际公开`flag_gems.mul`：BF16非连续[2,65536,8,36]，与torch参考逐位一致；调用方释放后231211008B（220.5MiB）全部释放，allocated从231211008到0，tuner无保留参数。此为隔离算子进程证据，不冒称生产服务净空闲显存增加同样数值；服务KV规划可能使用已释放容量。
- 原服务两轮C8文本16/16通过；原官方ERQA请求选取包含单题16图的连续8题，8/8 HTTP200；共24条零重试、无OOM。只最小回归，不是全400精度或C64无OOM保证。服务graph capture与两轮C8>=2输出token给出replay下界2，非直接设备counter。

保留测试错误：cpu-tests-001为离线worker替身未模拟新显式捕获（14pass/1fail），修正替身后002为15pass；gpu-tests-001的显式低层meta漏Triton必需warmup=False（2fail），修正测试参数后002为2pass；生产修复代码未因这些测试错误改变。上传首次SSH长命令被断开，确认远端目录未创建后改stdin传输。所有失败/旧候选/回执保留。

证据根：`/public-flash/jinghao/qwen3.6-35B/20261022-qwen36-35b-mx104-stack-regression/operator/libtuner-context-lifetime-001`。
- 最终独立verification.json SHA `1cdf88f2e40e42e05e80f4a0ff50fa4934c711fae3b8986d02a33a4bc066667b`。
- 最终patch-plan-004.json SHA `21fc5a0acd6a0e7ce54e85b04733b4a8d542cfd8df572711df08709e0e0d654c`；候选、原文件backup与source.patch同目录。
- libentry SHA `b639a0fa1aa0495ccb2a9ffc7327d780933f18c3601f858f2003bcc71dba4e51`；executor SHA `1ba36405d31638944602ff1878e05ce062c244a74ff234e5fdc424adec54d468`。
- commands/libtuner-lifetime-control-001..004、所有step.command.json均先归档SHA；最终控制004绑定plan004，支持精确rollback→launch-restored，但未执行回退。
- 独立入口commands/libtuner-lifetime-independent-002.py SHA `0a9965a0711a2e86b9f0337f5bf4d2a0711f7a6980a1596f86a60d6f885f1286`，原生exit0；独立检查0模型请求。
- continuation备份后CAS：`ba2eaf884364937cf0d7495595345cc679c4198da994e4f0b165181d84369ab9` → `2ede77cc94e0867d48471e7e6396fc34adfa8ed15a17430628e063c4dec0b3f4`。

保留候选；无新formal gate、未自动全量GPQA/ERQA、未自动性能、无提交推送。旧GPQA159及ERQA partial/OOM仍属历史实例，不能绑定到新服务。不宣称原OOM唯一根因已消除。当前无活动监控。
