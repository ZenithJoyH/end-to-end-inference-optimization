---
name: inference-accuracy-diagnosis
description: Diagnose correctness and accuracy regressions discovered during end-to-end LLM inference optimization. Use when baseline sanity or minimal regression fails, a formal score falls below its frozen threshold, evidence is invalid, or the user asks to investigate output-health symptoms. Output-health symptoms alone are diagnostic and do not invalidate a score that meets the threshold.
---

# Inference Accuracy Diagnosis

Use this Skill to isolate an observed accuracy problem to the smallest supported cause, produce a reproducible failing case, and define the fix and revalidation path. Stop stacking performance optimizations only for a failed frozen score threshold, failed required minimal regression, or invalid evidence that prevents a trustworthy score. A timeout, truncation, empty/repeated response, or similar output-health observation can be investigated without changing an already-passing accuracy verdict or automatically pausing optimization. Do not treat a score drop, one mismatched output, or disabling a component as root-cause proof by itself.

## Establish whether there is a real accuracy problem

Start from the exact failed result and classify it before changing code:

| Class | Typical signal | First action |
|---|---|---|
| Measurement invalid | wrong task/filter, incomplete samples, changed dataset/config, parser/schema mismatch, stale files | Repair the evaluation evidence and rerun the same contract |
| Identity/configuration drift | model, weights, tokenizer, chat template, endpoint, sampling, graph, service instance, or source differs | Restore a comparable service/manifest; use accuracy `gate-check` for gate validity |
| Request/output health | timeout, empty/truncated/malformed/repeated output, wrong stop behavior | Record as non-gating, then reproduce only when operational diagnosis is useful or requested |
| Numerical/semantic regression | stable baseline/candidate answer or tensor mismatch under the same inputs | Bisect changes and localize the first divergent layer/path |
| Execution-mode regression | graph capture/replay, concurrency, rank layout, or fallback path fails | Minimize across graph state, concurrency, shape, and rank coverage |
| Expected nondeterminism | uncontrolled seed/sampling or stochastic routing explains unstable output | Freeze randomness and determine whether the variance exceeds the contract |

If task provenance, sample completeness, service identity, or comparison conditions are invalid, record `measurement-invalid` rather than diagnosing model code. Fixing a gate mismatch is not an accuracy-root-cause investigation.

## Freeze the incident

Before reproduction, record:

- issue ID, triggering accuracy mode, covered experiment IDs, last known-good identity, failing candidate identity, and first observed time;
- exact config/contract/service manifest, runner and artifact SHA, metric/filter, sample set, score/health difference, and progress-monitor record;
- all retained changes since the last known-good result, their dependency order, actual import paths, and whether each path was hit;
- whether the problem appears in baseline sanity, scoped regression, full GPQA, optional output-health observation, graph capture/replay, single/C8, or particular ranks/shapes; state explicitly whether it is gate-blocking.

Preserve the failing artifacts and do not overwrite them with retries. Use the current case-specific remote directory for large logs and samples.

## Build the smallest faithful reproducer

1. Re-run the same failing request, sample ID, or tensor case with the same prompt/token IDs, generation settings, seed, endpoint, model identity, and stopping behavior.
2. Compare last known-good and candidate paths under identical conditions. Start with one request or the narrowest affected shape, then add C8, graph, long context, fallback, or distributed coverage only when needed to reproduce.
3. Capture raw request/response, token counts, finish reason when available, service errors, implementation-hit evidence, and stable hashes. Keep private dataset content in the external evidence location.
4. Repeat enough to separate deterministic divergence from stochastic variance. Do not use temperature or seed changes to make a failing sample disappear.
5. Do not specialize code to GPQA item IDs, answer strings, prompt text, or evaluation-only paths. Failing benchmark samples are localization evidence, not optimization targets.

When a rerun uses `$inference-accuracy-evaluation`, reuse its case-specific progress heartbeat. Do not create a duplicate monitor; keep the default 30-minute notifications and terminal cleanup behavior.

## Bisect by risk and execution boundary

Work from the last known-good state using reversible, single-variable comparisons. Preserve user changes and existing patches; do not reset shared repositories.

Check in this order unless evidence points elsewhere:

1. Evaluation task/data/filter and runner behavior.
2. Model/weights/tokenizer/chat template, endpoint, sampling, dtype/quantization, and launch configuration.
3. Candidate patch/config bisection in dependency order, prioritizing changes with the largest correctness surface.
4. graph capture versus repeated replay, single request versus C8, target versus fallback shapes, and short versus long context. Do not require a separate eager service unless it is deliberately introduced as a diagnostic reference.
5. single-rank/local reference versus distributed layout, communication, routing, and rank imbalance.
6. Plugin dispatch/backend selection, actual imported function, fallback behavior, and cache isolation.
7. Operator-level inputs/outputs, dtype, shape, stride/layout, masking, indexing, accumulation, overflow/underflow, NaN/Inf, boundary and zero-token behavior.

For attention/KV, verify positions, masks, cache writes/reads, block mapping, sequence boundaries, and prefill/decode transitions. For MoE, verify routing indices/weights, capacity, packing/unpacking, expert/rank mapping, and combine semantics. For fused or replacement operators, compare the complete semantic unit, including preprocessing, merge, copy, communication, and output layout.

Do not attribute the issue to the first change whose removal makes it disappear. Confirm that re-enabling the isolated change reproduces the failure and that the suspected path actually executed.

## Use other Skills at clear boundaries

- Invoke `$key-operator-analysis` only after the divergence has been isolated to a concrete operator, dispatch, layout, or adjacent fusion path.
- Invoke `$inference-profiling` only when execution-path or rank/graph-hit evidence is missing; profiler timing is not accuracy evidence.
- Use `$inference-accuracy-evaluation` `minimal-regression` to validate each candidate fix, and `formal-gate` when the original failure was formal GPQA or when policy requires a new gate.
- Pause `$inference-performance-evaluation` only when the frozen score threshold, required minimal regression, or evidence-validity scope is failing. An output-health-only investigation is non-gating and may run alongside continued performance work.
- After resolution changes the remaining optimization priorities, include the incident in the next `$inference-optimization-planning` review.

## Prove the root cause and resolution

A root cause is `confirmed` only when all applicable evidence exists:

- a stable minimal reproducer distinguishes last known-good from failing candidate;
- one isolated variable or execution boundary controls the divergence;
- the target path and implementation are proven to execute;
- mechanism-level evidence explains the observed output/score failure;
- the fix passes the reproducer, affected boundary/fallback matrix, graph capture/replay and concurrency/rank coverage as applicable;
- the original accuracy scope is rerun successfully with the exact fixed service identity.

Otherwise use `suspected`, `not-reproduced`, or `measurement-invalid`. A formal GPQA failure is resolved only by a new valid `formal-gate` for the fixed candidate; a small reproducer pass alone is insufficient.

## Record the incident

Update `models/<model>/<platform>/optimize/state.yml` with the stable issue ID, trigger, classification, failing evidence, last known-good and candidate identities, minimized reproducer, bisection result, root-cause confidence, fix/rollback, revalidation, remaining gaps, remote artifact links, and any superseded-decision summary; synchronize the human summary in `optimize/README.md`. Do not create an `optimize/history/` or per-incident directory.

Raw samples, configs, scripts, logs, bisection outputs, and service manifests remain in the external case directory. Only a final accuracy pass/gate status updates `acceptance/state.yml` and `acceptance/README.md`.

Return a compact result containing: issue ID, classification, whether the issue is gate-blocking, reproduction status, isolated boundary/change, root-cause confidence, supporting and opposing evidence, fix or rollback status, required revalidation, artifact path, and whether performance optimization may continue.
