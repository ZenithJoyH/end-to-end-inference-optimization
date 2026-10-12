# 20260911-glm53-flash-ppu-e2e：GLM-5.3-Flash-BF16 / PPU 端到端优化

## 摘要

- 执行规则：`0.18` / `2026-09-10`
- 验收范围：`diagnostic`
- 精度/性能状态：`passed` / `P1K targeted numeric gates passed; formal incomplete`
- 状态：`max_num_seqs=64 / exact-M64 Decode MoE candidate retained / P1K low-risk analysis converged / service stopped`；
  MQA 修复已提交并推送，本轮 M<=32 与 exact-M64 GEMM2 候选尚未提交或推送，
  最终四场景性能验收仍未完成。
- 目标：在 `PPU-13` 上建立可信基线，分层定位并优化 TTFT、TPOT 与吞吐，同时保持正确性、稳定性和资源边界。
- 模型/平台产物：[models/GLM-5.3-Flash-BF16/ppu](../../../models/GLM-5.3-Flash-BF16/ppu/)

## 已核验目标事实

- 模型：`/mnt/cpfs/models/GLM-5.3-Flash-BF16`，served name `glm5.3-flash`。
- 平台/Host：T-Head PPU，`PPU-13`，16×PPU-ZW810E。
- 源适配容器：`glm5.3-flash`，镜像
  `hy4-ppu07-snapshot:20260903@sha256:29a6712e24ca8e758ac8b33d3412892f0541bff108e2c057445fa671578237f6`。
- 当前运行配置：vLLM 0.24.0、BF16、TP16、max model len 80000、max seqs
  64、prefill eager、decode `FULL_DECODE_ONLY` graph。
- 初始 revision：vLLM `ee0da84a`、Plugin `db09b64a`、FlagGems `4a3cba02`、
  FlagGems-vllm `255ab560`。中间运行组合曾为 Plugin `96eb1bf`、FlagGems
  `fec9807`、FlagGems-vllm `255ab560`；该历史身份不再是最后验证实例。
- 当前已绑定交付 revision：Plugin `95b04f7`、FlagGems `9c9bff3`、
  FlagGems-vllm `f7443e7`。FlagGems clean；Plugin 和 FlagGems-vllm 保留本轮
  稳定性护栏与 M<=32/exact-M64 GEMM2 候选，为预期的未提交状态。
- exact-M64 后续 reprofile 与两个有界候选已完成；最后的 32768 token-budget
  探针已停止，8011 端口关闭且无遗留 vLLM 模型进程。

## 门禁与阻塞

- 独立优化容器：`glm5.3-flash-opt-20260911`；同镜像 ID、挂载一致性 passed，私有源码 revision 与实际 import 已验证。
- 用户已明确授权暂停源 vLLM 服务；源容器仍 running。服务退出后 16 张 PPU 均为 1 MiB、无运行进程。
- 适配项目未冻结正式性能 workload；当前先采用可复现的诊断矩阵，结果不能代表业务 SLO。
- 当前候选正式 GPQA 已完成 198 题，strict-match 为 172/198（86.87%）。用户确认门槛修正为 86% 并指示直接用该已完成结果判定，因此精度状态为 `passed`。原 wrapper 使用误写的 0.88 contract；此处记录为门槛修正后复判，不伪装为事前冻结。12 个 60K length-cap 响应作为非阻断输出健康风险保留。重复启动的 `formal-02` 已于 2026-09-11 14:55 +08:00 停止，部分产物不参与验收。

## 2026-09-18 服务中途退出

该事件是非阻断的输出健康问题，不改变 `172/198 >= 0.86` 的精度
gate。根因已确认：迁移后的 FlagGems-vllm MQA 算子仍从
`flag_gems.runtime` 取配置，使 FlagGems-vllm thead YAML 中的单个固定配置
没有生效，实际返回 144 个候选。新 shape
`M=2901,N=725,H=32,D=128` 在所有 TP rank 上同步在线 autotune，
在写入前 5 个 benchmark 结果后仍未完成，vLLM 的 300 秒 RPC 超时导致
EngineCore 和 API server 退出。同一 C8 热缓存复跑从首次约 133.87 秒降到
1.617 秒，复跑前后 DB SHA 不变，完成了单变量验证。详细证据与修复边界见
[优化事实与实验台账](../../../models/GLM-5.3-Flash-BF16/ppu/optimize/state.yml)。

修复将 MQA 算子的 runtime import 从 `flag_gems.runtime` 切换为
`flaggems_vllm.runtime`，并增加实际 tuner config 来源回归。完整模块测试为
`2 passed, 20 skipped`；直接算子覆盖非对齐 shape、原故障 shape、graph capture
与两次 replay，最大绝对误差不超过 `3.815e-6`。服务级用 32 请求构造总 prompt
token 精确为 2901 的批次，首次和立即复跑均 32/32 HTTP 200，复跑耗时
1.18455 秒，未再触发 MQA 多候选在线调优或 EngineCore 退出。修复证据位于远端
`diagnostics/accuracy-health-rpc-timeout-20260918-01/mqa-fix-validation-01/`；
两文件改动已提交为 `f7443e7` 并推送到
`ZenithJoyH/FlagGems-vllm: support-glm5.3-flash`，远端 HEAD 已核验；按用户要求
服务验证后保持停止。

## 初始候选原则

先核验框架中的明显浪费和工作点，再以 profiler 的真实生产 shape 决定算子替换或当前实现优化。
GLM-5.2 的 Indexer、Sparse MLA、MoE、采样与调度经验只作为候选机制，不继承其 TP16 MetaX 参数或性能数字。

## 已复现的算子慢路径

- 适配服务 FlagGems DB 的 906 张表中，892 张属于
  `_index_linearized_jit_function`；源码反查确认它对应 `aten.index.Tensor` 的
  FlagGems `index` 实现。
- 保留 thead 默认黑名单并追加 `index` 后，single 从约 131 秒降至 3.110 秒；
  C8 从两轮 8/8 在 240 秒超时恢复为 8/8 在 43.478–44.125 秒完成。
- single/C8 前后 `_index_linearized_jit_function` 表数量保持 892，运行命中记录不含
  `flag_gems.ops.index.index`，前缀缓存 query/hit 均为 0。
- 当前结论为 `reproduced`：FlagGems `index` 是该模型/平台/TP16 身份上的严重慢路径。
  正式 workload 的吞吐、TTFT、TPOT 尚未测量，不能把 sanity 改善写成最终性能收益。

完整结构化证据：[优化事实与实验台账](../../../models/GLM-5.3-Flash-BF16/ppu/optimize/state.yml)。

## 最新阶段状态

当前保留组合为 index 黑名单、native sparse MLA、
shape-gated native causal-conv、shape-gated vendor KDA 和
`max_num_batched_tokens=16384`，以及 shape-gated FlagGems MoE 分阶段配置。
MQA 固定配置已在运行时来源修复后生效，并通过原故障 shape 与服务级验证，
现计为生效的保留项。
`32768` 在长输出哨兵场景吞吐回退
1.523%，已拒绝并恢复 16384。最新证据排序和下一实验已合并到
[优化事实与实验台账](../../../models/GLM-5.3-Flash-BF16/ppu/optimize/state.yml)。

## 源码提交交付

- `vllm-plugin-FL` `support-glm5.3-flash`：`85302a7` index 黑名单、
  `dbb0e67` sparse MLA、`062c06f` causal-conv、`ef19fd9` Chunk KDA、
  `96eb1bf` large-M MoE stage config。
- `FlagGems` 原 `4a3cba0` day-0 kernels 与 `fec9807` MQA 配置已完成迁移，
  当前 `master` 和 `support-glm5.3-flash` 均为最新上游 `9c9bff3`。
- 2026-09-15 已分别推送到 `ZenithJoyH/vllm-plugin-FL` 和
  `ZenithJoyH/FlagGems`；当时 `git ls-remote` 核验远端 HEAD 为 `96eb1bf` 和
  `fec9807`。Plugin 聚焦单测 7/7 通过，两个仓库 YAML 解析通过。
- 远端容器缺少 GitHub HTTPS 凭据，首次尝试未更新任何 ref；最终使用经过
  SHA-256 校验的 Git bundle 与本机 GitHub SSH 身份完成。命令证据位于远端
  `commands/push-source-branches-20260915/`。
- 2026-09-18 将 vLLM 专用 MQA 调优配置和本任务全部新增的非 ATen GLM
  serving 算子归入 `ZenithJoyH/FlagGems-vllm` 新分支
  `support-glm5.3-flash@f7443e7`。
  fork `main` 已先纯 fast-forward 到上游 `6e7ac61`，新分支领先最新主分支
  8 个提交。迁移范围包括 graph-safe BF16 MQA、BF16 cache gather、indexer
  pool、prefill tail、kpool、causal-conv/update、recurrent KDA、safe gate、
  Chunk KDA、fused-MoE launcher 和 sparse-MLA small-head 支持。Plugin 在
  `support-glm5.3-flash@95b04f7` 统一改从 `flaggems_vllm` 公共 API 延迟导入。
  最终隔离验证使用不含旧模型提交的 FlagGems `9c9bff3`；公共导出、Plugin
  import/dispatch 均通过，FlagGems-vllm 测试 23/23、Plugin 测试 11/11
  通过；20 个 MQA focused 用例仍因缺少 vLLM DeepGEMM/FP8 reference 跳过。
  最后验证实例使用与 `FlagGems-vllm@f7443e7` 内容一致的工作树；本次事件证明上述测试没有覆盖
  MQA 迁移后的 runtime tune-config 来源。
  迁移证据位于远端 `commands/migrate-flaggems-vllm-20260918/`。

MoE 候选先将 trace 分解为时间几乎各半的 GEMM1/GEMM2，再对
M=4096/12401/16384 分阶段调参。保留配置在两场景正式 A/B/R 中
使输出吞吐分别改善 2.609%/0.344%，P99 TTFT 分别降低
3.714%/4.163%，比较器判定 `passed`。结构化数值与远端证据路径见
[优化事实与实验台账](../../../models/GLM-5.3-Flash-BF16/ppu/optimize/state.yml)。

保留 MoE 后的 16-rank trace 显示稳定热点迁移到 sparse MLA，fused MoE
累计设备时间约下降 14.8%。native sparse MLA 来自不暴露 tile 参数的预编译
扩展；其外围索引转换使用 BN1024 后，三个主 shape 微基准虽提升
3.55x–4.54x，但两场景端到端吞吐分别为 -0.041%/-0.005%，正式比较器
判 `failed`。该实验补丁已回退，停止前实例继续使用上述 MoE 保留组合、16384
和关闭的前缀缓存。证据、反例与下一阶段排序均已并入
[优化事实与实验台账](../../../models/GLM-5.3-Flash-BF16/ppu/optimize/state.yml)。

随后按 trace 前七个 shape 比较 general mm：thead 默认配置已经把 `mm`
列入 FlagGems 黑名单，停止前实例使用 native 路径。direct FlagGems 在六个
shape 上慢 17.6%–45.1%，仅 N=24 shape 持平，未达到 5% 门槛，因此未进入
服务 A/B，也没有新增代码改动。详细决策见
[优化事实与实验台账](../../../models/GLM-5.3-Flash-BF16/ppu/optimize/state.yml)。

## 2026-09-19 small-M Decode MoE 优化

P1K Decode trace 中 fused MoE 占设备时间 43.59%，且既有 large-M 配置
不覆盖 cached batch 32。本轮为 PPU aligned BF16、E=288、H=4096、
I=128、topk=8、1<=M<=32 的 GEMM2 增加有界配置。多 shape/多 seed
微基准中位加速 2.1424×，最低观测 1.3663×，数值和 graph
门禁均通过，落源后单测 18/18 通过。

P1024/D1024/C64/N128 targeted A/B/R 的输出吞吐中位数为
840.963 / 1004.382 / 847.618 tok/s；候选相对基线 +19.432%，
P99 TTFT 和 TPOT 分别降低 14.569% 与 16.262%，回退吞吐漂移
0.791%。三个有效角色均使用同一个冻结 FlagGems DB，SHA-256 为
`1917ccd26c170ca3d7c76197e662a862d3bfbdb1b6da064259bf2202eca38a83`，
测量期间未变且 WAL 为 0。

数值门槛已通过，但正式比较器因冻结契约要求 SLO attainment、
测量计划却未冻结 SLO 阈值而返回 `incomplete`。因此本轮只记为
P1K targeted 通过，不扩大为 formal/full 结论。获胜候选已保留在
FlagGems-vllm 工作树中，未提交、未推送；revert 服务已停止，
服务保持停止。

## 2026-09-19 后续候选、max64 分析与优化

small-M GEMM2 后的 16-rank reprofile 将 rank0 Decode 后续热点定位到
mHC pre、split-K reduction、MoE align 和 PCCL all-reduce。MoE align
source-path 虽快 3.635×，P1K 吞吐却下降 1.308%；mHC pre 虽在六个 shape
上中位快 5.528×，P1K 吞吐仍下降 0.587%，两者均已回退。精确
TP16 BF16 `[32,4096]` all-reduce 微基准也表明 PCCL 自动选择优于强制
Ring/Tree，后两者延迟分别增加 40.7%/236%。

三个连续负结果后测试 `max_num_seqs=32→64`。它使 P1K measured 吞吐中位数
从保守 max32 reference 的 1013.657 提升到 1277.797 tok/s（+26.058%），
但 P99 TPOT 从 31.281 增至 49.251 ms。用户明确将总输出吞吐设为主指标并接受
该延迟取舍，因此启动脚本已改为 max64。

max64 的 16-rank profile 解释了这个取舍：Decode step 近似设备时间从 max32 的
28.49 ms 增至 42.27 ms（+48.4%），但每步 token 数翻倍；同时 fused MoE 的
rank0 Decode device-activity 占比从 38.59% 增至 53.20%，成为首热点。针对真实
M64 baseline config 做 3-seed 扫描后，选取保持 BM32 padding 边界的 GEMM2
配置，算子中位加速 2.00306×，数值与 graph 门禁通过，聚焦测试 22/22 通过。

在同一 max64 P1K workload 上，候选 3 个 measured 轮的输出吞吐中位数为
1513.513 tok/s，相对前一版 max64 提升 18.447%，相对极差 2.687%；P99 TTFT
与 TPOT 分别改善 15.769% 与 15.561%，384/384 measured 请求成功。候选已保留、
未提交、未推送；服务已停止。

当时将 MoE align 与 mHC 视为“算子快但端到端慢”反例；该解释已被
2026-09-23 的候选 trace 纠正，具体见下文。本次 exact-M64 同时满足
live shape/config、首热点和无 profiler
服务复测，收益才得以兑现。完整数值、SHA 与远端路径见
[优化事实与实验台账](../../../models/GLM-5.3-Flash-BF16/ppu/optimize/state.yml)。

保留候选的后续 16-rank reprofile 又证明 rank0 Decode marker span 相对优化前
下降 16.018%，fused-MoE 活动时长下降 30.617%，其占比从 53.20% 降到
44.12%。剩余 GEMM1 扫描的最佳中位加速仅 1.048522×，未过 1.05× 算子门槛，
没有改源码。随后基于 Mixed 的四次约 16-request admission 测试 32768 token
budget，但三轮 warmup 离散 17.771%、没有 measured 结果或 +3% 晋级信号，已拒绝，
启动脚本仍使用 16384。P1K 低风险方向因此已收敛；下一步是修正契约后的 P1K
checkpoint，再按顺序进入 P4K scenario-entry baseline/profile。

## 2026-09-23 P32K 算子筛选与 mHC/MoE align 归因

P32K Sparse MLA BH4 特化在精确 `Hq=4/Hkv=1/SKV=80000/topk=2048`
边界上未超过 vendor：主 `SQ=32768` 只有 `0.831×`，因此在服务前
回退。

mHC/MoE align 的“微基准快但端到端无收益”已完成 trace 级纠正。
mHC baseline 虽由 `reference.torch` 路由，编译服务图已执行 FlagGems
`mhc_pre_fused_kernel_hc_mult_4`，所以 isolated reference graph 不是服务的真实
分母。MoE align 的旧候选则因生产 `expert_map` 条件一次都未命中；
C32 trace 中新 kernel 为 0 次，老 stage2 仍为 2772 次。因此历史
`-1.308%` 只是 no-op 候选漂移，不是局部收益被 overlap 抵消。

本轮进一步将 MoE align 特化扩到 EP map 与 `M=64`；16 个 EP map、
4 个 shape 的有效输出精确一致，完整 align 调用加速 2.84×–3.12×。
但候选在 TP16 服务的首批 C64 请求上发生 worker 同步停滞，未通过
服务门禁，因此未进入 P32K A/B/R；两份源码曾按 SHA 恢复，8011 关闭。
2026-09-23 用户明确要求保留该修复并自行测试端到端性能，因此同一候选已按
已验证 SHA 重新装入优化容器。用户随后启动服务，P4K/P16K/P32K/P65536
三轮共 1536/1536 请求成功，服务现仍在运行。调用链复核发现本轮 align
dispatch 选中 `default.flagos`，直接调用 FlagGems 通用实现，绕开本次
FlagGems-vllm 候选入口；没有候选 kernel trace，也没有同配置 A/B/R，
因而不能将跨日期吞吐提升归因于本修复。长输入日志显示 Prefill 期间
Decode 速率急降，P65536 KV cache 曾达 99.9%，下一轮优先验证阶段调度与
KV 容量。详细数值、证据 SHA 和当前状态见
[优化事实与实验台账](../../../models/GLM-5.3-Flash-BF16/ppu/optimize/state.yml)。
