# diag-001-hot1k：充分预热后同机1K对照完成

- 结论：**没有复现当前采样代码的显著热态回退**；原生比较、独立CPU复核和最终源服务核验全部passed。保留原PR1069，未安装新优化或修改原服务。
- 授权：用户明确要求：原测试结束后保持其他配置，充分预热采样再做同机1K受控；有差距才继续clone/filter。用户另外明确批准本远端目录。
- mode=targeted / scope=performance_only；P1024/D1024/C64/N128，finiteBatch。三组只比较旧/新采样过滤路径，其他均为当前软件栈；**不是整个历史opt15镜像的复刻**。
- mx-59，私有qwen3vl-hot1k-mx59-20261105/GPU6,7/TP2 BF16/8037；原用户qwen3vl/opt16/8030/GPU0,1全程保留。硬件与端口隔离差异各角色相同，不与历史GPU0/1或其他Host精确混算。

## 优化方向与瓶颈依据

[上一只读诊断](../../20261104-qwen3vl-opt16-performance-gap/README.md)观察到P1K对历史opt15总TPS-35.21%，但中位ITL仅约+4.8%，真实采样M1..64/int32专化在benchmark期间继续准备；启动dummy是M64/int64，graph完成不足以证明实际采样全热。新增out-of-place clone是另一个静态新增工作，尚未单独计时。先验证热态E2E是否真实退化，再决定是否深挖clone。

## 优化内容与适用边界

**本轮未改生产代码。** 从源有效状态无暂停commit生成snapshot293f7edeb76f455df16e9a36474229fe9de1ac3747359b7d413bcaacafdbd90f，规范化挂载Source/Destination/RW/Propagation逐项相同；私有/workspace与源不共享，完整源文件/配置/模型tokenizer指纹一致后才实验。

冻结old1→current→old2，仅两个filter实现、两个export和两个Plugin桥接文件切换。历史apply_top_k_top_p接口仅私有old角色使用，不给生产加兼容入口。Attention原paged/default split0、MoE/main+INT8寻址修复、FlagGems、vLLM与其他配置保持。原argv/env/cwd复用，只有GPU6/7及8037用于隔离；.91、prefixOFF、batch8192/seq64、FULL_AND_PIECEWISE64、max_model_len262144、有效T.7/P.8/K20/rep1均相同，**无model requestseed**。维护版client显式temperature.7与原模型默认一致；派生client数据seed跨角色配对，不是模型请求seed。

每role先6数值对照（M1/8/64、BF16-grid/任意FP32、V151936、old/new/public）、18变化输入组件graph回放，再模型startup只读profile元数据证明两rank实际MetaX函数成功返回、capture与至少2次真实replay；profile正式前移除。函数不替换、不增加RNG或数学操作。首次函数记录为dummy M64/int64，不冒充正式期全batch计数；实际请求按同正常调用链执行，正式期没有侵入counter或GPUcopy。

每role固定4遍HTTPcohort64..1/D8实际默认采样预热，随后维护版2完整1K预热+3计时；HTTPcohort不是每步GPUbatch证明。稳态规则预先固定：最后2预热TPS差幅≤3%，3计时差幅≤5%，旧/回切漂移≤3%，每个计时原生子进程前后缓存新增/改写metadata=0。全部轮保留，未丢慢轮或从duration扣停顿。目标为steady_state，冷启动不在优化目标内。

## 正确性与路径命中

三role共18组件例/54变化输入组件graph回放通过，两rankstartup backend/capture/replay成功返回和卸除profile通过。CPU独立FP64掩码在随机FP32例验证；BF16-grid与old/new精确对照。它们不是正式模型精度gate，不增加全模型跨batch位级门槛。

三次独立物理映射审计证明诊断worker仅GPU6/7、原worker仍0/1，无GPU共用；未声称宿主CPU/文件系统完全独占。所有role源码前后相同，old1/old2完整源码相同，current完整等于原始当前栈。各role实际KV容量均562,992tokens，prefixOFF，P1K无容量缩减变量。

## 性能效果

| 角色 | 全部3轮总TPS token/s | 中位数 | 组内差幅 | meanTTFT代理 ms | meanTPOT代理 ms | medianITL代理 ms |
|---|---|---:|---:|---:|---:|---:|
| 旧过滤路径 old1 | 3037.84, 3075.80, 3045.66 | 3045.66 | 1.246% | 1711.729 | 40.338 | 38.729 |
| 当前 PR1069 | 3046.84, 3086.50, 3030.17 | 3046.84 | 1.849% | 1723.277 | 40.277 | 38.700 |
| 回切旧过滤 old2 | 3071.25, 3082.82, 3048.41 | 3071.25 | 1.121% | 1717.202 | 39.982 | 38.452 |

当前对首旧 **+0.03874%**，回切对首旧 **+0.84038%**；当前对两次旧中位数的平均参考 **-0.37985%**。差距小于本组1.12–1.85%轮间波动和旧/回切漂移，没有可分辨的采样路径净退化，不能将+0.04%称为性能优化收益。

Prefill代理meanTTFT当前+0.675%，Decode代理meanTPOT -0.152%、medianITL -0.074%；都在冻结守护范围。指标包含排队、主机、采样、通信和网络残余，不是纯GPU阶段时间。三组所有15个原生完整轮均128成功、输入/输出各131072tokens；9个计时轮共1152个主请求全部成功。原生client自带资格请求不计入128统计，仍保留在原生流程中。

9个计时窗口编译缓存新增与改写均0，三组最大客户端全流token事件间隙分别0.42318/0.42943/0.46167秒。此为原生start_times/ttfts/itls重建的客户端事件间隙，不冒充GPU空闲trace或编译耗时；缓存metadata计数也不等于kernel执行次数。

### 对历史gap的解释边界

原大差距在充分预热后的当前栈同机对照中没有复现，支持先前冷专化/JIT或首次模块准备混入短输入测量的解释。旧矩阵首轮与尾部停顿、实际int32形状模板持续产生的证据保留。但旧opt15 CSV缺精确性能实例绑定，原opt16用户矩阵在GPU0/1、本次在6/7，**不能把两者全部历史差额都量化归给预热，也不能说所有长输入gap已解决**。本组只排除了当前采样版本在这套当前公共栈/P1K上的大幅稳态退化。

## 决定、风险与回退

保留原容器中的当前PR1069及MoE修复，原API PID3036790/startticks673628125/argv/env/cwd和源码/tokenizer指纹不变、models200；source_stop_calls=0。控制器已退出、私有当前代码恢复、诊断GPU进程释放。未修改或回退生产clone/filter，也未部署新代码或提交推送。

条件分支“热态还有差距再定位clone/filter”未触发：本组无超出波动的净退化；没有额外GPU微测、profile或改造。新增clone仍客观存在，**本轮没有独立测出它的耗时，更没有证明它零成本**。若未来有有效稳定回退，先核验真实请求布局和实际ATen clone注册backend，再做同注册环境的fullAPI/clone/sort对照，避免用nativeTorch-only clone成本直接替代模型成本。

本次无新完整精度gate或四场景正式验收，P4K/P16K/P32K未重测；原正式失败与历史数据不改判。任务必要待办已完成，唯一监控qwen3-vl-1k已删除。

## 准备事件与证据保留

另一模型远端参考读取被自动审批拒绝，未执行；实际工具链来自当前项目。最初上传因目录未授权被拒，用户明确授权后才创建该精确目录。详细内部元数据监控提示被拒，改用不含内部路径/PID/哈希的通用提示后创建，现已删除。

旧prepare因docker commit stdout附带提示未认出ID，在0模型请求时退出；recover复用快照、源码/mount重验通过，没有第二次commit。首组组件/graph及8320短预热完成后，CLI version/help各30sec超时，在0原生计时请求时退出并完整清理；失败原始记录保留。controlled-002元数据copy2/copystat触发EIO，未启CLI/model；controlled-003改为纯字节复制+SHA，先CPU CLI120预检passed/113flags/CLI与Python0.24.0+empty一致，再固定重开整个角色组；不是看到分数后挑轮。复制旧launch回执导致一次Popen前保护拒绝，唯一followup启动未重复。最终审核启动器一次本地转义错误未执行，修正后纯CPU复核已通过；没有重发模型。

## 规划复盘 plan-hot1k-close-001-20261105

当前累计收益：无新增代码优化；当前采样路径净变化与零不可区分。冷热准备证据改变了排序，优先保证真实采样形状/dtype覆盖与稳态准入，暂不投入clone或TLE重写。Prefill/Decode/Mixed仅有上述代理与客户端时间线，纯设备热点未知；未把局部M1加速比相加为模型收益。

下一触发：未来重启或新稳定回退，按同规则做targeted准入；若有可复现剩余差距，才使用实际ATen注册环境组件时序/必要profiling，再评估保持out-of-place语义的copy+mask融合。完整历史opt15栈需要新的源码/环境/设备绑定后才对照，不盲改现有MoE。当前不自动启动其他场景、精度、profile或新GPU任务。

## 外部证据

R=/public-flash/jinghao/qwen3-VL/20261105-qwen3vl-opt16-hot1k-mx59-001/controlled-003。所有脚本先归档SHA再执行；原生15轮详细JSON、client源码指纹、service/config/source快照、cache前后清单、Graph/物理映射及失败准备材料均在外部任务目录，未复制进模型记录。

- `/public-flash/jinghao/qwen3-VL/20261105-qwen3vl-opt16-hot1k-mx59-001/controlled-003/summary.json` SHA256 `d2cf6f69cda4d3868153c17fde779a5650ef5a34e27f919cd94cd770be8395d7`
- `/public-flash/jinghao/qwen3-VL/20261105-qwen3vl-opt16-hot1k-mx59-001/controlled-003/comparison-result.json` SHA256 `4970856c3b6edf697775bb7f28218100190f0b867bab0c9065f3ca54405ba857`
- `/public-flash/jinghao/qwen3-VL/20261105-qwen3vl-opt16-hot1k-mx59-001/controlled-003/independent-audit.json` SHA256 `5a27994af2cffc6d763718c7bd4b53dfada103e1b50e5360a105b9e5989fb6b4`
- `/public-flash/jinghao/qwen3-VL/20261105-qwen3vl-opt16-hot1k-mx59-001/controlled-003/fresh-final-audit.json` SHA256 `157dba37c32a5fb47106c3e9403397de018df949ec7b3f4f171ea82e35d47d08`
- `/public-flash/jinghao/qwen3-VL/20261105-qwen3vl-opt16-hot1k-mx59-001/controlled-003/source-preserved.json` SHA256 `f6e14c9560427c898a4fa47196e91ba4fb2031ad75f3c3c026340c0b05bd126c`
- `/public-flash/jinghao/qwen3-VL/20261105-qwen3vl-opt16-hot1k-mx59-001/controlled-003/plan.json` SHA256 `9670cad2e8d10a660686123f74a5f0f3889bbe35cd0d7a2c7ea892d43559f928`
- `/public-flash/jinghao/qwen3-VL/20261105-qwen3vl-opt16-hot1k-mx59-001/controlled-003/comparison.json` SHA256 `116187fd988ade638cff8838b8f4aed95c3680685f182f3858992a94b9138f36`

控制器controller_followup.py SHA8ffb65660d955c969b8d6aa6bf2c20b53766b98b47191fd40b5d8b5ece7fe496；独立审核d3ac5c07f3d46bbb10130f1c8a1553428e13a2a62c4887507558803b5284a134；fresh审核c2f15515d6640d5335cee0be76a7985006dd68c61ae7b6003b62f42a2abf2ef7。
