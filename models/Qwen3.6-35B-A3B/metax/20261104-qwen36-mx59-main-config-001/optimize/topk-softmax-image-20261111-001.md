# 指定镜像 topk_softmax 组件定位

用户授权：Excel复现环境改为 harbor.baai.ac.cn/flagrelease-public/qwen3.6-35b-metax001-gems5.5.0-tree0.7.0-cxnone-plugin0.2.0-vllm0.20.2-sglangnone-sglangflnone-cp312-pt28-maca37-x64-3.8.1:202611091810；在mx-59基于此镜像启动独立容器定位topk_softmax。

分类 diagnostic，非端到端性能优化或模型评测。本轮优先冻结镜像真实digest/依赖/source/public API/Plugin路由，不改包/源码/现有服务，不自动全量GPQA或ERQA。原mx59 qwen36-35b已不存在，用户指定镜像为本次独立组件环境来源；无源容器挂载可复制，不虚构mount_parity。新容器无模型/共享源码挂载，命令及结果通过docker cp回收。

用户既有远端工作目录 /public-flash/jinghao/qwen3.6-35B，本次唯一子目录 /public-flash/jinghao/qwen3.6-35B/20261104-qwen36-main-config-compat-mx59-001/operator/topk-softmax-image-20261111-001。2026-11-11只读：原目录root/root755，规范路径一致，共享盘4.6TiB可用，docker存储27TiB可用；指定镜像尚未本地存在。8卡均无进程，选择既有授权GPU4，测试前再次准入。新容器名 qwen36-topk-softmax-mx59-20261111-001。

预声明：调用真实FlagGems公开topk_softmax；同一输入以独立Torch softmax→topk→可选renormalize为oracle，检查权重、专家索引、source-row编码、输入不变与输出完整写入。先模型shape E256/K8、M1/32/64、FP32/BF16、renormalize两值；再以故障证据收窄扩展到K1/2与E128边界等。不把相等logits的不同索引直接当错误，先确认tie契约。有限图capture+至少两次变化输入replay；无GPU时停止不抢其他服务。若功能通过再决定是否需受控组件性能比较，不用一轮微测宣称E2E问题。异常出现保留raw日志/traceback；禁止launch后跨后端重试，后续对照使用新独立测试进程/新输出。不升级依赖。用户仅要求定位，暂不修改库。

证据状态：待实际执行；已有历史仅证明黑名单移除default.flagos后路由到vendor.metax，不足以证明算子故障。无新gate/性能验收。采用inference-accuracy-diagnosis及minimal-regression的组件范围方法；纯算子无prefix-cache要求。

实测镜像sha256:a4734ce7758490551c7cb7fed1794df8ccd9417a7356ac351d40bb128930fe65，独立容器662b178...已建立，无网络/无任何目录挂载。FG实际a456722a1的通用fused/topk_softmax.py，非MetaX特化；Torch2.8+metax3.7.0.7、FlagTreefe1d24f6/Triton3.6、FGV e1a02b6、vLLMbc150f5、Plugin1bc0c77。numeric001首个M64E256K8 FP32唯一输入通过，FP32随机/两种renorm全部通过；BF16M32遇到expertID不一致停止并保存原始输入输出。注意BF16存在相等值，原测试对非ties标签随机输入直接要求torch.topk索引相同过严，不能据此报算子错误。CPU tie-audit仅检查已保存张量，不重发kernel；若变化位置的原logit完全相同，则归类oracle-invalid/tie_order，保留原failed日志。numeric002只补未完成BF16/哨兵/graph，用原logit相等+权重误差/索引唯一/范围/source编码约束验证，不放宽非tie错误。原已通过FP32不重复跑。

性能组件预声明：数值与graph通过后，仅比较当前公开FlagGems API及Plugin vendor实际callee vllm._custom_ops.topk_softmax，FP32/M1,32,64,8192/E256/K8/renormTrue，预分配相同shape输出、同输入、同卡、128次调用graph；100次warmupreplay，3个固定准入窗口max/min<=1.05，准入后保留5次native→FG→native全部轮次。每窗口64次replay，CUDAevent设备耗时除调用数。任一shape不稳则该shape incomplete，不丢慢轮、不择优；不是E2E收益。命令benchmark-001.py与run-benchmark-001.py先归档SHA后执行；不改源码/配置。

## 最终组件结果（2026-11-11）

指定镜像已实际拉取且按不可变ID创建独立诊断容器，网络none、无挂载、无模型服务，物理GPU4。容器 `qwen36-topk-softmax-mx59-20261111-001` 留存供复核；未操作原有容器/服务。最终核验6个本轮相关源码文件SHA与初始一致；不是全包一致性或新模型精度gate。

- numeric001原生exit1及失败张量保留：过严oracle要求随机BF16的并列logits也必须与torch.topk选择完全相同索引，导致误拒绝。CPU审计20个变化索引对应logits逐项完全相等，权重最大误差3.73e-9；这不是已确认算子缺陷。
- 原numeric001已通过9个用例，numeric002仅补剩余13个用例、原生exit0。合计22个不同用例通过，包括FP32/BF16、两种renorm、E128/256/257、K1/2/8/32及ties；检查原输入不变、索引唯一/范围、权重容差和source-row编码。最大权重绝对误差2.98e-7，rtol1e-5/atol1e-6。真实公开API capture后2次变化输入graph replay通过。
- 并列logits允许不同tie-breaking，不等于模型输出逐位一致；本轮未执行模型精度或评判不同专家选择的端到端影响。
- FlagGems命中通用实现；vendor.metax的实际callee为 `vllm._custom_ops.topk_softmax -> torch.ops._moe_C.topk_softmax`。benchmark001先核验两者数值与source编码，再按预声明graph稳态协议执行。全部4个shape通过3窗口<=5%准入，5轮B/C/R全部保留，原生exit0。下表是每次调用设备时间的5轮中位数，不含分配/编译/Python dispatch，不是E2E吞吐。

| M / E256 K8 FP32 renorm=True | B原生µs | C FlagGemsµs | R原生µs | C相对B耗时 |
|---|---:|---:|---:|---:|
| 1 | 13.91056 | 10.93281 | 13.91022 | -21.406% |
| 32 | 14.32991 | 11.24878 | 14.33081 | -21.501% |
| 64 | 14.35528 | 11.32191 | 14.35659 | -21.131% |
| 8192 | 52.84659 | 68.36672 | 52.84541 | +29.368% |

确认的是大token batch M8192下FlagGems较MetaX native慢约29.4%；M1/32/64反而快约21%。因此不能把它写成普遍功能故障或所有shape的性能退化，也不能把这次组件数据当作历史黑名单或E2E退化的根因证明。

源码线索：E>128强制BLOCK_SIZE_ROWS=1/num_warps=1；kernel在全部E上softmax后逐K次max/剔除，并在renorm时重读输出。它是后续分析并行/归约/访存的候选机制，当前未profile/改tile/做机制单变量，不宣称确切瓶颈已定位。若继续优化，应先以真实目标服务trace取得M分布和该算子占比，再做对应shape特化与正确fallback，最后用同配置E2E检查；本轮到组件问题反馈为止。

远端原始产物：本实验ROOT下 `diagnostic-verification-001.json` SHA256 **8d23c1352873b0c901f1de68f993a9248a36d5affda808c11b53a8900bc53962**。所有准备/运行/失败/成功输出完整保留，无重放已完成矩阵，无修改库/黑名单/服务配置，无提交/推送或Issue发布。

- `audit-001.json` SHA256 `6f81eec91e0f87fa5ca6bce28a1e16c2be633002c4a9834bd892a3029b631e4a`
- `tie-audit-001.json` SHA256 `eb65bc2c5b5afa99906010a3cdc31c02792a58d30a8db16348234cedffa096eb`
- `numeric-001/result.json` SHA256 `7bb147d4df76091cc5adccec159b53bd1b12cd8971061b3138066e284268234e`
- `numeric-002/result.json` SHA256 `fa2d3b9b4bd79dff9421668caed93f2134ee11cfb5cb9ec2558191b61611f701`
- `benchmark-001/result.json` SHA256 `774e595b646df3dceccca66bf362134863f49fe3953c5898869ec564d3ad2f10`
- `numeric-001-native.json` SHA256 `d894619a3e38a3d0a21159634492f09d2572dfe41e3daa43d9ef5d2e86bc683a`
- `numeric-002-native.json` SHA256 `d965e67c31c7f01c98414ecc3acd0ba40a42ef5582b764da9c4c0578d41a585e`
- `benchmark-001-native.json` SHA256 `e21a8c019b5f414b2ef150663724b36923c5854588b3050a7ba2c3717a0eb312`

执行命令（各一次，先唯一归档SHA）：
- `commands/benchmark-001.py` SHA256 `322869c88ddc5c2bda07e4956b9e987973c1028ef8b125dc07d0626cdc25f72d`
- `commands/run-benchmark-001.py` SHA256 `ecc42a378a05756a81d910a30e4b94a68f07fa0db5bb58dfab4255ebad2be685`
- `commands/collect-001.py` SHA256 `1999c7305ee687650e3a7e2974bd732c16d97171b9c82c5ccf7d9f87e8d99475`

Excel已将两行环境写为用户指定完整镜像+真实digest；topk行更新为已测大batch性能差异，clone行明确仍是历史复现而非本镜像已重验。原模板、clone故障内容和GitHubIssue空白保留。

2026-11-12 用户批准精简公开范围后，性能反馈已提交 [FlagGems #8959](https://github.com/flagos-ai/FlagGems/issues/8959)，本地Excel已回填。仅发布既有组件证据，无新增测试或源码变更；见[最终发布记录](clone-image-issues-20261111-001.md)。
