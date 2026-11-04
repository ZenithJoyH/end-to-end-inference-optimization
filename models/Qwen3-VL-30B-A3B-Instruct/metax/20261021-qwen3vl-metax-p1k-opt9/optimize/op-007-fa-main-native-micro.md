# op-007：main.py 与沐曦原生 Attention microbenchmark

- 状态：complete-negative-for-main；2026-10-21 用户明确要求测量两者性能。
- 范围：独立算子、单卡每rank形状；不是服务性能Skill运行，不签发模型精度或四场景性能gate。
- 方法：`skills/key-operator-analysis/SKILL.md` 的算子正确性与microbenchmark方法。
- 容器：复用本案例已经隔离的 `qwen3vl-p1k-opt9-20261021`，不使用源适配容器承载测量。
- Host：mx-59；设备：物理GPU2（当前无计算进程）；GPU6/7现有用户服务不变。
- 独立镜像与挂载：当前优化镜像仍为749601f9，与已有verified谱系回执相同；源/优化两容器目录挂载Source、Destination、RW、Propagation逐项一致。

## 优化方向与瓶颈依据

比较当前未修改的 `/public-flash/jinghao/qwen3-VL/main.py` 与容器安装的 `flash_attn` 原生实现。候选SHA256为 `e2f78d30268caab7656193e070463eaab1271b9fac35c7ed57ffd4ef20cca642`；原生接口文件SHA256为 `a0ce682debda2e3b0457d3716e3c4bdc905d7d759238800494a5619f5a1d37c6`。原实现已有Split-KV，不能从候选源码机制推导收益。

## 测量前冻结的契约

Q16/KV2/D128、BF16、causal、scale=1/sqrt(128)，无ALiBi/softcap/window/dropout；物理page16、随机置换页表，标准连续Q。Decode比较native `flash_attn_with_kvcache` 与候选 `run`，Prefill比较native `flash_attn_varlen_func` 与候选 `run`。元数据预生成；两者都只读既有KV，不包含KV append、RoPE、模型层、TP通信、网络或调度。

覆盖Decode B1/8/32/64 × KV1024/2048/4096；Prefill B1/8×Q1024及B1/2×Q4096；另有ragged和非对齐正确性哨兵。父目标P1024/D1024/C64/N128；KV1K/2K覆盖该场景Decode增长，4K与Prefill4K仅为邻近哨兵。

主指标为无profiler的graph完整API设备延迟，包含候选forward、partial写读和combine及原生必要kernel。两侧不传out buffer，输出均由各自API生成；metadata构建和Python/allocator/capture/JIT不计入graph replay时间。单graph内重复调用：Decode32次，Prefill4次；不得只计候选主kernel而遗漏combine。

每侧预热20次并完成capture。graph warmup至少5个窗口、最多12个窗口，末3窗口max/min−1≤8%才准入；保留全部准入后9轮。每轮native→candidate→native，保留两组native以检查时间漂移。每轮graph replay数按两侧校准延迟的较小值计算以目标10ms、限制1…32次，规则测前冻结；按inner calls归一化。报告各轮值、中位数、P90、散差与native前后漂移；散差或漂移>8%为incomplete，不丢慢轮。

数值先对拍native，哨兵另外对FP32数学reference；atol=0.03、rtol=0.03、relative L2≤0.01、输出有限。每shape两次变化Q输入graph replay再对拍；失败不晋级有效性能结论。单shape最长180秒，总任务预算15分钟，超时保留日志；只结束本次benchmark进程，不停止任何服务。

## 优化内容与适用边界

不修改main.py、原生安装或服务；候选使用逐字节冻结副本。仅产生独立benchmark脚本、隔离JIT cache和结果。page映射以本次tensor为准，graph复用固定地址。此测量不验证之前识别出的非因果ALiBi、显式num_splits等通用ABI问题。

## 正确性与路径命中

18/18 shape通过native输出对拍，额外1组非对齐ragged哨兵对FP32参考通过；36次变化Q输入graph replay对拍通过。初次对拍最大绝对误差0.0078125、最大relative L2约0.2872%；变化输入replay最大relative L2约0.2878%。这只覆盖本次无ALiBi等支持条件，不是模型精度gate。

实际设备为MetaX C550/104 SM，torch2.8.0+metax3.7.0.7、Triton3.6.0、驱动3.8.1、MACA3.7.1.5。调用函数来自安装的flash_attn.flash_attn_interface和冻结候选模块；native扩展为flash_attn_2_cuda。两者调用各自真实实现，没有替换fallback。此轮未开启profiler。

## 性能效果

18/18完成稳态准入和全部9轮，无删除慢轮。**所有已测shape均为原生更快，当前main.py不应据此替换原生服务路径。** 下表单位为μs；延迟是graph内完整API调用的设备时间，经调用数归一化后的9轮中位数。比值为候选耗时/原生耗时，大于1表示候选更慢。

| 场景 | B | Q / KV长度 | 原生 μs | main.py μs | main/原生 | main splits |
|---|---:|---|---:|---:|---:|---:|
| sentinel-ragged | 2 | Q=17/5; KV=113/57 | 14.652 | 28.706 | 1.959× | 1 |
| decode-b1-k1024 | 1 | Q=1; KV=1024 | 17.895 | 54.886 | 3.067× | 32 |
| decode-b1-k2048 | 1 | Q=1; KV=2048 | 25.269 | 59.230 | 2.344× | 32 |
| decode-b1-k4096 | 1 | Q=1; KV=4096 | 27.252 | 68.892 | 2.528× | 32 |
| decode-b8-k1024 | 8 | Q=1; KV=1024 | 23.744 | 66.736 | 2.811× | 26 |
| decode-b8-k2048 | 8 | Q=1; KV=2048 | 32.130 | 80.022 | 2.491× | 26 |
| decode-b8-k4096 | 8 | Q=1; KV=4096 | 45.317 | 110.949 | 2.448× | 26 |
| decode-b32-k1024 | 32 | Q=1; KV=1024 | 41.135 | 89.344 | 2.172× | 7 |
| decode-b32-k2048 | 32 | Q=1; KV=2048 | 65.410 | 146.707 | 2.243× | 7 |
| decode-b32-k4096 | 32 | Q=1; KV=4096 | 112.884 | 267.149 | 2.367× | 7 |
| decode-b64-k1024 | 64 | Q=1; KV=1024 | 66.195 | 133.750 | 2.021× | 4 |
| decode-b64-k2048 | 64 | Q=1; KV=2048 | 113.443 | 242.848 | 2.141× | 4 |
| decode-b64-k4096 | 64 | Q=1; KV=4096 | 205.862 | 459.860 | 2.234× | 4 |
| prefill-b1-q1024 | 1 | Q=1024; KV=1024 | 64.702 | 182.008 | 2.813× | 1 |
| prefill-b8-q1024 | 8 | Q=1024; KV=1024 | 393.714 | 822.391 | 2.089× | 1 |
| prefill-b1-q4096 | 1 | Q=4096; KV=4096 | 494.640 | 1620.107 | 3.275× | 1 |
| prefill-b2-q4096 | 2 | Q=4096; KV=4096 | 1291.248 | 2913.984 | 2.257× | 1 |
| prefill-ragged | 2 | Q=1009/257; KV=1009/1021 | 122.569 | 221.388 | 1.806× | 1 |

12个Decode的候选耗时为原生2.02–3.07倍；4个等长Prefill为2.09–3.28倍。两组ragged哨兵也较慢。原生合并轮次最大散差0.80%，原生before/after各自最大散差1.38%，候选最大散差1.06%，原生前后中位漂移最大0.425%，均低于预冻结8%阈值。

各shape P90与全部原始轮次保存在JSON，并写入state.yml摘要。例：B64/KV1024原生P90为66.336μs，候选133.835μs；这是9轮调用均值的P90，不是单次调用尾延迟。

候选Prefill不拆分也慢，说明不能仅把差距归因于merge。Decode的split数量为B1→32、B8→26、B32→7、B64→4；tile/布局/资源与native策略不同。当前没有采集资源计数或剖析数据，具体瓶颈未证明，不把这些差异写成已确定根因。

这是合成随机输入、固定页映射与重复数据、隔离单卡上的稳态API设备耗时，不含Python/allocator、元数据构建、输出拷贝到服务buffer、KV append、TP通信及调度；未测Mixed服务或端到端吞吐。不能将上述比值直接换算为模型加速比。

## 决定、风险与回退

保留原生路径，不部署候选；没有生产补丁需要回退。测试结束GPU2上下文已退出，GPU6/7既有worker仍在；main.py和native接口SHA未变。当前测量证据足以否定“该候选在这些shape上比原生更快”，不外推其他head维度、硬件、dtype、页长或长上下文。

## 外部证据

计划目录：`/public-flash/jinghao/qwen3-VL/20261021-qwen3vl-metax-p1k-opt9/commands/op007-fa-main-native-20261021-a/`。
结果目录：同案例 `results/op007-fa-main-native-20261021-a/`。
远端变更命令（执行前记录）：只在不存在的新目录中保存benchmark与main.py冻结副本；`docker exec -e CUDA_VISIBLE_DEVICES=2 -e TRITON_CACHE_DIR=/tmp/qwen-vl/op007-fa-main-native-20261021-a ... /opt/conda/bin/python -P <benchmark.py>`。Host控制进程按shape串行、限时执行并收集原生JSON。源容器和现有服务不变。


已完成证据：

- `results/op007-fa-main-native-20261021-a/aggregate.json`，SHA256 `6d4675ebc742358a1f99902ffeda20311ac5c582c4352151cf88ec6903d5502a`。
- 同目录 `verification.json`，SHA256 `7d621c4828f0e4b03377b33b4a77463db59bb07c25c5b2ab93dcd88e49827aa8`；原始每shapeJSON含预热、9轮B/C/R、数值及graph结果。
- benchmark脚本SHA256 `b86e759ab9e4cd55dcbf71bfd0118a05d1e1e60583c312189f1c9cdef25b804b`；Host控制脚本SHA256 `2df32a85ce470da2f6a25f2d929f71e80dfa365d91ac1d4b1d0fc541a3f864ea`。
- native扩展SHA256 `d51997a6e75f56908ae3d42bf150081eb14e4d36d5a735580745c7416a6799c6`。
- 原始执行命令：`python3 /public-flash/jinghao/qwen3-VL/20261021-qwen3vl-metax-p1k-opt9/commands/op007-fa-main-native-20261021-a/host.py`；单shape复现参数和冻结候选由该脚本显式指定。总GPU测试流程约546.84秒。

知识差量：`contradicted/refined`。GQA打包、转置与自适应Split-KV是机制而非相对native收益证据；在当前Q16/KV2/D128矩阵上，完整调用测得全部负收益。后续应先匹配真实native API和每rank形状，保留merge及必要输出成本，不能由历史aggregate1.6537注释推广部署。


## 用户复现脚本交付

将同一测量核心参数化为仓库 `benchmarks/flash_attention_compare.py`，说明见 `benchmarks/README.md`。默认shape、seed、20次预热、graph内调用数和9轮native/candidate/native与原实验一致；额外检查native before/after各自散差，不会使原18组结果失效（原结果亦均满足）。支持source SHA、独立目录、子集、逐shape限时、JSON/CSV与失败保留。

远端变更命令在执行前记录：在 `commands/op007-fa-main-native-reproduce-v1/` 新建脚本副本（SHA256 `d71d5a62a303b4728b269501245ea75bd9fa9827a7707364cfd141324cba66ce`）；只在GPU2做 `--case decode-b64-k1024 --run-id validation-b64-k1024 --output-dir <case>/results/op007-fa-main-native-reproduce-v1` 验证。脚本不修改main.py、安装包或服务，不清理任何旧结果。此阶段不重跑全矩阵；完整18组来自原op007回执。

交付验证完成：新增9项CPU检查通过；全量216项测试通过（3项跳过），所需compile/help入口通过。新脚本在目标容器B64/KV1024完成默认9轮，native 66.265μs、candidate 133.690μs、比值 2.018；数值及2次变化Q graph检查通过。回执：`results/op007-fa-main-native-reproduce-v1/validation-b64-k1024/run.json`，SHA256 `ffa02d3e50c147dbc7a9459565228a6641b70c94eabcc5e2212fcaf5c21baf7b`。GPU2上下文退出，GPU6/7原有worker仍在。新脚本仅验证这一shape，未重跑全量18组。
