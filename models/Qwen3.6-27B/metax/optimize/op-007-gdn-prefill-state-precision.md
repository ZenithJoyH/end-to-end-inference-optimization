# OP007：GDN prefill最终状态精度定位与修复

用户2026-10-14授权保持原atol .002/rtol .02，区分BF16正常近似与实现精度缺陷。复用OP006保存的原失败输入，不重生成或改容差。先CPU FP64/FP32递推和等价组块代数、逐中间量BF16舍入消融，再隔离GPU验证。仅完整原7矩阵/双改变输入graph及新服务命中、graph和C8通过后扩展FG19为FG20（gdn_prefill）；失败保留原19项。source8002/其他任务/共享源码/vLLM/权重/tokenizer不改，无公开issue追加发布。正式GPQA50000失败保留，不签gate或宣称性能收益。

CPU命令 /public-flash/jinghao/qwen3.6-27B/optimize/flash_attention/20261012-qwen36-27b-metax-flash-attention/commands/op007-cpu-math.py SHA d71138acc914f37661d2bd24fc8c324bb85fafa802545a5c91c723e57adafa85，只torch CPU、不导入FG、不运行GPU。

CPU结果：FP64组块与递推max_abs1.67e-16、FP32/64递推max_abs6.79e-8；模拟全部BF16舍入目标.012186490579，与GPU.012186499313差8.73e-9，超限可由舍入复现。消融weighted RHS(beta*v/beta*k*expG)舍入后目标.015112828153，0超限。下一步GPU单变量只提高WY RHS/乘加精度，保持w/u存储BF16、其他stage/tolerance不变。离线probe完成后恢复FG19，不自动发布或晋级。

/public-flash/jinghao/qwen3.6-27B/optimize/flash_attention/20261012-qwen36-27b-metax-flash-attention/commands/op007-precise-rhs.py SHA c0536e17a0decb517a11b5a1e95c2fc4069261f3a32e04b0c89740d841e5c9fc

/public-flash/jinghao/qwen3.6-27B/optimize/flash_attention/20261012-qwen36-27b-metax-flash-attention/commands/op007-probe.py SHA de76cd840bd573524b8ca77e6bc9ce287770f109070b4f5b054e859f1cb54510

/public-flash/jinghao/qwen3.6-27B/optimize/flash_attention/20261012-qwen36-27b-metax-flash-attention/commands/start-op007-decode-01.sh SHA 3dabc16c8477e90947d3ddb5042220794128a71005d45a43e124333e5dc10130

/public-flash/jinghao/qwen3.6-27B/optimize/flash_attention/20261012-qwen36-27b-metax-flash-attention/commands/op007-bind-op007-decode-01.py SHA 0f7b5b76ba3cfe57ed09ccca4ebe867ae9a3d7c677bc22d7e355443b43808269

/public-flash/jinghao/qwen3.6-27B/optimize/flash_attention/20261012-qwen36-27b-metax-flash-attention/commands/op007-isolated-controller.py SHA d47d01172661c868504944ec61620eb6e5ffef2cfa007c424fae0f2d851ccf0f

commands/op007-launch.py SHA 375693ef919cebe0b2c0062d9e08d84b83d829b6e964c24cfc1536e94e07a712

首次launcher因host无psutil在import即失败，0进程/0服务变更；v2通过/proc记录出生，无新增依赖。commands/op007-launch-v2.py SHA eb63a35361c4d2b14e399b6dab8d174817bc2bd85628531813960eae7b0eb653

commands/op007-cpu-stage-audit.py SHA 277ea27c7adfe61a0bbf29decfc91193e350c007e9e6f0b261daf96502ce6a69

第一GPU探针分阶段stock未复现基线，invalid，不用于修复结论；FG19已恢复328087/create1791951340.74。v2加CPU/GPU输入roundtrip、完整stock先调用与moduleidentity检查，复用原compilecache；其他条件不变，完整7matrix继续记所有失败。

/public-flash/jinghao/qwen3.6-27B/optimize/flash_attention/20261012-qwen36-27b-metax-flash-attention/commands/op007-probe-v2.py SHA eca682733afde92a8d76630c135416472dd3b50f45b861933ab50f470ecc72bc

/public-flash/jinghao/qwen3.6-27B/optimize/flash_attention/20261012-qwen36-27b-metax-flash-attention/commands/start-op007-decode-02.sh SHA 3d839c43694181f4e854364767c67e22079297b53080ccdce28e596bd8c5dad8

/public-flash/jinghao/qwen3.6-27B/optimize/flash_attention/20261012-qwen36-27b-metax-flash-attention/commands/op007-bind-op007-decode-02.py SHA 0342aee3f4e86a870d6ef12b6da6acd71b318956f6db29b150f7f1f3ba528205

/public-flash/jinghao/qwen3.6-27B/optimize/flash_attention/20261012-qwen36-27b-metax-flash-attention/commands/op007-isolated-controller-v2.py SHA 3f7121adc4ed006d4b4bd1e44042b24311a79b7d38d8f49ebaa974677d482bfd

/public-flash/jinghao/qwen3.6-27B/optimize/flash_attention/20261012-qwen36-27b-metax-flash-attention/commands/op007-launch-probe-v2.py SHA 9341c3f6cd8607ada2729baa37f1fb6354bc4502a354899cbc2e92a010be42d4

修正完整调用7matrix及14changed-input graph均通过；分阶段直调数据仍不等同完整调用，不作为修复证据。最终通过完整调用wrapper捕获实际中间量，stock原失败必须精确复现后同输入candidate满足原容差；安装私有MetaX gdn_wy计算weighted RHS和dot为FP32 ieee，w/u存储仍BF16，generic/其他平台代码不改。增加原7之外257token持续状态/FP32beta、g=-.001/-.01两组各2replay，全部通过后才FG20+新C8/双rank实际preciseWY命中。性能未测/不能宣称收益，失败精确恢复两文件并FG19。

/public-flash/jinghao/qwen3.6-27B/optimize/flash_attention/20261012-qwen36-27b-metax-flash-attention/commands/op007-source-patch.json SHA bc1abb687730445b7fc59ee194b65eab01ec2f41a87912b5257e75eee503c972

/public-flash/jinghao/qwen3.6-27B/optimize/flash_attention/20261012-qwen36-27b-metax-flash-attention/commands/op007-apply-private.py SHA 12673b7b59faa6b24ad7cb763a9b5de39e0415ce592d530e16c79189f2462b77

/public-flash/jinghao/qwen3.6-27B/optimize/flash_attention/20261012-qwen36-27b-metax-flash-attention/commands/op007-installed-probe.py SHA 91c8d097051b3ef547ae65caec71ccdd7bc21939eb9c4fa1139b23711ebaa480

/public-flash/jinghao/qwen3.6-27B/optimize/flash_attention/20261012-qwen36-27b-metax-flash-attention/commands/start-op007-prefill-01.sh SHA 644604c345cec12a4157a3684b34543d245e28ac495fd74cc6e5e8770263d814

/public-flash/jinghao/qwen3.6-27B/optimize/flash_attention/20261012-qwen36-27b-metax-flash-attention/commands/op007-bind-op007-prefill-01.py SHA f5f979545cd5df6bbf56d5083723705be0c9bb17054a45596481a8742d2d3dd0

/public-flash/jinghao/qwen3.6-27B/optimize/flash_attention/20261012-qwen36-27b-metax-flash-attention/commands/op007-op007-prefill-01-c8-config.json SHA eeb6c1e42ec1daae1cf617e924a2f46e1fe646bb12a95a4b409ff3aefd8829c9

/public-flash/jinghao/qwen3.6-27B/optimize/flash_attention/20261012-qwen36-27b-metax-flash-attention/commands/start-op007-decode-03.sh SHA 44e038c99fa9da63fa261e90c30480bc5e550dca00a5a3c7546cae4094de45b6

/public-flash/jinghao/qwen3.6-27B/optimize/flash_attention/20261012-qwen36-27b-metax-flash-attention/commands/op007-bind-op007-decode-03.py SHA e97dc6797aa543dfb777ae08ee371e854041bac5428a651e9d436a7819e1bdd1

/public-flash/jinghao/qwen3.6-27B/optimize/flash_attention/20261012-qwen36-27b-metax-flash-attention/commands/op007-op007-decode-03-c8-config.json SHA ec7c6b31dd6d5789dc73d112451919f43a2cea94fc3bc7a2c64fec8e0f53b5dd

/public-flash/jinghao/qwen3.6-27B/optimize/flash_attention/20261012-qwen36-27b-metax-flash-attention/commands/op007-final-controller.py SHA b3382c66fe2be5add6dc2a637dad0f1b7c785d61ebcc63795b04929d70a65546

/public-flash/jinghao/qwen3.6-27B/optimize/flash_attention/20261012-qwen36-27b-metax-flash-attention/commands/op007-launch-final.py SHA c990e3d0f0c03dfba3004113e2e67bb341bd2e08b16892f039b0c2c3fe0da19d

commands/op007-cpu-final-audit.py SHA 4bc22c044471e2cf59efacd043f6e424810e9eda7aa33617bbe69fd5e6f6edb3

weighted-RHS-only修复原7通过，但冻结257token/慢衰减两组state超限4673/393（first call）故拒绝，恢复原源码FG19，失败全部保留。继续修复组块carry的FP32精度链：BF16输入不变，BF16 K@K FP32accum后乘beta、A_inv FP32、WY FP32、跨chunk h/innovation FP32、state-dot IEEE，最终输出BF16/stateFP32不变。仅MetaX BF16选新WY，其他平台generic及非BF16旧WY保持；FP32中间访存和dot成本未测，不声称性能改善。沿用原9matrix与18changed-inputreplay，same input原失败必须通过。

/public-flash/jinghao/qwen3.6-27B/optimize/flash_attention/20261012-qwen36-27b-metax-flash-attention/commands/op007-fp32-source-patch.json SHA 4e036c80563224c565d3c6f9af04be50ddd0ae95bfd1e496f2cc19c5a03de331

/public-flash/jinghao/qwen3.6-27B/optimize/flash_attention/20261012-qwen36-27b-metax-flash-attention/commands/op007-apply-fp32.py SHA ff8236f925d2cdc99d4f321eaf5c92726a9d1bc5a2f53e7c823bb3c225ed7170

/public-flash/jinghao/qwen3.6-27B/optimize/flash_attention/20261012-qwen36-27b-metax-flash-attention/commands/op007-fp32-probe.py SHA 7c2c551f3045be1edc0570c60fbaa44fcc6a4f0b8df65a4b7074faa5d30a1662

/public-flash/jinghao/qwen3.6-27B/optimize/flash_attention/20261012-qwen36-27b-metax-flash-attention/commands/start-op007-prefill-02.sh SHA a95565781773b9bcbed387c7d08aabd570b14627bb8f85c9c533d8e2bdb7dea3

/public-flash/jinghao/qwen3.6-27B/optimize/flash_attention/20261012-qwen36-27b-metax-flash-attention/commands/op007-bind-op007-prefill-02.py SHA de8b3f22e65b0aa583392139ec029e87e2131e389e3aeb6ba211e8e27b0e3cc1

/public-flash/jinghao/qwen3.6-27B/optimize/flash_attention/20261012-qwen36-27b-metax-flash-attention/commands/op007-op007-prefill-02-c8-config.json SHA 5e0ca34aed204894886e374bdd024759a29925ef4fb5fc3a05d9d992c68bd2ca

/public-flash/jinghao/qwen3.6-27B/optimize/flash_attention/20261012-qwen36-27b-metax-flash-attention/commands/start-op007-decode-04.sh SHA 110685b32104ff2c302708221051e00f488196aeb3425a383e229e16784ff08d

/public-flash/jinghao/qwen3.6-27B/optimize/flash_attention/20261012-qwen36-27b-metax-flash-attention/commands/op007-bind-op007-decode-04.py SHA 260cccd7f9019113572f02af831c2307a204c8c6f53c6eb8e89557e294285ab3

/public-flash/jinghao/qwen3.6-27B/optimize/flash_attention/20261012-qwen36-27b-metax-flash-attention/commands/op007-op007-decode-04-c8-config.json SHA abe3bdff3a60cada8a7a650322a6e9dd99a788e3e14ca71153db83b30f1f11ab

/public-flash/jinghao/qwen3.6-27B/optimize/flash_attention/20261012-qwen36-27b-metax-flash-attention/commands/op007-fp32-controller.py SHA 43765791db25533c0dd938b4bb881b9a2b1e83096f9495be2f7c930cc9462611

/public-flash/jinghao/qwen3.6-27B/optimize/flash_attention/20261012-qwen36-27b-metax-flash-attention/commands/op007-launch-fp32.py SHA eb134b90e33a213898d570bf4ac2e9f51eed16659685e8b154a0a6b4d0ff3bea

FP32通用H48配置在原输入首调用编译阶段超5min，尚无数值结果；取消精确offline365093/create1791953099.45及所属编译子进程，原控制器按失败回退source/FG19。此轮记incomplete-compile-aborted，不作为数值失败或性能。commands/op007-cancel-compilation.py SHA 17793618b723bdae9e8fd112e2b22237628dcbcef55c519775eb01174977ee6c。下一版仅FP32缩小调优配置，原9/18检查不变。

FP32调优有界版：只对FP32 inverse/H/O选择KKT BK64/W2/S1、H BK32/BV16/W4/S3、O BK32/BV32/W4/S1；原BF16/FP16调优与旧beta*K路径保留。不是吞吐晋级，无测量数字；以有限配置通过原9/18数值graph及服务验证为目标。

/public-flash/jinghao/qwen3.6-27B/optimize/flash_attention/20261012-qwen36-27b-metax-flash-attention/commands/op007-bounded-source-patch.json SHA 69c49626e162183b34ea42db30f512682a7c99c9af7309c5fab4ddddb5c24053

/public-flash/jinghao/qwen3.6-27B/optimize/flash_attention/20261012-qwen36-27b-metax-flash-attention/commands/op007-apply-bounded.py SHA cbaf9d967ce3da8379fb7ed588943ed2450cb42013afb187e8c33606d08129b8

/public-flash/jinghao/qwen3.6-27B/optimize/flash_attention/20261012-qwen36-27b-metax-flash-attention/commands/op007-bounded-probe.py SHA 024dee206d34260bb4ef9635e078b06c795ffc1286f4e7e7c41a688e46d1d2fd

/public-flash/jinghao/qwen3.6-27B/optimize/flash_attention/20261012-qwen36-27b-metax-flash-attention/commands/start-op007-prefill-03.sh SHA f77b31808a978b9a8d7d75d3f7fd1df5d21f0e2771a7463f4370a2bf3358f3ab

/public-flash/jinghao/qwen3.6-27B/optimize/flash_attention/20261012-qwen36-27b-metax-flash-attention/commands/op007-bind-op007-prefill-03.py SHA a404ae70a0d21dcd56c428c3776ed0a86d167e5075549e44bb72110ac5245a15

/public-flash/jinghao/qwen3.6-27B/optimize/flash_attention/20261012-qwen36-27b-metax-flash-attention/commands/op007-op007-prefill-03-c8-config.json SHA 77e6fbab0f9a739929b8dad9b08ddd146e99e53ed6de9f1878415b08a57c84ba

/public-flash/jinghao/qwen3.6-27B/optimize/flash_attention/20261012-qwen36-27b-metax-flash-attention/commands/start-op007-decode-05.sh SHA c2ff0e3c9d4849008123b6d775f2ecf615abbdec933d62b4b331f93beb3324a6

/public-flash/jinghao/qwen3.6-27B/optimize/flash_attention/20261012-qwen36-27b-metax-flash-attention/commands/op007-bind-op007-decode-05.py SHA d91b5f75a3305100e46d865eb1be01473db1a5170b29312cdd54b4f047c49901

/public-flash/jinghao/qwen3.6-27B/optimize/flash_attention/20261012-qwen36-27b-metax-flash-attention/commands/op007-op007-decode-05-c8-config.json SHA 5a07fc03354ead1cd746f1552ed6fd8683d52ca4621373b58b5a7616bfcc7e79

/public-flash/jinghao/qwen3.6-27B/optimize/flash_attention/20261012-qwen36-27b-metax-flash-attention/commands/op007-bounded-controller.py SHA ebb96bd4505fc3100ae157da00a8c6b93eea5bff182e6b41330b89d02fb0ea14

/public-flash/jinghao/qwen3.6-27B/optimize/flash_attention/20261012-qwen36-27b-metax-flash-attention/commands/op007-launch-bounded.py SHA 49b2c894ddfbcb56da083474e1d72652c8150a1d5eb368d9be5c7bf2f6065448

终态仅核验现有source/精确instance、原9/18数值graph、actual rank precisionWY/完整FG20白名单及现存C8，并保存patch/证据SHA，无模型请求/源修改。commands/op007-finalize-existing.py SHA 0e2bc19c090210eb4904d56081260d39a060486445e664a2dc723b2b2d8afe18

终态：数值修复通过并在独立优化容器启用gdn_prefill。原.002/.02不变：保存原失败输入，误差.00255618→5.4016709e-8；9矩阵/27检查、18changed-input graph全0超限，包括non-square/空段/跨chunk/零初态/leadingstride及257token慢衰减两组。总output max_abs.00048828125、state max_abs4.0531158e-6。

根因判断限定原输入/原容差：不是输入BF16量化本身、Vmajor或空段索引导致；不舍入的FP64组块与FP64递推一致，FP32递推误差6.79e-8，显式BF16中间舍入在CPU复现目标GPU差异至8.73e-9。数学公式/布局缺陷未被证实；该实现的中间精度策略不能满足冻结state容差，属于精度不足。weighted RHS-only版本原7通过，但两慢衰减状态失败4673/393，故拒绝、已回退；完整FP32 inverse/WY/innovation/跨组块carry修复保留。不能把原单元素或本修复因果等同历史GPQA低分。

仅私有FG-vLLM MetaX gdn_chunk.py +新增gdn_wy.py；BF16 QKV/最终outdtype保留，finalstateFP32及Vmajor不变。新WY按MetaX BF16选择，其他平台generic无改动；非FP32inverse保留旧beta*K路径和调优。FP32 KKT BK64/W2/S1、H BK32/BV16/W4/S3、O BK32/BV32/W4/S1为有界验证配置，未证明最快或跨平台/其他dtype通过。完整自动调优编译曾精确取消、记incomplete而非数值失败，所有失败与原件保留。

模型两rank各190 graphlaunch、96 precisionWY/96 prefillH、2880 FGpacked、960 SplitKV/merge；graph capture与两次新smoke通过。新C8十题/20filter样本、0timeout/0empty完成（T0/cap2048，只作健康/范围内sanity，不是50000完整精度）。当前服务qwen36-fa-opt:376022:1791953935.71，18002/GPU2、3，8192批预算/TP2BF16/prefixoff/graph64不变。原白名单完整保留+gdn_prefill，literal20→21项；此前FG19/FG20是历史角色标签，不能作为ATen实际注册数量。MTP仍fwd、非MTP packed；无blacklist/FGattention1。

FG-vLLM新Python指纹6ea79405ab055aa576bf22f9953cf87788044ef8ce60a265d68c733f80f76811；其他3repo指纹与原实例一致。源8002/共享代码/vLLM/权重/tokenizer无改动，无公开issue评论、提交/推送或新GPQA/性能请求。完整50000 native158/198<80失败仍保留，本轮只诊断算子与接入，不签gate、不宣布性能收益。pr_readiness experimental；目标仓库black/ruff/isort未安装，后续PR清理与其他硬件/dtype验证未完成。

终态回执 /public-flash/jinghao/qwen3.6-27B/optimize/flash_attention/20261012-qwen36-27b-metax-flash-attention/results/op007-terminal-validation.json SHA 82d65d9176f613ea02fe4ebe8a67ddff163af709567cfae3e5f286d27febd7e7
补丁 /public-flash/jinghao/qwen3.6-27B/optimize/flash_attention/20261012-qwen36-27b-metax-flash-attention/patches/op007-final-gdn-state-precision.patch SHA 2b1444324f212d6eba3593e5ff7957659b42717e5697a2ce09c109351caf75ee
服务 /public-flash/jinghao/qwen3.6-27B/optimize/flash_attention/20261012-qwen36-27b-metax-flash-attention/manifests/op007-prefill-03-service.json SHA d6d6c4bf4ba418a92423b573cc645da98f245f276a6c44c6e94c97c2e3479abe

知识delta：FP32 finalstate存储不意味着中间FP32精度；显式舍入消融可以区分数学/布局错误与精度预算不足；必须检查慢衰减的多chunk累积，不能以原7小矩阵或输出通过替代最终state检查。保留FP32正确基线，下一轮先测完整FG路径Prefill/Decode/Mixed净影响，再优化精度补偿/tiling，不关闭算子或以micro替代E2E。
