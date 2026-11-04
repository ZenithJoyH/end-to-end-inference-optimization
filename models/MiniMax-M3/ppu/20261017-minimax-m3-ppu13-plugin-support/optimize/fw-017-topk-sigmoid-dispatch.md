# fw-017 topk_sigmoid 独立分发接入

状态：prepared_CPU_contract_passed_hardware_pending。代码已在私有候选完成，最终415项CPU/static/mock测试通过，最小回归整体仍incomplete。用户要求用新版FlagGems-vllm的topk_sigmoid替代router中的单组grouped_topk复用，验证算子及模型并保留回退；随后明确要求保留占满16卡的glm5.3-flash-opt-20260911/8011服务，因此本轮不运行PPU计算、graph或启动MiniMax，不将CPU结果冒充硬件验证。

## 设计归属与边界

operator/replace，非性能验收。当前目标MiniMax-M3每层128专家、top-k4、scale2、sigmoid+bias。以已发布43e0980的源码树为起点；FGV为env-003的46387d7 + 原packed SwiGLU，独立算子支持CUDA device接口（PPU兼容接口仍需实测）、E≤256、k≤32、连续FP32/FP16/BF16输入、FP32 bias/weights及int32/int64索引。复用现有OOT router与CachedOp→OpManager→OpRegistry，不新增全局torch.ops patch或临时开关，不修改thead.yaml/权重/vLLM/FlagGems-vllm。

router仅负责分配原接口输出buffer、表达sigmoid语义并调用CachedOp("topk_sigmoid")；非sigmoid、AITER、hash保持原fused_topk_bias路径及参数，不重复应用scale。FlagOS backend负责调用新版公开接口及能力检查；CUDA vendor使用原生vLLM入口，仅原生符号存在时可选；reference提供遵循bias仅影响选择、NaN padding置零、零和归一化保护、稳定tie及source索引约定的PyTorch实现，以承接缺少FGV或其不支持的输入。仍遵循原有strict/fallback策略，不新增吞异常逻辑。FGV的kernel边界错误不得被声称为FlagOS成功，硬件阶段必须证明default.flagos命中。

## 冻结验证范围

本地inference-accuracy-evaluation/minimal-regression。本轮CPU/static/mock覆盖实际源码方法、dtype/shape/out buffer、None/int32/int64、renormalize/scale、bias/no-bias、零token、E1/2/128/256/257、并列/NaN padding、非连续输入、hash/AITER/softmax原路径、可选FGV缺失/旧版无符号、vendor符号检查及registry策略。测试保存远端case commands，不在Plugin新增test文件。CPU测试不证明PPU kernel数值、graph replay或模型语义。

硬件资源可用后另行验证真实FlagOS核对、CUDAGraph≥2 replay、原TP16 BF16/100000/C64/FULL_AND_PIECEWISE/无prefix配置C1+C8及必要正式GPQA。当前旧90.40% gate仅历史组合；本轮及env003新组合没有有效gate，不做性能比较或PR readiness通过声明。

## 隔离与回退

PPU-13当前容器minimaxM3/fad201d7b6ec，原安装`/workspace/vllm-plugin-FL.support-minimaxM3-refine001-20261017`完整保留。候选置于未挂载私有目录`/workspace/vllm-plugin-FL.topk-sigmoid-20261018`，本轮不切换editable安装，CPU仅显式读取候选源码。外部命令/patch/测试/结果在`/mnt/nfs/users/jinghao/minimaxM3/20261017-minimax-m3-ppu13-plugin-support/topk-dispatch-001-20261018`。回退分两层：Plugin重装旧路径（仍用新FGV）；完整已知健康组合还需重装`/workspace/FlagGems-vllm`，仅经后续明确授权停止/重启本任务精确服务。当前未更改安装/运行服务，因此无需执行回退；原8011工作负载不触碰。

## 验证结果与决定

最终10个源码文件变化（213插入/59删除），无Plugin新增test文件、无thead.yaml差异。router移除了旧支持判断和单组grouped_topk适配，改为分配FP32 weights、调用方要求的int32/int64 ids和int32 source buffer，再调用CachedOp；bias只影响选择、scale只在原位置执行一次。FlagOS公开接口返回None，adapter按原Plugin惯例返回调用方原buffer；CUDA adapter同样保留原生接口。新增reference文件仅属于Plugin reference backend，不修改FlagGems-vllm或复制其kernel。FlagOS注册同时检查开关、公开符号可调用和FGV device="cuda"能力（不把其他厂商等同CUDA）；vendor.cuda只有NVIDIA backend和原生_moe_C.topk_sigmoid均可用时才候选。

首轮411项通过；复核后增加非CUDA能力保护与4个反例，以及全程无GPU初始化断言，最终415项全部通过，failures/errors/skipped均0。实际运行CPU上的生产reference函数、router方法、backend adapter、OpImpl与OpRegistry；FlagGems/native kernel和设备检测由明确mock替代，只验证接线和契约，不证明真实backend命中或PPU数值。覆盖FP32/FP16/BF16、M0/1/5/33及router M0/1/8/65、E1/2/128/256/257（超FGV范围仅reference覆盖）、k1/4/32、None/int32/int64、bias/no-bias、renormalize、scale1/2、source约定、并列/NaN padding/全负无穷、非连续reference、无效buffer、hash/AITER/softmax不误替换、可选依赖旧版/缺失/禁用、blacklist、native能力和backend执行异常传播。现有pytest在Python3.12下产生断言重写弃用警告，不是模型或数值错误。

候选PY源码语法及git diff检查通过，最终远端应用patch与本地patch cmp一致。最终测试命令显式CUDA_VISIBLE_DEVICES/HIP_VISIBLE_DEVICES为空、OMP/MKL线程数为1，每项测试后断言torch.cuda.is_initialized=False。原Plugin源码diff仍为468e5432…，安装仍指向refine001；FGV仍指向env003的新目录，未因CPU测试改变。原8011服务没有接收停止/重启命令，未执行任何GPU算子或模型流量。

PPU/graph/C1/C8/formal GPQA/performance均not_run，原因是用户要求保留其他服务占用的设备。需要设备可用后严格取证default.flagos真实命中、核对128专家/top-k4/scale2的PPU数值、边界与graph≥2 replay，才能切换服务验证；当前不保留为已通过完整最小回归、不复用旧gate。strict模式下不支持的FlagOS输入会显式失败，非strict按既有OpManager策略尝试native/reference；本轮不修改其缓存或fallback规则。当前`pr_readiness=experimental`，未提交、推送或创建PR。

## 外部回执与回退

以下均相对上文远端run目录：

- `candidate-final.patch`及`candidate-applied-final.patch`，共同SHA256 `c7f82e15b98a31e549c4dc3af6d7ac76782e0c6f7294e0fb0575f2e7fa57b006`，基于43e0980，不含新增提交。
- `checks/candidate-source.json`，SHA256 `8777bcd4c50b018a2915edd9045461741afc30f811e29f44b6e1dad493f0eae1`；`checks/cpu-result.json`汇总415项、安装未变和验证边界。
- `checks/cpu-contract-v2.xml`，SHA256 `0efd3faede33fa976da04b0dc5d66f1e8c6aae01bb47b14fd9e44c8564f0a6a6`；`logs/cpu-contract-v2.log` SHA256 `5b5cc3d05cdd5a05b1f5040442391e82cf7e01ada803a274d17343bd2f8121d8`。
- `commands/test_cpu_contract_v2.py`，SHA256 `481406a253f63c30d0cfc252942be683139b901116d71c2a4f68d616a2eda2bb`；`commands/refine-and-test.sh`保存精确命令。首轮patch、411项日志及脚本原样保留。
- `backup/installed-plugin.patch`为原三文件diff，SHA256 `468e5432772c16c36279734978e7dbe4a132768742fb239e6bd99f15723b4507`。
- `commands/rollback-plugin-only.sh` SHA256 `c30885b4e7b8a21ea82e3e8001e1b2ba8bc1d537b72cfea14fb09f02ae8cdef1`；`commands/rollback-full-dependencies.sh` SHA256 `20952ff39da0f3615af6b7a880d5843760955ad77400471ee87c1d77a9a59f8a`。

回退脚本只调整editable路径，不停止/启动服务；如将来已有候选服务运行，需先按当时实测身份获准停止本任务服务，再回退并另做readiness与推理验证。当前尚未切换安装，两级回退均未执行，8011不在脚本作用范围。后续不自动监控/等待释放设备或重新启动验证，待用户明确可用条件。
