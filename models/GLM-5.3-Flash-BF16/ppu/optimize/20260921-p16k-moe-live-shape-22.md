# 20260921-p16k-moe-live-shape-22：P16K MoE 实际shape与配置覆盖

## 方向与冻结范围

- 状态：`rejected/reverted`；`operator/improve`。
- 父场景仍为 `P16384/D1024/C64/N128`，TP16/BF16/max-seqs64/MBT32768/FULL_DECODE_ONLY/前缀缓存关闭；服务保持停止。
- 点20当前trace中fused MoE占rank0 Prefill/Mixed/Decode设备活动汇总20.1812%/19.6521%/41.2481%，large-M主GEMM占Prefill/Mixed 11.4820%/11.7378%。活动可重叠，不是关键路径或收益上限。

## 规划复盘与首个证伪实验

`planning_review_p16k_04` 覆盖点20与点21：两项均未进入当前组合；累计同workload证据仍是点19的434.205→474.526 output tok/s（+9.286%，performance_only），不能与局部micro相加。当前Sparse MLA主kernel为不可调vendor黑盒，通用替代0.828x、输出buffer复用约1.00x；MQA限域方案有密集反例。Decode MoE仍是第一热点，因此转向MoE，但旧配置不能盲目重跑。

知识库已验证：M<=32与exact-M64 GEMM2已保留；M64 GEMM1最佳1.048522x未过门槛；P4K exact-M16384 GEMM2曾有约1.075x局部收益但短服务吞吐-0.634%并已回退。首个实验只解析点20现有rank0 trace中的live `M`/stage/config命中：

1. 从CPU custom-op/input shape与相邻kernel序列获取Prefill/Mixed/Decode实际M，不从MBT或并发上限猜测。
2. 对照当前FlagGems-vllm thead stage-config guard和实际函数对象，区分GEMM1/GEMM2、padding与已保留分支。
3. 只有出现旧实验未覆盖的新shape/config缺口，才建立3seed×3组完整stage微基准；中位至少1.05x、最低seed至少1.03x，并通过BF16 reference、边界、graph三次replay才允许源码候选。
4. 若live大M仅为已失败的M16384、或现有config已命中且无新机制，则停止点22，不重复P4K扫描。Decode M64保持守护，不改已保留配置。

若micro晋级，使用Accuracy Skill `minimal-regression`，再用Performance Skill `targeted` 做P16K/D128/C64/N128 A/B/R；吞吐至少+3%、回退和TTFT/TPOT/ITL守护通过才测完整父场景。高风险融合或语义变化触发完整精度；本轮shape审计本身不触发服务或精度测试。

## 外部产物

- 案例根：`/mnt/nfs/users/jinghao/glm5.3-flash/optimize/e2e-opt-20260911`。
- 分析脚本和输出只保存到 `commands/p16k-moe-live-shape-22-20260921/` 与点20 profile的 `analysis/` 新文件，不覆盖既有trace/summary。
- shape提取脚本SHA256 `3afe3c645093c14efde6b646bf1a361a53903d57e8faad6d6ead5bbb396354e6`；执行脚本SHA256 `609e1c4c04d0a8de9e0d95fdf1e319377edc02d510c2e8e9fb20c20402a03123`。
- shape结果：`analysis/moe-live-shapes-22.json`，SHA256
  `121fac6c54287524b225d2556d1e378f36a82a9e51bb301dbdbf58aefeb15182`。
- 有界微基准与执行脚本SHA256分别为
  `d2b441c5fcc526eeb1cb51f1e4dbed013bfaaf5cb0073356ed050f88e0ca8851`、
  `e3e965a8ed5ec2bf60d31e399c660b60955b58c3b099f623b5e84654cdf75941`。
- 微基准结果 `operators/moe-live-shape-22/m32768-config-scan.json`，SHA256
  `7d259594b15ff6fb0e059e8f938f46d4706972d55aff14283bb0ea0098c9212d`；
  源码命中复测 `m32768-source-hit.json`，SHA256
  `c8f83095dcd78c890dd7e130f6914fc6919810cb7636e466576b73a06e8cf947`。
- targeted根：`full-scenarios/p16384-d1024-c64-n128/candidates/moe-m32768-gemm2-22/milestone-p16k-d128/`；
  plan/comparison SHA256为 `3eb5b5e29f594ab057f84e53cb76b8edba380dbd65511c247d40f0af4222e901`、
  `d5fa2df26839c484a5b3918441f25aa497e7924aa121285705aa4c4bfaf4c8f5`。
- 本地生成只使用 `/private/tmp`；不向项目 `scripts/` 写入过程文件。

## 当前结果

已解析rank0 trace的1,866,640个事件和120个CPU marker。从精确
`vllm::moe_forward_shared` input shape得到：Prefill为`M16384/H4096`（42次）；
Mixed同时出现`M17377/H4096`（42次）和`M32768/H4096`（1302次）。
`M32768`是P4K旧扫描未覆盖的新主导shape，因此进入GEMM1/GEMM2各四个安全
config的有界扫描；Decode `M64`只作已保留精确分支的守护。

微基准使用3 seed×3交错配对组，对每个候选做graph capture和三次
replay，以当前`BM64/BN256/BK32/GM8/w4/s4`为同输入baseline。GEMM1所有
候选及GEMM2的单项拆分均未过门槛；只有GEMM2
`BK64/GM16/w8/s3`通过，总中位 `1.072534x`，最低seed中位
`1.072338x`，BF16数值通过。落到严格`M32768/E288/H4096/I128/topk8/BF16/GEMM2`
guard后，实际launcher源码命中复测为 `1.072917x`，最低seed `1.072473x`。

候选源码SHA256为
`40e5b372502b94e61d7ebf8fc5e553adf9e2e95c744b84d06f7bba5844795759`；回归测试
SHA256为 `09ae602d36ab5bf04847f44099a2d946d441a7b43276677f8a7cce08d00fa143`。
新guard与已保留small-M/M64 guard共41个聚焦单测通过。
首次launcher仍使用旧`/workspace/FlagGems-vllm`目录而在进入Python前失败，
已根据实际导入路径改为`/workspace/e2e-opt/glm53-20260911/FlagGems-vllm`；
该次未加载数据、未运行kernel，不是性能样本。

## 正确性与端到端结果

精度Skill显式模式为`minimal-regression`。候选graph服务启动、capture与多次replay
通过；C1为1/1、C8为8/8，结果SHA256分别为
`72cbf1a5c1d7f360754066feefc0145788a566ee98a99846a9fabd9d6cdffad2`、
`0353d974fa10e2fc244d8ac9d924147e797d835c200879b14ce124debdc1804b`。心跳
`glm-p16k-moe22-regression`按30分钟周期创建，短测结束后已停用。
这是最小回归通过，不是新的正式GPQA gate。

性能Skill显式模式为`targeted`；里程碑映射到父场景，但将Decode从1024缩短到128。
三角色均为fresh graph进程、6 warmup + 3 measured，前缀缓存关闭，共
3456/3456请求成功。

| 角色 | output tok/s | 正式轮离散 | P99 TTFT | P99 TPOT | P99 ITL | P99 E2E |
|---|---:|---:|---:|---:|---:|---:|
| baseline | 78.3892 | 0.0362% | 99640.61 ms | 797.286 ms | 3125.675 ms | 190567.00 ms |
| candidate | 78.4047 | 0.0216% | 99603.42 ms | 797.189 ms | 3123.616 ms | 190489.31 ms |
| revert | 78.3822 | 0.0071% | 99635.55 ms | 797.192 ms | 3126.164 ms | 190520.36 ms |

candidate相对baseline的输出吞吐只 `+0.0198%`，远低于`+3%`门槛；
TTFT/TPOT/ITL/E2E分别改善约0.0373%/0.0121%/0.0659%/0.0408%，均属可忽略量级。
revert相对baseline吞吐漂移为 `-0.0089%`，排除了环境漂移对结论的干扰。
比较器结果为`failed`，唯一issue是`output_throughput: primary improvement below threshold`；
comparison SHA256为
`7b108910e1a4c3568bbed1597928b51db6cf2447a62ff0ea3eb25f7b23227416`。

## 为什么算子变快而端到端没有收益

候选只加速MoE完整交易中的GEMM2一段，不消除alignment、GEMM1、activation、
MoE sum/通信、Sparse MLA与调度。点20 trace中所有large-M主GEMM的Mixed设备活动
也只占11.7378%；即使乐观地把这一整段都视为可加速且不重叠，
`1.072917x`按Amdahl折算也只给出约0.80%的上界代理，已低于3%服务门槛。
实际该活动还包含未被候选加速的GEMM、跨rank/流重叠，也不等于关键路径；
所以实测只剩 `+0.0198%`。这是“局部kernel比率”不能直接等同端到端收益的
具体反例，不是数值错误或性能环境失效。

## 决定与回退

候选拒绝，不测完整D1024，不进入交付脚本。实际源码已恢复到
`f70ff827bc1bce13fc42ca05ac7dd11e28ffd83745aee9808f0715ac7b9baa66`，新测试文件已从工作树移出；
候选源码、测试和命令仍在远端case目录可恢复。服务已停止，FlagGems-vllm工作树
恢复为本点前的1个修改文件+2个已有未跟踪测试。未提交、未推送。
