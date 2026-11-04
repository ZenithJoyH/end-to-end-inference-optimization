# op018：GEMM1 Decode 参数与 opt4 对照

本轮原生 targeted/performance_only 比较 **passed**，P4K/D1K/C64/N128 输出吞吐 B/C/R **899.66/940.41/898.50 token/s**，增量 C/B **+4.529%**，B/R 漂移 **-0.130%**。当前保留 **candidate**，qwen3vl-p64k-opt-20261015 / 8111 / API1044154。这轮baseline已含op017，不是完整opt4或P64恢复声明。

## 修改与边界

用户要求保持采样回退、gems-opt和当前GEMM2不变，先数值和graph再端到端。只改Plugin现有 `vllm_fl/configs/moe/metax/E=128,N=384,device_name=metax.json`，M8..64 GEMM1改为BM16/BN64/BK128/group1/4warps/3stages；M7和M65保护其余M，所有行仍为标准六字段。旧opt4 BF16小M在64/96/128KiB shared-memory选择分支一致，实际硬件helper已核实为64KiB。大M4096仍有warp8→4差异，M8192还有group1→8；两版有效PAIR_GATE_UP_DOT都False（当前缺省False与旧显式False相同），不把这一字段的有无误报成kernel变化。大M未调整。GEMM2整文件SHA **f392cfb568239f036bcc0ce16eadf5a6fa0b3ffbfb549310a916b248b3bfc7ca** 逐byte保持。没有库源码、worker、环境变量、采样、gems-opt/sort、黑名单或vLLM调整。两个GEMM复用token alignment，BM保持一致；is_embedded/fused-SiLU/direct-sum等实际控制分支没有改变。

目标每rank BF16：w1=(128,768,2048)，w2=(128,2048,384)，topk8，MetaX C550/TP2。沿用已有E/N/device文件匹配范围，不以模型名字作分支；同键其他模型/芯片/FP32未测。当前根表仍会由G2阶段表完整覆盖，因此没有新增G1阶段loader或Plugin传参。

## 正确性与graph

- CPU重放真实选择器M0..65536×3种config dtype，共589833检查；只有G1/M8..64变化，G2全部M及G1其他M一致。
- BF16/FP16完整MoE28组，含空/非对齐/边界/大M；8数学参考、14capture/28replay通过。前后最大绝对差0.0009765625，数学参考最大绝对差0.0012547374，符合冻结容差（BF16 atol.004/rtol.016；FP16 atol.0005/rtol.003）；范围外测试逐bit一致。
- 每个B/C/R及最终保留服务：双worker实际M64 G1/G2配置核验、生产capture、各16replay、17smoke/C8通过，KV562992。观察hooks恢复后才测性能，未把fallback当目标命中。
- 原不可变镜像谱系和规范化挂载校验通过；Docker inspect数组次序不稳定导致旧harness原始数组比较失败，改为规范化排序核验，未修改挂载或镜像。最终源容器四源码保持，目标只允许上述根JSON变化。
- minimal-regression通过，正式GPQA按用户要求暂缓，不能签发正式精度gate。

## 算子证据与端到端

完整MoE graph交错两profile/10blocks/50replay的中位延迟（ms）：M8 0.268424→0.231982，M32 0.477414→0.410094，M64 0.527608→0.460027，M65对照0.520420/0.520671。合成路由局部信号不冒充模型收益；预冻结晋级条件为M64更快且M8/M32无>5%退化，已满足。

随后原生无profiler P4096/D1024/C64/N128 finite-batch Mixed，seed42、temperature.7、ignoreEOS、prefixcacheoff；B/C/R各1个独立新服务，3固定预热末2TPS spread<=8%准入，2测量轮全部保留。阈值在测量前冻结：输出TPS>=2%提升，P99TTFT/TPOT/ITL回退<=10%，轮间spread和B/R drift<=8%。使用项目维护版runner/比较器，未自建benchmark。

| 角色 | 两轮测量TPS | 中位数TPS |
|---|---|---:|
| baseline | 896.26, 903.07 | 899.66 |
| candidate | 937.87, 942.95 | 940.41 |
| revert | 901.27, 895.72 | 898.50 |

| 客户端指标ms | baseline | candidate | revert | C/B变化 |
|---|---:|---:|---:|---:|
| p99_ttft_ms | 18426.93 | 18449.59 | 18480.90 | +0.123% |
| p99_tpot_ms | 69.98 | 67.02 | 70.47 | -4.233% |
| p99_itl_ms | 582.64 | 583.25 | 584.02 | +0.105% |

表中P99为原生比较器对各轮/进程P99的中位数汇总，不是合并请求的总体P99。TTFT是含网络/队列/调度的Prefill代理；TPOT/ITL也含Mixed干扰，不是纯设备阶段计时。只支持本轮P4K增量贡献，不将此前op017收益相加或乘成累计实测，不将历史opt4不同源码/配置栈视为同变量对照。原P64目标仍开放，本轮没有P64、固定四场景完整性能或正式模型精度验收。

## 保留、回退与复盘

当前保留candidate。如需回退，只把远端baseline-gemm1.json恢复到该根JSON，重启本任务独立服务并重新核验参数、graph、C8；G2文件保持现状，不使用历史PID。所有变更前已保存脚本、原表、候选和补丁；没有提交/推送或修改保护源服务。

pr_readiness=experimental：标准配置数据改动，无新增库代码，依赖已存在的阶段loader；目标数值/graph及P4K受控比较完成，其他匹配场景和正式精度未测。planning-op018-gemm1-result-20261017已更新；下一优先项是P64当前组合独立基线和阶段/KV证据，然后才考虑大M或框架差异。本轮不继续改动这些配置。

完整证据根：`/public-flash/jinghao/qwen3-VL/20261015-qwen3vl-metax-p64k-opt3`。最终回执results/op018-final.json，性能results/op018-comparison.json和results/performance/op018-{baseline,candidate,revert}-01/run-record.json，数值results/op018-numerics.json，微测results/op018-microtiming.json。当前服务manifest：`/public-flash/jinghao/qwen3-VL/20261015-qwen3vl-metax-p64k-opt3/manifests/op018-retained-service.json`。准确SHA见state.yml。
