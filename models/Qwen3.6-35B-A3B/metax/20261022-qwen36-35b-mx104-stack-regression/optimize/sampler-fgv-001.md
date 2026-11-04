# Current status

Implemented in current B; operator/import/actual-wrapper/graph checks passed. GDN registration and existing tuned MoE sources unchanged. Model service is not running, full-model graph/C8/GPQA and a new formal gate remain not run. Final design/coverage below supersedes preparatory drafts.

# Sampling filter integration into FlagGems-vllm

User explicitly requests current B use reference qwen3vl-pr943-split1-mx104-20261023 FGV filtering interface, preserving GDN registration and fused_moe tuning. Only private Plugin/FGV in B on mx-104 may change; reference is read-only, vLLM/weights/Gems remain unchanged.

Accuracy Skill mode minimal-regression: sampling is high risk. Numerical/alias/fallback/lifecycle/graph checks do not constitute formal GPQA or a new gate. Model service currently absent; GPU4/5 observed free, other devices untouched. No automatic performance testing or gate reuse.

Archive commands/sampler-fgv-audit-001.py SHA c3108d8b79777b65bf211cccc5d2e6f61be0d51ad2fea7699e9e2241a2c14cdb completed backup/read-only audit. Local pre-audit record writer failed on Unicode source encoding; preserved as observation, no model/source write. Plugin and FGV tar backups and exact target/reference sources are under operator/sampler-fgv-001. No production changes yet.

## Pre-coding contracts

| Project truth | Frozen scope |
|---|---|
| Operation/API | vLLM top-k/top-p in-place logits filter; requested FGV public apply_top_k_top_p |
| Editable | Target private Plugin registration/adapter/legacy filter/test; FGV generic/export/MetaX filter and aligned test/benchmark |
| Read-only | Reference container, vLLM, Gems, weights, GDN registration/class/kernel and FGV fused_moe tuning; frozen backup snapshots |
| Build | Existing editable packages; syntax compile and real Conda import, no pip/global reinstall |
| Validation | Actual old-native filter oracle, stable tie oracle, identity/unsupported/alias checks, fresh-process lifecycle; GPU4 finite tests if still free, capture plus two changed-input replays |
| Benchmark | Small operator-only baseline/new time in ms, fixed seeds/shapes; diagnostic only, no E2E claim or tuning search |
| Active set | FP32 contiguous [M,V], M0/1/7/8/32/64, V1/non-power-of-two/151936/248320; exact-BF16 and general-FP32, both int32/int64 k; k-only/p-only/both/none |
| Budgets | Fresh CPU process180s; finite GPU script900s; no model HTTP requests in operator tests |
| Autotune/profiler | Reuse reference MetaX kernels unchanged (fixed existing schedules), no new algorithm/search; generic other-vendor API unsupported; NVIDIA tune_configs not applicable. No new profiler required for API transfer |
| Fallback | FGV library NO_TORCH_COMPUTE_FALLBACK; generic unsupported raises before modification. Plugin explicit native MetaX fallback handles rejected metadata, matching reference integration |

| Semantics | Contract |
|---|---|
| Oracle | Installed vLLM apply_top_k_top_p_pytorch; both filter forms AST reviewed; chosen stable tie policy additionally compared with stable ascending-sort oracle |
| Input | FP32 MetaX CUDA-compatible rank2 contiguous logits; M<=64, 1<=V<=262144; k optional int32/int64 [M], 1<=k<=V; p optional FP32 [M], 0<=p<=1, matching device/layout |
| Output | Same tensor/data pointer/dtype/shape, excluded logits become -inf; no RNG in FGV filter; original vLLM random_sample and per-request generators untouched |
| Dtype/unsupported | BF16/FP16/FP64/int logits, noncontiguous/oversized/cross-device metadata rejected before changes, then explicit Plugin native fallback; M0/no-filter identity supported |
| Boundary | Finite values, +/-inf, ties and signed zero tested; NaN behavior assessed separately, no unvalidated NaN semantics claim; forward-only inference, no autograd contract |
| Tie policy | Stable token ordering for threshold ties in reference library may differ from unspecified unstable torch.sort tie order; do not claim bitwise model output identity or reuse old gate |
| Reference-only torch | Tests/benchmark use torch clone/sort/softmax/cumsum; library only empty allocations/metadata plus existing FlagGems compute kernels |

| Path | Selection and implementation | Verification |
|---|---|---|
| identity | No filters or supported zero M -> same input | Alias and zero checks |
| exact BF16 | Device-side exactness -> counting sort + FGV softmax/cumsum | Seeded/boundary numerics and graph |
| general FP32 | Existing FlagGems radix sweep (target/reference sweep AST equal) | FP32 numerics and graph |
| metadata unsupported | FGV raises NotImplementedError before writes | Plugin native fallback, input unchanged before fallback |
| non-MetaX/disabled policy | Existing path preserved; no new kernel/default for other vendors | Static and isolated routing tests; other hardware not claimed |

Register generic wrapper in register_model after normal native imports; default MetaX enabled subject to existing use_flaggems_op policy, no new startup flag. Keep native TopKTopPSampler class, forward/RNG/logprobs unchanged. Idempotent wrapper refreshes known existing from-import aliases. Restore simple MetaX PyTorch compatibility fallback; remove sampler subclass installation from ModelRunner but keep its GDN import. Old specialized Plugin kernels are archived after source backup. Optimization.md absent in installed target snapshot, workflow read and these scope-specific tables supplied; no deep kernel redesign.

Production candidate manifest b374ee7a375be6a0a544ba140d421bf9cc121945f84fc5149819d82aa55acc4b:14 files including aligned library test/benchmark; archive2 obsolete Plugin kernels. Reference kernel body reused in target existing _metax/fused layout, generic/export wiring adapted. Plugin adds registration+adapter, register_model hook, restores simple native compatibility patch, keeps GDN-only ModelRunner block, replaces subclass lifecycle test. No startup flag required; existing use_flaggems_op controls FGV/default MetaX route.

Before execution archive commands/sampler-fgv-apply-001.py SHA 6c5d3fb9076116dce7bdf59c9f6310c12483ea3c0bc0f1a01d906b1d79a4d6a5 and candidate-manifest-001.json. Complete protected source CAS, per-file backups, atomic writes; GDN/MoE hashes remain identical. Fresh real FGV backend export and native sampler class/registered wrapper are checked with required Conda/MACA/MPI environment. Import failure precisely restores this change only. Numerical/model gate remain pending.

Final apply SHA 8476f8f9ec07ef95132b443693b32e27c81054ba7f36a9feb9480032589ac014 supersedes unexecuted6c5d draft: source manifest compares only its exact four source roots; aligned FGV tests/benchmark are backed up but outside production source-manifest scope.

Finite validation command archived as commands/sampler-fgv-validate-001.py SHA 2e3a5806f9f8e2d0f1efe3df12b2285066383dc137851b8e6545aae3b742f0c4. Three fresh mx-smi checks reject any existing GPU4 process; use only B/CUDA_VISIBLE_DEVICES4 and leave other devices/services untouched. Native pytest collect, 45 operator cases including BF16/FP32, boundaries/unsupported/alias and two changed-input graph replays, then six fresh-process sampler import permutations. Operator budget900s, lifecycle900s, no model requests/service start/newgate. GPU access is scoped to the user-authorized current B GPU4/5 task environment; no service is stopped.

Additional wrapper check commands/sampler-fgv-wrapper-contract-001.py SHA ebc2bda347366ba43d5469d44c6f3067dd59ca1c44b5c2d1a8a3304b3820e09b uses actual FGV call and GPU filtering, verifies unchanged native sampler/RNG function and RNG state, unsupported-FP16 and disabled-policy native fallback, no broad error swallowing; non-MetaX registration is isolated mock-only, not hardware evidence. To execute only after core operator validation success, on same B/GPU4 and unique log. Current local accuracy bundle snapshot is /tmp/qwen35-sampler-fgv-001/accuracy-skill-bundle.json, archived at closeout; no old bundle SHA reused.

Minimal regression001:43 passed/1 failed (44 actual cases), p-only FP32[M64,V248320]2 mask entries differ; not a GPQA result. Lifecycle not yet run because controller stopped after failure. Accuracy diagnosis Skill invoked, issue sampler-fgv-001-top-p-only, promotion blocked. Preserve log and fixed source/tests, no tolerance change. Narrow reproducer commands/sampler-fgv-diagnose-001.py SHA adfed56508af0305de290bf71715e0ea2ba28015ac993f9a0432e46cfc092828 compares repeated masks, sorted values and cumulative threshold with same frozen seed. Planned safe coverage: reject top-p-only before modification at FGV boundary, Plugin native fallback; both k+p model path remains FGV and all supported cases retain exact assertions.

Diagnosis001 confirmed repeated masks identical, sorted values exactly equal; FlagGems cumulative reduction differs up to1.1324882507324219e-6 for same softmax, moving2 cumulative values across cutoff0.050000011920928955. No RNG involvement. Safe support narrowing instead of numerical tolerance change: FGV top-p-only raises before modification, Plugin original native fallback. Both-filter/k-only current model remains library; no kernel arithmetic changes. Fix commands/sampler-fgv-fix-002.py SHA 2b110073b75d40e5f2a47b11ec2e2db28bce703cee9d6e52e3024ad36cd8f6de, payload d0081cdfbf76c25d6aa4952f1fcb7200dcaa46c6e184ed3b28c33e5046019a07; preserve original test/kernel in fix-before-002. Exact supported-mask assertions unchanged, unsupported scope tests now check rejection+unchanged input+original native fallback. New full44+6 validation entry commands/sampler-fgv-validate-002.py SHAd3341980e463b66d24879955b8d5e0f9092d028b8d6f2741d7cae91255db3881 outputs validation-002; initial failed run never overwritten.

Current accuracy bundle1ed06a57f1f6e1ef39fb7fd872f579122b098a18f0255ade0a1160d6432c2b66 verified with explicit --selection minimal-regression; initial capability-only inspect correctly returned incomplete (missing selector), saved separately, not used as validation. No reinterpretation of incomplete receipt.

Conditional wrapper runner commands/sampler-fgv-run-wrapper-003.py SHA 8f2d56af3d5fb33a4e96fa990759bccdbb3009fc66c5b203c66f495f9d7f47c7 only executes after validation002 summary passed, bounded180s on sameGPU4; output wrapper-contract-003. Preserves all receipts/no model or service lifecycle.

Final wrapper runner SHA 475cb1e4a21b196b3b357bc6cae18772ddd9d86e5cd5455e58285a56a9def5b5 adds fresh GPU4 ownership check immediately before its finite test; unexecuted8f2d draft superseded.

Prepared independent final commands/sampler-fgv-final-004.py SHA 001144addc61b11e9ecbdf8c644d0720edfe1f3cbba0fdaee810fdfe5def3693: inactive until44 numerical/6 lifecycle/wrapper actual call receipts pass. Verify final complete four-package manifest equals exact reviewed additions/removals+fix, compile all protected Python, retain GDN/MoE bytes, audit no library torch compute, GET health only. CAS continuation current_job null, preserve old native jobs/history, no model/service operations. Full model graph/C8/GPQA remain not_run/incomplete and formal performance forbidden for changed sampling without new gate.

Before execution wrapper contract adds same-graph BF16-exact to general-FP32 replay (device-side path switching) without source changes. Final wrapper script SHA 76a3b0a7413e815c292298684dd4f2eabc736355f14d0089470b2c36e4890a38, runner SHA 9f93008e11de3c290dc5225aecc86d4dbc78cf5098628b676e13571497fddf6f; earlier drafts unexecuted. Exact prior44 tests remain frozen.

Wrapper003 observed0 actual library calls despite correct registration: inherited VLLM_FL_FLAGOS_WHITELIST contains existing primitive names, not new apply_top_k_top_p. No source numerical failure, all44/6 earlier checks remain. Keep wrapper003 failure log. Explicit requested FGV interface must actually execute: follow current full-FGV MoE integration using global use_flaggems() for this MetaX compound API, rather than primitive-op whitelist. Existing preference/global USE_FLAGGEMS disable still returns native. No Docker env/startup-script change, no automatic whitelist mutation. This supersedes the earlier planned use_flaggems_op policy for the new compound interface only. Policy fix payloadSHA c37aa386865c46b9f6e89d88ebfc15a909ab4bbd8fc2a7c8ead3b712bfe389ec, final wrapper probeSHA 7728aa1c40fb1289371bd3cc0bca72aecd86fdf370d9a26e4cd8650b57d6028e, runnerSHA 0be7cc6e3cb0906a98464f501920b33ed6a8be142db5542018a76f8e6002186b. Numeric kernels/GDN/MoE unchanged, final actual-call/RNG/fallback/repeated-install/same-graph proof required.

Archive before execution commands/sampler-fgv-policy-fix-005.py SHA 71a8a88fef42e4046d760d0c147a9eb925545f32a82bf9d1807587322e171ab0; only one Plugin wrapper file, original exact SHA protected/backup retained. Final runtime routing contract is global FlagGems enable, same as explicit full MoE API; primitive ATen whitelist remains unmodified.

Review of optional wrapper graph data found linspace(-2,2,257) is itself BF16-representable, so wrapper005 graph result alone cannot claim classification switching. Additional one focused commands/sampler-fgv-cross-graph-007.py SHA 66213bcacbb5848dc0da2b566a945d942990ff2250efe6c21801b7076ba5fa42 asserts actual representability/nonrepresentability before capture, then replays exactBF16 -> generalFP32 -> exactBF16 in the same graph. No production change; preserve earlier test/data limitation explicitly.

Final independent entry commands/sampler-fgv-final-008.py SHA d70e8f746a8d4868987fbd72213d9ea8ebe8f64dfcbe3e25dd04519a433394d7 supersedes unexecuted004 draft. Requires final wrapper005 and actual cross-classification007 receipts; expected source manifest includes exact policy005 delta and kernel fix002. Records initial six import permutations before policy-predicate-only delta, with final repeated-registration/native-class/RNG routing proof. No model/service launch or formal gate.

## Final result and evidence

Final source: Plugin wrapper fb2567f7e88e23d52b6692c1348d7f621b49e1e7264e38a4571f73da18117fd3, actual FGV MetaX filter dcfa764e3b90e07656a8da76248e9ad0eccc9403a4cfc2fc9ac29d7a745094be. register_model owns filtering registration; ModelRunner retains its GDN import only. Old Plugin shortlist/counting kernels are outside active source and retained in complete tar/per-file backups. No vLLM/Gems/weights/startup-script modifications, no package upgrades/reinstalls or commits/pushes; reference container read-only.

Validated44 numerical/alias/unsupported/fallback/graph cases and6 fresh import permutations. Six permutations preceded only the policy predicate delta (same import/registration structure); final wrapper005 independently rechecks repeated registration, actual library call, unchanged native class/RNG function and RNG state, unsupported-FP16 and disabled-global-policy native fallback, and no broad exception swallowing. Non-MetaX registration is mock-only. Cross-graph007 explicitly proves representability classification and exact-BF16 -> general-FP32 -> exact-BF16 in one graph,3 successful replays. Wrapper's earlier linspace test alone was not evidence for classification switching and is retained with that limitation.

Initial43/44 failure retained under validation-001; narrowed top-p-only to native path after independently reproduced equal sorted values and cumulative rounding at the cutoff. Supported-path exact assertions unchanged. Wrapper003 no-call failure identified inherited primitive whitelist omission; new explicit compound FGV API now follows global use_flaggems() as existing full MoE does, so normal current B startup requires no new env token/flag. Neither Docker env nor shared launcher was rewritten. Both-filter and k-only use library; top-p-only and rejected metadata use explicit original-native compatibility fallback.

Independent final verification: operator/sampler-fgv-001/independent-verification-008/verification.json SHA9317f0fe5f1e5c73f582a3e5e22168fedeb02862572ac129293238a6a81eda9d. Final complete four-package source manifest exactly equals reviewed changes/fixes;5209 Python files compile. Library production audit permits only torch.empty/empty_like allocations and existing FlagGems compute. All protected GDN/MoE/kernel/config hashes unchanged, notably FGV MoE c4673a and GDN109a6f plus Plugin GDNb4fb59 and MoE interfacea35ecf.

Backups: plugin-before.tar.gz SHA857eca470bb3a2d6f77b8cff9e563ffe56a0f95876400a84062290fefece3ec5, fgv-before.tar.gz SHA789724b514d8715bd02feda969c48fff3b82068a811ac26cc92ef628e9789e5c. Complete original files before001/002/005 and all failed logs retained. The optional benchmark entry is supplied but not run; no operator/E2E performance benefit claimed, no new profiler, no tuning search. Accuracy Skill minimal-regression operator portion passed; actual model service graph/C8/full GPQA are incomplete/not_run.

Continuation SHAd50ac9c8601332bc4cf4171315c9bf4480ed52aeefee428f6b4776a2a029a700/current_job null/phase sampler_fgv_integrated_operator_validated_pending_model_accuracy. Port18135 remains connection refused. No model service start/restart, no model requests, no new gate or monitor. Historical native scores remain immutable and cannot validate changed sampling. Final formal performance is not allowed for this new source until its exact model accuracy gate is obtained.

Knowledge delta: functional replacement at the filter boundary avoids replacing the vLLM RNG/logprobs class; primitive whitelist policy must not silently disable a requested compound-library API. Tiny cumulative errors can cross a sampling threshold even with exactly equal sorted values; explicit native fallback is safer than loosening mask assertions. These are scoped operator observations, not original13 GPQA causal proof or E2E speedup; no universal operator knowledge claim added.


性能后续（2026-10-27）：[blacklist-gap-001](blacklist-gap-001.md) 的受控B/A/B和两rankDecode trace确认本次API迁移没有保留原shortlist64优化，实际temp0.6/M64/V248320进入全词表radix；完整filter旧约2.30ms、新约10.58ms，同输入masks/保留值一致。此前44数值/生命周期通过仍仅为其原正确性范围，不再把接口迁移视为性能等价。当前尚未改生产实现或声称全workload恢复；新guardedshortlist需独立设计/精度/graph及E2E验证。


## 当前组合 sampler-shortlist-C64 正式回归补充

保留本实验原有结果与范围。当前组合（FGV guarded shortlist49e9、既有MoE/GDN调优、FlagTree fe1d24f6、Gems a456）在新独立回答缓存的一次原生rolling C64/fullGPQA198中得分158/198=79.7979798%，通过流量前冻结的用户NV77.53%阈值；198唯一doc/396filter行、旧160/147/161/154离线复算、当前同c2/source/manifest已独立通过。新gate SHA13b72e7e2035e0fd28e44f2c1c809e7532c109759978a7a6f83e1e85fc450deb，独立report SHAab644f95c7160ad791e74d844b67aa6cad23aefbd7aef6d6360ef5eb337dc46d；远端operator/sampler-shortlist-001/formal-c64-002/independent-verification-001。该分数证明当前组合，不声称本实验孤立精度收益，也不改历史C32/旧160绝对参考；完整四场景正式性能未运行。完整记录见[sampler-shortlist-001.md](sampler-shortlist-001.md)。


## 2026-10-28 当前 opt3 组合精度复测

用户重启后的当前组合、实际prefix-on/GPU4/5/TP2，原生GPQA198/滚动C64独立通过**161/198=81.3131% >= 77.53%**。198唯一doc/396filter行/原prompt-target-args/无旧回答缓存/前后fresh源码一致，旧160/147/161/154逐题重现。验证：`/public-flash/jinghao/qwen3.6-35B/20261022-qwen36-35b-mx104-stack-regression/accuracy/user-gpqa-erqa-c64-20261028-001/gpqa-followup-001/independent-verification-001/verification.json` SHA c9437b838bd089152dc01a11c3f32076e89941334e545a89b8f175606366ebb9。此为保留组合精度，不证明本点独立贡献，不与旧prefix-off不同配置计算收益。随后官方ERQA多模态C64发生FGV MoE临时cache13申请256MiB OOM，服务退出；GPQA已测通过分数仍有效，旧实例gate不可直接用于新实例/新参数。ERQA部分证据保留、完整400分数缺失，不自动恢复/补跑/性能。详见[user-gpqa-erqa-c64-20261028-001.md](user-gpqa-erqa-c64-20261028-001.md)。
