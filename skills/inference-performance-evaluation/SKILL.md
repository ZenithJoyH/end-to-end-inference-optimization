---
name: inference-performance-evaluation
description: Orchestrate baseline, phase-aware targeted/checkpoint, and formal no-profiler performance measurements during end-to-end LLM inference optimization. Use when establishing or simplifying a slow baseline, separating prefill and decode evidence for the current target, testing a milestone, formally closing one ordered scenario, or validating the final all-target combination; use the separate inference-profiling skill for trace attribution.
---

# Inference Performance Evaluation

Use this Skill to select the smallest valid performance test for the current optimization stage, run the maintained performance toolchain, and bind the result to the exact service, scenario, workload, and experiment. Do not create another benchmark runner or copy logic from `evaluation/performance/`.

## Select one mode

| Mode | Trigger | Minimum scope | Supported conclusion |
|---|---|---|---|
| `baseline` | A new optimization container has passed environment and correctness gates, or a scenario has no comparable baseline | Freeze the scenario catalog, then measure the acceptance set or a clearly identified scenario baseline without profiler | Baseline facts for exactly the measured scenarios |
| `targeted` | Testing one optimization hypothesis | Directly affected scenario(s), plus a cheap adjacent/fallback/stage sentinel when spillover risk exists | Local result for the listed `scenario_id` values only |
| `checkpoint` | Several changes are retained, the hotspot moves, candidates are combined, or a cross-scenario mechanism changes | Every affected scenario | Stage result for the listed affected set |
| `formal` | A milestone meets its pre-frozen major-improvement trigger, the current target is ready to close, or the final combination is frozen; the candidate has an exact valid accuracy gate | Intermediate: the current single ordered target scenario. Final: the complete acceptance set. Both use comparable baseline, candidate, and revert repetitions | Formal result for the current target, or the final all-target performance gate, according to the recorded lifecycle |

If the requested mode is not explicit, infer it from the trigger above. State the selected mode, scenarios, and conclusion boundary before executing.

## Read only what the mode needs

For every mode, read:

- `evaluation/performance/README.md` for maintained commands and current tool limits.
- The active case record and its experiment contract for scenario IDs, metrics, thresholds, service identity, and artifact paths.

Additionally:

- For `formal`, read `evaluation/README.md`, `docs/experiment-contract.md`, and invoke `$inference-accuracy-evaluation` in `gate-check` mode before sending performance traffic.
- When this invocation must create or restart the optimization service, read `docs/container-isolation.md` and satisfy its image-lineage and mount-parity gates first.

## Freeze the measurement contract

Before measuring, record:

- Skill mode, experiment ID, `scenario_id` list, `test_scope`, target/sentinel roles, and omitted acceptance scenarios.
- Model, tokenizer, Host, optimization container, service instance, engine, Plugin/FlagGems-vllm/FlagGems revisions, hardware/topology, graph mode, launch configuration, and client identity.
- Input/output lengths, endpoint, EOS/sampling, load mode, concurrency or arrival pattern, requests, seed, timeout, warmup, repetitions, main metrics, guard metrics, SLO, thresholds, and stop rules.
- For each case, its `stage=prefill|decode|mixed`, parent target scenario, phase-isolation method, residual cross-phase/scheduler cost, and cross-phase guard. Formal target cases are `mixed`.
- External or remote output directory. Use the user-provided remote work root only through its case-specific subdirectory.

For reduced input/output lengths, requests, concurrency, repetitions, or scenarios, create a matching reduced baseline. Map the milestone to its target scenario(s), record every workload difference and its promotion condition, and never compare a reduced candidate with a target/full-plan historical summary.

If a target baseline exceeds its pre-recorded diagnostic time budget, preserve the partial evidence as `deferred-too-slow/incomplete` and stop waiting. Select the project-recorded recovery strategy: run a smaller comparable `targeted` milestone, perform static analysis outside this Skill, or combine both. A reduced milestone may provide explicit numeric feedback for its own workload, but it is not the target baseline and cannot support a cross-workload speedup claim.

## Separate prefill and decode evidence

Before choosing an optimization direction for the current target scenario, maintain three explicit views:

- `prefill`: prompt processing, TTFT/input-token throughput, prefill shapes, and any service-internal prefill evidence;
- `decode`: autoregressive iterations, TPOT/ITL/output-token throughput, KV behavior, and decode batch shapes;
- `mixed`: phase interference, scheduling/queuing, resource contention, and the complete target workload.

TTFT and TPOT/ITL are client-visible proxies and may include queuing, scheduler, sampling, network, or streaming costs. Do not relabel them as pure device phase time. A phase-focused targeted plan may use a single-token/short-output prefill probe or a sufficiently long-output decode probe, but it must record the isolation method and residual costs, use its own comparable baseline, and map to a parent target scenario. Guard a prefill candidate with decode and mixed metrics; guard a decode candidate with prefill and mixed metrics. A phase-focused pass is an optimization signal only: verify every retained candidate on the parent `mixed` workload before treating the target scenario as improved or complete.

## Enforce the service gate

For every new vLLM baseline, candidate, and revert performance service:

1. Confirm the installed CLI supports `--no-enable-prefix-caching`.
2. Include `--no-enable-prefix-caching` in the effective launch command. Do not require `--no-enable-log-requests`.
3. Prove the running service uses that state from process/runtime evidence.
4. Record `launch_config.enable_prefix_caching=false` and `performance_context.prefix_cache_state=disabled` in the service manifest.

If prefix caching is the explicit optimization variable, require a separate contract, new baseline, cache preparation, reuse ratio, and hit evidence. Otherwise a missing or enabled state makes the comparison `incomplete`.

## Execute and validate

1. Generate and inspect the dry-run command before sending requests.
2. Use the maintained entry that matches the engine and purpose:
   - `evaluation/performance/vllm_perf.py` for parameterized vLLM measurements.
   - `evaluation/performance/compare_performance.py` for frozen baseline/candidate/revert comparisons.
   - Other maintained entries only within the limits stated in `evaluation/performance/README.md`.
3. Use unique run IDs and refuse to overwrite an existing run directory.
4. Validate request counts, successes, token counts, native result schema, required finite metrics, warmup status, repetitions, output SHA, current service/client identity, and the declared phase role. Preserve phase results separately rather than averaging prefill and decode into one attribution.
5. For comparable runs, evaluate the pre-frozen main metrics, guards, SLO, variability, and baseline/revert drift. Preserve the three-state result: `passed`, `failed`, or `incomplete`.

Stop and keep `incomplete` when the client is the bottleneck, the service identity or prefix-cache state is unproven, workloads differ, results are partial, warmup is unstable, repetitions are insufficient, or revert drift prevents attribution. Do not cherry-pick successful rounds or scenarios.

When performance evidence cannot localize the bottleneck, invoke `$inference-profiling`. Keep all profiler-on timings outside this Skill's baseline/candidate/revert comparison, and return to `targeted` or `checkpoint` mode afterward to verify end-to-end impact without profiler.

## Formal performance measurement

In `formal` mode:

1. Use `$inference-accuracy-evaluation` `gate-check` against the frozen candidate and current service facts. If it does not pass, do not run or claim formal performance; trigger `formal-gate` when a new accuracy gate is required.
2. Verify that each target in scope has separate Prefill, Decode, and Mixed evidence plus cross-phase guards. Trace-level phase timing is not mandatory when low-overhead evidence is sufficient; unresolved attribution must remain explicit rather than being silently merged.
3. Select scope from the lifecycle: `intermediate-single-target` runs only `current_target_scenario_id`; `final-all-targets` runs the complete pre-frozen acceptance set. Use the same candidate graph configuration.
4. Collect comparable independent baseline, candidate, and revert runs with the contracted warmup and repetitions.
5. Use `compare_performance.py` with the comparison contract that was already bound during measurement.
6. Limit the conclusion to the contracted model, platform, Host/topology, service configuration, and scenario set. Long-term capacity requires a separate sustained-load contract when the current client does not implement it.

Before starting, record `formal_run_lifecycle=intermediate-single-target|final-all-targets`. Use `intermediate-single-target` when the current ordered target's milestone met a significant-improvement threshold, its bottleneck materially migrated, or it is ready for a close decision; require exactly that target scenario and store the result in `optimize/`. If it meets the pre-frozen scene-completion criteria, advance to the next target scenario. Use `final-all-targets` only after every target is complete; require the complete acceptance set and store the accepted result in `acceptance/`. Both lifecycles use the same accuracy-gate, identity, repetition, and baseline/candidate/revert requirements within their declared scope.

## Record and route artifacts

Write the Skill mode, scenarios, plan/contract SHA, service manifests, run-record paths, comparison result, result state, conclusion boundary, and next trigger into the current experiment record.

- Initial baseline summaries belong in `models/<model>/<platform>/baseline/`.
- Targeted, checkpoint, failed, reverted, and `formal_run_lifecycle=intermediate-single-target` rounds belong in `models/<model>/<platform>/optimize/`.
- Only the accepted combination's latest qualifying `formal_run_lifecycle=final-all-targets` result and rollback entry belong in `models/<model>/<platform>/acceptance/`.
- Large JSON, logs, responses, traces, and profiler outputs remain in the external or remote case directory; store absolute paths and required checksums locally.

Return a compact result containing: mode, scenario IDs, stage/parent-target mapping, prefill/decode/mixed evidence and cross-phase guards, service identity, plan/contract evidence, result state, primary/guard metric changes, invalid or omitted evidence, conclusion boundary, artifact paths, and the next performance-test trigger.
