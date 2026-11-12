# mHC 案例索引

## GLM-5.3-Flash / PPU / graph Decode pre backend 替换

```yaml
case_id: 20260911-glm53-flash-ppu-e2e
case_link: ../../../../../docs/cases/20260911-glm53-flash-ppu-e2e/README.md
status: reverted
evidence_level: reproduced
environment:
  model: GLM-5.3-Flash-BF16
  platform: thead PPU
  hardware: 16x PPU-ZW810E
  engine_revision: ee0da84ab9e04ac7610e28580af62c365e898389
  plugin_revision: 95b04f7f321d94b2a21425bfc93cb34adcc0b7d0 plus uncommitted dispatch guards
  operator_library_revision: FlagGems-vllm f7443e776fc078318685dc8456ef5a8b2281d0f0 plus retained small-M MoE candidate
  mode: graph
operator_path:
  stage: decode
  impl_id: mhc_pre_with_norm default.reference versus default.flagos
  effective_shape: residual=[M,4,4096] BF16; fn=[24,16384] FP32; M in 1,8,16,24,32,1024
  dtype: BF16 residual/output with FP32 parameters and normalization intermediates
  layout: residual [tokens,hc_mult,hidden] with hidden contiguous
bottleneck_evidence: post-small-M rank0 Decode trace attributed 8.277 percent of summed device activity to mhc_pre
change:
  classification: operator/replace
  primary_variable: remove mhc_pre_with_norm from thead FlagOS blacklist
  applicability_guard: thead PPU, hc_mult=4, hidden=4096, graph-valid FlagGems implementation
results:
  operator: FlagGems median speedup 5.528x across six M shapes; minimum 5.309x; all eager/graph/correctness checks passed
  end_to_end: P1024/D1024/C64/N128 output throughput -0.587 percent; P99 TTFT -4.171 percent and P99 TPOT -1.821 percent improvements (negative means regression)
  correctness: direct operator numerical checks and graph capture/two replay passed; 16/16 service ranks hit flagos and all six full rounds completed
  regressions: candidate P99 TTFT regressed 4.171 percent and P99 TPOT regressed 1.821 percent
knowledge_delta:
  prior_belief: replacing an unfused or slower mHC pre path with a greater-than-five-times faster graph-valid kernel should materially improve Decode
  outcome: contradicted
  revised_belief: isolated mHC pre latency is not a sufficient promotion signal on this graph path; adjacent scheduling and overlap can erase the operator gain
  future_first_check: after direct graph correctness, run a short same-workload end-to-end A/B before broadening shapes or removing the stability blacklist
limits: one PPU platform, TP16, hc_mult=4, hidden=4096 and P1K/D1K finite-batch workload; no P4K/P16K/P32K claim
```

事实主记录见
[GLM-5.3-Flash PPU optimize state](../../../../../models/GLM-5.3-Flash-BF16/ppu/optimize/state.yml)，
原始产物位于远端 `full-scenarios/p1024-d1024-c64-n128/candidates/mhc-pre-flaggems-01/`。
