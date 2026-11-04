# accdiag-038：randn输出地址i64修复与受控验证

状态completed-operator-and-startup-only，2026-10-19 15:53+08完成终态核验。randn输出地址i64修复已应用于本次8010实际启动的新私有Gems；算子子集与唯一启动验证passed，完整模型最小回归仍incomplete/not_run（用户禁止模型请求）。保留FP32归约/index-i64/QSA M16与固定Plugin/FGVLLM版本，不访问8035，零HTTP推理/零全量GPQA，旧164/198 failed-score/no gate及性能阻塞不变。以下计划、在途与工具修正记录按时间保留，以末尾终态为准。

## 单变量设计与隔离

- 保持Plugin maina696859b+PR4553cb373b1/本地FP32、FGVLLMb4d3382/QSA M16、vLLM/Torch和原CLI；只改Gems `randn_kernel`输出program-id在乘法前转i64，offset_0..3继承i64。不动Philox counter/seed/offset与数值公式、API/dtype/grid、黑名单或权重。不是只把N或最终GEP扩位。
- 不直接修改private017（可能有其他消费者）或全局安装。优化容器未挂载的真实私有`/opt/qwen38-accdiag038-randn-i64-20261019/gems`由原Gems真实复制，去除生成的__pycache__等，全部源文件逐项比对，仅`src/flag_gems/ops/randn.py`允许不同。保留旧版源文件、差异patch、SHA和原目录作为回退材料；不自动回退。
- 非目标平台未硬件验证，修复是通用地址语义而非模型/机器ID特化；不增加Plugin hook、永久开关或dispatch。副本版本元信息按源revision/patch SHA声明，非上游新release。pr_readiness=experimental。
- 创建/测量前重核目标容器镜像/挂载、旧源/包SHA、8010空端口、卡8–15无其他负载和内存；仅只读查询目标卡，不操作0–7/8035。显存不足不抢占/停止服务、不扩大范围。

## 冻结验证矩阵

1. CPU：patch AST/唯一diff、算术边界沿用037正负阈值，已保留i64/index/QSA/FP32关键SHA；bundle与脚本执行前保存。
2. 仅物理PPU8算子测试（CUDA_VISIBLE_DEVICES=8，独立缓存，0模型请求）：旧版仅运行小shape且地址安全，FP32/FP16/BF16，空/1/511/512/513/2047/2048/2049/非对齐及多seed/offset，旧/新结果逐位比较。高block旧地址用有界索引探针写小scratch，只验证偏移与mask，**不运行旧版巨大越界写**。
3. 修复版完整BF16 `N=6400030720`：可用内存至少32GiB，预分配带首尾canary，分chunk填NaN，运行固定Philox参数的生产kernel，分chunk核全部有限、canary未动；选0/2^31/2^32/尾部相邻block，通过独立紧凑RNG reference逐位比较。不得为检查另分配6.4GB bool；chunk<=16M元素。大N原版不执行，也不以此称原→修→原完整GPU因果闭环。
4. 算子graph：生产修复kernel capture+至少2次replay（目标大shape，预分配，无模型请求），核采样block和首尾边界/全量有限；不新增随机算法或调优。不作性能结论。
5. 只有前述通过且测试进程/显存已释放，才仅8010一次startup，原无模型probe的037 CLI/包版本，PYTHONPATH唯一切换新Gems副本；空冷vLLM/Triton cache、保留原tuning/gems设置并记录差异。无模型诊断hook/ptrace/在线埋点。原生退出由事先READY的Host passive process-connector保存，用标准库gate进程exec原命令，避免首worker事件丢失。0HTTP推理；health/metrics只读、startup/capture观察，不要求模型replay或发smoke。

显式成功：算子正确性、canary/覆盖/大N及graph至少2replay，生成TTIR/LLVM证明store乘加已i64；startup两类graph7/7与health200/请求计数0并保存全8rank启动证据。失败/工具错误/非法访问首次冻结日志/原始信号/IR与配置，不自动改其它算子、重置卡、重启/恢复或扩大请求。服务如成功则保留；原生loop90min只等待，预算耗尽不杀模型。

## 原始证据

执行前冻结：`accdiag038-randn-i64.patch` SHA b4436836ac5d4656ec54c51101eba5bf8d5422a6b73c4735f836627a49eb02b1；`accdiag038-prepare.py` SHA 58b05fb76988b486f2cb9133d491d26dd407124dcfda549fa05f937981c63303（stdlib隔离/源核验，仅SMI只读，无GPU计算）。按单张卡查询8–15，PPU-SMI不支持逗号多卡selector，不把该工具用法失败计作设备故障。

准备v1已通过8–15空闲/镜像/挂载/全源复制校验，但`git apply --check`因补丁多一行空白上下文拒绝（未应用，0 GPU/0启动）。保留原件，v2仅改patch上下文，不改修复语义；`accdiag038-randn-i64-v2.patch` SHA15fc56d9feca57197e0a988e37a2fd3969d7fec56cca20999197b08f91562a0f；stdlib `accdiag038-apply-v2.py` SHA0026d7f39e9d1d7e04b2c4bffd4693302c9be143cb3290e871dd2c61b5fa64fa先重核新副本全树等于旧源，再apply-check/apply并要求仅randn不同。不是GPU/模型失败后的自动重试。

CASE=`/mnt/nfs/users/jinghao/qwen3.8-flash/20261015-qwen38-flash-next-ppu07-container/accuracy/acc-015-full-gpqa-ppu07-c64-current-i64-qsa-20261018`。
R38=`CASE/diagnostics/accdiag-038-randn-i64-fix-20261019/runtime-001`。commands集中CASE/commands，R下source-before/after、patch、operator-001、service-001、GPU结果/完整日志/被动退出和compile manifest/archive。执行前保存脚本/SHA，排他marker拒绝重复启动。

## 结论边界

终态审计工具成本修正（不改模型）：CPU reader3567233精确命令核验在归档上反复gzip seek（3:21累计读9.5GB、CPU持续工作），非服务卡死。保留旧审计脚本和stdout；若旧report仍未完成，仅`commands/accdiag038-stop-cpu-audit.py`（SHA0b2e1992731ab65b137004f7e563dec4dd1fd5736bbad89e205d9755cf02e4b0）记录自身PID/start/IO/原件并只向该CPU reader发1次SIGTERM（0模型信号），随后运行`accdiag038-startup-audit-stream-v2.py`（SHAfa6369f6f0cb1ead660c792e55976c6790c5fc94456a76fa9d961100db299c58）。V2顺序读tar，普通文件逐字节SHA、hardlink/symlink解析到已哈希内容并逐成员核manifest，保持同一检查标准，写新stream-002不覆盖原件；无GPU/推理测试重跑、无需服务重载。对应采集helper收尾入口`accdiag038-cleanup-watch-v2.py` SHA824ba7218d65e3fa46848bb9ad4ed5e440386c2a4f051dc622708fd1a7ac6dc7仅切换审计报告路径，仍只退出自己的Host采集helper，API/8worker不发信号。旧reader如果已自然完成则不停止、不重跑新审计。

唯一服务启动已2026-10-19 15:46+08 health200，两类capture均7/7、原生Application startup complete；controller已自然退出，归档10649编译文件/1791769590原始bytes，无权重/core导出。终态CPU全量审计在途，不提前称最终完整证据通过。仅结束本次Host被动collector的清理命令已在执行前冻结：`accdiag038-cleanup-watch.py` SHA5e72eaaf921340831eaff1e25c62817deda617cc67c8a55ccc3a4698f2a7b42c，要求终态审计passed、精确helper PID/start/argv与API/8worker不同后只发该helper一次SIGTERM；完整最后内核事件保留、API前后身份/health重核，0模型进程信号/0推理/0访问8035。服务保持运行，自动heartbeat不恢复。

CPU operator独立审计passed：22份现场/320归档成员逐项SHA与byte核验，report b4a8614391f45f7de88bfae78455c14f62e4c57f26524007f7d61a674df3e83c /manifest4b6031ec435abeefdf2a78f2264bc7a35cb22f8d65ddce004a0c90bf4146bea5。service主图编译及KV profile已继续推进，原生PIECEWISE7/7完成、FULL捕获在途；新服务BF16/N64 randn TTIR SHA4215d0ed97e448e90df3b5b38a28c582d317532d9696f7edbc1866dc841039e8逐行核验output_pid扩i64→muli i64→4store i64（不是只看最终指针dtype）。一次临时SSH正则过转义报告false属工具字段错误，随后逐行核实，未改代码/IR/marker。终态后只读CPU `accdiag038-startup-audit.py` SHAcea1b158cfa97af25898f011d5b7c4245640ea5b184418cd0b655988ebd6fb0f将验证精确API argv、8rank存活/TracerPid0、源/挂载、完整缓存归档和原生日志/被动事件前缀、零请求指标；原生capture进度主要rank0输出，不冒充独立8rank hook/replay。

本地Skill绑定复核：accuracy capability e2e/accuracy interface1.0.0、operation minimal-regression、bundle SHA6e94a080dd3b64544c535e1fd4bda506f55516374d14d0f8ca6aa148bba2c7b2；因禁止模型请求，本轮只交付operator-subset/startup，完整model minimal状态仍incomplete。CPU-only `accdiag038-offline-audit.py` SHA0d44a2c3a3f2dde584d1adbab1359ba1ae5f61e4fc993a90711bae4e4cc143c5按已生成证据核81项/18432项/4轮大N/reference/4store TTIR及LLVM shl i64/GEP、完整operator archive成员SHA和退出，不发推理或触碰GPU。`validate-local --records`执行未通过：其他案例缺失文档链接与既存过程产物迁移（493）等历史仓库范围问题，未删除/修复无关材料，不称全仓记录验收通过。

2026-10-19 15:34+08算子子集passed：81项安全小shape/3dtype/seed-offset及wrapper RNG状态逐位相等；18432项有界地址位模式CPU/device一致；固定版BF16 N6400030720完整有限覆盖/首尾4096 canary不变、9个逻辑block与独立紧凑RNG reference逐位相等。eager、graph capture、2 replay各自重验，原危险大N从未运行。进程自然exit0，被动connector无非零/信号退出/采集错误，PPU8测试结束显存回到119MiB。固定TTIR SHA471c826b98b5fccde336ae2157e4fa2f0bfb8bbdfc6687fe88a1f3b69f6c99d5：output_pid extsi→muli i64，4条store addptr均tensor<512xi64>；LLIR SHA4c9a0be7ea895cdf845ee973bb239b366369c105a3ed281ca10880cf2a333fba。operator cache归档320文件/1698498bytes/SHA731edf359e74232cddecb5429100c28eb2ed4b8a0f552c67ca4b43cff0506c27。仅算子正确性，不是模型精度/性能。进入唯一8010 startup；执行入口已冻结control --mode service，启动前重核全源与8–15空闲，无额外请求。

准备v2通过：新randn SHA48d700e32c7c7a57e8414ba944d04cf56bb5c299677233716163504c89d11bd4，12179文件仅1变更、旧树未动。执行前再冻结commands：operator SHA c405aa34462722dee47bf3d79f21a77a8b5dcf387b75765b4d4e16b9fc9cca9b；control SHA86be8f6d07ecf77c84bbc4f3f0754d68d8cadefd0110127575bbf8e902e0c01d；watch SHA c3dae5c0a852a8cba7a18ab28311367fe8e893a76c3178d72ad2b19128aae8ac；gate SHA9fecd3c156266fa2cc745b002d5f0cf6f060614950ea1ebc6f781342931e53ff。operator有界探针用uint32安全模拟旧signed-wrap位模式，避免探针本身触发有符号overflow sanitizer；旧实际有符号IR证据沿用037，不把模拟器称原kernel大N复现。gate先启动仅stdlib，Host按Docker exec精确PID绑定并等待被动connector ACK后才exec测试/服务，无ptrace/SIGSTOP。

算子子集通过与服务能启动，不解决历史GPQA164/198或60K不收敛，不签gate，不恢复性能优化。原037的工具干扰历史保留，不把本轮成功直接改写为完美observer A/B；大N地址缺陷机制与实际startup改进分别报告。需要继续模型精度/请求验证时等用户方向。

## 终态结果（覆盖上述在途状态，不覆盖旧证据）

- 唯一8010 startup正常就绪、health200，8个TP worker存活、API/全部worker TracerPid0；原生PIECEWISE7/7与FULL7/7 capture完成。精确argv SHA5744d999不变，API显式PYTHONPATH加载新private038 Gems；新副本保留017 index/index_put SHA与全部其他12178文件，Plugin647/FGVLLM1061文件、FP32 helper/QSA M16及权重/config前后核验不变，image/mount parity仍passed。未修改全局Gems安装或共享启动脚本。
- 81项安全数值/RNG状态、18432项有界地址位模式、BF16 N6400030720 eager/capture/2replay完整有限覆盖与canary/9block参考均passed；旧危险大N未执行。无新非法访问或任何被动记录的信号退出。服务新缓存3份randn IR（含BF16/N64 SHA4215d0ed）逐份确认乘法前i64与4store地址i64，不是只检查最终GEP。
- 独立CPU startup审计完整10649归档成员（逻辑1791769590bytes），逐项byte/SHA全部一致，归档222422705bytes / SHA67f403da0670b76bae54df769b4400265a8a1ba9c7eb44b837e18a31f928d8ad；report `startup-offline-audit-001/report.json` SHA2c074210fe8d8c22b159babd80fbc6850782a12fee6eb00f15406582921e6066 / manifest32c7f8de75a0462edb0ad084a98cd9861e6bc81d4455c0b2cba6446b81796e11。原CPU审计自然exit0；顺序读V2及stop-CPU脚本仅保存、均未执行，未停止CPU reader，未创建替代审计结果，不重复审计或测试。
- 本轮HTTP推理请求0；实际prompt/generation/request-success counters全部0、running/waiting0。startup内部profile/capture不冒充用户请求，也不是model replay证据。8rank独立诊断hook/逐层/请求token、模型graph两次replay/C1/C8/长生成均not_run；无新的模型精度/性能或正式gate。
- 控制器与CPU审计均自然退出；原版cleanup-watch仅结束本任务Host被动采集helper一次SIGTERM，**模型进程信号0**、API身份/health200前后不变。完整启动内核事件末尾已另存，cleanup回执SHA58307d8187391564eecee47423ce9713fd871b55d54f83483de3abeb223d6801；未访问8035、未触碰卡0–7，8010保留运行，heartbeat保持PAUSED。
- 根因分级：randn旧大N输出地址缺陷confirmed（静态IR/安全device位模式与固定大N证明）；其与037崩溃关联置信度提高（窄修复后本轮启动未复现），但原版危险全N未重跑，037曾有工具时序干扰且没有allocator/最终二进制sanitizer完整现场，不能称完美原→修→原事故因果闭环，更不能解释历史GPQA全部错误或60K不收敛。非目标平台/float64/complex未硬件回归，pr_readiness=experimental；无性能数字。

知识差量refined：N/Philox counter的dtype不能代替每条输出offset乘法的dtype证明；N64比较也不能保护先i32溢出后扩位的负地址。下一次优先从真实大shape反推pid/lane/UNROLL地址链，危险原实现先用小scratch探针和已保存IR，不冒险跑越界大N；修复时保持RNG算法与状态推进并做canary/全覆盖/reference/graph回归。没有理由仅凭formatted-output同步上报栈就认定printf本身是首个错误。
