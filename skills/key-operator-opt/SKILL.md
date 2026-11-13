---
name: key-operator-opt
description: Optimize hotspot ATen and vLLM fused operators using platform-specific case evidence. Use for operator dispatch, layout, fusion or kernel investigations, and to distill completed experiments into reusable platform guidance.
---

# Key Operator Optimization

Use this skill to turn an end-to-end bottleneck into a bounded operator investigation and a verifiable optimization decision, then make the next investigation of the same operator faster and deeper.

## Entry condition

Before deep operator work, identify evidence that the operator or its surrounding dispatch, layout, synchronization, or communication path materially affects the target end-to-end metric. A high theoretical FLOP count alone is not sufficient.

If the evidence still points to request scheduling, networking, tokenization, batching, service configuration, or framework orchestration, continue the system-level investigation without loading the operator knowledge base.

## Shared method

Read [operator-analysis-method.md](references/operator-analysis-method.md) when beginning a new operator analysis or designing its correctness and performance experiments. Apply the relevant parts rather than recreating a separate generic workflow.

Keep Prefill and Decode separate. Distinguish algorithm, framework/dispatch, Kernel, communication, and hardware effects. Record model shapes, dtype, layout, execution mode, hardware, framework revision, warmup, timing method, and correctness oracle.

For compute/bandwidth attribution and headroom, automatically apply the [SOP C5 trigger and handoff rules](../../docs/performance-optimization-sop.md#c5-用-roofline-连接瓶颈证据与下一步实验). First reuse the caller's valid [$inference-roofline-analysis](../inference-roofline-analysis/SKILL.md) result or matching active task; request a bounded new analysis through the coordinator only when the question or inputs require it. Return its candidate choice, expected removable cost and falsification experiment to the original decision point, without calling Roofline again on unchanged inputs. Carry phase/rank/shape-bound measured or explicitly estimated FLOPs, HBM traffic, timing and matching ceilings into the operator hypothesis. Compare existing providers before deep tuning when appropriate; target removable traffic/computation or execution inefficiency rather than a utilization percentage, and verify full-call cost plus no-profiler Mixed impact.

If analysis requires additional counters, return the precise gap to the coordinator for deduplication and scoped Profiling collection. Reuse the existing timeline and native reports, wait for a matching in-flight request, and preserve known unsupported/failed gaps until reopening conditions change. Do not start a separate profiler/benchmark chain merely because this operator task was entered from Roofline; numerical tests and full-call/E2E measurements remain separately assigned work under the existing validation contract.

## Knowledge routing

Match the target platform and operator using [knowledge-index.md](references/knowledge-index.md). For MetaX, the [platform guide](references/platforms/metax.md) connects a measured symptom to a first experiment, its counterexamples and the original evidence. If summarizing past cases, start from their experiment records. A new service run is only needed to establish a new runtime or performance claim.

For an existing provider, compare the complete operator through its public entry point (`operator/replace`). For a kernel or fusion change (`operator/improve`), isolate the proposed mechanism against the current implementation. Use the effective per-rank shapes and graph replay frequencies from the target stage to choose the comparison. If the emitted code points to a compiler change, compare the same kernel under the original, patched and restored private FlagTree builds. Check loaded binaries, isolate compiled caches, and cover other kernels that reach the changed rule. See the [compiler experiment in SOP C4](../../docs/performance-optimization-sop.md#修改优化容器内的-flagtree).

- For an operator with prior cases, read its stable `README.md`, then its `optimization-map.md`, then only the matching cards in `case-index.md`. This order gives the current mental model, actionable decisions, and supporting evidence without loading full historical cases.
- For MLA, latent KV cache, absorbed/unabsorbed execution, sparse MLA/DSA, or MLA backend selection, follow the MLA routes in the index. Read source snapshots only for the specific call chain being investigated.
- For mHC, multi-stream residual mixing, Sinkhorn normalization, or fused post+pre paths, read the mHC report.
- For a new operator, use the shared method. Keep the first full investigation in the actual case; create or extend the operator knowledge directory only when reusable facts or artifacts exist.

## Case-driven learning loop

Do not append complete case reports to an operator's stable `README.md`. Keep `docs/cases/<case>/` to a small number of readable summaries linking to the authoritative records under `models/<model>/<platform>/`: `baseline/` for the original environment and measurements, `optimize/state.yml` for the structured ledger, `optimize/README.md` for the multi-round overview, one `optimize/<experiment-id>.md` for each operator optimization point, and `acceptance/` for final acceptance configuration and status. Raw commands, patches, logs, traces and other large artifacts remain external; record their locations and checksums.

At the start of an operator optimization:

1. Match the live stage, effective per-rank shape, dtype, layout, backend, hardware, execution mode, and revision against the operator optimization map and case index.
2. Reuse only the closest supported mechanism, validation matrix, known failure, or first experiment. Treat unmatched dimensions as unknown, not as implicit compatibility.
3. Record the prior belief or existing knowledge that the new case will test.

When closing the case, read [case-to-knowledge.md](references/case-to-knowledge.md) and write an explicit knowledge delta:

- what was believed before;
- what the live path and experiment showed;
- what was confirmed, refined, contradicted, or left open;
- which future decision becomes faster or more precise;
- the exact scope and evidence level.

Then update at most the layers justified by the evidence:

1. Complete the relevant model/platform structured ledger, the optimization point's `<experiment-id>.md`, and the `optimize/README.md` summary index, then link them from the concise `docs/cases/<case>/` summary; do not duplicate the experiment body or raw artifacts there.
2. `operators/<operator>/case-index.md`: add a compact evidence card when the case materially analyzed the operator, including failed and negative experiments.
3. `operators/<operator>/optimization-map.md`: update when the case changes a future diagnostic check, candidate ranking, applicability guard, stop condition, or next experiment.
4. `operators/<operator>/README.md`: update only when the stable semantic, implementation model, bottleneck model, or cross-case conclusion changed. A new performance number alone is not sufficient.

When cases change the first experiment or stop condition for a platform, update `references/platforms/<platform>.md` with the signal, matching conditions, evidence level and source experiment. Link a new platform from the knowledge index once it has case-backed guidance. Keep full results in the experiment record and keep conflicting results visible with their scope.

If the case produces no new operator understanding, link it in the case index and state `knowledge_delta: none`; do not manufacture a lesson.

## Freshness and evidence

The bundled reports and source files are snapshots, not the current target runtime. Before proposing a code change:

1. Resolve the target model, framework, Plugin, backend, hardware, dtype, shapes, and execution mode.
2. Record the live code revision and verify that the documented symbol and dispatch path still exist.
3. Trace the real request path to the selected implementation or fallback.
4. Clearly separate copied knowledge, current verified facts, inference, and unresolved questions.

Do not attribute a model-level or system-level published speedup to one operator. Do not claim measured gains without target-hardware results.

Historical cases accelerate hypothesis selection; they never replace live dispatch proof, correctness checks, or same-condition end-to-end validation. Keep observation, reproduced, transferred, and invariant evidence visibly distinct. When a later case conflicts with the map, preserve both cards, narrow the old scope, and mark the disputed rule instead of silently overwriting history.

## Optimization output

Produce the smallest useful artifact for the task. It should normally include:

- operator role, inputs/outputs, shapes, dtype, layout, and Prefill/Decode behavior;
- source-to-Kernel call chain and actual dispatch evidence;
- FLOPs, memory traffic, arithmetic intensity, temporary memory, and likely bottleneck;
- baseline correctness oracle and benchmark matrix;
- profiler evidence tied to the end-to-end bottleneck;
- candidate optimization, applicability, costs, risks, fallback, and graph constraints;
- fair baseline/candidate results, error metrics, regressions, and scope of the conclusion.

When implementing an optimization, preserve a reference path, validate boundary and non-aligned shapes, and require the target graph path to capture and replay correctly. A separate eager service is optional diagnostic evidence, not a performance-optimization gate.
