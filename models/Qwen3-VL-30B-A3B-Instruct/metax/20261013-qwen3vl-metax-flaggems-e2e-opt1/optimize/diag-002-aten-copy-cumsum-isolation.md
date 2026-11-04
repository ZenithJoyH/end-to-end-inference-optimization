# diag-002 copy_/cumsum 性能波动隔离

用户2026-10-14明确要求保留收益较大的MoE优化，允许先将copy_、cumsum加入黑名单定位ATen波动。此指令仅覆盖该两个算子的诊断性切换；保持USE_FLAGGEMS=1、FL、其他原blacklist及MoE链路。op002原补丁在私有优化容器重新保留，源qwen-vl不改/不重启，vLLM只读，暂不做GPQA。

证据：diag001的8warm恢复未准入（6.69%>5%），但无>800ms token间隔；两seed两rank延迟trace均有效。seed7/8纯Decode相同tile下G1均值175/191us、G2约158/168us，跨seed内容/计算差异存在。Mixed内部全GPUgap从约16–18ms到160–196ms，CPU重叠copy_/cumsum/MoE；尚不能区分JIT/profiler/主机原因。pointwise_dynamic将stride编译为constexpr，copy_手动instantiate(rank)不走自动prepare_args；动态stride可形成新编译变体。但未在已检查默认Triton缓存时间窗找到相应新元数据，不能断言JIT根因。

契约：新同配置P1024/D1024/C64/N128 finite_batch B/C/R，op002所有角色相同（private FG-vllm SHA a3a271...），Baseline/Revert原四项mm,mm_out,layer_norm,log_softmax；C追加copy_,cumsum。单独比较该一次有意义的dispatch干预，不把先前失败数据混入。每角色新进程5warm+3measure，末3warm TPS spread<=5%，测量main/guard spread<=10%、B/R drift<=10%；主指标输出吞吐不退化（min_gain=0，此为稳定性诊断不是新5%收益门槛），P99TTFT/TPOT退化<=5%、P99ITL<=10%。1process/role用于快速定位，结果不等于两进程/role正式验收。每轮timeout600s、每实例外层2100s。一次系列；准入/请求/真实dispatch失败则停止并保留证据。

每实例16个短健康请求/C8，两个worker graph capture及16replay，bounded hook已撤销；新增CUDA dispatcher表证明copy_/cumsum是否取消FlagGems注册，MoE函数来源和GEMM2 stage1证明仍命中FlagGems-vllm。不修改产品worker/plugin逻辑。若关闭两项显著降低波动，再拆copy_和cumsum定位并优化FlagGems实现；若未改善不扩大blacklist，查其他主机/动态shape/路由因素。采集on时序仅归因，不作为收益。

执行前归档（remote-case commands下）：

- `prepare_aten01_isolation.py` SHA256 `e389727702cf261953139d8a8951c6cac31f5a7d0fd82b8057dfced65d271a3f`
- `aten01-bounded-observer/sitecustomize.py` SHA256 `15a9098300daad752653c68f5aa1bd9f41ea10ae8d21521344ad3f10f214f05f`
- `compare_aten01.py` SHA256 `f0e37480b8f39084c722e2fe3c0715d50f6f07691b8e0fb9e3ef9f9c693a97bb`
- `run_aten01_isolation.py` SHA256 `0bd52d48f80ea2c1b7708f1715d2f8dd683ffacb0ef94a8c0c0f7c99cb8685c7`

执行命令：`ssh mx-59 python3 <remote-case>/commands/run_aten01_isolation.py`。相同的临时observer路径用于三个角色，只在启动取证后撤销；黑名单差异绑定到comparison variable_path。

执行前澄清停止规则（尚未启动任何diag002实例）：请求/身份/dispatch失败停止；单角色warmup未准入则不收测量数据、保留native failed回执，仍各执行一次其余开/关/恢复角色作因果隔离，不盲重跑同角色。有不完整角色不计算精确收益，保存incomplete-isolation。早期准备v1未执行，实际v2 `commands/run_aten01_isolation_v2.py` SHA256 `aec45d128a97d408431b1b249597fbfecbacf9cd756ab6778fc7a11bf4bc903c`。运行命令：`ssh mx-59 python3 <remote-case>/commands/run_aten01_isolation_v2.py`。

完整生成回执 `<remote-case>/results/aten01-preparation.json` SHA256 `8610fc37d263cbb54902a4cde2f33ea7f3623fa113e376b5e596b0472eb1b5b5`；plan SHA `0310eb946e021c0b6a61dcd52b76965bd6df63d28a4dd3681982a0d0c1ae5fe9`，comparison SHA `c95a4485d755f78244e4eb35e6f181ee3aad24f42188ef76ffd8e664c6e6cd9e`。

新B健康/manifest/dryrun通过，两worker G2 stage1且copy_/cumsum CUDA表均/dev/null:488（FlagGems）。执行前收尾脚本 `commands/audit_aten01_final_sources.py` SHA256 `d37c717ed0692bde61243fbe477c12443e5f51faaac3d418b105f7475f98c194`；源四仓库须原身份，private仅允许已保留op002一文件且FG-vllm完整hasha3a271684679628c7574eb0040a9fe8988141ffdc99b516d973849af66a3ba73。R必须恢复原四项blacklist、仍stage1。

收尾核验实际使用 `commands/audit_aten01_final_sources_v2.py` SHA256 `04eaf9c0cc42a0cec7eaaf420e4313d0cda2717d4388ba99b2ae2ab2165859a1`，先验证R原四项blacklist/stage1与own18430连接拒绝，再写passed；v1未执行。

C健康/graph/manifest/dryrun通过；两个worker `aten::copy_` CUDA改为native CompositeExplicitAutograd默认后端、`aten::cumsum`改为native RegisterCUDA_0.cpp:8524；MoE G2 stage1不变。`cumsum.out`仍FlagGems/dev/null:488，本轮未扩大blacklist；如果仍出现其调用，需按真实trace区分，不声称所有cumsum overload均关闭。

C回执complete，warmup准入2.2426%。测量display TPS=[1718.36,1822.65,1726.71]、P99TPOT=[37.381,34.821,36.739]ms，三轮请求均128成功/0失败，比B同seed慢。先做R恢复验证，未将两项关闭作为保留候选；op002继续保留。

结果（稳态3轮中位数；1新进程/role，P1K D1024/C64/N128，非正式验收）：

| 状态 | 输出token/s | P99 TTFT ms | P99 TPOT ms | P99 ITL ms | TPS波动 | TPOT波动 |
|---|---:|---:|---:|---:|---:|---:|
| 保留MoE、原FG ATen |1919.53|3610.63|32.89|33.77|5.71%|6.41%|
| 关闭copy_/默认cumsum |1726.71|3558.71|36.74|36.93|6.04%|6.97%|
| 恢复两项FG |1901.62|3586.37|33.16|33.92|5.44%|5.95%|

关闭吞吐-10.05%、P99TPOT+11.70%，原生comparison failed是候选不满足门槛（不是原始数据失败）。仅变化blacklist env；三role原生run-record全部complete、24warm+measure轮均成功。旧数据不混入。控制程序最终compare返回1后raise，但所有服务此前已精确停止，无重跑/覆盖旧产物。

稳定性没有改善：关闭组r6仍97个>800ms间隔、max944.11ms，B/R均无>800ms；不能把先前稀有1.09s停顿仅归因于这两个FlagGems默认ATen。cumsum.out仍FG，本次未隔离单项/所有overload，JIT、profiler及其他主机原因未确诊。两seedM64 MoE kernel计算差异有trace证据，但未采router分布，不断言路由为唯一根因。

决定：按用户指令保留op002；临时两项blacklist已恢复，不作为性能候选。private仅FG-vllm op002一文件改变，源四仓库原身份、qwen3vl-opt1/8000 healthy、own18430关闭。精度暂缓，无GPQA、无正式精度gate或四场景验收。后续如需定位单项，做copy_-only/cumsum-only；不因组合退化断言单项都无价值，不扩大黑名单。

原生comparison `/public-flash/jinghao/qwen3-VL/20261013-qwen3vl-metax-flaggems-e2e-opt1/results/aten01-p1k-comparison.json` SHA256 `4170cbd033684780dea9ebb58b754dbcd16e54ce112a4a44be650b02b8bbef3c`；summary SHA256 `dfea39f9a7586abf35f25b3fd352edc1b1c18baa965db77bff43d40622653008`。收尾audit `results/aten01-final-source-audit-v2.json` SHA256 `2681a64ddafdb9f23791ca4c20e092f5b655942a2308dee86a1d911be3cdddf8`。
- `/public-flash/jinghao/qwen3-VL/20261013-qwen3vl-metax-flaggems-e2e-opt1/results/performance/aten01-base-target-p1k-01/run-record.json` SHA256 `3aad0f469e8745a778d67dd09b618b7c605c26a15853f4248bb3b2eb152e2c90`
- `/public-flash/jinghao/qwen3-VL/20261013-qwen3vl-metax-flaggems-e2e-opt1/results/performance/aten01-off-target-p1k-01/run-record.json` SHA256 `e6d8a594d73227d862ef9e8e8222fa76ff4f2543c835558daa9fe6b5175050f6`
- `/public-flash/jinghao/qwen3-VL/20261013-qwen3vl-metax-flaggems-e2e-opt1/results/performance/aten01-revert-target-p1k-01/run-record.json` SHA256 `c90e2daf9bc76b8488875c0e7913dcff56d5e2b364b02b3f7b5face419c5f137`
