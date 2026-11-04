# op-005 采样局部整数直方图

状态：**retained-targeted-performance-only**。分类 operator/improve；目标 P1024/D1024/C64/N128 的稳态输出吞吐。已回写源容器 `qwen3vl-p64k-opt-20261015` 及独立验证容器。当前9999服务健康且未重启，新代码下次重启导入；18144验证服务已停止，用卡已释放。

## 优化方向与瓶颈依据

双rank阶段trace中，Decode rank0的64步累计：MoE1159.384ms、radix sweep291.676ms、histogram81.156ms（64次，约1.268ms/次）。这些累计活动可能重叠，不是关键路径或端到端时间。Mixed trace仅覆盖初始64步，完整finite batch由无profiler测量验证。

op003计数跳过仅约3%完整算子加速，op004桶分组16无M64收益且M1变慢约24%，均未合入。实际热点支持局部整数histogram方案。

## 优化内容与适用边界

仅修改FlagGems-vllm中 `src/flaggems_vllm/runtime/backend/_metax/ops/top_k_top_p.py` 的 `_guarded_hist`：一次读入8192元素tile及有序整数key，用八个带mask的16桶 `tl.histogram` 生成计数，替代逐桶比较累加。沿用原grid、8轮4bit radix和全部下游浮点计算、排序、过滤及RNG逻辑；不是新增公开算子或dispatch。

范围沿用FP32 contiguous M<=64、1<=V<=262144，k int32/int64、p FP32。计数仍为int32，单行上界262144，未降低浮点dtype；原早退、metadata检查和Plugin fallback不变。当前MetaX C550/FlagTree3.6.0实测，其他架构/版本未测。

最终文件SHA：`941bdc544401872327ee299aa0ab73387b43893e363f8c25b465fb607eb551eb`。回写后审计两容器四仓均仅该文件变化；Plugin、vLLM、FlagGems gems-opt、MoE、JSON和其他配置与入口一致。

## 正确性与路径命中

以冻结的原FV实现为本轮数值oracle：47组输入、129次完整过滤对拍和sorted-values逐位检查通过，覆盖BF16精确/普通FP32/混合block、仅一行非BF16、M7/M63、最大词表、任意FP32位模式、NaN/Inf/±0/ties和metadata边界。5次算子graph capture、20次变化输入replay通过。

三个TP2服务均完成capture，每rank至少16次replay，smoke/C8和十题固定科学问答输出健康检查通过。固定算术请求均答42；ignore_eos定长请求中的重复仅记录为诊断现象。原路径trace命中实际radix kernels；候选/基线非临时service manifest仅 `flaggems_vllm_sha256` 不同，私有库导入和FlagOS MoE已核验。

**正式GPQA按用户要求未跑，不签发正式精度或最终四场景验收。**

## 性能效果

完整采样M64/V151936/非BF16：原7.527936ms、候选6.469888ms、回退7.528192ms；延迟降低14.05%，speedup1.1635×。这不是模型加速比。

端到端同一P1K/D1K/C64/N128，temperature0.7、模型topk20/topp0.8、ignore_eos、prefix cache关闭。每实例采样M1..64预热后，固定3轮预热、2轮计时；末两轮预热TPS差幅<=8%准入，全部计时轮保留。CLI seed固定随机输入，未额外固定每请求采样seed，不声称输出逐token复现。原性能脚本不传temperature，当前vLLM默认None沿用模型0.7，与本轮一致。

| 角色 | 两轮输出tok/s | 中位tok/s | 计时轮差幅 | P99 TTFT ms | P99 TPOT ms | P99 ITL ms |
|---|---|---:|---:|---:|---:|---:|
| 基线 | 1432.04 / 1478.17 | 1455.10 | 3.17% | 3577.61 | 43.11 | 44.20 |
| 候选 | 1505.09 / 1514.63 | 1509.86 | 0.63% | 3699.06 | 41.92 | 42.89 |
| 回退 | 1494.46 / 1475.65 | 1485.06 | 1.27% | 3610.59 | 42.65 | 42.92 |

候选较基线+3.76%，较回退+1.67%；基线/回退漂移2.06%。P99 TTFT较基线+3.39%，P99 TPOT/ITL改善约2.75%/2.97%，满足预冻结10%守护。每轮128/128成功。比较器按原2%主指标、8%波动/漂移门槛判passed，scope仅performance_only。P99是两轮各自分位数的中位数，不是合并请求P99。

收益较小且有时间漂移，保留此优化点，但不把3.8%作为稳定、孤立、可外推的模型收益。未与历史opt9 CSV计算加速比，未将启动、首轮或profiler-on时间计入性能。

## 决定、风险与回退

仅保留op005，不合并op003/op004。源与独立容器已回写相同的测试字节，其他配置不变；当前9999不重启，下一次重启导入。验证GPU0/1及补充检查GPU2已释放，仅原9999 GPU6/7继续使用。未提交或推送代码。

源备份为远端 `patches/source-container-before-hist.py`；独立容器备份 `patches/sampling_hist_base.py`。回退应在用户控制的服务重启窗口内，先确认当前SHA941bdc，再恢复相应备份、验证原SHA；不使用git reset覆盖其他改动。

下一轮如继续：先采新稳态三阶段证据，再按host gap/通信或MoE访存重排，不重复盲扫tile。优化后未reprofile；不推广到其他平台、模型、场景或长期容量。单案例不足以修订SOP。

## 外部证据

远端根目录：`/public-flash/jinghao/qwen3-VL/20261021-qwen3vl-metax-p1k-opt9`。全部命令、plan、原始结果、日志、trace及补丁在该目录，必要SHA见state.yml。

- 比较：`results/hist-target-comparison.json`，SHA `1658ec0f8f5b4026aa6ced16efb02310014daa1a23d3c8cc7c8733e72d659a0c`。
- 回写：`results/histogram-retained.json`，SHA `0d25916cdd3423206dee519a7821f2c02415640488eb5268e65f27826d07c961`。
- 回写后审计：`results/stack-after-retain.json`，SHA `19ed55603a8082fe9e0d1bc2d673d5da1cc106089b96c0dc7fb4468e22774169`。
- 补充数值/graph：`results/sampling-hist-extra-validation.json`，SHA `c8dececb051ad33fa56c1b710fcdead1ca81eca6dbf10056cd8034843cced60f`。
- 完整B/C/R：`results/performance/hist-target-{baseline,candidate,revert}/run-record.json`。

## 实施前计划与阶段记录

以下保留实施前冻结的设计表和推进记录；当前状态以以上最终结论及state.yml为准。

Planned before implementation. Direction operator/improve, steady P1024/D1024/C64/N128. Runtime Decode trace rank0: histogram64calls81.156ms (~1.268ms/call), sweep512calls291.676ms, MoE6144calls1159.384ms. Originalhist loads same input once per each of8passes and forms16x1024comparisonaccumulators; candidate reads8192keys once, computes eightmasked16bin local histograms and identical integer global atomic adds. No dtype, float math, sort order, output/RNG or API change. No op003/op004 combined. Risk: compiler histogram lowering/registers.

| Project truth | Frozen choice |
|---|---|
| Editable | Independent container private FlagGems-vllm MetaX top_k_top_p.py, _guarded_hist only |
| Read-only | vLLM, Plugin, FlagGems, MoE, test oracle and benchmark workload after freeze |
| Build | Triton JIT; no C++ build |
| Validation | External standalone original/candidate bitwise masks, sorted values incl NaN, ties, signed zero; device graph changed-input replay twice; TP2 smoke/C8 |
| Benchmark | Original vs candidate vs revert full sampling GPU event median, interleaved; then maintained no-profiler E2E runner |
| Active set | FP32 contiguous M1,8,32,64; V nonaligned and151936; exact BF16, fractional(.7), mixed blocks; k int32/int64; p FP32 |
| Aggregation | Per-shape medians; no geometric average disguising regressions; target full E2E process/round medians |
| Timeouts | operator validation300s per stage, E2E900s/round, controlled service startup1800s |
| Profiler | Torch profiler in isolated service, ranks0/1; inactive for performance |
| Autotune | Exempt: fixed existing8192elementCTA coverage,local16-bin integer histogram; NVIDIA unmodified; MetaX-only device guard; NVIDIA unmodified |
| Fallback | Existing unsupported NotImplementedError and Plugin original fallback unchanged; no torch compute fallback |

| Alignment contract | Choice |
|---|---|
| Reference | Current exact runtime FV operator and vLLM ee0da84 apply_top_k_top_p_pytorch |
| Input | FP32 contiguous rank2 cuda, 0<=M<=64,1<=V<=262144; optional contiguous k int32/int64[M],1..V; p FP32[M],0..1 |
| Output | Same storage/in-place logits, FP32, masks -inf; preserve kept bits/tie policy |
| Dtype/promotion | No change; BF16 used only for exact representability guard/count path; FP32 radix for nonexact values |
| Semantics | Preserve NaN/Inf/signed-zero/ties by original output oracle (no assertion that all such logits are model-valid); no RNG |
| Autograd | Inference forward-only unchanged |
| Unsupported | Existing metadata/layout/size cases unchanged |
| Torch usage | Test/reference/allocation only, no added production torch compute |

| Path | Trigger | Implementation/config | Risk/check |
|---|---|---|---|
| early return | Empty M or no filters | Unchanged | Alias/zero tests |
| exact BF16 | Every CTA bad==0 | Unchanged BF16 path | Exact full-sort/mask parity |
| fractional/general | Any bad>0 CTA | Exact same FP32 radix global hist counts via masked local histogram; sweep unchanged | Mixed CTAs/global batch fallback/graph changed inputs |
| unsupported | Existing metadata checks | Existing Plugin fallback unchanged | Boundary rejection |


Freeze: hist-comparison.json, minE2E2%,guards<=10%,spread/drift8%,3warm+2measure. Micro>=5% supports promotion; no product source edit before external bitwise fullfilter andgraph. GPQA deferred by user,performance_only.

Results:not_run.

External fullfilter105 comparisons across35data/shapegroups and4captures/16changed-input graph replays passed bitwise. Full sampling M64fractional original7.527936ms,candidate6.469888ms,revert7.528192ms (14.1%less latency,16.35%speedup). M8fractional1.467136→1.307392ms, M32fractional4.025088→3.490048ms. BF16exactM64unchanged. Promote to full target maintained B/C/R, not yet retained. Command remotecommands/run_hist_bcr.py; contract hist-comparison.json frozen before all runs.

Original full target baseline complete:3warm+2measure, all128requests successful eachround. Last2warm TPS1511.033/1439.135, spread4.874%; measuredTPS1432.036/1478.166,median1455.101,spread3.170%. Median per-round P99TTFT3577.614ms,TPOT43.109ms,ITL44.199ms,E2EL46958.266ms. Native runSHA96fef861f28799b42585e1aee3ab849aead7d8ff510f1fcf3d42fb04e9bdbb7a. CandidateprivatepatchSHA941bdc544401872327ee299aa0ab73387b43893e363f8c25b465fb607eb551eb,service startup inprogress; source usercontainer unchanged.

Candidate TP2 service graph capture and16replays perrank, nine smoke/C8requests andten scienceprompt C8 regression passed. Nonvolatile service manifests differ only in flaggems_vllm_sha256; launchargs,model,tokenizer,Plugin,gems-opt,vLLM,hardware,image,prefixcache preparation identical. Candidate healthSHAbcb85155dcede44a1b987be9c5a26268f4fe10bf1f2ac6bcc694bbab903e07a4; scienceSHA8080de5d5ad53232905a56d508e34233d139757583b9a0acb9018d58347aec05. External fullfilter/graph probeSHA52a47f5b007bd3a0c31f9a823e641ab8a10a95ce1ee94cd7aba526ee2757cf90. Candidate3warm+2measurement now inprogress.

Candidate full target complete: measured1505.094/1514.627tok/s,median1509.861 vsbaseline1455.101 (+3.7633%),all128/128success. Median per-round P99TTFT3699.061ms (+3.39%),P99TPOT41.925ms,P99ITL42.888ms; meanTPOT40.583ms. Candidate runSHA307f996723494189789e2b769106580140764e1b265cf5ebbb6855c285bf5c15. Original-source revert is starting; retention awaits full BCR/drift, no source usercontainer writeback yet.

FullBCR frozen comparison passed (scope performance_only),comparisonSHA1658ec0f8f5b4026aa6ced16efb02310014daa1a23d3c8cc7c8733e72d659a0c. TPS B1455.101/C1509.861/R1485.058; CvsB+3.763%,CvsR+1.670%,B/Rdrift+2.059%. Positive observed but modest;3.8% is not a stable isolated causal estimate. Additional12groups/24filter comparisons/1capture4changed replays passed (SHAc8dececb051ad33fa56c1b710fcdead1ca81eca6dbf10056cd8034843cced60f). Combined external coverage47groups/129fullfiltercomparisons/5captures20changedreplays. Revert own18144 stopped before extra tests; user9999 untouched. Before-retain full4repo audits bothcontainers passed SHA1365a8c531575e03ef5a6ad8bfec18d2d004a5dc06568fe61b61b192c1ceba95. Execute archived retain_sampling_hist_v2.py SHA41fed1561b0702fce361f9feec5ca14e5fb920fd606d658bd32c5b93f03e16de, then after-audit.


## opt10 后续只读诊断

用户重启生产服务后出现按batch M补编译的慢轮。此前受控BCR显式预热M1…64，普通启动脚本不包含该步骤，不能直接比较不同预热状态。见 [diag-006](diag-006-opt10-throughput-variance.md)；产品代码和配置保持原样。
