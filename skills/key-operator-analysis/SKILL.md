---
name: key-operator-analysis
description: Analyze critical LLM inference operators and reuse the local MLA Attention and mHC knowledge base when profiling identifies an operator-level bottleneck. Use for operator semantics, source-to-kernel tracing, performance modeling, benchmark design, and optimization validation; do not use for service-level tuning without operator evidence.
---

# Key Operator Analysis

Use this skill to turn an end-to-end bottleneck into a bounded operator investigation and a verifiable optimization decision.

## Entry condition

Before deep operator work, identify evidence that the operator or its surrounding dispatch, layout, synchronization, or communication path materially affects the target end-to-end metric. A high theoretical FLOP count alone is not sufficient.

If the evidence still points to request scheduling, networking, tokenization, batching, service configuration, or framework orchestration, continue the system-level investigation without loading the operator knowledge base.

## Shared method

Read [operator-analysis-method.md](references/operator-analysis-method.md) when beginning a new operator analysis or designing its correctness and performance experiments. Apply the relevant parts rather than recreating a separate generic workflow.

Keep Prefill and Decode separate. Distinguish algorithm, framework/dispatch, Kernel, communication, and hardware effects. Record model shapes, dtype, layout, execution mode, hardware, framework revision, warmup, timing method, and correctness oracle.

## Knowledge routing

Use [knowledge-index.md](references/knowledge-index.md) to select only the materials needed for the current operator.

- For MLA, latent KV cache, absorbed/unabsorbed execution, sparse MLA/DSA, or MLA backend selection, read the MLA report first. Read source snapshots only for the specific call chain being investigated.
- For mHC, multi-stream residual mixing, Sinkhorn normalization, or fused post+pre paths, read the mHC report.
- For a new operator, use the shared method and create a focused knowledge directory only after facts or reusable artifacts exist.

## Freshness and evidence

The bundled reports and source files are snapshots, not the current target runtime. Before proposing a code change:

1. Resolve the target model, framework, Plugin, backend, hardware, dtype, shapes, and execution mode.
2. Record the live code revision and verify that the documented symbol and dispatch path still exist.
3. Trace the real request path to the selected implementation or fallback.
4. Clearly separate copied knowledge, current verified facts, inference, and unresolved questions.

Do not attribute a model-level or system-level published speedup to one operator. Do not claim measured gains without target-hardware results.

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
