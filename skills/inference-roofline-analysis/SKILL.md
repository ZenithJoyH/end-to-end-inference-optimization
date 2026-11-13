---
name: inference-roofline-analysis
description: Analyze phase-separated LLM inference FLOPs, HBM traffic, timing, and matching hardware ceilings to identify bottlenecks and propose falsifiable optimization experiments. Use for compute-versus-bandwidth diagnosis, Roofline headroom, or hotspot migration using current traces, counters, or explicitly labeled estimates; collection belongs to inference-profiling and formal gains require no-profiler performance evaluation.
---

# Inference Roofline Analysis

Use Roofline to connect current Prefill/Decode/Mixed evidence to the next optimization decision. This Skill consumes existing evidence and produces a bounded diagnosis; it does not launch services, collect counters, change code, or run benchmarks itself. Read [references/roofline.md](references/roofline.md) for measurement conventions, platform discovery, formulas, examples, and the decision table.

## Automatic use in the optimization loop

The user does not need to name this Skill on each optimization task. At scenario direction selection, profiling handoff, hotspot/working-point migration and planning review, apply the automatic trigger rules in [SOP C5](../../docs/performance-optimization-sop.md#c5-用-roofline-连接瓶颈证据与下一步实验). Invoke when compute/bandwidth/efficiency attribution could change the next experiment, a hardware-headroom claim supports costly tuning, or changed inputs invalidate the earlier conclusion. The main Agent dispatches concrete analysis under the existing delegation rules.

Reuse an existing result when candidate, phase/rank/shape, measurement conventions and coverage still support the decision. If Roofline would not change an already supported request/host/communication experiment, note that reason in the existing decision and continue. Do not force counter collection or repeatedly invoke Skills on unchanged evidence.

Return the result to the requesting profiling, operator or planning workflow. The next-direction decision must use the bottleneck, removable cost, critical-path contribution, confidence and gaps to rank candidates and explain adoption/deferral. Select a first falsification experiment with guards and stop conditions; a chart or utilization report alone is not the deliverable. Use the existing experiment/planning records, without an additional trigger ledger.

Apply the shared handoff/reuse rules in SOP C5 before dispatch. Check completed results and in-flight requests for the same decision and binding; attach to an existing task rather than launch another. A known unsupported counter or exhausted request remains a recorded gap until its explicit reopening condition changes. A changed candidate does not implicitly preserve other phases: verify unaffected bindings and execution paths before reuse.

Missing-evidence and next-Skill outputs are requests returned to the main coordinator. Do not recursively invoke the caller or launch a new profiling/operator/planning cycle from this analysis. Only new evidence, changed inputs or a distinct decision question justify re-entry. Carry the original task budget and failed-attempt history across handoffs.

## Establish the question and scope

Read the current case contract, optimization-point record, no-profiler baseline summary, and linked profiling evidence. Resolve the current `scenario_id`, candidate/service identity, steady-state admission, hardware/partition, rank/worker coverage, phase-boundary method, actual batch/query/KV shapes, dtype/quantization, graph, and implementation-hit evidence.

State the decision this analysis must support: compute versus HBM bandwidth, inefficient execution below the roof, avoidable work despite a high roof efficiency, or a bottleneck that moved after a retained change. Keep Prefill and Decode separate and use Mixed to check interference. A shared mixed kernel remains mixed unless its work can actually be attributed; token ratios do not establish separate traffic or FLOPs.

This is a local project Skill, not permission for remote execution. Apply project delegation, container isolation, source ownership, and modification boundaries. Do not scan other models or the adaptation workspace to fill missing inputs.

## Audit the evidence before calculating

For each selected kernel or range, establish:

- source artifact and checksum where available, capture command/tool version, exact metric names/units, collection scope and multiplicity;
- algorithmic FLOPs (`F_algo`) versus executed work (`F_exec`), counting convention, Tensor/SIMT/integer path, padding/recomputation and uncounted operations;
- measured HBM read/write bytes versus logical traffic estimates, cache level, sampling/extrapolation boundaries and rank/worker coverage;
- time boundary and source, overlap/concurrency, graph replay, warmup, replay/cache/clock policy and measurement perturbation;
- compute and bandwidth ceilings with matching precision, execution unit, dense/sparse mode, partition, frequency conditions, and specification or calibration source.

PyTorch allocation statistics do not measure HBM traffic; partial FLOPs estimates do not count all fused kernels. A GPU utilization percentage does not identify a roof. Do not attach a Tensor Core ceiling to scalar reductions or mix integer operations with floating-point counts without a matching model.

When evidence is missing, retain unknown values and distinguish `measured`, `estimated`, and `incomplete` attribution in the report; these are evidence descriptions, not new native gate states. Request only the smallest useful collection through the coordinator and `$inference-profiling`: preserve a valid timeline and request only missing native counter reports; use `analyze` for sufficient existing data, and `capture/reprofile` only for the missing collection scope. Counter unavailability does not block independently supported, authorized experiments. Do not silently install tools, widen permissions, or substitute another vendor's counters.

## Calculate and interpret the distance

For a consistent work convention and scope, calculate HBM bytes `Q=Q_read+Q_write`, intensity `I=F/Q`, achieved performance `P=F/t`, achieved bandwidth `BW=Q/t`, roof `P_roof=min(C_peak,BW_peak*I)`, and efficiency `eta=P/P_roof`. Report the ceiling source alongside the result; keep specification and empirical roofs separate.

Calculate hardware roof efficiency from executed work when that count is valid. If only algorithmic work is available, label the result as a useful-work estimate and explain the missing executed work. Never mix `F_algo` on one axis with `F_exec` on another. Zero or unavailable denominators leave the corresponding ratio undefined rather than forcing a numeric result.

Start with representative kernels, then reconcile them with the phase timeline and critical path. Do not sum overlapping kernel durations as elapsed phase time, average per-kernel utilization percentages, sum rank times as service latency, or extrapolate a sampled hotspot to full-stage measured traffic. An aggregate stage roof is a loose bound; heterogeneous kernels may have different compute ceilings and serial resource constraints.

Check at least one competing explanation. Low roof efficiency may reflect dependency latency, low parallelism, instruction throughput, cache/shared-memory limits, synchronization or measurement distortion. High efficiency can coexist with redundant bytes, padding or recomputation. The phase name alone does not determine its bottleneck.

## Produce the next experiment

Route by the mechanism in the reference decision table and the project classification:

- `framework`: remove demonstrated orchestration waste, change batching/graph working point, or reorganize data/communication;
- `operator/replace`: compare a compatible existing public implementation on the actual phase/rank shapes;
- `operator/improve`: reduce traffic/work or improve the current kernel, fusion, layout, parallelism or code generation; recommend `$key-operator-opt` and SOP C4 to the coordinator when relevant.

For each proposed direction, state the evidence, affected critical-path share, predicted change in bytes/operations/waits, added full-call costs, applicability guard, one primary variable, smallest falsification experiment, success/stop conditions, rollback, and cross-phase metrics. Use ranges or `unknown` where the evidence does not support precise gains. `1/eta` is fixed-work model headroom, not an end-to-end speedup promise.

The executor follows existing correctness/accuracy and target graph capture/replay requirements. Propose no-profiler `targeted/checkpoint` Mixed measurements and cross-phase guards through `$inference-performance-evaluation`; the coordinator dispatches them at the existing promotion point, reusing valid results. After a retained change, reassess the working point and evidence freshness; recommend scoped collection through Profiling only when necessary and return conclusions for the next planning decision. Do not automatically start a full planning review after every analysis; follow its existing triggers. This Skill cannot declare formal acceptance or authorize weight/tokenizer changes.

## Record the result

Use the existing optimization-point Markdown and evidence/hypothesis/next-action fields in `optimize/state.yml`; update the README index as needed. Follow the [Roofline diagnostic record contract](../../docs/experiment-contract.md#roofline-诊断记录按需). Keep raw traces and counter exports external. Do not add a mandatory YAML schema, native gate, model subdirectory or per-capture business ledger.

Return: scenario/candidate identity; phase/rank/shape scope; measured/estimated/missing coverage; FLOPs/HBM/time/ceiling conventions; intensity, achieved throughput/bandwidth and roof distance where valid; supported bottleneck and alternatives; next falsifiable experiment and Skill handoff; limitations and record paths. Missing hardware evidence limits the conclusion, not unrelated authorized work.
