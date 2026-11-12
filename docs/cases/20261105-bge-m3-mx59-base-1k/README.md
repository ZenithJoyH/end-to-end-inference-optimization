# BGE-M3 / mx-59：1K发布镜像对比

> 最新结果：A/B/A对比已完成；当前45228.88、发布26678.94、当前复测76719.81 tok/s。发布镜像未表现出优势，但A/A2漂移69.63%，结论为稳态未证实，不能当正式加速比。GPU3已释放，源服务与原脚本/历史数据保持原状。

- 范围：诊断性1K embedding镜像状态对比，不是正式四场景验收。
- 用户给定base：harbor.baai.ac.cn/flagos-inner-models-release/bge-m3-metax:fp16-dense-vllm0.24.0-ef7339f1-r1-20261104，ID sha256:1785f7a848059ca51932b938b4fdd75565603c456fe1d7bb1251348c42c22472。用户明确所称base是这份发布镜像，而不是IMAGE_MANIFEST中内部构建base ID 11eb78…。
- 源适配容器BGE-M3已有可写层整改；保留现有服务，当前代码通过--pause=false快照复刻到专用比较容器；发布镜像直接创建另一个比较容器。两者保持源挂载一致、同卡串行测量。
- 用户明确授权停止Host PID2575320及释放其显卡，并要求改用该卡；先核对进程启动身份/容器/子树，保存停止命令与证据，不停止容器或无关服务。
- 远程工作根由用户明确给定：/public-flash/jinghao/BGEM3/test/perf_test/benchmark_results/bge-m3，根owner root:root/0755，约12TB空闲，真实路径相同；只建唯一子目录，不改原CSV。
- 历史1K：C64/N256，所有请求成功、实际1024 tokens；SUMMARY 40553.59 tok/s、39.60 req/s。统计第4/5轮分别32897.6123/48209.5723 tok/s，波动明显，历史数据仅作观察。
- 性能Skill调用方明确mode=targeted，scenario=embedding-p1024-c64-n256；方法入口已读。维护版runner只支持/v1/completions，不能签发embedding原生比较回执；本次沿用用户已经指定并维护的原生embedding脚本采集，不新写HTTP性能引擎。自动化正式工具状态unsupported/incomplete，诊断数据单独报告。
- 精度Skill mode=baseline-sanity；BGE encoder不适用GPQA/Decode/生成式C8模板。固定embedding请求及C8用原生/v1/embeddings做形状/有限值/归一化与双侧数值比较，不能签发正式精度gate。原发布范围TP1/eager保留，graph门禁不适用于此显式eager诊断，不升级为正式graph验收。

新远端变更工具先记录：/tmp/bgem3-base-case-setup-20261105.py上传至Host /tmp/bgem3-base-case-setup-20261105-m5q8j2.py。只创建唯一case及commands/manifests/results，保存脱敏inspect结构、脚本冻结副本和历史产物SHA；尚不启动/停止服务。工具SHA256：8b307487f905c10f241996f86789c237f90f73a1409f5aa8436ed03fe720b31a。

详细状态与实验见[模型记录](../../../models/BGE-M3/metax/20261105-bge-m3-mx59-base-1k/README.md)。

远端case已建立：`/public-flash/jinghao/BGEM3/test/perf_test/benchmark_results/bge-m3/20261105-bge-m3-mx59-base-1k.x4jxof0i`。PID2575320确认是minicpm-v-4.7-1b容器内8031服务，GPU3 EngineCore为其子进程，启动tick 672014937。用户已明确授权停止该服务及释放显卡。下一命令为case/commands/authorized-stop.py；本地工具`/tmp/bgem3-stop-authorized-20261105.py` SHA256 `f7267bed19897669a9c35e21bcdf5af0a4f2cf12495f1c1117c430cb4d6403a6`。先保存身份/完整子树/mx-smi，精确PID+starttime+cgroup检查后TERM主服务，再仅处理同子树剩余进程；不按进程名/宽泛group停止，不停止容器。保存after并确认GPU3无进程、原BGE8000 health200。

下一变更工具case/commands/prepare.py：从BGE-M3用docker commit --pause=false生成独立当前状态快照（禁止默认暂停），提交前后比对三库内容/安装和模型配置；随后从快照与用户明确给定发布镜像分别create/start两个idle容器，均沿用源两项挂载并用仓库verify-container-mounts.py做机器可读门禁。GPU3空闲前提，原服务不改/不重启。源码、依赖、权重不编辑。包SHA256 `27cafe109092a5aa06de4a606e69c05d2cb523c4df1081efe131ccb3f3a5e207`；文件SHA {"fingerprint.py": "493d13a3a6eb4126b74e881024e148a53265f06344fa31a2a86b79afbaa549df", "prepare.py": "f657d35e1493dfc585a1ab49b639e1c2add2fa2b00484fd3e48a08d5f75ee1d9", "verify-container-mounts.py": "32adacf39859e88ad6e2dad04ada248a00b636c795fed67d34328f5264bec3e3"}。每条mutation argv在执行前保存commands/mutation-xx.json。

授权停止完成：MiniCPM-V-4.7-1B/8031及其子树已退出，GPU3无计算进程。只向核验的主进程/残留关联进程发信号，没有停止容器；BGE8000 health仍200。前后证据case/manifests/authorized-stop.{before,after}.json。GPU6只是最初空闲候选，未创建或运行实验；用户选GPU3后本案例实际身份冻结为TP1/GPU3。

首次prepare在快照已创建之后失败：Docker将--pause弃用提示写stdout，工具误把提示和镜像ID合在一起传image inspect。source前后源码/安装指纹相同；未创建新容器或执行benchmark。快照实际ID为sha256:632f985eee774f5cf25d716d23e84d837e718002033c9a264709b3491d0d74d8。准备v2只读取该固定快照继续复刻，不重做commit；另核对Docker新--no-pause选项和事件，不能只凭命令声明证明源服务未暂停。v2控制器先保存再执行，后续mutation文件使用-v2避免覆盖旧回执。

测量执行方案已保存：case/commands/compare.py，服务控制器service.py。A-current→B-release→A2-current同GPU3/18340串行，均固定5轮、前3轮预热/后2轮统计（全部保留）；末3轮预热span/median<=15%、测量span/median<=15%、A/A2漂移<=15%，否则明确标incomplete，不挑选轮次。各侧启动参数/进程env、CLI prefix支持、导入路径、原生JSON、单条/C8输出都保存；双侧embedding维度1024/有限/单位norm，maxabs<=1e-3、cosine>=.99999。原始客户端始终在当前快照容器执行，保持同一代码，不对源BGE施加压测。每侧900s超时，错误停止推进并回收本任务新服务。数值门槛不等于正式模型精度gate。工具包SHA256 `8b9ffa189be207a6a51abde020718fb294d39b70087c9cc7b8f65493f6d26b8e`；文件SHA {"service.py": "1688493f83945f4d5c8ceef39f7358e6dcd42cfab01a71c9930cd7e5b1cea7f4", "compare.py": "82e161d58529efff5f74cb94e8f5da9525ab42dbf52af485ff0de08a05f977d4", "performance-skill-bundle.json": "4e27796b3c628daa6266a4ecdd356c446e172fe0de25d3fced7ddc11abd145ae"}。

执行前补充客户端PID回执和900s停止路径：client.py只包装现有benchmark.main，超时向精确PID/starttime发送SIGINT，由既有wrapper回收本轮原生client进程组；不新写HTTP性能引擎。最终工具包SHA256 `68dc3bf6805b1f044aae70e105bd705a3961751c84bea7f0b0dba882bd5d7d7d`，文件SHA {"service.py": "1688493f83945f4d5c8ceef39f7358e6dcd42cfab01a71c9930cd7e5b1cea7f4", "compare.py": "ebd8742dd1970ac83b75817e5f2ffe80918406194068e3a496770432c46308fe", "client.py": "2bcee0da963c1e6735ae4ecc2bfb6f14bffa15fc1b2ae96ccd74bbdb86e3cfcb", "performance-skill-bundle.json": "4e27796b3c628daa6266a4ecdd356c446e172fe0de25d3fced7ddc11abd145ae"}。准备门禁PREPARED.json已通过，两侧挂载与源相同，当前快照源码/安装指纹与源一致，发布镜像ID为用户指定原始镜像。事件审计仅有commit、无pause/unpause；BGE health200。

A-current首组完成：后2轮均值45228.8765696 tok/s、44.168824775 req/s；所有请求成功，原生prompt tokens一致。预热3轮吞吐span超过15%准入限制，因此本组不是已证实稳态；后2轮span通过。继续按原冻结协议收集发布镜像与A2，保留全部轮次。该差异不用于正式加速结论。

本地新案例schema4、三阶段身份一致性与实验文档链接检查通过。项目级check-project-records未通过，报错均为既有其他模型的文档/过程产物问题；未修改或迁移这些无关材料，不把全局检查标为通过。

完成后只读审计及证据封存工具：case/commands/final-audit.py（本地/tmp/bgem3-compare-final-audit-20261105.py），SHA256 `f2e76be2a3aab02f984ee1060fc9c54d368a5186feeea076b8ef7b50bc30fc36`。核对源与新容器三库/安装指纹、原脚本/历史结果不变、本轮新服务已退出、GPU3无进程、BGE8000 health200，保存FINAL_AUDIT与外部产物SHA清单；不停止/删除容器，不修改运行环境。

## 完成结果

| 组别 | Total tok/s | Req/s | Mean E2EL(ms) | 各轮P99均值(ms) |
|---|---:|---:|---:|---:|
| A-current | 45228.88 | 44.17 | 1121.54 | 4238.29 |
| B-release | 26678.94 | 26.05 | 1737.07 | 5719.10 |
| A2-current | 76719.81 | 74.92 | 950.71 | 2587.63 |

全部15轮/3840个benchmark请求成功；C1/C8数值检查通过。三组预热均未通过15%稳定准入，A/A2漂移69.63%，不能认定稳态收益或退化根因。原始结果与审计见`/public-flash/jinghao/BGEM3/test/perf_test/benchmark_results/bge-m3/20261105-bge-m3-mx59-base-1k.x4jxof0i`；COMPARISON SHA256 `faa01afc2bcd21069a411830dddd717be5698bf68fbecff285269bcba6a93eb9`。镜像/挂载/实际导入身份已核对，最终审计passed；源三库/原脚本/历史产物不变，原BGE8000 health200，两个新容器保留idle、GPU3释放。未提交推送，未做正式精度/四场景验收。

最终本地三阶段schema/身份/实验链接/仅Markdown与YAML材料检查通过。远端case根README.md保存独立可读结果摘要，后于SHA256SUMS生成，不在旧SHA清单内；原生COMPARISON/FINAL_AUDIT及测量证据保持原样。
