# perf-009 新旧容器端到端性能归档对照

状态：只读比较完成；复核时间 2026-10-23T10:54:24.471043+08:00。仅读取用户性能CSV和相关既有记录，没有模型请求、压测、重启、源码/配置/缓存或其他远端变更。没有调用新的性能测量模式，也不签发性能验收。

主要对比10月20日旧容器的 `MiniMax-M3.1-new` 与用户提供10月22日新容器的 `MiniMax-M3.1-new2`；旧身份有同日reqdiag-001记录支持，新身份有用户说明和acc-007记录支持，但缺少逐轮冻结服务绑定，保留该限制。三个场景均D1024/C64/N128，全部三轮CSV标记SUCCESS、128请求，输入P×128和输出131072 tokens一致。

| 输入长度 | 旧总吞吐 token/s | new2总吞吐 token/s | 变化 | 旧平均TTFT ms | new2平均TTFT ms | 旧平均TPOT ms | new2平均TPOT ms |
|---|---:|---:|---:|---:|---:|---:|---:|
| p4096 | 3733.53 | 3767.47 | +0.91% | 10625.19 | 10553.08 | 75.10 | 74.41 |
| p16384 | 4562.92 | 4600.15 | +0.82% | 113388.76 | 112535.23 | 105.61 | 104.72 |
| p32768 | 4873.41 | 4915.50 | +0.86% | 272534.59 | 270245.01 | 97.72 | 96.87 |

总吞吐（输入+输出）仅高0.82%–0.91%，平均TTFT降低约0.68%–0.84%、平均TPOT降低约0.84%–0.92%；属于小幅改善观察，证据不足以证明稳定的代码收益。输出吞吐相同workload下同方向增加。TTFT/TPOT来自Mixed客户端口径，包含排队调度等，不能作为纯设备Prefill/Decode耗时。

## 汇总与稳态边界

CSV的SUMMARY与第2/3轮均值吻合，当前脚本固定RUNS=3、SKIP_FIRST=1。本次沿用历史汇总解释，保留所有三轮；没有事后新删首轮或声称满足现行稳态准入。new2 P16的Run1为3684.15，而Run2/3为4599.52/4600.78 token/s，存在明显进入稳态前差异。只有两个汇总测量、没有独立服务重复和回退，不足以确认约0.9%的稳定收益。

相关服务开启prefix cache；P4日志三轮seed0，未保留命中率与缓存准备证据。CSV也没有逐轮源码/客户端/设备/完整启动身份，不能把后续精度manifest自动绑定给先前性能测量；历史结果不按默认禁用缓存门禁追认或改写。缺P1K和独立阶段证据，正式结论incomplete。

## 更早opt7参考（不可作为同Flash单变量基线）

| 输入长度 | opt7总吞吐 token/s | new2总吞吐 token/s | new2相对opt7 |
|---|---:|---:|---:|
| p4096 | 4048.38 | 3767.47 | -6.94% |
| p16384 | 4469.73 | 4600.15 | +2.92% |
| p32768 | 4529.76 | 4915.50 | +8.52% |

opt7是10月18日的旧preview时期系列，与10月20日Flash旧容器结果分开。数字显示并非所有输入长度都提高，但权重/版本/测量身份不同，不能推断单个算子退化或将其算作当前迁移收益。

## 原始证据

根：`/mnt/nfs/users/jinghao/minimaxM3.1/test/perf_test/benchmark_results`。仅小体量路径/SHA与数字摘要写入state；原CSV保留远端。

- `/mnt/nfs/users/jinghao/minimaxM3.1/test/perf_test/benchmark_results/MiniMax-M3.1-new/MiniMax-M3.1-new_16384in_1024out_c64_n128_20261020_092553.csv`，SHA `f912e7673da178e55626c47d779f5175183fc0ab7e362d87937bd5822705dd99`；3轮总吞吐 `[4419.9, 4564.03, 4561.82]`。
- `/mnt/nfs/users/jinghao/minimaxM3.1/test/perf_test/benchmark_results/MiniMax-M3.1-new/MiniMax-M3.1-new_32768in_1024out_c64_n128_20261020_092553.csv`，SHA `a87b87a8015bd8e9307dc5d2279c95736482830b8be28ff732875aa3dd0d247c`；3轮总吞吐 `[4819.74, 4872.48, 4874.34]`。
- `/mnt/nfs/users/jinghao/minimaxM3.1/test/perf_test/benchmark_results/MiniMax-M3.1-new/MiniMax-M3.1-new_4096in_1024out_c64_n128_20261020_092553.csv`，SHA `e88aa8fd8d918726e5bd9e4ea8186c2f7d65b7a948b0f9ed39cf7c562915bbf2`；3轮总吞吐 `[3218.23, 3728.7, 3738.37]`。
- `/mnt/nfs/users/jinghao/minimaxM3.1/test/perf_test/benchmark_results/MiniMax-M3.1-new2/MiniMax-M3.1-new2_16384in_1024out_c64_n128_20261022_151947.csv`，SHA `5f2044cdbff68eabff98a6881e6546c16589a11a77a307d56c622b6070c68c17`；3轮总吞吐 `[3684.15, 4599.52, 4600.78]`。
- `/mnt/nfs/users/jinghao/minimaxM3.1/test/perf_test/benchmark_results/MiniMax-M3.1-new2/MiniMax-M3.1-new2_32768in_1024out_c64_n128_20261022_151947.csv`，SHA `e4aef9550e5433e0bd9c0de0b7ae686f3868224ab80feb2bd8b605751be184e1`；3轮总吞吐 `[4843.31, 4915.6, 4915.4]`。
- `/mnt/nfs/users/jinghao/minimaxM3.1/test/perf_test/benchmark_results/MiniMax-M3.1-new2/MiniMax-M3.1-new2_4096in_1024out_c64_n128_20261022_171439.csv`，SHA `8df1f9469f40abe746428e78da536c0b8a72cc39cf8fbb93188f05de3b6a3669`；3轮总吞吐 `[3772.29, 3769.48, 3765.45]`。
- `/mnt/nfs/users/jinghao/minimaxM3.1/test/perf_test/benchmark_results/MiniMax-M3.1-opt7/MiniMax-M3.1-opt7_16384in_1024out_c64_n128_20261018_222444.csv`，SHA `032e50144a8047c614e97314ae7c56689a11f690ff28cbc04907a856d5a91dc6`；3轮总吞吐 `[4459.26, 4469.66, 4469.8]`。
- `/mnt/nfs/users/jinghao/minimaxM3.1/test/perf_test/benchmark_results/MiniMax-M3.1-opt7/MiniMax-M3.1-opt7_32768in_1024out_c64_n128_20261018_222444.csv`，SHA `6d958b717728b57dd72265133205fea7692912dbd2bf6cc433335702a150dad3`；3轮总吞吐 `[4524.46, 4530.07, 4529.46]`。
- `/mnt/nfs/users/jinghao/minimaxM3.1/test/perf_test/benchmark_results/MiniMax-M3.1-opt7/MiniMax-M3.1-opt7_4096in_1024out_c64_n128_20261018_222444.csv`，SHA `2497a44b9ba152582d561295859e36df694a7ddcc6478cc88e99f1aa62e921bc`；3轮总吞吐 `[4015.0, 4045.29, 4051.47]`。

当前性能脚本SHA `46fff4b1fd27f31833856d76a46f2434c29cd2143206092d8345a9bcd67be563`；P4 perf.log SHA `c8087ad901bbca1c36a8a31d29d805ab711fcbb39cde3bf82ef405d6eb3192f2`。当前脚本不等于已冻结的历史脚本身份。旧容器同日服务归属见[reqdiag-001](../../20261019-flash-three-task-accuracy/optimize/reqdiag-001.md)，新服务精度事实见[acc-007](acc-007.md)。
