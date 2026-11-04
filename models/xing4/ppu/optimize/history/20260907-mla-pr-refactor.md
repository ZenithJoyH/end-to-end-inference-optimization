# MLA 小 head 自动分派 PR 重构

本轮把已验证的 `BLOCK_H=16` 实验补丁整理为 FlagGems PR 候选。最终实现按运行时 shape、dtype 和 layout 自动选择，不使用模型名、机器身份、容器身份或实验环境变量。

## 设计边界

- 调用链：vLLM Plugin `forward_mqa` → FlagGems `flash_mla_with_kvcache` → dense decode dispatch。
- 目标路径：`SQ=1`、`0 < H_rank <= 16`、`DQK=576`、`DV=512`、BF16、page 16/64、Q 最后一维连续。
- 选择：目标路径使用 `BLOCK_H=16`，stage 2/3 继续 autotune；其他输入保留原 `BLOCK_H=64` autotuner。
- kernel 数学、KV layout、`BLOCK_N=64`、warp 数和返回契约不变；TLE 路径仍有原优先级。
- 代码结构：一个共享 `@triton.jit` kernel 主体，两个独立 autotuner 包装；不依赖另一个 autotuner 的 `.fn` 属性。
- 首个否证测试：H8/H16 数值或 graph 失败、H32 fallback 改变、最终同配置服务吞吐收益不能复现。

## 远端变更命令

目标仅为隔离优化容器 `xingchen4-e2e-20260904` 内的 `/workspace/FlagGems` 私有副本：

```text
docker exec -i xingchen4-e2e-20260904 sh -lc 'cd /workspace/FlagGems && git apply --check -'
docker exec -i xingchen4-e2e-20260904 sh -lc 'cd /workspace/FlagGems && git apply -'
```

维护版 runner 部署及性能研究命令：

```text
tar evaluation/performance、evaluation/accuracy、standard_perf.py | docker exec -i ... tar -xf -
python3 standard_perf.py --runner /workspace/test/perf_test/vllm_perf.py --model teleai-flagos --tokenizer /mnt/cpfs/models/XingChen4-29B-A4B --host 127.0.0.1 --port 8000 --input-lengths 1024 --output-length 1024 --concurrency 64 --requests 128 --performance-only ...
```

补丁应用前先停止该容器中的当前优化服务；不操作源适配容器 `xingchen4-24-new`。最终验证和性能结果在本目录继续记录，原始日志与 JSON 保存于优化容器的外部产物目录。

## 验证状态

| 场景 | 结果 | 状态 |
|---|---|---|
| H8/H16、page16/64、BF16 dense decode | 与原BH64输出/LSE一致；eager、capture和两次replay通过 | `executed_passed` |
| H32 | 自动回到BH64，输出/LSE与显式原kernel一致 | `executed_passed` |
| 上游pytest新case | PPU环境受模块级NVIDIA FlashMLA条件影响，6项被skip | `not_run`；由独立硬件reference覆盖 |
| xing4 TP4 graph服务 | 最终服务环境无旧变量；实际FlagGems SHA匹配；候选cache有6个BH16条目；C8 8/8 | `executed_passed` |
| 同配置端到端candidate/revert | 输出及总吞吐中位数均提升73.15% | `executed_passed`，性能研究范围 |

## 性能结果

最终重构代码的page16微基准在B64、S1024/4096/16384分别为`0.18621/0.69190/2.69267 ms`，原BH64为`0.83762/2.98804/11.46206 ms`，加速`4.50/4.32/4.26倍`。page64对应加速`4.61/4.25/4.16倍`。原始JSON：

- `/workspace/e2e-artifacts/pr-refactor-micro-p16.json`
- `/workspace/e2e-artifacts/pr-refactor-micro-p64.json`
- `/workspace/e2e-artifacts/pr-refactor-boundary.json`
- `/workspace/e2e-artifacts/pr-refactor-boundary-p64.json`

page16微基准使用的物理PPU4当时与受保护服务共置，page64使用空闲PPU5；因此微基准只作为算子方向和数值证据，不用于端到端收益结论。下面的candidate/revert均改在同一组空闲PPU8–11完成。

端到端固定`P1024/D1024/C64/N128`，一轮预热、两轮measured，随机定长、temperature0、ignore-eos。两种实现均在同一物理PPU8–11、同一容器、相同服务参数和独立新缓存目录运行：

| 实现 | measured输出吞吐 token/s | 中位数 | measured总吞吐 token/s | 中位数 |
|---|---|---:|---|---:|
| 自动小head候选 | 1213.23，1137.21 | 1175.22 | 2426.46，2274.42 | 2350.44 |
| FlagGems原实现revert | 592.27，765.19 | 678.73 | 1184.55，1530.39 | 1357.47 |

候选相对revert的两个主指标均提升`73.15%`。每轮128请求全部成功，输入/输出token总数分别为131072。revert两轮相对spread约25.5%，候选约6.5%，因此该结果支持明显正收益，但不用于声明稳定容量或统计置信区间。原始run-record：

- `/workspace/e2e-artifacts/pr-refactor-perf-candidate-v2/candidate-01/run-record.json`
- `/workspace/e2e-artifacts/pr-refactor-perf-revert/revert-01/run-record.json`

首次维护版runner预检因vLLM 0.24普通`--help`隐藏完整参数而失败，未发送请求；修复为`--help=all`后，相关43项本地单测通过，失败run-record继续保留在`/workspace/e2e-artifacts/pr-refactor-perf-candidate/candidate-01/`。

## 当前运行与PR边界

最终服务位于`xingchen4-e2e-20260904`，服务标签为`pr-refactor-final`，宿主机端点`127.0.0.1:18000`，选择物理PPU8–11。选择这组卡是因为另一个受保护的`xingchen4-opt`服务占用PPU1–4；该服务全程未停止或修改，最终health为200。

最终FlagGems源码SHA为`45eaf0e7342dcf9bfd0987dacb11dea6572d948b2334805639e50840b7d450c9`，测试SHA为`cda6ae24958760777c19f95abb9699111bf7c77512780891bf2738439cf6e40c`，补丁SHA为`7f2789a28620a103d30a9013d64a14426d9682ff1a418970bc942cf59e4a356d`。未安装的Black/isort/ruff未执行；Python编译和`git diff --check`通过。非PPU平台、FP16、其他DQK/DV/page、不同TP head shape及正式GPQA未实测；这些输入保持原BH64路径，不能据此声明其他硬件性能通过。

`pr_readiness=ready_for_review`：补丁和测试已去除实验变量、模型/Host判断、PID打印及`Autotuner.fn`依赖，回退为反向应用最终补丁。此状态不表示上游已接受，也不表示正式模型精度验收完成。

2026-09-07 已将上述两个 FlagGems 文件提交并推送到
[`ZenithJoyH/FlagGems:sparse-mla-opt`](https://github.com/ZenithJoyH/FlagGems/tree/sparse-mla-opt)，提交为
[`dbd96aa2e9b4dd8e383fd4f01056a4ac201fdb4b`](https://github.com/ZenithJoyH/FlagGems/commit/dbd96aa2e9b4dd8e383fd4f01056a4ac201fdb4b)。
一次性发布命令不再保存在模型目录，远端提交及 commit ID 是核验依据；未创建 PR。
