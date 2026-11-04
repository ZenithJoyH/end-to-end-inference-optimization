# op-023: P16K native mm_out provider

## Direction and status

- Classification: `operator/replace`.
- Status: `complete_passed_d128`.
- Purpose: measure whether the retained op010 native `mm_out` provider remains beneficial at P16K before treating its P4K gain as portable.
- Isolation: PPU0–7, port 8031, fresh sequential service instances; retained service50 on PPU8–15/8030 must remain untouched and healthy.
- Milestone: P16384/D128/C64/N64, three warmup plus three measured rounds per role.

## Frozen A/B/R

| Role | Service | Provider environment |
|---|---|---|
| A | service58 | `_conv_depthwise2d,index,normal_` |
| B | service59 | `_conv_depthwise2d,index,normal_,mm,mm_out` |
| R | service60 | `_conv_depthwise2d,index,normal_` |

The platform backend list already excludes `mm`; therefore `mm` is native in every role and the real single-variable provider delta is `mm_out`: FlagGems in A/R versus native in B. Source content, model, scheduler, QSA bound, M64 MoE config, graph mode, devices, workload and benchmark contract must be identical.

## Gates

- Each fresh service must prove readiness, FULL graph capture, at least two changed-input replays, the expected runtime dispatch path, and exact source SHA.
- Every benchmark round must complete with zero failed requests and required finite metrics; warmup and measured stability must satisfy the maintained runner.
- Candidate B must improve median output throughput and total-token throughput by at least 1% versus the A/R control, while median/P99 TTFT, TPOT, ITL and E2E must not regress more than 3%.
- A/R control drift above 5%, any source/service identity drift, unknown PPU0–7 process, graph failure, request failure, or 8030 health/identity change invalidates the comparison.
- Only the frozen 8031 root PID and its verified descendants may be stopped. Port 8030 and its process tree must never receive a signal.
- Promote to P16384/D1024/C64/N128 only if the D128 A/B/R passes. Otherwise reject and leave 8031 stopped.

## Evidence boundary

The existing P4K op010 A/B/R passed at D128 and D1024, but it does not establish a P16K gain. This experiment is a P16K milestone and is not formal performance acceptance. Formal accuracy remains blocked by the inherited GPQA 170/198 result below the frozen 88% threshold.

The initial service58 A attempt produced only two warmup rounds before being deliberately stopped. It overlapped the perf-014 Decode baseline on the same host and therefore contaminated both measurements despite using a separate device group. No measured A rounds exist and no A/B/R conclusion is allowed. Service58 was stopped by its frozen PID/start-ticks, 8031 is closed, PPU0–7 are free, and 8030 remained healthy. Perf-014 is now complete; resume with new unique service/run IDs from a fresh A while 8030 remains idle and healthy.

## Fresh A/B/R result

Fresh service61/service62/service63 completed all graph, path, source-identity, 8030 guard and 3+3 performance steps. A/B/R measured output-throughput medians were 50.600131/52.206263/50.691990 tok/s, and total-throughput medians were 6527.416956/6734.607910/6539.266724 tok/s. B relative to the A/R mean improved output and total throughput by 3.0806%, duration by 2.9886%, and P99 TTFT/TPOT/ITL/E2E by 3.0153%/3.0752%/2.8763%/2.9800%. A/R output drift was 0.1815%. Every measured round completed 64/64 requests with zero failures; warmup output spreads were 0.1476%/0.2744%/0.1330%.

The maintained comparator returned `incomplete`, not numerical `failed`. The frozen contract declared only the blacklist environment variable as changeable, while the role-specific manifests also changed `/evidence/role`, runtime/log paths and startup-log hashes. The comparator therefore emitted `cases={}` and refused attribution. The contract and manifests were not modified after measurement, D1024 was not run, and the result is retained only as strong diagnostic evidence.

- Evidence root: `/mnt/nfs/users/jinghao/qwen3.8-flash/20260919-qwen38-flash-next-ppu-e2e/op023-p16k-native-mmout-provider/fresh-abr-service61-63`.
- A/B/R run-record SHA-256: `856d306b4d75ecc064b7cc1baf5ce3813d8e962b507d8c8363ef2794cd20ecdf`, `519743ae62a3e081fbfde255191eebc82ea50ad064a718fdf680b7fe782d67ac`, `5c34513cd20930226d6b5d4fa05fd1f335a7c9edff9300e5b44c26a836ffe9ad`.
- Comparator SHA-256: `a37d04925ec44b489d792882a989458a7526175dd1ef0c0178eda17ad66d87d7`.
- Cleanup: service63 and its exact process tree stopped; 8031 closed; PPU0–7 free; 8030 remained the frozen healthy service.

## Repaired-contract result

The incomplete service61–63 evidence was not relabeled. A new contract was frozen before any replacement measurement: normalized service manifests set role-specific evidence to a stable null value, keep runtime/log/role material in sidecars, require A-to-B identity diff to be exactly the blacklist environment path and A-to-R to be empty, and evaluate output, total throughput and duration against the A/R midpoint.

Fresh service80/81/82 passed all identity, graph, dispatch, source and performance gates. Every role ran 3 warmup plus 3 measured rounds; every round completed 64/64 requests with zero failures. Container-view guards proved all roles loaded `/workspace/FlagGems/src/flag_gems/fused/qsa.py` SHA `e18fbb229d9c4a5c2b06a6858ae4679596e1a6f971a4ff8878acbbc4f469db23` from candidate container `9b65cc77...` and retained the static-score wrapper.

| Role | Output tok/s | Total tok/s | Duration (s) |
|---|---:|---:|---:|
| A, FlagGems `mm_out` | 50.771875 | 6549.571908 | 161.349171 |
| B, native `mm_out` | 52.430219 | 6763.498208 | 156.245772 |
| R, FlagGems `mm_out` | 50.688291 | 6538.789484 | 161.615235 |

B versus the A/R midpoint improved output and total throughput by 3.3513% and reduced duration by 3.2427%. All median/P99 TTFT, TPOT, ITL and E2E metrics improved about 3.01%–3.27%; A/R output drift was 0.1648%. The maintained comparator returned `passed`, `issues=[]`, with A-to-B changed path only the blacklist append and A-to-R empty. Comparator SHA-256 is `69553cba0138f4a8640fd2574134b10aec1d7038d928c13ae37aad8792f9ec5e`; final decision SHA-256 is `df52e7867206c90a73c10a359c58606c153ca07a26d31dd83f69c19af315d2ac`.

Evidence root: `/mnt/nfs/users/jinghao/qwen3.8-flash/20260919-qwen38-flash-next-ppu-e2e/op023-p16k-native-mmout-provider/repaired-contract-fresh-abr-service80-82-qsa-guarded-v2`. The result retains native `mm_out` for the current P16K combination but remains a D128 milestone; D1024 was not run or inferred. A/B/R services were precisely stopped, 8031 and PPU0–7 were cleared, and retained 8030 remained unchanged and healthy.
