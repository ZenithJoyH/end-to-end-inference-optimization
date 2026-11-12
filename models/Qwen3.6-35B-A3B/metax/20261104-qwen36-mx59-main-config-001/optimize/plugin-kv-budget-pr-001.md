# plugin-kv-budget-pr-001

用户2026-11-05明确授权：将当前KV cache显存预算修正单独提交PR，目标release/0.2，仅相关改动。

基准：upstream release/0.2@6e11d0ab687247fdf4347a52788ec4f2baf57c79（vLLM0.20.2），独立临时克隆 /private/tmp/vllm-fl-kv-budget-pr-20261105-001。生产范围仅worker.py调用和纯CPU memory_policy.py，不携带GDN/采样/MoE/图像拆批/配置/依赖变化，独立于GDN PR699。

设计：框架内存预算，A1/A3/E2；复用WorkerFL.determine_available_memory及真实before_create快照，只在MetaX自动profiling分支补扣一次正初始nonTorch占用，结果下界0。既有显式kv_cache_memory_bytes与其他平台路径保持；无新env、模型/路径/shape硬编码。helper语义保持当前部署30ca53eb；清晰类型/格式整理不改变公式。非KV数据读写/量化/数值kernel，无graph地址或stream调度变化。删除条件：框架已在相同预算路径计入全量初始nonTorch时移除此补偿，避免双扣。

计划验证：直接纯CPU算术边界+实际Worker方法AST执行（仅移除依赖Torch的decorator，依赖桩仅验证控制路径）验证MetaX/其他vendor/显式覆盖/profile异常，执行语句来自提交源码，不复制公式作为路径实现。基线应暴露漏扣；不可把这些当硬件或模型通过。现容器同预算修复的历史短程/GPU证据单独注明为历史，不当本次release提交新验证。不操作运行容器、GPU、模型服务，不发模型请求；PR保留有效吞吐/覆盖边界，无性能收益或全部OOM消除声明。

适用规范：C1沿用返回int与显式覆盖，B4 profile异常不吞不重试，D1无开关，E1/E3无cache读写与stream变更，F1/F2新增接线与边界，F4/F7提交前格式/lint/单元检查及未测披露，F5单主题。预期3文件（worker、helper、test），不上传本项目记录/内部数据。

发布状态：准备中。

## 发布前检查

11项CPU测试通过（4算术/7实际Worker方法控制路径）；用未改release worker替换候选重跑7项接线测试，有且仅有2项失败（初始占用漏扣及耗尽预算未归零），无fixture错误。已恢复并验证最终worker SHA256 `1ad4d858dd6a88acbd76a9f19596ff442cd98396f19fa7782a4b1a9de10d0422` 与当前部署精确相同。helper保持同return表达式，仅整理类型/注释/格式；当前requested在初始化由total_memory*util产生float，类型标注相应接受int|float，结果int。

全部适用pre-commit hooks通过，无SKIP；新增helper/test单独ruff check+format通过；git diff --check与AST通过。基准6e11d0a，恰3文件（worker+helper+test），其余GDN/采样/MoE/依赖/配置原样不带入。CPU测试不能代替硬件启动/graph/精度/吞吐；本次未执行这些测试，不重启运行容器。

## Published PR (current final status)

Ready for review: [vllm-plugin-FL #702](https://github.com/flagos-ai/vllm-plugin-FL/pull/702), open/non-draft, base=release/0.2. Head d1b0f14d1658670c6dbc97760b3cc5c57df1677a, parent=6e11d0ab687247fdf4347a52788ec4f2baf57c79, branch ZenithJoyH:fix/metax-physical-kv-budget-20261105-001. Verified 3 changed files, 1 commit, +213/-0; no GDN PR699 dependency or unrelated container edits.

Final SHA256: worker.py=1ad4d858dd6a88acbd76a9f19596ff442cd98396f19fa7782a4b1a9de10d0422; memory_policy.py=667e8ca3f890526cca39f4e3f8b7ab42909ae1441b060d940ae315f62ae0a3b1; test_memory_policy.py=9efb089af87775f198d08e82f7f5e5537d359fbbb0a3048cc5956e94d29e252d.

11 CPU tests and applicable pre-commit hooks passed. The unmodified Worker has exactly two expected assertion failures in the seven wiring tests. No GPU/model startup, graph, accuracy or performance rerun for this release patch; disclosed in PR. No internal model results uploaded.

CI triggered on PR creation: https://github.com/flagos-ai/vllm-plugin-FL/actions/runs/41955717045 was in_progress at final check; labeler passed. Commit status list was empty at this observation, so no new CLA assertion. CI not yet claimed passed.

## Requested-limit hint follow-up (pre-record)

User identified a source-level inconsistency after warmup: auto budget deducts initial non-Torch occupancy, but the requested-limit manual hint still omits it. No new OOM is claimed. Scope: only correct the MetaX requested-limit hint in compile_or_warm_up_model plus tests. Keep self.non_torch_memory as the profiling increment, and preserve the initial-free-memory hint (its base already accounts for pre-existing occupancy). Reuse physical_kv_cache_budget with profiled weights/activation/increment plus graph and existing redundancy buffer; no new helper/API/config.

Validate actual warmup method host logic with device/warmup doubles, nonzero graph bytes and independent expected literal hints. Preserve worker bookkeeping and free-memory hint, check other vendors, explicit override and no-graph mode. This is CPU wiring validation, not actual GPU warmup/capture or an OOM reproduction. Amend existing PR702 on release/0.2 as a new commit; no container/service changes.

Warmup-hint follow-up validated before push: 4 new warmup method tests reproduce exactly two failures against PR702 d1b0f14 (both requested-limit hints too high by initial occupancy; free-based hints correct). Candidate now passes all15 tests. Test positive scenario uses compile warmup + kernel warmup + capture callback before reading the real DEBUG message: requested270MiB versus free-based370MiB, with graph30MiB and existing buffer150MiB. No-graph300/400MiB, non-MetaX370/370MiB and explicit-override/no-hints also covered. These are host lifecycle doubles, not real GPU warmup/capture or OOM validation.

AST audit: determine_available_memory unchanged from d1b0f14; every assignment to non_torch_memory unchanged; gpu-limit hint unchanged; helper bytes unchanged. Production diff only8 added lines in requested-limit hint. All applicable pre-commit hooks and diff check pass. No deployed container/source/service changes.

Warmup follow-up published in existing PR702: commit42b27b3ed5f2259e2a3a1d5f2a5163b5d283d3c6, parent d1b0f14. Exactly2 files in the new commit (worker +8 lines, tests +121/-3); total PR still only original3 related files, base release/0.2. Head update used expected-head lease and fast-forward, preserving the previous commit. PR testing description updated to15 CPU tests and explicit host-double warmup limitations; no OOM reproduction claimed.

Follow-up final source SHA256: worker.py3e8963cd52bf3ca4c1c3e66ce052fd90f57ec83b6fff14f605568b46d8d4bf9f; test_memory_policy.py22c427b15da905b2a519e439f2cef8d02161bc8953fcf83b6b12a74abf869b1f. Deployed worker remains unchanged by this PR-only task; earlier byte-equality to deployment is historical for d1b0f14, not a claim that this new manual-hint fix is deployed.

## Deployment alignment (pre-record)

User explicitly requested applying latest PR to current container Plugin. Target mx-59/qwen36-35b, IDb96e1f3a3c61bcf2946803b8d88aace5bcff7599466023de86007db9e9fb4094/image9f420f54. PR702 current head42b27b3, exact3 files fetched and byte-compared with locally tested candidate. Private Plugin /workspace/vllm-plugin-FL outside existing /public-flash and /data binds; no mount/source sharing changes.

Read-only preflight: service is active on GPU4/5/8020, original0.9/full-decode-only/no-prefix parameters. No stop/restart or hot reload; preserve exact current API/EngineCore/workers PID/start_ticks/full-argv SHA before/after. Disk update applies to next process load; do not claim active process has reloaded it.

Apply exactly worker.py1ad4d858->3e8963cd, helper30ca53eb->667e8ca3 (same formula, annotation/doc only), test688cf260->22c427b1. Use SHA CAS for all3, exact PR SHA/content checks, retain original bytes+metadata+diff, full four-package source manifest before/after; only expected3 changes. Run the deployed standalone15 CPU tests with no Torch/model/GPU workload; compare real import origin via find_spec and keep source private. Failure triggers guarded byte rollback; no replay/overwriting old artifacts. Remote archive: /public-flash/jinghao/qwen3.6-35B/20261104-qwen36-main-config-compat-mx59-001/kv-pr702-align-20261105-001.

Deployment commands frozen: apply-container.py SHA2569a7b2a5fe09554ec535770d49b6f4160aecd59b9b79c71920ba0466f1c03bf1b; apply-host.py95082c7eb7c757cc1b61d3de73f988bca0c3c1065b5ca25f26cdd3bb0fe6b872; payload.jsona411a1351d1260e2f13f8600fa4af564b28f74428140d18db88c7b775938c66d. Guard all3 old SHA + exact container/image/private mounts +4 exact service identities; active service not restarted.

## Deployment alignment completed

Native exit0; application status passed. mx-59/qwen36-35b private Plugin now exactly matches PR702@42b27b3 for the3 intended files. Worker3e8963cd, helper667e8ca3, test22c427b1; deployed standalone15 CPU tests passed. Compared6517 package/source records before/after: only these3 changed, other6514 equal. Full model/FGV/Gems numerical code, Plugin GDN/sampler/MoE and startup config remain unchanged. File owner/group/mode preserved; original bytes and diffs retained under backup/.

Actual import origin vllm_fl points to /workspace/vllm-plugin-FL/vllm_fl/__init__.py. Exact current API/EngineCore/TP0/TP1 PID/start_ticks/complete-argv SHA identities remained unchanged. No service restart or hot reload, no model/GPU test or requests. Active service retains already loaded prior code; the new requested-limit DEBUG hint is picked up on the next process start. Existing accuracy/performance bindings are not rebound to a future restarted service.

Artifacts: /public-flash/jinghao/qwen3.6-35B/20261104-qwen36-main-config-compat-mx59-001/kv-pr702-align-20261105-001/{application.json,native-result.json,source-before.json,source-after.json,service-before.json,service-after.json,origins.json,tests.stderr.log,backup/,commands/}. Rollback requires current3 candidate SHA guards and restoring each backed-up file's original metadata/bytes; do not overwrite later edits or restart active service automatically.

Final receipt SHA256: application.json dd975540abeef8ae1ec28f2011602bb96c0ec414118ab8fe0f82ab51efb8dbad; source-before.json d28456bd6bc8cb86f8584740c92b4ed6c59c3ab5e0c0507fe0af867a348d41ce; source-after.json 4e8b9289aba4b537cc3d59cfc21280ee65f204dd2368b4fd0d76ca6b0ab428b7.

## Review response — 2026-11-06

User authorized responding to current review or adjusting the PR. Reviewer ceci3 asked why MetaX needs the additional memory accounting. Verified current head42b27b3 and the full snapshot/profiling path; replied in [the original thread](https://github.com/flagos-ai/vllm-plugin-FL/pull/702#discussion_r4488418891) explaining absolute requested memory versus incremental non-Torch profiling, an explicitly illustrative arithmetic example, and the MetaX-only validation scope. Explicitly noted that device-wide occupancy does not identify a specific library leak, that the issue is not proven exclusive to MetaX, and that the free-memory recommendation must not deduct initial occupancy again. No code change or push was needed for this question; thread remains unresolved for reviewer confirmation.

All 3 PR file Git blob hashes matched the local verification copy. Re-ran `python3 tests/unit_tests/test_memory_policy.py -v`: all15 CPU tests passed; `git diff --check` passed. No GPU/model requests or container/service changes; no new claim of OOM prevention or performance validation.

## Withdrawn after reverted-service validation — 2026-11-06

用户明确要求关闭#702，并在PR说明回退验证结果及撤回原因，保留补丁和测试记录。已发布[撤回说明](https://github.com/flagos-ai/vllm-plugin-FL/pull/702#issuecomment-6681144523)，随后GitHub API确认PR状态closed、merged=false，关闭时间2026-11-06 16:59:29（Asia/Shanghai）。head仍为42b27b3ed5f2259e2a3a1d5f2a5163b5d283d3c6，分支fix/metax-physical-kv-budget-20261105-001未删除，提交、差异、测试与review记录完整保留。未改PR原描述/测试历史，未改容器或运行服务。

说明记录了回退后当前服务TP2、显存利用率0.9、prefix-on，模型默认采样1/.95/20、思考开启、65536输出上限、C64完整ERQA400：400 HTTP200、零失败/超时，245/400=61.25%；两题length空final按错计，连续日志与终态复核未观察到OOM。引用本地[完整实验记录](erqa-kv-revert-default-c64-20261106-001.md)，终态报告SHAca244767d6efcc7ba11c9cb6dc9c0babb174f1a3e0f86d0beedc361e4d24a5b1。

撤回基于运行必要性证据不足，而非认定源码计账差异不存在。GDN导入注册也在重启前回退，未建立纯KV单变量因果；额外扣减会降低KV容量，其吞吐影响未验证。以后有可复现运行问题、初始占用实测和受控对照时可重新评估。已有补丁及15项CPU测试结论不改写，不宣称普遍不会OOM。
