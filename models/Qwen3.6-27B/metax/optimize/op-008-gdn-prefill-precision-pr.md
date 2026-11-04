# OP008：GDN prefill精度修复的issue更新与关联PR

用户2026-10-14明确要求更新issue923为当前精度问题，并创建关联PR；授权发布当前最小修复/合成回归及必要数字，不上传私有路径、容器/PID、样本快照、完整日志/trace或其他优化补丁。仅新fork分支，不更新forkmain或合并。原模型服务376022经精确停止后完成独立scratch验证，恢复同源服务390234/18002/2、3卡。

上游当前main6123527f05497e08bc677cb40e8364502c4f5a32、tree7092e0b30bf6871de1c60285975f342a27b4d821；gdn_chunk.py与原29e80363基线逐字相等。仅MetaX gdn_chunk、gdn_wy及独立MetaX回归测试，不包含OP001 FA、decode nullpage修复、Plugin适配或部署配置。

读取目标AGENTS/workflow；optimization.md/deep_opt.md不存在，rg核查后标记缺失，当前任务是已验证精度修复的PR整理，不宣称性能G6验收。

| 项目真相 | 冻结值 |
|---|---|
| operator/API | 已导出的chunk_gated_delta_rule_fwd，MetaX runtime Vmajor七元组，无对应单一torch API；参考为相同量化输入的FP32递推 |
| editable | MetaX gdn_chunk.py、新gdn_wy.py、MetaX专属测试 |
| read-only | vLLM/Plugin/其他backend/当前服务/权重；上游原回归、benchmark不修改 |
| build/lint | compileall与上游black24.8/isort5.12/flake8 7.1；依赖只在本地tmp venv |
| validation | 原7+慢衰减2的原.002/.02与两changed-input graph；新增提交测试与saved-input既有证据分别核验 |
| benchmark | not_run，本PR精度修复Draft，原bench入口保留，性能不宣称 |
| timeout | 有界GPU1800s、服务readiness1800s；不重评GPQA |
| autotune | MetaX FP32 path限定已通过配置，privateWY W4/S2固定tile64，NVIDIA配置不适用；不是最快参数证明 |
| production audit | 新helper只metadata/empty allocation/Triton；取消新增o.to，output直接分配qdtype。原入口contiguous/zeros/metadata-sync沿用，是上游已有路径，不引入torch compute fallback；完整G3历史债务明确留待上游另行清理 |

| 对齐契约 | 冻结值 |
|---|---|
| target dtype | BF16 Q/K/V相等才新FP32链；beta BF16/FP32，g/state FP32；非BF16旧WY保持 |
| shape/layout | B,T,Hg,K / HV,V，HV%Hg=0，K<=256/BT64，Vmajor[N,HV,V,K]，packed varlen及contiguity原语义 |
| output | out原BF16、finalstateFP32、device/七元组/不改initial_state不变；finalstate可关闭/initial可空 |
| promotion | inverse/WY/innovation/hcarry FP32 IEEE；normalized BF16输入量化不重做 |
| scope | forward-only；训练/NaNInf/其他dtype/设备未测不扩展承诺；旧unsupported规则保留 |
| oracle | CPU同quantized-input FP32递推，另FP64代数与舍入根因证据；production不import测试 |

| 路径 | 实现/配置/验证 |
|---|---|
| special accuracy | MetaX Q/K/V同BF16，Triton FP32中间链、指定有限配置，9矩阵+graph与真实模型命中 |
| existing general | 其他dtype旧WY及非FP32inverse beta*K、其他backend文件不变，增加dtype保持检查 |
| unsupported | 沿用当前MetaX K>256等错误，不增加torch fallback或silent retry |
| export/registration | 沿用既有runtime导出，不新增public op；privatehelper无独立注册或NVIDIA配置要求 |

公开issue/PR仅报上述问题与合成复现及结果边界，明确原布局误用已纠正，无性能/模型GPQA因果结论。

PR最终可发布源3files SHA {"src/flaggems_vllm/runtime/backend/_metax/fused/gdn_chunk.py": "5e25ad426ca99400e4fa778fbbe133fccb4d8b37c59cb9a93f9f67e2d1bac5f8", "src/flaggems_vllm/runtime/backend/_metax/fused/gdn_wy.py": "082a40de047525acdce21fbded2187da084f6ae0622d056730cdd9d1ea9f61d3", "tests/test_FLA/test_metax_gdn_prefill_state_precision.py": "d9bac7f63288e7b1eab8cfdccc6404d34e799d3957830c4e8e8bf095e8f605e1"}；检查black/isort/flake8/compileall/gitdiff均通过。FP32输出dtype直接allocation，不新增Torchcast；非BF16默认DOTprecision/tuning用dtypegate保持。新增公开合成9graph+BF16/FP16 noFinal2，共11cases；FP32legacy/static保持但硬件不重测，不宣称其他dtype完整覆盖。

公开upstreamarchive commands/op008-upstream-base.tar SHA df015d5add26d02ec02b6431782dc6ebdfc05d8e2ef0dd383cbb8284f9d97ed9

/public-flash/jinghao/qwen3.6-27B/optimize/flash_attention/20261012-qwen36-27b-metax-flash-attention/commands/op008-public-pr-files.json SHA 2cf7fd26cc3f8de708cde8fce4f8bdb1ecf6d4a7694ef27707b063a1e2531e3d

/public-flash/jinghao/qwen3.6-27B/optimize/flash_attention/20261012-qwen36-27b-metax-flash-attention/commands/op008-prepare-scratch.py SHA 307b0e434045d4e27ce3b7e3847f343cee71b28fb7f1f4a8a866fcdf96bbe02c

/public-flash/jinghao/qwen3.6-27B/optimize/flash_attention/20261012-qwen36-27b-metax-flash-attention/commands/op008-pr-original-matrix.py SHA 2a63bf68f34a33307f0eb7135b3ada73544c578e1947da97332de1b7d5efac7c

/public-flash/jinghao/qwen3.6-27B/optimize/flash_attention/20261012-qwen36-27b-metax-flash-attention/commands/start-op008-pr-restore-01.sh SHA 69b353550bdb3d1119d17217df7f3eab316690c191f5a1db43e007703723a934

/public-flash/jinghao/qwen3.6-27B/optimize/flash_attention/20261012-qwen36-27b-metax-flash-attention/commands/op008-bind-op008-pr-restore-01.py SHA 810302c771d10a8a1a31b9cf6a7aac3e7561faa114c2eecc2149258dd5b058d4

/public-flash/jinghao/qwen3.6-27B/optimize/flash_attention/20261012-qwen36-27b-metax-flash-attention/commands/op008-pr-controller.py SHA 901557c7177672909fbdc957a40d580b92b25d635639a86627185374f1b7ce26

/public-flash/jinghao/qwen3.6-27B/optimize/flash_attention/20261012-qwen36-27b-metax-flash-attention/commands/op008-launch-pr.py SHA f776b167dde591cab8814afa7b46899acddd515c90a150ec3a8d26e054e00354

2026-10-14终态：completed/draft-pr-published/current-source-restored。已更新[Issue #923](https://github.com/flagos-ai/FlagGems-vllm/issues/923)为正确V-major输入下BF16中间舍入累积导致final-state超原容差，并创建[Draft PR #925](https://github.com/flagos-ai/FlagGems-vllm/pull/925)。PR正文`Fixes #923`，issue反向链接PR；已附加到当前任务。fork ZenithJoyH/FlagGems-vllm、分支fix/metax-gdn-prefill-state-precision-923、head83333ea402b45daa8b0a4e1a1e4e7248f50598d0、treeead3ba692a252321e89b1479bd9f09da27ec6f8e。读取GitHub复核issue正文、PR head/draft、恰好三文件及全部内容逐字一致；未合并。CI单次查询未返回commit status或fork workflow runs，不视为CI通过。

公开回执：`/public-flash/jinghao/qwen3.6-27B/optimize/flash_attention/20261012-qwen36-27b-metax-flash-attention/results/op008-publication.json`、[issue正文](../../../../docs/cases/20261012-qwen36-27b-metax-flash-attention/op008-issue-body-public.md)、[PR正文](../../../../docs/cases/20261012-qwen36-27b-metax-flash-attention/op008-pr-body-public.md)。三文件只包含MetaX forward精度修复/合成测试，不含其他优化、部署或私有输入；无新增Torch计算fallback。保留Draft，性能代价、backward、其他平台及dtype完整覆盖待评估，不能宣称模型GPQA或端到端收益。

外部证据根目录沿用本案例，终态控制器results/op008-pr-validation-progress.json SHA4bd58e16a46a9bf19adaf14483dd55accb81daa14f6bca03dbc9760f01c82115。原版synthetic seed100复现final-state断言失败，7870/393216元素超限，报告的最大超限元素绝对误差.010247725993394852；output此前通过。日志logs/op008-pr-upstream-reproduce-slow-carry.log，results/op008-pr-baseline-junit.xml；不是编译失败。

最终公开源码测试11 passed/85.55s，日志logs/op008-pr-published-regression-tests.log、results/op008-pr-candidate-junit.xml。原9矩阵/18改变输入graph及保存失败输入另行核验通过，results/op008-pr-original-matrix.json SHA583d71712eeb5b016a064438c4f694d0894d592569fb4f92da78e3af4bf28468；原atol.002/rtol.02保持，原失败点误差5.4016709327697754e-08，输出和状态超限均0。公开源码从独立scratch导入，gdn_chunk SHA5e25ad426ca99400e4fa778fbbe133fccb4d8b37c59cb9a93f9f67e2d1bac5f8，与发布字节一致；私有失败tensor未发布。

恢复op008-pr-restore-01，精确实例qwen36-fa-opt:390234:1791956405.71，manifests/op008-pr-restore-01-service.json SHA2cedc22e4db40be53e18969f7c14b371513a3a05d94ff4f33f70d4bdf9911208。运行目录仍为OP007已验证源码，四repo SHA/TP2BF16/8192/prefixoff/完整21项白名单相等，FG attention=1、无blacklist；未把公开scratch重新部署进服务。新双rank graph各190launch、96precisionWY/prefill命中和两smoke通过；既有C8同源码/同配置等价回执results/op008-op008-pr-restore-01-C8-equivalence.json SHAa555fe61a5f99adc7d878d82dccb558d1a21d03cb1259228eaacb42f7a9d9677，new_C8_requests0。终态只读再次核对PID390234及出生时间1791956405.71相等。源8002、其他GPU任务/共享源码未操作；未重跑正式GPQA或性能，历史native50000的158/198失败保留，无正式gate。
