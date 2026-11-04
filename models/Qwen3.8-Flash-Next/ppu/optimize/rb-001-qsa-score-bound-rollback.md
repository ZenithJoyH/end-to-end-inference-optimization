# rb-001: QSA score-bound rollback

Status: `applied_runtime_and_candidate_decision`.

This rollback supersedes the retention decisions for `op-006-qsa-static-bound8448` and the dependent active use of `op-008-qsa-runtime-score-bound`.

## Scope

The retained candidate no longer sets `VLLM_FL_QSA_STATIC_SCORE_COLUMNS`. With the current Plugin source, `_qsa_runtime_score_columns(None, ...)` returns `None`; FlagGems then selects `columns = capacity`. Thus the optional score-bound code is dormant and execution uses the original unbounded score width. No model weights, tokenizer, vLLM source, MoE tuning, native `mm/mm_out` selection, graph mode, scheduler, or cache setting changed.

This is a functional rollback of the QSA bound, not deletion of the optional guarded source implementation. Keeping the dormant code preserves prior evidence and avoids changing a shared imported source while other bisection work remains. It is no longer part of the active candidate or future launch contract.

## Evidence and decision

The bound candidate `acc-008` scored `167/198 = 84.3434%` with 19 generations capped at 60,000 tokens. The otherwise-identical dual-service unbounded run `acc-009` scored `174/198 = 87.8788%` with eight caps. Removing the bound therefore recovered seven net correct answers and reduced caps by eleven, although it remained one correct answer below the frozen 88% gate.

The full runs also show expected sampling-path movement: 13 previously incorrect questions became correct while six previously correct questions became incorrect. The score comparison proves that the bound is harmful in this formal scope, but the remaining gate failure is not declared resolved.

Current ports 8000 and 8010 were read back from `/proc`; neither process environment contains `VLLM_FL_QSA_STATIC_SCORE_COLUMNS`. Both services remain graph-ready and HTTP healthy. The acc-009 service manifest SHA-256 is `39ffb3dbd5df6804e0129533db4e142c957d5992f705abefec6266bdf830758f` and runtime evidence SHA-256 is `7ace250de0e8408a778c6fa2b571d3f0e9b142c96c87416cefcd4b06b7d2a821`.

## Consequences

- `op-006` is rejected and rolled back from the retained candidate despite its prior P4K performance gain.
- `op-008` remains in source only as a guarded, inactive implementation; it provides no active runtime score bound without the removed environment setting and is not credited in the retained combination.
- Historical performance and correctness artifacts remain valid records of the configurations measured, but cannot represent the current candidate.
- Formal accuracy remains gate-blocking at `174/198`; performance optimization may not resume until the remaining one-question gap is diagnosed and a new formal result passes.

External evidence root: `/mnt/nfs/users/jinghao/qwen3.8-flash/20260919-qwen38-flash-next-ppu-e2e/accuracy/acc-009-full-gpqa-dual-qsa-unbounded-20260922`.
