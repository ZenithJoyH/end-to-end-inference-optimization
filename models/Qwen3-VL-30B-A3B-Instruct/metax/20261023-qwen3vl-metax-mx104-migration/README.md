# Qwen3-VL / MetaX：mx-104 迁移与后续验证

最新[op-003](optimize/op-003-metax-fla-pr638.md)已按用户要求将PR638长单请求prefill连续KV路由应用到当前优化容器，仅改MetaX flash_attn.py，保留decode split1/采样/gems-opt/MoE。28项CPU/mock与源码后验通过，GPU/graph/完整精度/性能未测；现有用户opt11服务未重启，补丁等待下次重启生效。现场实际为9999/CUDA0,1/prefixOFF，与下述历史18977/GPU4,5/prefixON不同，不混用实例或门禁。

最新[僵尸清理维护](optimize/maint-003-current-container-zombies.md)已将当前容器138个Z全部回收至0，PID1/Bash和容器身份保持不变。此维护开始时模型服务已未运行，未启动或重启；下述服务运行验证属于此前仓库安装阶段。标准FlagGems-vllm安装保留。

2026-10-26当前安装状态：[env-002仓库整理](optimize/env-002-consolidate-flaggems-vllm.md)已完成；优化容器内当前FlagGems-vllm代码直接安装到 `/workspace/FlagGems-vllm`（模型Python3.12），不再依赖PYTHONPATH覆盖。旧实验副本与旧Plugin备份已校验归档后删除，四个所需仓库保留；当前split1/prefixON/GPU4,5/18977服务graph16/C8通过。下述迁移性能/精度数据仍属于其历史测量实例，没有本次新分数或性能复测。

迁移与本轮受控对照已完成。容器 `qwen3vl-pr943-split1-mx104-20261023` 位于 mx-104，物理 GPU4/5、TP2、端口18977，served model `qwen3vl-pr977`。已恢复原 split1 与原 helper，prefix cache ON，采样、gems-opt、MoE及其他模型配置保持；恢复后两rank graph capture/至少16次replay、C8和health均通过。

ERQA400通过阈值40：原生182/398=45.73，2条超时拒答按全部400计错后为45.50。分数仍绑定原mx104测量实例；未导入mx59的GPQA gate，也未签发新Host GPQA gate或正式验收。

两组独立 split0→1→0 对照共180轮，12轮固定预热后保留全部3测量，原生SHA、逐条长度、成功数及六实例前后源码一致性均通过。聚合为每进程三轮中位数再取两个进程中位数：

| 场景 | split0输出 token/s | split1输出 token/s | split0总 token/s | split1总 token/s | 吞吐变化 | mean TPOT变化 |
|---|---:|---:|---:|---:|---:|---:|
| P1024/D1024/C64/N128 |1599.35|1417.58|3198.70|2835.17|-11.37%|+13.33%|
| P65536/D128/C8/N16（缩减长KV） |13.96198|8.61427|7162.50|4419.12|-38.30%|+85.27%|

冻结比较结果为 **failed：有效性能回退**。回切split0的输出聚合漂移分别+0.04656%/-0.08280%，波动与独立重复门禁通过。TTFT/TPOT是客户端代理，未据此宣称纯设备阶段归因。完整P64K/D1K/C64/N128尚未扩大；下一步需为扩大范围冻结新契约和匹配基线，不能外推缩减数字。

历史5/W12预热不稳、SC64客户端cwd遮蔽、CWD64原生输入多1token均保留，未混入本次测量；采样M1–64完整准备及仅按输入有效性预检的seed1042使本轮可复现完成。没有修改算子/编译器来修复这些测量准备问题。

- [baseline](baseline/README.md)
- [完整实验记录与复盘](optimize/env-001-migrate-mx104.md)
- [optimize](optimize/README.md)
- [acceptance（未完成正式验收）](acceptance/README.md)

远端原始证据：`/public-flash/jinghao/qwen3-VL/20261023-qwen3vl-metax-mx104-migration`。最终比较 `results/performance-iv64-comparison.json`，恢复 `results/restored-iv64.json`；准确SHA与运行身份见state。控制器已退出，本轮监控已停用，split1服务保留。代码未提交或推送，生产9999与其他服务未操作。
