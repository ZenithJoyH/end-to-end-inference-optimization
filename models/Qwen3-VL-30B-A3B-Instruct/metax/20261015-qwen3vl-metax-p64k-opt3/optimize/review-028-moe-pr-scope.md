# review028: Follow-up review of PR943 scope and markers

User asks whether repeated markers are necessary and whether the MoE changes are reasonable or can be improved. Preserve the ongoing PR task; prioritize restoration of8111, which completed successfully before the review. No additional GPU work or production-source change is made for this read-only review.

## Runtime/validation handoff

pr027 completed49GPU cases,31mathematical references,21captures/42changed-input/routing replays; dedicated TP2 service passed11HTTP requests including C8, with exact source/stage proof and>=16replays in each worker. Source8111/qwen3vl-opt9 was restored from the saved configuration; argv, runtime environment whitelist, repository states/hashes, cwd/log match exactly and smoke returned42. Receipt results/pr027-source-restored.json SHA256872bcfc0ed5a41e8f47d7bdfaecf5a7e6aa6d9da6852ad315606ec9d845b922d. The dedicated service is stopped; its container remains available, idle.

## Marker conclusion and minimal correction

Module-level pytestmark already marks every test. The upstream checker currently searches only function decorator AST, so five duplicate function markers were unnecessary. Reduce to one explicit function marker solely for this CI compatibility, retaining the module marker and all test bodies. Upstream checker passes locally. No new test/perf file is introduced, no CI check is weakened and the production operator hash remains bc655dbc521538710b054c2af8f496ed45d0d214f0d71e9ea3fdf8731aa7605b. A generic checker fix that understands module-level pytestmark would be the longer-term cleaner alternative, but is outside this focused PR.

## Reproduced review findings

1. **P2: Tuning eligibility is wider than measured inputs.** Current getter keys only E128/logicalN384/dtype, not H or top-k. Actual try_get_optimal_moe_config returns the same measured table for H4096/topk4 as for tested H2048/topk8. This is an unvalidated performance choice, not a proven numerical failure. Device/capacity selection is also absent from this table path.
2. **P2: dtype=None does not mean plain half.** Actual _get_config_dtype_str returns None for OCP MX schemes. A packed OCP example w1=(128,1536,1024),w2=(128,2048,384),topk8 thus enters the measured half table before dequantization. This route was reproduced at host-selection level; OCP GPU numerics were not tested. Restrict measured half tuning to actual fp16/bf16 and full logical shape, leaving nonmatches to the existing selector.
3. **P2: Shared-memory estimate uses paired tiles after pairing is disabled.** With64KiB and default E64/M8192/N1024/K2048/topk8/BF16 GEMM1, actual get_default_config selects BM128/BN128/BK64/stage1/PAIR_GATE_UP_DOT=False. It estimated two weight tiles before setting PAIR false. Under the ordinary-tile estimate, one stage is32768bytes and two fit65536bytes. This proves conservative selection; it does not prove stage2 compiles within the final compiler allocation or is faster. Determine the actual paired/regular path first, then estimate/cap stages for that path and verify on hardware.

The stage-specific optimization itself is sound for the tested target. Both GEMMs reuse one alignment, so their BLOCK_SIZE_M must agree. An exhaustive0..65536host sweep confirms current tables agree throughout; no present mismatch was found. Preserve this invariant when simplifying or retuning.

A simpler design is to express measured profiles in the existing MetaX get_default_config(...,gemm_stage=...) path with a complete supported shape/dtype/device boundary, rather than extending the embedded-table lookup with a second shape-specific table protocol. That would require explicit testing of the is_embedded/default execution branches; do not treat this as a source-only cosmetic move. Shared-memory fallback logic also affects models beyond this measured shape, so its scope deserves independent validation or a separate focused change.

## Decision boundary

The target correctness/graph checks passed; this does not validate all newly matched shapes/quantization/device choices. In response to the user's explicit review steering, keep PR943 Draft while these production review findings are resolved. Original request to mark ready remains pending for that reason; do not claim it was completed. Do not alter the restored runtime, tuning values, blacklists, sampling or gems-opt just to tidy the PR. Review artifacts are external controls review_host.py/review-host.json under commands/pr027-marker-gpu-graph-20261019.

## Published marker simplification

Commit [514142c304fb9f9034269be4280c3b7cd5686f34](https://github.com/ZenithJoyH/FlagGems-vllm/commit/514142c304fb9f9034269be4280c3b7cd5686f34) removes only4redundant decorators, with a normal expected-head update. The final test diff against upstream is one added CI-compatibility marker line; production MoE bytes remain unchanged. The local current marker checker and formatting passed. PR body now documents verified GPU/graph/restore results and the reproduced review concerns; it remains Draft. No runtime restart or GPU job was initiated for review028.

## Resolution

User authorized remediation and promotion in the next turn. [pr029](pr-029-moe-scope-cleanup.md) resolves the reproduced scope/memory issues, preserves the minimal marker, verifies the exact final operator and TP2 service, restores8111 unchanged, passes final MetaX CI and marks PR943 Ready at090ef1d. Earlier Draft status above describes the review handoff, not the final PR state.
