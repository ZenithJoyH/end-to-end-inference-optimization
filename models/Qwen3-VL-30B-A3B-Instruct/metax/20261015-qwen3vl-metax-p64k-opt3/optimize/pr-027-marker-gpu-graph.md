# pr027: CI marker repair and independent GPU/graph validation for PR943

User requests fixing the marker failure, validating GPU correctness and graph in an independent container, then marking PR943 ready only after passing. Preserve other runtime configurations. On2026-10-19 user explicitly authorized stopping current8111 (qwen3vl-opt9) to free GPU0/1 and restoring it with its original configuration after validation.

## Frozen scope

| Item | Contract |
|---|---|
| PR | flagos-ai/FlagGems-vllm943; head808cedfc36589430fbd97fcd483bfbf0f4eff74b, base b4d3382bb04da4e0ab444849697865b4d5fcd86e |
| Runtime source | qwen3vl-p64k-opt-20261015 on mx-59, GPU0/1,8111; user restart produced opt9; original source qwen3vl-flaggems-e2e-20261013 protected |
| Editable | Isolated publication copy: marker decorators on existing fused MoE tests only; validation container's private PR operator file |
| Read-only | Live source/index/HEAD; Plugin, gems-opt, sampling, vLLM, weights/tokenizer, other services and devices |
| Container | New dedicated verification container from immutable pause=false snapshot of actual source; exact same directory mounts, runtime settings; separate private caches/logs |
| Validation | e2e/accuracy minimal-regression; exact PR MoE path, BF16/FP16, representative tuned M boundaries, fallback dtypes/shapes, numerical reference and changed-input graph capture with>=2replays; zero/odd shapes and routing/inplace cases |
| Numerical contract | Preserve existing reference tolerances; freeze exact matrix/tolerances in saved validation script before execution; FP32 reference only in test code |
| Graph/service | Standalone public operator graphs plus graph service smoke/C8 if permitted resources and source service configuration fit; record any incomplete scope explicitly |
| Benchmark/formal accuracy | No new performance claim, GPQA remains deferred by user |
| Publication | Normal expected-head non-force update; may integrate current upstream baseline in publication history to edit its existing test without add/add conflicts; no runtime upgrade |
| Ready gate | Marker CI passes and exact submitted MoE GPU numerical/graph validation passes; no silent reuse of historical graph gate |

All8GPUs were occupied; only current8111/GPU0,1 may be stopped after saving actual argv/runtime environment whitelist/process start identity. Other services remain untouched. Restore is required even if validation fails. Scripts/configs must be saved under existing remote case commands/pr027-marker-gpu-graph-20261019 before execution, with hashes recorded here/state.yml. No new operator test/perf files will be introduced; external regression controls remain remote.

Use local accuracy skill bundle with mode minimal-regression. Operator-level result does not imply formal model accuracy or end-to-end performance acceptance. Resource, lineage/mount, deployment and restore receipts remain native external artifacts.

## Preparation receipts

Captured actual opt9 API argv, whitelisted runtime environment, stdout/cwd, descendant PID/start identities and source repositories in source-recovery.json before any stop. Same source API and source fingerprints were checked again when making the immutable snapshot with pause=false. Docker emits a deprecation notice on stdout; first container creation failed by treating that notice as part of the image ID. No container was created and the source service was unaffected. Corrected control_v2.py reuses the actual generated snapshot ID, verifies its parent, and completes lineage/mount/content checks. Snapshot image and full sanitized target inspect are in lineage-mount-gate.json; image_lineage=verified,mount_parity=passed, SHA256 a43aba9704a7ebc6305a7bf98cb766ada81ccd77be5dbd2d04783026eb943eae. Two original binds and host IPC/network/devices/resources are unchanged.

Marker-only change adds decorators to all5existing functions; AST bodies unchanged and upstream checker passes. Exact PR MoE byte hash is bc655dbc521538710b054c2af8f496ed45d0d214f0d71e9ea3fdf8731aa7605b. Publication will integrate the current upstream parent only in GitHub history to amend its already-existing test; it does not upgrade the runtime. Controls/validation/publication plan are archived before execution with hashes in state.yml.

GPU contract freezes40tuned BF16/FP16 cases M0..8193 including nearest-row boundaries; mathematical reference at M1/64/4096/8192 and selected changed graph inputs. Historical tolerances retained: BF16 atol.004/rtol.016, FP16 atol.0005/rtol.003. Three fallback dtypes including FP32 are covered on E4/H128/I64 with M1/17/4096; FP32 atol.0001/rtol.001.18target captures plus3fallback captures each replay twice with changed activations, routing IDs and weights; compare against fresh execution and selected independent FP32 math. No new benchmark, no relaxed threshold. Tests remain external case artifacts.

## GPU operator validation completed

Exact submitted MetaX operator byte hash bc655dbc521538710b054c2af8f496ed45d0d214f0d71e9ea3fdf8731aa7605b passed49GPU cases and31FP32 mathematical reference checks on C550 / torch2.8.0+metax3.7.0.7 / FlagTree3.6.0, actual shared memory65536bytes.21captures/42replays update input tensors, expert IDs and router weights, with no host dispatch during replay. E128/H2048/I384 covers BF16/FP16 M0..8193 and in-place output; nonmatching E4/H128/I64 covers BF16/FP16/FP32, zero/odd rows and original noncontiguous-input assertion. No tolerances were changed. Native results/pr027-gpu-numerics.json and logs/pr027-gpu-validation.log retain full per-case/config/error proof.

Published marker commit29c250c4805d6599bf4c7f62561914bae7afbe71 normally integrates upstream b4d3382 in the publication branch. Final PR diff is the original MoE file plus5marker decorator lines in existing tests/test_fused_moe.py, with no test body change or new test/perf files. Upstream rule-check now succeeds; no CI policy was weakened. Services remain on their original source revisions. Dedicated TP2 service on18143 is now validating worker-level graph/matching stage evidence. Source8111 restore remains mandatory.

## Runtime restoration completed; review steering

Dedicated TP2 graph service passed11HTTP requests including C8, both workers captured graphs and replayed>=16times, and actualM64G1stage3/G2stage1 matched expected configs. Service receipt results/pr027-service-graph.json SHA25672bcd1a962a051f7fd0f47d5a6dcaa91ea5181e203d1aeeb8838a87b8652112d. Dedicated service was stopped and releasedGPU0/1; no other services/devices were operated on. Source8111 was restarted from exact source-recovery argv/runtime environment/cwd/log. All four source repository states and critical hashes match, readiness reports opt9 and smoke returned42. Native results/pr027-source-restored.json SHA256872bcfc0ed5a41e8f47d7bdfaecf5a7e6aa6d9da6852ad315606ec9d845b922d. No source code/config update occurred.

At29c250c, all applicable upstream CI jobs passed (rule, formatting, target selection, both MetaX variants and summary; NVIDIA skipped). Before ready transition, the user explicitly asked for marker/design review. review028 reduced the redundant5decorators to1compatibility decorator and reproduced broader tuning/OCP key and shared-memory-estimation concerns. Source MoE bytes are unchanged. PR remains Draft/needs_revision while those findings are resolved; the previously requested ready transition is not claimed complete. GPU/graph/operator-level regression passed, full model accuracy/performance acceptance remains outside this request.
