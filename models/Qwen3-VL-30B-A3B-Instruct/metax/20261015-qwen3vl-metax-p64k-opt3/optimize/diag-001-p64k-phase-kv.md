# diag-001-p64k-phase-kv

状态planned；本轮user明确优先P65536/D1024/C64/N128，主指标稳态输出吞吐，守护TTFT/TPOT/ITL/errors。源qwen3vl-flaggems-e2e-20261013/8000/GPU4,5保持运行，创建新独立容器GPU0,1，保留用户MoE JSON及sort int32，不新增算子黑名单。

初始只读证据：opt3三轮67.74/68.03/68.09token/s，P99TTFT约928秒、平均TTFT约661秒、平均TPOT约96.7ms。源服务累计78次KV抢占，仅为整段服务累计，不归因本场景；需在独立场景测增量与重算。Prefill/Decode/Mixed热点均待分解。手测原SUMMARY预先跳过Run1，所有原始轮保留，不混用稳态native结果。

采用performance技能targeted/performance_only；必要时profiling capture→analyze，两rank及graph路径核验。完整P64K一轮约1927秒，先冻结自身可比的缩减milestone，保持P64K、明确N/C/D差异，记录KV容量与preempt增量，再晋级原始C64/N128混合负载。不会将缩减收益冒充原始目标收益，也不执行正式GPQA。

环境门禁、阶段探针的实际契约、原生路径及SHA在state中持续更新。尚无新增性能结论或产品改动。

## 当前环境与三阶段取证

新容器 image_lineage/mount_parity passed，四仓库内容与源opt3完全一致；16请求C8健康、两worker graph至少两次重放和16次后hook恢复均通过，MoE GEMM2 stage1 JSON、sort int32与FG注册命中已核验。KV容量529824token；8×(65536+1024)=532480，差2656token，可能引发Decode后半段或新Prefill准入的容量冲突，尚待受控增量证实。

profiling capture→analyze：P64K/D16/C1/N2 Prefill、P64K/D256/C8/N8长KV Decode、P64K/D128/C16/N16 Mixed，各1warm+1profile，0.7/20/0.8、ignoreEOS、range0，128iterations上限、两rank。计数增量包含两轮与原生客户端test请求，不能当成纯测量轮计数；profiler时间不作收益。原始P64K基线约32分钟/轮，先用上述有明确差异的诊断探针选方向。

相对opt2所有三轮中位数的手测趋势：P4K+15.31%、P16K+5.77%、P64K+1.67%。这是用户不同批次的观察，不是独立容器可控A/B；长Prefill稀释排序收益为待trace检验的解释。
