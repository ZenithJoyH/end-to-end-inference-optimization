# op-024: P16K graph QSA score bound 4352

## Direction and status

- Classification: `operator/improve`.
- Status: `complete_valid_failed`.
- Target: remove P16K FULL Decode graph score-capacity waste left by op008, which still captures against `max_model_len=80000` and therefore uses the static 8448-column cap.
- Mechanism: change only `VLLM_FL_QSA_STATIC_SCORE_COLUMNS=8448` to `4352` on an isolated P16K service; no source edit and no max-model-len change.
- Milestone: P16384/D128/C64/N64, three warmup plus three measured rounds for fresh A/B/R.

## Evidence and safety boundary

Existing operator evidence shows 4352 covers `(16384+1024)/4` and improves the complete Decode QSA transaction by 13.64% versus 8448 with matching selected sets, BF16 downstream output and graph capture plus two replays. Non-capture P16K Prefill/Mixed already derives the actual CPU-metadata bound under op008; this experiment isolates the remaining FULL Decode graph waste.

The candidate is not a general service configuration. P32768/D1024 requires 8448 columns, and the current graph key has no sequence-capacity dimension. Candidate launch/request validation must reject `input_len + output_len > 17408`; the service must never receive P32K or unknown-length traffic. `max_model_len` stays 80000 to preserve the single-variable comparison.

## Frozen A/B/R and gates

- A: static score columns 8448.
- B: static score columns 4352.
- R: static score columns 8448.
- PPU0–7/8031, fresh sequential services; retained 8030 remains idle, identity-frozen and healthy.
- Before measurement, freeze a comparison contract that permits the one semantic environment change and normalizes or explicitly permits role-specific non-semantic evidence metadata. Do not repair it after measurement.
- Each arm must prove readiness, all 11 FULL Decode graph keys, two changed-input replays, expected effective score width/path, exact source identity, zero failures and stable warmup.
- A/R output-throughput drift must be at most 1%.
- B relative to the A/R control must improve output and total throughput by at least 1% and duration by at least 1%; median/P99 TTFT, TPOT, ITL and E2E may not regress more than 5%.
- Any length-bound violation, graph miss/fallback/recapture, source drift, 8030 identity change, request failure or invalid comparator stops the experiment. Promote to exact P16384/D1024 only after a valid D128 comparator pass.

## Rollback

Stop only the frozen 8031 root PID and verified descendants, restore static 8448 in the next fresh service, and verify source SHA, readiness, all graph keys and changed-input replay. No reverse source patch is required.

## Result

The fresh sequential service67/68/69 A/B/R completed all 18 rounds with 64/64 requests and zero failures. Warmup output-throughput spreads were 0.1555%, 0.1773% and 0.0522%.

| Arm | Score columns | Duration (s) | Output tok/s | Total tok/s |
|---|---:|---:|---:|---:|
| A | 8448 | 156.559819 | 52.325048 | 6749.931145 |
| B | 4352 | 156.555443 | 52.326510 | 6750.119811 |
| R | 8448 | 155.765050 | 52.592029 | 6784.371718 |

B versus the A/R midpoint was -0.251681% for output and total throughput. Duration reduction was -0.251667%, meaning B was slightly slower. A/R output drift was 0.50894%, and every median/P99 TTFT, TPOT, ITL and E2E regression stayed below 1%, so the control and guard evidence are valid.

The maintained comparator returned `failed`, not `incomplete`; its only issue was output-throughput improvement below threshold. The actual cross-role changed path remained exactly `/launch_config/selected_environment/VLLM_FL_QSA_STATIC_SCORE_COLUMNS`. Comparator SHA-256 is `097ac7bb7e9a71341b1e1488bcd3566f288eca1f87c21f44c5f2d54a8a6b2ece`.

All arms proved the 11 FULL Decode graph keys, two changed-input replays, the expected 8448/4352/8448 score width and zero QSA graph fallback or recapture. Fixed replay outputs matched across arms, and the source fingerprint remained `e1ac465db82b210f8e3d6aaf7bc2a8f908bd6d2bfb905c2f2696c482e2531560`. Random long-context generated-text exact hashes differed as a post-hoc diagnostic; this was not a frozen decision gate and does not override the fixed replay evidence.

Original experiment decision: reject 4352, keep 8448, and do not expand this candidate to D1024. Final decision SHA-256 is `1b5199b3699a430739108810bf91941dda9d59b786b81b9e1254dfea081fe242`. Evidence root is `/mnt/nfs/users/jinghao/qwen3.8-flash/20260919-qwen38-flash-next-ppu-e2e/op024-p16k-qsa-graph-score-bound-4352/fresh-abr-service67-69`. Cleanup released 8031 and PPU0-7; retained 8030 stayed unchanged and healthy.

Current decision: the comparison still rejects 4352 versus its historical 8448 control, but [rb-001](rb-001-qsa-score-bound-rollback.md) subsequently removed all static QSA score bounds after formal accuracy evidence. Therefore “keep 8448” is historical only and does not describe the current candidate.
