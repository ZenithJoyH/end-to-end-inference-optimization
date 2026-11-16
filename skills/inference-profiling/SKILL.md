---
name: inference-profiling
description: Capture, validate, and analyze profiler traces, CPU/system reports, and communication/rank evidence with explicit prefill/decode/mixed phase separation for end-to-end LLM inference bottleneck attribution. Use when low-overhead measurements cannot localize CPU hotspots or waits, communication, rank load imbalance, request/scheduler, memory/graph, dispatch, or operator bottlenecks, or when a retained optimization may have moved the hotspot; do not use profiler-on timings as formal performance evidence.
---

# Inference Profiling

Use this Skill to turn a representative inference scenario into valid diagnostic evidence and an actionable bottleneck hypothesis. Evidence may be a trace, native counter report, or scoped CPU/system/communication report; a device trace is not required when it would not answer the question. Profiling is a diagnostic capability: performance gains must be confirmed later with `$inference-performance-evaluation` on no-profiler runs.

## Select one mode

| Mode | Trigger | Output |
|---|---|---|
| `capture` | A decision-relevant timeline, native-counter, or CPU/system/communication evidence gap requires collection | Validated scoped artifacts of the needed type, with binding and coverage |
| `analyze` | Existing valid current evidence supports the requested analysis or a bounded assessment of its gaps | Phase-scoped attribution, hotspot/wait evidence, competing explanations, and a next experiment or scoped limitation |
| `reprofile` | Hotspot migration matters to the decision, comparable earlier evidence exists, and a remaining gap needs new collection | A scoped comparable diagnostic capture and hotspot-migration conclusion; not a speedup claim |

First apply the shared evidence, in-flight task and gap checks in [SOP C5](../../docs/performance-optimization-sop.md#c5-用-roofline-连接瓶颈证据与下一步实验). A request for collection and analysis does not require recollecting sufficient valid data: use `analyze` directly, or have the coordinator assign only decision-relevant missing collection. Without comparable earlier evidence, any necessary collection uses `capture` with its comparison limit; retained changes alone do not mandate a new capture. Known unsupported or exhausted requests return a gap and reopening condition rather than another attempt on unchanged inputs.

## Read only relevant sources

- When using maintained trace/benchmark runners, read the `Profiling 与 SGLang 诊断` section of `evaluation/performance/README.md` for commands, result semantics, and current tool limitations.
- Read the active case and experiment contract for scenario IDs, service identity, external artifact directory, and the bottleneck question.
- For CPU hotspots/waits, communication, rank imbalance, or unresolved request/scheduler/KV/system gaps, read the relevant branch of [system-bottlenecks.md](references/system-bottlenecks.md). Start with its coverage table and reuse existing evidence; do not collect every category.
- When a selected system branch needs executable target-Linux steps, read only the matching [system-diagnosis-tools.md](references/system-diagnosis-tools.md) recipe. It provides bounded native commands and interpretation, not a new collector or permission to run attach commands on the local control machine.
- For offline forward/layer navigation or overlap/fusion candidate extraction from an existing trace, read [trace-analysis.md](references/trace-analysis.md). Use the maintained analyzer with explicit, checksum-bound boundaries; it does not collect traces or prove critical-path savings.
- When compute/HBM counters are needed for Roofline diagnosis, read the [Roofline measurement reference](../inference-roofline-analysis/references/roofline.md) for phase/rank binding, counter discovery and capture limitations. Collection and validity remain here; quantitative roof-distance analysis belongs to `$inference-roofline-analysis`.
- If container/service preparation is required, read `docs/container-isolation.md` before changing the optimization environment.
- After analysis converges to a specific operator, dispatch, layout, or adjacent fusion path, recommend `$key-operator-opt` to the main coordinator; reuse any existing operator task and do not preload the whole knowledge base or recursively launch it from a counter-supplement task.

## Establish the diagnostic contract

Before capture, record:

- Profiling mode, experiment ID, representative `scenario_id`, required phase coverage (`prefill`, `decode`, `mixed`), the phase-boundary method, the question the evidence must answer, and why lower-overhead evidence is insufficient.
- Model, Host, optimization container, service instance, engine, Plugin/FlagGems-vllm/FlagGems revisions, hardware/topology, graph mode, profiler mechanism, and expected process/thread/worker/rank/group coverage. For cross-rank timing, record the correlation method, clock domain and alignment uncertainty.
- Input/output lengths, endpoint, EOS/sampling, concurrency, requests, warmup, profiled rounds, timeout, relevant trace/native-counter/system-report and output directories, and stop rules; mark inapplicable output types explicitly.
- The nearest available no-profiler baseline or targeted performance run, or its deferred/not-run state. It provides context only; an unfinished baseline does not prevent authorized static-first or scoped diagnosis. Do not mix its timings with profiler-on timings or fabricate a completed baseline.

Choose the smallest scenario that still exercises the suspected path. Use the user-provided remote work directory only through the current case-specific subdirectory, and verify how the chosen tool writes artifacts and how they are accessed. Do not infer a container/Host path mapping.

Select the method automatically from the signal and current evidence; do not wait for the user to choose a tool. Existing sufficient metrics/reports go directly to `analyze`; a bounded unknown/unavailable result can also be delivered without new collection. Only an unresolved gap that could change the next candidate justifies the cheapest relevant recipe below. Reuse one capture across matching diagnostic branches, assigning only uncovered scope under C5 and the original budget; entering another branch is not a new collection cycle.

| Signal | First method/report | Decision-relevant upgrade |
|---|---|---|
| Thread/host hotspot or delayed submission | [Thread interval statistics and existing stacks](references/system-diagnosis-tools.md#cpu) | One bounded Python/native on-CPU sample; device correlation only if needed |
| Low CPU with stalls, quota/lock/IPC suspicion | [PID/TID state and verified cgroup deltas](references/system-diagnosis-tools.md#waits) | Only authorized PID-filtered off-CPU/scheduling evidence with sufficient event coverage |
| Long collective or slow scaling | [Group/step/ready/completion and link counters](references/system-diagnosis-tools.md#communication) | Installed native communication probe only with exclusive resources and verified CLI |
| Rank/stage/expert/replica skew | [Existing source-event comparison table](references/system-diagnosis-tools.md#rank) | Just the missing logical step/role/peer evidence; not all-rank recapture |
| Queue, return, KV, graph or system drift | [Service/request metrics](references/system-diagnosis-tools.md#request-scheduler), [KV/graph](references/system-diagnosis-tools.md#kv-graph), [resources](references/system-diagnosis-tools.md#system) | Missing service events or [device timeline](references/system-diagnosis-tools.md#timeline) only when attribution affects the decision |

## Capture and validate evidence

Declare whether the missing evidence is timeline, native counters, CPU/system/communication reports, or a scoped combination. Keep existing valid artifacts and bindings. For a timeline, use the steps below; for counters only, use the native-report branch afterward; for CPU/system/communication reports, use [system-bottlenecks.md](references/system-bottlenecks.md#证据绑定工具选择与停止规则). Validate each artifact type separately and mark unrelated checks inapplicable. Neither a counter report nor a CPU stack/resource sample requires a new device trace, and neither constitutes a trace-validity pass.

1. Confirm the target service supports and has enabled the intended profiler without modifying the source adaptation container.
2. Inventory the trace directory before the run, including filenames, sizes, timestamps, and checksums when practical.
3. Generate and inspect a dry-run command using `evaluation/performance/vllm_profile.py` or `sglang_profile.py` as appropriate.
4. Execute with a unique output directory and preserve the command, stdout/stderr, native benchmark result, and validation record.
5. Re-inventory the trace directory and require a new or changed, non-empty, parseable trace in the expected time window. Old files, ordinary benchmark JSON, or a successful client exit are not capture proof.
6. Check expected worker/rank coverage and verify the suspected graph/backend path was actually exercised. Missing required coverage or asynchronous export leaves the requested trace result `incomplete`; retain any valid narrower scope and its supported conclusions rather than treating all evidence as invalid.

On timeout or non-zero exit, retain evidence and inspect profiler/service state. Do not silently restart services, reuse a stale trace, or retry indefinitely.

If the workload ended but trace export is still in flight, attach bounded read-only observation/recovery to that original capture within its remaining total budget; do not launch another workload or reset the budget. Validate the recovered artifact's source/capture association, parseability, expected coverage and export completion evidence; unchanged file size alone does not prove completion. Preserve the runner's original `incomplete`/non-zero receipt and record later recovery separately rather than rewriting its exit status. Budget exhaustion returns the remaining export gap and reopening condition.

For a **native counter supplement**, first verify the installed vendor tool, supported metrics, permissions and existing report coverage. The maintained `vllm_profile.py`/`sglang_profile.py` trace runners do not automatically produce FLOPs/HBM counters. The main coordinator assigns the saved, bounded vendor-native capture under the same authorization, optimization container, device ownership and frozen total budget; the assigned executor uses the [measurement reference](../inference-roofline-analysis/references/roofline.md) to define the scope, not as an executable wrapper.

Validate the original native report/export: report identity and capture time, parseability, exact metrics/units, kernel/range and call coverage, phase/rank/shape/graph/backend binding, tool errors and replay/cache/clock conditions. New collection must show its new capture; analysis may reuse a still-valid earlier report. If a timeline exists, retain its ID and the association basis; otherwise bind the native report through its own workload/range/call identity and mark trace linkage inapplicable. Unmatched conditions remain separate evidence. Native report validity does not require a trace, and trace existence does not validate counters. Separate artifact validity from sufficiency for this question: valid partial coverage can support a narrower result, while unsupported metrics, permission gaps or missing required coverage return the remaining gap and reopening condition; no fake trace pass or cross-vendor fallback.

One main coordinator owns dispatch and deduplication. Match requests by decision/question, candidate/service binding, scope/method and unresolved gap, not a renamed branch, artifact or task ID. Before collection, reference matching completed or in-flight work and wait or merge through its owner instead of starting another. A supplement returns artifacts, validity and question coverage to its original request; it does not automatically start the analysis-to-operator chain below. Re-entry requires evidence or changed premises that can remove the recorded gap or change the pending decision. Preserve the original gap, budget and attempt history; a new file or a different Skill is not progress or permission to retry an exhausted request.

## Analyze bottlenecks

Build an evidence chain from end-to-end behavior to the narrowest supported layer:

1. First associate the available evidence with Prefill, Decode, and Mixed/interference using reliable service markers, iteration/token boundaries, shapes, or execution semantics. A system report spanning a mixed window can support a mixed conclusion without a device trace. If a reliable phase boundary cannot be established, mark finer phase attribution `unknown/incomplete`; never divide total time by assumption.
2. Within each evidenced phase/window, separate request/network, scheduler/batching, CPU work/waits, sampling, memory/graph, communication, dispatch, and kernel activity as coverage permits. Do not combine the same kernel's Prefill and Decode calls when ranking hotspots because their shapes, counts, and optimization choices may differ.
3. Distinguish host runtime/driver activity, device kernels, communication, memory copies, synchronization, graph gaps, and unclassified events.
4. Identify supported per-phase durations/counts, representative shapes, rank imbalance, serialization, gaps, fallback, and implementation-hit evidence, then describe Prefill/Decode interference using the mixed evidence. Do not invent device activity or phase durations absent from a system report.
   For the next-direction shortlist, also distinguish raw cumulative duration from dependency-critical elapsed contribution and evidenced contention. Bind the objective/window, group actual per-rank shapes and repeated calls, and identify overlap or another limiter that would remain after a candidate speedup. Use [SOP C2](../../docs/performance-optimization-sop.md#c2-生成并维护实际候选排名) and the [screening method](../inference-roofline-analysis/references/roofline.md#热点筛选与净收益排序); unknown contribution stays unknown. Collect only missing evidence that could change the ranking.
5. Compare each leading explanation against at least one plausible alternative, such as client limitation, warmup, cache state, graph break, load imbalance, phase interference, or an adjacent copy/merge cost.
   For CPU, distinguish on-CPU work from runnable delay, blocking and device waits. For communication, distinguish participant arrival skew from transport/service cost and unhidden dependency time. For rank imbalance, compare the same logical work within the actual TP/PP/EP/DP group, not rank averages across unrelated work. Follow the relevant [system diagnosis branch](references/system-bottlenecks.md); insufficient clocks, stacks or peer coverage leave the corresponding cause unknown.
6. Automatically check the [SOP C5 triggers](../../docs/performance-optimization-sop.md#c5-用-roofline-连接瓶颈证据与下一步实验) at analysis handoff. When compute/bandwidth/roof-distance attribution could change the decision, return that trigger and existing counters, shape/work estimates and available timing/path evidence to the main coordinator for bounded `$inference-roofline-analysis` dispatch or reuse; do not invoke it from this subtask. Preserve FLOPs/traffic/time conventions, coverage and replay/cache/clock effects. Any resulting collection gap returns to the same coordinator for deduplication and scoped assignment; this analysis does not start capture itself. Missing counters or a device trace do not block independently supported CPU/wait/communication experiments or explicitly bounded estimates.
7. When the evidence supports a candidate, propose one falsifiable phase-scoped experiment with expected cross-phase/Mixed effects and a stop condition; explain which bytes, computation or waits it should remove and what would reject that mechanism. Otherwise return the bounded limitation, reopening condition and, if useful within the budget, a smallest discriminating diagnostic request; do not invent a performance hypothesis to fill the output.

Use `trace_to_summary.py` only as a category summary. Its possibly overlapping activity-duration sums are not critical-path time, device utilization, CPU self time, or proof of end-to-end impact. Inspect the timeline and relevant events before attributing a root cause.

When layer/pass structure or concurrency could change the next experiment, use `evaluation/performance/trace_analysis.py` on the existing valid trace. Preserve unknown attribution, crossing-boundary events, per-rank/device groups and source-event links. Treat its overlap/fusion rows as hypotheses requiring dependency and full-call checks under SOP C2, not as removable time. Keep the diagnostic sidecar external and reference it from the same optimization-point record.

Classify the next optimization as `framework`, `operator/replace`, or `operator/improve` using the project's mechanism-based rules. A hot kernel is a candidate, not proof that optimizing it will improve the service.

## Reprofile without overstating results

For `reprofile`, first reuse valid post-change evidence through `analyze` if it already answers the migration question. Only a remaining decision-relevant collection gap with comparable earlier evidence warrants `reprofile`; keep scenario, profiler settings, warmup, rounds and interpretation comparable and state deliberate differences. Without a usable earlier comparison, use necessary scoped `capture` and do not assert hotspot migration. Report persistence, shrinkage, migration or ambiguity within actual coverage. Return this diagnosis to the coordinator, which checks existing valid or in-flight validation before assigning any still-required no-profiler `targeted/checkpoint` run at the existing promotion point. A counter supplement alone does not trigger another benchmark. Do not derive a speedup percentage by comparing profiler traces.

## Record and route artifacts

Write the mode, scenario, service identity, profiler configuration, artifact inventory/checksums and type-specific validity as applicable, process/worker/rank coverage, phase coverage and boundary evidence, separate Prefill/Decode/Mixed hotspot summaries, interference, competing explanations, confidence, next experiment, result state, and artifact paths into the current experiment record.

For system diagnosis, add only decision-relevant process/thread roles, sampling window/rate and losses, on/off-CPU interpretation, cgroup/NUMA constraints, communication group/message and correlation evidence, comparable per-rank workload and skew, clock uncertainty, and exposed wait/critical-path evidence. Reuse existing evidence/hypothesis/next-action fields; these are not a new schema or acceptance gate. Preserve raw stacks/resource/native reports externally and do not retain unfiltered environment dumps or secrets.

Make the diagnostic return consumable by the original planning decision: name the selected branch, whether each original hypothesis is supported, rejected or still unknown, the current binding/coverage, removable critical-path cost and added CPU/copy/communication/queueing costs (or what remains unmeasured), affected candidates and the assigned return point. The coordinator uses this result to change or confirm the ranking in that same review; a diagnostic subtask does not launch another planning loop, and a supported CPU/wait/communication experiment need not first pass through Roofline.

For a system recipe, return why it was the cheapest useful method, actual command/window/tool/permission outcome and any failure alternative. The coordinator explicitly records adopted/downgraded/deferred candidates and the immediate falsification experiment in the existing C2/planning point; storing a report alone does not satisfy the handoff, and collection success alone triggers no additional benchmark.

When Roofline is used, include the measured/estimated status, FLOPs convention, HBM read/write totals, timing scope, ceiling sources, arithmetic intensity, achieved throughput/bandwidth, roof efficiency, and resulting hypothesis as specified in the [experiment contract](../../docs/experiment-contract.md#roofline-诊断记录按需). Keep missing values unknown and do not treat roof efficiency as an acceptance gate or a predicted end-to-end speedup.

- Resolve the active case's `optimize/` from its existing record: new cases use `models/<model>/<platform>/<case-id>/optimize/`; preserve a legacy layout only when it is the active case, without migrating it. Update its `state.yml` with conclusions, stable profile IDs, decision boundaries and external links. When profiling supports an active optimization point, add phase-separated evidence, competing explanations and direction to the matching `optimize/<experiment-id>.md`, then update that case's `optimize/README.md`. Keep captures within that optimization-point document; do not create an `optimize/history/`, profiling subdirectory or separate Markdown per trace.
- Large traces, raw logs, and tool outputs remain in the external or remote case directory.
- Capture/analyze scripts, service manifests, trace summaries, source excerpts, and generated commands remain external; do not copy the profiling work directory under `models/`.
- Profiling artifacts do not enter `acceptance/` as formal performance evidence.

Return a compact result containing: mode, original request/task identity, scenario ID, service identity, separate timeline/native-counter/system-report validity and process/thread/worker/rank coverage as applicable, reused artifacts, phase-boundary evidence, separate Prefill/Decode/Mixed hotspots and interference, rejected or unresolved alternatives, conclusion boundary, artifact paths, unresolved gaps and reopening conditions, and the next-action recommendation for the coordinator. A supplement returns only its assigned evidence and validity, not a new optimization cycle.
