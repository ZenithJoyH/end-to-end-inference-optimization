# max-num-seqs A/B/R 服务编排审计

## 审计对象

- 现有脚本：`restart-candidate-maxseq64.sh`
- 回退草案：`revert-candidate-maxseq32-draft.sh`
- 目标容器：`qwen3.8-flash-opt-candidate-20260919`
- 唯一允许切换的服务：容器内/宿主机端口 `8030` 的 Qwen3.8 vLLM root 及其已冻结子进程树

回退草案未执行，不是运行证据。

## 现有 maxseq64 脚本的最小必修集合

1. **在 TERM 前冻结并重验 PID start ticks。** 现有 `candidate-before-maxseq64.json` 只保存 PID/argv，随后单独 `kill -TERM PID`，存在 PID reuse/TOCTOU 窗口。应保存 `/proc/<pid>/stat` field 22，并在同一 Python 进程中重验 start ticks + 完整 argv 后调用 `os.kill(pid, SIGTERM)`。
2. **将子进程等待从宽泛 model grep 缩小到冻结的 8030 进程树。** 现有第 61–69 行会把同容器任意 `VLLM::EngineCore`/`Worker_TP` 视为目标，可能因无关服务误阻塞；readiness 的宽泛 `pgrep` 又可能在目标已死时被其他端口误判为存活。应只等待 root 的冻结 PID/start-ticks 树，且只向 root 发 TERM。
3. **证明唯一参数变化。** 现有脚本只检查旧服务的 `--max-num-seqs=32`，没有比较完整 argv/关键 env。应冻结 before argv/env，并断言 after 值仅把 `--max-num-seqs` 后的 `32` 改为 `64`。
4. **把 graph 门禁提升到 capture 完成。** 现有 manifest 只判断日志含有 `Capturing CUDA graphs`，进度 1% 也会通过。应要求 `Capturing CUDA graphs (decode, FULL): 100%`、`Application startup complete`、`Asynchronous scheduling is enabled.` 和 `enable_prefix_caching=False`。
5. **使所有证据路径排他且不对活日志做可变 hash。** 现有 before/after/manifest/log 虽有大部分 `test ! -e`，但 `host-ppu-smi.after-maxseq64-launch.txt` 直接 `>` 可覆盖；manifest 中的 live log hash 也会随服务继续写日志而失效。应使用显式 unique run-id 的新目录，通过 `mkdir` 排他创建，并在 readiness/capture 后冻结 startup log snapshot，只对 snapshot 取 hash。

上述五项是满足“精确身份、只停 8030、单变量、graph capture 完成、不覆盖证据”的最小必修集合；不需要改容器、设备、模型、TP、内存比例或 graph 参数。

## maxseq32 回退草案的保护

- 启动前要求用户传入未使用的 unique run-id，并以新 `transitions/<run-id>/` 目录作为排他锁；部分失败证据也会保留。
- 核对容器 ID、image ID、running state，并要求 maxseq64 raw manifest 中的 `service_instance_id` 与当前 8030 PID/start ticks 完全一致。
- 冻结 before 服务的完整 argv、关键 env 和子进程 PID/start-ticks 树；同一 Python 进程重验后只对 root 发 TERM，无 KILL fallback。
- 新服务必须与 before 完整 argv 相等，唯一差异是 `--max-num-seqs 64 -> 32`；关键 env 必须完全相等。
- readiness 期间每次用新 PID/start ticks/argv 重验身份，不用宽泛 `pgrep`。
- raw manifest 记录 before/after service identity、唯一参数差异、代码内容 hash、不可变 startup log snapshot 和 PPU snapshot。

## 执行后仍需的门禁

1. 用 raw manifest 生成唯一的 revert comparison manifest，不覆盖原 `candidate-maxseq32-service-comparison.json`。
2. 执行 `run-graph-replay-smoke.sh` 的两次以上 replay 和 baseline canonical 对比。
3. 只有 smoke 通过后才运行 `maxseq32-*-revert-*` 性能轮次。
4. A/B/R 比较时固定 service manifest 和 service instance ID，不混用 restart 前后两个 PID 的结果。
