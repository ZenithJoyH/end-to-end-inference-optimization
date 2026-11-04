# fw-018：FP32 router GEMM 接入

当前默认策略已由[fw-020](fw-020-fp32-router-opt-in.md)改为opt-in：保留本项实现，但默认模型使用原vLLM GateLinear。下文为接入时的设计和历史CPU600证据。

## 冻结范围与设计

用户要求将新版 FGV fp32_router_gemm 与 OAI experts 接入，但仅做代码和CPU测试，不影响8011。
本项属于 operator/replace，关联 fw-019；以 fw-017 未安装私有候选为共同父状态。当前安装不切换。
私有候选 `/workspace/vllm-plugin-FL.m3-router-oai-20261018`，依赖 FGV46387d7；vLLM只读。

复用 GateLinear 的 PluggableLayer OOT 注册和 Plugin CachedOp/OpRegistry/FlagOS backend，增加 reference backend。
条件以能力而非模型名判断：CUDA接口、H6144/E128、输入BF16/FP32、权重FP32、无bias、out_dtype FP32。
在 opaque 自定义算子内部依据实际M选择：M≤32调用Plugin分发，M>32保留原FP32 F.linear；fake实现不按M拒绝。
不设置 max_num_seqs=32，不改变64并发；其他shape/dtype/bias/输出契约保留 upstream GateLinear.forward。
FlagOS只在 FGV开关启用、CUDA backend和公开symbol存在时注册可用；reference提供同语义FP32 linear。
旧vLLM缺少GateLinear时不增加该OOT项，不能破坏其余Plugin导入。不开启新硬件或服务。

## 首个证伪和晋级

CPU检查实际候选源码、registry/adapter、OOT注册、M0/1/31/32/33/64及更大M、unsupported shape/dtype/bias、fake和CPU torch.compile动态分支。
与F.linear(x.float(),weight)比较，显式证明M>32不调用FGV/dispatch且不会污染小M选择；kernel使用mock，不等同PPU数值通过。
外置测试，不新增Plugin test文件、thead.yaml差异。任一契约不符先修复，不切换安装。
后续设备可用并获准后，需独立PPU数值、TP16 capture+两次replay、模型最小回归和正式GPQA≥88%，再谈性能。

## 阶段/性能/回退

Decode小M可能减少router开销；Prefill大M保留原linear；Mixed收益未测，当前三阶段时间/shape频率均unknown。
理论矩阵乘为2*M*6144*128 FLOPs，FP32权重约3MiB；不得从此推断端到端加速。
当前无可比性能数据，pr_readiness=experimental；回退为不激活新候选或恢复旧editable路径，原候选不修改。
外部产物计划：`/mnt/nfs/users/jinghao/minimaxM3/20261017-minimax-m3-ppu13-plugin-support/router-oai-001-20261018`。
结果：CPU契约通过；硬件、device graph和模型验证not_run，精度最小回归整体incomplete。

## 最终实现与 CPU 结果

最终候选基于43e0980+fw-017，14个生产源码文件变动（合计406插入/69删除），无新增Plugin测试或thead.yaml修改。
GateLinearFL复用现有OOT白/黑名单；新注册重复执行幂等，遇到不同OOT实现冲突仍显式报错，不覆盖别人的注册。
GateLinear缺失的旧vLLM不注册该项；shape/dtype/bias/out_dtype/设备/开关不匹配直接执行upstream forward。
M≤32通过CachedOp选择FlagOS或原有reference策略；M>32在opaque custom op内部执行与原OOT路径同语义的FP32 linear，不调用FGV。

最终600项CPU/static/mock全部通过（失败/错误/跳过均0，14.90秒）：fw-018专项69项、fw-019专项115项、组合源码静态1项、fw-017回归415项。
本项执行当前vLLM GateLinear和PluggableLayer的原始快照，ReplicatedLinear/device/FGV用隔离mock；证明选择、cast、返回bias、注册键及回退行为，不能证明硬件kernel。
CPU torch.compile使用fullgraph=True/dynamic=True与GraphModule.forward测试backend，依次M2/64/32/129/8只在2/32/8调用mock小M实现；fake/meta支持M65536，无按32拒绝。
测试每项前后断言torch.cuda.is_initialized=False，CUDA/HIP可见设备为空，OMP/MKL各1线程。PPU graph、真实kernel、模型C1/C8和正式精度未执行。
容器未安装ruff，lint未运行；源文件语法和git diff --check通过，未在目标环境额外安装工具。

首轮准备与文件上传重叠导致补丁暂时为空，在干净新副本上停止；校验后恢复，未影响原安装。
首轮CPU为479通过/115 fixture错误，原因是测试mock未建立vllm父包；只修复外置测试后594通过，再增加真实vLLM/OOT测试并补充新Gate注册幂等，最终600通过。
早期补丁/日志/XML均原样保留，不将fixture错误归因为模型精度下降。

## 外部证据与回退

以下相对上文router-oai-001-20261018目录：

- `candidate-final.patch`与`checks/applied-final.patch` cmp一致，SHA256 `9772819d375332431821dde3c38dbafa005e0e42c6c53ea7eabb6fa390f0573e`。
- `checks/candidate-source.json` SHA256 `16feb0bc0e6397cb55b8808456fcf56fe6bf099199b51b1acb51e68acfdd1a60`。
- `checks/cpu-contract-v3.xml` SHA256 `cef862a12e6517210719f970266ffb50deb38408fe543e8ca16f4c2926c1d9a5`。
- `logs/cpu-contract-v3.log` SHA256 `59914ee811bf4c1f5e2fbacb195f6f152e1ee0dfa20e81e1e5f5207b7281a3d4`。
- `commands/test_router_oai_cpu_v3.py` SHA256 `b1e116a57cd90ce73f6481a2adb1530ca85509c0ae3df8c118a736714183e2c0`。
- `commands/finalize-cpu.sh` SHA256 `4ce9ee65b8f0ffca7446bd92e4bf5f1263af45e179a56538dd3da82dc51bf413`；执行命令先保存再运行。
- `checks/cpu-result.json`记录2026-10-18T02:35:40Z复核：原Plugin diff仍为468e5432…，editable仍指向refine001；FGV仍是env-003私有目录。8011原API/engine/16workers均存在、health200，无停止/重启或设备计算。

新候选未激活，所以当前无需回退。fw-017目录、原refine001安装和旧FGV副本完整保留；已有两级回退脚本见fw-017的外部证据章节，未执行。
若将来激活后需回退，须先核对并停止当时本任务服务，再恢复Plugin-only或完整依赖组合，不能操作8011。
本项保留为prepared/pending硬件候选，未提交/推送，pr_readiness=experimental。知识差量仅为已核验的接入与回退边界；无可迁移的PPU性能结论，不修改算子调优地图。
