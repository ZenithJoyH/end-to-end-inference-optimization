# 20261010-minimax-m31-w8a8-ppu-tp8-e2e / optimize

本案例固定为 **TP8**。由原混合记录按已记录身份拆分；不表示新的评测或当前运行事实。

<!-- e2e:summary:start -->

- 案例：20261010-minimax-m31-w8a8-ppu-tp8-e2e
- 当前状态：FG-upgraded-minimal-passed-new-formal-pending
- 当前候选：op017 fusion + FG3b76f81 + PPU INT8 provider compatibility; native105+2 and short ERQA6/6 passed; new full accuracy pending
- 下一步：User-requested ERQA rerun complete245/400=61.25%; monitor paused. Await user direction. Preserve old GPQA/Math500/ERQA history; no current-source GPQA gate, no automatic evaluation or performance.

| 实验 | 状态/决定 | 场景 | 文档 |
|---|---|---|---|
| env-002 | retain mandatory private correctness fix; establish correct TP8 baseline; no performance improvement claim | — | [env-002.md](env-002.md) |
| diag-001 | diagnosticcompleted, temporaryobserverrolledback | — | [diag-001.md](diag-001.md) |
| fix-001 | retain mandatory private correctness fix; establish correct TP8 baseline; no performance improvement claim | — | [fix-001.md](fix-001.md) |
| perf-002 | preserve all evidence; retain valid mixed baseline; no implicit retry or contract extension; plan019 independent remaining phase baselines | — | [perf-002.md](perf-002.md) |
| perf-003 | diagnostic complete | — | [perf-003.md](perf-003.md) |
| fw-004 | notretained; safe7 restoration/minimal/original198native rebind passed; stoppedsequence notresumed | — | [fw-004.md](fw-004.md) |
| diag-002 | restore-preflight-blocked-new-external-clients | — | [diag-002.md](diag-002.md) |
| diag-003 | mechanism-confirmed | — | [diag-003.md](diag-003.md) |
| diag-004 | completed-latest-still-affected-issue-submitted | — | [diag-004.md](diag-004.md) |
| op-003 | retain fix002 exactinteger +op003 K256 M64/1024/8192 forP1 basednative3role +7.58/allguards/currentfull164>=81; contributioncomposite only; finalfour incomplete | — | [op-003.md](op-003.md) |
| diag-005 | rootcause-confirmed | — | [diag-005.md](diag-005.md) |
| fix-002 | model-formal-passed-combination-performance-pending | — | [fix-002.md](fix-002.md) |
| op-004 | pending | p1024-d1024-c64-n128 | [op-004.md](op-004.md) |
| diag-006 | latest not promoted to production; current fourstage retained; isolated newer compiler tested in target container | — | [diag-006.md](diag-006.md) |
| perf-004 | completed-baseline-three-phases-passed | — | [perf-004.md](perf-004.md) |
| op-005 | reject prototype for production; keepindependentcorrectness/profiling evidence, productionunchanged | — | [op-005.md](op-005.md) |
| op-006 | productionunchanged; do not implement configpair hook | — | [op-006.md](op-006.md) |
| op-007 | G2pipeline2 rejected; preservecurrentopt2; currentprofilebeforefurtheroperatorchanges | — | [op-007.md](op-007.md) |
| perf-005 | incomplete capture dryrun; originalconfig restored107passed | — | [perf-005.md](perf-005.md) |
| perf-006 | passed allrank phase+roleaudit; currentopt2 restoredminimal107passed | — | [perf-006.md](perf-006.md) |
| op-008 | retained-by-explicit-user-instruction | — | [op-008.md](op-008.md) |
| op-009 | not deployed; no production change | — | [op-009.md](op-009.md) |
| op-010 | notdeployed;stopG2configurationstrategy | — | [op-010.md](op-010.md) |
| op-011 | notdeployed, no modelsourcechanged | — | [op-011.md](op-011.md) |
| op-012 | rejected-microcriterion | — | [op-012.md](op-012.md) |
| op-013 | retained by explicit user2.17% decision; new candidate fullGPQA169/198 passed; handoff for user benchmark | — | [op-013.md](op-013.md) |
| perf-007 | complete phase diagnosis, root restored and105+2 passed | — | [perf-007.md](perf-007.md) |
| op-014 | user-retained exact evaluated M16/M32 candidate; fresh107/graph38 and native score rebind/check passed; quiet manual E2E handoff complete; native performance criterion remains failed | — | [op-014.md](op-014.md) |
| op-015 | rejected | — | [op-015.md](op-015.md) |
| op-016 | {"result": "retained", "basis": "all three pre-frozen native comparisons passed, B/R drift within2%, latency guards passed", "current_service": {"path": "/mnt/nfs/users/jinghao/minimaxM3.1/optimize/20261010-minimax-m31-w8a8-ppu-tp8-e2e/profiles/op016-services-20261016-01/retained/service-verified.json", "sha256": "7a7013503b3c35f17788484320b199cdbb252fd30440987a69cae59391c9a238", "live_identity": {"exists": true, "state": "S", "startticks_match": true, "argv_match": true}, "fv_tree": "f3ef1408546bdef4a89f7d7ec9ec8ddc795b3997668bbc52d70afe24f8419045", "name": "MiniMax-M3.1-opt5", "health_http": "200"}, "accuracy": "new op016169/198=85.35%>=81; current retained instance same-source native rebind/check passed", "full_four_scene_acceptance": "incomplete"} | — | [op-016.md](op-016.md) |
| env-003 | completed-minimal-passed-formal-pending | — | [env-003.md](env-003.md) |
| env-004 | completed-minimal-passed-formal-pending | — | [env-004.md](env-004.md) |
| op-017 | fusion integrated; new formal166/198=83.8384% passed81%; awaiting user E2E performance | — | [op-017.md](op-017.md) |

| 场景 | 角色 | 指标 | 数值 | 单位 | 范围 |
|---|---|---|---|---|---|

<!-- e2e:summary:end -->

<!-- pr-documents:start -->
## 交付说明

[pr-001](pr-001.md) · [pr-002](pr-002.md)
<!-- pr-documents:end -->
