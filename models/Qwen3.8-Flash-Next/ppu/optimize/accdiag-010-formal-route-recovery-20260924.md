# accdiag-010: recover formal per-doc dual-service routing

Issue: `acc-issue-004-gpqa-completed-wrong-answers`; formal acc-010 remains 174/198 below 0.88. This is read-only log correlation, not a replay or score correction. Existing frozen sources: acc-010 `evaluation/formal-run.log`, `evaluation/proxy.log`, recovered 198-item HTTP/sample index from accdiag-008, and the archived proxy source `commands/dual-service-proxy.py` whose backend 0 is port 8000 and backend 1 is port 8010.

Preliminary doc 168 check: evaluator response at 2026-09-23 03:54:17, `use 3019.36s`, aligns with proxy completion at 03:54:17.520, `elapsed=3019.357`, `backend=0`. Thus formal doc 168 ran on **8000**, not on the untouched 8010 service used for later C8 long replays. Any comparison to 8010 is cross-endpoint and cannot isolate concurrency. Current 8000 was restarted during later diagnostics, so even a new 8000 replay is not the original formal process identity.

Frozen next action: parse exactly 198 evaluator response log lines using the previously validated doc-id/line index; match each to exactly one proxy completion by response timestamp and elapsed duration, with strict tolerances and one-to-one uniqueness. Record unmatched or ambiguous cases instead of guessing routes. Only if fully matched, summarize score/cap/wrong-completed counts by backend and save `formal-http-recovered/route-match.json` as a new external artifact. Do not edit the original formal logs, samples, services or proxy.

## Result

Status: `completed_full198_route_recovered`. The frozen script `docs/cases/20260919-qwen38-flash-next-ppu-e2e/commands/accdiag010-recover-formal-route.py` matched all **198** evaluator responses one-to-one to proxy completions. For 196, timestamp/duration and unused-proxy-line exclusion yielded a unique match. Two responses finished in the same second with close durations; their evaluator and proxy completion orders agreed, and their client-minus-proxy durations were within 0.1 second. The maximum absolute duration difference across the 198 pairs is 0.041 second. The exact per-doc mapping, method and line numbers are preserved in `formal-http-recovered/route-match.json`.

| Formal backend | Port | Unique docs | Strict correct | 60K length caps | Completed wrong |
|---|---:|---:|---:|---:|---:|
| 0 | 8000 | 100 | 87 | 4 (`12,32,64,88`) | 9 (`30,76,90,102,106,140,160,164,168`) |
| 1 | 8010 | 98 | 87 | 3 (`71,127,145`) | 8 (`17,69,89,113,147,157,167,171`) |

This sums to the frozen 174/198 result, seven caps and 17 completed misses. Doc 168 is a **unique** match to backend 0/8000: evaluator 03:54:17, `use 3019.36s`; proxy line 392 at 03:54:17.520, `elapsed=3019.357`. The raw proxy source maps backend 0 to port 8000. Thus accdiag-008/009 C8 long replays on 8010 were **cross-port comparisons**; they cannot isolate concurrency or the original formal 8000 process. Later diagnostics restarted 8000, and its original pre-diagnostic `LD_LIBRARY_PATH` was not preserved, so current 8000 is also not an exact process-identity replay of formal acc-010.

The two formal replicas do not show a gross one-sided accuracy collapse: 87/100 and 87/98 correct, with 4 versus 3 caps. These are different routed item subsets under the same formal run, **not** paired per-item service A/B; the small score-rate difference is not causal evidence about card group or instance quality. No service, evaluator, proxy or frozen score was changed.

External artifact: `/mnt/nfs/users/jinghao/qwen3.8-flash/20260919-qwen38-flash-next-ppu-e2e/accuracy/acc-010-full-gpqa-dual-user-services-20260923/diagnostics/accdiag-008-current-output-replay-20260924/formal-http-recovered/route-match.json` (73,635 bytes; SHA-256 `d62a7de59378b297a7e9fdb37b70c34158225431d3bc9b468a721de653610715`).
