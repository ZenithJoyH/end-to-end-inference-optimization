# PR1067 沐曦59硬件验证

状态：**数值/Graph通过，配置性能不适合晋级**。[PR #1067](https://github.com/flagos-ai/FlagGems-vllm/pull/1067) 已补入GPU测试与负优化结果，仍为草稿；专用验证容器已停止，GPU释放。无模型请求或其他服务操作。

## 优化方向与瓶颈依据

本轮验证容器内旧MoE调参能否作为最新主线默认值。分类operator/improve/config，目标是BF16/C550/E256/H2048/I256/topk8的M64 Decode shape与M8192 Prefill shape；这是单GPU算子核验，不能等同模型Prefill/Decode阶段时间或Mixed端到端收益。模型完整GPQA/ERQA及四场景性能均未运行。

用户已授权在mx-59使用指定202611020932镜像，并确认目录/public-flash/jinghao/qwen3.6-35B。镜像ID9f420f54与104当前qwen36容器基础镜像相同。依赖为Torch2.8.0+metax3.7.0.7、FlagTree0.7.0+metax.gitfe1d24f6、Gems5.5.0.dev0+ga456722a1、vLLM0.20.2+empty；C55064GiB，驱动3.8.1/MACA3.7.1.5。

## 优化内容与适用边界

新建独立source/verification容器，源仅created，验证容器无挂载；镜像谱系由用户精确镜像ID与源码SHA核验，mount工具只证明empty mount parity，不冒称它能验证lineage。原镜像安装库MoE仍为c4673aea。固定main00f4ed653展开到私有baseline/candidate目录，候选仅生产get_default_config为a288621f；其他生产节点AST相同。每个测试进程以PYTHONPATH选择私有源码，不安装或升级依赖，不修改用户的104/59已有容器。实验打印、GDN、采样、vLLM和模型不变。

主线977已有更新TP2配置及UNFUSE_SILU/BK128 fast path。PR保留该fast path，只拟迁移旧BF16 M64/M8192非快路径设置；不是把旧源码整文件覆盖当前主线。最后追加的fb7c9f94仅新增GPU测试，生产补丁与被测a1913版本相同。

## 正确性与路径命中

main和PR公开flaggems_vllm.fused_experts_impl都实际绑定私有_metax.ops.fused_moe，无generic假命中；完整算子计时记录两个实际launch config。主线11项和PR同11项GPU测试全部通过、0skip，共44次变化输入Graph replay：BF16均匀M1/63/64/65/8191/8192/8193、BF16集中M64/8192、FP16均匀哨兵M64/8192。独立FP32专家投影/SiLU/加权归约，原rtol0.1/atol0.01不放宽；Graph每次先填NaN输出，再以0.5/-0.75两种新输入重放。

81项host配置测试、pre-commit、wheel构建及生产源码打包一致性通过。GPU测试源SHA7d9264fe65716d47b71c35c0567ccef7ff857800f9caeaaa19e68d85e19372fc已随PR提交。无新正式精度gate。

## 性能效果

main/candidate/revert各独立进程，单GPU0；每角色10完整公开MoE和4内部非快路径阶段，共42项，294个测量轮全部保留。完整输入SHA三组相同。统一仓库benchmark.base.do_bench_cudagraph，10次预热调用后最多8窗口，末3窗口range/median<=3%才准入；随后7轮rep50ms取中位数，全部准入。比较基准为main与revert各自中位数的均值；B/R漂移阈值预先冻结3%。

| 场景 | main/revert参考ms | PR ms | 延迟变化 | B/R漂移 | 结论 |
|---|---:|---:|---:|---:|---|
| 完整公开MoE BF16 M64 均匀 | 0.490107 | 0.494771 | +0.95% | -0.16% | 未见收益 |
| 完整公开MoE BF16 M64 集中 | 0.102095 | 0.112001 | **+9.70%** | -0.67% | 性能回退 |
| 完整公开MoE BF16 M8192 均匀 | 2.352887 | 2.348221 | -0.20% | +1.59% | 实际fast path配置相同，不宣称收益 |
| 内部非快路径GEMM1 BF16 M8192 | 1.432250 | 1.632179 | **+13.96%** | +0.03% | 性能回退 |
| 内部非快路径GEMM2 BF16 M8192 | 1.014176 | 1.018635 | — | **+5.86%** | 漂移超限incomplete，不归因 |

独立核验原生终态exit0、42行/每行7轮、输入SHA、实际配置、22项JUnit/44变化输入replay、前后源码及容器身份。报告总状态incomplete_drift_with_valid_case_regressions：单个GEMM2不能得出收益结论，两项明确回退各自通过漂移守护。没有丢轮、放宽阈值或择优补跑。新主线数据不能与旧104pre-977微测混用，旧3.5x不能支持当前主线合并。

## 决定、风险与回退

候选不晋级、不转ready；保持PR草稿并披露负结果。此结论仅否定旧设置相对当前主线的晋级依据，不自动改用户104的c467，也不推断当前模型精度或总吞吐。无任意新kernel调参、profiler、依赖升级或全量评测。

归档后核验专用容器ID/镜像/仅sleep进程，精确停止qwen36-pr1067-verify-mx59-20261104；source保留created、镜像和原始证据保留。结束时mx-smi无计算进程。未停任何源服务或其他容器，没有创建监控。

补交测试时自动审批曾因fork未核实拦截。随后GitHub只读核验用户ZenithJoyH、fork所有权/admin以及官方PR1067同一head，并确认代码无内部路径/凭据/模型数据，重试获准；没有换工具绕过或未解决审批阻塞。

## 外部证据

ROOT：/public-flash/jinghao/qwen3.6-35B/20261104-qwen36-mx59-pr1067-verification-001。

- 独立核验：independent-verification-001/verification.json，SHA899d3082f8c984d832f1d6e68e734cf846a2dd80c30cdf3ea3367db25002dabc。
- 两组GPU测试：main-gpu-tests-001.log、candidate-gpu-tests-001.log；JUnit在independent-verification-001，各11项0skip/0error。
- 三角色原始结果：runs/{main,candidate,revert}-benchmark-001/report.json，完整7轮和输入/launch配置均保留。
- 关闭回执：closeout-001.json，SHA60ffebe844938b948db7e6fefb5b4991aa18ce56b75f48f265081cadeef2f85b。
- artifacts-closeout-001.json为自身log闭合前中间索引，保留；artifacts-final-002.json在原生退出后对稳定文件重新生成，是最终索引，无旧证据覆盖或GPU重放。
- PR：https://github.com/flagos-ai/FlagGems-vllm/pull/1067，head fb7c9f9461e5b88b64617eb996db42636ddfc423。

本地记录补充：本case YAML、42条指标及文件链接核验通过。项目全局check-project-records被其他案例文档字段和Qwen38过程产物违规阻塞，保留原错误且不修改无关任务；不把全局检查写成passed。已回读PR新GPU测试，发布字节与实际执行7d9264fe完全相同。
