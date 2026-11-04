# acc-008: current-candidate dual-service full GPQA

Status: `failed_gate_diagnosis_running`.

Accuracy mode: `formal-gate`, using the user's explicit two-service design. Two identical TP8 graph services will run from `qwen3.8-flash-opt-candidate-20260919` on PPU0–7 and PPU8–15. The 198-question `gpqa_diamond_generative_cot` set is distributed through the verified dual-service request path; it is one full evaluation of the same current candidate, not two different candidates.

Frozen generation settings:

- `temperature=1.0`
- `top_p=0.95`
- `top_k=20`
- `min_p=0.0`
- `presence_penalty=0.0`
- `repetition_penalty=1.0`
- `max_gen_toks=60000`
- evaluator concurrency 64, `limit=0`, expected unique questions 198

The formal threshold remains 0.88 on `exact_match,strict-match`. The service configuration retains graph mode, TP8, max model length 80000, max sequences 64, max batched tokens 4096, disabled prefix caching, the retained M64 tuned configuration, QSA static bound 8448, async scheduling, and native `mm/mm_out` provider selection.

External artifact root: `/mnt/nfs/users/jinghao/qwen3.8-flash/20260919-qwen38-flash-next-ppu-e2e/accuracy/acc-008-full-gpqa-dual-service-current-candidate-20260922`.

The full run completed and its progress heartbeat `qwen3-8-gpqa-2` was deleted. A separate diagnosis heartbeat `qwen3-8-qsa` monitors the bounded-versus-unbounded reproducer.

Because the repository's standard gate schema binds one service instance, this explicit dual-service run must preserve both live identities and the routing evidence. A valid full score will be reported as full numerical GPQA evidence; a consumable single-service accuracy gate is issued only if the maintained acceptance tool can bind the complete dual-service identity without weakening its checks.

## Live binding

The formal preflight passed and the full evaluator started with run UUID `a8e7870e0dbe43fb854d042f0ed0e1ce`.

- Service A: port 8000, PPU0–7, PID/startticks `3923895/275928055`.
- Service B: port 8010, PPU8–15, PID/startticks `3923905/275928058`.
- Logical proxy: port 8041, PID/startticks `1455/275956587` in `qwen38-eval-e2e-20260919`.
- Combined service manifest SHA-256: `5aece6fc1321b393452cbf70293d6bf941cd1392611324b8af6e9a0b60bbf430`.
- Runtime evidence SHA-256: `05262e9241f170fef82031a2586e9378bf4f87a6f16e65622c28e7a0a56a38b2`.
- Frozen contract SHA-256: `4181f11f22ba7e83fcce46c0ac8f35974bac36512537f274f8f5e6c9d87dd8ea`.
- Task/data provenance SHA-256: `f313e85b0eff524a60ed5542f57bef3950b3e9ed426c870326369a763ac85995`.
- Skill bundle SHA-256: `a691e98289a9562aa706008d9fcec955d8816ab4b14a18ba35bb4b68833cee00`.

The full run completed 198/198 unique questions. Strict-match was `167/198 = 84.3434%`, below the frozen `0.88` threshold; flexible-extract was `55/198 = 27.7778%`. The score verdict is `FAIL`.

## Accuracy diagnosis

The 19 rows reported as timeout were not transport, proxy, HTTP, worker-crash, or request-timeout failures. All 19 returned HTTP 200 with `finish_reason=length`, exactly `completion_tokens=60000`, reasoning text present, and final `message.content=null`. The evaluator's `parse_generations()` converted this missing final answer to `<TIMEOUT>`. Thus the confirmed direct failure mode is a generation-length cap after reasoning consumed the entire allowance.

- Timeout doc IDs: `8,12,15,32,48,64,71,79,88,90,93,94,115,121,127,130,145,147,185`.
- Non-timeout score: `167/179 = 93.30%`; only 12 completed outputs were wrong.
- Subject concentration: 16/19 timeouts are Organic Chemistry, two Molecular Biology, and one general Chemistry.
- No API timeout, proxy 5xx, service crash, empty raw HTTP response, or device failure was observed.

The strongest suspected regression is the retained `VLLM_FL_QSA_STATIC_SCORE_COLUMNS=8448` optimization. QSA compression ratio is four, so this static score width covers approximately 33,792 visible tokens. The FlagGems operator contract requires the caller-provided width to cover every visible compressed block, while GPQA permits 60,000 generated tokens. Stratifying by that boundary gives:

| Run | total tokens <=33792 | total tokens >33792 |
|---|---:|---:|
| Historical identical user-sampling run | 165/175 correct, 0 capped | 11/23 correct, 8 capped |
| Current bound8448 candidate | 164/175 correct, 0 capped | 3/23 correct, 19 capped |

Below the boundary the candidate changed by only one question; above it the candidate lost eight correct answers and all 19 current caps occur there. The historical identical sampling result was `176/198 = 88.8889%`; its eight capped doc IDs are a subset of the current 19. Of the 11 new caps, nine were historically correct and two historically wrong, explaining the net `176 -> 167` score drop exactly. This makes the bound a high-confidence suspected optimization regression, but not yet a confirmed root cause because prior independent graph replicas also showed trajectory divergence.

Diagnosis `accdiag-001-qsa-bound-long-gpqa-20260922` kept port 8010 unchanged and ran port 8000 with only `VLLM_FL_QSA_STATIC_SCORE_COLUMNS` removed. Five historical-correct/current-capped requests (`12,15,64,121,127`) were replayed identically to both services with the frozen sampling parameters, the API adapter's actual seed 1234, and max 60,000 tokens.

The A/B completed 10/10 without request errors:

| Role | Final answers | 60K length caps | Correct |
|---|---:|---:|---:|
| bound8448 | 1/5 | 4/5 | 0/5 |
| unbounded | 3/5 | 2/5 | 0/5 |

Removing the bound changed docs 12, 64, and 121 from a 60K cap to normal `finish_reason=stop` at 43,584, 37,877, and 46,959 completion tokens. Doc 127 capped on both sides, while doc 15 moved in the opposite direction: the bound side stopped at 57,115 tokens and the unbounded side capped. All emitted answers were wrong. Therefore `8448` is confirmed to amplify long-reasoning truncation for some requests, but it is not a sufficient explanation or fix for the failed score. The next faithful test is a full 198-question dual-service formal run with the bound removed from both replicas; this determines the net score before bisection proceeds to the remaining current-combination changes.

Primary evidence:

- Result: `/mnt/nfs/users/jinghao/qwen3.8-flash/20260919-qwen38-flash-next-ppu-e2e/accuracy/acc-008-full-gpqa-dual-service-current-candidate-20260922/results/Qwen3.8-Flash-Next-current-optimized-dual-full-gpqa-20260922/a8e7870e0dbe43fb854d042f0ed0e1ce/gpqa_diamond_generative_cot/Qwen3.8-Flash-Next/results_2026-09-22T04-13-39.526414.json`
- Samples: same directory, `samples_gpqa_diamond_generative_cot_2026-09-22T04-13-39.526414.jsonl`
- Verdict: `/mnt/nfs/users/jinghao/qwen3.8-flash/20260919-qwen38-flash-next-ppu-e2e/accuracy/acc-008-full-gpqa-dual-service-current-candidate-20260922/evaluation/score-verdict.log`
- Diagnosis: `/mnt/nfs/users/jinghao/qwen3.8-flash/20260919-qwen38-flash-next-ppu-e2e/accuracy/acc-008-full-gpqa-dual-service-current-candidate-20260922/diagnostics/accdiag-001-qsa-bound-long-gpqa-20260922`
- A/B summary: same diagnosis directory, `results/summary.json`
