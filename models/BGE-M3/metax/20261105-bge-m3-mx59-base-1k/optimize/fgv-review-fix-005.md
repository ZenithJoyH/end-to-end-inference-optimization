# fgv-review-fix-005：FlagGems-vllm PR 审查修复

2026-11-09，用户明确要求修复审查问题并直接应用 BGE-M3 实际安装源码，保持功能不变。沿用已验证独立容器，使用当前空闲 GPU7，源服务不重启。先核验当前三库、安装、模型与挂载一致，再跑新 baseline；源码私有目录不受共享挂载覆盖。此轮为维护修复，不恢复 batch-budget-004。

## 优化内容与边界

FGV-R1 抽取共享 FP32 metadata/能力校验，在布局复制前调用，同时保留底层 API 防护；FGV-R2 使用固定 vLLM0.24 34 参数契约，不依赖本机 vLLM 源码；FGV-R3 使用设备局部 Generator。补算子 marker、非连续非法参数零 copy/launch、RNG、无 vLLM 和 NaN/Inf 测试；扩展仓库 benchmark 比较默认 direct profile 与既有 FP32 选择策略。kernel AST 和 heuristic 配置必须保持不变，不放宽容差。

## 验证契约

既有 FGV FP32/half/swap/API 全集与新增用例，python -O 错误路径、完整 diff pre-commit；FP16/FP32/native/C8/8种joint 配对模型回归，atol1e-5/rtol1e-4 不变。模型沿用既有 eager/不支持 encoder prefix cache 的范围，不宣称 graph 或正式 GPQA gate。算子 microbenchmark 以仓库 kernel 计时、同输入两策略、3轮全部保留，覆盖127/128/129、1024/1025、4096/8192、1/16heads 与D128/256守护。资源 guard 不关闭以制造 OOM；不把 microbenchmark 当作端到端收益。

## 外部证据与执行

根 `/public-flash/jinghao/BGEM3/test/perf_test/benchmark_results/bge-m3/20261109-bge-m3-fgv-review-fix-005`；所有命令执行前保存 commands 并冻结 SHA，原文备份 before/source 与 before/candidate。准备工具先检查原 patch SHA、源码/安装/模型与挂载，发布工具必须匹配旧逐文件SHA及 VALIDATED.json 绑定的 manifest。任何失败停止发布、保留原始日志。当前准备中。

准备门禁通过：当前三库/安装/模型及挂载一致，GPU7空闲，源BGE-M3当前无运行模型服务。最终pre-commit导入分组与首次manifest不同，尚未部署任何代码；保留初版材料，使用manifest-v2/deploy-v2/payload-v2冻结最终格式。先前baseline命令因工具文件未上传而退出，未启动服务。functional.py SHA `555bcff9178de011605f7c2d6ffc9f9a5013a3a31d24e564c4ede57ec832488d`，deploy-v2 SHA `6f1ff542137eace363649b685e2be07bcc3df757db2aed42fab369d07bed0594`。

测量前复核：kernel事件计时可能受host patch空隙影响，改为仓库cudagraph模式计时，确保策略override只在capture执行，不计入replay。新增算子真实capture与两次新输入/哨兵replay测试；不扩大模型graph支持。最终使用manifest-v3/payload-v3/deploy-v3，内核和heuristic仍不变；尚未部署v1/v2。validate.sh SHA `94c52382be3b625efccfb48501f9637496b76b2337689e970407b1743f66c3ef`，manifest-v3 SHA `1cc8264b84a1ea859e58a98295cabf1a4282449ddcd441f268b9926de6fc13a4`。

隔离候选已部署，patch SHA `34ebbd6c6b976f7ce2ce779b86c13f4c2e09752d670ca81158ef57dc648d4f2e`。发布门禁 gate.py SHA `2afaa104d200305c36f2553a322de79ce709b88ff0febca5c31b5a2c89105f89`，rollback.py SHA `a14fc2f8739c2f117744ce2fba1bdd71aeb809ceeb8b65fc862b62fc42123e71`。门禁要求JUnit零失败/错误/skip、既有数量不减、127060模型数值配对通过、pre-commit通过、manifest与kernel AST不变。回退仅恢复本轮四文件且拒绝后续漂移，不重启源服务。

封存工具finalize.py SHA `3230fd0526f5636dda95e2cfb34725a4c1e8d80190e0f539a5bf5db8317db31a`，发布后再次核验source/candidate三库一致、安装/模型/原服务状态不变、GPU7释放，并封存FINAL_REPORT与SHA256SUMS。NaN/Inf本轮覆盖V的三类非有限值及独立FP64对照，不新增Q/K非有限值语义声明。

最终发布入口commands/publish.py SHA `6f2dc60d6206aa4e3f1c589a33659418574162204103b5e59911ca1a7f2d7b9f`：源完整指纹须与开始时完全一致，隔离候选diff --check及门禁通过后才执行source部署；最后再次diff --check并核验源码/导入/模型/原服务和GPU7释放。不会停止或重启源容器。

发布前另核验3轮各16组benchmark原生数据：正数有限latency、确切shape、零error、cudagraph模式；3轮全部保留并汇总median及所有回退shape。benchmark-check.py SHA `cc15c71a438060b8b145c2b3ccc22538e42ae1a77e6cb20911d81e148ab3740a`；最终只执行commands/run-publish.sh（先benchmark检查再publish门禁），SHA `db602e0041d35fa080501e8f275ba469fb637abd35d2615da745c1cacff7446a`。

## 最终结果

已应用到 `BGE-M3:/workspace/bge-m3/tune-src/FlagGems-vllm` 实际 editable 源码，源与隔离候选完整指纹一致。最终 patch SHA `34ebbd6c6b976f7ce2ce779b86c13f4c2e09752d670ca81158ef57dc648d4f2e`；HEAD 不变。仅修改 attention.py、flash_api.py、tests/test_flash_attn_varlen_func.py 和 benchmark/test_flash_attn_varlen_func.py 四文件；其余原有 diff 保留，原 kernel AST、direct.py、launcher.py、heuristic 配置不变。没有修改 FG、Plugin、vLLM、权重、启动脚本或源码安装绑定，没有 commit/push。

- FGV 常规166、python -O44、Plugin364，共574项回归通过；零fail/error/skip。python -O仅有pytest预期assertion模式提示，未放宽容差。
- 原13个配置策略参数用例现在可由算子marker收集。基础ABI测试使用独立固定vLLM0.24契约；无vLLM模块可用时仍通过。
- 非连续非法输入在ensure/copy/attention之前拒绝，out不变；局部Generator可复现且CPU/当前设备RNG不变。V NaN/+Inf/-Inf与独立FP64 oracle对照通过。
- FP32算子真实graph capture及两次新输入、NaN哨兵输出/LSE replay通过；这不表示BGE模型graph已获支持。
- 新baseline与candidate配对：FP16/FP32/native/C8及8种joint输出，共127060数值逐位一致，max_abs=0.0，原atol1e-5/rtol1e-4不变。
- FGV完整diff 8文件的pre-commit通过；部署前后diff --check通过。
- 用户曾停止的MBT实验未恢复。本轮启动和清理仅限隔离容器临时服务，GPU7已释放。源容器在任务开始/结束均无运行模型服务；没有为了发布启动或重启源服务，不能把历史health状态当作当前在线服务证明。

## 性能验证

同GPU7 MetaX C550、FP32/packed self-attention、同IEEE运算和资源guard，仓库cudagraph计时比较“默认direct配置选择”与“既有FP32选择策略”。3轮各16shape，所有轮次保留，下表为3轮延迟中位数，单位ms。**此对照用于补齐原有调参策略证据，不是本轮校验维护改动的性能收益，也不是端到端吞吐结论。**

| length / heads / D | 默认profile ms | 现有策略 ms | 加速比 |
|---|---:|---:|---:|
| 127 / 1 / 64 | 0.028330 | 0.028351 | 0.9993x |
| 127 / 16 / 64 | 0.029031 | 0.029020 | 1.0004x |
| 128 / 1 / 64 | 0.028349 | 0.020989 | 1.3507x |
| 128 / 16 / 64 | 0.029012 | 0.021162 | 1.3710x |
| 129 / 1 / 64 | 0.031328 | 0.025010 | 1.2526x |
| 129 / 16 / 64 | 0.032218 | 0.025326 | 1.2721x |
| 1024 / 1 / 64 | 0.201711 | 0.138373 | 1.4577x |
| 1024 / 16 / 64 | 0.590589 | 0.325123 | 1.8165x |
| 1025 / 1 / 64 | 0.204774 | 0.204748 | 1.0001x |
| 1025 / 16 / 64 | 0.598260 | 0.420745 | 1.4219x |
| 4096 / 1 / 64 | 0.542271 | 0.541869 | 1.0007x |
| 4096 / 16 / 64 | 5.803403 | 4.603803 | 1.2606x |
| 8192 / 1 / 64 | 2.324838 | 1.860546 | 1.2495x |
| 8192 / 16 / 64 | 23.150816 | 18.221963 | 1.2705x |
| 257 / 16 / 128 | 0.084342 | 0.084418 | 0.9991x |
| 257 / 16 / 256 | 1.281709 | 1.281336 | 1.0003x |

所有实测回退也已保留：P127/H1/D64延迟+0.073%，P257/H16/D128延迟+0.091%；这两组策略本身不变，不据微小计时波动宣称真实回退或收益。D128/D256安全guard两侧保持相同，不移除guard制造OOM，也不声称已量化guard本身加速。阈值两侧与长上下文已补测，kernel结果仍按原精度验证。

## 决定、风险与回退

保留本轮维护修复，FGV补丁可交PR review，仍如实披露其他厂商硬件未测、仅有既有mock ABI证据，以及未执行正式精度/端到端性能验收。没有新增FA4、NV FP32、模型graph或Q/K非有限输入语义支持声明。算子目录/注册/公开API不增加新operator。
必要回退：`docker exec BGE-M3 /flagos/bin/python /public-flash/jinghao/BGEM3/test/perf_test/benchmark_results/bge-m3/20261109-bge-m3-fgv-review-fix-005/commands/rollback.py source`；先核对4文件仍为本轮SHA，才从before/source恢复原文，拒绝后续漂移。回退工具已保存未执行，不重启服务。

最终证据：`/public-flash/jinghao/BGEM3/test/perf_test/benchmark_results/bge-m3/20261109-bge-m3-fgv-review-fix-005/FINAL_REPORT.json`，SHA `5043609db769ab8ceb48e252e96f50877abf178a01a2eab0c54408c021e2143b`；`/public-flash/jinghao/BGEM3/test/perf_test/benchmark_results/bge-m3/20261109-bge-m3-fgv-review-fix-005/SHA256SUMS.json`，SHA `fafb265a911e76f8d738f0421098fe1a06dbd248aabdff3dc29bd5185c7b739f`。模型原始输出、全部原生JSON、JUnit、benchmark轮次、最终完整patch和逐文件备份均保留远端。`BENCHMARK_REPORT.json`保留全部16shape三轮及所有回退。
