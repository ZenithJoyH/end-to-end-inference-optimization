# diag-001: QSA TopK stream-sync attribution

- Direction: `operator/replace` diagnostic; determine whether native
  `torch.topk/mbtopk` causes the 3:1 `cudaStreamSynchronize` correlation in
  `prof-004`.
- Scope: isolated PPU0, FP32 logits, rows 64/4096, columns 1024/1280/8448,
  `k=512`; eager and graph replay with an elementwise control.
- Result: the corrected probe hit native mbtopk kernels for all 12
  shape/mode combinations via native sbtopk/mbtopk kernels, graph capture
  succeeded for all six shapes, and
  control-adjusted `cudaStreamSynchronize` was `0.0` per TopK everywhere.
- Decision: hypothesis refuted; stop the TopK replacement direction. The
  profiler correlation must not be treated as causality or recoverable time.
- Evidence:
  `/mnt/nfs/users/jinghao/qwen3.8-flash/20260919-qwen38-flash-next-ppu-e2e/microbench/qsa-topk-sync-probe-002/result.json`
  (SHA-256
  `dee626daf2faf1e026092325329fc804ad00fc82c3bc4cf36e33657fd2c11e24`).
- Invalid predecessor: `qsa-topk-sync-probe-001` double-counted CPU and GPU
  annotation markers and is retained as invalid diagnostic evidence.
