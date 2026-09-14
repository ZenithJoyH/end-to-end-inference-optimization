---
name: inference-profiling
description: Capture, validate, analyze, and repeat profiler traces with explicit prefill/decode/mixed phase separation for end-to-end LLM inference bottleneck attribution. Use when low-overhead measurements cannot localize a phase, framework, communication, memory, dispatch, or operator bottleneck, or when a retained optimization may have moved the hotspot; do not use profiler-on timings as formal performance evidence.
---

# Inference Profiling

Use this Skill to turn a representative inference scenario into valid trace evidence and an actionable bottleneck hypothesis. Profiling is a diagnostic capability: performance gains must be confirmed later with `$inference-performance-evaluation` on no-profiler runs.

## Select one mode

| Mode | Trigger | Output |
|---|---|---|
| `capture` | Low-overhead metrics cannot localize the bottleneck, or no valid trace exists for the current service and scenario | A newly generated, validated trace set with service, rank/worker, scenario, and command identity |
| `analyze` | A valid current trace set already exists | Phase decomposition, hotspot evidence, competing explanations, and the next falsifiable experiment |
| `reprofile` | A retained optimization, combined candidate, or changed workload may have moved the hotspot | A comparable diagnostic trace and hotspot-migration conclusion; not a speedup claim |

When a request includes both collection and analysis, run `capture` followed by `analyze`. Use `reprofile` only when the earlier trace and capture conditions are available for comparison.

## Read only relevant sources

- Read the `Profiling 与 SGLang 诊断` section of `evaluation/performance/README.md` for maintained commands, result semantics, and current tool limitations.
- Read the active case and experiment contract for scenario IDs, service identity, external artifact directory, and the bottleneck question.
- If container/service preparation is required, read `docs/container-isolation.md` before changing the optimization environment.
- After analysis converges to a specific operator, dispatch, layout, or adjacent fusion path, invoke `$key-operator-analysis`; do not preload the whole operator knowledge base.

## Establish the diagnostic contract

Before capture, record:

- Profiling mode, experiment ID, representative `scenario_id`, required phase coverage (`prefill`, `decode`, `mixed`), the phase-boundary method, the question the trace must answer, and why lower-overhead evidence is insufficient.
- Model, Host, optimization container, service instance, engine, Plugin/FlagGems-vllm/FlagGems revisions, hardware/topology, graph mode, profiler mechanism, and expected worker/rank coverage.
- Input/output lengths, endpoint, EOS/sampling, concurrency, requests, warmup, profiled rounds, timeout, trace directory, output directory, and stop rules.
- The nearest no-profiler baseline or targeted performance run. It provides context only; do not mix its timings with profiler-on timings.

Choose the smallest scenario that still exercises the suspected path. Use the user-provided remote work directory only through the current case-specific subdirectory, and verify how the server writes traces and how the client sees them. Do not infer a container/Host path mapping.

## Capture and validate traces

1. Confirm the target service supports and has enabled the intended profiler without modifying the source adaptation container.
2. Inventory the trace directory before the run, including filenames, sizes, timestamps, and checksums when practical.
3. Generate and inspect a dry-run command using `evaluation/performance/vllm_profile.py` or `sglang_profile.py` as appropriate.
4. Execute with a unique output directory and preserve the command, stdout/stderr, native benchmark result, and validation record.
5. Re-inventory the trace directory and require a new or changed, non-empty, parseable trace in the expected time window. Old files, ordinary benchmark JSON, or a successful client exit are not capture proof.
6. Check expected worker/rank coverage and verify the suspected graph/backend path was actually exercised. Missing coverage or asynchronous export that has not completed leaves the result `incomplete`.

On timeout or non-zero exit, retain evidence and inspect profiler/service state. Do not silently restart services, reuse a stale trace, or retry indefinitely.

## Analyze bottlenecks

Build an evidence chain from end-to-end behavior to the narrowest supported layer:

1. First split the trace into Prefill, Decode, and Mixed/interference evidence using reliable service markers, iteration/token boundaries, shapes, or execution semantics. If a reliable boundary cannot be established, mark phase attribution `unknown/incomplete`; never divide total time by assumption.
2. Within each phase, separate request/network, scheduler/batching, sampling, memory/graph, communication, dispatch, and kernel activity. Do not combine the same kernel's Prefill and Decode calls when ranking hotspots because their shapes, counts, and optimization choices may differ.
3. Distinguish host runtime/driver activity, device kernels, communication, memory copies, synchronization, graph gaps, and unclassified events.
4. Identify per-phase cumulative time, call counts, representative shapes, rank imbalance, serialization, gaps, fallback, and implementation-hit evidence, then describe Prefill/Decode interference in the mixed timeline.
5. Compare each leading explanation against at least one plausible alternative, such as client limitation, warmup, cache state, graph break, load imbalance, phase interference, or an adjacent copy/merge cost.
6. Convert the result into one falsifiable phase-scoped experiment with an expected cross-phase and mixed end-to-end effect plus a stop condition.

Use `trace_to_summary.py` only as a category summary. Its possibly overlapping activity-duration sums are not critical-path time, device utilization, CPU self time, or proof of end-to-end impact. Inspect the timeline and relevant events before attributing a root cause.

Classify the next optimization as `framework`, `operator/replace`, or `operator/improve` using the project's mechanism-based rules. A hot kernel is a candidate, not proof that optimizing it will improve the service.

## Reprofile without overstating results

For `reprofile`, keep the scenario, profiler settings, warmup, rounds, and trace interpretation comparable to the earlier capture. Report whether the hotspot persisted, shrank, moved, or became ambiguous. Then invoke `$inference-performance-evaluation` in `targeted` or `checkpoint` mode to measure actual no-profiler performance. Do not derive a speedup percentage by comparing profiler traces.

## Record and route artifacts

Write the mode, scenario, service identity, profiler configuration, trace inventory/checksums, worker/rank coverage, phase coverage and boundary evidence, separate Prefill/Decode/Mixed hotspot summaries, interference, competing explanations, confidence, next experiment, result state, and artifact paths into the current experiment record.

- Profiling summaries and links belong in `models/<model>/<platform>/optimize/`.
- Large traces, raw logs, and tool outputs remain in the external or remote case directory.
- Profiling artifacts do not enter `acceptance/` as formal performance evidence.

Return a compact result containing: mode, scenario ID, service identity, trace validity and worker/rank coverage, phase-boundary evidence, separate Prefill/Decode/Mixed hotspots and interference, rejected or unresolved alternatives, conclusion boundary, artifact paths, and the next Skill to invoke.
