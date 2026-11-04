# acc-004: current opt15 GPQA and ERQA C32

User authorizes both full datasets again at C32. GPQA retains most recent65536 cap; ERQA retains prior18000 cap (stated before execution). Each once sequentially; strictGPQA64 and nativeERQA40 unchanged. Currentsource1718819/ticks1149208177 confirmed same source/config/defaultT.7P.8K20rep1/prefixON/GPU0,1.

Mode local inference-accuracy-evaluation/formal-gate; bundle1ed06a57f1f6e1ef39fb7fd872f579122b098a18f0255ade0a1160d6432c2b66. Existing evaluation/accuracy tools and original SHA runner, official v1 evaluator/ERQA native flagevalmm reused read-only. New unique root under same parent mount; no container/source change.

Remote root: `/public-flash/jinghao/qwen3-VL/20261028-qwen3vl-opt15-c64-default-accuracy/c32-gpqa65536-erqa18000`. CPU prepare proves current idle/PID/source; actual GPQA198factory upstream exact to latestC64/65536; native provenance only concurrency metadata64->32; ERQA original400/630images/score source and original factory checks.

Nine normal smoke/C8 requests thenGPQA198/C32 andERQA400/C32. Native retries/timeouts unchanged;GPQA controller12h/ERQA6h. ValidGPQA low score still completesERQA. Source left running; finally only ownproxy stops. Native questionIDs coverage, not unique messageSHA. Prefix cache retained/no requestseed means concurrency/batch/warmcache affect comparison; no isolated numerical causal claim. Graph onlycurrentstartupcapture+normalgraphsmoke, no directreplay counter.

Execution: exclusivearchivebootstrap.py -> bootstrap -> prepare(CPUonly) -> preparedcheck -> unique start_controller.py. No oldscripts rerun. No source restart/clearcache/performance/scoringrule changes.

Monitor qwen3-vl-opt15-c32 every30min, terminate after both datasets and service finalaudit.

## Command SHA256
- bootstrap.py `fd2c217cef0a2afd422c36f8fa21122282bac94d689545d444c4ff50c62498b1`
- default_sampling_proxy.py `fa882649c300d40aeab87cbcae6fa4243750597572e12297b284f2af276cd4c0`
- proxy_cpu_test.py `a4cc4c2d27fc2788d1980af019cea26e6d268139506b0a16a09ec7e617b1819d`
- collect_current.py `9c6e4d35d5f8a9fb8895fa3f9118bc927ffcbb6d68cd4b19c96fea47b128350d`
- accuracy_controller.py `e605d5bf735d3c0ba67d4e1eb76984167be75f30b3ca7ec83d82164873592d6c`
- payload_parity.py `2259f89f19e758e701683936c1337939d957189f890824fc01022054978f0b10`
- start_controller.py `9a145ab2373c4c8e7b12be103e04cc438f17148bb3f0b9a19418bb1f09bc4f57`
- prepare.py `b27a973737f0249fd2e548ffa9a824d6a75438e444cbec4bad3f6559d605fb4d`

CPU preparation passed with zero model requests: two identical GPQA provenance snapshots;198 upstream bodies exact to lastC64/65536, task metadata only concurrency64->32; ERQA400/630images/factory/sourcepassed; source identityexact/idle. Prepared66e51588, contract6c3595cb, parity07150318. Unique frozen controller ready to start.

## Running

Uniquecontroller3000927/ticks1154420516; normal smoke/C8/sourcepassed2026-10-29 08:24:28Asia/Shanghai. GPQA198/C32 began08:24:36; first32 requests allcap65536/no sampling overrides,0returned at initialcheck. ERQA400/C32/cap18000 will follow. No model restart or source edits; monitor qwen3-vl-opt15-c32 active.

2026-10-29 morning heartbeat:198 GPQA requests sent,193 unique HTTP200 returned,5 active/0 waiting; native progress latest190/198, no finalscore. No proxy errors; all198cap65536/no sampling override. Samecontroller active and models200. ERQA not yetstarted; continue existing sequential plan, no new requests.

GPQA completed2026-10-29 09:17Asia/Shanghai:127/198=64.141414>=64 passed; original gate-check PASS. Versus latestC64 cap65536=125/198, +2 correct/+1.010101 percentage points, not isolated deterministic concurrency benefit. ERQA started09:17; latest native items345/400, no finalscore; original timeout/retry and proxyBrokenPipe diagnostics retained, no added requests/retries. User model models200.

09:36Asia/Shanghai heartbeat: ERQA368/400 native unique question IDs saved; proxy426 attempts/394 returns/380unique200 with26BrokenPipe from native timeout/retry flow. Controller active, model32running/0waiting/models200. No final ERQA score; keep original retries/configuration and wait, no extra calls.

Terminal09:58Asia/Shanghai: ERQA176/400=44.00>=40,0reject; bothdatasets passed, sourceleft running. Archive CPU-only independent finalaudit commands/final_audit.py SHA2873da0060c85b867991a95cac1fed321473856559a77374feaec1cee98782fa before execution. It verifies GPQA198/provenance/gate, ERQA400/source630images/filter denominator, default sampling audit, source before/after/current and controller exit. No newmodel requests.

## Final independently verified result

Completed2026-10-29 09:58Asia/Shanghai. GPQA127/198=64.141414>=64 passed; ERQA176/400=44.00>=40 passed,0rejected, native/all400 scores identical. Compared with C64 at same per-dataset caps: GPQA+2correct/+1.010101pp; ERQA-6correct/-1.50pp. No claim that concurrency deterministically improves accuracy; unseeded sampling/cache/batch history differs. C64 failures remain unchanged and their mechanism unconfirmed.

Independent CPU audit passed: native198unique/provenance/runner/sample score and original gate check; ERQA400unique/176boolean correct/0reject,630images+original scoring source exact; allactual GPQA cap65536 andERQA18000/default sampling/no seed. ERQA461attempts/461responses/399unique message bodies and61BrokenPipe remain diagnostic; native400 unique IDs define complete coverage. No model requests were added.

Source before/afterGPQA/afterERQA/final/current exact for source/model/tokenizer/argv/env/PID1718819/ticks1149208177. Controller exited; only ownadapter stopped; source models200 and idle. No restart, clearcache, deployment or performance run.

Artifacts under remote experimentroot:
- results/gpqa-completed.json SHA57350f5232edb72def033c6f99cacd51ef1387af3bbbfdbde17c77a7b1c6b840
- results/gpqa-accuracy-gate.json checked independently; only current C32/cap65536/transport/instance binding.
- results/erqa-completed.json SHA652cd532c300e93ab70255aff277994603386edfc431824671872cefba132886
- results/completed.json SHAd0c7982b3c6995708f6421539676a3e2776c8d623209e578c42a06ccf190272b
- results/user-service-final.json SHAb0a9df37c5b47380fd93baff2468f245a2733ca74d961cb8ea7dd037e2a64d14
- results/independent-final-audit.json SHA204494ff17dcf04580111da3970306bca87e929411e1f16d25dac4c064c85870

Both requested datasets and finalaudit complete; stop this monitor. No further model work scheduled.

Monitor qwen3-vl-opt15-c32 successfully deleted after terminal audit.
