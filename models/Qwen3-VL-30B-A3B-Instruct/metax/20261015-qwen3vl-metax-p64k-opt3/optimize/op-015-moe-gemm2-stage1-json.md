# op-015：通过现有 MoE JSON 使用 stage1

已在独立容器8111生效，28组完整MoE逐bit一致及生产双卡graph/replay、17次smoke/C8通过；只调整GEMM2小M的stage参数。其他配置和源8000保持；端到端收益未测，正式精度暂缓。

用户要求保留采样回退、gems-opt 与其他配置，只调整 GEMM2 stage。当前 PR595 标准 JSON 同一行用于两个 GEMM；M64 num_stages=3。严格只改 GEMM2 需要新的阶段配置约定，直接改行则同时影响 GEMM1，已向用户明确两种选择。

## 实施前契约

| 项目 | 冻结值 |
|---|---|
| 目标 | mx-59 / qwen3vl-p64k-opt-20261015 / API8111 / TP2 GPU0,1 |
| 模型/输入 | Qwen3-VL-30B-A3B BF16；MoE E128/topk8/hidden2048/rank intermediate384 |
| 允许变更 | 当前 Plugin MoE JSON；仅用户选择 GEMM2-only 时扩展库阶段加载 |
| 禁止变化 | 采样参考路径、gems-opt/c3c5f5ab、sort、其他 JSON 字段、黑名单、启动参数及 vLLM 源码 |
| Build | 纯 JSON/必要 Python，无重装或依赖更新 |
| 验证 | 当前选择器 CPU 重放/边界/标准 JSON 兼容；空闲且允许重启后最小数值、生产 graph capture+2 replay、smoke/C8 |
| 性能 | 当前不建立收益结论；后续同配置稳态端到端测量 |
| Timeout | CPU检查60s；若允许运行，数值300s、服务启动600s/请求120s |
| Autotune | 本轮是外部已调优参数选择；不新增 kernel 或 NVIDIA autotune 候选，豁免新 tune_configs |
| fallback | 原有配置/算子路径，不新增 torch compute fallback |

数值契约：不变更 tensor dtype、累加/输出类型、路由、SiLU、缩放、求和顺序定义；仅 num_stages 编译调度参数，实际误差须数值验证，不以静态语义声明代替。目标 inference forward；量化、其他平台、训练不扩展覆盖。非命中文件沿现有 fallback，零 token 等原路径保持。

路径契约：标准 JSON 最近 M 选择及设备名优先于 vendor 别名保持；目标行调 stage，其他行不变；未指定配置目录和其他 E/N/dtype 保持原路径。验证脚本放案例目录，不向两个算子仓库新增 test/perf 文件。

## 准备阶段（已完成）

用户已明确选择仅 GEMM2 阶段配置支持，并允许当前测试全部结束后重启验证。新增 gemm2/ 下同名标准完整 JSON，原共享 JSON SHA ec38e926b545f76888b4d4a1775405df422b6d66ba5a4659203090c4a6073ffa 保持。M64 行 stage1，M65 恢复 stage3，其他行复制原表，使最近 M 的边界和所有其他选参不变。库只增加通用阶段目录读取与 MetaX GEMM2 配置选择，校验 BLOCK_SIZE_M 相同以复用原 token alignment。Plugin 只补 package-data，apply 不加特例；库无 vLLM/Plugin import。

CPU 执行真实 loader 与 selector AST，M0..65536、三种配置 dtype 共589863项检查通过。GEMM1 全部不变；实际变化仅 M49..64 的 GEMM2 stages3→1，M8..48 已是1；M65/544/545等边界、缺阶段文件、device/vendor优先级、dtype/E/N不命中、缓存副本与错位BM报错均通过。此为配置证据，不是 GPU 数值或性能通过。

控制器3176925已启动等待，只有 P64 三个成功轮次与 SUMMARY 写出、服务空闲、无 benchmark 客户端、精确 API 与源码身份未变才停止8111。当时尚未修改产品文件、未发验证流量；之后执行28组数值、6组数学参考、独立graph及生产双worker16次replay、17次smoke/C8。正式精度仍暂缓，性能收益未测。

远端脚本/补丁/CPU结果：/public-flash/jinghao/qwen3-VL/20261015-qwen3vl-metax-p64k-opt3/commands/op015-gemm2-stage1-20261017；控制器日志为同一案例 logs/op015-controller.log。

## 实际交付与验证

已在用户 opt6 三轮全部完成、SUMMARY 写出且服务空闲后写入独立容器 qwen3vl-p64k-opt-20261015，重启同一 argv 的8111/qwen3vl-opt6。当前 API PID 932846；当前服务清单 /public-flash/jinghao/qwen3-VL/20261015-qwen3vl-metax-p64k-opt3/manifests/op015-service.json。源8000容器源码、镜像、挂载保持，gems-opt与vLLM工作区未变；原共享JSON保持原SHA。

配置入口仍为 VLLM_TUNED_CONFIG_FOLDER=/workspace/vllm-plugin-FL/vllm_fl/configs/moe/metax；新增 gemm2/E=128,N=384,device_name=metax.json。根表供GEMM1，MetaX GEMM2另读可选阶段表，缺文件时沿用共享表。阶段表使用相同完整扁平格式，未加入vLLM不识别字段；M65行用于将较大M恢复到原stage3区间。对两个GEMM复用的token alignment校验BLOCK_SIZE_M一致。Plugin apply、FlagGems、vLLM和采样入口未改。

minimal-regression：28组BF16/FP16完整MoE前后对比通过；最大绝对差 0；全部逐bit一致=True。另有6组独立PyTorch数学参考，10次独立graph capture、各2次replay；生产FULL_AND_PIECEWISE双worker各16次原始replay，17个smoke/C8请求通过。真实M64 dispatch确认GEMM1 stage3、GEMM2 stage1，所有其他config字段相同。外部observer有界撤销，不添加产品测试/perf文件。

CPU选参检查覆盖M0..65536及三类配置dtype，实际仅M49..64/GEMM2 stage3→1；M8..48原已stage1。测试覆盖空输入、边界M48/49/64/65/544/545、大M8192、缺文件/不匹配dtype和E/N、硬件/vendor优先、缓存副本隔离和BM不一致报错。

没有执行新端到端性能对照，不能据此宣称恢复opt4；正式GPQA按用户指令暂缓。已测硬件仅MetaX，GPU数值覆盖BF16/FP16；其他dtype/平台未据此签发通过。PR准备范围为当前集成，跨仓依赖是FlagGems-vllm阶段loader与Plugin阶段配置/打包规则。

回退准备：commands/op015-gemm2-stage1-20261017/rollback.py，仅在自己的精确API停止且无测试流量后恢复4文件；不会回退gems-opt、采样或其他配置，恢复后重启。未自动执行回退。

最终验证 /public-flash/jinghao/qwen3-VL/20261015-qwen3vl-metax-p64k-opt3/results/op015-final.json；SHA256 55520a2edf6c798492ea23934b1982a5fc74e75f788d59a088e7c14e4b4214d2。数值 /public-flash/jinghao/qwen3-VL/20261015-qwen3vl-metax-p64k-opt3/results/op015-numerics.json；服务 /public-flash/jinghao/qwen3-VL/20261015-qwen3vl-metax-p64k-opt3/results/op015r2-health.json；原用户完整CSV校验及内容记录于 commands/op015-gemm2-stage1-20261017/completed-user-benchmark.json。完整SHA索引见state.yml本实验evidence，原始日志仍保存在远端。

## 验证工具事件与结果边界

初次控制器传完整快照作命令行参数触发ARG_MAX，发生在产品写入前；改为读取已保存快照路径。初次生产启动的外部import观测器未防止在途导入帧重复安装hook，重复写证据触发FileExistsError。该运行记measurement-invalid，日志logs/op015-service.log与初始launch保留。最小CPU复现显示重复安装3次，加入class sentinel/first-call保护后为1次；只修改外部观测器，产品四文件未再变化，生产原范围在新op015r2证据命名空间重跑通过。恢复脚本另显式识别同start_ticks的已退出Z进程并使用唯一执行产物，未覆盖失败证据。

实际API932846、KV562992tokens；最终观察无运行/排队请求。原runtime环境和argv沿用，验证仅额外设置observer目录的PYTHONPATH，详见manifest temporary_observer；两worker import/apply/dispatch/replay观测hook均有界恢复。未修改启动脚本加入该观察器，用户之后按原脚本重启仍直接加载产品阶段配置。

## opt7 性能后续（2026-10-17）

[diag016](diag-016-opt7-stage1-gap.md)核验当前源码/两份JSON与本次交付一致；用户重启的新API942226与本次验证API932846区分。手工P4K SUMMARY为867.38TPS，比opt6低3.69%、比opt4低11.98%，stage-only未恢复性能；该差值不是受控stage因果贡献。新服务未重新注入dispatch观测hook，不能把本记录旧身份的graph/replay证明直接重绑定。GEMM1及tile/warp/group保持原选择的承诺不变，这也意味着未恢复完整opt4参数组合。
