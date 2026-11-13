---
name: inference-profiling
description: Capture, validate, analyze, and repeat profiler traces with explicit prefill/decode/mixed phase separation for end-to-end LLM inference bottleneck attribution. Use when low-overhead measurements cannot localize a phase, framework, communication, memory, dispatch, or operator bottleneck, or when a retained optimization may have moved the hotspot; do not use profiler-on timings as formal performance evidence.
---

# Inference Profiling

Use this Skill to turn a representative inference scenario into valid trace evidence and an actionable bottleneck hypothesis. Profiling is a diagnostic capability: performance gains must be confirmed later with `$inference-performance-evaluation` on no-profiler runs.

## Select one mode

| Mode | Trigger | Output |
|---|---|---|
| `capture` | A decision-relevant timeline or native-counter evidence gap requires collection | A validated new trace set and/or scoped native counter report, with binding and coverage |
| `analyze` | Sufficient valid current traces/counter reports already exist | Phase decomposition, hotspot evidence, competing explanations, and the next falsifiable experiment |
| `reprofile` | A retained optimization, combined candidate, or changed workload may have moved the hotspot | A comparable diagnostic capture and hotspot-migration conclusion; not a speedup claim |

First apply the shared evidence, in-flight task and gap checks in [SOP C5](../../docs/performance-optimization-sop.md#c5-用-roofline-连接瓶颈证据与下一步实验). A request for collection and analysis does not require recollecting sufficient valid data: use `analyze` directly, or collect only the missing scope before analysis. Use `reprofile` only when the earlier evidence and capture conditions are available for comparison. Known unsupported or exhausted requests return a gap and reopening condition rather than another attempt on unchanged inputs.

## Read only relevant sources

- Read the `Profiling 与 SGLang 诊断` section of `evaluation/performance/README.md` for maintained commands, result semantics, and current tool limitations.
- Read the active case and experiment contract for scenario IDs, service identity, external artifact directory, and the bottleneck question.
- For offline forward/layer navigation or overlap/fusion candidate extraction from an existing trace, read [trace-analysis.md](references/trace-analysis.md). Use the maintained analyzer with explicit, checksum-bound boundaries; it does not collect traces or prove critical-path savings.
- When compute/HBM counters are needed for Roofline diagnosis, read the [Roofline measurement reference](../inference-roofline-analysis/references/roofline.md) for phase/rank binding, counter discovery and capture limitations. Collection and validity remain here; quantitative roof-distance analysis belongs to `$inference-roofline-analysis`.
- If container/service preparation is required, read `docs/container-isolation.md` before changing the optimization environment.
- After analysis converges to a specific operator, dispatch, layout, or adjacent fusion path, recommend `$key-operator-opt` to the main coordinator; reuse any existing operator task and do not preload the whole knowledge base or recursively launch it from a counter-supplement task.

## Establish the diagnostic contract

Before capture, record:

- Profiling mode, experiment ID, representative `scenario_id`, required phase coverage (`prefill`, `decode`, `mixed`), the phase-boundary method, the question the trace must answer, and why lower-overhead evidence is insufficient.
- Model, Host, optimization container, service instance, engine, Plugin/FlagGems-vllm/FlagGems revisions, hardware/topology, graph mode, profiler mechanism, and expected worker/rank coverage.
- Input/output lengths, endpoint, EOS/sampling, concurrency, requests, warmup, profiled rounds, timeout, relevant trace/native-report and output directories, and stop rules; mark inapplicable output types explicitly.
- The nearest no-profiler baseline or targeted performance run. It provides context only; do not mix its timings with profiler-on timings.

Choose the smallest scenario that still exercises the suspected path. Use the user-provided remote work directory only through the current case-specific subdirectory, and verify how the server writes traces and how the client sees them. Do not infer a container/Host path mapping.

## Capture and validate evidence

Declare whether the missing evidence is timeline, native counters or both. Keep existing valid artifacts and bindings. For a timeline, use the steps below; for counters only, use the native-report branch afterward. Do not collect a second timeline merely to satisfy the trace checks when the requested output is a counter report.

1. Confirm the target service supports and has enabled the intended profiler without modifying the source adaptation container.
2. Inventory the trace directory before the run, including filenames, sizes, timestamps, and checksums when practical.
3. Generate and inspect a dry-run command using `evaluation/performance/vllm_profile.py` or `sglang_profile.py` as appropriate.
4. Execute with a unique output directory and preserve the command, stdout/stderr, native benchmark result, and validation record.
5. Re-inventory the trace directory and require a new or changed, non-empty, parseable trace in the expected time window. Old files, ordinary benchmark JSON, or a successful client exit are not capture proof.
6. Check expected worker/rank coverage and verify the suspected graph/backend path was actually exercised. Missing coverage or asynchronous export that has not completed leaves the result `incomplete`.

On timeout or non-zero exit, retain evidence and inspect profiler/service state. Do not silently restart services, reuse a stale trace, or retry indefinitely.

For a **native counter supplement**, first verify the installed vendor tool, supported metrics, permissions and existing report coverage. The maintained `vllm_profile.py`/`sglang_profile.py` trace runners do not automatically produce FLOPs/HBM counters. Dispatch a saved, bounded vendor-native capture command under the same authorization, assigned optimization container, device ownership and frozen total budget; use the [measurement reference](../inference-roofline-analysis/references/roofline.md) to define the scope, not as an executable wrapper.

Validate the original native report/export: report identity and new capture time, parseability, exact metrics/units, kernel/range and call coverage, phase/rank/shape/graph/backend binding, tool errors and replay/cache/clock conditions. Retain the original timeline ID and document how the reports can be associated; unmatched conditions remain separate evidence. Native report validity does not require a new trace, and trace existence does not validate native counters. Unsupported metrics, missing permission or incomplete coverage return a scoped gap, attempted evidence and reopening condition; no fake trace pass or cross-vendor fallback.

One main coordinator owns dispatch and deduplication. Before collection, reference any matching in-flight analysis/capture task and wait or merge through its owner instead of starting another. A supplement returns artifacts and validity to its original request; it does not automatically start the full analysis-to-operator chain below. Re-enter Roofline only after new evidence or changed inputs, within the original budget.

## Analyze bottlenecks

Build an evidence chain from end-to-end behavior to the narrowest supported layer:

1. First split the trace into Prefill, Decode, and Mixed/interference evidence using reliable service markers, iteration/token boundaries, shapes, or execution semantics. If a reliable boundary cannot be established, mark phase attribution `unknown/incomplete`; never divide total time by assumption.
2. Within each phase, separate request/network, scheduler/batching, sampling, memory/graph, communication, dispatch, and kernel activity. Do not combine the same kernel's Prefill and Decode calls when ranking hotspots because their shapes, counts, and optimization choices may differ.
3. Distinguish host runtime/driver activity, device kernels, communication, memory copies, synchronization, graph gaps, and unclassified events.
4. Identify per-phase cumulative time, call counts, representative shapes, rank imbalance, serialization, gaps, fallback, and implementation-hit evidence, then describe Prefill/Decode interference in the mixed timeline.
   For the next-direction shortlist, also distinguish raw cumulative duration from dependency-critical elapsed contribution and evidenced contention. Bind the objective/window, group actual per-rank shapes and repeated calls, and identify overlap or another limiter that would remain after a candidate speedup. Use [SOP C2](../../docs/performance-optimization-sop.md#c2-生成并维护实际候选排名) and the [screening method](../inference-roofline-analysis/references/roofline.md#热点筛选与净收益排序); unknown contribution stays unknown. Collect only missing evidence that could change the ranking.
5. Compare each leading explanation against at least one plausible alternative, such as client limitation, warmup, cache state, graph break, load imbalance, phase interference, or an adjacent copy/merge cost.
6. Automatically check the [SOP C5 triggers](../../docs/performance-optimization-sop.md#c5-用-roofline-连接瓶颈证据与下一步实验) at analysis handoff. When the decision depends on compute versus bandwidth or distance to a hardware ceiling, pass representative hotspot counters, shape/work estimates and the phase timeline to `$inference-roofline-analysis` without requiring the user to name it. Reuse a valid result for unchanged evidence. Preserve FLOPs/traffic/time conventions, counter coverage and replay/cache/clock effects. If it requests missing evidence, perform only the scoped capture under existing authorization, then return the evidence; a missing counter does not block independently supported experiments.
7. Convert the result into one falsifiable phase-scoped experiment with an expected cross-phase and mixed end-to-end effect plus a stop condition. Explain which bytes, computation, or waits it should remove and what evidence would reject that mechanism.

Use `trace_to_summary.py` only as a category summary. Its possibly overlapping activity-duration sums are not critical-path time, device utilization, CPU self time, or proof of end-to-end impact. Inspect the timeline and relevant events before attributing a root cause.

When layer/pass structure or concurrency could change the next experiment, use `evaluation/performance/trace_analysis.py` on the existing valid trace. Preserve unknown attribution, crossing-boundary events, per-rank/device groups and source-event links. Treat its overlap/fusion rows as hypotheses requiring dependency and full-call checks under SOP C2, not as removable time. Keep the diagnostic sidecar external and reference it from the same optimization-point record.

Classify the next optimization as `framework`, `operator/replace`, or `operator/improve` using the project's mechanism-based rules. A hot kernel is a candidate, not proof that optimizing it will improve the service.

## Reprofile without overstating results

For `reprofile`, keep the scenario, profiler settings, warmup, rounds, and evidence interpretation comparable to the earlier capture. Report whether the hotspot persisted, shrank, moved, or became ambiguous. Return this diagnosis to the coordinator, which schedules any still-required no-profiler `targeted/checkpoint` performance validation at the existing promotion point and reuses valid results. A counter supplement alone does not trigger another benchmark. Do not derive a speedup percentage by comparing profiler traces.

## Record and route artifacts

Write the mode, scenario, service identity, profiler configuration, trace inventory/checksums, worker/rank coverage, phase coverage and boundary evidence, separate Prefill/Decode/Mixed hotspot summaries, interference, competing explanations, confidence, next experiment, result state, and artifact paths into the current experiment record.

When Roofline is used, include the measured/estimated status, FLOPs convention, HBM read/write totals, timing scope, ceiling sources, arithmetic intensity, achieved throughput/bandwidth, roof efficiency, and resulting hypothesis as specified in the [experiment contract](../../docs/experiment-contract.md#roofline-诊断记录按需). Keep missing values unknown and do not treat roof efficiency as an acceptance gate or a predicted end-to-end speedup.

- Profiling conclusions, stable profile IDs, decision boundaries, and external links update `models/<model>/<platform>/optimize/state.yml`. When profiling supports an active optimization point, add its phase-separated bottleneck evidence, competing explanations, and resulting direction to the matching `optimize/<experiment-id>.md`, then update the linked multi-round summary in `optimize/README.md`. Keep trace captures within that one optimization-point document; do not create an `optimize/history/`, a profiling subdirectory, or separate Markdown per trace.
- Large traces, raw logs, and tool outputs remain in the external or remote case directory.
- Capture/analyze scripts, service manifests, trace summaries, source excerpts, and generated commands remain external; do not copy the profiling work directory under `models/`.
- Profiling artifacts do not enter `acceptance/` as formal performance evidence.

Return a compact result containing: mode, original request/task identity, scenario ID, service identity, separate timeline/native-report validity and worker/rank coverage as applicable, reused artifacts, phase-boundary evidence, separate Prefill/Decode/Mixed hotspots and interference, rejected or unresolved alternatives, conclusion boundary, artifact paths, unresolved gaps and reopening conditions, and the next-action recommendation for the coordinator. A supplement returns only its assigned evidence and validity, not a new optimization cycle.
