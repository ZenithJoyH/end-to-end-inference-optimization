# op-026: post-prof007 P16K fused-MoE frontier audit

## Decision

Status: `stopped_before_microbenchmark`. No distinct complete fused-MoE transaction candidate has credible headroom of at least 8%.

The profiler category is a real hotspot but phase attribution must account for asynchronous launch. Rank0 Decode-classified fused-MoE activity is 22.220s block256/M4096 and 1.467s block128/small-M: 93.81% versus 6.19%. The M4096 work is queued from Mixed/Prefill and begins inside later Decode marker windows, so the 23.719s aggregate cannot be interpreted as an M64 bottleneck.

The actual request stream uses graph buckets M=1,2,4,8,16,24,32,40 plus M4096. The retained M64 BM16 configuration is a capture/guard key and is not reached by this workload. Current provider is Plugin `CachedOp` through the FlagGems fused-MoE kernel; no compatible T-Head native provider is installed.

Previously rejected directions remain closed: M40/48/56/63 BM16 produced only +0.344% service output after promising microbench results; GEMM2 BN128 and GEMM1+SiLU regressed the complete transaction; split-K has insufficient mathematical headroom. The only different existing no-pad implementation targets another platform and M>=8192, contains `.item()` host synchronization and is not graph-safe, so it is not a valid PPU M4096 candidate.

Any future mechanism must time align/permute, GEMM1, activation/up, GEMM2 weighted routing and sum/unpermute together for M=1/2/4/8/16/24/32/40/4096 plus graph guard 48/56/64, and must pass graph replay, routing extremes and numerical gates. Stop below 8% frequency-weighted complete-transaction gain.
