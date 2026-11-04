# acc-009: dual-service full GPQA with QSA static bound removed

Status: `failed_gate_rollback_retained`.

Accuracy mode: `formal-gate`, used as the original-scope revalidation for `acc-issue-003-full-gpqa-reasoning-length-cap`.

This experiment changes one launch variable relative to failed `acc-008`: both TP8 replicas omit `VLLM_FL_QSA_STATIC_SCORE_COLUMNS=8448`. Model weights, tokenizer, graph mode, TP8 topology, two-replica routing, Plugin/FlagGems source, MoE tuned config, native `mm/mm_out` selection, max model length, scheduler, prefix-cache state, evaluator, task, prompts, sampling, concurrency, maximum generation length, metric, and threshold remain frozen.

Frozen formal contract:

- task `gpqa_diamond_generative_cot`, 198 unique questions;
- strict-match exact match threshold `0.88`;
- `temperature=1.0`, `top_p=0.95`, `top_k=20`, `min_p=0.0`;
- `presence_penalty=0.0`, `repetition_penalty=1.0`;
- API adapter seed `1234`, `max_gen_toks=60000`, evaluator concurrency `64`;
- ports 8000 and 8010, TP8 per replica, logical proxy port 8041;
- prefix caching disabled and graph mode `FULL_AND_PIECEWISE`.

Success means a valid strict-match score `>=0.88`. A lower score remains gate-blocking even if truncations decrease. Output-health changes will be reported separately from the numerical gate.

External artifact root: `/mnt/nfs/users/jinghao/qwen3.8-flash/20260919-qwen38-flash-next-ppu-e2e/accuracy/acc-009-full-gpqa-dual-qsa-unbounded-20260922`.

Progress heartbeat `qwen3-8-acc009` was deleted after terminal completion.

Both live replicas were verified to omit `VLLM_FL_QSA_STATIC_SCORE_COLUMNS`, use the expected PPU0–7/PPU8–15 split, retain the frozen provider and MoE settings, disable prefix caching, and complete full graph capture. Two task/data provenance captures matched. The first preflight attempt correctly stopped before model evaluation because the generated service manifest omitted the required observed `flaggems_vllm_installed` boolean; its evidence is preserved under `evaluation/preflight-failed-attempt-1/`. The manifest generator was repaired to record `true`, the second preflight passed, and the formal runner started all 198 requests with an empty per-run cache.

The full run completed 198/198 unique questions with no API failure. Strict-match was `174/198 = 87.8788%`, below the frozen `0.88` threshold by one correct answer, so the formal verdict is `FAIL` and no gate was issued. Eight samples reached exactly 60,000 completion tokens with no final answer, versus 19 in acc-008. The unbounded candidate recovered 13 previously incorrect questions and lost six previously correct questions, a net gain of seven.

Result SHA-256: `11d7ed2b5b1e44b3404e39d70e9c502ce0de9260dae26742b7c29cb48da5a7ff`. Samples SHA-256: `ff132d2c74a6f009222f944e1ee5118521aa902b12631d79ea83a1aac0deac3f`. Score-verdict SHA-256: `447def37efa637a75ca06928934811dd2b943a71599202a03476b9a50e6682fe`.

The user selected rollback. The unbounded service state is retained as [rb-001](rb-001-qsa-score-bound-rollback.md); the QSA bound is no longer part of the active candidate. Formal accuracy remains blocked and the next bisection must start from this unbounded state.

Planned bisection after this run if it fails: preserve the exact formal contract and move to the next high-risk current-combination boundary, beginning with the QSA runtime implementation versus the last adaptation path, followed by the MoE tuned config and native `mm/mm_out` provider selection. Each step requires a new service identity and formal evidence; no performance promotion resumes before a passing gate.
