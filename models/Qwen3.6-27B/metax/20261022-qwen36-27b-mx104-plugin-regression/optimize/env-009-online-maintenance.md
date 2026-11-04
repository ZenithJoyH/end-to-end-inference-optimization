# env-009: Online environment cleanup and container slimming

env-009 在线维护完成：新root登录/交互Bash已取消旧VLLM_FL_METAX_CONTIGUOUS_SINGLE_PREFILL，其他已核验环境变量及原bashrc内容保持；Docker固化Env与当前模型进程已继承值未改，完全移除仍需以后重建容器。可写层6.18→4.43GiB，实际减少1.75GiB；清理pip下载缓存和两份已归档历史验证缓存。当前API/Engine/两worker PID/startticks/完整环境SHA、源码/全部包版本与health200均未变；当前vLLM/Triton/Inductor缓存及模型、源码、回退备份均保留，无信号/重启/推理或性能测试。

User explicitly authorizes removing residualVLLM_FL_METAX_CONTIGUOUS_SINGLE_PREFILL and slimming B without affecting the running model; preserve other environment. Only mx-104/qwen36-27b-regression-b-20261022, same containerID5b198123/image50b91afb. No restart/signals/model requests/source/dependency changes, no host-wide image prune.

Docker Config.Env is immutable for a running container. Do not edit Docker daemon metadata or recreate the container. The bounded online change is one unset at the end of /root/.bashrc, covering new root login/interactive bash. Keep current API/Engine/worker env bytes and Docker Config.Env unchanged; direct docker exec without a shell still inherits the immutable original value. This is an explicit limit, not a full physical removal claim. All other checked shell vars must exactly match before/after.

Initial Docker SizeRw6631686144B, SizeRootFs25155854336B. Private candidate caches: /root/.cache/pip1103458304B (reproducible download cache), /opt/qwen27-pr638-accuracy-cache997986304B and /opt/qwen27-regression-cache879833088B (prior validation compile caches). Preliminary reference scan finds only its own inline probe command, not a production process; controller excludes its ownPID and repeats all process cwd/exe/fd/maps/cmd/environment plus installed-origin checks, rejecting any actual reference. No permission gaps allowed.

Preserve current /root/.cache/vllm4718043136B, /tmp/torchinductor_root1172205568B, /root/.triton139034624B; all models/tokenizers, four source repos/Git/installed packages, rollback backups and mounted results. Apt/Conda/runtime libraries unchanged. Do not delete arbitrary/tmp or unused-looking packages. Snapshot shell file and exact service identities/full environment hashes (not raw secret env), four source content hashes/all package versions. Prepare exact file manifests; archive+read-back hash verify both old compile caches outside writable layer under current remote case. Only reproduciblepip downloadcache is discarded without archival. Apply only after primary review of planSHA and cache-idle/source/service guards; fail closed on drift. Use low CPU/IO priority.

Command `/public-flash/jinghao/qwen3.6-27B/20261022-qwen36-27b-mx104-plugin-regression/commands/env009-online-cleanup-20261028.py` SHA256 `9c3df10bd7d6f977ad81caeb4c186225addf562b4f3b661efdf93dc4664ce058`, syntax passed. Prepare only archives/snapshots/plan, no removals or shell changes. Outputs /public-flash/jinghao/qwen3.6-27B/20261022-qwen36-27b-mx104-plugin-regression/manifests/env009-online-cleanup-20261028 with0700 permissions. New shell config remains reversible from exact bashrc.before. No optimization/performance resume. Status: online scope completed; immutable Docker/live process env physical removal deferred.

## Primary plan review before apply

Plan SHAe279ed1a0bb97873ce289cced1e37c965bb1f8cb47abbcd6cfde2feec329147d; before snapshotSHA39d00052f48838d2b62716c70bfd10709581b7e37334fb465d86fa8da1c520cb. All source/version/service guards passed before and after preparation; zero actual process/cache references (controller self excluded), no permission gaps. Target manifests stable. Cachedir nominal allocated total2981277696B. OldPR638cache archive203856160B SHA6ae8df94a9a59868688f1a659b8005bb620a2d85346bbdf11950823155c12eb5,11939 regular files readback verified; oldregressioncache archive183704567B SHA57c5f6f69e707eb93ffc5adef59aa829586eb73dc2d51922f003be9898a9d3f5,2908 files verified. Pip cache onlyhttp-v2/selfcheck, no installed-origin references; safe discard authorized by slimming request. Current compilation caches and rollback/source dirs excluded.

Installed Docker update --help confirms no Env mutation interface. Apply same registered script with --apply-plan-sha256 e279ed1a0bb97873ce289cced1e37c965bb1f8cb47abbcd6cfde2feec329147d. Current Docker Config.Env and running process environ remain immutable and unchanged; only new rootBash startup removes legacy variable. No false claim of removing image metadata or live env.

## Completion and exact limitation

Container apply completed2026-10-28 09:49:15 CST; host size/health inspection09:50:25CST. Registered controller receipt /public-flash/jinghao/qwen3.6-27B/20261022-qwen36-27b-mx104-plugin-regression/manifests/env009-online-cleanup-20261028/receipt.json SHAab1b4ffc81fd4de3de3163cef9f301cdaa36bd43c9299d6e37c86dd5daa9bc0f; host-final-verification.json SHA4630af0e768c02e305978fd4e949a3b26b6ae151b019eec17844fb21921a4c90. The final host observation was collected via bounded Docker inspect/du/health in the tool transcript and saved as a separate receipt; destructive changes were confined to the preregistered controller.

| Measure | Before | After | Change |
|---|---:|---:|---:|
| Docker SizeRw | 6631686144B | 4753870848B | -1877815296B (1.75GiB) |
| Docker SizeRootFs reported | 25155854336B | 23278039040B | -1877815296B |
| Visible allocated files in removed roots | 2981277696B | 0 | Nominal2.78GiB, not equal to physical Docker-layer saving |

The inherited image layers are unchanged; removing lower-layerpip cache creates a whiteout rather than freeing underlying image bytes. Do not present2.78GiB nominal removal as actual writable-layer reduction. Two archived historical compile caches occupy203856160+183704567B in the mounted external case, outside container writable layer;14847 files readback SHA verified. Current caches retain exact original allocated sizes4718043136B vLLM,139034624B Triton and1172205568B TorchInductor. Source/rollback directories and installed packages remain.

Only /root/.bashrc changed by appending an explanatory comment and one unset. Original fileSHA7807c02031ab71bd51256b0e9d4344efdd72b7e39eb6051b8aafdf902bfa17d9; afterSHA03220d5576f345f23e4ef29ece8d5df021aa5c420d150f5f9c3796dac5b3057e. Newlogin andinteractive environments equal their original snapshots after removing exactly this variable. Existing shells/processes are untouched; directdocker exec inherits the unchanged Config.Env value1. This is functional cleanup for newBash sessions, NOT true removal from immutable Docker/image config or the running process. No daemon-metadata edit, snapshot-image swap or container recreation performed.

Rollback materials: bashrc.before (0600) and exact original hash in the private0700 evidence directory. Restore only after verifying currentafterSHA to avoid overwriting later user edits. Optional old compile caches can be restored from their hash-verified tar archives to their original empty paths after a fresh reference/identity check; not restored now. Pip download cache is reproducible and intentionally discarded; no packages uninstalled. Historical performance cache states must not be silently assumed still present.

User-requested nondisruptive online scope complete. No automatic action on the deferred immutable-environment part; it requires a separately authorized maintenance/recreation plan if desired. Formal performance remains paused, no precision gate reissued.
