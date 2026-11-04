# env-007: Update Plugin release/0.2

User requests updating Plugin in the retained B container. Continue the previously specified and currently checked-out release/0.2 branch. Old HEAD7cb559947cb61fd8b69fa5027d8ec113e528a644; latest upstream verified on2026-10-27 is1bc0c775ffbdf4a0b0e2efb5e847d586e902273f.

Scope: private /workspace/vllm-plugin-FL, existing editable installation. Preserve PR638 attention code and existing metax.yaml changes. Back up both modified files, binary patch, tracked hashes, four source identities and service before fetching/reviewing upstream. Three-way merge each dirty file in staged tree; conflicts prevent live tree changes. Review syntax and reuse prior CPU attention tests before applying a fast-forward and the reviewed merged files. No source changes to vLLM/Gems, dependency upgrades, model requests or service restart; performance remains paused.

This is environment maintenance, not new operator design. Existing PR638 remains in the MetaX backend. Review upstream APIs/dependencies before apply. Prior precision gates do not validate the new source; hardware graph/accuracy/performance remain not_run.

Command saved before execution: `/public-flash/jinghao/qwen3.6-27B/20261022-qwen36-27b-mx104-plugin-regression/commands/env007-update-plugin-20261027.py`, SHA256 `665c8374b40d2d12eaa5e8922c79f1878297162cbc7d34c45a35ea7882ccc3a4`; syntax passed. Prepare only backs up/fetches/stages a plan. Apply requires the reviewed plan SHA.

Evidence root: /public-flash/jinghao/qwen3.6-27B/20261022-qwen36-27b-mx104-plugin-regression/manifests/env007-plugin-update-20261027. Status: completed.

## Prepared plan review

Plan SHA256 `26d84f0a59d458867fc87493067f3f368aca8b7ebb7c8991e7651c800046030c`. Upstream contains exactly one new commit: PR638, +29/-4 in MetaX flash_attn.py. Its upstream bytes equal current bytes SHA f49f4a5b401a5ca66f04f10b27e7b6f186e3efe1c8d214556efb0b1edaf36514. The merged metax.yaml remains exactly current SHA13592c2b2d31064748aaae0e5cf259c9dc14313242c0eea84e585465e1ab89a1. No dependency, entry point or framework changes. Staged300 Python files parsed.

Reuse command `/public-flash/jinghao/qwen3.6-27B/20261022-qwen36-27b-mx104-plugin-regression/commands/env007-reuse-cpu-tests-20261027.py` SHA256 `58a23d810431ff793b4048b47f3e217a5cd7401ff619d5a419e50539a4e40fd2`: same prior8 CPU/mock routing tests and28 differential cases, only ROOT/output paths changed, original frozen harness hash still checked. GPU hidden, OMP1, no model requests.

After tests pass execute env007-update-plugin with `--apply-plan-sha256 26d84f0a59d458867fc87493067f3f368aca8b7ebb7c8991e7651c800046030c`; no dependency installation or service control.

Source fast-forward complete: apply-receipt SHA814eba72b603e03740dd8f1ac9f1005db102b773efe781ffbf23d041293aca1d; only remaining tracked diff is metax.yaml. All4 package source hashes identical before/after (same custom SHA algorithm for both).8 CPU tests and28 differential cases passed. Service identity andhealth200 unchanged.

Refresh editable package revision metadata so pip/version diagnostics also report new HEAD. Command `/public-flash/jinghao/qwen3.6-27B/20261022-qwen36-27b-mx104-plugin-regression/commands/env007-refresh-editable-20261027.py` SHA256 `99d413a924e79e4a2fd1b5a3a76631290d6eec39adcb27aeea9009459d63cced`, syntax passed. Uses pip install --no-deps --no-build-isolation -e with PIP_NO_INDEX=1, no vendor build and all GPUs hidden. Backs up installed Plugin metadata/editable loaders/generated version file first; verifies all other package versions and tracked bytes unchanged, fresh isolated import/entrypoints/editable path/new revision and service unchanged. Only generated untracked _version.py may change. No service reload or model request.

## Service exit observed before metadata refresh

Source apply completed04:23:29Z with currentAPI/Engine/workers unchanged andhealth200. Before metadata refresh, health connection refused; original metadata controller stopped at service precheck before pip, no install log or before snapshot exists. Fresh docker top has only7 shell processes, no model process. service-new.log reports12:24:18 CST EngineDeadError fromAsyncLLM followed by API shutdown. Rootcause unknown; no service signal/restart/inference sent by update commands. Actual attention and all other source bytes were unchanged across source fast-forward; do not assert a cause from timing.

Continue only the already authorized editable metadata update with a new exact snapshot of current empty service/connection-refused state, keep it unchanged rather than requiring a now-nonexistent service. All source/package/version safeguards remain. New command `/public-flash/jinghao/qwen3.6-27B/20261022-qwen36-27b-mx104-plugin-regression/commands/env007-refresh-editable-v2-20261027.py` SHA256 `b6ec3cb93f67aaeefcb7f0c9d3c63230f5f4ba6636f9065270e9b76f054f2bca`, syntax checked. Distinct backup directory/log retains first precheck failure evidence; no retry of model work.

Editable package successfully installed with no-index/no-deps/no-build-isolation:0.2.2rc2.post1+g1bc0c775f.d20261027. Subsequent isolated import with ALL GPUs hidden failed in preexisting FlagGems/Triton driver initialization (0 active drivers); no model request or service action. Keep logs; do not rerun pip. Final verification uses normal import with target physicalGPU2,3 visible, FLAGGEMS_VENDORmetax, USE_FLAGTUNE0, threads1; only imports and identity checks, no model/tensor/kernel benchmark. Command `/public-flash/jinghao/qwen3.6-27B/20261022-qwen36-27b-mx104-plugin-regression/commands/env007-verify-final-20261027.py` SHA256 `a2a2cb41fe65ff5494f950be9ce0d067de5ae7b25b40c28cb3b5217ff5fea7df`, syntax checked. Verify all tracked bytes/other package versions/config/entrypoints and version identity, retain exact current service observation.

Validation environment correction: direct docker exec omits login-shell MACA_PATH; visibleGPU import failed before any final receipt in Triton hdrmaca_dirs becauseMACA_PATH None. Read-only bash-lc inspection confirms MACA_PATH=/opt/maca, MACA_HOME=/opt/maca, vendor libraries from login environment; user startup script likewise assumes this shell initialization. Run the same SHA-frozen final-verifier via docker exec B bash -lc with only process-local FLAGGEMS_VENDOR=metax USE_FLAGTUNE=0 CUDA_VISIBLE_DEVICES=2,3 MACA_VISIBLE_DEVICES=2,3 OMP_NUM_THREADS=1 and /opt/conda/bin/python -I. No production env/source changes, no reinstall, no model launch. Retain failed checks; prior script-only import outcome must not be called pass.

## Final result

Plugin updated in B at /workspace/vllm-plugin-FL to release/0.2 HEAD1bc0c775ffbdf4a0b0e2efb5e847d586e902273f. Editable version0.2.2rc2.post1+g1bc0c775f.d20261027; real import resolves private checkout and generated git_version1bc0c775f, original two plugin entrypoints unchanged. Latest commit is PR638, whose effective attention bytes were already installed; attention code unchanged and now tracked clean. Only metax.yaml remains dirty, originalSHA13592c2b2d31064748aaae0e5cf259c9dc14313242c0eea84e585465e1ab89a1 fully preserved. All tracked source bytes equal reviewed staged tree;249 other installed package versions unchanged. No vLLM/Gems/model/script changes, no commit/push.

Validation:8 reused CPU/mock routing methods and28 FP16/BF16 differential cases passed;300 upstream Python files plus generated _version.py parsed; git diff --check passed; fresh isolated import PASSED in actual login-shell MACA environment with physicalGPU2,3 visible. Hidden-GPU and direct-exec missing-MACA_PATH failed checks retained as environment evidence; neither altered code or caused reinstall retries. No device numerical/graph/model accuracy or performance requests. Prior accuracy scores163/198 and239/400 remain historical run artifacts; no new score or new gate claimed.

Final verification /public-flash/jinghao/qwen3.6-27B/20261022-qwen36-27b-mx104-plugin-regression/manifests/env007-plugin-update-20261027/final-verification.json SHA256 `6cf6cfd2085c8779eda1aa3b946d3f647aac3342af473c5ee769730d89ead431`; CPU test receipt8940cb13a662b461973ac584b1b1f828db150388bc51b508d2f38ac19717d8c2; installer loga61cec989fda3c1b030a6355dabbf7f074941e2144dd60bed4e8a02621aead45. Source apply receipt814eba72b603e03740dd8f1ac9f1005db102b773efe781ffbf23d041293aca1d.

Current service:9998 absent, no API/Engine/workers. Original service exited at12:24:18CST with EngineDeadError before pip was run; rootcause not established. Source-only fast-forward had already verified same service healthy at04:23:29Z. No stop/restart/signal from this task and no automatic restart. Performance remains paused.

Recovery checkpoint: oldHEAD7cb5599 objects remain in repo; exact old dirty files/base/patch and tracked hashes are in original/, base/, before.patch, before.json. Editable installed metadata/loaders and old generated version backed up in editable-before-v2 (earlier incomplete precheck backup editable-before also retained). No rollback applied. Upstream attention matches pre-update bytes; restoring old baseline must also restore preserved config and metadata, with fresh identity checks rather than blindly rerunning old scripts.

Current user-new-instance full accuracy completed underacc-008:GPQA162/198 passed155 threshold,ERQA244/400=61percent full400/zero exclusions. This validates the current bound combined stack/config, not an isolated PR performance benefit. No performance test or service restart by agent.

## 2026-10-28 环境变量只读核查

B容器与镜像Config.Env完全相同，只有PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin和VLLM_FL_METAX_CONTIGUOUS_SINGLE_PREFILL=1。当前Plugin HEAD仍1bc0c775，git grep在vllm_fl中无该旧开关引用，PR638已自动选择，因此变量是镜像残留，不控制当前优化。/root/.bashrc:100-104加载MACA_HOME/MACA_PATH=/opt/maca及PATH/LD_LIBRARY_PATH；/etc/bash.bashrc:72加载/etc/profile.d/conda.sh，登录和交互bash均自动激活base。直接docker exec不经过shell只继承镜像PATH/旧变量，未加载MACA/Conda。当前8010服务进程另继承USE_FLAGGEMS=1、VLLM_USE_FLAGGEMS=1、FLAGGEMS_VENDOR=metax、VLLM_FL_STRICT=0、CUDA_VISIBLE_DEVICES/MACA_VISIBLE_DEVICES=2,3及blacklist9，容器层未预设这些；USE_FLAGTUNE和白名单未设置。全程只读，没有修改环境或重启服务。
