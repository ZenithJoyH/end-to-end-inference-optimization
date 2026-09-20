# Hy4 full GPQA formal gate (passed)

- Host/container/service: `PPU-07` / `hy4-opt-20260914` / `hy4` on port `8010`.
- Service graph mode: `FULL_DECODE_ONLY`, TP16, `max-model-len=100000`,
  `max-num-batched-tokens=2048`, prefix caching explicitly disabled.
- Source identities: Plugin `f7d1aaa`, FlagGems `0e02755`, FlagGems-vllm
  `a26a902` plus `flaggems-vllm-hq4-graph-capture-gap.patch`.
- Startup repair: the latest migrated FlagGems-vllm sparse MLA covered HQ4 only for
  `SQ<=64` and `SQ>=128`. Default graph capture includes `SQ=72..120`, which fell
  through to a generic HQ64/HQ128-only kernel and raised `Unsupported h_q`.
  The patch extends the HQ4 prefill specialization to `SQ=65..2048`.
- Focused validation: 9 sparse MLA tests passed, including `SQ=65/72/127`; graph
  capture and two replays passed for `SQ=72/128`. The full service then captured
  all `51/51` graph sizes. Two chat smoke replays returned `stop` with content `OK`.
- Formal contract: `gpqa_diamond_generative_cot`, 198 unique documents, metric
  `exact_match,strict-match`, frozen threshold `0.87`, seed 42, C64,
  `max_gen_toks=80000`, `reasoning_effort=high`.
- Dataset revision: `content-sha256:167548b01bcfd7d38d0eb80bb01bd1e6dded4d3aa14b41a4bdba0beb5423dadc`;
  two independent provenance captures were byte-identical.
- Evaluation image: `harbor.baai.ac.cn/flageval/flageval-llmeval:v1`, image ID
  `sha256:bcefa10b9be062ed449ac1e7b7925fa4f9a46e1361fbb25cc6e99616bc59a4f5`.
- Native run UUID: `004dd92608e94977b18ed9567f88338b`.
- Result: 198/198 completed, no timeout, strict-match
  `0.9292929292929293 >= 0.87`; flexible-extract `0.4494949494949495`.
- Gate: `accuracy-gate.json`, SHA256
  `503516c80851a17c27620bccfae7440792fa8d444f136023e830ca2fe47ee77a`;
  bound run-record SHA256
  `55ecb5e6a69774a2c773bc010d50b875c1f8cfa5f3a20dcfb6afd2ff3d7065f4`.
- The scheduled heartbeat was removed after the evaluation reached terminal state.
- Remote artifacts: `/mnt/nfs/users/jinghao/hy4-preview/optimize/20260914-hy4-preview-ppu-e2e/results/accuracy/formal-gate-20260918-f7d1aaa-a26a902-01`.

The native evaluator completed successfully, but the first wrapper finalization
failed because provenance validation used `str.splitlines()`: GPQA document 4
contains legal `U+2028`, which was incorrectly treated as a JSONL boundary. The
native JSONL remained valid and the evaluator-loaded document matched the frozen
fingerprint. Validation now frames records by physical file newlines; 35 focused
tests, including the `U+2028` regression and no-inference finalization, passed.
The original validator files are retained under `validation-repair-original/`.
The existing native run was finalized without issuing model requests, then the
gate was issued and independently checked. A later runtime check found port 8010
stopped and all 16 PPUs released; this does not change the immutable gate evidence.
