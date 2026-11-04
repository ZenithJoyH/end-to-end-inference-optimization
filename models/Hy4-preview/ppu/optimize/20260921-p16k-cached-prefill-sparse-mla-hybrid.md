# 20260921-p16k-cached-prefill-sparse-mla-hybrid

- experiment-id：`20260921-p16k-cached-prefill-sparse-mla-hybrid`
- 分类：`operator/replace`
- 状态：`milestone_passed_parent_and_accuracy_pending`
- milestone：`P16384/D128/C16/N16`

## 方向与假设

- 父场景：`P16384/D1024/C64/N128`；筛选 milestone：`P16384/D128/C16/N16`。
- 实际热点：P16K rank0 trace 中，cached chunked-prefill continuation 的
  generic sparse MLA 固定以 `SQ=2048/HQ4/DQK576/DV512/topk2048`
  运行；`execute_new_0_cached_1` bucket 内共 6381 次，平均约
  `6.148 ms`。
- 旧知识：PPU native sparse MLA 对 score-selected SQ2029/2048 曾测得
  `1.056x–1.089x`；FlagGems-vllm full-prefix grouped 在纯 prefix 更快，因此
  whole-batch native replacement 不成立。
- 新假设：在 T-Head/Hy4 边界保留 full-prefix grouped，仅对
  score-selected/cached-prefill rows 使用 native 主 kernel，能同时避免纯
  prefix 回退和 P16K 长 KV 下的 generic gather 瓶颈。

## 冻结契约

- 分类：`operator/replace`，跨仓库边界为 Plugin dispatch +
  FlagGems-vllm T-Head vLLM-specialized operator。
- 首个证伪实验：在目标 PPU 上对 `SKV=16384`、
  `SQ={512,2048}` 的 score-selected/full-prefix/mixed-group 做完整调用
  microbenchmark，包含 classify、fallback 与 grouped overwrite。
- 算子晋级条件：主导 score-selected SQ2048 至少 `1.08x`，
  mixed-group 至少 `1.05x`，full-prefix 不低于 `0.98x`；BF16
  `atol/rtol=2e-2`、cosine `>=0.9999`，graph capture + 两次 replay。
- 服务晋级条件：先做同配置 `P16384/D128/C16/N16`
  no-profiler baseline/candidate/revert，output throughput `>=2%`，P99
  TTFT/TPOT/ITL 任一回退不超过 `5%`，然后才进父场景。
- 停止条件：无法从 metadata 稳定区分初始 full-prefix 与 cached
  continuation；数值/graph 失败；完整调用不过门槛；或服务收益
  低于 `2%`。

## 当前状态

- 实施：已在 Plugin T-Head 调用边界加入 capability/metadata guard，并在
  FlagGems-vllm T-Head backend 新增
  `flash_mla_sparse_cached_prefill_fwd`。初始 full-prefix group 仍由 grouped
  kernel 处理；只有 cached-prefill 的 score-selected rows 使用 PPU native
  主 kernel；小 SQ Decode 仍走原 split-K。FlagGems 通用仓库未修改。
- A/B 开关：`VLLM_FL_THEAD_CACHED_PREFILL_SPARSE_MLA_HYBRID`，默认 `1`；
  服务实验分别显式使用 `0/1/0`。Plugin 运行日志会对实际命中输出一次
  `Using T-Head cached-prefill native/grouped sparse MLA hybrid`。
- 当前源码未提交、未推送；服务已停止，8010 未监听。
- 决定：`milestone_passed_pending_parent_and_accuracy_gate`。保留候选源码，
  但尚未声称父场景或 formal 验收通过。

## 算子验证

- 独立完整调用、`SKV=16384`：
  - SQ512 score-selected `1.1210x`，mixed `1.4051x`；
  - SQ2048 score-selected `1.0827x`，mixed `1.2149x`；
  - guarded full-prefix 约 `1.00x`。
- 集成源码后的复验：SQ2048 score-selected `1.0783x`，因比冻结的单次
  `1.08x` 门槛低约 0.17 个百分点，没有直接晋级。随后保持门槛不变，做
  3 组确定性 index 分布、每组 9 对 baseline/candidate 的交错确认：三组
  中位数 `1.0844x/1.0888x/1.0747x`，总中位数 `1.0844x`，且每组均高于
  `1.05x`，因此通过抗时序噪声的确认门禁。
- 最大绝对误差 `3.05e-5`，cosine `>=0.9999995`；graph capture 和两次
  replay 通过。
- Plugin 聚焦测试 `4/4`、FlagGems-vllm T-Head Hy4 测试 `30/30`、
  `compileall` 和 `git diff --check` 通过。

关键算子证据：

- 独立 benchmark：
  `/mnt/nfs/users/jinghao/hy4-preview/optimize/20260914-hy4-preview-ppu-e2e/results/operator/sparse-mla-p16k-cached-prefill-hybrid-20260921-01/summary.json`
  (`sha256=926ae849b3384e489ffd30be02ff3f5d1466890c66bb7a57eccbc89c22b7078c`)。
- 集成 benchmark：
  `/mnt/nfs/users/jinghao/hy4-preview/optimize/20260914-hy4-preview-ppu-e2e/results/operator/sparse-mla-p16k-cached-prefill-hybrid-20260921-03/summary.json`
  (`sha256=c95e282ebfe46afca3d29f43d25d4883df5ccf14273e90904bc54819395ce34c`)。
- 交错确认：
  `/mnt/nfs/users/jinghao/hy4-preview/optimize/20260914-hy4-preview-ppu-e2e/results/operator/p16k-cached-prefill-score-confirm-20260921-01/summary.json`
  (`sha256=156fab2c5dd25d81e4f7899f2b4ede21ebecac5c490c281aabd48f73f4b2c6fe`)。

## 服务级 milestone A/B/revert

场景固定为 `P16384/D128/C16/N16`，TP16、graph
`FULL_DECODE_ONLY`、`max-num-batched-tokens=2048`、prefix cache 关闭；
每个独立服务实例执行 1 次预热和 2 次计量。三段均成功生成完整
run-record，唯一允许变化的路径为
`/launch_config/environment/VLLM_FL_THEAD_CACHED_PREFILL_SPARSE_MLA_HYBRID`。

| 指标（计量中位数） | baseline | candidate | revert | candidate 改善 |
|---|---:|---:|---:|---:|
| Output throughput (tok/s) | 12.9728 | 13.5640 | 12.9755 | +4.558% |
| Total throughput (tok/s) | 1673.485 | 1749.762 | 1673.833 | +4.558% |
| P99 TTFT (ms) | 149860.69 | 143095.91 | 149846.70 | -4.514% |
| P99 TPOT (ms) | 1109.15 | 1058.37 | 1109.00 | -4.579% |
| P99 ITL (ms) | 1444.10 | 1381.17 | 1444.26 | -4.358% |
| 等价完整批次时长 (s) | 157.869 | 150.987 | 157.837 | -4.359% |

- output throughput 超过 `+2%` 主门槛，三项尾延迟均改善；标准比较结果为
  `passed`，`issues=[]`。
- baseline→revert output drift 仅 `+0.0208%`；两次计量轮的 output
  throughput 差分别约 `0.072%/0.078%/0.135%`（baseline/candidate/revert），
  测量稳定。
- 实际命中日志为 baseline/candidate/revert=`0/1/0`，证明没有用 fallback
  成功代替目标路径命中。
- 每个计量轮均 16/16 完成且 candidate 无空输出。相同种子的逐请求文本并非
  全部逐字确定，但 candidate 与 baseline 的一致数（R2/R3=`5/3`）和
  baseline 与独立 revert（`6/3`）相当，没有观察到候选特有的额外分歧；
  正式语义正确性仍以新源码身份的精度 gate 为准。

结果根目录：
`/mnt/nfs/users/jinghao/hy4-preview/optimize/20260914-hy4-preview-ppu-e2e/results/performance/20260921-p16k-d128-c16-n16-cached-prefill-hybrid-01/`。
正式比较回执为 `comparison-result-device-id-repaired.json`
(`sha256=b300e3ae3c5692671ce8bb259d96e6f3f8047e6a9cbca03e2df786f199825f2f`)。

原始 service manifest 把设备编号写成整数，维护版比较器要求字符串设备
标识。原始 run-record 和 service snapshot 均未覆盖；实验生成了带原始路径
和 SHA 的派生记录，只执行 `[0..15] -> ["0".."15"]` 的无损元数据修复。
生成器已同步改为写字符串，修复脚本 SHA256 为
`eb6414e2cebf40f48ea2d2a5ffe8855ff485e49d68b59e89018ad4c44389c1cb`。

## 源码身份与回退

- Plugin 当前 sparse MLA 入口 SHA256：
  `898dcc340770dae47663fd00ff313bd1fdd71a979fd194b5fa739bdfa420a18f`。
- FlagGems-vllm 当前 sparse MLA SHA256：
  `38d1f5e5fa9599b198ab3add1bbf0547fa2cbbe643ad0025ec04cfb0ae01e27c`。
- 独立 patch SHA256：FlagGems-vllm
  `2d577759fc16075de19197c49d990afcf178fe1825d2b6857714a0516b1ee200`；
  Plugin 主改动
  `a498b29b0e25b58a7c4c156b66c9124ad72aa70905d2356b5250f583164b71dd`，
  toggle `16792b2d66f30802e1cac59557c8e9f27ebc56ab4460ee75ac67d3ebc7a2c453`，
  hit log `4d830a85d49e579c516d8c53e70f7d97490c3a7fb3bbc4a27cc4d286cc49df13`。
- 快速回退可在启动时显式设置 hybrid 环境变量为 `0`；源码回退按 hit-log、
  toggle、Plugin 主 patch、FlagGems-vllm patch 的逆序应用，且必须先核对
  当前 SHA，避免覆盖本任务更早的未提交优化。

## 结论边界与下一步

这轮已经证明候选在 P16K 长 prompt 的缩减 Mixed milestone 上获得可重复的
`+4.56%` 端到端输出吞吐，且尾延迟同步改善；收益明显高于此前只在 pure
Decode 接入 native sparse MLA 的 `+0.196%`，原因是新 guard 命中了实际占比
更高的 cached chunked-prefill continuation。

仍未完成两项晋级条件：

1. 当前新源码身份没有正式精度 gate；此前 GPQA 结果不能自动覆盖本改动。
2. 尚未在父场景 `P16384/D1024/C64/N128` 做同配置 baseline/candidate/revert。

因此当前只保留为 milestone candidate。下一步应先完成新源码的最小/正式
精度 gate，再运行父场景的中间正式性能检查；不得把 `+4.56%` 直接外推为
父场景收益。
