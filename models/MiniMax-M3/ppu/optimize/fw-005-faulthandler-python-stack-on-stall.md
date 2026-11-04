# fw-005：faulthandler Python 慢路径栈

## 契约

- 分类：`framework`
- 父目标：`p1024-d1024-c64-n128`
- 状态：`complete`
- 假设：`fw-004` 中 CPython 对象/字典/字符串构建是某个可识别的 Python 上层路径，而不是泛化的解释器随机采样。

## 诊断设计

- 启动独立诊断服务；所有 baseline 参数不变，仅通过任务目录下的 `sitecustomize.py` 注册 `faulthandler` all-thread 栈转储。
- workload：无 profiler `P1024/D256/C64/N128`，最多 6 轮。触发与 fw-004 一致：同一客户端先观察到 PPU max `>=50%`，随后 16 卡连续两秒 max `<=20%`。
- 命中后只向 4 个代表 Worker 各发送一次已验证的诊断信号，不重复触发。
- 所有本轮时延均为诊断数据，不与 baseline 计算收益。
- 停止：首次命中或 6 轮用完；完成后必须恢复无 `sitecustomize` 的原始服务，并重做 graph/health/文本 smoke。

## 结果

- v1 (`SIGUSR2`) 和 v2 (`SIGUSR1`) 均成功复现首轮慢路径，但底层运行时在 `sitecustomize` 之后重新占用了两个常规用户信号，栈文件为空；两次作为诊断方法证据保留，不作性能结论。
- v3 改用启动后确认未被占用的实时信号 40；先在 API 进程验证生成 1500-byte Python 栈且 health 通过，再执行最多 6 轮的触发捕获。
- v3 首轮命中：output throughput `319.13 tok/s`，单请求 max ITL `7.139 s`；后五轮稳定在 `462.95–466.77 tok/s`，max ITL 约 `0.777 s`。这些是诊断时序，不作正式收益。
- 4/4 代表 TP Worker 的主线程共同停在 `FlagGems/src/flag_gems/utils/models/sql.py:171 build_sql_model_by_db`，由 `get_config -> ConfigCache.__contains__ -> LibTuner.run` 触发 SQLAlchemy `automap.prepare()` 对 SQLite schema 的全库 reflection。上层路径是 `index_linearized...m_32_n_32 -> flag_gems.ops.index -> model_runner._prepare_input_ids`。
- 当前 Triton 3.6 配置库约 6.7 MB，包含 605 张表；16 个 worker 在新 config table 首次查询时同步做全库 reflection，解释了全卡设备空闲而 worker 各占一核的现象。
- 诊断服务已停止，无 `sitecustomize` 的原始服务已恢复，graph capture、health 和北京文本 smoke 通过。

## 证据

- `/mnt/nfs/users/jinghao/minimaxM3/20260921-minimax-m3-ppu-e2e/profiling/fw-005-faulthandler-python-stack-on-stall`
- `/mnt/nfs/users/jinghao/minimaxM3/20260921-minimax-m3-ppu-e2e/profiling/fw-005-faulthandler-python-stack-on-stall-v2`
- `/mnt/nfs/users/jinghao/minimaxM3/20260921-minimax-m3-ppu-e2e/profiling/fw-005-faulthandler-python-stack-on-stall-v3`
- `/mnt/nfs/users/jinghao/minimaxM3/20260921-minimax-m3-ppu-e2e/transitions/fw005-restore-no-sitecustomize-service`

## 决定

`diagnostic_complete_no_code_change`。下一实验 `fw-006-flaggems-targeted-schema-reflection` 只将 SQLAlchemy reflection 从整个数据库限制为当前请求的 table，不改 config key、config 值、kernel 或调度语义。
