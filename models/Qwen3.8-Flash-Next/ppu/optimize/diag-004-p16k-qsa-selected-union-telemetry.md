# diag-004: P16K QSA selected-union telemetry

Status: `incomplete_output_consistency`. This correctness/structure diagnostic ran on PPU8–15/8032 using a separate private source copy and Triton cache, but stopped at its frozen output-consistency gate.

Capture a bounded set of real P16K producer fixtures for Prefill, Mixed and Decode, including selected indices, request-run boundaries and the minimum page/cache metadata needed for offline exact analysis. Reuse the proven page-wise bounded capture pattern rather than materializing the full KV cache.

Offline, recompute exact same-request R4 union membership and report eligible rows/groups, union size and reuse distributions at p50/p90/p99/max, fallback/overflow rates, request-boundary ownership and tail behavior. Never combine rows across requests. Compare captured selected outputs with the uninstrumented producer and require fixed changed-input replay consistency.

Do not implement grouped sparse attention in this experiment. Do not allocate or clear a full token-domain direct-address workspace. This diagnostic may run concurrently with diag003, so no service or kernel timing from the run is valid. Its only promotion condition is structural evidence that a compact implementation can plausibly exceed 8% complete-QSA gain and 1% exact-Mixed gain.

## Result

The exact P16384/D128/C64/N64 capture workload completed 64/64 requests with zero failures and produced bounded Prefill, Mixed and Decode fixtures without materializing the full KV cache. The three fixture manifests are:

- Prefill: 4096 rows, one request run, selected width 2051, 1024 score columns and one cache page; SHA-256 `5f372bac80522a4aeecf98714d30c07ee827cc49e75acce5c059adb969fe53ba`.
- Mixed: 4096 rows, two request runs starting at `[0, 1, 4096]`, 4128 score columns and five pages; SHA-256 `fb014246d3d1f06f8b4924764241f7e58ec55f371815dd0be8a7cb141f182d34`.
- Decode: 32 rows, 32 single-row request runs, 4128 score columns and 96 pages; SHA-256 `ce42893fecfd3c7b3ee3d2bb9d3e10c90cb3c99f7c2719217f6b737db3794b04`.

The private-import guard passed for all eight live TP workers. The workload elapsed 423.499 seconds while diag003 was concurrently active, so it is explicitly invalid as performance evidence.

The hard gate failed: the same frozen request changed from an eight-token, `length`-terminated response beginning with `<think>` before capture to a four-token, `stop`-terminated response containing `41` after capture. The comparison receipt SHA-256 is `14c560d0376f3a8f9c885567116c699872bf7de91a09e2537f7e4a6440447626`. Therefore the A-B-B-A replay and offline R4 union/eligible/fallback/overflow computation were not run, and the captured fixtures cannot promote a candidate.

Final incomplete receipt: `/mnt/nfs/users/jinghao/qwen3.8-flash/20260919-qwen38-flash-next-ppu-e2e/diag004-20260921-r2/evidence/final-receipt.incomplete.json`, SHA-256 `812e685eef7a1bee2cc97312fa28a305d0d9061f8291b7192aad4e460f3f9e8a`. The 8032 process tree was precisely stopped, PPU8–15 were released, the private source/cache was deleted, and the shared optimization source remained unchanged.
