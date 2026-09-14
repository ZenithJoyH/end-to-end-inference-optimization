---
name: inference-accuracy-evaluation
description: Orchestrate graph-mode correctness checks and formal GPQA accuracy gates during end-to-end LLM inference optimization. Use before establishing a performance baseline, after every retained optimization for scoped regression, after 4–5 low-risk changes, immediately after high-risk changes, before formal performance, and when validating a final candidate; do not use as a generic benchmark suite unrelated to the active optimization target.
---

# Inference Accuracy Evaluation

Use this skill to select the correct accuracy-validation depth, execute the existing project workflow, and bind the result to the exact inference service being optimized. It orchestrates existing tools; it does not implement another model evaluator.

## Select the mode

Choose one mode and record it with the experiment IDs it covers:

| Mode | Trigger | Output scope |
|---|---|---|
| `baseline-sanity` | Before accepting the optimization container and performance baseline | Baseline service correctness status; no formal gate |
| `minimal-regression` | After every optimization point before retaining its performance result | Only the changed path, boundary/fallback shapes, and required graph capture/replay behavior |
| `formal-gate` | After 4–5 retained low-risk points, immediately after a high-risk change, or for a final candidate without an exact valid gate | Full GPQA score and service-bound accuracy gate |
| `gate-check` | Immediately before formal candidate performance | Validity of an existing gate against the current service identity |

Low-risk batching changes only the frequency of `formal-gate`; it never removes `minimal-regression`. Treat numerical semantics, dtype/quantization, attention/KV cache, MoE routing, sampling/top-k/top-p, cross-op fusion, new algorithms/backends, broad custom-op dispatch, rank layout/communication, graph/fallback coverage, or suspicious output as high risk.

## Read only the needed workflow

- For `baseline-sanity` or `minimal-regression`, read the correctness and experiment-loop sections of [the SOP](../../docs/performance-optimization-sop.md) and the active case contract. Load operator-specific references only after the changed path is known.
- For `formal-gate` or `gate-check`, read [the evaluation entrypoint](../../evaluation/README.md), [the accuracy tool contract](../../evaluation/accuracy/README.md), and [the experiment contract](../../docs/experiment-contract.md) before running commands.

## Required identity and artifacts

Bind every result to the target Host, optimization container, service instance, model/weights, tokenizer, engine, Plugin, FlagGems-vllm, FlagGems, launch configuration, graph mode, and covered experiment IDs. Resolve these from the current runtime; do not reuse a historical manifest because paths or version strings look similar.

When the user supplied a remote work directory, place remote configs, inspect evidence, logs, samples, results, health review, and gate under its unique case directory. Keep intermediate accuracy records under the model/platform `optimize/` record; only the final candidate summary and accepted status belong in `acceptance/`. Large or sensitive artifacts remain remote, with paths and necessary checksums recorded locally.

## Schedule progress notifications

Whenever `baseline-sanity`, `minimal-regression`, or `formal-gate` starts an actual accuracy-evaluation process, create a recurring heartbeat automation attached to the current Codex task before launching the process. The default cadence is every 30 minutes; use a user-specified cadence when provided. `gate-check` only validates existing evidence and does not create a monitor.

Use a case- and experiment-specific automation name. Reuse or update an existing matching monitor instead of creating duplicates. Record its automation ID, cadence, start time, monitored Host/process and artifact paths in the experiment record. For a long-running `formal-gate`, successful monitor creation is a preflight requirement unless the user explicitly waives periodic notifications. If scheduling is unavailable, report that before starting and do not pretend monitoring is active; this operational gap does not change the numerical meaning of a completed accuracy result.

Each heartbeat must inspect the exact evaluation process and bound artifacts read-only, then notify the current task even when progress is unchanged because the user explicitly requested periodic reports. Include:

- case/experiment ID, accuracy mode, current stage, elapsed time, process health, and last artifact update;
- completed unique questions out of 198 only when the current samples/run evidence supports that count; never use raw JSONL line count when multiple filters can create multiple rows;
- newly observed errors, timeouts, empty/truncated output indicators, or stalled progress;
- ETA only when supported by observed progress; otherwise say it is unavailable;
- terminal state and result/gate paths when completed, failed, or cancelled.

The monitor must not alter, restart, or duplicate the evaluator or model service. When evaluation reaches a terminal state, send the terminal notification and pause or delete the matching heartbeat. The main accuracy workflow must also clean it up on normal completion, failure, cancellation, or early stop and record cleanup evidence. A short evaluation that finishes before the first 30-minute tick still creates and then removes the monitor without emitting a misleading progress update.

## Baseline and minimal regression

1. Identify the changed semantic surface and a trustworthy reference or prior path.
2. Test representative, boundary, non-aligned, fallback, empty/zero-token, dtype and layout cases that the change can affect. Require the target graph service to start, capture, and complete at least two replays. Eager service validation is not required for performance optimization.
3. Run fixed smoke and C8 service checks when the change can affect request-level behavior. Inspect timeouts, empty or truncated output, malformed text, abnormal repetition, errors, and target-path/fallback evidence.
4. Record `passed`, `failed`, or `incomplete` with the exact experiment ID. A minimal pass is not a formal model-accuracy pass.
5. On a required minimal-regression failure or invalid evidence, stop candidate promotion and invoke `$inference-accuracy-diagnosis`. Fix or revert before adding another optimization point. Timeout, empty/truncated output, repetition, or formatting symptoms may trigger diagnosis, but do not independently fail accuracy when a valid formal score meets the frozen threshold.

## Formal gate

Use the prescribed target-machine flow; do not substitute an auxiliary runner:

1. Confirm container lineage and mount parity have passed, and capture the current candidate service manifest. When formal accuracy and performance share the service, retain `--no-enable-prefix-caching` and prove prefix caching is disabled.
2. In a container based on `harbor.baai.ac.cn/flageval/flageval-llmeval:v1`, use `evaluation/accuracy/formal_accuracy.py` around the SHA-verified original `test/Accuracy_test/llmrun.py`.
3. Capture task and dataset provenance, freeze the metric/threshold and sample contract, then run `--preflight-only` against the current service.
4. Run full `gpqa_diamond_generative_cot` with `limit=0` and `expected_samples=198`. Do not replace the default single-service runner with the parallel runner unless the user explicitly requested a shard or multi-service design.
5. Validate task/config/service identity and native evidence needed to prove that the reported score belongs to this candidate and frozen threshold. Record timeout, truncation, empty or duplicate output only as optional diagnostics.
6. Issue the gate with `evaluation/accuracy/acceptance.py issue`. The accuracy verdict is `passed` exactly when the valid formal `score >= threshold`; equality passes.

If a batched set of 4–5 changes scores below the threshold, freeze the set and invoke `$inference-accuracy-diagnosis`. Isolate the responsible point by rollback or splitting, fix or revert it, run minimal regression, then rerun the same formal scope. Do not resume stacking performance changes until a new valid `score >= threshold` gate exists. A combined pass proves only the bound combination, not every point independently.

When the formal score is below threshold or score evidence is invalid, invoke `$inference-accuracy-diagnosis` with the frozen contract, service identity, failed artifacts, last known-good evidence, and covered experiment IDs. Locate and repair or revert the regression, then rerun the same formal contract; do not loosen the metric, filter, sample set, or threshold as a substitute for diagnosis. Output-health observations alone remain non-gating when the valid score meets threshold.

## Gate check and invalidation

Before formal performance, run `evaluation/accuracy/acceptance.py check` with a freshly captured service manifest. Reuse the gate only when it still binds the exact frozen source, configuration, artifacts, and service identity.

A service restart, source/configuration change, weight or tokenizer change, inference-affecting launch change, or mismatched artifact checksum invalidates the old gate. Run `formal-gate` again when the final candidate lacks an exact valid gate.

## Report

State the mode, covered experiment IDs, service identity, checks performed, evidence locations, progress-monitor ID/cadence/status, result, limitations, next trigger, and whether formal performance is allowed. Use `incomplete` when required evidence is missing; never convert diagnostic or minimal checks into a formal acceptance claim.
