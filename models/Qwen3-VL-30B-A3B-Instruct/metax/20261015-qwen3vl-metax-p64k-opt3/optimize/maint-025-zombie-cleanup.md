# maint025: Reap orphaned zombies without restarting the container

User requested cleaning defunct processes in the current container on 2026-10-19. Target is the existing isolated `qwen3vl-p64k-opt-20261015` on mx-59. The protected source container and other workloads remain out of scope.

Read-only inventory/connectivity and runtime checks found180zombies, all parented by PID1 (`sleep infinity`). There is no live vLLM/benchmark process in this target: only PID1 and six existing interactive bash sessions. PID1 is single-threaded, sleeping and untraced. Host has CAP_SYS_PTRACE; neither host nor container has gdb. The underlying cause is a non-reaping container keepalive process, following previous model/validation process exits. Zombies cannot be killed directly.

Planned maintenance control is `commands/maint025-zombies-20261019/reap_zombies.py` under the existing remote case. It first proves the procedure on a disposable sleep parent with four exited children. Only after that succeeds, the apply mode requires the exact container identity, idle sleep PID1, single thread, unchanged start time, all zombies under PID1 and no active workload. It briefly seizes PID1, executes nonblocking wait4 for each exact recorded child using an existing syscall instruction, restores all general registers, and detaches. No text/stack/FP memory or signal disposition is changed. Recheck requires zero zombies, same container start identity and preserved live process PID/start pairs. No container/model restart or source/config changes are authorized by this script. This one-time cleanup does not install a permanent reaper.

Each script is saved before execution. Raw process details and final receipt stay under the remote case; only the verified conclusions and hashes are recorded locally. Validation and completion are pending.

Kernel interface references: [ptrace](https://man7.org/linux/man-pages/man2/ptrace.2.html), [waitpid](https://man7.org/linux/man-pages/man2/waitpid.2.html).

## Completed cleanup

Disposable-parent selftest passed: all four exited children reaped, complete general-register restoration verified, parent still sleeping and untraced after detach. The exact saved script SHA256 is `e6856c7ac09396551120a1fd31990e6444cb5685cd03f96b2cf66aa310a744bc`. The guarded target apply then reaped all180recorded zombies; zero remained. The same container ID/start timestamp, PID1 start identity and all six bash PID/start identities were preserved. No restart, process termination, source/configuration change or signal-disposition change occurred in the target. The only killed process was the disposable selftest sleep process created by the maintenance script.

Native result: `/public-flash/jinghao/qwen3-VL/20261015-qwen3vl-metax-p64k-opt3/results/maint025-zombie-cleanup.json`, SHA256`07bb4e8a651f8a363f2570c055e7ae0fabf2a398c3ed19cd14877942f1d9d0be`. Selftest/apply logs are `logs/maint025-selftest.log` and `logs/maint025-apply.log` in the same remote case. PID1 remains sleep infinity; this is a completed one-time cleanup, not permanent zombie prevention. Independent delayed recheck at2026-10-19T02:44:07Z passed: zero zombies, six bash sessions, unchanged container start, PID1 sleeping/untraced. Receipt `results/maint025-independent-check.json`, SHA256`b66e0226512e22bed13890b4c2f9db1c75a4ea8d1e84bc07e8a586e2b5b4c319`.
