# cleanup-003: narrow the DeepSeek MetaX patch to compiler tuning

User requested inspection/consolidation of patches/deepseek_v4_metax.py. Scope mx-103/deepseekV4-flash private editable /opt/vllm-plugin-fl, same main a696859b9, vLLM0.24 empty. No new performance optimization, kernel/dtype/layout/communication change or shared-source edit.

The 222-line module mixes model support checks, activation/dispatch configuration, and an Inductor RMS launch workaround. Reuse existing configs/deepseek_v4_metax.py for model-scoped configure_for_model and idempotent initialization. Platform and spawned Worker hooks remain at the same lifecycle points. The patch retains only _fingerprint and install_rms, with AST-identical behavior. Do not remove the actual Inductor workaround without a separate numerical/performance experiment; vLLM model registries cannot express generated-kernel launch configuration. Native compiler replacement is its future deletion condition.

Remove 12 eager imports and the duplicate early manager initialization/prewarm. Existing ModelRunner.load_model already prewarms all loaded CachedOps before compilation and capture; lazy OpManager initialization handles any earlier real dispatch. No changes to ModelRunner or dispatch core. This is substantive removal of duplicate lifecycle work, with no claim that relocating configuration deletes its function.

Before applying: private candidate, full source/index/patch backup, exact service identity and idle check; compare all35 actual dispatch bindings and enabled policy values against entry in inherited/clean processes, native registration/loading, CPU boundary tests, exact RMS AST, native prewarm behavior. Reload only exact task service if unchanged and idle; no container restart. Preserve startup script and currently observed prefix-cache setting. Reuse e2e/accuracy minimal-regression: C1x2, two C8 rounds, >10K nonaligned prefill x2; graph capture and >=2 actual replays. No formal score or performance claim; old formal gate remains historical. Other hardware/full CI untested; pr_readiness experimental.

Remote artifacts: /public-flash/jinghao/deepseekV4/20261022-thinking-gpqa-metax103/plugin-cleanup-20261027-04. Commands and SHA list are recorded before remote execution. Rollback restores only these four files after resolving/stopping exact service; later edits must be rejected.

Pre-execution SHA256:
- commands/minimal-regression.py `92e2f7d6450a5516ca62a77c772d1161b396e5024726a1f6a101e78b643e7fbe`
- commands/candidate-files-v2.json `9e616d4ce63e756d31fa73b6a232a5746d40cab9e9caa1b2a8109a4492c021d9`
- commands/remove.json `37517e5f3dc66819f61f5a7bb8ace1921282415f10551d2defa5c3eb0985b570`
- commands/probe.py `2555c31ca037e9a78ded56a7dd8128d448502dd6d69ce9f3656a06e0f60118ac`
- commands/apply-and-run.py `c22657f9faece3a3c38d2e2fdf41b09fd11adf2b34fcd416d950b148fa2b2a2f`
- commands/prepare.py `50bb2473113006fb2c464ad4cc64cf817d0b6506abd15aa4dfb11cf6da4c1f44`
- candidate/vllm_fl/platform.py `bab2c26d9dd81cef96050dd161b2ba68f86a3395b60017e7b704c320f61e5bc0`
- candidate/vllm_fl/patches/deepseek_v4_metax.py `1593a6060c46e46d2c60967a39e8478a8603e27aa725f7785485d79277fbc47e`
- candidate/vllm_fl/configs/deepseek_v4_metax.py `8eba4e6da82db49e37a803d8a39d5078331954dceda94cc058b587e1b378f1b9`
- candidate/vllm_fl/worker/worker.py `f51a7e96b0d2cb84d74d6b9d4e65c8498e5491104b7c9ac79845816c4e5becba`
- local stage.py `17e9c266765ea88e00b20c8f55766f21d6058eb28a87877a32eefcaf667496a9`

Preflight passed: baseline and inherited/clean candidate policies and35 bindings identical; existing prewarm resolves/freeze loaded ops; five retained CPU regressions passed.13 mock model-config positive/negative guards and exact RMS/config function AST passed. Skill bundle SHA1ed06a57f1f6e1ef39fb7fd872f579122b098a18f0255ade0a1160d6432c2b66. API939058/ticks1151169735 retained until guarded activation. Source patch222->127 lines, total net10 lines removed; remaining config logic moved without claiming deletion.
- commands/final-review.py `c316de5e9e0943f5f5ab5cd4f98e3d13cc3718806b64365f27213d64872f2549`
- static-checks.json `f7353f84a4952d3e9355beb8e08a67db75af5817a833fb56738cd1f9ac2942ca`
- skill-bundle.json `40605374230efd02ad9b4ba62f379c2b7038d5f9c00025d3c00de3194a34c538`
- local activate.py `52340075a234096803fb017161e7900a67f9ec42bb7efc117d6ce4f2777e8333`
- commands/rollback-source.py `3fcf76d6005f1bf7ef2a526eb43bdfb46aab1f716b73fe149c9be4f11612d163`
- commands/summary.py `c4312c6477384572c8a20c518724b8c1a8c68c81182348be3edbbc44718f0449`

## Retained result

The original patch mixed model activation/dispatch with compiler tuning. It now owns only `_fingerprint` and `install_rms`: **222 -> 127 lines**. Model activation/support checks remain at the same Platform/Worker lifecycle points through existing configs/deepseek_v4_metax.py. The12 eager module imports, early manager initialization and duplicate prewarm were removed; existing ModelRunner prewarm before compilation/capture suffices. Total source net reduction is **10 lines**, with33 changed paths unchanged; relocation is not counted as deleting functionality. No new patch file or environment activation.

Remaining RMS patch modifies Inductor CachingAutotuner.precompile/recheck_autotune_cache, restricted to three validated mathematical bodies of RMS4096. It preserves XBLOCK1/R0_BLOCK2048/stages1 and existing role/device warp choices and skips stale autotuning-cache selections. This is a compiler compatibility/tuning workaround, not a native model implementation. Removing it requires a separate compiler-selection/numerical/performance comparison; this task does not claim it is universally necessary or permanently unremovable. No generic vLLM model extension supplies an equivalent generated-Inductor-kernel launch choice.

Verification executed: baseline/inherited/clean candidate effective policy and35 impl_id bindings identical; existing prewarm freezes loaded supported CachedOps;13 config boundary checks; exact AST for RMS and configure_for_model;48 mock RMS role/rank/warm cases; five CPU behavior regressions; wheel build/package checks; fresh graph service capture sizes1/2/4/8/16/32/64;20/20 C1/C8/long-input requests passed. Native FULL replay counts shape1=15 and padded shape8 max6 (native exact8 row count2). No OOM/illegal memory/traceback in this run. No full GPQA/MATH500 or performance rerun, no new formal gate; other hardware/full CI not tested. pr_readiness experimental.

Container identity/image/mounts unchanged; source remains private /opt/vllm-plugin-fl. Native vLLM and FG/FGV not modified. Current API961222/startticks1151586767, start09:59:50UTC, ready10:04:21UTC. Prefix cache remains user current ON; startup script byte-identical. Cudagraph-metrics is the pre-existing validation-only flag, not a script change. AOT cache reuse was observed; this is not a cold-compile benchmark.

Summary: `/public-flash/jinghao/deepseekV4/20261022-thinking-gpqa-metax103/plugin-cleanup-20261027-04/summary.json`, SHA `574c2f7f61b244a1b5066f3b7abe15d49d8c42ffa065ce2c0487adb22691560c`.

result: `/public-flash/jinghao/deepseekV4/20261022-thinking-gpqa-metax103/plugin-cleanup-20261027-04/result.json`, SHA `6ba3336e97fb4d799ac8c0708a6800c3a5c1d3719d386a2ed59c0305cb7e439d`.

complete_review_patch: `/public-flash/jinghao/deepseekV4/20261022-thinking-gpqa-metax103/plugin-cleanup-20261027-04/complete-review.patch`, SHA `697230741f1a797d9fd57c099dbe1169111525b82c0f1e3ed4f01f32b8773a9c`.

backup: `/public-flash/jinghao/deepseekV4/20261022-thinking-gpqa-metax103/plugin-cleanup-20261027-04/before/plugin-source.tar.gz`, SHA `27ddbd74bb138359decc00057ea1d4330781e76b89c238231b511c81a4390426`.

Rollback: freshly resolve and stop exact task service, then commands/rollback-source.py restores only the four edited files from before/plugin-source.tar.gz and rejects later edits/live model workers. Relaunch preserved args; do not restart container. No git index entries altered, no commit/push.
