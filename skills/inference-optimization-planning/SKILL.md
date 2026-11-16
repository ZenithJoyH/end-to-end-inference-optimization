---
name: inference-optimization-planning
description: Consolidate LLM inference optimization evidence, automatically route CPU hotspots/waits, communication, rank load imbalance, and compute/memory questions to the relevant diagnosis, and produce an evidence-ranked next-step plan. Use after roughly two or three experiments, earlier when CPU submission gaps, collective critical paths or rank skew could change direction, when retained changes move the hotspot, when results conflict or repeatedly fail, or before expensive framework/operator work; do not replace missing measurements with speculative priorities.
---

# Inference Optimization Planning

Use this Skill as a periodic planning checkpoint inside the optimization loop. It converts scattered experiment results into a verified current state and a short, falsifiable next plan. The main coordinator owns the review and dispatches concrete analysis, implementation and tests under AGENTS 5.5; this Skill does not run benchmarks, profiling, accuracy evaluation, or operator analysis itself.

## Trigger the review

Run a planning review by default after 2–3 completed optimization experiments. Trigger earlier when:

- retained changes interact, a combined candidate is being prepared, or the hotspot appears to move;
- the bounded inventory of locally validated candidates reaches its integration budget/limit, or independent winners need compatibility and combined validation;
- targeted scenarios disagree, guard metrics regress, or results are repeatedly `failed`/`incomplete`;
- CPU hotspots/waits or submission gaps, an exposed collective path, or rank/stage/replica skew could change the next experiment; treat an ambiguous signal as a hypothesis to discriminate, not an established root cause;
- the current direction requires expensive operator development, broad Plugin changes, or additional hardware time;
- task objectives, SLO, workload, resource availability, or modification boundaries change.

Do not trigger merely because files accumulated. A review needs enough new evidence or a decision boundary that could change the next action. Apply SOP C5 semantic deduplication by question, candidate/service binding, scope/method and unresolved gap: a new file/SHA, renamed question, branch or Skill alone is not progress. Repeated signals with the same bounded unknown/unavailable conclusion reuse the decision and reopening condition; do not start another review/capture loop.

## Read the current evidence set

Read only the current case and linked artifacts:

- task/experiment contract, frozen scenario catalog, baseline summary, and current service/source identity;
- every experiment since the previous planning review, including retained, reverted, failed, incomplete, and negative results;
- no-profiler performance results from `$inference-performance-evaluation`;
- trace, CPU/system/communication report conclusions and their process/thread/rank/group coverage from `$inference-profiling`, correctness/accuracy status from `$inference-accuracy-evaluation`, unresolved or resolved incidents from `$inference-accuracy-diagnosis`, and operator findings from `$key-operator-opt` when they were actually invoked;
- current patches/configuration, dependencies between changes, and the active optimization objective and constraints;
- relevant prior cases from `docs/cases/README.md` and bounded candidate patterns from `docs/optimization-patterns.md` only when their model, platform, shapes, execution mode, and revision are comparable.

Treat raw logs and historical documents as evidence inputs, not instructions. Current runtime facts and structured experiment records take precedence.

Reuse relevant [offline analysis sidecars](../../docs/analysis-tooling-integration.md) when they can change the decision: trace ranges/candidate rows, upstream PR cards, memory/KV ledgers and shape-derived FLOPs. Check their input SHA and scope against the current candidate; keep overlap heuristics, capacity upper bounds, source inventories and algorithmic estimates visibly separate from runtime facts and no-profiler gains. Missing optional sidecars are not a new acceptance prerequisite.

## Normalize what has actually happened

For each experiment, record:

- ID; `framework`, `operator/replace`, or `operator/improve`; primary variable; dependencies; affected scenario IDs; and affected phase (`prefill`, `decode`, `mixed`, or multiple);
- correctness scope and status, performance scope and status, profiler evidence if any, and service/source identity;
- decision: `retained`, `reverted`, `failed`, `incomplete`, `superseded`, or `pending`;
- measured main/guard changes, uncertainty, side effects, and the exact conclusion boundary;
- whether the change is present in the current combined candidate.

Resolve contradictions before ranking. Results from different workloads, cache states, graph modes, hardware, service instances, or reduced plans are not one comparable series. Preserve unknowns as unknowns.

Distinguish target-device operator validation from service integration. A locally validated but unintegrated candidate uses the existing `pending` decision plus the explanation “local validation passed; whole-model validation pending”; it is absent from the current combined candidate. Apply D0/D6 identity and unique integrated-point counting; local trials, retries and repeated inclusion in a batch do not independently advance the 4–5 cadence. Mainline baseline/accuracy evidence covers only its bound mainline, not independent branches. Keep tile/warp trials under their existing optimization point with external detailed results rather than creating a model-validation cycle or document per trial.

## Reconstruct the current optimization state

Use the same-configuration baseline-to-current combined measurement as the authoritative cumulative effect. Do not add isolated speedup percentages: sequential changes share denominators and may overlap, cancel, or interact.

Separate:

- confirmed cumulative improvement for each measured scenario;
- separate Prefill, Decode, and Mixed evidence for the current target, including cross-phase guards and unresolved phase attribution;
- isolated contribution supported by A/B or revert evidence;
- interaction effects that need an ablation or combined checkpoint;
- correctness debt, untested scenarios, engineering debt, and rollback readiness;
- eliminated, reduced, unchanged, newly exposed, and still-ambiguous bottlenecks.

When Roofline evidence informs the decision, consume the result of [$inference-roofline-analysis](../inference-roofline-analysis/SKILL.md) and check that its phase/rank/shape, FLOPs convention, HBM traffic, timing scope, and ceiling match the current candidate. When inputs change, first check their impact and unaffected bindings; request refreshed analysis only for affected scope whose earlier conclusion no longer supports this decision. Missing collection goes through the coordinator and Profiling. Distinguish hardware measurements from estimates and missing coverage. Compare kernel headroom with timeline gaps, communication, and the target critical path where evidenced; missing critical-path contribution stays unknown rather than forcing a trace for a bounded kernel estimate. A kernel near its roof can still waste bytes or computation. Do not interpret a low FLOP/s percentage alone as poor execution, or assume Prefill is compute-bound and Decode bandwidth-bound by name.

When a baseline is explicitly deferred under SOP baseline-recovery, use verified runtime/source/shape facts for bounded diagnosis and falsification probes; do not force a complete baseline or device trace merely to enter planning. Preserve the missing baseline and acceptance limits, and do not invent cumulative gains.

Use admitted steady-state measurements as the default evidence for bottleneck ranking and cumulative benefit. Cold-start,
first-request, first-batch, and pre-steady anomalies may expose an insufficient warmup contract, but must not redirect the
optimization plan toward startup-only work unless the user explicitly made cold start an objective. Do not repair apparent
instability by dropping the first measured round after seeing it; request a new comparable measurement contract instead.

If several changes have entered the service candidate but the combination lacks coverage of all affected scenarios, apply [SOP D7 validation deduplication](../../docs/performance-optimization-sop.md#d7-性能场景与分层测试频率) before dispatching `$inference-performance-evaluation` in `checkpoint` mode. Reuse valid native results that satisfy the current candidate/service, workload, graph/cache, phase/guards, correctness, comparison and repetition requirements; an eligible formal result can answer a narrower checkpoint question without changing its original purpose or receipt. An old targeted run cannot become formal or count again as an independent repetition. If a running formal/checkpoint covers the need, wait/merge through its owner; serialize any uncovered scope rather than start a duplicate workload. A diagnosis-only supplement with unchanged candidate/workload does not itself require another performance run. If the new bottleneck is ambiguous, first check evidence, analyses and in-flight tasks under SOP C5; dispatch analysis on valid data before requesting new capture. Route only a decision-relevant remaining gap through `$inference-profiling`, preserving valid artifacts and requesting counters alone when appropriate. If the configured accuracy trigger is due, check existing valid gates/in-flight evaluations before requesting missing work through `$inference-accuracy-evaluation`; retain all required identity and native-gate checks. Keep the planning result `incomplete` only for its required missing scope; optional unavailable diagnosis/counters do not invalidate independently supported decisions or a valid measurement result.

## Automatically route decision-relevant diagnosis

At every review, including one triggered early by a system signal, apply the [SOP C0.4 automatic planning handoff](../../docs/performance-optimization-sop.md#c04-系统诊断自动衔接规划复盘) alongside the [C5 Roofline triggers](../../docs/performance-optimization-sop.md#c5-用-roofline-连接瓶颈证据与下一步实验). Select the relevant [C0 diagnostic branch](../../docs/performance-optimization-sop.md#c0-系统瓶颈分诊与取证) automatically; do not ask the user to name a Skill or choose between CPU, communication and rank diagnosis. Read only the selected branch of the Profiling [system diagnosis reference](../inference-profiling/references/system-bottlenecks.md), or the Roofline method when applicable. For a remaining collection gap, select the cheapest useful method through [SOP C0.5](../../docs/performance-optimization-sop.md#c05-症状驱动的工具选择与退出), which links the executable tool recipe; do not maintain another tool table here. Existing sufficient analysis is consumed directly without tool preflight or new metrics; offline evidence does not require a live PID or target connection.

| Decision-relevant signal | Automatic route and discriminating output |
|---|---|
| CPU hotspot/wait, delayed device submission or output, or one thread busy while average CPU is low | Profiling CPU branch: bind API/tokenizer/scheduler/worker roles and the observed phase/window; distinguish on-CPU work, runnable/quota delay, blocking and downstream device waits. A device gap alone does not prove CPU saturation |
| Collective activity appears to limit the target or scaling | Profiling communication branch: compare the same group/collective/iteration and message scope, separate participant arrival skew from communication service and exposed dependency. If late arrival points upstream, the coordinator routes the remaining question to CPU/rank diagnosis rather than presuming a slow network |
| Rank, PP stage, EP expert or DP replica skew | Profiling load branch: compare appropriate TP/PP/EP/DP roles, logical work, effective/padded tokens and shapes; distinguish workload skew, persistently slow execution and dependency/pipeline waits. Equal request counts or utilization do not establish equal work |
| Compute, HBM traffic or execution-efficiency explanation would change implementation/validation investment | `$inference-roofline-analysis`: bind current phase/rank/shape, timing and measured/estimated counters; request only decision-relevant missing collection through Profiling |

These routes share one evidence-state decision, not a fixed CPU→communication→rank→Roofline sequence:

1. If a current, adequately scoped analysis already answers the question or supplies a reusable bounded unknown/unavailable conclusion, use it directly. If valid matching traces or CPU/system/communication/counter reports exist without analysis, dispatch Profiling `analyze` or the relevant Roofline analysis; no new device trace is required for a CPU/system question. Check the applicable source/binding, workload/window, phase/role/group/shape coverage, units, correlation and clock uncertainty before reuse; PID/TID is relevant to process sampling, while metrics/NIC/device reports use their endpoint/interface/device scope. Map a shared capture/report to all relevant questions under C5 before requesting only the remaining coverage; do not recollect the same window per branch/tool. Artifact validity and sufficiency for this question are separate: retain valid partial evidence while narrowing the conclusion and missing scope.
2. Only an unresolved gap that can change the ranking warrants bounded Profiling `capture`, using C0.5 method selection within the original total budget and D0 resource-conflict coordination. For suspected hotspot migration, use `reprofile` only with comparable previous evidence and capture conditions; otherwise capture just the new missing scope and state the comparison limit. Reuse valid unaffected artifacts after an impact/binding check rather than recollecting everything.
3. Before dispatch, reference semantically matching in-flight work and merge/wait through its owner. For unavailable, failed or budget-exhausted evidence, preserve the native status and valid partial coverage, return bounded partial/unknown for the missing scope without invalidating independent evidence or valid performance results, and retain the gap, attempts and reopening condition; do not retry through another Skill or reset history by renaming the question. Re-entry needs a material change in usable coverage/reliability, mechanism, ranking or next experiment; a known blocker needs its stated tool/permission/scope condition to change. Candidate revision changes alone do not reopen an unchanged unavailable counter. CPU/wait/queue/communication evidence can support a direct experiment without first collecting Roofline counters; record why Roofline would not change that decision.
4. Specify the original decision/question and hypothesis, plausible counter-explanation, existing input artifacts/bindings, exact missing coverage, selected mode/branch, executor and authorized target scope, expected discriminating artifacts/validity, total budget, success/stop conditions and return point in the existing record. For communication/rank questions include logical group/work correlation and timing uncertainty; insufficient coverage remains unknown. This is a scoped task description, not a new schema or collector.

Every analysis/supplement returns to the original coordinator and the same decision point. It does not recursively delegate, call another Skill to open a second optimization loop, or restart the review/budget. The coordinator alone decides any subsequent CPU/rank/communication handoff, operator experiment or validation, carrying the original total budget and attempt history. When evidence is sufficient, proceed to ranking and the smallest supported experiment; when it adds no decision-relevant information, select a supported alternative or defer/replan within the original limits, without regenerating the same analysis.

## Rank the next directions

Generate a short ranked list, normally the next 1–3 directions, using [SOP C2](../../docs/performance-optimization-sop.md#c2-生成并维护实际候选排名) and the shared [hotspot/net-benefit method](../inference-roofline-analysis/references/roofline.md#热点筛选与净收益排序). Automatically screen for objective-specific critical-path impact or evidenced contention, actual shape/call coverage, and whether further Roofline analysis would change the decision. Reuse the current analysis shortlist; do not require counters or kernel tuning for every operator.

At direction selection, each review and hotspot migration, automatically evaluate [SOP C3.1 communication-compute fusion and overlap](../../docs/performance-optimization-sop.md#c31-通算融合与-overlap-候选) against the current bottleneck; do not wait for the user to name it. Exposed communication/copy, tile/chunk/microbatch readiness or kernel memory stalls can justify a candidate, while communication/rank waits that could reflect CPU/rank arrival skew first use existing evidence to distinguish it; only a remaining decision-relevant gap returns to that diagnostic branch. Distinguish comm-compute fusion, stream/chunk/microbatch overlap, copy-compute overlap and kernel-internal prefetch/pipelining. Read the relevant [operator reference](../key-operator-opt/references/comm-compute-fusion-overlap.md) only when a branch is decision-relevant; no signal or a known unavailable capability warrants a brief deferral/reopening condition, not new collection.

For any shortlisted fusion/overlap direction, bind the actual group/shape/topology, primitive and graph support, legal dependencies, full producer→communication/synchronization→consumer boundary and resource competition. Rank its removable exposed cost against added pack/copy/launch/buffer/synchronization, pipeline fill/drain and smaller-chunk efficiency losses. Record adopted/downgraded/deferred and why in the existing next-1–3 shortlist; simultaneous streams or a shorter isolated kernel is not a gain. Apply D0 quick local screening, completed local validation and bounded pending inventory/batch integration, with existing high-risk model/accuracy triggers at service integration. Only the coordinator assigns decision-relevant missing diagnosis under C5; do not create a fusion→Profiling→Roofline loop or mechanically require traces/counters for each trial.

```text
objective-specific hotspot → removable critical-path cost minus added execution cost
→ net-benefit interval → evidence confidence, engineering/validation cost and risk
→ first falsification experiment and guards
```

Use the serial/Amdahl mapping only for its stated assumptions; for concurrent kernels, collectives or ranks, recompute the changed dependency path and newly exposed bottleneck. Do not simply multiply cumulative kernel time, or overlap-subtracted time, by a kernel speedup fraction. Separate fixed-work roof headroom from reductions in FLOPs/bytes, count coverage once, deduct only additions not already included in candidate full-call timing, and keep profiler and no-profiler timing provenance distinct. Tail percentiles and throughput/goodput require their own workload evidence rather than arithmetic on mean phase latency.

Compare net-benefit intervals first, then explain confidence, production applicability, implementation/validation cost, correctness/compatibility and maintenance risk. Do not numerically subtract dimensionless risk or developer time from milliseconds, invent confidence probabilities, or choose the largest theoretical headroom by itself. When intervals overlap, prefer supported, cheaper-to-validate, reversible alternatives; when upside is large but evidence weak, choose the smallest discriminating probe before deep implementation. If no credible positive net benefit is supported, select a bounded diagnostic or defer explicitly. Re-evaluate the default framework/replace/improve order against this evidence after retained changes; isolated candidate gains are not additive.

For every proposed direction include:

- rank, layer/strategy, target phase and bottleneck, supporting and opposing evidence;
- expected main-metric effect for the target phase and Mixed workload, plus cross-phase and tail guards;
- objective/timing unit, raw hotspot time and window, critical-path share or contention evidence, coverage weighting, fixed-work or work-reduction assumptions, full-call added costs including CPU work, copy/layout, communication, synchronization and queueing, net-benefit interval and its provenance/confidence;
- applicable scenario/shape/dtype/layout/graph/platform boundary;
- dependencies, implementation scope, correctness risk, validation cost, and rollback path;
- the smallest first experiment that can falsify it, including parent `scenario_id`, local versus service-integration scope, applicable performance Skill mode only when service measurement is due, correctness trigger, profiling need, success threshold, and stop condition.

For system- or Roofline-derived directions, state the predicted reduction in CPU work, traffic, computation, or exposed waits, the affected critical-path share, competing explanations, and the measurement that would falsify the mechanism. A shorter collective, a lower CPU percentage or more even ranks alone is not an end-to-end benefit: account for the remaining bottleneck, changed batch/work distribution and added costs. Missing counters reduce confidence without vetoing otherwise supported experiments. After a retained change, reassess batch/KV working point, intensity when relevant and hotspot migration before reusing the old ranking; use `reprofile` only under the routing conditions above. Local operator results remain pending whole-model validation; confirm service-integrated gains with no-profiler Mixed measurements and cross-phase guards.

Explain how each CPU, communication, rank or Roofline result changed or confirmed the next 1–3 directions: which was adopted, downgraded or deferred and why, then bind the selected direction to the immediate single-variable experiment, guards and stop conditions. Rejected hypotheses and unresolved alternatives must affect confidence or priority. Do not merely link the analysis while carrying forward an unsupported old priority. If collection is needed, specify its narrow question and scope instead of creating an open-ended profiling loop.

Also list deferred directions and why they are lower priority. Do not present an unmeasured kernel hotspot, historical speedup, or theoretical peak as expected end-to-end gain without discounting and an explicit validation plan.

## Produce a concrete next cycle

When resources and independence permit, automatically dispatch a bounded set of valuable CPU, communication and/or operator explorations in parallel under [SOP D0](../../docs/performance-optimization-sop.md#d0-并行探索局部筛选与批次集成). Single-variable control applies within each independent experiment, not as a global one-branch limit. Specify each branch's input candidate/baseline, executor, hypothesis, private source/import/compiler/cache/random state, service/port when needed, device and CPU/NUMA/NIC/memory/disk allocation, dependencies, outputs and time/quantity/risk budget. Resource availability alone is not independence: isolate shared-resource effects or serialize contested measurements, writes to shared source/install/cache state, and shared-service start/stop. Do not duplicate an evidence gap, widen the Host scope or relax container/mount gates to create parallelism.

Keep one primary integration direction with a limited number of independent explorations. Use small representative reference/numerical and complete-call checks for quick operator trials; only selected candidates complete affected real-shape/boundary/fallback coverage and applicable graph capture plus two changed-input replays before a local-pass claim, reusing binding-valid checks; do not start/restart a whole model, run model regression, Mixed or GPQA for every trial. Bound the pending inventory by the recorded time/count/risk budget and integration triggers: a local winner, complementary compatible winners, budget/limit reached, changed bottleneck or a service-decision milestone. At a trigger, select, integrate or retire candidates rather than accumulate unchecked work. Apply D0 branch-return/parent and implementation-binding checks after mainline or dependency changes; refresh only affected local evidence before assembling compatible winners into a bounded candidate service. Satisfy model smoke/minimal regression and required service-performance coverage using D7 reuse of valid/in-flight covering results, assigning only the uncovered scope rather than always running targeted then checkpoint; promote to the mainline only after applicable checks pass. High-risk candidates may be explored in isolation, but a preselected batch containing them receives immediate existing full-accuracy/model validation once at integration, before further unvalidated stacking; individual offline members need not each run a full model first. On combined failure, use dependency-aware rollback/bisection and reuse unaffected local checks; isolated end-to-end contributions remain unknown unless an ablation is decision-relevant. All final formal accuracy and full-scenario requirements remain intact; isolated speedup percentages never add into a combined benefit.

The review output must contain:

1. Current objective, baseline identity, current candidate identity, and evidence cutoff.
2. Experiment ledger and retained-change dependency order.
3. Per-scenario baseline-to-current results and cumulative conclusion boundary.
4. Current Prefill/Decode/Mixed bottleneck map, phase interaction, cross-phase guards, and evidence gaps.
5. Ranked next directions with first experiments and stop conditions.
6. The next optimization cycle: one primary integration direction, bounded independent parallel explorations when feasible, resource/measurement isolation and integration order, optional sentinel, required Skill invocations, and next review/integration triggers; include diagnostic routing, reuse/dispatch state and return point when evidence is decision-relevant.

Do not expand the authorized modification scope. Under the current AGENTS rules, task-private `vllm-plugin-FL`, `FlagGems-vllm` and `FlagGems` source changes, and a private FlagTree build for this task's operator code generation, are within the stated optimization authorization; isolation, delegation and validation still apply. Changes to vLLM source, weights, the base image, or shared/system state beyond existing authorization require the applicable explicit approval. Identify the exact boundary and rank an in-scope alternative separately instead of requesting approval merely because a task-private FlagGems-vllm file changes. At service-candidate integration, communication/rank-data-layout and other high-risk changes follow the existing [SOP D6](../../docs/performance-optimization-sop.md#d6-精度评测节奏与风险触发) immediate accuracy trigger, not a new gate.

## Record the checkpoint

Resolve the active case directory from its current record and [model artifact contract](../../docs/model-artifact-contract.md); new cases use `models/<model>/<platform>/<case-id>/`, while legacy layouts remain readable without automatic migration. Update that case's `optimize/state.yml` with the stable review ID, current candidate, experiment ledger, phase bottlenecks, ranked next directions, immediate experiment, evidence cutoff, next review trigger, and compact summaries of superseded decisions. Verify that every optimization-point ledger entry has a matching `optimize/<experiment-id>.md` covering its direction, content, effect, correctness, decision, and evidence, including reverted, failed, incomplete, and superseded points. Synchronize the same case's `optimize/README.md` as the human-readable multi-round overview and link index. Do not create an `optimize/history/`, planning work directory, or per-review file.

Keep raw benchmark, trace, accuracy artifacts, commands, and process scripts at their existing external locations; the structured state links evidence rather than copying it. Only the final frozen result updates `acceptance/state.yml` and `acceptance/README.md`.

Return a compact summary containing: review ID, evidence cutoff, current cumulative state, retained/reverted/incomplete experiments, current bottleneck, top next directions, immediate next experiment, required Skill calls, blockers, updated state/README paths, and next review trigger.
