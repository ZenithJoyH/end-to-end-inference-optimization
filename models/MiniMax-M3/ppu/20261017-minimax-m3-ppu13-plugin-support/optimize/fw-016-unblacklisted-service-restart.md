# fw-016 无卷积黑名单服务重启验证

状态：minimal-regression通过，服务保留运行；启动约16分钟的慢调优现场已保留。用户明确要求重启当前服务，验证撤销thead.yaml修改后的推理，有问题先保留现场分析。未改源码/配置或自动回退。

后续正式精度：[accformal-006](accformal-006-ppu13-gpqa-c64-60k.md)绑定本次相同实例完成全量198题/C64/60K/阈值88%评测，strict-match 179/198=90.40%，gate签发及复验通过，14条60K截断单独记录；本文件重启阶段最小回归本身仍不是正式gate。

## 范围与冻结契约

目标PPU-13 / `minimaxM3`，私有Plugin `/workspace/vllm-plugin-FL.support-minimaxM3-refine001-20261017`、HEAD620892ab；保留fw-014三个源码文件修改，fw-015移除新增测试及yaml差异。唯一待验证变量为不再设置conv3d/cudnn_convolution黑名单。源代码、vLLM及算子库不继续修改。

重启前现场核验旧实例 `fad201d7b6ec:8024:23178:493728712` health200、running/waiting均0。先保存当前源码、启动argv、日志、PID/start ticks、模型和依赖指纹，再只停止该实例及其匹配子进程。使用同启动配置：TP16 BF16、block128、max_model_len100000、max_num_seqs64、max_num_batched_tokens8192、prefix关闭，FULL_AND_PIECEWISE sizes1/2/4/8/16/32/64，8024。

按本地inference-accuracy-evaluation / minimal-regression执行，bundle SHA256 `6e94a080dd3b64544c535e1fd4bda506f55516374d14d0f8ca6aa148bba2c7b2`。重用fw-014原始固定两次C1 + 一轮C8请求，temp0/seed42/max_tokens4096，输出按原先mm:think剥离和水化学式等价规则核验。完整服务需16rank双模式capture及至少2次FULL replay；观察所有请求错误、超时、空输出、截断、异常重复和乱码。PIECEWISE实际replay单独记录，不夸大覆盖。正式GPQA及性能not_run。

## 现场保留与诊断

前台监控；启动等待预算1200秒，超预算或进程退出只记录incomplete，不自动杀服务、恢复黑名单或重复启动。若观察到原样配置的conv3d autotune等待，按精度定位技能冻结日志/服务身份，做只读worker堆栈、设备和原生执行路径分析；问题定位证据与机制根因区分。进一步修改或停止故障现场需遵从用户后续指令。

远端产物目录：`/mnt/nfs/users/jinghao/minimaxM3/20261017-minimax-m3-ppu13-plugin-support/restart-001`，含commands/runtime/logs/checks。旧证据保留不覆盖，脚本执行前已保存。回退能力保留于原健康checkout、refine-001和cleanup-001快照；本次不自动执行回退。

## 当前启动观察与只读定位

2026-10-17 17:05:39 +08:00 启动新实例 `fad201d7b6ec:8024:30544:494374945`。59/59分片约17:07:25读完；17:08:09、17:09:19、17:12:17采样时health均connection-refused、capture记录0、ERROR/Traceback0，TP0/1/15存活，主线程均在视觉Conv3d的Triton autotune设备同步。采样设备记录显示PPU持续工作，不以100%利用率等同模型服务健康。

真实路径：`WorkerFL.determine_available_memory → ModelRunnerFL.profile_run → embed_multimodal → _process_video_input → vision_tower.patch_embedding(nn.Conv3d) → FlagGems ops/conv3d.py:384 → libentry → Triton autotuner.check_disk_cache/benchmark → testing.do_bench → torch.cuda.synchronize`。这是启动多模态显存探测，不是实际文本Prefill/Decode，也不是MoE请求执行。原生缺少vllm._C的warning在上一健康实例同样存在，不作为本次独立根因。

`checks/conv3d-locals-01/02/03.json`提供TP0 tuning key：N=399360、pad后CI=16、CO=1280，input/kernel D/H/W=(2,14,14)，stride=(2,14,14)、padding0、groups1，output空间(1,1,1)，BF16。模型配置num_channels=3，通用Conv3d源码为满足dot K≥16先补齐通道，再遍历392个kernel空间位置。该形状pad后理论计算约6.412TFLOP（原3通道逻辑约1.202TFLOP），pad后输入约5.010GB、输出约1.022GB；这是理论量，不是实测吞吐或kernel时长。

`checks/conv3d-locals-02.json`抓到某候选内部`estimate_ms=4537.877734375`、`n_warmup=1`、`n_repeat=1`。当前THead tune_configs.yaml静态列出11组conv3d候选。多轮do_bench采样行在221（5次估算后的同步）和247（正式计时后的同步）之间变化，Config对象地址也变化；因此已证明候选扫描有推进，不能把长时间未ready直接宣布为永久死锁或kernel正确性bug。内部计时只作启动诊断，不用于正式性能收益比较。

已定位到大规模视觉patch embedding的Conv3d多配置冷调优开销；这是对旧“conv3d autotune同步长时等待”的细化，不归罪于新路由dtype或worker patch，也不推断模型精度回退。只读观察期间没有修改代码、thead.yaml或缓存，也没有再次重启服务。

## 最终结果与结论边界

17:21:43.890 +08:00第4轮现场采样已health200，TP0/1/15均返回worker工作队列等待；相对17:05:39启动约965秒（16分05秒）。原生日志记录17:21:31 `init engine (profile, create kv cache, warmup model) took 845.35 s`；此时间包括profile、KV和预热，不能全归为Conv3d kernel耗时。多轮同步阶段、Config地址变化及最终自行完成，证实本轮不是永久死锁。没有证明下次重启必然更快，也没有清缓存/重复冷启动实验。

两次C1及一轮C8全部完成，最终答案10/10正确，health200。输入185–7241 token、输出22–115 token，均HTTP200/finish_reason=stop，错误/超时/空输出/截断/乱码/异常重复均0。16rank均完成FULL及PIECEWISE各7/7 capture，224条capture记录；native graph计数FULL180、PIECEWISE0、NONE4，满足至少两次FULL replay。PIECEWISE仅capture，未声称请求replay覆盖。

重启后manifest与结束manifest比较：同一服务身份、启动参数、模型配置/tokenizer/权重清单、实际安装vLLM和三个源码树全部不变。Plugin仍只有3个源码文件diff；thead.yaml仍与HEAD一致，无新增测试文件。C1/C8验证期间没有恢复黑名单或修改算子。服务继续保留在127.0.0.1:8024。

本轮结论是“撤销thead.yaml修改后文本推理最小回归正常，但冷启动显著偏慢”；不是完整GPQA、真实图像/视频正确性、100K边界、其他平台或正式性能验收。`pr_readiness=experimental`。前台监控已自然完成，无定时任务需停用；不自动发起后续评测或修改。

若后续需要修复，优先证伪两类候选：匹配非重叠patch embedding的Conv3d→矩阵乘法等价路径，或用经数值/硬件验证的配置避免全量在线扫描；是否接回原生实现应在现有backend/capability边界处理。上述均为未实施方案，不为本轮保留现场而实施修复。

## 可追溯证据

- `runtime/service-manifest.json` SHA256 `af0c73d7102ef7f98575b4cda6b5f5471f8978758f9ce5b14e08ba6d243f365b`；Plugin源码manifest `43ecee69696a24411a4b2da27afc530aa2dd83dc90e837e5a08c1463ecd9644e`，两个算子库与实际安装vLLM指纹不变。
- `runtime/plugin-before-restart.tar.gz` SHA256 `a3c8f639d84dc5adf7c89f8e93e091ff75419c3e6a73c2626a126960fffb11ab`；源码patch SHA256 `468e5432772c16c36279734978e7dbe4a132768742fb239e6bd99f15723b4507`。
- `commands/start-service.sh` SHA256 `1988e94dc2bd2aba08819d65d8f27a3cc31227bc8b1c3b04dd85494aa87d341a`；`logs/previous-service.log`和`logs/service.log`分别保留重启前后现场。
- `checks/operator-startup-analysis.json` SHA256 `ad23a38e67c6254a6c451d84a4271a834a82fffbccaaeadef5a2e54866d0f38c`；底层文件Conv3d SHA256 `604a9af50476d581d04e8baf267ec16385284e2a2fae8ed579b3423314a79011`，THead tuning YAML SHA256 `5ab96b70367ef55edfe745d71526edba8064301080f144ee0703eeb295ba8415`。
- `checks/result.json` SHA256 `ed6c9f500aba9e52108d09a022b125b453389a48f0bff18d0f1885e3bcdd5d8a`；`checks/native-verification.json` SHA256 `f247d07b114241f9b8ea90733ed646232c3709d1067676cd436f667670a342ce`。
- `runtime/service-manifest-after.json` SHA256 `1ee5cc04d788f55664b712415d3863332efdd244307deb84975e4c616d6c8e96`；`checks/startup-validation.json` SHA256 `d0a3be87944344c261a296911474676010f3f37f78a96f029331cdb4a92975c5`。
- `logs/service-frozen.log` SHA256 `1917ba42e65822ae8ddf552ce71e84cca2aefe888608338dcbda47697b614326`，与仍写入的实时service.log分开保存。

知识差量：`refined`，下次遇到此限域启动等待，应先检查实际tuning key、候选是否变化、do_bench同步阶段与repeat，区分冷调优过慢和永久不返回；现阶段不建立跨shape/跨平台性能规律。
