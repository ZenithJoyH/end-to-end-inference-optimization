---
name: key-operator-analysis
description: Analyze critical LLM inference operators, reuse case-derived optimization knowledge, and distill verified end-to-end operator cases into deeper reusable understanding. Use when profiling identifies an operator, dispatch, layout, fusion, or adjacent communication bottleneck, or when closing such a case; do not use for service-level tuning without operator evidence.
---

# Key Operator Analysis

Use this skill to turn an end-to-end bottleneck into a bounded operator investigation and a verifiable optimization decision, then make the next investigation of the same operator faster and deeper.

## Entry condition

Before deep operator work, identify evidence that the operator or its surrounding dispatch, layout, synchronization, or communication path materially affects the target end-to-end metric. A high theoretical FLOP count alone is not sufficient.

If the evidence still points to request scheduling, networking, tokenization, batching, service configuration, or framework orchestration, continue the system-level investigation without loading the operator knowledge base.

## Shared method

Read [operator-analysis-method.md](references/operator-analysis-method.md) when beginning a new operator analysis or designing its correctness and performance experiments. Apply the relevant parts rather than recreating a separate generic workflow.

Keep Prefill and Decode separate. Distinguish algorithm, framework/dispatch, Kernel, communication, and hardware effects. Record model shapes, dtype, layout, execution mode, hardware, framework revision, warmup, timing method, and correctness oracle.

## Knowledge routing

Use [knowledge-index.md](references/knowledge-index.md) to select only the materials needed for the current operator.

- For an operator with prior cases, read its stable `README.md`, then its `optimization-map.md`, then only the matching cards in `case-index.md`. This order gives the current mental model, actionable decisions, and supporting evidence without loading full historical cases.
- For MLA, latent KV cache, absorbed/unabsorbed execution, sparse MLA/DSA, or MLA backend selection, follow the MLA routes in the index. Read source snapshots only for the specific call chain being investigated.
- For mHC, multi-stream residual mixing, Sinkhorn normalization, or fused post+pre paths, read the mHC report.
- For a new operator, use the shared method. Keep the first full investigation in the actual case; create or extend the operator knowledge directory only when reusable facts or artifacts exist.

## Case-driven learning loop

Do not append complete case reports to an operator's stable `README.md`. Keep `docs/cases/<case>/` to a small number of readable summaries linking to the authoritative records under `models/<model>/<platform>/`: `baseline/` for the original environment and measurements, `optimize/` for experiments, commands, patches, failures and rollback, and `acceptance/` for final acceptance configuration and status. Raw logs, traces and other large artifacts remain external; record their locations and checksums.

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

1. Complete the relevant model/platform records and link them from the concise `docs/cases/<case>/` summary; do not duplicate the experiment history or raw artifacts there.
2. `operators/<operator>/case-index.md`: add a compact evidence card when the case materially analyzed the operator, including failed and negative experiments.
3. `operators/<operator>/optimization-map.md`: update when the case changes a future diagnostic check, candidate ranking, applicability guard, stop condition, or next experiment.
4. `operators/<operator>/README.md`: update only when the stable semantic, implementation model, bottleneck model, or cross-case conclusion changed. A new performance number alone is not sufficient.

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

When implementing an optimization, preserve a reference path, validate boundary and non-aligned shapes, and cover eager plus graph capture/replay when the serving path uses graph execution.
