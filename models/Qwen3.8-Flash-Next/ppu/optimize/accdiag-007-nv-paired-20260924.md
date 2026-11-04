# accdiag-007: NV raw GPQA versus PPU acc-010, paired read-only audit

Date: 2026-09-24. No model service, evaluator, source tree, or frozen result was changed. This is observational diagnosis, not an accuracy gate or a causal A/B.

User clarification on 2026-09-24: NVIDIA and current PPU use **different adaptation code**. Accordingly, all paired counts below describe only model-response outcomes on the same questions. They must not be used as a source-change A/B, a direct numerical-precision gap, or evidence that a particular current-PPU operator is wrong. Subsequent root-cause work is restricted to current PPU responses and the current adaptation environment; see [accdiag-008](accdiag-008-current-output-replay-20260924.md).

## Provenance and comparability

- User-provided NVIDIA-native sample file: `/mnt/nfs/users/jinghao/qwen3.8-flash/gpqa_nv.jsonl`, 23,326,400 bytes, modified 2026-09-24 10:19:40 +08:00, SHA-256 `2364b3702079cf7678f5be9583cdd6d3f5eb1f744dfcd9c92af16c5f0a7cb528`.
- PPU acc-010 frozen samples: `results/Qwen3.8-Flash-Next-user-dual-maxseq32-20260923/89c1eccbb0524ac693740f8bc4a0c154/gpqa_diamond_generative_cot/Qwen3.8-Flash-Next/samples_gpqa_diamond_generative_cot_2026-09-23T04-27-33.340116.jsonl` beneath the acc-010 external root; SHA-256 `a86841d0583bb5e421711b797502a03b7f022a9b60fdcb015191768e4cecb5ae`.
- Each file has 396 rows: 198 distinct `doc_id` for `strict-match` plus 198 for `flexible-extract`. The comparison uses **only** the 198 unique `strict-match` records. All 198 `doc_hash`, `prompt_hash`, `target_hash`, rendered prompt arguments, and target letters match exactly. Thus this is the same task content and answer key, not a choice-order mismatch.
- Both embedded generation arguments specify temperature 1.0, top-p 0.95, top-k 20, `do_sample=false`, and stop string `</s>`. **NV specifies `max_gen_toks=90000`; PPU specifies `max_gen_toks=60000`.** PPU additionally spells out min-p 0, presence penalty 0, repetition penalty 1; NV omits these fields, so their effective server defaults are not proven from this file. The NV file does not establish the model weights/revision, serving engine, reasoning parser, API seed, device topology, concurrency, or request routing. NV samples contain full reasoning text, whereas PPU `resps` contain only the final `content` returned by its Qwen3 reasoning parser. Therefore this is a paired outcome comparison but **not** a hardware-only or one-variable precision test.

## Strict-match outcomes

| Outcome across 198 paired questions | Count | Doc IDs where useful |
|---|---:|---|
| Both correct | 170 | — |
| NV correct, PPU wrong | 14 | `12,30,32,64,69,71,88,89,90,102,127,140,164,168` |
| NV wrong, PPU correct | 4 | `10,13,21,79` |
| Both wrong | 10 | `17,76,106,113,145,147,157,160,167,171` |

NV is **184/198 = 92.9293%**; PPU acc-010 is **174/198 = 87.8788%**. The net difference is ten questions, or 5.0505 percentage points. The `flexible-extract` view happens to score 63/198 on both files, but it is not the frozen formal-gate metric and must not be substituted for strict-match.

The 14 NV-only correct cases divide into six PPU 60K length caps (`12,32,64,71,88,127`) and eight PPU completed final-answer errors (`30,69,89,90,102,140,164,168`). PPU's seventh cap, `145`, is wrong in both runs (NV selected `C`, target `A`). The four PPU-only correct cases include three NV wrong letters (`10,13,21`) and one NV invalid/no final answer (`79`). In the eight PPU completed-error cases, the acc-010 strict parser extracted the model's explicit final letter; these are not a PPU final-letter extraction failure. Prior item audit identified particularly clear reasoning errors on `140` and `168`, probable on `164`, while `30,69,89,90,102` have domain ambiguity or route/label concerns and need adjudication before being called numerical regressions.

## Length-budget evidence

Using the model's local tokenizer at `/mnt/cpfs/models/Qwen3.8-Flash-Next` inside `qwen3.8-flash-opt-candidate-20260919`, with `add_special_tokens=False`, the NV full-response text token counts for PPU-capped IDs are:

| Doc ID | NV tokens | NV strict result | PPU result |
|---|---:|---|---|
| 12 | 44,167 | correct B | 60K, invalid |
| 32 | 73,403 | correct B | 60K, invalid |
| 64 | 71,129 | correct D | 60K, invalid |
| 71 | 58,794 | correct A | 60K, invalid |
| 88 | 86,306 | correct A | 60K, invalid |
| 127 | 86,651 | correct A | 60K, invalid |
| 145 | 85,702 | wrong C | 60K, invalid |

Four of NV's six successes on PPU-capped questions finish **well beyond** PPU's 60K budget (`32,64,88,127`); budget mismatch is a concrete major confound. However, NV finishes `12` and `71` **below** 60K while PPU runs to 60K, demonstrating a different generation trajectory, not just a shorter hard limit. Across all NV strict samples, 14 responses tokenize above 60K and 10 of those are scored correct. These token counts are from the extracted raw text, not NV server usage records, and a hypothetical 60K NV rerun cannot be scored by simply discarding those ten results: early answer markers, parser behavior, and generation state would need to be checked.

NV `timeout=false` on all 198 samples, including invalid/no-final-answer docs `79` and `147`, whose raw text tokenizes to 89,997 and 89,969 tokens respectively and ends mid-reasoning. Thus its timeout flag alone underreports near-90K truncation; the NV file lacks HTTP finish reasons and authoritative usage counts. PPU's seven caps have independent HTTP `finish_reason=length`, 60K usage, `content=null`, and invalid strict extraction documented in acc-010.

## Diagnostic conclusion and next discriminating test

The observed 10-question net gap is a combination of non-identical generation budget, PPU no-final-answer events, and completed answer-trajectory differences; it is **not evidence that one PPU kernel causes a five-point precision loss**. Increasing PPU's budget might recover some capped questions, but `145` shows a longer NV answer can still be wrong, and `12/71` plus the eight completed flips show it will not isolate all differences. The historical PPU 181/198 reference also cautions against attributing the entire gap to the PPU platform, though it is not a matched baseline.

To isolate cause, first obtain NV run identity/config (model revision, server command, parser, seed, concurrency and actual finish/usage evidence), then run a matched-budget controlled comparison. A smaller fixed replay should prioritize `12,71` (NV answers before 60K, PPU caps) and `140,168` (completed wrong versus correct), checking first divergent token/logits and actual implementation hits on the same PPU card group before changing another knob. A new full 198-question formal gate on the exact candidate identity remains necessary before changing the 174/198 verdict.

Read-only audit script: `docs/cases/20260919-qwen38-flash-next-ppu-e2e/commands/compare-nv-acc010-gpqa.py`. Token counts used `AutoTokenizer.from_pretrained(..., local_files_only=True, trust_remote_code=True).encode(response, add_special_tokens=False)` against the immutable NV raw responses. The tokenizer loaded the local model file despite a `qwen4_exp` architecture warning; the counts are useful to distinguish large length-budget classes, not substituted for provider usage.
