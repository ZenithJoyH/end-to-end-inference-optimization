# cleanup-002: production initialization and native weight-loader reuse

User authorized production consolidation in current mx-103/deepseekV4-flash, using PR #427 as a design reference, specifically challenging metax_deepseek JSON files. Target current private /opt/vllm-plugin-fl, HEAD a696859b9 on upgrade/20261020-main; not a rebase onto PR #427. PR observed head d15d7003, base a696859b9. vLLM0.24 source stays read-only; FG/FGV remain unchanged. This is a bounded configuration/initialization refactor, not a new performance optimization or kernel change.

Audit: the native model_cls extension is used by CausalLM; its existing load_weights already handles model/checkpoint traversal and expert mapping. Our load_weights merely delegates and has an audit decorator disabled by the current profile (_expected=None). Remove it, inheriting the native method. Do not replace MetaX attention constructors by constructing native CUDA attention then replacing it, or patch native globals to inject classes. Native constructors have no layer/attention factory extension and fused TileLang mHC is not a MetaX backend. Keep the MetaX KV ABI, mctlass INT8 experts, native P2P exchange, and validated decode/prefill/indexer math unchanged.

Two JSON files are redundant policy/launch snapshots: metax_deepseek_v4_compilation.json is unreferenced by production or the current inline launch script. metax_deepseek_v4.json duplicates existing immutable FrameworkPolicy, MoePolicy and KernelPolicy defaults plus platform YAML dispatch and compiler tuning. Remove both files; initialize existing typed defaults directly; use existing metax.yaml and the two required model-scoped overrides through the existing config loader/SelectionPolicy API. RMS4096 mathematical-body fingerprints and rank warp selection remain as local implementation tuning, without the external profile or case audit paths. This is not a wholesale JSON-to-Python profile copy.

Remove unused vendor-import blocker/checkpoint audit infrastructure and per-process binding audit/log files; preserve import order, native CachedOp prewarm/epoch handling, idempotent activation, and RMS tuning. Remove the redundant overwrite of native DeepseekV4ForCausalLM registration; the existing ModelRegistry alias DeepseekV4FLForCausalLM remains model-selected, preserving native stock registration. Keep the two genuine MoE tuning JSON tables: these are consumed by kernels and are not serving/activation profiles. Keep their package-data rule; remove dispatch JSON packaging.

Before installed source changes: full current source archive, patch/index, three-repo identity and live PID/startticks/args, exact inherited-config snapshot. Build private candidate and compare framework/kernel/MoE values, per-op policy, every actual impl_id, native alias and blacklists against baseline, then clean-environment probes and retained five CPU checks. If equal, install the source edits at the existing editable path. Validate fresh graph service under the current user launch arguments (prefix cache preserved as currently observed), fixed C1/C8 requests and two actual graph replays. Do not reuse the old formal gate for changed source/new instance; no new formal score or speedup claim. Minimal regression via local e2e/accuracy, explicit mode minimal-regression; no new formal performance planned.

Record pr_readiness experimental, other platform hardware/full repository CI untested. Source current-container edits are explicitly requested; existing private source used, no container restart or shared-source edit. Only the exact current task service may restart to activate code after candidate checks, with prior command and rollback preserved. No source edits until proof of equality.

Remote root: `/public-flash/jinghao/deepseekV4/20261022-thinking-gpqa-metax103/plugin-cleanup-20261027-02`. commands, backups, probes, logs and regression evidence remain remote.

Pre-execution checksums:
- commands/prepare.py `ee5b413619b16911e5e01314608c4cdb70d2582dde6c57ca11ec9b62e6cd55e7`
- commands/probe.py `b0cd0f6de64828741dceb394a6a220678c4af920bf5e6e1eacd9ff24b90f3481`
- commands/candidate-files.json `b3c1604a571a79e7e50cc8c0d2d215ce600cd10b0b1ded4e0cdb538821339bab`
- candidate/pyproject.toml `181d71cdac2ac2993a17a09b7696e9b0a7788e000192a958d1ee348a244c1dc9`
- candidate/tests/unit_tests/test_deepseek_v4_layer_boundaries.py `d1e03bf76296937c3f1990c4a6654ffad8b6194808535ca34b07601f3a12ba2f`
- candidate/vllm_fl/__init__.py `39ce2b3c098073c599dd0a0937ff6a7dc886fd95a257384b1b0b22d99fa813bd`
- candidate/vllm_fl/patches/deepseek_v4_metax.py `5b3aeefa3a546e6e8892ab981ef5a816efb93b224caf56e14c1172cdbcc66e41`
- candidate/vllm_fl/dispatch/config/utils.py `b37813d2e9a6c05282f41a2d89a891d4fe6448f5fabd6bc53a6d2bb1cf90924e`
- candidate/vllm_fl/models/deepseek_v4.py `44c3e64bff5104391034eea0e3894c00edb898ebab7f6f03b17ffd88b2b41912`
- local stage-prepare.py `a61bacae4eed404d967bcec8ca1884d01380f03ce4a64dba36675b68259e8c2f`

Initial preflight compared all 35 bindings and effective values successfully, then rejected an inaccurate verifier expectation: native ModelRegistry stores package vllm.models.deepseek_v4, not the nvidia.model leaf. Corrected by comparing actual baseline and native module prefix; no active source edits happened. Also audited all Plugin/FG/FGV/vLLM Python sources: the old paged_indexer_mqa_logits and its private kernel have no consumers; remove them while preserving the used match kernel and every remaining function AST exactly.
- candidate/vllm_fl/ops/deepseek_v4_indexer_decode.py `9730a4e681a9471c5a3294c64ed18552532bb63461163e63edfa65648b8a85fa`
- commands/candidate-files-v2.json `be501829e678e31d0a54fd6198eddaeb31edd4daa79c77ae4a902c34d4912d62`
- commands/resume-preflight.py `658484ed721e7a0c5e7fa95e3ae327b69ff48aecf9729958dd91ea8ec83ca225`

Private candidate preflight passed: 35 actual dispatch bindings, exact framework/kernel/MoE/blacklist values equal, inherited and clean activation environments, native weight-loader inheritance and preserved native stock registration, five retained CPU regressions. Next bounded activation: build wheel before stopping; verify idle service/exact process; preserve original environment only in memory; SIGTERM only exact API and wait for its associated tree; apply scoped edits; relaunch original args/cwd with native cudagraph-metrics diagnostic only (not added to user script); fresh graph capture and C1/C8/long-prefill minimal regression. No full score reuse or performance comparison.
- commands/apply-and-run.py `d2576aa8add88a8261ce397580f50b45920e57b6938f8a1f83ff80945a202d54`
- commands/minimal-regression.py `8dade1b0a1aaa82675c4e2c86639a7061343a525adf97cf0d456b3529c8b57c4`
- local stage-activate.py `721fd320f3e55a4cede31ee02a0558611859690d80570eeef9cea05fe5ef696f`
- commands/final-review.py `0555ad7c548818ba7a9578353819d54b8a0cf7cf851b0b6c05fe2bd8d0e7e017` (final review is read-only apart from case evidence; rollback refuses live workers and later edits).
- commands/rollback-source.py `93ee15e34168145fe790345082a3e0269564d70fcc938e14a1d5aaad8b696484` (final review is read-only apart from case evidence; rollback refuses live workers and later edits).

## Final consolidation: cleanup-003 follow-on

The v2 source passed fresh graph service/C1/C8/long-prefill requests. Final code audit found remaining Plugin-only historical logging: _TOPK_FIX_STATE and _log_topk_fix include GPU ks min/max -> CPU sync, plus a disabled prefill_native_topk experiment (explicitly false in both original JSON and typed defaults) and an external tree_topk import fallback. Remove those diagnostic-only statements, the disabled trial module/flag and external fallback; use the existing local decode_topk_tree directly. All active top-k selection/scoring math remains unchanged. The disabled flag is the only intentionally removed configuration key; it is not a changed choice. This is a low-risk cleanup, not a new numerical backend.

Final subcase /public-flash/jinghao/deepseekV4/20261022-thinking-gpqa-metax103/plugin-cleanup-20261027-03 holds independent source archive/instance/probes/regression; v2 artifacts remain immutable. Recheck all35 bindings and enabled effective values before a second targeted service reload. No new full accuracy/performance claim.
- final commands/final-review.py `0e6b7017a6ad0b2d4420240f0064c265cd3a92fb3f07daaf9483ef161d40afe2`
- final commands/minimal-regression.py `5df0a07a4b45d9360762d6df98a55aab57090421e5b6cf9707a0037651a56202`
- final commands/candidate-files-v2.json `377135622892691648c9fa9b4c812a46c48be79c1bd828b84c6da4604a62dd12`
- final commands/remove.json `b67bcb44fcc8fbf084b4d54295a69ca8be225ffddab061b66ef1adecfdfe5cca`
- final commands/probe.py `c9946ab3d6479135da0f9e2c64cd00c9a033abc56e880f663b46c7664c460759`
- final commands/apply-and-run.py `69b93cc911ac74077a277eb00edeee2299b6dfe163ce6eacae4775ff74b75c0d`
- final commands/prepare.py `db8bafe29bbb90fea606d586b27ee294849d9ca18dd92f904225eafab4b46c7f`
- final commands/rollback-source.py `20104352592a30c24e41351cd37a9b7e4e783c130a0814dca70089f1eabaab6d`
- final candidate/vllm_fl/dsv4_config.py `7b4548764bb051efd4055f45b1d2f4f61bcd89369aea215f61ffc13f5f71f6de`
- final candidate/vllm_fl/ops/sparse_attn_indexer.py `aa5a421f36b4572f7e7b234f584e333ec24b9290601fc4ba66f2dc5ce39354f8`
- final stage.py `3f4ab0740c0dddf96c4fb0a93af7c92c41b072a8ee4018ecf04fc3605f490245`
- final commands/topk-equivalence.py `35e96c733f15df506918ef43ddb965b4653d194544caa04e6b9a82f7b3188d82`; compare actual CPU fill/merge outputs before/after logging removal, with identical stub kernel, not hardware-kernel evidence.
- final commands/cleanup-index.py `201006db067dfabd631e0daa05c35b3a8636950988884093c7ac95c2b042629e`; remove only the deleted trial module intent-to-add entry after proving no HEAD/staged content. All other index entries preserved. Rollback re-adds the restored file with git add -N.
- final commands/summarize.py `47ca9dfa534889ad3a615ac5a568c3a20babdbc66046d86733e389e0cb62b647`; aggregate original-to-final scope, include untracked resources in complete review patch and verify healthy same-instance service. Raw final result old_profile_json_removed is a generic removed-path field reused for the trial module; summary uses separate correct names for model JSON and trial removal.

## Final retained result

2026-10-27, final current container service verified healthy/idle. Full status inventory **36 -> 33 changed files**, including the three untracked package/real-MoE-resource files; **776 net lines removed** from this task's entry source. Remaining production Python changes: 29. Final tracked diff: 30 files, 7545 insertions / 8 deletions. No rebase/cherry-pick/commit/push.

Removed both metax_deepseek_v4 JSON files; current activation uses existing typed Python defaults and standard platform dispatch YAML with only two scoped required choices. No activation environment/path or new user launch flags. The two actual MoE tuning tables remain: they are operator parameter data, not model startup profiles. Current script is unchanged, including the user's prefix-cache ON setting. Validation uses the native cudagraph-metrics flag only in the verification service; this flag was not added to the user script.

Native CausalLM weight loading is directly inherited; the stock native registration is no longer overwritten. Removed dead checkpoint-audit/dependency guard/legacy profile infrastructure, the unused old indexer launcher/kernel, the disabled native-prefill-topk trial module/flag, historical warning/counter plumbing and its GPU->CPU ks probes, and the external tree_topk path fallback. Kept the actual indexer/tree-topk/MetaX packed KV/mHC/MCTlass and native-P2P math/optimizations. No new implementation is substituted merely to reduce file count.

### Remaining adapter rationale

| Group | Native reuse and required remainder |
|---|---|
| Model / checkpoint | Native model_cls hook, native loading/expert mapping and native MoE classes; narrow MetaX constructors and mHC calls remain because vLLM0.24 has no attention/layer factory there and its CUDA TileLang fused mHC path is not this backend. No global native-class mutation or construct-and-replace duplicate attention. |
| Attention / indexer | Native FlashMLA forward splitting, metadata/cache classes and common compressor state retained; local packed FP8 KV address/layout, graph-safe indexer and TP query/head sharding remain required for the current MetaX path. |
| W8A8 / vendor | Native compressed-tensors/modular-MoE workspaces/activation/reduction with MCTlass numerical kernels and the two real tuning tables; empty vLLM has no usable CUDA vendor GEMM implementation here. |
| Initialization / policy | Native platform/worker/model-registry entry points and existing SelectionPolicy/CachedOp prewarm; immutable defaults and scoped RMS4096 compile tuning. No model-specific serving/activation JSON. |

Validation: all **35 actual impl_id bindings** and enabled policies equal to the entry configuration, both inherited and clean activation environments. Five retained CPU regressions passed. Forty-eight mock RMS role/rank/warm configuration comparisons passed; 12 actual CPU short-row fill/merge comparisons passed with the same deterministic kernel callback (these do not claim GPU-kernel performance). Final graph service loaded all62 shards through native weight loading and captured sizes1/2/4/8/16/32/64. **20/20 requests passed**: C1x2, two C8 rounds, two10417-token long-prefill fixed-answer cases. Native vLLM graph table proves shape1 FULL count14 and padded-shape8 FULL count8. No OOM/illegal memory/traceback observed in this validation. Intermediate v2 also passed its independent20-request regression and remains archived.

Final summary: `/public-flash/jinghao/deepseekV4/20261022-thinking-gpqa-metax103/plugin-cleanup-20261027-03/summary.json`, SHA `2caea53e00c155c366561a6a7655d5d0f6ae63e68457a698af77bea3cd59ac45`. Final minimal result SHA `366614fa8919e8ce5f51aae5c2eabc26e7213d3c6e9ff8c4ed5aa325c2d7b0d4`; intermediate v2 result SHA `ad623fbf47b5a9e0507fae325a09182c40e62610917ea1f2fd1cb91006cdb3e7`.

Complete diff includes untracked source/resources: `/public-flash/jinghao/deepseekV4/20261022-thinking-gpqa-metax103/plugin-cleanup-20261027-03/complete-review.patch`, SHA `2facf7ee4abc5e3f4826846f3a581a7da17da84b3c0db7fc5e45c30c5c260f12`. All originals and before/index/patch evidence remain external. Native graph counter rows and original request/response artifacts remain in final case. The version-specific optional FlagTune/xgboost fallback observed at startup is unchanged from the existing environment; no dependency changes were made or unrelated fixes added.

Rollback: stop only the freshly re-resolved current task service (never the container), run final-case commands/rollback-source.py, restore the trial file's prior intent-to-add metadata with git add -N for that exact path, then run cleanup02 commands/rollback-source.py to restore the task-entry source and both original JSON files. Both restore scripts refuse live model workers and later source edits. Restart from cleanup02/before/runtime.json arguments/environment guidance. The original user script remains untouched.

**No new full GPQA/MATH500 or end-to-end performance measurement was run.** Prior scores belong to the old source/instance and are not rebound to this refactor. Obtain a new formal gate before formal performance. Other-platform hardware and full repository CI remain untested; pr_readiness=experimental. Model service is left running under a waiting supervisor that reaps its API when stopped.
