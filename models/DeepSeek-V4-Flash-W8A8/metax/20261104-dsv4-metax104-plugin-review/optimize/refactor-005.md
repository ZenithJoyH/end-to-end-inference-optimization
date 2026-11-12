# refactor-005：收敛主线上的 FGV 改动

用户要求解释并收敛改动量。此前主线迁移完整保留38项历史整改，并非最近SiLU新增38项；大块来自Plugin数值kernel迁移。当前源树与refactor004一致，API1040582/ticks1217076548、health200。只在独立候选准备收敛，当前运行服务不动。

First bounded reduction: {
  "experiment_id": "refactor-005",
  "status": "source_convergence_prepared",
  "scope": "Reduce active FGV patch on pinned main27011d53; preserve public APIs, active math, tests, running service; no commit/push",
  "baseline": "refactor-004/mainline01/final-result02",
  "remote_directory": "/public-flash/jinghao/deepseekV4/20261104-dsv4-metax104-plugin-review/refactor01/converge01",
  "actions": [
    "Remove stale DSV4_INTEGRATION.md from repository patch; keep full prior artifacts",
    "Restore unused public gather implementation and its independent added tests to upstream, preserve upstream tests",
    "Remove private decode_half_d=False experimental branch and unreachable full-dimension kernel; fixed deployed policy is True",
    "Restore upstream import ordering and unaffected common QNorm host wrapper, retain runtime specialization fix required by vendor kernel"
  ],
  "validation": [
    "AST equality for all retained kernels",
    "Partial-evaluation equivalence for default selected decode dispatch",
    "CPU metadata-only launch transcript equivalence and error cases; no GPU libraries imported",
    "YAML/public API/test coverage and format checks",
    "Whole source/index guards and current API identity/health"
  ],
  "limits": "No latest-mainline GPU/graph/formal/performance result; do not transfer old validation to slim candidate"
}

First reduction source candidate: 38 files +6144/-530 to 35 files +5649/-511 (495 added lines removed). Remaining 23 production Python, 2 configs, 7 tests, 2 benchmarks, 1 contract doc. No active core tests removed. All 1338 retained JIT ASTs unchanged apart from independent gather restored to exact upstream; default-policy dispatch matches at AST and 34 metadata/launch/error cases, no GPU libraries imported. Formatting black24.8/isort5.12 profileblack/flake8 7.1 passed for 3 edited production files. Earlier CPU AST audit initially included intentionally reverted gather; corrected scope and separately proved exact upstream restoration, without weakening active-path assertions. Local temporary git rm refused staged new doc, so archived the duplicate outside candidate and removed only that copied file; remote untouched at that stage.

Install source-only convergence command: commands/apply-convergence01.py; SHA and frozen artifacts: {"apply-convergence01.py": "16129c105cb6bbf4c06ee6a2e345efa5c0acd43d32e482d8aa38b52080d975a8", "candidate-manifest01.json": "e90e9f08a9311444cc77cb466c7b80c03c9e62cf5e43e87d4b2cfd0bcee81857", "slim-mainline01.patch": "9cc572e1ebbb9ae8e536d17e7800c2a6f1fd7b57124d8d7247a90adb9f9923e7", "cpu-review01.json": "c2ddfa103b111c9258173b91027121ea8b180bd270224577717415469da9ac53", "scope-audit01.json": "4fec4d0b7414585355c3209cd1be09a78c45aa5e4cba8b067e8e73dd7a9ad27a", "style01.json": "21c5a4b17fc9d4c3d9d44195803979a6f6fce4c46df2973af556589c8e5f461c", "check-convergence01.py": "49f9627f42e19135718bf2f6cd03291285d38cedb9841b5385670cebca8daeca"}
Only 7 files in the already-installed new mainline tree change; current API must still be1040582/ticks1217076548 (created before that new editable tree existed), otherwise guard blocks. Back up old index/patch and those7 files, then source guard and branch to refactor/dsv4-main-slim-20261105. No restart/importGPU/testGPU/dependency/commit/push. Full numerical/graph/model/performance on new mainline remains not_run; source convergence does not grant a gate.

Final installed-source result: source_patch_converged_pending_gpu_validation. Same private source directory /opt/dsv4-sources/FlagGems-vllm-main-20261105, branch refactor/dsv4-main-slim-20261105,35 status entries fully staged,0 unstaged/untracked. Scope: 38 files changed, 6144 insertions(+), 530 deletions(-) -> 35 files changed, 5649 insertions(+), 511 deletions(-). Result SHA aada544d2811a78b181ae0d7d56f00e1ca6645f2ef98b10f6eb7b7d6aa183434, manifest e90e9f08a9311444cc77cb466c7b80c03c9e62cf5e43e87d4b2cfd0bcee81857, patch 9cc572e1ebbb9ae8e536d17e7800c2a6f1fd7b57124d8d7247a90adb9f9923e7. Original7 files/index/full patch kept at /public-flash/jinghao/deepseekV4/20261104-dsv4-metax104-plugin-review/refactor01/converge01/backup. API1040582/ticks1217076548 and argvSHA unchanged,18001health200, no service action/commit/push. This completes source convergence only, GPU/graph/formal/performance remain not_run for latest-mainline slim source.

Remaining added-code concentration: sparse MLA decode1499 + prefill843 + mHC795 + indexer decode411 + prefill305 =3853 lines, about68% of added lines. These are numerical implementations/validated-path variants migrated from Plugin, not duplicate public wrapper exports; replacement by mainline implementations requires contract/shape/numerical/graph evidence rather than deleting them to lower file count. GDN import-time compiler mutation removal is retained because the package imports the module even in non-GDN models.

Further boundary debt: indexer_dequantize_fp8 is an explicit reference.pytorch decomposition still wired from Plugin. Removing its public API alone breaks registration. Any further relocation is a coordinated Plugin reference change and must be tracked separately; current source/format audit is not full PR acceptance.
