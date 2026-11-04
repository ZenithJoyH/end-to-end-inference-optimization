# acc-003: opt15 full GPQA with output cap65536

User authorized a new full GPQA run with64k output cap (65536 as previously clarified).

Mode: local inference-accuracy-evaluation/formal-gate. GPQA198/C64/strict-match64, once. Original native filter unchanged; no score splicing. opt15/8030/GPU0,1 TP2, prefixON, model defaults T.7/P.8/K20/rep1, no requestseed. No service restart, source edits, cache clearing, ERQA or performance.

Remote root: `/public-flash/jinghao/qwen3-VL/20261028-qwen3vl-opt15-c64-default-accuracy/gpqa-full-cap65536`. Existing parent realpath and free space checked. Connectivity-check sandbox RPC incident resolved by elevated project connectivity-check; passed.

Reuse official v1 evaluator and original SHA runner. gen_kwargs adds only max_gen_toks65536. Freeze current source identity, native task/filter, two provenance snapshots and CPU factory parity for all198 against old actual upstream bodies. New UUID/response cache; old model KV cache retained. Native timeout7200/retries3 unchanged; total controller budget12h. Nine normal smoke/C8 requests before fullrun.

Graph evidence: current startup capture plus normal graph-configured smoke/C8; no direct replay counter. Warm cache and unseeded scheduling dynamics remain a comparison limit.

Archive commands before execution: transfer commands/bootstrap.py exclusively; run bootstrap.py then CPU-only prepare.py; inspect prepared; start_controller.py once with exclusive manifest. Finally stops only own proxy and verifies same user model.

Monitor: qwen3-vl-gpqa-64k, every30min, delete after terminal audit.

## Frozen command SHA256

- bootstrap.py `e35b3ea30682d24d677ff6d243d1741344cd2f7532b0e178cee62e5c8e089aea`
- default_sampling_proxy.py `832ac1270f12b5785922f9e8d838fe40292ab4f6a41967317f1ef1793d0965df`
- proxy_cpu_test.py `93ab0a0df98bad3722711234476b7fb1268bb35479bcb8ab550ebcaf92068dd8`
- collect_current.py `9c6e4d35d5f8a9fb8895fa3f9118bc927ffcbb6d68cd4b19c96fea47b128350d`
- accuracy_controller.py `996e41d792ea66f1c20137f2191ffd8e080058c44269cfc8c17516cb8302b8b5`
- payload_parity.py `21e4bc5d2bbf992b319e38c0a8f5b121ede1665545b977ae67e7d843b5952b6e`
- start_controller.py `5e16b418fba61f0f4058ad3c423978ab8d1605d5184ed4573789d8e28877e809`
- prepare.py `f581477c3ec517962f496fd10d49df428015afa373474c45a01e2ecb79b3adcc`

CPU preparation guard incident: task_config includes effective max_gen_toks; exact whole-dict comparison rejected the authorized18000->65536 change. Zero model requests. Both provenance captures and198 actual factory parity passed. Preserve prepare.py/logs; finish_prepare.py normalizes ONLY this verified field and still requires all other task/filter fields exact, then freezes contract.
- finish_prepare.py `40132bf9bc5597fd3d1d413d0dcf2fc7f725171f7c9850750ed491179f20d112`

Preparation passed: prepared cc8e7c9b, contract49a9e1c0, payload13684129. All198 same original messages/stops/default sampling, only outputcap changes; source same PID/ticks/code/argv/env. Start the single frozen controller next.

## Started

Unique controller2784641/ticks1151385325, source unchanged. Normal smoke/C8/source passed15:58:31UTC; GPQA198/C64 started2026-10-28T15:58:39UTC (23:58:39Asia/Shanghai). No restart. Skill bundle 1ed06a57f1f6e1ef39fb7fd872f579122b098a18f0255ade0a1160d6432c2b66.

Initial actual traffic audit:133 forwarded,69 HTTP completed, all observed cap65536, no sampling/seed overrides, all upstream SHA in the frozen198 payload set. No final score yet.

2026-10-29 00:22Asia/Shanghai heartbeat:198 sent,187 unique HTTP responses,11 active/0 waiting, no proxy errors. Native periodic logger last180/198; no terminal score. All198 forwarded caps65536/no sampling overrides. Controller same PID/ticks and source models200. Continue existing run; no new requests or restart.

Terminal2026-10-29 00:47Asia/Shanghai: native125/198=63.131313<64, no gate. Controller exited, original model preserved. Invoke local inference-accuracy-diagnosis under existing issue accdiag-opt15-c64-gpqa-001; formal below threshold remains unconfirmed cause. Archive CPU-only independent audit commands/final_audit.py SHAf22f13692ea174fe82b2b5f593c580eea872e80e6bc79afa626b306c59fd1c80 before execution; verify native evidence, all198 original filter/metric, cap-only argument parity, source identity and paired outcomes. No model calls or scoring changes.

## Final result and independent audit

Completed2026-10-29 00:47Asia/Shanghai: **125/198=63.131313%, below64; no gate**. All198 unique native samples, native score/perdoc sum, frozen provenance/runner, original strict/flexible filters and metric reproduced. All198 actual requests cap65536, no sampling/seed override, HTTP200/no proxy errors; all match frozen payload SHA. Current original PID1718819/ticks1149208177, repositories/model/tokenizer/argv/env exact; models200 and idle. Controller exited and only own adapter stopped.

Compared with18000 fullrun:110 bothcorrect,58 bothwrong,15 newlycorrect and15 newlywrong; zero identical complete responses. New correct IDs7,8,49,51,56,60,74,91,98,102,139,149,160,168,194. Newly wrong23,27,57,66,69,75,80,105,128,131,152,159,170,173,179. Ten reach65536:48,66,68,71,85,88,127,128,180,187. Eleven strict invalid, including115. Ending-pattern screen found no explicit correct final-letter/strict-failed candidate in this run; this is not independent scientific relabeling of all answers.

Original source/runtime unchanged and only payload cap changed, but unseeded trajectories and retained warm cache differ. Same total score does not mean same answers; increased cap did not achieve threshold in this run. No claim of isolated cap causality or model/library root cause. Keep original125/198 and prior11-item diagnosis separate. Issueaccdiag-opt15-c64-gpqa-001 remains valid formal failure/rootcauseunconfirmed; no new optimization, rerun or production change.

Remote artifacts under this experiment root:
- results/gpqa-completed.json SHA876afed3ec456b74e5192690abe796370bf0cfb2000e055ce623404f10c9a5bc
- results/completed.json SHA095311c1015cea4b08a9b4e0a5b3f8630d43dc0c66f575ad1d0a7df724f5558e
- results/user-service-final.json SHAe81edeca4a9ee13047062e02b8d63e75c7bb5cbbfe4b429cf08c3c83c22b19c5
- results/independent-final-audit.json SHA63efcec7014e96555671c52478ab638ab5df258798c49aaccca47bf6570584b3
- Native result076e42a5be3a3cb4f77e7c541b44632134fdf5a0e4a35aca2bc7bc1379d7ead2 and samples1b9fad5b6bec2fd07dfa527e135dcc601e92a556c807928a47d0fb490e22312f remain remote.

Requested task complete; delete qwen3-vl-gpqa-64k monitor after this terminal audit.

Monitor qwen3-vl-gpqa-64k deleted successfully after terminal audit.
