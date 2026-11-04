# op-025: post-prof007 P16K QSA frontier audit

## Decision

Status: `stopped_before_microbenchmark`. No new QSA implementation currently has a credible complete `select + sparse` gain of at least 8%, so no device or service experiment was started.

prof007 confirms QSA is the largest Decode device category: sparse plus MQA is 29.497s, about 29.1% of summed device activity. Mixed contains 9.479s. These are overlapping profiler activities, not direct critical-path savings.

The most obvious source change is already eliminated by compiler evidence. Although the scorer source expresses K-cache loading inside a four-indexer-head static loop, the cached PPU TTIR has one K load and all four heads reuse its result. A manual hoist would duplicate compiler CSE rather than create new work reduction.

Existing negative evidence remains binding: the static 4352 graph cap produced -0.252% output throughput in valid A/B/R; the rows4096 literal-group specialization regressed; metadata-only headroom was about 1.06%; and the exact R4 direct-address implementation regressed the complete transaction by more than 32% because of its 33.6MiB clear/build workspace.

## Deferred diagnostics

Two mechanisms may be reopened only after missing evidence is collected:

1. A score-to-TopK-to-expand pipeline that avoids materializing and rereading full FP32 logits without reducing columns or precision. First bind real P16K phase/graph-key logical shapes and time score, all TopK kernels, expand and sparse as one complete transaction.
2. Exact same-request cross-row K/V reuse using compact/on-chip/chunk-local union state, never the rejected full-domain clear/build workspace. First collect P16K union and request-boundary telemetry; P4K overlap cannot be extrapolated.

Both must pass exact ordered-TopK and integer outputs, existing BF16/FP32 attention tolerances, single-graph changed-input A/B/A replay, request-boundary and P32K fallback tests. Stop if complete-QSA eager or graph gain is below 8%, predicted exact Mixed gain is below 1%, or any large clear/build workspace returns.
