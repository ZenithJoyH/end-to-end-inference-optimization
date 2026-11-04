# fgv-moe-001: MetaX FlagGems-vllm MoE backend integration

- 当前状态：**已完成并保留。最后完成评测的 B/r39 两rank实际调用 MetaX FlagGems-vllm `fused_experts_impl`；一次原生滚动 C64/full198 的 GPQA strict 为160/198（80.81%），独立核验通过并已生成当前准确启动身份的新gate。** 达到预冻结的用户NV77.53%参考，也等于原160/198绝对门槛。全部198唯一题/396filter行、原task/prompt/target/genargs、strict评分、5756源码、前后manifest及当前无hooks/unpaused均通过。15项数值/graph2复用、当前服务graph2/rank+C8 8/8/长C1=42通过。单文件MoE改动和PR638保留；仅启动额外显式设置`PYTHONUNBUFFERED=1`，新gate绑定该实际配置。没有性能测量或单变量因果结论；小时监控已删除。

## Direction and evidence
Explicit user request: include MetaX in the NVIDIA non-LoRA branch and use flaggems_vllm.fused_experts_impl. This is a requested backend integration, with no isolated performance claim. The current MetaX path uses TritonExpertsFL.apply and individual CachedOps; installed FGV e1a02b6 has existing private MetaX fused_moe/GDN changes, all retained. Actual model: BF16 E256/K2048/intermediate256 per TP rank/top8/TP2/SILU, unquantized, no LoRA.

## Change and boundaries
Only private B file /workspace/vllm-plugin-FL/vllm_fl/ops/fused_moe/fused_moe_utils.py changes: add metax to original nvidia condition; replace flag_gems import/call with flaggems_vllm; preserve output.copy_ and kwargs. The generic info_once remains in code but is not execution proof; actual rankPID-bound native library dispatch records and runtime function-source identity are used. W8A8 explicit rejection/specialized class, Kunlunxin and LoRA pipelines stay unchanged. No global FGV ATen enable, vLLM/model/PR638 edits or dependency upgrades. Other platforms and quantization remain hardware-untested; this model uses SILU.

## Correctness and execution proof
Modes `minimal-regression` then `formal-gate`, covering this retained combination. CPU actual-AST routing11 and GPU numerical15 (existing tolerances, BF16/FP16 boundary/bulk shapes, graph capture/two replays) passed. Numerical report `followup-001/gpu-numerical.json` SHA706b006a5766bd28d48b28a92f398fd4ba4e1132a2c7f92be15c7255738cb6a5 is reused without rerun. Source guards bind all5756 files, sole production change is utils b03; installed MetaX FGV callee c575 is unchanged.

Latest bounded lifecycle: exact original r38 stop → same MoE patch → r39 launch with explicit logging-only unbuffering → graph2/rank/C8/fixedlongC1 and actual perworker native FGV dispatch → original frozen native rollingC64/full198 once, freshcache. Threshold0.7753 comes from the user's NV77.53 reference and is frozen before new traffic. Old160/147/C64161/PR154 and all rejected/failed receipts stay intact. Final independent003 verifies all198docs/396filterrows, native strict, current exact launch/runtime/source and fresh binding. No profiler or score retry.

## Performance
Not measured. No formal performance run or speedup claim in this change.

## Decision, risks and rollback
Only dedicated B/eval/GPU0/1; source/A and GPU2..5 untouched. Preserve failures and never replay submitted model requests. Before minimal succeeds, an actual failure triggers exact r39 stop, restore this single file, original-launch r40 qualification. The controller owns restoration; observers do not restart services. Once formal starts, preserve candidate and all partials without score retries. Prior r31 score cannot bind changed source or the explicit unbuffered launch. Preserve all other local edits, including PR638 and FGV optimization code.

## External evidence
CASE/operator/fgv-moe-001. Every new executable is uniquely archived under CASE/commands with SHA before execution. Raw sources, patches, numerical results and logs remain external.

Before execution, archive unique source and prep commands:
- `commands/fgv-moe-route-cpu-001.py` SHA `62ee529e3eb0ca772d90147d4d5212003d8a674ac55df75763c8327812bba1ce`.
- `commands/fgv-moe-freeze-before-001.py` SHA `088a7530c64e7545c93d475aadefb248fc9284f3705b8164841c98092e3ae2f7`.
- `commands/fgv-moe-utils-before-001.py` SHA `a9a0301e298595d3f9f66c51548eacc4e589f7b09b71d0d914634d909619c161`.
- `commands/fgv-moe-utils-after-001.py` SHA `b03c3c3d880c9ef7f1e0c0f2639d8ef9ecbdadb4400bd6dada2e2478c027479c`.

CPU actual-AST routing11 cases passed; W8A8 guard and non-fast-pipeline AST unchanged, NVIDIA kwargs unchanged (mock only). Before hardware execution, freeze GPU matrix: BF16 M=[0,1,8,9,64,65,128,129,257,513,8192], FP16 M=[1,8,9,64], E256/K2048/D256/top8; existing reference for M<=129, independent grouped FP32 oracle for bulk, existing rtol0.1/atol>=0.01. BF16 M64 capture/two replay. GPU0 only after exact r31 stop; 0 model requests.
- `commands/q35_fgv_moe_ownership_001.py` SHA `f7c38434ee5ab3d58ec3569eaa167052beb5c744a572cb56cc7c9310c2fcd77f`.
- `commands/fgv-moe-launch-service-001.py` SHA `1f526078b45a361111223e73c6be6f4d58f79d355f1cbba1e9f0bbd4a3a3de0f`.
- `commands/fgv-moe-stop-service-001.py` SHA `af0d89d738e7c486428509c04aff609386ebce6fb60129a637053a24126ae939`.
- `commands/fgv-moe-qualify-service-001.py` SHA `86a9865b56b8b64918985ca4d6822db37b3a49099dd88cf6d8ce1cf83c9ee831`.
- `commands/fgv-moe-gpu-numerical-001.py` SHA `3c467c05d4c9ddf0d25fb02c3aa1c44f612755157b6a235b78809f513c521584`.

Freeze001 verified5756 source hashes and saved rollback bytes, then observer metadata failed because /workspace/FlagGems has no .git (private installed snapshot). No production/source/service/model change. Preserve original script/partial proof. New completion records git_repository=false/revision=null for snapshots and uses complete source identity, without replaying old freeze. `commands/fgv-moe-freeze-complete-001.py` SHA`343a09594975f029d562041129d09c1a174561e8bf3c3c8ebb0a0057a441668e`.

Freeze completion passed, preparation SHAcebd08cea42601fb62552eddb80da7877547a57bdad3fc1fd5dbb6282d3d8b50. GPU002 is the same finite matrix plus exact child PID/start/argv receipt before import; GPU001 is archived but never executed. Lifecycle guards preserve source/partial evidence, cancel only case-owned test PID, and restore this one file/r34 only before formal if needed. Original formal tools accept a finite schema3 threshold; new0.7753 user reference is frozen before this new run, no historical threshold_source impersonation.
- `commands/fgv-moe-gpu-numerical-002.py` SHA `265774bc76303dc79f2a4319af6b136f103508e870accde1ec1bb0794d79f3c2`.
- `commands/fgv-moe-long-c1-001.py` SHA `6ee32827612a0a8acd488b62f9252f6fed045b00a25a28431f49ead05a3d11fb`.
- `commands/fgv-moe-prepare-formal-001.py` SHA `7a1d4ead88d2d1711ecbeadf9ba09003c6b16a03dd4ef6f8895dc21ce13b6cb0`.
- `commands/run-fgv-moe-c64-001.py` SHA `7a59caed5cc63186722323de82b1bd2e1e67368b78bf1fdcdfe3f40dbf06c4ab`.
- `commands/start-fgv-moe-c64-001.py` SHA `2b7b4b80bd0afafa12f074ed5f5770089284e15abdcf284ad4f8ab26152ab3f0`.
- `commands/fgv-moe-001-execution-plan.json` SHA `dcfc3e797383b9a0a576d7976031cb923433b8112d978cd1a31517d0b9a447bc`.

App returned monitor ID qwen35b-flaggems-vllm-moe-c64. Starter002 only corrects that metadata ID, preserving every inner001 plan/controller/helper SHA and service/model action. Starter001 remains archived and never executed. Before execute `commands/start-fgv-moe-c64-002.py` SHA`dcc7e310f28ac0407f85b90c50bb34994407bceb5c5acb7395b36c7083c74b10`.

Unique job submitted: accuracy-fgv-moe-c64-001, wrapper PID2066566/start1130549469, launch SHAe8c3b05e19c66f9dc761b39c14b43e3f0e848f1ab139f2bf2259b7d17d6963ad, command SHAd3781e333da908ec88de82b243a2420fa97e9534630290ae8d27ca5e251beabe. Monitor qwen35b-flaggems-vllm-moe-c64 ACTIVE hourly. No replay of this starter/controller or any resulting GPU/model submissions.

First job nativeexit2: GPU002 import failed before any MoE kernel because standalone docker-exec did not inherit service MACA_PATH/MACA_HOME/PATH/LD_LIBRARY_PATH. Source was not applied, formal0, numerical cases0; r34 original-source restoration/graph+C8/manifest passed, original failures preserved. Before another service transition, archive an import-only environment check using every frozen launch-v2 environment key (GPU0 only), no model/kernel calls. `commands/fgv-moe-import-env-001.py` SHA`bd755e16e99c8e2ceca4a73ffad020fcadbdf3570787d02064676c77b4cecdce`.

Original001 restored r34 and endednative2/error gpu-numerical, source_applied=false/formal_started=false/restore_error=null; no numerical progress file or completed case exists. New bounded followup will inherit all launch-v2 environment keys for standalone GPU validation. Keep all original output. Followup preparation only reads current r34/full5756 and creates a unique external followup directory; no service/model actions. `commands/fgv-moe-followup-prepare-001.py` SHA`bba42e028fbc5d1f6ca7a0bfe325da7ec60f7fb2807fcc5bb8ce7de2677fd9a9`.

Full launch-environment import check passed: actual exported callee is private MetaX fused_moe.fused_experts_impl (source SHA c575c8a798232cd86e18e1239d2a314cd0e3afe21faf5951c45798c84f706679),0 kernels/model. Fresh followup preparation SHA86ac425fc3d937f9ac02324229073ef76354925f04609b789918d596b38153c9 binds restored r34 PID333307/start1130555146 and all5756 unchanged. New unique followup does not replay old controller; only remaining previously unexecuted numerical matrix/source integration/native198. GPU003 matrix unchanged, environment now exactly launch-v2 except GPU0 visibility. New service r35, exact early rollback r36.
- `commands/q35_fgv_moe_ownership_002.py` SHA `fa1d19506a62fd3010077b00f6bde5715526e5dba0d5a8107e11bc2bdc8f735d`.
- `commands/fgv-moe-launch-service-002.py` SHA `cba5e4bdb1be79394959dec106775979962b0ddb5e813ba71d5908c94385c9e0`.
- `commands/fgv-moe-stop-service-002.py` SHA `152a2d06d11e55701f411f2763be3cda9251a830e74eaa47da8459b6e6f56fd0`.
- `commands/fgv-moe-qualify-service-002.py` SHA `71c176d8f1d197e8a1d5c31ca585b99c03f91f5e3031630390a5084a97fa0da4`.
- `commands/fgv-moe-gpu-numerical-003.py` SHA `4e926079770e13c2877786110753a78db34bc3a5856de6a5d24dbfd46909f6e0`.
- `commands/fgv-moe-run-gpu-env-001.py` SHA `e464ef247891ea8feba0ab9c0968f15a53f9c2e467a259a251c96dd6dd0a44c7`.
- `commands/fgv-moe-long-c1-002.py` SHA `ccf93c3bc470b9a583a3be14deaca3d4f3d449fe2055942788d7999e9ece874d`.
- `commands/fgv-moe-prepare-formal-002.py` SHA `eb542a282f30347a4419f87af2dd38cef4263b954d379fdd3a7ad544aa704a9e`.
- `commands/run-fgv-moe-c64-followup-001.py` SHA `55551c912f12912587510036ee9fc51ad4c1704a87c3c6094338f43f619288e4`.
- `commands/start-fgv-moe-c64-followup-001.py` SHA `910df9a0cd0ceb9e53a9d990cf102b3c0682489d24ab79baa585d2077e9a5727`.
- `commands/fgv-moe-002-execution-plan.json` SHA `0fe069fd7c1d21aee006627c02b5fe7b3dc056ad83e5253b3f58fedba2228ddf`.

Prepared but inactive terminal verification for actual followup ROOT/r35, native job launchc4bdb15feee8aae01c141ed73fb401e4aed45d442668b5312bfeadddf27eccbf/commandde5ef4e90cb0919c4df9b88fbd10755d646cedb40e029f50cc33fb2626cea1fd. Run only after complete native198/396, summary no error/native terminal and same r35 identity. Reproduce original160/147, priorC64161 and PR154 offline, then current strict and threshold0.7753, no generation. Fresh runtime/callee/protected5756 source/manifest/graph/C8 checks. Output independent-verification-001 must be absent; preserve any observer failure in new unique versions, no model replay.
- `commands/score-fgv-moe-native-independent-001.py` SHA `5f28640089cf815d67f7a3bd00491721520e2ddf81205f1fa12c762161f0b742`.
- `commands/verify-fgv-moe-final-independent-001.py` SHA `2715ca8f368cdeb4a2bc366efe92f657c632ac04f7798bdf391ed4615cc0daee`.

Actual followup launch: PID2105828/start1130623094; launch SHAc4bdb15feee8aae01c141ed73fb401e4aed45d442668b5312bfeadddf27eccbf, command SHAde5ef4e90cb0919c4df9b88fbd10755d646cedb40e029f50cc33fb2626cea1fd. GPU003 numerical15 cases and BF16M64 capture2 replay all passed (report SHA706b006a5766bd28d48b28a92f398fd4ba4e1132a2c7f92be15c7255738cb6a5); actual vendor callee sourcec575c8a798232cd86e18e1239d2a314cd0e3afe21faf5951c45798c84f706679. Single utils file applied b03c3c3d880c9ef7f1e0c0f2639d8ef9ecbdadb4400bd6dada2e2478c027479c, applied receipt74069ec3327cdeab996edb385490ff7c13809da3b04f0d0e8eae9936a05fa353. r35 launch SHA77289dc101b32a62cf9eae2e50b7153f4f9b747d6cdbaec0e2fa7f05d030c519, currently loading; no model-level passing claim yet.

Before execution, unique read-only native start observation `commands/fgv-moe-formal-start-observation-001.py` SHA`7f4c1b1b1b3861746a3f499ebc9eebac4b3802af4e506b3d68bd5e71e334f4d3`; only execute once nativephase running_formal_C64, verifies zero reused answers/effective C64/user threshold, exact wrapper/service and dispatch source. No model/admin requests.

Followup001 reached actual r35: GPU15+graph2 passed, both ranks exported private MetaX fused_experts_impl(c575...), each emitted32 native MoE dispatch records, graph qualification/C8 exact8/8/longC1=42 passed. Controller incorrectly required a suppressed custom logger.info_once string, treated this observer condition as failure, and automatically restored original utils/r36 (passed); formal0. Preserve nativeerror/summary and all successful artifacts. New independent file verifies real PID-bound library logs and existing completed tests without model traffic. Next continuation reuses numeric15 proof (no numerical rerun), applies same b03 source and validates fresh r37. Before execute `commands/fgv-moe-followup2-prepare-001.py` SHA`f03d1614a0d667107bd6fbc188740ca421e4bc0937c870da8ee6ab060d7040ec`.

Observer false-negative preserved: prior r35 actual minimal independently passed (report SHA d3078b3f5387c059e672ca6f153f4be42551317c6132cd84e1885cbed0b196c8). Current old-source r36 PID348959/start1130651546 verified; unique followup002 preparation SHAfc19f28f356df230ce63d9ff6d12a3b604da83b178e64801eff66972dcacc158. Same source reapplied to r37, exact early rollbackr38. Native worker PID-bound MoE=ON library dispatch proof replaces suppressed custominfo_once. Reuse passed15 numerical+graph2; zero new numerical cases. Fresh r37 graph/C8/long and exactly one native C64/full198 only, threshold0.7753 userNVcriterion frozen before traffic. Prior formal submissions zero.
- `commands/q35_fgv_moe_ownership_003.py` SHA `d8905646168a34fbc2642a573f7e6c231a8df895f1b159af8e298f42ebb007f9`.
- `commands/fgv-moe-launch-service-003.py` SHA `7403751915df36f32b49570d5e7b8e9356022047c072059155b8aab9e281265d`.
- `commands/fgv-moe-stop-service-003.py` SHA `87172bf8413c1ca5da43e4f7fc1dca792245264a6a906c905120670e8177aedd`.
- `commands/fgv-moe-qualify-service-003.py` SHA `004a52f09ec0649e723ce391828eef7b6c972ef4f71968f828c421bbcc7ffc18`.
- `commands/fgv-moe-long-c1-003.py` SHA `2c013a8b07812ac3315cbddeccafffe99767552d34c9dd8521e75154dcd49d4b`.
- `commands/fgv-moe-prepare-formal-003.py` SHA `334b43bc5a2426768809067adcc8516bd1906fe9efb2133f68b888ce74709b03`.
- `commands/run-fgv-moe-c64-followup-002.py` SHA `be50f5e485d042ac5d2109e478dd96ee1b5674e444664eaf12dc0b2ccab4207a`.
- `commands/start-fgv-moe-c64-followup-002.py` SHA `0db84e18f3f1833b99cd8b1fb6909dcdc250cdc36eac6d8434d330e91a613abf`.
- `commands/fgv-moe-003-execution-plan.json` SHA `b4b1fe8f324f7d23e7ebb964f27b17c92d68dc7c380ecd4dc3330ea3900a4a9f`.

Unique followup002 submitted once: wrapperPID2187799/start1130811224, native launchSHA80eae5feeba699eb24f2777b2149725ec016b010c10318201b640df05d6105a1/commandSHAbbb8f05c19c084f7b6362dfca8a40cd69df18718d94155f344dc95afd0e49fa0. Final independent002 tools prepared inactive (001 bound obsolete r35 never executed). Full verifier only after terminal full198/396 +same r37 restored-nohooks/manifest/gate; reuse numerical706b reference, independently match actual rankPID native library log lines. No model traffic from these tools.
- `commands/score-fgv-moe-native-independent-002.py` SHA `406005cdfbbb89021189d95574b34786d01eb0473c38e9894349ff6d408cdbdf`.
- `commands/verify-fgv-moe-final-independent-002.py` SHA `eccd4686e0fa0d2f29c235412ede2fb2cc9e3e695dc36b6677200d4b074198fe`.
- `commands/fgv-moe-formal-start-observation-002.py` SHA `7f1317ce7a4610a052146fb3825256a8d579f4b5524f91d2904b0aa1b8a4112b`.

Accuracy skill fullbundle SHA1ed06a57f1f6e1ef39fb7fd872f579122b098a18f0255ade0a1160d6432c2b66 frozen; caller modes minimal-regression/formal-gate. Final verifier prepared only, not executed/passed.
- `commands/fgv-moe-accuracy-skill-bundle-001.json` SHA `40605374230efd02ad9b4ba62f379c2b7038d5f9c00025d3c00de3194a34c538`.
- `commands/fgv-moe-independent-verification-002-prepared-plan.json` SHA `880cdeec52e81fb41e2aff4645747cf7f8151db7dab30de7d54e650490d1d207`.

Followup002 observer again false-negative: after r37 graceful exit, exact worker354307/354308 each32 nativeFGV lines appeared; graph2/C8/long42 allpassed,0formal. Native stdout buffering is now evidenced. Next unique preparation only verifies prior success/restoration and creates explicit logging-only launch config PYTHONUNBUFFERED=1. New fullgate binds exact newlaunch (no oldgate rebind), inference argv/remaining env unchanged. Originaltools/config/sourceproofs retained. Script commands/fgv-moe-followup3-prepare-001.py SHAd2fc7165912a1cb20b6400ec317aced34a582abbe37a821de466780b93299d47.

Pre-upload correction: historical status explicitly r37. Final followup3 preparationSHA 7f868573d2689bd7c1913b1b81e3e78dd5f5f42ee451708f50ce80140f2510e5.

Followup003 prepared from restored r38 PID358617/start1130833994. Prior r37 actualminimal independentlypassed reportSHAaa5b6ba42800546a0d7ad26d0cc09247c25377595d983f1d600f549a22e60ea3,formal0; priorcontrollerresultpreserved. NewprepSHA2c050b25d594edaeb99b263463c2e0fa8d8f9e8ec6079de97b73e6bca56fb42f/expectedcontinuation0cd4c8bc9ab033775dfa50ce6f014922b03cfa901e5145ef2100d3de02542ed7. Explicit launchcopycommands/fgv-moe-launch-config-unbuffered-001.json SHA5bb1d197bc36fb65ccae5ebdfb5ba84a126b8d1e330b4994c9612db481604a65 changes onlyPYTHONUNBUFFERED=1. Newmanifest observer whitelists/validates thatflag; formalnewgate exactlaunch, no rebind. Backend/numerical/tolerance unchanged; freshservice r39, earlyrollbackoriginalr40;0newnumerical,9qualification,198formal.
- `commands/q35_fgv_moe_ownership_004.py` SHA `40d8e53bee786cee47d7951ed428c2467d03fcac611e2feff2df9343d0725100`.
- `commands/fgv-moe-stop-service-004.py` SHA `ac5ac533c71f216e02dd185b61de9bfbe114679f8f6b373d91a4c6707966afa8`.
- `commands/fgv-moe-long-c1-004.py` SHA `6c3e9434b10ba783b0c4d6a86019e8cc73012bf8c12950ab4bc590ce2ad6b08f`.
- `commands/fgv-moe-launch-service-004.py` SHA `c3c3c6226430e8c44c40a55224548d746d1d890b18b2ded7108fb7843fa36c1d`.
- `commands/fgv-moe-qualify-service-004.py` SHA `9736cd4571064c33c6f3fc2cc6b8146d8252f87cbb5ea4c65d6df18244d9f699`.
- `commands/fgv-moe-fresh-manifest-001.py` SHA `8f9d15b85c1b13b271999e9c6f3aab8534bc19bbd46b6c3e4a2863ef89a01a5e`.
- `commands/fgv-moe-prepare-formal-004.py` SHA `dbdfd735ee297816a6ceed57dbbe2884da94073ca97329f756050fb8f800d5a5`.
- `commands/run-fgv-moe-c64-followup-003.py` SHA `706b52523e8584847229623a051ad477c0b9cfdf33367cc3b6ea235357f05949`.
- `commands/start-fgv-moe-c64-followup-003.py` SHA `5dfeb48fe659cc82ef80e977e648de113fc590f054898c20cf6213cef2fbafc4`.
- `commands/fgv-moe-004-execution-plan.json` SHA `6542f19c7f8e5e59226ec95439b0364e22c753488f36426b7f8e28efcb20c0a2`.

Followup003 submitted once wrapperPID2213335/start1130881755, launchSHAe077ab514d33f6ea879ed6c825df35b23c4f59cd0f2273d1ad61feaddece9748/commandSHA9cbfea3ff8b4ece6c5dbc5c6f0d8691661406870e06e95ae206bcd50682bf16b. Native independent003 ready only after fullterminal/r39; validates logged-onlyflag explicitly. Old001/002 offline tools archived neverexecuted; none applicable to latestroot. Score closure AST unchanged.
- `commands/score-fgv-moe-native-independent-003.py` SHA `fbc26647f8ba654068e8ba1ade75d1a9308e79cad73b5e6c3d71716f0adcc238`.
- `commands/verify-fgv-moe-final-independent-003.py` SHA `0ddee2c300c4580485542602f0a47cf333f83e6b59e54e2f386b8469c21ad20d`.
- `commands/fgv-moe-formal-start-observation-003.py` SHA `6cf343076fe378df8281071b39f167333e1c0d50d8d27fabee5a9e51c9fac61a`.
- `commands/fgv-moe-independent-verification-003-prepared-plan.json` SHA `759fe5bdb846313c04b8ee2c877452811dd83c96a65ff8d895d19a606aae572d`.
- `commands/fgv-moe-accuracy-skill-bundle-001.json` SHA `40605374230efd02ad9b4ba62f379c2b7038d5f9c00025d3c00de3194a34c538`.

Current r39 minimalSHA582f631d6726c45f06f1a46ccf9c591a379ec5ab5b709cad635656b95e986584; qualificationSHA1a7120ed67b6f84ea57ce0d1bdfc5b1f2a66c9c8eb10ac074b5803779776c2bd; longSHAf4e754b9a36d37a03c59d766af10ce7a0424901823607d6a8d043be9daed390e; manifestSHAaf8beb47a3894269d969f079c5f19dab8a2bbebd34f273bc2d33f70b0b0f9c48. API PID363351/start1130884516, launchSHA95ef2015da0784ae6d96501569af5ffae9a2e680b2e231c82c039502f9c07db9. Native fullC64 run_id9e2936f03294452898d8a30833e004e6, actual submitted once; no newscore yet.

Before one-time start observer: native initialization1/cache0/198pending/C64 confirmed from actual formal.log. Execute commands/fgv-moe-formal-start-observation-003.py SHA6cf343076fe378df8281071b39f167333e1c0d50d8d27fabee5a9e51c9fac61a; archive unique .command.json before executing, no model/admin requests. Existingformaltraffic now present; no full198 retry for any observer error.

One-time startobserver003 exit0: reportSHAe4b91012e87c0e563b87e90e1770c6b1ecc00e57bfadb774f1cd33742c5da977, commandSHA84b37777feab6cc71aba717161a203d7e0430e8a91df891cb8bc586a76ba2838, resultSHA3029156610b98e946a8bb720dd7a9d591b8f39a9407211b88eb141963bd102b9. Actualwrapper2213335/1130881755 and r39API363351/1130884516 match; nativeinit1/cache0/198/C64 correct; realnative metricsrunning64/waiting0, no directdevice-shapeclaim. Modeltraffic alreadyinflight; no replays. Hourlyquietmonitor will independently verify eventualterminal anddeleteitself.

2026-10-26 terminal review before independent execution: controller nativeexit0 SHAca967f54f29eaedaef179e2b2e086d5cef7a34dfd2ce9a586c4a615d0e1c1393; formalexit0; summarySHAe56c92306180131e752de9c8408a6fd4a8b03489396fec2f8a7ea24e88cf5464, errornull/minimal+formaltrue. Native160/198=.8080808080808081, exact198unique/396strict+flexible rows reviewed, currentr39samePID/start. Currentjobnull/continuationSHAe503739d3e79df52faac62850d5e149c136debff55002b507b21d5eb42b3091c. Independent outputabsent. Execute existing reviewed003verifierSHA0ddee2c300c4580485542602f0a47cf333f83e6b59e54e2f386b8469c21ad20d under unique commands/fgv-moe-independent-final-003.command.json; archivecommandSHA before execute, no generation/restart/sourceedit. Native score preliminary until independent completes.

Independent003 exit0, commandSHAa93cc7229943fd211cd0cf562d36508bec164f1833257a906af19ea2d8fcdd04/resultSHAa9cbc5a5cea9d85b8474dab96107b309b82ed9348e901d0faabdae84a8f00882. FinalverificationSHA2bec056ec4dd667f3e501fbee106ba079bd874de612890d424a8daa19c3c12a8/native scoreSHAf8feb8304c52f650ee8f4b239f7479c6b1f677e7d95a8f51e12634ef9d1f63a5:160/198=80.8081%,threshold77.53%,passed. Source5756/currentr39two-rank/nohooks/unpaused/manifest/nativefilter198+396/newgate verified. GateSHA4f23550de1ae0d062dca376adfdd049f307f9813f7b280dfdc91113632bcf42f. Prior160/147/161/PR154 all reproduced offline; health0timeout/0empty, budget65536doc81/185/195 retained. Single run only, no causal/performance claim. Closeout after appmonitor delete by uniquecommands/fgv-moe-independent-closeout-001.py SHA01e8899fd98fe6d47eb9cde6eeb4207bfc2392c40caba4bf1de0a25ea3083618,CAS expectede503739d3e79df52faac62850d5e149c136debff55002b507b21d5eb42b3091c;no service/source mutation.

## 独立完成结果（2026-10-26）

正式native/controller均exit0，原生strict160/198=0.8080808080808081。独立工具003退出0，报告`followup-003/independent-verification-001/verification.json` SHA`2bec056ec4dd667f3e501fbee106ba079bd874de612890d424a8daa19c3c12a8`；原生离线逐题重算SHA`f8feb8304c52f650ee8f4b239f7479c6b1f677e7d95a8f51e12634ef9d1f63a5`；当前r39新gate SHA`4f23550de1ae0d062dca376adfdd049f307f9813f7b280dfdc91113632bcf42f`。旧160/147、C64161和PR154均在无新生成的离线流程中逐题重现。

本轮0超时、0空输出；doc81/185/195到65536生成预算，原样纳入strict，未挑题或补跑。相较旧PR154本轮分数多6题，但198文本均变化、30题strict翻转，只有一次新评测，不把分差作为隔离因果或性能收益。旧错误、恢复和分数均保留。

CAS完成收尾：continuation SHA`191fec992471383c08260183ca08eaaa43c709d065f02fe920e4b5c667bcbfcf`，独立收尾SHA`bf9801f4a334bd817dce179a915866f44caded75ffebb7fef2194e97a23eb55e`。应用已确认删除`qwen35b-flaggems-vllm-moe-c64`监控。当前服务保持r39及已验证的单文件MoE改动/显式无缓冲启动身份；不自动启动性能或修改公开PR。

## Read-only audit of user startup script (2026-10-26)

/public-flash/jinghao/qwen3.6-35B/start-model-flagos.sh SHA6b96b85232226734641d8f8225c9392159d89123743a3c4cf5ee8d7302414dff selects no container or environment; directly nohup vllm. Host and plain B docker-exec PATH resolve no vllm; explicit /opt/conda/bin/vllm exists in B. Plain exec lacks MACA_PATH. Explicit B Python resolves vllm=/workspace/vllm/vllm, Plugin=/workspace/vllm-plugin-FL/vllm_fl, FGV=/opt/FlagGems-vllm/src/flaggems_vllm. Private /workspace and /opt are not shared mounts; actual MoE bytes remain b03. Script being in a shared directory does not select modified private code.

Script GPU6,7/port8010/model /public-flash/models/Qwen3.6-35B-A3B/FULL_AND_PIECEWISE/whitelist and switches differ from evaluated r39 GPU0,1/18135/model /data/Qwen3.6-35B-A3B-nomtp/FULL_DECODE_ONLY/frozen launch environment. Within B with proper Python and MACA env it can load same edited libraries, but running the unchanged script does not reproduce evaluated configuration. No script edits, model requests, service changes, or new monitor.

## User-requested startup script adjustment (2026-10-26)

Before execution: commands/adjust-start-model-flagos-20261026-001.py SHA6bf4e76a82cb5e0530d5c4fd21fc491359ecf113cb9e23f28d220701e33f59c9. Target oldSHA6b96b85232226734641d8f8225c9392159d89123743a3c4cf5ee8d7302414dff, proposedSHA96ccdd386d579e87092f0a43ce681f9301319191e1309337bc1c28fc8b12d5a8. Explicitly targets evaluatedB/containerID/image and immutable unbuffered launchconfig5bb1; originalmodel/argv/env includingGPU0,1/port18135/FULL_DECODE_ONLY preserved. Host entrypoint uses explicit B Python and complete MACA env via config. Guards5756sources/actualpackagepaths. ExistinghealthyidenticalAPI returnswithoutstart; busy/changedservice/activecontroller/occupiedGPU orport refuses, no stop/kill/sourcewrites. Freshfuturestarts get unique logs and receipt, oldgate is not automatically reused. --check is read-only and is the only runtime path tested here; no live startup/restart or modelgeneration. Originaluserfile backedup under CASE/commands with oldpermissions; only atomicallyreplaceafter unique syntax/preflight success and exact r39 before/afteridentity.

Startup script adjustment completed: targetSHA96ccdd386d579e87092f0a43ce681f9301319191e1309337bc1c28fc8b12d5a8, auditSHA9ed3bd836417130c28efb26a37abd41c1f9e9209a1b8c0107094d5671f322865. Old exactbytes/0755/uid0/gid0 preserved in CASE/commands/start-model-flagos-before-20261026-001.sh. bashsyntax and real --check passed; currentr39 PID363351/start1130884516 unchanged,5756sources/importpaths/actualenv match,0newstart/restart/modelrequests. Future host execution selects exactB/config/GPU0,1/18135/modelnomtp/FULL_DECODE_ONLY. Alreadyhealthyidenticalservice exits withoutduplicate; conflictsrefuse,nokill. Newmanualinstances have unique logs/receipts and require new gate binding. Actualnewservice start branch was not exercised because currentvalidatedservice remains running; no gate/profile/performance changes or monitor.

User explicitly requests minimal startup instructions only. Beforeexecute commands/simplify-start-model-flagos-20261026-001.py SHAd114656702c253d65daef711f9c20f4bfaf6d117192c3f45c637d366beb3fa0f; oldscriptSHA96ccdd386d579e87092f0a43ce681f9301319191e1309337bc1c28fc8b12d5a8 to new35lineSHA8751576abc160df5459c4d2a0dd88f481e6e848c8a067c2a69160ef67d17db37. KeepBselection+literalvalidatedexports+vllmargv+nohup/unique log,removevalidation/locking/ready/state code and --check. Static shlexenv/argv parity andbashsyntax only; neverrunlaunchscript orstart/stopcurrentr39. Previousfullscript archivedwithpermissions beforeatomicreplace.

Simplifier001 stopped beforebackup/write because oldr39PID no longer exists; rawfailure preserved, original96cc script remains untouched. Freshreadonly confirms containerBrunning,r39PID363351absent, no partialbackup/newscript files. Task only edits script; no service is required to be live. New unique commands/simplify-start-model-flagos-20261026-002.py SHAf9d89b99e911a7d09cd8818456391366d99e0b8a904b0f1ac9f496f4ab445582 changes serviceguard tooptionalabsence-aware snapshot, keeps staticenv/argv parity and exactscriptSHAbackup; no model/service actions.

User-requested simplification completed: 35lines, literal Bdocker selection/exports/original vllmargv/cwd/nohup/unique logs only. All exported values and service argv statically equal validated5bb1 configuration; bashsyntaxpassed. TargetSHA8751576abc160df5459c4d2a0dd88f481e6e848c8a067c2a69160ef67d17db37; backedup190line versionSHA96cc atcommands/start-model-flagos-before-simple-20261026-002.sh; reportSHA4e47824ca6ef624035988389e89ea4e904f3104c0db9b5761fafd54addfbc353. No startupscript execution/service operations/modelrequests. --check/duplicate checks/locking/readiness/status/hash machinery removed as requested. Oldr39PID was already absent, Brunning; prior160/198 score validhistorical, any future process has a new gatebinding requirement. No monitor or evaluation started.

User requests run directly inside B, asks removing contiguous-prefill env and PYTHONPATH. Actual PR638flashsource f49 lines809-815 uses decoder/singleprefill/context>=2048/KVunquantized automatic conditions, no env read; only envs.py definition remains. Proposed29line containerscript removesdockerwrapper/PYTHONPATH/legacyflag/devmode/workerextension; unsets inherited threevars. Otherliteralenv/argv unchanged. Before execute commands/adjust-start-model-container-20261026-001.py SHAa91fc6a2e7f8c98fc5d910e25ecec30857bb11e64448f8133c42b5a173468ecb; newscriptSHAc6c03db1d4714df5876a15f94490c213ba0016208e4d7617c41774d569bcc955. Will perform staticparity/bashsyntax/real installed-package import and actual CLIhelp under clearedenv only, no modelstart/request/kernel numerical test or full198; backup before atomicreplace on success. Current private inference sources and frozenconfig untouched; old160score binds oldevaluatedlaunch, not silently rebound.

## 容器内直接启动及环境清理（2026-10-26）

按用户要求，当前共享启动脚本改为进入专用B容器后直接执行，29行，无外层docker exec。脚本SHA`c6c03db1d4714df5876a15f94490c213ba0016208e4d7617c41774d569bcc955`，旧35行宿主机入口备份`commands/start-model-flagos-before-container-20261026-001.sh`。本次审核报告SHA`a4de016d6dd127d0b4f2ede26fab9ecb52ebe50e3c4ad153d469b5ba5f8770c2`。

`VLLM_FL_METAX_CONTIGUOUS_SINGLE_PREFILL`当前仅剩envs.py声明，没有消费者。PR638实际flash源码SHAf49在809–815行按DECODER、单prefill、context>=2048、KV未量化自动选择连续KV，不再需要该环境开关。因此从脚本移除并unset继承值，未修改Plugin源码。

去掉PYTHONPATH时同时移除了`--worker-extension-cls qwen35_runtime_rpc.RuntimeEvidenceWorkerExtension`和取证用开发模式，避免启动再依赖案例runtime-tools路径。真实B Python在清除三变量后导入vllm/Plugin/FlagGems/FGV通过，均为当前私有安装路径，FGV导出的MetaX fused_experts_impl源SHAc575保持；真实`vllm serve <model> --help`退出0，bash语法通过。其余启动env/模型argv与原验证配置静态相同。

没有执行启动脚本、启动/停止模型、发送模型请求或重跑GPQA。原160/198仍是旧r39准确启动身份上的历史有效结果；本次仅证明静态无用开关及新环境下导入/CLI可用，不冒充新服务启动、精度或gate重绑定。旧r39先前已退出的事实保留。

## Read-only necessity audit of remaining exports (2026-10-26)

No script changes in this question. Plain B container already inherits FLAGGEMS_ATEN_SHAPE_AWARE=0,USE_FLAGTUNE=0,VLLM_FL_STRICT=0,PYTHONNOUSERSITE=1,VLLM_TUNED_CONFIG_FOLDER=privateMetaxconfigpath; MACA_PATH/HOME/LD_LIBRARY_PATH/PYTHONUNBUFFERED absent and PATH lacksMACA/conda. Thus removing a duplicate export is distinct from unsetting inherited policy. CurrentPlugin/Gems/FGV/vLLM Python source has no FLAGGEMS_ATEN_SHAPE_AWARE consumer. Plugin policy.py412 defaultsVLLM_FL_STRICT to0. FlagTune resolve_tuning_mode199-227 distinguishes explicit0(Default) from unset(adapted ops mayCostModel), so do not label USE_FLAGTUNE=0 universallyredundant; currentcontaineralreadysets0. vLLM fused_moe.py1063 readsVLLM_TUNED_CONFIG_FOLDER, affects tunedconfigselection/fallback though not a service startup requirement.

MetaX Triton compiler.py91 requiresMACA_PATH and options computesMACA_PATH/lib; driver.py20 also readsMACA_PATH. CurrentTorch cpp_extension.py83 localMACA_HOME is derived from os.getenv(MACA_PATH), not the MACA_HOME env, so standalone MACA_HOME env is compatibility-only for checked paths. PATH need not replace allsystempaths; prefixMACA/conda bins suffices. LD_LIBRARY_PATH can remove duplicateMACA/lib and trailingemptyentry; retain runtime/MPI dirs unless a complete no-LD startup is separatelyvalidated. PYTHONNOUSERSITE is optional user-package isolation (already1), PYTHONUNBUFFERED is optional immediate logging. No new model requests or startup performed.

User authorizes further startup minimization. Beforeexecute commands/minimize-start-model-flagos-20261026-001.py SHA5c08622459d74758782fc7f5542ca6ec61a4c7ea539e861093c15b23d7462406 and CPUprobe start-model-flagos-minimal-cpu-check-20261026-001.py SHA11133b85e3d73e2dddbce6f3f4291e4ba7729b6f6b0dcab4445ded1a728b6e47. Proposed24line targetSHAfcbd40efeb0a0a379fca63bf07f988dfeb3cae85dfa555d648cb6883653b2f4a, oldc6c03... backedup beforereplace. Remove inheriteddefaults/unusedshapeaware/log-onlyunbuffering/MACA_HOME, simplifyPATHprefix/LDdirs. Keep FlagTune0/tunedfolder via B inheritance (do notunset). ActualvLLM memorydefault0.92 differs, keep explicit0.9. generationconfig defaultauto and localJSON.6/.95/k20 matchesoverride, removeboth duplicateargs. NativeAutoConfig/Tokenizer/Processor withtrustfalse mustpassbefore removingtrustflag. Actualnewprefix imports/CLI help only, no modelboot/request/full198 or sourcechanges.

CPUcheck001 importedlibraries but observer incorrectly expected LD path prefix afterimport. Existing OpenCV import prepends its ownlibrarydirs (known existingruntimebehavior); this is not launcherfailure. Target stilloldc6c becauseatomicapply not reached; preserve001 stagedbackup/result. Unique002 observes LD beforeimports and records bothbefore/after, exactsame24line scriptsource and modelchecks. Beforeexecute commands/minimize-start-model-flagos-20261026-002.py SHA9e4bd59aaf5a6becab43f7936e32c31fb65f28f39ff8cdc54ee956cd766f7919 / start-model-flagos-minimal-cpu-check-20261026-002.py SHA6675eabc115ee59ab63ae17cdb7f2f359e3e8d17b6ffda20ab112e1edb64bfde. No startup/modeltraffic.

Further minimization complete: 24line containerentryscript SHAfcbd40efeb0a0a379fca63bf07f988dfeb3cae85dfa555d648cb6883653b2f4a; auditSHA b67de6c24716a58db6bcfddb28ab21a8cdf0ab70f9e5b53a94f9abef33bbecc0; previous29line version backedup commands/start-model-flagos-before-minimal-20261026-002.sh. Removed discussed duplicateexports/log-onlyunbuffering/MACA_HOME; PATHprefix+LDdedup, tune0/strict0/PYNO1/tunedfolder verified inherited. Removed generationauto/samplingoverride matchinglocalgenerationJSON, andtrustremote flag after actualAutoConfig/Tokenizer/Processor trustfalse/local-only allnative constructorspassed. CurrentvLLM memorydefault0.92, so explicit0.9 retained. Bashsyntax/actualprivateimports/CLIhelp passed; CLI/help and CPU constructors only, no modelstart/request/full198 or sourcechanges. CPUobserver001 oldresult kept; OpenCV normallyprependslib64,002capturedLD beforeimports to validatecorrectly, not a modelstartupfailure. Old160score remains historical oldr39launch, no gate rebind.


## 当前组合 sampler-shortlist-C64 正式回归补充

保留本实验原有结果与范围。当前组合（FGV guarded shortlist49e9、既有MoE/GDN调优、FlagTree fe1d24f6、Gems a456）在新独立回答缓存的一次原生rolling C64/fullGPQA198中得分158/198=79.7979798%，通过流量前冻结的用户NV77.53%阈值；198唯一doc/396filter行、旧160/147/161/154离线复算、当前同c2/source/manifest已独立通过。新gate SHA13b72e7e2035e0fd28e44f2c1c809e7532c109759978a7a6f83e1e85fc450deb，独立report SHAab644f95c7160ad791e74d844b67aa6cad23aefbd7aef6d6360ef5eb337dc46d；远端operator/sampler-shortlist-001/formal-c64-002/independent-verification-001。该分数证明当前组合，不声称本实验孤立精度收益，也不改历史C32/旧160绝对参考；完整四场景正式性能未运行。完整记录见[sampler-shortlist-001.md](sampler-shortlist-001.md)。


## 2026-10-28 当前 opt3 组合精度复测

用户重启后的当前组合、实际prefix-on/GPU4/5/TP2，原生GPQA198/滚动C64独立通过**161/198=81.3131% >= 77.53%**。198唯一doc/396filter行/原prompt-target-args/无旧回答缓存/前后fresh源码一致，旧160/147/161/154逐题重现。验证：`/public-flash/jinghao/qwen3.6-35B/20261022-qwen36-35b-mx104-stack-regression/accuracy/user-gpqa-erqa-c64-20261028-001/gpqa-followup-001/independent-verification-001/verification.json` SHA c9437b838bd089152dc01a11c3f32076e89941334e545a89b8f175606366ebb9。此为保留组合精度，不证明本点独立贡献，不与旧prefix-off不同配置计算收益。随后官方ERQA多模态C64发生FGV MoE临时cache13申请256MiB OOM，服务退出；GPQA已测通过分数仍有效，旧实例gate不可直接用于新实例/新参数。ERQA部分证据保留、完整400分数缺失，不自动恢复/补跑/性能。详见[user-gpqa-erqa-c64-20261028-001.md](user-gpqa-erqa-c64-20261028-001.md)。
