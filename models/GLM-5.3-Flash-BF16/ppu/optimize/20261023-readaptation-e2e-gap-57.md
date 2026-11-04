# 20261023-readaptation-e2e-gap-57 重新适配后端到端差距定位

## 范围与状态

用户要求分析当前`glm5.3-flash-opt-0924`结果与重新适配前的gap。本轮只读分析已存在CSV、源码、服务日志与GET metrics，不发模型请求、不停止用户测试、不改代码或参数。性能Skill只消费既有结果，不启动新模式测量；规划Skill用于跨版本差异复盘，具体算子路径用key-operator-analysis核对。

实际API为`3882470:545289590`，用户自行按原脚本重启；TP16/BF16/MBT32768/maxseq64/maxlen80000/FULL_DECODE_ONLY/关闭前缀缓存不变。先前Agent交付实例`3866321`不是当前测试实例，不静默改绑旧gate。

## 已完成结果

用户目录：`/mnt/nfs/users/jinghao/glm5.3-flash/test/benchmark_results/glm5.3-flash-opt-0924`。本次脚本三轮、SUMMARY取第2/3轮算术均值；保留所有轮，不把脚本首轮排除当作新预冻结稳态证明。

| workload，D1024/C64/N128 | 三轮输出 token/s | SUMMARY | 成功数 |
|---|---|---:|---|
| P1024 | 1022.94 / 1096.02 / 1096.59 | 1096.30 | 每轮128/128 |
| P4096 | 343.08 / 425.07 / 388.78 | 406.92 | 每轮128/128 |

P4K当前平均TTFT37222.43ms、平均TPOT119.75ms；2026-09-23历史用户同P/D/C/N记录为输出979.12token/s、平均TTFT11437.97ms、TPOT53.53ms。旧文件原SHA见state；当前远端只剩新结果目录，旧原件尚不能现场重验，跨版本数字仅描述历史差异，不能拆出单算子净贡献。P16K仍在用户测试中，不把未完成数字当结果。

当前CSV SHA：P1K`9f00c652cb4ee90ed9d429ec45251c0511c4c00bc02fc9c5b54140e243d245f2`；P4K`7905356a613426361cda39cf4f38af84fa91b847a349a078acd84321c5aeda35`。用户runner`/mnt/nfs/users/jinghao/glm5.3-flash/test/vllm_perf.py` SHA`df2fe8793b5d521e1160fe51404afc66efbe847363c144445c6bbe1e65ecaa59`，没有独立原生JSON/冻结比较回执。

## 路径及框架线索（先期观察）

1. 新日志实际`flash_mla_sparse_fwd`、长Prefill KDA/conv和mHC选中`glm5.flaggems`；旧Sparse MLA沿thead vendor原生路径。历史点31已证实当时generic H4实现慢于vendor，但不能拿历史micro比例直接解释本轮完整差距。
2. 用户P16K正在运行的现场：44running、16capacity-waiting、KV约93%、累计抢占2次。只证明当时容量压力，不把累计值归给P4K或直接认定唯一根因。
3. 当前cache metrics显示自动block_size320000/mamba_block_size80000/num_gpu_blocks1689；启动汇总显示135120000tokens与1689x，但与实际占用/排队并不直接对应，必须核对混合缓存组的真实页粒度与分配，不能照日志宣称实际可驻留135M token。

尚未做新profile、受控backend对照、缓存布局实验或修复；不将点56同缓存+2.7148%当作恢复旧路径性能的证据。后续优先从跨版本缓存页粒度和真实Prefill算子路径证伪，而不是继续微调align。

证据采集命令先保存到点56`user-retain-03/commands/gap-capture-v1.py`，在新外部根`/mnt/nfs/users/jinghao/glm5.3-flash/optimize/e2e-opt-20260911/resume-20261023-point57-readaptation-gap/commands/capture-gap-v1.py`保留执行副本；SHA`947b11245919defe640e74d52be355d3d6bda9e6a53af6957346a4d1a7a597cf`。仅读取当前CSV/日志前缀/源码index/白名单进程环境和GET metrics，用户测试继续运行，不对新实例签gate或发生成请求。

## 15:29证据闭环与差异复盘

外部根的`readonly-gap-evidence-v1.json` SHA为`f3365ac77e85a569f727029b57a46e0b051a63f0bf95d7a09560ef4501bbc35b`，保存读取当刻CSV三份、日志前缀字节/SHA、API argv/白名单环境、源码及当前四库源/三库index核验。源码与保留的align匹配；本轮未重启或发送生成请求。P16K此时仅Run1成功128/128、1396.66s、93.85token/s，仍是部分结果，不与旧稳态SUMMARY计算正式回归率。

### MoE：旧特化没有在当前调用库上生效

当前API未设置`VLLM_FL_USE_FLAGGEMS_VLLM`，实际`vllm_fl/envs.py:17–19`默认0。日志选中`invoke_fused_moe_triton_kernel/default.flagos`，其adapter `dispatch/backends/flaggems/impl/fused_moe.py:110–113`因此导入`flag_gems`，不是旧优化承载的`flaggems_vllm`。当前FG与原版的差异只是一份align补丁，没有把旧FGV GEMM2特化迁入FG。

旧[exact-M64 GEMM2](20260919-maxseq64-m64-gemm2-01.md)曾在E288/H4096/I128/topk8下将该时点P1K输出1277.797→1513.513token/s（+18.447%）。这是有历史服务收益的路径，如今不能因FGV安装存在就声称仍命中。旧时点MBT16384，不能把1513.513与当前1096.30当精确同配置回归率，也不能把18.447%直接当本轮损失份额。首个证伪应只恢复实际库/公共边界的同一GEMM2选择；不要全局切开关1，同时更换alignment、激活、topk等路径。

### Prefill/Mixed：长停顿比单个普通Decode step更突出

P4K纯Decode日志（14:54:36–14:55:16、14:59:56–15:00:36）约1126–1165token/s；14:49–14:50及14:55:26后却出现已有43–48个running、generation约0–5token/s的连续10秒窗口，正在接纳后续Prefill，KV仅约29–33%。当前median ITL55.61ms、P99 ITL57.38ms，但mean TPOT119.75ms，支持少量长间隔严重拖慢请求生命周期，不能说每一个纯设备Decode step都慢了一倍。没有raw逐token结果，不能还原每次停顿的精确组成。

当前Sparse MLA实际日志为`glm5.flaggems`，经公共adapter调用FGV普通H4 Triton；旧路径为thead native flash_mla。当前KDA/conv走公共FGV `ops/kda_bounded.py` / `ops/causal_conv1d.py`，thead覆盖目录没有这几个op的定制覆盖，旧配置则显式优先vendor。KDA内部仍复用多个64-token core，不能只凭导出目录说每个数值kernel都变了。历史[点31](20260922-p32k-sparse-mla-bh4-31.md)generic慢于vendor，只支持调查方向，不能替代当前P4K同shape测量或拆出MLA/KDA/conv/MM各自份额。下一profile应覆盖晚到Prefill进入前后，而不是继续只采P1K纯Decode。

### 缓存：容量压力、准入限制和容量统计不能混为一谈

当前`models/glm5/cache.py:48–105`使用独立KDA tensor，没有reference的KDA/MLA slot共享；628–658按所有非tail spec求page字节和、计算共同num_blocks，再给每层分配page×num_blocks。这是需要核算的内存浪费方向，但尚未从运行中group specs重建真实总字节，不能编造可回收容量。

并发汇总669–677以所有compress_ratio=1且非tail spec的最大block_size计算，未排除MambaSpec，KDA的80000会进入max。因此启动日志135120000tokens/1689x不能代表真实MLA可驻留容量；调度block_size320000是组间LCM，不是每个MLA物理页都320000token，不可直接按它估算OOM。

P16K曾约93%占用并累计抢占2→4；15:29快照却只有30.924%占用、15running/49capacity-waiting，所以capacity标签不等于总HBM已满。P4K停顿时也仅约30%占用，不能将全部58.44%差距归因于KV容量；应核对各组spec、manager预算及准入，不改MBT/并发掩盖。

### 可比性、责任范围与下一步

P4K第2/3轮425.07/388.78token/s，极差/均值8.918%超原5%稳态契约。当前脚本仅三轮固定跳首轮，没有native逐请求JSON、冻结稳定窗，seed/采样/客户端与旧记录也未全量核对。58.4402%是历史跨版本汇总的描述差距，尚不是单个改动的因果份额；不能删除慢轮，亦不能把全部差距解释成冷启动。

之前仅证明新路径内部align +2.7148%，没有完成旧优化栈到新公共栈的等价性能验收，这是验证范围缺口。规划57排序为：先恢复MoE实际特化命中，再在公共接口内对照Sparse MLA/vendor并定位Prefill KDA/conv/MM阻塞，再核算混合KV预算和准入。保留公共模型，不恢复旧整套PPU模型分支，MBT/推理参数保持。任何新实验须等用户释放当前测试后冻结单变量、数值/graph和Mixed/阶段守护；本次仅报告，不自动修复或测试。

## 用户下一轮配置问答：只切Sparse MLA算子

用户计划手动设置VLLM_FL_USE_FLAGGEMS_VLLM=1，询问如何切vendor；本轮只读核对，不替用户修改服务。当前独立分派键是 `flash_mla_sparse_fwd`，thead注册impl_id=`vendor.thead`，不是高层`attention_backend`。公共MLA resolver将已有vendor实现纳入同一个OperatorBinding，故无需恢复旧PPU模型。

启动环境可用 `VLLM_FL_PER_OP='flash_mla_sparse_fwd=vendor'`，当前manager仅保留显式顺序匹配候选，不追加flagos；vendor不可用会报错。需要在可用性筛选阶段回退可用`vendor|flagos`，已选择实现的执行错误不被当前binding静默吞掉。平台YAML也可在op_backends下为该键填写vendor/flagos顺序；环境per-op覆盖平台默认（若另设完整VLLM_FL_CONFIG则该文件优先）。重启后应确认实际first-use日志为vendor.thead，并通过目标graph/模型最小回归；本轮未验证切换组合的硬件性能/完整精度。

FGV开关1还会将分步MoE的alignment等共享算子切到FGV，原保留在FG的align补丁不再经同一adapter调用，不能沿用+2.71%净收益。为隔离Sparse MLA贡献，建议两个对照都固定FGV=1，只改该per-op键flagos/vendor；不能同时改全局prefer或attention_backend。
