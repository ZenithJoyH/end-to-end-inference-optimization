# diag-008: Fixed-seed C1 regression diagnosis

Status: completed and validated. All9 scoped requests correct; each selected sample repeated3 times with identical generated token IDs and all returned sampled/top5 logprobs. Original full50000 failure remains unresolved.

User authorized selected reproductions of the 11 formerly correct questions on 2026-10-13. This is a diagnostic probe, not a formal score or performance run.

The 11 IDs are 10,21,48,88,93,94,97,98,129,166,186. All new responses ended with stop, not length; the old/new texts split after 158-2327 characters. The prompts, golds and extraction rules are unchanged.

Select IDs 21,93,129 before measuring: short electrochemistry, long organic chemistry, and a physics cutoff. Run three identical requests per ID sequentially with C1, seed1234, temperature1, top_p0.95, top_k20, max_tokens50000, stop </s>. All diagnostic requests request token IDs and top5 logprobs; these additional observation flags are consistent across repeats and differ from historical C32. No source, model service, gold or formal contract changes.

Identical C1 generations would establish repeatability only for these examples. Differences from historical C32 would be batch-associated, but cannot alone distinguish batching RNG from batch-dependent numeric changes. If C1 differs, compare first divergent tokens at an identical token prefix and their returned logprobs; top5 distributions do not establish equality of the entire vocabulary. Stop on errors or exact model-instance/source drift; no retries or automatic full re-evaluation.

Remote case: `/public-flash/jinghao/qwen3.6-27B/optimize/flash_attention/20261012-qwen36-27b-metax-flash-attention`.

Existing-result audit: `results/diag008-eleven-audit.json`, SHA256 `7eaba33584a045ea5a47ae9ef5ae98bfa7d40ceb5f32139a74d0d801b0cfe337`. Audit command SHA256 `ba0369a88d035fee1fd7638d36fe264970702ba1acf19670fdee4175986ffd13`. This audit preceded the new requests.

Prepared remote commands:

- `/public-flash/jinghao/qwen3.6-27B/optimize/flash_attention/20261012-qwen36-27b-metax-flash-attention/commands/diag008-c1-worker.py`, SHA256 `bc70cbff0ec462986bd14b442473aff0b3b7836f31c64b7275207cdb2d09803d`.

- `/public-flash/jinghao/qwen3.6-27B/optimize/flash_attention/20261012-qwen36-27b-metax-flash-attention/commands/diag008-prepare-launch.py`, SHA256 `40d4258c611cc617b828f2ca1266432153cf9539641cde9e028c07dab73660af`.

Launched in `qwen36-fa-gpqa-fixed-20261012`, PID2702/create1791865261.58; receipt SHA256 `c5b37fa4a2035f88e868ded281a943291643ea7b442a7eefb36d7efab08fa369`. Plan SHA256 `1d10bd2df0ba577544dfbcd1f4b560cca15d25e7dd2d7a4b230ba44e9fe85d28`. Exact current model instance and all four source hashes passed launch verification; service was idle.

Code audit: private Plugin ModelRunner creates a per-request `torch.Generator` and `manual_seed(sampling_params.seed)` for RANDOM_SEED. vLLM native sampler overwrites each seeded row with `exponential_(generator=generator)` before probability/noise argmax. No MetaX-specific sampler override was found in the private Plugin. This is source evidence, not a runtime proof that every GPU RNG or model kernel is batch invariant. Raw logprobs are computed before temperature/top-k/top-p; temperature remains1 and no penalties are requested. Top5 returned values are observations of the model distribution, not the full sampling distribution.

Terminal validator: `/public-flash/jinghao/qwen3.6-27B/optimize/flash_attention/20261012-qwen36-27b-metax-flash-attention/commands/diag008-finalize-existing.py`, SHA256 `ed87a74d30804c904ca57ab72307551300e5fd3e9f473ec23b5ae205363932ba`; verifies existing evidence only.

## Existing eleven-question reasoning audit

All eleven have unchanged prompts/golds and stop termination; no empty output, truncation or extraction mismatch was found. These categories describe observable changes in the answer text, not the GPU root cause.

| ID | Old -> new (gold) | Observable change |
|---|---|---|
|10|A -> B (A)|Virology knowledge claims reverse: proofreading/dsRNA degradation versus intrinsic/extrinsic apoptosis.|
|21|B -> A (B)|Thermodynamic part agrees; the claimed direction of oxygen reaction kinetics reverses.|
|48|A -> C (A)|Sigmatropic rearrangement substrate/product assignment changes.|
|88|A -> D (A)|NMR neighboring proton groups change, giving triplet-of-triplets versus triplet.|
|93|B -> A (B)|Intramolecular Diels-Alder diene/dienophile placement and ester/propyl regiochemistry change. Old29981 tokens, new8205; both stop.|
|94|A -> B (A)|Gilman reagent epoxide opening switches to the more substituted carbon, inconsistent with the dataset explanation.|
|97|C -> A (C)|Metathesis precursor carbon framework/bridged ring assignment changes.|
|98|A -> B (A)|NMR splitting connectivity changes, selecting a different carboxylic-acid isomer.|
|129|B -> A (B)|Assumed ground telescope cutoff changes3500A ->4000A; the same redshift equation then chooses a different answer.|
|166|C -> A (C)|Odd cat state treatment switches coth to tanh and changes covariance/entropy assumptions.|
|186|D -> B (D)|ESPRESSO limiting magnitude/mode assumptions change, adding one detectable star.|

No changed gold or late output budget cutoff explains these eleven flips. Several reflect sensitivity to knowledge, structural mapping, or an unstated physical/instrument assumption. The computational origin of the earlier token-trajectory change remains to be determined from the bounded C1 experiment.

First bounded response: ID21 repeat1 chose B (gold B), stop,3332 completion tokens and3332 returned token IDs/logprobs. This is a partial observation; all repetitions are still required to assess repeatability. The monitor is active for this exact nine-request process and will validate/pause on terminal without submitting more model requests.

## Monitor checkpoint 2026-10-13 04:56 UTC

4/9 completed, exact evaluator process alive; ID93 repeat2 active. No errors or detected foreign request load; current service metrics1 running/0 waiting. IDs21/93/129 first repeats all chose B correctly, with3332/39570/5061 completion tokens, all stop. ID21 repeat2 again chose B; its prompt IDs, entire3332 generated token IDs and all returned sampled/top5 logprobs exactly equal repeat1 (top5 delta0, finite values).

This is meaningful C1 repeatability evidence for ID21, despite another long request occurring between the repeats. The first three selected questions recover relative to the historical C32/50000 run, but observation flags also differ and one paired repeat cannot distinguish batch-dependent numerical changes from sampling effects in C32. Await all9; no final validation, new formal gate, model mutation or extra request.

## Validated terminal result, 2026-10-13 05:26 UTC

| ID | Gold | Historical C32/30000 | Historical C32/50000 | C1/50000 repeats1,2,3 | Tokens per repeat | Token IDs / returned logprobs equality |
|---|---|---|---|---|---:|---|
|21|B|B|A|B,B,B|3332|Both exactly equal|
|93|B|B|A|B,B,B|39570|Both exactly equal|
|129|B|B|A|B,B,B|5061|Both exactly equal|

9 requests completed normally, no timeout or error,61.58 minutes total. All9 pairwise repeat comparisons have identical prompt IDs, generated IDs, response text and every returned sampled/top5 logprob; no first divergent token exists within these C1 repeats.736 metric observations show max1 running,0 waiting, no metric error/foreign load. Current model is idle. The terminal validator rechecked exact model PID/create time and all4 source hashes, all unchanged. No new model requests were generated during validation, and no gate was issued.

The selected C1 trajectories are reproducible across intervening requests, including the long39570-token organic case. This argues against an uncontrolled seed or persistent single-request nondeterminism in this selected scope. It does not prove all11 samples or fullGPQA are correct. The historical C32 wrong responses are genuine reasoning changes: ID21 reverses kinetic direction, ID93 reverses regioisomer assignment, ID129 changes the optical cutoff assumption. The C1 final answers use the gold-consistent alternative reasoning. None of the eleven historical wrong responses was truncated.

Batch-associated execution sensitivity is suspected, but RNG/scheduling versus batch-shape model arithmetic is not isolated. Historical C32 did not return token IDs/probabilities; C1 also enables consistent observation flags. Thus this is not a strictly one-variable causal C1/C32 comparison. Seed1234 can reproduce a C1 trajectory while deterministic batch-shape logit differences alter a long temperature1 trajectory. There is no evidence here localizing a faulty FlagGems/native attention kernel, GatedDeltaNet kernel, GEMM or distributed operation. Returned top5 equality is not full-vocabulary equality.

Next falsifier proposal only: use identical observation flags for controlled C1/C32 and compare probabilities at identical token prefixes; localize the first layer/operator difference only if the distribution evidence supports it. No additional requests were started. Full50000 score158/198 remains below80, performance remains blocked and no source/model change or fix has been applied.

Evidence (remote case root above):

- `results/diag008-c1-fixed-seed/terminal.json`, SHA256 `ef35d0c930ccdb84b1ae221c8dad84d0fa5fd35bef867e4d64f2357eacce2ad5`.
- `results/diag008-c1-fixed-seed/host-validation.json`, SHA256 `04069fc329e475c0c5f5d0307577aba14bef5261fd64b249fee6f085de1e8c04`.
- `results/diag008-c1-fixed-seed/metrics.json`, SHA256 `cb241b0d8fa554fbc806e2598274f79d4d626ae59fd6ddd8981286dd6c288c67`.

The monitor is paused after terminal validation. Existing formal results, contracts and source service8002 are preserved.
