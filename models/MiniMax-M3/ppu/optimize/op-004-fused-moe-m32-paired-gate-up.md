# op-004：M32 fused MoE Gate/Up 共同 dot 路径

## 契约与预冻结判断

- 分类：`operator/improve`；父目标：`p1024-d1024-c64-n128`，重点是 Decode/Mixed 中 graph M32 的 BF16 fused MoE。
- 瓶颈：历史 `prof-001` 的 rank0 `fused_moe_kernel` 累计 7.694/20.286 秒设备活动，M32 graph bucket 约 497 次；这是候选排序证据，不是当前服务端到端时间占比。
- 单变量：T-Head 现有 GEMM1 kernel 的 `PAIR_GATE_UP_DOT=False→True`。其代码在一次 K 循环内计算 Gate/Up 两组 dot，而当前默认分两轮循环；`op-002` 未测试这个算法分支。保持所有 tile/stage、权重、路由、dtype 和生成配置不变。
- 形状：MiniMax-M3 `E=128`、`hidden=6144`、每 TP `intermediate=192`、`top-k=4`、BF16、SiLU、无 bias；以 M32 为主，M1/2/4/8/16 为 graph/fallback 守护。
- 第一轮是独立进程的完整 `ops_experts_impl` microbenchmark，不编辑运行服务源码；旧路径为数值 oracle，预冻结 `atol=0.12,rtol=0.03`。搜索与独立确认分开，使用同输入、同权重、同计时边界。
- 晋级门槛：M32 完整调用至少快 10%，且其他生产 graph bucket 不明显退化，数值、目标 graph capture 和至少两次 replay 通过。否则拒绝，不进入服务集成。
- 若晋级：先用私有源码副本及 capability/shape guard 保留默认 fallback，做最小回归、P1K Decode/Mixed 无 profiler 的同配置 candidate/revert，Prefill/TTFT 守护，并重跑正式 198 题 GPQA（高风险算法分支）。只有同服务精度 gate 后才运行正式性能比较。

## 资源与变更边界

- 用户于 2026-09-23 明确允许停止优化容器内的 8013 服务供测试。停服前验证 `minimaxM3-opt-20260921` 内精确进程、启动参数、日志 fd 与端口；只发送 TERM 给该实例，等待 16 卡计算进程排空，不停止适配源容器或其他服务。
- 8013 服务 `max_model_len=100000`，不同于上一轮 GPQA gate 绑定的已退出 8023/131072 实例，不能用作可比服务或继承其 gate。
- 当前 Plugin/FlagGems 既有未提交改动属于前序候选或用户工作，保持原样；第一轮 microbenchmark 仅在自身进程临时覆盖 `get_default_config`，退出即恢复。

## 状态与证据

- 状态：`complete / rejected_no_source_change`。用户允许的 8013 进程经过容器、PID、启动 tick、命令及日志路径精确匹配后收到 TERM；进程退出、端口关闭，`ppu-smi` 显示 16 卡无计算进程。未停止源适配容器。
- 单卡完整调用筛选（PPU-ZW810E，`triton.testing.do_bench`，30 ms warmup + 150 ms rep，p50；该搜索不是 graph 或正式端到端证据）：M32 当前 `0.45224 ms`，paired `0.58892 ms`，慢 `30.22%`；M16 当前 `0.31316 ms`，paired `0.36652 ms`，慢 `17.04%`。
- 所有 M=1/2/4/8/16/32 的 BF16 输出对照通过（`atol=0.12,rtol=0.03`）；M16/M32 的 GEMM1 fast path 有命中。M1/2/4/8 未命中 paired GEMM1，微小计时差异不视为收益。
- M32 未达至少 10% 完整调用改善，反而明显退化，因此不做 graph、服务最小回归、正式 GPQA 或端到端集成；这些项目为 `not_run`，不是通过。未修改 FlagGems-vllm 源码，实验进程退出即恢复配置函数。
- 旧算子筛选：`/mnt/nfs/users/jinghao/minimaxM3/20260921-minimax-m3-ppu-e2e/results/op002-fused-moe-config-screen.json`。
- 旧 TP16 profile：`/mnt/nfs/users/jinghao/minimaxM3/20260921-minimax-m3-ppu-e2e/profiling/prof-001-p1k-mixed-stall/summaries/phase-rank-analysis.json`。
- 新控制命令与结果将在同一远程 case 的 `commands/`、`results/` 下使用不覆盖的 `op004` 文件名；记录实际 SHA、服务转移和失败/回退结果。
- 已保存停服命令：`/mnt/nfs/users/jinghao/minimaxM3/20260921-minimax-m3-ppu-e2e/commands/op004-stop-8013.sh`，SHA256 `9a0efe59f21120a2d5397281c1fd1ac14d360d5268cdd136efd171f9dd72e3fe`。
- 已保存基准脚本：`/mnt/nfs/users/jinghao/minimaxM3/20260921-minimax-m3-ppu-e2e/commands/performance/benchmark-op004-paired-gate-up.py`，SHA256 `63c5d90271507dd25f56cff746ab808918cbc3238f30d827b123c915f08b53b6`。
- 原始结果：`/mnt/nfs/users/jinghao/minimaxM3/20260921-minimax-m3-ppu-e2e/results/op004-paired-gate-up-search.json`，SHA256 `e4904cbd6978d2946fa4f59c4ac44b46356e215923da57fa5a40fa894ffd5ef9`。
