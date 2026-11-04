# op024: Inline retained MoE configuration

Planned source-only migration, no restart/GPU tests. User explicitly requested removing the newly added external JSON loader and Plugin JSON assets, placing the current tuned parameters in the operator. Continue existing isolated target container.

## Pre-coding project truth

| Item | Frozen contract |
|---|---|
| Operator / source | Existing FlagGems-vllm fused_experts_impl; parameter storage migration only |
| Editable | Generic MoE external branch, MetaX configuration/selector, local JSON helper, two private Plugin JSON files and their packaging entry |
| Read-only | All kernels and other host compute functions; vLLM, FlagGems/gems-opt, sampling, Worker, shared start-model.sh and source container |
| Build | Editable pure Python, no build/reinstall |
| Validation | CPU actual old/new selectors, full M0..65536 and boundaries/nonmatches/cache isolation; AST invariance, syntax/whitespace |
| Benchmark / aggregation | Not run; no new throughput claim |
| Active set | Current MetaX E128/logicalN384, config dtype None/fp16/bf16, both GEMM stages, unchanged nearest-M rules |
| Timeout | CPU120s; no service/GPU work |
| Profiler / autotune | Not applicable to parameter-storage migration; explicit user request exempts inline measured local table, no NVIDIA autotune changes |
| Fallback | Original embedded/default library selection, no new torch fallback |

## Tensor/semantics contract

| Item | Contract |
|---|---|
| API | Existing fused_experts_impl, no new torch API or exported operator |
| Input / output | Shape/dtype/layout/alias, routing, activation, quantization, accumulation, device and in-place behavior unchanged |
| Dtype | Preserve existing fp16/bf16 configuration file matching; other dtypes retain original embedded/default behavior |
| Numerics / autograd | No computation code changed; forward inference only; actual numerical/graph revalidation not claimed |
| Reference | Saved original JSONs and actual pre-change selector; CPU tests only |

## Path design

| Path | Trigger | Implementation / checks |
|---|---|---|
| Tuned | MetaX target E/N/dtype/block selection | Inline separate G1/G2 tables, same insertion order and closest-M/copy behavior; exhaustive CPU equivalence |
| Existing general/default | Nonmatching keys or batch-invariant | Preserve original library configuration/default selection; targeted CPU checks |
| Empty / special / unsupported | Existing operator logic | All compute/JIT AST unchanged; no new branch or torch compute |

Two Plugin JSON files and utils/moe_config.py will be backed up in the remote case before removal. No new tests/perf files will be added to operator repositories. New service graph and output checks remain incomplete because the user owns restart. Full GPQA remains deferred.

## Completed migration

The retained root11 and GEMM2 eight M rows are materialized once in `_TUNED_HALF_MOE_CONFIGS` inside `/workspace/FlagGems-vllm/src/flaggems_vllm/runtime/backend/_metax/ops/fused_moe.py`. The MetaX selector chooses the proper stage table for E128/logicalN384 with config dtype None/fp16/bf16 and no block selector, exactly matching the former file domain. Rows retain insertion order, nearest-M ties, copied dictionaries, the is_embedded=True execution branch, and equal BLOCK_SIZE_M for shared assignment. The existing API and all compute/default kernels remain unchanged. Matching no longer depends on an external folder.

Generic get_moe_configs is restored to its baseline embedded-table implementation, with the external import/branch removed. The new utils/moe_config.py and exactly two private Plugin JSON files were backed up in the remote controls and removed. Plugin package-data entry for those files is removed. No tests/perf files were added in either source repository. User explicitly requested inline tuning; this is a measured local MetaX exemption to the normal no-hardcoded-candidate guidance, not a new autotune search or NVIDIA change. optimization.md/deep_opt.md were absent and no new kernel design was attempted.

## Correctness and path evidence

Before writing product files, actual old/new host selectors were executed as isolated AST using mocked runtime metadata/default function, without importing torch/vLLM or initializing a GPU.393240 matching comparisons cover each M0..65536 plus65537/131072/2147483647, both stages and config dtype None/fp16/bf16. Every selected dict and is_embedded flag matched.126nonmatching key/dtype/block cases and72unset/empty/missing/invalid directory independence checks passed. Batch invariant falls through to default as before on MetaX; copy isolation, invalid stage errors, closest-M ties and original generic embedded lookups passed.

All34other generic host functions and30other MetaX host/compute functions have unchanged AST; all9generic and5MetaX Triton JIT functions are unchanged. Candidate JSON/hash was verified before applying and actual deployed file inventories match that exact candidate. Source syntax/whitespace and a full FlagGems-vllm src reference scan confirm no VLLM_TUNED_CONFIG_FOLDER, load_moe_configs or utils.moe_config reference remains. Kernel arithmetic and parameter values were not retuned. This is strong source/parameter evidence, not a new numerical model or graph pass.

M64 G1 remains BM16/BN64/BK128/G1/W4/S3; G2 is identical except S1. M8192 G1 remains BM128/BN128/BK64/G1/W8/S1; G2 remains BM128/BN128/BK64/G8/W4/S1.

Minimal-regression is incomplete at the service level: no fresh GPU numerical, graph capture/replays, HTTP or E2E test was run and no restart was performed. Old workers keep imported code/cached configs. Previous results remain historical; current source does not inherit an automatic graph or formal-accuracy gate. GPQA remains deferred by user. No new performance benefit is claimed.

## Retention, rollback and handoff

Source migration is complete in isolated qwen3vl-p64k-opt-20261015. Four repository revisions and normalized mounts/image were preserved; only the three source/packaging changes and three intended removals were permitted by full inventories. Sampling files, gems-opt, vLLM, Worker, all other parameter values and current service identity were unchanged. Source container was not operated on.

The shared start-model.sh is deliberately unchanged. Its old VLLM_TUNED_CONFIG_FOLDER export is now ignored by FlagGems-vllm; official native vLLM support is untouched. The next user-owned restart loads the inline parameter source. It still requires actual path/config proof, graph/smoke regression and the same steady-state preparation before new E2E conclusions.

Remote controls and rollback bytes are under `/public-flash/jinghao/qwen3-VL/20261015-qwen3vl-metax-p64k-opt3/commands/op024-moe-inline-20261019`: candidate.json contains every before/after file; baseline-configs retains exact two JSONs. Scoped rollback restores only those six files after identity checks, then user restarts when appropriate. Never reset repositories or restore old sampling code. Native receipts are results/op024-cpu-check.json and results/op024-inline-final.json; exact SHA/path map is in state.yml. pr_readiness=experimental until service/hardware evidence is renewed.

Planning review planning-op024-inline-handoff records op021 dispatch superseded, op022 direct adapter retained, native stage proposal cancelled, and op024 complete on disk. Combined throughput remains unknown. The next action is user-owned restart/validation/results; no further optimization or automatic restart was launched. No SOP revision is justified.
