---
name: key-operator-opt
description: Optimize hotspot ATen and vLLM fused operators using platform-specific case evidence. Use for operator dispatch, layout, fusion, communication-compute fusion/overlap or kernel investigations, and to distill completed experiments into reusable guidance. Evaluate fusion/overlap when dependency and resource evidence supports it, rather than loading every reference for every operator.
---

# Key Operator Optimization

Use this skill to turn an end-to-end bottleneck into a bounded operator investigation and a verifiable optimization decision, then make the next investigation of the same operator faster and deeper.

## Entry condition

Before deep operator work, identify evidence that the operator or its surrounding dispatch, layout, synchronization, or communication path materially affects the target end-to-end metric. A high theoretical FLOP count alone is not sufficient.

Screen and rank the operator against framework alternatives with [SOP C2](../../docs/performance-optimization-sop.md#c2-生成并维护实际候选排名) and the [shared net-benefit method](../inference-roofline-analysis/references/roofline.md#热点筛选与净收益排序). Carry the caller's hotspot shortlist, objective-specific critical-path/contending-resource evidence and actual shape coverage. Estimate full-call net benefit with overhead and overlap boundaries; a large kernel duration or low roof efficiency alone does not justify deep tuning. If the mechanism is weakly supported, propose a cheap falsification experiment before implementation, returning the result to the original coordinator rather than opening another analysis loop.

Before routing a networking/framework bottleneck away, perform the lightweight C3.1 mechanism check below: a communication-compute fusion may need an operator investigation, while stream/chunk/copy scheduling can reuse only the shared fusion/overlap reference. Return pure framework orchestration to the coordinator for its framework task; do not force a numerical-kernel implementation or preload unrelated operator knowledge.

## Shared method

Read [operator-analysis-method.md](references/operator-analysis-method.md) when beginning a new operator analysis or designing its correctness and performance experiments. Apply the relevant parts rather than recreating a separate generic workflow.

Keep Prefill and Decode separate. Distinguish algorithm, framework/dispatch, Kernel, communication, and hardware effects. Record model shapes, dtype, layout, execution mode, hardware, framework revision, warmup, timing method, and correctness oracle.

For compute/bandwidth attribution and headroom, automatically apply the [SOP C5 trigger and handoff rules](../../docs/performance-optimization-sop.md#c5-用-roofline-连接瓶颈证据与下一步实验). First reuse the caller's valid [$inference-roofline-analysis](../inference-roofline-analysis/SKILL.md) result or matching active task; request a bounded new analysis through the coordinator only when the question or inputs require it. Return its candidate choice, expected removable cost and falsification experiment to the original decision point, without calling Roofline again on unchanged inputs. Carry phase/rank/shape-bound measured or explicitly estimated FLOPs, HBM traffic, timing and matching ceilings into the operator hypothesis. Compare existing providers before deep tuning when appropriate; target removable traffic/computation or execution inefficiency rather than a utilization percentage, and verify complete-call cost during local screening. Verify no-profiler Mixed impact at service-integration promotion, not after every operator trial.

If analysis requires additional counters, return the precise gap to the coordinator for deduplication and scoped Profiling collection. Reuse the existing timeline and native reports, wait for a matching in-flight request, and preserve known unsupported/failed gaps until reopening conditions change. Do not start a separate profiler/benchmark chain merely because this operator task was entered from Roofline; numerical tests and full-call/E2E measurements remain separately assigned work under the existing validation contract.

When current evidence suggests exposed communication/copy, producer-consumer barriers, chunk/microbatch readiness or kernel-internal memory waits, automatically assess the [SOP C3.1 fusion/overlap candidates](../../docs/performance-optimization-sop.md#c31-通算融合与-overlap-候选). For communication/rank waits that could reflect late arrival, distinguish that explanation using existing evidence; unrelated or already resolved branches need no new CPU/rank diagnosis. Read only the applicable branch of [comm-compute-fusion-overlap.md](references/comm-compute-fusion-overlap.md). Distinguish framework scheduling, existing-provider replacement and new fused/pipelined kernel work; verify actual platform primitives and complete producer→communication/synchronization→consumer cost before recommending a candidate. This is an optional mechanism-based route, not a new profiling or whole-model validation cycle per trial.

## Local screening and service promotion

Apply [SOP D0](../../docs/performance-optimization-sop.md#d0-并行探索局部筛选与批次集成) with a validation scope proportional to the decision. “Local” here means isolated operator validation on the target device/environment, not this project's control-tool unit tests. It does not add an operator-only mode to the model accuracy or performance runners.

| Scope | Required evidence and conclusion |
|---|---|
| Individual operator trial | Start with an independent reference/numerical oracle on small representative real shapes and affected contract surfaces, plus a fair complete-call benchmark including conversions/merge/copy. Record actual test scope and source/binary/cache identity; reuse still-valid unaffected checks instead of rerunning a complete matrix for every tile. Failed numerical tests reject/repair that candidate; absent target hardware stays untested. A quick partial pass is not yet a locally validated candidate |
| Locally selected candidate | Before declaring local validation passed, cover applicable real per-rank shapes/dtypes/layouts, boundaries/non-alignment/empty cases, affected fallback/dispatch, complete-call gains/regressions and graph capture plus at least two changed-input replays. Reuse checks only where source/contract/compiler/shape/graph bindings remain valid. Record existing `pending` with “local validation passed; whole-model validation pending”, exclude it from the current combined candidate and integrated low-risk count. Do not start/restart a full model or run model regression, Mixed, GPQA or profiling for each tile/warp/stage trial |
| Bounded service integration batch | Select winners and compatible complementary candidates; apply D0 branch-return/parent-identity checks before assembling the isolated integration candidate, reusing unaffected local evidence and rechecking only invalidated scope, then create the candidate service for validation. Satisfy model smoke/minimal regression and representative no-profiler service-performance coverage under D0/D7. Reuse valid or in-flight covering results in their original mode/purpose; assign only uncovered scope in the smallest required mode, without a mandatory targeted→checkpoint→formal sequence. A batch containing algorithm/backend/fusion/numerical or other existing high-risk changes immediately receives the original full-accuracy validation at this integration milestone, before further unvalidated stacking. It need not first run a full model for every isolated member |
| Mainline retention and final acceptance | Promote only after the applicable service checks pass. Keep model/full-accuracy scope and gate identity explicit; final formal accuracy and all-target performance remain unchanged. Combined failure triggers dependency-aware rollback/bisection, not repeated successful local tests; individual end-to-end contribution remains unknown without needed ablation, which is not mandatory for every member |

The coordinator may dispatch several useful independent operator/system branches when resources permit, retaining one variable per experiment. Give each branch private source/import paths, compiler/build and tuning caches, random/test state, device/CPU/memory/NIC/disk scope, and any service instance/port it actually needs. Do not mutate shared install/cache/source state or overlap contested measurements/shared-service lifecycle operations; isolate interference or serialize them. Preserve mount parity and existing authorization, do not add Host scope or duplicate an in-flight gap.

Freeze each branch's time/count/risk budget and the pending-candidate inventory/integration trigger in the current optimization-point/planning record. Integrate, reject or defer on local winners, complementary readiness, inventory/budget limit, changed hotspot or the planned milestone; do not grow an unlimited unvalidated queue. Keep raw trial details external under the existing point. Local speedups support screening only, and never add into an asserted combined end-to-end speedup.

## Knowledge routing

Match the target platform and operator using [knowledge-index.md](references/knowledge-index.md). For MetaX, the [platform guide](references/platforms/metax.md) connects a measured symptom to a first experiment, its counterexamples and the original evidence. If summarizing past cases, start from their experiment records. A new service run is only needed to establish a new runtime or performance claim.

Before implementing a model-specific fast path or fusion, query relevant upstream history using [upstream-pr-history.md](references/upstream-pr-history.md) when it could avoid duplicate work or expose regression risks. Read only the matching cards and current callers. Keep PR metadata verification, diff review and target-platform reproduction distinct; a merged PR or a refreshed index does not prove the running backend uses it. Return the useful sources and their effect on the candidate decision to the existing experiment record.

For an existing provider, compare the complete operator through its public entry point (`operator/replace`). For a kernel or fusion change (`operator/improve`), isolate the proposed mechanism against the current implementation. Use the effective per-rank shapes and graph replay frequencies from the target stage to choose the comparison. If the emitted code points to a compiler change, compare the same kernel under the original, patched and restored private FlagTree builds. Check loaded binaries, isolate compiled caches, and cover other kernels that reach the changed rule. See the [compiler experiment in SOP C4](../../docs/performance-optimization-sop.md#修改优化容器内的-flagtree).

- For an operator with prior cases, read its stable `README.md`, then its `optimization-map.md`, then only the matching cards in `case-index.md`. This order gives the current mental model, actionable decisions, and supporting evidence without loading full historical cases.
- For MLA, latent KV cache, absorbed/unabsorbed execution, sparse MLA/DSA, or MLA backend selection, follow the MLA routes in the index. Read source snapshots only for the specific call chain being investigated.
- For mHC, multi-stream residual mixing, Sinkhorn normalization, or fused post+pre paths, read the mHC report.
- For a new operator, use the shared method. Keep the first full investigation in the actual case; create or extend the operator knowledge directory only when reusable facts or artifacts exist.

## Case-driven learning loop

Do not append complete case reports to an operator's stable `README.md`. Keep `docs/cases/<case>/` to readable summaries linking to the authoritative active case: resolve its existing record, normally `models/<model>/<platform>/<case-id>/`, while preserving a legacy active layout without migration. Within that case use `baseline/` for original measurements, `optimize/state.yml` for the ledger, `optimize/README.md` for the overview, one `optimize/<experiment-id>.md` per optimization point, and `acceptance/` for final status. Raw commands, patches, logs, traces and other large artifacts remain external; record their locations and checksums.

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

Historical cases accelerate hypothesis selection; they never replace current dispatch proof and operator correctness. Same-condition end-to-end validation is required for service promotion and acceptance, not each isolated local trial. Keep observation, reproduced, transferred, and invariant evidence visibly distinct. When a later case conflicts with the map, preserve both cards, narrow the old scope, and mark the disputed rule instead of silently overwriting history.

## Optimization output

Produce the smallest useful artifact for the task. It should normally include:

- operator role, inputs/outputs, shapes, dtype, layout, and Prefill/Decode behavior;
- source-to-Kernel call chain and actual dispatch evidence;
- FLOPs, memory traffic, arithmetic intensity, temporary memory, and likely bottleneck;
- baseline correctness oracle and benchmark matrix;
- available diagnostic evidence (trace/report, runtime/source/shape facts or bounded assumptions), its target connection and gaps; no new profiler run is required just to fill this output;
- candidate optimization, applicability, costs, risks, fallback, and graph constraints;
- fair baseline/candidate results, error metrics, regressions, and scope of the conclusion.

Preserve a reference path during implementation. Apply the local-screening table above: quick trials use scoped representative checks; selected candidates complete affected boundaries/fallback and applicable graph capture plus two changed-input replays before local-pass claims. Reuse binding-valid checks and distinguish local graph proof from service-integration proof. A separate eager service remains optional diagnostic evidence, not a gate.
