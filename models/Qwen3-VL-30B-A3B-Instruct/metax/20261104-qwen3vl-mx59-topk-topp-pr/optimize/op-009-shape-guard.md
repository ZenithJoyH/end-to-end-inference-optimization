# op-009-shape-guard: PR1069 prefix-statistics integration

Current: PRupdated039f03ed;guard32/131072 validated, source unchanged; supplementary B64/V4096 inheritedreferencegap disclosed.

User explicitly requests guarded implementation, numerical equivalence/correctness/graph/performance verification and updating PR1069. Source qwen3vl opt17 must remain unchanged.

Guard m>=32 and n>=131072 with p present is frozen before new measurements. Smaller batch/vocab retains original per-CTA reductions without prefix launch/workspace. One constexpr mask branch shares all original floating-point/tie logic; prefix statistics are int32, independently CPUint64-oracle checked. MetaX fixed4warps, no NVIDIA/autotune/dependency change. Reuses installed scan capability verified in op008; no wider compiler feature changes. No profiler needed for this bounded integration: op008 supplies stage/launch/shape-crossing evidence. Prefill/Decode/Mixed E2E unknown; pure sampling operator scope, not formal model-performance invocation.

{
  "id": "op-009-shape-guard",
  "host": "mx-59",
  "remote_root": "/public-flash/jinghao/qwen3-VL/20261104-qwen3vl-mx59-topk-topp-pr/op009-guard-prefix-20261106",
  "user_scope": "Add shape guard, preserve semantics, validate correctness/graph/performance, update PR1069; no source model changes",
  "guard": "m>=32 and n>=131072, p present; k-only unchanged",
  "baseline_PR_head": "ce0feddceb0d74a031081e57ce9ff9d24fef3b84",
  "image_lineage": "reuse verified immutable18128 snapshot only after fresh full source+clone static/import/model/mount parity",
  "clone": "qwen3vl-topk-guard1069-20261106",
  "physical_gpu": 6,
  "commands_sha256": {
    "control.py": "fd07a6c782da242088bd3e4bae6a2146735f377c41c0845edd8f41eedc31870f",
    "backend-baseline.py": "0f3f4eeb160032a6832e0ac214e947bb9fe435570f4de22eb1791f63d4befbb4",
    "tests-candidate.py": "abb9e0f980b4dd64460e40100e82b8c830dbf9bea65d8e9d1e1f7adc63d6845b",
    "mounts.py": "32adacf39859e88ad6e2dad04ada248a00b636c795fed67d34328f5264bec3e3",
    "benchmark-candidate.py": "68961c3dd85a7e24f4406b31a18a7410f08802bcfc95ac15e9f088dd6e99fcb2",
    "component.py": "42eb262456185057882510d2099d6dfc285540c445c812766eab15e32402cc38",
    "identity.py": "f50f65e0a8ecf09ed55d57e7831ffcd76efc7b26ad9a1c8ff2ce4de497de2edd",
    "backend-candidate.py": "8e34b2921baadc8c619288027f9ed1e8e14155b176b24d79edcedd671ba06f13"
  },
  "matrix_pairs": [
    [
      1,
      4096
    ],
    [
      1,
      151936
    ],
    [
      8,
      151936
    ],
    [
      8,
      262144
    ],
    [
      31,
      131072
    ],
    [
      32,
      131071
    ],
    [
      32,
      131072
    ],
    [
      32,
      151936
    ],
    [
      64,
      4096
    ],
    [
      64,
      151936
    ],
    [
      64,
      262144
    ]
  ],
  "distributions": [
    "BF16-grid",
    "FP32"
  ],
  "modes": [
    "k20p.8",
    "p.8"
  ],
  "row_count": 44,
  "performance": "upstream get_latency KERNEL and CUDAGRAPH;20warmcalls,20mswarm/50msrep;3stable admission<=10%max8;5fixedB/C/R cycles;<=5%B/Rdrift;all retained",
  "keep_rule": "all correctness/graph passed, disabled-path no material>5% reproducible regression; enabled B32/B64 large vocab latency not regressed>5% in either timing, B64 BF16151936/262144 normal+graph retain improvement; no E2E claim",
  "stop": "any source/resource/mount/import/correctness error ->finallyrestore clone files+stop own clone; no model requests",
  "changes": "integer statistics + static metadata guard only; no sampling/softmax/cumsum/float mask/tie semantics change; no dependencies or autotune search (MetaX fixed4warps <=1024 stats)",
  "PR_main_sync": "current upstream5db6f9e0 merged; sole library-only exports conflict resolved by union; no unrelated source customization"
}

Read operator standard A/B/C/D/E/F, upstream AGENTS/workflow, local key-operator-analysis and performance Skill; use upstream Benchmark.get_latency, not model runner. Tests cover31/32 batch and131071/131072/131073 vocabulary boundaries, k-only, original oracle/tolerance, actual kernel dispatch, no alias/RNG changes and changed-input graph sentinels. PR main conflict is library-only API set; preserve all current main entries and top_k_top_p. Existing main changes are not deployed to source; component files alone tested in isolated original stack.

Upload/unique controller launch script `/tmp/qwen3vl-pr1069-guard-20261106/upload.py` SHA256 `7a0620e2b27e40af2f7b92d9e8e2afbcdac87eccbe51d0aabd8453ca22cd64aa`, creates only new declared root, archives commands/config, no overwrite.

Resource protection: GPU6/7 newly carry unrelated VLLM1052850/1052851. First controller1099192 exited before any source/container/GPU operation. GPU3 PCI0000:5c:00.0 free. New controller central GPU=3 drives resource regex, both visibility vars and runtime PID mapping; explicit static audit before upload/launch. Original failures retained, no unrelated service stopped.
{
  "id": "op-009-shape-guard",
  "host": "mx-59",
  "remote_root": "/public-flash/jinghao/qwen3-VL/20261104-qwen3vl-mx59-topk-topp-pr/op009-guard-prefix-20261106/v2",
  "user_scope": "Add shape guard, preserve semantics, validate correctness/graph/performance, update PR1069; no source model changes",
  "guard": "m>=32 and n>=131072, p present; k-only unchanged",
  "baseline_PR_head": "ce0feddceb0d74a031081e57ce9ff9d24fef3b84",
  "image_lineage": "reuse verified immutable18128 snapshot only after fresh full source+clone static/import/model/mount parity",
  "clone": "qwen3vl-topk-guard1069-20261106",
  "physical_gpu": 3,
  "commands_sha256": {
    "control.py": "b9c22c867c7e4c900ab06602e7735d1b949cf183b54302c7a1539513dbcb298e",
    "backend-baseline.py": "0f3f4eeb160032a6832e0ac214e947bb9fe435570f4de22eb1791f63d4befbb4",
    "tests-candidate.py": "abb9e0f980b4dd64460e40100e82b8c830dbf9bea65d8e9d1e1f7adc63d6845b",
    "mounts.py": "32adacf39859e88ad6e2dad04ada248a00b636c795fed67d34328f5264bec3e3",
    "benchmark-candidate.py": "68961c3dd85a7e24f4406b31a18a7410f08802bcfc95ac15e9f088dd6e99fcb2",
    "component.py": "7469724baa82d01091341b7431277da05f9308b35e53d73d04ab1f55a4c370cc",
    "identity.py": "f50f65e0a8ecf09ed55d57e7831ffcd76efc7b26ad9a1c8ff2ce4de497de2edd",
    "backend-candidate.py": "8e34b2921baadc8c619288027f9ed1e8e14155b176b24d79edcedd671ba06f13"
  },
  "matrix_pairs": [
    [
      1,
      4096
    ],
    [
      1,
      151936
    ],
    [
      8,
      151936
    ],
    [
      8,
      262144
    ],
    [
      31,
      131072
    ],
    [
      32,
      131071
    ],
    [
      32,
      131072
    ],
    [
      32,
      151936
    ],
    [
      64,
      4096
    ],
    [
      64,
      151936
    ],
    [
      64,
      262144
    ]
  ],
  "distributions": [
    "BF16-grid",
    "FP32"
  ],
  "modes": [
    "k20p.8",
    "p.8"
  ],
  "row_count": 44,
  "performance": "upstream get_latency KERNEL and CUDAGRAPH;20warmcalls,20mswarm/50msrep;3stable admission<=10%max8;5fixedB/C/R cycles;<=5%B/Rdrift;all retained",
  "keep_rule": "all correctness/graph passed, disabled-path no material>5% reproducible regression; enabled B32/B64 large vocab latency not regressed>5% in either timing, B64 BF16151936/262144 normal+graph retain improvement; no E2E claim",
  "stop": "any source/resource/mount/import/correctness error ->finallyrestore clone files+stop own clone; no model requests",
  "changes": "integer statistics + static metadata guard only; no sampling/softmax/cumsum/float mask/tie semantics change; no dependencies or autotune search (MetaX fixed4warps <=1024 stats)",
  "PR_main_sync": "current upstream5db6f9e0 merged; sole library-only exports conflict resolved by union; no unrelated source customization",
  "resource_incident": "GPU6/7 newly occupied; first control1099192 exited before source identity/container/GPU; GPU3 fresh same-GPU B/C/R"
}
Upload SHA256 b5fee454a10de589100974c1ca66d76cdee04d2707686197f291c595b2bb7c6c

Independent CPU/read-only final audit script staged SHA256 `cee0d72e04bce7a20a12dd1ab7ae1b99f32ace6567cbc3b35fd973bada928daf`:44pairs/two methods, all5B/C/R rounds, fixedpromotion guard,48bitwise/134UT/24extra replay, actualGPU3, source full identity/models200 and stopped clone.

Audit upload script SHA256 `c21c164cea95fa814d3c56b383a688fc8045168c46b16e8b10308019b1c23e75`; archives unique command only, no GPU work.

134 hardware tests passed, including original91+43guard/oracle/graph tests; separate48B/C bitwise and8capture/24replay passed. pre-commit(all9 PR files),54CIhelper tests,pins,YAML andall12 export checks passed. Static AST audit confirms all original helper functions unchanged except mask and public host dispatch; only addedfunction is integer prefix scan. Source allocation-only newTorchcalls, no compute fallback or dependency change. Merge main5db6f9e0; sole conflict API set union; netPR remains9files. Payload matches hardware-tested backend/tests/benchmark bytes. Local merged tree c45251a451e974af90f9f8c04663d9ae7f7bf7a4; proposedGitHub treepayloadSHA256 5e3d85805c50ee8fa622cdf5cc5374ff60f504bb0bdea7977d8b1c3b91e51de8. No PR write before final promotion audit.

Additional repository artifact/reference gate frozen before execution: after existing controller exits and clone stops, run updated upstream benchmark/test_top_k_top_p_metax.py exactly once on same GPU3/candidate,20 native-reference rows. Modekernel/warmup20ms/repetition50ms, clone inclusive. Require20 metrics and allSpeedUp>=0.9 vs independent Torch reference. This validates submitted benchmark code and standard repo target, does not replace five-round44-row B/C/R comparison. Same immutable private clone, freeGPU/sourceidentity guards, no model traffic, finally restore all3private files/stop clone/source-preserved. commands/native_benchmark.py SHA256 `b8150b7cc1d0332f82bb8985ae169e37b62a1e8291ada32176b3c36f1b90df26`.

All44controlled rows admitted/comparable and independent promotionpassed, normal B/R driftmax1.2243%,graph0.4877%. Original service preserved, clone restored/stopped. One post-controller native-reference gate launch command `/tmp/qwen3vl-pr1069-guard-20261106/upload_native.py` SHA256 `4995af97ee2985cd08b44a677149fb663b76691004abd9f35804e7091e92a8d6`.

Pre-publication: primary frozen controlled44-row guard promotion PASSED, all88 comparisons admitted, maxdisabled-path change1.0123%. Supplementary upstream benchmark pytest2passed/20rows; all8newguarded rows>=1.487xTorch,18/20>=0.9; both B64/V4096 unchanged sentinels0.459/0.471x fail supplemental all-row criterion, retained as native-benchmark-failure.json, not relabeled passed. User explicitly requires preserving small-vocab original path; no unrelated small-path optimization added and no universal reference performance gate claimed. Same-input controlled baseline/candidate/revert proves no new small-path regression. Source-preserved-native passed and ownclone stopped. PR body explicitly discloses inherited reference gap.
Proposed publication: merge commit parents ce0feddceb0d74a031081e57ce9ff9d24fef3b84 +5db6f9e0e17228aa90465993f826916cc8a3edf5; tree c45251a451e974af90f9f8c04663d9ae7f7bf7a4; only9PR paths vs main; non-forced branch update with exact expected head ce0fedd. PR body SHA256 `b3ea108a9f1d7bc5ce19a5f135feb752a81dfd1031423a3b97d84fb1f5350925`.

## Completed result

PR1069 updated to [039f03ed143914ec3a80a21394bf732118a13cf2](https://github.com/flagos-ai/FlagGems-vllm/commit/039f03ed143914ec3a80a21394bf732118a13cf2), Open/ready and mergeable. Merge parents ce0fedd+main5db6f9e0; server tree c45251a451e974af90f9f8c04663d9ae7f7bf7a4 exactly matches local merged tree, netdiff9PR files. Published backend/tests/benchmark content fetched back and exactly matches hardware-tested assets. No live-container code deployment or model restart.

134 hardware UT passed (original91+43),48before/after bitwise cases, extra8captures/24changed-input replay passed; UT14captures/42replays. Input and RNG unchanged. CPUint64 oracle independently validates sum/exclusiveprefix; original independent Torch/FP64 references/tolerances unchanged. Existing sorting helpers AST unchanged; only mask integer statistics, host metadata dispatch and new integer scan differ. precommit all9PR files/54CIhelper/pins/YAML/all12export checks passed.

Guard retained: M>=32 AND V>=131072, with p present. Smaller batch/vocab does not launch prefix kernel or allocate its buffers; k-only bypasses unchanged. Controlled44rows x2methods x5B/C/R rounds alladmitted/comparable. Max B/R drift1.2243%normal/0.4877%graph. Disabled-path maxchange1.0123%. B32/V131072/BF16/k20p.8 normal0.840192→0.820736ms(-2.32%),graph-3.32%; B32/V151936 normal-3.26%,graph-3.54%; B64/V151936 normal1.754368→1.686144ms(-3.89%),graph-3.59%; B64/V262144 normal2.891264→2.790016ms(-3.50%),graph-3.64%. ArbitraryFP32 improves less; allresults retained below. No model/E2E benefit claim or precision gate.

Additional upstream benchmark itself ran once: pytest2passed/20metrics.8/8guarded rows>=1.487x independentTorch;18/20allrows>=0.9. Two unchanged B64/V4096 sentinels0.459xBF16grid/0.471xFP32 failed the supplementary universal-reference criterion; native-benchmark-failure.json retained, not relabeled passed. Same-input controlled B/C/R shows oldsmallpath unchanged (BF16 normal+0.87%,graph-0.15%); source confirms original reductions/no newprefix on smallvocab. User explicitly requires originalsmallshape path, so no unrelated smallshape tuning added; PR explicitly discloses inherited performance gap and universal0.9reference checkbox remains unchecked. Requested guard relative-to-old promotion passed; this is not universal operator-reference performance acceptance. Not an accuracy failure. No hidden gate relaxation or best-row selection.

Both GPUcontrollers exited and restored/stopped their privateclone; final source-preserved-native.json passed samecode/config/PID/models200. InitialGPU6/7resource rejection is historical,0requests/0candidate/GPUcalls; GPU3freshcomparison used throughout. Other services untouched. Rawresults/rounds/commands remain remote in declaredv2root. CI queued after push, not claimed passed.

### Complete normalized performance

Ordinary upstream KERNEL method and standalone-filter CUDAGRAPH method, cloneinclusive; negative percent means lower latency. bf16grid is FP32 with BF16-representable values, p=p-only.8, both=k20/p.8. Historical GPU6 numbers are not baselines here.

| Input | M | V | Mode | Baseline ordinary ms | Candidate ordinary ms | Ordinary change | Graph change |
|---|---:|---:|---|---:|---:|---:|---:|
| BF16-grid | 1 | 4096 | both | 0.118528 | 0.119040 | +0.43% | +0.20% |
| BF16-grid | 1 | 4096 | p | 0.115200 | 0.115456 | +0.22% | -0.02% |
| BF16-grid | 1 | 151936 | both | 0.275712 | 0.276480 | +0.28% | +0.49% |
| BF16-grid | 1 | 151936 | p | 0.269824 | 0.270848 | +0.38% | +0.29% |
| BF16-grid | 8 | 151936 | both | 0.598528 | 0.601600 | +0.51% | -0.30% |
| BF16-grid | 8 | 151936 | p | 0.522752 | 0.519680 | -0.59% | -0.03% |
| BF16-grid | 8 | 262144 | both | 0.589312 | 0.589696 | +0.07% | +0.06% |
| BF16-grid | 8 | 262144 | p | 0.551680 | 0.551936 | +0.05% | -0.80% |
| BF16-grid | 31 | 131072 | both | 0.820352 | 0.819712 | -0.08% | +0.03% |
| BF16-grid | 31 | 131072 | p | 0.757504 | 0.757248 | -0.03% | +0.33% |
| BF16-grid | 32 | 131071 | both | 0.886528 | 0.887936 | +0.16% | -0.02% |
| BF16-grid | 32 | 131071 | p | 0.818944 | 0.818944 | +0.00% | +0.10% |
| BF16-grid | 32 | 131072 | both | 0.840192 | 0.820736 | -2.32% | -3.32% |
| BF16-grid | 32 | 131072 | p | 0.774912 | 0.754944 | -2.58% | -2.63% |
| BF16-grid | 32 | 151936 | both | 0.974848 | 0.943104 | -3.26% | -3.54% |
| BF16-grid | 32 | 151936 | p | 0.903168 | 0.873216 | -3.32% | -4.15% |
| BF16-grid | 64 | 4096 | both | 0.562176 | 0.567040 | +0.87% | -0.15% |
| BF16-grid | 64 | 4096 | p | 0.480512 | 0.485376 | +1.01% | +0.28% |
| BF16-grid | 64 | 151936 | both | 1.754368 | 1.686144 | -3.89% | -3.59% |
| BF16-grid | 64 | 151936 | p | 1.608320 | 1.545728 | -3.89% | -4.16% |
| BF16-grid | 64 | 262144 | both | 2.891264 | 2.790016 | -3.50% | -3.64% |
| BF16-grid | 64 | 262144 | p | 2.640384 | 2.541952 | -3.73% | -3.70% |
| FP32 | 1 | 4096 | both | 0.119808 | 0.120320 | +0.43% | +0.21% |
| FP32 | 1 | 4096 | p | 0.115200 | 0.115456 | +0.22% | +0.06% |
| FP32 | 1 | 151936 | both | 0.279040 | 0.280064 | +0.37% | +0.38% |
| FP32 | 1 | 151936 | p | 0.270080 | 0.271104 | +0.38% | +0.40% |
| FP32 | 8 | 151936 | both | 1.171200 | 1.170432 | -0.07% | +0.42% |
| FP32 | 8 | 151936 | p | 1.150464 | 1.150208 | -0.02% | +0.00% |
| FP32 | 8 | 262144 | both | 1.804288 | 1.804672 | +0.02% | +0.10% |
| FP32 | 8 | 262144 | p | 1.768192 | 1.768448 | +0.01% | +0.09% |
| FP32 | 31 | 131072 | both | 3.119104 | 3.117312 | -0.06% | +0.02% |
| FP32 | 31 | 131072 | p | 3.054592 | 3.052288 | -0.08% | -0.02% |
| FP32 | 32 | 131071 | both | 4.764032 | 4.758656 | -0.11% | -0.10% |
| FP32 | 32 | 131071 | p | 4.698368 | 4.695552 | -0.06% | -0.07% |
| FP32 | 32 | 131072 | both | 2.980864 | 2.957824 | -0.77% | -0.81% |
| FP32 | 32 | 131072 | p | 2.915584 | 2.894208 | -0.73% | -0.72% |
| FP32 | 32 | 151936 | both | 3.439360 | 3.402496 | -1.07% | -1.04% |
| FP32 | 32 | 151936 | p | 3.367808 | 3.333888 | -1.01% | -1.04% |
| FP32 | 64 | 4096 | both | 0.508928 | 0.508288 | -0.13% | -0.09% |
| FP32 | 64 | 4096 | p | 0.499072 | 0.498432 | -0.13% | -0.15% |
| FP32 | 64 | 151936 | both | 6.526720 | 6.456832 | -1.07% | -1.10% |
| FP32 | 64 | 151936 | p | 6.381824 | 6.318336 | -0.99% | -1.01% |
| FP32 | 64 | 262144 | both | 10.928128 | 10.823040 | -0.96% | -1.01% |
| FP32 | 64 | 262144 | p | 10.675968 | 10.573440 | -0.96% | -0.94% |

Artifacts:
- `results/benchmark.json`: `cd4b4af540eab148b4cb5fd435e4b6f945c34d68b7a5420f137014fbd8db4c23`
- `results/component-correctness.json`: `86edc9e2dd7165a28901e935884481ed04b5bd7c5037f3ea9dfbb331a6453707`
- `results/completed.json`: `eaddb648ce98b8f9b07983b91f520f5411124873c0dc81641a0a5cb292b27b06`
- `results/source-preserved.json`: `08c0787a434a3c5e38822d243f63b1e5d4265dcb71a0b3f6ef87a3a5f0ffe589`
- `results/runtime-mapping.json`: `aae94a9f74aa6395028f432dc4842e1ff74baae98bf6b2f65a9e20a4f24715cd`
- `logs/pytest.log`: `cbcc3c8767d48ca95ae7fa41d3c479b8eee6d0c70b7a480a025efc23d3b4eb34`
- `manifests/upstream-benchmark.json`: `1dc8bcb27fabac9d9f96f5cec3b500ec544b2682937d57f0ac844ed517a5e758`
- independent-final-audit.json: `10c712e23e8a7dc3a7b28f24eee114c1d4f62c848a4d0bab797b62ae38df9db2`
- upstream-native-benchmark.json: `73e6013767425fcb1560ef556362bd2d1b06675ab9524f6d1e6ff65589689732`

Latest remote CI: rule-check679 succeeded; basic-ci2165 in_progress. Local temporary checkout now clean at published039f03ed, all tested/published bytes identical. No CI completion claim for basic-ci.
