# perf-016：当前 acc-011 配置的 P16K 三阶段入口基线

## 冻结范围

- `baseline` / `performance_only`；父目标为 `p16384-d1024-c64-n128`，不是正式验收，也不继承已重启服务的旧精度 gate。
- 当前候选组合：maxseq32、batched-tokens4096、async、FULL_AND_PIECEWISE graph、QSA 无静态边界、native `mm`、FlagGems `mm_out`、私有 FlagGems SQLite 修复。基线服务在 PPU0–7 的 8010 顺序运行；PPU8–15 的 8000 保持原样且空闲。
- 服务为同一优化容器内 8010 的新实例，显式 `--no-enable-prefix-caching`；事前冻结原 argv、关键环境、PID/start-ticks、容器身份，完成后精确恢复。graph capture 和两次 changed-input replay 必须有原始证据。
- Prefill：P16384/D1/C32/N64，突出 prompt 处理，仍含排队/调度/单 token Decode。主指标 total-token throughput，TTFT 守护。
- Decode：P16384/D1024/C32/N64，突出长 Decode，仍含长 prompt Prefill。主指标 output throughput，TTFT/TPOT/ITL/E2E 守护。
- Mixed：P16384/D1024/C64/N128，原目标 finite batch，观察 Prefill/Decode 干扰及排队。主指标 output throughput，TTFT/TPOT/ITL/E2E 守护。
- 每阶段 3 次预热 + 3 次正式轮；预热最后两轮主指标相对 spread 不超过 10%；保留全部正式轮，零失败。超时每轮 3600 秒。稳态准入失败时标 `incomplete`，不事后剔除慢轮。
- 诊断预算：每阶段最多 90 分钟；不能完成则保存部分产物并标 `deferred-too-slow/incomplete`，转入缩减 milestone，不推算目标吞吐。

## 前置事实与假设

旧 `perf-015` 三阶段已完整，但其 maxseq64、M64 tuned MoE 和 native `mm_out` 与现态不同，不能用作现态基线。`op-027` 只覆盖 D128。当前 C64 超过 maxseq32；需要三阶段与队列/KV/抢占证据才能区分准入成本和 Decode 代价。

2026-09-24 只读预检：8000 PID/start-ticks `1335499/294745394`、8010 `3432267/296610886`，健康且 running/waiting 均为 0；未发现评测客户端。远程任务根目录为规范绝对路径，owner UID 0、权限 0775，可用空间约 9.3 TB；新案例目录尚不存在。

## 执行和结果

状态：`complete_three_phase_scenario_entry_performance_only`。远端唯一案例目录为 `/mnt/nfs/users/jinghao/qwen3.8-flash/20260919-qwen38-flash-next-ppu-e2e/perf016-current-acc011-p16k-three-phase-entry-20260924`。8010 原实例 `3432267/296610886` 已精确停止，性能实例 `3975078/296772273` 完成测量后精确停止，原 argv/env 已恢复为新实例 `2641118/297617620`；8000 仍是 `1335499/294745394`。性能实例的 graph capture、两次 changed-input replay 和显式 prefix cache disabled 均已核验。恢复回执为 `services/original-restored/restore-receipt.json`。

Prefill 已完成：3 预热 + 3 计量，每轮 64/64、零失败。最后两次预热总 token 吞吐 5717.071/5716.224 tok/s，spread 0.0148%，准入通过。正式三轮 5712.576/5714.961/5713.816 tok/s，中位 5713.816 tok/s；P99 TTFT 91760.675/91755.465/91799.686 ms。原生回执 `performance/perf016-prefill-baseline-01/run-record.json`，SHA-256 `b1bbe948108699f9311aee91c3d1f1668176a9ee49c14f9597d231bdd7a8c57c`。这是阶段专项，不是完整 P16K/D1024 目标吞吐。

Decode 已完成：3 预热 + 3 计量，每轮 64/64、零失败。最后两次预热输出吞吐 180.085/180.740 tok/s，spread 0.3628%，准入通过。正式三轮输出吞吐中位 181.107 tok/s、duration 中位 361.864s；P99 TTFT/TPOT/ITL/E2E 的逐轮中位分别为 91902.568/168.277/751.929/262773.379 ms。原生回执 `performance/perf016-decode-baseline-01/run-record.json`，SHA-256 `7262bd3da8914d884fe70c24504ae1031d80f2850cb1d64af9ede612888ea131`。这是 C32 长 Decode 专项，不能替代 C64 Mixed。

Mixed 已完成：3 预热 + 3 计量，每轮 128/128、零失败。最后两次预热输出吞吐 182.730/182.754 tok/s，spread 0.01294%，准入通过。正式三轮输出吞吐中位 182.540 tok/s、总 token 吞吐中位 3103.183 tok/s；P99 TTFT/TPOT/ITL/E2E 的逐轮中位分别为 266824.750/169.826/753.610/439280.180 ms。原生回执 `performance/perf016-mixed-baseline-01/run-record.json`，SHA-256 `cfd12ccd5c6e6adbe86f7a92bb4b5cc5a9e739bfbd21ec549eb0de0ef71c78a4`。测量时 C64 观察到 running32/waiting32、KV 约 20%、抢占为 0；这支持检验 maxseq 接纳瓶颈，但尚不能证明调大上限会改善端到端结果。

执行中发现第一版 service manifest 从旧 8000 模板继承了错误的描述性字段 `performance_context.idle_peer_service="8010 on PPU8-15"`。实际目标 URL、8010 进程 argv/env、PPU0–7、`device_ids`、服务实例、graph 和容器身份均已核验正确；真实空闲对端是 8000/PPU8–15。该字段不影响推理执行，但不能改写已被 Prefill run 以 SHA 绑定的 manifest。保留原件和该问题记录，另建只修正此元数据的新 manifest 用于后续阶段；Prefill 数值仅在原始回执完整且所有实质身份字段正确时作为带注释的阶段证据，不与另一阶段做数值 A/B。

## 结论边界

本轮只建立当前配置的无 profiler P16K 三阶段入口基线，不与旧不同配置结果计算加速比；`fw-016` 的任何性能结论须另做同卡 A/B/R。当前服务实例重启后，正式精度 gate 仍须重新取得。
