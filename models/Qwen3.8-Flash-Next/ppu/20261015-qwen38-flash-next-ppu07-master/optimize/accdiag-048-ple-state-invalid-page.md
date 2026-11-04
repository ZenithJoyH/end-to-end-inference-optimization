# accdiag-048：PLE状态kernel非法页访问离线定位

用户2026-10-20要求定位acc016算子故障。范围为现有日志、实际源码、编译产物和CPU地址计算分析；不修复生产源码、不重启8010、不访问8035、不发推理/GPU测试、不重跑全量GPQA。按inference-accuracy-diagnosis及key-operator-analysis执行。

输入事故为acc016：驱动`Exception invalid page`位于`_ple_conv_state_kernel`，随后rank5/4/1 watchdog报非法访问、服务退出。正式结果故障污染incomplete/no gate，旧有效acc015164/198失败不改写。本轮目标是区分实际索引越界、乘法位宽、状态layout与graph复用；没有首次GPU状态/有效索引现场时不得冒充机制已完整闭环。

原始CASE=/mnt/nfs/users/jinghao/qwen3.8-flash/20261015-qwen38-flash-next-ppu07-container/accuracy/acc-016-full-gpqa-ppu07-c64-fp32-fixed-qk-20261020。源码以evidence/source-before.json/source-after.json和实际容器字节交叉核验。远端新离线命令/报告将保存CASE/diagnostics/accdiag-048-ple-state-invalid-page-20261020及CASE/commands，执行前记录SHA；不覆盖原始事故产物。

初始发现：实际Plugin `gpu/ple_layer.py`直接import官方FlagGems-vllm `ple_short_conv_`；QSA-only环境开关不代表所有PLE调用均禁用。`ops/qwen4/ple_conv.py`输出kernel把row提前转i64，但state写回kernel加载row后直接乘ss0，尚须对照实际特化TTIR及驱动故障指令，不能只凭源码静态形态定事故根因。

执行前冻结CPU-only脚本`/private/tmp/accdiag048-offline.py`→CASE/commands/accdiag048-offline.py，SHA `6bfd3600942e541cc5332d2e701d658c7bbe50d969346de12b6b0f291604ed46`。AST编译/地址算术检查通过；本机py_compile写默认系统缓存被拒绝仅工具缓存权限，不是源码语法或模型事故，改用不落pyc的AST检查，未更改目标代码。脚本只复制已有事故日志/源码/编译二进制到排他新D，离线llvm-objdump，CPU计算合法row地址并与驱动寄存器反推核对；docker exec清空PYTHONPATH/CUDA且不import模型/Torch/Triton，不加载或执行kernel。执行命令仅`python3 CASE/commands/accdiag048-offline.py`，不重试、不覆盖旧证据。

## 离线结论

**已确认源码及编译路径存在地址位宽缺陷，且本次驱动寄存器与该机制精确吻合；事故归因为高置信度，修复/设备验证尚未执行。** 问题在FlagGems-vllm，不是FlagGems通用index/index_put，也不能把NCCL watchdog当首错算子。

实际库`/opt/qwen38-fgvllm-main-20261019-b4d3382` HEAD `b4d3382bb04da4e0ab444849697865b4d5fcd86e`、git工作区clean；`src/flaggems_vllm/ops/qwen4/ple_conv.py` SHA `163ebcd33074941a65ba8767ad518a4cf38073833f4617d1e59edfe60bc4e03b`。Plugin private副本没有.git，身份按正式source树SHA和文件字节核，不虚称其git工作区clean；实际ple_layer.py SHA `31693d169e00a9cdcba760ac4c83fa3dddc7278cd005a852a75c1ef2bbc51a62`。

调用链：Plugin `Qwen3_8FlashNextPLELayer._short_conv_dilated_decode_batched`（ple_layer.py:518）→官方`ple_short_conv_`→先`_ple_conv_kernel`计算卷积输出→`_ple_conv_state_kernel`读取旧历史并原地写回。输出kernel第75行已有`.to(tl.int64)`；**state kernel第165行缺该转换**，第188/197行状态读/写共享`row * ss0`。QSA-only开关只控制可选接入组，不禁用PR455后这条直接import的PLE基础调用；ATen的index/index_put修复和index_select黑名单不覆盖这个独立Triton kernel。

4个现有state特化的TTIR均为`load i32 → muli(row,204800):i32 → addptr`；LLVM仍为`mul i32 → sext i32 to i64 → getelementptr bfloat`，不是调试元数据中的无害i32，也不是仅输入dtype=i32。匹配Decode二进制反汇编：`0x130 s.mull.i32 sreg7,sreg5,0x32000`，`0x148 s.cnvt.i64.i32`，`0x178 shll.b64 ...1`，`0x180 add.i64`；即**溢出后再扩位，再乘BF16的2字节**。0x1a0发起旧state读取，0x1d8为其等待；与驱动PC减load基址精确相同。

有效每rank PLE channels10240、history9，state元素stride=(204800,1,10240)，NULL0；保存特化rows66135或84094，故合法row可远超32位地址边界。首个溢出row是`floor((2^31-1)/204800)+1=10486`，**不是旧generic stride102400路径的20972**。row范围mask只判断row合法，不能阻止乘积溢出；HAS_INITIAL=false最多阻止读旧状态，仍不能使错误写回地址正确。CPU无界整数遍历当前84093个非NULL合法row，其中73608个row的原i32地址不等于正确地址；该统计不是模型实际使用了73608个row。

### 与本次寄存器现场的吻合

三个驱动dump均为相对PC0x1d8、函数长度608（0x260）字节，与现有Decode特化的函数长度和局部指令相同；原始driver没有launch二进制SHA，因此不冒称已唯一绑定所有缓存变体。三个dump的`s6=0x12768000,s7=0xffffffff`均对应已sign-extend并左移后的byte offset **-3985211392**。按该指令数据流反推、并在所有保存容量范围内唯一满足的row为**11242**；它合法，且不是从scheduler block ID猜测。

| 值 | 正确i64 | 原i32后扩位 |
|---|---:|---:|
| row × 204800（元素） | 2302361600 | -1992605696 |
| BF16 byte offset | 4604723200 | -3985211392 |
| 实际地址相对正确地址的偏差 | 0 | -8589934592（-8GiB） |

首dump state基址由s8/s9得到0xe5c000000，正确row起点0xf6e768000，错误row起点0xd6e768000；第二dump基址不同但同样偏移-8GiB。结合driver明确在PLE旧状态读处invalid page，是本次非法访问的强机制证据，不需要假设QSA、FP32通信或脏状态数值才能解释。原完整indices/PT及真实row向量未保存，因此以上明确为**基于匹配机器码数据流的寄存器反推**，不伪称设备输入逐值读取或受控GPU再现。C1小索引的通过不能覆盖这个地址边界；graph只复用了已有错误地址计算，不足以单独称graph pointer生命周期错误。

## 取证完整性与下一步

唯一CPU执行成功，D/report.json SHA `9b1dc74d88f660b7a45f0e37149e2660834be6c5a11e159fc6915adccf71e28a`，MANIFEST.json SHA `963e268424fdff94edc8302c503e74b3c83c30203f4cc7036216c7255de2c334`。588文件/182491263bytes逐文件SHA/大小独立复核全部一致；包含原事故服务+8rank日志、native API/token日志、实际源码、4个state特化及已有输出特化、完整TTIR/LLIR/二进制/离线反汇编、CPU地址边界检查、3份寄存器反推和repo身份。没有新增GPU state/PT，也没有把旧047两条张量计入formal事故。

最窄修复建议是state kernel加载row后立即`.to(tl.int64)`，在乘ss0前扩位，让读历史与写回共用正确地址；不改数学/采样，不改权重，不靠降低并发或禁用graph隐藏问题。**本轮没有改生产源码或验证修复。** 后续需用户批准修复/设备受控验证；危险原实现先做有界地址探针而不是直接大池非法访问，固定实现覆盖row10485/10486/11242、高row、NULL/负数/空请求、prefill/decode、旧历史读/写回/canary及capture+至少两次changed-index replay。再按批准预算做同服务小范围回归；重启8010或新增埋点另行确认，8035保持不访问，全量GPQA不自动启动。静态/CPU通过不代替固定kernel GPU和新正式精度gate，也不能据本事故认定此前60K推理不收敛由该缺陷造成。

knowledge_delta=refined：大状态地址审计必须覆盖每条独立kernel的加载→乘法→扩位顺序，不能以输出kernel/通用index已修复推定state写回也安全；阈值由真实row stride决定。此处只完成离线定位阶段，无性能结论。
