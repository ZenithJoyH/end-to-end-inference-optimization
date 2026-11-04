# op-002-moe-stage-tile-diagnostic：MetaX MoE stage tile 有界诊断

状态 microbenchmark_confirmation_running；分类 operator/improve；正式目标 P1024/D1024/C64/N128。保持FlagGems启用与当前白名单、公共fused_experts_impl及caller-buffer复用，vLLM源码只读。

## 依据与范围

prof-001两个rank证明MoE分别是Mixed约35%、Decode约42%的累计kernel活动热点。实际hidden2048、E256/top8、TP2每rank intermediate256/BF16，目标M64和Mixed M8192（另有7393边界）。这不是随机慢轮归因。现有MetaX TP2默认config的M/N/K tile范围与当前shape匹配，先做有限配置扫描，不套用PPU历史最优值。

## 实验与首个证伪

仅在独立进程、预检空闲GPU0运行仓库既有CallerBufferMoEBenchmark/Benchmark.get_latency graph计时，复用同一输入与caller buffers。保持BLOCK_M及排序padding不变，一次只改变一个GEMM stage的N/K、warps/stages配置，最多8个候选；baseline与每候选成对重复3次并保存全部原始值。先M64再M8192，数值参考包括原路径和FP32逐expert参考（小M）。缓存预热后计时，不记录编译时间为收益。进程内hook只影响独立诊断进程，服务源码和既有module对象不改。GPQA与microbenchmark使用不同设备，微基准结果不算服务性能。

## 正确性、晋级与停止

输出容差BF16 atol2e-4/rtol2e-2（原路径同输入）；报告max_abs及normalized_RMS，graph capture和至少两次replay；任何NaN/Inf或明显退化拒绝。完整MoE transaction中位加速>=1.05且重复可复现，才设计受shape/dtype/config严格限制的MetaX backend实现。若扫描不达门槛停止，不扩大无界搜索。服务改动还需最小回归、正式GPQA>=0.8、无profiler同配置baseline/candidate/revert和延迟守护；随机慢轮未解决时不宣称端到端收益。

## 代码与回退

当前没有服务源码补丁；进程内hook退出即恢复。后续若有候选只改FlagGems-vllm的MetaX后端，其他平台/非目标shape配置不变；修改前已有完整SHA源码快照，增量补丁与SHA保护回退另存远端。

## 外部证据

全部命令、manifest、原始微基准和数值记录写入 `/public-flash/jinghao/qwen3.6-35B/20261013-qwen36-35b-metax-e2e-current`，执行前保存到commands。

设备预检拒绝GPU4：已有无关TP worker占用61GB/70%以上利用率，未启动诊断、未停止该服务。改用当前无进程且0%利用率的GPU0，执行前再次检查；当前模型评测仍独占GPU6/7。

## 首轮完整扫描结果

32个stage/shape配置结束，所有失败、退化保存。M64未找到更快候选；M8192 GEMM2不改。M8192 GEMM1最优N128/K64/8warps/2stages，保持BM64，三对完整流程中位1.427691x、最小1.426912x，seed42输出逐位相同；其余N128/4warps为1.369983x。仅做独立诊断，未修改服务。随后两新seed×随机/极偏斜routing×M7393/8192及8191/8193数值边界复核中；本点尚无无profiler服务收益，不能宣称解决随机慢轮。

- 扫描：远端`results/op-002-moe-tile-scan.json`、`logs/op-002-moe-tile-scan-v2.log`。
- 复核：远端`results/op-002-moe-tile-confirm.json`、`commands/moe-tile-confirm.py`。

## 历史精度阻碍与决定（30000上限旧轮，现已由65536达标gate解除）

原服务未改动，完整GPQA strict-match为149/198=75.2525%，低于冻结0.8；198唯一题及两个filter/结果provenance验证通过，未签发gate。本点候选未进入当前服务，不能归因于尚未部署的优化。暂停新增性能改动，先按inference-accuracy-diagnosis核验。API原生198响应中30个finish_reason=length且completion_tokens=30000，其中25没有原生answer标记；168个正常stop都有标记。这支持输出预算阻碍，但尚未证明扩展预算会达到80，不把健康症状单独当作score失败规则。

当前新65536预算proposal只改max_gen_toks，保留全部198/严格metric/0.8/其他采样/模型source。两次provenance一致、命令和contract已准备，尚未执行；等待用户确认变更已冻结契约。原低分及所有历史原始数据保留。额外发现12题选项被原生helper去括号改写、171题出现重复选项；未自行改helper/filter/数据。

证据：远端accuracy/anchor-failure-evidence.json、anchor-output-budget-diagnosis.json、anchor-evaluation-diagnosis.json；proposal见accuracy/proposed-g64k-{config,contract}.json和commands/proposed-g64k-full-command.json。
