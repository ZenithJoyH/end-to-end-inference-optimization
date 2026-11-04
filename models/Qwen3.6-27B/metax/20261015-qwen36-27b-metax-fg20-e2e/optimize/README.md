# 20261015-qwen36-27b-metax-fg20-e2e / optimize

<!-- e2e:summary:start -->

- 案例：20261015-qwen36-27b-metax-fg20-e2e
- 当前状态：completed/requested-revert-and-Decode-diagnosis; performance-incomplete
- 当前候选：original20FG restored; metadata andfull candidate patches archived/privateC alsooriginal
- 下一步：No automatic rerun or deployment. Next planned point: FP32 GDN redundant JIT bucket keys, firstvalidate stable compile variants/numeric/graph before new all-role contract; keep all87oldrounds,10%spread,1%drift,.002/.02 and20FG. Exacthistoricalbucketpair/perrankstall unavailable.

| 实验 | 状态/决定 | 场景 | 文档 |
|---|---|---|---|
| env-001-script-scope-baseline | Current baseline measured3phases and bothranktrace; no new gain; operator point follows from separated B64graph20.1% packed hotspot | p1024-d1024-c64-n128 | [env-001-script-scope-baseline.md](env-001-script-scope-baseline.md) |
| op-001-gdn-packed-decode-bv16 | 12case/96step/24changed-input pairs passed and bitwise; full-callB64-11.14%<20% frozen; no install/E2E; original service restoration follows controller | p1024-d1024-c64-n128 | [op-001-gdn-packed-decode-bv16.md](op-001-gdn-packed-decode-bv16.md) |
| op-002-gdn-packed-decode-warps4 | Real15case numeric/graph passed; new3role3phase87rounds/27measured valid, Decode+1.3902%/Mixed+1.3316%<2%, guard/spread/drift pass; original source and private code restored | p1024-d1024-c64-n128 | [op-002-gdn-packed-decode-warps4.md](op-002-gdn-packed-decode-warps4.md) |
| combo-001-gdn-packed-bv16-warps4 | Numerical/graph passed; B64 latency+8.93%, no E2E, original restored; later cache inspection revealed ABI gap | p1024-d1024-c64-n128 | [combo-001-gdn-packed-bv16-warps4.md](combo-001-gdn-packed-bv16-warps4.md) |
| framework-002-mixed-batch-overlap | FreshBCR87rounds/27measured/9408requests0failed andallSHAverified; PF+0.5804%passed, D+0.2495%incompletebaselineTTFT13.445%, M+0.2646%failed2%; maxB/Rmetricdrift0.998445%<=1. Original20FG/source18002 restored. Decode newunusedbucketGDNJIT diagnosed; no rerun/drop/relax/deploy. | p1024-d1024-c64-n128 | [framework-002-mixed-batch-overlap.md](framework-002-mixed-batch-overlap.md) |
| op-003-metax-full-small-integer | 194numeric/16replay/micro+modelactualFGfixedfull passed. CommonnewbaselineMixed0.1794%measuredoutputspread<10%; nofull old/new E2Epaired gain. Finaloriginalfullrestored S+C, patches/evidencekept; independentGDNHredundantJIT exposed. | p1024-d1024-c64-n128 | [op-003-metax-full-small-integer.md](op-003-metax-full-small-integer.md) |

| 场景 | 角色 | 指标 | 数值 | 单位 | 范围 |
|---|---|---|---|---|---|
| p1024-d1-c64-n128-prefill | baseline | total_token_throughput | 5637.136083570706 | tok/s | op002r2 targeted/diagnostic; candidate rejected, original restored |
| p1024-d1-c64-n128-prefill | candidate | total_token_throughput | 5674.391979482466 | tok/s | op002r2 targeted/diagnostic; candidate rejected, original restored |
| p1024-d1-c64-n128-prefill | revert | total_token_throughput | 5662.969827893035 | tok/s | op002r2 targeted/diagnostic; candidate rejected, original restored |
| p1024-d512-c64-n64-decode | baseline | output_throughput | 937.5673861876342 | tok/s | op002r2 targeted/diagnostic; candidate rejected, original restored |
| p1024-d512-c64-n64-decode | candidate | output_throughput | 950.6011558122502 | tok/s | op002r2 targeted/diagnostic; candidate rejected, original restored |
| p1024-d512-c64-n64-decode | revert | output_throughput | 938.6878424504529 | tok/s | op002r2 targeted/diagnostic; candidate rejected, original restored |
| p1024-d256-c64-n128-mixed | baseline | output_throughput | 696.3424253005743 | tok/s | op002r2 targeted/diagnostic; candidate rejected, original restored |
| p1024-d256-c64-n128-mixed | candidate | output_throughput | 705.6151797239713 | tok/s | op002r2 targeted/diagnostic; candidate rejected, original restored |
| p1024-d256-c64-n128-mixed | revert | output_throughput | 698.1784304232615 | tok/s | op002r2 targeted/diagnostic; candidate rejected, original restored |

<!-- e2e:summary:end -->
