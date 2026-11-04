# op-001-metax-gqa-decode-scheduler

状态：精度定位中，operator/improve，实验补丁尚未部署。完整GPQA77.27%低于冻结80%；端到端性能未测，不能签发正式精度gate或宣称优化达标。

## 目标与实际路径

目标为mx-59、Qwen3.6-27B、TP2 BF16，正式场景依次P1K/P4K/P16K/P32K、D1024/C64/N128。先冻结P1K作为当前目标；缩减里程碑仅服务该目标，不替代正式四场景。

Plugin AttentionFLBackend→flaggems_vllm.ops.attention→flash_api→MetaX scheduling/splitkv。每rank Q12/KV2/D256，GQA6。模型64层中16层full attention、48层linear attention，本改动仅full-attention Decode。GQA交换将单query重排为6行，原调度普通Decode只允许max_q≤4，导致目标落入legacy。

## 实施、边界与回退

私有`/workspace/FlagGems-vllm`仅修改MetaX的`scheduling.py`和`splitkv.py`。BF16 paged、非local/无dropout等原外层能力约束保留；新增guard要求head交换、seqused_k、D256、packed rows5..16、total_q=batch*rows、Q头等于KV头、maxK>16，才允许现有SplitKV，tile M16/N16。显式num_splits=1保留关闭功能。

首个版本暴露B1输出非连续stride被新连续FP32 partial缓冲沿用的问题；修复给partial独立row/head/batch strides，merge继续使用caller输出strides，且不再临时修改params。未改kernel数值算法、Plugin、vLLM、权重或tokenizer。

容器由源有效适配状态快照复刻，image_lineage verified、mount_parity passed、原Python源码和git状态一致。源码在未挂载的私有/workspace；源0/1卡8002保留，新2/3卡18002服务不能与历史配置直接计算精确收益。

原文件在私有`/opt/fa-opt-backup/`，候选字节在/public-flash/jinghao/qwen3.6-27B/optimize/flash_attention/20261012-qwen36-27b-metax-flash-attention/patches/final-candidate-{scheduling,splitkv}.py，切换仅用已保存commands/switch-source.py并校验字节，禁止git reset。当前独立服务已撤回两处补丁，用于原路径GPQA精度复现。

## 正确性与路径证据

首轮78项54通过/24失败，全部失败在B1。accdiag-001定位：无split误差0.000383，split约0.16，原out strides(256,1536,1)与partial应为(512,256,1)不一致。修复后原78项全部通过，含48 GPU项（ratios5/6/8/16，pages16/32/784，B1/B4，auto/3，非连续Q/out/cache/table、空KV/动态KV、FP32 reference/LSE和两次graph replay）。

额外长KV8项全部通过：GQA6/page784、KV30001/65537、B1/B4、Q幅值1/4、动态KV及非连续布局、graph两次回放。CPU9600 selector对比中9504选择不变、96项变动全部落入新增guard；仅静态CPU证据。

附加非目标失败如实保留：18项forced M4/D256编译断言在原SplitKV复现；默认fallback在模型驻留时未完成已安全停止，incomplete。已有M16短query/长K的36项中30通过/6严格FP32容差失败；9组代表性original-contiguous与candidate-strided结果逐元素bitwise相等，证明这些代表性误差继承，不能改写为36项通过。证据results/accdiag003-inherited-bf16-cancellation.json。

真实服务P1K/D32/C64/N64 trace两rank均512次partial/512次merge、32次graph launch；16 full-attention层×32 Decode轮对应。generic varlen144次包括Prefill与mixed query，不是纯Prefill设备时间。Profiler-on耗时不作为收益。

## 算子性能证据

BF16 Q12/KV2/D256、page784、maxK参数262144、graph完整API调用包含布局copy/partial/merge，同GPU/进程5轮交错、每轮40次replay，所有测量保留。

| B64形状 | baseline ms | candidate ms | revert ms | 加速 |
|---|---:|---:|---:|---:|
| KV1024 | 1.143482 | 0.307776 | 1.143277 | 3.715× |
| KV4096 | 4.450733 | 0.931104 | 4.454560 | 4.780× |
| KV16384 | 17.701721 | 3.413011 | 17.707584 | 5.187× |

最大绝对差≤0.0009765625。完整B1/B16/B64×三KV×两maxK参数在state.yml及results/op001-micro.json。证据等级reproduced仅限算子，不能外推模型吞吐。

## GPQA失败与精度定位

C8早期固定前10题、输出cap2048：strict40%/flex70%，无超时，仅短输出观察。随后正式同固定198题、seed42、temperature1/top_p0.95/top_k20/max_gen_toks30000、C32，strict阈值80%在测量前冻结。

候选正式153/198=77.272727%，failed，无gate。198唯一题、多filters、实际采样配置、原生metadata、数据来源及样本SHA复验有效。45道strict错误中18道达到30000token上限，另27道未截断答错；不删题、不改变阈值或过滤器。该观察不证明补丁导致失败；原路径同契约正式分数为156/198＝78.79%。

accdiag-002冻结候选02的服务身份、配置、题目和原生结果。结果SHA `55d2d09152439721e56343c247f3fbb449f5673287949845c9c57cedcbe7b288`，样本SHA `6b10add2df7252b66441413a5deab7efc230670d0f50210d482665e1b5982199`，详情results/accdiag002-frozen-failure.json。

已在独立容器仅撤回本任务两处源码，用原配置和同契约启动baseline-01正式198题复现；输出与缓存使用新命名空间。复用30分钟监控`qwen36-metax-flash-attention-op001`，不重复创建，终态停用。对温度1/C32的两个分数差异仍需结合随机性和样本级证据，不能单轮差异直接宣布根因。

AGENTS第7节及精度定位Skill要求阈值失败时暂停叠加性能优化。已询问用户是否允许本案例诊断性baseline/candidate/revert；未获明确答复不发送性能流量。即使允许，也不能签发精度gate或正式验收。

## 后续与PR边界

P1K/D128/C64/N128 targeted计划冻结并dry-run通过，尚未执行：4预热/3测量，末3预热spread≤5%，测量全保留；吞吐+5%，meanTTFT/p99TPOT守护≤10%，baseline/revert漂移≤10%。晋级需有效GPQA80% gate和对应正式P1K，最终覆盖四原始场景。

源码与现有用户测试review补丁/public-flash/jinghao/qwen3.6-27B/optimize/flash_attention/20261012-qwen36-27b-metax-flash-attention/patches/op001-review-source-and-tests.patch，SHA256 `03c16f53a156a261ca86e710a08fb1e5ae5058fca150c0e8b1b0342c488d23e1`。AST及git diff --check通过，格式工具未安装，其他平台/模型未测，pr_readiness experimental。未提交/推送。

全部原始证据在/public-flash/jinghao/qwen3.6-27B/optimize/flash_attention/20261012-qwen36-27b-metax-flash-attention；本地state.yml保存配置指纹及索引，不复制大体积样本、trace、日志。下一步同契约精度二分；取得有效gate或明确诊断性能例外后才进入端到端性能验证。

原路径baseline-01预检通过、原始task/data provenance逐项相等；服务身份qwen36-fa-opt:52746:1791777949.05，评测PID1925，进程回执manifests/gpqa-baseline01-process.json。两rank原路径trace各190次mcGraphLaunch、992次generic varlen、SplitKV零次；launch计数不是Decode步数。正式评测使用独立UUID缓存。

Seed接口核验：正式wrapper的CLI/harness seed为42；原生model_args没有seed，实际API类默认self._seed=1234并发送到HTTP。baseline/candidate采用完全相同接口；此前“seed42”仅指harness，不能解读为HTTP seed42。未改变已冻结配置、题目或阈值，原始证据见manifests/gpqa-seed-interface-audit.json。

完整原路径GPQA已结束：156/198＝78.787878%，低于冻结80%，无gate。原生task/config/service/题目内容来源验证通过；396行覆盖198唯一题及strict/flexible各198，超时0/拒绝0。两个路径的doc/target/arguments完全相同；strict双方正确149、仅原路径正确7、仅候选正确4、双方错误38。原路径也未达标，标记inherited-accuracy-blocker；候选少3题的差异尚未因果定位，不能以单次分数断言补丁无影响或导致退化。结果SHA4e0e69a3aa7cf1069636506b33ceae7a3d2ed54c15976f569612a1d477ea5009，samples SHA790b431bbf62de59f33ca946e4d3163a697a9b754749ea237836811f4d819d39，完整路径见state.yml。监控已PAUSED；当前heartbeat仅只读核验、未重启/修改评测或服务。原路径18002无运行/排队请求，保持现状；端到端性能仍未测，诊断性例外待人类明确答复。

用户2026-10-12要求继续精度原因定位：accdiag-004离线审计确认生成采样匹配模型自带配置，无非截断missing strict regex、无明显正确final tail被strict误拒。原路径14题到30000cap，其中11题strict错；候选18题cap全部strict错。发现GPQA helper的方括号删除损坏12题科学选项，doc171四个不同公式被压成四个相同字符串，`.index`把gold从原始shuffle正确C变为A。仅移除删除regex的内存隔离helper复现可恢复12题选项及doc171正确标签，198原始问题不变。当前在原服务进行doc171/81两次原/恢复对照，C1、同温度/seed/30kcap，属于最小诊断，不改全量旧分数或签发gate。证据及SHA见state.yml。

修复与重测：doc171两次原/修复对照均B错误→C正确，采样/服务/seed一致。额外doc81原prompt返回A错误（7788 tokens），修复对照未完成已取消，保留5/8计划请求结果，不写成全部通过；取消控制脚本遇到第五响应完成竞态，诊断客户端已退出143，记录PID未落盘缺口，模型精确停止/重启均有独立绑定回执。用户明确批准修复任务后全198正式重测。新评测容器qwen36-fa-gpqa-fixed-20261012只改私有helper删除方括号的regex，旧评测器不改；新provenance SHAa94d859ab2f6855592fc927f6dc44614204c04bef08afc64736ad7cf64379f15，原198题内容指纹不变，仅12条处理后doc变化。模型candidate04与candidate02所有稳定字段相等；重新校验22个权重/tokenizer文件、双rank各190mcGraphLaunch/960partial/960merge。正式preflight通过，评测PID337已启动，harness42/API1234/C32/temp1/top_p.95/top_k20/cap30000/strict80均不变。终态按已有工具验真和达标gate绑定，监控复用原ID每30分钟并在终态停用，未启动性能流量。完整结果仍pending，不能宣称数据修复已恢复模型80分。

修正版完整正式终态：159/198＝80.303030% ≥80%，passed；原生198唯一、全部filter/题目内容/模型/endpoint/配置来源核验通过，无超时/拒绝；exactcurrentinstance/source复验一致，gate issue及check通过。结果/样本/gate SHA及路径在state.yml。数据修复12题旧4正确/新5正确，未改prompt186题中9错→对/4对→错，总+6不全归因数据修复；39道剩余错误不宣称已定位。完整阈值阻塞在用户批准的新契约下解除，当前candidate04可在正常性能门禁前提下继续P1K；本次heartbeat未开展性能或服务变更。监控已PAUSED，重启需正规rebind、代码或配置变化需重评；旧153/198和156/198证据不覆盖。
